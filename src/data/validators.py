"""
Data validation schemas using Pandera for FuelTech data.

Provides comprehensive validation schemas for both 37-field and 64-field
FuelTech formats with domain-specific constraints and quality checks.

Author: A02-DATA-PANDAS Agent
Created: 2025-01-02
"""

from typing import Any, Dict, Optional

import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Exception raised when data validation fails."""


class SchemaManager:
    """
    Manager class for validation schemas.
    Handles schema selection and validation execution.
    """

    def __init__(self):
        """Initialize schema manager."""
        self.schemas = {
            "v1.0": self._create_v1_schema(),
            "v2.0": self._create_v2_schema(),
        }

    def _create_v1_schema(self) -> DataFrameSchema:
        """Create validation schema for v1.0 (37 fields) format."""
        return DataFrameSchema(
            columns={
                # Core timing and engine data
                "time": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(86400),  # Max 24 hours
                    ],
                    nullable=False,
                    description="Time in seconds from session start",
                ),
                "rpm": Column(
                    dtype="int64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(15000),
                    ],
                    nullable=False,
                    description="Engine RPM",
                ),
                "tps": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(100),
                    ],
                    nullable=True,
                    description="Throttle Position Sensor (%)",
                ),
                "throttle_position": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(100),
                    ],
                    nullable=True,
                    description="Physical throttle position",
                ),
                "ignition_timing": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(-45),  # Max retard
                        Check.less_than_or_equal_to(60),  # Max advance
                    ],
                    nullable=True,
                    description="Ignition timing in degrees",
                ),
                "map": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(-1.5),  # Deep vacuum
                        Check.less_than_or_equal_to(5.0),  # Max boost
                    ],
                    nullable=True,
                    description="Manifold Absolute Pressure (bar)",
                ),
                # Lambda and fuel system
                "closed_loop_target": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0.5),
                        Check.less_than_or_equal_to(1.5),
                    ],
                    nullable=True,
                    description="Closed loop lambda target",
                ),
                "closed_loop_o2": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0.5),
                        Check.less_than_or_equal_to(1.5),
                    ],
                    nullable=True,
                    description="Closed loop O2 sensor reading",
                ),
                "closed_loop_correction": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(-50),
                        Check.less_than_or_equal_to(50),
                    ],
                    nullable=True,
                    description="Closed loop correction percentage",
                ),
                "o2_general": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0.5),
                        Check.less_than_or_equal_to(1.5),
                    ],
                    nullable=True,
                    description="General O2 sensor reading",
                ),
                "ethanol_content": Column(
                    dtype="int64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(100),
                    ],
                    nullable=True,
                    description="Ethanol content percentage",
                ),
                # Engine control status
                "two_step": Column(
                    dtype="string",
                    checks=[Check.isin(["ON", "OFF", ""])],
                    nullable=True,
                    description="Two-step rev limiter status",
                ),
                "launch_validated": Column(
                    dtype="string",
                    checks=[Check.isin(["ON", "OFF", ""])],
                    nullable=True,
                    description="Launch control validation status",
                ),
                "gear": Column(
                    dtype="int64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(8),
                    ],
                    nullable=True,
                    description="Current gear",
                ),
                # Fuel system
                "fuel_temp": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(-40),
                        Check.less_than_or_equal_to(150),
                    ],
                    nullable=True,
                    description="Fuel temperature (°C)",
                ),
                "flow_bank_a": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(10000),
                    ],
                    nullable=True,
                    description="Flow bank A (cc/min)",
                ),
                "injection_phase_angle": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(720),
                    ],
                    nullable=True,
                    description="Injection phase angle (degrees)",
                ),
                "injector_duty_a": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(100),
                    ],
                    nullable=True,
                    description="Injector duty cycle A (%)",
                ),
                "injection_time_a": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(100),
                    ],
                    nullable=True,
                    description="Injection time bank A (ms)",
                ),
                "fuel_pressure": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(10),
                    ],
                    nullable=True,
                    description="Fuel pressure (bar)",
                ),
                "fuel_level": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(100),
                    ],
                    nullable=True,
                    description="Fuel level (%)",
                ),
                # Temperature monitoring
                "engine_temp": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(-40),
                        Check.less_than_or_equal_to(200),
                    ],
                    nullable=True,
                    description="Engine coolant temperature (°C)",
                ),
                "air_temp": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(-40),
                        Check.less_than_or_equal_to(150),
                    ],
                    nullable=True,
                    description="Intake air temperature (°C)",
                ),
                # Electrical and auxiliary
                "oil_pressure": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(10),
                    ],
                    nullable=True,
                    description="Oil pressure (bar)",
                ),
                "battery_voltage": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(8),
                        Check.less_than_or_equal_to(18),
                    ],
                    nullable=True,
                    description="Battery voltage (V)",
                ),
                "ignition_dwell": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(0),
                        Check.less_than_or_equal_to(20),
                    ],
                    nullable=True,
                    description="Ignition dwell time (ms)",
                ),
                "fan1_enrichment": Column(
                    dtype="float64",
                    checks=[
                        Check.greater_than_or_equal_to(-50),
                        Check.less_than_or_equal_to(50),
                    ],
                    nullable=True,
                    description="Fan 1 enrichment (%)",
                ),
                # Status flags (boolean as string)
                "engine_sync": Column(
                    dtype="string",
                    checks=[Check.isin(["ON", "OFF", ""])],
                    nullable=True,
                    description="Engine synchronization status",
                ),
                "decel_cutoff": Column(
                    dtype="string",
                    checks=[Check.isin(["ON", "OFF", ""])],
                    nullable=True,
                    description="Deceleration fuel cutoff status",
                ),
                "engine_cranking": Column(
                    dtype="string",
                    checks=[Check.isin(["ON", "OFF", ""])],
                    nullable=True,
                    description="Engine cranking status",
                ),
                "idle": Column(
                    dtype="string",
                    checks=[Check.isin(["ON", "OFF", ""])],
                    nullable=True,
                    description="Idle status",
                ),
                "first_pulse_cranking": Column(
                    dtype="string",
                    checks=[Check.isin(["ON", "OFF", ""])],
                    nullable=True,
                    description="First pulse cranking status",
                ),
                "accel_decel_injection": Column(
                    dtype="string",
                    checks=[Check.isin(["ON", "OFF", ""])],
                    nullable=True,
                    description="Acceleration/deceleration injection status",
                ),
                # Control outputs
                "active_adjustment": Column(
                    dtype="int64",
                    checks=[
                        Check.greater_than_or_equal_to(-100),
                        Check.less_than_or_equal_to(100),
                    ],
                    nullable=True,
                    description="Active adjustment (%)",
                ),
                "fan1": Column(
                    dtype="string",
                    checks=[Check.isin(["ON", "OFF", ""])],
                    nullable=True,
                    description="Fan 1 status",
                ),
                "fan2": Column(
                    dtype="string",
                    checks=[Check.isin(["ON", "OFF", ""])],
                    nullable=True,
                    description="Fan 2 status",
                ),
                "fuel_pump": Column(
                    dtype="string",
                    checks=[Check.isin(["ON", "OFF", ""])],
                    nullable=True,
                    description="Fuel pump status",
                ),
            },
            strict=True,
            coerce=True,
            description="FuelTech v1.0 (37 fields) validation schema",
        )

    def _create_v2_schema(self) -> DataFrameSchema:
        """Create validation schema for v2.0 (64 fields) format."""
        # Start with v1.0 schema and add extended fields
        base_schema = self._create_v1_schema()

        extended_columns = {
            # Consumption and efficiency
            "total_consumption": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(1000),
                ],
                nullable=True,
                description="Total fuel consumption (L)",
            ),
            "average_consumption": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(50),
                ],
                nullable=True,
                description="Average fuel consumption (km/L)",
            ),
            "instant_consumption": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(500),
                ],
                nullable=True,
                description="Instantaneous fuel consumption (L/h)",
            ),
            "total_distance": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(10000),
                ],
                nullable=True,
                description="Total distance traveled (km)",
            ),
            "range": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(2000),
                ],
                nullable=True,
                description="Estimated range (km)",
            ),
            # Performance metrics
            "estimated_power": Column(
                dtype="int64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(2000),
                ],
                nullable=True,
                description="Estimated engine power (HP)",
            ),
            "estimated_torque": Column(
                dtype="int64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(5000),
                ],
                nullable=True,
                description="Estimated engine torque (Nm)",
            ),
            "traction_speed": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(400),
                ],
                nullable=True,
                description="Traction speed (km/h)",
            ),
            "acceleration_speed": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(400),
                ],
                nullable=True,
                description="Acceleration speed (km/h)",
            ),
            "acceleration_distance": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(10000),
                ],
                nullable=True,
                description="Acceleration distance (m)",
            ),
            # Traction control
            "traction_control_slip": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(100),
                ],
                nullable=True,
                description="Traction control slip (%)",
            ),
            "traction_control_slip_rate": Column(
                dtype="int64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(100),
                ],
                nullable=True,
                description="Traction control slip rate (%)",
            ),
            "delta_tps": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(-500),
                    Check.less_than_or_equal_to(500),
                ],
                nullable=True,
                description="TPS rate of change (%/s)",
            ),
            # IMU and dynamics
            "g_force_accel": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(-5),
                    Check.less_than_or_equal_to(5),
                ],
                nullable=True,
                description="Longitudinal G-force",
            ),
            "g_force_lateral": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(-5),
                    Check.less_than_or_equal_to(5),
                ],
                nullable=True,
                description="Lateral G-force",
            ),
            "g_force_accel_raw": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(-10),
                    Check.less_than_or_equal_to(10),
                ],
                nullable=True,
                description="Raw longitudinal G-force",
            ),
            "g_force_lateral_raw": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(-10),
                    Check.less_than_or_equal_to(10),
                ],
                nullable=True,
                description="Raw lateral G-force",
            ),
            # Vehicle attitude
            "pitch_angle": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(-90),
                    Check.less_than_or_equal_to(90),
                ],
                nullable=True,
                description="Vehicle pitch angle (degrees)",
            ),
            "pitch_rate": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(-360),
                    Check.less_than_or_equal_to(360),
                ],
                nullable=True,
                description="Pitch rate (degrees/s)",
            ),
            "roll_angle": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(-180),
                    Check.less_than_or_equal_to(180),
                ],
                nullable=True,
                description="Vehicle roll angle (degrees)",
            ),
            "roll_rate": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(-360),
                    Check.less_than_or_equal_to(360),
                ],
                nullable=True,
                description="Roll rate (degrees/s)",
            ),
            "heading": Column(
                dtype="float64",
                checks=[
                    Check.greater_than_or_equal_to(0),
                    Check.less_than_or_equal_to(360),
                ],
                nullable=True,
                description="Vehicle heading (degrees)",
            ),
            # Advanced engine control
            "accel_enrichment": Column(
                dtype="string",
                checks=[Check.isin(["ON", "OFF", ""])],
                nullable=True,
                description="Acceleration enrichment status",
            ),
            "decel_enrichment": Column(
                dtype="string",
                checks=[Check.isin(["ON", "OFF", ""])],
                nullable=True,
                description="Deceleration enrichment status",
            ),
            "injection_cutoff": Column(
                dtype="string",
                checks=[Check.isin(["ON", "OFF", ""])],
                nullable=True,
                description="Injection cutoff status",
            ),
            "after_start_injection": Column(
                dtype="string",
                checks=[Check.isin(["ON", "OFF", ""])],
                nullable=True,
                description="After start injection status",
            ),
            "start_button_toggle": Column(
                dtype="string",
                checks=[Check.isin(["ON", "OFF", ""])],
                nullable=True,
                description="Start button toggle status",
            ),
        }

        # Combine base schema columns with extended columns
        all_columns = {**base_schema.columns, **extended_columns}

        return DataFrameSchema(
            columns=all_columns,
            strict=True,
            coerce=True,
            description="FuelTech v2.0 (64 fields) validation schema",
        )

    def get_schema(self, version: str) -> DataFrameSchema:
        """
        Get validation schema for specified version.

        Args:
            version: Schema version ('v1.0' or 'v2.0')

        Returns:
            Validation schema

        Raises:
            ValidationError: If version not supported
        """
        if version not in self.schemas:
            raise ValidationError(f"Unsupported schema version: {version}")

        return self.schemas[version]

    def validate_dataframe(
        self, df: pd.DataFrame, version: str, strict: bool = True
    ) -> Dict[str, Any]:
        """
        Validate DataFrame against schema.

        Args:
            df: DataFrame to validate
            version: Schema version to use
            strict: Fail on any validation error

        Returns:
            Validation results dictionary

        Raises:
            ValidationError: If strict=True and validation fails
        """
        schema = self.get_schema(version)
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "schema_version": version,
            "validated_rows": len(df),
            "validated_columns": len(df.columns),
        }

        try:
            # Perform validation
            validated_df = schema.validate(df, lazy=not strict)
            results["validated_df"] = validated_df

            logger.info(
                f"DataFrame validation successful: {len(df)} rows, {len(df.columns)} columns"
            )

        except pa.errors.SchemaErrors as e:
            results["is_valid"] = False

            # Parse validation errors from the error dictionary structure
            if hasattr(e, "args") and e.args:
                error_dict = e.args[0]
                if isinstance(error_dict, dict) and "DATA" in error_dict:
                    for error_type, error_list in error_dict["DATA"].items():
                        for error in error_list:
                            if isinstance(error, dict):
                                error_info = {
                                    "column": error.get("column"),
                                    "check": error.get("check"),
                                    "failure_case": error.get("failure_case"),
                                    "index": error.get("index"),
                                    "error": error.get("error", str(error)),
                                    "type": error_type,
                                }
                            else:
                                error_info = {
                                    "column": None,
                                    "check": None,
                                    "failure_case": None,
                                    "index": None,
                                    "error": str(error),
                                    "type": error_type,
                                }
                            results["errors"].append(error_info)
                else:
                    # Fallback for other error structures
                    results["errors"].append(
                        {
                            "column": None,
                            "check": None,
                            "failure_case": None,
                            "index": None,
                            "error": str(e),
                            "type": "UNKNOWN",
                        }
                    )
            else:
                # Simple fallback
                results["errors"].append(
                    {
                        "column": None,
                        "check": None,
                        "failure_case": None,
                        "index": None,
                        "error": str(e),
                        "type": "UNKNOWN",
                    }
                )

            if strict:
                logger.error(f"DataFrame validation failed: {len(results['errors'])} errors")
                raise ValidationError(f"Validation failed with {len(results['errors'])} errors")
            else:
                logger.warning(
                    f"DataFrame validation completed with {len(results['errors'])} errors"
                )

        except Exception as e:
            results["is_valid"] = False
            results["errors"].append({"error": str(e), "type": type(e).__name__})

            if strict:
                logger.error(f"Validation error: {str(e)}")
                raise ValidationError(f"Validation error: {str(e)}")

        return results


class DataValidator:
    """
    High-level data validator for FuelTech data.
    Provides simplified interface for validation operations.
    """

    def __init__(self):
        """Initialize data validator."""
        self.schema_manager = SchemaManager()

    def auto_validate(
        self, df: pd.DataFrame, expected_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Auto-validate DataFrame with version detection.

        Args:
            df: DataFrame to validate
            expected_version: Expected schema version (optional)

        Returns:
            Validation results
        """
        # Determine version based on column count if not provided
        if not expected_version:
            col_count = len(df.columns)
            if col_count == 37:
                expected_version = "v1.0"
            elif col_count == 64:
                expected_version = "v2.0"
            else:
                return {
                    "is_valid": False,
                    "errors": [f"Unsupported column count: {col_count}"],
                    "detected_version": None,
                }

        # Perform validation
        results = self.schema_manager.validate_dataframe(
            df=df, version=expected_version, strict=False
        )

        results["detected_version"] = expected_version
        return results

    def validate_sample(
        self, df: pd.DataFrame, sample_size: int = 1000, version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a sample of the DataFrame for quick checks.

        Args:
            df: DataFrame to validate
            sample_size: Number of rows to sample
            version: Schema version

        Returns:
            Validation results for the sample
        """
        # Sample the data
        if len(df) > sample_size:
            df_sample = df.sample(n=sample_size, random_state=42)
        else:
            df_sample = df.copy()

        return self.auto_validate(df_sample, version)

    def get_validation_summary(self, results: Dict[str, Any]) -> str:
        """
        Generate human-readable validation summary.

        Args:
            results: Validation results dictionary

        Returns:
            Formatted summary string
        """
        summary = []
        summary.append(f"Validation Results Summary")
        summary.append(f"{'='*50}")
        summary.append(f"Status: {'PASSED' if results['is_valid'] else 'FAILED'}")
        summary.append(f"Schema Version: {results.get('detected_version', 'Unknown')}")
        summary.append(f"Validated Rows: {results.get('validated_rows', 0):,}")
        summary.append(f"Validated Columns: {results.get('validated_columns', 0)}")

        if results.get("errors"):
            summary.append(f"\nErrors ({len(results['errors'])}):")
            for i, error in enumerate(results["errors"][:5]):  # Show first 5 errors
                summary.append(f"  {i+1}. {error}")
            if len(results["errors"]) > 5:
                summary.append(f"  ... and {len(results['errors']) - 5} more")

        if results.get("warnings"):
            summary.append(f"\nWarnings ({len(results['warnings'])}):")
            for i, warning in enumerate(results["warnings"][:3]):  # Show first 3 warnings
                summary.append(f"  {i+1}. {warning}")

        return "\n".join(summary)


# Global validator instance
validator = DataValidator()


def validate_fueltech_data(
    df: pd.DataFrame,
    version: Optional[str] = None,
    sample_only: bool = False,
    sample_size: int = 1000,
) -> Dict[str, Any]:
    """
    Convenience function to validate FuelTech data.

    Args:
        df: DataFrame to validate
        version: Schema version ('v1.0' or 'v2.0')
        sample_only: Validate only a sample for performance
        sample_size: Sample size if sample_only=True

    Returns:
        Validation results dictionary
    """
    if sample_only:
        return validator.validate_sample(df, sample_size, version)
    else:
        return validator.auto_validate(df, version)


if __name__ == "__main__":
    # Example usage
    import pandas as pd

    # Create sample data for testing
    sample_data = pd.DataFrame(
        {
            "time": [0.0, 0.04, 0.08],
            "rpm": [1000, 2000, 3000],
            "tps": [0.0, 50.0, 100.0],
            "map": [-0.5, 0.0, 1.5],
            # ... add other required columns
        }
    )

    # Validate the data
    results = validate_fueltech_data(sample_data, version="v1.0")

    print("Validation Results:")
    print(validator.get_validation_summary(results))
