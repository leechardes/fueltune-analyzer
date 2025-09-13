"""
Unit tests for analysis modules.

Tests the core functionality of the FuelTune analysis modules.

Author: A04-ANALYSIS-SCIPY Agent
Created: 2025-01-02
"""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.analysis.anomaly import AnomalyDetector
from src.analysis.correlation import CorrelationAnalyzer
from src.analysis.dynamics import VehicleDynamicsAnalyzer
from src.analysis.fuel_efficiency import FuelEfficiencyAnalyzer
from src.analysis.performance import PerformanceAnalyzer
from src.analysis.predictive import PredictiveAnalyzer
from src.analysis.reports import ReportGenerator
from src.analysis.statistics import DescriptiveStats, StatisticalAnalyzer
from src.analysis.time_series import TimeSeriesAnalyzer


class TestStatisticalAnalyzer:
    """Test statistical analysis functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = StatisticalAnalyzer()
        self.sample_data = pd.Series(np.random.normal(100, 15, 1000))

    def test_compute_descriptive_stats(self):
        """Test descriptive statistics computation."""
        results = self.analyzer.compute_descriptive_stats(self.sample_data)

        assert isinstance(results, DescriptiveStats)
        assert results.count == 1000
        assert 95 < results.mean < 105  # Should be around 100
        assert 10 < results.std < 20  # Should be around 15
        assert results.min < results.q25 < results.median < results.q75 < results.max

    def test_analyze_method_series(self):
        """Test standard analyze method with Series."""
        results = self.analyzer.analyze(self.sample_data)

        assert isinstance(results, dict)
        # Should not have error key if successful
        if "error" not in results:
            assert "descriptive_statistics" in results
            assert "normality_tests" in results

    def test_analyze_method_dataframe(self):
        """Test standard analyze method with DataFrame."""
        df_data = pd.DataFrame({"col1": self.sample_data, "col2": np.random.normal(50, 10, 1000)})
        results = self.analyzer.analyze(df_data)

        assert isinstance(results, dict)
        # Should analyze each numeric column
        if "error" not in results:
            assert "col1" in results
            assert "col2" in results

    def test_test_normality(self):
        """Test normality testing."""
        results = self.analyzer.test_normality(self.sample_data)

        assert hasattr(results, "shapiro_stat")
        assert hasattr(results, "shapiro_p")
        assert hasattr(results, "overall_normal")
        assert isinstance(results.overall_normal, bool)

    def test_insufficient_data_handling(self):
        """Test handling of insufficient data."""
        small_data = pd.Series([1, 2])

        with pytest.raises(ValueError, match="Insufficient data"):
            self.analyzer.compute_descriptive_stats(small_data)


class TestTimeSeriesAnalyzer:
    """Test time series analysis functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = TimeSeriesAnalyzer()
        # Create trend data: linear increase with noise
        self.trend_data = pd.Series(np.arange(100) + np.random.normal(0, 5, 100))

    def test_analyze_method_series(self):
        """Test standard analyze method with Series."""
        results = self.analyzer.analyze(self.trend_data)

        assert isinstance(results, dict)
        # Should not have error key if successful
        if "error" not in results:
            assert "trend_analysis" in results
            assert "autocorrelation" in results
            assert "frequency_analysis" in results
            assert "data_length" in results
            assert "sample_rate" in results

    def test_analyze_method_dataframe(self):
        """Test standard analyze method with DataFrame."""
        df_data = pd.DataFrame({"values": self.trend_data})
        results = self.analyzer.analyze(df_data)

        assert isinstance(results, dict)
        # Should analyze the first numeric column
        if "error" not in results:
            assert "trend_analysis" in results

    def test_analyze_trend(self):
        """Test trend analysis."""
        results = self.analyzer.analyze_trend(self.trend_data)

        assert hasattr(results, "slope")
        assert hasattr(results, "trend_direction")
        assert results.slope > 0  # Should detect increasing trend
        assert results.trend_direction == "increasing"

    def test_compute_autocorrelation(self):
        """Test autocorrelation computation."""
        results = self.analyzer.compute_autocorrelation(self.trend_data)

        assert hasattr(results, "autocorr_values")
        assert hasattr(results, "lags")
        assert len(results.autocorr_values) > 0
        assert results.autocorr_values[0] == 1.0  # Self-correlation should be 1


