# FuelTune Analyzer - System Architecture

## Architecture Overview

The FuelTune Analyzer is architected as a modern Python web application built on Streamlit, designed for professional engine tuning data analysis. The system follows clean architecture principles with clear separation of concerns, emphasizing maintainability, scalability, and performance.

## High-Level System Design

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Streamlit UI]
        COMP[UI Components]
        PAGES[Page Modules]
    end

    subgraph "Application Layer"
        SRV[Services]
        CTRL[Controllers]
        VALID[Validators]
    end

    subgraph "Domain Layer"
        MODELS[Domain Models]
        BIZ[Business Logic]
        CALC[Calculations Engine]
    end

    subgraph "Infrastructure Layer"
        DB[Database Layer]
        FILES[File System]
        CACHE[Caching Layer]
    end

    subgraph "External Systems"
        CSV[CSV Files]
        EXPORT[Export Files]
        REPORTS[Generated Reports]
    end

    UI --> COMP
    COMP --> SRV
    SRV --> MODELS
    MODELS --> DB
    SRV --> FILES
    SRV --> CACHE
    FILES --> CSV
    SRV --> EXPORT
    SRV --> REPORTS
```

## Layered Architecture

### 1. Presentation Layer (Streamlit Frontend)

The presentation layer provides an intuitive web interface for users to interact with the system.

#### Components
- **Main Application**: Central Streamlit app configuration and routing
- **Page Modules**: Individual pages for different functionalities
- **UI Components**: Reusable components for consistent user experience
- **State Management**: Session state handling and user interaction tracking

```python
# Architecture pattern for presentation layer
app/
├── main.py                 # Main application entry point
├── pages/                  # Page-specific modules
│   ├── 1_🚗_Vehicles.py    # Vehicle management interface
│   ├── 2_📊_Data_Import.py  # Data import workflows
│   ├── 3_🗂️_Tables.py      # Table editing interface
│   ├── 4_📈_Analysis.py     # Analysis and visualization
│   └── 5_📋_Reports.py      # Report generation
├── components/             # Reusable UI components
│   ├── vehicle_selector.py
│   ├── data_table_viewer.py
│   ├── chart_components.py
│   └── file_uploader.py
└── utils/
    ├── session_state.py    # State management utilities
    ├── ui_helpers.py       # UI helper functions
    └── navigation.py       # Navigation utilities
```

### 2. Application Layer (Services & Controllers)

The application layer orchestrates business operations and coordinates between the presentation and domain layers.

#### Services Architecture
```python
# Service layer organization
app/services/
├── __init__.py
├── base_service.py         # Base service with common functionality
├── vehicle_service.py      # Vehicle profile management
├── csv_service.py          # CSV import/export operations
├── analysis_service.py     # Data analysis orchestration
├── table_service.py        # Tuning table operations
├── export_service.py       # Report and data export
└── notification_service.py # User notifications and alerts
```

#### Service Dependencies
```mermaid
graph LR
    VS[Vehicle Service] --> DR[Data Repository]
    CS[CSV Service] --> VP[Validation Pipeline]
    AS[Analysis Service] --> CE[Calculation Engine]
    TS[Table Service] --> IE[Interpolation Engine]
    ES[Export Service] --> TG[Template Generator]

    VP --> VR[Validation Rules]
    CE --> SA[Statistical Analysis]
    IE --> MA[Mathematical Algorithms]
    TG --> RT[Report Templates]
```

### 3. Domain Layer (Business Logic & Models)

The domain layer contains core business logic, domain models, and calculation engines.

#### Domain Model Structure
```python
# Domain models organization
app/models/
├── __init__.py
├── base.py                 # Base model classes
├── vehicle.py              # Vehicle domain models
│   ├── Vehicle
│   ├── VehicleConfig
│   └── FuelProperties
├── log.py                  # Log data models
│   ├── LogEntry
│   ├── LogSession
│   └── LogMetadata
├── table.py                # Tuning table models
│   ├── Table
│   ├── TableSnapshot
│   └── TableMetadata
├── analysis.py             # Analysis models
│   ├── AnalysisResult
│   ├── StatisticalSummary
│   └── Recommendation
└── validation.py           # Validation models
    ├── ValidationResult
    ├── ValidationRule
    └── ValidationError
