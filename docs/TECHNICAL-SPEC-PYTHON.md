# FuelTune Analyzer - Technical Specification (Python/Streamlit)

## Technology Stack Overview

### Core Framework
- **Streamlit 1.28+**: Primary web application framework
- **Python 3.11+**: Programming language and runtime
- **SQLAlchemy 2.0+**: Database ORM and query builder
- **Pydantic 2.0+**: Data validation and serialization
- **Alembic**: Database migration management

### Data Processing & Analysis
- **Pandas 2.0+**: Data manipulation and time series analysis
- **NumPy 1.24+**: Numerical computing and array operations
- **SciPy 1.11+**: Statistical analysis and signal processing
- **Scikit-learn 1.3+**: Machine learning algorithms
- **Polars**: High-performance alternative to pandas (optional)

### Visualization & UI
- **Plotly 5.15+**: Interactive charts and 3D visualization
- **Streamlit-Plotly-Events**: Chart interaction handling
- **Streamlit-Aggrid**: Advanced data grid components
- **Streamlit-Extras**: Additional UI components
- **Matplotlib 3.7+**: Static chart generation for reports

### Database Support
- **SQLite**: Development and single-user deployments
- **PostgreSQL 15+**: Multi-user production deployments
- **Psycopg2**: PostgreSQL adapter for Python
- **SQLite3**: Built-in SQLite interface

### Development & Testing
- **Pytest 7.4+**: Testing framework
- **Coverage.py**: Code coverage analysis
- **Black**: Code formatting
- **Flake8**: Code linting
- **Mypy**: Static type checking
- **Pre-commit**: Git hooks for code quality

### Deployment & Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration
- **Nginx**: Reverse proxy and static file serving
- **Redis**: Caching and session management
- **Gunicorn**: WSGI server for production

## Application Architecture

### 1. Streamlit Application Structure

```
app/
├── main.py                 # Main Streamlit application entry point
├── config/
│   ├── __init__.py
│   ├── settings.py         # Configuration management
│   └── database.py         # Database configuration
├── models/
│   ├── __init__.py
│   ├── base.py            # SQLAlchemy base model
│   ├── vehicle.py         # Vehicle and configuration models
│   ├── table.py           # Tuning table models
│   ├── log.py             # Log data models
│   └── analysis.py        # Analysis result models
├── services/
│   ├── __init__.py
│   ├── database_service.py # Database operations
│   ├── csv_service.py     # CSV import/export
│   ├── analysis_service.py # Data analysis engine
│   ├── table_service.py   # Table operations
│   └── export_service.py  # Report generation
├── components/
│   ├── __init__.py
│   ├── vehicle_manager.py # Vehicle profile management
│   ├── data_importer.py   # CSV import interface
│   ├── table_editor.py    # Interactive table editing
│   ├── chart_viewer.py    # Chart visualization
│   └── report_generator.py # Report creation
├── utils/
│   ├── __init__.py
│   ├── validation.py      # Data validation utilities
│   ├── calculations.py    # Engine calculations
│   ├── interpolation.py   # Table interpolation
│   └── helpers.py         # General utilities
└── pages/
    ├── 1_🚗_Vehicles.py    # Vehicle management page
    ├── 2_📊_Data_Import.py  # Data import page
    ├── 3_🗂️_Tables.py      # Table management page
    ├── 4_📈_Analysis.py     # Data analysis page
    └── 5_📋_Reports.py      # Report generation page
```

### 2. Database Schema Design

#### Core Models
```python
# Vehicle Model
class Vehicle(Base):
    id: int
    name: str
    make: str
    model: str
    year: int
    engine_displacement: float
    fuel_type: FuelType
    target_afr: float
    max_rpm: int
    max_boost: float
    created_at: datetime
    updated_at: datetime
    is_active: bool

# Vehicle Configuration
class VehicleConfig(Base):
    id: int
    vehicle_id: int
    cylinder_count: int
    compression_ratio: float
    stroke: float
    bore: float
    firing_order: str
    injector_size: float
    fuel_rail_pressure: float
    fuel_pump_capacity: float
    spark_plug_gap: float
    coil_dwell_time: float
    forced_induction_type: str
    target_lambda_idle: float
    target_lambda_cruise: float
    target_lambda_wot: float
    egt_limit: float
    knock_threshold: float
    lean_protection_lambda: float
```

