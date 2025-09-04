"""
Engine Performance Analysis Module for FuelTune.

Provides comprehensive engine performance analysis including power/torque
estimation, acceleration analysis, boost efficiency, knock detection,
and thermal analysis for automotive telemetry data.

Author: A04-ANALYSIS-SCIPY Agent
Created: 2025-01-02
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import interpolate, optimize, signal
from scipy.ndimage import gaussian_filter
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

from ..data.cache import cached_analysis as cache_result
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PowerTorqueResults:
    """Results from power and torque analysis."""

    power_curve: pd.DataFrame  # rpm, power, torque
    max_power: float
    max_power_rpm: float
    max_torque: float
    max_torque_rpm: float
    power_band: Tuple[float, float]  # RPM range for 90% of max power
    torque_band: Tuple[float, float]  # RPM range for 90% of max torque
    specific_power: float  # Power per unit displacement
    bmep: np.ndarray  # Brake Mean Effective Pressure
    volumetric_efficiency: np.ndarray


@dataclass
class AccelerationAnalysis:
    """Results from acceleration analysis."""

    acceleration_profile: pd.DataFrame  # time, speed, acceleration
    zero_to_100_time: float
    quarter_mile_time: float
    quarter_mile_speed: float
    max_acceleration: float
    acceleration_at_speed: Dict[int, float]  # speed -> acceleration
    power_to_weight_ratio: float
    launch_efficiency: float


@dataclass
class BoostAnalysis:
    """Results from boost/turbocharger analysis."""

    boost_pressure_profile: pd.DataFrame
    max_boost: float
    boost_threshold_rpm: float
    turbo_lag: float  # Time to reach target boost
    boost_efficiency: np.ndarray
    compressor_map_point: Optional[Tuple[float, float]]  # flow, pressure ratio
    intercooler_efficiency: float
    wastegate_activity: np.ndarray


@dataclass
class KnockDetection:
    """Results from knock detection analysis."""

    knock_events: List[Tuple[float, float, float]]  # time, intensity, frequency
    knock_intensity_profile: pd.DataFrame
    knock_prone_conditions: Dict[str, Any]
    ignition_timing_correlation: float
    load_correlation: float
    temperature_correlation: float
    knock_mitigation_suggestions: List[str]


@dataclass
class ThermalAnalysis:
    """Results from thermal analysis."""

    temperature_profiles: Dict[str, pd.DataFrame]  # sensor -> profile
    heat_rejection_rate: np.ndarray
    thermal_efficiency: np.ndarray
    cooling_effectiveness: float
    overheating_events: List[Tuple[float, float, str]]  # start_time, duration, severity
    thermal_stress_indicators: Dict[str, float]


@dataclass
class PerformanceMetrics:
    """Overall performance metrics summary."""

    indicated_power: float
    brake_power: float
    mechanical_efficiency: float
    thermal_efficiency: float
    volumetric_efficiency: float
    fuel_conversion_efficiency: float
    specific_fuel_consumption: float
    power_density: float
    torque_density: float
    performance_rating: str  # A-F rating


class PerformanceAnalyzer:
    """Advanced engine performance analysis for FuelTune telemetry data."""

    def __init__(self, engine_displacement: float = 2.0, vehicle_weight: float = 1500):
        """
        Initialize performance analyzer.

        Args:
            engine_displacement: Engine displacement in liters
            vehicle_weight: Vehicle weight in kg
        """
        self.engine_displacement = engine_displacement
        self.vehicle_weight = vehicle_weight
        self.logger = logger

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Standard analyze method for performance analysis.

        Args:
            data: Input DataFrame with engine/vehicle data

        Returns:
            Dictionary with comprehensive performance analysis results
        """
        try:
            results = {}
            
            # Power/Torque analysis if RPM data available
            if "engine_rpm" in data.columns or "rpm" in data.columns:
                rpm_col = "engine_rpm" if "engine_rpm" in data.columns else "rpm"
                try:
                    power_torque = self.analyze_power_torque(data, rpm_col=rpm_col)
                    results["power_torque"] = power_torque
                except Exception as e:
                    self.logger.warning(f"Power/torque analysis failed: {e}")
            
            # Acceleration analysis if speed/time data available
            if ("vehicle_speed" in data.columns or "speed" in data.columns) and "time" in data.columns:
                speed_col = "vehicle_speed" if "vehicle_speed" in data.columns else "speed"
                try:
                    acceleration = self.analyze_acceleration(data, speed_col=speed_col, time_col="time")
                    results["acceleration"] = acceleration
                except Exception as e:
                    self.logger.warning(f"Acceleration analysis failed: {e}")
            
            # Thermal analysis if temperature data available
            temp_cols = [col for col in data.columns if "temp" in col.lower()]
            if temp_cols:
                try:
                    thermal = self.analyze_thermal_behavior(data, temp_columns=temp_cols)
                    results["thermal"] = thermal
                except Exception as e:
                    self.logger.warning(f"Thermal analysis failed: {e}")
            
            if not results:
                results["warning"] = "No suitable columns found for performance analysis"
                results["available_columns"] = list(data.columns)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}

    @cache_result("analysis", ttl=3600)
    def analyze_power_torque(
        self,
        data: pd.DataFrame,
        rpm_col: str = "engine_rpm",
        manifold_pressure_col: str = "manifold_pressure",
        air_flow_col: str = "maf_sensor",
        fuel_flow_col: str = "fuel_flow_rate",
        displacement: Optional[float] = None,
    ) -> PowerTorqueResults:
        """
        Analyze engine power and torque characteristics.

        Args:
            data: DataFrame with engine data
            rpm_col: Column name for engine RPM
            manifold_pressure_col: Column name for manifold pressure
            air_flow_col: Column name for air flow rate
            fuel_flow_col: Column name for fuel flow rate
            displacement: Engine displacement override

        Returns:
            PowerTorqueResults object
        """
        try:
            required_cols = [rpm_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            displacement = displacement or self.engine_displacement

            # Clean data
            clean_data = data[(data[rpm_col] > 500) & data[rpm_col].notna()].copy()  # Avoid idle

            if len(clean_data) < 10:
                raise ValueError("Insufficient data for power/torque analysis")

            # Estimate power and torque if not directly available
            power_estimated = False
            torque_estimated = False

            if "engine_power" in clean_data.columns:
                power = clean_data["engine_power"].values
            else:
                # Estimate power from air flow and fuel flow
                if air_flow_col in clean_data.columns and fuel_flow_col in clean_data.columns:
                    # Simplified power estimation: P = (air_flow * fuel_flow * efficiency_factor)
                    air_flow = clean_data[air_flow_col].fillna(0).values
                    fuel_flow = clean_data[fuel_flow_col].fillna(0).values
                    power = air_flow * fuel_flow * 0.1  # Rough approximation
                    power_estimated = True
                else:
                    # Very rough estimation based on RPM and displacement
                    rpm = clean_data[rpm_col].values
                    power = rpm * displacement * 0.001  # Very rough
                    power_estimated = True

            if "engine_torque" in clean_data.columns:
                torque = clean_data["engine_torque"].values
            else:
                # Calculate torque from power and RPM
                rpm = clean_data[rpm_col].values
                torque = (power * 60) / (2 * np.pi * rpm / 60)  # P = T * ω
                torque_estimated = True

            # Create power curve
            power_curve_data = pd.DataFrame(
                {
                    "rpm": clean_data[rpm_col].values,
                    "power": power,
                    "torque": torque,
                }
            )

            # Sort by RPM and remove duplicates
            power_curve_data = power_curve_data.sort_values("rpm").drop_duplicates("rpm")

            # Smooth the curves if estimated
            if power_estimated or torque_estimated:
                window_size = min(21, len(power_curve_data) // 5)
                if window_size >= 3:
                    power_curve_data["power"] = signal.savgol_filter(
                        power_curve_data["power"], window_size, 3
                    )
                    power_curve_data["torque"] = signal.savgol_filter(
                        power_curve_data["torque"], window_size, 3
                    )

            # Find maximum values
            max_power_idx = power_curve_data["power"].idxmax()
            max_power = power_curve_data.loc[max_power_idx, "power"]
            max_power_rpm = power_curve_data.loc[max_power_idx, "rpm"]

            max_torque_idx = power_curve_data["torque"].idxmax()
            max_torque = power_curve_data.loc[max_torque_idx, "torque"]
            max_torque_rpm = power_curve_data.loc[max_torque_idx, "rpm"]

            # Find power and torque bands (90% of maximum)
            power_threshold = max_power * 0.9
            torque_threshold = max_torque * 0.9

            power_band_data = power_curve_data[power_curve_data["power"] >= power_threshold]
            if len(power_band_data) > 0:
                power_band = (power_band_data["rpm"].min(), power_band_data["rpm"].max())
            else:
                power_band = (max_power_rpm, max_power_rpm)

            torque_band_data = power_curve_data[power_curve_data["torque"] >= torque_threshold]
            if len(torque_band_data) > 0:
                torque_band = (torque_band_data["rpm"].min(), torque_band_data["rpm"].max())
            else:
                torque_band = (max_torque_rpm, max_torque_rpm)

            # Calculate specific power (kW/L)
            specific_power = max_power / displacement

            # Calculate BMEP (Brake Mean Effective Pressure)
            # BMEP = (Torque * 4π) / Displacement
            bmep = (torque * 4 * np.pi) / displacement

            # Estimate volumetric efficiency
            if manifold_pressure_col in clean_data.columns and air_flow_col in clean_data.columns:
                manifold_pressure = clean_data[manifold_pressure_col].fillna(101.325).values  # kPa
                air_flow = clean_data[air_flow_col].fillna(0).values  # kg/h
                rpm = clean_data[rpm_col].values

                # Theoretical air flow
                theoretical_air_flow = (displacement * rpm * manifold_pressure) / (120 * 101.325)
                theoretical_air_flow *= 1.225  # Air density at STP (kg/m³)

                volumetric_efficiency = np.where(
                    theoretical_air_flow > 0,
                    (air_flow / 3.6) / theoretical_air_flow,  # Convert kg/h to kg/s
                    0,
                )
                volumetric_efficiency = np.clip(volumetric_efficiency, 0, 2)  # Reasonable limits
            else:
                volumetric_efficiency = np.ones_like(power) * 0.85  # Assume 85% VE

            return PowerTorqueResults(
                power_curve=power_curve_data,
                max_power=max_power,
                max_power_rpm=max_power_rpm,
                max_torque=max_torque,
                max_torque_rpm=max_torque_rpm,
                power_band=power_band,
                torque_band=torque_band,
                specific_power=specific_power,
                bmep=bmep,
                volumetric_efficiency=volumetric_efficiency,
            )

        except Exception as e:
            self.logger.error(f"Error in power/torque analysis: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def analyze_acceleration(
        self,
        data: pd.DataFrame,
        speed_col: str = "vehicle_speed",
        time_col: str = "time",
        power_col: Optional[str] = None,
    ) -> AccelerationAnalysis:
        """
        Analyze vehicle acceleration performance.

        Args:
            data: DataFrame with vehicle data
            speed_col: Column name for vehicle speed
            time_col: Column name for time
            power_col: Optional column name for power

        Returns:
            AccelerationAnalysis object
        """
        try:
            required_cols = [speed_col, time_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Clean and sort data
            clean_data = data[data[speed_col].notna() & data[time_col].notna()].copy()

            clean_data = clean_data.sort_values(time_col)

            if len(clean_data) < 10:
                raise ValueError("Insufficient data for acceleration analysis")

            # Calculate acceleration
            speed_kmh = clean_data[speed_col].values
            speed_ms = speed_kmh / 3.6  # Convert to m/s
            time_s = clean_data[time_col].values

            # Calculate time differences
            dt = np.diff(time_s)
            dt = np.where(dt > 0, dt, 0.1)  # Avoid division by zero

            # Calculate acceleration
            dv = np.diff(speed_ms)
            acceleration_ms2 = dv / dt

            # Smooth acceleration data
            if len(acceleration_ms2) >= 5:
                window_size = min(11, len(acceleration_ms2) // 3)
                if window_size >= 3 and window_size % 2 == 1:
                    acceleration_ms2 = signal.savgol_filter(acceleration_ms2, window_size, 2)

            # Create acceleration profile
            acceleration_profile = pd.DataFrame(
                {
                    "time": time_s[1:],  # Skip first point due to diff
                    "speed": speed_kmh[1:],
                    "acceleration": acceleration_ms2 * 3.6,  # Convert to km/h/s for readability
                }
            )

            # Find 0-100 km/h time
            zero_to_100_time = np.nan
            start_speed = 5  # Start from 5 km/h to avoid noise
            target_speed = 100

            start_mask = speed_kmh >= start_speed
            target_mask = speed_kmh >= target_speed

            if np.any(start_mask) and np.any(target_mask):
                start_time = time_s[start_mask][0]
                target_indices = np.where(target_mask)[0]

                if len(target_indices) > 0:
                    target_time = time_s[target_indices[0]]
                    zero_to_100_time = target_time - start_time

            # Quarter mile analysis (very simplified)
            quarter_mile_time = np.nan
            quarter_mile_speed = np.nan

            # Estimate based on acceleration profile (rough approximation)
            if not np.isnan(zero_to_100_time) and zero_to_100_time > 0:
                # Very rough estimation: quarter mile ≈ 1.5 * 0-100 time
                quarter_mile_time = zero_to_100_time * 1.5
                # Estimate speed at quarter mile
                max_speed_in_data = np.max(speed_kmh)
                quarter_mile_speed = min(max_speed_in_data, 140)  # Rough estimate

            # Maximum acceleration
            max_acceleration = np.max(acceleration_ms2) if len(acceleration_ms2) > 0 else 0

            # Acceleration at specific speeds
            acceleration_at_speed = {}
            target_speeds = [30, 50, 80, 100, 120]

            for target in target_speeds:
                # Find closest speed point
                speed_diff = np.abs(speed_kmh[1:] - target)
                if len(speed_diff) > 0:
                    closest_idx = np.argmin(speed_diff)
                    if speed_diff[closest_idx] < 10:  # Within 10 km/h
                        acceleration_at_speed[target] = acceleration_ms2[closest_idx]

            # Power-to-weight ratio
            if power_col and power_col in clean_data.columns:
                max_power = clean_data[power_col].max()
                power_to_weight_ratio = max_power / self.vehicle_weight  # kW/kg
            else:
                # Estimate from acceleration
                # P = F * v = m * a * v
                if max_acceleration > 0:
                    # Rough estimation at 50 km/h
                    velocity_50 = 50 / 3.6  # m/s
                    estimated_power = (
                        self.vehicle_weight * max_acceleration * velocity_50 / 1000
                    )  # kW
                    power_to_weight_ratio = estimated_power / self.vehicle_weight
                else:
                    power_to_weight_ratio = 0.1  # Default low value

            # Launch efficiency (0-60 km/h acceleration consistency)
            launch_efficiency = 1.0  # Default perfect efficiency
            if len(acceleration_profile) > 10:
                # Look at acceleration consistency in 0-60 km/h range
                launch_mask = (acceleration_profile["speed"] >= 5) & (
                    acceleration_profile["speed"] <= 60
                )
                if np.any(launch_mask):
                    launch_accel = acceleration_profile.loc[launch_mask, "acceleration"]
                    if len(launch_accel) > 5:
                        # Efficiency based on coefficient of variation
                        cv = (
                            np.std(launch_accel) / np.mean(launch_accel)
                            if np.mean(launch_accel) > 0
                            else 1
                        )
                        launch_efficiency = max(0, 1 - cv)

            return AccelerationAnalysis(
                acceleration_profile=acceleration_profile,
                zero_to_100_time=zero_to_100_time,
                quarter_mile_time=quarter_mile_time,
                quarter_mile_speed=quarter_mile_speed,
                max_acceleration=max_acceleration,
                acceleration_at_speed=acceleration_at_speed,
                power_to_weight_ratio=power_to_weight_ratio,
                launch_efficiency=launch_efficiency,
            )

        except Exception as e:
            self.logger.error(f"Error in acceleration analysis: {e}")
            raise

    def analyze_boost_performance(
        self,
        data: pd.DataFrame,
        boost_pressure_col: str = "boost_pressure",
        rpm_col: str = "engine_rpm",
        throttle_col: str = "throttle_position",
        intake_temp_col: str = "intake_air_temp",
    ) -> BoostAnalysis:
        """
        Analyze turbocharger/supercharger boost performance.

        Args:
            data: DataFrame with boost data
            boost_pressure_col: Column name for boost pressure
            rpm_col: Column name for engine RPM
            throttle_col: Column name for throttle position
            intake_temp_col: Column name for intake air temperature

        Returns:
            BoostAnalysis object
        """
        try:
            required_cols = [boost_pressure_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Clean data
            clean_data = data[data[boost_pressure_col].notna()].copy()

            if len(clean_data) < 10:
                raise ValueError("Insufficient data for boost analysis")

            # Create boost pressure profile
            boost_pressure_profile = pd.DataFrame(
                {
                    "time": range(len(clean_data)),  # Simplified time index
                    "boost_pressure": clean_data[boost_pressure_col].values,
                    "rpm": (
                        clean_data[rpm_col].values
                        if rpm_col in clean_data.columns
                        else np.zeros(len(clean_data))
                    ),
                    "throttle": (
                        clean_data[throttle_col].values
                        if throttle_col in clean_data.columns
                        else np.ones(len(clean_data)) * 100
                    ),
                }
            )

            # Maximum boost pressure
            max_boost = clean_data[boost_pressure_col].max()

            # Boost threshold RPM (where boost starts building)
            boost_threshold_rpm = 0
            if rpm_col in clean_data.columns:
                # Find RPM where boost exceeds 10% of max
                boost_threshold = max_boost * 0.1
                boost_mask = clean_data[boost_pressure_col] > boost_threshold
                if np.any(boost_mask):
                    boost_threshold_rpm = clean_data.loc[boost_mask, rpm_col].min()

            # Turbo lag estimation (simplified)
            turbo_lag = 0.0
            if throttle_col in clean_data.columns:
                # Look for throttle opening events and corresponding boost response
                throttle = clean_data[throttle_col].values
                boost = clean_data[boost_pressure_col].values

                # Find throttle opening events (derivative > threshold)
                if len(throttle) > 10:
                    throttle_diff = np.diff(throttle)
                    opening_events = np.where(throttle_diff > 20)[0]  # Large throttle opening

                    if len(opening_events) > 0:
                        # Look at boost response after first event
                        event_idx = opening_events[0]
                        if event_idx < len(boost) - 10:
                            boost_before = boost[event_idx]
                            boost_target = boost_before + (max_boost - boost_before) * 0.8

                            # Find time to reach target boost
                            boost_after = boost[event_idx : event_idx + 10]
                            target_indices = np.where(boost_after >= boost_target)[0]

                            if len(target_indices) > 0:
                                turbo_lag = target_indices[0] * 0.1  # Assume 100ms intervals

            # Boost efficiency (simplified calculation)
            if throttle_col in clean_data.columns:
                throttle = clean_data[throttle_col].values
                boost = clean_data[boost_pressure_col].values

                # Efficiency = actual boost / expected boost based on throttle
                expected_boost = (throttle / 100) * max_boost
                boost_efficiency = np.where(
                    expected_boost > 0, np.minimum(boost / expected_boost, 2.0), 0  # Cap at 200%
                )
            else:
                boost_efficiency = np.ones(len(clean_data))

            # Compressor map point (very simplified)
            compressor_map_point = None
            if rpm_col in clean_data.columns:
                # Rough estimation based on RPM and boost
                rpm = clean_data[rpm_col].values
                boost = clean_data[boost_pressure_col].values

                # Find point of maximum boost
                max_boost_idx = np.argmax(boost)
                if max_boost_idx < len(rpm):
                    flow_estimate = (
                        rpm[max_boost_idx] * self.engine_displacement / 1000
                    )  # Rough flow
                    pressure_ratio = (
                        boost[max_boost_idx] + 101.325
                    ) / 101.325  # Absolute pressure ratio
                    compressor_map_point = (flow_estimate, pressure_ratio)

            # Intercooler efficiency
            intercooler_efficiency = 0.8  # Default assumption
            if intake_temp_col in clean_data.columns:
                # Calculate efficiency based on temperature drop
                intake_temps = clean_data[intake_temp_col].values
                ambient_temp = 25  # Assumed ambient temperature

                if len(intake_temps) > 0:
                    avg_intake_temp = np.mean(intake_temps)
                    # Rough estimation of intercooler efficiency
                    if avg_intake_temp > ambient_temp:
                        temp_rise = avg_intake_temp - ambient_temp
                        # Assume perfect intercooler would reduce to ambient + 10°C
                        intercooler_efficiency = max(0, 1 - (temp_rise - 10) / 50)

            # Wastegate activity (simplified detection)
            wastegate_activity = np.zeros(len(clean_data))
            if len(boost_pressure_profile) > 10:
                # Look for boost pressure plateaus indicating wastegate operation
                boost_smooth = signal.savgol_filter(
                    boost_pressure_profile["boost_pressure"],
                    min(11, len(boost_pressure_profile) // 3),
                    2,
                )
                boost_derivative = np.gradient(boost_smooth)

                # Wastegate likely active when boost levels off despite high RPM
                plateau_threshold = 0.1  # Very small boost change
                wastegate_activity = np.abs(boost_derivative) < plateau_threshold

            return BoostAnalysis(
                boost_pressure_profile=boost_pressure_profile,
                max_boost=max_boost,
                boost_threshold_rpm=boost_threshold_rpm,
                turbo_lag=turbo_lag,
                boost_efficiency=boost_efficiency,
                compressor_map_point=compressor_map_point,
                intercooler_efficiency=intercooler_efficiency,
                wastegate_activity=wastegate_activity.astype(float),
            )

        except Exception as e:
            self.logger.error(f"Error in boost analysis: {e}")
            raise

    def detect_knock(
        self,
        data: pd.DataFrame,
        knock_sensor_col: str = "knock_sensor",
        ignition_timing_col: str = "ignition_timing",
        load_col: str = "engine_load",
        coolant_temp_col: str = "coolant_temp",
        frequency_threshold: float = 6000,  # Hz
        intensity_threshold: float = 0.5,
    ) -> KnockDetection:
        """
        Detect engine knock events and analyze patterns.

        Args:
            data: DataFrame with engine data
            knock_sensor_col: Column name for knock sensor
            ignition_timing_col: Column name for ignition timing
            load_col: Column name for engine load
            coolant_temp_col: Column name for coolant temperature
            frequency_threshold: Frequency threshold for knock detection
            intensity_threshold: Intensity threshold for knock detection

        Returns:
            KnockDetection object
        """
        try:
            if knock_sensor_col not in data.columns:
                # If no knock sensor, create dummy results
                return KnockDetection(
                    knock_events=[],
                    knock_intensity_profile=pd.DataFrame(),
                    knock_prone_conditions={},
                    ignition_timing_correlation=0.0,
                    load_correlation=0.0,
                    temperature_correlation=0.0,
                    knock_mitigation_suggestions=[],
                )

            # Clean data
            clean_data = data[data[knock_sensor_col].notna()].copy()

            if len(clean_data) < 10:
                raise ValueError("Insufficient knock sensor data")

            knock_sensor_values = clean_data[knock_sensor_col].values

            # Simple knock detection based on amplitude
            knock_events = []
            for i, intensity in enumerate(knock_sensor_values):
                if intensity > intensity_threshold:
                    # Estimate frequency (simplified)
                    frequency = frequency_threshold + (intensity - intensity_threshold) * 1000
                    time = i * 0.1  # Assume 100ms intervals
                    knock_events.append((time, intensity, frequency))

            # Create knock intensity profile
            knock_intensity_profile = pd.DataFrame(
                {
                    "time": range(len(knock_sensor_values)),
                    "knock_intensity": knock_sensor_values,
                }
            )

            # Analyze knock-prone conditions
            knock_prone_conditions = {}

            if len(knock_events) > 0:
                knock_times = [event[0] for event in knock_events]
                knock_indices = [
                    int(t / 0.1) for t in knock_times if int(t / 0.1) < len(clean_data)
                ]

                if knock_indices:
                    # Conditions during knock events
                    if load_col in clean_data.columns:
                        knock_loads = clean_data.iloc[knock_indices][load_col].values
                        knock_prone_conditions["avg_load_during_knock"] = np.mean(knock_loads)

                    if coolant_temp_col in clean_data.columns:
                        knock_temps = clean_data.iloc[knock_indices][coolant_temp_col].values
                        knock_prone_conditions["avg_temp_during_knock"] = np.mean(knock_temps)

            # Correlation analysis
            ignition_timing_correlation = 0.0
            load_correlation = 0.0
            temperature_correlation = 0.0

            if len(knock_sensor_values) > 10:
                if ignition_timing_col in clean_data.columns:
                    timing_values = clean_data[ignition_timing_col].values
                    if len(timing_values) == len(knock_sensor_values):
                        ignition_timing_correlation = np.corrcoef(
                            knock_sensor_values, timing_values
                        )[0, 1]
                        if np.isnan(ignition_timing_correlation):
                            ignition_timing_correlation = 0.0

                if load_col in clean_data.columns:
                    load_values = clean_data[load_col].values
                    if len(load_values) == len(knock_sensor_values):
                        load_correlation = np.corrcoef(knock_sensor_values, load_values)[0, 1]
                        if np.isnan(load_correlation):
                            load_correlation = 0.0

                if coolant_temp_col in clean_data.columns:
                    temp_values = clean_data[coolant_temp_col].values
                    if len(temp_values) == len(knock_sensor_values):
                        temperature_correlation = np.corrcoef(knock_sensor_values, temp_values)[
                            0, 1
                        ]
                        if np.isnan(temperature_correlation):
                            temperature_correlation = 0.0

            # Knock mitigation suggestions
            knock_mitigation_suggestions = []

            if len(knock_events) > 5:  # Significant knock activity
                knock_mitigation_suggestions.append("Consider using higher octane fuel")

                if ignition_timing_correlation > 0.3:
                    knock_mitigation_suggestions.append("Reduce ignition timing advance")

                if temperature_correlation > 0.3:
                    knock_mitigation_suggestions.append("Improve engine cooling system")

                if load_correlation > 0.3:
                    knock_mitigation_suggestions.append("Reduce engine load or boost pressure")

            return KnockDetection(
                knock_events=knock_events,
                knock_intensity_profile=knock_intensity_profile,
                knock_prone_conditions=knock_prone_conditions,
                ignition_timing_correlation=ignition_timing_correlation,
                load_correlation=load_correlation,
                temperature_correlation=temperature_correlation,
                knock_mitigation_suggestions=knock_mitigation_suggestions,
            )

        except Exception as e:
            self.logger.error(f"Error in knock detection: {e}")
            raise

    def create_performance_plots(
        self,
        power_torque: Optional[PowerTorqueResults] = None,
        acceleration: Optional[AccelerationAnalysis] = None,
        boost: Optional[BoostAnalysis] = None,
        title: str = "Performance Analysis",
    ) -> Dict[str, go.Figure]:
        """
        Create comprehensive performance analysis plots.

        Args:
            power_torque: Power/torque analysis results
            acceleration: Acceleration analysis results
            boost: Boost analysis results
            title: Base title for plots

        Returns:
            Dictionary of plot names -> plotly figures
        """
        try:
            plots = {}

            # 1. Power and Torque curves
            if power_torque:
                fig_power_torque = make_subplots(
                    rows=1,
                    cols=1,
                    specs=[[{"secondary_y": True}]],
                    subplot_titles=["Power and Torque Curves"],
                )

                # Power curve
                fig_power_torque.add_trace(
                    go.Scatter(
                        x=power_torque.power_curve["rpm"],
                        y=power_torque.power_curve["power"],
                        mode="lines",
                        name="Power",
                        line=dict(color="red", width=2),
                    ),
                    secondary_y=False,
                )

                # Torque curve
                fig_power_torque.add_trace(
                    go.Scatter(
                        x=power_torque.power_curve["rpm"],
                        y=power_torque.power_curve["torque"],
                        mode="lines",
                        name="Torque",
                        line=dict(color="blue", width=2),
                    ),
                    secondary_y=True,
                )

                # Mark maximum points
                fig_power_torque.add_trace(
                    go.Scatter(
                        x=[power_torque.max_power_rpm],
                        y=[power_torque.max_power],
                        mode="markers",
                        name=f"Max Power ({power_torque.max_power:.1f} kW)",
                        marker=dict(color="red", size=10, symbol="star"),
                    ),
                    secondary_y=False,
                )

                fig_power_torque.add_trace(
                    go.Scatter(
                        x=[power_torque.max_torque_rpm],
                        y=[power_torque.max_torque],
                        mode="markers",
                        name=f"Max Torque ({power_torque.max_torque:.1f} Nm)",
                        marker=dict(color="blue", size=10, symbol="star"),
                    ),
                    secondary_y=True,
                )

                # Set axis titles
                fig_power_torque.update_xaxes(title_text="RPM")
                fig_power_torque.update_yaxes(title_text="Power (kW)", secondary_y=False)
                fig_power_torque.update_yaxes(title_text="Torque (Nm)", secondary_y=True)

                fig_power_torque.update_layout(
                    title=f"{title} - Power and Torque Curves",
                    legend=dict(x=0.7, y=0.95),
                )
                plots["power_torque_curves"] = fig_power_torque

            # 2. Acceleration profile
            if acceleration:
                fig_accel = make_subplots(
                    rows=2,
                    cols=1,
                    subplot_titles=["Speed vs Time", "Acceleration vs Speed"],
                    vertical_spacing=0.15,
                )

                # Speed vs time
                fig_accel.add_trace(
                    go.Scatter(
                        x=acceleration.acceleration_profile["time"],
                        y=acceleration.acceleration_profile["speed"],
                        mode="lines",
                        name="Speed",
                        line=dict(color="green", width=2),
                    ),
                    row=1,
                    col=1,
                )

                # Acceleration vs speed
                fig_accel.add_trace(
                    go.Scatter(
                        x=acceleration.acceleration_profile["speed"],
                        y=acceleration.acceleration_profile["acceleration"],
                        mode="lines+markers",
                        name="Acceleration",
                        line=dict(color="orange", width=2),
                        marker=dict(size=4),
                    ),
                    row=2,
                    col=1,
                )

                # Mark 0-100 time if available
                if not np.isnan(acceleration.zero_to_100_time):
                    fig_accel.add_annotation(
                        x=0.1,
                        y=0.9,
                        text=f"0-100 km/h: {acceleration.zero_to_100_time:.2f}s",
                        xref="paper",
                        yref="paper",
                        showarrow=False,
                        font=dict(size=12, color="red"),
                        bgcolor="white",
                        bordercolor="red",
                    )

                fig_accel.update_xaxes(title_text="Time (s)", row=1, col=1)
                fig_accel.update_yaxes(title_text="Speed (km/h)", row=1, col=1)
                fig_accel.update_xaxes(title_text="Speed (km/h)", row=2, col=1)
                fig_accel.update_yaxes(title_text="Acceleration (km/h/s)", row=2, col=1)

                fig_accel.update_layout(
                    title=f"{title} - Acceleration Analysis",
                    height=600,
                )
                plots["acceleration_analysis"] = fig_accel

            # 3. Boost pressure analysis
            if boost:
                fig_boost = go.Figure()

                # Boost pressure profile
                fig_boost.add_trace(
                    go.Scatter(
                        x=boost.boost_pressure_profile["time"],
                        y=boost.boost_pressure_profile["boost_pressure"],
                        mode="lines",
                        name="Boost Pressure",
                        line=dict(color="purple", width=2),
                    )
                )

                # Mark maximum boost
                max_boost_time = boost.boost_pressure_profile.loc[
                    boost.boost_pressure_profile["boost_pressure"].idxmax(), "time"
                ]

                fig_boost.add_trace(
                    go.Scatter(
                        x=[max_boost_time],
                        y=[boost.max_boost],
                        mode="markers",
                        name=f"Max Boost ({boost.max_boost:.1f} bar)",
                        marker=dict(color="red", size=10, symbol="star"),
                    )
                )

                # Add turbo lag annotation if available
                if boost.turbo_lag > 0:
                    fig_boost.add_annotation(
                        x=0.1,
                        y=0.9,
                        text=f"Turbo Lag: {boost.turbo_lag:.2f}s",
                        xref="paper",
                        yref="paper",
                        showarrow=False,
                        font=dict(size=12, color="blue"),
                        bgcolor="white",
                        bordercolor="blue",
                    )

                fig_boost.update_layout(
                    title=f"{title} - Boost Pressure Analysis",
                    xaxis_title="Time Index",
                    yaxis_title="Boost Pressure (bar)",
                )
                plots["boost_analysis"] = fig_boost

            return plots

        except Exception as e:
            self.logger.error(f"Error creating performance plots: {e}")
            raise

    def generate_performance_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive performance analysis summary.

        Args:
            data: DataFrame with vehicle/engine data

        Returns:
            Dictionary with all performance analysis results
        """
        try:
            results = {}

            # Power/Torque Analysis
            try:
                power_torque_results = self.analyze_power_torque(data)
                results["power_torque"] = power_torque_results
            except Exception as e:
                self.logger.warning(f"Power/torque analysis failed: {e}")

            # Acceleration Analysis
            try:
                acceleration_results = self.analyze_acceleration(data)
                results["acceleration"] = acceleration_results
            except Exception as e:
                self.logger.warning(f"Acceleration analysis failed: {e}")

            # Boost Analysis
            try:
                boost_results = self.analyze_boost_performance(data)
                results["boost"] = boost_results
            except Exception as e:
                self.logger.warning(f"Boost analysis failed: {e}")

            # Knock Detection
            try:
                knock_results = self.detect_knock(data)
                results["knock_detection"] = knock_results
            except Exception as e:
                self.logger.warning(f"Knock detection failed: {e}")

            # Create plots
            plots = self.create_performance_plots(
                power_torque=results.get("power_torque"),
                acceleration=results.get("acceleration"),
                boost=results.get("boost"),
            )
            results["plots"] = plots

            # Performance summary metrics
            summary_metrics = {}

            if "power_torque" in results:
                pt = results["power_torque"]
                summary_metrics["max_power_kw"] = pt.max_power
                summary_metrics["max_torque_nm"] = pt.max_torque
                summary_metrics["specific_power_kw_per_l"] = pt.specific_power

            if "acceleration" in results:
                acc = results["acceleration"]
                summary_metrics["zero_to_100_time_s"] = acc.zero_to_100_time
                summary_metrics["power_to_weight_ratio"] = acc.power_to_weight_ratio
                summary_metrics["max_acceleration_ms2"] = acc.max_acceleration

            if "boost" in results:
                boost = results["boost"]
                summary_metrics["max_boost_bar"] = boost.max_boost
                summary_metrics["turbo_lag_s"] = boost.turbo_lag

            results["summary_metrics"] = summary_metrics

            return results

        except Exception as e:
            self.logger.error(f"Error generating performance summary: {e}")
            raise
