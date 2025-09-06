"""
Unit tests for models.py - Comprehensive test coverage for SQLAlchemy models.

Tests cover:
- Model creation and validation
- Relationships between models
- Constraints and indexes
- DatabaseManager functionality
- Bulk operations
- Query operations

Author: FIX-DATA Agent
Created: 2025-01-02
"""

import tempfile

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.data.models import (
    Base,
    DatabaseManager,
    DataQualityCheck,
    DataSession,
    FuelTechCoreData,
    FuelTechExtendedData,
    get_database,
)


class TestDataSessionModel:
    """Test suite for DataSession model."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    def test_create_data_session(self, db_session):
        """Test creating a DataSession instance."""
        session_data = DataSession(
            session_name="Test Session",
            filename="test.csv",
            file_hash="abc123def456",
            format_version="v1.0",
            field_count=37,
            total_records=1000,
            duration_seconds=120.5,
            sample_rate_hz=10.0,
            file_size_mb=2.5,
            quality_score=85.5,
            metadata_json={"test": "data"},
        )

        db_session.add(session_data)
        db_session.commit()

        # Verify the session was created
        assert session_data.id is not None
        assert session_data.session_name == "Test Session"
        assert session_data.format_version == "v1.0"
        assert session_data.quality_score == 85.5
        assert session_data.metadata_json == {"test": "data"}

    def test_data_session_defaults(self, db_session):
        """Test DataSession default values."""
        session_data = DataSession(
            session_name="Default Test",
            filename="default.csv",
            file_hash="def123abc456",
            format_version="v2.0",
            field_count=64,
        )

        db_session.add(session_data)
        db_session.commit()

        # Check defaults
        assert session_data.total_records == 0
        assert session_data.import_status == "pending"
        assert session_data.validation_status == "pending"
        assert session_data.error_count == 0
        assert session_data.warning_count == 0
        assert session_data.original_encoding == "utf-8"
        assert session_data.created_at is not None
        assert session_data.updated_at is not None

    def test_data_session_unique_constraint(self, db_session):
        """Test file_hash unique constraint."""
        hash_value = "duplicate_hash_123"

        # First session should succeed
        session1 = DataSession(
            session_name="First",
            filename="first.csv",
            file_hash=hash_value,
            format_version="v1.0",
            field_count=37,
        )
        db_session.add(session1)
        db_session.commit()

        # Second session with same hash should fail
        session2 = DataSession(
            session_name="Second",
            filename="second.csv",
            file_hash=hash_value,
            format_version="v1.0",
            field_count=37,
        )
        db_session.add(session2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_data_session_quality_score_constraint(self, db_session):
        """Test quality_score check constraint."""
        # Valid quality score should work
        valid_session = DataSession(
            session_name="Valid",
            filename="valid.csv",
            file_hash="valid123",
            format_version="v1.0",
            field_count=37,
            quality_score=75.5,
        )
        db_session.add(valid_session)
        db_session.commit()

        # Invalid quality score (> 100) should fail
        invalid_session = DataSession(
            session_name="Invalid",
            filename="invalid.csv",
            file_hash="invalid123",
            format_version="v1.0",
            field_count=37,
            quality_score=150.0,
        )
        db_session.add(invalid_session)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_data_session_format_version_constraint(self, db_session):
        """Test format_version check constraint."""
        # Valid versions should work
        for version in ["v1.0", "v2.0"]:
            valid_session = DataSession(
                session_name=f"Valid {version}",
                filename=f"valid_{version}.csv",
                file_hash=f"hash_{version}",
                format_version=version,
                field_count=37 if version == "v1.0" else 64,
            )
            db_session.add(valid_session)

        db_session.commit()

        # Invalid version should fail
        invalid_session = DataSession(
            session_name="Invalid Version",
            filename="invalid_version.csv",
            file_hash="invalid_version_hash",
            format_version="v3.0",
            field_count=37,
        )
        db_session.add(invalid_session)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestFuelTechCoreDataModel:
    """Test suite for FuelTechCoreData model."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    @pytest.fixture
    def test_session(self, db_session):
        """Create test DataSession for foreign key relations."""
        session_data = DataSession(
            session_name="Core Test Session",
            filename="core_test.csv",
            file_hash="core123",
            format_version="v1.0",
            field_count=37,
        )
        db_session.add(session_data)
        db_session.commit()
        return session_data

    def test_create_core_data(self, db_session, test_session):
        """Test creating FuelTechCoreData instance."""
        core_data = FuelTechCoreData(
            session_id=test_session.id,
            time=1.5,
            rpm=2500,
            tps=45.5,
            throttle_position=50.0,
            ignition_timing=15.5,
            map=1.2,
            closed_loop_target=0.85,
            engine_temp=90.5,
            battery_voltage=14.2,
        )

        db_session.add(core_data)
        db_session.commit()

        assert core_data.id is not None
        assert core_data.session_id == test_session.id
        assert core_data.rpm == 2500
        assert core_data.tps == 45.5

    def test_core_data_relationships(self, db_session, test_session):
        """Test relationships between CoreData and DataSession."""
        core_data = FuelTechCoreData(session_id=test_session.id, time=2.0, rpm=3000, tps=60.0)

        db_session.add(core_data)
        db_session.commit()

        # Test relationship from core_data to session
        assert core_data.session.session_name == "Core Test Session"

        # Test relationship from session to core_data
        assert len(test_session.core_data) == 1
        assert test_session.core_data[0].rpm == 3000

    def test_core_data_constraints(self, db_session, test_session):
        """Test FuelTechCoreData constraints."""
        # Test RPM range constraint
        invalid_rpm_data = FuelTechCoreData(
            session_id=test_session.id,
            time=1.0,
            rpm=-100,  # Invalid: RPM should be >= 0
            tps=50.0,
        )

        db_session.add(invalid_rpm_data)
        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

        # Test TPS range constraint
        invalid_tps_data = FuelTechCoreData(
            session_id=test_session.id,
            time=1.0,
            rpm=2000,
            tps=150.0,  # Invalid: TPS should be <= 100
        )

        db_session.add(invalid_tps_data)
        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

        # Test negative time constraint
        invalid_time_data = FuelTechCoreData(
            session_id=test_session.id,
            time=-1.0,  # Invalid: time should be >= 0
            rpm=2000,
            tps=50.0,
        )

        db_session.add(invalid_time_data)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_core_data_string_fields(self, db_session, test_session):
        """Test string field handling in CoreData."""
        core_data = FuelTechCoreData(
            session_id=test_session.id,
            time=1.0,
            rpm=2000,
            two_step="ON",
            launch_validated="OFF",
            engine_sync="ON",
            decel_cutoff="OFF",
            idle="ON",
        )

        db_session.add(core_data)
        db_session.commit()

        assert core_data.two_step == "ON"
        assert core_data.launch_validated == "OFF"
        assert core_data.engine_sync == "ON"


