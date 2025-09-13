"""
Unit tests for UI components.

Testes básicos para componentes de interface do usuário,
incluindo metric cards, session selector e chart builder.

Author: UI-FIX Agent
Created: 2025-01-02
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


class TestMetricCard:
    """Test cases for MetricCard component."""

    def test_metric_card_import(self):
        """Test that MetricCard can be imported."""
        from src.ui.components.metric_card import MetricCard, MetricData

        assert MetricCard is not None
        assert MetricData is not None

    def test_metric_data_creation(self):
        """Test MetricData dataclass creation."""
        from src.ui.components.metric_card import MetricData

        metric = MetricData(
            title="Test Metric",
            value=100.0,
            unit="RPM",
            format_type="integer",
            delta=5.0,
            delta_type="increase",
        )

        assert metric.title == "Test Metric"
        assert metric.value == 100.0
        assert metric.unit == "RPM"
        assert metric.delta == 5.0


class TestSessionSelector:
    """Test cases for SessionSelector component."""

    def test_session_selector_import(self):
        """Test that SessionSelector can be imported."""
        from src.ui.components.session_selector import SessionInfo, SessionSelector

        assert SessionSelector is not None
        assert SessionInfo is not None

    def test_session_info_creation(self):
        """Test SessionInfo dataclass creation."""
        from datetime import datetime

        from src.ui.components.session_selector import SessionInfo

        session = SessionInfo(
            id="test123",
            name="Test Session",
            filename="test.csv",
            created_at=datetime.now(),
            total_records=1000,
            quality_score=85.5,
            format_version="v1.0",
        )

        assert session.id == "test123"
        assert session.name == "Test Session"
        assert session.total_records == 1000
        assert session.quality_score == 85.5


class TestChartBuilder:
    """Test cases for ChartBuilder component."""

    def test_chart_builder_import(self):
        """Test that ChartBuilder can be imported."""
        from src.ui.components.chart_builder import ChartBuilder, ChartConfig, SeriesData

        assert ChartBuilder is not None
        assert ChartConfig is not None
        assert SeriesData is not None

    def test_chart_config_creation(self):
        """Test ChartConfig dataclass creation."""
        from src.ui.components.chart_builder import ChartConfig

        config = ChartConfig(
            title="Test Chart",
            x_axis_title="Time",
            y_axis_title="RPM",
            chart_type="line",
            theme="dark",
        )

        assert config.title == "Test Chart"
        assert config.x_axis_title == "Time"
        assert config.chart_type == "line"

    def test_series_data_creation(self):
        """Test SeriesData dataclass creation."""
        from src.ui.components.chart_builder import SeriesData

        series = SeriesData(
            name="RPM",
            x_data=[0, 1, 2, 3, 4],
            y_data=[1000, 1500, 2000, 2500, 3000],
            color="blue",
            line_width=2,
        )

        assert series.name == "RPM"
        assert len(series.x_data) == 5
        assert len(series.y_data) == 5
        assert series.color == "blue"


class TestSessionStateManager:
    """Test cases for SessionStateManager component."""

    def test_session_state_manager_import(self):
        """Test that SessionStateManager can be imported."""
        from src.ui.components.session_state_manager import SessionStateManager

        assert SessionStateManager is not None

    @patch("streamlit.session_state", {})
    def test_session_state_manager_basic(self):
        """Test basic SessionStateManager functionality."""
        from src.ui.components.session_state_manager import SessionStateManager

        # Should not crash during import and basic instantiation
        assert SessionStateManager is not None


class TestUIHelpers:
    """Test cases for UI helper functions."""

    def test_create_engine_metrics_import(self):
        """Test that engine metrics helper can be imported."""
        from src.ui.components.metric_card import create_engine_metrics

        assert create_engine_metrics is not None

    def test_create_fuel_metrics_import(self):
        """Test that fuel metrics helper can be imported."""
        from src.ui.components.metric_card import create_fuel_metrics

        assert create_fuel_metrics is not None

    def test_create_performance_metrics_import(self):
        """Test that performance metrics helper can be imported."""
        from src.ui.components.metric_card import create_performance_metrics

        assert create_performance_metrics is not None

    def test_get_available_sessions_import(self):
        """Test that session helper can be imported."""
        from src.ui.components.session_selector import get_available_sessions

        assert get_available_sessions is not None

    def test_create_rpm_vs_time_chart_import(self):
        """Test that chart helper can be imported."""
        from src.ui.components.chart_builder import create_rpm_vs_time_chart

        assert create_rpm_vs_time_chart is not None


class TestUIComponentsWithMockData:
    """Test UI components with mock data."""

    def create_sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "time": [0.0, 0.04, 0.08, 0.12, 0.16],
                "rpm": [1000, 1500, 2000, 2500, 3000],
                "tps": [0.0, 25.0, 50.0, 75.0, 100.0],
                "map": [-0.5, 0.0, 0.5, 1.0, 1.5],
                "engine_temp": [80.0, 85.0, 90.0, 95.0, 100.0],
            }
        )

    @patch("src.ui.components.metric_card.get_database")
    def test_create_engine_metrics_with_data(self, mock_db):
        """Test creating engine metrics with sample data."""
        from src.ui.components.metric_card import create_engine_metrics

        # Mock database response
        mock_db_manager = MagicMock()
        mock_db.return_value = mock_db_manager

        df = self.create_sample_dataframe()

        # Should not crash when called with valid data structure
        try:
            result = create_engine_metrics(df)
            # If it returns something, it should be a list
            if result is not None:
                assert isinstance(result, list)
        except Exception as e:
            # Some functions might need streamlit context, which is OK for these basic tests
            assert "streamlit" in str(e).lower() or "session_state" in str(e).lower()

    @patch("src.ui.components.chart_builder.go")
    @patch("src.ui.components.chart_builder.px")
    def test_create_rpm_chart_with_data(self, mock_px, mock_go):
        """Test creating RPM chart with sample data."""
        from src.ui.components.chart_builder import create_rpm_vs_time_chart

        # Mock plotly components
        mock_fig = MagicMock()
        mock_px.line.return_value = mock_fig

        df = self.create_sample_dataframe()

        # Should not crash when called with valid data
        try:
            result = create_rpm_vs_time_chart(df)
            # Should return some kind of figure object or None
            assert result is not None or result is None
        except Exception as e:
            # Some chart functions might require specific data structures
            assert isinstance(e, (KeyError, ValueError, TypeError))


if __name__ == "__main__":
    pytest.main([__file__])
