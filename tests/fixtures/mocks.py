"""
Mock objects and factories for FuelTune tests.

Provides mock implementations for external dependencies,
database connections, and complex objects.
"""

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Union
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from faker import Faker

fake = Faker("pt_BR")


class MockDatabase:
    """Mock database for testing database operations."""

    def __init__(self):
        self.sessions = {}
        self.analyses = {}
        self.connection_count = 0
        self.is_connected = False

    def connect(self):
        """Mock database connection."""
        self.is_connected = True
        self.connection_count += 1
        return self

    def disconnect(self):
        """Mock database disconnection."""
        self.is_connected = False

    def execute(self, query: str, params: tuple = None):
        """Mock query execution."""
        if not self.is_connected:
            raise Exception("Database not connected")
        return MockCursor(query, params)

    def create_session(self, session_data: Dict):
        """Mock session creation."""
        session_id = session_data.get("id", f"session_{len(self.sessions)}")
        self.sessions[session_id] = session_data
        return session_id

    def get_session(self, session_id: str):
        """Mock session retrieval."""
        return self.sessions.get(session_id)

    def list_sessions(self):
        """Mock session listing."""
        return list(self.sessions.values())


class MockCursor:
    """Mock database cursor."""

    def __init__(self, query: str, params: tuple = None):
        self.query = query
        self.params = params
        self.fetchone_result = None
        self.fetchall_result = []

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result

    def execute(self, query: str, params: tuple = None):
        self.query = query
        self.params = params
        return self


class MockCache:
    """Mock cache for testing cache operations."""

    def __init__(self):
        self.data = {}
        self.hits = 0
        self.misses = 0
        self.access_log = []

    def get(self, key: str):
        """Mock cache get operation."""
        self.access_log.append(("get", key))
        if key in self.data:
            self.hits += 1
            return self.data[key]
        else:
            self.misses += 1
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Mock cache set operation."""
        self.access_log.append(("set", key, ttl))
        self.data[key] = value

    def delete(self, key: str):
        """Mock cache delete operation."""
        self.access_log.append(("delete", key))
        if key in self.data:
            del self.data[key]
            return True
        return False

    def clear(self):
        """Mock cache clear operation."""
        self.access_log.append(("clear",))
        self.data.clear()

    def size(self):
        """Mock cache size operation."""
        return len(self.data)

    def hit_rate(self):
        """Calculate hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0


class MockCSVParser:
    """Mock CSV parser for testing."""

    def __init__(self):
        self.parse_calls = []
        self.validate_calls = []
        self.detected_format = "37_fields"
        self.field_mappings = {}

    def detect_format(self, file_path: Path):
        """Mock format detection."""
        self.parse_calls.append(("detect_format", file_path))
        return self.detected_format

    def parse(self, file_path: Path, format_type: str = None):
        """Mock CSV parsing."""
        self.parse_calls.append(("parse", file_path, format_type))
        # Return sample data based on format
        if format_type == "37_fields" or self.detected_format == "37_fields":
            return self._get_sample_37_field_data()
        else:
            return self._get_sample_64_field_data()

    def validate(self, data: pd.DataFrame):
        """Mock data validation."""
        self.validate_calls.append(("validate", len(data)))
        # Return validation results
        return {
            "is_valid": True,
            "errors": [],
            "warnings": ["Sample warning for testing"],
            "row_count": len(data),
            "column_count": len(data.columns) if not data.empty else 0,
        }

    def _get_sample_37_field_data(self):
        """Generate sample 37-field data."""
        size = 100
        return pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=size, freq="1S"),
                "rpm": np.random.randint(1000, 3000, size),
                "throttle": np.random.uniform(0, 100, size),
                "boost": np.random.uniform(-0.5, 2.0, size),
                "afr": np.random.uniform(12.0, 16.0, size),
            }
        )

    def _get_sample_64_field_data(self):
        """Generate sample 64-field data."""
        data = self._get_sample_37_field_data()
        # Add additional fields for 64-field format
        size = len(data)
        data["egt1"] = np.random.uniform(300, 800, size)
        data["egt2"] = np.random.uniform(300, 800, size)
        data["lambda2"] = np.random.uniform(0.7, 1.3, size)
        return data


