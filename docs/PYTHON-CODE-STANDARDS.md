# FuelTune Streamlit - Python Code Standards

## Overview

This document establishes comprehensive coding standards, best practices, and quality guidelines for the FuelTune Analyzer Python/Streamlit implementation. All code must conform to these standards to ensure maintainability, performance, and reliability.

**IMPORTANTE:** Este documento é a REFERÊNCIA OBRIGATÓRIA para todo desenvolvimento. Todos os agentes de implementação devem seguir rigorosamente estes padrões para evitar retrabalho.

## Core Principles

### 1. Code Quality Pillars
- **Readability**: Code should be self-documenting and easily understood
- **Reliability**: Robust error handling and comprehensive testing
- **Performance**: Efficient algorithms and optimal resource usage
- **Maintainability**: Modular design with clear separation of concerns
- **Security**: Input validation and secure data handling
- **Professional UI**: NO EMOJIS - Use Material Design Icons only

### 2. Quality Metrics
- **Code Coverage**: Minimum 90% test coverage
- **Complexity**: Maximum cyclomatic complexity of 10 per function
- **Documentation**: All public APIs must have docstrings
- **Type Safety**: Full type hint coverage for all functions
- **Performance**: Sub-second response for typical operations

## Python Standards

### 1. PEP 8 Compliance

#### Code Formatting
```python
# Line length: 88 characters (Black formatter standard)
# Use 4 spaces for indentation, never tabs

# Good example
def calculate_power_curve(
    rpm_data: list[float], 
    torque_data: list[float],
    atmospheric_correction: float = 1.0
) -> PowerCurve:
    """Calculate power curve from RPM and torque data."""
    pass

# Bad example
def calc_pwr(r,t,c=1.0):
    pass
```

#### Naming Conventions
```python
# Module names: lowercase with underscores
import data_processor
import vehicle_manager

# Class names: PascalCase
class VehicleService:
    pass

class LogAnalysisEngine:
    pass

# Function/variable names: snake_case
def process_csv_data():
    pass

user_id = 12345
session_data = {}

# Constants: UPPER_SNAKE_CASE
MAX_RPM_LIMIT = 20000
DEFAULT_LAMBDA_TARGET = 0.85
CSV_CHUNK_SIZE = 10000

# Private attributes: leading underscore
class DatabaseService:
    def __init__(self):
        self._connection = None
        self._session_factory = None
```

### 2. Type Hints

#### Comprehensive Type Annotations
```python
from typing import Optional, Union, List, Dict, Tuple, Any
from typing_extensions import TypedDict
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

# Function signatures with full type hints
def import_csv_data(
    file_path: Path,
    vehicle_id: int,
    validation_rules: Optional[Dict[str, Any]] = None
) -> Tuple[str, int, List[str]]:
    """
    Import CSV data with comprehensive type safety.
    
    Args:
        file_path: Path to CSV file
        vehicle_id: Target vehicle identifier
        validation_rules: Optional validation configuration
        
    Returns:
        Tuple of (session_id, imported_rows, warnings)
    """
    pass

# Class with type hints
class LogEntry(BaseModel):
    """Type-safe log entry model."""
    
    timestamp: float
    rpm: int
    throttle_position: Optional[float] = None
    lambda_sensor: Optional[float] = None
    flags: Dict[str, bool] = {}
    created_at: datetime = datetime.now()

# Generic types for reusable components
from typing import TypeVar, Generic

T = TypeVar('T')

class Repository(Generic[T]):
    """Generic repository pattern with type safety."""
    
    def get_by_id(self, id_value: int) -> Optional[T]:
        pass
    
    def create(self, entity: T) -> T:
        pass
```

#### Type Aliases for Complex Types
```python
# Define type aliases for complex structures
LogData = Dict[str, Union[float, int, bool]]
SessionMetadata = Dict[str, Union[str, int, float, datetime]]
ValidationResult = Tuple[bool, List[str], List[str]]  # success, errors, warnings
ChartData = List[Tuple[float, float]]  # [(x, y), ...]

# Use in function signatures
def analyze_session_data(
    log_data: List[LogData],
    metadata: SessionMetadata
) -> ValidationResult:
    pass
```

### 3. Documentation Standards

#### Docstring Format (Google Style)
```python
def calculate_air_fuel_ratio(
    lambda_value: float,
    fuel_type: str = "gasoline"
) -> float:
    """Calculate air-fuel ratio from lambda sensor reading.
    
    This function converts lambda sensor values to actual air-fuel ratios
    based on the stoichiometric ratio for the specified fuel type.
    
    Args:
        lambda_value: Lambda sensor reading (0.5-2.0 typical range)
        fuel_type: Type of fuel ("gasoline", "ethanol", "e85", etc.)
        
    Returns:
        Calculated air-fuel ratio as a float
        
    Raises:
        ValueError: If lambda_value is outside valid range (0.5-2.0)
        KeyError: If fuel_type is not in supported fuel database
        
    Example:
        >>> calculate_air_fuel_ratio(0.85, "gasoline")
        12.495
        >>> calculate_air_fuel_ratio(0.78, "ethanol")  
        7.02
        
    Note:
        For forced induction engines, lambda values below 0.8 are common
        under boost conditions and should not be considered errors.
    """
    if not 0.5 <= lambda_value <= 2.0:
        raise ValueError(f"Lambda value {lambda_value} outside valid range")
    
    stoich_ratios = {
        "gasoline": 14.7,
        "ethanol": 9.0,
        "e85": 9.8
    }
    
    if fuel_type not in stoich_ratios:
        raise KeyError(f"Unsupported fuel type: {fuel_type}")
    
    return stoich_ratios[fuel_type] * lambda_value
```

