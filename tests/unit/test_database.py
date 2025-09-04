"""
Unit tests for database.py - Comprehensive test coverage for FuelTechDatabase class.

Tests cover:
- Database initialization and teardown
- Session management
- File import with validation
- Data insertion and retrieval
- Quality assessment integration
- Export functionality
- Error handling

Author: FIX-DATA Agent
Created: 2025-01-02
"""

import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from src.data.database import DatabaseError, DataImportError, FuelTechDatabase, get_database
from src.data.models import Base, DataQualityCheck, DataSession, FuelTechCoreData


class TestFuelTechDatabase:
    """Test suite for FuelTechDatabase class."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file."""
        temp_fd, temp_path = tempfile.mkstemp(suffix=".db")
        os.close(temp_fd)
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def db_instance(self, temp_db_path):
        """Create FuelTechDatabase instance for testing."""
        return FuelTechDatabase(temp_db_path, create_tables=True)

    @pytest.fixture
    def sample_csv_data_v1(self):
        """Create sample CSV data for v1.0 format (37 fields)."""
        return pd.DataFrame(
            {
                "time": [0.0, 0.1, 0.2, 0.3, 0.4],
                "rpm": [800, 1000, 1200, 1400, 1600],
                "tps": [10.5, 15.2, 20.8, 25.1, 30.4],
                "throttle_position": [10.0, 15.0, 20.0, 25.0, 30.0],
                "ignition_timing": [12.5, 13.2, 14.1, 15.0, 16.2],
                "map": [1.0, 1.1, 1.2, 1.3, 1.4],
                "closed_loop_target": [0.85, 0.86, 0.87, 0.88, 0.89],
                "closed_loop_o2": [0.84, 0.85, 0.86, 0.87, 0.88],
                "closed_loop_correction": [2.1, 1.8, 1.5, 1.2, 0.9],
                "o2_general": [0.85, 0.86, 0.87, 0.88, 0.89],
                "two_step": ["OFF", "OFF", "OFF", "OFF", "OFF"],
                "ethanol_content": [85, 85, 85, 85, 85],
                "launch_validated": ["OFF", "OFF", "OFF", "OFF", "OFF"],
                "fuel_temp": [45.2, 45.5, 45.8, 46.1, 46.4],
                "gear": [1, 1, 2, 2, 2],
                "flow_bank_a": [250.5, 280.2, 310.8, 340.1, 370.4],
                "injection_phase_angle": [180, 180, 180, 180, 180],
                "injector_duty_a": [25.1, 28.5, 32.2, 35.8, 39.4],
                "injection_time_a": [5.2, 5.8, 6.4, 7.1, 7.8],
                "engine_temp": [85.2, 86.1, 87.0, 87.9, 88.8],
                "air_temp": [25.1, 25.3, 25.5, 25.7, 25.9],
                "oil_pressure": [4.2, 4.3, 4.4, 4.5, 4.6],
                "fuel_pressure": [3.8, 3.9, 4.0, 4.1, 4.2],
                "battery_voltage": [13.8, 13.9, 14.0, 14.1, 14.2],
                "ignition_dwell": [3.5, 3.6, 3.7, 3.8, 3.9],
                "fan1_enrichment": [0.0, 0.0, 0.0, 0.0, 0.0],
                "fuel_level": [75.2, 75.1, 75.0, 74.9, 74.8],
                "engine_sync": ["ON", "ON", "ON", "ON", "ON"],
                "decel_cutoff": ["OFF", "OFF", "OFF", "OFF", "OFF"],
                "engine_cranking": ["OFF", "OFF", "OFF", "OFF", "OFF"],
                "idle": ["OFF", "OFF", "OFF", "OFF", "OFF"],
                "first_pulse_cranking": ["OFF", "OFF", "OFF", "OFF", "OFF"],
                "accel_decel_injection": ["OFF", "OFF", "OFF", "OFF", "OFF"],
                "active_adjustment": [0, 0, 0, 0, 0],
                "fan1": ["OFF", "OFF", "OFF", "OFF", "OFF"],
                "fan2": ["OFF", "OFF", "OFF", "OFF", "OFF"],
                "fuel_pump": ["ON", "ON", "ON", "ON", "ON"],
            }
        )

    @pytest.fixture
    def sample_csv_file(self, sample_csv_data_v1):
        """Create temporary CSV file with sample data."""
        temp_fd, temp_path = tempfile.mkstemp(suffix=".csv")
        os.close(temp_fd)

        sample_csv_data_v1.to_csv(temp_path, index=False)

        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_database_initialization(self, temp_db_path):
        """Test database initialization creates all tables correctly."""
        db = FuelTechDatabase(temp_db_path, create_tables=True)

        # Check database file was created
        assert os.path.exists(temp_db_path)

        # Check tables were created
        engine = create_engine(f"sqlite:///{temp_db_path}")
        Base.metadata.reflect(bind=engine)

        expected_tables = {
            "data_sessions",
            "fueltech_core_data",
            "fueltech_extended_data",
            "data_quality_checks",
        }

        actual_tables = set(Base.metadata.tables.keys())
        assert expected_tables.issubset(actual_tables)

    def test_database_initialization_failure(self):
        """Test database initialization failure handling."""
        # Try to create database in non-existent directory without permission
        invalid_path = "/root/nonexistent/database.db"

        with pytest.raises(DatabaseError):
            db = FuelTechDatabase(invalid_path, create_tables=True)

    def test_session_context_manager(self, db_instance):
        """Test database session context manager."""
        with db_instance.get_session() as session:
            assert session is not None
            # Session should be active
            assert session.is_active

    def test_session_context_manager_error_handling(self, db_instance):
        """Test session context manager handles errors correctly."""
        with pytest.raises(Exception):
            with db_instance.get_session() as session:
                # Force an error
                session.execute("INVALID SQL")

    def test_calculate_file_hash(self, db_instance, sample_csv_file):
        """Test file hash calculation."""
        hash1 = db_instance.calculate_file_hash(sample_csv_file)
        hash2 = db_instance.calculate_file_hash(sample_csv_file)

        # Hash should be consistent
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 character hex string

        # Verify it's actually a valid SHA-256
        expected_hash = hashlib.sha256()
        with open(sample_csv_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                expected_hash.update(chunk)

        assert hash1 == expected_hash.hexdigest()

    @patch("src.data.database.CSVParser")
    @patch("src.data.database.validate_fueltech_data")
    @patch("src.data.database.normalize_fueltech_data")
    @patch("src.data.database.assess_fueltech_data_quality")
    def test_import_csv_file_success(
        self,
        mock_assess,
        mock_normalize,
        mock_validate,
        mock_parser,
        db_instance,
        sample_csv_file,
        sample_csv_data_v1,
    ):
        """Test successful CSV file import."""
        # Setup mocks
        parser_instance = Mock()
        parser_instance.parse_csv.return_value = sample_csv_data_v1
        parser_instance.get_file_info.return_value = {"file_size_mb": 0.1}
        parser_instance.detected_version = "v1.0"
        parser_instance.encoding = "utf-8"
        mock_parser.return_value = parser_instance

        mock_validate.return_value = {"is_valid": True, "errors": []}
        mock_normalize.return_value = (sample_csv_data_v1, {"outliers_fixed": 0})
        mock_assess.return_value = {"overall_score": 85.5, "detailed_results": []}

        # Import file
        result = db_instance.import_csv_file(sample_csv_file)

        # Verify result
        assert result["status"] == "completed"
        assert "session_id" in result
        assert result["total_records"] == len(sample_csv_data_v1)
        assert "csv_parsing" in result["steps_completed"]
        assert "data_validation" in result["steps_completed"]
        assert "data_normalization" in result["steps_completed"]
        assert "quality_assessment" in result["steps_completed"]

        # Verify mocks were called
        parser_instance.parse_csv.assert_called_once()
        mock_validate.assert_called_once()
        mock_normalize.assert_called_once()
        mock_assess.assert_called_once()

    def test_import_csv_file_not_found(self, db_instance):
        """Test import fails when file doesn't exist."""
        non_existent_file = "/nonexistent/file.csv"

        with pytest.raises(DataImportError) as exc_info:
            db_instance.import_csv_file(non_existent_file)

        assert "File not found" in str(exc_info.value)

    @patch("src.data.database.CSVParser")
    def test_import_csv_file_parsing_error(self, mock_parser, db_instance, sample_csv_file):
        """Test import handles parsing errors gracefully."""
        # Setup parser to raise error
        parser_instance = Mock()
        parser_instance.parse_csv.side_effect = Exception("Parsing failed")
        mock_parser.return_value = parser_instance

        with pytest.raises(DataImportError) as exc_info:
            db_instance.import_csv_file(sample_csv_file)

        assert "Import failed" in str(exc_info.value)

    def test_import_csv_file_duplicate_detection(self, db_instance, sample_csv_file):
        """Test duplicate file detection works correctly."""
        sample_data = pd.DataFrame(
            {
                "time": [0.0, 0.1],
                "rpm": [800, 1000],
                "tps": [10.5, 15.2],
            }
        )

        # First import should succeed
        with patch("src.data.database.CSVParser") as mock_parser, patch(
            "src.data.database.validate_fueltech_data"
        ) as mock_validate, patch(
            "src.data.database.normalize_fueltech_data"
        ) as mock_normalize, patch(
            "src.data.database.assess_fueltech_data_quality"
        ) as mock_assess:

            # Setup mocks
            parser_instance = Mock()
            parser_instance.parse_csv.return_value = sample_data
            parser_instance.get_file_info.return_value = {"file_size_mb": 0.1}
            parser_instance.detected_version = "v1.0"
            parser_instance.encoding = "utf-8"
            mock_parser.return_value = parser_instance

            mock_validate.return_value = {"is_valid": True, "errors": []}
            mock_normalize.return_value = (sample_data, {"outliers_fixed": 0})
            mock_assess.return_value = {"overall_score": 85.5, "detailed_results": []}

            result1 = db_instance.import_csv_file(sample_csv_file)
            assert result1["status"] == "completed"

            # Second import should be skipped
            result2 = db_instance.import_csv_file(sample_csv_file, force_reimport=False)
            assert result2["status"] == "skipped"
            assert result2["reason"] == "file_already_imported"

    def _setup_import_mocks(self, csv_file):
        """Helper to setup mocks for import tests."""
        sample_data = pd.DataFrame(
            {
                "time": [0.0, 0.1],
                "rpm": [800, 1000],
                "tps": [10.5, 15.2],
                # Add other required fields...
            }
        )

        with patch("src.data.database.CSVParser") as mock_parser, patch(
            "src.data.database.validate_fueltech_data"
        ) as mock_validate, patch(
            "src.data.database.normalize_fueltech_data"
        ) as mock_normalize, patch(
            "src.data.database.assess_fueltech_data_quality"
        ) as mock_assess:

            parser_instance = Mock()
            parser_instance.parse_csv.return_value = sample_data
            parser_instance.get_file_info.return_value = {"file_size_mb": 0.1}
            parser_instance.detected_version = "v1.0"
            parser_instance.encoding = "utf-8"
            mock_parser.return_value = parser_instance

            mock_validate.return_value = {"is_valid": True, "errors": []}
            mock_normalize.return_value = (sample_data, {"outliers_fixed": 0})
            mock_assess.return_value = {"overall_score": 85.5, "detailed_results": []}

    def test_get_sessions(self, db_instance):
        """Test retrieving sessions summary."""
        # Initially should be empty
        sessions = db_instance.get_sessions()
        assert isinstance(sessions, list)
        assert len(sessions) == 0

        # Create a test session
        with db_instance.get_session() as db:
            test_session = DataSession(
                session_name="Test Session",
                filename="test.csv",
                file_hash="abc123",
                format_version="v1.0",
                field_count=37,
                total_records=100,
            )
            db.add(test_session)
            db.commit()

        # Now should have one session
        sessions = db_instance.get_sessions()
        assert len(sessions) == 1
        assert sessions[0]["name"] == "Test Session"

    def test_get_session_data(self, db_instance):
        """Test retrieving session data."""
        # Create test session and data
        with db_instance.get_session() as db:
            test_session = DataSession(
                id=str(uuid4()),
                session_name="Test Session",
                filename="test.csv",
                file_hash="abc123",
                format_version="v1.0",
                field_count=37,
                total_records=2,
            )
            db.add(test_session)
            db.flush()  # Get the ID

            # Add some core data
            core_data = [
                FuelTechCoreData(
                    session_id=test_session.id,
                    time=0.0,
                    rpm=800,
                    tps=10.5,
                    throttle_position=10.0,
                ),
                FuelTechCoreData(
                    session_id=test_session.id,
                    time=0.1,
                    rpm=1000,
                    tps=15.2,
                    throttle_position=15.0,
                ),
            ]

            for data in core_data:
                db.add(data)

            db.commit()

            # Retrieve data
            result_df = db_instance.get_session_data(test_session.id)
            assert len(result_df) == 2
            assert "time" in result_df.columns
            assert "rpm" in result_df.columns

    def test_get_session_data_with_time_range(self, db_instance):
        """Test retrieving session data with time range filter."""
        # Create test data with different time stamps
        with db_instance.get_session() as db:
            test_session = DataSession(
                id=str(uuid4()),
                session_name="Test Session",
                filename="test.csv",
                file_hash="abc123",
                format_version="v1.0",
                field_count=37,
                total_records=3,
            )
            db.add(test_session)
            db.flush()

            # Add core data with different times
            times = [0.0, 0.5, 1.0]
            for i, time_val in enumerate(times):
                core_data = FuelTechCoreData(
                    session_id=test_session.id,
                    time=time_val,
                    rpm=800 + i * 100,
                    tps=10.0 + i * 5.0,
                )
                db.add(core_data)

            db.commit()

            # Test time range filter
            result_df = db_instance.get_session_data(test_session.id, time_range=(0.2, 0.8))

            # Should only get the middle record (time=0.5)
            assert len(result_df) == 1
            assert result_df.iloc[0]["time"] == 0.5

    def test_get_session_quality(self, db_instance):
        """Test retrieving session quality assessment."""
        # Create test session and quality check
        with db_instance.get_session() as db:
            test_session = DataSession(
                id=str(uuid4()),
                session_name="Test Session",
                filename="test.csv",
                file_hash="abc123",
                format_version="v1.0",
                field_count=37,
                total_records=100,
            )
            db.add(test_session)
            db.flush()

            # Add quality check
            quality_check = DataQualityCheck(
                session_id=test_session.id,
                check_type="range_check",
                status="passed",
                severity="info",
                message="All values within range",
                error_percentage=0.0,
            )
            db.add(quality_check)
            db.commit()

            # Retrieve quality info
            quality_info = db_instance.get_session_quality(test_session.id)
            assert quality_info["session_id"] == test_session.id
            assert len(quality_info["checks"]) == 1
            assert quality_info["checks"][0]["check_type"] == "range_check"

    def test_export_session_data_csv(self, db_instance):
        """Test exporting session data to CSV."""
        # Create test session and data
        with db_instance.get_session() as db:
            test_session = DataSession(
                id=str(uuid4()),
                session_name="Export Test",
                filename="test.csv",
                file_hash="def456",
                format_version="v1.0",
                field_count=37,
                total_records=1,
            )
            db.add(test_session)
            db.flush()

            # Add test data
            core_data = FuelTechCoreData(session_id=test_session.id, time=0.0, rpm=800, tps=10.5)
            db.add(core_data)
            db.commit()

            # Export to temporary file
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
                export_path = tmp_file.name

            try:
                db_instance.export_session_data(test_session.id, export_path, format="csv")

                # Verify export file exists and has content
                assert os.path.exists(export_path)

                # Read and verify content
                exported_df = pd.read_csv(export_path)
                assert len(exported_df) == 1
                assert exported_df.iloc[0]["rpm"] == 800

            finally:
                if os.path.exists(export_path):
                    os.unlink(export_path)

    def test_delete_session(self, db_instance):
        """Test deleting a session."""
        # Create test session
        with db_instance.get_session() as db:
            test_session = DataSession(
                id=str(uuid4()),
                session_name="Delete Test",
                filename="test.csv",
                file_hash="ghi789",
                format_version="v1.0",
                field_count=37,
                total_records=0,
            )
            db.add(test_session)
            db.commit()
            session_id = test_session.id

        # Delete without confirmation should fail
        result = db_instance.delete_session(session_id, confirm=False)
        assert result is False

        # Delete with confirmation should succeed
        result = db_instance.delete_session(session_id, confirm=True)
        assert result is True

        # Session should no longer exist
        with db_instance.get_session() as db:
            deleted_session = db.query(DataSession).filter(DataSession.id == session_id).first()
            assert deleted_session is None

    def test_delete_nonexistent_session(self, db_instance):
        """Test deleting a non-existent session."""
        fake_id = str(uuid4())
        result = db_instance.delete_session(fake_id, confirm=True)
        assert result is False

    def test_get_database_stats(self, db_instance):
        """Test retrieving database statistics."""
        stats = db_instance.get_database_stats()

        # Check structure
        assert "sessions" in stats
        assert "records" in stats
        assert "quality" in stats
        assert "database" in stats

        # Initially should be all zeros
        assert stats["sessions"]["total"] == 0
        assert stats["records"]["core_data"] == 0
        assert stats["quality"]["total_checks"] == 0

        # Check database info
        assert stats["database"]["file_path"] == str(db_instance.db_path)
        assert stats["database"]["size_mb"] >= 0

    def test_insert_data_records_core_only(self, db_instance, sample_csv_data_v1):
        """Test inserting core data records only."""
        # Create test session
        with db_instance.get_session() as db:
            test_session = DataSession(
                id=str(uuid4()),
                session_name="Insert Test",
                filename="test.csv",
                file_hash="jkl012",
                format_version="v1.0",
                field_count=37,
                total_records=len(sample_csv_data_v1),
            )
            db.add(test_session)
            db.commit()
            session_id = test_session.id

        # Insert data
        db_instance._insert_data_records(sample_csv_data_v1, session_id, "v1.0")

        # Verify data was inserted
        with db_instance.get_session() as db:
            count = (
                db.query(FuelTechCoreData).filter(FuelTechCoreData.session_id == session_id).count()
            )
            assert count == len(sample_csv_data_v1)

    def test_insert_quality_results(self, db_instance):
        """Test inserting quality assessment results."""
        # Create test session
        with db_instance.get_session() as db:
            test_session = DataSession(
                id=str(uuid4()),
                session_name="Quality Test",
                filename="test.csv",
                file_hash="mno345",
                format_version="v1.0",
                field_count=37,
                total_records=100,
            )
            db.add(test_session)
            db.commit()
            session_id = test_session.id

        # Mock quality results
        quality_results = {
            "detailed_results": [
                {
                    "check_name": "range_check",
                    "status": "passed",
                    "severity": "info",
                    "message": "All values within range",
                    "error_percentage": 0.0,
                    "details": {"min_val": 0, "max_val": 100},
                }
            ]
        }

        # Insert quality results
        db_instance._insert_quality_results(quality_results, session_id)

        # Verify results were inserted
        with db_instance.get_session() as db:
            count = (
                db.query(DataQualityCheck).filter(DataQualityCheck.session_id == session_id).count()
            )
            assert count == 1


class TestGlobalDatabaseInstance:
    """Test the global database instance functionality."""

    def test_get_database_singleton(self):
        """Test that get_database returns singleton instance."""
        db1 = get_database(":memory:")
        db2 = get_database(":memory:")

        # Should be the same instance
        assert db1 is db2

    def test_get_database_different_path(self):
        """Test that different paths create different instances."""
        db1 = get_database(":memory:")
        db2 = get_database("test.db")

        # Should be different instances
        assert db1 is not db2


class TestDatabaseManagerIntegration:
    """Integration tests with DatabaseManager from models.py."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file."""
        temp_fd, temp_path = tempfile.mkstemp(suffix=".db")
        os.close(temp_fd)
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_database_manager_integration(self, temp_db_path):
        """Test that FuelTechDatabase properly integrates with DatabaseManager."""
        db = FuelTechDatabase(temp_db_path)

        # Should have initialized db_manager
        assert db.db_manager is not None
        assert db.db_manager.database_url == f"sqlite:///{Path(temp_db_path).absolute()}"

        # Should be able to create session
        with db.get_session() as session:
            assert session is not None

    def test_bulk_operations(self, temp_db_path):
        """Test bulk data operations work correctly."""
        db = FuelTechDatabase(temp_db_path)

        # Create test session
        session_record = db.db_manager.create_session_record(
            session_name="Bulk Test",
            filename="bulk.csv",
            file_hash="bulk123",
            format_version="v1.0",
            field_count=37,
            total_records=100,
        )

        # Prepare bulk data
        bulk_data = []
        for i in range(10):
            bulk_data.append({"time": i * 0.1, "rpm": 800 + i * 100, "tps": 10.0 + i * 2.0})

        # Insert bulk data
        db.db_manager.bulk_insert_core_data(session_record.id, bulk_data)

        # Verify data was inserted
        with db.get_session() as session:
            count = (
                session.query(FuelTechCoreData)
                .filter(FuelTechCoreData.session_id == session_record.id)
                .count()
            )
            assert count == 10


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file."""
        temp_fd, temp_path = tempfile.mkstemp(suffix=".db")
        os.close(temp_fd)
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        # Try to connect to invalid database URL
        with patch("src.data.models.create_engine") as mock_engine:
            mock_engine.side_effect = SQLAlchemyError("Connection failed")

            with pytest.raises(DatabaseError):
                db = FuelTechDatabase("invalid://database")

    def test_transaction_rollback(self, temp_db_path):
        """Test that failed transactions are properly rolled back."""
        db = FuelTechDatabase(temp_db_path)

        # Force a transaction error by inserting invalid data
        with pytest.raises(Exception):
            with db.get_session() as session:
                # Create session with invalid data that should fail constraints
                invalid_session = DataSession(
                    session_name="Test",
                    filename="test.csv",
                    file_hash="abc123",
                    format_version="invalid_version",  # Should fail constraint
                    field_count=37,
                    total_records=0,
                )
                session.add(invalid_session)
                session.commit()

        # Verify no data was committed
        with db.get_session() as session:
            count = session.query(DataSession).count()
            assert count == 0
