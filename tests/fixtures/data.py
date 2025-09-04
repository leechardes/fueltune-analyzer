"""
Data fixtures for FuelTune tests.

Provides realistic test data for different scenarios including
normal operation, edge cases, and error conditions.
"""

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
from typing import Dict, List, Any
from faker import Faker

fake = Faker("pt_BR")


@pytest.fixture
def realistic_telemetry_data():
    """
    Realistic telemetry data simulating a real FuelTech logging session.
    """
    size = 1000

    # Create realistic time series data
    start_time = datetime(2024, 1, 1, 10, 0, 0)
    timestamps = [start_time + timedelta(seconds=i) for i in range(size)]

    # RPM simulation - realistic engine behavior
    base_rpm = 1200
    rpm_variation = np.sin(np.linspace(0, 4 * np.pi, size)) * 1500 + 2000
    rpm = np.maximum(rpm_variation + base_rpm, 800).astype(int)

    # Throttle position - correlated with RPM
    throttle = np.clip((rpm - 800) / 60 + np.random.normal(0, 5, size), 0, 100)

    # Boost pressure - correlated with throttle
    boost = np.clip((throttle / 100) * 2.5 - 0.5 + np.random.normal(0, 0.2, size), -0.5, 3.0)

    # Air/Fuel Ratio - realistic AFR behavior
    afr = np.clip(14.7 - (boost * 0.8) + np.random.normal(0, 0.3, size), 10.0, 18.0)

    # Temperature data
    iat = np.clip(25 + (throttle / 10) + np.random.normal(0, 2, size), 15, 80)

    ect = np.clip(82 + (throttle / 20) + np.random.normal(0, 3, size), 70, 110)

    # Pressure data
    oil_pressure = np.clip((rpm / 100) + np.random.normal(0, 0.5, size), 1.0, 6.0)

    fuel_pressure = np.clip(3.5 + np.random.normal(0, 0.2, size), 2.8, 4.2)

    # Ignition timing
    ignition_advance = np.clip(15 + (boost * 2) + np.random.normal(0, 1, size), 5, 25)

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "rpm": rpm,
            "throttle": throttle,
            "boost": boost,
            "afr": afr,
            "iat": iat,
            "ect": ect,
            "oil_pressure": oil_pressure,
            "fuel_pressure": fuel_pressure,
            "ignition_advance": ignition_advance,
        }
    )


@pytest.fixture
def fueltech_37_field_data():
    """
    Sample data matching FuelTech 37-field format.
    """
    size = 100

    return pd.DataFrame(
        {
            "TIME": pd.date_range("2024-01-01 10:00:00", periods=size, freq="1S"),
            "RPM": np.random.randint(800, 8000, size),
            "TPS": np.random.uniform(0, 100, size),
            "Posição_do_acelerador": np.random.uniform(0, 100, size),
            "Ponto_de_ignição": np.random.uniform(5, 25, size),
            "Pressão_do_coletor": np.random.uniform(-0.5, 3.0, size),
            "Razão_ar_combustível": np.random.uniform(10.0, 18.0, size),
            "Temperatura_do_ar_admissão": np.random.uniform(15, 80, size),
            "Temperatura_do_liquido": np.random.uniform(70, 110, size),
            "Pressão_do_óleo": np.random.uniform(1.0, 6.0, size),
            "Pressão_do_combustível": np.random.uniform(2.8, 4.2, size),
            "Voltagem_da_bateria": np.random.uniform(12.0, 14.5, size),
            "Velocidade_do_veiculo": np.random.uniform(0, 200, size),
            "MAP": np.random.uniform(20, 300, size),
            "Lambda": np.random.uniform(0.7, 1.3, size),
            "Correção_de_combustível": np.random.uniform(-30, 30, size),
            "Duty_cycle_bico": np.random.uniform(0, 100, size),
            "Frequencia_dos_bicos": np.random.uniform(0, 200, size),
            "Angulo_da_borboleta": np.random.uniform(0, 90, size),
            "Posição_da_valvula_IAC": np.random.uniform(0, 100, size),
            "Target_AFR": np.random.uniform(10.0, 18.0, size),
            "Erro_AFR": np.random.uniform(-2.0, 2.0, size),
            "Correção_ignição": np.random.uniform(-10, 10, size),
            "Knock_retard": np.random.uniform(0, 15, size),
            "Avanço_total": np.random.uniform(5, 35, size),
            "Temperatura_EGT_1": np.random.uniform(300, 900, size),
            "Temperatura_EGT_2": np.random.uniform(300, 900, size),
            "Temperatura_EGT_3": np.random.uniform(300, 900, size),
            "Temperatura_EGT_4": np.random.uniform(300, 900, size),
            "Pressão_combustível_alta": np.random.uniform(30, 80, size),
            "Duty_bomba_combustível": np.random.uniform(0, 100, size),
            "Sensor_velocidade_1": np.random.uniform(0, 200, size),
            "Sensor_velocidade_2": np.random.uniform(0, 200, size),
            "Marcha_atual": np.random.randint(1, 7, size),
            "Clutch_switch": np.random.choice([0, 1], size),
            "Brake_switch": np.random.choice([0, 1], size),
            "AC_request": np.random.choice([0, 1], size),
        }
    )