#### Log Data Models
```python
# Log Entry (37+ fields from FuelTech)
class LogEntry(Base):
    id: int
    vehicle_id: int
    session_id: str
    timestamp: float
    rpm: int
    throttle_position: float
    ignition_timing: float
    map_pressure: float
    lambda_sensor: float
    two_step: bool
    launch_validated: bool
    gear: int
    fuel_flow_bank_a: float
    total_fuel_flow: float
    injection_angle: float
    injector_opening_a: float
    injection_time_bank_a: float
    engine_temp: float
    air_temp: float
    oil_pressure: float
    fuel_pressure: float
    fuel_diff_pressure: float
    battery_voltage: float
    ignition_dwell: float
    sync_signal: bool
    decel_cutoff: bool
    engine_start: bool
    idle: bool
    first_start_pulse: bool
    fast_decay_injection: bool
    active_adjustment: bool
    cooling_fan_2: bool
    fuel_pump: bool
    delta_tps: float
    two_step_button: bool
    fast_injection: bool
    decay_injection: bool
    injection_cutoff: bool
    post_start_injection: bool
    start_button_toggle: bool
    created_at: datetime

# Log Session Metadata
class LogSession(Base):
    session_id: str
    vehicle_id: int
    point_count: int
    start_time: float
    end_time: float
    duration: float
    min_rpm: int
    max_rpm: int
    avg_rpm: float
    min_map: float
    max_map: float
    avg_map: float
    avg_lambda: float
    created_at: datetime
```

#### Tuning Table Models
```python
# Tuning Tables
class Table(Base):
    id: int
    vehicle_id: int
    name: str
    type: TableType  # fuel, ignition, boost, custom
    description: str
    rpm_axis: list[float]  # JSON array
    map_axis: list[float]  # JSON array
    data: list[list[float]]  # 2D JSON array
    min_value: float
    max_value: float
    created_at: datetime
    updated_at: datetime
    version: int
    is_active: bool

# Table Snapshots for Version Control
class Snapshot(Base):
    id: int
    table_id: int
    vehicle_id: int
    snapshot_name: str
    description: str
    data_backup: str  # JSON stringified table data
    metadata: str  # JSON stringified metadata
    created_at: datetime
    created_by: str
    is_auto_snapshot: bool
```

### 3. Service Layer Architecture

#### Database Service
```python
class DatabaseService:
    """Core database operations and connection management"""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """Get database session with proper cleanup"""

    def init_db(self) -> None:
        """Initialize database schema"""

    def health_check(self) -> bool:
        """Check database connectivity"""
```

#### CSV Processing Service
```python
class CSVService:
    """Handle CSV import/export operations"""

    def import_fueltech_csv(self, file_path: str, vehicle_id: int) -> ImportResult:
        """Import FuelTech CSV with field mapping and validation"""

    def validate_csv_structure(self, df: pd.DataFrame) -> ValidationResult:
        """Validate CSV has required fields and data types"""

    def map_csv_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map CSV columns to database fields"""

    def batch_insert_log_data(self, session: Session, data: list[LogEntry]) -> None:
        """Efficiently insert large datasets"""
```

#### Analysis Service
```python
class AnalysisService:
    """Core data analysis and calculations"""

    def calculate_session_statistics(self, session_id: str) -> SessionStats:
        """Calculate basic statistics for log session"""

    def detect_knock_events(self, log_data: pd.DataFrame) -> list[KnockEvent]:
        """Analyze data for knock detection"""

    def analyze_air_fuel_ratio(self, log_data: pd.DataFrame) -> AFRAnalysis:
        """Analyze lambda sensor data and AFR trends"""

    def generate_tune_suggestions(self, analysis_data: dict) -> list[Suggestion]:
        """AI-powered tuning recommendations"""

    def calculate_power_torque(self, log_data: pd.DataFrame) -> PowerCurve:
        """Calculate estimated power and torque curves"""
```

#### Table Service
```python
class TableService:
    """Tuning table operations and editing"""

    def create_table(self, vehicle_id: int, table_config: TableConfig) -> Table:
        """Create new tuning table with default values"""

    def interpolate_table(self, table: Table, method: str = 'linear') -> Table:
        """Apply interpolation algorithm to table data"""

    def smooth_table_region(self, table: Table, region: Region, factor: float) -> Table:
        """Smooth specific table region"""

    def create_snapshot(self, table_id: int, name: str) -> Snapshot:
        """Create table snapshot for version control"""

    def compare_snapshots(self, snap1_id: int, snap2_id: int) -> ComparisonResult:
        """Compare two table snapshots"""
```

### 4. Streamlit Component Design

#### Vehicle Manager Component
```python
def vehicle_manager_component():
    """Vehicle profile management interface"""

    # Vehicle selection/creation
    st.selectbox("Select Vehicle", options=get_vehicles())

    # Vehicle configuration form
    with st.form("vehicle_config"):
        name = st.text_input("Vehicle Name")
        make = st.text_input("Make")
        model = st.text_input("Model")
        year = st.number_input("Year", min_value=1900)
        # ... additional fields

        submitted = st.form_submit_button("Save Vehicle")
        if submitted:
            save_vehicle_config(...)
```

