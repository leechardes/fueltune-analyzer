"""
Time Series Analysis Module for FuelTune.

Provides comprehensive time series analysis capabilities including
trend analysis, seasonality decomposition, autocorrelation, and
frequency domain analysis for automotive telemetry data.

Author: A04-ANALYSIS-SCIPY Agent
Created: 2025-01-02
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.signal import butter, filtfilt, find_peaks, welch
from scipy.stats import linregress
from sklearn.preprocessing import StandardScaler

from ..data.cache import cached_analysis as cache_result
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TrendAnalysisResults:
    """Results from trend analysis."""

    slope: float
    intercept: float
    r_value: float
    p_value: float
    std_err: float
    trend_strength: str  # 'strong', 'moderate', 'weak', 'none'
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    seasonal_component: bool
    detrended_data: np.ndarray


@dataclass
class SeasonalDecomposition:
    """Results from seasonal decomposition."""

    observed: np.ndarray
    trend: np.ndarray
    seasonal: np.ndarray
    residual: np.ndarray
    seasonal_strength: float
    trend_strength: float
    seasonal_period: Optional[int]


@dataclass
class AutocorrelationResults:
    """Results from autocorrelation analysis."""

    autocorr_values: np.ndarray
    lags: np.ndarray
    significant_lags: List[int]
    max_autocorr_lag: int
    max_autocorr_value: float
    ljung_box_stat: float
    ljung_box_p: float
    is_white_noise: bool


@dataclass
class FrequencyAnalysisResults:
    """Results from frequency domain analysis."""

    frequencies: np.ndarray
    power_spectral_density: np.ndarray
    dominant_frequencies: List[float]
    dominant_periods: List[float]
    total_power: float
    frequency_peaks: Dict[str, float]
    bandwidth_95: float  # 95% of power bandwidth


@dataclass
class ChangePointResults:
    """Results from change point detection."""

    change_points: List[int]
    change_point_scores: List[float]
    segments: List[Tuple[int, int]]
    segment_statistics: List[Dict[str, float]]


class TimeSeriesAnalyzer:
    """Advanced time series analysis for FuelTune telemetry data."""

    def __init__(self, sample_rate: float = 1.0):
        """
        Initialize time series analyzer.

        Args:
            sample_rate: Data sampling rate in Hz
        """
        self.sample_rate = sample_rate
        self.logger = logger

    def analyze(self, data: Union[pd.DataFrame, pd.Series]) -> Dict[str, Any]:
        """
        Standard analyze method for time series analysis.

        Args:
            data: Input time series data (DataFrame or Series)

        Returns:
            Dictionary with comprehensive time series analysis results
        """
        try:
            if isinstance(data, pd.DataFrame):
                # For DataFrame, analyze the first numeric column
                numeric_columns = data.select_dtypes(include=[np.number]).columns
                if len(numeric_columns) == 0:
                    raise ValueError("No numeric columns found in DataFrame")
                
                series_data = data[numeric_columns[0]]
            else:
                series_data = data
            
            # Perform comprehensive time series analysis
            trend_result = self.analyze_trend(series_data)
            autocorr_result = self.compute_autocorrelation(series_data)
            freq_result = self.analyze_frequency_domain(series_data)
            
            return {
                "trend_analysis": trend_result,
                "autocorrelation": autocorr_result,
                "frequency_analysis": freq_result,
                "data_length": len(series_data),
                "sample_rate": self.sample_rate,
            }
            
        except Exception as e:
            self.logger.error(f"Time series analysis failed: {e}")
            return {"error": str(e)}

    @cache_result("analysis", ttl=3600)
    def analyze_trend(
        self,
        data: Union[pd.Series, np.ndarray],
        timestamps: Optional[Union[pd.Series, np.ndarray]] = None,
    ) -> TrendAnalysisResults:
        """
        Analyze trend in time series data.

        Args:
            data: Time series data
            timestamps: Timestamps (if None, uses index)

        Returns:
            TrendAnalysisResults object
        """
        try:
            # Prepare data
            if isinstance(data, pd.Series):
                clean_data = data.dropna()
                if timestamps is None:
                    x = np.arange(len(clean_data))
                else:
                    timestamps = timestamps[clean_data.index]
                    x = np.arange(len(timestamps))
                y = clean_data.values
            else:
                # Remove NaN values
                mask = ~np.isnan(data)
                y = data[mask]
                if timestamps is None:
                    x = np.arange(len(y))
                else:
                    timestamps = np.array(timestamps)[mask]
                    x = np.arange(len(timestamps))

            if len(y) < 3:
                raise ValueError("Insufficient data for trend analysis")

            # Linear regression for trend
            slope, intercept, r_value, p_value, std_err = linregress(x, y)

            # Determine trend strength based on R-squared
            r_squared = r_value**2
            if r_squared > 0.7:
                trend_strength = "strong"
            elif r_squared > 0.3:
                trend_strength = "moderate"
            elif r_squared > 0.1:
                trend_strength = "weak"
            else:
                trend_strength = "none"

            # Determine trend direction
            if abs(slope) < np.std(y) * 0.01:  # Very small slope relative to data variation
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"

            # Detrend data
            trend_line = slope * x + intercept
            detrended_data = y - trend_line

            # Check for seasonal component using autocorrelation
            autocorr = np.correlate(detrended_data, detrended_data, mode="full")
            autocorr = autocorr[autocorr.size // 2 :]
            autocorr = autocorr / autocorr[0]  # Normalize

            # Look for significant autocorrelation beyond lag 1
            seasonal_component = np.any(np.abs(autocorr[10 : min(len(autocorr), 100)]) > 0.3)

            return TrendAnalysisResults(
                slope=slope,
                intercept=intercept,
                r_value=r_value,
                p_value=p_value,
                std_err=std_err,
                trend_strength=trend_strength,
                trend_direction=trend_direction,
                seasonal_component=seasonal_component,
                detrended_data=detrended_data,
            )

        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}")
            raise

    def decompose_seasonal(
        self,
        data: Union[pd.Series, np.ndarray],
        period: Optional[int] = None,
        model: str = "additive",
    ) -> SeasonalDecomposition:
        """
        Perform seasonal decomposition of time series.

        Args:
            data: Time series data
            period: Seasonal period (auto-detected if None)
            model: 'additive' or 'multiplicative'

        Returns:
            SeasonalDecomposition object
        """
        try:
            # Convert to pandas Series if needed
            if isinstance(data, np.ndarray):
                series = pd.Series(data)
            else:
                series = data.dropna()

            if len(series) < 10:
                raise ValueError("Insufficient data for seasonal decomposition")

            # Auto-detect period if not provided
            if period is None:
                period = self._detect_seasonal_period(series.values)

            if period is None or period >= len(series) // 2:
                # No clear seasonality, return simple trend decomposition
                trend = self._extract_trend(series.values)
                seasonal = np.zeros_like(series.values)
                residual = series.values - trend
                seasonal_strength = 0.0
            else:
                # Perform seasonal decomposition
                trend = self._extract_trend(series.values, period)
                seasonal = self._extract_seasonal(series.values, trend, period, model)
                residual = series.values - trend - seasonal
                seasonal_strength = np.var(seasonal) / np.var(series.values)

            trend_strength = np.var(trend) / np.var(series.values)

            return SeasonalDecomposition(
                observed=series.values,
                trend=trend,
                seasonal=seasonal,
                residual=residual,
                seasonal_strength=seasonal_strength,
                trend_strength=trend_strength,
                seasonal_period=period,
            )

        except Exception as e:
            self.logger.error(f"Error in seasonal decomposition: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def compute_autocorrelation(
        self, data: Union[pd.Series, np.ndarray], max_lags: Optional[int] = None
    ) -> AutocorrelationResults:
        """
        Compute autocorrelation function and related statistics.

        Args:
            data: Time series data
            max_lags: Maximum number of lags to compute

        Returns:
            AutocorrelationResults object
        """
        try:
            # Prepare data
            if isinstance(data, pd.Series):
                clean_data = data.dropna().values
            else:
                clean_data = data[~np.isnan(data)]

            if len(clean_data) < 10:
                raise ValueError("Insufficient data for autocorrelation analysis")

            # Set max_lags if not provided
            if max_lags is None:
                max_lags = min(len(clean_data) // 4, 100)

            # Compute autocorrelation
            autocorr_full = np.correlate(clean_data, clean_data, mode="full")
            mid = len(autocorr_full) // 2
            autocorr_values = autocorr_full[mid : mid + max_lags + 1]
            autocorr_values = autocorr_values / autocorr_values[0]  # Normalize

            lags = np.arange(len(autocorr_values))

            # Find significant lags (beyond 95% confidence interval)
            n = len(clean_data)
            confidence_interval = 1.96 / np.sqrt(n)
            significant_lags = []

            for i in range(1, len(autocorr_values)):
                if abs(autocorr_values[i]) > confidence_interval:
                    significant_lags.append(i)

            # Find maximum autocorrelation (excluding lag 0)
            if len(autocorr_values) > 1:
                max_autocorr_lag = np.argmax(np.abs(autocorr_values[1:])) + 1
                max_autocorr_value = autocorr_values[max_autocorr_lag]
            else:
                max_autocorr_lag = 0
                max_autocorr_value = 1.0

            # Ljung-Box test for white noise
            ljung_box_stat, ljung_box_p = self._ljung_box_test(clean_data, min(10, max_lags))
            is_white_noise = ljung_box_p > 0.05

            return AutocorrelationResults(
                autocorr_values=autocorr_values,
                lags=lags,
                significant_lags=significant_lags,
                max_autocorr_lag=max_autocorr_lag,
                max_autocorr_value=max_autocorr_value,
                ljung_box_stat=ljung_box_stat,
                ljung_box_p=ljung_box_p,
                is_white_noise=is_white_noise,
            )

        except Exception as e:
            self.logger.error(f"Error in autocorrelation analysis: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def analyze_frequency_domain(
        self, data: Union[pd.Series, np.ndarray], window: str = "hann"
    ) -> FrequencyAnalysisResults:
        """
        Analyze frequency domain characteristics using FFT and Welch's method.

        Args:
            data: Time series data
            window: Window function for spectral estimation

        Returns:
            FrequencyAnalysisResults object
        """
        try:
            # Prepare data
            if isinstance(data, pd.Series):
                clean_data = data.dropna().values
            else:
                clean_data = data[~np.isnan(data)]

            if len(clean_data) < 10:
                raise ValueError("Insufficient data for frequency analysis")

            # Detrend data
            clean_data = signal.detrend(clean_data)

            # Compute power spectral density using Welch's method
            frequencies, psd = welch(
                clean_data,
                fs=self.sample_rate,
                window=window,
                nperseg=min(256, len(clean_data) // 4),
                overlap=None,
            )

            # Remove DC component
            if frequencies[0] == 0:
                frequencies = frequencies[1:]
                psd = psd[1:]

            # Find dominant frequencies
            peaks, properties = find_peaks(psd, prominence=np.max(psd) * 0.1)
            dominant_frequencies = frequencies[peaks].tolist()
            dominant_periods = [1 / f if f > 0 else np.inf for f in dominant_frequencies]

            # Sort by power (descending)
            if len(peaks) > 0:
                peak_powers = psd[peaks]
                sorted_indices = np.argsort(peak_powers)[::-1]
                dominant_frequencies = [dominant_frequencies[i] for i in sorted_indices]
                dominant_periods = [dominant_periods[i] for i in sorted_indices]

            # Keep only top 5 dominant frequencies
            dominant_frequencies = dominant_frequencies[:5]
            dominant_periods = dominant_periods[:5]

            # Compute total power
            total_power = np.trapz(psd, frequencies)

            # Classify frequency peaks
            frequency_peaks = {}
            for i, freq in enumerate(dominant_frequencies):
                if freq < 0.1:
                    frequency_peaks[f"very_low_freq_{i+1}"] = freq
                elif freq < 1.0:
                    frequency_peaks[f"low_freq_{i+1}"] = freq
                elif freq < 10.0:
                    frequency_peaks[f"mid_freq_{i+1}"] = freq
                else:
                    frequency_peaks[f"high_freq_{i+1}"] = freq

            # Compute 95% power bandwidth
            cumulative_power = np.cumsum(psd) / np.sum(psd)
            bandwidth_95_idx = np.where(cumulative_power >= 0.95)[0]
            bandwidth_95 = (
                frequencies[bandwidth_95_idx[0]] if len(bandwidth_95_idx) > 0 else frequencies[-1]
            )

            return FrequencyAnalysisResults(
                frequencies=frequencies,
                power_spectral_density=psd,
                dominant_frequencies=dominant_frequencies,
                dominant_periods=dominant_periods,
                total_power=total_power,
                frequency_peaks=frequency_peaks,
                bandwidth_95=bandwidth_95,
            )

        except Exception as e:
            self.logger.error(f"Error in frequency domain analysis: {e}")
            raise

    def detect_change_points(
        self,
        data: Union[pd.Series, np.ndarray],
        method: str = "variance",
        min_segment_length: int = 10,
    ) -> ChangePointResults:
        """
        Detect change points in time series data.

        Args:
            data: Time series data
            method: Change point detection method ('variance', 'mean')
            min_segment_length: Minimum length of segments

        Returns:
            ChangePointResults object
        """
        try:
            # Prepare data
            if isinstance(data, pd.Series):
                clean_data = data.dropna().values
            else:
                clean_data = data[~np.isnan(data)]

            if len(clean_data) < 20:
                raise ValueError("Insufficient data for change point detection")

            change_points = []
            change_point_scores = []

            # Simple variance-based change point detection
            window_size = max(min_segment_length, len(clean_data) // 20)

            for i in range(window_size, len(clean_data) - window_size):
                left_segment = clean_data[i - window_size : i]
                right_segment = clean_data[i : i + window_size]

                if method == "variance":
                    left_var = np.var(left_segment)
                    right_var = np.var(right_segment)
                    score = abs(left_var - right_var) / (left_var + right_var + 1e-8)
                elif method == "mean":
                    left_mean = np.mean(left_segment)
                    right_mean = np.mean(right_segment)
                    pooled_std = np.sqrt((np.var(left_segment) + np.var(right_segment)) / 2)
                    score = abs(left_mean - right_mean) / (pooled_std + 1e-8)
                else:
                    raise ValueError(f"Unknown change point method: {method}")

                if score > 1.0:  # Threshold for significant change
                    change_points.append(i)
                    change_point_scores.append(score)

            # Remove nearby change points (keep only the one with highest score)
            if change_points:
                filtered_points = []
                filtered_scores = []

                i = 0
                while i < len(change_points):
                    # Find all points within min_segment_length
                    group_points = [change_points[i]]
                    group_scores = [change_point_scores[i]]

                    j = i + 1
                    while (
                        j < len(change_points)
                        and change_points[j] - change_points[i] < min_segment_length
                    ):
                        group_points.append(change_points[j])
                        group_scores.append(change_point_scores[j])
                        j += 1

                    # Keep point with highest score
                    best_idx = np.argmax(group_scores)
                    filtered_points.append(group_points[best_idx])
                    filtered_scores.append(group_scores[best_idx])

                    i = j

                change_points = filtered_points
                change_point_scores = filtered_scores

            # Create segments
            segments = []
            segment_starts = [0] + change_points
            segment_ends = change_points + [len(clean_data)]

            for start, end in zip(segment_starts, segment_ends):
                segments.append((start, end))

            # Compute segment statistics
            segment_statistics = []
            for start, end in segments:
                segment_data = clean_data[start:end]
                stats = {
                    "mean": float(np.mean(segment_data)),
                    "std": float(np.std(segment_data)),
                    "length": int(end - start),
                    "start_idx": int(start),
                    "end_idx": int(end),
                }
                segment_statistics.append(stats)

            return ChangePointResults(
                change_points=change_points,
                change_point_scores=change_point_scores,
                segments=segments,
                segment_statistics=segment_statistics,
            )

        except Exception as e:
            self.logger.error(f"Error in change point detection: {e}")
            raise

    def create_time_series_plots(
        self,
        data: Union[pd.Series, np.ndarray],
        timestamps: Optional[Union[pd.Series, np.ndarray]] = None,
        title: str = "Time Series Analysis",
    ) -> Dict[str, go.Figure]:
        """
        Create comprehensive time series plots.

        Args:
            data: Time series data
            timestamps: Timestamps
            title: Base title for plots

        Returns:
            Dictionary of plot names -> plotly figures
        """
        try:
            plots = {}

            # Prepare data
            if isinstance(data, pd.Series):
                clean_data = data.dropna()
                if timestamps is None:
                    timestamps = pd.Series(range(len(clean_data)), index=clean_data.index)
                else:
                    timestamps = timestamps[clean_data.index]
            else:
                mask = ~np.isnan(data)
                clean_data = pd.Series(data[mask])
                if timestamps is None:
                    timestamps = pd.Series(range(len(clean_data)))
                else:
                    timestamps = pd.Series(np.array(timestamps)[mask])

            # 1. Time series plot with trend
            trend_results = self.analyze_trend(clean_data, timestamps)

            fig_ts = go.Figure()
            fig_ts.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=clean_data,
                    mode="lines",
                    name="Data",
                    line=dict(color="blue", width=1),
                )
            )

            # Add trend line
            trend_line = trend_results.slope * np.arange(len(clean_data)) + trend_results.intercept
            fig_ts.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=trend_line,
                    mode="lines",
                    name=f"Trend (R²={trend_results.r_value**2:.3f})",
                    line=dict(color="red", width=2, dash="dash"),
                )
            )

            fig_ts.update_layout(
                title=f"{title} - Time Series with Trend",
                xaxis_title="Time",
                yaxis_title="Value",
                showlegend=True,
            )
            plots["time_series"] = fig_ts

            # 2. Seasonal decomposition plot
            decomposition = self.decompose_seasonal(clean_data)

            fig_decomp = make_subplots(
                rows=4,
                cols=1,
                subplot_titles=["Observed", "Trend", "Seasonal", "Residual"],
                shared_xaxes=True,
                vertical_spacing=0.08,
            )

            # Observed
            fig_decomp.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=decomposition.observed,
                    mode="lines",
                    name="Observed",
                    line=dict(color="blue"),
                ),
                row=1,
                col=1,
            )

            # Trend
            fig_decomp.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=decomposition.trend,
                    mode="lines",
                    name="Trend",
                    line=dict(color="red"),
                ),
                row=2,
                col=1,
            )

            # Seasonal
            fig_decomp.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=decomposition.seasonal,
                    mode="lines",
                    name="Seasonal",
                    line=dict(color="green"),
                ),
                row=3,
                col=1,
            )

            # Residual
            fig_decomp.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=decomposition.residual,
                    mode="lines",
                    name="Residual",
                    line=dict(color="orange"),
                ),
                row=4,
                col=1,
            )

            fig_decomp.update_layout(
                title=f"{title} - Seasonal Decomposition",
                height=800,
                showlegend=False,
            )
            plots["decomposition"] = fig_decomp

            # 3. Autocorrelation plot
            autocorr_results = self.compute_autocorrelation(clean_data)

            fig_autocorr = go.Figure()
            fig_autocorr.add_trace(
                go.Scatter(
                    x=autocorr_results.lags,
                    y=autocorr_results.autocorr_values,
                    mode="lines+markers",
                    name="Autocorrelation",
                    line=dict(color="blue"),
                )
            )

            # Add confidence bands
            n = len(clean_data)
            confidence_interval = 1.96 / np.sqrt(n)
            fig_autocorr.add_hline(
                y=confidence_interval,
                line_dash="dash",
                line_color="red",
                annotation_text="95% Confidence",
            )
            fig_autocorr.add_hline(
                y=-confidence_interval,
                line_dash="dash",
                line_color="red",
            )

            fig_autocorr.update_layout(
                title=f"{title} - Autocorrelation Function",
                xaxis_title="Lag",
                yaxis_title="Autocorrelation",
            )
            plots["autocorrelation"] = fig_autocorr

            # 4. Power spectral density plot
            freq_results = self.analyze_frequency_domain(clean_data)

            fig_psd = go.Figure()
            fig_psd.add_trace(
                go.Scatter(
                    x=freq_results.frequencies,
                    y=10 * np.log10(freq_results.power_spectral_density),  # Convert to dB
                    mode="lines",
                    name="Power Spectral Density",
                    line=dict(color="purple"),
                )
            )

            # Mark dominant frequencies
            for i, freq in enumerate(freq_results.dominant_frequencies[:3]):
                idx = np.argmin(np.abs(freq_results.frequencies - freq))
                psd_db = 10 * np.log10(freq_results.power_spectral_density[idx])
                fig_psd.add_trace(
                    go.Scatter(
                        x=[freq],
                        y=[psd_db],
                        mode="markers",
                        name=f"Peak {i+1} ({freq:.3f} Hz)",
                        marker=dict(size=10, color="red"),
                    )
                )

            fig_psd.update_layout(
                title=f"{title} - Power Spectral Density",
                xaxis_title="Frequency (Hz)",
                yaxis_title="PSD (dB)",
                xaxis_type="log" if max(freq_results.frequencies) > 10 else "linear",
            )
            plots["power_spectral_density"] = fig_psd

            return plots

        except Exception as e:
            self.logger.error(f"Error creating time series plots: {e}")
            raise

    def _detect_seasonal_period(self, data: np.ndarray) -> Optional[int]:
        """Detect seasonal period using autocorrelation."""
        try:
            if len(data) < 20:
                return None

            # Compute autocorrelation
            autocorr = np.correlate(data, data, mode="full")
            autocorr = autocorr[len(autocorr) // 2 :]
            autocorr = autocorr / autocorr[0]

            # Look for peaks in autocorrelation
            max_lag = min(len(data) // 4, 100)
            peaks, _ = find_peaks(autocorr[1:max_lag], height=0.3)

            if len(peaks) > 0:
                return peaks[0] + 1  # +1 because we started from index 1
            else:
                return None

        except Exception:
            return None

    def _extract_trend(self, data: np.ndarray, period: Optional[int] = None) -> np.ndarray:
        """Extract trend component using moving average."""
        if period is None:
            # Simple linear trend
            x = np.arange(len(data))
            slope, intercept = np.polyfit(x, data, 1)
            return slope * x + intercept
        else:
            # Moving average trend
            if period < 3:
                period = 3

            # Use centered moving average
            trend = np.full_like(data, np.nan)
            half_period = period // 2

            for i in range(half_period, len(data) - half_period):
                trend[i] = np.mean(data[i - half_period : i + half_period + 1])

            # Fill edges with linear extrapolation
            valid_indices = ~np.isnan(trend)
            if np.any(valid_indices):
                valid_trend = trend[valid_indices]
                valid_x = np.where(valid_indices)[0]

                # Fill beginning
                for i in range(half_period):
                    trend[i] = np.interp(i, valid_x, valid_trend)

                # Fill end
                for i in range(len(data) - half_period, len(data)):
                    trend[i] = np.interp(i, valid_x, valid_trend)

            return trend

    def _extract_seasonal(
        self, data: np.ndarray, trend: np.ndarray, period: int, model: str = "additive"
    ) -> np.ndarray:
        """Extract seasonal component."""
        if model == "additive":
            detrended = data - trend
        else:  # multiplicative
            detrended = data / (trend + 1e-8)

        seasonal = np.zeros_like(data)

        # Average over each seasonal position
        for i in range(period):
            indices = np.arange(i, len(data), period)
            if len(indices) > 1:
                seasonal_value = np.mean(detrended[indices])
                seasonal[indices] = seasonal_value

        # Center the seasonal component
        if model == "additive":
            seasonal = seasonal - np.mean(seasonal)

        return seasonal

    def _ljung_box_test(self, data: np.ndarray, lags: int) -> Tuple[float, float]:
        """Perform Ljung-Box test for autocorrelation."""
        try:
            from scipy.stats import chi2

            n = len(data)
            autocorr_full = np.correlate(data, data, mode="full")
            mid = len(autocorr_full) // 2
            autocorr = autocorr_full[mid + 1 : mid + lags + 1]
            autocorr = autocorr / autocorr_full[mid]

            # Ljung-Box statistic
            lb_stat = n * (n + 2) * np.sum([autocorr[i] ** 2 / (n - i - 1) for i in range(lags)])

            # p-value from chi-square distribution
            p_value = 1 - chi2.cdf(lb_stat, lags)

            return lb_stat, p_value

        except Exception:
            return np.nan, np.nan