@pytest.fixture
def anomaly_data():
    """
    Data with known anomalies for testing anomaly detection.
    """
    size = 500
    normal_data = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=size, freq="1S"),
            "rpm": np.random.normal(2000, 200, size),
            "throttle": np.random.normal(50, 10, size),
            "boost": np.random.normal(1.5, 0.3, size),
            "afr": np.random.normal(14.7, 0.5, size),
            "iat": np.random.normal(35, 5, size),
        }
    )

    # Inject anomalies
    anomaly_indices = [100, 200, 300, 400]

    for idx in anomaly_indices:
        # RPM spike
        normal_data.loc[idx, "rpm"] = 8000
        # AFR lean spike
        normal_data.loc[idx, "afr"] = 18.0
        # Temperature spike
        normal_data.loc[idx, "iat"] = 90

    normal_data["is_anomaly"] = False
    normal_data.loc[anomaly_indices, "is_anomaly"] = True

    return normal_data


@pytest.fixture
def corrupt_csv_data():
    """
    Various types of corrupted CSV data for error testing.
    """
    return {
        "missing_headers": "data1,data2,data3\n1,2,3\n4,5,6\n",
        "inconsistent_columns": "col1,col2,col3\n1,2,3\n4,5\n6,7,8,9\n",
        "invalid_numbers": "rpm,throttle,boost\ninvalid,25.0,1.5\n2000,abc,2.0\n",
        "empty_file": "",
        "only_headers": "timestamp,rpm,throttle,boost,afr\n",
        "mixed_separators": "timestamp;rpm,throttle|boost\n2024-01-01,2000;50|1.5\n",
    }


@pytest.fixture
def performance_test_data():
    """
    Large dataset for performance testing.
    """
    size = 50000

    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=size, freq="100ms"),
            "rpm": np.random.randint(800, 8000, size),
            "throttle": np.random.uniform(0, 100, size),
            "boost": np.random.uniform(-0.5, 3.0, size),
            "afr": np.random.uniform(10.0, 18.0, size),
            "iat": np.random.uniform(15, 80, size),
            "ect": np.random.uniform(70, 110, size),
            "oil_pressure": np.random.uniform(1.0, 6.0, size),
            "fuel_pressure": np.random.uniform(2.8, 4.2, size),
            "ignition_advance": np.random.uniform(5, 25, size),
        }
    )


@pytest.fixture
def empty_dataframe():
    """Empty DataFrame with correct columns for testing edge cases."""
    return pd.DataFrame(
        columns=[
            "timestamp",
            "rpm",
            "throttle",
            "boost",
            "afr",
            "iat",
            "ect",
            "oil_pressure",
            "fuel_pressure",
            "ignition_advance",
        ]
    )