class TestFuelTechExtendedDataModel:
    """Test suite for FuelTechExtendedData model."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    @pytest.fixture
    def test_session(self, db_session):
        """Create test DataSession for foreign key relations."""
        session_data = DataSession(
            session_name="Extended Test Session",
            filename="extended_test.csv",
            file_hash="extended123",
            format_version="v2.0",
            field_count=64,
        )
        db_session.add(session_data)
        db_session.commit()
        return session_data

    def test_create_extended_data(self, db_session, test_session):
        """Test creating FuelTechExtendedData instance."""
        extended_data = FuelTechExtendedData(
            session_id=test_session.id,
            time=2.5,
            total_consumption=15.5,
            average_consumption=8.2,
            estimated_power=300,
            estimated_torque=450,
            g_force_accel=0.8,
            g_force_lateral=-0.3,
            pitch_angle=2.5,
            roll_angle=-1.2,
        )

        db_session.add(extended_data)
        db_session.commit()

        assert extended_data.id is not None
        assert extended_data.session_id == test_session.id
        assert extended_data.estimated_power == 300
        assert extended_data.g_force_accel == 0.8

    def test_extended_data_relationships(self, db_session, test_session):
        """Test relationships between ExtendedData and DataSession."""
        extended_data = FuelTechExtendedData(
            session_id=test_session.id, time=3.0, estimated_power=250
        )

        db_session.add(extended_data)
        db_session.commit()

        # Test relationship from extended_data to session
        assert extended_data.session.session_name == "Extended Test Session"

        # Test relationship from session to extended_data
        assert len(test_session.extended_data) == 1
        assert test_session.extended_data[0].estimated_power == 250

    def test_extended_data_constraints(self, db_session, test_session):
        """Test FuelTechExtendedData constraints."""
        # Test estimated_power range constraint
        invalid_power_data = FuelTechExtendedData(
            session_id=test_session.id,
            time=1.0,
            estimated_power=-50,  # Invalid: should be >= 0
        )

        db_session.add(invalid_power_data)
        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

        # Test g_force_accel range constraint
        invalid_g_data = FuelTechExtendedData(
            session_id=test_session.id,
            time=1.0,
            g_force_accel=10.0,  # Invalid: should be <= 5
        )

        db_session.add(invalid_g_data)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestDataQualityCheckModel:
    """Test suite for DataQualityCheck model."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    @pytest.fixture
    def test_session(self, db_session):
        """Create test DataSession for foreign key relations."""
        session_data = DataSession(
            session_name="Quality Test Session",
            filename="quality_test.csv",
            file_hash="quality123",
            format_version="v1.0",
            field_count=37,
        )
        db_session.add(session_data)
        db_session.commit()
        return session_data

    def test_create_quality_check(self, db_session, test_session):
        """Test creating DataQualityCheck instance."""
        quality_check = DataQualityCheck(
            session_id=test_session.id,
            check_type="range_check",
            field_name="rpm",
            status="passed",
            severity="info",
            message="RPM values within expected range",
            affected_records=0,
            total_records=1000,
            error_percentage=0.0,
            details_json={"min_value": 800, "max_value": 7000},
        )

        db_session.add(quality_check)
        db_session.commit()

        assert quality_check.id is not None
        assert quality_check.check_type == "range_check"
        assert quality_check.status == "passed"
        assert quality_check.details_json["min_value"] == 800

    def test_quality_check_relationships(self, db_session, test_session):
        """Test relationships between QualityCheck and DataSession."""
        quality_check = DataQualityCheck(
            session_id=test_session.id,
            check_type="consistency_check",
            status="warning",
            message="Minor inconsistencies found",
        )

        db_session.add(quality_check)
        db_session.commit()

        # Test relationship from quality_check to session
        assert quality_check.session.session_name == "Quality Test Session"

        # Test relationship from session to quality_checks
        assert len(test_session.quality_checks) == 1
        assert test_session.quality_checks[0].check_type == "consistency_check"

    def test_quality_check_defaults(self, db_session, test_session):
        """Test DataQualityCheck default values."""
        quality_check = DataQualityCheck(
            session_id=test_session.id, check_type="basic_check", status="passed"
        )

        db_session.add(quality_check)
        db_session.commit()

        # Check defaults
        assert quality_check.severity == "info"
        assert quality_check.affected_records == 0
        assert quality_check.total_records == 0
        assert quality_check.error_percentage == 0.0
        assert quality_check.check_timestamp is not None

    def test_multiple_quality_checks(self, db_session, test_session):
        """Test multiple quality checks for same session."""
        checks = [
            DataQualityCheck(
                session_id=test_session.id,
                check_type="range_check",
                field_name="rpm",
                status="passed",
            ),
            DataQualityCheck(
                session_id=test_session.id,
                check_type="null_check",
                field_name="tps",
                status="warning",
            ),
            DataQualityCheck(
                session_id=test_session.id,
                check_type="outlier_check",
                field_name="map",
                status="failed",
            ),
        ]

        for check in checks:
            db_session.add(check)

        db_session.commit()

        # Verify all checks are associated with session
        assert len(test_session.quality_checks) == 3
        check_types = [check.check_type for check in test_session.quality_checks]
        assert "range_check" in check_types
        assert "null_check" in check_types
        assert "outlier_check" in check_types


