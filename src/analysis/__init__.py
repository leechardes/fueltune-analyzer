"""
FuelTune Analysis Module.

Comprehensive scientific analysis capabilities for automotive telemetry data.

Author: A04-ANALYSIS-SCIPY Agent + IMPLEMENT-ANALYSIS-ENGINE Agent
Created: 2025-01-02
Updated: 2025-09-04 - Added Analysis Engine Components
"""

from .anomaly import AnomalyDetector, AnomalyResults
from .binning import (
    AdaptiveBinner,
    BinCell,
    BinningConfig,
    BinningResult,
    analyze_bin_density,
    calculate_bin_statistics,
    create_adaptive_bins,
)
from .confidence import (
    ConfidenceConfig,
    ConfidenceLevel,
    ConfidenceResult,
    ConfidenceScorer,
    DataQualityIssue,
    DataQualityMetrics,
    assess_data_quality,
    calculate_confidence_score,
    validate_analysis_confidence,
)
from .correlation import CorrelationAnalyzer, CorrelationMatrix
from .dynamics import GForceAnalysis, VehicleDynamicsAnalyzer
from .fuel_efficiency import BSFCAnalysisResults, FuelEfficiencyAnalyzer
from .performance import PerformanceAnalyzer, PowerTorqueResults
from .predictive import FailurePredictionResults, PredictiveAnalyzer
from .reports import ExecutiveSummary, ReportGenerator
from .safety import (
    SafetyConfig,
    SafetyLevel,
    SafetyResult,
    SafetyValidator,
    SafetyViolation,
    ViolationType,
    apply_safety_constraints,
    check_critical_parameters,
    validate_safety_limits,
)

# Analysis Engine Components (Added 2025-09-04)
from .segmentation import (
    EngineState,
    EngineStateSegmenter,
    SegmentationResult,
    SegmentConfig,
    calculate_segment_statistics,
    identify_operating_states,
    segment_log_data,
)
from .statistics import DescriptiveStats, StatisticalAnalyzer
from .suggestions import (
    SuggestionConfig,
    SuggestionEngine,
    SuggestionPriority,
    SuggestionsResult,
    SuggestionType,
    TuningSuggestion,
    calculate_suggestion_impact,
    generate_tuning_suggestions,
    rank_suggestions_by_priority,
)
from .time_series import TimeSeriesAnalyzer, TrendAnalysisResults

__all__ = [
    # Original Analyzers
    "AnomalyDetector",
    "CorrelationAnalyzer",
    "VehicleDynamicsAnalyzer",
    "FuelEfficiencyAnalyzer",
    "PerformanceAnalyzer",
    "PredictiveAnalyzer",
    "ReportGenerator",
    "StatisticalAnalyzer",
    "TimeSeriesAnalyzer",
    # Original Results Classes
    "AnomalyResults",
    "CorrelationMatrix",
    "GForceAnalysis",
    "BSFCAnalysisResults",
    "PowerTorqueResults",
    "FailurePredictionResults",
    "ExecutiveSummary",
    "DescriptiveStats",
    "TrendAnalysisResults",
    # Analysis Engine Classes (Added 2025-09-04)
    "EngineStateSegmenter",
    "SegmentationResult",
    "SegmentConfig",
    "EngineState",
    "AdaptiveBinner",
    "BinningResult",
    "BinningConfig",
    "BinCell",
    "SuggestionEngine",
    "SuggestionsResult",
    "SuggestionConfig",
    "TuningSuggestion",
    "SuggestionType",
    "SuggestionPriority",
    "ConfidenceScorer",
    "ConfidenceResult",
    "ConfidenceConfig",
    "DataQualityMetrics",
    "ConfidenceLevel",
    "DataQualityIssue",
    "SafetyValidator",
    "SafetyResult",
    "SafetyConfig",
    "SafetyViolation",
    "SafetyLevel",
    "ViolationType",
    # Analysis Engine Functions (Added 2025-09-04)
    "segment_log_data",
    "calculate_segment_statistics",
    "identify_operating_states",
    "create_adaptive_bins",
    "analyze_bin_density",
    "calculate_bin_statistics",
    "generate_tuning_suggestions",
    "rank_suggestions_by_priority",
    "calculate_suggestion_impact",
    "calculate_confidence_score",
    "assess_data_quality",
    "validate_analysis_confidence",
    "validate_safety_limits",
    "check_critical_parameters",
    "apply_safety_constraints",
]

__version__ = "1.0.0"