```

#### Business Logic Engines
```python
# Business logic engines
app/engines/
├── __init__.py
├── calculation_engine.py   # Core mathematical calculations
├── analysis_engine.py      # Statistical analysis algorithms
├── interpolation_engine.py # Table interpolation methods
├── validation_engine.py    # Data validation logic
└── recommendation_engine.py # AI-powered suggestions
```

### 4. Infrastructure Layer (Data & External Services)

The infrastructure layer handles data persistence, external integrations, and system resources.

#### Database Architecture
```python
# Database layer structure
app/infrastructure/
├── database/
│   ├── __init__.py
│   ├── connection.py       # Database connection management
│   ├── repositories/       # Data access layer
│   │   ├── base_repository.py
│   │   ├── vehicle_repository.py
│   │   ├── log_repository.py
│   │   ├── table_repository.py
│   │   └── analysis_repository.py
│   └── migrations/         # Database schema migrations
├── cache/
│   ├── __init__.py
│   ├── redis_cache.py      # Redis caching implementation
│   └── memory_cache.py     # In-memory caching fallback
├── storage/
│   ├── __init__.py
│   ├── file_storage.py     # File system operations
│   └── temp_storage.py     # Temporary file management
└── external/
    ├── __init__.py
    └── export_adapters.py   # External format adapters
```

## Data Flow Architecture

### 1. CSV Import Pipeline

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant CS as CSV Service
    participant VP as Validation Pipeline
    participant DE as Data Engine
    participant DB as Database
    participant AS as Analysis Service

    UI->>CS: Upload CSV File
    CS->>VP: Validate File Structure
    VP-->>CS: Validation Result
    CS->>DE: Process Data Chunks
    DE->>DB: Batch Insert Data
    DB-->>DE: Confirmation
    DE-->>CS: Processing Result
    CS->>AS: Trigger Analysis
    AS-->>CS: Analysis Complete
    CS-->>UI: Import Success
```

### 2. Real-time Analysis Pipeline

```mermaid
flowchart TD
    A[Log Data Input] --> B{Data Validation}
    B -->|Valid| C[Statistical Analysis]
    B -->|Invalid| D[Error Handling]
    C --> E[Pattern Detection]
    E --> F[Outlier Detection]
    F --> G[Trend Analysis]
    G --> H[Performance Metrics]
    H --> I[Safety Analysis]
    I --> J[Generate Recommendations]
    J --> K[Cache Results]
    K --> L[Update UI]

    D --> M[Log Errors]
    M --> N[User Notification]
```

### 3. Table Editing Workflow

```mermaid
stateDiagram-v2
    [*] --> LoadTable
    LoadTable --> DisplayTable
    DisplayTable --> EditCell: User Edit
    EditCell --> ValidateChange
    ValidateChange --> ApplyChange: Valid
    ValidateChange --> ShowError: Invalid
    ShowError --> DisplayTable
    ApplyChange --> UpdateSnapshot
    UpdateSnapshot --> RefreshView
    RefreshView --> DisplayTable
    DisplayTable --> SaveTable: User Save
    SaveTable --> [*]
```

## Microservices Design Patterns

### 1. Repository Pattern

```python
from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    """Abstract base repository defining common data operations."""

    @abstractmethod
    def get_by_id(self, id_value: int) -> Optional[T]:
        """Retrieve entity by ID."""
        pass

    @abstractmethod
    def get_all(self, limit: int = 100) -> List[T]:
        """Retrieve all entities with optional limit."""
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity."""
        pass

    @abstractmethod
    def update(self, id_value: int, updates: dict) -> Optional[T]:
        """Update existing entity."""
        pass

    @abstractmethod
    def delete(self, id_value: int) -> bool:
        """Delete entity by ID."""
        pass

class LogRepository(BaseRepository[LogEntry]):
    """Specialized repository for log data operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_session_data(self, session_id: str) -> List[LogEntry]:
        """Get all log entries for a specific session."""
        return self.session.query(LogEntry).filter(
            LogEntry.session_id == session_id
        ).order_by(LogEntry.timestamp).all()

    def get_rpm_range(self, session_id: str, rpm_min: int, rpm_max: int) -> List[LogEntry]:
        """Get log entries within RPM range."""
        return self.session.query(LogEntry).filter(
            LogEntry.session_id == session_id,
            LogEntry.rpm.between(rpm_min, rpm_max)
        ).all()
```

### 2. Service Layer Pattern