#### Module-Level Documentation
```python
"""
FuelTune Analyzer Data Processing Module

This module provides core data processing functionality for FuelTech ECU
log data, including CSV import, validation, and transformation pipelines.

Classes:
    CSVProcessor: Main CSV processing and validation
    DataValidator: Data quality and range validation
    SessionManager: Log session lifecycle management

Functions:
    import_fueltech_csv: High-level CSV import interface
    validate_log_data: Comprehensive data validation
    calculate_session_stats: Statistical analysis of log sessions

Typical Usage:
    processor = CSVProcessor()
    result = processor.import_file("data.csv", vehicle_id=1)
    
    if result.success:
        stats = calculate_session_stats(result.session_id)
        print(f"Imported {result.row_count} data points")

Author: FuelTune Development Team
Version: 1.0.0
"""
```

### 4. Error Handling

#### Custom Exception Hierarchy
```python
class FuelTuneException(Exception):
    """Base exception for FuelTune application."""
    pass

class ValidationException(FuelTuneException):
    """Data validation errors."""
    
    def __init__(self, message: str, field_name: str = None, value: Any = None):
        super().__init__(message)
        self.field_name = field_name
        self.value = value

class ImportException(FuelTuneException):
    """CSV import and processing errors."""
    
    def __init__(self, message: str, file_path: str = None, line_number: int = None):
        super().__init__(message)
        self.file_path = file_path
        self.line_number = line_number

class DatabaseException(FuelTuneException):
    """Database operation errors."""
    pass
```

#### Proper Exception Handling
```python
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

def import_csv_file(file_path: Path, vehicle_id: int) -> ImportResult:
    """Import CSV with comprehensive error handling."""
    
    try:
        # Validate file exists and is readable
        if not file_path.exists():
            raise ImportException(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ImportException(f"Path is not a file: {file_path}")
        
        # Process with detailed error context
        with open(file_path, 'r', encoding='utf-8') as file:
            processor = CSVProcessor()
            return processor.process(file, vehicle_id)
            
    except ImportException:
        # Re-raise application exceptions
        raise
        
    except UnicodeDecodeError as e:
        logger.error("Encoding error in file %s: %s", file_path, str(e))
        raise ImportException(
            f"File encoding error. Please ensure UTF-8 encoding.",
            str(file_path)
        ) from e
        
    except pd.errors.EmptyDataError:
        logger.error("Empty CSV file: %s", file_path)
        raise ImportException("CSV file is empty", str(file_path))
        
    except Exception as e:
        logger.error("Unexpected error importing %s: %s", file_path, str(e))
        raise ImportException(
            "Unexpected error during import. Please check logs.",
            str(file_path)
        ) from e

# Context manager for database operations
@contextmanager
def database_transaction(session: Session):
    """Context manager for database transactions."""
    try:
        yield session
        session.commit()
        logger.debug("Database transaction committed successfully")
    except Exception as e:
        session.rollback()
        logger.error("Database transaction failed: %s", str(e))
        raise DatabaseException("Database operation failed") from e
```

## Streamlit Best Practices

### 0. Professional UI Standards (CRÍTICO)

#### Interface Profissional SEM Emojis
```python
# ❌ NUNCA FAZER - Emojis não profissionais
st.title("🚗 Vehicle Management")
st.button("✅ Save")
st.metric("💰 Sales", "$10,000")

# ✅ CORRETO - Interface profissional
st.title("Vehicle Management")
st.button("Save")
st.metric("Sales", "$10,000")

# ✅ CORRETO - Com Material Icons quando necessário
import streamlit as st

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">
<style>
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>
""", unsafe_allow_html=True)

# Usar Material Icons para ícones
st.markdown('<span class="material-symbols-outlined">home</span> Dashboard', unsafe_allow_html=True)
```

#### CSS Adaptativo para Temas Claro/Escuro
```css
/* ❌ NUNCA - Cores fixas que quebram temas */
background-color: #ffffff;
color: #000000;

/* ❌ NUNCA - Fallbacks com cores fixas */
--bg-primary: var(--background-color, #ffffff);

/* ✅ CORRETO - Variáveis CSS adaptativas */
:root {
    --bg-primary: var(--background-color);
    --text-primary: var(--text-color);
    --bg-secondary: var(--secondary-background-color);
    --text-secondary: var(--text-secondary-color);
}

/* ✅ CORRETO - Cores semânticas que funcionam em ambos temas */
.success { color: var(--success-color, #28a745); }
.error { color: var(--error-color, #dc3545); }
.warning { color: var(--warning-color, #ffc107); }
```

