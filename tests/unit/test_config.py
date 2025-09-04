"""
Unit tests for configuration module.
"""

import os
from pathlib import Path
from unittest.mock import patch


def test_config_import():
    """Test that config module can be imported."""
    from config import Config, config

    assert isinstance(config, Config)


def test_default_values():
    """Test default configuration values."""
    from config import Config

    # Test default values when no environment variables are set
    with patch.dict(os.environ, {}, clear=True):
        test_config = Config()
        assert test_config.APP_NAME == "FuelTune Streamlit"
        assert test_config.APP_VERSION == "1.0.0"
        assert test_config.DEBUG is False
        assert test_config.LOG_LEVEL == "INFO"
        assert test_config.FUELTECH_FIELDS_COUNT == 64
        assert test_config.STREAMLIT_SERVER_PORT == 8501


def test_environment_variable_override():
    """Test that environment variables override defaults."""
    from config import Config

    test_env = {
        "APP_NAME": "Test App",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        "FUELTECH_FIELDS_COUNT": "128",
    }

    with patch.dict(os.environ, test_env, clear=True):
        test_config = Config()
        assert test_config.APP_NAME == "Test App"
        assert test_config.DEBUG is True
        assert test_config.LOG_LEVEL == "DEBUG"
        assert test_config.FUELTECH_FIELDS_COUNT == 128


def test_project_paths():
    """Test that project paths are correctly set."""
    from config import config

    assert isinstance(config.PROJECT_ROOT, Path)
    assert isinstance(config.DATA_DIR, Path)
    assert isinstance(config.SAMPLES_DIR, Path)
    assert isinstance(config.LOGS_DIR, Path)
    assert isinstance(config.DOCS_DIR, Path)

    # Test path relationships
    assert config.DATA_DIR == config.PROJECT_ROOT / "data"
    assert config.SAMPLES_DIR == config.DATA_DIR / "samples"


def test_get_log_file_path():
    """Test log file path generation."""
    from config import config

    log_path = config.get_log_file_path()
    assert isinstance(log_path, Path)
    assert log_path.name == "fueltune.log"
    assert log_path.parent == config.LOGS_DIR


@patch("pathlib.Path.mkdir")
def test_validate_config(mock_mkdir):
    """Test configuration validation."""
    from config import Config

    test_config = Config()
    test_config.validate_config()

    # Should create required directories
    assert mock_mkdir.call_count >= 3  # DATA_DIR, SAMPLES_DIR, DOCS_DIR


def test_get_database_config():
    """Test database configuration generation."""
    from config import Config

    test_config = Config()
    db_config = test_config.get_database_config()

    assert isinstance(db_config, dict)
    assert "url" in db_config
    assert "echo" in db_config
    assert db_config["url"] == test_config.DATABASE_URL
    assert db_config["echo"] == test_config.DEBUG


def test_allowed_extensions_parsing():
    """Test that ALLOWED_EXTENSIONS is correctly parsed from string."""
    from config import Config

    test_env = {"ALLOWED_EXTENSIONS": "csv,xlsx,json,txt"}

    with patch.dict(os.environ, test_env, clear=True):
        test_config = Config()
        assert test_config.ALLOWED_EXTENSIONS == ["csv", "xlsx", "json", "txt"]


def test_boolean_parsing():
    """Test boolean values are correctly parsed."""
    from config import Config

    # Test various boolean representations
    test_cases = [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("1", False),  # Only 'true' should be True
        ("yes", False),
        ("", False),
    ]

    for env_value, expected in test_cases:
        with patch.dict(os.environ, {"DEBUG": env_value}, clear=True):
            test_config = Config()
            assert test_config.DEBUG == expected, f"Failed for '{env_value}', expected {expected}"
