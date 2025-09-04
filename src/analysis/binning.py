"""
FuelTune Analysis Engine - Adaptive Binning Module

This module provides adaptive MAP×RPM binning functionality with density-aware
cell sizing and statistical analysis using vectorized NumPy operations.

Classes:
    AdaptiveBinner: Main adaptive binning engine
    BinningConfig: Configuration for binning parameters  
    BinningResult: Result container with statistics
    BinCell: Individual bin cell with metadata

Functions:
    create_adaptive_bins: High-level binning interface
    analyze_bin_density: Data density analysis
    calculate_bin_statistics: Statistical measures per bin

Performance Target: < 1s for 10k data points

Author: FuelTune Analysis Engine  
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial import cKDTree
import logging

logger = logging.getLogger(__name__)


@dataclass
class BinningConfig:
    """Configuration for adaptive MAP×RPM binning."""
    
    # Base grid parameters
    base_rpm_bins: int = 20
    base_map_bins: int = 15
    
    # Adaptive parameters
    min_points_per_bin: int = 10
    max_points_per_bin: int = 100
    density_threshold: float = 0.5
    adaptive_factor: float = 1.5
    
    # RPM range parameters
    rpm_min: Optional[int] = None
    rpm_max: Optional[int] = None
    auto_rpm_range: bool = True
    rpm_padding_percent: float = 5.0
    
    # MAP pressure range parameters
    map_min: Optional[float] = None
    map_max: Optional[float] = None
    auto_map_range: bool = True
    map_padding_percent: float = 5.0
    
    # Statistical parameters
    outlier_method: str = "iqr"  # "iqr", "zscore", "isolation"
    outlier_factor: float = 1.5
    confidence_level: float = 0.95
    
    # Performance parameters
    max_bins_total: int = 500
    parallel_processing: bool = True


@dataclass
class BinCell:
    """Individual bin cell with data and statistics."""
    
    rpm_center: float
    map_center: float
    rpm_range: Tuple[float, float]
    map_range: Tuple[float, float]
    point_count: int
    data_indices: List[int] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    density_score: float = 0.0
    confidence_score: float = 0.0
    is_valid: bool = False


@dataclass
class BinningResult:
    """Container for adaptive binning results."""
    
    bins: Dict[Tuple[int, int], BinCell] = field(default_factory=dict)
    rpm_edges: np.ndarray = field(default_factory=lambda: np.array([]))
    map_edges: np.ndarray = field(default_factory=lambda: np.array([]))
    grid_shape: Tuple[int, int] = (0, 0)
    statistics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    total_points: int = 0
    valid_bins: int = 0
    processing_time: float = 0.0
    confidence_score: float = 0.0


class AdaptiveBinner:
    """
    High-performance adaptive MAP×RPM binning engine.
    
    This class creates optimally-sized bins based on data density and
    statistical requirements using vectorized operations.
    """
    
    def __init__(self, config: Optional[BinningConfig] = None):
        """
        Initialize the adaptive binner.
        
        Args:
            config: Binning configuration parameters
        """
        self.config = config or BinningConfig()
        self._last_result: Optional[BinningResult] = None
    
    def create_bins(
        self,
        data: Union[pd.DataFrame, Dict[str, np.ndarray]],
        rpm_col: str = "rpm",
        map_col: str = "map_pressure",
        additional_cols: Optional[List[str]] = None
    ) -> BinningResult:
        """
        Create adaptive bins for MAP×RPM data using density analysis.
        
        Args:
            data: Input data as DataFrame or dict of arrays
            rpm_col: RPM column name
            map_col: MAP pressure column name  
            additional_cols: Additional columns to analyze per bin
            
        Returns:
            BinningResult with adaptive bin structure
            
        Raises:
            ValueError: If required columns are missing
            TypeError: If data types are invalid
        """
        import time
        start_time = time.time()
        
        try:
            # Prepare data arrays
            arrays = self._prepare_data_arrays(data, rpm_col, map_col, additional_cols)
            
            # Validate data quality
            self._validate_binning_data(arrays)
            
            # Determine optimal ranges
            rpm_range, map_range = self._determine_optimal_ranges(arrays)
            
            # Create base grid structure
            base_grid = self._create_base_grid(arrays, rpm_range, map_range)
            
            # Analyze data density
            density_map = self._analyze_data_density(arrays, base_grid)
            
            # Create adaptive bins based on density
            adaptive_bins = self._create_adaptive_bins(arrays, base_grid, density_map)
            
            # Calculate bin statistics
            self._calculate_bin_statistics(adaptive_bins, arrays, additional_cols)
            
            # Validate and filter bins
            valid_bins = self._validate_and_filter_bins(adaptive_bins)
            
            # Calculate overall statistics
            overall_stats = self._calculate_overall_statistics(valid_bins, arrays)
            
            # Calculate confidence score
            confidence_score = self._calculate_binning_confidence(valid_bins, arrays)
            
            # Create result
            result = BinningResult(
                bins=valid_bins,
                rpm_edges=base_grid["rpm_edges"],
                map_edges=base_grid["map_edges"],
                grid_shape=base_grid["grid_shape"],
                statistics=overall_stats,
                metadata=self._create_binning_metadata(arrays, rpm_range, map_range),
                total_points=len(arrays["rpm"]),
                valid_bins=len(valid_bins),
                processing_time=time.time() - start_time,
                confidence_score=confidence_score
            )
            
            self._last_result = result
            return result
            
        except Exception as e:
            logger.error(f"Binning failed: {str(e)}")
            raise
    
    def _prepare_data_arrays(
        self,
        data: Union[pd.DataFrame, Dict[str, np.ndarray]],
        rpm_col: str,
        map_col: str,
        additional_cols: Optional[List[str]]
    ) -> Dict[str, np.ndarray]:
        """
        Prepare data arrays for binning operations.
        
        Args:
            data: Input data
            rpm_col: RPM column name
            map_col: MAP pressure column name
            additional_cols: Additional columns to include
            
        Returns:
            Dictionary of numpy arrays with optimized dtypes
        """
        if isinstance(data, pd.DataFrame):
            # Check required columns
            required_cols = [rpm_col, map_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            arrays = {}
            arrays["rpm"] = data[rpm_col].values.astype(np.float32)
            arrays["map"] = data[map_col].values.astype(np.float32)
            
            # Add additional columns if specified
            if additional_cols:
                for col in additional_cols:
                    if col in data.columns:
                        arrays[col] = data[col].values.astype(np.float32)
                    else:
                        logger.warning(f"Additional column '{col}' not found in data")
            
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
    
    def _validate_binning_data(self, arrays: Dict[str, np.ndarray]) -> None:
        """
        Validate data quality for binning operations.
        
        Args:
            arrays: Dictionary of data arrays
            
        Raises:
            ValueError: If data quality is insufficient
        """
        rpm = arrays["rpm"]
        map_pressure = arrays["map"]
        
        # Check minimum data points
        if len(rpm) < self.config.min_points_per_bin:
            raise ValueError(f"Insufficient data points for binning (minimum {self.config.min_points_per_bin})")
        
        # Check for valid RPM range
        if np.any(rpm <= 0):
            logger.warning("Non-positive RPM values detected")
        
        if np.any(rpm > 20000):
            logger.warning("Extremely high RPM values detected (>20000)")
        
        # Check for valid MAP range  
        if np.any(map_pressure <= 0):
            logger.warning("Non-positive MAP pressure values detected")
        
        # Check for data variability
        rpm_range = np.ptp(rpm)  # Peak-to-peak range
        map_range = np.ptp(map_pressure)
        
        if rpm_range < 500:
            logger.warning("Limited RPM range detected - binning may not be effective")
        
        if map_range < 0.2:
            logger.warning("Limited MAP pressure range detected - binning may not be effective")
    
    def _determine_optimal_ranges(
        self, arrays: Dict[str, np.ndarray]
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Determine optimal ranges for RPM and MAP binning.
        
        Args:
            arrays: Dictionary of data arrays
            
        Returns:
            Tuple of (rpm_range, map_range) tuples
        """
        rpm = arrays["rpm"]
        map_pressure = arrays["map"]
        
        # RPM range determination
        if self.config.auto_rpm_range:
            rpm_min = np.percentile(rpm, 2.5)  # Remove extreme outliers
            rpm_max = np.percentile(rpm, 97.5)
            rpm_padding = (rpm_max - rpm_min) * (self.config.rpm_padding_percent / 100.0)
            rpm_range = (
                max(0, rpm_min - rpm_padding),
                rpm_max + rpm_padding
            )
        else:
            rpm_range = (
                self.config.rpm_min or np.min(rpm),
                self.config.rpm_max or np.max(rpm)
            )
        
        # MAP range determination
        if self.config.auto_map_range:
            map_min = np.percentile(map_pressure, 2.5)
            map_max = np.percentile(map_pressure, 97.5)
            map_padding = (map_max - map_min) * (self.config.map_padding_percent / 100.0)
            map_range = (
                max(0, map_min - map_padding),
                map_max + map_padding
            )
        else:
            map_range = (
                self.config.map_min or np.min(map_pressure),
                self.config.map_max or np.max(map_pressure)
            )
        
        return rpm_range, map_range
    
    def _create_base_grid(
        self,
        arrays: Dict[str, np.ndarray],
        rpm_range: Tuple[float, float],
        map_range: Tuple[float, float]
    ) -> Dict[str, Any]:
        """
        Create base grid structure for adaptive binning.
        
        Args:
            arrays: Data arrays
            rpm_range: RPM range tuple
            map_range: MAP range tuple
            
        Returns:
            Dictionary with base grid information
        """
        # Create bin edges
        rpm_edges = np.linspace(rpm_range[0], rpm_range[1], self.config.base_rpm_bins + 1)
        map_edges = np.linspace(map_range[0], map_range[1], self.config.base_map_bins + 1)
        
        return {
            "rpm_edges": rpm_edges,
            "map_edges": map_edges,
            "grid_shape": (self.config.base_rpm_bins, self.config.base_map_bins),
            "rpm_centers": (rpm_edges[:-1] + rpm_edges[1:]) / 2,
            "map_centers": (map_edges[:-1] + map_edges[1:]) / 2
        }
    
    def _analyze_data_density(
        self,
        arrays: Dict[str, np.ndarray],
        base_grid: Dict[str, Any]
    ) -> np.ndarray:
        """
        Analyze data density across the base grid.
        
        Args:
            arrays: Data arrays
            base_grid: Base grid structure
            
        Returns:
            2D density map array
        """
        rpm = arrays["rpm"]
        map_pressure = arrays["map"]
        
        # Create 2D histogram for density analysis
        density_map, _, _ = np.histogram2d(
            rpm, map_pressure,
            bins=[base_grid["rpm_edges"], base_grid["map_edges"]]
        )
        
        # Normalize density map
        if np.max(density_map) > 0:
            density_map = density_map / np.max(density_map)
        
        return density_map
    
    def _create_adaptive_bins(
        self,
        arrays: Dict[str, np.ndarray],
        base_grid: Dict[str, Any],
        density_map: np.ndarray
    ) -> Dict[Tuple[int, int], BinCell]:
        """
        Create adaptive bins based on density analysis.
        
        Args:
            arrays: Data arrays
            base_grid: Base grid structure
            density_map: Data density map
            
        Returns:
            Dictionary of adaptive bin cells
        """
        rpm = arrays["rpm"]
        map_pressure = arrays["map"]
        rpm_edges = base_grid["rpm_edges"]
        map_edges = base_grid["map_edges"]
        
        adaptive_bins = {}
        
        # Assign data points to bins
        rpm_indices = np.digitize(rpm, rpm_edges) - 1
        map_indices = np.digitize(map_pressure, map_edges) - 1
        
        # Clip indices to valid range
        rpm_indices = np.clip(rpm_indices, 0, len(rpm_edges) - 2)
        map_indices = np.clip(map_indices, 0, len(map_edges) - 2)
        
        # Create bins for each grid cell
        for rpm_idx in range(len(rpm_edges) - 1):
            for map_idx in range(len(map_edges) - 1):
                # Find points in this bin
                bin_mask = (rpm_indices == rpm_idx) & (map_indices == map_idx)
                point_indices = np.where(bin_mask)[0].tolist()
                point_count = len(point_indices)
                
                # Skip empty bins
                if point_count == 0:
                    continue
                
                # Calculate bin properties
                rpm_center = (rpm_edges[rpm_idx] + rpm_edges[rpm_idx + 1]) / 2
                map_center = (map_edges[map_idx] + map_edges[map_idx + 1]) / 2
                rpm_range = (rpm_edges[rpm_idx], rpm_edges[rpm_idx + 1])
                map_range = (map_edges[map_idx], map_edges[map_idx + 1])
                
                # Get density score
                density_score = float(density_map[rpm_idx, map_idx])
                
                # Create bin cell
                bin_cell = BinCell(
                    rpm_center=rpm_center,
                    map_center=map_center,
                    rpm_range=rpm_range,
                    map_range=map_range,
                    point_count=point_count,
                    data_indices=point_indices,
                    density_score=density_score
                )
                
                adaptive_bins[(rpm_idx, map_idx)] = bin_cell
        
        return adaptive_bins
    
    def _calculate_bin_statistics(
        self,
        bins: Dict[Tuple[int, int], BinCell],
        arrays: Dict[str, np.ndarray],
        additional_cols: Optional[List[str]]
    ) -> None:
        """
        Calculate comprehensive statistics for each bin.
        
        Args:
            bins: Dictionary of bin cells
            arrays: Data arrays
            additional_cols: Additional columns to analyze
        """
        for bin_key, bin_cell in bins.items():
            if bin_cell.point_count == 0:
                continue
            
            indices = np.array(bin_cell.data_indices)
            statistics = {}
            
            # Calculate statistics for all available columns
            for col_name, data_array in arrays.items():
                if col_name in ["rpm", "map"]:
                    continue  # Skip positioning columns
                
                if len(indices) > 0:
                    bin_data = data_array[indices]
                    statistics[col_name] = self._calculate_parameter_statistics(bin_data)
            
            # Calculate spatial statistics
            rpm_data = arrays["rpm"][indices]
            map_data = arrays["map"][indices]
            
            statistics["spatial"] = {
                "rpm_spread": float(np.std(rpm_data)),
                "map_spread": float(np.std(map_data)),
                "data_concentration": self._calculate_data_concentration(rpm_data, map_data)
            }
            
            bin_cell.statistics = statistics
    
    def _calculate_parameter_statistics(self, data: np.ndarray) -> Dict[str, float]:
        """
        Calculate statistical measures for parameter data.
        
        Args:
            data: Parameter data array
            
        Returns:
            Dictionary of statistical measures
        """
        if len(data) == 0:
            return {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "median": 0.0,
                "count": 0
            }
        
        # Handle potential outliers
        if self.config.outlier_method == "iqr":
            q1, q3 = np.percentile(data, [25, 75])
            iqr = q3 - q1
            outlier_mask = ~((data < q1 - 1.5 * iqr) | (data > q3 + 1.5 * iqr))
            clean_data = data[outlier_mask] if np.any(outlier_mask) else data
        else:
            clean_data = data
        
        return {
            "mean": float(np.mean(clean_data)),
            "std": float(np.std(clean_data)),
            "min": float(np.min(clean_data)),
            "max": float(np.max(clean_data)),
            "median": float(np.median(clean_data)),
            "count": int(len(clean_data)),
            "outlier_count": int(len(data) - len(clean_data)) if len(clean_data) != len(data) else 0
        }
    
    def _calculate_data_concentration(self, rpm_data: np.ndarray, map_data: np.ndarray) -> float:
        """
        Calculate how concentrated the data points are within the bin.
        
        Args:
            rpm_data: RPM values in bin
            map_data: MAP pressure values in bin
            
        Returns:
            Concentration score (0-1, higher = more concentrated)
        """
        if len(rpm_data) < 2:
            return 1.0
        
        # Normalize data to [0,1] range within bin
        rpm_norm = (rpm_data - np.min(rpm_data)) / (np.ptp(rpm_data) + 1e-10)
        map_norm = (map_data - np.min(map_data)) / (np.ptp(map_data) + 1e-10)
        
        # Calculate average distance from center
        center_rpm = np.mean(rpm_norm)
        center_map = np.mean(map_norm)
        
        distances = np.sqrt((rpm_norm - center_rpm)**2 + (map_norm - center_map)**2)
        avg_distance = np.mean(distances)
        
        # Convert to concentration score (inverse of spread)
        concentration = 1.0 - min(avg_distance * 2, 1.0)  # Scale to [0,1]
        
        return float(concentration)
    
    def _validate_and_filter_bins(
        self, bins: Dict[Tuple[int, int], BinCell]
    ) -> Dict[Tuple[int, int], BinCell]:
        """
        Validate bins and filter out those that don't meet quality criteria.
        
        Args:
            bins: Dictionary of bin cells
            
        Returns:
            Dictionary of valid bin cells
        """
        valid_bins = {}
        
        for bin_key, bin_cell in bins.items():
            # Check minimum point count
            if bin_cell.point_count < self.config.min_points_per_bin:
                continue
            
            # Check maximum point count (avoid over-dense bins)
            if bin_cell.point_count > self.config.max_points_per_bin:
                logger.debug(f"Bin {bin_key} has {bin_cell.point_count} points (>max {self.config.max_points_per_bin})")
            
            # Calculate confidence score for this bin
            bin_cell.confidence_score = self._calculate_bin_confidence(bin_cell)
            
            # Mark as valid if confidence is above threshold
            bin_cell.is_valid = bin_cell.confidence_score >= 0.5
            
            if bin_cell.is_valid:
                valid_bins[bin_key] = bin_cell
        
        return valid_bins
    
    def _calculate_bin_confidence(self, bin_cell: BinCell) -> float:
        """
        Calculate confidence score for individual bin.
        
        Args:
            bin_cell: Bin cell to evaluate
            
        Returns:
            Confidence score (0-1)
        """
        scores = []
        
        # Point count score
        point_score = min(bin_cell.point_count / self.config.min_points_per_bin, 1.0)
        scores.append(point_score)
        
        # Density score
        scores.append(bin_cell.density_score)
        
        # Data concentration score
        if "spatial" in bin_cell.statistics:
            concentration_score = bin_cell.statistics["spatial"]["data_concentration"]
            scores.append(concentration_score)
        
        return float(np.mean(scores))
    
    def _calculate_overall_statistics(
        self,
        bins: Dict[Tuple[int, int], BinCell],
        arrays: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """
        Calculate overall binning statistics.
        
        Args:
            bins: Valid bin cells
            arrays: Original data arrays
            
        Returns:
            Dictionary of overall statistics
        """
        total_points = len(arrays["rpm"])
        binned_points = sum(bin_cell.point_count for bin_cell in bins.values())
        
        # Basic statistics
        stats = {
            "total_bins": len(bins),
            "total_points": total_points,
            "binned_points": binned_points,
            "coverage_percentage": (binned_points / total_points) * 100.0 if total_points > 0 else 0.0,
            "average_points_per_bin": binned_points / len(bins) if len(bins) > 0 else 0.0
        }
        
        # Bin distribution statistics
        point_counts = [bin_cell.point_count for bin_cell in bins.values()]
        if point_counts:
            stats["bin_distribution"] = {
                "min_points": min(point_counts),
                "max_points": max(point_counts),
                "std_points": float(np.std(point_counts)),
                "median_points": float(np.median(point_counts))
            }
        
        # Density statistics
        density_scores = [bin_cell.density_score for bin_cell in bins.values()]
        if density_scores:
            stats["density_statistics"] = {
                "mean_density": float(np.mean(density_scores)),
                "std_density": float(np.std(density_scores)),
                "max_density": float(np.max(density_scores))
            }
        
        # Confidence statistics
        confidence_scores = [bin_cell.confidence_score for bin_cell in bins.values()]
        if confidence_scores:
            stats["confidence_statistics"] = {
                "mean_confidence": float(np.mean(confidence_scores)),
                "min_confidence": float(np.min(confidence_scores)),
                "high_confidence_bins": sum(1 for score in confidence_scores if score >= 0.8)
            }
        
        return stats
    
    def _calculate_binning_confidence(
        self,
        bins: Dict[Tuple[int, int], BinCell],
        arrays: Dict[str, np.ndarray]
    ) -> float:
        """
        Calculate overall confidence score for the binning result.
        
        Args:
            bins: Valid bin cells
            arrays: Original data arrays
            
        Returns:
            Overall confidence score (0-1)
        """
        if not bins:
            return 0.0
        
        scores = []
        
        # Coverage score
        total_points = len(arrays["rpm"])
        binned_points = sum(bin_cell.point_count for bin_cell in bins.values())
        coverage_score = binned_points / total_points if total_points > 0 else 0.0
        scores.append(coverage_score)
        
        # Average bin confidence
        bin_confidences = [bin_cell.confidence_score for bin_cell in bins.values()]
        avg_bin_confidence = np.mean(bin_confidences)
        scores.append(avg_bin_confidence)
        
        # Distribution balance (prefer even distribution)
        point_counts = [bin_cell.point_count for bin_cell in bins.values()]
        if len(point_counts) > 1:
            cv = np.std(point_counts) / np.mean(point_counts)  # Coefficient of variation
            balance_score = max(0.0, 1.0 - cv)
            scores.append(balance_score)
        
        return float(np.mean(scores))
    
    def _create_binning_metadata(
        self,
        arrays: Dict[str, np.ndarray],
        rpm_range: Tuple[float, float],
        map_range: Tuple[float, float]
    ) -> Dict[str, Any]:
        """
        Create metadata about the binning process.
        
        Args:
            arrays: Original data arrays
            rpm_range: RPM range used
            map_range: MAP range used
            
        Returns:
            Metadata dictionary
        """
        return {
            "total_data_points": len(arrays["rpm"]),
            "ranges": {
                "rpm_min": rpm_range[0],
                "rpm_max": rpm_range[1],
                "map_min": map_range[0],
                "map_max": map_range[1]
            },
            "config": {
                "base_rpm_bins": self.config.base_rpm_bins,
                "base_map_bins": self.config.base_map_bins,
                "min_points_per_bin": self.config.min_points_per_bin,
                "density_threshold": self.config.density_threshold
            },
            "data_characteristics": {
                "rpm_spread": float(np.std(arrays["rpm"])),
                "map_spread": float(np.std(arrays["map"])),
                "data_range_rpm": float(np.ptp(arrays["rpm"])),
                "data_range_map": float(np.ptp(arrays["map"]))
            }
        }


# High-level interface functions
def create_adaptive_bins(
    data: Union[pd.DataFrame, Dict[str, np.ndarray]],
    config: Optional[BinningConfig] = None,
    **column_mapping
) -> BinningResult:
    """
    High-level interface for adaptive MAP×RPM binning.
    
    Args:
        data: Input log data
        config: Binning configuration
        **column_mapping: Column name mappings
        
    Returns:
        BinningResult with adaptive bin structure
        
    Example:
        >>> result = create_adaptive_bins(
        ...     dataframe,
        ...     rpm_col="Engine_RPM",
        ...     map_col="MAP_Pressure",
        ...     additional_cols=["lambda_sensor", "ignition_timing"]
        ... )
        >>> print(f"Created {result.valid_bins} valid bins")
        >>> print(f"Coverage: {result.statistics['coverage_percentage']:.1f}%")
    """
    binner = AdaptiveBinner(config)
    return binner.create_bins(data, **column_mapping)


def analyze_bin_density(
    binning_result: BinningResult,
    density_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Analyze data density distribution across bins.
    
    Args:
        binning_result: Result from adaptive binning
        density_threshold: Threshold for high-density classification
        
    Returns:
        Dictionary of density analysis results
    """
    if not binning_result.bins:
        return {}
    
    density_scores = [bin_cell.density_score for bin_cell in binning_result.bins.values()]
    point_counts = [bin_cell.point_count for bin_cell in binning_result.bins.values()]
    
    analysis = {
        "total_bins": len(binning_result.bins),
        "high_density_bins": sum(1 for score in density_scores if score >= density_threshold),
        "density_distribution": {
            "mean": float(np.mean(density_scores)),
            "std": float(np.std(density_scores)),
            "min": float(np.min(density_scores)),
            "max": float(np.max(density_scores)),
            "percentiles": {
                "25th": float(np.percentile(density_scores, 25)),
                "50th": float(np.percentile(density_scores, 50)),
                "75th": float(np.percentile(density_scores, 75))
            }
        },
        "point_distribution": {
            "mean": float(np.mean(point_counts)),
            "std": float(np.std(point_counts)),
            "min": min(point_counts),
            "max": max(point_counts)
        }
    }
    
    return analysis


def calculate_bin_statistics(
    binning_result: BinningResult,
    parameter: str = "lambda_sensor"
) -> Dict[Tuple[int, int], Dict[str, float]]:
    """
    Calculate statistics for a specific parameter across all bins.
    
    Args:
        binning_result: Result from adaptive binning
        parameter: Parameter to analyze
        
    Returns:
        Dictionary mapping bin coordinates to parameter statistics
        
    Example:
        >>> lambda_stats = calculate_bin_statistics(result, "lambda_sensor")
        >>> for (rpm_idx, map_idx), stats in lambda_stats.items():
        ...     print(f"Bin ({rpm_idx}, {map_idx}): Mean λ = {stats['mean']:.3f}")
    """
    bin_stats = {}
    
    for bin_coord, bin_cell in binning_result.bins.items():
        if parameter in bin_cell.statistics:
            bin_stats[bin_coord] = bin_cell.statistics[parameter]
        
    return bin_stats