#### Componentes Streamlit Profissionais
```python
# ❌ DEPRECATED - Gera warnings
st.dataframe(df, use_container_width=True)
st.plotly_chart(fig, use_container_width=True)

# ✅ CORRETO - Sintaxe atual
st.dataframe(df, use_container_width=True)  # Ainda válido no Streamlit 1.29+
# OU se aparecer deprecation warning:
st.dataframe(df, width=None)  # Full width
st.plotly_chart(fig, use_container_width=True)  # Ainda válido
```

#### Checklist de Interface Profissional
- [ ] ZERO emojis no código (substituir por Material Icons)
- [ ] ZERO cores hexadecimais hardcoded (#ffffff, #000000)
- [ ] ZERO uso de !important no CSS
- [ ] Usar APENAS variáveis CSS do Streamlit
- [ ] Testar em tema claro E escuro
- [ ] Interface minimalista e corporativa

### 1. Component Organization

#### Page Structure
```python
# pages/1_Vehicles.py  # SEM EMOJI no nome do arquivo
import streamlit as st
from typing import Optional
from app.services.vehicle_service import VehicleService
from app.components.vehicle_form import VehicleFormComponent

# Page configuration
st.set_page_config(
    page_title="Vehicle Management",
    page_icon=None,  # Ou usar um ícone SVG/PNG profissional
    layout="wide",
    initial_sidebar_state="expanded"
)

def main() -> None:
    """Main vehicle management page."""
    
    st.title("Vehicle Management")  # SEM EMOJI
    st.markdown("---")
    
    # Initialize services
    vehicle_service = get_vehicle_service()
    
    # Sidebar controls
    with st.sidebar:
        selected_vehicle = vehicle_selector(vehicle_service)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if selected_vehicle:
            display_vehicle_details(selected_vehicle)
        else:
            display_vehicle_creation_form()
    
    with col2:
        display_vehicle_statistics(selected_vehicle)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_vehicle_list() -> list[Vehicle]:
    """Get cached vehicle list."""
    return VehicleService().get_all_vehicles()

if __name__ == "__main__":
    main()
```

#### Reusable Components
```python
# app/components/vehicle_form.py
import streamlit as st
from typing import Optional, Callable
from app.models.vehicle import Vehicle, VehicleCreate

class VehicleFormComponent:
    """Reusable vehicle form component."""
    
    def __init__(self, on_submit: Callable[[VehicleCreate], None]):
        self.on_submit = on_submit
    
    def render(self, vehicle: Optional[Vehicle] = None) -> None:
        """Render the vehicle form."""
        
        with st.form("vehicle_form", clear_on_submit=True):
            # Form fields with validation
            name = st.text_input(
                "Vehicle Name",
                value=vehicle.name if vehicle else "",
                max_chars=100,
                help="Enter a descriptive name for your vehicle"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                make = st.text_input("Make", value=vehicle.make if vehicle else "")
                year = st.number_input(
                    "Year", 
                    min_value=1900, 
                    max_value=2030,
                    value=vehicle.year if vehicle else 2020
                )
            
            with col2:
                model = st.text_input("Model", value=vehicle.model if vehicle else "")
                displacement = st.number_input(
                    "Displacement (L)",
                    min_value=0.1,
                    max_value=20.0,
                    step=0.1,
                    format="%.1f",
                    value=vehicle.engine_displacement if vehicle else 2.0
                )
            
            # Fuel type selection
            fuel_type = st.selectbox(
                "Fuel Type",
                options=["gasoline", "ethanol", "e85", "methanol", "race_fuel"],
                index=["gasoline", "ethanol", "e85", "methanol", "race_fuel"].index(
                    vehicle.fuel_type if vehicle else "gasoline"
                )
            )
            
            # Submit button
            submitted = st.form_submit_button("Save Vehicle", type="primary")
            
            if submitted and self._validate_form(name, make, model, year):
                vehicle_data = VehicleCreate(
                    name=name,
                    make=make,
                    model=model,
                    year=year,
                    engine_displacement=displacement,
                    fuel_type=fuel_type
                )
                self.on_submit(vehicle_data)
    
    def _validate_form(self, name: str, make: str, model: str, year: int) -> bool:
        """Validate form inputs."""
        errors = []
        
        if not name.strip():
            errors.append("Vehicle name is required")
        if not make.strip():
            errors.append("Make is required")
        if not model.strip():
            errors.append("Model is required")
        if not 1900 <= year <= 2030:
            errors.append("Year must be between 1900 and 2030")
        
        if errors:
            for error in errors:
                st.error(error)
            return False
        
        return True
```

### 2. State Management

#### Session State Best Practices
```python
# app/utils/session_state.py
import streamlit as st
from typing import Any, Optional, TypeVar, Generic, Dict
from dataclasses import dataclass, field

T = TypeVar('T')

class SessionStateManager:
    """Centralized session state management."""
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get value from session state with default."""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set value in session state."""
        st.session_state[key] = value
    
    @staticmethod
    def has(key: str) -> bool:
        """Check if key exists in session state."""
        return key in st.session_state
    
    @staticmethod
    def delete(key: str) -> None:
        """Delete key from session state."""
        if key in st.session_state:
            del st.session_state[key]
    
    @staticmethod
    def clear() -> None:
        """Clear all session state."""
        st.session_state.clear()

@dataclass
class AppState:
    """Application state container."""
    
    selected_vehicle_id: Optional[int] = None
    current_session_id: Optional[str] = None
    import_progress: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def load_from_session(cls) -> 'AppState':
        """Load application state from session."""
        return cls(
            selected_vehicle_id=SessionStateManager.get('selected_vehicle_id'),
            current_session_id=SessionStateManager.get('current_session_id'),
            import_progress=SessionStateManager.get('import_progress', {}),
            user_preferences=SessionStateManager.get('user_preferences', {})
        )
    
    def save_to_session(self) -> None:
        """Save application state to session."""
        SessionStateManager.set('selected_vehicle_id', self.selected_vehicle_id)
        SessionStateManager.set('current_session_id', self.current_session_id)
        SessionStateManager.set('import_progress', self.import_progress)
        SessionStateManager.set('user_preferences', self.user_preferences)
```

### 3. Caching Strategy

#### Data Caching
```python
import streamlit as st
import pandas as pd
from functools import wraps
from typing import Any, Callable

# Database query caching
@st.cache_data(ttl=300, show_spinner=False)  # 5-minute cache
def get_vehicles_cached() -> list[Vehicle]:
    """Cached vehicle retrieval."""
    return VehicleService().get_all_vehicles()

@st.cache_data(ttl=60)  # 1-minute cache for frequently changing data
def get_session_statistics(session_id: str) -> Dict[str, float]:
    """Cached session statistics."""
    return AnalysisService().calculate_session_stats(session_id)

# Resource caching for expensive operations
@st.cache_resource
def get_database_engine():
    """Cached database engine (singleton)."""
    return create_engine(DATABASE_URL)

@st.cache_resource
def get_analysis_service():
    """Cached analysis service instance."""
    return AnalysisService(get_database_engine())

# Custom cache decorator for complex scenarios
def cache_with_key(key_func: Callable[..., str], ttl: int = 3600):
    """Custom caching decorator with dynamic keys."""
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cache_dict = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = key_func(*args, **kwargs)
            
            if cache_key in cache_dict:
                result, timestamp = cache_dict[cache_key]
                if time.time() - timestamp < ttl:
                    return result
            
            result = func(*args, **kwargs)
            cache_dict[cache_key] = (result, time.time())
            return result
        
        return wrapper
    return decorator

# Usage example
@cache_with_key(
    key_func=lambda session_id, analysis_type: f"{session_id}_{analysis_type}",
    ttl=1800  # 30 minutes
)
def get_analysis_results(session_id: str, analysis_type: str) -> AnalysisResult:
    """Cached analysis results with custom key generation."""
    return AnalysisService().analyze_session(session_id, analysis_type)
```

## Data Processing Standards

### 1. Pandas Best Practices

#### Efficient DataFrames
```python
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class DataProcessor:
    """Optimized pandas data processing."""
    
    @staticmethod
    def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage with appropriate dtypes."""
        
        # Define optimal dtypes for FuelTech data
        dtype_map = {
            'rpm': 'int16',              # RPM fits in 16-bit integer
            'throttle_position': 'float32',  # Float32 sufficient for percentages
            'lambda_sensor': 'float32',      # Float32 sufficient for lambda
            'engine_temp': 'float32',        # Temperature values
            'map_pressure': 'float32',       # Pressure values
            'two_step': 'bool',              # Boolean flags
            'launch_validated': 'bool',      # Boolean flags
            'gear': 'int8',                  # Gear fits in 8-bit integer
        }
        
        for column, dtype in dtype_map.items():
            if column in df.columns:
                try:
                    df[column] = df[column].astype(dtype)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not convert {column} to {dtype}: {e}")
        
        return df
    
    @staticmethod
    def vectorized_calculations(df: pd.DataFrame) -> pd.DataFrame:
        """Perform vectorized calculations for performance."""
        
        # Vectorized AFR calculation
        df['afr'] = df['lambda_sensor'] * 14.7  # Gasoline stoichiometric ratio
        
        # Vectorized load calculation
        df['engine_load'] = (df['throttle_position'] * df['map_pressure']) / 100.0
        
        # Vectorized power estimation (simplified formula)
        df['estimated_power'] = (
            df['rpm'] * df['engine_load'] * 0.001  # Simplified power formula
        )
        
        # Boolean operations
        df['high_load'] = (df['throttle_position'] > 80) & (df['map_pressure'] > 1.0)
        df['lean_condition'] = df['lambda_sensor'] > 1.05
        
        return df
    
    @staticmethod
    def efficient_groupby_operations(df: pd.DataFrame) -> Dict[str, float]:
        """Efficient aggregation using groupby."""
        
        # Group by RPM ranges for analysis
        df['rpm_range'] = pd.cut(
            df['rpm'], 
            bins=[0, 2000, 4000, 6000, 8000, 20000],
            labels=['idle', 'low', 'mid', 'high', 'redline']
        )
        
        # Efficient aggregation
        stats = df.groupby('rpm_range').agg({
            'lambda_sensor': ['mean', 'std'],
            'engine_temp': ['mean', 'max'],
            'throttle_position': ['mean', 'max'],
            'map_pressure': ['mean', 'max']
        }).round(3)
        
        return stats.to_dict()
```

#### Memory-Efficient Processing
```python
def process_large_csv(file_path: Path, chunk_size: int = 10000) -> Iterator[pd.DataFrame]:
    """Process large CSV files in chunks to manage memory."""
    
    # Read CSV in chunks
    chunk_iter = pd.read_csv(
        file_path,
        chunksize=chunk_size,
        dtype=OPTIMIZED_DTYPES,
        parse_dates=['timestamp'] if 'timestamp' in REQUIRED_COLUMNS else None,
        usecols=REQUIRED_COLUMNS  # Only read required columns
    )
    
    for chunk in chunk_iter:
        # Process chunk
        chunk = clean_data(chunk)
        chunk = validate_data(chunk)
        chunk = transform_data(chunk)
        
        yield chunk
        
        # Explicit memory cleanup
        del chunk
        gc.collect()

def memory_efficient_merge(
    left_df: pd.DataFrame, 
    right_df: pd.DataFrame,
    on: str,
    chunk_size: int = 10000
) -> pd.DataFrame:
    """Memory-efficient DataFrame merge for large datasets."""
    
    results = []
    
    # Process left DataFrame in chunks
    for start_idx in range(0, len(left_df), chunk_size):
        end_idx = min(start_idx + chunk_size, len(left_df))
        left_chunk = left_df.iloc[start_idx:end_idx]
        
        # Merge chunk
        merged_chunk = pd.merge(left_chunk, right_df, on=on, how='inner')
        results.append(merged_chunk)
        
        # Memory cleanup
        del left_chunk, merged_chunk
        gc.collect()
    
    return pd.concat(results, ignore_index=True)
```

### 2. NumPy Optimization

#### Vectorized Operations
```python
import numpy as np
from typing import Tuple

def calculate_power_torque_vectorized(
    rpm_array: np.ndarray,
    fuel_flow_array: np.ndarray,
    map_pressure_array: np.ndarray,
    engine_displacement: float = 2.0
) -> Tuple[np.ndarray, np.ndarray]:
    """Vectorized power and torque calculations."""
    
    # Vectorized calculations using numpy
    # Estimated torque based on fuel flow and MAP
    torque_nm = (
        fuel_flow_array * map_pressure_array * engine_displacement * 10.0
    )
    
    # Power calculation: P = (Torque × RPM) / 9549
    power_hp = (torque_nm * rpm_array) / 9549.0 / 0.746  # Convert to HP
    
    # Smooth the curves using numpy convolve
    window = np.ones(5) / 5  # Simple moving average
    torque_smooth = np.convolve(torque_nm, window, mode='same')
    power_smooth = np.convolve(power_hp, window, mode='same')
    
    return power_smooth, torque_smooth

def detect_outliers_vectorized(
    data_array: np.ndarray,
    z_threshold: float = 3.0
) -> np.ndarray:
    """Vectorized outlier detection using Z-score."""
    
    mean = np.mean(data_array)
    std = np.std(data_array)
    
    # Calculate Z-scores vectorized
    z_scores = np.abs((data_array - mean) / std)
    
    # Return boolean array of outliers
    return z_scores > z_threshold
```

## Database Standards

### 1. SQLAlchemy Best Practices

#### Model Definitions
```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Vehicle(Base, TimestampMixin):
    """Vehicle model with comprehensive validation."""
    
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    engine_displacement = Column(Float, nullable=True)
    fuel_type = Column(String(20), nullable=False, default="gasoline")
    target_afr = Column(Float, nullable=True)
    max_rpm = Column(Integer, nullable=True)
    max_boost = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    log_sessions = relationship("LogSession", back_populates="vehicle")
    tables = relationship("Table", back_populates="vehicle")
    
    @validates('year')
    def validate_year(self, key, year):
        if not 1900 <= year <= 2030:
            raise ValueError("Year must be between 1900 and 2030")
        return year
    
    @validates('fuel_type')
    def validate_fuel_type(self, key, fuel_type):
        valid_types = ['gasoline', 'ethanol', 'methanol', 'e85', 'race_fuel', 'custom']
        if fuel_type not in valid_types:
            raise ValueError(f"Fuel type must be one of: {valid_types}")
        return fuel_type
    
    def __repr__(self):
        return f"<Vehicle(id={self.id}, name='{self.name}', make='{self.make}')>"

class LogEntry(Base, TimestampMixin):
    """Log entry model with optimized indexes."""
    
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    
    # Core telemetry fields with appropriate indexes
    timestamp = Column(Float, nullable=False, index=True)
    rpm = Column(Integer, nullable=False, index=True)
    throttle_position = Column(Float, nullable=True)
    ignition_timing = Column(Float, nullable=True)
    map_pressure = Column(Float, nullable=True, index=True)  # Frequently queried
    lambda_sensor = Column(Float, nullable=True, index=True)  # Frequently analyzed
    
    # Additional fields... (all 37+ fields from data dictionary)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_vehicle_session_time', 'vehicle_id', 'session_id', 'timestamp'),
        Index('idx_rpm_map', 'rpm', 'map_pressure'),
    )
```

#### Repository Pattern
```python
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

class BaseRepository:
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: Session, model_class):
        self.session = session
        self.model_class = model_class
    
    def get_by_id(self, id_value: int) -> Optional[Any]:
        """Get entity by ID."""
        return self.session.query(self.model_class).filter(
            self.model_class.id == id_value
        ).first()
    
    def get_all(self, limit: int = 1000) -> List[Any]:
        """Get all entities with limit."""
        return self.session.query(self.model_class).limit(limit).all()
    
    def create(self, **kwargs) -> Any:
        """Create new entity."""
        entity = self.model_class(**kwargs)
        self.session.add(entity)
        self.session.flush()  # Get ID without committing
        return entity
    
    def update(self, id_value: int, **kwargs) -> Optional[Any]:
        """Update entity by ID."""
        entity = self.get_by_id(id_value)
        if entity:
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            self.session.flush()
        return entity
    
    def delete(self, id_value: int) -> bool:
        """Delete entity by ID."""
        rows_affected = self.session.query(self.model_class).filter(
            self.model_class.id == id_value
        ).delete()
        return rows_affected > 0

class LogRepository(BaseRepository):
    """Specialized repository for log entries."""
    
    def __init__(self, session: Session):
        super().__init__(session, LogEntry)
    
    def get_session_data(
        self, 
        session_id: str,
        limit: Optional[int] = None
    ) -> List[LogEntry]:
        """Get all log entries for a session."""
        query = self.session.query(LogEntry).filter(
            LogEntry.session_id == session_id
        ).order_by(LogEntry.timestamp)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_rpm_range_data(
        self,
        session_id: str,
        rpm_min: int,
        rpm_max: int
    ) -> List[LogEntry]:
        """Get log entries within RPM range."""
        return self.session.query(LogEntry).filter(
            and_(
                LogEntry.session_id == session_id,
                LogEntry.rpm >= rpm_min,
                LogEntry.rpm <= rpm_max
            )
        ).all()
    
    def calculate_session_statistics(self, session_id: str) -> Dict[str, float]:
        """Calculate session statistics using database aggregation."""
        stats = self.session.query(
            func.count(LogEntry.id).label('point_count'),
            func.min(LogEntry.timestamp).label('start_time'),
            func.max(LogEntry.timestamp).label('end_time'),
            func.avg(LogEntry.rpm).label('avg_rpm'),
            func.min(LogEntry.rpm).label('min_rpm'),
            func.max(LogEntry.rpm).label('max_rpm'),
            func.avg(LogEntry.lambda_sensor).label('avg_lambda')
        ).filter(LogEntry.session_id == session_id).first()
        
        return {
            'point_count': stats.point_count or 0,
            'start_time': stats.start_time or 0,
            'end_time': stats.end_time or 0,
            'duration': (stats.end_time or 0) - (stats.start_time or 0),
            'avg_rpm': round(stats.avg_rpm or 0, 1),
            'min_rpm': stats.min_rpm or 0,
            'max_rpm': stats.max_rpm or 0,
            'avg_lambda': round(stats.avg_lambda or 0, 3)
        }
```

## Testing Standards

### 1. Unit Testing with Pytest

#### Test Structure
```python
# tests/unit/test_csv_processor.py
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from app.services.csv_processor import CSVProcessor
from app.exceptions import ValidationException, ImportException

class TestCSVProcessor:
    """Comprehensive unit tests for CSV processor."""
    
    @pytest.fixture
    def sample_csv_data(self) -> str:
        """Sample CSV data for testing."""
        return """TIME,RPM,Posição_do_acelerador,MAP,Sonda_Geral
0.000,800,0.0,0.98,0.985
0.100,850,5.2,1.02,0.982
0.200,900,10.5,1.05,0.978"""
    
    @pytest.fixture
    def csv_processor(self) -> CSVProcessor:
        """CSV processor fixture."""
        return CSVProcessor()
    
    @pytest.fixture
    def temp_csv_file(self, sample_csv_data: str) -> Path:
        """Create temporary CSV file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    def test_import_valid_csv(self, csv_processor: CSVProcessor, temp_csv_file: Path):
        """Test successful CSV import."""
        result = csv_processor.import_file(temp_csv_file, vehicle_id=1)
        
        assert result.success is True
        assert result.session_id is not None
        assert result.rows_imported == 3
        assert len(result.warnings) == 0
        assert len(result.errors) == 0
    
    def test_import_missing_file(self, csv_processor: CSVProcessor):
        """Test import with non-existent file."""
        non_existent_file = Path("/non/existent/file.csv")
        
        with pytest.raises(ImportException) as exc_info:
            csv_processor.import_file(non_existent_file, vehicle_id=1)
        
        assert "File not found" in str(exc_info.value)
    
    def test_validate_csv_structure_valid(self, csv_processor: CSVProcessor, temp_csv_file: Path):
        """Test CSV structure validation with valid file."""
        df = pd.read_csv(temp_csv_file)
        validation = csv_processor.validate_structure(df)
        
        assert validation.is_valid is True
        assert len(validation.errors) == 0
        assert "TIME" in validation.detected_fields
        assert "RPM" in validation.detected_fields
    
    def test_validate_csv_structure_missing_required_fields(self, csv_processor: CSVProcessor):
        """Test CSV validation with missing required fields."""
        # CSV missing required TIME field
        invalid_data = "RPM,MAP\n800,0.98\n900,1.02"
        df = pd.read_csv(pd.StringIO(invalid_data))
        
        validation = csv_processor.validate_structure(df)
        
        assert validation.is_valid is False
        assert any("TIME" in error for error in validation.errors)
    
    @pytest.mark.parametrize("rpm_value,expected_valid", [
        (800, True),
        (7000, True),
        (0, True),
        (20000, True),
        (-100, False),
        (25000, False)
    ])
    def test_validate_rpm_ranges(
        self, 
        csv_processor: CSVProcessor, 
        rpm_value: int, 
        expected_valid: bool
    ):
        """Test RPM range validation with various values."""
        test_data = f"TIME,RPM\n0.0,{rpm_value}"
        df = pd.read_csv(pd.StringIO(test_data))
        
        validation = csv_processor.validate_data(df)
        
        assert validation.is_valid == expected_valid
    
    def test_field_mapping(self, csv_processor: CSVProcessor):
        """Test Portuguese to English field mapping."""
        portuguese_fields = ['Posição_do_acelerador', 'Ponto_de_ignição', 'Sonda_Geral']
        english_fields = csv_processor.map_field_names(portuguese_fields)
        
        expected = ['throttle_position', 'ignition_timing', 'lambda_sensor']
        assert english_fields == expected
    
    @patch('app.services.database_service.DatabaseService')
    def test_database_integration(self, mock_db_service: Mock, csv_processor: CSVProcessor, temp_csv_file: Path):
        """Test database integration during import."""
        mock_session = Mock()
        mock_db_service.return_value.get_session.return_value.__enter__.return_value = mock_session
        
        result = csv_processor.import_file(temp_csv_file, vehicle_id=1)
        
        # Verify database interactions
        mock_session.add.assert_called()
        mock_session.commit.assert_called_once()
        assert result.success is True
```

#### Integration Testing
```python
# tests/integration/test_data_pipeline.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

from app.models.base import Base
from app.services.csv_processor import CSVProcessor
from app.services.database_service import DatabaseService
from app.services.analysis_service import AnalysisService

class TestDataPipeline:
    """Integration tests for complete data pipeline."""
    
    @pytest.fixture(scope="class")
    def test_db(self):
        """Create test database."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal
    
    @pytest.fixture
    def db_session(self, test_db):
        """Database session fixture."""
        session = test_db()
        yield session
        session.close()
    
    def test_complete_import_and_analysis_workflow(self, db_session, sample_large_csv):
        """Test complete workflow from CSV import to analysis."""
        
        # Step 1: Import CSV data
        csv_processor = CSVProcessor(db_session)
        import_result = csv_processor.import_file(sample_large_csv, vehicle_id=1)
        
        assert import_result.success
        assert import_result.rows_imported > 100
        
        # Step 2: Verify data in database
        log_count = db_session.query(LogEntry).filter(
            LogEntry.session_id == import_result.session_id
        ).count()
        
        assert log_count == import_result.rows_imported
        
        # Step 3: Run analysis
        analysis_service = AnalysisService(db_session)
        analysis_result = analysis_service.analyze_session(import_result.session_id)
        
        assert analysis_result.success
        assert analysis_result.statistics is not None
        assert analysis_result.statistics['avg_rpm'] > 0
        
        # Step 4: Validate analysis results
        assert 'point_count' in analysis_result.statistics
        assert 'avg_lambda' in analysis_result.statistics
        assert analysis_result.statistics['point_count'] == import_result.rows_imported
```

### 2. Performance Testing

#### Load Testing
```python
# tests/performance/test_performance.py
import pytest
import time
import psutil
import os
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from app.services.csv_processor import CSVProcessor

class TestPerformance:
    """Performance benchmarking tests."""
    
    @pytest.mark.performance
    def test_large_file_import_performance(self, large_csv_file):
        """Test import performance with large files."""
        csv_processor = CSVProcessor()
        
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        result = csv_processor.import_file(large_csv_file, vehicle_id=1)
        
        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        processing_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        # Performance assertions
        rows_per_second = result.rows_imported / processing_time
        
        assert rows_per_second > 10000, f"Import too slow: {rows_per_second:.0f} rows/sec"
        assert memory_usage < 512, f"Memory usage too high: {memory_usage:.0f} MB"
        
        print(f"Performance metrics:")
        print(f"  Rows imported: {result.rows_imported:,}")
        print(f"  Processing time: {processing_time:.2f}s")
        print(f"  Rows per second: {rows_per_second:.0f}")
        print(f"  Memory usage: {memory_usage:.0f} MB")
    
    @pytest.mark.performance
    def test_concurrent_analysis_performance(self, sample_session_ids):
        """Test concurrent analysis performance."""
        analysis_service = AnalysisService()
        
        start_time = time.time()
        
        # Run analyses concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(analysis_service.analyze_session, session_id)
                for session_id in sample_session_ids
            ]
            
            results = [future.result() for future in futures]
        
        end_time = time.time()
        
        # Verify all analyses completed successfully
        assert all(result.success for result in results)
        
        # Performance assertion
        total_time = end_time - start_time
        avg_time_per_analysis = total_time / len(sample_session_ids)
        
        assert avg_time_per_analysis < 5.0, f"Analysis too slow: {avg_time_per_analysis:.2f}s avg"
```

## Quality Assurance

### 1. Code Quality Tools

#### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black, --multi-line=3]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-redis]
  
  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, ., -x, tests/]
