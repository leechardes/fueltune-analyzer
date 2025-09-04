"""
Unit tests for caching module.

Tests memory cache, disk cache, cache manager,
and caching decorators for FuelTech data.

Author: A02-DATA-PANDAS Agent
Created: 2025-01-02
"""

import json
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.data.cache import (
    CacheEntry,
    DiskCache,
    FuelTechCacheManager,
    MemoryCache,
    cached_analysis,
    cached_dataframe,
    get_cache_manager,
)


class TestCacheEntry:
    """Test cases for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating CacheEntry instance."""
        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            data="test_data",
            created_at=now,
            last_accessed=now,
            access_count=1,
            size_bytes=100,
            metadata={"test": "value"},
        )

        assert entry.key == "test_key"
        assert entry.data == "test_data"
        assert entry.created_at == now
        assert entry.access_count == 1
        assert entry.size_bytes == 100
        assert entry.metadata["test"] == "value"


class TestMemoryCache:
    """Test cases for MemoryCache class."""

    def setup_method(self):
        """Setup for each test method."""
        self.cache = MemoryCache(max_size_mb=1, max_entries=10, default_ttl=3600)

    def test_memory_cache_initialization(self):
        """Test memory cache initialization."""
        assert self.cache.max_size_bytes == 1024 * 1024  # 1MB
        assert self.cache.max_entries == 10
        assert self.cache.default_ttl == 3600
        assert len(self.cache._cache) == 0
        assert self.cache._total_size == 0

    def test_set_and_get_simple(self):
        """Test basic set and get operations."""
        self.cache.set("key1", "value1")

        value = self.cache.get("key1")
        assert value == "value1"

    def test_get_nonexistent_key(self):
        """Test getting non-existent key."""
        value = self.cache.get("nonexistent")
        assert value is None

    def test_set_with_ttl(self):
        """Test setting with TTL."""
        self.cache.set("key1", "value1", ttl=1)  # 1 second TTL

        # Should be available immediately
        assert self.cache.get("key1") == "value1"

        # Wait and check expiration
        time.sleep(1.1)
        assert self.cache.get("key1") is None

    def test_set_with_metadata(self):
        """Test setting with metadata."""
        metadata = {"type": "test", "created_by": "unittest"}
        self.cache.set("key1", "value1", metadata=metadata)

        # Metadata is stored but not directly accessible via get
        assert self.cache.get("key1") == "value1"
        assert "key1" in self.cache._cache
        assert self.cache._cache["key1"].metadata == metadata

    def test_delete(self):
        """Test cache deletion."""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

        deleted = self.cache.delete("key1")
        assert deleted is True
        assert self.cache.get("key1") is None

        # Delete non-existent key
        deleted = self.cache.delete("nonexistent")
        assert deleted is False

    def test_clear(self):
        """Test cache clearing."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        assert len(self.cache._cache) == 2

        self.cache.clear()

        assert len(self.cache._cache) == 0
        assert self.cache._total_size == 0

    def test_access_count_tracking(self):
        """Test that access count is tracked."""
        self.cache.set("key1", "value1")

        # Initial access count should be 1 (from set)
        entry = self.cache._cache["key1"]
        assert entry.access_count == 1

        # Get should increment access count
        self.cache.get("key1")
        assert entry.access_count == 2

        self.cache.get("key1")
        assert entry.access_count == 3

    def test_lru_eviction_by_entries(self):
        """Test LRU eviction based on entry count."""
        cache = MemoryCache(max_size_mb=10, max_entries=3)  # Small entry limit

        # Fill cache to capacity
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert len(cache._cache) == 3

        # Add one more - should evict oldest
        cache.set("key4", "value4")

        assert len(cache._cache) == 3
        assert cache.get("key1") is None  # Should be evicted (oldest)
        assert cache.get("key4") == "value4"  # Should be present (newest)

    def test_calculate_size_dataframe(self):
        """Test size calculation for DataFrame."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        size = self.cache._calculate_size(df)

        assert size > 0
        assert isinstance(size, int)

    def test_calculate_size_numpy_array(self):
        """Test size calculation for numpy array."""
        arr = np.array([1, 2, 3, 4, 5])
        size = self.cache._calculate_size(arr)

        assert size == arr.nbytes

    def test_calculate_size_string(self):
        """Test size calculation for string."""
        text = "Hello, World!"
        size = self.cache._calculate_size(text)

        assert size == len(text)

    def test_calculate_size_dict(self):
        """Test size calculation for dictionary."""
        data = {"key": "value", "number": 42}
        size = self.cache._calculate_size(data)

        assert size > 0
        assert isinstance(size, int)

    def test_get_stats(self):
        """Test cache statistics."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        stats = self.cache.get_stats()

        assert stats["entries"] == 2
        assert stats["total_size_mb"] >= 0
        assert stats["max_size_mb"] == 1
        assert stats["max_entries"] == 10
        assert 0 <= stats["utilization"] <= 100
        assert 0 <= stats["size_utilization"] <= 100

    def test_expired_entry_cleanup(self):
        """Test that expired entries are cleaned up on access."""
        self.cache.set("key1", "value1", ttl=1)
        assert self.cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should be cleaned up and return None
        assert self.cache.get("key1") is None
        assert "key1" not in self.cache._cache


class TestDiskCache:
    """Test cases for DiskCache class."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = DiskCache(cache_dir=self.temp_dir, max_size_mb=1, compression=False)

    def teardown_method(self):
        """Cleanup after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_disk_cache_initialization(self):
        """Test disk cache initialization."""
        assert self.cache.cache_dir.exists()
        assert self.cache.max_size_bytes == 1024 * 1024
        assert self.cache.compression is False
        assert self.cache.metadata_db.exists()

    def test_set_and_get_simple(self):
        """Test basic set and get operations."""
        self.cache.set("key1", "value1")

        value = self.cache.get("key1")
        assert value == "value1"

    def test_get_nonexistent_key(self):
        """Test getting non-existent key."""
        value = self.cache.get("nonexistent")
        assert value is None

    def test_set_and_get_dataframe(self):
        """Test caching DataFrame objects."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        self.cache.set("df_key", df)
        retrieved_df = self.cache.get("df_key")

        assert isinstance(retrieved_df, pd.DataFrame)
        pd.testing.assert_frame_equal(df, retrieved_df)

    def test_set_with_ttl(self):
        """Test setting with TTL."""
        self.cache.set("key1", "value1", ttl=1)

        # Should be available immediately
        assert self.cache.get("key1") == "value1"

        # Wait and check expiration
        time.sleep(1.1)
        assert self.cache.get("key1") is None

    def test_delete(self):
        """Test cache deletion."""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

        deleted = self.cache.delete("key1")
        assert deleted is True
        assert self.cache.get("key1") is None

        # Delete non-existent key
        deleted = self.cache.delete("nonexistent")
        assert deleted is False

    def test_clear(self):
        """Test cache clearing."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        self.cache.clear()

        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None

    def test_get_filename_generation(self):
        """Test filename generation from keys."""
        filename1 = self.cache._get_filename("key1")
        filename2 = self.cache._get_filename("key2")
        filename1_again = self.cache._get_filename("key1")

        # Same key should generate same filename
        assert filename1 == filename1_again

        # Different keys should generate different filenames
        assert filename1 != filename2

        # Filenames should have .pkl extension
        assert filename1.endswith(".pkl")

    def test_get_stats(self):
        """Test cache statistics."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", {"data": "value2"})

        stats = self.cache.get_stats()

        assert stats["entries"] == 2
        assert stats["files"] <= stats["entries"]  # Files might be less due to cleanup
        assert stats["total_size_mb"] >= 0
        assert stats["max_size_mb"] == 1
        assert 0 <= stats["size_utilization"] <= 100
        assert str(self.cache.cache_dir) in stats["cache_dir"]

    def test_metadata_tracking(self):
        """Test that metadata is properly stored and tracked."""
        metadata = {"type": "test", "created_by": "unittest"}
        self.cache.set("key1", "value1", metadata=metadata)

        # Get should work
        assert self.cache.get("key1") == "value1"

        # Metadata should be in database
        import sqlite3

        with sqlite3.connect(self.cache.metadata_db) as conn:
            result = conn.execute(
                "SELECT metadata FROM cache_metadata WHERE key = ?", ("key1",)
            ).fetchone()

            assert result is not None
            stored_metadata = json.loads(result[0])
            assert stored_metadata == metadata


