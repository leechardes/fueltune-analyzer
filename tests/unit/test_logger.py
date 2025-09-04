"""
Unit tests for logger module.
"""

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_logger_import():
    """Test that logger module can be imported."""
    from src.utils.logger import get_logger, logger, setup_logger

    assert callable(setup_logger)
    assert callable(get_logger)
    assert isinstance(logger, logging.Logger)


def test_setup_logger_basic():
    """Test basic logger setup."""
    from src.utils.logger import setup_logger

    test_logger = setup_logger("test_logger")
    assert isinstance(test_logger, logging.Logger)
    assert test_logger.name == "test_logger"


def test_setup_logger_with_level():
    """Test logger setup with specific level."""
    from src.utils.logger import setup_logger

    test_logger = setup_logger("test_logger", level="DEBUG")
    assert test_logger.level == logging.DEBUG

    test_logger = setup_logger("test_logger2", level="ERROR")
    assert test_logger.level == logging.ERROR


def test_setup_logger_with_file():
    """Test logger setup with custom log file."""
    from src.utils.logger import setup_logger

    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        test_logger = setup_logger("test_logger", log_file=temp_path)

        # Check that file handler is added
        file_handlers = [h for h in test_logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

        # Test logging to file
        test_logger.info("Test message")

        # Verify file contains log message
        assert temp_path.exists()
        content = temp_path.read_text()
        assert "Test message" in content

    finally:
        temp_path.unlink(missing_ok=True)


def test_setup_logger_no_console():
    """Test logger setup without console output."""
    from src.utils.logger import setup_logger

    test_logger = setup_logger("test_logger", console_output=False)

    # Should not have console handler
    console_handlers = [h for h in test_logger.handlers if isinstance(h, logging.StreamHandler)]
    # File handler is also a StreamHandler, so check for stdout specifically
    stdout_handlers = [h for h in console_handlers if h.stream.name == "<stdout>"]
    assert len(stdout_handlers) == 0


def test_get_logger():
    """Test get_logger function."""
    from src.utils.logger import get_logger

    logger1 = get_logger("test")
    logger2 = get_logger("test")

    # Should return the same logger instance
    assert logger1 is logger2


def test_custom_formatter():
    """Test custom formatter functionality."""
    from src.utils.logger import CustomFormatter

    formatter = CustomFormatter("%(levelname)s - %(message)s")

    # Create a test record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # Test formatting
    formatted = formatter.format(record)
    assert "Test message" in formatted


def test_custom_formatter_with_colors():
    """Test custom formatter with color output."""
    from src.utils.logger import CustomFormatter

    formatter = CustomFormatter("%(levelname)s - %(message)s")
    formatter._console_output = True  # Enable colors

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="Test error",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    # Should contain ANSI color codes
    assert "\033[" in formatted  # Color code present
    assert "Test error" in formatted


@patch("src.utils.logger.config")
def test_setup_logger_uses_config(mock_config):
    """Test that setup_logger uses config values."""
    from src.utils.logger import setup_logger

    # Mock config values
    mock_config.LOG_LEVEL = "WARNING"
    mock_config.get_log_file_path.return_value = Path("/tmp/test.log")

    test_logger = setup_logger("config_test_logger")  # Use unique name

    # Should use config log level
    assert test_logger.level == logging.WARNING

    # Should call config for log file path
    mock_config.get_log_file_path.assert_called_once()


def test_logger_prevents_duplicate_handlers():
    """Test that logger doesn't add duplicate handlers."""
    from src.utils.logger import setup_logger

    # Set up logger twice
    logger1 = setup_logger("duplicate_test")
    initial_handler_count = len(logger1.handlers)

    logger2 = setup_logger("duplicate_test")

    # Should be the same logger with same number of handlers
    assert logger1 is logger2
    assert len(logger2.handlers) == initial_handler_count


def test_logger_file_creation():
    """Test that logger creates log file if it doesn't exist."""
    from src.utils.logger import setup_logger

    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "test.log"
        assert not log_file.exists()

        test_logger = setup_logger("test", log_file=log_file)
        test_logger.info("Test message")

        # Log file should be created
        assert log_file.exists()


@pytest.mark.parametrize(
    "level,expected",
    [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
    ],
)
def test_logger_levels(level, expected):
    """Test different logging levels."""
    from src.utils.logger import setup_logger

    test_logger = setup_logger("level_test", level=level)
    assert test_logger.level == expected
