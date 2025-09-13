"""
FuelTune Analysis Engine - Intelligent Suggestions Module

This module provides intelligent tuning suggestions based on analysis of
engine data, segmentation results, and adaptive binning with confidence scoring.

Classes:
    SuggestionEngine: Main suggestion generation engine
    SuggestionConfig: Configuration for suggestion parameters
    TuningSuggestion: Individual tuning suggestion container
    SuggestionsResult: Complete suggestions result with ranking

Functions:
    generate_tuning_suggestions: High-level suggestions interface
    rank_suggestions_by_priority: Priority-based suggestion ranking
    calculate_suggestion_impact: Impact estimation for suggestions

Performance Target: < 1s for 10k data points analysis

Author: FuelTune Analysis Engine
Version: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .binning import BinCell, BinningResult
from .confidence import ConfidenceScorer
from .segmentation import EngineState, SegmentationResult

logger = logging.getLogger(__name__)


class SuggestionType(Enum):
    """Types of tuning suggestions."""

    FUEL_CORRECTION = "fuel_correction"
    IGNITION_TIMING = "ignition_timing"
    BOOST_ADJUSTMENT = "boost_adjustment"
    SAFETY_LIMIT = "safety_limit"
    OPTIMIZATION = "optimization"
    DIAGNOSTIC = "diagnostic"


class SuggestionPriority(Enum):
    """Priority levels for suggestions."""

    CRITICAL = 1  # Safety-related, immediate action required
    HIGH = 2  # Significant performance/reliability impact
    MEDIUM = 3  # Moderate improvement opportunity
    LOW = 4  # Minor optimization or informational


@dataclass
class SuggestionConfig:
    """Configuration for suggestion generation."""

    # AFR/Lambda targets
    target_lambda_idle: float = 1.0
    target_lambda_cruise: float = 1.0
    target_lambda_power: float = 0.85
    target_lambda_boost: float = 0.80
    lambda_tolerance: float = 0.05

    # Safety thresholds
    max_egt_warning: float = 850.0  # °C
    max_egt_critical: float = 900.0  # °C
    lean_limit_warning: float = 1.1
    rich_limit_warning: float = 0.7

    # Ignition timing limits
    max_advance_na: float = 35.0  # degrees BTDC
    max_advance_boost: float = 25.0
    knock_safety_margin: float = 2.0

    # Statistical confidence requirements
    min_confidence_score: float = 0.7
    min_points_for_suggestion: int = 20
    outlier_filter_enabled: bool = True

    # Suggestion ranking weights
    safety_weight: float = 0.4
    performance_weight: float = 0.3
    confidence_weight: float = 0.2
    impact_weight: float = 0.1


@dataclass
class TuningSuggestion:
    """Individual tuning suggestion with metadata."""

    suggestion_type: SuggestionType
    priority: SuggestionPriority
    title: str
    description: str

    # Target parameters
    parameter: str
    current_value: float
    suggested_value: float
    adjustment_percentage: float

    # Context information
    engine_state: Optional[EngineState] = None
    rpm_range: Optional[Tuple[int, int]] = None
    map_range: Optional[Tuple[float, float]] = None
    affected_bins: List[Tuple[int, int]] = field(default_factory=list)

    # Scoring and validation
    confidence_score: float = 0.0
    impact_score: float = 0.0
    safety_score: float = 0.0
    data_points: int = 0

    # Supporting evidence
    evidence: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Calculate adjustment percentage after initialization."""
        if self.current_value != 0:
            self.adjustment_percentage = (
                (self.suggested_value - self.current_value) / self.current_value
            ) * 100.0


@dataclass
class SuggestionsResult:
    """Container for complete suggestions analysis."""

    suggestions: List[TuningSuggestion] = field(default_factory=list)
    summary_statistics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    total_suggestions: int = 0
    critical_suggestions: int = 0
    processing_time: float = 0.0
    overall_confidence: float = 0.0


