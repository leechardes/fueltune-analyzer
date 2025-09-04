"""
FuelTune Analysis Engine - Confidence Scoring Module

This module provides comprehensive confidence scoring for analysis results,
suggestions, and data quality using statistical methods and machine learning
techniques with vectorized NumPy operations.

Classes:
    ConfidenceScorer: Main confidence calculation engine
    ConfidenceConfig: Configuration for scoring parameters
    ConfidenceResult: Result container with detailed metrics
    DataQualityMetrics: Data quality assessment container

Functions:
    calculate_confidence_score: High-level confidence calculation
    assess_data_quality: Comprehensive data quality analysis
    validate_analysis_confidence: Validation of analysis reliability

Performance Target: < 100ms for confidence calculations

Author: FuelTune Analysis Engine
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence level classifications."""
    
    VERY_LOW = "very_low"      # 0.0 - 0.2
    LOW = "low"                # 0.2 - 0.4  
    MODERATE = "moderate"      # 0.4 - 0.6
    HIGH = "high"              # 0.6 - 0.8
    VERY_HIGH = "very_high"    # 0.8 - 1.0


class DataQualityIssue(Enum):
    """Types of data quality issues."""
    
    INSUFFICIENT_DATA = "insufficient_data"
    HIGH_NOISE_LEVEL = "high_noise_level"
    MISSING_VALUES = "missing_values"
    OUTLIERS_PRESENT = "outliers_present"
    NON_MONOTONIC_TIME = "non_monotonic_time"
    VALUE_RANGE_INVALID = "value_range_invalid"
    TEMPORAL_GAPS = "temporal_gaps"
    LOW_VARIABILITY = "low_variability"


@dataclass
class ConfidenceConfig:
    """Configuration for confidence scoring algorithms."""
    
    # Data quantity thresholds
    min_points_very_high: int = 1000
    min_points_high: int = 500
    min_points_moderate: int = 200
    min_points_low: int = 50
    
    # Data quality thresholds
    max_missing_percentage: float = 5.0
    max_outlier_percentage: float = 10.0
    max_noise_cv: float = 0.3  # Coefficient of variation for noise
    min_temporal_consistency: float = 0.95
    
    # Statistical significance thresholds
    min_sample_size_ttest: int = 30
    significance_level: float = 0.05
    min_effect_size: float = 0.3
    
    # Clustering and consistency parameters
    min_silhouette_score: float = 0.5
    consistency_window_size: int = 10
    trend_consistency_threshold: float = 0.8
    
    # Parameter-specific thresholds
    lambda_valid_range: Tuple[float, float] = (0.5, 2.0)
    rpm_valid_range: Tuple[int, int] = (0, 15000)
    map_valid_range: Tuple[float, float] = (0.0, 5.0)
    
    # Confidence calculation weights
    data_quantity_weight: float = 0.25
    data_quality_weight: float = 0.30
    statistical_significance_weight: float = 0.25
    consistency_weight: float = 0.20


@dataclass
class DataQualityMetrics:
    """Container for data quality assessment metrics."""
    
    # Basic metrics
    total_points: int = 0
    missing_count: int = 0
    missing_percentage: float = 0.0
    
    # Statistical metrics
    outlier_count: int = 0
    outlier_percentage: float = 0.0
    noise_level: float = 0.0
    signal_to_noise_ratio: float = 0.0
    
    # Temporal metrics
    temporal_consistency: float = 0.0
    time_gaps_count: int = 0
    sampling_regularity: float = 0.0
    
    # Value range metrics
    range_violations: Dict[str, int] = field(default_factory=dict)
    value_distribution_quality: float = 0.0
    
    # Quality issues
    identified_issues: List[DataQualityIssue] = field(default_factory=list)
    overall_quality_score: float = 0.0


@dataclass
class ConfidenceResult:
    """Container for comprehensive confidence analysis."""
    
    # Overall confidence
    overall_confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.VERY_LOW
    
    # Component scores
    data_quantity_score: float = 0.0
    data_quality_score: float = 0.0
    statistical_significance_score: float = 0.0
    consistency_score: float = 0.0
    
    # Detailed metrics
    data_quality_metrics: DataQualityMetrics = field(default_factory=DataQualityMetrics)
    statistical_tests: Dict[str, Any] = field(default_factory=dict)
    consistency_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Recommendations
    confidence_factors: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    reliability_warnings: List[str] = field(default_factory=list)
    
    # Metadata
    calculation_time: float = 0.0
    parameters_analyzed: List[str] = field(default_factory=list)