@pytest.fixture
def single_row_data():
    """Single row DataFrame for testing edge cases."""
    return pd.DataFrame(
        {
            "timestamp": ["2024-01-01 10:00:00"],
            "rpm": [2000],
            "throttle": [50.0],
            "boost": [1.5],
            "afr": [14.7],
            "iat": [35.0],
            "ect": [85.0],
            "oil_pressure": [3.5],
            "fuel_pressure": [3.8],
            "ignition_advance": [15.0],
        }
    )


@pytest.fixture
def extreme_values_data():
    """Data with extreme but valid values for boundary testing."""
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=10, freq="1S"),
            "rpm": [0, 800, 8000, 9000, 10000, 12000, 15000, 18000, 20000, 25000],
            "throttle": [0, 10, 50, 90, 100, 100, 100, 100, 100, 100],
            "boost": [-1.0, -0.5, 0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 10.0],
            "afr": [8.0, 10.0, 12.0, 14.7, 16.0, 18.0, 20.0, 22.0, 25.0, 30.0],
            "iat": [-10, 0, 15, 35, 60, 80, 100, 120, 150, 200],
            "ect": [0, 50, 70, 85, 100, 110, 120, 130, 140, 200],
            "oil_pressure": [0, 0.5, 1.0, 3.0, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0],
            "fuel_pressure": [0, 1.0, 2.8, 3.8, 4.2, 5.0, 6.0, 8.0, 10.0, 15.0],
            "ignition_advance": [-10, 0, 5, 15, 25, 35, 40, 45, 50, 60],
        }
    )


@pytest.fixture
def time_series_gaps_data():
    """Data with time gaps for testing time series analysis."""
    timestamps = []
    base_time = datetime(2024, 1, 1, 10, 0, 0)

    # Normal sequence
    for i in range(100):
        timestamps.append(base_time + timedelta(seconds=i))

    # Gap of 10 minutes
    base_time = base_time + timedelta(seconds=100) + timedelta(minutes=10)

    # Continue sequence
    for i in range(100):
        timestamps.append(base_time + timedelta(seconds=i))

    # Another gap of 1 hour
    base_time = base_time + timedelta(seconds=100) + timedelta(hours=1)

    # Final sequence
    for i in range(100):
        timestamps.append(base_time + timedelta(seconds=i))

    size = len(timestamps)

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "rpm": np.random.randint(1000, 3000, size),
            "throttle": np.random.uniform(20, 80, size),
            "boost": np.random.uniform(0.5, 2.0, size),
            "afr": np.random.uniform(13.0, 16.0, size),
            "iat": np.random.uniform(25, 45, size),
        }
    )


@pytest.fixture
def field_mapping_test_data():
    """Test data for field mapping validation."""
    return {
        "fueltech_37_original": [
            "TIME",
            "RPM",
            "TPS",
            "Posição_do_acelerador",
            "Ponto_de_ignição",
            "Pressão_do_coletor",
            "Razão_ar_combustível",
            "Temperatura_do_ar_admissão",
        ],
        "fueltech_37_expected": [
            "time",
            "rpm",
            "tps",
            "throttle_position",
            "ignition_timing",
            "manifold_pressure",
            "air_fuel_ratio",
            "intake_air_temperature",
        ],
        "unknown_fields": ["UNKNOWN_FIELD_1", "MYSTERY_SENSOR", "UNDEFINED_PARAMETER"],
        "mixed_case_fields": ["Time", "Rpm", "TPS", "throttle_Position", "IGNITION_TIMING"],
    }


@pytest.fixture
def database_test_data():
    """Test data for database operations."""
    return {
        "valid_session": {
            "id": "test_session_001",
            "name": "Teste de Pista 1",
            "created_at": datetime(2024, 1, 1, 10, 0, 0),
            "description": "Sessão de teste na pista de Interlagos",
            "vehicle": "Golf GTI",
            "driver": "João Silva",
            "track": "Interlagos",
            "weather": "Ensolarado",
            "temperature": 25.0,
        },
        "invalid_session": {
            "id": "",  # Invalid empty ID
            "name": "",  # Invalid empty name
            "created_at": "invalid_date",
            "temperature": "not_a_number",
        },
    }