class MockAnalysisEngine:
    """Mock analysis engine for testing analysis modules."""

    def __init__(self):
        self.analysis_calls = []
        self.results = {}

    def calculate_fuel_efficiency(self, data: pd.DataFrame):
        """Mock fuel efficiency calculation."""
        self.analysis_calls.append(("fuel_efficiency", len(data)))
        return {
            "avg_consumption": 8.5,
            "efficiency_score": 0.85,
            "consumption_trend": "stable",
            "recommendations": ["Mantenha RPM entre 2000-3000 para melhor eficiência"],
        }

    def detect_anomalies(self, data: pd.DataFrame):
        """Mock anomaly detection."""
        self.analysis_calls.append(("anomaly_detection", len(data)))
        # Return some fake anomalies
        anomaly_indices = [10, 50, 90] if len(data) > 100 else []
        return {
            "anomaly_count": len(anomaly_indices),
            "anomaly_indices": anomaly_indices,
            "anomaly_scores": [0.95, 0.88, 0.92],
            "anomaly_types": ["rpm_spike", "afr_lean", "temperature_high"],
        }

    def calculate_performance_metrics(self, data: pd.DataFrame):
        """Mock performance metrics calculation."""
        self.analysis_calls.append(("performance_metrics", len(data)))
        return {
            "max_power_rpm": 6500,
            "peak_torque_rpm": 4200,
            "acceleration_0_100": 8.5,
            "quarter_mile": 16.2,
            "efficiency_rating": "B+",
        }

    def generate_correlation_matrix(self, data: pd.DataFrame):
        """Mock correlation matrix generation."""
        self.analysis_calls.append(("correlation_matrix", len(data)))
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        return np.random.rand(len(numeric_cols), len(numeric_cols))


class MockFileSystem:
    """Mock file system for testing file operations."""

    def __init__(self):
        self.files = {}
        self.directories = set(["/"])
        self.access_log = []

    def exists(self, path: Union[str, Path]):
        """Check if file or directory exists."""
        path_str = str(path)
        self.access_log.append(("exists", path_str))
        return path_str in self.files or path_str in self.directories

    def read_file(self, path: Union[str, Path]):
        """Mock file reading."""
        path_str = str(path)
        self.access_log.append(("read", path_str))
        if path_str in self.files:
            return self.files[path_str]
        raise FileNotFoundError(f"File not found: {path_str}")

    def write_file(self, path: Union[str, Path], content: str):
        """Mock file writing."""
        path_str = str(path)
        self.access_log.append(("write", path_str))
        self.files[path_str] = content

    def create_directory(self, path: Union[str, Path]):
        """Mock directory creation."""
        path_str = str(path)
        self.access_log.append(("mkdir", path_str))
        self.directories.add(path_str)

    def list_files(self, directory: Union[str, Path], pattern: str = "*"):
        """Mock file listing."""
        dir_str = str(directory)
        self.access_log.append(("list", dir_str, pattern))
        # Return files in the directory
        return [f for f in self.files.keys() if f.startswith(dir_str)]


@pytest.fixture
def mock_database():
    """Fixture providing mock database instance."""
    return MockDatabase()


@pytest.fixture
def mock_cache():
    """Fixture providing mock cache instance."""
    return MockCache()


@pytest.fixture
def mock_csv_parser():
    """Fixture providing mock CSV parser instance."""
    return MockCSVParser()


@pytest.fixture
def mock_analysis_engine():
    """Fixture providing mock analysis engine instance."""
    return MockAnalysisEngine()


@pytest.fixture
def mock_file_system():
    """Fixture providing mock file system instance."""
    return MockFileSystem()