```

#### PyProject.toml Configuration
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --tb=short --strict-markers"
markers = [
    "unit: Unit tests",
    "integration: Integration tests", 
    "performance: Performance tests",
    "slow: Tests that run slowly"
]

[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/venv/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
```

### 2. Continuous Integration

#### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: fueltune_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
      
      - name: Lint with flake8
        run: |
          flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 app tests --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
      
      - name: Type check with mypy
        run: mypy app
      
      - name: Test with pytest
        run: |
          pytest tests/ --cov=app --cov-report=xml --cov-report=term-missing
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/fueltune_test
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

## Implementação de Features Críticas

### Referências Obrigatórias para Agentes

Todos os agentes de implementação DEVEM incluir:

```markdown
## 📚 Padrões de Código Obrigatórios
Este agente segue RIGOROSAMENTE os padrões definidos em:
- **PYTHON-CODE-STANDARDS.md** (este documento)
- Seções específicas aplicáveis:
  - [Professional UI Standards] - Interface sem emojis
  - [CSS Adaptativo] - Temas claro/escuro
  - [Type Hints] - Type safety completo
  - [Error Handling] - Tratamento robusto
  - [Performance] - Otimização obrigatória
```

### Padrões para Features Faltantes (65% do Sistema)

#### 1. MAP EDITOR (src/maps/)
```python
# Estrutura OBRIGATÓRIA
src/maps/
├── __init__.py
├── editor.py          # SEM emojis, COM type hints
├── operations.py      # Algoritmos otimizados
├── algorithms.py      # Numpy/scipy vectorizado
├── visualization.py   # Plotly profissional
├── snapshots.py      # Versionamento robusto
└── ftmanager.py      # Bridge sem perdas

# Padrões específicos:
- Zero emojis em toda UI
- Material Icons para ações
- CSS adaptativo obrigatório
- Performance < 100ms para operações
- Type hints 100% coverage
- Docstrings Google Style
```