class TestFuelTechCacheManager:
    """Test cases for FuelTechCacheManager class."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = FuelTechCacheManager(
            memory_cache_mb=1, disk_cache_mb=1, cache_dir=self.temp_dir
        )

    def teardown_method(self):
        """Cleanup after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        assert self.cache_manager.memory_cache is not None
        assert self.cache_manager.disk_cache is not None
        assert isinstance(self.cache_manager.PREFIXES, dict)

    def test_generate_key(self):
        """Test cache key generation."""
        key1 = self.cache_manager._generate_key("df", "session1", "filter")
        key2 = self.cache_manager._generate_key("df", "session1", "filter", {"param": "value"})
        key3 = self.cache_manager._generate_key("df", "session2", "filter")

        assert key1 != key2  # Different parameters
        assert key1 != key3  # Different sessions
        assert "df:session1:filter" in key1
        assert "df:session1:filter" in key2
        assert "df:session2:filter" in key3

    def test_dataframe_caching_small(self):
        """Test DataFrame caching for small data (should go to memory)."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        session_id = "test_session"
        operation = "filter_data"

        # Should return None initially
        cached_df = self.cache_manager.get_dataframe(session_id, operation)
        assert cached_df is None

        # Set DataFrame
        self.cache_manager.set_dataframe(session_id, operation, df)

        # Should retrieve from cache
        cached_df = self.cache_manager.get_dataframe(session_id, operation)
        assert isinstance(cached_df, pd.DataFrame)
        pd.testing.assert_frame_equal(df, cached_df)

    def test_dataframe_caching_with_parameters(self):
        """Test DataFrame caching with parameters."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        session_id = "test_session"
        operation = "filter_data"
        params1 = {"filter": "rpm > 1000"}
        params2 = {"filter": "rpm > 2000"}

        # Cache with different parameters
        self.cache_manager.set_dataframe(session_id, operation, df, params1)

        # Should get None with different parameters
        cached_df = self.cache_manager.get_dataframe(session_id, operation, params2)
        assert cached_df is None

        # Should get DataFrame with same parameters
        cached_df = self.cache_manager.get_dataframe(session_id, operation, params1)
        assert isinstance(cached_df, pd.DataFrame)

    def test_analysis_result_caching(self):
        """Test analysis result caching."""
        result = {"mean_rpm": 2500, "max_tps": 100.0}
        session_id = "test_session"
        analysis_type = "basic_stats"

        # Should return None initially
        cached_result = self.cache_manager.get_analysis_result(session_id, analysis_type)
        assert cached_result is None

        # Set analysis result
        self.cache_manager.set_analysis_result(session_id, analysis_type, result)

        # Should retrieve from cache
        cached_result = self.cache_manager.get_analysis_result(session_id, analysis_type)
        assert cached_result == result

    def test_chart_data_caching(self):
        """Test chart data caching."""
        chart_data = {"x": [1, 2, 3, 4], "y": [10, 20, 30, 40], "title": "Test Chart"}
        session_id = "test_session"
        chart_type = "line_chart"

        # Should return None initially
        cached_data = self.cache_manager.get_chart_data(session_id, chart_type)
        assert cached_data is None

        # Set chart data
        self.cache_manager.set_chart_data(session_id, chart_type, chart_data)

        # Should retrieve from cache
        cached_data = self.cache_manager.get_chart_data(session_id, chart_type)
        assert cached_data == chart_data

    def test_invalidate_session(self):
        """Test session invalidation."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = {"test": "data"}

        session_id = "test_session"

        # Cache some data for the session
        self.cache_manager.set_dataframe(session_id, "operation1", df)
        self.cache_manager.set_analysis_result(session_id, "analysis1", result)

        # Verify data is cached
        assert self.cache_manager.get_dataframe(session_id, "operation1") is not None
        assert self.cache_manager.get_analysis_result(session_id, "analysis1") is not None

        # Invalidate session
        self.cache_manager.invalidate_session(session_id)

        # Data should be gone
        assert self.cache_manager.get_dataframe(session_id, "operation1") is None
        assert self.cache_manager.get_analysis_result(session_id, "analysis1") is None

    def test_get_stats(self):
        """Test cache manager statistics."""
        # Add some data
        df = pd.DataFrame({"a": [1, 2, 3]})
        self.cache_manager.set_dataframe("session1", "op1", df)

        stats = self.cache_manager.get_stats()

        assert "memory_cache" in stats
        assert "disk_cache" in stats
        assert "timestamp" in stats

        # Memory cache should have some data
        assert stats["memory_cache"]["entries"] > 0

    def test_clear_all(self):
        """Test clearing all caches."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = {"test": "data"}

        # Cache some data
        self.cache_manager.set_dataframe("session1", "op1", df)
        self.cache_manager.set_analysis_result("session1", "analysis1", result)

        # Clear all caches
        self.cache_manager.clear_all()

        # All data should be gone
        assert self.cache_manager.get_dataframe("session1", "op1") is None
        assert self.cache_manager.get_analysis_result("session1", "analysis1") is None


