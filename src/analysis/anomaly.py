"""
Anomaly Detection Module for FuelTune.

Provides comprehensive anomaly detection capabilities using multiple
algorithms including statistical methods, clustering, and machine learning
approaches for automotive telemetry data.

Author: A04-ANALYSIS-SCIPY Agent
Created: 2025-01-02
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
from sklearn.cluster import DBSCAN
from sklearn.covariance import EllipticEnvelope
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from ..data.cache import cached_analysis as cache_result
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AnomalyResults:
    """Container for anomaly detection results."""

    anomaly_scores: np.ndarray
    anomaly_labels: np.ndarray  # 1 for normal, -1 for anomaly
    anomaly_indices: List[int]
    method: str
    threshold: float
    confidence: float
    n_anomalies: int
    anomaly_rate: float


@dataclass
class StatisticalAnomalies:
    """Results from statistical anomaly detection."""

    z_score_anomalies: List[int]
    iqr_anomalies: List[int]
    modified_z_score_anomalies: List[int]
    combined_anomalies: List[int]
    thresholds: Dict[str, float]


@dataclass
class ClusteringAnomalies:
    """Results from clustering-based anomaly detection."""

    cluster_labels: np.ndarray
    noise_points: List[int]  # DBSCAN noise points
    cluster_scores: np.ndarray
    outlier_clusters: List[int]
    dbscan_params: Dict[str, Any]


@dataclass
class TimeSeriesAnomalies:
    """Results from time series anomaly detection."""

    point_anomalies: List[int]
    contextual_anomalies: List[int]
    collective_anomalies: List[Tuple[int, int]]  # (start, end) indices
    seasonal_anomalies: List[int]
    trend_anomalies: List[int]


@dataclass
class MultiVariateAnomalies:
    """Results from multivariate anomaly detection."""

    mahalanobis_anomalies: List[int]
    elliptic_envelope_anomalies: List[int]
    pca_anomalies: List[int]
    reconstruction_errors: np.ndarray
    covariance_matrix: np.ndarray


class AnomalyDetector:
    """Advanced anomaly detection for FuelTune telemetry data."""

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        """
        Initialize anomaly detector.

        Args:
            contamination: Expected proportion of anomalies in data
            random_state: Random seed for reproducibility
        """
        self.contamination = contamination
        self.random_state = random_state
        self.logger = logger

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Standard analyze method for anomaly detection.

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with comprehensive anomaly analysis results
        """
        try:
            # Generate comprehensive summary
            return self.generate_anomaly_summary(data)
        except Exception as e:
            self.logger.error(f"Anomaly analysis failed: {e}")
            return {"error": str(e)}

    def detect_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Main method to detect anomalies using multiple techniques.

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with anomaly detection results
        """
        results = {"anomalies": [], "scores": [], "methods_used": []}

        # Try statistical anomalies
        try:
            stat_result = self.detect_statistical_anomalies(data)
            results["anomalies"].extend(stat_result.get("anomalies", []))
            results["methods_used"].append("statistical")
        except Exception as e:
            self.logger.warning(f"Statistical detection failed: {e}")

        # Try isolation forest
        try:
            iso_result = self.detect_isolation_forest_anomalies(data)
            results["anomalies"].extend(iso_result.anomaly_scores.tolist())
            results["methods_used"].append("isolation_forest")
        except Exception as e:
            self.logger.warning(f"Isolation forest detection failed: {e}")

        return results

    @cache_result("analysis", ttl=3600)
    def detect_isolation_forest_anomalies(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        n_estimators: int = 100,
    ) -> AnomalyResults:
        """
        Detect anomalies using Isolation Forest algorithm.

        Args:
            data: Input data (multivariate)
            n_estimators: Number of trees in the forest

        Returns:
            AnomalyResults object
        """
        try:
            # Prepare data
            if isinstance(data, pd.DataFrame):
                X = data.select_dtypes(include=[np.number]).fillna(data.median())
            else:
                X = np.array(data)
                if len(X.shape) == 1:
                    X = X.reshape(-1, 1)

            if X.shape[0] < 10:
                raise ValueError("Insufficient data for Isolation Forest")

            # Standardize data
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Fit Isolation Forest
            iso_forest = IsolationForest(
                contamination=self.contamination,
                n_estimators=n_estimators,
                random_state=self.random_state,
                n_jobs=-1,
            )

            # Predict anomalies
            anomaly_labels = iso_forest.fit_predict(X_scaled)
            anomaly_scores = iso_forest.score_samples(X_scaled)

            # Get anomaly indices
            anomaly_indices = np.where(anomaly_labels == -1)[0].tolist()

            # Calculate statistics
            n_anomalies = len(anomaly_indices)
            anomaly_rate = n_anomalies / len(X)

            # Estimate threshold from scores
            threshold = np.percentile(anomaly_scores, self.contamination * 100)

            return AnomalyResults(
                anomaly_scores=anomaly_scores,
                anomaly_labels=anomaly_labels,
                anomaly_indices=anomaly_indices,
                method="Isolation Forest",
                threshold=threshold,
                confidence=0.95,  # Default confidence
                n_anomalies=n_anomalies,
                anomaly_rate=anomaly_rate,
            )

        except Exception as e:
            self.logger.error(f"Error in Isolation Forest anomaly detection: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def detect_lof_anomalies(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        n_neighbors: int = 20,
    ) -> AnomalyResults:
        """
        Detect anomalies using Local Outlier Factor (LOF).

        Args:
            data: Input data (multivariate)
            n_neighbors: Number of neighbors for LOF

        Returns:
            AnomalyResults object
        """
        try:
            # Prepare data
            if isinstance(data, pd.DataFrame):
                X = data.select_dtypes(include=[np.number]).fillna(data.median())
            else:
                X = np.array(data)
                if len(X.shape) == 1:
                    X = X.reshape(-1, 1)

            if X.shape[0] < max(n_neighbors + 1, 10):
                raise ValueError("Insufficient data for LOF")

            # Standardize data
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Fit LOF
            lof = LocalOutlierFactor(
                n_neighbors=n_neighbors,
                contamination=self.contamination,
                n_jobs=-1,
            )

            # Predict anomalies
            anomaly_labels = lof.fit_predict(X_scaled)
            anomaly_scores = lof.negative_outlier_factor_

            # Get anomaly indices
            anomaly_indices = np.where(anomaly_labels == -1)[0].tolist()

            # Calculate statistics
            n_anomalies = len(anomaly_indices)
            anomaly_rate = n_anomalies / len(X)

            # Estimate threshold
            threshold = np.percentile(anomaly_scores, self.contamination * 100)

            return AnomalyResults(
                anomaly_scores=anomaly_scores,
                anomaly_labels=anomaly_labels,
                anomaly_indices=anomaly_indices,
                method="Local Outlier Factor",
                threshold=threshold,
                confidence=0.95,
                n_anomalies=n_anomalies,
                anomaly_rate=anomaly_rate,
            )

        except Exception as e:
            self.logger.error(f"Error in LOF anomaly detection: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def detect_statistical_anomalies(
        self, data: Union[pd.Series, np.ndarray], z_threshold: float = 3.0
    ) -> StatisticalAnomalies:
        """
        Detect anomalies using statistical methods (Z-score, IQR, Modified Z-score).

        Args:
            data: Input data (univariate)
            z_threshold: Z-score threshold for anomaly detection

        Returns:
            StatisticalAnomalies object
        """
        try:
            # Convert to numpy array and remove NaN
            if isinstance(data, pd.Series):
                clean_data = data.dropna().values
                original_indices = data.dropna().index.tolist()
            else:
                clean_data = data[~np.isnan(data)]
                original_indices = list(range(len(clean_data)))

            if len(clean_data) < 10:
                raise ValueError("Insufficient data for statistical anomaly detection")

            # 1. Z-score method
            z_scores = np.abs(stats.zscore(clean_data))
            z_score_anomalies = [
                original_indices[i] for i, z in enumerate(z_scores) if z > z_threshold
            ]

            # 2. IQR method
            q1 = np.percentile(clean_data, 25)
            q3 = np.percentile(clean_data, 75)
            iqr = q3 - q1
            iqr_lower = q1 - 1.5 * iqr
            iqr_upper = q3 + 1.5 * iqr
            iqr_anomalies = [
                original_indices[i]
                for i, val in enumerate(clean_data)
                if val < iqr_lower or val > iqr_upper
            ]

            # 3. Modified Z-score method (using median)
            median = np.median(clean_data)
            mad = np.median(np.abs(clean_data - median))
            modified_z_scores = (
                0.6745 * (clean_data - median) / mad if mad != 0 else np.zeros_like(clean_data)
            )
            modified_z_score_anomalies = [
                original_indices[i]
                for i, z in enumerate(modified_z_scores)
                if np.abs(z) > z_threshold
            ]

            # Combined anomalies (union of all methods)
            combined_anomalies = list(
                set(z_score_anomalies + iqr_anomalies + modified_z_score_anomalies)
            )

            # Thresholds used
            thresholds = {
                "z_score": z_threshold,
                "iqr_lower": iqr_lower,
                "iqr_upper": iqr_upper,
                "modified_z_score": z_threshold,
            }

            return StatisticalAnomalies(
                z_score_anomalies=z_score_anomalies,
                iqr_anomalies=iqr_anomalies,
                modified_z_score_anomalies=modified_z_score_anomalies,
                combined_anomalies=combined_anomalies,
                thresholds=thresholds,
            )

        except Exception as e:
            self.logger.error(f"Error in statistical anomaly detection: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def detect_clustering_anomalies(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        eps: float = 0.5,
        min_samples: int = 5,
    ) -> ClusteringAnomalies:
        """
        Detect anomalies using DBSCAN clustering.

        Args:
            data: Input data (multivariate)
            eps: DBSCAN epsilon parameter
            min_samples: DBSCAN minimum samples parameter

        Returns:
            ClusteringAnomalies object
        """
        try:
            # Prepare data
            if isinstance(data, pd.DataFrame):
                X = data.select_dtypes(include=[np.number]).fillna(data.median())
            else:
                X = np.array(data)
                if len(X.shape) == 1:
                    X = X.reshape(-1, 1)

            if X.shape[0] < min_samples * 2:
                raise ValueError("Insufficient data for DBSCAN clustering")

            # Standardize data
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Fit DBSCAN
            dbscan = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1)
            cluster_labels = dbscan.fit_predict(X_scaled)

            # Noise points (label = -1) are considered anomalies
            noise_points = np.where(cluster_labels == -1)[0].tolist()

            # Compute cluster scores (distance to cluster center)
            cluster_scores = np.zeros(len(X))
            unique_clusters = np.unique(cluster_labels[cluster_labels != -1])

            for cluster_id in unique_clusters:
                cluster_mask = cluster_labels == cluster_id
                if np.any(cluster_mask):
                    cluster_center = np.mean(X_scaled[cluster_mask], axis=0)
                    distances = np.linalg.norm(X_scaled[cluster_mask] - cluster_center, axis=1)
                    cluster_scores[cluster_mask] = distances

            # Set high scores for noise points
            cluster_scores[cluster_labels == -1] = np.max(cluster_scores) + 1

            # Identify outlier clusters (very small clusters)
            cluster_sizes = {
                cluster_id: np.sum(cluster_labels == cluster_id) for cluster_id in unique_clusters
            }
            min_cluster_size = max(min_samples, len(X) * 0.02)  # At least 2% of data
            outlier_clusters = [
                cluster_id for cluster_id, size in cluster_sizes.items() if size < min_cluster_size
            ]

            return ClusteringAnomalies(
                cluster_labels=cluster_labels,
                noise_points=noise_points,
                cluster_scores=cluster_scores,
                outlier_clusters=outlier_clusters,
                dbscan_params={"eps": eps, "min_samples": min_samples},
            )

        except Exception as e:
            self.logger.error(f"Error in clustering anomaly detection: {e}")
            raise

    def detect_multivariate_anomalies(
        self, data: Union[pd.DataFrame, np.ndarray]
    ) -> MultiVariateAnomalies:
        """
        Detect multivariate anomalies using multiple methods.

        Args:
            data: Input data (multivariate)

        Returns:
            MultiVariateAnomalies object
        """
        try:
            # Prepare data
            if isinstance(data, pd.DataFrame):
                X = data.select_dtypes(include=[np.number]).fillna(data.median())
            else:
                X = pd.DataFrame(data).fillna(pd.DataFrame(data).median())

            if X.shape[0] < 10 or X.shape[1] < 2:
                raise ValueError("Insufficient data for multivariate anomaly detection")

            # Standardize data
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # 1. Mahalanobis distance method
            try:
                cov_matrix = np.cov(X_scaled.T)
                inv_cov_matrix = np.linalg.pinv(cov_matrix)
                mean = np.mean(X_scaled, axis=0)

                mahalanobis_distances = []
                for i in range(len(X_scaled)):
                    diff = X_scaled[i] - mean
                    md = np.sqrt(diff.T @ inv_cov_matrix @ diff)
                    mahalanobis_distances.append(md)

                mahalanobis_distances = np.array(mahalanobis_distances)
                threshold_md = np.percentile(mahalanobis_distances, (1 - self.contamination) * 100)
                mahalanobis_anomalies = np.where(mahalanobis_distances > threshold_md)[0].tolist()

            except Exception as e:
                self.logger.warning(f"Mahalanobis distance failed: {e}")
                mahalanobis_anomalies = []
                cov_matrix = np.eye(X_scaled.shape[1])

            # 2. Elliptic Envelope method
            try:
                elliptic_env = EllipticEnvelope(
                    contamination=self.contamination,
                    random_state=self.random_state,
                )
                elliptic_labels = elliptic_env.fit_predict(X_scaled)
                elliptic_envelope_anomalies = np.where(elliptic_labels == -1)[0].tolist()

            except Exception as e:
                self.logger.warning(f"Elliptic Envelope failed: {e}")
                elliptic_envelope_anomalies = []

            # 3. PCA reconstruction error method
            try:
                # Use PCA to reduce dimensionality
                n_components = min(X_scaled.shape[1] - 1, max(1, X_scaled.shape[1] // 2))
                pca = PCA(n_components=n_components, random_state=self.random_state)
                X_pca = pca.fit_transform(X_scaled)
                X_reconstructed = pca.inverse_transform(X_pca)

                # Compute reconstruction errors
                reconstruction_errors = np.sum((X_scaled - X_reconstructed) ** 2, axis=1)
                threshold_pca = np.percentile(reconstruction_errors, (1 - self.contamination) * 100)
                pca_anomalies = np.where(reconstruction_errors > threshold_pca)[0].tolist()

            except Exception as e:
                self.logger.warning(f"PCA reconstruction failed: {e}")
                pca_anomalies = []
                reconstruction_errors = np.zeros(len(X_scaled))

            return MultiVariateAnomalies(
                mahalanobis_anomalies=mahalanobis_anomalies,
                elliptic_envelope_anomalies=elliptic_envelope_anomalies,
                pca_anomalies=pca_anomalies,
                reconstruction_errors=reconstruction_errors,
                covariance_matrix=cov_matrix,
            )

        except Exception as e:
            self.logger.error(f"Error in multivariate anomaly detection: {e}")
            raise

    def detect_time_series_anomalies(
        self,
        data: Union[pd.Series, np.ndarray],
        timestamps: Optional[Union[pd.Series, np.ndarray]] = None,
        window_size: int = 50,
    ) -> TimeSeriesAnomalies:
        """
        Detect time series specific anomalies.

        Args:
            data: Time series data
            timestamps: Optional timestamps
            window_size: Window size for analysis

        Returns:
            TimeSeriesAnomalies object
        """
        try:
            # Convert to pandas Series if needed
            if isinstance(data, np.ndarray):
                series = pd.Series(data)
            else:
                series = data.dropna()

            if len(series) < window_size:
                raise ValueError("Insufficient data for time series anomaly detection")

            point_anomalies = []
            contextual_anomalies = []
            collective_anomalies = []
            seasonal_anomalies = []
            trend_anomalies = []

            # 1. Point anomalies using rolling statistics
            rolling_mean = series.rolling(window=window_size, center=True).mean()
            rolling_std = series.rolling(window=window_size, center=True).std()

            # Z-score based on local statistics
            local_z_scores = np.abs((series - rolling_mean) / rolling_std)
            point_anomalies = series.index[local_z_scores > 3].tolist()

            # 2. Contextual anomalies (seasonal)
            if len(series) > window_size * 4:
                try:
                    # Simple seasonal decomposition
                    seasonal_period = min(window_size, len(series) // 4)
                    seasonal_component = np.zeros_like(series)

                    for i in range(seasonal_period):
                        seasonal_indices = np.arange(i, len(series), seasonal_period)
                        if len(seasonal_indices) > 1:
                            seasonal_mean = np.mean(series.iloc[seasonal_indices])
                            seasonal_component[seasonal_indices] = seasonal_mean

                    seasonal_residuals = series - seasonal_component
                    seasonal_threshold = 3 * np.std(seasonal_residuals)
                    seasonal_anomalies = series.index[
                        np.abs(seasonal_residuals) > seasonal_threshold
                    ].tolist()

                except Exception as e:
                    self.logger.warning(f"Seasonal anomaly detection failed: {e}")

            # 3. Collective anomalies (consecutive unusual patterns)
            try:
                # Look for consecutive points that deviate from trend
                diff_series = series.diff().fillna(0)
                rolling_diff_mean = diff_series.rolling(window=window_size // 2).mean()
                rolling_diff_std = diff_series.rolling(window=window_size // 2).std()

                diff_z_scores = np.abs((diff_series - rolling_diff_mean) / rolling_diff_std)
                unusual_points = diff_z_scores > 2

                # Find consecutive unusual patterns
                collective_start = None
                for i, is_unusual in enumerate(unusual_points):
                    if is_unusual and collective_start is None:
                        collective_start = i
                    elif not is_unusual and collective_start is not None:
                        if i - collective_start >= 3:  # At least 3 consecutive points
                            collective_anomalies.append((collective_start, i - 1))
                        collective_start = None

            except Exception as e:
                self.logger.warning(f"Collective anomaly detection failed: {e}")

            # 4. Trend anomalies
            try:
                # Detect sudden trend changes using rolling regression slopes
                slopes = []
                for i in range(len(series) - window_size + 1):
                    y_window = series.iloc[i : i + window_size].values
                    x_window = np.arange(len(y_window))
                    slope = np.polyfit(x_window, y_window, 1)[0]
                    slopes.append(slope)

                slopes = np.array(slopes)
                slope_changes = np.abs(np.diff(slopes))
                trend_change_threshold = np.percentile(slope_changes, 95)

                trend_change_points = np.where(slope_changes > trend_change_threshold)[0]
                trend_anomalies = [i + window_size // 2 for i in trend_change_points]

            except Exception as e:
                self.logger.warning(f"Trend anomaly detection failed: {e}")

            return TimeSeriesAnomalies(
                point_anomalies=point_anomalies,
                contextual_anomalies=contextual_anomalies,
                collective_anomalies=collective_anomalies,
                seasonal_anomalies=seasonal_anomalies,
                trend_anomalies=trend_anomalies,
            )

        except Exception as e:
            self.logger.error(f"Error in time series anomaly detection: {e}")
            raise

    def create_anomaly_plots(
        self,
        data: Union[pd.DataFrame, pd.Series],
        anomaly_results: Union[AnomalyResults, StatisticalAnomalies, TimeSeriesAnomalies],
        title: str = "Anomaly Detection",
    ) -> Dict[str, go.Figure]:
        """
        Create comprehensive anomaly detection plots.

        Args:
            data: Original data
            anomaly_results: Anomaly detection results
            title: Base title for plots

        Returns:
            Dictionary of plot names -> plotly figures
        """
        try:
            plots = {}

            if isinstance(anomaly_results, AnomalyResults):
                # 1. Anomaly score plot
                fig_scores = go.Figure()

                if isinstance(data, pd.Series):
                    x_axis = data.index
                else:
                    x_axis = range(len(data))

                # Plot anomaly scores
                fig_scores.add_trace(
                    go.Scatter(
                        x=x_axis,
                        y=anomaly_results.anomaly_scores,
                        mode="lines+markers",
                        name="Anomaly Score",
                        line=dict(color="blue"),
                        marker=dict(size=4),
                    )
                )

                # Highlight anomalies
                if anomaly_results.anomaly_indices:
                    anomaly_x = [x_axis[i] for i in anomaly_results.anomaly_indices]
                    anomaly_y = [
                        anomaly_results.anomaly_scores[i] for i in anomaly_results.anomaly_indices
                    ]

                    fig_scores.add_trace(
                        go.Scatter(
                            x=anomaly_x,
                            y=anomaly_y,
                            mode="markers",
                            name="Anomalies",
                            marker=dict(color="red", size=8, symbol="circle-open"),
                        )
                    )

                # Add threshold line
                fig_scores.add_hline(
                    y=anomaly_results.threshold,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Threshold ({anomaly_results.threshold:.3f})",
                )

                fig_scores.update_layout(
                    title=f"{title} - {anomaly_results.method} Scores",
                    xaxis_title="Index",
                    yaxis_title="Anomaly Score",
                )
                plots["anomaly_scores"] = fig_scores

                # 2. Data with anomalies highlighted (for time series)
                if isinstance(data, pd.Series):
                    fig_data = go.Figure()

                    # Plot original data
                    fig_data.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data.values,
                            mode="lines",
                            name="Data",
                            line=dict(color="blue"),
                        )
                    )

                    # Highlight anomalies
                    if anomaly_results.anomaly_indices:
                        anomaly_data_x = [data.index[i] for i in anomaly_results.anomaly_indices]
                        anomaly_data_y = [data.iloc[i] for i in anomaly_results.anomaly_indices]

                        fig_data.add_trace(
                            go.Scatter(
                                x=anomaly_data_x,
                                y=anomaly_data_y,
                                mode="markers",
                                name="Anomalies",
                                marker=dict(color="red", size=8, symbol="circle-open"),
                            )
                        )

                    fig_data.update_layout(
                        title=f"{title} - Data with Anomalies",
                        xaxis_title="Index",
                        yaxis_title="Value",
                    )
                    plots["data_with_anomalies"] = fig_data

            elif isinstance(anomaly_results, StatisticalAnomalies):
                # Statistical anomalies plot
                if isinstance(data, pd.Series):
                    fig_stat = go.Figure()

                    # Plot data
                    fig_stat.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data.values,
                            mode="lines+markers",
                            name="Data",
                            line=dict(color="blue"),
                            marker=dict(size=4),
                        )
                    )

                    # Highlight different types of anomalies
                    anomaly_types = [
                        ("Z-Score", anomaly_results.z_score_anomalies, "red"),
                        ("IQR", anomaly_results.iqr_anomalies, "orange"),
                        ("Modified Z-Score", anomaly_results.modified_z_score_anomalies, "purple"),
                    ]

                    for anomaly_type, anomaly_indices, color in anomaly_types:
                        if anomaly_indices:
                            anomaly_x = [data.index[i] for i in anomaly_indices if i < len(data)]
                            anomaly_y = [data.iloc[i] for i in anomaly_indices if i < len(data)]

                            fig_stat.add_trace(
                                go.Scatter(
                                    x=anomaly_x,
                                    y=anomaly_y,
                                    mode="markers",
                                    name=f"{anomaly_type} Anomalies",
                                    marker=dict(color=color, size=8, symbol="circle-open"),
                                )
                            )

                    fig_stat.update_layout(
                        title=f"{title} - Statistical Anomaly Detection",
                        xaxis_title="Index",
                        yaxis_title="Value",
                    )
                    plots["statistical_anomalies"] = fig_stat

            elif isinstance(anomaly_results, TimeSeriesAnomalies):
                # Time series anomalies plot
                if isinstance(data, pd.Series):
                    fig_ts = go.Figure()

                    # Plot data
                    fig_ts.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data.values,
                            mode="lines",
                            name="Data",
                            line=dict(color="blue"),
                        )
                    )

                    # Highlight different types of anomalies
                    anomaly_types = [
                        ("Point", anomaly_results.point_anomalies, "red", "circle-open"),
                        ("Seasonal", anomaly_results.seasonal_anomalies, "orange", "square-open"),
                        ("Trend", anomaly_results.trend_anomalies, "purple", "diamond-open"),
                    ]

                    for anomaly_type, anomaly_indices, color, symbol in anomaly_types:
                        if anomaly_indices:
                            # Filter valid indices
                            valid_indices = [i for i in anomaly_indices if i < len(data)]
                            if valid_indices:
                                anomaly_x = [data.index[i] for i in valid_indices]
                                anomaly_y = [data.iloc[i] for i in valid_indices]

                                fig_ts.add_trace(
                                    go.Scatter(
                                        x=anomaly_x,
                                        y=anomaly_y,
                                        mode="markers",
                                        name=f"{anomaly_type} Anomalies",
                                        marker=dict(color=color, size=8, symbol=symbol),
                                    )
                                )

                    # Highlight collective anomalies as shapes
                    for start, end in anomaly_results.collective_anomalies:
                        if start < len(data) and end < len(data):
                            fig_ts.add_vrect(
                                x0=data.index[start],
                                x1=data.index[end],
                                fillcolor="yellow",
                                opacity=0.3,
                                layer="below",
                                line_width=0,
                            )

                    fig_ts.update_layout(
                        title=f"{title} - Time Series Anomaly Detection",
                        xaxis_title="Time",
                        yaxis_title="Value",
                    )
                    plots["time_series_anomalies"] = fig_ts

            return plots

        except Exception as e:
            self.logger.error(f"Error creating anomaly plots: {e}")
            raise

    def generate_anomaly_summary(self, data: Union[pd.DataFrame, pd.Series]) -> Dict[str, Any]:
        """
        Generate comprehensive anomaly detection summary.

        Args:
            data: Input data

        Returns:
            Dictionary with all anomaly analysis results
        """
        try:
            results = {}

            # Apply different methods based on data type
            if isinstance(data, pd.Series):
                # Univariate analysis
                statistical = self.detect_statistical_anomalies(data)
                time_series = self.detect_time_series_anomalies(data)

                # Convert to DataFrame for multivariate methods
                data_df = data.to_frame()
                isolation_forest = self.detect_isolation_forest_anomalies(data_df)
                lof = self.detect_lof_anomalies(data_df)

                results["statistical"] = statistical
                results["time_series"] = time_series
                results["isolation_forest"] = isolation_forest
                results["lof"] = lof

                # Create plots
                plots = {}
                plots.update(self.create_anomaly_plots(data, statistical, "Statistical"))
                plots.update(self.create_anomaly_plots(data, time_series, "Time Series"))
                plots.update(self.create_anomaly_plots(data, isolation_forest, "Isolation Forest"))
                results["plots"] = plots

            else:
                # Multivariate analysis
                isolation_forest = self.detect_isolation_forest_anomalies(data)
                lof = self.detect_lof_anomalies(data)
                clustering = self.detect_clustering_anomalies(data)
                multivariate = self.detect_multivariate_anomalies(data)

                results["isolation_forest"] = isolation_forest
                results["lof"] = lof
                results["clustering"] = clustering
                results["multivariate"] = multivariate

                # Create plots for the first column if it exists
                if not data.empty and len(data.columns) > 0:
                    first_col = data.iloc[:, 0]
                    plots = self.create_anomaly_plots(first_col, isolation_forest, "Multivariate")
                    results["plots"] = plots

            # Summary statistics
            all_anomalies = set()

            for key, value in results.items():
                if key != "plots":
                    if hasattr(value, "anomaly_indices"):
                        all_anomalies.update(value.anomaly_indices)
                    elif hasattr(value, "combined_anomalies"):
                        all_anomalies.update(value.combined_anomalies)
                    elif hasattr(value, "noise_points"):
                        all_anomalies.update(value.noise_points)

            total_points = len(data)
            results["summary"] = {
                "total_data_points": total_points,
                "unique_anomalies": len(all_anomalies),
                "anomaly_rate": len(all_anomalies) / total_points if total_points > 0 else 0,
                "methods_applied": len(
                    [k for k in results.keys() if k != "plots" and k != "summary"]
                ),
            }

            return results

        except Exception as e:
            self.logger.error(f"Error generating anomaly summary: {e}")
            raise
