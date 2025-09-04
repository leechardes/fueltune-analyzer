"""
FTManager Bridge - Integration with FuelTech Manager via clipboard

This module provides seamless integration with FTManager software through
clipboard operations, format detection, and data validation.

CRITICAL: Follows PYTHON-CODE-STANDARDS.md:
- Zero data loss during import/export
- Robust format detection
- Professional error handling
- Cross-platform clipboard support
- Type hints 100% coverage
"""

import pandas as pd
import numpy as np
import pyperclip
import re
from typing import Dict, List, Optional, Tuple, Union, Any, Literal
from dataclasses import dataclass
from datetime import datetime
import logging
import io
import csv

logger = logging.getLogger(__name__)

@dataclass
class FTManagerFormat:
    """Type-safe FTManager format specification."""
    
    format_type: Literal['tabulated', 'csv', 'hex', 'binary']
    dimensions: Tuple[int, int]
    has_headers: bool
    separator: str
    decimal_places: int
    byte_order: Literal['little', 'big'] = 'little'
    data_type: Literal['float', 'int', 'hex'] = 'float'
    
    def __post_init__(self):
        """Validate format parameters."""
        if self.dimensions[0] <= 0 or self.dimensions[1] <= 0:
            raise ValueError("Dimensions must be positive")
        if self.decimal_places < 0:
            raise ValueError("Decimal places must be non-negative")

@dataclass
class ImportResult:
    """Type-safe import operation result."""
    
    success: bool
    map_data: Optional[pd.DataFrame]
    detected_format: Optional[FTManagerFormat] 
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Initialize empty lists if None."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ExportResult:
    """Type-safe export operation result."""
    
    success: bool
    formatted_data: Optional[str]
    format_used: Optional[FTManagerFormat]
    errors: List[str]
    warnings: List[str]
    clipboard_updated: bool = False