```python
from typing import List, Dict, Any
from app.models.log import LogEntry, LogSession
from app.repositories.log_repository import LogRepository
from app.engines.analysis_engine import AnalysisEngine

class AnalysisService:
    """Service orchestrating data analysis operations."""

    def __init__(self, log_repository: LogRepository, analysis_engine: AnalysisEngine):
        self.log_repo = log_repository
        self.analysis_engine = analysis_engine

    def analyze_session(self, session_id: str) -> AnalysisResult:
        """Perform comprehensive session analysis."""

        # 1. Retrieve session data
        log_entries = self.log_repo.get_session_data(session_id)

        if not log_entries:
            raise ValueError(f"No data found for session {session_id}")

        # 2. Convert to analysis format
        analysis_data = self._prepare_analysis_data(log_entries)

        # 3. Execute analysis pipeline
        results = self.analysis_engine.analyze(analysis_data)

        # 4. Generate recommendations
        recommendations = self._generate_recommendations(results)

        # 5. Package results
        return AnalysisResult(
            session_id=session_id,
            statistics=results.statistics,
            outliers=results.outliers,
            trends=results.trends,
            recommendations=recommendations,
            quality_score=results.quality_score
        )

    def compare_sessions(self, session_ids: List[str]) -> ComparisonResult:
        """Compare multiple sessions for trend analysis."""

        session_analyses = []
        for session_id in session_ids:
            analysis = self.analyze_session(session_id)
            session_analyses.append(analysis)

        return self.analysis_engine.compare_analyses(session_analyses)
```

### 3. Command Pattern for Complex Operations

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from dataclasses import dataclass

class Command(ABC):
    """Abstract command interface."""

    @abstractmethod
    def execute(self) -> Any:
        """Execute the command."""
        pass

    @abstractmethod
    def undo(self) -> Any:
        """Undo the command."""
        pass

@dataclass
class TableEditCommand(Command):
    """Command for table editing operations."""

    table_id: int
    row: int
    col: int
    new_value: float
    old_value: float
    table_service: 'TableService'

    def execute(self) -> bool:
        """Apply the table edit."""
        return self.table_service.update_cell(
            self.table_id, self.row, self.col, self.new_value
        )

    def undo(self) -> bool:
        """Revert the table edit."""
        return self.table_service.update_cell(
            self.table_id, self.row, self.col, self.old_value
        )

class CommandInvoker:
    """Command invoker with undo/redo support."""

    def __init__(self):
        self.command_history: List[Command] = []
        self.current_index = -1

    def execute_command(self, command: Command) -> Any:
        """Execute command and add to history."""
        result = command.execute()

        # Remove any commands after current position
        self.command_history = self.command_history[:self.current_index + 1]

        # Add new command
        self.command_history.append(command)
        self.current_index += 1

        return result

    def undo(self) -> bool:
        """Undo last command."""
        if self.current_index >= 0:
            command = self.command_history[self.current_index]
            result = command.undo()
            self.current_index -= 1
            return result
        return False

    def redo(self) -> bool:
        """Redo next command."""
        if self.current_index < len(self.command_history) - 1:
            self.current_index += 1
            command = self.command_history[self.current_index]
            return command.execute()
        return False
```

## Caching Architecture

### 1. Multi-Layer Caching Strategy

```mermaid
graph TB
    subgraph "Caching Layers"
        L1[L1: Streamlit Cache]
        L2[L2: Application Cache]
        L3[L3: Database Cache]
        L4[L4: Redis Cache]
    end

    subgraph "Data Sources"
        DB[(Database)]
        FILES[File System]
        CALC[Calculations]
    end

    APP[Application] --> L1
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> DB
    L4 --> FILES
    L2 --> CALC
```

### 2. Cache Implementation

```python
from typing import Optional, Any, Dict, Callable
import time
import redis
import pickle
from functools import wraps

class CacheManager:
    """Multi-tier cache manager."""

    def __init__(self, redis_url: Optional[str] = None):
        self.memory_cache: Dict[str, tuple] = {}  # (value, expiry)
        self.redis_client = redis.from_url(redis_url) if redis_url else None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache hierarchy."""

        # L1: Memory cache
        if key in self.memory_cache:
            value, expiry = self.memory_cache[key]
            if time.time() < expiry:
                return value
            else:
                del self.memory_cache[key]

        # L2: Redis cache
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    value = pickle.loads(cached_data)
                    # Promote to memory cache
                    self.memory_cache[key] = (value, time.time() + 300)  # 5 min
                    return value
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache hierarchy."""

        # Set in memory cache
        self.memory_cache[key] = (value, time.time() + min(ttl, 300))  # Max 5 min

        # Set in Redis cache
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, pickle.dumps(value))
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

# Cache decorator
def cached(ttl: int = 3600, key_func: Optional[Callable] = None):
    """Caching decorator with custom key generation."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try cache first
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
```

## Performance Optimization Architecture

### 1. Database Optimization

#### Connection Pooling
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

class DatabaseManager:
    """Optimized database connection management."""

    def __init__(self, database_url: str):
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=20,              # Number of connections to maintain
            max_overflow=10,           # Additional connections allowed
            pool_pre_ping=True,        # Validate connections
            pool_recycle=3600,         # Recycle connections every hour
            echo=False                 # Set to True for SQL debugging
        )

        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self):
        """Get database session with proper cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
