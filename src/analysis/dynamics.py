"""
Vehicle Dynamics Analysis Module for FuelTune.

Provides comprehensive vehicle dynamics analysis including G-force analysis,
pitch/roll/yaw dynamics, lateral/longitudinal acceleration analysis,
and stability metrics for automotive telemetry data.

Author: A04-ANALYSIS-SCIPY Agent
Created: 2025-01-02
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import signal

from ..data.cache import cached_analysis as cache_result
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class GForceAnalysis:
    """Results from G-force analysis."""

    longitudinal_g: np.ndarray
    lateral_g: np.ndarray
    combined_g: np.ndarray
    max_longitudinal_g: float
    max_lateral_g: float
    max_combined_g: float
    g_force_profile: pd.DataFrame
    g_force_distribution: Dict[str, int]  # Range -> count
    comfort_rating: float  # 0-1 scale


@dataclass
class AttitudeAnalysis:
    """Results from vehicle attitude analysis."""

    pitch_angle: np.ndarray
    roll_angle: np.ndarray
    yaw_rate: np.ndarray
    max_pitch: float
    max_roll: float
    max_yaw_rate: float
    attitude_stability: float
    motion_sickness_index: float
    cornering_analysis: Dict[str, float]


@dataclass
class StabilityMetrics:
    """Vehicle stability analysis results."""

    stability_factor: float
    understeer_gradient: float
    oversteer_tendency: float
    stability_events: List[Tuple[float, str, float]]  # time, event_type, severity
    traction_loss_events: List[int]
    stability_rating: str  # A-F rating


@dataclass
class TrackAnalysis:
    """Track/circuit analysis results."""

    cornering_speed_profile: pd.DataFrame
    sector_times: List[float]
    optimal_racing_line: Optional[np.ndarray]
    braking_zones: List[Tuple[int, int]]  # start, end indices
    acceleration_zones: List[Tuple[int, int]]
    track_map: Optional[pd.DataFrame]  # lat, lon, speed, sector


@dataclass
class DrivingStyle:
    """Driving style analysis results."""

    aggressiveness_score: float  # 0-10 scale
    smoothness_score: float  # 0-10 scale
    efficiency_score: float  # 0-10 scale
    consistency_score: float  # 0-10 scale
    driving_characteristics: Dict[str, float]
    improvement_suggestions: List[str]


class VehicleDynamicsAnalyzer:
    """Advanced vehicle dynamics analysis for FuelTune telemetry data."""

    def __init__(self, wheelbase: float = 2.7, track_width: float = 1.5):
        """
        Initialize dynamics analyzer.

        Args:
            wheelbase: Vehicle wheelbase in meters
            track_width: Track width in meters
        """
        self.wheelbase = wheelbase
        self.track_width = track_width
        self.logger = logger

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Main analysis method for vehicle dynamics.

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with dynamics analysis results
        """
        try:
            results = {}

            # Analyze G-forces if acceleration data exists
            if "accel_x" in data.columns or "accelerometer_x" in data.columns:
                try:
                    g_force = self.analyze_g_forces(data)
                    results["g_forces"] = {
                        "peak_lateral": g_force.peak_lateral_g,
                        "peak_longitudinal": g_force.peak_longitudinal_g,
                    }
                except Exception as e:
                    self.logger.warning(f"G-force analysis failed: {e}")

            # Analyze stability
            if "vehicle_speed" in data.columns:
                try:
                    stability = self.analyze_stability(data)
                    results["stability"] = {
                        "stability_index": stability.stability_index,
                        "control_score": stability.control_score,
                    }
                except Exception as e:
                    self.logger.warning(f"Stability analysis failed: {e}")

            return results
        except Exception as e:
            self.logger.error(f"Dynamics analysis failed: {e}")
            return {"error": str(e)}

    @cache_result("analysis", ttl=3600)
    def analyze_g_forces(
        self,
        data: pd.DataFrame,
        accel_x_col: str = "accel_x",
        accel_y_col: str = "accel_y",
        accel_z_col: str = "accel_z",
        speed_col: str = "vehicle_speed",
    ) -> GForceAnalysis:
        """
        Analyze G-force characteristics from IMU data.

        Args:
            data: DataFrame with IMU data
            accel_x_col: Column for longitudinal acceleration
            accel_y_col: Column for lateral acceleration
            accel_z_col: Column for vertical acceleration
            speed_col: Column for vehicle speed

        Returns:
            GForceAnalysis object
        """
        try:
            # Check available columns
            available_cols = [
                col for col in [accel_x_col, accel_y_col, accel_z_col] if col in data.columns
            ]

            if not available_cols:
                # Estimate from speed if available
                if speed_col in data.columns:
                    return self._estimate_g_forces_from_speed(data, speed_col)
                else:
                    raise ValueError("No acceleration data available")

            # Clean data
            clean_data = data[data[available_cols].notna().any(axis=1)].copy()

            if len(clean_data) < 10:
                raise ValueError("Insufficient IMU data")

            # Extract acceleration components (convert from m/s² to g)
            g_constant = 9.80665

            if accel_x_col in available_cols:
                longitudinal_g = clean_data[accel_x_col].fillna(0).values / g_constant
            else:
                longitudinal_g = np.zeros(len(clean_data))

            if accel_y_col in available_cols:
                lateral_g = clean_data[accel_y_col].fillna(0).values / g_constant
            else:
                lateral_g = np.zeros(len(clean_data))

            if accel_z_col in available_cols:
                vertical_g = clean_data[accel_z_col].fillna(0).values / g_constant
                # Remove gravity component (assume 1g downward when stationary)
                vertical_g = vertical_g - 1.0
            else:
                vertical_g = np.zeros(len(clean_data))

            # Calculate combined G-force
            combined_g = np.sqrt(longitudinal_g**2 + lateral_g**2)

            # Find maximum values
            max_longitudinal_g = np.max(np.abs(longitudinal_g))
            max_lateral_g = np.max(np.abs(lateral_g))
            max_combined_g = np.max(combined_g)

            # Create G-force profile
            g_force_profile = pd.DataFrame(
                {
                    "time": range(len(longitudinal_g)),
                    "longitudinal_g": longitudinal_g,
                    "lateral_g": lateral_g,
                    "vertical_g": vertical_g,
                    "combined_g": combined_g,
                }
            )

            # G-force distribution analysis
            g_ranges = [(0, 0.3), (0.3, 0.6), (0.6, 0.9), (0.9, 1.2), (1.2, np.inf)]
            g_range_labels = ["low", "moderate", "high", "very_high", "extreme"]

            g_force_distribution = {}
            for (min_g, max_g), label in zip(g_ranges, g_range_labels):
                count = np.sum((combined_g >= min_g) & (combined_g < max_g))
                g_force_distribution[label] = count

            # Comfort rating (lower G-forces = more comfortable)
            # Based on sustained G-force levels
            comfort_penalty = 0
            for g_val in combined_g:
                if g_val > 0.5:
                    comfort_penalty += (g_val - 0.5) * 0.1
                if g_val > 1.0:
                    comfort_penalty += (g_val - 1.0) * 0.2

            comfort_rating = max(0, 1 - comfort_penalty / len(combined_g))

            return GForceAnalysis(
                longitudinal_g=longitudinal_g,
                lateral_g=lateral_g,
                combined_g=combined_g,
                max_longitudinal_g=max_longitudinal_g,
                max_lateral_g=max_lateral_g,
                max_combined_g=max_combined_g,
                g_force_profile=g_force_profile,
                g_force_distribution=g_force_distribution,
                comfort_rating=comfort_rating,
            )

        except Exception as e:
            self.logger.error(f"Error in G-force analysis: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def analyze_vehicle_attitude(
        self,
        data: pd.DataFrame,
        gyro_x_col: str = "gyro_x",
        gyro_y_col: str = "gyro_y",
        gyro_z_col: str = "gyro_z",
        accel_x_col: str = "accel_x",
        accel_y_col: str = "accel_y",
        accel_z_col: str = "accel_z",
    ) -> AttitudeAnalysis:
        """
        Analyze vehicle attitude (pitch, roll, yaw) from IMU data.

        Args:
            data: DataFrame with IMU data
            gyro_x_col: Column for X-axis gyroscope
            gyro_y_col: Column for Y-axis gyroscope
            gyro_z_col: Column for Z-axis gyroscope
            accel_x_col: Column for X-axis accelerometer
            accel_y_col: Column for Y-axis accelerometer
            accel_z_col: Column for Z-axis accelerometer

        Returns:
            AttitudeAnalysis object
        """
        try:
            # Check available data
            gyro_cols = [col for col in [gyro_x_col, gyro_y_col, gyro_z_col] if col in data.columns]
            accel_cols = [
                col for col in [accel_x_col, accel_y_col, accel_z_col] if col in data.columns
            ]

            if not gyro_cols and not accel_cols:
                raise ValueError("No IMU data available for attitude analysis")

            # Clean data
            available_cols = gyro_cols + accel_cols
            clean_data = data[data[available_cols].notna().any(axis=1)].copy()

            if len(clean_data) < 10:
                raise ValueError("Insufficient IMU data")

            # Initialize attitude arrays
            pitch_angle = np.zeros(len(clean_data))
            roll_angle = np.zeros(len(clean_data))
            yaw_rate = np.zeros(len(clean_data))

            # Extract gyroscope data (angular rates)
            if gyro_x_col in clean_data.columns:
                clean_data[gyro_x_col].fillna(0).values
            else:
                np.zeros(len(clean_data))

            if gyro_y_col in clean_data.columns:
                clean_data[gyro_y_col].fillna(0).values
            else:
                np.zeros(len(clean_data))

            if gyro_z_col in clean_data.columns:
                yaw_rate = clean_data[gyro_z_col].fillna(0).values
            else:
                yaw_rate = np.zeros(len(clean_data))

            # Extract accelerometer data for attitude estimation
            if accel_x_col in clean_data.columns:
                accel_x = clean_data[accel_x_col].fillna(0).values
            else:
                accel_x = np.zeros(len(clean_data))

            if accel_y_col in clean_data.columns:
                accel_y = clean_data[accel_y_col].fillna(0).values
            else:
                accel_y = np.zeros(len(clean_data))

            if accel_z_col in clean_data.columns:
                accel_z = clean_data[accel_z_col].fillna(0).values
            else:
                accel_z = np.ones(len(clean_data)) * 9.80665  # Default 1g downward

            # Estimate pitch and roll from accelerometer (when not accelerating)
            # This is a simplified approach - real implementation would use sensor fusion

            # Low-pass filter accelerometer data to remove noise
            if len(accel_x) > 5:
                accel_x_filtered = signal.savgol_filter(accel_x, min(11, len(accel_x) // 2), 3)
                accel_y_filtered = signal.savgol_filter(accel_y, min(11, len(accel_y) // 2), 3)
                accel_z_filtered = signal.savgol_filter(accel_z, min(11, len(accel_z) // 2), 3)
            else:
                accel_x_filtered = accel_x
                accel_y_filtered = accel_y
                accel_z_filtered = accel_z

            # Calculate attitude angles from accelerometer
            for i in range(len(clean_data)):
                # Normalize acceleration vector
                acc_magnitude = np.sqrt(
                    accel_x_filtered[i] ** 2 + accel_y_filtered[i] ** 2 + accel_z_filtered[i] ** 2
                )
                if acc_magnitude > 0:
                    ax_norm = accel_x_filtered[i] / acc_magnitude
                    ay_norm = accel_y_filtered[i] / acc_magnitude
                    az_norm = accel_z_filtered[i] / acc_magnitude

                    # Calculate pitch and roll (in radians, then convert to degrees)
                    pitch_angle[i] = (
                        np.arctan2(ax_norm, np.sqrt(ay_norm**2 + az_norm**2)) * 180 / np.pi
                    )
                    roll_angle[i] = np.arctan2(ay_norm, az_norm) * 180 / np.pi

            # Find maximum values
            max_pitch = np.max(np.abs(pitch_angle))
            max_roll = np.max(np.abs(roll_angle))
            max_yaw_rate = np.max(np.abs(yaw_rate))

            # Calculate attitude stability (lower variation = more stable)
            pitch_stability = 1 / (1 + np.std(pitch_angle))
            roll_stability = 1 / (1 + np.std(roll_angle))
            yaw_stability = 1 / (1 + np.std(yaw_rate))
            attitude_stability = (pitch_stability + roll_stability + yaw_stability) / 3

            # Motion sickness index (based on sudden attitude changes)
            pitch_jerk = (
                np.abs(np.diff(pitch_angle, n=2)) if len(pitch_angle) > 2 else np.array([0])
            )
            roll_jerk = np.abs(np.diff(roll_angle, n=2)) if len(roll_angle) > 2 else np.array([0])

            motion_sickness_index = (np.mean(pitch_jerk) + np.mean(roll_jerk)) / 2

            # Cornering analysis
            cornering_analysis = {
                "avg_lateral_attitude": np.mean(np.abs(roll_angle)),
                "max_cornering_angle": max_roll,
                "cornering_consistency": (
                    1 / (1 + np.std(roll_angle[np.abs(roll_angle) > 2]))
                    if np.any(np.abs(roll_angle) > 2)
                    else 1.0
                ),
            }

            return AttitudeAnalysis(
                pitch_angle=pitch_angle,
                roll_angle=roll_angle,
                yaw_rate=yaw_rate,
                max_pitch=max_pitch,
                max_roll=max_roll,
                max_yaw_rate=max_yaw_rate,
                attitude_stability=attitude_stability,
                motion_sickness_index=motion_sickness_index,
                cornering_analysis=cornering_analysis,
            )

        except Exception as e:
            self.logger.error(f"Error in attitude analysis: {e}")
            raise

    def analyze_driving_style(
        self,
        data: pd.DataFrame,
        speed_col: str = "vehicle_speed",
        throttle_col: str = "throttle_position",
        brake_col: str = "brake_pressure",
        steering_col: Optional[str] = None,
    ) -> DrivingStyle:
        """
        Analyze driving style characteristics.

        Args:
            data: DataFrame with vehicle data
            speed_col: Column for vehicle speed
            throttle_col: Column for throttle position
            brake_col: Column for brake pressure
            steering_col: Optional column for steering angle

        Returns:
            DrivingStyle object
        """
        try:
            required_cols = [speed_col]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Clean data
            clean_data = data[data[speed_col].notna()].copy()

            if len(clean_data) < 50:
                raise ValueError("Insufficient data for driving style analysis")

            # Calculate speed changes
            speed = clean_data[speed_col].values
            speed_diff = np.diff(speed)
            time_intervals = np.ones(len(speed_diff))  # Assume 1-second intervals

            # Acceleration and deceleration analysis
            accelerations = speed_diff / time_intervals
            accelerations = accelerations[np.abs(accelerations) < 10]  # Remove outliers

            # Aggressiveness score (0-10)
            # Based on hard acceleration/braking events
            hard_accel_events = np.sum(accelerations > 2)  # >2 km/h/s
            hard_brake_events = np.sum(accelerations < -3)  # <-3 km/h/s

            total_events = len(accelerations)
            aggressive_event_ratio = (hard_accel_events + hard_brake_events) / total_events
            aggressiveness_score = min(10, aggressive_event_ratio * 50)  # Scale to 0-10

            # Smoothness score (0-10)
            # Based on consistency of inputs
            speed_smoothness = 1 / (1 + np.std(speed_diff))

            throttle_smoothness = 1.0
            if throttle_col in clean_data.columns:
                throttle = clean_data[throttle_col].fillna(0).values
                throttle_diff = np.abs(np.diff(throttle))
                throttle_smoothness = 1 / (1 + np.mean(throttle_diff) / 10)

            brake_smoothness = 1.0
            if brake_col in clean_data.columns:
                brake = clean_data[brake_col].fillna(0).values
                brake_diff = np.abs(np.diff(brake))
                brake_smoothness = 1 / (1 + np.mean(brake_diff) / 10)

            smoothness_score = (speed_smoothness + throttle_smoothness + brake_smoothness) / 3 * 10

            # Efficiency score (0-10)
            # Based on maintaining steady speeds and gentle inputs
            steady_speed_time = np.sum(np.abs(speed_diff) < 1) / len(speed_diff)

            # Penalty for excessive speed changes
            efficiency_penalty = np.mean(np.abs(speed_diff)) / 10
            efficiency_score = max(0, (steady_speed_time * 10) - efficiency_penalty)

            # Consistency score (0-10)
            # Based on repeatability of driving patterns

            # Analyze speed distribution consistency
            speed_bins = np.histogram(speed, bins=10)[0]
            speed_distribution_entropy = -np.sum(
                (speed_bins / np.sum(speed_bins)) * np.log(speed_bins / np.sum(speed_bins) + 1e-10)
            )

            # Higher entropy = more consistent speed usage
            consistency_score = min(10, speed_distribution_entropy)

            # Detailed driving characteristics
            driving_characteristics = {
                "avg_speed": np.mean(speed),
                "speed_variance": np.var(speed),
                "max_acceleration": np.max(accelerations) if len(accelerations) > 0 else 0,
                "max_deceleration": np.min(accelerations) if len(accelerations) > 0 else 0,
                "hard_events_per_minute": (hard_accel_events + hard_brake_events)
                / (len(clean_data) / 60),
                "speed_consistency": (
                    1 / (1 + np.std(speed) / np.mean(speed)) if np.mean(speed) > 0 else 0
                ),
            }

            # Add throttle characteristics if available
            if throttle_col in clean_data.columns:
                throttle = clean_data[throttle_col].fillna(0).values
                driving_characteristics["avg_throttle"] = np.mean(throttle)
                driving_characteristics["throttle_variance"] = np.var(throttle)

            # Improvement suggestions
            improvement_suggestions = []

            if aggressiveness_score > 6:
                improvement_suggestions.append("Reduce aggressive acceleration and braking")

            if smoothness_score < 5:
                improvement_suggestions.append("Apply throttle and brake inputs more gradually")

            if efficiency_score < 5:
                improvement_suggestions.append("Maintain more consistent speeds")

            if consistency_score < 5:
                improvement_suggestions.append("Develop more consistent driving patterns")

            # Speed-specific suggestions
            if np.std(speed) > 15:
                improvement_suggestions.append("Reduce speed variations for better fuel economy")

            return DrivingStyle(
                aggressiveness_score=aggressiveness_score,
                smoothness_score=smoothness_score,
                efficiency_score=efficiency_score,
                consistency_score=consistency_score,
                driving_characteristics=driving_characteristics,
                improvement_suggestions=improvement_suggestions,
            )

        except Exception as e:
            self.logger.error(f"Error in driving style analysis: {e}")
            raise

    def create_dynamics_plots(
        self,
        g_force_analysis: Optional[GForceAnalysis] = None,
        attitude_analysis: Optional[AttitudeAnalysis] = None,
        driving_style: Optional[DrivingStyle] = None,
        title: str = "Vehicle Dynamics",
    ) -> Dict[str, go.Figure]:
        """
        Create comprehensive vehicle dynamics plots.

        Args:
            g_force_analysis: G-force analysis results
            attitude_analysis: Attitude analysis results
            driving_style: Driving style analysis results
            title: Base title for plots

        Returns:
            Dictionary of plot names -> plotly figures
        """
        try:
            plots = {}

            # 1. G-force analysis plots
            if g_force_analysis:
                # G-force profile over time
                fig_g_profile = go.Figure()

                fig_g_profile.add_trace(
                    go.Scatter(
                        x=g_force_analysis.g_force_profile["time"],
                        y=g_force_analysis.g_force_profile["longitudinal_g"],
                        mode="lines",
                        name="Longitudinal G",
                        line=dict(color="red"),
                    )
                )

                fig_g_profile.add_trace(
                    go.Scatter(
                        x=g_force_analysis.g_force_profile["time"],
                        y=g_force_analysis.g_force_profile["lateral_g"],
                        mode="lines",
                        name="Lateral G",
                        line=dict(color="blue"),
                    )
                )

                fig_g_profile.add_trace(
                    go.Scatter(
                        x=g_force_analysis.g_force_profile["time"],
                        y=g_force_analysis.g_force_profile["combined_g"],
                        mode="lines",
                        name="Combined G",
                        line=dict(color="green", width=2),
                    )
                )

                fig_g_profile.update_layout(
                    title=f"{title} - G-Force Profile",
                    xaxis_title="Time",
                    yaxis_title="G-Force",
                    legend=dict(x=0.02, y=0.98),
                )
                plots["g_force_profile"] = fig_g_profile

                # G-G diagram (lateral vs longitudinal)
                fig_gg = go.Figure()

                fig_gg.add_trace(
                    go.Scatter(
                        x=g_force_analysis.lateral_g,
                        y=g_force_analysis.longitudinal_g,
                        mode="markers",
                        name="G-G Plot",
                        marker=dict(
                            color=g_force_analysis.combined_g,
                            colorscale="Viridis",
                            colorbar=dict(title="Combined G"),
                            size=4,
                            opacity=0.7,
                        ),
                    )
                )

                # Add limit circles
                theta = np.linspace(0, 2 * np.pi, 100)
                for g_limit in [0.5, 1.0, 1.5]:
                    fig_gg.add_trace(
                        go.Scatter(
                            x=g_limit * np.cos(theta),
                            y=g_limit * np.sin(theta),
                            mode="lines",
                            name=f"{g_limit}g limit",
                            line=dict(dash="dash", color="gray"),
                            showlegend=g_limit == 1.0,
                        )
                    )

                fig_gg.update_layout(
                    title=f"{title} - G-G Diagram",
                    xaxis_title="Lateral G-Force",
                    yaxis_title="Longitudinal G-Force",
                    xaxis=dict(scaleanchor="y", scaleratio=1),
                    yaxis=dict(scaleanchor="x", scaleratio=1),
                )
                plots["g_g_diagram"] = fig_gg

            # 2. Attitude analysis plots
            if attitude_analysis:
                fig_attitude = make_subplots(
                    rows=3,
                    cols=1,
                    subplot_titles=["Pitch Angle", "Roll Angle", "Yaw Rate"],
                    vertical_spacing=0.1,
                )

                # Pitch
                fig_attitude.add_trace(
                    go.Scatter(
                        x=list(range(len(attitude_analysis.pitch_angle))),
                        y=attitude_analysis.pitch_angle,
                        mode="lines",
                        name="Pitch",
                        line=dict(color="red"),
                    ),
                    row=1,
                    col=1,
                )

                # Roll
                fig_attitude.add_trace(
                    go.Scatter(
                        x=list(range(len(attitude_analysis.roll_angle))),
                        y=attitude_analysis.roll_angle,
                        mode="lines",
                        name="Roll",
                        line=dict(color="blue"),
                    ),
                    row=2,
                    col=1,
                )

                # Yaw rate
                fig_attitude.add_trace(
                    go.Scatter(
                        x=list(range(len(attitude_analysis.yaw_rate))),
                        y=attitude_analysis.yaw_rate,
                        mode="lines",
                        name="Yaw Rate",
                        line=dict(color="green"),
                    ),
                    row=3,
                    col=1,
                )

                fig_attitude.update_xaxes(title_text="Time", row=3, col=1)
                fig_attitude.update_yaxes(title_text="Degrees", row=1, col=1)
                fig_attitude.update_yaxes(title_text="Degrees", row=2, col=1)
                fig_attitude.update_yaxes(title_text="deg/s", row=3, col=1)

                fig_attitude.update_layout(
                    title=f"{title} - Vehicle Attitude",
                    height=600,
                    showlegend=False,
                )
                plots["vehicle_attitude"] = fig_attitude

            # 3. Driving style radar chart
            if driving_style:
                categories = ["Aggressiveness", "Smoothness", "Efficiency", "Consistency"]
                values = [
                    driving_style.aggressiveness_score,
                    driving_style.smoothness_score,
                    driving_style.efficiency_score,
                    driving_style.consistency_score,
                ]

                fig_style = go.Figure()

                fig_style.add_trace(
                    go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill="toself",
                        name="Driving Style",
                        line_color="blue",
                    )
                )

                fig_style.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 10],
                        )
                    ),
                    title=f"{title} - Driving Style Analysis",
                    showlegend=False,
                )
                plots["driving_style"] = fig_style

            return plots

        except Exception as e:
            self.logger.error(f"Error creating dynamics plots: {e}")
            raise

    def _estimate_g_forces_from_speed(self, data: pd.DataFrame, speed_col: str) -> GForceAnalysis:
        """Estimate G-forces from speed data when IMU not available."""
        try:
            clean_data = data[data[speed_col].notna()].copy()
            speed_ms = clean_data[speed_col].values / 3.6  # Convert to m/s

            # Calculate acceleration from speed
            dt = 1.0  # Assume 1 second intervals
            acceleration_ms2 = np.diff(speed_ms) / dt

            # Convert to G-force
            g_constant = 9.80665
            longitudinal_g = acceleration_ms2 / g_constant

            # Assume no lateral acceleration data
            lateral_g = np.zeros_like(longitudinal_g)
            combined_g = np.abs(longitudinal_g)

            # Pad arrays to match original length
            longitudinal_g = np.append(longitudinal_g, longitudinal_g[-1])
            lateral_g = np.append(lateral_g, 0)
            combined_g = np.append(combined_g, combined_g[-1])

            # Calculate metrics
            max_longitudinal_g = np.max(np.abs(longitudinal_g))
            max_lateral_g = 0.0
            max_combined_g = np.max(combined_g)

            # Create profile
            g_force_profile = pd.DataFrame(
                {
                    "time": range(len(longitudinal_g)),
                    "longitudinal_g": longitudinal_g,
                    "lateral_g": lateral_g,
                    "vertical_g": np.zeros_like(longitudinal_g),
                    "combined_g": combined_g,
                }
            )

            # Distribution
            g_ranges = [(0, 0.3), (0.3, 0.6), (0.6, 0.9), (0.9, 1.2), (1.2, np.inf)]
            g_range_labels = ["low", "moderate", "high", "very_high", "extreme"]

            g_force_distribution = {}
            for (min_g, max_g), label in zip(g_ranges, g_range_labels):
                count = np.sum((combined_g >= min_g) & (combined_g < max_g))
                g_force_distribution[label] = count

            # Comfort rating
            comfort_rating = max(0, 1 - np.mean(combined_g))

            return GForceAnalysis(
                longitudinal_g=longitudinal_g,
                lateral_g=lateral_g,
                combined_g=combined_g,
                max_longitudinal_g=max_longitudinal_g,
                max_lateral_g=max_lateral_g,
                max_combined_g=max_combined_g,
                g_force_profile=g_force_profile,
                g_force_distribution=g_force_distribution,
                comfort_rating=comfort_rating,
            )

        except Exception as e:
            self.logger.error(f"Error estimating G-forces from speed: {e}")
            raise

    def generate_dynamics_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive vehicle dynamics analysis summary.

        Args:
            data: DataFrame with vehicle/IMU data

        Returns:
            Dictionary with all dynamics analysis results
        """
        try:
            results = {}

            # G-Force Analysis
            try:
                g_force_results = self.analyze_g_forces(data)
                results["g_force_analysis"] = g_force_results
            except Exception as e:
                self.logger.warning(f"G-force analysis failed: {e}")

            # Attitude Analysis
            try:
                attitude_results = self.analyze_vehicle_attitude(data)
                results["attitude_analysis"] = attitude_results
            except Exception as e:
                self.logger.warning(f"Attitude analysis failed: {e}")

            # Driving Style Analysis
            try:
                driving_style_results = self.analyze_driving_style(data)
                results["driving_style"] = driving_style_results
            except Exception as e:
                self.logger.warning(f"Driving style analysis failed: {e}")

            # Create plots
            plots = self.create_dynamics_plots(
                g_force_analysis=results.get("g_force_analysis"),
                attitude_analysis=results.get("attitude_analysis"),
                driving_style=results.get("driving_style"),
            )
            results["plots"] = plots

            return results

        except Exception as e:
            self.logger.error(f"Error generating dynamics summary: {e}")
            raise