#### 2. ANALYSIS ENGINE (src/analysis/)
```python
# Estrutura OBRIGATÓRIA
src/analysis/
├── __init__.py
├── segmentation.py   # Classificador otimizado
├── binning.py       # Algoritmos adaptativos
├── suggestions.py   # Motor com confidence score
├── confidence.py    # Cálculos precisos
└── safety.py       # Validações críticas

# Padrões específicos:
- Numpy vectorization obrigatória
- Pandas optimized dtypes
- Memory-efficient processing
- Comprehensive error handling
- Performance benchmarks incluídos
```

#### 3. FTMANAGER INTEGRATION (src/integration/)
```python
# Estrutura OBRIGATÓRIA
src/integration/
├── __init__.py
├── ftmanager_bridge.py   # Interface principal
├── format_detector.py    # Detecção robusta
├── clipboard_manager.py  # Cross-platform
└── validators.py        # Validações completas

# Padrões específicos:
- Compatibilidade 100% com FTManager
- Zero perda de precisão
- Detecção automática de formato
- Feedback claro ao usuário (sem emojis)
```

### Workflow de Implementação

1. **SEMPRE** ler este documento ANTES de implementar
2. **SEMPRE** seguir estrutura de pastas definida
3. **SEMPRE** incluir type hints completos
4. **NUNCA** usar emojis na interface
5. **NUNCA** usar cores hardcoded
6. **SEMPRE** testar em tema claro E escuro
7. **SEMPRE** otimizar para performance

### Métricas de Qualidade Obrigatórias

```python
# Todo código DEVE atender:
class QualityMetrics:
    TYPE_HINTS_COVERAGE = 100  # %
    TEST_COVERAGE = 90  # % mínimo
    MAX_COMPLEXITY = 10  # Cyclomatic
    MAX_LINE_LENGTH = 88  # Black standard
    PERFORMANCE_TARGET = 1.0  # segundos máximo
    EMOJI_COUNT = 0  # ZERO emojis
    HARDCODED_COLORS = 0  # ZERO cores fixas
```

---

*Este documento é a REFERÊNCIA OBRIGATÓRIA para todo desenvolvimento no FuelTune Analyzer. O não cumprimento destes padrões resultará em REJEIÇÃO do código e RETRABALHO obrigatório.*

**ÚLTIMA ATUALIZAÇÃO:** Incluídos padrões de UI profissional (sem emojis) e CSS adaptativo baseados em A04-STREAMLIT-PROFESSIONAL.md