class TestCachingDecorators:
    """Test caching decorators."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()

        # Mock the global cache manager
        self.mock_cache_manager = FuelTechCacheManager(
            memory_cache_mb=1, disk_cache_mb=1, cache_dir=self.temp_dir
        )

    def teardown_method(self):
        """Cleanup after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("src.data.cache.get_cache_manager")
    def test_cached_dataframe_decorator(self, mock_get_cache_manager):
        """Test cached_dataframe decorator."""
        mock_get_cache_manager.return_value = self.mock_cache_manager

        call_count = 0

        @cached_dataframe("test_operation", ttl=3600)
        def expensive_dataframe_operation(session_id, param1=None):
            nonlocal call_count
            call_count += 1
            return pd.DataFrame({"result": [call_count, param1 or 0]})

        # First call should execute function
        result1 = expensive_dataframe_operation("session1", param1=10)
        assert call_count == 1
        assert isinstance(result1, pd.DataFrame)

        # Second call with same parameters should use cache
        result2 = expensive_dataframe_operation("session1", param1=10)
        assert call_count == 1  # Should not increment
        pd.testing.assert_frame_equal(result1, result2)

        # Different parameters should execute function again
        result3 = expensive_dataframe_operation("session1", param1=20)
        assert call_count == 2

    @patch("src.data.cache.get_cache_manager")
    def test_cached_analysis_decorator(self, mock_get_cache_manager):
        """Test cached_analysis decorator."""
        mock_get_cache_manager.return_value = self.mock_cache_manager

        call_count = 0

        @cached_analysis("test_analysis", ttl=3600)
        def expensive_analysis(session_id, param1=None):
            nonlocal call_count
            call_count += 1
            return {"result": call_count, "param": param1}

        # First call should execute function
        result1 = expensive_analysis("session1", param1="test")
        assert call_count == 1
        assert result1["result"] == 1

        # Second call should use cache
        result2 = expensive_analysis("session1", param1="test")
        assert call_count == 1  # Should not increment
        assert result1 == result2

    @patch("src.data.cache.get_cache_manager")
    def test_decorator_without_session_id(self, mock_get_cache_manager):
        """Test decorator behavior when session_id is not provided."""
        mock_get_cache_manager.return_value = self.mock_cache_manager

        call_count = 0

        @cached_dataframe("test_operation")
        def operation_without_session_id(some_param):
            nonlocal call_count
            call_count += 1
            return pd.DataFrame({"result": [call_count]})

        # Should execute function normally (no caching)
        result1 = operation_without_session_id("param1")
        result2 = operation_without_session_id("param1")

        assert call_count == 2  # Both calls should execute
        assert isinstance(result1, pd.DataFrame)
        assert isinstance(result2, pd.DataFrame)