```

#### Query Optimization
```python
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import selectinload, joinedload

class OptimizedLogRepository:
    """Performance-optimized log data repository."""

    def get_session_data_optimized(self, session_id: str) -> List[LogEntry]:
        """Optimized query for session data with selective loading."""

        return self.session.query(LogEntry).filter(
            LogEntry.session_id == session_id
        ).options(
            # Optimize loading strategy
            selectinload(LogEntry.analysis_results)
        ).order_by(
            LogEntry.timestamp  # Use indexed column for ordering
        ).all()

    def get_aggregated_statistics(self, session_id: str) -> Dict[str, float]:
        """Use database aggregation instead of Python processing."""

        result = self.session.query(
            func.count(LogEntry.id).label('point_count'),
            func.avg(LogEntry.rpm).label('avg_rpm'),
            func.min(LogEntry.rpm).label('min_rpm'),
            func.max(LogEntry.rpm).label('max_rpm'),
            func.avg(LogEntry.lambda_sensor).label('avg_lambda'),
            func.stddev(LogEntry.lambda_sensor).label('lambda_stddev')
        ).filter(
            LogEntry.session_id == session_id
        ).first()

        return {
            'point_count': result.point_count or 0,
            'avg_rpm': round(result.avg_rpm or 0, 1),
            'min_rpm': result.min_rpm or 0,
            'max_rpm': result.max_rpm or 0,
            'avg_lambda': round(result.avg_lambda or 0, 3),
            'lambda_stddev': round(result.lambda_stddev or 0, 4)
        }
```

### 2. Memory Optimization

```python
import gc
import psutil
import os
from contextlib import contextmanager

