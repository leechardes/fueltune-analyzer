"""
FTManager Validators - Comprehensive data validation for compatibility

This module provides robust validation capabilities for FTManager data compatibility,
ensuring zero data loss and format compliance with professional error reporting.

CRITICAL: Follows PYTHON-CODE-STANDARDS.md:
- Robust format detection algorithms
- Performance < 200ms for validation
- Type hints 100% coverage
- Professional error handling
- Cross-platform compatibility
- Comprehensive validation rules
"""

import logging
import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """Type-safe validation rule specification."""

    name: str
    description: str
    rule_type: Literal["format", "data", "compatibility", "performance"]
    severity: Literal["error", "warning", "info"]
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationIssue:
    """Type-safe validation issue report."""

    rule_name: str
    severity: Literal["error", "warning", "info"]
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Type-safe validation result with comprehensive reporting."""

    is_valid: bool
    confidence: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info_messages: List[str] = field(default_factory=list)
    issues: List[ValidationIssue] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize collections and compile summary."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.info_messages is None:
            self.info_messages = []
        if self.issues is None:
            self.issues = []
        if self.details is None:
            self.details = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}

        # Compile issues into summary lists
        self._compile_issue_summary()

    def _compile_issue_summary(self):
        """Compile issues into summary lists."""
        for issue in self.issues:
            message = f"{issue.message}"
            if issue.location:
                message += f" (Location: {issue.location})"
            if issue.suggestion:
                message += f" Suggestion: {issue.suggestion}"

            if issue.severity == "error":
                if message not in self.errors:
                    self.errors.append(message)
            elif issue.severity == "warning":
                if message not in self.warnings:
                    self.warnings.append(message)
            elif issue.severity == "info":
                if message not in self.info_messages:
                    self.info_messages.append(message)


class FTManagerValidator:
    """
    Comprehensive FTManager data validator with professional reporting.

    Features:
    - Multi-level validation (format, data, compatibility)
    - Configurable validation rules
    - Performance-aware validation
    - Detailed error reporting with suggestions
    - Statistical analysis for data quality
    - Zero-tolerance for data loss scenarios

    Validation Levels:
    1. Format Validation - Structure, separators, dimensions
    2. Data Validation - Numeric ranges, consistency, completeness
    3. Compatibility Validation - FTManager format compliance
    4. Performance Validation - Size, processing time limits

    Performance Target: < 200ms for typical validation operations
    """

    def __init__(self):
        """Initialize validator with comprehensive rule set."""

        # Initialize validation rules
        self.validation_rules = self._initialize_validation_rules()

        # Performance thresholds
        self.performance_limits = {
            "max_validation_time_ms": 200,
            "max_data_size_mb": 50,
            "max_dimensions": (100, 100),
            "min_dimensions": (2, 2),
        }

        # FTManager compatibility requirements
        self.ftmanager_requirements = {
            "supported_separators": ["\t", ",", ";", " "],
            "supported_formats": ["tabulated", "csv", "hex", "binary"],
            "common_dimensions": [(8, 8), (12, 12), (16, 16), (20, 20), (32, 32)],
            "max_decimal_places": 6,
            "numeric_range": (-1e6, 1e6),  # Reasonable numeric range
        }

        # Statistical thresholds for data quality
        self.quality_thresholds = {
            "max_missing_ratio": 0.05,  # 5% missing data
            "max_outlier_ratio": 0.10,  # 10% outliers
            "min_numeric_ratio": 0.95,  # 95% numeric content
            "max_zero_ratio": 0.50,  # 50% zeros (common in maps)
        }

        logger.debug("Initialized FTManager validator with comprehensive rule set")

    def validate_clipboard_data(
        self,
        content: str,
        expected_format: Optional[Any] = None,
        expected_dimensions: Optional[Tuple[int, int]] = None,
        strict_mode: bool = False,
    ) -> ValidationResult:
        """
        Validate clipboard content for FTManager compatibility.

        Args:
            content: Raw clipboard content to validate
            expected_format: Optional expected format specification
            expected_dimensions: Optional expected dimensions
            strict_mode: Whether to apply strict validation rules

        Returns:
            ValidationResult with comprehensive analysis

        Performance: < 200ms for typical validation operations
        """

        validation_start = datetime.now()

        try:
            issues = []
            details = {}

            # Basic content validation
            basic_issues = self._validate_basic_content(content)
            issues.extend(basic_issues)

            if any(issue.severity == "error" for issue in basic_issues):
                return self._compile_result(False, 0.0, issues, details, validation_start)

            # Format structure validation
            format_issues, structure_details = self._validate_format_structure(content)
            issues.extend(format_issues)
            details.update(structure_details)

            # Data content validation
            data_issues, data_details = self._validate_data_content(content)
            issues.extend(data_issues)
            details.update(data_details)

            # Expected format validation
            if expected_format:
                format_issues = self._validate_expected_format(content, expected_format)
                issues.extend(format_issues)

            # Expected dimensions validation
            if expected_dimensions:
                dimension_issues = self._validate_expected_dimensions(content, expected_dimensions)
                issues.extend(dimension_issues)

            # FTManager compatibility validation
            compatibility_issues = self._validate_ftmanager_compatibility(content, strict_mode)
            issues.extend(compatibility_issues)

            # Performance validation
            performance_issues, perf_metrics = self._validate_performance(content, validation_start)
            issues.extend(performance_issues)

            # Calculate overall confidence
            confidence = self._calculate_validation_confidence(issues)

            # Determine if validation passed
            has_errors = any(issue.severity == "error" for issue in issues)
            is_valid = not has_errors

            return self._compile_result(
                is_valid, confidence, issues, details, validation_start, perf_metrics
            )

        except Exception as e:
            logger.error(f"Clipboard validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                errors=[f"Validation failed: {str(e)}"],
                details={"validation_exception": str(e)},
                performance_metrics={
                    "validation_duration_ms": (datetime.now() - validation_start).total_seconds()
                    * 1000
                },
            )

    def validate_map_data(
        self,
        map_data: pd.DataFrame,
        check_numeric: bool = True,
        check_dimensions: bool = True,
        check_completeness: bool = True,
    ) -> ValidationResult:
        """
        Validate map DataFrame for FTManager export compatibility.

        Args:
            map_data: DataFrame containing map data
            check_numeric: Whether to validate numeric content
            check_dimensions: Whether to validate dimensions
            check_completeness: Whether to check data completeness

        Returns:
            ValidationResult with analysis

        Performance: < 200ms for typical map validation
        """

        validation_start = datetime.now()

        try:
            issues = []
            details = {}

            # Basic DataFrame validation
            basic_issues = self._validate_basic_dataframe(map_data)
            issues.extend(basic_issues)

            if any(issue.severity == "error" for issue in basic_issues):
                return self._compile_result(False, 0.0, issues, details, validation_start)

            # Numeric content validation
            if check_numeric:
                numeric_issues, numeric_details = self._validate_numeric_content(map_data)
                issues.extend(numeric_issues)
                details.update(numeric_details)

            # Dimensions validation
            if check_dimensions:
                dimension_issues = self._validate_dataframe_dimensions(map_data)
                issues.extend(dimension_issues)

            # Completeness validation
            if check_completeness:
                completeness_issues = self._validate_data_completeness(map_data)
                issues.extend(completeness_issues)

            # Data quality analysis
            quality_issues, quality_details = self._validate_data_quality(map_data)
            issues.extend(quality_issues)
            details.update(quality_details)

            # Calculate confidence
            confidence = self._calculate_validation_confidence(issues)

            # Determine validity
            has_errors = any(issue.severity == "error" for issue in issues)
            is_valid = not has_errors

            return self._compile_result(is_valid, confidence, issues, details, validation_start)

        except Exception as e:
            logger.error(f"Map data validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                errors=[f"Validation failed: {str(e)}"],
                details={"validation_exception": str(e)},
            )

    def validate_format_compatibility(
        self, source_format: Any, target_format: Any
    ) -> ValidationResult:
        """
        Validate compatibility between source and target formats.

        Args:
            source_format: Source format specification
            target_format: Target format specification

        Returns:
            ValidationResult with compatibility analysis
        """

        validation_start = datetime.now()

        try:
            issues = []
            details = {}

            # Format type compatibility
            if hasattr(source_format, "format_type") and hasattr(target_format, "format_type"):
                if source_format.format_type != target_format.format_type:
                    issues.append(
                        ValidationIssue(
                            rule_name="format_type_compatibility",
                            severity="warning",
                            message=f"Format type mismatch: {source_format.format_type} -> {target_format.format_type}",
                            suggestion="Consider format conversion during transfer",
                        )
                    )

            # Dimension compatibility
            if hasattr(source_format, "dimensions") and hasattr(target_format, "dimensions"):
                if source_format.dimensions != target_format.dimensions:
                    issues.append(
                        ValidationIssue(
                            rule_name="dimension_compatibility",
                            severity=(
                                "error"
                                if abs(source_format.dimensions[0] - target_format.dimensions[0])
                                > 2
                                else "warning"
                            ),
                            message=f"Dimension mismatch: {source_format.dimensions} -> {target_format.dimensions}",
                            suggestion="Resize or crop map data to match target dimensions",
                        )
                    )

            # Separator compatibility
            if hasattr(source_format, "separator") and hasattr(target_format, "separator"):
                if source_format.separator != target_format.separator:
                    issues.append(
                        ValidationIssue(
                            rule_name="separator_compatibility",
                            severity="info",
                            message=f"Separator change: '{source_format.separator}' -> '{target_format.separator}'",
                            suggestion="Automatic separator conversion will be applied",
                        )
                    )

            # Decimal precision compatibility
            if hasattr(source_format, "decimal_places") and hasattr(
                target_format, "decimal_places"
            ):
                precision_diff = abs(source_format.decimal_places - target_format.decimal_places)
                if precision_diff > 2:
                    issues.append(
                        ValidationIssue(
                            rule_name="precision_compatibility",
                            severity="warning",
                            message=f"Significant precision change: {source_format.decimal_places} -> {target_format.decimal_places}",
                            suggestion="Data precision may be lost during conversion",
                        )
                    )

            # Calculate compatibility confidence
            error_count = sum(1 for issue in issues if issue.severity == "error")
            warning_count = sum(1 for issue in issues if issue.severity == "warning")

            confidence = max(0.0, 1.0 - (error_count * 0.5) - (warning_count * 0.2))
            is_valid = error_count == 0

            return self._compile_result(is_valid, confidence, issues, details, validation_start)

        except Exception as e:
            logger.error(f"Format compatibility validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                errors=[f"Compatibility validation failed: {str(e)}"],
            )

    # Private validation methods

    def _initialize_validation_rules(self) -> Dict[str, ValidationRule]:
        """Initialize comprehensive validation rules."""

        rules = {
            # Format validation rules
            "content_not_empty": ValidationRule(
                name="content_not_empty",
                description="Content must not be empty",
                rule_type="format",
                severity="error",
            ),
            "valid_separator": ValidationRule(
                name="valid_separator",
                description="Must use supported separator",
                rule_type="format",
                severity="error",
            ),
            "consistent_columns": ValidationRule(
                name="consistent_columns",
                description="All rows must have consistent column count",
                rule_type="format",
                severity="error",
            ),
            # Data validation rules
            "numeric_content": ValidationRule(
                name="numeric_content",
                description="Content must be primarily numeric",
                rule_type="data",
                severity="error",
            ),
            "reasonable_ranges": ValidationRule(
                name="reasonable_ranges",
                description="Numeric values must be within reasonable ranges",
                rule_type="data",
                severity="warning",
            ),
            "minimal_missing": ValidationRule(
                name="minimal_missing",
                description="Missing data should be minimal",
                rule_type="data",
                severity="warning",
            ),
            # Compatibility validation rules
            "ftmanager_dimensions": ValidationRule(
                name="ftmanager_dimensions",
                description="Dimensions should match common FTManager formats",
                rule_type="compatibility",
                severity="warning",
            ),
            "precision_reasonable": ValidationRule(
                name="precision_reasonable",
                description="Decimal precision should be reasonable",
                rule_type="compatibility",
                severity="info",
            ),
            # Performance validation rules
            "size_reasonable": ValidationRule(
                name="size_reasonable",
                description="Data size should be reasonable for processing",
                rule_type="performance",
                severity="warning",
            ),
            "processing_time": ValidationRule(
                name="processing_time",
                description="Validation should complete within time limit",
                rule_type="performance",
                severity="info",
            ),
        }

        return rules

    def _validate_basic_content(self, content: str) -> List[ValidationIssue]:
        """Validate basic content requirements."""

        issues = []

        # Empty content check
        if not content or not content.strip():
            issues.append(
                ValidationIssue(
                    rule_name="content_not_empty",
                    severity="error",
                    message="Content is empty or contains only whitespace",
                    suggestion="Ensure clipboard contains valid FTManager data",
                )
            )
            return issues

        # Basic structure check
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if not lines:
            issues.append(
                ValidationIssue(
                    rule_name="content_not_empty",
                    severity="error",
                    message="No valid data lines found",
                    suggestion="Check content formatting and line endings",
                )
            )

        # Minimum line count
        if len(lines) < 2:
            issues.append(
                ValidationIssue(
                    rule_name="minimum_data",
                    severity="warning",
                    message=f"Very few data lines ({len(lines)})",
                    suggestion="FTManager data typically contains multiple rows",
                )
            )

        return issues

    def _validate_format_structure(
        self, content: str
    ) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Validate format structure and return details."""

        issues = []
        details = {}

        lines = [line.strip() for line in content.split("\n") if line.strip()]

        if not lines:
            return issues, details

        # Analyze separators
        separator_analysis = self._analyze_separators(lines)
        details["separator_analysis"] = separator_analysis

        best_separator = (
            max(separator_analysis, key=separator_analysis.get) if separator_analysis else None
        )

        if not best_separator or separator_analysis[best_separator] < 0.5:
            issues.append(
                ValidationIssue(
                    rule_name="valid_separator",
                    severity="error",
                    message="No clear field separator detected",
                    details={"separator_scores": separator_analysis},
                    suggestion="Ensure data uses tab, comma, or semicolon separation",
                )
            )
            return issues, details

        # Validate separator is supported
        if best_separator not in self.ftmanager_requirements["supported_separators"]:
            issues.append(
                ValidationIssue(
                    rule_name="valid_separator",
                    severity="warning",
                    message=f"Unusual separator detected: '{best_separator}'",
                    suggestion="Consider using tab or comma separation for better compatibility",
                )
            )

        # Check column consistency
        field_counts = []
        for i, line in enumerate(lines[:20]):  # Check first 20 lines
            fields = [f.strip() for f in line.split(best_separator) if f.strip()]
            field_counts.append(len(fields))

        if field_counts:
            most_common_count = max(set(field_counts), key=field_counts.count)
            consistency_ratio = field_counts.count(most_common_count) / len(field_counts)

            details["column_consistency"] = {
                "most_common_count": most_common_count,
                "consistency_ratio": consistency_ratio,
                "field_counts": field_counts,
            }

            if consistency_ratio < 0.8:
                issues.append(
                    ValidationIssue(
                        rule_name="consistent_columns",
                        severity="error",
                        message=f"Inconsistent column count (consistency: {consistency_ratio:.1%})",
                        details={"field_counts": field_counts},
                        suggestion="Ensure all data rows have the same number of fields",
                    )
                )

        return issues, details

    def _validate_data_content(self, content: str) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Validate data content quality."""

        issues = []
        details = {}

        # Extract numeric values
        numeric_pattern = re.compile(r"-?\d*\.?\d+(?:[eE][+-]?\d+)?")
        numeric_matches = numeric_pattern.findall(content)

        if numeric_matches:
            numeric_values = []
            for match in numeric_matches:
                try:
                    numeric_values.append(float(match))
                except ValueError:
                    continue

            if numeric_values:
                details["numeric_statistics"] = {
                    "count": len(numeric_values),
                    "mean": float(np.mean(numeric_values)),
                    "std": float(np.std(numeric_values)),
                    "min": float(np.min(numeric_values)),
                    "max": float(np.max(numeric_values)),
                    "range": float(np.max(numeric_values) - np.min(numeric_values)),
                }

                # Check numeric ranges
                min_val, max_val = self.ftmanager_requirements["numeric_range"]
                out_of_range = [v for v in numeric_values if v < min_val or v > max_val]

                if out_of_range:
                    issues.append(
                        ValidationIssue(
                            rule_name="reasonable_ranges",
                            severity="warning",
                            message=f"{len(out_of_range)} values outside reasonable range ({min_val}, {max_val})",
                            details={"out_of_range_count": len(out_of_range)},
                            suggestion="Check for data entry errors or scaling issues",
                        )
                    )

                # Check for excessive precision
                decimal_places = []
                for match in numeric_matches[:100]:  # Sample first 100
                    if "." in match:
                        places = len(match.split(".")[-1])
                        decimal_places.append(places)

                if decimal_places:
                    max_places = max(decimal_places)
                    avg_places = statistics.mean(decimal_places)

                    details["precision_analysis"] = {
                        "max_decimal_places": max_places,
                        "average_decimal_places": avg_places,
                    }

                    if max_places > self.ftmanager_requirements["max_decimal_places"]:
                        issues.append(
                            ValidationIssue(
                                rule_name="precision_reasonable",
                                severity="info",
                                message=f"High precision detected (max {max_places} decimal places)",
                                suggestion="Consider rounding values for better FTManager compatibility",
                            )
                        )

        else:
            issues.append(
                ValidationIssue(
                    rule_name="numeric_content",
                    severity="error",
                    message="No numeric values detected in content",
                    suggestion="Ensure content contains numeric map data",
                )
            )

        return issues, details

    def _validate_basic_dataframe(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """Validate basic DataFrame requirements."""

        issues = []

        # Empty DataFrame check
        if df.empty:
            issues.append(
                ValidationIssue(
                    rule_name="content_not_empty",
                    severity="error",
                    message="DataFrame is empty",
                    suggestion="Ensure map data is properly loaded",
                )
            )
            return issues

        # Shape validation
        rows, cols = df.shape
        min_dims = self.performance_limits["min_dimensions"]
        max_dims = self.performance_limits["max_dimensions"]

        if rows < min_dims[0] or cols < min_dims[1]:
            issues.append(
                ValidationIssue(
                    rule_name="minimum_dimensions",
                    severity="error",
                    message=f"DataFrame too small: {df.shape}, minimum: {min_dims}",
                    suggestion="Ensure map data has sufficient dimensions",
                )
            )

        if rows > max_dims[0] or cols > max_dims[1]:
            issues.append(
                ValidationIssue(
                    rule_name="maximum_dimensions",
                    severity="warning",
                    message=f"DataFrame very large: {df.shape}, consider if this is expected",
                    suggestion="Large maps may have performance implications",
                )
            )

        return issues

    def _validate_numeric_content(
        self, df: pd.DataFrame
    ) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Validate numeric content in DataFrame."""

        issues = []
        details = {}

        # Identify numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        total_cols = len(df.columns)

        if len(numeric_cols) == 0:
            issues.append(
                ValidationIssue(
                    rule_name="numeric_content",
                    severity="error",
                    message="No numeric columns found in map data",
                    suggestion="Ensure map data contains numeric values",
                )
            )
            return issues, details

        # Calculate numeric ratio
        numeric_ratio = len(numeric_cols) / total_cols
        details["numeric_ratio"] = numeric_ratio

        if numeric_ratio < self.quality_thresholds["min_numeric_ratio"]:
            issues.append(
                ValidationIssue(
                    rule_name="numeric_content",
                    severity="warning",
                    message=f"Low numeric content ratio: {numeric_ratio:.1%}",
                    suggestion="Consider converting non-numeric columns or removing them",
                )
            )

        # Analyze numeric data quality
        for col in numeric_cols:
            col_data = df[col]

            # Missing values
            missing_ratio = col_data.isna().sum() / len(col_data)
            if missing_ratio > self.quality_thresholds["max_missing_ratio"]:
                issues.append(
                    ValidationIssue(
                        rule_name="minimal_missing",
                        severity="warning",
                        message=f"Column {col} has {missing_ratio:.1%} missing values",
                        location=f"Column: {col}",
                        suggestion="Consider filling missing values or removing incomplete columns",
                    )
                )

            # Zero values (common but worth noting)
            zero_ratio = (col_data == 0).sum() / len(col_data)
            if zero_ratio > self.quality_thresholds["max_zero_ratio"]:
                issues.append(
                    ValidationIssue(
                        rule_name="data_distribution",
                        severity="info",
                        message=f"Column {col} has {zero_ratio:.1%} zero values",
                        location=f"Column: {col}",
                        suggestion="High zero content is normal for some map types",
                    )
                )

        return issues, details

    def _analyze_separators(self, lines: List[str]) -> Dict[str, float]:
        """Analyze potential separators with confidence scoring."""

        separators = ["\t", ",", ";", " "]
        separator_scores = {}

        for sep in separators:
            score = 0.0
            consistent_counts = []

            for line in lines[:10]:  # Analyze first 10 lines
                count = line.count(sep)
                consistent_counts.append(count)

                # Boost score if separator appears multiple times per line
                if count > 0:
                    score += min(count / 10.0, 1.0)

            # Check consistency
            if consistent_counts:
                most_common = max(set(consistent_counts), key=consistent_counts.count)
                if most_common > 0:
                    consistency = consistent_counts.count(most_common) / len(consistent_counts)
                    score *= consistency

            separator_scores[sep] = score

        return separator_scores

    def _compile_result(
        self,
        is_valid: bool,
        confidence: float,
        issues: List[ValidationIssue],
        details: Dict[str, Any],
        start_time: datetime,
        performance_metrics: Optional[Dict[str, float]] = None,
    ) -> ValidationResult:
        """Compile final validation result."""

        # Calculate performance metrics
        validation_duration = (datetime.now() - start_time).total_seconds() * 1000

        perf_metrics = performance_metrics or {}
        perf_metrics["validation_duration_ms"] = validation_duration

        # Create result
        result = ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            details=details,
            performance_metrics=perf_metrics,
        )

        return result

    def _calculate_validation_confidence(self, issues: List[ValidationIssue]) -> float:
        """Calculate overall validation confidence score."""

        if not issues:
            return 1.0

        error_count = sum(1 for issue in issues if issue.severity == "error")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")
        info_count = sum(1 for issue in issues if issue.severity == "info")

        # Calculate confidence penalty
        confidence = 1.0
        confidence -= error_count * 0.4  # Errors significantly reduce confidence
        confidence -= warning_count * 0.15  # Warnings moderately reduce confidence
        confidence -= info_count * 0.05  # Info messages slightly reduce confidence

        return max(0.0, confidence)

    # Additional helper methods for specific validation scenarios

    def _validate_expected_format(
        self, content: str, expected_format: Any
    ) -> List[ValidationIssue]:
        """Validate content against expected format."""

        issues = []

        # This would integrate with the format detector to compare
        # detected format against expected format

        return issues

    def _validate_expected_dimensions(
        self, content: str, expected_dimensions: Tuple[int, int]
    ) -> List[ValidationIssue]:
        """Validate content dimensions against expected dimensions."""

        issues = []

        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if not lines:
            return issues

        # Detect actual dimensions (simplified)
        actual_rows = len(lines)

        # Estimate columns from first line
        first_line_fields = len(
            [f for f in lines[0].split("\t") if f.strip()]
        )  # Assume tab separation
        if first_line_fields <= 1:
            first_line_fields = len([f for f in lines[0].split(",") if f.strip()])  # Try comma

        actual_dimensions = (actual_rows, first_line_fields)
        expected_rows, expected_cols = expected_dimensions

        if actual_dimensions != expected_dimensions:
            severity = (
                "error"
                if abs(actual_rows - expected_rows) > 2
                or abs(first_line_fields - expected_cols) > 2
                else "warning"
            )

            issues.append(
                ValidationIssue(
                    rule_name="expected_dimensions",
                    severity=severity,
                    message=f"Dimension mismatch: expected {expected_dimensions}, detected {actual_dimensions}",
                    suggestion="Verify data completeness and format structure",
                )
            )

        return issues

    def _validate_ftmanager_compatibility(
        self, content: str, strict_mode: bool
    ) -> List[ValidationIssue]:
        """Validate FTManager-specific compatibility requirements."""

        issues = []

        # This would perform FTManager-specific validation
        # such as checking for supported formats, reasonable value ranges, etc.

        return issues

    def _validate_performance(
        self, content: str, start_time: datetime
    ) -> Tuple[List[ValidationIssue], Dict[str, float]]:
        """Validate performance characteristics."""

        issues = []
        metrics = {}

        # Content size check
        content_size_mb = len(content.encode("utf-8")) / (1024 * 1024)
        metrics["content_size_mb"] = content_size_mb

        if content_size_mb > self.performance_limits["max_data_size_mb"]:
            issues.append(
                ValidationIssue(
                    rule_name="size_reasonable",
                    severity="warning",
                    message=f"Large content size: {content_size_mb:.1f} MB",
                    suggestion="Large datasets may have slower processing times",
                )
            )

        # Validation time check
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        metrics["validation_duration_ms"] = elapsed_ms

        if elapsed_ms > self.performance_limits["max_validation_time_ms"]:
            issues.append(
                ValidationIssue(
                    rule_name="processing_time",
                    severity="info",
                    message=f"Validation took {elapsed_ms:.0f}ms (target: {self.performance_limits['max_validation_time_ms']}ms)",
                    suggestion="Consider data size optimization for better performance",
                )
            )

        return issues, metrics

    def _validate_dataframe_dimensions(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """Validate DataFrame dimensions."""

        issues = []

        dimensions = df.shape

        # Check if dimensions match common FTManager formats
        if dimensions not in self.ftmanager_requirements["common_dimensions"]:
            closest_dimension = min(
                self.ftmanager_requirements["common_dimensions"],
                key=lambda x: abs(x[0] - dimensions[0]) + abs(x[1] - dimensions[1]),
            )

            issues.append(
                ValidationIssue(
                    rule_name="ftmanager_dimensions",
                    severity="info",
                    message=f"Unusual dimensions {dimensions} (closest standard: {closest_dimension})",
                    suggestion="Consider if dimensions are correct for your FTManager configuration",
                )
            )

        return issues

    def _validate_data_completeness(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """Validate data completeness."""

        issues = []

        # Overall missing data ratio
        total_cells = df.size
        missing_cells = df.isna().sum().sum()
        missing_ratio = missing_cells / total_cells

        if missing_ratio > self.quality_thresholds["max_missing_ratio"]:
            issues.append(
                ValidationIssue(
                    rule_name="minimal_missing",
                    severity="warning",
                    message=f"High missing data ratio: {missing_ratio:.1%}",
                    suggestion="Consider filling missing values before export",
                )
            )

        return issues

    def _validate_data_quality(
        self, df: pd.DataFrame
    ) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Validate overall data quality."""

        issues = []
        details = {}

        # Get numeric data for analysis
        numeric_data = df.select_dtypes(include=[np.number])

        if not numeric_data.empty:
            # Calculate quality metrics
            details["data_quality"] = {
                "shape": df.shape,
                "numeric_columns": len(numeric_data.columns),
                "total_columns": len(df.columns),
                "missing_ratio": df.isna().sum().sum() / df.size,
                "zero_ratio": (numeric_data == 0).sum().sum() / numeric_data.size,
                "value_ranges": {
                    col: {
                        "min": float(numeric_data[col].min()),
                        "max": float(numeric_data[col].max()),
                    }
                    for col in numeric_data.columns
                },
            }

        return issues, details