@pytest.fixture
def mock_streamlit_components():
    """Comprehensive mock for Streamlit components."""
    with patch("streamlit.title") as mock_title, patch("streamlit.write") as mock_write, patch(
        "streamlit.sidebar"
    ) as mock_sidebar, patch("streamlit.columns") as mock_columns, patch(
        "streamlit.file_uploader"
    ) as mock_uploader, patch(
        "streamlit.selectbox"
    ) as mock_selectbox, patch(
        "streamlit.button"
    ) as mock_button, patch(
        "streamlit.success"
    ) as mock_success, patch(
        "streamlit.error"
    ) as mock_error, patch(
        "streamlit.warning"
    ) as mock_warning, patch(
        "streamlit.info"
    ) as mock_info, patch(
        "streamlit.plotly_chart"
    ) as mock_plotly:

        # Configure default return values
        mock_columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_uploader.return_value = None
        mock_selectbox.return_value = "Option 1"
        mock_button.return_value = False

        yield {
            "title": mock_title,
            "write": mock_write,
            "sidebar": mock_sidebar,
            "columns": mock_columns,
            "file_uploader": mock_uploader,
            "selectbox": mock_selectbox,
            "button": mock_button,
            "success": mock_success,
            "error": mock_error,
            "warning": mock_warning,
            "info": mock_info,
            "plotly_chart": mock_plotly,
        }


@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state."""
    session_state = {}

    class MockSessionState:
        def __getitem__(self, key):
            return session_state.get(key)

        def __setitem__(self, key, value):
            session_state[key] = value

        def __contains__(self, key):
            return key in session_state

        def get(self, key, default=None):
            return session_state.get(key, default)

        def setdefault(self, key, default):
            return session_state.setdefault(key, default)

    return MockSessionState()


@pytest.fixture
def temporary_sqlite_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name

    # Create basic table structure
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP,
            description TEXT,
            vehicle TEXT,
            driver TEXT,
            track TEXT
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            analysis_type TEXT,
            results TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    """
    )
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


class MockEventSystem:
    """Mock event system for testing event-driven features."""

    def __init__(self):
        self.events = []
        self.listeners = {}

    def emit(self, event_type: str, data: Any = None):
        """Emit an event."""
        event = {"type": event_type, "data": data, "timestamp": datetime.now()}
        self.events.append(event)

        # Notify listeners
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                listener(event)

    def on(self, event_type: str, callback: callable):
        """Register event listener."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def off(self, event_type: str, callback: callable):
        """Unregister event listener."""
        if event_type in self.listeners:
            self.listeners[event_type].remove(callback)

    def get_events(self, event_type: str = None):
        """Get events by type."""
        if event_type:
            return [e for e in self.events if e["type"] == event_type]
        return self.events.copy()

    def clear_events(self):
        """Clear all events."""
        self.events.clear()


@pytest.fixture
def mock_event_system():
    """Fixture providing mock event system."""
    return MockEventSystem()


def create_mock_config(overrides: Dict[str, Any] = None):
    """Create a mock configuration object."""
    default_config = {
        "DATABASE_URL": "sqlite:///:memory:",
        "CACHE_TTL": 3600,
        "LOG_LEVEL": "INFO",
        "MAX_FILE_SIZE": 100 * 1024 * 1024,  # 100MB
        "SUPPORTED_FORMATS": ["csv", "txt"],
        "DEFAULT_SESSION_NAME": "Nova Sessão",
        "ANALYSIS_TIMEOUT": 300,
        "CACHE_ENABLED": True,
        "DEBUG": False,
    }

    if overrides:
        default_config.update(overrides)

    return type("MockConfig", (), default_config)()


@pytest.fixture
def mock_config():
    """Fixture providing mock configuration."""
    return create_mock_config()


@pytest.fixture
def factory_session_data():
    """Factory for creating test session data."""

    def _create_session(name: str = None, **kwargs):
        defaults = {
            "id": fake.uuid4(),
            "name": name or fake.sentence(nb_words=3),
            "created_at": fake.date_time_between(start_date="-1y", end_date="now"),
            "description": fake.text(max_nb_chars=200),
            "vehicle": fake.random_element(["Golf GTI", "Civic Type R", "Focus RS"]),
            "driver": fake.name(),
            "track": fake.random_element(["Interlagos", "Jacarepaguá", "Tarumã"]),
            "weather": fake.random_element(["Ensolarado", "Nublado", "Chuva"]),
            "temperature": fake.random.uniform(15.0, 35.0),
        }
        defaults.update(kwargs)
        return defaults

    return _create_session
