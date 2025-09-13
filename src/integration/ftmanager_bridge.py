"""
FTManager Bridge - Main integration class for FuelTech Manager compatibility

This module provides the main bridge class that orchestrates clipboard operations,
format detection, and data validation for seamless FTManager integration.

CRITICAL: Follows PYTHON-CODE-STANDARDS.md:
- Zero emojis in interface
- Professional error handling
- Type hints 100% coverage
- Performance < 1s for typical operations
- Cross-platform clipboard compatibility
- Robust format detection algorithms
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

import pandas as pd
import streamlit as st

from ..maps.ftmanager import FTManagerBridge as CoreBridge
from .clipboard_manager import ClipboardManager
from .format_detector import FTManagerFormatDetector
from .validators import FTManagerValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class IntegrationResult:
    """Type-safe integration operation result."""

    success: bool
    operation: Literal["import", "export", "validate", "detect"]
    data: Optional[pd.DataFrame] = None
    formatted_output: Optional[str] = None
    detected_format: Optional[Dict[str, Any]] = None
    validation_result: Optional[ValidationResult] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Initialize empty collections if None."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class FTManagerIntegrationBridge:
    """
    Professional FTManager integration bridge with comprehensive features.

    This class orchestrates all FTManager integration operations including:
    - Clipboard import/export with auto-detection
    - Format validation and compatibility checking
    - Cross-platform clipboard management
    - Professional error handling and feedback

    Performance Targets:
    - Format detection: < 100ms
    - Data import: < 500ms
    - Data export: < 300ms
    - Validation: < 200ms
    """

    def __init__(self) -> None:
        """Initialize integration bridge with all components."""

        try:
            # Initialize core components
            self.core_bridge = CoreBridge()
            self.format_detector = FTManagerFormatDetector()
            self.clipboard_manager = ClipboardManager()
            self.validator = FTManagerValidator()

            # Integration metadata
            self.last_operation_time: Optional[datetime] = None
            self.operation_count: int = 0

            logger.info("FTManager Integration Bridge initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize FTManager Integration Bridge: %s", e)
            raise

    def import_from_clipboard(
        self,
        validate_data: bool = True,
        auto_detect_format: bool = True,
        expected_dimensions: Optional[Tuple[int, int]] = None,
    ) -> IntegrationResult:
        """
        Import map data from clipboard with comprehensive validation.

        Args:
            validate_data: Whether to perform data validation
            auto_detect_format: Whether to auto-detect format
            expected_dimensions: Optional expected map dimensions

        Returns:
            IntegrationResult with import status and data

        Performance: < 500ms for typical operations
        """

        operation_start = datetime.now()

        try:
            # Get clipboard content through manager
            clipboard_result = self.clipboard_manager.get_content()
            if not clipboard_result.success or not clipboard_result.content:
                return IntegrationResult(
                    success=False,
                    operation="import",
                    errors=["Clipboard is empty or inaccessible"],
                    metadata={"operation_time": operation_start.isoformat()},
                )

            clipboard_content = clipboard_result.content

            # Auto-detect format if requested
            detected_format = None
            if auto_detect_format:
                detection_result = self.format_detector.detect_format(clipboard_content)
                if not detection_result.success:
                    return IntegrationResult(
                        success=False,
                        operation="import",
                        errors=detection_result.errors,
                        warnings=detection_result.warnings,
                        metadata={"operation_time": operation_start.isoformat()},
                    )
                detected_format = detection_result.format_spec

            # Validate format and data if requested
            validation_result = None
            if validate_data:
                validation_result = self.validator.validate_clipboard_data(
                    clipboard_content,
                    expected_format=detected_format,
                    expected_dimensions=expected_dimensions,
                )

                if not validation_result.is_valid:
                    return IntegrationResult(
                        success=False,
                        operation="import",
                        validation_result=validation_result,
                        errors=validation_result.errors,
                        warnings=validation_result.warnings,
                        metadata={"operation_time": operation_start.isoformat()},
                    )

            # Perform import using core bridge
            import_result = self.core_bridge.import_from_clipboard()

            # Track operation
            self._track_operation()

            # Compile results
            return IntegrationResult(
                success=import_result.success,
                operation="import",
                data=import_result.map_data,
                detected_format=self._format_to_dict(import_result.detected_format),
                validation_result=validation_result,
                errors=import_result.errors,
                warnings=import_result.warnings,
                metadata={
                    "operation_time": operation_start.isoformat(),
                    "processing_duration_ms": (datetime.now() - operation_start).total_seconds()
                    * 1000,
                    "data_shape": (
                        import_result.map_data.shape if import_result.map_data is not None else None
                    ),
                    "format_detected": detected_format is not None,
                    "validation_performed": validate_data,
                    **import_result.metadata,
                },
            )

        except Exception as e:
            logger.error("Import operation failed: %s", e)
            return IntegrationResult(
                success=False,
                operation="import",
                errors=[f"Import failed: {str(e)}"],
                metadata={"operation_time": operation_start.isoformat()},
            )

    def export_to_clipboard(
        self,
        map_data: pd.DataFrame,
        format_name: Optional[str] = None,
        custom_format: Optional[Dict[str, Any]] = None,
        validate_before_export: bool = True,
    ) -> IntegrationResult:
        """
        Export map data to clipboard in FTManager format.

        Args:
            map_data: DataFrame containing map data to export
            format_name: Optional known format name to use
            custom_format: Optional custom format specification
            validate_before_export: Whether to validate data before export

        Returns:
            IntegrationResult with export status and formatted data

        Performance: < 300ms for typical operations
        """

        operation_start = datetime.now()

        try:
            # Validate input data
            if map_data is None or map_data.empty:
                return IntegrationResult(
                    success=False,
                    operation="export",
                    errors=["Cannot export empty or null map data"],
                    metadata={"operation_time": operation_start.isoformat()},
                )

            # Validate data before export if requested
            validation_result = None
            if validate_before_export:
                validation_result = self.validator.validate_map_data(
                    map_data, check_numeric=True, check_dimensions=True
                )

                if not validation_result.is_valid:
                    return IntegrationResult(
                        success=False,
                        operation="export",
                        validation_result=validation_result,
                        errors=validation_result.errors,
                        warnings=validation_result.warnings,
                        metadata={"operation_time": operation_start.isoformat()},
                    )

            # Determine target format
            target_format = None
            if format_name:
                supported_formats = self.core_bridge.get_supported_formats()
                target_format = supported_formats.get(format_name)

                if target_format is None:
                    return IntegrationResult(
                        success=False,
                        operation="export",
                        errors=[f"Unknown format name: {format_name}"],
                        metadata={"operation_time": operation_start.isoformat()},
                    )

            elif custom_format:
                # Convert custom format dict to FTManagerFormat
                try:
                    target_format = self._dict_to_format(custom_format)
                except Exception as e:
                    return IntegrationResult(
                        success=False,
                        operation="export",
                        errors=[f"Invalid custom format: {str(e)}"],
                        metadata={"operation_time": operation_start.isoformat()},
                    )

            # Perform export using core bridge
            export_result = self.core_bridge.export_to_clipboard(
                map_data, target_format=target_format, update_clipboard=True
            )

            # Track operation
            self._track_operation()

            # Compile results
            return IntegrationResult(
                success=export_result.success,
                operation="export",
                data=map_data,
                formatted_output=export_result.formatted_data,
                detected_format=self._format_to_dict(export_result.format_used),
                validation_result=validation_result,
                errors=export_result.errors,
                warnings=export_result.warnings,
                metadata={
                    "operation_time": operation_start.isoformat(),
                    "processing_duration_ms": (datetime.now() - operation_start).total_seconds()
                    * 1000,
                    "data_shape": map_data.shape,
                    "clipboard_updated": export_result.clipboard_updated,
                    "format_used": format_name or "auto",
                    "validation_performed": validate_before_export,
                },
            )

        except Exception as e:
            logger.error("Export operation failed: %s", e)
            return IntegrationResult(
                success=False,
                operation="export",
                errors=[f"Export failed: {str(e)}"],
                metadata={"operation_time": operation_start.isoformat()},
            )

    def detect_clipboard_format(self) -> IntegrationResult:
        """
        Detect FTManager format in current clipboard content.

        Returns:
            IntegrationResult with detection results

        Performance: < 100ms for format detection
        """

        operation_start = datetime.now()

        try:
            # Get clipboard content
            clipboard_result = self.clipboard_manager.get_content()
            if not clipboard_result.success or not clipboard_result.content:
                return IntegrationResult(
                    success=False,
                    operation="detect",
                    errors=["Clipboard is empty or inaccessible"],
                    metadata={"operation_time": operation_start.isoformat()},
                )

            # Detect format
            detection_result = self.format_detector.detect_format(clipboard_result.content)

            # Track operation
            self._track_operation()

            return IntegrationResult(
                success=detection_result.success,
                operation="detect",
                detected_format=self._format_to_dict(detection_result.format_spec),
                errors=detection_result.errors,
                warnings=detection_result.warnings,
                metadata={
                    "operation_time": operation_start.isoformat(),
                    "processing_duration_ms": (datetime.now() - operation_start).total_seconds()
                    * 1000,
                    "confidence_score": detection_result.confidence,
                    "format_candidates": detection_result.candidates,
                },
            )

        except Exception as e:
            logger.error("Format detection failed: %s", e)
            return IntegrationResult(
                success=False,
                operation="detect",
                errors=[f"Detection failed: {str(e)}"],
                metadata={"operation_time": operation_start.isoformat()},
            )

    def validate_clipboard_content(
        self,
        expected_format: Optional[str] = None,
        expected_dimensions: Optional[Tuple[int, int]] = None,
    ) -> IntegrationResult:
        """
        Validate current clipboard content against FTManager requirements.

        Args:
            expected_format: Optional expected format name
            expected_dimensions: Optional expected dimensions

        Returns:
            IntegrationResult with validation results

        Performance: < 200ms for validation operations
        """

        operation_start = datetime.now()

        try:
            # Get clipboard content
            clipboard_result = self.clipboard_manager.get_content()
            if not clipboard_result.success or not clipboard_result.content:
                return IntegrationResult(
                    success=False,
                    operation="validate",
                    errors=["Clipboard is empty or inaccessible"],
                    metadata={"operation_time": operation_start.isoformat()},
                )

            # Get expected format specification if provided
            expected_format_spec = None
            if expected_format:
                supported_formats = self.core_bridge.get_supported_formats()
                expected_format_spec = supported_formats.get(expected_format)

                if expected_format_spec is None:
                    return IntegrationResult(
                        success=False,
                        operation="validate",
                        errors=[f"Unknown expected format: {expected_format}"],
                        metadata={"operation_time": operation_start.isoformat()},
                    )

            # Perform validation
            validation_result = self.validator.validate_clipboard_data(
                clipboard_result.content,
                expected_format=expected_format_spec,
                expected_dimensions=expected_dimensions,
            )

            # Track operation
            self._track_operation()

            return IntegrationResult(
                success=validation_result.is_valid,
                operation="validate",
                validation_result=validation_result,
                errors=validation_result.errors,
                warnings=validation_result.warnings,
                metadata={
                    "operation_time": operation_start.isoformat(),
                    "processing_duration_ms": (datetime.now() - operation_start).total_seconds()
                    * 1000,
                    "expected_format": expected_format,
                    "expected_dimensions": expected_dimensions,
                    "validation_details": validation_result.details,
                },
            )

        except Exception as e:
            logger.error("Validation failed: %s", e)
            return IntegrationResult(
                success=False,
                operation="validate",
                errors=[f"Validation failed: {str(e)}"],
                metadata={"operation_time": operation_start.isoformat()},
            )

    def get_supported_formats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get dictionary of supported FTManager formats.

        Returns:
            Dictionary mapping format names to format specifications
        """

        try:
            core_formats = self.core_bridge.get_supported_formats()

            # Convert to serializable dictionaries
            supported_formats = {}
            for name, format_spec in core_formats.items():
                format_dict = self._format_to_dict(format_spec)
                if format_dict is not None:
                    supported_formats[name] = format_dict

            return supported_formats

        except Exception as e:
            logger.error("Failed to get supported formats: %s", e)
            return {}

    def get_integration_stats(self) -> Dict[str, Any]:
        """
        Get integration bridge statistics and status.

        Returns:
            Dictionary with integration statistics
        """

        try:
            clipboard_status = self.clipboard_manager.get_status()

            return {
                "bridge_initialized": True,
                "operation_count": self.operation_count,
                "last_operation_time": (
                    self.last_operation_time.isoformat() if self.last_operation_time else None
                ),
                "clipboard_status": clipboard_status,
                "supported_format_count": len(self.get_supported_formats()),
                "components_status": {
                    "core_bridge": True,
                    "format_detector": True,
                    "clipboard_manager": clipboard_status["available"],
                    "validator": True,
                },
            }

        except Exception as e:
            logger.error("Failed to get integration stats: %s", e)
            return {"bridge_initialized": False, "error": str(e)}

    def create_streamlit_ui(self) -> None:
        """
        Create professional Streamlit UI for FTManager integration.

        Features:
        - Import/export controls
        - Format detection display
        - Validation feedback
        - Professional styling (no emojis)
        """

        st.markdown(
            """
        <style>
        .ftmanager-container {
            background-color: var(--background-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .ftmanager-header {
            font-weight: 600;
            color: var(--text-color);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .format-info {
            background-color: var(--secondary-background-color);
            border-left: 4px solid var(--primary-color);
            padding: 0.75rem;
            margin: 0.5rem 0;
        }
        
        .success-message {
            color: var(--success-color, #28a745);
            font-weight: 500;
        }
        
        .error-message {
            color: var(--error-color, #dc3545);
            font-weight: 500;
        }
        
        .warning-message {
            color: var(--warning-color, #ffc107);
            font-weight: 500;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="ftmanager-container">', unsafe_allow_html=True)
        st.markdown(
            '<div class="ftmanager-header">FTManager Integration</div>', unsafe_allow_html=True
        )

        # Create tabs for different operations
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Import from Clipboard", "Export to Clipboard", "Format Detection", "Validation"]
        )

        with tab1:
            self._create_import_ui()

        with tab2:
            self._create_export_ui()

        with tab3:
            self._create_detection_ui()

        with tab4:
            self._create_validation_ui()

        st.markdown("</div>", unsafe_allow_html=True)

        # Display integration statistics
        with st.expander("Integration Statistics"):
            stats = self.get_integration_stats()
            st.json(stats)

    # Private helper methods

    def _create_import_ui(self) -> None:
        """Create import tab UI."""

        st.write("Import map data from FTManager via clipboard")

        col1, col2 = st.columns(2)

        with col1:
            validate_data = st.checkbox("Validate data", value=True)
            auto_detect = st.checkbox("Auto-detect format", value=True)

        with col2:
            expected_rows = st.number_input("Expected rows", min_value=1, value=16)
            expected_cols = st.number_input("Expected columns", min_value=1, value=16)

        if st.button("Import from Clipboard", type="primary"):
            with st.spinner("Importing from clipboard..."):
                result = self.import_from_clipboard(
                    validate_data=validate_data,
                    auto_detect_format=auto_detect,
                    expected_dimensions=(expected_rows, expected_cols) if validate_data else None,
                )

            self._display_result(result, "Import")

    def _create_export_ui(self) -> None:
        """Create export tab UI."""

        st.write("Export current map data to clipboard for FTManager")

        # Check if there's map data in session state
        if "current_map_data" not in st.session_state:
            st.warning("No map data available for export")
            return

        map_data = st.session_state["current_map_data"]

        col1, col2 = st.columns(2)

        with col1:
            format_options = ["Auto"] + list(self.get_supported_formats().keys())
            selected_format = st.selectbox("Export format", format_options)

        with col2:
            validate_export = st.checkbox("Validate before export", value=True)

        if st.button("Export to Clipboard", type="primary"):
            with st.spinner("Exporting to clipboard..."):
                result = self.export_to_clipboard(
                    map_data,
                    format_name=selected_format if selected_format != "Auto" else None,
                    validate_before_export=validate_export,
                )

            self._display_result(result, "Export")

    def _create_detection_ui(self) -> None:
        """Create detection tab UI."""

        st.write("Detect FTManager format in current clipboard content")

        if st.button("Detect Format", type="primary"):
            with st.spinner("Detecting format..."):
                result = self.detect_clipboard_format()

            self._display_result(result, "Detection")

    def _create_validation_ui(self) -> None:
        """Create validation tab UI."""

        st.write("Validate current clipboard content")

        col1, col2 = st.columns(2)

        with col1:
            format_options = ["Any"] + list(self.get_supported_formats().keys())
            expected_format = st.selectbox("Expected format", format_options)

        with col2:
            check_dimensions = st.checkbox("Check dimensions", value=True)

        exp_rows = 16
        exp_cols = 16
        if check_dimensions:
            col3, col4 = st.columns(2)
            with col3:
                exp_rows = st.number_input("Expected rows", min_value=1, value=16, key="val_rows")
            with col4:
                exp_cols = st.number_input("Expected cols", min_value=1, value=16, key="val_cols")

        if st.button("Validate Clipboard", type="primary"):
            with st.spinner("Validating clipboard content..."):
                result = self.validate_clipboard_content(
                    expected_format=expected_format if expected_format != "Any" else None,
                    expected_dimensions=(
                        (int(exp_rows), int(exp_cols)) if check_dimensions else None
                    ),
                )

            self._display_result(result, "Validation")

    def _display_result(self, result: IntegrationResult, operation: str) -> None:
        """Display operation result with professional styling."""

        if result.success:
            st.markdown(
                f'<div class="success-message">{operation} completed successfully</div>',
                unsafe_allow_html=True,
            )

            # Display detected format if available
            if result.detected_format:
                st.markdown('<div class="format-info">', unsafe_allow_html=True)
                st.write("**Detected Format:**")
                st.json(result.detected_format)
                st.markdown("</div>", unsafe_allow_html=True)

            # Display data preview if available
            if result.data is not None:
                with st.expander("Data Preview"):
                    st.dataframe(result.data.head(10))

            # Display formatted output if available
            if result.formatted_output:
                with st.expander("Formatted Output"):
                    st.code(
                        result.formatted_output[:1000] + "..."
                        if len(result.formatted_output) > 1000
                        else result.formatted_output
                    )

        else:
            st.markdown(
                f'<div class="error-message">{operation} failed</div>', unsafe_allow_html=True
            )

        # Display errors
        if result.errors:
            st.error("Errors:")
            for error in result.errors:
                st.write(f"• {error}")

        # Display warnings
        if result.warnings:
            st.warning("Warnings:")
            for warning in result.warnings:
                st.write(f"• {warning}")

        # Display metadata
        if result.metadata:
            with st.expander("Operation Details"):
                st.json(result.metadata)

    def _track_operation(self) -> None:
        """Track operation for statistics."""

        self.operation_count += 1
        self.last_operation_time = datetime.now()

    def _format_to_dict(self, format_spec: Any) -> Optional[Dict[str, Any]]:
        """Convert format specification to dictionary."""

        if format_spec is None:
            return None

        try:
            return {
                "format_type": format_spec.format_type,
                "dimensions": format_spec.dimensions,
                "has_headers": format_spec.has_headers,
                "separator": format_spec.separator,
                "decimal_places": format_spec.decimal_places,
                "byte_order": getattr(format_spec, "byte_order", "little"),
                "data_type": getattr(format_spec, "data_type", "float"),
            }
        except Exception as e:
            logger.error("Failed to convert format to dict: %s", e)
            return None

    def _dict_to_format(self, format_dict: Dict[str, Any]) -> Any:
        """Convert dictionary to format specification."""

        try:
            from ..maps.ftmanager import FTManagerFormat

            return FTManagerFormat(
                format_type=format_dict.get("format_type", "tabulated"),
                dimensions=tuple(format_dict.get("dimensions", (16, 16))),
                has_headers=format_dict.get("has_headers", True),
                separator=format_dict.get("separator", "\t"),
                decimal_places=format_dict.get("decimal_places", 2),
                byte_order=format_dict.get("byte_order", "little"),
                data_type=format_dict.get("data_type", "float"),
            )
        except Exception as e:
            logger.error("Failed to convert dict to format: %s", e)
            raise
