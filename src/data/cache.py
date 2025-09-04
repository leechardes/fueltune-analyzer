"""
Caching strategy and implementation for FuelTech data.

Provides multi-level caching for data processing, analysis results,
and expensive computations to improve application performance.

Author: A02-DATA-PANDAS Agent
Created: 2025-01-02
"""

import hashlib
import json
import pickle
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

import numpy as np
import pandas as pd

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""

    key: str
    data: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    size_bytes: int
    metadata: Dict[str, Any]
    expires_at: Optional[datetime] = None


class CacheError(Exception):
    """Exception raised during cache operations."""


class MemoryCache:
    """
    In-memory cache with LRU eviction and size limits.
    """

    def __init__(self, max_size_mb: int = 256, max_entries: int = 1000, default_ttl: int = 3600):
        """
        Initialize memory cache.

        Args:
            max_size_mb: Maximum cache size in MB
            max_entries: Maximum number of cache entries
            default_ttl: Default time-to-live in seconds
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.default_ttl = default_ttl

        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._total_size = 0

        logger.info(f"Memory cache initialized: {max_size_mb}MB, {max_entries} entries")

    def _calculate_size(self, obj: Any) -> int:
        """Estimate object size in bytes."""
        try:
            if isinstance(obj, pd.DataFrame):
                return int(obj.memory_usage(deep=True).sum())
            elif isinstance(obj, np.ndarray):
                return int(obj.nbytes)
            elif isinstance(obj, (str, bytes)):
                return len(obj)
            elif isinstance(obj, dict):
                return len(json.dumps(obj, default=str).encode("utf-8"))
            else:
                return len(pickle.dumps(obj))
        except Exception:
            # Fallback estimation
            return 1024  # 1KB default

    def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        if not self._cache:
            return

        # Sort by last accessed time
        sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].last_accessed)

        # Remove oldest entries until we're under limits
        while (
            len(self._cache) > self.max_entries or self._total_size > self.max_size_bytes
        ) and sorted_entries:

            key, entry = sorted_entries.pop(0)
            self._total_size -= entry.size_bytes
            del self._cache[key]
            logger.debug(f"Evicted cache entry: {key}")

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        if entry.expires_at is None:
            return False
        return datetime.now() > entry.expires_at

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            # Check expiration
            if self._is_expired(entry):
                self.delete(key)
                return None

            # Update access statistics
            entry.last_accessed = datetime.now()
            entry.access_count += 1

            return entry.data

    def set(
        self,
        key: str,
        data: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set item in cache."""
        with self._lock:
            # Calculate size with error handling
            try:
                size_bytes = self._calculate_size(data)
            except Exception:
                # Use fallback size if calculation fails
                size_bytes = 1024  # 1KB default

            # Check if item is too large
            if size_bytes > self.max_size_bytes:
                logger.warning(f"Item too large for cache: {key} ({size_bytes} bytes)")
                return

            # Remove existing entry if present
            if key in self._cache:
                self._total_size -= self._cache[key].size_bytes

            # Calculate expiration
            expires_at = None
            if ttl is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            elif self.default_ttl > 0:
                expires_at = datetime.now() + timedelta(seconds=self.default_ttl)

            # Create cache entry
            entry = CacheEntry(
                key=key,
                data=data,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                size_bytes=size_bytes,
                metadata=metadata or {},
                expires_at=expires_at,
            )

            self._cache[key] = entry
            self._total_size += size_bytes

            # Evict if necessary
            self._evict_lru()

    def delete(self, key: str) -> bool:
        """Delete item from cache."""
        with self._lock:
            entry = self._cache.pop(key, None)
            if entry:
                self._total_size -= entry.size_bytes
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._total_size = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                "entries": len(self._cache),
                "total_size_mb": self._total_size / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "max_entries": self.max_entries,
                "utilization": (len(self._cache) / self.max_entries) * 100,
                "size_utilization": (self._total_size / self.max_size_bytes) * 100,
            }


