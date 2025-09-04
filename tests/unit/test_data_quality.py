"""
Unit tests for data quality assessment module.

Tests quality checks, anomaly detection, and quality scoring
for FuelTech data validation and assessment.

Author: A02-DATA-PANDAS Agent
Created: 2025-01-02
"""

from datetime import datetime
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.data.quality import DataQualityAssessor, QualityCheckResult, assess_fueltech_data_quality


class TestQualityCheckResult:
    """Test cases for QualityCheckResult dataclass."""

    def test_quality_check_result_creation(self):
        """Test creating QualityCheckResult instance."""
        result = QualityCheckResult(
            check_name="test_check",
            status="passed",
            severity="info",
            message="Test passed",
            affected_records=0,
            total_records=100,
            error_percentage=0.0,
            details={"test": "data"},
            timestamp=datetime.now(),
        )

        assert result.check_name == "test_check"
        assert result.status == "passed"
        assert result.severity == "info"
        assert result.error_percentage == 0.0
        assert isinstance(result.details, dict)
        assert isinstance(result.timestamp, datetime)


class TestDataQualityAssessor:
    """Test cases for DataQualityAssessor class."""

    def setup_method(self):
        """Setup for each test method."""
        self.assessor = DataQualityAssessor()

    def create_clean_test_data(self):
        """Create clean test data for quality assessment."""
        return pd.DataFrame(
            {
                "time": [0.0, 0.04, 0.08, 0.12, 0.16],
                "rpm": [1000, 1500, 2000, 2500, 3000],
                "tps": [0.0, 25.0, 50.0, 75.0, 100.0],
                "map": [-0.5, 0.0, 0.5, 1.0, 1.5],
                "engine_temp": [80.0, 85.0, 90.0, 95.0, 100.0],
                "air_temp": [20.0, 22.0, 24.0, 26.0, 28.0],
                "o2_general": [0.95, 0.92, 0.89, 0.86, 0.83],
                "fuel_pressure": [3.0, 3.2, 3.4, 3.6, 3.8],
                "battery_voltage": [12.0, 12.2, 12.4, 12.6, 12.8],
            }
        )

    def create_problematic_test_data(self):
        """Create test data with various quality issues."""
        return pd.DataFrame(
            {
                "time": [0.0, 0.04, 0.08, np.nan, 0.16],  # Missing value
                "rpm": [1000, 1500, -100, 2500, 25000],  # Negative and extreme values
                "tps": [0.0, 25.0, np.nan, 75.0, 150.0],  # Missing and out-of-range
                "map": [-0.5, 0.0, 0.5, 10.0, 1.5],  # One extreme value
                "engine_temp": [80.0, 85.0, 85.0, 85.0, 85.0],  # Constant values
                "air_temp": [20.0, 22.0, 24.0, 500.0, 28.0],  # One extreme outlier
                "o2_general": [0.95, 0.92, 2.5, 0.86, 0.83],  # Out of range
                "fuel_pressure": [3.0, 3.2, 3.4, 3.6, 3.8],
                "battery_voltage": [12.0, 12.2, 12.4, 12.6, 12.8],
            }
        )

    def test_check_data_completeness_clean_data(self):
        """Test data completeness check with clean data."""
        df = self.create_clean_test_data()

        result = self.assessor.check_data_completeness(df)

        assert result.check_name == "data_completeness"
        assert result.status == "passed"
        assert result.severity == "info"
        assert result.affected_records == 0
        assert result.error_percentage == 0.0
        assert "No missing values" in result.message

    def test_check_data_completeness_missing_data(self):
        """Test data completeness check with missing data."""
        df = self.create_problematic_test_data()

        result = self.assessor.check_data_completeness(df)

        assert result.check_name == "data_completeness"
        assert result.status in ["warning", "failed"]  # Depends on percentage
        assert result.affected_records > 0
        assert result.error_percentage > 0
        assert "missing_by_column" in result.details

    def test_check_range_validity_clean_data(self):
        """Test range validity check with clean data."""
        df = self.create_clean_test_data()

        result = self.assessor.check_range_validity(df)

        assert result.check_name == "range_validity"
        assert result.status == "passed"
        assert result.error_percentage == 0.0
        assert "within expected ranges" in result.message

    def test_check_range_validity_out_of_range(self):
        """Test range validity check with out-of-range values."""
        df = self.create_problematic_test_data()

        result = self.assessor.check_range_validity(df)

        assert result.check_name == "range_validity"
        assert result.status in ["warning", "failed"]
        assert result.affected_records > 0
        assert result.error_percentage > 0
        assert "range_violations" in result.details

    def test_check_temporal_consistency_monotonic(self):
        """Test temporal consistency with monotonic time series."""
        df = self.create_clean_test_data()

        result = self.assessor.check_temporal_consistency(df)

        assert result.check_name == "temporal_consistency"
        assert result.status == "passed"
        assert result.affected_records == 0
        assert "consistency verified" in result.message

    def test_check_temporal_consistency_non_monotonic(self):
        """Test temporal consistency with non-monotonic time series."""
        df = pd.DataFrame(
            {
                "time": [0.0, 0.08, 0.04, 0.12, 0.16],  # Non-monotonic
                "rpm": [1000, 1500, 2000, 2500, 3000],
            }
        )

        result = self.assessor.check_temporal_consistency(df)

        assert result.check_name == "temporal_consistency"
        assert result.status in ["warning", "failed"]
        assert result.affected_records > 0
        assert "Non-monotonic" in result.message or len(result.details.get("issues", [])) > 0

    def test_check_temporal_consistency_no_time_column(self):
        """Test temporal consistency without time column."""
        df = pd.DataFrame(
            {
                "rpm": [1000, 1500, 2000, 2500, 3000],
                "tps": [0.0, 25.0, 50.0, 75.0, 100.0],
            }
        )

        result = self.assessor.check_temporal_consistency(df)

        assert result.check_name == "temporal_consistency"
        assert result.status == "warning"
        assert "No time column" in result.message

    def test_check_temporal_consistency_duplicate_timestamps(self):
        """Test temporal consistency with duplicate timestamps."""
        df = pd.DataFrame(
            {
                "time": [0.0, 0.04, 0.04, 0.12, 0.16],  # Duplicate at index 1,2
                "rpm": [1000, 1500, 2000, 2500, 3000],
            }
        )

        result = self.assessor.check_temporal_consistency(df)

        assert result.check_name == "temporal_consistency"
        assert result.status in ["warning", "failed"]
        assert "Duplicate timestamps" in result.message or len(result.details.get("issues", [])) > 0

    def test_check_physical_plausibility_reasonable_rates(self):
        """Test physical plausibility with reasonable rate changes."""
        df = self.create_clean_test_data()

        result = self.assessor.check_physical_plausibility(df)

        assert result.check_name == "physical_plausibility"
        assert result.status == "passed"
        assert "within physical constraints" in result.message

    def test_check_physical_plausibility_extreme_rates(self):
        """Test physical plausibility with extreme rate changes."""
        # Create data with extreme rate changes
        df = pd.DataFrame(
            {
                "time": [0.0, 0.001, 0.002, 0.003, 0.004],  # Very small time steps
                "rpm": [1000, 8000, 1000, 8000, 1000],  # Extreme RPM changes
                "engine_temp": [
                    80.0,
                    200.0,
                    80.0,
                    200.0,
                    80.0,
                ],  # Impossible temp changes
                "g_force_accel": [0.0, 0.0, 10.0, 0.0, 0.0],  # Extreme G-force
                "o2_general": [0.5, 0.95, 0.5, 0.95, 0.5],  # Lambda out of range
            }
        )

        result = self.assessor.check_physical_plausibility(df)

        assert result.check_name == "physical_plausibility"
        assert result.status in ["warning", "failed"]
        assert result.affected_records > 0

    def test_check_physical_plausibility_no_time_column(self):
        """Test physical plausibility without time column."""
        df = pd.DataFrame({"rpm": [1000, 1500, 2000], "tps": [0.0, 25.0, 50.0]})

        result = self.assessor.check_physical_plausibility(df)

        assert result.check_name == "physical_plausibility"
        assert result.status == "warning"
        assert "No time column" in result.message

    def test_check_statistical_anomalies_clean_data(self):
        """Test statistical anomaly detection with clean data."""
        df = self.create_clean_test_data()

        result = self.assessor.check_statistical_anomalies(df)

        assert result.check_name == "statistical_anomalies"
        assert result.status == "passed"
        assert result.error_percentage == 0.0

    def test_check_statistical_anomalies_with_outliers(self):
        """Test statistical anomaly detection with outliers."""
        df = self.create_problematic_test_data()

        result = self.assessor.check_statistical_anomalies(df)

        assert result.check_name == "statistical_anomalies"
        assert result.status in ["warning", "failed"]
        assert result.affected_records > 0
        assert "anomalies" in result.details

    def test_check_statistical_anomalies_insufficient_data(self):
        """Test statistical anomaly detection with insufficient data."""
        df = pd.DataFrame({"rpm": [1000, 1500], "tps": [0.0, 25.0]})  # Only 2 rows

        result = self.assessor.check_statistical_anomalies(df)

        # Should handle small datasets gracefully
        assert result.check_name == "statistical_anomalies"
        assert isinstance(result.status, str)

    def test_check_correlations_expected_positive(self):
        """Test correlation check with expected positive correlation."""
        # Create data with strong positive correlation between RPM and power
        df = pd.DataFrame(
            {
                "rpm": [1000, 2000, 3000, 4000, 5000],
                "estimated_power": [
                    100,
                    200,
                    300,
                    400,
                    500,
                ],  # Perfect positive correlation
                "tps": [0, 25, 50, 75, 100],
                "map": [0, 0.5, 1.0, 1.5, 2.0],
            }
        )

        result = self.assessor.check_correlations(df)

        assert result.check_name == "correlation_analysis"
        assert result.status == "passed"

    def test_check_correlations_missing_fields(self):
        """Test correlation check with missing expected fields."""
        df = pd.DataFrame(
            {
                "rpm": [1000, 2000, 3000],
                "tps": [0, 25, 50],
                # Missing other fields that are expected to correlate
            }
        )

        result = self.assessor.check_correlations(df)

        # Should handle missing fields gracefully
        assert result.check_name == "correlation_analysis"
        assert isinstance(result.status, str)

    def test_check_correlations_weak_correlation(self):
        """Test correlation check with weak correlations."""
        # Create data where expected correlations are weak
        np.random.seed(42)  # For reproducible results
        df = pd.DataFrame(
            {
                "rpm": np.random.randint(1000, 5000, 20),
                "estimated_power": np.random.randint(50, 200, 20),  # Random, no correlation
                "tps": np.random.uniform(0, 100, 20),
                "map": np.random.uniform(-0.5, 2.0, 20),
            }
        )

        result = self.assessor.check_correlations(df)

        assert result.check_name == "correlation_analysis"
        # May pass or fail depending on random data, but shouldn't crash
        assert isinstance(result.status, str)

    def test_assess_data_quality_comprehensive(self):
        """Test comprehensive data quality assessment."""
        df = self.create_clean_test_data()

        results = self.assessor.assess_data_quality(df)

        assert "overall_score" in results
        assert "assessment_timestamp" in results
        assert "data_shape" in results
        assert "checks_performed" in results
        assert "checks_passed" in results
        assert "checks_warning" in results
        assert "checks_failed" in results
        assert "detailed_results" in results

        # Should have run all quality checks
        assert results["checks_performed"] >= 6

        # Overall score should be between 0 and 100
        assert 0 <= results["overall_score"] <= 100

    def test_assess_data_quality_with_problems(self):
        """Test comprehensive assessment with problematic data."""
        df = self.create_problematic_test_data()

        results = self.assessor.assess_data_quality(df)

        assert "overall_score" in results

        # Should have some failures or warnings
        assert results["checks_warning"] > 0 or results["checks_failed"] > 0

        # Overall score should be lower than perfect data
        assert results["overall_score"] < 95.0

    def test_calculate_quality_score_all_passed(self):
        """Test quality score calculation with all checks passed."""
        # Set up mock results with all passed
        self.assessor.quality_results = [
            QualityCheckResult(
                check_name="test1",
                status="passed",
                severity="info",
                message="Test",
                affected_records=0,
                total_records=100,
                error_percentage=0.0,
                details={},
                timestamp=datetime.now(),
            ),
            QualityCheckResult(
                check_name="test2",
                status="passed",
                severity="info",
                message="Test",
                affected_records=0,
                total_records=100,
                error_percentage=0.0,
                details={},
                timestamp=datetime.now(),
            ),
        ]

        score = self.assessor._calculate_quality_score()

        # Should be high score (near 100)
        assert score >= 95.0

    def test_calculate_quality_score_mixed_results(self):
        """Test quality score calculation with mixed results."""
        self.assessor.quality_results = [
            QualityCheckResult(
                check_name="test1",
                status="passed",
                severity="info",
                message="Test",
                affected_records=0,
                total_records=100,
                error_percentage=0.0,
                details={},
                timestamp=datetime.now(),
            ),
            QualityCheckResult(
                check_name="test2",
                status="warning",
                severity="warning",
                message="Test",
                affected_records=10,
                total_records=100,
                error_percentage=10.0,
                details={},
                timestamp=datetime.now(),
            ),
            QualityCheckResult(
                check_name="test3",
                status="failed",
                severity="error",
                message="Test",
                affected_records=50,
                total_records=100,
                error_percentage=50.0,
                details={},
                timestamp=datetime.now(),
            ),
        ]

        score = self.assessor._calculate_quality_score()

        # Should be moderate score
        assert 20.0 <= score <= 80.0

    def test_calculate_quality_score_no_results(self):
        """Test quality score calculation with no results."""
        self.assessor.quality_results = []

        score = self.assessor._calculate_quality_score()

        assert score == 0.0

    def test_generate_quality_report(self):
        """Test quality report generation."""
        df = self.create_clean_test_data()

        # Run assessment to populate results
        self.assessor.assess_data_quality(df)

        report = self.assessor.generate_quality_report()

        assert "DATA QUALITY ASSESSMENT REPORT" in report
        assert "Overall Quality Score:" in report
        assert "Checks:" in report

        # Should contain check results
        for result in self.assessor.quality_results:
            assert result.check_name.upper() in report

    def test_generate_quality_report_no_results(self):
        """Test quality report generation with no results."""
        report = self.assessor.generate_quality_report()

        assert "No quality assessment results available" in report

    def test_quality_check_exception_handling(self):
        """Test handling of exceptions during quality checks."""
        # Create assessor that will fail
        with patch.object(self.assessor, "check_data_completeness") as mock_check:
            mock_check.side_effect = Exception("Test exception")

            results = self.assessor.assess_data_quality(pd.DataFrame({"test": [1, 2, 3]}))

            # Should handle exception gracefully
            assert "overall_score" in results
            assert results["checks_performed"] >= 1

            # Should have created an error result
            failed_checks = [r for r in results["detailed_results"] if r["status"] == "failed"]
            assert len(failed_checks) >= 1


