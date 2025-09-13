"""
Fuel Efficiency Analysis Module for FuelTune.

Provides comprehensive fuel efficiency analysis including BSFC calculation,
consumption patterns, efficiency maps, and optimal operating point analysis
for automotive telemetry data.

Author: A04-ANALYSIS-SCIPY Agent
Created: 2025-01-02
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import interpolate
from scipy.ndimage import gaussian_filter

from ..data.cache import cached_analysis as cache_result
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class BSFCAnalysisResults:
    """Results from Brake Specific Fuel Consumption analysis."""

    bsfc_values: np.ndarray
    power_values: np.ndarray
    fuel_flow_values: np.ndarray
    min_bsfc: float
    min_bsfc_power: float
    optimal_range: Tuple[float, float]  # Power range for optimal BSFC
    efficiency_percentage: float
    bsfc_map: Optional[np.ndarray] = None
    rpm_grid: Optional[np.ndarray] = None
    load_grid: Optional[np.ndarray] = None


@dataclass
class FuelConsumptionPattern:
    """Results from fuel consumption pattern analysis."""

    consumption_by_rpm: Dict[str, float]  # RPM range -> avg consumption
    consumption_by_load: Dict[str, float]  # Load range -> avg consumption
    consumption_by_speed: Dict[str, float]  # Speed range -> avg consumption
    idle_consumption: float
    cruise_consumption: float
    acceleration_consumption: float
    deceleration_consumption: float
    driving_modes: Dict[str, Dict[str, float]]  # mode -> stats


@dataclass
class EfficiencyMap:
    """Results from efficiency map analysis."""

    rpm_bins: np.ndarray
    load_bins: np.ndarray
    efficiency_grid: np.ndarray
    fuel_consumption_grid: np.ndarray
    power_grid: np.ndarray
    optimal_points: List[Tuple[float, float, float]]  # rpm, load, efficiency
    efficiency_contours: Dict[str, np.ndarray]


@dataclass
class OptimalOperatingPoints:
    """Results from optimal operating point analysis."""

    best_efficiency_point: Tuple[float, float, float]  # rpm, load, efficiency
    best_power_point: Tuple[float, float, float]  # rpm, load, power
    best_economy_point: Tuple[float, float, float]  # rpm, load, fuel_economy
    operating_envelope: Dict[str, Tuple[float, float]]  # parameter -> (min, max)
    recommended_shift_points: List[float]  # RPM values
    efficiency_zones: Dict[str, Dict[str, Any]]  # zone_name -> zone_data


@dataclass
class EconomyMetrics:
    """Results from fuel economy metrics analysis."""

    mpg_overall: float
    mpg_city: float
    mpg_highway: float
    liters_per_100km: float
    fuel_cost_per_mile: float
    co2_emissions_per_mile: float
    efficiency_rating: str  # A-F rating
    comparison_to_baseline: float  # percentage improvement/degradation


class FuelEfficiencyAnalyzer:
    """Advanced fuel efficiency analysis for FuelTune telemetry data."""

    def __init__(self, fuel_density: float = 0.75, fuel_carbon_content: float = 0.87):
        """
        Initialize fuel efficiency analyzer.

        Args:
            fuel_density: Fuel density in kg/L (default: gasoline)
            fuel_carbon_content: Carbon content ratio (default: gasoline)
        """
        self.fuel_density = fuel_density
        self.fuel_carbon_content = fuel_carbon_content
        self.logger = logger

    def calculate_basic_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate basic fuel efficiency metrics.

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with basic fuel metrics
        """
        metrics = {}

        # Check for fuel-related columns
        fuel_cols = [col for col in data.columns if "fuel" in col.lower()]

        for col in fuel_cols:
            if data[col].dtype in [np.float64, np.int64]:
                metrics[col] = {
                    "mean": float(data[col].mean()),
                    "std": float(data[col].std()),
                    "min": float(data[col].min()),
                    "max": float(data[col].max()),
                    "total": float(data[col].sum()),
                }

        # Calculate fuel consumption if possible
        if "fuel_rate" in data.columns:
            metrics["average_consumption"] = float(data["fuel_rate"].mean())
            metrics["total_consumption"] = float(data["fuel_rate"].sum())

        return metrics

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Main analysis method for fuel efficiency.

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with fuel efficiency analysis results
        """
        try:
            results = {"basic_metrics": self.calculate_basic_metrics(data)}

            # Try BSFC analysis if columns exist
            if "engine_power" in data.columns and "fuel_flow_rate" in data.columns:
                try:
                    bsfc = self.analyze_bsfc(data)
                    results["bsfc"] = {
                        "mean_bsfc": bsfc.mean_bsfc,
                        "optimal_bsfc": bsfc.optimal_bsfc,
                    }
                except Exception as e:
                    self.logger.warning(f"BSFC analysis failed: {e}")

            return results
        except Exception as e:
            self.logger.error(f"Fuel efficiency analysis failed: {e}")
            return {"error": str(e)}

    @cache_result("analysis", ttl=3600)
    def analyze_bsfc(
        self,
        data: pd.DataFrame,
        power_col: str = "engine_power",
        fuel_flow_col: str = "fuel_flow_rate",
        rpm_col: str = "engine_rpm",
        load_col: str = "engine_load",
    ) -> BSFCAnalysisResults:
        """
        Analyze Brake Specific Fuel Consumption (BSFC).

        Args:
            data: DataFrame with engine data
            power_col: Column name for engine power
            fuel_flow_col: Column name for fuel flow rate
            rpm_col: Column name for engine RPM
            load_col: Column name for engine load

        Returns:
            BSFCAnalysisResults object
        """
        try:
            # Check required columns
            required_cols = [power_col, fuel_flow_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Clean data - remove zeros and negatives
            clean_data = data[
                (data[power_col] > 0)
                & (data[fuel_flow_col] > 0)
                & data[power_col].notna()
                & data[fuel_flow_col].notna()
            ].copy()

            if len(clean_data) < 10:
                raise ValueError("Insufficient data for BSFC analysis")

            # Calculate BSFC (g/kWh)
            # BSFC = fuel_flow_rate (kg/h) * 1000 / power (kW)
            power_values = clean_data[power_col].values
            fuel_flow_values = clean_data[fuel_flow_col].values

            bsfc_values = (fuel_flow_values * 1000) / power_values

            # Remove outliers (beyond 3 sigma)
            bsfc_mean = np.mean(bsfc_values)
            bsfc_std = np.std(bsfc_values)
            mask = np.abs(bsfc_values - bsfc_mean) < 3 * bsfc_std

            bsfc_values = bsfc_values[mask]
            power_values = power_values[mask]
            fuel_flow_values = fuel_flow_values[mask]

            # Find minimum BSFC and corresponding power
            min_bsfc_idx = np.argmin(bsfc_values)
            min_bsfc = bsfc_values[min_bsfc_idx]
            min_bsfc_power = power_values[min_bsfc_idx]

            # Define optimal range (within 10% of minimum BSFC)
            optimal_threshold = min_bsfc * 1.1
            optimal_mask = bsfc_values <= optimal_threshold
            if np.any(optimal_mask):
                optimal_powers = power_values[optimal_mask]
                optimal_range = (np.min(optimal_powers), np.max(optimal_powers))
            else:
                optimal_range = (min_bsfc_power, min_bsfc_power)

            # Calculate efficiency percentage (lower BSFC = higher efficiency)
            # Reference: typical gasoline engine BSFC ~250 g/kWh
            reference_bsfc = 250.0
            efficiency_percentage = (reference_bsfc / min_bsfc) * 100

            # Create BSFC map if RPM and load data available
            bsfc_map = None
            rpm_grid = None
            load_grid = None

            if rpm_col in data.columns and load_col in data.columns:
                try:
                    rpm_data = clean_data[rpm_col].values[mask]
                    load_data = clean_data[load_col].values[mask]

                    # Create grid for interpolation
                    rpm_min, rpm_max = np.percentile(rpm_data, [5, 95])
                    load_min, load_max = np.percentile(load_data, [5, 95])

                    rpm_grid = np.linspace(rpm_min, rpm_max, 20)
                    load_grid = np.linspace(load_min, load_max, 20)

                    # Interpolate BSFC values onto grid
                    points = np.column_stack([rpm_data, load_data])
                    grid_rpm, grid_load = np.meshgrid(rpm_grid, load_grid)

                    bsfc_map = interpolate.griddata(
                        points, bsfc_values, (grid_rpm, grid_load), method="linear"
                    )

                    # Smooth the map
                    bsfc_map = gaussian_filter(bsfc_map, sigma=1.0)

                except Exception as e:
                    self.logger.warning(f"Failed to create BSFC map: {e}")

            return BSFCAnalysisResults(
                bsfc_values=bsfc_values,
                power_values=power_values,
                fuel_flow_values=fuel_flow_values,
                min_bsfc=min_bsfc,
                min_bsfc_power=min_bsfc_power,
                optimal_range=optimal_range,
                efficiency_percentage=efficiency_percentage,
                bsfc_map=bsfc_map,
                rpm_grid=rpm_grid,
                load_grid=load_grid,
            )

        except Exception as e:
            self.logger.error(f"Error in BSFC analysis: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def analyze_consumption_patterns(
        self,
        data: pd.DataFrame,
        fuel_flow_col: str = "fuel_flow_rate",
        rpm_col: str = "engine_rpm",
        load_col: str = "engine_load",
        speed_col: str = "vehicle_speed",
        accel_col: Optional[str] = None,
    ) -> FuelConsumptionPattern:
        """
        Analyze fuel consumption patterns across different operating conditions.

        Args:
            data: DataFrame with vehicle data
            fuel_flow_col: Column name for fuel flow rate
            rpm_col: Column name for engine RPM
            load_col: Column name for engine load
            speed_col: Column name for vehicle speed
            accel_col: Optional column name for acceleration

        Returns:
            FuelConsumptionPattern object
        """
        try:
            # Check required columns
            required_cols = [fuel_flow_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            clean_data = data[data[fuel_flow_col] > 0].copy()

            if len(clean_data) < 10:
                raise ValueError("Insufficient data for consumption pattern analysis")

            # Consumption by RPM ranges
            consumption_by_rpm = {}
            if rpm_col in clean_data.columns:
                rpm_ranges = [
                    (0, 1000, "idle"),
                    (1000, 2000, "low_rpm"),
                    (2000, 3000, "mid_rpm"),
                    (3000, 4000, "high_rpm"),
                    (4000, np.inf, "very_high_rpm"),
                ]

                for rpm_min, rpm_max, label in rpm_ranges:
                    mask = (clean_data[rpm_col] >= rpm_min) & (clean_data[rpm_col] < rpm_max)
                    if np.any(mask):
                        avg_consumption = clean_data.loc[mask, fuel_flow_col].mean()
                        consumption_by_rpm[label] = avg_consumption

            # Consumption by load ranges
            consumption_by_load = {}
            if load_col in clean_data.columns:
                load_ranges = [
                    (0, 20, "light_load"),
                    (20, 40, "moderate_load"),
                    (40, 60, "medium_load"),
                    (60, 80, "heavy_load"),
                    (80, 100, "full_load"),
                ]

                for load_min, load_max, label in load_ranges:
                    mask = (clean_data[load_col] >= load_min) & (clean_data[load_col] < load_max)
                    if np.any(mask):
                        avg_consumption = clean_data.loc[mask, fuel_flow_col].mean()
                        consumption_by_load[label] = avg_consumption

            # Consumption by speed ranges
            consumption_by_speed = {}
            if speed_col in clean_data.columns:
                speed_ranges = [
                    (0, 10, "stationary"),
                    (10, 30, "city_speed"),
                    (30, 60, "suburban"),
                    (60, 90, "highway"),
                    (90, np.inf, "high_speed"),
                ]

                for speed_min, speed_max, label in speed_ranges:
                    mask = (clean_data[speed_col] >= speed_min) & (
                        clean_data[speed_col] < speed_max
                    )
                    if np.any(mask):
                        avg_consumption = clean_data.loc[mask, fuel_flow_col].mean()
                        consumption_by_speed[label] = avg_consumption

            # Identify driving modes
            idle_consumption = 0.0
            cruise_consumption = 0.0
            acceleration_consumption = 0.0
            deceleration_consumption = 0.0

            if speed_col in clean_data.columns:
                # Idle: speed < 5 km/h
                idle_mask = clean_data[speed_col] < 5
                if np.any(idle_mask):
                    idle_consumption = clean_data.loc[idle_mask, fuel_flow_col].mean()

                # Cruise: steady speed (calculate acceleration if not provided)
                if accel_col is None and len(clean_data) > 1:
                    # Calculate acceleration from speed
                    speed_diff = clean_data[speed_col].diff()
                    time_diff = 1.0  # Assume 1 second intervals
                    acceleration = speed_diff / time_diff
                else:
                    acceleration = (
                        clean_data[accel_col] if accel_col else pd.Series(0, index=clean_data.index)
                    )

                # Cruise: low acceleration, moderate speed
                cruise_mask = (
                    (abs(acceleration) < 0.5)
                    & (clean_data[speed_col] > 30)
                    & (clean_data[speed_col] < 80)
                )
                if np.any(cruise_mask):
                    cruise_consumption = clean_data.loc[cruise_mask, fuel_flow_col].mean()

                # Acceleration: positive acceleration
                accel_mask = acceleration > 1.0
                if np.any(accel_mask):
                    acceleration_consumption = clean_data.loc[accel_mask, fuel_flow_col].mean()

                # Deceleration: negative acceleration
                decel_mask = acceleration < -1.0
                if np.any(decel_mask):
                    deceleration_consumption = clean_data.loc[decel_mask, fuel_flow_col].mean()

            # Analyze driving modes
            driving_modes = {
                "idle": {
                    "avg_consumption": idle_consumption,
                    "percentage_time": (
                        (len(clean_data[clean_data[speed_col] < 5]) / len(clean_data) * 100)
                        if speed_col in clean_data.columns
                        else 0
                    ),
                },
                "cruise": {
                    "avg_consumption": cruise_consumption,
                    "percentage_time": (
                        (np.sum(cruise_mask) / len(clean_data) * 100)
                        if "cruise_mask" in locals()
                        else 0
                    ),
                },
                "acceleration": {
                    "avg_consumption": acceleration_consumption,
                    "percentage_time": (
                        (np.sum(accel_mask) / len(clean_data) * 100)
                        if "accel_mask" in locals()
                        else 0
                    ),
                },
                "deceleration": {
                    "avg_consumption": deceleration_consumption,
                    "percentage_time": (
                        (np.sum(decel_mask) / len(clean_data) * 100)
                        if "decel_mask" in locals()
                        else 0
                    ),
                },
            }

            return FuelConsumptionPattern(
                consumption_by_rpm=consumption_by_rpm,
                consumption_by_load=consumption_by_load,
                consumption_by_speed=consumption_by_speed,
                idle_consumption=idle_consumption,
                cruise_consumption=cruise_consumption,
                acceleration_consumption=acceleration_consumption,
                deceleration_consumption=deceleration_consumption,
                driving_modes=driving_modes,
            )

        except Exception as e:
            self.logger.error(f"Error in consumption pattern analysis: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def create_efficiency_map(
        self,
        data: pd.DataFrame,
        rpm_col: str = "engine_rpm",
        load_col: str = "engine_load",
        fuel_flow_col: str = "fuel_flow_rate",
        power_col: Optional[str] = None,
        grid_size: int = 25,
    ) -> EfficiencyMap:
        """
        Create comprehensive efficiency map.

        Args:
            data: DataFrame with engine data
            rpm_col: Column name for engine RPM
            load_col: Column name for engine load
            fuel_flow_col: Column name for fuel flow rate
            power_col: Optional column name for power
            grid_size: Size of the interpolation grid

        Returns:
            EfficiencyMap object
        """
        try:
            required_cols = [rpm_col, load_col, fuel_flow_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Clean data
            clean_data = data[
                (data[rpm_col] > 0)
                & (data[load_col] >= 0)
                & (data[fuel_flow_col] > 0)
                & data[rpm_col].notna()
                & data[load_col].notna()
                & data[fuel_flow_col].notna()
            ].copy()

            if len(clean_data) < 20:
                raise ValueError("Insufficient data for efficiency map creation")

            # Create grid
            rpm_min, rpm_max = np.percentile(clean_data[rpm_col], [5, 95])
            load_min, load_max = np.percentile(clean_data[load_col], [5, 95])

            rpm_bins = np.linspace(rpm_min, rpm_max, grid_size)
            load_bins = np.linspace(load_min, load_max, grid_size)

            grid_rpm, grid_load = np.meshgrid(rpm_bins, load_bins)

            # Prepare data for interpolation
            points = clean_data[[rpm_col, load_col]].values
            fuel_values = clean_data[fuel_flow_col].values

            # Interpolate fuel consumption
            fuel_consumption_grid = interpolate.griddata(
                points, fuel_values, (grid_rpm, grid_load), method="linear"
            )

            # Calculate or interpolate power
            if power_col and power_col in clean_data.columns:
                power_values = clean_data[power_col].values
                power_grid = interpolate.griddata(
                    points, power_values, (grid_rpm, grid_load), method="linear"
                )
            else:
                # Estimate power from RPM and load
                # Simplified model: Power ∝ RPM × Load
                estimated_power = (grid_rpm * grid_load) / 1000  # Rough estimation
                power_grid = estimated_power

            # Calculate efficiency (power/fuel_consumption)
            efficiency_grid = np.divide(
                power_grid,
                fuel_consumption_grid,
                out=np.zeros_like(power_grid),
                where=fuel_consumption_grid != 0,
            )

            # Smooth grids
            fuel_consumption_grid = gaussian_filter(fuel_consumption_grid, sigma=1.0)
            power_grid = gaussian_filter(power_grid, sigma=1.0)
            efficiency_grid = gaussian_filter(efficiency_grid, sigma=1.0)

            # Find optimal points (top 5% efficiency)
            valid_mask = ~np.isnan(efficiency_grid) & (efficiency_grid > 0)
            if np.any(valid_mask):
                efficiency_threshold = np.percentile(efficiency_grid[valid_mask], 95)
                optimal_mask = efficiency_grid >= efficiency_threshold

                optimal_points = []
                optimal_indices = np.where(optimal_mask)

                for i, j in zip(optimal_indices[0], optimal_indices[1]):
                    rpm = rpm_bins[j] if j < len(rpm_bins) else rpm_bins[-1]
                    load = load_bins[i] if i < len(load_bins) else load_bins[-1]
                    efficiency = efficiency_grid[i, j]
                    optimal_points.append((rpm, load, efficiency))

                # Sort by efficiency (descending)
                optimal_points.sort(key=lambda x: x[2], reverse=True)
                optimal_points = optimal_points[:10]  # Keep top 10
            else:
                optimal_points = []

            # Create efficiency contours
            efficiency_contours = {}
            if np.any(valid_mask):
                efficiency_levels = np.percentile(efficiency_grid[valid_mask], [10, 25, 50, 75, 90])
                for i, level in enumerate(efficiency_levels):
                    level_name = f"efficiency_{10 + i * 20}th_percentile"
                    contour_mask = efficiency_grid >= level
                    efficiency_contours[level_name] = contour_mask

            return EfficiencyMap(
                rpm_bins=rpm_bins,
                load_bins=load_bins,
                efficiency_grid=efficiency_grid,
                fuel_consumption_grid=fuel_consumption_grid,
                power_grid=power_grid,
                optimal_points=optimal_points,
                efficiency_contours=efficiency_contours,
            )

        except Exception as e:
            self.logger.error(f"Error creating efficiency map: {e}")
            raise

    def find_optimal_operating_points(
        self,
        data: pd.DataFrame,
        rpm_col: str = "engine_rpm",
        load_col: str = "engine_load",
        fuel_flow_col: str = "fuel_flow_rate",
        power_col: Optional[str] = None,
    ) -> OptimalOperatingPoints:
        """
        Find optimal operating points for different objectives.

        Args:
            data: DataFrame with engine data
            rpm_col: Column name for engine RPM
            load_col: Column name for engine load
            fuel_flow_col: Column name for fuel flow rate
            power_col: Optional column name for power

        Returns:
            OptimalOperatingPoints object
        """
        try:
            required_cols = [rpm_col, load_col, fuel_flow_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Clean data
            clean_data = data[
                (data[rpm_col] > 0) & (data[load_col] >= 0) & (data[fuel_flow_col] > 0)
            ].copy()

            if len(clean_data) < 10:
                raise ValueError("Insufficient data for optimal point analysis")

            # Calculate efficiency metrics
            if power_col and power_col in clean_data.columns:
                power_values = clean_data[power_col].values
            else:
                # Estimate power (simplified)
                power_values = (clean_data[rpm_col] * clean_data[load_col]) / 1000

            fuel_efficiency = power_values / clean_data[fuel_flow_col].values
            fuel_economy = 1 / clean_data[fuel_flow_col].values  # Inverse of consumption

            # Find best points
            best_efficiency_idx = np.argmax(fuel_efficiency)
            best_power_idx = np.argmax(power_values)
            best_economy_idx = np.argmax(fuel_economy)

            best_efficiency_point = (
                clean_data.iloc[best_efficiency_idx][rpm_col],
                clean_data.iloc[best_efficiency_idx][load_col],
                fuel_efficiency[best_efficiency_idx],
            )

            best_power_point = (
                clean_data.iloc[best_power_idx][rpm_col],
                clean_data.iloc[best_power_idx][load_col],
                power_values[best_power_idx],
            )

            best_economy_point = (
                clean_data.iloc[best_economy_idx][rpm_col],
                clean_data.iloc[best_economy_idx][load_col],
                fuel_economy[best_economy_idx],
            )

            # Define operating envelope
            operating_envelope = {
                "rpm": (clean_data[rpm_col].min(), clean_data[rpm_col].max()),
                "load": (clean_data[load_col].min(), clean_data[load_col].max()),
                "fuel_flow": (clean_data[fuel_flow_col].min(), clean_data[fuel_flow_col].max()),
                "power": (power_values.min(), power_values.max()) if power_col else (0, 0),
            }

            # Recommended shift points (where efficiency drops significantly)
            recommended_shift_points = []
            rpm_sorted = clean_data.sort_values(rpm_col)

            # Simple heuristic: recommend shifts at efficiency drops > 10%
            window_size = max(10, len(rpm_sorted) // 20)
            for i in range(window_size, len(rpm_sorted) - window_size):
                prev_efficiency = np.mean(fuel_efficiency[i - window_size : i])
                next_efficiency = np.mean(fuel_efficiency[i : i + window_size])

                if (
                    prev_efficiency > 0
                    and (prev_efficiency - next_efficiency) / prev_efficiency > 0.1
                ):
                    recommended_shift_points.append(rpm_sorted.iloc[i][rpm_col])

            # Keep only unique shift points
            recommended_shift_points = sorted(list(set(recommended_shift_points)))

            # Define efficiency zones
            efficiency_zones = {}

            # High efficiency zone (top 25%)
            high_eff_threshold = np.percentile(fuel_efficiency, 75)
            high_eff_mask = fuel_efficiency >= high_eff_threshold
            if np.any(high_eff_mask):
                efficiency_zones["high_efficiency"] = {
                    "rpm_range": (
                        clean_data.loc[high_eff_mask, rpm_col].min(),
                        clean_data.loc[high_eff_mask, rpm_col].max(),
                    ),
                    "load_range": (
                        clean_data.loc[high_eff_mask, load_col].min(),
                        clean_data.loc[high_eff_mask, load_col].max(),
                    ),
                    "avg_efficiency": np.mean(fuel_efficiency[high_eff_mask]),
                }

            # Medium efficiency zone (25-75%)
            med_eff_mask = (fuel_efficiency >= np.percentile(fuel_efficiency, 25)) & (
                fuel_efficiency < high_eff_threshold
            )
            if np.any(med_eff_mask):
                efficiency_zones["medium_efficiency"] = {
                    "rpm_range": (
                        clean_data.loc[med_eff_mask, rpm_col].min(),
                        clean_data.loc[med_eff_mask, rpm_col].max(),
                    ),
                    "load_range": (
                        clean_data.loc[med_eff_mask, load_col].min(),
                        clean_data.loc[med_eff_mask, load_col].max(),
                    ),
                    "avg_efficiency": np.mean(fuel_efficiency[med_eff_mask]),
                }

            # Low efficiency zone (bottom 25%)
            low_eff_mask = fuel_efficiency < np.percentile(fuel_efficiency, 25)
            if np.any(low_eff_mask):
                efficiency_zones["low_efficiency"] = {
                    "rpm_range": (
                        clean_data.loc[low_eff_mask, rpm_col].min(),
                        clean_data.loc[low_eff_mask, rpm_col].max(),
                    ),
                    "load_range": (
                        clean_data.loc[low_eff_mask, load_col].min(),
                        clean_data.loc[low_eff_mask, load_col].max(),
                    ),
                    "avg_efficiency": np.mean(fuel_efficiency[low_eff_mask]),
                }

            return OptimalOperatingPoints(
                best_efficiency_point=best_efficiency_point,
                best_power_point=best_power_point,
                best_economy_point=best_economy_point,
                operating_envelope=operating_envelope,
                recommended_shift_points=recommended_shift_points,
                efficiency_zones=efficiency_zones,
            )

        except Exception as e:
            self.logger.error(f"Error finding optimal operating points: {e}")
            raise

    def calculate_economy_metrics(
        self,
        data: pd.DataFrame,
        distance_col: str = "distance",
        fuel_consumed_col: str = "fuel_consumed",
        fuel_price_per_liter: float = 1.50,
    ) -> EconomyMetrics:
        """
        Calculate comprehensive fuel economy metrics.

        Args:
            data: DataFrame with trip data
            distance_col: Column name for distance traveled
            fuel_consumed_col: Column name for fuel consumed
            fuel_price_per_liter: Fuel price per liter

        Returns:
            EconomyMetrics object
        """
        try:
            required_cols = [distance_col, fuel_consumed_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                # Try to calculate from other columns if available
                if "fuel_flow_rate" in data.columns and "time" in data.columns:
                    # Calculate fuel consumed from flow rate and time
                    data = data.copy()
                    time_diff = data["time"].diff().fillna(0)  # Assuming time in seconds
                    data[fuel_consumed_col] = (
                        data["fuel_flow_rate"] * time_diff / 3600
                    )  # Convert to liters

            # Clean data
            clean_data = data[(data[distance_col] > 0) & (data[fuel_consumed_col] > 0)].copy()

            if len(clean_data) < 5:
                raise ValueError("Insufficient data for economy metrics calculation")

            total_distance = clean_data[distance_col].sum()  # km
            total_fuel = clean_data[fuel_consumed_col].sum()  # liters

            if total_distance == 0 or total_fuel == 0:
                raise ValueError("Zero distance or fuel consumption")

            # Calculate MPG (Miles Per Gallon)
            mpg_overall = (total_distance * 0.621371) / (
                total_fuel * 0.264172
            )  # km to miles, L to gallons

            # Calculate L/100km
            liters_per_100km = (total_fuel / total_distance) * 100

            # Estimate city vs highway (simplified)
            # Assume speeds < 50 km/h are city, > 50 km/h are highway
            if "vehicle_speed" in clean_data.columns:
                city_mask = clean_data["vehicle_speed"] < 50
                highway_mask = clean_data["vehicle_speed"] >= 50

                if np.any(city_mask):
                    city_distance = clean_data.loc[city_mask, distance_col].sum()
                    city_fuel = clean_data.loc[city_mask, fuel_consumed_col].sum()
                    mpg_city = (
                        (city_distance * 0.621371) / (city_fuel * 0.264172) if city_fuel > 0 else 0
                    )
                else:
                    mpg_city = mpg_overall

                if np.any(highway_mask):
                    highway_distance = clean_data.loc[highway_mask, distance_col].sum()
                    highway_fuel = clean_data.loc[highway_mask, fuel_consumed_col].sum()
                    mpg_highway = (
                        (highway_distance * 0.621371) / (highway_fuel * 0.264172)
                        if highway_fuel > 0
                        else 0
                    )
                else:
                    mpg_highway = mpg_overall
            else:
                mpg_city = mpg_overall
                mpg_highway = mpg_overall

            # Calculate costs
            fuel_cost_per_mile = (fuel_price_per_liter * (total_fuel / total_distance)) / 0.621371

            # Calculate CO2 emissions (simplified)
            # Gasoline: ~2.31 kg CO2 per liter
            co2_per_liter = 2.31  # kg CO2 per liter of gasoline
            co2_emissions_per_mile = (co2_per_liter * (total_fuel / total_distance)) / 0.621371

            # Efficiency rating (A-F based on L/100km)
            if liters_per_100km <= 5:
                efficiency_rating = "A"
            elif liters_per_100km <= 7:
                efficiency_rating = "B"
            elif liters_per_100km <= 9:
                efficiency_rating = "C"
            elif liters_per_100km <= 11:
                efficiency_rating = "D"
            elif liters_per_100km <= 13:
                efficiency_rating = "E"
            else:
                efficiency_rating = "F"

            # Comparison to baseline (typical car: 8.5 L/100km)
            baseline_consumption = 8.5
            comparison_to_baseline = (
                (baseline_consumption - liters_per_100km) / baseline_consumption
            ) * 100

            return EconomyMetrics(
                mpg_overall=mpg_overall,
                mpg_city=mpg_city,
                mpg_highway=mpg_highway,
                liters_per_100km=liters_per_100km,
                fuel_cost_per_mile=fuel_cost_per_mile,
                co2_emissions_per_mile=co2_emissions_per_mile,
                efficiency_rating=efficiency_rating,
                comparison_to_baseline=comparison_to_baseline,
            )

        except Exception as e:
            self.logger.error(f"Error calculating economy metrics: {e}")
            raise

    def create_efficiency_plots(
        self,
        bsfc_results: Optional[BSFCAnalysisResults] = None,
        efficiency_map: Optional[EfficiencyMap] = None,
        consumption_patterns: Optional[FuelConsumptionPattern] = None,
        title: str = "Fuel Efficiency Analysis",
    ) -> Dict[str, go.Figure]:
        """
        Create comprehensive fuel efficiency plots.

        Args:
            bsfc_results: BSFC analysis results
            efficiency_map: Efficiency map results
            consumption_patterns: Consumption pattern results
            title: Base title for plots

        Returns:
            Dictionary of plot names -> plotly figures
        """
        try:
            plots = {}

            # 1. BSFC scatter plot
            if bsfc_results:
                fig_bsfc = go.Figure()

                fig_bsfc.add_trace(
                    go.Scatter(
                        x=bsfc_results.power_values,
                        y=bsfc_results.bsfc_values,
                        mode="markers",
                        name="BSFC Data",
                        marker=dict(
                            color=bsfc_results.fuel_flow_values,
                            colorscale="Viridis",
                            colorbar=dict(title="Fuel Flow (L/h)"),
                            size=6,
                            opacity=0.7,
                        ),
                    )
                )

                # Mark optimal point
                fig_bsfc.add_trace(
                    go.Scatter(
                        x=[bsfc_results.min_bsfc_power],
                        y=[bsfc_results.min_bsfc],
                        mode="markers",
                        name=f"Optimal Point ({bsfc_results.min_bsfc:.1f} g/kWh)",
                        marker=dict(color="red", size=12, symbol="star"),
                    )
                )

                # Mark optimal range
                fig_bsfc.add_vrect(
                    x0=bsfc_results.optimal_range[0],
                    x1=bsfc_results.optimal_range[1],
                    fillcolor="green",
                    opacity=0.2,
                    layer="below",
                    annotation_text="Optimal Range",
                )

                fig_bsfc.update_layout(
                    title=f"{title} - BSFC Analysis",
                    xaxis_title="Power (kW)",
                    yaxis_title="BSFC (g/kWh)",
                )
                plots["bsfc_scatter"] = fig_bsfc

                # 2. BSFC map (if available)
                if bsfc_results.bsfc_map is not None:
                    fig_map = go.Figure(
                        data=go.Contour(
                            x=bsfc_results.rpm_grid,
                            y=bsfc_results.load_grid,
                            z=bsfc_results.bsfc_map,
                            colorscale="RdYlBu_r",
                            contours=dict(showlabels=True, labelfont=dict(size=10)),
                            colorbar=dict(title="BSFC (g/kWh)"),
                        )
                    )

                    fig_map.update_layout(
                        title=f"{title} - BSFC Map",
                        xaxis_title="RPM",
                        yaxis_title="Engine Load (%)",
                    )
                    plots["bsfc_map"] = fig_map

            # 3. Efficiency map contour plot
            if efficiency_map:
                fig_eff_map = go.Figure(
                    data=go.Contour(
                        x=efficiency_map.rpm_bins,
                        y=efficiency_map.load_bins,
                        z=efficiency_map.efficiency_grid,
                        colorscale="Viridis",
                        contours=dict(showlabels=True),
                        colorbar=dict(title="Efficiency"),
                    )
                )

                # Add optimal points
                if efficiency_map.optimal_points:
                    opt_rpm = [point[0] for point in efficiency_map.optimal_points]
                    opt_load = [point[1] for point in efficiency_map.optimal_points]
                    opt_eff = [point[2] for point in efficiency_map.optimal_points]

                    fig_eff_map.add_trace(
                        go.Scatter(
                            x=opt_rpm,
                            y=opt_load,
                            mode="markers",
                            name="Optimal Points",
                            marker=dict(color="red", size=10, symbol="star"),
                            text=[f"Eff: {eff:.2f}" for eff in opt_eff],
                            textposition="top center",
                        )
                    )

                fig_eff_map.update_layout(
                    title=f"{title} - Efficiency Map",
                    xaxis_title="RPM",
                    yaxis_title="Engine Load (%)",
                )
                plots["efficiency_map"] = fig_eff_map

            # 4. Consumption patterns bar chart
            if consumption_patterns:
                # RPM consumption
                if consumption_patterns.consumption_by_rpm:
                    fig_rpm = go.Figure(
                        data=go.Bar(
                            x=list(consumption_patterns.consumption_by_rpm.keys()),
                            y=list(consumption_patterns.consumption_by_rpm.values()),
                            marker_color="lightblue",
                        )
                    )
                    fig_rpm.update_layout(
                        title=f"{title} - Consumption by RPM Range",
                        xaxis_title="RPM Range",
                        yaxis_title="Fuel Flow (L/h)",
                    )
                    plots["consumption_by_rpm"] = fig_rpm

                # Driving modes pie chart
                if consumption_patterns.driving_modes:
                    modes = list(consumption_patterns.driving_modes.keys())
                    percentages = [
                        consumption_patterns.driving_modes[mode]["percentage_time"]
                        for mode in modes
                    ]

                    fig_modes = go.Figure(
                        data=go.Pie(
                            labels=modes,
                            values=percentages,
                            textinfo="label+percent",
                        )
                    )
                    fig_modes.update_layout(title=f"{title} - Time Distribution by Driving Mode")
                    plots["driving_modes"] = fig_modes

            return plots

        except Exception as e:
            self.logger.error(f"Error creating efficiency plots: {e}")
            raise

    def generate_efficiency_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive fuel efficiency analysis summary.

        Args:
            data: DataFrame with vehicle/engine data

        Returns:
            Dictionary with all efficiency analysis results
        """
        try:
            results = {}

            # BSFC Analysis
            try:
                bsfc_results = self.analyze_bsfc(data)
                results["bsfc_analysis"] = bsfc_results
            except Exception as e:
                self.logger.warning(f"BSFC analysis failed: {e}")

            # Consumption Patterns
            try:
                consumption_patterns = self.analyze_consumption_patterns(data)
                results["consumption_patterns"] = consumption_patterns
            except Exception as e:
                self.logger.warning(f"Consumption pattern analysis failed: {e}")

            # Efficiency Map
            try:
                efficiency_map = self.create_efficiency_map(data)
                results["efficiency_map"] = efficiency_map
            except Exception as e:
                self.logger.warning(f"Efficiency map creation failed: {e}")

            # Optimal Operating Points
            try:
                optimal_points = self.find_optimal_operating_points(data)
                results["optimal_points"] = optimal_points
            except Exception as e:
                self.logger.warning(f"Optimal points analysis failed: {e}")

            # Economy Metrics
            try:
                economy_metrics = self.calculate_economy_metrics(data)
                results["economy_metrics"] = economy_metrics
            except Exception as e:
                self.logger.warning(f"Economy metrics calculation failed: {e}")

            # Create plots
            plots = self.create_efficiency_plots(
                bsfc_results=results.get("bsfc_analysis"),
                efficiency_map=results.get("efficiency_map"),
                consumption_patterns=results.get("consumption_patterns"),
            )
            results["plots"] = plots

            return results

        except Exception as e:
            self.logger.error(f"Error generating efficiency summary: {e}")
            raise
