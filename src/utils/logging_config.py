"""
Logging configuration for FuelTune Streamlit application.
Provides centralized logging setup with file and console handlers.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

try:
    from config import config
except ImportError:
    # Fallback configuration for testing environments
    class FallbackConfig:
        LOG_LEVEL = "INFO"

        def get_log_file_path(self):
            return Path("logs/fueltune.log")

    config = FallbackConfig()


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

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Set logging level
    log_level = level or getattr(config, "LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
    )

    console_formatter = CustomFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_formatter._console_output = True

    # File handler
    if log_file is None:
        if hasattr(config, "get_log_file_path"):
            log_file = config.get_log_file_path()
        else:
            log_file = Path("logs/fueltune.log")

    # Ensure log directory exists
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
    return setup_logger(name)


# Create default logger instance
logger = get_logger()
