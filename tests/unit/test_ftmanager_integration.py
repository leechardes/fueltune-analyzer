"""
Unit tests for FTManager Integration components

Tests comprehensive functionality of the FTManager Bridge including:
- Format detection with various input types
- Clipboard operations across platforms
- Data validation with edge cases
- Integration bridge orchestration

CRITICAL: Follows PYTHON-CODE-STANDARDS.md
- Type hints 100% coverage
- Professional test structure
- Performance testing included
- Comprehensive edge case coverage
"""

from datetime import datetime
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from src.integration.clipboard_manager import ClipboardManager, ClipboardResult
from src.integration.format_detector import DetectionResult, FTManagerFormatDetector

# Import components under test
from src.integration.ftmanager_bridge import FTManagerIntegrationBridge
from src.integration.validators import FTManagerValidator


class TestFTManagerFormatDetector:
    """Comprehensive tests for format detection algorithms."""

    @pytest.fixture
    def format_detector(self) -> FTManagerFormatDetector:
        """Create format detector instance."""
        return FTManagerFormatDetector()

    @pytest.fixture
    def sample_tabulated_data(self) -> str:
        """Sample tab-separated FTManager data."""
        return """0.850\t0.860\t0.870\t0.880
0.840\t0.850\t0.860\t0.870
0.830\t0.840\t0.850\t0.860
0.820\t0.830\t0.840\t0.850"""

    @pytest.fixture
    def sample_csv_data(self) -> str:
        """Sample CSV format data."""
        return """0.850,0.860,0.870,0.880
0.840,0.850,0.860,0.870
0.830,0.840,0.850,0.860
0.820,0.830,0.840,0.850"""

    @pytest.fixture
    def sample_with_headers(self) -> str:
        """Sample data with headers."""
        return """Col1\tCol2\tCol3\tCol4
0.850\t0.860\t0.870\t0.880
0.840\t0.850\t0.860\t0.870
0.830\t0.840\t0.850\t0.860"""

    def test_detect_tabulated_format(
        self, format_detector: FTManagerFormatDetector, sample_tabulated_data: str
    ):
        """Test detection of tab-separated format."""

        result = format_detector.detect_format(sample_tabulated_data)

        assert result.success
        assert result.confidence > 0.8
        assert result.format_spec is not None
        assert result.format_spec.format_type == "tabulated"
        assert result.format_spec.separator == "\t"
        assert result.format_spec.dimensions == (4, 4)
        assert not result.format_spec.has_headers

    def test_detect_csv_format(
        self, format_detector: FTManagerFormatDetector, sample_csv_data: str
    ):
        """Test detection of CSV format."""

        result = format_detector.detect_format(sample_csv_data)

        assert result.success
        assert result.confidence > 0.7
        assert result.format_spec.format_type == "csv"
        assert result.format_spec.separator == ","
        assert result.format_spec.dimensions == (4, 4)

    def test_detect_headers(
        self, format_detector: FTManagerFormatDetector, sample_with_headers: str
    ):
        """Test header detection."""

        result = format_detector.detect_format(sample_with_headers)

        assert result.success
        assert result.format_spec.has_headers
        assert result.format_spec.dimensions == (3, 4)  # Excludes header row

    def test_empty_content_handling(self, format_detector: FTManagerFormatDetector):
        """Test handling of empty content."""

        result = format_detector.detect_format("")

        assert not result.success
        assert "empty" in result.errors[0].lower()

    def test_invalid_content_handling(self, format_detector: FTManagerFormatDetector):
        """Test handling of invalid content."""

        invalid_content = "This is just plain text without any structure"
        result = format_detector.detect_format(invalid_content)

        assert not result.success or result.confidence < 0.3

    def test_confidence_threshold(
        self, format_detector: FTManagerFormatDetector, sample_tabulated_data: str
    ):
        """Test confidence threshold functionality."""

        # Test with high threshold
        result = format_detector.detect_format(sample_tabulated_data, confidence_threshold=0.9)

        # Result depends on actual confidence, but should respect threshold
        if result.confidence < 0.9:
            assert not result.success

    def test_performance_requirement(
        self, format_detector: FTManagerFormatDetector, sample_tabulated_data: str
    ):
        """Test performance requirement (< 100ms)."""

        start_time = datetime.now()
        result = format_detector.detect_format(sample_tabulated_data)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        assert duration_ms < 100  # Performance requirement
        assert result.detection_metadata["detection_duration_ms"] < 100

    def test_content_structure_analysis(
        self, format_detector: FTManagerFormatDetector, sample_tabulated_data: str
    ):
        """Test content structure analysis."""

        analysis = format_detector.analyze_content_structure(sample_tabulated_data)

        assert "line_statistics" in analysis
        assert "character_analysis" in analysis
        assert "separator_analysis" in analysis
        assert analysis["line_statistics"]["total_lines"] == 4
        assert analysis["separator_analysis"]["tab"]["count"] > 0