class TestDatabaseManager:
    """Test suite for DatabaseManager class."""

    @pytest.fixture
    def temp_db_file(self):
        """Create temporary database file."""
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()
        yield temp_file.name
        # Cleanup
        import os

        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

    @pytest.fixture
    def db_manager(self, temp_db_file):
        """Create DatabaseManager instance."""
        db_url = f"sqlite:///{temp_db_file}"
        manager = DatabaseManager(db_url)
        manager.init_database()
        return manager

    def test_database_manager_init(self, temp_db_file):
        """Test DatabaseManager initialization."""
        db_url = f"sqlite:///{temp_db_file}"
        manager = DatabaseManager(db_url)

        assert manager.database_url == db_url
        assert manager.engine is None
        assert manager.SessionLocal is None

        # Initialize database
        manager.init_database()

        assert manager.engine is not None
        assert manager.SessionLocal is not None

    def test_get_session(self, db_manager):
        """Test getting database session."""
        session = db_manager.get_session()
        assert session is not None
        session.close()

    def test_get_session_not_initialized(self):
        """Test error when getting session before initialization."""
        manager = DatabaseManager()

        with pytest.raises(RuntimeError, match="Database not initialized"):
            manager.get_session()

    def test_create_session_record(self, db_manager):
        """Test creating session record."""
        session_record = db_manager.create_session_record(
            session_name="Test Session",
            filename="test.csv",
            file_hash="abc123",
            format_version="v1.0",
            field_count=37,
            total_records=500,
            quality_score=88.5,
        )

        assert session_record.id is not None
        assert session_record.session_name == "Test Session"
        assert session_record.total_records == 500
        assert session_record.quality_score == 88.5

    def test_get_session_by_hash(self, db_manager):
        """Test retrieving session by file hash."""
        # Create session
        hash_value = "unique_hash_123"
        created_session = db_manager.create_session_record(
            session_name="Hash Test",
            filename="hash_test.csv",
            file_hash=hash_value,
            format_version="v1.0",
            field_count=37,
        )

        # Retrieve by hash
        retrieved_session = db_manager.get_session_by_hash(hash_value)

        assert retrieved_session is not None
        assert retrieved_session.id == created_session.id
        assert retrieved_session.session_name == "Hash Test"

        # Test non-existent hash
        non_existent = db_manager.get_session_by_hash("nonexistent_hash")
        assert non_existent is None

    def test_get_sessions_summary(self, db_manager):
        """Test getting sessions summary."""
        # Initially empty
        summary = db_manager.get_sessions_summary()
        assert isinstance(summary, list)
        assert len(summary) == 0

        # Create some sessions
        session1 = db_manager.create_session_record(
            session_name="First Session",
            filename="first.csv",
            file_hash="hash1",
            format_version="v1.0",
            field_count=37,
            total_records=100,
        )

        session2 = db_manager.create_session_record(
            session_name="Second Session",
            filename="second.csv",
            file_hash="hash2",
            format_version="v2.0",
            field_count=64,
            total_records=200,
        )

        # Get summary
        summary = db_manager.get_sessions_summary()
        assert len(summary) == 2

        # Check summary structure
        for session_info in summary:
            assert "id" in session_info
            assert "name" in session_info
            assert "filename" in session_info
            assert "format" in session_info
            assert "records" in session_info

    def test_bulk_insert_core_data(self, db_manager):
        """Test bulk inserting core data."""
        # Create session
        session_record = db_manager.create_session_record(
            session_name="Bulk Core Test",
            filename="bulk_core.csv",
            file_hash="bulk_core_hash",
            format_version="v1.0",
            field_count=37,
        )

        # Prepare bulk data
        bulk_data = []
        for i in range(5):
            bulk_data.append(
                {
                    "time": i * 0.1,
                    "rpm": 1000 + i * 100,
                    "tps": 10.0 + i * 5.0,
                    "throttle_position": 10.0 + i * 5.0,
                    "engine_temp": 85.0 + i * 0.5,
                }
            )

        # Insert data
        db_manager.bulk_insert_core_data(session_record.id, bulk_data)

        # Verify data was inserted
        session = db_manager.get_session()
        try:
            count = (
                session.query(FuelTechCoreData)
                .filter(FuelTechCoreData.session_id == session_record.id)
                .count()
            )
            assert count == 5

            # Verify data content
            first_record = (
                session.query(FuelTechCoreData)
                .filter(
                    FuelTechCoreData.session_id == session_record.id,
                    FuelTechCoreData.time == 0.0,
                )
                .first()
            )
            assert first_record.rpm == 1000
            assert first_record.tps == 10.0
        finally:
            session.close()

    def test_bulk_insert_extended_data(self, db_manager):
        """Test bulk inserting extended data."""
        # Create session
        session_record = db_manager.create_session_record(
            session_name="Bulk Extended Test",
            filename="bulk_extended.csv",
            file_hash="bulk_extended_hash",
            format_version="v2.0",
            field_count=64,
        )

        # Prepare bulk extended data
        bulk_data = []
        for i in range(3):
            bulk_data.append(
                {
                    "time": i * 0.2,
                    "estimated_power": 250 + i * 10,
                    "estimated_torque": 400 + i * 20,
                    "g_force_accel": 0.5 + i * 0.1,
                    "total_consumption": 10.0 + i * 1.0,
                }
            )

        # Insert data
        db_manager.bulk_insert_extended_data(session_record.id, bulk_data)

        # Verify data was inserted
        session = db_manager.get_session()
        try:
            count = (
                session.query(FuelTechExtendedData)
                .filter(FuelTechExtendedData.session_id == session_record.id)
                .count()
            )
            assert count == 3

            # Verify data content
            first_record = (
                session.query(FuelTechExtendedData)
                .filter(
                    FuelTechExtendedData.session_id == session_record.id,
                    FuelTechExtendedData.time == 0.0,
                )
                .first()
            )
            assert first_record.estimated_power == 250
        finally:
            session.close()


