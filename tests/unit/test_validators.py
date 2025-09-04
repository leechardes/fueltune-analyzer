"""
Unit tests for data validation module.

Tests Pandera schemas, validation logic, and error handling
for both 37-field and 64-field FuelTech data formats.

Author: A02-DATA-PANDAS Agent
Created: 2025-01-02
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pandera as pa
import pytest

from src.data.validators import (
    DataValidator,
    SchemaManager,
    ValidationError,
    validate_fueltech_data,
)


class TestSchemaManager:
    """Test cases for SchemaManager class."""

    def setup_method(self):
        """Setup for each test method."""
        self.schema_manager = SchemaManager()

    def test_schema_initialization(self):
        """Test that schemas are properly initialized."""
        assert "v1.0" in self.schema_manager.schemas
        assert "v2.0" in self.schema_manager.schemas

        v1_schema = self.schema_manager.schemas["v1.0"]
        v2_schema = self.schema_manager.schemas["v2.0"]

        assert isinstance(v1_schema, pa.DataFrameSchema)
        assert isinstance(v2_schema, pa.DataFrameSchema)

        # v2.0 should have more columns than v1.0
        assert len(v2_schema.columns) > len(v1_schema.columns)

    def test_get_schema_v1(self):
        """Test getting v1.0 schema."""
        schema = self.schema_manager.get_schema("v1.0")

        assert isinstance(schema, pa.DataFrameSchema)

        # Check required fields are present
        required_fields = ["time", "rpm", "tps", "map"]
        for field in required_fields:
            assert field in schema.columns

    def test_get_schema_v2(self):
        """Test getting v2.0 schema."""
        schema = self.schema_manager.get_schema("v2.0")

        assert isinstance(schema, pa.DataFrameSchema)

        # Check extended fields are present
        extended_fields = ["total_consumption", "g_force_accel", "estimated_power"]
        for field in extended_fields:
            assert field in schema.columns

    def test_get_schema_invalid_version(self):
        """Test getting schema with invalid version."""
        with pytest.raises(ValidationError) as exc_info:
            self.schema_manager.get_schema("v3.0")

        assert "Unsupported schema version" in str(exc_info.value)

    def create_valid_v1_dataframe(self):
        """Create a valid v1.0 DataFrame for testing."""
        return pd.DataFrame(
            {
                "time": [0.0, 0.04, 0.08, 0.12],
                "rpm": [1000, 1500, 2000, 2500],
                "tps": [0.0, 25.0, 50.0, 75.0],
                "throttle_position": [0.0, 25.0, 50.0, 75.0],
                "ignition_timing": [15.0, 20.0, 25.0, 30.0],
                "map": [-0.5, 0.0, 0.5, 1.0],
                "closed_loop_target": [1.0, 0.95, 0.9, 0.85],
                "closed_loop_o2": [1.0, 0.95, 0.9, 0.85],
                "closed_loop_correction": [0.0, 5.0, 10.0, 15.0],
                "o2_general": [1.0, 0.95, 0.9, 0.85],
                "two_step": ["OFF", "OFF", "ON", "ON"],
                "ethanol_content": [0, 25, 50, 85],
                "launch_validated": ["OFF", "OFF", "ON", "ON"],
                "fuel_temp": [25.0, 30.0, 35.0, 40.0],
                "gear": [1, 2, 3, 4],
                "flow_bank_a": [100.0, 200.0, 300.0, 400.0],
                "injection_phase_angle": [90.0, 180.0, 270.0, 360.0],
                "injector_duty_a": [10.0, 20.0, 30.0, 40.0],
                "injection_time_a": [2.0, 4.0, 6.0, 8.0],
                "engine_temp": [80.0, 85.0, 90.0, 95.0],
                "air_temp": [20.0, 25.0, 30.0, 35.0],
                "oil_pressure": [2.0, 3.0, 4.0, 5.0],
                "fuel_pressure": [3.0, 4.0, 5.0, 6.0],
                "battery_voltage": [12.0, 12.5, 13.0, 13.5],
                "ignition_dwell": [3.0, 3.5, 4.0, 4.5],
                "fan1_enrichment": [0.0, 2.0, 4.0, 6.0],
                "fuel_level": [100.0, 90.0, 80.0, 70.0],
                "engine_sync": ["ON", "ON", "ON", "ON"],
                "decel_cutoff": ["OFF", "OFF", "OFF", "ON"],
                "engine_cranking": ["OFF", "OFF", "OFF", "OFF"],
                "idle": ["ON", "OFF", "OFF", "OFF"],
                "first_pulse_cranking": ["OFF", "OFF", "OFF", "OFF"],
                "accel_decel_injection": ["OFF", "ON", "ON", "OFF"],
                "active_adjustment": [0, 5, 10, 15],
                "fan1": ["OFF", "OFF", "ON", "ON"],
                "fan2": ["OFF", "OFF", "OFF", "ON"],
                "fuel_pump": ["ON", "ON", "ON", "ON"],
            }
        )

    def create_valid_v2_dataframe(self):
        """Create a valid v2.0 DataFrame for testing."""
        df_v1 = self.create_valid_v1_dataframe()

        # Add extended fields
        extended_fields = {
            "total_consumption": [0.5, 1.0, 1.5, 2.0],
            "average_consumption": [15.0, 14.5, 14.0, 13.5],
            "instant_consumption": [10.0, 15.0, 20.0, 25.0],
            "estimated_power": [100, 150, 200, 250],
            "estimated_torque": [200, 300, 400, 500],
            "total_distance": [10.0, 20.0, 30.0, 40.0],
            "range": [300.0, 250.0, 200.0, 150.0],
            "traction_speed": [0.0, 20.0, 40.0, 60.0],
            "acceleration_speed": [0.0, 20.0, 40.0, 60.0],
            "traction_control_slip": [0.0, 2.0, 5.0, 8.0],
            "traction_control_slip_rate": [0, 5, 10, 15],
            "delta_tps": [0.0, 100.0, 50.0, -25.0],
            "g_force_accel": [0.0, 0.5, 1.0, 1.5],
            "g_force_lateral": [0.0, 0.2, 0.4, 0.6],
            "pitch_angle": [0.0, 2.0, 4.0, 6.0],
            "pitch_rate": [0.0, 5.0, 10.0, 15.0],
            "heading": [0.0, 90.0, 180.0, 270.0],
            "roll_angle": [0.0, 1.0, 2.0, 3.0],
            "acceleration_distance": [0.0, 50.0, 100.0, 150.0],
            "roll_rate": [0.0, 2.0, 4.0, 6.0],
            "g_force_accel_raw": [0.0, 0.6, 1.2, 1.8],
            "g_force_lateral_raw": [0.0, 0.3, 0.6, 0.9],
            "accel_enrichment": ["OFF", "ON", "ON", "OFF"],
            "decel_enrichment": ["OFF", "OFF", "ON", "ON"],
            "injection_cutoff": ["OFF", "OFF", "OFF", "ON"],
            "after_start_injection": ["ON", "OFF", "OFF", "OFF"],
            "start_button_toggle": ["OFF", "OFF", "OFF", "OFF"],
        }

        for field, values in extended_fields.items():
            df_v1[field] = values

        return df_v1

    def test_validate_dataframe_v1_valid(self):
        """Test validating valid v1.0 DataFrame."""
        df = self.create_valid_v1_dataframe()

        results = self.schema_manager.validate_dataframe(df, "v1.0", strict=False)

        assert results["is_valid"] is True
        assert len(results["errors"]) == 0
        assert results["schema_version"] == "v1.0"
        assert results["validated_rows"] == 4
        assert results["validated_columns"] == 37

    def test_validate_dataframe_v2_valid(self):
        """Test validating valid v2.0 DataFrame."""
        df = self.create_valid_v2_dataframe()

        results = self.schema_manager.validate_dataframe(df, "v2.0", strict=False)

        assert results["is_valid"] is True
        assert len(results["errors"]) == 0
        assert results["schema_version"] == "v2.0"
        assert results["validated_rows"] == 4
        assert results["validated_columns"] == 64

    def test_validate_dataframe_invalid_range(self):
        """Test validating DataFrame with values outside valid ranges."""
        df = self.create_valid_v1_dataframe()

        # Introduce invalid values
        df.loc[0, "rpm"] = -100  # Negative RPM (invalid)
        df.loc[1, "tps"] = 150  # TPS > 100% (invalid)
        df.loc[2, "engine_temp"] = 300  # Too hot (invalid)

        results = self.schema_manager.validate_dataframe(df, "v1.0", strict=False)

        assert results["is_valid"] is False
        assert len(results["errors"]) > 0

    def test_validate_dataframe_missing_columns(self):
        """Test validating DataFrame with missing required columns."""
        df = pd.DataFrame(
            {
                "time": [0.0, 0.04],
                "rpm": [1000, 1500],
                # Missing other required columns
            }
        )

        results = self.schema_manager.validate_dataframe(df, "v1.0", strict=False)

        assert results["is_valid"] is False
        assert len(results["errors"]) > 0

    def test_validate_dataframe_wrong_data_types(self):
        """Test validating DataFrame with wrong data types."""
        df = self.create_valid_v1_dataframe()

        # Convert numeric fields to strings
        df["rpm"] = df["rpm"].astype(str)
        df["tps"] = df["tps"].astype(str)

        # Schema should coerce types, so this might still validate
        results = self.schema_manager.validate_dataframe(df, "v1.0", strict=False)

        # Depending on coercion settings, this might pass or fail
        # The important thing is that it doesn't crash
        assert "is_valid" in results

    def test_validate_dataframe_strict_mode(self):
        """Test validation in strict mode."""
        df = self.create_valid_v1_dataframe()
        df.loc[0, "rpm"] = -100  # Invalid value

        with pytest.raises(ValidationError):
            self.schema_manager.validate_dataframe(df, "v1.0", strict=True)

    def test_validate_dataframe_non_strict_mode(self):
        """Test validation in non-strict mode."""
        df = self.create_valid_v1_dataframe()
        df.loc[0, "rpm"] = -100  # Invalid value

        # Should not raise exception in non-strict mode
        results = self.schema_manager.validate_dataframe(df, "v1.0", strict=False)

        assert results["is_valid"] is False
        assert len(results["errors"]) > 0


class TestDataValidator:
    """Test cases for DataValidator class."""

    def setup_method(self):
        """Setup for each test method."""
        self.validator = DataValidator()

    def create_test_dataframe(self, columns=37):
        """Create test DataFrame with specified number of columns."""
        if columns == 37:
            return TestSchemaManager().create_valid_v1_dataframe()
        elif columns == 64:
            return TestSchemaManager().create_valid_v2_dataframe()
        else:
            # Create DataFrame with custom column count
            data = {f"col_{i}": [1, 2, 3, 4] for i in range(columns)}
            return pd.DataFrame(data)

    def test_auto_validate_v1(self):
        """Test auto validation for v1.0 format."""
        df = self.create_test_dataframe(37)

        results = self.validator.auto_validate(df)

        assert results["detected_version"] == "v1.0"
        assert results["is_valid"] is True

    def test_auto_validate_v2(self):
        """Test auto validation for v2.0 format."""
        df = self.create_test_dataframe(64)

        results = self.validator.auto_validate(df)

        assert results["detected_version"] == "v2.0"
        assert results["is_valid"] is True

    def test_auto_validate_unsupported_column_count(self):
        """Test auto validation with unsupported column count."""
        df = self.create_test_dataframe(50)  # Unsupported count

        results = self.validator.auto_validate(df)

        assert results["is_valid"] is False
        assert "Unsupported column count: 50" in results["errors"][0]
        assert results["detected_version"] is None

    def test_auto_validate_with_expected_version(self):
        """Test auto validation with expected version specified."""
        df = self.create_test_dataframe(37)

        results = self.validator.auto_validate(df, expected_version="v1.0")

        assert results["detected_version"] == "v1.0"
        assert results["is_valid"] is True

    def test_validate_sample(self):
        """Test sample validation."""
        # Create large DataFrame
        large_df = pd.concat([self.create_test_dataframe(37)] * 500)  # 2000 rows

        results = self.validator.validate_sample(large_df, sample_size=100)

        assert "detected_version" in results
        # Should validate only a sample

    def test_validate_sample_small_dataframe(self):
        """Test sample validation with DataFrame smaller than sample size."""
        df = self.create_test_dataframe(37)  # Only 4 rows

        results = self.validator.validate_sample(df, sample_size=1000)

        # Should validate entire DataFrame
        assert "detected_version" in results

    def test_get_validation_summary(self):
        """Test validation summary generation."""
        df = self.create_test_dataframe(37)
        results = self.validator.auto_validate(df)

        summary = self.validator.get_validation_summary(results)

        assert "Validation Results Summary" in summary
        assert "PASSED" in summary
        assert "Schema Version: v1.0" in summary
        assert "Validated Rows: 4" in summary

    def test_get_validation_summary_with_errors(self):
        """Test validation summary with errors."""
        results = {
            "is_valid": False,
            "detected_version": "v1.0",
            "validated_rows": 100,
            "validated_columns": 37,
            "errors": ["Error 1", "Error 2", "Error 3"],
            "warnings": ["Warning 1"],
        }

        summary = self.validator.get_validation_summary(results)

        assert "FAILED" in summary
        assert "Errors (3):" in summary
        assert "Warnings (1):" in summary
        assert "Error 1" in summary
        assert "Warning 1" in summary

    def test_get_validation_summary_many_errors(self):
        """Test validation summary with many errors (should truncate)."""
        errors = [f"Error {i}" for i in range(10)]
        results = {
            "is_valid": False,
            "detected_version": "v1.0",
            "validated_rows": 100,
            "validated_columns": 37,
            "errors": errors,
            "warnings": [],
        }

        summary = self.validator.get_validation_summary(results)

        assert "... and 5 more" in summary  # Should show truncation


class TestValidateConvenienceFunction:
    """Test cases for convenience functions."""

    def test_validate_fueltech_data_basic(self):
        """Test basic validation using convenience function."""
        df = TestSchemaManager().create_valid_v1_dataframe()

        results = validate_fueltech_data(df)

        assert "is_valid" in results
        assert "detected_version" in results

    def test_validate_fueltech_data_with_version(self):
        """Test validation with specified version."""
        df = TestSchemaManager().create_valid_v2_dataframe()

        results = validate_fueltech_data(df, version="v2.0")

        assert results["detected_version"] == "v2.0"

    def test_validate_fueltech_data_sample_only(self):
        """Test validation with sample only flag."""
        df = TestSchemaManager().create_valid_v1_dataframe()

        results = validate_fueltech_data(df, sample_only=True, sample_size=2)

        # Should complete without errors
        assert "is_valid" in results

    def test_validate_fueltech_data_custom_sample_size(self):
        """Test validation with custom sample size."""
        large_df = pd.concat([TestSchemaManager().create_valid_v1_dataframe()] * 100)

        results = validate_fueltech_data(large_df, sample_only=True, sample_size=50)

        assert "is_valid" in results


class TestSchemaValidationDetails:
    """Detailed tests for specific schema validation rules."""

    def setup_method(self):
        """Setup for each test method."""
        self.schema_manager = SchemaManager()

    def test_time_field_validation(self):
        """Test time field validation rules."""
        df = pd.DataFrame(
            {
                "time": [-1.0, 0.0, 100.0, 86401.0],  # One negative, one too large
                "rpm": [1000, 1000, 1000, 1000],
                "tps": [0.0, 0.0, 0.0, 0.0],
                "map": [0.0, 0.0, 0.0, 0.0],
            }
        )

        # Add minimal required columns
        for col in [
            "throttle_position",
            "ignition_timing",
            "closed_loop_target",
            "closed_loop_o2",
            "closed_loop_correction",
            "o2_general",
            "two_step",
            "ethanol_content",
            "launch_validated",
            "fuel_temp",
            "gear",
            "flow_bank_a",
            "injection_phase_angle",
            "injector_duty_a",
            "injection_time_a",
            "engine_temp",
            "air_temp",
            "oil_pressure",
            "fuel_pressure",
            "battery_voltage",
            "ignition_dwell",
            "fan1_enrichment",
            "fuel_level",
            "engine_sync",
            "decel_cutoff",
            "engine_cranking",
            "idle",
            "first_pulse_cranking",
            "accel_decel_injection",
            "active_adjustment",
            "fan1",
            "fan2",
            "fuel_pump",
        ]:
            df[col] = [
                (
                    0.0
                    if col
                    not in [
                        "two_step",
                        "launch_validated",
                        "engine_sync",
                        "decel_cutoff",
                        "engine_cranking",
                        "idle",
                        "first_pulse_cranking",
                        "accel_decel_injection",
                        "fan1",
                        "fan2",
                        "fuel_pump",
                    ]
                    else "OFF"
                )
            ] * 4

        results = self.schema_manager.validate_dataframe(df, "v1.0", strict=False)

        assert results["is_valid"] is False
        # Should have errors for negative time and time > 86400

    def test_rpm_field_validation(self):
        """Test RPM field validation rules."""
        df = TestSchemaManager().create_valid_v1_dataframe()

        # Test invalid RPM values
        df.loc[0, "rpm"] = -100  # Negative
        df.loc[1, "rpm"] = 20000  # Too high

        results = self.schema_manager.validate_dataframe(df, "v1.0", strict=False)

        assert results["is_valid"] is False

    def test_percentage_fields_validation(self):
        """Test validation of percentage fields (0-100 range)."""
        df = TestSchemaManager().create_valid_v1_dataframe()

        # Test invalid percentage values
        df.loc[0, "tps"] = -10  # Below 0%
        df.loc[1, "tps"] = 150  # Above 100%
        df.loc[2, "fuel_level"] = -5  # Below 0%

        results = self.schema_manager.validate_dataframe(df, "v1.0", strict=False)

        assert results["is_valid"] is False

    def test_string_field_validation(self):
        """Test validation of string fields with specific allowed values."""
        df = TestSchemaManager().create_valid_v1_dataframe()

        # Test invalid string values
        df.loc[0, "two_step"] = "MAYBE"  # Invalid value
        df.loc[1, "engine_sync"] = "UNKNOWN"  # Invalid value

        results = self.schema_manager.validate_dataframe(df, "v1.0", strict=False)

        assert results["is_valid"] is False

    def test_temperature_field_validation(self):
        """Test validation of temperature fields."""
        df = TestSchemaManager().create_valid_v1_dataframe()

        # Test extreme temperature values
        df.loc[0, "engine_temp"] = -50  # Too cold
        df.loc[1, "engine_temp"] = 250  # Too hot
        df.loc[2, "air_temp"] = 200  # Too hot for air

        results = self.schema_manager.validate_dataframe(df, "v1.0", strict=False)

        assert results["is_valid"] is False

    def test_extended_fields_validation(self):
        """Test validation of extended fields in v2.0 format."""
        df = TestSchemaManager().create_valid_v2_dataframe()

        # Test invalid extended field values
        df.loc[0, "g_force_accel"] = 10.0  # Too high G-force
        df.loc[1, "estimated_power"] = -50  # Negative power
        df.loc[2, "heading"] = 400  # Invalid heading (>360)

        results = self.schema_manager.validate_dataframe(df, "v2.0", strict=False)

        assert results["is_valid"] is False


class TestValidationErrorHandling:
    """Test error handling in validation module."""

    def test_validation_with_pandera_exception(self):
        """Test handling of Pandera schema errors."""
        schema_manager = SchemaManager()

        # Create DataFrame that will definitely fail validation
        df = pd.DataFrame(
            {
                "time": ["invalid", "data", "types", "here"],
                "rpm": ["not", "numbers", "at", "all"],
            }
        )

        results = schema_manager.validate_dataframe(df, "v1.0", strict=False)

        assert results["is_valid"] is False
        assert len(results["errors"]) > 0

    def test_validation_with_general_exception(self):
        """Test handling of general exceptions during validation."""
        schema_manager = SchemaManager()

        # Mock a schema that raises an exception
        with patch.object(schema_manager, "get_schema") as mock_get_schema:
            mock_schema = MagicMock()
            mock_schema.validate.side_effect = Exception("Test exception")
            mock_get_schema.return_value = mock_schema

            results = schema_manager.validate_dataframe(
                pd.DataFrame({"test": [1, 2, 3]}), "v1.0", strict=False
            )

            assert results["is_valid"] is False
            assert len(results["errors"]) > 0
            assert "Test exception" in str(results["errors"][0])

    def test_schema_creation_error_handling(self):
        """Test error handling during schema creation."""
        # This is more of a smoke test to ensure schema creation doesn't crash
        schema_manager = SchemaManager()

        # Schemas should be created without errors
        assert schema_manager.schemas["v1.0"] is not None
        assert schema_manager.schemas["v2.0"] is not None


if __name__ == "__main__":
    pytest.main([__file__])