class TestGetCacheManager:
    """Test the global cache manager getter."""

    def test_get_cache_manager_singleton(self):
        """Test that get_cache_manager returns same instance."""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()

        assert manager1 is manager2

    def test_get_cache_manager_with_parameters(self):
        """Test get_cache_manager with custom parameters."""
        manager = get_cache_manager(memory_mb=64, disk_mb=128, cache_dir="custom_cache")

        assert isinstance(manager, FuelTechCacheManager)
        # Parameters should be used for initialization


class TestCacheErrorHandling:
    """Test error handling in caching module."""

    def setup_method(self):
        """Setup for each test method."""
        self.cache = MemoryCache(max_size_mb=1, max_entries=10)

    def test_cache_set_oversized_item(self):
        """Test setting item larger than cache capacity."""
        # Create large data that exceeds cache size
        large_data = "x" * (2 * 1024 * 1024)  # 2MB, larger than 1MB cache

        # Should not crash, but item won't be cached
        self.cache.set("large_key", large_data)

        # Item should not be in cache
        assert self.cache.get("large_key") is None

    def test_cache_size_calculation_error(self):
        """Test handling of size calculation errors."""
        # Mock _calculate_size to raise exception
        with patch.object(self.cache, "_calculate_size") as mock_calc:
            mock_calc.side_effect = Exception("Size calculation error")

            # Should not crash but use fallback size
            self.cache.set("test_key", "test_value")

            # Should still be able to retrieve
            assert self.cache.get("test_key") == "test_value"

    def test_disk_cache_file_corruption(self):
        """Test handling of corrupted cache files."""
        temp_dir = tempfile.mkdtemp()

        try:
            cache = DiskCache(cache_dir=temp_dir, max_size_mb=1)

            # Set a value
            cache.set("key1", {"data": "value"})

            # Corrupt the cache file
            cache_files = list(Path(temp_dir).glob("*.pkl"))
            if cache_files:
                with open(cache_files[0], "wb") as f:
                    f.write(b"corrupted data")

                # Should handle corruption gracefully
                result = cache.get("key1")
                assert result is None  # Should return None for corrupted data

        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__])