class TestClipboardManager:
    """Comprehensive tests for cross-platform clipboard operations."""

    @pytest.fixture
    def clipboard_manager(self) -> ClipboardManager:
        """Create clipboard manager instance."""
        return ClipboardManager()

    def test_initialization(self, clipboard_manager: ClipboardManager):
        """Test clipboard manager initialization."""

        assert clipboard_manager.platform in ["windows", "darwin", "linux"]
        assert isinstance(clipboard_manager.available_methods, list)
        assert clipboard_manager.operation_stats is not None

    @patch("src.integration.clipboard_manager.pyperclip")
    def test_get_content_success(self, mock_pyperclip: Mock, clipboard_manager: ClipboardManager):
        """Test successful content retrieval."""

        test_content = "test clipboard content"
        mock_pyperclip.paste.return_value = test_content

        # Force use of pyperclip method
        clipboard_manager.available_methods = ["pyperclip"]
        clipboard_manager.active_method = "pyperclip"

        result = clipboard_manager.get_content()

        assert result.success
        assert result.content == test_content
        assert result.method_used == "pyperclip"

    @patch("src.integration.clipboard_manager.pyperclip")
    def test_set_content_success(self, mock_pyperclip: Mock, clipboard_manager: ClipboardManager):
        """Test successful content setting."""

        test_content = "test content to set"
        mock_pyperclip.copy.return_value = None
        mock_pyperclip.paste.return_value = test_content  # For verification

        clipboard_manager.available_methods = ["pyperclip"]
        clipboard_manager.active_method = "pyperclip"

        result = clipboard_manager.set_content(test_content)

        assert result.success
        assert result.content == test_content
        mock_pyperclip.copy.assert_called_once_with(test_content)

    def test_content_validation(self, clipboard_manager: ClipboardManager):
        """Test content validation functionality."""

        # Test oversized content
        large_content = "x" * (60 * 1024 * 1024)  # 60MB
        result = clipboard_manager.set_content(large_content, validate_content=True)

        assert not result.success
        assert "size" in result.errors[0].lower()

    def test_clipboard_status(self, clipboard_manager: ClipboardManager):
        """Test clipboard status reporting."""

        status = clipboard_manager.get_status()

        assert isinstance(status, dict)
        assert "available" in status
        assert "platform" in status
        assert "available_methods" in status
        assert "operation_stats" in status

    def test_performance_requirement(self, clipboard_manager: ClipboardManager):
        """Test performance requirement (< 100ms)."""

        # Mock to ensure quick response
        with patch.object(clipboard_manager, "_get_by_method", return_value="test"):
            start_time = datetime.now()
            clipboard_manager.get_content()
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            assert duration_ms < 100  # Performance requirement