class DiskCache:
    """
    Disk-based cache for persistent storage of larger datasets.
    """

    def __init__(
        self,
        cache_dir: Union[str, Path] = "cache",
        max_size_mb: int = 1024,
        compression: bool = True,
    ):
        """
        Initialize disk cache.

        Args:
            cache_dir: Directory for cache files
            max_size_mb: Maximum cache size in MB
            compression: Whether to compress cache files
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.compression = compression

        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize metadata database
        self.metadata_db = self.cache_dir / "metadata.db"
        self._init_metadata_db()

        logger.info(f"Disk cache initialized: {self.cache_dir}, {max_size_mb}MB")

    def _init_metadata_db(self) -> None:
        """Initialize metadata SQLite database."""
        with sqlite3.connect(self.metadata_db) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    size_bytes INTEGER NOT NULL,
                    expires_at TEXT,
                    metadata TEXT
                )
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_metadata(last_accessed)"
            )

    def _get_filename(self, key: str) -> str:
        """Generate filename for cache key."""
        hash_obj = hashlib.md5(key.encode("utf-8"))
        return f"{hash_obj.hexdigest()}.pkl"

    def _cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        now = datetime.now().isoformat()

        with sqlite3.connect(self.metadata_db) as conn:
            # Find expired entries
            expired = conn.execute(
                "SELECT key, filename FROM cache_metadata WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,),
            ).fetchall()

            # Remove expired files and metadata
            for key, filename in expired:
                file_path = self.cache_dir / filename
                if file_path.exists():
                    file_path.unlink()

                conn.execute("DELETE FROM cache_metadata WHERE key = ?", (key,))

    def _evict_lru(self) -> None:
        """Evict least recently used entries to stay under size limit."""
        # Calculate current size
        total_size = 0
        for file_path in self.cache_dir.glob("*.pkl"):
            if file_path.exists():
                total_size += file_path.stat().st_size

        if total_size <= self.max_size_bytes:
            return

        # Get entries sorted by last accessed
        with sqlite3.connect(self.metadata_db) as conn:
            entries = conn.execute(
                "SELECT key, filename, size_bytes FROM cache_metadata ORDER BY last_accessed ASC"
            ).fetchall()

            # Remove oldest entries
            for key, filename, size_bytes in entries:
                if total_size <= self.max_size_bytes:
                    break

                file_path = self.cache_dir / filename
                if file_path.exists():
                    file_path.unlink()
                    total_size -= size_bytes

                conn.execute("DELETE FROM cache_metadata WHERE key = ?", (key,))
                logger.debug(f"Evicted disk cache entry: {key}")

    def get(self, key: str) -> Optional[Any]:
        """Get item from disk cache."""
        self._cleanup_expired()

        with sqlite3.connect(self.metadata_db) as conn:
            result = conn.execute(
                "SELECT filename, expires_at FROM cache_metadata WHERE key = ?", (key,)
            ).fetchone()

            if result is None:
                return None

            filename, expires_at = result

            # Check expiration
            if expires_at:
                if datetime.now() > datetime.fromisoformat(expires_at):
                    self.delete(key)
                    return None

            # Load data from file
            file_path = self.cache_dir / filename
            if not file_path.exists():
                # Clean up orphaned metadata
                conn.execute("DELETE FROM cache_metadata WHERE key = ?", (key,))
                return None

            try:
                with open(file_path, "rb") as f:
                    data = pickle.load(f)

                # Update access statistics
                now = datetime.now().isoformat()
                conn.execute(
                    "UPDATE cache_metadata SET last_accessed = ?, access_count = access_count + 1 WHERE key = ?",
                    (now, key),
                )

                return data

            except Exception as e:
                logger.error(f"Failed to load cache entry {key}: {str(e)}")
                self.delete(key)
                return None

    def set(
        self,
        key: str,
        data: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set item in disk cache."""
        filename = self._get_filename(key)
        file_path = self.cache_dir / filename

        try:
            # Serialize data to file
            with open(file_path, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

            # Get file size
            size_bytes = file_path.stat().st_size

            # Calculate expiration
            expires_at = None
            if ttl is not None:
                expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()

            # Update metadata
            now = datetime.now().isoformat()
            metadata_json = json.dumps(metadata or {})

            with sqlite3.connect(self.metadata_db) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache_metadata
                    (key, filename, created_at, last_accessed, size_bytes, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (key, filename, now, now, size_bytes, expires_at, metadata_json),
                )

            # Clean up if necessary
            self._evict_lru()

        except Exception as e:
            logger.error(f"Failed to cache item {key}: {str(e)}")
            if file_path.exists():
                file_path.unlink()

    def delete(self, key: str) -> bool:
        """Delete item from disk cache."""
        with sqlite3.connect(self.metadata_db) as conn:
            result = conn.execute(
                "SELECT filename FROM cache_metadata WHERE key = ?", (key,)
            ).fetchone()

            if result:
                filename = result[0]
                file_path = self.cache_dir / filename

                if file_path.exists():
                    file_path.unlink()

                conn.execute("DELETE FROM cache_metadata WHERE key = ?", (key,))
                return True

        return False

    def clear(self) -> None:
        """Clear all disk cache entries."""
        # Remove all pickle files
        for file_path in self.cache_dir.glob("*.pkl"):
            file_path.unlink()

        # Clear metadata
        with sqlite3.connect(self.metadata_db) as conn:
            conn.execute("DELETE FROM cache_metadata")

    def get_stats(self) -> Dict[str, Any]:
        """Get disk cache statistics."""
        total_size = 0
        file_count = 0

        for file_path in self.cache_dir.glob("*.pkl"):
            if file_path.exists():
                total_size += file_path.stat().st_size
                file_count += 1

        with sqlite3.connect(self.metadata_db) as conn:
            entry_count = conn.execute("SELECT COUNT(*) FROM cache_metadata").fetchone()[0]

        return {
            "entries": entry_count,
            "files": file_count,
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "size_utilization": (total_size / self.max_size_bytes) * 100,
            "cache_dir": str(self.cache_dir),
        }


class FuelTechCacheManager:
    """
    Multi-level cache manager for FuelTech data processing.

    Combines memory and disk caching with intelligent cache key generation
    and automatic cache invalidation based on data changes.
    """

    def __init__(
        self,
        memory_cache_mb: int = 256,
        disk_cache_mb: int = 1024,
        cache_dir: Union[str, Path] = "cache",
    ):
        """
        Initialize cache manager.

        Args:
            memory_cache_mb: Memory cache size in MB
            disk_cache_mb: Disk cache size in MB
            cache_dir: Directory for disk cache
        """
        self.memory_cache = MemoryCache(max_size_mb=memory_cache_mb)
        self.disk_cache = DiskCache(cache_dir=cache_dir, max_size_mb=disk_cache_mb)

        # Cache prefixes for different data types
        self.PREFIXES = {
            "dataframe": "df",
            "analysis": "analysis",
            "aggregation": "agg",
            "chart_data": "chart",
            "quality_results": "quality",
            "statistics": "stats",
        }

        logger.info("FuelTech cache manager initialized")

    def _generate_key(
        self,
        prefix: str,
        session_id: str,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate cache key from components."""
        key_parts = [prefix, session_id, operation]

        if parameters:
            # Create deterministic hash of parameters
            param_str = json.dumps(parameters, sort_keys=True, default=str)
            param_hash = hashlib.md5(param_str.encode("utf-8")).hexdigest()[:8]
            key_parts.append(param_hash)

        return ":".join(key_parts)

    def get_dataframe(
        self,
        session_id: str,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[pd.DataFrame]:
        """Get cached DataFrame."""
        key = self._generate_key("df", session_id, operation, parameters)

        # Try memory cache first
        data = self.memory_cache.get(key)
        if data is not None:
            logger.debug(f"Cache hit (memory): {key}")
            return data

        # Try disk cache
        data = self.disk_cache.get(key)
        if data is not None:
            logger.debug(f"Cache hit (disk): {key}")
            # Promote to memory cache
            self.memory_cache.set(key, data, ttl=3600)
            return data

        logger.debug(f"Cache miss: {key}")
        return None

    def set_dataframe(
        self,
        session_id: str,
        operation: str,
        data: pd.DataFrame,
        parameters: Optional[Dict[str, Any]] = None,
        ttl: int = 7200,
    ) -> None:
        """Cache DataFrame data."""
        key = self._generate_key("df", session_id, operation, parameters)

        # Determine cache level based on data size
        data_size = data.memory_usage(deep=True).sum()

        if data_size < 50 * 1024 * 1024:  # < 50MB -> memory cache
            self.memory_cache.set(key, data, ttl=ttl)
            logger.debug(f"Cached to memory: {key}")
        else:  # >= 50MB -> disk cache
            self.disk_cache.set(key, data, ttl=ttl)
            logger.debug(f"Cached to disk: {key}")

    def get_analysis_result(
        self,
        session_id: str,
        analysis_type: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get cached analysis result."""
        key = self._generate_key("analysis", session_id, analysis_type, parameters)

        # Analysis results are typically small, check memory first
        data = self.memory_cache.get(key)
        if data is not None:
            return data

        # Check disk cache
        return self.disk_cache.get(key)

    def set_analysis_result(
        self,
        session_id: str,
        analysis_type: str,
        result: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        ttl: int = 3600,
    ) -> None:
        """Cache analysis result."""
        key = self._generate_key("analysis", session_id, analysis_type, parameters)

        # Analysis results go to memory cache (usually small)
        self.memory_cache.set(key, result, ttl=ttl)

    def get_chart_data(
        self,
        session_id: str,
        chart_type: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get cached chart data."""
        key = self._generate_key("chart", session_id, chart_type, parameters)
        return self.memory_cache.get(key)

    def set_chart_data(
        self,
        session_id: str,
        chart_type: str,
        data: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        ttl: int = 1800,
    ) -> None:
        """Cache chart data."""
        key = self._generate_key("chart", session_id, chart_type, parameters)
        self.memory_cache.set(key, data, ttl=ttl)

    def invalidate_session(self, session_id: str) -> None:
        """Invalidate all cache entries for a session."""
        # Memory cache
        keys_to_delete = []
        for key in self.memory_cache._cache.keys():
            if f":{session_id}:" in key:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            self.memory_cache.delete(key)

        # Disk cache - more complex as we need to query metadata
        with sqlite3.connect(self.disk_cache.metadata_db) as conn:
            keys_to_delete = conn.execute(
                "SELECT key FROM cache_metadata WHERE key LIKE ?",
                (f"%:{session_id}:%",),
            ).fetchall()

            for (key,) in keys_to_delete:
                self.disk_cache.delete(key)

        logger.info(f"Invalidated cache for session {session_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            "memory_cache": self.memory_cache.get_stats(),
            "disk_cache": self.disk_cache.get_stats(),
            "timestamp": datetime.now().isoformat(),
        }

    def clear_all(self) -> None:
        """Clear all caches."""
        self.memory_cache.clear()
        self.disk_cache.clear()
        logger.info("Cleared all caches")


# Cache decorators for automatic caching
def cached_dataframe(operation: str, ttl: int = 7200, use_parameters: bool = True):
    """Decorator for caching DataFrame operations."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract session_id from arguments - only from kwargs or first arg if named session_id
            session_id = kwargs.get("session_id")
            if not session_id and args and hasattr(func, "__code__"):
                # Check if first parameter is named 'session_id'
                param_names = func.__code__.co_varnames[: func.__code__.co_argcount]
                if param_names and param_names[0] == "session_id":
                    session_id = args[0]

            if not session_id:
                # No caching if no session_id
                return func(*args, **kwargs)

            # Get cache manager
            cache_manager = get_cache_manager()

            # Generate parameters for cache key
            parameters = kwargs if use_parameters else None

            # Try to get cached result
            cached_result = cache_manager.get_dataframe(session_id, operation, parameters)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            if isinstance(result, pd.DataFrame):
                cache_manager.set_dataframe(session_id, operation, result, parameters, ttl)

            return result

        return wrapper

    return decorator


def cached_analysis(analysis_type: str, ttl: int = 3600, use_parameters: bool = True):
    """Decorator for caching analysis results."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract session_id from arguments - only from kwargs or first arg if named session_id
            session_id = kwargs.get("session_id")
            if not session_id and args and hasattr(func, "__code__"):
                # Check if first parameter is named 'session_id'
                param_names = func.__code__.co_varnames[: func.__code__.co_argcount]
                if param_names and param_names[0] == "session_id":
                    session_id = args[0]

            if not session_id:
                return func(*args, **kwargs)

            # Get cache manager
            cache_manager = get_cache_manager()

            # Generate parameters for cache key
            parameters = kwargs if use_parameters else None

            # Try to get cached result
            cached_result = cache_manager.get_analysis_result(session_id, analysis_type, parameters)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            if isinstance(result, dict):
                cache_manager.set_analysis_result(
                    session_id, analysis_type, result, parameters, ttl
                )

            return result

        return wrapper

    return decorator


# Global cache manager instance
_cache_manager = None


def get_cache_manager(
    memory_mb: int = 256, disk_mb: int = 1024, cache_dir: str = "cache"
) -> FuelTechCacheManager:
    """Get the global cache manager instance."""
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = FuelTechCacheManager(
            memory_cache_mb=memory_mb, disk_cache_mb=disk_mb, cache_dir=cache_dir
        )

    return _cache_manager


if __name__ == "__main__":
    # Example usage and testing
    import numpy as np

    # Initialize cache manager
    cache = FuelTechCacheManager(memory_cache_mb=64, disk_cache_mb=128)

    # Create test data
    test_df = pd.DataFrame(
        {
            "time": np.arange(0, 10, 0.1),
            "rpm": np.random.randint(1000, 3000, 100),
            "tps": np.random.uniform(0, 100, 100),
        }
    )

    session_id = "test_session_001"

    # Cache DataFrame
    print("Caching DataFrame...")
    cache.set_dataframe(session_id, "filtered_data", test_df, {"filter": "rpm > 2000"})

    # Retrieve from cache
    print("Retrieving from cache...")
    cached_df = cache.get_dataframe(session_id, "filtered_data", {"filter": "rpm > 2000"})

    print(f"Cache hit: {cached_df is not None}")
    print(f"Data shape: {cached_df.shape if cached_df is not None else 'None'}")

    # Cache analysis result
    analysis_result = {
        "mean_rpm": test_df["rpm"].mean(),
        "max_tps": test_df["tps"].max(),
        "duration": test_df["time"].max() - test_df["time"].min(),
    }

    cache.set_analysis_result(session_id, "basic_stats", analysis_result)
    cached_analysis = cache.get_analysis_result(session_id, "basic_stats")

    print(f"Analysis cache hit: {cached_analysis is not None}")

    # Show cache stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")
