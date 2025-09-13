"""
FuelTune Analysis Engine - Engine State Segmentation Module

This module provides automatic segmentation of log data by engine operating states
using vectorized NumPy operations for optimal performance.

Classes:
    EngineStateSegmenter: Main segmentation engine
    SegmentationResult: Result container with metadata
    SegmentConfig: Configuration for segmentation parameters

Functions:
    segment_log_data: High-level segmentation interface
    calculate_segment_statistics: Statistical analysis of segments
    identify_operating_states: Automatic state classification

Performance Target: < 1s for 10k data points

Author: FuelTune Analysis Engine
Version: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class EngineState(Enum):
    """Engine operating state classifications."""

    IDLE = "idle"
    LIGHT_LOAD = "light_load"
    MODERATE_LOAD = "moderate_load"
    HIGH_LOAD = "high_load"
    BOOST = "boost"
    OVERRUN = "overrun"
    LAUNCH = "launch"
    TWO_STEP = "two_step"


@dataclass
class SegmentConfig:
    """Configuration for engine state segmentation."""

    # RPM thresholds
    idle_rpm_max: int = 1200
    light_load_rpm_min: int = 1200
    light_load_rpm_max: int = 3000
    moderate_load_rpm_min: int = 2500
    high_load_rpm_min: int = 4000

    # Load thresholds (TPS %)
    idle_tps_max: float = 5.0
    light_load_tps_max: float = 25.0
    moderate_load_tps_min: float = 20.0
    high_load_tps_min: float = 60.0

    # MAP pressure thresholds (bar)
    atmospheric_pressure: float = 1.0
    boost_threshold: float = 1.05
    high_boost_threshold: float = 1.5

    # Lambda thresholds
    overrun_lambda_min: float = 1.3
    launch_lambda_max: float = 0.9

    # Time-based parameters
    minimum_segment_duration: float = 0.5  # seconds
    stability_window: int = 10  # data points for stability check

    # Statistical parameters
    outlier_z_threshold: float = 3.0


@dataclass
class SegmentationResult:
    """Container for segmentation results."""

    segments: Dict[EngineState, np.ndarray] = field(default_factory=dict)
    segment_indices: Dict[EngineState, List[Tuple[int, int]]] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    total_points: int = 0
    processing_time: float = 0.0
    confidence_score: float = 0.0


class EngineStateSegmenter:
    """
    High-performance engine state segmentation using vectorized operations.

    This class identifies distinct operating states from engine telemetry data
    using optimized NumPy algorithms for real-time analysis.
    """

    def __init__(self, config: Optional[SegmentConfig] = None):
        """
        Initialize the segmenter with configuration.

        Args:
            config: Segmentation configuration parameters
        """
        self.config = config or SegmentConfig()
        self._last_result: Optional[SegmentationResult] = None

    def segment_data(
        self,
        data: Union[pd.DataFrame, Dict[str, np.ndarray]],
        timestamp_col: str = "timestamp",
        rpm_col: str = "rpm",
        tps_col: str = "throttle_position",
        map_col: str = "map_pressure",
        lambda_col: str = "lambda_sensor",
        two_step_col: str = "two_step",
        launch_col: str = "launch_validated",
    ) -> SegmentationResult:
        """
        Segment engine data by operating states using vectorized operations.

        Args:
            data: Input data as DataFrame or dict of arrays
            timestamp_col: Timestamp column name
            rpm_col: RPM column name
            tps_col: Throttle position column name
            map_col: MAP pressure column name
            lambda_col: Lambda sensor column name
            two_step_col: Two-step active column name
            launch_col: Launch control active column name

        Returns:
            SegmentationResult with classified segments

        Raises:
            ValueError: If required columns are missing
            TypeError: If data types are invalid
        """
        import time

        start_time = time.time()

        try:
            # Convert data to numpy arrays for vectorized operations
            arrays = self._prepare_data_arrays(
                data, timestamp_col, rpm_col, tps_col, map_col, lambda_col, two_step_col, launch_col
            )

            # Validate data quality
            self._validate_data_quality(arrays)

            # Classify states using vectorized operations
            state_classifications = self._classify_states_vectorized(arrays)

            # Post-process segments for stability and minimum duration
            processed_segments = self._post_process_segments(
                state_classifications, arrays["timestamp"]
            )

            # Calculate statistics
            statistics = self._calculate_segment_statistics(processed_segments, arrays)

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(processed_segments, arrays)

            # Create result
            result = SegmentationResult(
                segments=processed_segments,
                segment_indices=self._extract_segment_indices(processed_segments),
                statistics=statistics,
                metadata=self._create_metadata(arrays),
                total_points=len(arrays["rpm"]),
                processing_time=time.time() - start_time,
                confidence_score=confidence_score,
            )

            self._last_result = result
            return result

        except Exception as e:
            logger.error(f"Segmentation failed: {str(e)}")
            raise

    def _prepare_data_arrays(
        self,
        data: Union[pd.DataFrame, Dict[str, np.ndarray]],
        timestamp_col: str,
        rpm_col: str,
        tps_col: str,
        map_col: str,
        lambda_col: str,
        two_step_col: str,
        launch_col: str,
    ) -> Dict[str, np.ndarray]:
        """
        Convert input data to optimized numpy arrays.

        Args:
            data: Input data
            *_col: Column names

        Returns:
            Dictionary of numpy arrays with optimized dtypes

        Raises:
            ValueError: If required columns are missing
        """
        if isinstance(data, pd.DataFrame):
            arrays = {}

            # Required columns
            required_cols = [timestamp_col, rpm_col, tps_col, map_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Extract arrays with optimized dtypes
            arrays["timestamp"] = data[timestamp_col].values.astype(np.float64)
            arrays["rpm"] = data[rpm_col].values.astype(np.int16)
            arrays["tps"] = data[tps_col].values.astype(np.float32)
            arrays["map"] = data[map_col].values.astype(np.float32)

            # Optional columns with safe defaults
            arrays["lambda"] = (
                data[lambda_col].values.astype(np.float32)
                if lambda_col in data.columns
                else np.ones(len(data), dtype=np.float32)
            )
            arrays["two_step"] = (
                data[two_step_col].values.astype(bool)
                if two_step_col in data.columns
                else np.zeros(len(data), dtype=bool)
            )
            arrays["launch"] = (
                data[launch_col].values.astype(bool)
                if launch_col in data.columns
                else np.zeros(len(data), dtype=bool)
            )

        elif isinstance(data, dict):
            arrays = {}
            for key, array in data.items():
                if isinstance(array, (list, tuple)):
                    arrays[key] = np.array(array)
                else:
                    arrays[key] = array
        else:
            raise TypeError("Data must be DataFrame or dict of arrays")

        return arrays

    def _validate_data_quality(self, arrays: Dict[str, np.ndarray]) -> None:
        """
        Validate data quality and raise warnings for potential issues.

        Args:
            arrays: Dictionary of data arrays

        Raises:
            ValueError: If data quality is insufficient
        """
        rpm = arrays["rpm"]
        tps = arrays["tps"]
        map_pressure = arrays["map"]

        # Check for minimum data points
        if len(rpm) < 10:
            raise ValueError("Insufficient data points for segmentation (minimum 10)")

        # Check for valid RPM range
        if np.any((rpm < 0) | (rpm > 20000)):
            logger.warning("RPM values outside expected range (0-20000)")

        # Check for valid TPS range
        if np.any((tps < 0) | (tps > 100)):
            logger.warning("TPS values outside expected range (0-100%)")

        # Check for valid MAP pressure range
        if np.any(map_pressure < 0):
            logger.warning("Negative MAP pressure values detected")

        # Check for data consistency
        if len(np.unique([len(arr) for arr in arrays.values()])) > 1:
            raise ValueError("All data arrays must have the same length")

    def _classify_states_vectorized(
        self, arrays: Dict[str, np.ndarray]
    ) -> Dict[EngineState, np.ndarray]:
        """
        Classify engine states using vectorized NumPy operations.

        Args:
            arrays: Dictionary of data arrays

        Returns:
            Dictionary mapping states to boolean masks
        """
        rpm = arrays["rpm"]
        tps = arrays["tps"]
        map_pressure = arrays["map"]
        lambda_val = arrays["lambda"]
        two_step = arrays["two_step"]
        launch = arrays["launch"]

        # Initialize state masks
        state_masks = {}

        # Special states (highest priority)
        state_masks[EngineState.TWO_STEP] = two_step
        state_masks[EngineState.LAUNCH] = launch | (
            (lambda_val <= self.config.launch_lambda_max) & (tps > 80.0) & (rpm < 4000)
        )

        # Overrun state (engine braking)
        state_masks[EngineState.OVERRUN] = (
            (lambda_val >= self.config.overrun_lambda_min) & (tps < 5.0) & (rpm > 2000)
        )

        # Boost conditions
        boost_condition = map_pressure > self.config.boost_threshold

        # Load-based states
        state_masks[EngineState.IDLE] = (rpm <= self.config.idle_rpm_max) & (
            tps <= self.config.idle_tps_max
        )

        state_masks[EngineState.LIGHT_LOAD] = (
            (rpm >= self.config.light_load_rpm_min)
            & (rpm <= self.config.light_load_rpm_max)
            & (tps <= self.config.light_load_tps_max)
            & ~boost_condition
        )

        state_masks[EngineState.MODERATE_LOAD] = (
            (rpm >= self.config.moderate_load_rpm_min)
            & (tps >= self.config.moderate_load_tps_min)
            & (tps < self.config.high_load_tps_min)
            & ~boost_condition
        )

        state_masks[EngineState.HIGH_LOAD] = (
            (rpm >= self.config.high_load_rpm_min)
            & (tps >= self.config.high_load_tps_min)
            & ~boost_condition
        )

        state_masks[EngineState.BOOST] = boost_condition & (tps > self.config.moderate_load_tps_min)

        # Apply hierarchy (special states override general states)
        special_states = [EngineState.TWO_STEP, EngineState.LAUNCH, EngineState.OVERRUN]
        special_mask = np.zeros(len(rpm), dtype=bool)

        for state in special_states:
            if state in state_masks:
                special_mask |= state_masks[state]

        # Clear overlaps with special states
        for state in [
            EngineState.IDLE,
            EngineState.LIGHT_LOAD,
            EngineState.MODERATE_LOAD,
            EngineState.HIGH_LOAD,
            EngineState.BOOST,
        ]:
            if state in state_masks:
                state_masks[state] &= ~special_mask

        return state_masks

    def _post_process_segments(
        self, state_classifications: Dict[EngineState, np.ndarray], timestamps: np.ndarray
    ) -> Dict[EngineState, np.ndarray]:
        """
        Post-process segments for stability and minimum duration.

        Args:
            state_classifications: Raw state classifications
            timestamps: Timestamp array

        Returns:
            Processed state classifications
        """
        processed = {}

        for state, mask in state_classifications.items():
            if not np.any(mask):
                processed[state] = mask
                continue

            # Find continuous segments
            segments = self._find_continuous_segments(mask)

            # Filter by minimum duration
            valid_mask = np.zeros_like(mask, dtype=bool)

            for start_idx, end_idx in segments:
                segment_duration = timestamps[end_idx - 1] - timestamps[start_idx]

                if segment_duration >= self.config.minimum_segment_duration:
                    valid_mask[start_idx:end_idx] = True

            processed[state] = valid_mask

        return processed

    def _find_continuous_segments(self, mask: np.ndarray) -> List[Tuple[int, int]]:
        """
        Find continuous True segments in boolean mask.

        Args:
            mask: Boolean mask array

        Returns:
            List of (start_index, end_index) tuples
        """
        if not np.any(mask):
            return []

        # Find transitions
        diff = np.diff(np.concatenate(([False], mask, [False])).astype(int))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]

        return list(zip(starts, ends))

    def _calculate_segment_statistics(
        self, segments: Dict[EngineState, np.ndarray], arrays: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for each segment.

        Args:
            segments: Segmented data
            arrays: Raw data arrays

        Returns:
            Dictionary of statistics per segment
        """
        statistics = {}

        for state, mask in segments.items():
            if not np.any(mask):
                statistics[state.value] = {"count": 0, "duration": 0.0, "percentage": 0.0}
                continue

            # Basic counts
            count = np.sum(mask)
            percentage = (count / len(mask)) * 100.0

            # Time statistics
            masked_timestamps = arrays["timestamp"][mask]
            if len(masked_timestamps) > 0:
                duration = np.sum(np.diff(masked_timestamps))
            else:
                duration = 0.0

            # Parameter statistics
            stats_dict = {
                "count": int(count),
                "duration": float(duration),
                "percentage": float(percentage),
                "rpm_stats": self._calculate_parameter_stats(arrays["rpm"][mask]),
                "tps_stats": self._calculate_parameter_stats(arrays["tps"][mask]),
                "map_stats": self._calculate_parameter_stats(arrays["map"][mask]),
                "lambda_stats": self._calculate_parameter_stats(arrays["lambda"][mask]),
            }

            statistics[state.value] = stats_dict

        return statistics

    def _calculate_parameter_stats(self, values: np.ndarray) -> Dict[str, float]:
        """
        Calculate statistical measures for a parameter array.

        Args:
            values: Parameter values

        Returns:
            Dictionary of statistical measures
        """
        if len(values) == 0:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "median": 0.0}

        return {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values)),
        }

    def _extract_segment_indices(
        self, segments: Dict[EngineState, np.ndarray]
    ) -> Dict[EngineState, List[Tuple[int, int]]]:
        """
        Extract segment indices for each state.

        Args:
            segments: Segmented boolean masks

        Returns:
            Dictionary of segment index ranges per state
        """
        indices = {}

        for state, mask in segments.items():
            indices[state] = self._find_continuous_segments(mask)

        return indices

    def _create_metadata(self, arrays: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Create metadata about the segmentation process.

        Args:
            arrays: Data arrays

        Returns:
            Metadata dictionary
        """
        return {
            "total_points": len(arrays["rpm"]),
            "time_range": {
                "start": float(np.min(arrays["timestamp"])),
                "end": float(np.max(arrays["timestamp"])),
                "duration": float(np.max(arrays["timestamp"]) - np.min(arrays["timestamp"])),
            },
            "rpm_range": {"min": int(np.min(arrays["rpm"])), "max": int(np.max(arrays["rpm"]))},
            "config": {
                "idle_rpm_max": self.config.idle_rpm_max,
                "boost_threshold": self.config.boost_threshold,
                "minimum_segment_duration": self.config.minimum_segment_duration,
            },
        }

    def _calculate_confidence_score(
        self, segments: Dict[EngineState, np.ndarray], arrays: Dict[str, np.ndarray]
    ) -> float:
        """
        Calculate confidence score for the segmentation quality.

        Args:
            segments: Segmented data
            arrays: Raw data arrays

        Returns:
            Confidence score between 0.0 and 1.0
        """
        total_points = len(arrays["rpm"])
        classified_points = sum(np.sum(mask) for mask in segments.values())

        # Classification coverage
        coverage_score = classified_points / total_points if total_points > 0 else 0.0

        # State distribution balance (penalize single-state dominance)
        state_counts = [np.sum(mask) for mask in segments.values() if np.sum(mask) > 0]
        if len(state_counts) > 1:
            balance_score = 1.0 - (np.std(state_counts) / np.mean(state_counts))
            balance_score = max(0.0, min(1.0, balance_score))
        else:
            balance_score = 0.5  # Neutral score for single state

        # Data quality score
        quality_score = self._assess_data_quality(arrays)

        # Combined confidence score
        confidence = coverage_score * 0.5 + balance_score * 0.3 + quality_score * 0.2
        return max(0.0, min(1.0, confidence))

    def _assess_data_quality(self, arrays: Dict[str, np.ndarray]) -> float:
        """
        Assess data quality for confidence calculation.

        Args:
            arrays: Data arrays

        Returns:
            Quality score between 0.0 and 1.0
        """
        scores = []

        # Check for data completeness
        completeness = 1.0 - (np.sum(np.isnan(arrays["rpm"])) / len(arrays["rpm"]))
        scores.append(completeness)

        # Check for reasonable value ranges
        rpm_valid = np.mean((arrays["rpm"] >= 0) & (arrays["rpm"] <= 15000))
        scores.append(rpm_valid)

        tps_valid = np.mean((arrays["tps"] >= 0) & (arrays["tps"] <= 100))
        scores.append(tps_valid)

        # Check for temporal consistency
        time_diffs = np.diff(arrays["timestamp"])
        temporal_consistency = np.mean(time_diffs > 0)  # Monotonic time
        scores.append(temporal_consistency)

        return float(np.mean(scores))


# High-level interface functions
def segment_log_data(
    data: Union[pd.DataFrame, Dict[str, np.ndarray]],
    config: Optional[SegmentConfig] = None,
    **column_mapping,
) -> SegmentationResult:
    """
    High-level interface for log data segmentation.

    Args:
        data: Input log data
        config: Segmentation configuration
        **column_mapping: Column name mappings

    Returns:
        SegmentationResult with classified engine states

    Example:
        >>> result = segment_log_data(
        ...     dataframe,
        ...     rpm_col="Engine_RPM",
        ...     tps_col="Throttle_Position"
        ... )
        >>> print(f"Found {len(result.segments)} engine states")
        >>> print(f"Confidence: {result.confidence_score:.2f}")
    """
    segmenter = EngineStateSegmenter(config)
    return segmenter.segment_data(data, **column_mapping)


def calculate_segment_statistics(segmentation_result: SegmentationResult) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics from segmentation results.

    Args:
        segmentation_result: Result from segmentation

    Returns:
        Dictionary of comprehensive statistics
    """
    if not segmentation_result.statistics:
        return {}

    summary_stats = {
        "total_segments": len([s for s in segmentation_result.segments.values() if np.any(s)]),
        "total_points": segmentation_result.total_points,
        "processing_time": segmentation_result.processing_time,
        "confidence_score": segmentation_result.confidence_score,
        "state_distribution": {},
    }

    # Calculate state distribution
    for state_name, stats in segmentation_result.statistics.items():
        if stats["count"] > 0:
            summary_stats["state_distribution"][state_name] = {
                "percentage": stats["percentage"],
                "duration": stats["duration"],
                "avg_rpm": stats["rpm_stats"]["mean"],
            }

    return summary_stats


def identify_operating_states(
    data: Union[pd.DataFrame, Dict[str, np.ndarray]], return_dominant_only: bool = True
) -> Union[List[EngineState], EngineState]:
    """
    Quickly identify dominant operating states in log data.

    Args:
        data: Input log data
        return_dominant_only: Return only the most dominant state

    Returns:
        List of engine states or single dominant state

    Example:
        >>> dominant_state = identify_operating_states(data)
        >>> print(f"Primary operating state: {dominant_state.value}")
    """
    result = segment_log_data(data)

    # Get states sorted by percentage
    state_percentages = []
    for state_name, stats in result.statistics.items():
        if stats["count"] > 0:
            state_percentages.append((EngineState(state_name), stats["percentage"]))

    state_percentages.sort(key=lambda x: x[1], reverse=True)

    if return_dominant_only:
        return state_percentages[0][0] if state_percentages else EngineState.IDLE
    else:
        return [state for state, _ in state_percentages]
