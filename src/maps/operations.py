"""
Map Operations - Core editing operations for tuning maps

This module provides optimized operations for map editing including
copy/paste, increment/decrement, region selection, and batch operations.

CRITICAL: Follows PYTHON-CODE-STANDARDS.md:
- Type hints 100% coverage
- Performance < 100ms for operations
- Error handling comprehensive
- NumPy vectorization for efficiency
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class CellSelection:
    """Type-safe cell selection container."""

    start_row: int
    end_row: int
    start_col: int
    end_col: int

    def __post_init__(self):
        """Validate selection bounds."""
        if self.start_row > self.end_row:
            self.start_row, self.end_row = self.end_row, self.start_row
        if self.start_col > self.end_col:
            self.start_col, self.end_col = self.end_col, self.start_col


@dataclass
class MapOperation:
    """Type-safe operation record for undo/redo."""

    operation_type: str  # 'increment', 'smooth', 'interpolate', 'paste'
    timestamp: datetime
    affected_cells: CellSelection
    old_values: np.ndarray
    new_values: np.ndarray
    parameters: Dict[str, Any]


class MapOperations:
    """
    Core map editing operations with vectorized performance.

    All operations are optimized using NumPy vectorization for
    performance targets < 100ms on typical map sizes (16x16 to 32x32).
    """

    def __init__(self):
        """Initialize map operations handler."""
        self.operation_history: List[MapOperation] = []
        self.clipboard_data: Optional[np.ndarray] = None
        self.max_history_size = 50

    def increment_region(
        self,
        map_data: pd.DataFrame,
        selection: CellSelection,
        increment_value: float,
        apply_limits: bool = True,
    ) -> pd.DataFrame:
        """
        Increment values in selected region with optional limits.

        Args:
            map_data: Source map DataFrame
            selection: Cell selection region
            increment_value: Value to add to selected cells
            apply_limits: Whether to apply reasonable limits based on map type

        Returns:
            Modified DataFrame with incremented values

        Raises:
            ValueError: If selection is invalid

        Performance: < 50ms for 32x32 maps
        """

        try:
            # Validate selection bounds
            self._validate_selection(map_data, selection)

            # Create working copy
            result_df = map_data.copy()

            # Get numeric columns only
            numeric_cols = result_df.select_dtypes(include=[np.number]).columns

            if len(numeric_cols) == 0:
                raise ValueError("No numeric columns found in map data")

            # Extract selection bounds
            row_slice = slice(selection.start_row, selection.end_row + 1)
            col_indices = numeric_cols[selection.start_col : selection.end_col + 1]

            # Store old values for undo
            old_values = result_df.loc[row_slice, col_indices].values.copy()

            # Vectorized increment operation
            result_df.loc[row_slice, col_indices] += increment_value

            # Apply limits if requested
            if apply_limits:
                result_df = self._apply_value_limits(result_df, col_indices)

            # Store new values
            new_values = result_df.loc[row_slice, col_indices].values.copy()

            # Record operation for undo
            operation = MapOperation(
                operation_type="increment",
                timestamp=datetime.now(),
                affected_cells=selection,
                old_values=old_values,
                new_values=new_values,
                parameters={"increment_value": increment_value, "apply_limits": apply_limits},
            )

            self._add_to_history(operation)

            logger.debug(
                f"Incremented region by {increment_value}, affected {old_values.size} cells"
            )

            return result_df

        except Exception as e:
            logger.error(f"Increment region operation failed: {e}")
            raise

    def copy_region(self, map_data: pd.DataFrame, selection: CellSelection) -> np.ndarray:
        """
        Copy selected region to clipboard.

        Args:
            map_data: Source map DataFrame
            selection: Region to copy

        Returns:
            Copied data as NumPy array

        Performance: < 10ms for any reasonable selection
        """

        try:
            self._validate_selection(map_data, selection)

            # Get numeric columns
            numeric_cols = map_data.select_dtypes(include=[np.number]).columns

            # Extract selection
            row_slice = slice(selection.start_row, selection.end_row + 1)
            col_indices = numeric_cols[selection.start_col : selection.end_col + 1]

            # Copy to clipboard
            self.clipboard_data = map_data.loc[row_slice, col_indices].values.copy()

            logger.debug(
                f"Copied region {selection} to clipboard, shape: {self.clipboard_data.shape}"
            )

            return self.clipboard_data

        except Exception as e:
            logger.error(f"Copy region operation failed: {e}")
            raise

    def paste_region(
        self, map_data: pd.DataFrame, target_selection: CellSelection, resize_if_needed: bool = True
    ) -> pd.DataFrame:
        """
        Paste clipboard data to target selection.

        Args:
            map_data: Target map DataFrame
            target_selection: Where to paste data
            resize_if_needed: Whether to resize clipboard data to fit selection

        Returns:
            Modified DataFrame with pasted data

        Raises:
            ValueError: If no clipboard data or incompatible sizes

        Performance: < 20ms for typical operations
        """

        try:
            if self.clipboard_data is None:
                raise ValueError("No data in clipboard")

            self._validate_selection(map_data, target_selection)

            result_df = map_data.copy()
            numeric_cols = result_df.select_dtypes(include=[np.number]).columns

            # Calculate target dimensions
            target_rows = target_selection.end_row - target_selection.start_row + 1
            target_cols = target_selection.end_col - target_selection.start_col + 1

            # Get clipboard dimensions
            clip_rows, clip_cols = self.clipboard_data.shape

            # Prepare data to paste
            paste_data = self.clipboard_data

            if resize_if_needed and (clip_rows != target_rows or clip_cols != target_cols):
                # Resize clipboard data using interpolation
                from scipy.interpolate import griddata

                # Create coordinate grids
                clip_x, clip_y = np.meshgrid(np.arange(clip_cols), np.arange(clip_rows))
                target_x, target_y = np.meshgrid(
                    np.linspace(0, clip_cols - 1, target_cols),
                    np.linspace(0, clip_rows - 1, target_rows),
                )

                # Interpolate to new size
                paste_data = griddata(
                    (clip_x.flatten(), clip_y.flatten()),
                    self.clipboard_data.flatten(),
                    (target_x, target_y),
                    method="cubic",
                    fill_value=self.clipboard_data.mean(),
                )

            elif clip_rows != target_rows or clip_cols != target_cols:
                raise ValueError(
                    f"Clipboard size {clip_rows}x{clip_cols} doesn't match "
                    f"target size {target_rows}x{target_cols}"
                )

            # Store old values for undo
            row_slice = slice(target_selection.start_row, target_selection.end_row + 1)
            col_indices = numeric_cols[target_selection.start_col : target_selection.end_col + 1]
            old_values = result_df.loc[row_slice, col_indices].values.copy()

            # Paste data
            result_df.loc[row_slice, col_indices] = paste_data

            # Record operation
            operation = MapOperation(
                operation_type="paste",
                timestamp=datetime.now(),
                affected_cells=target_selection,
                old_values=old_values,
                new_values=paste_data.copy(),
                parameters={"resize_if_needed": resize_if_needed},
            )

            self._add_to_history(operation)

            logger.debug(f"Pasted data to region {target_selection}")

            return result_df

        except Exception as e:
            logger.error(f"Paste region operation failed: {e}")
            raise

    def fill_region(
        self,
        map_data: pd.DataFrame,
        selection: CellSelection,
        fill_value: float,
        fill_pattern: str = "constant",
    ) -> pd.DataFrame:
        """
        Fill selected region with value or pattern.

        Args:
            map_data: Target map DataFrame
            selection: Region to fill
            fill_value: Base value for filling
            fill_pattern: Pattern type ('constant', 'gradient_x', 'gradient_y')

        Returns:
            Modified DataFrame with filled region

        Performance: < 30ms for 32x32 regions
        """

        try:
            self._validate_selection(map_data, selection)

            result_df = map_data.copy()
            numeric_cols = result_df.select_dtypes(include=[np.number]).columns

            # Calculate region dimensions
            rows = selection.end_row - selection.start_row + 1
            cols = selection.end_col - selection.start_col + 1

            # Generate fill data based on pattern
            if fill_pattern == "constant":
                fill_data = np.full((rows, cols), fill_value)

            elif fill_pattern == "gradient_x":
                # Horizontal gradient from fill_value to fill_value * 1.5
                x_gradient = np.linspace(fill_value, fill_value * 1.5, cols)
                fill_data = np.tile(x_gradient, (rows, 1))

            elif fill_pattern == "gradient_y":
                # Vertical gradient
                y_gradient = np.linspace(fill_value, fill_value * 1.5, rows)
                fill_data = np.tile(y_gradient.reshape(-1, 1), (1, cols))

            else:
                raise ValueError(f"Unknown fill pattern: {fill_pattern}")

            # Apply fill
            row_slice = slice(selection.start_row, selection.end_row + 1)
            col_indices = numeric_cols[selection.start_col : selection.end_col + 1]

            # Store old values
            old_values = result_df.loc[row_slice, col_indices].values.copy()

            # Fill region
            result_df.loc[row_slice, col_indices] = fill_data

            # Record operation
            operation = MapOperation(
                operation_type="fill",
                timestamp=datetime.now(),
                affected_cells=selection,
                old_values=old_values,
                new_values=fill_data.copy(),
                parameters={"fill_value": fill_value, "fill_pattern": fill_pattern},
            )

            self._add_to_history(operation)

            logger.debug(f"Filled region {selection} with pattern '{fill_pattern}'")

            return result_df

        except Exception as e:
            logger.error(f"Fill region operation failed: {e}")
            raise

    def scale_region(
        self,
        map_data: pd.DataFrame,
        selection: CellSelection,
        scale_factor: float,
        scale_mode: str = "multiply",
    ) -> pd.DataFrame:
        """
        Scale values in selected region.

        Args:
            map_data: Target map DataFrame
            selection: Region to scale
            scale_factor: Scaling factor
            scale_mode: Scaling mode ('multiply', 'percentage', 'offset')

        Returns:
            Modified DataFrame with scaled values

        Performance: < 20ms for vectorized operations
        """

        try:
            self._validate_selection(map_data, selection)

            result_df = map_data.copy()
            numeric_cols = result_df.select_dtypes(include=[np.number]).columns

            row_slice = slice(selection.start_row, selection.end_row + 1)
            col_indices = numeric_cols[selection.start_col : selection.end_col + 1]

            # Store old values
            old_values = result_df.loc[row_slice, col_indices].values.copy()

            # Apply scaling based on mode
            if scale_mode == "multiply":
                result_df.loc[row_slice, col_indices] *= scale_factor

            elif scale_mode == "percentage":
                # Scale by percentage: new = old * (1 + factor/100)
                result_df.loc[row_slice, col_indices] *= 1.0 + scale_factor / 100.0

            elif scale_mode == "offset":
                # Add offset to current values
                result_df.loc[row_slice, col_indices] += scale_factor

            else:
                raise ValueError(f"Unknown scale mode: {scale_mode}")

            # Get new values
            new_values = result_df.loc[row_slice, col_indices].values.copy()

            # Record operation
            operation = MapOperation(
                operation_type="scale",
                timestamp=datetime.now(),
                affected_cells=selection,
                old_values=old_values,
                new_values=new_values,
                parameters={"scale_factor": scale_factor, "scale_mode": scale_mode},
            )

            self._add_to_history(operation)

            logger.debug(f"Scaled region {selection} by {scale_factor} ({scale_mode})")

            return result_df

        except Exception as e:
            logger.error(f"Scale region operation failed: {e}")
            raise

    def undo_last_operation(self, map_data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Undo the last operation.

        Args:
            map_data: Current map DataFrame

        Returns:
            DataFrame with last operation undone, or None if no history

        Performance: < 10ms for restoration
        """

        try:
            if not self.operation_history:
                return None

            last_operation = self.operation_history.pop()
            result_df = map_data.copy()

            # Restore old values
            numeric_cols = result_df.select_dtypes(include=[np.number]).columns
            selection = last_operation.affected_cells

            row_slice = slice(selection.start_row, selection.end_row + 1)
            col_indices = numeric_cols[selection.start_col : selection.end_col + 1]

            result_df.loc[row_slice, col_indices] = last_operation.old_values

            logger.debug(f"Undid operation: {last_operation.operation_type}")

            return result_df

        except Exception as e:
            logger.error(f"Undo operation failed: {e}")
            raise

    def clear_history(self) -> None:
        """Clear operation history to free memory."""
        self.operation_history.clear()
        logger.debug("Operation history cleared")

    def get_clipboard_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about clipboard contents.

        Returns:
            Dictionary with clipboard info or None if empty
        """

        if self.clipboard_data is None:
            return None

        return {
            "shape": self.clipboard_data.shape,
            "size": self.clipboard_data.size,
            "mean": float(np.mean(self.clipboard_data)),
            "min": float(np.min(self.clipboard_data)),
            "max": float(np.max(self.clipboard_data)),
            "dtype": str(self.clipboard_data.dtype),
        }

    def _validate_selection(self, map_data: pd.DataFrame, selection: CellSelection) -> None:
        """Validate that selection is within DataFrame bounds."""

        max_row = len(map_data) - 1
        max_col = len(map_data.select_dtypes(include=[np.number]).columns) - 1

        if selection.start_row < 0 or selection.end_row > max_row:
            raise ValueError(
                f"Row selection out of bounds: {selection.start_row}-{selection.end_row}"
            )

        if selection.start_col < 0 or selection.end_col > max_col:
            raise ValueError(
                f"Column selection out of bounds: {selection.start_col}-{selection.end_col}"
            )

    def _apply_value_limits(self, map_data: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Apply reasonable value limits based on map type heuristics."""

        result_df = map_data.copy()

        for col in columns:
            # Detect likely map type from values and apply appropriate limits
            col_data = result_df[col]
            mean_val = col_data.mean()

            if 8 <= mean_val <= 20:
                # Likely AFR values - limit to reasonable range
                result_df[col] = col_data.clip(8.0, 20.0)
            elif -10 <= mean_val <= 50:
                # Likely ignition timing - limit to safe range
                result_df[col] = col_data.clip(-10.0, 50.0)
            elif 0 <= mean_val <= 3:
                # Likely boost pressure - limit to safe range
                result_df[col] = col_data.clip(0.0, 3.0)

            # Otherwise no limits applied

        return result_df

    def _add_to_history(self, operation: MapOperation) -> None:
        """Add operation to history with size management."""

        self.operation_history.append(operation)

        # Limit history size to prevent memory issues
        if len(self.operation_history) > self.max_history_size:
            self.operation_history.pop(0)

    def get_operation_history_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of operation history for debugging.

        Returns:
            List of operation summaries
        """

        return [
            {
                "type": op.operation_type,
                "timestamp": op.timestamp.isoformat(),
                "affected_cells": f"{op.affected_cells.start_row}-{op.affected_cells.end_row}, "
                f"{op.affected_cells.start_col}-{op.affected_cells.end_col}",
                "parameters": op.parameters,
            }
            for op in self.operation_history
        ]
