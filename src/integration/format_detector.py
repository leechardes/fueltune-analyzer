"""
FTManager Format Detector - Advanced format detection algorithms

This module provides sophisticated format detection capabilities for FTManager
data with high accuracy and confidence scoring.

CRITICAL: Follows PYTHON-CODE-STANDARDS.md:
- Robust format detection algorithms
- Performance < 100ms for detection
- Type hints 100% coverage
- Professional error handling
- Cross-platform compatibility
"""

import logging
import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class FormatCandidate:
    """Type-safe format candidate with confidence score."""

    format_type: Literal["tabulated", "csv", "hex", "binary"]
    separator: str
    dimensions: Tuple[int, int]
    has_headers: bool
    decimal_places: int
    confidence: float
    evidence: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate candidate parameters."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.dimensions[0] <= 0 or self.dimensions[1] <= 0:
            raise ValueError("Dimensions must be positive")


@dataclass
class DetectionResult:
    """Type-safe format detection result."""

    success: bool
    format_spec: Optional[Any] = None
    confidence: float = 0.0
    candidates: List[FormatCandidate] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    detection_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize empty collections if None."""
        if self.candidates is None:
            self.candidates = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.detection_metadata is None:
            self.detection_metadata = {}


class FTManagerFormatDetector:
    """
    Advanced FTManager format detection with machine learning-inspired scoring.

    Features:
    - Multi-stage detection pipeline
    - Confidence scoring with evidence tracking
    - Pattern recognition for various FTManager formats
    - Robust handling of edge cases and noise
    - Performance optimized for real-time detection

    Detection Pipeline:
    1. Content preprocessing and cleaning
    2. Separator detection with statistical analysis
    3. Dimension analysis with validation
    4. Header detection using heuristics
    5. Data type and precision analysis
    6. Confidence scoring and ranking

    Performance Target: < 100ms for typical detection operations
    """

    def __init__(self):
        """Initialize format detector with detection patterns and weights."""

        # Define separator patterns and their typical contexts
        self.separator_patterns = {
            "\t": {
                "name": "tab",
                "regex": re.compile(r"\t"),
                "weight": 0.9,  # High weight for FTManager standard
                "context": "tabulated",
            },
            ",": {"name": "comma", "regex": re.compile(r","), "weight": 0.7, "context": "csv"},
            ";": {
                "name": "semicolon",
                "regex": re.compile(r";"),
                "weight": 0.6,
                "context": "csv_european",
            },
            " ": {
                "name": "space",
                "regex": re.compile(r" {2,}"),  # Multiple spaces
                "weight": 0.5,
                "context": "space_separated",
            },
        }

        # Define format type patterns
        self.format_patterns = {
            "tabulated": {
                "pattern": re.compile(r"^[\d\.\-\+\s\t]+$", re.MULTILINE),
                "weight": 0.9,
                "description": "Tab-separated numeric data",
            },
            "csv": {
                "pattern": re.compile(r"^[\d\.\-\+,;\s]+$", re.MULTILINE),
                "weight": 0.8,
                "description": "Comma/semicolon separated values",
            },
            "hex": {
                "pattern": re.compile(r"^[0-9A-Fa-f\s\t]+$", re.MULTILINE),
                "weight": 0.7,
                "description": "Hexadecimal data format",
            },
            "binary": {
                "pattern": re.compile(r"^[01\s\t]+$", re.MULTILINE),
                "weight": 0.6,
                "description": "Binary data format",
            },
        }

        # Define common FTManager dimensions with confidence weights
        self.common_dimensions = {
            (16, 16): 0.9,  # Most common FTManager format
            (20, 20): 0.8,  # Common for larger maps
            (12, 12): 0.7,  # Smaller maps
            (8, 8): 0.6,  # Very small maps
            (32, 32): 0.5,  # Large maps (less common)
        }

        # Header detection patterns
        self.header_patterns = [
            re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$"),  # Variable names
            re.compile(r"^[A-Z][a-z]+$"),  # Title case
            re.compile(r"^[a-z]+$"),  # Lowercase
            re.compile(r"^[A-Z]+$"),  # Uppercase
        ]

        # Numeric patterns for data validation
        self.numeric_patterns = {
            "integer": re.compile(r"^-?\d+$"),
            "float": re.compile(r"^-?\d*\.?\d+$"),
            "scientific": re.compile(r"^-?\d*\.?\d+[eE][+-]?\d+$"),
            "hex": re.compile(r"^[0-9A-Fa-f]+$"),
        }

        logger.debug("Initialized FTManager format detector with pattern recognition")

    def detect_format(
        self, content: str, confidence_threshold: float = 0.7, max_candidates: int = 5
    ) -> DetectionResult:
        """
        Detect FTManager format with comprehensive analysis.

        Args:
            content: Raw content to analyze
            confidence_threshold: Minimum confidence for successful detection
            max_candidates: Maximum number of candidates to return

        Returns:
            DetectionResult with format specification and confidence

        Performance: < 100ms for typical content analysis
        """

        detection_start = datetime.now()

        try:
            # Validate input
            if not content or not content.strip():
                return DetectionResult(
                    success=False,
                    errors=["Content is empty or whitespace only"],
                    detection_metadata={"detection_time": detection_start.isoformat()},
                )

            # Preprocess content
            cleaned_content, preprocessing_warnings = self._preprocess_content(content)

            # Generate format candidates
            candidates = self._generate_candidates(cleaned_content)

            if not candidates:
                return DetectionResult(
                    success=False,
                    errors=["No valid format candidates detected"],
                    warnings=preprocessing_warnings,
                    detection_metadata={
                        "detection_time": detection_start.isoformat(),
                        "content_length": len(content),
                        "cleaned_length": len(cleaned_content),
                    },
                )

            # Sort candidates by confidence and limit
            candidates.sort(key=lambda x: x.confidence, reverse=True)
            top_candidates = candidates[:max_candidates]

            # Select best candidate
            best_candidate = top_candidates[0]

            # Check confidence threshold
            success = best_candidate.confidence >= confidence_threshold

            # Convert to format specification if successful
            format_spec = None
            if success:
                format_spec = self._candidate_to_format_spec(best_candidate)

            # Compile detection metadata
            detection_duration = (datetime.now() - detection_start).total_seconds() * 1000

            return DetectionResult(
                success=success,
                format_spec=format_spec,
                confidence=best_candidate.confidence,
                candidates=top_candidates,
                errors=(
                    []
                    if success
                    else [
                        f"Confidence {best_candidate.confidence:.2f} below threshold {confidence_threshold}"
                    ]
                ),
                warnings=preprocessing_warnings,
                detection_metadata={
                    "detection_time": detection_start.isoformat(),
                    "detection_duration_ms": detection_duration,
                    "content_analysis": {
                        "original_length": len(content),
                        "cleaned_length": len(cleaned_content),
                        "line_count": len(cleaned_content.split("\n")),
                        "preprocessing_warnings": len(preprocessing_warnings),
                    },
                    "candidate_analysis": {
                        "total_candidates": len(candidates),
                        "returned_candidates": len(top_candidates),
                        "confidence_range": (
                            [candidates[-1].confidence, candidates[0].confidence]
                            if candidates
                            else [0, 0]
                        ),
                    },
                    "best_candidate_evidence": best_candidate.evidence,
                },
            )

        except Exception as e:
            logger.error(f"Format detection failed: {e}")
            return DetectionResult(
                success=False,
                errors=[f"Detection failed: {str(e)}"],
                detection_metadata={"detection_time": detection_start.isoformat()},
            )

    def analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """
        Analyze content structure for debugging and insight.

        Args:
            content: Content to analyze

        Returns:
            Dictionary with structural analysis results
        """

        try:
            lines = [line.strip() for line in content.split("\n") if line.strip()]

            if not lines:
                return {"error": "No content lines found"}

            # Basic statistics
            line_lengths = [len(line) for line in lines]
            char_frequencies = {}
            numeric_lines = 0

            for line in lines:
                for char in line:
                    char_frequencies[char] = char_frequencies.get(char, 0) + 1

                # Check if line is primarily numeric
                numeric_chars = sum(1 for c in line if c.isdigit() or c in ".-+")
                if len(line) > 0 and numeric_chars / len(line) > 0.7:
                    numeric_lines += 1

            # Separator analysis
            separator_analysis = {}
            for sep_char, sep_info in self.separator_patterns.items():
                count = char_frequencies.get(sep_char, 0)
                separator_analysis[sep_info["name"]] = {
                    "count": count,
                    "frequency": count / sum(char_frequencies.values()) if char_frequencies else 0,
                    "average_per_line": count / len(lines) if lines else 0,
                }

            return {
                "line_statistics": {
                    "total_lines": len(lines),
                    "average_length": statistics.mean(line_lengths) if line_lengths else 0,
                    "length_std": statistics.stdev(line_lengths) if len(line_lengths) > 1 else 0,
                    "min_length": min(line_lengths) if line_lengths else 0,
                    "max_length": max(line_lengths) if line_lengths else 0,
                },
                "character_analysis": {
                    "total_characters": sum(char_frequencies.values()),
                    "unique_characters": len(char_frequencies),
                    "most_common": sorted(
                        char_frequencies.items(), key=lambda x: x[1], reverse=True
                    )[:10],
                },
                "separator_analysis": separator_analysis,
                "content_type": {
                    "numeric_lines": numeric_lines,
                    "numeric_ratio": numeric_lines / len(lines) if lines else 0,
                    "likely_data_format": numeric_lines / len(lines) > 0.8 if lines else False,
                },
            }

        except Exception as e:
            logger.error(f"Content structure analysis failed: {e}")
            return {"error": str(e)}

    # Private methods for detection pipeline

    def _preprocess_content(self, content: str) -> Tuple[str, List[str]]:
        """Preprocess content for analysis."""

        warnings = []

        # Remove excessive whitespace and normalize line endings
        cleaned = re.sub(r"\r\n|\r", "\n", content)
        cleaned = re.sub(r"\n\s*\n", "\n", cleaned)  # Remove empty lines
        cleaned = cleaned.strip()

        # Check for potential encoding issues
        if any(ord(c) > 127 for c in cleaned):
            warnings.append("Non-ASCII characters detected, may indicate encoding issues")

        # Check for suspiciously long lines (might be binary data)
        lines = cleaned.split("\n")
        long_lines = [i for i, line in enumerate(lines) if len(line) > 1000]
        if long_lines:
            warnings.append(f"Very long lines detected at positions: {long_lines}")

        return cleaned, warnings

    def _generate_candidates(self, content: str) -> List[FormatCandidate]:
        """Generate format candidates with confidence scoring."""

        candidates = []
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        if not lines:
            return candidates

        # Detect possible separators
        separator_scores = self._analyze_separators(lines)

        # Generate candidates for each separator
        for separator, score in separator_scores.items():
            if score < 0.3:  # Skip low-confidence separators
                continue

            try:
                # Detect dimensions for this separator
                dimensions = self._detect_dimensions(lines, separator)
                if dimensions is None:
                    continue

                # Detect headers
                has_headers = self._detect_headers(lines[0], separator)

                # Detect decimal places
                decimal_places = self._detect_decimal_places(content, separator)

                # Determine format type
                format_type = self._determine_format_type(content, separator)

                # Calculate confidence
                confidence = self._calculate_confidence(
                    content, separator, dimensions, has_headers, format_type, lines
                )

                # Collect evidence for transparency
                evidence = {
                    "separator_score": score,
                    "dimension_match": dimensions in self.common_dimensions,
                    "format_type": format_type,
                    "header_detection": has_headers,
                    "decimal_consistency": decimal_places,
                    "line_consistency": self._check_line_consistency(lines, separator),
                }

                candidate = FormatCandidate(
                    format_type=format_type,
                    separator=separator,
                    dimensions=dimensions,
                    has_headers=has_headers,
                    decimal_places=decimal_places,
                    confidence=confidence,
                    evidence=evidence,
                )

                candidates.append(candidate)

            except Exception as e:
                logger.warning(f"Failed to create candidate for separator '{separator}': {e}")
                continue

        return candidates

    def _analyze_separators(self, lines: List[str]) -> Dict[str, float]:
        """Analyze potential separators with scoring."""

        separator_scores = {}

        for sep_char, sep_info in self.separator_patterns.items():
            score = 0.0
            consistent_counts = []

            for line in lines[:10]:  # Analyze first 10 lines
                count = line.count(sep_char)
                consistent_counts.append(count)

                # Check if fields look numeric after splitting
                if count > 0:
                    fields = line.split(sep_char)
                    numeric_fields = sum(
                        1 for field in fields if self._is_numeric_field(field.strip())
                    )

                    if len(fields) > 1:
                        numeric_ratio = numeric_fields / len(fields)
                        score += numeric_ratio * sep_info["weight"]

            # Check consistency of separator counts across lines
            if consistent_counts:
                most_common_count = max(set(consistent_counts), key=consistent_counts.count)
                consistency = consistent_counts.count(most_common_count) / len(consistent_counts)
                score *= consistency

                # Boost score if separator appears consistently
                if consistency > 0.8 and most_common_count > 0:
                    score *= 1.5

            separator_scores[sep_char] = min(score, 1.0)  # Cap at 1.0

        return separator_scores

    def _detect_dimensions(self, lines: List[str], separator: str) -> Optional[Tuple[int, int]]:
        """Detect map dimensions for given separator."""

        try:
            data_lines = lines.copy()

            # Skip potential header
            if self._detect_headers(lines[0], separator):
                data_lines = lines[1:]

            if not data_lines:
                return None

            # Count columns from first data line
            first_line_fields = [f.strip() for f in data_lines[0].split(separator) if f.strip()]
            cols = len(first_line_fields)

            # Verify column consistency
            consistent_lines = 0
            for line in data_lines[: min(20, len(data_lines))]:  # Check first 20 lines
                line_fields = [f.strip() for f in line.split(separator) if f.strip()]
                if abs(len(line_fields) - cols) <= 1:  # Allow small variations
                    consistent_lines += 1

            if consistent_lines / min(20, len(data_lines)) < 0.8:
                return None  # Inconsistent column count

            rows = len(data_lines)

            if rows > 0 and cols > 0:
                return (rows, cols)

            return None

        except Exception as e:
            logger.error(f"Dimension detection failed: {e}")
            return None

    def _detect_headers(self, first_line: str, separator: str) -> bool:
        """Detect if first line contains headers."""

        try:
            fields = [field.strip() for field in first_line.split(separator) if field.strip()]

            if not fields:
                return False

            # Count numeric vs non-numeric fields
            numeric_count = 0
            header_indicators = 0

            for field in fields:
                if self._is_numeric_field(field):
                    numeric_count += 1
                else:
                    # Check for header-like patterns
                    for pattern in self.header_patterns:
                        if pattern.match(field):
                            header_indicators += 1
                            break

            # If majority of fields are non-numeric and look like headers
            if len(fields) > 0:
                non_numeric_ratio = (len(fields) - numeric_count) / len(fields)
                header_ratio = header_indicators / len(fields)

                return non_numeric_ratio > 0.5 or header_ratio > 0.3

            return False

        except Exception:
            return False

    def _detect_decimal_places(self, content: str, separator: str) -> int:
        """Detect common number of decimal places."""

        try:
            # Find numeric values in content
            numeric_pattern = re.compile(r"-?\d*\.\d+")
            matches = numeric_pattern.findall(content)

            if not matches:
                return 0  # No decimal numbers found

            # Count decimal places
            decimal_counts = []
            for match in matches[:50]:  # Sample first 50 matches
                decimal_part = match.split(".")[-1]
                decimal_counts.append(len(decimal_part))

            if decimal_counts:
                # Return most common decimal place count
                return max(set(decimal_counts), key=decimal_counts.count)

            return 2  # Default

        except Exception:
            return 2  # Default fallback

    def _determine_format_type(
        self, content: str, separator: str
    ) -> Literal["tabulated", "csv", "hex", "binary"]:
        """Determine format type based on content analysis."""

        try:
            # Check against format patterns
            format_scores = {}

            for format_name, format_info in self.format_patterns.items():
                if format_info["pattern"].search(content):
                    format_scores[format_name] = format_info["weight"]

            if not format_scores:
                return "tabulated"  # Default fallback

            # Consider separator context
            if separator == "\t":
                format_scores["tabulated"] = format_scores.get("tabulated", 0) * 1.5
            elif separator == ",":
                format_scores["csv"] = format_scores.get("csv", 0) * 1.5

            # Return format with highest score
            best_format = max(format_scores, key=format_scores.get)
            return best_format

        except Exception:
            return "tabulated"  # Safe fallback

    def _calculate_confidence(
        self,
        content: str,
        separator: str,
        dimensions: Tuple[int, int],
        has_headers: bool,
        format_type: str,
        lines: List[str],
    ) -> float:
        """Calculate overall confidence score for format candidate."""

        try:
            confidence_factors = []

            # Separator confidence
            sep_info = self.separator_patterns.get(separator, {"weight": 0.5})
            confidence_factors.append(sep_info["weight"])

            # Dimension confidence (boost for common FTManager sizes)
            dim_confidence = self.common_dimensions.get(dimensions, 0.3)
            confidence_factors.append(dim_confidence)

            # Format type confidence
            format_confidence = self.format_patterns.get(format_type, {"weight": 0.5})["weight"]
            confidence_factors.append(format_confidence)

            # Data consistency confidence
            consistency_score = self._check_line_consistency(lines, separator)
            confidence_factors.append(consistency_score)

            # Numeric content confidence
            numeric_score = self._calculate_numeric_confidence(content)
            confidence_factors.append(numeric_score)

            # Calculate weighted average
            total_confidence = sum(confidence_factors) / len(confidence_factors)

            # Apply bonus for perfect matches
            if dimensions in [(16, 16), (20, 20)] and separator == "\t":
                total_confidence *= 1.1  # Boost for standard FTManager formats

            return min(total_confidence, 1.0)  # Cap at 1.0

        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5  # Safe fallback

    def _check_line_consistency(self, lines: List[str], separator: str) -> float:
        """Check consistency of line structure."""

        try:
            if len(lines) < 2:
                return 0.5

            # Skip potential header
            data_lines = lines[1:] if self._detect_headers(lines[0], separator) else lines

            if not data_lines:
                return 0.0

            # Check field count consistency
            field_counts = []
            for line in data_lines[: min(20, len(data_lines))]:
                fields = [f.strip() for f in line.split(separator) if f.strip()]
                field_counts.append(len(fields))

            if not field_counts:
                return 0.0

            # Calculate consistency score
            most_common_count = max(set(field_counts), key=field_counts.count)
            consistency = field_counts.count(most_common_count) / len(field_counts)

            return consistency

        except Exception:
            return 0.5

    def _calculate_numeric_confidence(self, content: str) -> float:
        """Calculate confidence based on numeric content ratio."""

        try:
            # Count total characters vs numeric characters
            total_chars = len(content)
            if total_chars == 0:
                return 0.0

            numeric_chars = sum(1 for c in content if c.isdigit() or c in ".-+")
            separator_chars = sum(1 for c in content if c in "\t, ;")
            sum(1 for c in content if c.isspace())

            # Calculate ratio of data characters vs total
            data_chars = numeric_chars + separator_chars
            data_ratio = data_chars / total_chars

            # Boost if high numeric content
            if data_ratio > 0.7:
                return min(data_ratio * 1.2, 1.0)

            return data_ratio

        except Exception:
            return 0.5

    def _is_numeric_field(self, field: str) -> bool:
        """Check if field represents numeric data."""

        if not field:
            return False

        # Check against numeric patterns
        for pattern_name, pattern in self.numeric_patterns.items():
            if pattern.match(field):
                return True

        # Fallback: try to convert to float
        try:
            float(field)
            return True
        except ValueError:
            return False

    def _candidate_to_format_spec(self, candidate: FormatCandidate) -> Any:
        """Convert format candidate to FTManagerFormat specification."""

        try:
            from ..maps.ftmanager import FTManagerFormat

            return FTManagerFormat(
                format_type=candidate.format_type,
                dimensions=candidate.dimensions,
                has_headers=candidate.has_headers,
                separator=candidate.separator,
                decimal_places=candidate.decimal_places,
                byte_order="little",  # Default
                data_type="float",  # Default
            )

        except Exception as e:
            logger.error(f"Failed to convert candidate to format spec: {e}")
            return None