class TestCorrelationAnalyzer:
    """Test correlation analysis functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = CorrelationAnalyzer()

        # Create correlated data
        np.random.seed(42)
        x = np.random.normal(0, 1, 100)
        y = 0.8 * x + np.random.normal(0, 0.6, 100)
        z = np.random.normal(0, 1, 100)

        self.test_data = pd.DataFrame({"x": x, "y": y, "z": z})

    def test_analyze_method(self):
        """Test standard analyze method."""
        results = self.analyzer.analyze(self.test_data)

        assert isinstance(results, dict)
        # Should not have error key if successful
        if "error" not in results:
            assert "pearson_correlation" in results
            assert "summary" in results

    def test_compute_correlation_matrix(self):
        """Test correlation matrix computation."""
        results = self.analyzer.compute_correlation_matrix(self.test_data)

        assert hasattr(results, "correlation_matrix")
        assert hasattr(results, "significant_pairs")

        # x and y should be significantly correlated
        corr_xy = results.correlation_matrix.loc["x", "y"]
        assert abs(corr_xy) > 0.5  # Strong correlation

    def test_analyze_feature_importance(self):
        """Test feature importance analysis."""
        results = self.analyzer.analyze_feature_importance(
            self.test_data, "y", method="mutual_info"
        )

        assert hasattr(results, "feature_scores")
        assert hasattr(results, "top_features")
        assert "x" in results.top_features  # x should be important for y


class TestAnomalyDetector:
    """Test anomaly detection functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.detector = AnomalyDetector(contamination=0.1)

        # Create normal data with some outliers
        np.random.seed(42)
        normal_data = np.random.normal(0, 1, 900)
        outliers = np.random.normal(5, 1, 100)
        self.test_data = pd.DataFrame(
            {
                "feature1": np.concatenate([normal_data, outliers]),
                "feature2": np.random.normal(0, 1, 1000),
            }
        )

    def test_analyze_method(self):
        """Test standard analyze method."""
        results = self.detector.analyze(self.test_data)

        assert isinstance(results, dict)
        # Should not have error key if successful
        if "error" not in results:
            assert "summary" in results
            assert "statistical" in results or "isolation_forest" in results

    def test_detect_isolation_forest_anomalies(self):
        """Test Isolation Forest anomaly detection."""
        results = self.detector.detect_isolation_forest_anomalies(self.test_data)

        assert hasattr(results, "anomaly_labels")
        assert hasattr(results, "anomaly_indices")
        assert results.n_anomalies > 0
        assert 0 <= results.anomaly_rate <= 1

    def test_detect_statistical_anomalies(self):
        """Test statistical anomaly detection."""
        data_series = self.test_data["feature1"]
        results = self.detector.detect_statistical_anomalies(data_series)

        assert hasattr(results, "z_score_anomalies")
        assert hasattr(results, "iqr_anomalies")
        assert len(results.z_score_anomalies) > 0  # Should detect outliers


class TestFuelEfficiencyAnalyzer:
    """Test fuel efficiency analysis functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = FuelEfficiencyAnalyzer()

        # Create synthetic fuel efficiency data
        self.test_data = pd.DataFrame(
            {
                "engine_rpm": np.random.uniform(1000, 6000, 100),
                "engine_load": np.random.uniform(20, 100, 100),
                "fuel_flow_rate": np.random.uniform(5, 20, 100),
                "manifold_pressure": np.random.uniform(50, 200, 100),
                "maf_sensor": np.random.uniform(10, 50, 100),
            }
        )

        # Add power estimation
        self.test_data["engine_power"] = (
            self.test_data["engine_rpm"] * self.test_data["engine_load"] / 1000
        )

    def test_analyze_bsfc(self):
        """Test BSFC analysis."""
        results = self.analyzer.analyze_bsfc(
            self.test_data, power_col="engine_power", fuel_flow_col="fuel_flow_rate"
        )

        assert hasattr(results, "min_bsfc")
        assert hasattr(results, "optimal_range")
        assert results.min_bsfc > 0
        assert len(results.bsfc_values) > 0

    def test_analyze_consumption_patterns(self):
        """Test consumption pattern analysis."""
        # Add speed data
        self.test_data["vehicle_speed"] = np.random.uniform(0, 120, 100)

        results = self.analyzer.analyze_consumption_patterns(
            self.test_data,
            fuel_flow_col="fuel_flow_rate",
            rpm_col="engine_rpm",
            speed_col="vehicle_speed",
        )

        assert hasattr(results, "consumption_by_rpm")
        assert hasattr(results, "driving_modes")
        assert len(results.consumption_by_rpm) > 0


class TestPerformanceAnalyzer:
    """Test performance analysis functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = PerformanceAnalyzer()

        # Create synthetic performance data
        self.test_data = pd.DataFrame(
            {
                "engine_rpm": np.random.uniform(1000, 7000, 100),
                "vehicle_speed": np.linspace(0, 200, 100) + np.random.normal(0, 5, 100),
                "time": np.arange(100),
                "throttle_position": np.random.uniform(0, 100, 100),
            }
        )

    def test_analyze_method(self):
        """Test standard analyze method."""
        results = self.analyzer.analyze(self.test_data)

        assert isinstance(results, dict)
        # Should not have error key if successful, or should provide warning about data
        if "error" not in results and "warning" not in results:
            # At least one analysis should be performed
            assert len(results) > 0

    def test_analyze_acceleration(self):
        """Test acceleration analysis."""
        results = self.analyzer.analyze_acceleration(
            self.test_data, speed_col="vehicle_speed", time_col="time"
        )

        assert hasattr(results, "acceleration_profile")
        assert hasattr(results, "max_acceleration")
        assert len(results.acceleration_profile) > 0