class SuggestionEngine:
    """
    Intelligent tuning suggestion engine using advanced analytics.

    This class generates actionable tuning suggestions based on engine data
    analysis, segmentation results, and adaptive binning with confidence scoring.
    """

    def __init__(self, config: Optional[SuggestionConfig] = None):
        """
        Initialize the suggestion engine.

        Args:
            config: Suggestion generation configuration
        """
        self.config = config or SuggestionConfig()
        self.confidence_scorer = ConfidenceScorer()
        self._last_result: Optional[SuggestionsResult] = None

    def generate_suggestions(
        self,
        data: Union[pd.DataFrame, Dict[str, np.ndarray]],
        segmentation_result: Optional[SegmentationResult] = None,
        binning_result: Optional[BinningResult] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> SuggestionsResult:
        """
        Generate comprehensive tuning suggestions from analysis data.

        Args:
            data: Raw engine data
            segmentation_result: Engine state segmentation results
            binning_result: Adaptive binning results
            additional_context: Additional context information

        Returns:
            SuggestionsResult with prioritized suggestions

        Raises:
            ValueError: If data is insufficient for analysis
        """
        import time

        start_time = time.time()

        try:
            # Prepare data for analysis
            analysis_data = self._prepare_analysis_data(data)

            # Validate data sufficiency
            self._validate_analysis_data(analysis_data)

            # Generate suggestions by category
            fuel_suggestions = self._generate_fuel_suggestions(
                analysis_data, segmentation_result, binning_result
            )

            ignition_suggestions = self._generate_ignition_suggestions(
                analysis_data, segmentation_result, binning_result
            )

            safety_suggestions = self._generate_safety_suggestions(
                analysis_data, segmentation_result
            )

            optimization_suggestions = self._generate_optimization_suggestions(
                analysis_data, binning_result
            )

            # Combine all suggestions
            all_suggestions = (
                fuel_suggestions
                + ignition_suggestions
                + safety_suggestions
                + optimization_suggestions
            )

            # Calculate confidence scores for all suggestions
            self._calculate_suggestion_confidence(all_suggestions, analysis_data)

            # Rank suggestions by priority and confidence
            ranked_suggestions = self._rank_suggestions(all_suggestions)

            # Calculate summary statistics
            summary_stats = self._calculate_summary_statistics(ranked_suggestions, analysis_data)

            # Create result
            result = SuggestionsResult(
                suggestions=ranked_suggestions,
                summary_statistics=summary_stats,
                metadata=self._create_suggestions_metadata(analysis_data, additional_context),
                total_suggestions=len(ranked_suggestions),
                critical_suggestions=len(
                    [s for s in ranked_suggestions if s.priority == SuggestionPriority.CRITICAL]
                ),
                processing_time=time.time() - start_time,
                overall_confidence=self._calculate_overall_confidence(ranked_suggestions),
            )

            self._last_result = result
            return result

        except Exception as e:
            logger.error(f"Suggestion generation failed: {str(e)}")
            raise

    def _prepare_analysis_data(
        self, data: Union[pd.DataFrame, Dict[str, np.ndarray]]
    ) -> Dict[str, np.ndarray]:
        """
        Prepare data arrays for suggestion analysis.

        Args:
            data: Input data

        Returns:
            Dictionary of analysis-ready arrays
        """
        if isinstance(data, pd.DataFrame):
            arrays = {}

            # Required columns with safe defaults
            arrays["rpm"] = data.get("rpm", pd.Series(dtype=float)).values.astype(np.float32)
            arrays["throttle_position"] = data.get(
                "throttle_position", pd.Series(dtype=float)
            ).values.astype(np.float32)
            arrays["map_pressure"] = data.get("map_pressure", pd.Series(dtype=float)).values.astype(
                np.float32
            )
            arrays["lambda_sensor"] = data.get(
                "lambda_sensor", pd.Series(dtype=float)
            ).values.astype(np.float32)

            # Optional performance columns
            optional_cols = ["ignition_timing", "engine_temp", "intake_temp", "fuel_pressure"]
            for col in optional_cols:
                if col in data.columns:
                    arrays[col] = data[col].values.astype(np.float32)
                else:
                    arrays[col] = np.full(len(arrays["rpm"]), np.nan, dtype=np.float32)

        elif isinstance(data, dict):
            arrays = {}
            for key, array in data.items():
                if isinstance(array, (list, tuple)):
                    arrays[key] = np.array(array, dtype=np.float32)
                else:
                    arrays[key] = array.astype(np.float32)
        else:
            raise TypeError("Data must be DataFrame or dict of arrays")

        return arrays

    def _validate_analysis_data(self, arrays: Dict[str, np.ndarray]) -> None:
        """
        Validate data sufficiency for suggestion generation.

        Args:
            arrays: Analysis data arrays

        Raises:
            ValueError: If data is insufficient
        """
        required_cols = ["rpm", "lambda_sensor"]

        for col in required_cols:
            if col not in arrays or len(arrays[col]) == 0:
                raise ValueError(f"Required column '{col}' is missing or empty")

        # Check minimum data points
        if len(arrays["rpm"]) < self.config.min_points_for_suggestion:
            raise ValueError(
                f"Insufficient data points (minimum {self.config.min_points_for_suggestion})"
            )

        # Check data quality
        lambda_values = arrays["lambda_sensor"]
        valid_lambda = lambda_values[(lambda_values > 0.5) & (lambda_values < 2.0)]

        if len(valid_lambda) < len(lambda_values) * 0.8:
            logger.warning(
                "Lambda sensor data quality may be poor - suggestions may be less reliable"
            )

    def _generate_fuel_suggestions(
        self,
        data: Dict[str, np.ndarray],
        segmentation_result: Optional[SegmentationResult],
        binning_result: Optional[BinningResult],
    ) -> List[TuningSuggestion]:
        """
        Generate fuel-related tuning suggestions.

        Args:
            data: Analysis data
            segmentation_result: Segmentation results
            binning_result: Binning results

        Returns:
            List of fuel tuning suggestions
        """
        suggestions = []
        lambda_values = data["lambda_sensor"]
        rpm_values = data["rpm"]

        # Remove invalid readings
        valid_mask = (lambda_values > 0.5) & (lambda_values < 2.0) & ~np.isnan(lambda_values)
        clean_lambda = lambda_values[valid_mask]
        clean_rpm = rpm_values[valid_mask]

        if len(clean_lambda) == 0:
            return suggestions

        # Analyze by engine states if segmentation is available
        if segmentation_result:
            suggestions.extend(self._analyze_fuel_by_states(data, segmentation_result))

        # Analyze by RPM bins if binning is available
        if binning_result:
            suggestions.extend(self._analyze_fuel_by_bins(data, binning_result))

        # General fuel analysis
        suggestions.extend(self._analyze_general_fuel_trends(clean_lambda, clean_rpm))

        return suggestions

    def _analyze_fuel_by_states(
        self, data: Dict[str, np.ndarray], segmentation_result: SegmentationResult
    ) -> List[TuningSuggestion]:
        """Analyze fuel requirements by engine operating states."""
        suggestions = []

        for state_name, state_stats in segmentation_result.statistics.items():
            if state_stats["count"] < self.config.min_points_for_suggestion:
                continue

            state = EngineState(state_name)
            lambda_stats = state_stats.get("lambda_stats", {})

            if not lambda_stats:
                continue

            current_lambda = lambda_stats["mean"]
            target_lambda = self._get_target_lambda_for_state(state)

            # Check if adjustment is needed
            if abs(current_lambda - target_lambda) > self.config.lambda_tolerance:

                # Calculate fuel correction percentage
                fuel_correction = ((target_lambda - current_lambda) / current_lambda) * 100.0

                # Determine priority based on deviation magnitude
                deviation_ratio = abs(current_lambda - target_lambda) / target_lambda
                if deviation_ratio > 0.15:
                    priority = SuggestionPriority.HIGH
                elif deviation_ratio > 0.08:
                    priority = SuggestionPriority.MEDIUM
                else:
                    priority = SuggestionPriority.LOW

                # Create suggestion
                suggestion = TuningSuggestion(
                    suggestion_type=SuggestionType.FUEL_CORRECTION,
                    priority=priority,
                    title=f"Fuel Correction - {state.value.replace('_', ' ').title()}",
                    description=f"Adjust fuel delivery for {state.value} conditions. "
                    f"Current λ: {current_lambda:.3f}, Target λ: {target_lambda:.3f}",
                    parameter="fuel_correction",
                    current_value=current_lambda,
                    suggested_value=target_lambda,
                    adjustment_percentage=fuel_correction,
                    engine_state=state,
                    data_points=state_stats["count"],
                    evidence={
                        "current_stats": lambda_stats,
                        "target_lambda": target_lambda,
                        "deviation_ratio": deviation_ratio,
                        "state_duration": state_stats["duration"],
                    },
                )

                suggestions.append(suggestion)

        return suggestions

    def _analyze_fuel_by_bins(
        self, data: Dict[str, np.ndarray], binning_result: BinningResult
    ) -> List[TuningSuggestion]:
        """Analyze fuel requirements by MAP×RPM bins."""
        suggestions = []

        for bin_coord, bin_cell in binning_result.bins.items():
            if bin_cell.point_count < self.config.min_points_for_suggestion:
                continue

            if "lambda_sensor" not in bin_cell.statistics:
                continue

            lambda_stats = bin_cell.statistics["lambda_sensor"]
            current_lambda = lambda_stats["mean"]

            # Determine target lambda based on load conditions
            target_lambda = self._get_target_lambda_for_bin(bin_cell)

            # Check if significant deviation exists
            if abs(current_lambda - target_lambda) > self.config.lambda_tolerance:

                fuel_correction = ((target_lambda - current_lambda) / current_lambda) * 100.0

                suggestion = TuningSuggestion(
                    suggestion_type=SuggestionType.FUEL_CORRECTION,
                    priority=SuggestionPriority.MEDIUM,
                    title=f"Bin Fuel Correction ({int(bin_cell.rpm_center)}rpm, {bin_cell.map_center:.2f}bar)",
                    description=f"Adjust fuel in bin at {int(bin_cell.rpm_center)}rpm, "
                    f"{bin_cell.map_center:.2f}bar MAP. Current λ: {current_lambda:.3f}",
                    parameter="fuel_table",
                    current_value=current_lambda,
                    suggested_value=target_lambda,
                    adjustment_percentage=fuel_correction,
                    rpm_range=(int(bin_cell.rpm_range[0]), int(bin_cell.rpm_range[1])),
                    map_range=bin_cell.map_range,
                    affected_bins=[bin_coord],
                    data_points=bin_cell.point_count,
                    evidence={
                        "bin_stats": lambda_stats,
                        "target_lambda": target_lambda,
                        "bin_confidence": bin_cell.confidence_score,
                    },
                )

                suggestions.append(suggestion)

        return suggestions

    def _analyze_general_fuel_trends(
        self, lambda_values: np.ndarray, rpm_values: np.ndarray
    ) -> List[TuningSuggestion]:
        """Analyze general fuel trends across the dataset."""
        suggestions = []

        # Overall rich/lean bias detection
        overall_lambda = np.mean(lambda_values)

        if overall_lambda < 0.8:
            suggestions.append(
                TuningSuggestion(
                    suggestion_type=SuggestionType.FUEL_CORRECTION,
                    priority=SuggestionPriority.HIGH,
                    title="Overall Rich Condition Detected",
                    description=f"Engine is running consistently rich (λ={overall_lambda:.3f}). "
                    f"Consider reducing base fuel delivery.",
                    parameter="base_fuel",
                    current_value=overall_lambda,
                    suggested_value=0.9,
                    adjustment_percentage=((0.9 - overall_lambda) / overall_lambda) * 100,
                    data_points=len(lambda_values),
                    evidence={
                        "mean_lambda": overall_lambda,
                        "std_lambda": float(np.std(lambda_values)),
                        "rich_percentage": float(np.mean(lambda_values < 0.85) * 100),
                    },
                )
            )

        elif overall_lambda > 1.1:
            suggestions.append(
                TuningSuggestion(
                    suggestion_type=SuggestionType.SAFETY_LIMIT,
                    priority=SuggestionPriority.CRITICAL,
                    title="Overall Lean Condition Detected",
                    description=f"Engine is running dangerously lean (λ={overall_lambda:.3f}). "
                    f"Increase fuel delivery immediately.",
                    parameter="base_fuel",
                    current_value=overall_lambda,
                    suggested_value=1.0,
                    adjustment_percentage=((1.0 - overall_lambda) / overall_lambda) * 100,
                    data_points=len(lambda_values),
                    evidence={
                        "mean_lambda": overall_lambda,
                        "lean_percentage": float(np.mean(lambda_values > 1.05) * 100),
                        "max_lambda": float(np.max(lambda_values)),
                    },
                    warnings=["Lean conditions can cause engine damage"],
                )
            )

        return suggestions

    def _generate_ignition_suggestions(
        self,
        data: Dict[str, np.ndarray],
        segmentation_result: Optional[SegmentationResult],
        binning_result: Optional[BinningResult],
    ) -> List[TuningSuggestion]:
        """Generate ignition timing suggestions."""
        suggestions = []

        # Check if ignition timing data is available
        if "ignition_timing" not in data or np.all(np.isnan(data["ignition_timing"])):
            return suggestions

        timing_values = data["ignition_timing"]
        valid_mask = ~np.isnan(timing_values)

        if np.sum(valid_mask) < self.config.min_points_for_suggestion:
            return suggestions

        # Analyze timing by operating states
        if segmentation_result:
            suggestions.extend(self._analyze_timing_by_states(data, segmentation_result))

        return suggestions

    def _analyze_timing_by_states(
        self, data: Dict[str, np.ndarray], segmentation_result: SegmentationResult
    ) -> List[TuningSuggestion]:
        """Analyze ignition timing by engine states."""
        suggestions = []

        timing_data = data["ignition_timing"]
        data.get("map_pressure", np.ones_like(timing_data))

        for state_name, state_stats in segmentation_result.statistics.items():
            if state_stats["count"] < self.config.min_points_for_suggestion:
                continue

            state = EngineState(state_name)

            # Get timing statistics for this state
            # Note: This would require state masks from segmentation result
            # For now, we'll use overall statistics as example

            current_timing = 25.0  # Placeholder - would get from state data
            is_boost = "boost" in state_name.lower()
            max_timing = self.config.max_advance_boost if is_boost else self.config.max_advance_na

            if current_timing > max_timing:
                suggestion = TuningSuggestion(
                    suggestion_type=SuggestionType.IGNITION_TIMING,
                    priority=SuggestionPriority.HIGH,
                    title=f"Excessive Timing Advance - {state.value.replace('_', ' ').title()}",
                    description=f"Ignition timing ({current_timing:.1f}°) exceeds safe limits "
                    f"for {state.value} conditions (max {max_timing:.1f}°)",
                    parameter="ignition_timing",
                    current_value=current_timing,
                    suggested_value=max_timing - self.config.knock_safety_margin,
                    adjustment_percentage=0,
                    engine_state=state,
                    data_points=state_stats["count"],
                    evidence={
                        "current_timing": current_timing,
                        "max_safe_timing": max_timing,
                        "is_boost_condition": is_boost,
                    },
                    warnings=["Excessive timing can cause knock and engine damage"],
                )

                suggestions.append(suggestion)

        return suggestions

    def _generate_safety_suggestions(
        self, data: Dict[str, np.ndarray], segmentation_result: Optional[SegmentationResult]
    ) -> List[TuningSuggestion]:
        """Generate safety-related suggestions."""
        suggestions = []

        lambda_values = data["lambda_sensor"]

        # Detect dangerously lean conditions
        extremely_lean_mask = lambda_values > self.config.lean_limit_warning
        if np.any(extremely_lean_mask):
            lean_percentage = np.mean(extremely_lean_mask) * 100

            suggestion = TuningSuggestion(
                suggestion_type=SuggestionType.SAFETY_LIMIT,
                priority=SuggestionPriority.CRITICAL,
                title="Dangerous Lean Conditions Detected",
                description=f"Engine running dangerously lean {lean_percentage:.1f}% of the time. "
                f"Maximum λ observed: {np.max(lambda_values):.3f}",
                parameter="safety_limit",
                current_value=float(np.max(lambda_values)),
                suggested_value=self.config.lean_limit_warning,
                adjustment_percentage=0,
                data_points=int(np.sum(extremely_lean_mask)),
                evidence={
                    "lean_percentage": lean_percentage,
                    "max_lambda": float(np.max(lambda_values)),
                    "lean_threshold": self.config.lean_limit_warning,
                },
                warnings=[
                    "Lean conditions can cause engine damage",
                    "Check fuel system pressure and delivery",
                    "Review fuel maps immediately",
                ],
            )

            suggestions.append(suggestion)

        # Detect extremely rich conditions
        extremely_rich_mask = lambda_values < self.config.rich_limit_warning
        if np.any(extremely_rich_mask):
            rich_percentage = np.mean(extremely_rich_mask) * 100

            suggestion = TuningSuggestion(
                suggestion_type=SuggestionType.SAFETY_LIMIT,
                priority=SuggestionPriority.HIGH,
                title="Extremely Rich Conditions Detected",
                description=f"Engine running extremely rich {rich_percentage:.1f}% of the time. "
                f"Minimum λ observed: {np.min(lambda_values):.3f}",
                parameter="safety_limit",
                current_value=float(np.min(lambda_values)),
                suggested_value=self.config.rich_limit_warning,
                adjustment_percentage=0,
                data_points=int(np.sum(extremely_rich_mask)),
                evidence={
                    "rich_percentage": rich_percentage,
                    "min_lambda": float(np.min(lambda_values)),
                    "rich_threshold": self.config.rich_limit_warning,
                },
                warnings=[
                    "Extreme richness causes poor performance and emissions",
                    "Check for injector issues or incorrect fuel pressure",
                    "Review base fuel maps",
                ],
            )

            suggestions.append(suggestion)

        return suggestions

    def _generate_optimization_suggestions(
        self, data: Dict[str, np.ndarray], binning_result: Optional[BinningResult]
    ) -> List[TuningSuggestion]:
        """Generate optimization suggestions."""
        suggestions = []

        if not binning_result:
            return suggestions

        # Analyze bin coverage and data density
        total_bins = len(binning_result.bins)
        high_confidence_bins = sum(
            1 for bin_cell in binning_result.bins.values() if bin_cell.confidence_score > 0.8
        )

        if high_confidence_bins / total_bins < 0.6:
            suggestion = TuningSuggestion(
                suggestion_type=SuggestionType.OPTIMIZATION,
                priority=SuggestionPriority.MEDIUM,
                title="Improve Data Coverage",
                description=f"Only {high_confidence_bins}/{total_bins} bins have high confidence. "
                f"Consider additional data logging in underrepresented areas.",
                parameter="data_coverage",
                current_value=high_confidence_bins / total_bins,
                suggested_value=0.8,
                adjustment_percentage=0,
                data_points=binning_result.total_points,
                evidence={
                    "high_confidence_bins": high_confidence_bins,
                    "total_bins": total_bins,
                    "coverage_ratio": high_confidence_bins / total_bins,
                },
            )

            suggestions.append(suggestion)

        return suggestions

    def _get_target_lambda_for_state(self, state: EngineState) -> float:
        """Get target lambda for specific engine state."""
        targets = {
            EngineState.IDLE: self.config.target_lambda_idle,
            EngineState.LIGHT_LOAD: self.config.target_lambda_cruise,
            EngineState.MODERATE_LOAD: self.config.target_lambda_cruise,
            EngineState.HIGH_LOAD: self.config.target_lambda_power,
            EngineState.BOOST: self.config.target_lambda_boost,
            EngineState.OVERRUN: 1.2,  # Lean for overrun
            EngineState.LAUNCH: 0.78,  # Rich for launch
            EngineState.TWO_STEP: 0.75,  # Very rich for two-step
        }

        return targets.get(state, 1.0)

    def _get_target_lambda_for_bin(self, bin_cell: BinCell) -> float:
        """Get target lambda based on bin conditions."""
        # Estimate load based on MAP pressure
        if bin_cell.map_center > 1.5:  # High boost
            return self.config.target_lambda_boost
        elif bin_cell.map_center > 1.05:  # Light boost
            return 0.88
        elif bin_cell.rpm_center > 6000:  # High RPM
            return self.config.target_lambda_power
        elif bin_cell.rpm_center < 2000:  # Low RPM
            return self.config.target_lambda_idle
        else:  # Cruise conditions
            return self.config.target_lambda_cruise

    def _calculate_suggestion_confidence(
        self, suggestions: List[TuningSuggestion], data: Dict[str, np.ndarray]
    ) -> None:
        """Calculate confidence scores for all suggestions."""
        for suggestion in suggestions:
            # Base confidence on data points
            data_confidence = min(suggestion.data_points / 100.0, 1.0)

            # Safety suggestions get higher confidence
            safety_bonus = 0.2 if suggestion.suggestion_type == SuggestionType.SAFETY_LIMIT else 0.0

            # Calculate final confidence
            suggestion.confidence_score = min(data_confidence + safety_bonus, 1.0)

            # Calculate impact score based on deviation magnitude
            if suggestion.current_value != 0:
                deviation = (
                    abs(suggestion.suggested_value - suggestion.current_value)
                    / suggestion.current_value
                )
                suggestion.impact_score = min(deviation * 2, 1.0)

            # Calculate safety score (inverse of risk)
            if suggestion.suggestion_type == SuggestionType.SAFETY_LIMIT:
                suggestion.safety_score = 1.0
            elif suggestion.priority == SuggestionPriority.CRITICAL:
                suggestion.safety_score = 0.9
            else:
                suggestion.safety_score = 0.5

    def _rank_suggestions(self, suggestions: List[TuningSuggestion]) -> List[TuningSuggestion]:
        """Rank suggestions by priority and weighted scoring."""

        def calculate_rank_score(suggestion: TuningSuggestion) -> float:
            """Calculate combined ranking score."""
            priority_score = (5 - suggestion.priority.value) / 4.0  # Higher priority = higher score

            weighted_score = (
                suggestion.safety_score * self.config.safety_weight
                + suggestion.impact_score * self.config.performance_weight
                + suggestion.confidence_score * self.config.confidence_weight
                + priority_score * self.config.impact_weight
            )

            return weighted_score

        # Calculate rank scores
        for suggestion in suggestions:
            suggestion.evidence["rank_score"] = calculate_rank_score(suggestion)

        # Sort by rank score (highest first)
        return sorted(suggestions, key=lambda s: s.evidence["rank_score"], reverse=True)

    def _calculate_summary_statistics(
        self, suggestions: List[TuningSuggestion], data: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """Calculate summary statistics for suggestions."""
        if not suggestions:
            return {}

        # Count by priority
        priority_counts = {}
        for priority in SuggestionPriority:
            priority_counts[priority.name.lower()] = sum(
                1 for s in suggestions if s.priority == priority
            )

        # Count by type
        type_counts = {}
        for suggestion_type in SuggestionType:
            type_counts[suggestion_type.value] = sum(
                1 for s in suggestions if s.suggestion_type == suggestion_type
            )

        # Calculate average scores
        avg_confidence = np.mean([s.confidence_score for s in suggestions])
        avg_impact = np.mean([s.impact_score for s in suggestions])
        avg_safety = np.mean([s.safety_score for s in suggestions])

        return {
            "priority_distribution": priority_counts,
            "type_distribution": type_counts,
            "average_scores": {
                "confidence": float(avg_confidence),
                "impact": float(avg_impact),
                "safety": float(avg_safety),
            },
            "data_coverage": {
                "total_data_points": len(data["rpm"]),
                "suggestions_with_high_confidence": sum(
                    1 for s in suggestions if s.confidence_score > 0.8
                ),
            },
        }

    def _calculate_overall_confidence(self, suggestions: List[TuningSuggestion]) -> float:
        """Calculate overall confidence in the suggestions."""
        if not suggestions:
            return 0.0

        # Weight by priority (critical suggestions more important)
        weighted_confidence = 0.0
        total_weight = 0.0

        for suggestion in suggestions:
            priority_weight = (5 - suggestion.priority.value) / 4.0
            weighted_confidence += suggestion.confidence_score * priority_weight
            total_weight += priority_weight

        return weighted_confidence / total_weight if total_weight > 0 else 0.0

    def _create_suggestions_metadata(
        self, data: Dict[str, np.ndarray], additional_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create metadata for the suggestions result."""
        metadata = {
            "analysis_parameters": {
                "min_confidence_score": self.config.min_confidence_score,
                "min_points_for_suggestion": self.config.min_points_for_suggestion,
                "lambda_tolerance": self.config.lambda_tolerance,
            },
            "data_characteristics": {
                "total_points": len(data["rpm"]),
                "rpm_range": [float(np.min(data["rpm"])), float(np.max(data["rpm"]))],
                "lambda_range": [
                    float(np.min(data["lambda_sensor"])),
                    float(np.max(data["lambda_sensor"])),
                ],
            },
        }

        if additional_context:
            metadata["additional_context"] = additional_context

        return metadata


# High-level interface functions
def generate_tuning_suggestions(
    data: Union[pd.DataFrame, Dict[str, np.ndarray]],
    config: Optional[SuggestionConfig] = None,
    segmentation_result: Optional[SegmentationResult] = None,
    binning_result: Optional[BinningResult] = None,
    **kwargs,
) -> SuggestionsResult:
    """
    High-level interface for generating tuning suggestions.

    Args:
        data: Engine log data
        config: Suggestion configuration
        segmentation_result: Optional segmentation results
        binning_result: Optional binning results
        **kwargs: Additional context

    Returns:
        SuggestionsResult with prioritized suggestions

    Example:
        >>> suggestions = generate_tuning_suggestions(
        ...     dataframe,
        ...     segmentation_result=seg_result,
        ...     binning_result=bin_result
        ... )
        >>>
        >>> print(f"Generated {len(suggestions.suggestions)} suggestions")
        >>> for suggestion in suggestions.suggestions[:5]:  # Top 5
        ...     print(f"- {suggestion.title} ({suggestion.priority.name})")
    """
    engine = SuggestionEngine(config)
    return engine.generate_suggestions(data, segmentation_result, binning_result, kwargs)


def rank_suggestions_by_priority(suggestions: List[TuningSuggestion]) -> List[TuningSuggestion]:
    """
    Rank suggestions by priority and impact.

    Args:
        suggestions: List of tuning suggestions

    Returns:
        Sorted list of suggestions
    """
    return sorted(
        suggestions, key=lambda s: (s.priority.value, -s.confidence_score, -s.impact_score)
    )


def calculate_suggestion_impact(
    suggestion: TuningSuggestion, current_performance: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Calculate estimated impact of implementing a suggestion.

    Args:
        suggestion: Tuning suggestion to analyze
        current_performance: Current performance metrics

    Returns:
        Dictionary of estimated impact metrics

    Example:
        >>> impact = calculate_suggestion_impact(suggestion)
        >>> print(f"Estimated performance improvement: {impact['performance_gain']:.1f}%")
    """
    impact = {
        "confidence": suggestion.confidence_score,
        "safety_improvement": suggestion.safety_score,
        "performance_gain": suggestion.impact_score * 100,  # Convert to percentage
        "implementation_difficulty": 1.0 - (suggestion.data_points / 1000),  # More data = easier
        "risk_level": 1.0 - suggestion.safety_score,
    }

    # Adjust based on suggestion type
    if suggestion.suggestion_type == SuggestionType.SAFETY_LIMIT:
        impact["priority_multiplier"] = 2.0
    elif suggestion.suggestion_type == SuggestionType.FUEL_CORRECTION:
        impact["priority_multiplier"] = 1.5
    else:
        impact["priority_multiplier"] = 1.0

    return impact
