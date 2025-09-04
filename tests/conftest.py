"""
Pytest configuration and shared fixtures for FuelTune Streamlit tests.
"""

import tempfile
from pathlib import Path
import os
import sys

import pandas as pd
import pytest

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import fixtures from fixtures module
from tests.fixtures.data import *
from tests.fixtures.mocks import *


# Test data fixtures
@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing."""
    return pd.DataFrame(
        {
            "timestamp": [
                "2023-01-01 10:00:00",
                "2023-01-01 10:01:00",
                "2023-01-01 10:02:00",
            ],
            "rpm": [1000, 1500, 2000],
            "throttle": [10.5, 25.0, 45.2],
            "boost": [0.5, 1.2, 2.1],
            "afr": [14.7, 13.8, 12.9],
            "iat": [25.0, 26.5, 28.0],
        }
    )


@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        sample_csv_data.to_csv(f.name, index=False)
        yield Path(f.name)
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components for testing."""
    import sys
    from unittest.mock import MagicMock

    # Mock streamlit module
    mock_st = MagicMock()
    sys.modules["streamlit"] = mock_st

    # Configure common streamlit methods
    mock_st.title = MagicMock()
    mock_st.write = MagicMock()
    mock_st.sidebar = MagicMock()
    mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
    mock_st.file_uploader = MagicMock()
    mock_st.selectbox = MagicMock()
    mock_st.multiselect = MagicMock()
    mock_st.button = MagicMock()
    mock_st.success = MagicMock()
    mock_st.error = MagicMock()
    mock_st.warning = MagicMock()
    mock_st.info = MagicMock()
    mock_st.plotly_chart = MagicMock()

    yield mock_st


@pytest.fixture
def fueltech_sample_fields():
    """Sample FuelTech field mappings for testing."""
    return {
        "timestamp": "Time",
        "rpm": "Engine RPM",
        "throttle": "Throttle Position",
        "boost": "Manifold Pressure",
        "afr": "Air/Fuel Ratio",
        "iat": "Intake Air Temperature",
        "ect": "Engine Coolant Temperature",
        "ignition_advance": "Ignition Advance",
        "fuel_pressure": "Fuel Pressure",
        "oil_pressure": "Oil Pressure",
    }


@pytest.fixture
def large_sample_data():
    """Large sample dataset for performance testing."""
    import numpy as np

    size = 10000
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2023-01-01", periods=size, freq="1S"),
            "rpm": np.random.randint(800, 8000, size),
            "throttle": np.random.uniform(0, 100, size),
            "boost": np.random.uniform(-0.5, 3.0, size),
            "afr": np.random.uniform(10.0, 18.0, size),
            "iat": np.random.uniform(15.0, 80.0, size),
        }
    )


@pytest.fixture
def invalid_csv_data():
    """Invalid CSV data for error testing."""
    return "invalid,csv,data\n1,2\n3,4,5,6"


@pytest.fixture(autouse=True)
def reset_config():
    """Reset configuration before each test."""
    # This fixture runs automatically before each test
    yield
    # Any cleanup can go here


# Pytest marks for test categorization
pytestmark = [
    pytest.mark.filterwarnings("ignore::UserWarning"),
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
]