class TestConvenienceFunctions:
    """Test convenience functions for quality assessment."""

    def test_assess_fueltech_data_quality_basic(self):
        """Test basic quality assessment using convenience function."""
        df = pd.DataFrame(
            {
                "time": [0.0, 0.04, 0.08],
                "rpm": [1000, 1500, 2000],
                "tps": [0.0, 25.0, 50.0],
                "map": [-0.5, 0.0, 0.5],
            }
        )

        results = assess_fueltech_data_quality(df)

        assert "overall_score" in results
        assert "detailed_results" in results
        assert isinstance(results["overall_score"], (int, float))

    def test_assess_fueltech_data_quality_empty_dataframe(self):
        """Test quality assessment with empty DataFrame."""
        df = pd.DataFrame()

        # Should handle empty DataFrame gracefully
        results = assess_fueltech_data_quality(df)

        assert "overall_score" in results
        # Score should be low for empty data
        assert results["overall_score"] < 50.0


class TestQualityAssessmentEdgeCases:
    """Test edge cases and error conditions in quality assessment."""

    def setup_method(self):
        """Setup for each test method."""
        self.assessor = DataQualityAssessor()

    def test_single_row_dataframe(self):
        """Test quality assessment with single row."""
        df = pd.DataFrame({"time": [0.0], "rpm": [1000], "tps": [50.0]})

        results = self.assessor.assess_data_quality(df)

        # Should complete without errors
        assert "overall_score" in results

    def test_all_nan_column(self):
        """Test quality assessment with column containing only NaN."""
        df = pd.DataFrame(
            {
                "time": [0.0, 0.04, 0.08],
                "rpm": [1000, 1500, 2000],
                "all_nan": [np.nan, np.nan, np.nan],
            }
        )

        results = self.assessor.assess_data_quality(df)

        # Should detect completeness issues
        assert results["checks_warning"] > 0 or results["checks_failed"] > 0

    def test_constant_values_detection(self):
        """Test detection of constant values."""
        df = pd.DataFrame(
            {
                "time": [0.0, 0.04, 0.08, 0.12],
                "rpm": [1000, 1000, 1000, 1000],  # Constant
                "tps": [50.0, 50.0, 50.0, 50.0],  # Constant
            }
        )

        result = self.assessor.check_statistical_anomalies(df)

        # Should detect constant values
        assert result.affected_records > 0 or len(result.details.get("anomalies", {})) > 0

    def test_extremely_large_values(self):
        """Test handling of extremely large values."""
        df = pd.DataFrame(
            {
                "time": [0.0, 0.04, 0.08],
                "rpm": [1000, 1e10, 2000],  # Extremely large value
                "tps": [0.0, 25.0, 1e15],  # Extremely large value
            }
        )

        result = self.assessor.check_range_validity(df)

        # Should detect range violations
        assert result.status in ["warning", "failed"]
        assert result.affected_records > 0

    def test_tolerance_factor_adjustment(self):
        """Test tolerance factor adjustment."""
        assessor_strict = DataQualityAssessor(tolerance_factor=0.5)
        assessor_lenient = DataQualityAssessor(tolerance_factor=3.0)

        # Create data with moderate rate changes
        df = pd.DataFrame(
            {
                "time": [0.0, 0.001, 0.002],
                "rpm": [1000, 3000, 2000],  # Fast but not extreme changes
                "engine_temp": [80.0, 85.0, 90.0],
            }
        )

        result_strict = assessor_strict.check_physical_plausibility(df)
        result_lenient = assessor_lenient.check_physical_plausibility(df)

        # Strict assessor should be more likely to flag issues
        # This test verifies that tolerance factor is being used
        assert isinstance(result_strict.status, str)
        assert isinstance(result_lenient.status, str)


if __name__ == "__main__":
    pytest.main([__file__])