class TestFTManagerValidator:
    """Comprehensive tests for FTManager validation algorithms."""

    @pytest.fixture
    def validator(self) -> FTManagerValidator:
        """Create validator instance."""
        return FTManagerValidator()

    @pytest.fixture
    def valid_map_data(self) -> pd.DataFrame:
        """Create valid map data for testing."""
        return pd.DataFrame(np.random.uniform(0.7, 1.3, (16, 16)))

    @pytest.fixture
    def valid_clipboard_content(self) -> str:
        """Create valid clipboard content."""
        return """0.850\t0.860\t0.870\t0.880
0.840\t0.850\t0.860\t0.870
0.830\t0.840\t0.850\t0.860
0.820\t0.830\t0.840\t0.850"""

    def test_validate_valid_clipboard_data(
        self, validator: FTManagerValidator, valid_clipboard_content: str
    ):
        """Test validation of valid clipboard data."""

        result = validator.validate_clipboard_data(valid_clipboard_content)

        assert result.is_valid
        assert result.confidence > 0.7
        assert len(result.errors) == 0

    def test_validate_empty_clipboard_data(self, validator: FTManagerValidator):
        """Test validation of empty clipboard data."""

        result = validator.validate_clipboard_data("")

        assert not result.is_valid
        assert len(result.errors) > 0
        assert "empty" in result.errors[0].lower()

    def test_validate_valid_map_data(
        self, validator: FTManagerValidator, valid_map_data: pd.DataFrame
    ):
        """Test validation of valid DataFrame."""

        result = validator.validate_map_data(valid_map_data)

        assert result.is_valid
        assert result.confidence > 0.8
        assert len(result.errors) == 0

    def test_validate_empty_dataframe(self, validator: FTManagerValidator):
        """Test validation of empty DataFrame."""

        empty_df = pd.DataFrame()
        result = validator.validate_map_data(empty_df)

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_validate_non_numeric_dataframe(self, validator: FTManagerValidator):
        """Test validation of non-numeric DataFrame."""

        non_numeric_df = pd.DataFrame([["a", "b"], ["c", "d"]])
        result = validator.validate_map_data(non_numeric_df, check_numeric=True)

        assert not result.is_valid
        assert any("numeric" in error.lower() for error in result.errors)

    def test_validate_expected_dimensions(
        self, validator: FTManagerValidator, valid_clipboard_content: str
    ):
        """Test validation against expected dimensions."""

        # Content has 4x4 dimensions
        result = validator.validate_clipboard_data(
            valid_clipboard_content, expected_dimensions=(4, 4)
        )

        assert result.is_valid

        # Test mismatch
        result = validator.validate_clipboard_data(
            valid_clipboard_content, expected_dimensions=(16, 16)
        )

        assert len(result.warnings) > 0 or len(result.errors) > 0

    def test_performance_requirement(
        self, validator: FTManagerValidator, valid_clipboard_content: str
    ):
        """Test performance requirement (< 200ms)."""

        start_time = datetime.now()
        result = validator.validate_clipboard_data(valid_clipboard_content)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        assert duration_ms < 200  # Performance requirement
        assert result.performance_metrics["validation_duration_ms"] < 200

    def test_format_compatibility_validation(self, validator: FTManagerValidator):
        """Test format compatibility validation."""

        # Create mock format objects
        source_format = Mock()
        source_format.format_type = "tabulated"
        source_format.dimensions = (16, 16)
        source_format.separator = "\t"
        source_format.decimal_places = 2

        target_format = Mock()
        target_format.format_type = "csv"
        target_format.dimensions = (16, 16)
        target_format.separator = ","
        target_format.decimal_places = 2

        result = validator.validate_format_compatibility(source_format, target_format)

        # Should have warnings about format type difference
        assert result.is_valid  # Compatible despite differences
        assert len(result.warnings) > 0


class TestFTManagerIntegrationBridge:
    """Comprehensive tests for integration bridge orchestration."""

    @pytest.fixture
    def integration_bridge(self) -> FTManagerIntegrationBridge:
        """Create integration bridge instance."""
        return FTManagerIntegrationBridge()

    @pytest.fixture
    def sample_map_data(self) -> pd.DataFrame:
        """Create sample map data."""
        return pd.DataFrame(np.random.uniform(0.7, 1.3, (16, 16)))

    def test_initialization(self, integration_bridge: FTManagerIntegrationBridge):
        """Test integration bridge initialization."""

        assert integration_bridge.core_bridge is not None
        assert integration_bridge.format_detector is not None
        assert integration_bridge.clipboard_manager is not None
        assert integration_bridge.validator is not None
        assert integration_bridge.operation_count == 0

    def test_get_supported_formats(self, integration_bridge: FTManagerIntegrationBridge):
        """Test getting supported formats."""

        formats = integration_bridge.get_supported_formats()

        assert isinstance(formats, dict)
        assert len(formats) > 0
        # Should contain common FTManager formats
        assert any("16" in key for key in formats.keys())

    def test_get_integration_stats(self, integration_bridge: FTManagerIntegrationBridge):
        """Test integration statistics."""

        stats = integration_bridge.get_integration_stats()

        assert isinstance(stats, dict)
        assert "bridge_initialized" in stats
        assert "operation_count" in stats
        assert "supported_format_count" in stats
        assert "components_status" in stats

    @patch("src.integration.ftmanager_bridge.st")
    def test_create_streamlit_ui(
        self, mock_st: Mock, integration_bridge: FTManagerIntegrationBridge
    ):
        """Test Streamlit UI creation."""

        # Mock streamlit components
        mock_st.markdown.return_value = None
        mock_st.tabs.return_value = [Mock(), Mock(), Mock(), Mock()]
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()

        # Should not raise exceptions
        integration_bridge.create_streamlit_ui()

        # Verify UI elements were created
        assert mock_st.markdown.called
        assert mock_st.tabs.called

    @patch.object(FTManagerIntegrationBridge, "_track_operation")
    def test_operation_tracking(
        self, mock_track: Mock, integration_bridge: FTManagerIntegrationBridge
    ):
        """Test operation tracking functionality."""

        # Mock clipboard operations
        with patch.object(integration_bridge.clipboard_manager, "get_content") as mock_get:
            mock_result = ClipboardResult(success=False, content=None)
            mock_get.return_value = mock_result

            # Call method that should track operations
            integration_bridge.import_from_clipboard()

            # Should have attempted to track operation
            mock_track.assert_called_once()


