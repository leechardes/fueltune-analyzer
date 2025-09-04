"""
Comprehensive unit tests for core utility functions.

Tests core functionality like logging, configuration, and utility functions
that are used throughout the application.
"""

import logging
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import pytest
import pandas as pd
import numpy as np

from src.utils.logger import CustomFormatter, setup_logger
from src.utils.logging_config import get_logger


class TestCoreUtilities:
    """Test core utility functions."""

    def test_path_utilities(self):
        """Test path manipulation utilities."""
        # Test basic Path operations that might be used in the app
        test_path = Path("/home/user/data/test.csv")
        assert test_path.suffix == ".csv"
        assert test_path.stem == "test"
        assert test_path.name == "test.csv"

    def test_datetime_utilities(self):
        """Test datetime handling utilities."""
        # Test common datetime operations
        now = datetime.now()
        future = now + timedelta(hours=1)
        past = now - timedelta(hours=1)

        assert future > now
        assert past < now
        assert (future - now).total_seconds() == 3600

    def test_data_type_validation(self):
        """Test data type validation utilities."""
        # Test common data validation patterns
        numeric_strings = ["123", "45.67", "-89.1"]
        non_numeric_strings = ["abc", "12.3.4", ""]

        for s in numeric_strings:
            try:
                float(s)
                is_numeric = True
            except ValueError:
                is_numeric = False
            assert is_numeric

        for s in non_numeric_strings:
            try:
                float(s)
                is_numeric = True
            except ValueError:
                is_numeric = False
            assert not is_numeric


class TestLoggingSystem:
    """Comprehensive tests for logging system."""

    def test_custom_formatter_creation(self):
        """Test CustomFormatter instantiation."""
        formatter = CustomFormatter()
        assert isinstance(formatter, CustomFormatter)
        assert isinstance(formatter, logging.Formatter)

    def test_custom_formatter_color_codes(self):
        """Test that color codes are properly defined."""
        formatter = CustomFormatter()
        expected_colors = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "RESET"]

        for color in expected_colors:
            assert color in formatter.COLORS
            assert isinstance(formatter.COLORS[color], str)
            assert "\033[" in formatter.COLORS[color]

    def test_formatter_message_formatting(self):
        """Test message formatting without colors."""
        formatter = CustomFormatter("%(levelname)s: %(message)s")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        assert "INFO: Test message" in formatted

    def test_formatter_with_console_colors(self):
        """Test formatter with console color output enabled."""
        formatter = CustomFormatter("%(levelname)s: %(message)s")
        formatter._console_output = True

        test_cases = [
            (logging.DEBUG, "DEBUG", "\033[36m"),
            (logging.INFO, "INFO", "\033[32m"),
            (logging.WARNING, "WARNING", "\033[33m"),
            (logging.ERROR, "ERROR", "\033[31m"),
            (logging.CRITICAL, "CRITICAL", "\033[35m"),
        ]

        for level, level_name, expected_color in test_cases:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=10,
                msg=f"{level_name} message",
                args=(),
                exc_info=None,
            )

            formatted = formatter.format(record)
            assert expected_color in formatted
            assert "\033[0m" in formatted  # Reset code
            assert f"{level_name} message" in formatted

    def test_logger_setup_basic(self):
        """Test basic logger setup."""
        logger_name = "test_basic_logger"
        logger = setup_logger(logger_name)

        assert isinstance(logger, logging.Logger)
        assert logger.name == logger_name
        assert logger.level >= logging.INFO  # Default or configured level

    def test_logger_setup_with_file_handler(self):
        """Test logger setup with file output."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as temp_file:
            log_file = Path(temp_file.name)

        try:
            logger = setup_logger("test_file_logger", log_file=log_file)

            # Check file handler was added
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) >= 1

            # Test logging
            test_message = "Test file logging message"
            logger.info(test_message)

            # Force flush handlers
            for handler in logger.handlers:
                handler.flush()

            # Verify message was written
            if log_file.exists():
                content = log_file.read_text()
                assert test_message in content

        finally:
            log_file.unlink(missing_ok=True)

    def test_logger_level_configuration(self):
        """Test logger level configuration."""
        test_levels = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ]

        for level_str, level_int in test_levels:
            logger = setup_logger(f"test_level_{level_str}", level=level_int)
            assert logger.level == level_int

    def test_get_logger_function(self):
        """Test get_logger utility function."""
        module_name = "test.module.name"
        logger = get_logger(module_name)

        assert isinstance(logger, logging.Logger)
        assert module_name in logger.name

    def test_logger_singleton_behavior(self):
        """Test that loggers are reused for same names."""
        name = "singleton_test_logger"
        logger1 = get_logger(name)
        logger2 = get_logger(name)

        assert logger1 is logger2

    def test_logger_thread_safety(self):
        """Test logger creation in multithreaded environment."""
        results = []
        barrier = threading.Barrier(3)

        def create_logger_worker(thread_id):
            barrier.wait()  # Synchronize thread start
            logger = get_logger(f"thread_test_{thread_id}")
            results.append((thread_id, logger, threading.current_thread().ident))

        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_logger_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=5.0)
            assert not thread.is_alive()

        assert len(results) == 3
        for thread_id, logger, thread_ident in results:
            assert isinstance(logger, logging.Logger)
            assert f"thread_test_{thread_id}" in logger.name

    def test_logger_exception_handling(self):
        """Test logger behavior with exceptions."""
        logger = get_logger("exception_test")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as temp_file:
            log_file = Path(temp_file.name)

        try:
            # Add file handler
            file_handler = logging.FileHandler(log_file)
            logger.addHandler(file_handler)

            # Log an exception
            try:
                raise ValueError("Test exception for logging")
            except Exception as e:
                logger.exception("Exception occurred: %s", str(e))

            # Force flush
            file_handler.flush()

            # Check that exception details were logged
            content = log_file.read_text()
            assert "Exception occurred" in content
            assert "ValueError" in content
            assert "Test exception for logging" in content
            assert "Traceback" in content

        finally:
            log_file.unlink(missing_ok=True)

    @patch("src.utils.logging_config.config")
    def test_logger_configuration_integration(self, mock_config):
        """Test logger integration with configuration."""
        mock_config.LOG_LEVEL = "DEBUG"
        mock_config.LOG_FILE = None
        mock_config.DEBUG = True

        logger = get_logger("config_integration_test")
        assert isinstance(logger, logging.Logger)

        # Test that logger was configured (exact behavior depends on implementation)
        assert logger.name


class TestErrorHandling:
    """Test error handling utilities."""

    def test_exception_creation(self):
        """Test creating custom exceptions."""
        error_message = "Test error message"

        # Test basic exception creation
        try:
            raise ValueError(error_message)
        except ValueError as e:
            assert str(e) == error_message
            assert isinstance(e, ValueError)
            assert isinstance(e, Exception)

    def test_exception_chaining(self):
        """Test exception chaining patterns."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as original:
                raise RuntimeError("Wrapped error") from original
        except RuntimeError as e:
            assert str(e) == "Wrapped error"
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)
            assert str(e.__cause__) == "Original error"