class MemoryManager:
    """Memory usage monitoring and optimization."""

    @staticmethod
    def get_memory_usage() -> float:
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    @staticmethod
    @contextmanager
    def memory_monitor(operation_name: str, max_memory_mb: float = 1024):
        """Context manager for memory monitoring."""
        start_memory = MemoryManager.get_memory_usage()

        try:
            yield
        finally:
            end_memory = MemoryManager.get_memory_usage()
            memory_used = end_memory - start_memory

            logger.info(f"{operation_name}: {memory_used:.1f}MB used")

            if memory_used > max_memory_mb:
                logger.warning(f"{operation_name}: High memory usage ({memory_used:.1f}MB)")
                gc.collect()  # Force garbage collection

    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage."""

        # Convert object columns to category when beneficial
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique values
                df[col] = df[col].astype('category')

        # Downcast numeric columns
        for col in df.select_dtypes(include=['int']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')

        for col in df.select_dtypes(include=['float']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')

        return df
```

## Security Architecture

### 1. Input Validation

```python
from pydantic import BaseModel, validator, Field
from typing import Optional, Union
import re

class SecureLogEntry(BaseModel):
    """Secure log entry model with comprehensive validation."""

    timestamp: float = Field(..., ge=0.0, description="Timestamp must be positive")
    rpm: int = Field(..., ge=0, le=20000, description="RPM must be 0-20000")
    throttle_position: Optional[float] = Field(None, ge=0.0, le=100.0)
    lambda_sensor: Optional[float] = Field(None, ge=0.5, le=2.0)

    @validator('timestamp')
    def validate_timestamp_format(cls, v):
        """Validate timestamp is reasonable."""
        if v > 999999:  # More than 11 days of logging
            raise ValueError("Timestamp too large")
        return v

    @validator('lambda_sensor')
    def validate_lambda_sensor(cls, v):
        """Validate lambda sensor reading is physically possible."""
        if v is not None and (v < 0.5 or v > 2.0):
            raise ValueError("Lambda sensor reading outside physical limits")
        return v

class SecureVehicle(BaseModel):
    """Secure vehicle model with sanitized inputs."""

    name: str = Field(..., min_length=1, max_length=100)
    make: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    year: int = Field(..., ge=1900, le=2030)

    @validator('name', 'make', 'model')
    def sanitize_text_fields(cls, v):
        """Sanitize text fields to prevent injection."""
        # Remove potential SQL injection patterns
        sanitized = re.sub(r'[<>"\';\\]', '', v.strip())

        if not sanitized:
            raise ValueError("Field cannot be empty after sanitization")

        return sanitized
```

### 2. Database Security

```python
from sqlalchemy import text
from sqlalchemy.orm import Session

class SecureDatabaseOperations:
    """Secure database operations with parameterized queries."""

    def __init__(self, session: Session):
        self.session = session

    def get_session_data_secure(self, session_id: str, user_id: int) -> List[LogEntry]:
        """Secure session data retrieval with user authorization."""

        # Use parameterized query to prevent SQL injection
        query = text("""
            SELECT le.* FROM log_entries le
            JOIN log_sessions ls ON le.session_id = ls.session_id
            JOIN vehicles v ON ls.vehicle_id = v.id
            WHERE le.session_id = :session_id
            AND v.user_id = :user_id
            ORDER BY le.timestamp
        """)

        result = self.session.execute(
            query,
            {'session_id': session_id, 'user_id': user_id}
        )

        return [LogEntry(**row._asdict()) for row in result.fetchall()]

    def sanitize_search_term(self, search_term: str) -> str:
        """Sanitize user search input."""
        # Remove dangerous characters
        sanitized = re.sub(r'[%_\\]', '', search_term.strip())

        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        return sanitized
```

## Monitoring & Observability

### 1. Logging Architecture

```python
import logging
import structlog
from typing import Dict, Any
import time
from contextlib import contextmanager

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

class ApplicationLogger:
    """Centralized application logging."""

    def __init__(self):
        self.logger = structlog.get_logger()

    @contextmanager
    def operation_timer(self, operation: str, **context):
        """Time operations with structured logging."""
        start_time = time.time()

        self.logger.info(
            "Operation started",
            operation=operation,
            **context
        )

        try:
            yield
            duration = time.time() - start_time
            self.logger.info(
                "Operation completed",
                operation=operation,
                duration_ms=round(duration * 1000, 2),
                **context
            )
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                "Operation failed",
                operation=operation,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                **context
            )
            raise

    def log_csv_import(self, filename: str, rows: int, duration: float, errors: List[str]):
        """Log CSV import operation."""
        self.logger.info(
            "CSV import completed",
            filename=filename,
            rows_imported=rows,
            duration_seconds=duration,
            error_count=len(errors),
            errors=errors[:5] if errors else []  # Log first 5 errors
        )

    def log_analysis_result(self, session_id: str, analysis_type: str, quality_score: float):
        """Log analysis completion."""
        self.logger.info(
            "Analysis completed",
            session_id=session_id,
            analysis_type=analysis_type,
            quality_score=quality_score
        )
```

### 2. Performance Monitoring

```python
import time
from typing import Dict, List
from dataclasses import dataclass
from collections import deque

@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    operation: str
    duration: float
    timestamp: float
    memory_usage: float
    success: bool

class PerformanceMonitor:
    """Application performance monitoring."""

    def __init__(self, max_metrics: int = 1000):
        self.metrics: deque = deque(maxlen=max_metrics)
        self.operation_stats: Dict[str, List[float]] = {}

    def record_operation(self, metric: PerformanceMetric):
        """Record performance metric."""
        self.metrics.append(metric)

        if metric.operation not in self.operation_stats:
            self.operation_stats[metric.operation] = []

        self.operation_stats[metric.operation].append(metric.duration)

        # Keep only recent metrics per operation
        if len(self.operation_stats[metric.operation]) > 100:
            self.operation_stats[metric.operation] = self.operation_stats[metric.operation][-100:]

    def get_operation_stats(self, operation: str) -> Dict[str, float]:
        """Get statistical summary for operation."""
        if operation not in self.operation_stats:
            return {}

        durations = self.operation_stats[operation]

        return {
            'count': len(durations),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'p95_duration': sorted(durations)[int(0.95 * len(durations))]
        }

    def get_slow_operations(self, threshold: float = 1.0) -> List[PerformanceMetric]:
        """Get operations slower than threshold."""
        return [
            metric for metric in self.metrics
            if metric.duration > threshold
        ]
```

## Deployment Architecture

### 1. Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY main.py .

# Create non-root user
RUN useradd -m -u 1000 fueltune
USER fueltune

# Expose port
EXPOSE 8503

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8503/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "main.py", "--server.port=8503", "--server.address=0.0.0.0"]
```

### 2. Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  fueltune-app:
    build: .
    ports:
      - "8503:8503"
    environment:
      - DATABASE_URL=postgresql://fueltune:password@postgres:5432/fueltune
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: fueltune
      POSTGRES_USER: fueltune
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - fueltune-app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

*This architecture document provides comprehensive guidance for implementing, deploying, and maintaining the FuelTune Analyzer system. All development should follow these architectural patterns and principles.*