#### Data Import Component
```python
def data_import_component():
    """CSV data import interface"""

    # File upload
    uploaded_file = st.file_uploader(
        "Upload FuelTech CSV",
        type=['csv'],
        help="Select your FuelTech log file"
    )

    if uploaded_file:
        # Preview data
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())

        # Validation results
        validation = validate_csv_structure(df)
        if validation.errors:
            st.error("CSV validation failed")
            for error in validation.errors:
                st.error(error)
        else:
            # Import controls
            vehicle_id = st.selectbox("Target Vehicle", get_vehicles())
            if st.button("Import Data"):
                import_result = csv_service.import_fueltech_csv(
                    uploaded_file, vehicle_id
                )
                st.success(f"Imported {import_result.rows} data points")
```

#### Interactive Table Editor
```python
def table_editor_component(table_id: int):
    """Interactive tuning table editor"""

    table = get_table_by_id(table_id)

    # Table visualization
    fig = create_3d_surface_plot(table)
    selected_point = plotly_events(
        fig,
        click_event=True,
        key="table_click"
    )

    # Edit controls
    if selected_point:
        row, col = get_cell_from_click(selected_point[0])
        current_value = table.data[row][col]

        new_value = st.number_input(
            f"Edit Cell [{row},{col}]",
            value=current_value,
            step=0.1
        )

        if st.button("Update Cell"):
            update_table_cell(table_id, row, col, new_value)
            st.experimental_rerun()

    # Table operations
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Interpolate"):
            interpolate_table(table_id)
    with col2:
        if st.button("Smooth"):
            smooth_table(table_id)
    with col3:
        if st.button("Create Snapshot"):
            create_table_snapshot(table_id)
```

### 5. Data Processing Pipeline

#### CSV Import Pipeline
```python
class CSVImportPipeline:
    """Multi-stage CSV processing pipeline"""

    def execute(self, file_path: str, vehicle_id: int) -> ImportResult:
        """Execute complete import pipeline"""

        # Stage 1: Read and validate
        df = self.read_csv_file(file_path)
        validation = self.validate_structure(df)

        if not validation.is_valid:
            return ImportResult(success=False, errors=validation.errors)

        # Stage 2: Data cleaning
        df_clean = self.clean_data(df)

        # Stage 3: Field mapping
        df_mapped = self.map_fields(df_clean)

        # Stage 4: Type conversion
        df_typed = self.convert_types(df_mapped)

        # Stage 5: Session creation
        session_id = self.create_session(df_typed, vehicle_id)

        # Stage 6: Batch insert
        self.batch_insert_data(df_typed, session_id, vehicle_id)

        # Stage 7: Calculate statistics
        self.calculate_session_stats(session_id)

        return ImportResult(
            success=True,
            session_id=session_id,
            rows_imported=len(df_typed)
        )
```

#### Real-time Analysis Pipeline
```python
class AnalysisPipeline:
    """Real-time data analysis pipeline"""

    def analyze_session(self, session_id: str) -> AnalysisResult:
        """Comprehensive session analysis"""

        # Load session data
        log_data = self.load_session_data(session_id)

        # Parallel analysis tasks
        with ThreadPoolExecutor() as executor:
            # Basic statistics
            stats_future = executor.submit(
                self.calculate_statistics, log_data
            )

            # Knock detection
            knock_future = executor.submit(
                self.detect_knock_events, log_data
            )

            # AFR analysis
            afr_future = executor.submit(
                self.analyze_afr, log_data
            )

            # Performance metrics
            perf_future = executor.submit(
                self.calculate_performance, log_data
            )

        # Collect results
        return AnalysisResult(
            statistics=stats_future.result(),
            knock_events=knock_future.result(),
            afr_analysis=afr_future.result(),
            performance=perf_future.result()
        )
```

### 6. Caching Strategy

#### Streamlit Caching
```python
# Database query caching
@st.cache_data(ttl=300)  # 5-minute cache
def get_vehicles() -> list[Vehicle]:
    """Cached vehicle list retrieval"""
    return database_service.get_all_vehicles()

@st.cache_data(ttl=60)   # 1-minute cache
def get_session_data(session_id: str) -> pd.DataFrame:
    """Cached session data with short TTL"""
    return database_service.get_session_data(session_id)

# Expensive calculation caching
@st.cache_data(ttl=3600) # 1-hour cache
def calculate_power_curve(session_id: str) -> dict:
    """Cache expensive power curve calculations"""
    return analysis_service.calculate_power_curve(session_id)
```