class ConfidenceScorer:
    """
    Advanced confidence scoring engine for analysis results.
    
    This class calculates multi-dimensional confidence scores based on
    data quality, statistical significance, and consistency metrics.
    """
    
    def __init__(self, config: Optional[ConfidenceConfig] = None):
        """
        Initialize the confidence scorer.
        
        Args:
            config: Configuration for confidence calculations
        """
        self.config = config or ConfidenceConfig()
        self._last_result: Optional[ConfidenceResult] = None
    
    def calculate_confidence(
        self,
        data: Union[pd.DataFrame, Dict[str, np.ndarray]],
        analysis_result: Optional[Any] = None,
        target_parameter: str = "lambda_sensor",
        reference_values: Optional[Dict[str, float]] = None
    ) -> ConfidenceResult:
        """
        Calculate comprehensive confidence score for analysis data.
        
        Args:
            data: Input data for confidence analysis
            analysis_result: Optional analysis result to validate
            target_parameter: Primary parameter for confidence calculation
            reference_values: Optional reference values for comparison
            
        Returns:
            ConfidenceResult with detailed confidence metrics
            
        Raises:
            ValueError: If data is insufficient for analysis
        """
        import time
        start_time = time.time()
        
        try:
            # Prepare data arrays
            arrays = self._prepare_confidence_data(data)
            
            # Calculate data quantity score
            quantity_score = self._calculate_data_quantity_score(arrays)
            
            # Assess data quality
            quality_metrics = self._assess_data_quality(arrays)
            quality_score = quality_metrics.overall_quality_score
            
            # Calculate statistical significance
            statistical_score, statistical_tests = self._calculate_statistical_significance(
                arrays, target_parameter, reference_values
            )
            
            # Calculate consistency score
            consistency_score, consistency_metrics = self._calculate_consistency_score(arrays)
            
            # Calculate weighted overall confidence
            overall_confidence = self._calculate_weighted_confidence(
                quantity_score, quality_score, statistical_score, consistency_score
            )
            
            # Determine confidence level
            confidence_level = self._determine_confidence_level(overall_confidence)
            
            # Generate recommendations
            factors, improvements, warnings = self._generate_confidence_recommendations(
                quantity_score, quality_score, statistical_score, consistency_score, quality_metrics
            )
            
            # Create result
            result = ConfidenceResult(
                overall_confidence=overall_confidence,
                confidence_level=confidence_level,
                data_quantity_score=quantity_score,
                data_quality_score=quality_score,
                statistical_significance_score=statistical_score,
                consistency_score=consistency_score,
                data_quality_metrics=quality_metrics,
                statistical_tests=statistical_tests,
                consistency_metrics=consistency_metrics,
                confidence_factors=factors,
                improvement_suggestions=improvements,
                reliability_warnings=warnings,
                calculation_time=time.time() - start_time,
                parameters_analyzed=list(arrays.keys())
            )
            
            self._last_result = result
            return result
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {str(e)}")
            raise
    
    def _prepare_confidence_data(
        self, data: Union[pd.DataFrame, Dict[str, np.ndarray]]
    ) -> Dict[str, np.ndarray]:
        """
        Prepare data arrays for confidence analysis.
        
        Args:
            data: Input data
            
        Returns:
            Dictionary of prepared arrays
        """
        if isinstance(data, pd.DataFrame):
            arrays = {}
            
            # Standard columns with safe extraction
            for col in ["timestamp", "rpm", "throttle_position", "map_pressure", "lambda_sensor"]:
                if col in data.columns:
                    arrays[col] = data[col].values.astype(np.float64)
                else:
                    # Create placeholder array
                    arrays[col] = np.full(len(data), np.nan, dtype=np.float64)
            
            # Optional columns
            optional_cols = ["ignition_timing", "engine_temp", "intake_temp", "fuel_pressure"]
            for col in optional_cols:
                if col in data.columns:
                    arrays[col] = data[col].values.astype(np.float64)
        
        elif isinstance(data, dict):
            arrays = {}
            for key, array in data.items():
                if isinstance(array, (list, tuple)):
                    arrays[key] = np.array(array, dtype=np.float64)
                else:
                    arrays[key] = array.astype(np.float64)
        else:
            raise TypeError("Data must be DataFrame or dict of arrays")
        
        return arrays
    
    def _calculate_data_quantity_score(self, arrays: Dict[str, np.ndarray]) -> float:
        """
        Calculate confidence score based on data quantity.
        
        Args:
            arrays: Data arrays
            
        Returns:
            Data quantity score (0-1)
        """
        # Use the largest array for point count
        point_count = max(len(array) for array in arrays.values() if len(array) > 0)
        
        if point_count == 0:
            return 0.0
        
        # Score based on thresholds
        if point_count >= self.config.min_points_very_high:
            return 1.0
        elif point_count >= self.config.min_points_high:
            return 0.8
        elif point_count >= self.config.min_points_moderate:
            return 0.6
        elif point_count >= self.config.min_points_low:
            return 0.4
        else:
            # Linear scaling for very low counts
            return (point_count / self.config.min_points_low) * 0.4
    
    def _assess_data_quality(self, arrays: Dict[str, np.ndarray]) -> DataQualityMetrics:
        """
        Comprehensive data quality assessment.
        
        Args:
            arrays: Data arrays
            
        Returns:
            DataQualityMetrics with detailed assessment
        """
        if not arrays:
            return DataQualityMetrics()
        
        # Get primary data length
        total_points = max(len(array) for array in arrays.values() if len(array) > 0)
        
        if total_points == 0:
            return DataQualityMetrics()
        
        metrics = DataQualityMetrics(total_points=total_points)
        
        # Calculate missing values
        missing_counts = []
        for array in arrays.values():
            if len(array) > 0:
                missing_count = np.sum(np.isnan(array))
                missing_counts.append(missing_count)
        
        metrics.missing_count = int(np.mean(missing_counts)) if missing_counts else 0
        metrics.missing_percentage = (metrics.missing_count / total_points) * 100.0
        
        # Assess outliers and noise for each numeric parameter
        outlier_counts = []
        noise_levels = []
        
        for param_name, array in arrays.items():
            if len(array) == 0 or param_name == "timestamp":
                continue
            
            # Remove NaN values for analysis
            clean_data = array[~np.isnan(array)]
            if len(clean_data) < 10:
                continue
            
            # Outlier detection using IQR method
            q1, q3 = np.percentile(clean_data, [25, 75])
            iqr = q3 - q1
            outlier_bounds = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
            outliers = (clean_data < outlier_bounds[0]) | (clean_data > outlier_bounds[1])
            outlier_counts.append(np.sum(outliers))
            
            # Noise level assessment (coefficient of variation of residuals)
            if len(clean_data) > 20:
                # Simple noise estimation using local variance
                window_size = min(10, len(clean_data) // 5)
                local_stds = []
                
                for i in range(window_size, len(clean_data) - window_size):
                    window = clean_data[i-window_size:i+window_size]
                    local_stds.append(np.std(window))
                
                if local_stds:
                    noise_level = np.mean(local_stds) / (np.mean(clean_data) + 1e-10)
                    noise_levels.append(noise_level)
        
        metrics.outlier_count = int(np.sum(outlier_counts)) if outlier_counts else 0
        metrics.outlier_percentage = (metrics.outlier_count / total_points) * 100.0
        metrics.noise_level = float(np.mean(noise_levels)) if noise_levels else 0.0
        
        # Temporal consistency assessment
        if "timestamp" in arrays and len(arrays["timestamp"]) > 1:
            timestamps = arrays["timestamp"]
            clean_timestamps = timestamps[~np.isnan(timestamps)]
            
            if len(clean_timestamps) > 1:
                # Check monotonicity
                time_diffs = np.diff(clean_timestamps)
                positive_diffs = np.sum(time_diffs > 0)
                metrics.temporal_consistency = positive_diffs / len(time_diffs)
                
                # Count time gaps (unusual jumps)
                median_diff = np.median(time_diffs[time_diffs > 0])
                large_gaps = time_diffs > (median_diff * 5)
                metrics.time_gaps_count = int(np.sum(large_gaps))
                
                # Sampling regularity (consistency of time intervals)
                if median_diff > 0:
                    cv_time_diffs = np.std(time_diffs) / median_diff
                    metrics.sampling_regularity = max(0.0, 1.0 - cv_time_diffs)
        
        # Value range validation
        range_validations = {
            "lambda_sensor": self.config.lambda_valid_range,
            "rpm": self.config.rpm_valid_range,
            "map_pressure": self.config.map_valid_range
        }
        
        for param, (min_val, max_val) in range_validations.items():
            if param in arrays:
                clean_data = arrays[param][~np.isnan(arrays[param])]
                if len(clean_data) > 0:
                    violations = np.sum((clean_data < min_val) | (clean_data > max_val))
                    metrics.range_violations[param] = int(violations)
        
        # Identify quality issues
        issues = []
        
        if total_points < self.config.min_points_moderate:
            issues.append(DataQualityIssue.INSUFFICIENT_DATA)
        
        if metrics.missing_percentage > self.config.max_missing_percentage:
            issues.append(DataQualityIssue.MISSING_VALUES)
        
        if metrics.outlier_percentage > self.config.max_outlier_percentage:
            issues.append(DataQualityIssue.OUTLIERS_PRESENT)
        
        if metrics.noise_level > self.config.max_noise_cv:
            issues.append(DataQualityIssue.HIGH_NOISE_LEVEL)
        
        if metrics.temporal_consistency < self.config.min_temporal_consistency:
            issues.append(DataQualityIssue.NON_MONOTONIC_TIME)
        
        if metrics.time_gaps_count > total_points * 0.1:
            issues.append(DataQualityIssue.TEMPORAL_GAPS)
        
        for param, violations in metrics.range_violations.items():
            if violations > 0:
                issues.append(DataQualityIssue.VALUE_RANGE_INVALID)
                break
        
        metrics.identified_issues = issues
        
        # Calculate overall quality score
        quality_components = [
            1.0 - min(metrics.missing_percentage / 100.0, 1.0),
            1.0 - min(metrics.outlier_percentage / 100.0, 1.0),
            1.0 - min(metrics.noise_level, 1.0),
            metrics.temporal_consistency,
            metrics.sampling_regularity
        ]
        
        metrics.overall_quality_score = float(np.mean(quality_components))
        
        return metrics
    
    def _calculate_statistical_significance(
        self,
        arrays: Dict[str, np.ndarray],
        target_parameter: str,
        reference_values: Optional[Dict[str, float]]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate statistical significance metrics.
        
        Args:
            arrays: Data arrays
            target_parameter: Parameter for significance testing
            reference_values: Reference values for comparison
            
        Returns:
            Tuple of (significance_score, test_results)
        """
        tests = {}
        
        if target_parameter not in arrays:
            return 0.0, tests
        
        target_data = arrays[target_parameter]
        clean_data = target_data[~np.isnan(target_data)]
        
        if len(clean_data) < self.config.min_sample_size_ttest:
            tests["insufficient_data"] = True
            return 0.0, tests
        
        # Basic statistical properties
        tests["sample_size"] = len(clean_data)
        tests["mean"] = float(np.mean(clean_data))
        tests["std"] = float(np.std(clean_data))
        tests["stderr"] = float(stats.sem(clean_data))
        
        # Confidence interval
        confidence_interval = stats.t.interval(
            1 - self.config.significance_level,
            len(clean_data) - 1,
            loc=np.mean(clean_data),
            scale=stats.sem(clean_data)
        )
        tests["confidence_interval_95"] = [float(confidence_interval[0]), float(confidence_interval[1])]
        
        # Normality test
        if len(clean_data) >= 8:  # Minimum for Shapiro-Wilk
            shapiro_stat, shapiro_p = stats.shapiro(clean_data[:5000])  # Limit for performance
            tests["normality_test"] = {
                "statistic": float(shapiro_stat),
                "p_value": float(shapiro_p),
                "is_normal": shapiro_p > self.config.significance_level
            }
        
        # One-sample t-test against reference if provided
        significance_score = 0.5  # Base score
        
        if reference_values and target_parameter in reference_values:
            reference = reference_values[target_parameter]
            t_stat, p_value = stats.ttest_1samp(clean_data, reference)
            
            tests["one_sample_ttest"] = {
                "statistic": float(t_stat),
                "p_value": float(p_value),
                "reference_value": reference,
                "is_significant": p_value < self.config.significance_level
            }
            
            # Effect size (Cohen's d)
            cohens_d = (np.mean(clean_data) - reference) / np.std(clean_data)
            tests["effect_size"] = float(abs(cohens_d))
            
            # Adjust significance score based on effect size and p-value
            if tests["effect_size"] >= self.config.min_effect_size:
                if p_value < 0.001:
                    significance_score = 1.0
                elif p_value < 0.01:
                    significance_score = 0.9
                elif p_value < 0.05:
                    significance_score = 0.8
                else:
                    significance_score = 0.6
            else:
                significance_score = 0.4  # Small effect size
        
        # Sample size adequacy
        sample_size_score = min(len(clean_data) / 500.0, 1.0)  # Full score at 500+ points
        
        # Combined significance score
        final_score = (significance_score * 0.7 + sample_size_score * 0.3)
        
        return float(final_score), tests
    
    def _calculate_consistency_score(
        self, arrays: Dict[str, np.ndarray]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate data consistency metrics.
        
        Args:
            arrays: Data arrays
            
        Returns:
            Tuple of (consistency_score, metrics_dict)
        """
        metrics = {}
        
        # Temporal consistency (already calculated in quality assessment)
        temporal_score = 1.0
        if "timestamp" in arrays:
            timestamps = arrays["timestamp"]
            clean_timestamps = timestamps[~np.isnan(timestamps)]
            
            if len(clean_timestamps) > 1:
                time_diffs = np.diff(clean_timestamps)
                positive_diffs = np.sum(time_diffs > 0)
                temporal_score = positive_diffs / len(time_diffs)
        
        metrics["temporal_consistency"] = temporal_score
        
        # Parameter consistency (relationships between parameters)
        relationship_scores = []
        
        if "rpm" in arrays and "throttle_position" in arrays:
            # RPM-TPS relationship consistency
            rpm_clean = arrays["rpm"][~np.isnan(arrays["rpm"])]
            tps_clean = arrays["throttle_position"][~np.isnan(arrays["throttle_position"])]
            
            if len(rpm_clean) > 10 and len(tps_clean) > 10:
                # Calculate correlation
                min_len = min(len(rpm_clean), len(tps_clean))
                correlation = np.corrcoef(rpm_clean[:min_len], tps_clean[:min_len])[0, 1]
                
                if not np.isnan(correlation):
                    relationship_scores.append(abs(correlation))
                    metrics["rpm_tps_correlation"] = float(correlation)
        
        # Trend consistency (local trend stability)
        trend_scores = []
        
        for param_name, array in arrays.items():
            if param_name == "timestamp" or len(array) < 20:
                continue
            
            clean_data = array[~np.isnan(array)]
            if len(clean_data) < 20:
                continue
            
            # Calculate local trend consistency
            window_size = self.config.consistency_window_size
            trend_consistencies = []
            
            for i in range(window_size, len(clean_data) - window_size):
                window = clean_data[i-window_size:i+window_size]
                
                # Simple trend direction consistency
                diffs = np.diff(window)
                positive_trends = np.sum(diffs > 0)
                negative_trends = np.sum(diffs < 0)
                
                if len(diffs) > 0:
                    trend_consistency = max(positive_trends, negative_trends) / len(diffs)
                    trend_consistencies.append(trend_consistency)
            
            if trend_consistencies:
                avg_trend_consistency = np.mean(trend_consistencies)
                trend_scores.append(avg_trend_consistency)
                metrics[f"{param_name}_trend_consistency"] = float(avg_trend_consistency)
        
        # Variance consistency (stability of variance across time)
        variance_scores = []
        
        for param_name, array in arrays.items():
            if param_name == "timestamp" or len(array) < 50:
                continue
            
            clean_data = array[~np.isnan(array)]
            if len(clean_data) < 50:
                continue
            
            # Split data into segments and compare variances
            n_segments = 5
            segment_size = len(clean_data) // n_segments
            variances = []
            
            for i in range(n_segments):
                start_idx = i * segment_size
                end_idx = start_idx + segment_size
                segment = clean_data[start_idx:end_idx]
                
                if len(segment) > 1:
                    variances.append(np.var(segment))
            
            if len(variances) > 1:
                # Coefficient of variation of variances
                cv_variance = np.std(variances) / (np.mean(variances) + 1e-10)
                variance_consistency = max(0.0, 1.0 - cv_variance)
                variance_scores.append(variance_consistency)
                metrics[f"{param_name}_variance_consistency"] = float(variance_consistency)
        
        # Combined consistency score
        all_scores = [temporal_score] + relationship_scores + trend_scores + variance_scores
        
        if all_scores:
            consistency_score = np.mean(all_scores)
        else:
            consistency_score = 0.5  # Neutral score when insufficient data
        
        metrics["overall_consistency"] = float(consistency_score)
        
        return float(consistency_score), metrics
    
    def _calculate_weighted_confidence(
        self,
        quantity_score: float,
        quality_score: float,
        statistical_score: float,
        consistency_score: float
    ) -> float:
        """
        Calculate weighted overall confidence score.
        
        Args:
            quantity_score: Data quantity score
            quality_score: Data quality score
            statistical_score: Statistical significance score
            consistency_score: Data consistency score
            
        Returns:
            Overall weighted confidence score
        """
        weighted_confidence = (
            quantity_score * self.config.data_quantity_weight +
            quality_score * self.config.data_quality_weight +
            statistical_score * self.config.statistical_significance_weight +
            consistency_score * self.config.consistency_weight
        )
        
        return max(0.0, min(1.0, weighted_confidence))
    
    def _determine_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """
        Determine confidence level classification.
        
        Args:
            confidence_score: Numerical confidence score
            
        Returns:
            ConfidenceLevel enum value
        """
        if confidence_score >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.6:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.4:
            return ConfidenceLevel.MODERATE
        elif confidence_score >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _generate_confidence_recommendations(
        self,
        quantity_score: float,
        quality_score: float,
        statistical_score: float,
        consistency_score: float,
        quality_metrics: DataQualityMetrics
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Generate confidence factors, improvements, and warnings.
        
        Args:
            quantity_score: Data quantity score
            quality_score: Data quality score
            statistical_score: Statistical significance score
            consistency_score: Data consistency score
            quality_metrics: Detailed quality metrics
            
        Returns:
            Tuple of (factors, improvements, warnings)
        """
        factors = []
        improvements = []
        warnings = []
        
        # Positive confidence factors
        if quantity_score >= 0.8:
            factors.append("Sufficient data quantity for reliable analysis")
        
        if quality_score >= 0.8:
            factors.append("High data quality with minimal noise and outliers")
        
        if statistical_score >= 0.8:
            factors.append("Statistically significant results with adequate effect size")
        
        if consistency_score >= 0.8:
            factors.append("Consistent data patterns and stable trends")
        
        # Improvement suggestions
        if quantity_score < 0.6:
            improvements.append(f"Collect more data points (currently {quality_metrics.total_points}, recommend >500)")
        
        if quality_score < 0.6:
            improvements.append("Improve data quality by addressing sensor calibration or filtering")
        
        if DataQualityIssue.MISSING_VALUES in quality_metrics.identified_issues:
            improvements.append(f"Address missing values ({quality_metrics.missing_percentage:.1f}% missing)")
        
        if DataQualityIssue.OUTLIERS_PRESENT in quality_metrics.identified_issues:
            improvements.append(f"Investigate outliers ({quality_metrics.outlier_percentage:.1f}% detected)")
        
        if DataQualityIssue.HIGH_NOISE_LEVEL in quality_metrics.identified_issues:
            improvements.append("Reduce signal noise through sensor maintenance or filtering")
        
        if consistency_score < 0.6:
            improvements.append("Improve measurement consistency through calibration or methodology")
        
        # Reliability warnings
        if quantity_score < 0.4:
            warnings.append("Insufficient data may lead to unreliable conclusions")
        
        if quality_score < 0.4:
            warnings.append("Poor data quality significantly reduces analysis reliability")
        
        if DataQualityIssue.VALUE_RANGE_INVALID in quality_metrics.identified_issues:
            warnings.append("Values outside expected ranges may indicate sensor malfunction")
        
        if DataQualityIssue.NON_MONOTONIC_TIME in quality_metrics.identified_issues:
            warnings.append("Time inconsistencies may affect temporal analysis accuracy")
        
        if statistical_score < 0.3:
            warnings.append("Results may not be statistically significant - interpret with caution")
        
        return factors, improvements, warnings


# High-level interface functions
def calculate_confidence_score(
    data: Union[pd.DataFrame, Dict[str, np.ndarray]],
    config: Optional[ConfidenceConfig] = None,
    target_parameter: str = "lambda_sensor",
    reference_values: Optional[Dict[str, float]] = None
) -> ConfidenceResult:
    """
    High-level interface for confidence score calculation.
    
    Args:
        data: Input data for analysis
        config: Configuration for confidence calculation
        target_parameter: Primary parameter for confidence assessment
        reference_values: Optional reference values for comparison
        
    Returns:
        ConfidenceResult with comprehensive confidence metrics
        
    Example:
        >>> confidence = calculate_confidence_score(
        ...     dataframe,
        ...     target_parameter="lambda_sensor",
        ...     reference_values={"lambda_sensor": 1.0}
        ... )
        >>> print(f"Confidence: {confidence.confidence_level.value} ({confidence.overall_confidence:.2f})")
        >>> for factor in confidence.confidence_factors:
        ...     print(f"+ {factor}")
    """
    scorer = ConfidenceScorer(config)
    return scorer.calculate_confidence(data, None, target_parameter, reference_values)


def assess_data_quality(
    data: Union[pd.DataFrame, Dict[str, np.ndarray]],
    config: Optional[ConfidenceConfig] = None
) -> DataQualityMetrics:
    """
    Comprehensive data quality assessment.
    
    Args:
        data: Input data for quality assessment
        config: Configuration for quality thresholds
        
    Returns:
        DataQualityMetrics with detailed quality analysis
        
    Example:
        >>> quality = assess_data_quality(dataframe)
        >>> print(f"Overall quality: {quality.overall_quality_score:.2f}")
        >>> print(f"Issues found: {len(quality.identified_issues)}")
        >>> for issue in quality.identified_issues:
        ...     print(f"- {issue.value.replace('_', ' ').title()}")
    """
    scorer = ConfidenceScorer(config)
    arrays = scorer._prepare_confidence_data(data)
    return scorer._assess_data_quality(arrays)


def validate_analysis_confidence(
    analysis_result: Any,
    min_confidence: float = 0.6
) -> Tuple[bool, List[str]]:
    """
    Validate if analysis results meet minimum confidence requirements.
    
    Args:
        analysis_result: Analysis result with confidence metrics
        min_confidence: Minimum required confidence score
        
    Returns:
        Tuple of (is_valid, validation_messages)
        
    Example:
        >>> is_valid, messages = validate_analysis_confidence(result, 0.7)
        >>> if not is_valid:
        ...     print("Analysis validation failed:")
        ...     for msg in messages:
        ...         print(f"- {msg}")
    """
    messages = []
    
    # Check if result has confidence information
    if not hasattr(analysis_result, 'confidence_score') and not hasattr(analysis_result, 'overall_confidence'):
        messages.append("Analysis result does not contain confidence information")
        return False, messages
    
    # Get confidence score
    confidence_score = getattr(analysis_result, 'confidence_score', None)
    if confidence_score is None:
        confidence_score = getattr(analysis_result, 'overall_confidence', 0.0)
    
    # Validate confidence level
    is_valid = confidence_score >= min_confidence
    
    if not is_valid:
        messages.append(f"Confidence score {confidence_score:.3f} below minimum required {min_confidence:.3f}")
    
    # Additional validation checks
    if hasattr(analysis_result, 'data_points'):
        data_points = analysis_result.data_points
        if data_points < 100:
            messages.append(f"Low data point count ({data_points}) may affect reliability")
    
    if hasattr(analysis_result, 'warnings') and analysis_result.warnings:
        messages.extend([f"Warning: {warning}" for warning in analysis_result.warnings])
    
    return is_valid, messages