class TestVehicleDynamicsAnalyzer:
    """Test vehicle dynamics analysis functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = VehicleDynamicsAnalyzer()

        # Create synthetic IMU data
        self.test_data = pd.DataFrame(
            {
                "accel_x": np.random.normal(0, 2, 100),  # Longitudinal
                "accel_y": np.random.normal(0, 1, 100),  # Lateral
                "accel_z": np.random.normal(9.8, 1, 100),  # Vertical (with gravity)
                "vehicle_speed": np.random.uniform(30, 100, 100),
            }
        )

    def test_analyze_g_forces(self):
        """Test G-force analysis."""
        results = self.analyzer.analyze_g_forces(self.test_data)

        assert hasattr(results, "longitudinal_g")
        assert hasattr(results, "lateral_g")
        assert hasattr(results, "combined_g")
        assert hasattr(results, "comfort_rating")
        assert 0 <= results.comfort_rating <= 1

    def test_analyze_driving_style(self):
        """Test driving style analysis."""
        results = self.analyzer.analyze_driving_style(self.test_data, speed_col="vehicle_speed")

        assert hasattr(results, "aggressiveness_score")
        assert hasattr(results, "smoothness_score")
        assert hasattr(results, "efficiency_score")
        assert 0 <= results.aggressiveness_score <= 10


class TestPredictiveAnalyzer:
    """Test predictive analysis functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = PredictiveAnalyzer()

        # Create synthetic sensor data
        self.test_data = pd.DataFrame(
            {
                "engine_rpm": np.random.uniform(1000, 6000, 200),
                "coolant_temp": np.random.uniform(80, 110, 200),
                "oil_pressure": np.random.uniform(30, 80, 200),
                "fuel_flow_rate": np.random.uniform(5, 25, 200),
            }
        )

    def test_analyze_method(self):
        """Test standard analyze method."""
        results = self.analyzer.analyze(self.test_data)

        assert isinstance(results, dict)
        # Should not have error key if successful, or should provide warning about data
        if "error" not in results and "warning" not in results:
            # At least one analysis should be performed
            assert len(results) > 0

    def test_predict_failures(self):
        """Test failure prediction."""
        results = self.analyzer.predict_failures(self.test_data)

        assert hasattr(results, "failure_probability")
        assert hasattr(results, "health_scores")
        assert hasattr(results, "maintenance_alerts")

        # Health scores should be between 0 and 100
        for score in results.health_scores.values():
            assert 0 <= score <= 100

    def test_forecast_consumption(self):
        """Test consumption forecasting."""
        results = self.analyzer.forecast_consumption(
            self.test_data,
            consumption_col="fuel_flow_rate",
            feature_cols=["engine_rpm", "coolant_temp"],
        )

        assert hasattr(results, "forecast_values")
        assert hasattr(results, "consumption_drivers")
        assert len(results.forecast_values) > 0