class TestModelIndexes:
    """Test that database indexes are properly created."""

    def test_table_indexes_created(self):
        """Test that all expected indexes are created."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)

        # Test DataSession indexes
        session_indexes = inspector.get_indexes("data_sessions")
        index_names = [idx["name"] for idx in session_indexes]

        expected_session_indexes = [
            "idx_session_name",
            "idx_created_at",
            "idx_import_status",
        ]

        for expected_idx in expected_session_indexes:
            assert expected_idx in index_names

        # Test FuelTechCoreData indexes
        core_indexes = inspector.get_indexes("fueltech_core_data")
        core_index_names = [idx["name"] for idx in core_indexes]

        expected_core_indexes = [
            "idx_session_time",
            "idx_rpm",
            "idx_map_rpm",
            "idx_engine_temp",
        ]

        for expected_idx in expected_core_indexes:
            assert expected_idx in core_index_names

    def test_unique_constraints(self):
        """Test unique constraints are properly enforced."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)

        # Check DataSession unique constraint on file_hash
        session_constraints = inspector.get_unique_constraints("data_sessions")
        constraint_columns = [constraint["column_names"] for constraint in session_constraints]

        assert ["file_hash"] in constraint_columns


class TestCascadeDeletes:
    """Test cascade delete functionality."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    def test_cascade_delete_core_data(self, db_session):
        """Test that deleting session cascades to core data."""
        # Create session
        session_data = DataSession(
            session_name="Cascade Test",
            filename="cascade.csv",
            file_hash="cascade123",
            format_version="v1.0",
            field_count=37,
        )
        db_session.add(session_data)
        db_session.commit()

        # Add core data
        core_data = FuelTechCoreData(session_id=session_data.id, time=1.0, rpm=2000)
        db_session.add(core_data)
        db_session.commit()

        # Verify data exists
        assert db_session.query(FuelTechCoreData).count() == 1

        # Delete session
        db_session.delete(session_data)
        db_session.commit()

        # Core data should be deleted too
        assert db_session.query(FuelTechCoreData).count() == 0

    def test_cascade_delete_quality_checks(self, db_session):
        """Test that deleting session cascades to quality checks."""
        # Create session
        session_data = DataSession(
            session_name="Quality Cascade Test",
            filename="quality_cascade.csv",
            file_hash="quality_cascade123",
            format_version="v1.0",
            field_count=37,
        )
        db_session.add(session_data)
        db_session.commit()

        # Add quality check
        quality_check = DataQualityCheck(
            session_id=session_data.id, check_type="test_check", status="passed"
        )
        db_session.add(quality_check)
        db_session.commit()

        # Verify data exists
        assert db_session.query(DataQualityCheck).count() == 1

        # Delete session
        db_session.delete(session_data)
        db_session.commit()

        # Quality check should be deleted too
        assert db_session.query(DataQualityCheck).count() == 0


class TestGlobalDatabaseManager:
    """Test global database manager instance."""

    def test_get_database_singleton(self):
        """Test that get_database returns same instance."""
        manager1 = get_database()
        manager2 = get_database()

        assert manager1 is manager2

    def test_global_manager_properties(self):
        """Test properties of global database manager."""
        manager = get_database()

        assert isinstance(manager, DatabaseManager)
        assert manager.database_url == "sqlite:///data/fueltech_data.db"


class TestModelValidation:
    """Test model field validation and constraints."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    def test_required_fields(self, db_session):
        """Test that required fields are enforced."""
        # Test DataSession required fields
        with pytest.raises(Exception):  # Missing required fields
            session_data = DataSession()
            db_session.add(session_data)
            db_session.commit()

        # Rollback after expected failure
        db_session.rollback()

        # Test FuelTechCoreData required fields
        test_session = DataSession(
            session_name="Test",
            filename="test.csv",
            file_hash="test123",
            format_version="v1.0",
            field_count=37,
        )
        db_session.add(test_session)
        db_session.commit()

        with pytest.raises(Exception):  # Missing session_id
            core_data = FuelTechCoreData(time=1.0, rpm=2000)
            db_session.add(core_data)
            db_session.commit()

        # Rollback after expected failure
        db_session.rollback()

    def test_field_lengths(self, db_session):
        """Test field length constraints."""
        # Test string field lengths don't cause issues with reasonable values
        session_data = DataSession(
            session_name="A" * 100,  # Long but reasonable session name
            filename="test.csv",
            file_hash="a" * 64,  # SHA-256 length
            format_version="v1.0",
            field_count=37,
        )

        db_session.add(session_data)
        db_session.commit()  # Should succeed

        assert session_data.session_name == "A" * 100
