"""
Configuration module for FuelTune Streamlit application.
Handles environment variables and application settings.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Application settings
        self.APP_NAME: str = os.getenv("APP_NAME", "FuelTune Streamlit")
        self.APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
        self.DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

        # Database settings
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///fueltune.db")

        # Data processing settings
        self.MAX_FILE_SIZE: str = os.getenv("MAX_FILE_SIZE", "50MB")
        allowed_exts_str = os.getenv("ALLOWED_EXTENSIONS", "csv,xlsx,xls")
        self.ALLOWED_EXTENSIONS: list = allowed_exts_str.split(",") if allowed_exts_str else []

        # FuelTech configuration
        self.FUELTECH_FIELDS_COUNT: int = int(os.getenv("FUELTECH_FIELDS_COUNT", "64"))

        # Streamlit settings
        self.STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8503"))
        self.STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")

        # Cache settings
        self.CACHE_EXPIRY_HOURS: int = int(os.getenv("CACHE_EXPIRY_HOURS", "24"))

        # Project paths
        self.PROJECT_ROOT: Path = Path(__file__).parent.absolute()
        self.DATA_DIR: Path = self.PROJECT_ROOT / "data"
        self.SAMPLES_DIR: Path = self.DATA_DIR / "samples"
        self.LOGS_DIR: Path = self.PROJECT_ROOT / "logs"
        self.DOCS_DIR: Path = self.PROJECT_ROOT / "docs"

    def get_log_file_path(self) -> Path:
        """Get the log file path, creating directory if needed."""
        self.LOGS_DIR.mkdir(exist_ok=True)
        return self.LOGS_DIR / "fueltune.log"

    def validate_config(self) -> None:
        """Validate configuration settings."""
        # Ensure required directories exist
        for directory in [self.DATA_DIR, self.SAMPLES_DIR, self.DOCS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_database_config(self) -> dict:
        """Get database configuration."""
        return {
            "url": self.DATABASE_URL,
            "echo": self.DEBUG,
        }


# Create config instance
config = Config()

# Validate configuration on import
config.validate_config()