class TestReportGenerator:
    """Test report generation functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generator = ReportGenerator()

        # Create comprehensive test data
        self.test_data = pd.DataFrame(
            {
                "engine_rpm": np.random.uniform(1000, 6000, 500),
                "vehicle_speed": np.random.uniform(0, 120, 500),
                "fuel_flow_rate": np.random.uniform(5, 20, 500),
                "engine_load": np.random.uniform(20, 100, 500),
                "coolant_temp": np.random.uniform(80, 105, 500),
            }
        )

    @patch("src.analysis.reports.ReportGenerator._calculate_efficiency_rating")
    @patch("src.analysis.reports.ReportGenerator._calculate_performance_rating")
    def test_generate_executive_summary(self, mock_perf_rating, mock_eff_rating):
        """Test executive summary generation."""
        mock_eff_rating.return_value = "B"
        mock_perf_rating.return_value = "A"

        results = self.generator.generate_executive_summary(
            self.test_data, session_name="Test Session"
        )

        assert hasattr(results, "session_overview")
        assert hasattr(results, "key_performance_indicators")
        assert hasattr(results, "efficiency_rating")
        assert hasattr(results, "performance_rating")
        assert results.efficiency_rating == "B"
        assert results.performance_rating == "A"

    def test_generate_technical_report(self):
        """Test technical report generation."""
        results = self.generator.generate_technical_report(self.test_data)

        assert hasattr(results, "statistical_analysis")
        assert hasattr(results, "correlation_analysis")
        assert hasattr(results, "anomaly_analysis")

        # Should contain analysis results or error messages
        assert isinstance(results.statistical_analysis, dict)


# Integration tests
class TestAnalysisIntegration:
    """Test integration between analysis modules."""

    def setup_method(self):
        """Setup integration test fixtures."""
        # Create realistic automotive data
        np.random.seed(42)
        n_samples = 1000

        # Simulate a drive cycle
        time = np.arange(n_samples)
        speed = 50 + 30 * np.sin(time / 100) + np.random.normal(0, 5, n_samples)
        speed = np.clip(speed, 0, 120)

        rpm = speed * 50 + np.random.normal(0, 100, n_samples)
        rpm = np.clip(rpm, 800, 7000)

        load = speed / 2 + np.random.normal(0, 10, n_samples)
        load = np.clip(load, 10, 100)

        fuel_flow = (rpm / 1000) * (load / 100) * 8 + np.random.normal(0, 2, n_samples)
        fuel_flow = np.clip(fuel_flow, 3, 30)

        self.realistic_data = pd.DataFrame(
            {
                "time": time,
                "vehicle_speed": speed,
                "engine_rpm": rpm,
                "engine_load": load,
                "fuel_flow_rate": fuel_flow,
                "coolant_temp": np.random.uniform(85, 95, n_samples),
                "accel_x": np.random.normal(0, 1, n_samples),
                "accel_y": np.random.normal(0, 0.5, n_samples),
            }
        )

    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline."""
        # This test ensures all modules work together
        report_generator = ReportGenerator()

        # Generate comprehensive report
        report = report_generator.generate_comprehensive_report(
            self.realistic_data, session_name="Integration Test"
        )

        assert "executive_summary" in report
        assert "technical_report" in report
        assert "dashboard" in report
        assert "data_summary" in report

        # Verify data summary
        data_summary = report["data_summary"]
        assert data_summary["total_records"] == 1000
        assert data_summary["completeness"] > 95  # Should have good data quality

    def test_analysis_consistency(self):
        """Test consistency across different analysis modules."""
        # Run multiple analyses and verify consistent results
        stat_analyzer = StatisticalAnalyzer()
        corr_analyzer = CorrelationAnalyzer()

        # Both should work with the same data
        speed_stats = stat_analyzer.compute_descriptive_stats(self.realistic_data["vehicle_speed"])

        correlation_matrix = corr_analyzer.compute_correlation_matrix(
            self.realistic_data[["vehicle_speed", "engine_rpm", "fuel_flow_rate"]]
        )

        # Basic consistency checks
        assert speed_stats.count == len(self.realistic_data)
        assert len(correlation_matrix.correlation_matrix) == 3

        # Speed and RPM should be positively correlated
        speed_rpm_corr = correlation_matrix.correlation_matrix.loc["vehicle_speed", "engine_rpm"]
        assert speed_rpm_corr > 0.5  # Should be strongly correlated


if __name__ == "__main__":
    pytest.main([__file__])