class TestIntegrationPerformance:
    """Performance tests for FTManager integration components."""

    @pytest.fixture
    def large_dataset(self) -> str:
        """Create large dataset for performance testing."""

        # Create 50x50 map data (reasonable large size)
        data_lines = []
        for i in range(50):
            row = "\t".join([f"{0.85 + (i * 0.001) + (j * 0.0001):.4f}" for j in range(50)])
            data_lines.append(row)

        return "\n".join(data_lines)

    def test_format_detection_performance(self, large_dataset: str):
        """Test format detection performance with large datasets."""

        detector = FTManagerFormatDetector()

        start_time = datetime.now()
        result = detector.detect_format(large_dataset)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        assert duration_ms < 100  # Should complete within 100ms
        assert result.success

    def test_validation_performance(self, large_dataset: str):
        """Test validation performance with large datasets."""

        validator = FTManagerValidator()

        start_time = datetime.now()
        result = validator.validate_clipboard_data(large_dataset)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        assert duration_ms < 200  # Should complete within 200ms
        assert result.is_valid


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_malformed_data_handling(self):
        """Test handling of malformed data."""

        detector = FTManagerFormatDetector()

        # Test various malformed inputs
        malformed_inputs = [
            "incomplete\trow",
            "mixed,\tseparators\t,here",
            "123.456.789",  # Invalid number
            "\t\t\t\t",  # Only separators
        ]

        for malformed_input in malformed_inputs:
            result = detector.detect_format(malformed_input)
            # Should handle gracefully without exceptions
            assert isinstance(result, DetectionResult)

    def test_unicode_handling(self):
        """Test handling of unicode content."""

        detector = FTManagerFormatDetector()

        unicode_content = "0.850\t0.860\tαβγ\t0.880"
        result = detector.detect_format(unicode_content)

        # Should handle unicode gracefully
        assert isinstance(result, DetectionResult)

    def test_extremely_large_input(self):
        """Test handling of extremely large input."""

        detector = FTManagerFormatDetector()

        # Create very large input
        large_input = "0.85\t0.86\n" * 10000  # 10k lines

        result = detector.detect_format(large_input)

        # Should complete without memory issues
        assert isinstance(result, DetectionResult)


# Integration test that combines multiple components
class TestFullIntegrationWorkflow:
    """Test complete integration workflow."""

    @pytest.fixture
    def sample_ftmanager_data(self) -> str:
        """Create realistic FTManager data."""

        return """0.785\t0.795\t0.805\t0.815\t0.825\t0.835\t0.845\t0.855
0.780\t0.790\t0.800\t0.810\t0.820\t0.830\t0.840\t0.850
0.775\t0.785\t0.795\t0.805\t0.815\t0.825\t0.835\t0.845
0.770\t0.780\t0.790\t0.800\t0.810\t0.820\t0.830\t0.840
0.765\t0.775\t0.785\t0.795\t0.805\t0.815\t0.825\t0.835
0.760\t0.770\t0.780\t0.790\t0.800\t0.810\t0.820\t0.830
0.755\t0.765\t0.775\t0.785\t0.795\t0.805\t0.815\t0.825
0.750\t0.760\t0.770\t0.780\t0.790\t0.800\t0.810\t0.820"""

    def test_complete_import_export_cycle(self, sample_ftmanager_data: str):
        """Test complete import/export cycle."""

        # Initialize components
        bridge = FTManagerIntegrationBridge()

        # Mock clipboard with sample data
        with patch.object(bridge.clipboard_manager, "get_content") as mock_get:
            mock_get.return_value = ClipboardResult(success=True, content=sample_ftmanager_data)

            # Import data
            import_result = bridge.import_from_clipboard()

            assert import_result.success
            assert import_result.data is not None
            assert import_result.detected_format is not None

            # Mock clipboard for export
            with patch.object(bridge.clipboard_manager, "set_content") as mock_set:
                mock_set.return_value = ClipboardResult(success=True)

                # Export the imported data
                export_result = bridge.export_to_clipboard(import_result.data)

                assert export_result.success
                assert export_result.formatted_output is not None