#### Redis Caching (Production)
```python
class CacheService:
    """Redis-based caching for production"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    def get_session_analysis(self, session_id: str) -> Optional[dict]:
        """Get cached analysis results"""
        cached = self.redis.get(f"analysis:{session_id}")
        return json.loads(cached) if cached else None

    def cache_session_analysis(self, session_id: str, analysis: dict, ttl: int = 3600):
        """Cache analysis results with TTL"""
        self.redis.setex(
            f"analysis:{session_id}",
            ttl,
            json.dumps(analysis, cls=CustomEncoder)
        )
```

### 7. Performance Optimization

#### Database Optimization
- **Connection Pooling**: SQLAlchemy connection pool configuration
- **Query Optimization**: Indexed columns and efficient queries
- **Batch Operations**: Bulk insert/update operations
- **Lazy Loading**: On-demand data loading for large datasets

#### Data Processing Optimization
- **Pandas Optimization**: Efficient data types and vectorized operations
- **Chunked Processing**: Process large CSV files in chunks
- **Parallel Processing**: Multi-threading for independent calculations
- **Memory Management**: Explicit cleanup of large DataFrames

#### Frontend Optimization
- **Streamlit Session State**: Efficient state management
- **Component Reuse**: Cached component rendering
- **Lazy Loading**: Progressive data loading for charts
- **Pagination**: Limit displayed data volume

### 8. Error Handling & Logging

#### Structured Logging
```python
import logging
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
```

#### Exception Handling
```python
class FuelTuneException(Exception):
    """Base exception class"""
    pass

class ValidationException(FuelTuneException):
    """Data validation errors"""
    pass

class ImportException(FuelTuneException):
    """CSV import errors"""
    pass

class DatabaseException(FuelTuneException):
    """Database operation errors"""
    pass

# Global exception handler
def handle_exception(func):
    """Decorator for consistent exception handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationException as e:
            logger.error("Validation error", error=str(e))
            st.error(f"Data validation failed: {e}")
        except ImportException as e:
            logger.error("Import error", error=str(e))
            st.error(f"Import failed: {e}")
        except DatabaseException as e:
            logger.error("Database error", error=str(e))
            st.error("Database operation failed. Please try again.")
        except Exception as e:
            logger.error("Unexpected error", error=str(e))
            st.error("An unexpected error occurred. Please contact support.")
    return wrapper
```

### 9. Security Considerations

#### Input Validation
```python
from pydantic import BaseModel, validator

class LogEntryInput(BaseModel):
    timestamp: float
    rpm: int
    throttle_position: Optional[float]
    # ... other fields

    @validator('rpm')
    def validate_rpm(cls, v):
        if not 0 <= v <= 20000:
            raise ValueError('RPM must be between 0 and 20000')
        return v

    @validator('throttle_position')
    def validate_throttle(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError('Throttle position must be between 0 and 100')
        return v
```

#### Database Security
- **Parameterized Queries**: SQLAlchemy ORM prevents SQL injection
- **Connection Encryption**: SSL/TLS for database connections
- **User Authentication**: Session-based authentication (if multi-user)
- **Data Sanitization**: Input cleaning and validation

### 10. Testing Strategy

#### Unit Testing
```python
import pytest
from unittest.mock import Mock, patch

class TestCSVService:
    """Unit tests for CSV service"""

    def test_import_valid_csv(self):
        """Test successful CSV import"""
        service = CSVService()
        result = service.import_fueltech_csv("test.csv", 1)
        assert result.success
        assert result.rows_imported > 0

    def test_import_invalid_csv(self):
        """Test CSV validation failure"""
        service = CSVService()
        with pytest.raises(ValidationException):
            service.import_fueltech_csv("invalid.csv", 1)
```

#### Integration Testing
```python
class TestDatabaseIntegration:
    """Integration tests for database operations"""

    @pytest.fixture
    def test_db(self):
        """Create test database"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine

    def test_vehicle_crud_operations(self, test_db):
        """Test vehicle CRUD operations"""
        # Test create, read, update, delete operations
```

#### End-to-End Testing
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

class TestE2EWorkflow:
    """End-to-end workflow testing"""

    def test_complete_import_workflow(self):
        """Test complete CSV import workflow"""
        driver = webdriver.Chrome()

        # Navigate to application
        driver.get("http://localhost:8503")

        # Upload CSV file
        upload = driver.find_element(By.XPATH, "//input[@type='file']")
        upload.send_keys("/path/to/test.csv")

        # Verify import success
        success_msg = driver.find_element(By.CLASS_NAME, "success")
        assert "Imported" in success_msg.text
```

---

*This technical specification provides comprehensive guidance for implementing the FuelTune Analyzer using Python and Streamlit. All development should follow these architectural patterns and technical standards.*