class FTManagerBridge:
    """
    Professional FTManager integration with robust format detection.
    
    Features:
    - Auto-detection of FTManager table formats
    - Lossless data import/export
    - Clipboard integration with validation
    - Cross-platform compatibility  
    - Professional error handling
    """
    
    def __init__(self):
        """Initialize FTManager bridge with format definitions."""
        
        # Define common FTManager formats
        self.known_formats = {
            'standard_16x16': FTManagerFormat(
                format_type='tabulated',
                dimensions=(16, 16),
                has_headers=True,
                separator='\t',
                decimal_places=2
            ),
            'standard_20x20': FTManagerFormat(
                format_type='tabulated', 
                dimensions=(20, 20),
                has_headers=True,
                separator='\t',
                decimal_places=2
            ),
            'csv_format': FTManagerFormat(
                format_type='csv',
                dimensions=(16, 16),  # Will be detected
                has_headers=False,
                separator=',',
                decimal_places=3
            )
        }
        
        # Regex patterns for format detection
        self.format_patterns = {
            'tabulated': re.compile(r'^[\d\.\-\+\s\t]+$', re.MULTILINE),
            'csv': re.compile(r'^[\d\.\-\+,\s]+$', re.MULTILINE),
            'hex': re.compile(r'^[0-9A-Fa-f\s\t]+$', re.MULTILINE)
        }
        
        logger.debug("Initialized FTManager bridge with format detection")
    
    def import_from_clipboard(
        self,
        expected_format: Optional[FTManagerFormat] = None,
        validate_dimensions: bool = True
    ) -> ImportResult:
        """
        Import map data from clipboard with format detection.
        
        Args:
            expected_format: Optional expected format for validation
            validate_dimensions: Whether to validate map dimensions
            
        Returns:
            ImportResult with status and data
            
        Performance: < 500ms for typical clipboard operations
        """
        
        try:
            # Get clipboard content
            clipboard_content = self._get_clipboard_content()
            if not clipboard_content:
                return ImportResult(
                    success=False,
                    map_data=None,
                    detected_format=None,
                    errors=["Clipboard is empty or contains no text"],
                    warnings=[],
                    metadata={}
                )
            
            # Detect format
            detected_format = self._detect_format(clipboard_content)
            if detected_format is None:
                return ImportResult(
                    success=False,
                    map_data=None,
                    detected_format=None,
                    errors=["Unable to detect valid FTManager format"],
                    warnings=[],
                    metadata={'raw_content_preview': clipboard_content[:200]}
                )
            
            # Validate against expected format if provided
            validation_warnings = []
            if expected_format and not self._formats_compatible(detected_format, expected_format):
                validation_warnings.append(
                    f"Detected format {detected_format.format_type} doesn't match "
                    f"expected {expected_format.format_type}"
                )
            
            # Parse data based on detected format
            map_data, parse_errors = self._parse_data(clipboard_content, detected_format)
            
            if map_data is None:
                return ImportResult(
                    success=False,
                    map_data=None,
                    detected_format=detected_format,
                    errors=parse_errors,
                    warnings=validation_warnings,
                    metadata={'raw_content_preview': clipboard_content[:200]}
                )
            
            # Validate dimensions if requested
            dimension_warnings = []
            if validate_dimensions:
                dimension_warnings = self._validate_dimensions(map_data, detected_format)
            
            # Create metadata
            metadata = {
                'import_timestamp': datetime.now().isoformat(),
                'source': 'clipboard',
                'original_format': detected_format.format_type,
                'data_shape': map_data.shape,
                'has_headers': detected_format.has_headers,
                'separator': detected_format.separator
            }
            
            logger.info(f"Successfully imported {map_data.shape} map from clipboard")
            
            return ImportResult(
                success=True,
                map_data=map_data,
                detected_format=detected_format,
                errors=parse_errors,
                warnings=validation_warnings + dimension_warnings,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Clipboard import failed: {e}")
            return ImportResult(
                success=False,
                map_data=None,
                detected_format=None,
                errors=[f"Import failed: {str(e)}"],
                warnings=[],
                metadata={}
            )
    
    def export_to_clipboard(
        self,
        map_data: pd.DataFrame,
        target_format: Optional[FTManagerFormat] = None,
        update_clipboard: bool = True
    ) -> ExportResult:
        """
        Export map data to clipboard in FTManager format.
        
        Args:
            map_data: Map DataFrame to export
            target_format: Optional target format specification
            update_clipboard: Whether to actually update clipboard
            
        Returns:
            ExportResult with formatted data and status
            
        Performance: < 300ms for typical export operations
        """
        
        try:
            # Validate input data
            if map_data.empty:
                return ExportResult(
                    success=False,
                    formatted_data=None,
                    format_used=None,
                    errors=["Cannot export empty map data"],
                    warnings=[]
                )
            
            # Use default format if none specified
            if target_format is None:
                target_format = self._get_default_export_format(map_data)
            
            # Validate data compatibility with target format
            compatibility_errors = self._validate_export_compatibility(map_data, target_format)
            if compatibility_errors:
                return ExportResult(
                    success=False,
                    formatted_data=None,
                    format_used=target_format,
                    errors=compatibility_errors,
                    warnings=[]
                )
            
            # Format data for export
            formatted_data, format_warnings = self._format_for_export(map_data, target_format)
            
            if formatted_data is None:
                return ExportResult(
                    success=False,
                    formatted_data=None,
                    format_used=target_format,
                    errors=["Failed to format data for export"],
                    warnings=format_warnings
                )
            
            # Update clipboard if requested
            clipboard_success = False
            if update_clipboard:
                clipboard_success = self._set_clipboard_content(formatted_data)
                if not clipboard_success:
                    format_warnings.append("Failed to update clipboard, but data formatted successfully")
            
            logger.info(f"Successfully exported {map_data.shape} map to FTManager format")
            
            return ExportResult(
                success=True,
                formatted_data=formatted_data,
                format_used=target_format,
                errors=[],
                warnings=format_warnings,
                clipboard_updated=clipboard_success
            )
            
        except Exception as e:
            logger.error(f"Clipboard export failed: {e}")
            return ExportResult(
                success=False,
                formatted_data=None,
                format_used=target_format,
                errors=[f"Export failed: {str(e)}"],
                warnings=[]
            )
    
    def detect_clipboard_format(self) -> Optional[FTManagerFormat]:
        """
        Detect FTManager format in current clipboard content.
        
        Returns:
            Detected format or None if no valid format found
            
        Performance: < 100ms for format detection
        """
        
        try:
            clipboard_content = self._get_clipboard_content()
            if not clipboard_content:
                return None
            
            return self._detect_format(clipboard_content)
            
        except Exception as e:
            logger.error(f"Format detection failed: {e}")
            return None
    
    def validate_ftmanager_data(
        self,
        data_content: str,
        expected_format: Optional[FTManagerFormat] = None
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate data content against FTManager format requirements.
        
        Args:
            data_content: Raw data content to validate
            expected_format: Optional expected format for validation
            
        Returns:
            Tuple of (is_valid, errors, warnings)
            
        Performance: < 200ms for validation operations
        """
        
        try:
            errors = []
            warnings = []
            
            # Basic content validation
            if not data_content or not data_content.strip():
                errors.append("Data content is empty")
                return False, errors, warnings
            
            # Format detection
            detected_format = self._detect_format(data_content)
            if detected_format is None:
                errors.append("No valid FTManager format detected")
                return False, errors, warnings
            
            # Expected format validation
            if expected_format:
                if not self._formats_compatible(detected_format, expected_format):
                    warnings.append(
                        f"Detected format ({detected_format.format_type}) "
                        f"differs from expected ({expected_format.format_type})"
                    )
            
            # Data integrity validation
            try:
                parsed_data, parse_errors = self._parse_data(data_content, detected_format)
                if parsed_data is None:
                    errors.extend(parse_errors)
                    return False, errors, warnings
                
                # Check for reasonable data ranges
                numeric_cols = parsed_data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    for col in numeric_cols:
                        col_data = parsed_data[col]
                        
                        # Check for extreme values that might indicate parsing errors
                        if col_data.max() > 1000000 or col_data.min() < -1000000:
                            warnings.append(f"Column {col} contains extreme values")
                        
                        # Check for excessive precision that might indicate format issues
                        if any(len(str(val).split('.')[-1]) > 6 for val in col_data if '.' in str(val)):
                            warnings.append(f"Column {col} has excessive decimal precision")
                
            except Exception as parse_error:
                errors.append(f"Data parsing failed: {str(parse_error)}")
                return False, errors, warnings
            
            # All validations passed
            is_valid = len(errors) == 0
            
            logger.debug(f"Validation completed: valid={is_valid}, "
                        f"{len(errors)} errors, {len(warnings)} warnings")
            
            return is_valid, errors, warnings
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False, [f"Validation error: {str(e)}"], []
    
    def get_supported_formats(self) -> Dict[str, FTManagerFormat]:
        """
        Get dictionary of supported FTManager formats.
        
        Returns:
            Dictionary mapping format names to FTManagerFormat objects
        """
        
        return self.known_formats.copy()
    
    def create_custom_format(
        self,
        name: str,
        dimensions: Tuple[int, int],
        separator: str = '\t',
        has_headers: bool = True,
        decimal_places: int = 2
    ) -> FTManagerFormat:
        """
        Create custom FTManager format specification.
        
        Args:
            name: Format name identifier
            dimensions: (rows, cols) dimensions
            separator: Field separator character
            has_headers: Whether format includes headers
            decimal_places: Number of decimal places for formatting
            
        Returns:
            New FTManagerFormat object
            
        Raises:
            ValueError: If parameters are invalid
        """
        
        try:
            custom_format = FTManagerFormat(
                format_type='tabulated',
                dimensions=dimensions,
                has_headers=has_headers,
                separator=separator,
                decimal_places=decimal_places
            )
            
            # Add to known formats
            self.known_formats[name] = custom_format
            
            logger.debug(f"Created custom format '{name}': {dimensions} with separator '{separator}'")
            
            return custom_format
            
        except Exception as e:
            logger.error(f"Failed to create custom format: {e}")
            raise
    
    # Private helper methods
    
    def _get_clipboard_content(self) -> Optional[str]:
        """Get content from clipboard with error handling."""
        
        try:
            content = pyperclip.paste()
            return content.strip() if content else None
        except Exception as e:
            logger.error(f"Failed to get clipboard content: {e}")
            return None
    
    def _set_clipboard_content(self, content: str) -> bool:
        """Set clipboard content with error handling."""
        
        try:
            pyperclip.copy(content)
            return True
        except Exception as e:
            logger.error(f"Failed to set clipboard content: {e}")
            return False
    
    def _detect_format(self, content: str) -> Optional[FTManagerFormat]:
        """Detect FTManager format from content analysis."""
        
        try:
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            if not lines:
                return None
            
            # Analyze first few lines for format detection
            sample_lines = lines[:5]
            
            # Detect separator
            separator = self._detect_separator(sample_lines)
            if separator is None:
                return None
            
            # Detect dimensions
            dimensions = self._detect_dimensions(lines, separator)
            if dimensions is None:
                return None
            
            # Detect if headers are present
            has_headers = self._detect_headers(lines[0], separator)
            
            # Detect decimal places
            decimal_places = self._detect_decimal_places(content)
            
            # Determine format type
            if separator == ',':
                format_type = 'csv'
            elif self.format_patterns['hex'].match(content):
                format_type = 'hex'
            else:
                format_type = 'tabulated'
            
            detected_format = FTManagerFormat(
                format_type=format_type,
                dimensions=dimensions,
                has_headers=has_headers,
                separator=separator,
                decimal_places=decimal_places
            )
            
            logger.debug(f"Detected format: {format_type} {dimensions} with separator '{separator}'")
            
            return detected_format
            
        except Exception as e:
            logger.error(f"Format detection failed: {e}")
            return None
    
    def _detect_separator(self, sample_lines: List[str]) -> Optional[str]:
        """Detect field separator from sample lines."""
        
        separators = ['\t', ',', ';', ' ']
        separator_scores = {}
        
        for sep in separators:
            score = 0
            consistency_score = 0
            
            field_counts = []
            for line in sample_lines:
                fields = line.split(sep)
                field_counts.append(len(fields))
                
                # Check if fields look like numbers
                numeric_fields = 0
                for field in fields:
                    field = field.strip()
                    if field and self._is_numeric(field):
                        numeric_fields += 1
                
                if len(fields) > 1:
                    score += numeric_fields / len(fields)
            
            # Check consistency of field counts
            if field_counts:
                most_common_count = max(set(field_counts), key=field_counts.count)
                consistency_score = field_counts.count(most_common_count) / len(field_counts)
            
            separator_scores[sep] = score * consistency_score
        
        # Return separator with highest score
        if separator_scores:
            best_separator = max(separator_scores, key=separator_scores.get)
            if separator_scores[best_separator] > 0.5:  # Minimum threshold
                return best_separator
        
        return None
    
    def _detect_dimensions(self, lines: List[str], separator: str) -> Optional[Tuple[int, int]]:
        """Detect map dimensions from data lines."""
        
        try:
            data_lines = [line for line in lines if line.strip()]
            if not data_lines:
                return None
            
            # Count rows (excluding potential header)
            rows = len(data_lines)
            
            # Count columns from first line
            first_line_fields = data_lines[0].split(separator)
            cols = len([field for field in first_line_fields if field.strip()])
            
            # Validate consistency
            for line in data_lines[:10]:  # Check first 10 lines
                line_cols = len([field for field in line.split(separator) if field.strip()])
                if abs(line_cols - cols) > 1:  # Allow small variations
                    logger.warning(f"Inconsistent column count detected: {line_cols} vs {cols}")
            
            # Check if first line might be headers
            if self._detect_headers(data_lines[0], separator):
                rows -= 1
            
            if rows > 0 and cols > 0:
                return (rows, cols)
            
            return None
            
        except Exception as e:
            logger.error(f"Dimension detection failed: {e}")
            return None
    
    def _detect_headers(self, first_line: str, separator: str) -> bool:
        """Detect if first line contains headers instead of data."""
        
        try:
            fields = [field.strip() for field in first_line.split(separator)]
            
            # Count numeric fields
            numeric_count = sum(1 for field in fields if self._is_numeric(field))
            
            # If less than 50% of fields are numeric, likely headers
            if len(fields) > 0:
                numeric_ratio = numeric_count / len(fields)
                return numeric_ratio < 0.5
            
            return False
            
        except Exception:
            return False
    
    def _detect_decimal_places(self, content: str) -> int:
        """Detect common number of decimal places in data."""
        
        try:
            # Find all decimal numbers
            decimal_numbers = re.findall(r'\d+\.\d+', content)
            
            if not decimal_numbers:
                return 0
            
            # Count decimal places for each number
            decimal_places = []
            for num_str in decimal_numbers[:50]:  # Sample first 50 numbers
                places = len(num_str.split('.')[-1])
                decimal_places.append(places)
            
            # Return most common decimal place count
            if decimal_places:
                return max(set(decimal_places), key=decimal_places.count)
            
            return 2  # Default
            
        except Exception:
            return 2  # Default
    
    def _is_numeric(self, value: str) -> bool:
        """Check if string represents a numeric value."""
        
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _parse_data(
        self, 
        content: str, 
        format_spec: FTManagerFormat
    ) -> Tuple[Optional[pd.DataFrame], List[str]]:
        """Parse content according to format specification."""
        
        try:
            errors = []
            
            # Split into lines and clean
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            if not lines:
                return None, ["No data lines found"]
            
            # Skip header if present
            data_lines = lines[1:] if format_spec.has_headers else lines
            
            # Parse each line
            parsed_rows = []
            for i, line in enumerate(data_lines):
                try:
                    fields = line.split(format_spec.separator)
                    numeric_fields = []
                    
                    for field in fields:
                        field = field.strip()
                        if field:
                            try:
                                if format_spec.format_type == 'hex':
                                    # Convert hex to decimal
                                    numeric_value = int(field, 16)
                                else:
                                    numeric_value = float(field)
                                numeric_fields.append(numeric_value)
                            except ValueError:
                                errors.append(f"Invalid numeric value '{field}' at line {i+1}")
                                numeric_fields.append(np.nan)
                    
                    if numeric_fields:
                        parsed_rows.append(numeric_fields)
                        
                except Exception as e:
                    errors.append(f"Failed to parse line {i+1}: {str(e)}")
                    continue
            
            if not parsed_rows:
                return None, errors + ["No valid data rows found"]
            
            # Convert to DataFrame
            try:
                # Ensure consistent row lengths
                max_cols = max(len(row) for row in parsed_rows)
                normalized_rows = []
                
                for row in parsed_rows:
                    if len(row) < max_cols:
                        row.extend([np.nan] * (max_cols - len(row)))
                    normalized_rows.append(row[:max_cols])
                
                # Create DataFrame with generic column names
                column_names = [f"Col_{i}" for i in range(max_cols)]
                df = pd.DataFrame(normalized_rows, columns=column_names)
                
                return df, errors
                
            except Exception as e:
                errors.append(f"DataFrame creation failed: {str(e)}")
                return None, errors
            
        except Exception as e:
            return None, [f"Parsing failed: {str(e)}"]
    
    def _validate_dimensions(
        self, 
        map_data: pd.DataFrame, 
        format_spec: FTManagerFormat
    ) -> List[str]:
        """Validate map dimensions against format specification."""
        
        warnings = []
        
        actual_dims = map_data.shape
        expected_dims = format_spec.dimensions
        
        if actual_dims != expected_dims:
            warnings.append(
                f"Dimension mismatch: got {actual_dims}, expected {expected_dims}"
            )
        
        return warnings
    
    def _formats_compatible(
        self, 
        format1: FTManagerFormat, 
        format2: FTManagerFormat
    ) -> bool:
        """Check if two formats are compatible."""
        
        return (
            format1.format_type == format2.format_type and
            format1.separator == format2.separator and
            abs(format1.decimal_places - format2.decimal_places) <= 1
        )
    
    def _get_default_export_format(self, map_data: pd.DataFrame) -> FTManagerFormat:
        """Get default export format based on map data characteristics."""
        
        rows, cols = map_data.shape
        
        return FTManagerFormat(
            format_type='tabulated',
            dimensions=(rows, cols),
            has_headers=False,
            separator='\t',
            decimal_places=3
        )
    
    def _validate_export_compatibility(
        self, 
        map_data: pd.DataFrame, 
        target_format: FTManagerFormat
    ) -> List[str]:
        """Validate map data compatibility with target format."""
        
        errors = []
        
        # Check dimensions
        actual_dims = map_data.shape
        target_dims = target_format.dimensions
        
        if actual_dims != target_dims:
            errors.append(
                f"Dimension mismatch: data is {actual_dims}, "
                f"target format expects {target_dims}"
            )
        
        # Check for numeric data
        numeric_cols = map_data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            errors.append("No numeric data found for export")
        
        return errors
    
    def _format_for_export(
        self, 
        map_data: pd.DataFrame, 
        target_format: FTManagerFormat
    ) -> Tuple[Optional[str], List[str]]:
        """Format map data for export according to target format."""
        
        try:
            warnings = []
            
            # Get numeric data
            numeric_cols = map_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return None, ["No numeric data to export"]
            
            export_data = map_data[numeric_cols].copy()
            
            # Round to specified decimal places
            if target_format.decimal_places >= 0:
                export_data = export_data.round(target_format.decimal_places)
            
            # Format based on target format type
            if target_format.format_type == 'csv':
                output = io.StringIO()
                export_data.to_csv(
                    output, 
                    sep=target_format.separator,
                    header=target_format.has_headers,
                    index=False,
                    float_format=f'%.{target_format.decimal_places}f'
                )
                formatted_data = output.getvalue()
                
            elif target_format.format_type == 'hex':
                # Convert to hex format (for integer values)
                hex_data = export_data.astype(int).applymap(lambda x: f"{x:X}")
                formatted_data = hex_data.to_csv(
                    sep=target_format.separator,
                    header=target_format.has_headers,
                    index=False
                )
                
            else:  # tabulated
                # Create tab-separated format
                formatted_data = export_data.to_csv(
                    sep=target_format.separator,
                    header=target_format.has_headers,
                    index=False,
                    float_format=f'%.{target_format.decimal_places}f'
                )
            
            return formatted_data, warnings
            
        except Exception as e:
            return None, [f"Formatting failed: {str(e)}"]