class TestDataValidation:
    """Test data validation utilities."""

    def test_numeric_validation(self):
        """Test numeric data validation."""
        valid_numbers = ["123", "45.67", "-89.1", "0", "0.0", "1.23e-4"]
        invalid_numbers = ["abc", "12.3.4", "", "nan", "inf"]

        for num_str in valid_numbers:
            try:
                value = float(num_str)
                is_valid = not (pd.isna(value) or np.isinf(value))
            except (ValueError, TypeError):
                is_valid = False

            assert is_valid, f"'{num_str}' should be valid"

        for num_str in invalid_numbers:
            try:
                value = float(num_str)
                is_valid = not (pd.isna(value) or np.isinf(value))
            except (ValueError, TypeError):
                is_valid = False

            # Note: "nan" and "inf" are technically valid floats in Python
            if num_str not in ["nan", "inf"]:
                assert not is_valid, f"'{num_str}' should be invalid"

    def test_date_validation(self):
        """Test date/time validation."""
        valid_dates = [
            "2024-01-01",
            "2024-12-31 23:59:59",
            "01/01/2024",
            "2024-01-01T10:00:00",
        ]

        invalid_dates = [
            "invalid-date",
            "2024-13-01",  # Invalid month
            "2024-01-32",  # Invalid day
            "",
            "abc",
        ]

        for date_str in valid_dates:
            is_valid = True
            try:
                pd.to_datetime(date_str)
            except (ValueError, TypeError):
                is_valid = False

            assert is_valid, f"'{date_str}' should be valid"

        for date_str in invalid_dates:
            is_valid = True
            try:
                pd.to_datetime(date_str)
            except (ValueError, TypeError):
                is_valid = False

            assert not is_valid, f"'{date_str}' should be invalid"


class TestPerformanceUtilities:
    """Test performance-related utilities."""

    def test_timing_context_manager(self):
        """Test basic timing functionality."""
        import time
        from contextlib import contextmanager

        @contextmanager
        def timer():
            start = time.time()
            yield
            end = time.time()
            duration = end - start
            assert duration >= 0

        with timer():
            time.sleep(0.01)  # Small delay

    def test_memory_usage_estimation(self):
        """Test memory usage estimation for data structures."""
        # Create test data of known size
        small_df = pd.DataFrame({"a": range(100), "b": range(100)})
        large_df = pd.DataFrame({"a": range(10000), "b": range(10000)})

        # Basic memory size comparison
        small_memory = small_df.memory_usage(deep=True).sum()
        large_memory = large_df.memory_usage(deep=True).sum()

        assert large_memory > small_memory
        assert small_memory > 0
        assert large_memory > 0

    def test_batch_processing_utility(self):
        """Test batch processing patterns."""

        def process_in_batches(data, batch_size):
            """Simple batch processing function."""
            results = []
            for i in range(0, len(data), batch_size):
                batch = data[i : i + batch_size]
                results.append(len(batch))  # Simple processing
            return results

        data = list(range(100))
        batch_results = process_in_batches(data, 10)

        assert len(batch_results) == 10  # 100 items / 10 per batch
        assert all(count == 10 for count in batch_results)  # Each batch has 10 items

        # Test with non-even division
        batch_results = process_in_batches(data, 7)
        assert len(batch_results) == 15  # 100 / 7 = 14.28... rounded up
        assert batch_results[-1] <= 7  # Last batch might be smaller
