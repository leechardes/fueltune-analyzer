"""
Logging configuration for FuelTune Streamlit application.
Provides centralized logging setup with file and console handlers.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from config import config


class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    # Color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        """Format the log record with colors for console."""
        if hasattr(self, "_console_output"):
            color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
            reset = self.COLORS["RESET"]
            record.levelname = f"{color}{record.levelname}{reset}"

        return super().format(record)


def setup_logger(
    name: str = "fueltune",
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    console_output: bool = True,
) -> logging.Logger:
    """
    Set up and configure logger with file and console handlers.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (defaults to config log path)
        console_output: Whether to output to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set logging level first (even if handlers already exist)
    log_level = level or config.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers if we need to reconfigure
    if logger.handlers and (level is not None or log_file is not None):
        logger.handlers.clear()
    elif logger.handlers:
        return logger

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
    )

    console_formatter = CustomFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_formatter._console_output = True

    # File handler
    if log_file is None:
        log_file = config.get_log_file_path()

    # Ensure parent directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.info(f"Logger '{name}' initialized with level {log_level}")
    return logger


def get_logger(name: str = "fueltune") -> logging.Logger:
    """
    Get or create a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    # If logger already exists, just return it
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    return setup_logger(name)


# Create default logger instance (will be recreated as needed)
logger = get_logger()
