"""
SQLAlchemy Data Models for FuelTech analyzer.

Defines database schemas for both 37-field and 64-field FuelTech data formats.
Includes base models, relationships, and indexing strategies.

Author: A02-DATA-PANDAS Agent
Created: 2025-01-02
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

from ..utils.logging_config import get_logger

logger = get_logger(__name__)

Base = declarative_base()
metadata = MetaData()


class DataSession(Base):
    """
    Data session table to group related FuelTech log entries.
    Each session represents one data logging period.
    """

    __tablename__ = "data_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256 hash for deduplication
    format_version = Column(String(10), nullable=False)  # v1.0 (37 fields) or v2.0 (64 fields)
    field_count = Column(Integer, nullable=False)
    total_records = Column(Integer, nullable=False, default=0)
    duration_seconds = Column(Float)  # Total duration of the session
    sample_rate_hz = Column(Float)  # Estimated sample rate

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    import_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    validation_status = Column(String(20), default="pending")  # pending, valid, invalid

    # File information
    file_size_mb = Column(Float)
    original_encoding = Column(String(20), default="utf-8")

    # Quality metrics
    quality_score = Column(Float)  # 0-100 quality score
    error_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)

    # Additional metadata as JSON
    metadata_json = Column(JSON)

    # Vehicle relationship
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=True, comment="ID do veículo vinculado")

    # Relationships
    vehicle = relationship("Vehicle", back_populates="sessions")
    core_data = relationship(
        "FuelTechCoreData", back_populates="session", cascade="all, delete-orphan"
    )
    extended_data = relationship(
        "FuelTechExtendedData", back_populates="session", cascade="all, delete-orphan"
    )
    quality_checks = relationship(
        "DataQualityCheck", back_populates="session", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("file_hash", name="uix_file_hash"),
        CheckConstraint("quality_score >= 0 AND quality_score <= 100", name="chk_quality_score"),
        CheckConstraint('format_version IN ("v1.0", "v2.0")', name="chk_format_version"),
        Index("idx_session_name", "session_name"),
        Index("idx_created_at", "created_at"),
        Index("idx_import_status", "import_status"),
    )


class FuelTechCoreData(Base):
    """
    Core FuelTech data table (37 fields - original format).
    Contains essential engine parameters present in all FuelTech versions.
    """

    __tablename__ = "fueltech_core_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("data_sessions.id"), nullable=False)

    # Core timing and engine data
    time = Column(Float, nullable=False)  # Time in seconds
    rpm = Column(Integer, nullable=False)  # Engine RPM
    tps = Column(Float)  # Throttle Position Sensor (%)
    throttle_position = Column(Float)  # Physical throttle position
    ignition_timing = Column(Float)  # Ignition advance (degrees)
    map = Column(Float)  # Manifold Absolute Pressure (bar)

    # Lambda and fuel system
    closed_loop_target = Column(Float)  # Lambda target
    closed_loop_o2 = Column(Float)  # O2 sensor closed loop
    closed_loop_correction = Column(Float)  # Closed loop correction (%)
    o2_general = Column(Float)  # General O2 sensor
    ethanol_content = Column(Integer)  # Ethanol percentage

    # Engine control and status
    two_step = Column(String(10))  # Two-step status (ON/OFF)
    launch_validated = Column(String(10))  # Launch validated (ON/OFF)
    gear = Column(Integer)  # Current gear

    # Fuel system
    fuel_temp = Column(Float)  # Fuel temperature (°C)
    flow_bank_a = Column(Float)  # Flow bank A (cc/min)
    injection_phase_angle = Column(Float)  # Injection phase angle
    injector_duty_a = Column(Float)  # Injector duty cycle A (%)
    injection_time_a = Column(Float)  # Injection time bank A (ms)
    fuel_pressure = Column(Float)  # Fuel pressure (bar)
    fuel_level = Column(Float)  # Fuel level (%)

    # Temperature monitoring
    engine_temp = Column(Float)  # Engine temperature (°C)
    air_temp = Column(Float)  # Air temperature (°C)

    # Electrical and auxiliary
    oil_pressure = Column(Float)  # Oil pressure (bar)
    battery_voltage = Column(Float)  # Battery voltage (V)
    ignition_dwell = Column(Float)  # Ignition dwell (ms)
    fan1_enrichment = Column(Float)  # Fan 1 enrichment

    # Engine status flags
    engine_sync = Column(String(10))  # Engine sync (ON/OFF)
    decel_cutoff = Column(String(10))  # Deceleration cutoff (ON/OFF)
    engine_cranking = Column(String(10))  # Engine cranking (ON/OFF)
    idle = Column(String(10))  # Idle status (ON/OFF)
    first_pulse_cranking = Column(String(10))  # First pulse cranking (ON/OFF)
    accel_decel_injection = Column(String(10))  # AE/DE injection (ON/OFF)

    # Control and outputs
    active_adjustment = Column(Integer)  # Active adjustment (%)
    fan1 = Column(String(10))  # Fan 1 (ON/OFF)
    fan2 = Column(String(10))  # Fan 2 (ON/OFF)
    fuel_pump = Column(String(10))  # Fuel pump (ON/OFF)

    # Relationships
    session = relationship("DataSession", back_populates="core_data")

    # Indexes for performance
    __table_args__ = (
        Index("idx_session_time", "session_id", "time"),
        Index("idx_rpm", "rpm"),
        Index("idx_map_rpm", "map", "rpm"),
        Index("idx_engine_temp", "engine_temp"),
        CheckConstraint("rpm >= 0 AND rpm <= 15000", name="chk_rpm_range"),
        CheckConstraint("tps >= 0 AND tps <= 100", name="chk_tps_range"),
        CheckConstraint("time >= 0", name="chk_time_positive"),
    )


class FuelTechExtendedData(Base):
    """
    Extended FuelTech data table (additional 27 fields for 64-field format).
    Contains advanced telemetry, performance metrics, and IMU data.
    """

    __tablename__ = "fueltech_extended_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("data_sessions.id"), nullable=False)
    time = Column(Float, nullable=False)  # Time in seconds (matches core data)

    # Consumption and efficiency metrics
    total_consumption = Column(Float)  # Total consumption (L)
    average_consumption = Column(Float)  # Average consumption (km/L)
    instant_consumption = Column(Float)  # Instantaneous consumption (L/h)
    total_distance = Column(Float)  # Total distance (km)
    range = Column(Float)  # Range (km)

    # Performance metrics
    estimated_power = Column(Integer)  # Estimated power (HP)
    estimated_torque = Column(Integer)  # Estimated torque (Nm)
    traction_speed = Column(Float)  # Traction speed (km/h)
    acceleration_speed = Column(Float)  # Acceleration speed (km/h)
    acceleration_distance = Column(Float)  # Acceleration distance (m)

    # Traction control
    traction_control_slip = Column(Float)  # Traction control slip (%)
    traction_control_slip_rate = Column(Integer)  # Slip rate (%)
    delta_tps = Column(Float)  # TPS variation (%/s)

    # IMU and dynamics data
    g_force_accel = Column(Float)  # Longitudinal G-force
    g_force_lateral = Column(Float)  # Lateral G-force
    g_force_accel_raw = Column(Float)  # Raw longitudinal G-force
    g_force_lateral_raw = Column(Float)  # Raw lateral G-force

    # Vehicle attitude
    pitch_angle = Column(Float)  # Pitch angle (degrees)
    pitch_rate = Column(Float)  # Pitch rate (degrees/s)
    roll_angle = Column(Float)  # Roll angle (degrees)
    roll_rate = Column(Float)  # Roll rate (degrees/s)
    heading = Column(Float)  # Heading/yaw (degrees)

    # Advanced engine control
    accel_enrichment = Column(String(10))  # Acceleration enrichment (ON/OFF)
    decel_enrichment = Column(String(10))  # Deceleration enrichment (ON/OFF)
    injection_cutoff = Column(String(10))  # Injection cutoff (ON/OFF)
    after_start_injection = Column(String(10))  # After start injection (ON/OFF)
    start_button_toggle = Column(String(10))  # Start button toggle (ON/OFF)

    # Relationships
    session = relationship("DataSession", back_populates="extended_data")

    # Indexes for performance
    __table_args__ = (
        Index("idx_extended_session_time", "session_id", "time"),
        Index("idx_g_forces", "g_force_accel", "g_force_lateral"),
        Index("idx_performance", "estimated_power", "estimated_torque"),
        Index("idx_traction", "traction_control_slip"),
        CheckConstraint("estimated_power >= 0 AND estimated_power <= 2000", name="chk_power_range"),
        CheckConstraint(
            "estimated_torque >= 0 AND estimated_torque <= 5000",
            name="chk_torque_range",
        ),
        CheckConstraint("g_force_accel >= -7.0 AND g_force_accel <= 7.0", name="chk_g_accel_range"),
        CheckConstraint(
            "g_force_lateral >= -7.0 AND g_force_lateral <= 7.0", name="chk_g_lateral_range"
        ),
    )


class DataQualityCheck(Base):
    """
    Data quality assessment results for each session.
    Stores validation results, anomalies, and quality metrics.
    """

    __tablename__ = "data_quality_checks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("data_sessions.id"), nullable=False)

    # Check metadata
    check_type = Column(String(50), nullable=False)  # range_check, consistency_check, etc.
    field_name = Column(String(100))  # Field being checked
    check_timestamp = Column(DateTime, default=func.now())

    # Results
    status = Column(String(20), nullable=False)  # passed, warning, failed
    severity = Column(String(20), default="info")  # info, warning, error, critical
    message = Column(Text)  # Human-readable message

    # Metrics
    affected_records = Column(Integer, default=0)
    total_records = Column(Integer, default=0)
    error_percentage = Column(Float, default=0.0)

    # Details as JSON
    details_json = Column(JSON)  # Additional check-specific data

    # Relationships
    session = relationship("DataSession", back_populates="quality_checks")

    # Indexes
    __table_args__ = (
        Index("idx_quality_session_type", "session_id", "check_type"),
        Index("idx_quality_status", "status"),
        Index("idx_quality_timestamp", "check_timestamp"),
    )


class Vehicle(Base):
    """
    Modelo de dados para veículos cadastrados.
    Armazena todas as informações técnicas do veículo para contextualização
    dos dados de telemetria.
    """
    __tablename__ = "vehicles"
    
    # Identificação Principal
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, comment="Nome/modelo do veículo")
    nickname = Column(String(100), comment="Apelido ou nome popular")
    plate = Column(String(20), comment="Placa do veículo")
    year = Column(Integer, comment="Ano de fabricação")
    brand = Column(String(100), comment="Marca do veículo")
    model = Column(String(100), comment="Modelo específico")
    
    # Especificações do Motor
    engine_displacement = Column(Float, comment="Cilindrada em litros")
    engine_cylinders = Column(Integer, comment="Número de cilindros")
    engine_configuration = Column(String(50), comment="Configuração: V6, I4, V8, etc")
    engine_aspiration = Column(String(50), comment="Naturally Aspirated, Turbo, Supercharged")
    
    # Sistema de Injeção
    injector_type = Column(String(100), comment="Tipo de bico injetor")
    injector_count = Column(Integer, comment="Quantidade de bicos")
    injector_flow_rate = Column(Float, comment="Vazão em cc/min")
    fuel_rail_pressure = Column(Float, comment="Pressão do rail em bar")
    
    # Turbocompressor
    turbo_brand = Column(String(100), comment="Marca do turbocompressor")
    turbo_model = Column(String(100), comment="Modelo do turbocompressor")
    max_boost_pressure = Column(Float, comment="Pressão máxima em bar")
    wastegate_type = Column(String(50), comment="Internal/External wastegate")
    
    # Transmissão
    transmission_type = Column(String(50), comment="Manual/Automatic/CVT")
    gear_count = Column(Integer, comment="Número de marchas")
    final_drive_ratio = Column(Float, comment="Relação final da transmissão")
    
    # Características Físicas
    curb_weight = Column(Float, comment="Peso em ordem de marcha (kg)")
    power_weight_ratio = Column(Float, comment="Relação peso/potência")
    drivetrain = Column(String(50), comment="FWD, RWD, AWD")
    tire_size = Column(String(50), comment="Medida dos pneus")
    
    # Sistema de Combustível
    fuel_type = Column(String(50), comment="Gasoline, Ethanol, Flex, Diesel")
    octane_rating = Column(Integer, comment="Octanagem do combustível")
    fuel_system = Column(String(100), comment="Port Injection, Direct, Dual")
    
    # Performance Estimada
    estimated_power = Column(Float, comment="Potência estimada em HP")
    estimated_torque = Column(Float, comment="Torque estimado em Nm")
    max_rpm = Column(Integer, comment="RPM máximo do motor")
    
    # Sistema de Bancadas de Injeção
    # Bancada A (Principal)
    bank_a_enabled = Column(Boolean, default=True, comment="Bancada A habilitada (sempre ativa)")
    bank_a_mode = Column(String(20), default='semissequencial', comment="Modo: multiponto, semissequencial, sequencial")
    bank_a_outputs = Column(JSON, comment="Lista de saídas utilizadas: [1, 2, 3, 4] etc")
    bank_a_injector_flow = Column(Float, comment="Vazão por bico em lb/h")
    bank_a_injector_count = Column(Integer, comment="Quantidade de bicos na bancada A")
    bank_a_total_flow = Column(Float, comment="Vazão total calculada (lb/h)")
    bank_a_dead_time = Column(Float, comment="Dead time dos injetores em ms")
    
    # Bancada B (Auxiliar)
    bank_b_enabled = Column(Boolean, default=False, comment="Bancada B habilitada")
    bank_b_mode = Column(String(20), default='semissequencial', comment="Modo: multiponto, semissequencial, sequencial")
    bank_b_outputs = Column(JSON, comment="Lista de saídas utilizadas: [5, 6, 7, 8] etc")
    bank_b_injector_flow = Column(Float, comment="Vazão por bico em lb/h")
    bank_b_injector_count = Column(Integer, comment="Quantidade de bicos na bancada B")
    bank_b_total_flow = Column(Float, comment="Vazão total calculada (lb/h)")
    bank_b_dead_time = Column(Float, comment="Dead time dos injetores em ms")
    
    # Limites operacionais para mapas
    max_map_pressure = Column(Float, default=5.0, comment="Pressão MAP máxima em bar")
    min_map_pressure = Column(Float, default=-1.0, comment="Pressão MAP mínima em bar")
    
    # Metadados de Sistema
    created_at = Column(DateTime, default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Última atualização")
    is_active = Column(Boolean, default=True, comment="Veículo está ativo")
    notes = Column(Text, comment="Observações adicionais")
    
    # Relacionamentos
    sessions = relationship("DataSession", back_populates="vehicle", cascade="all, delete-orphan")
    # fuel_maps = relationship("FuelMap", back_populates="vehicle", cascade="all, delete-orphan")  # Temporariamente desabilitado até FuelMap ser criado
    
    # Índices para Performance
    __table_args__ = (
        Index("idx_vehicle_name", "name"),
        Index("idx_vehicle_brand_model", "brand", "model"),
        Index("idx_vehicle_active", "is_active"),
        Index("idx_vehicle_created", "created_at"),
        Index("idx_vehicle_year", "year"),
    )
    
    def __repr__(self):
        return f"<Vehicle(id={self.id}, name='{self.name}', year={self.year})>"
    
    @property
    def display_name(self):
        """Nome formatado para exibição."""
        if self.nickname:
            return f"{self.name} ({self.nickname})"
        return f"{self.name} ({self.year})" if self.year else self.name
    
    @property
    def technical_summary(self):
        """Resumo técnico do veículo."""
        parts = []
        if self.engine_displacement:
            parts.append(f"{self.engine_displacement}L")
        if self.engine_configuration:
            parts.append(self.engine_configuration)
        if self.engine_aspiration and self.engine_aspiration != "Naturally Aspirated":
            parts.append(self.engine_aspiration)
        return " ".join(parts) if parts else "Não especificado"
    
    @property
    def bank_configuration_summary(self):
        """Resumo da configuração de bancadas."""
        summary = []
        
        if self.bank_a_enabled:
            bank_a_flow = self.bank_a_total_flow or 0
            summary.append(f"Bancada A: {bank_a_flow:.0f} lb/h ({self.bank_a_mode})")
        
        if self.bank_b_enabled:
            bank_b_flow = self.bank_b_total_flow or 0
            summary.append(f"Bancada B: {bank_b_flow:.0f} lb/h ({self.bank_b_mode})")
        
        return " | ".join(summary) if summary else "Bancadas não configuradas"
    
    @property
    def total_injector_flow(self):
        """Vazão total de todas as bancadas ativas."""
        total = 0
        if self.bank_a_enabled and self.bank_a_total_flow:
            total += self.bank_a_total_flow
        if self.bank_b_enabled and self.bank_b_total_flow:
            total += self.bank_b_total_flow
        return total
    
    def calculate_bank_flow(self, bank: str) -> float:
        """Calcula vazão total de uma bancada específica."""
        if bank.upper() == 'A':
            flow_per_injector = self.bank_a_injector_flow or 0
            injector_count = self.bank_a_injector_count or 0
        elif bank.upper() == 'B':
            flow_per_injector = self.bank_b_injector_flow or 0
            injector_count = self.bank_b_injector_count or 0
        else:
            return 0.0
        
        return flow_per_injector * injector_count
    
    def update_calculated_flows(self):
        """Atualiza vazões calculadas das bancadas."""
        if self.bank_a_enabled:
            self.bank_a_total_flow = self.calculate_bank_flow('A')
        
        if self.bank_b_enabled:
            self.bank_b_total_flow = self.calculate_bank_flow('B')
    
    def get_bank_outputs(self, bank: str) -> List[int]:
        """Retorna lista de saídas configuradas para uma bancada."""
        import json
        
        if bank.upper() == 'A':
            outputs_json = self.bank_a_outputs
        elif bank.upper() == 'B':
            outputs_json = self.bank_b_outputs
        else:
            return []
        
        if not outputs_json:
            return []
        
        try:
            if isinstance(outputs_json, str):
                return json.loads(outputs_json)
            elif isinstance(outputs_json, list):
                return outputs_json
            else:
                return []
        except:
            return []
    
    def has_output_conflicts(self) -> Tuple[bool, List[int]]:
        """Verifica se há conflitos de saídas entre bancadas."""
        if not self.bank_b_enabled:
            return False, []
        
        outputs_a = set(self.get_bank_outputs('A'))
        outputs_b = set(self.get_bank_outputs('B'))
        
        conflicts = list(outputs_a.intersection(outputs_b))
        return len(conflicts) > 0, conflicts


class DatabaseManager:
    """
    Database manager for FuelTech data models.
    Handles connection, table creation, and basic operations.
    """

    def __init__(self, database_url: str = "sqlite:///data/fueltech_data.db"):
        """
        Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

    def init_database(self) -> None:
        """Initialize database connection and create tables."""
        try:
            self.engine = create_engine(
                self.database_url,
                echo=False,  # Set to True for SQL logging
                pool_pre_ping=True,
                connect_args=(
                    {"check_same_thread": False} if "sqlite" in self.database_url else {}
                ),
            )

            # Create all tables
            Base.metadata.create_all(bind=self.engine)

            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            logger.info(f"Database initialized: {self.database_url}")

        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

    def get_session(self):
        """Get database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call init_database() first.")
        return self.SessionLocal()

    def create_session_record(
        self,
        session_name: str,
        filename: str,
        file_hash: str,
        format_version: str,
        field_count: int,
        **kwargs,
    ) -> DataSession:
        """
        Create a new data session record.

        Args:
            session_name: Name of the session
            filename: Original filename
            file_hash: File hash for deduplication
            format_version: Format version (v1.0 or v2.0)
            field_count: Number of fields
            **kwargs: Additional metadata

        Returns:
            Created DataSession instance
        """
        db = self.get_session()
        try:
            session_record = DataSession(
                session_name=session_name,
                filename=filename,
                file_hash=file_hash,
                format_version=format_version,
                field_count=field_count,
                **kwargs,
            )

            db.add(session_record)
            db.commit()
            db.refresh(session_record)

            logger.info(f"Session record created: {session_record.id}")
            return session_record

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create session record: {str(e)}")
            raise
        finally:
            db.close()

    def get_session_by_hash(self, file_hash: str) -> Optional[DataSession]:
        """Get session by file hash."""
        db = self.get_session()
        try:
            return db.query(DataSession).filter(DataSession.file_hash == file_hash).first()
        finally:
            db.close()

    def get_sessions_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all sessions."""
        db = self.get_session()
        try:
            sessions = db.query(DataSession).order_by(DataSession.created_at.desc()).all()
            return [
                {
                    "id": s.id,
                    "name": s.session_name,
                    "filename": s.filename,
                    "format": s.format_version,
                    "records": s.total_records,
                    "duration": s.duration_seconds,
                    "quality_score": s.quality_score,
                    "status": s.import_status,
                    "created_at": s.created_at,
                }
                for s in sessions
            ]
        finally:
            db.close()

    def bulk_insert_core_data(self, session_id: str, data_records: List[Dict]) -> None:
        """Bulk insert core data records."""
        import numpy as np
        
        # Clean and validate data before insertion
        cleaned_records = []
        skipped_count = 0
        
        for record in data_records:
            # Skip records with invalid values
            skip_record = False
            cleaned_record = {"session_id": session_id}
            
            for key, value in record.items():
                # Check for invalid values
                if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
                    skip_record = True
                    break
                
                # Convert string numbers to appropriate types
                if key == "rpm":
                    try:
                        # Convert RPM to integer
                        rpm_value = float(str(value))
                        if rpm_value < 0 or rpm_value > 20000:
                            skip_record = True
                            break
                        cleaned_record[key] = int(rpm_value)
                    except (ValueError, TypeError):
                        skip_record = True
                        break
                elif key in ["throttle_position", "tps"]:
                    try:
                        tps_value = float(value)
                        if tps_value < -5 or tps_value > 105:
                            skip_record = True
                            break
                        cleaned_record[key] = tps_value
                    except (ValueError, TypeError):
                        skip_record = True
                        break
                elif key == "map":
                    try:
                        map_value = float(value)
                        if map_value < -1 or map_value > 5:
                            skip_record = True
                            break
                        cleaned_record[key] = map_value
                    except (ValueError, TypeError):
                        skip_record = True
                        break
                elif key == "engine_temp":
                    try:
                        temp_value = float(value)
                        if temp_value < -50 or temp_value > 200:
                            skip_record = True
                            break
                        cleaned_record[key] = temp_value
                    except (ValueError, TypeError):
                        skip_record = True
                        break
                elif key == "o2_general":
                    try:
                        o2_value = float(value)
                        if o2_value < 0 or o2_value > 2:
                            skip_record = True
                            break
                        cleaned_record[key] = o2_value
                    except (ValueError, TypeError):
                        skip_record = True
                        break
                else:
                    # For other fields, just ensure it's a valid number if it should be
                    if isinstance(value, str) and key != "id":
                        try:
                            cleaned_record[key] = float(value)
                        except (ValueError, TypeError):
                            cleaned_record[key] = value
                    else:
                        cleaned_record[key] = value
            
            if not skip_record:
                cleaned_records.append(cleaned_record)
            else:
                skipped_count += 1
        
        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} records with invalid values")
        
        if not cleaned_records:
            logger.warning("No valid records to insert after cleaning")
            return
        
        db = self.get_session()
        try:
            db.bulk_insert_mappings(FuelTechCoreData, cleaned_records)
            db.commit()
            logger.info(f"Bulk inserted {len(cleaned_records)} core data records (skipped {skipped_count} invalid)")

        except Exception as e:
            db.rollback()
            logger.error(f"Bulk insert failed: {str(e)}")
            raise
        finally:
            db.close()

    def bulk_insert_extended_data(self, session_id: str, data_records: List[Dict]) -> None:
        """Bulk insert extended data records."""
        db = self.get_session()
        try:
            # Add session_id to each record
            for record in data_records:
                record["session_id"] = session_id

            db.bulk_insert_mappings(FuelTechExtendedData, data_records)
            db.commit()

            logger.info(f"Bulk inserted {len(data_records)} extended data records")

        except Exception as e:
            db.rollback()
            logger.error(f"Bulk insert failed: {str(e)}")
            raise
        finally:
            db.close()


# Global database manager instance
db_manager = DatabaseManager()


def get_database() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager


if __name__ == "__main__":
    # Example usage
    db = DatabaseManager()
    db.init_database()

    # Create a test session
    session = db.create_session_record(
        session_name="Test Session",
        filename="test.csv",
        file_hash="abc123",
        format_version="v2.0",
        field_count=64,
    )

    print(f"Created session: {session.id}")

    # Get sessions summary
    summary = db.get_sessions_summary()
    print(f"Sessions: {summary}")
