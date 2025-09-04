"""
Advanced Correlation Analysis Module for FuelTune.

Provides comprehensive correlation analysis capabilities including
Pearson, Spearman, and partial correlation, feature importance,
and causal analysis for automotive telemetry data.

Author: A04-ANALYSIS-SCIPY Agent
Created: 2025-01-02
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
from scipy.linalg import pinv
from scipy.stats import pearsonr, spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from ..data.cache import cached_analysis as cache_result
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CorrelationMatrix:
    """Container for correlation matrix results."""

    correlation_matrix: pd.DataFrame
    p_values: pd.DataFrame
    significant_pairs: List[Tuple[str, str, float, float]]  # var1, var2, corr, p_value
    method: str
    sample_size: int


@dataclass
class PartialCorrelationResults:
    """Results from partial correlation analysis."""

    partial_corr_matrix: pd.DataFrame
    control_variables: List[str]
    significant_partial_correlations: List[Tuple[str, str, float]]


@dataclass
class FeatureImportanceResults:
    """Results from feature importance analysis."""

    feature_scores: pd.DataFrame  # feature, importance, rank
    method: str
    target_variable: str
    top_features: List[str]


@dataclass
class CausalAnalysisResults:
    """Results from causal analysis."""

    granger_results: Dict[str, Dict[str, Tuple[float, float]]]  # cause -> effect -> (stat, p)
    causal_graph: Dict[str, List[str]]  # variable -> list of variables it causes
    causal_strength: Dict[Tuple[str, str], float]


@dataclass
class CrossCorrelationResults:
    """Results from cross-correlation analysis."""

    max_correlation: float
    optimal_lag: int
    correlation_function: np.ndarray
    lags: np.ndarray
    confidence_interval: float


class CorrelationAnalyzer:
    """Advanced correlation analysis for FuelTune telemetry data."""

    def __init__(self, significance_level: float = 0.05):
        """
        Initialize correlation analyzer.

        Args:
            significance_level: Statistical significance level
        """
        self.significance_level = significance_level
        self.logger = logger

    def get_correlation_matrix(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Get correlation matrix for the data.

        Args:
            data: Input DataFrame

        Returns:
            Correlation matrix as DataFrame
        """
        try:
            numeric_data = data.select_dtypes(include=[np.number])
            return numeric_data.corr()
        except Exception as e:
            self.logger.warning(f"Error computing correlation matrix: {e}")
            return pd.DataFrame()

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Standard analyze method for correlation analysis.

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with comprehensive correlation analysis results
        """
        try:
            # Generate comprehensive summary
            return self.generate_correlation_summary(data)
        except Exception as e:
            self.logger.error(f"Correlation analysis failed: {e}")
            return {"error": str(e)}

    @cache_result("analysis", ttl=3600)
    def compute_correlation_matrix(
        self,
        data: pd.DataFrame,
        method: str = "pearson",
        min_periods: int = 30,
    ) -> CorrelationMatrix:
        """
        Compute correlation matrix with significance testing.

        Args:
            data: DataFrame with numerical columns
            method: Correlation method ('pearson', 'spearman', 'kendall')
            min_periods: Minimum number of observations for correlation

        Returns:
            CorrelationMatrix object
        """
        try:
            # Remove non-numeric columns
            numeric_data = data.select_dtypes(include=[np.number])

            if numeric_data.empty:
                raise ValueError("No numeric columns found in data")

            # Remove columns with too few observations
            valid_columns = []
            for col in numeric_data.columns:
                if numeric_data[col].notna().sum() >= min_periods:
                    valid_columns.append(col)

            if len(valid_columns) < 2:
                raise ValueError("Insufficient valid columns for correlation analysis")

            numeric_data = numeric_data[valid_columns]

            # Compute correlation matrix
            if method == "pearson":
                corr_matrix = numeric_data.corr(method="pearson")
            elif method == "spearman":
                corr_matrix = numeric_data.corr(method="spearman")
            elif method == "kendall":
                corr_matrix = numeric_data.corr(method="kendall")
            else:
                raise ValueError(f"Unknown correlation method: {method}")

            # Compute p-values
            p_values = pd.DataFrame(np.nan, index=corr_matrix.index, columns=corr_matrix.columns)

            significant_pairs = []

            for i, col1 in enumerate(corr_matrix.columns):
                for j, col2 in enumerate(corr_matrix.columns):
                    if i < j:  # Only upper triangle
                        # Get clean data for both variables
                        mask = numeric_data[[col1, col2]].notna().all(axis=1)
                        clean_data = numeric_data.loc[mask, [col1, col2]]

                        if len(clean_data) >= min_periods:
                            if method == "pearson":
                                corr_val, p_val = pearsonr(clean_data[col1], clean_data[col2])
                            elif method == "spearman":
                                corr_val, p_val = spearmanr(clean_data[col1], clean_data[col2])
                            elif method == "kendall":
                                corr_val, p_val = stats.kendalltau(
                                    clean_data[col1], clean_data[col2]
                                )

                            p_values.loc[col1, col2] = p_val
                            p_values.loc[col2, col1] = p_val

                            # Check significance
                            if p_val < self.significance_level and abs(corr_val) > 0.1:
                                significant_pairs.append((col1, col2, corr_val, p_val))

            # Fill diagonal of p_values with 0 (perfect correlation with self)
            np.fill_diagonal(p_values.values, 0)

            return CorrelationMatrix(
                correlation_matrix=corr_matrix,
                p_values=p_values,
                significant_pairs=significant_pairs,
                method=method,
                sample_size=len(numeric_data),
            )

        except Exception as e:
            self.logger.error(f"Error in correlation matrix computation: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def compute_partial_correlation(
        self,
        data: pd.DataFrame,
        target_vars: List[str],
        control_vars: List[str],
    ) -> PartialCorrelationResults:
        """
        Compute partial correlation controlling for specified variables.

        Args:
            data: DataFrame with numerical data
            target_vars: Variables to compute partial correlations between
            control_vars: Variables to control for

        Returns:
            PartialCorrelationResults object
        """
        try:
            # Validate inputs
            all_vars = target_vars + control_vars
            missing_vars = [var for var in all_vars if var not in data.columns]
            if missing_vars:
                raise ValueError(f"Missing variables in data: {missing_vars}")

            # Get clean data
            clean_data = data[all_vars].dropna()

            if len(clean_data) < len(all_vars) + 10:
                raise ValueError("Insufficient data for partial correlation analysis")

            # Standardize data
            scaler = StandardScaler()
            scaled_data = pd.DataFrame(
                scaler.fit_transform(clean_data),
                columns=clean_data.columns,
                index=clean_data.index,
            )

            # Compute partial correlation matrix
            n_target = len(target_vars)
            partial_corr_matrix = pd.DataFrame(
                np.eye(n_target),
                index=target_vars,
                columns=target_vars,
            )

            significant_partial_correlations = []

            for i, var1 in enumerate(target_vars):
                for j, var2 in enumerate(target_vars):
                    if i < j:
                        # Regress both variables on control variables
                        X_control = scaled_data[control_vars].values
                        y1 = scaled_data[var1].values
                        y2 = scaled_data[var2].values

                        # Fit regression models
                        reg1 = LinearRegression().fit(X_control, y1)
                        reg2 = LinearRegression().fit(X_control, y2)

                        # Compute residuals
                        residuals1 = y1 - reg1.predict(X_control)
                        residuals2 = y2 - reg2.predict(X_control)

                        # Partial correlation is correlation of residuals
                        partial_corr, p_value = pearsonr(residuals1, residuals2)

                        partial_corr_matrix.loc[var1, var2] = partial_corr
                        partial_corr_matrix.loc[var2, var1] = partial_corr

                        # Check significance
                        if p_value < self.significance_level and abs(partial_corr) > 0.1:
                            significant_partial_correlations.append((var1, var2, partial_corr))

            return PartialCorrelationResults(
                partial_corr_matrix=partial_corr_matrix,
                control_variables=control_vars,
                significant_partial_correlations=significant_partial_correlations,
            )

        except Exception as e:
            self.logger.error(f"Error in partial correlation computation: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def analyze_feature_importance(
        self,
        data: pd.DataFrame,
        target_variable: str,
        method: str = "mutual_info",
        n_features: int = 10,
    ) -> FeatureImportanceResults:
        """
        Analyze feature importance for predicting target variable.

        Args:
            data: DataFrame with features and target
            target_variable: Name of target variable
            method: Importance method ('mutual_info', 'f_regression', 'random_forest')
            n_features: Number of top features to return

        Returns:
            FeatureImportanceResults object
        """
        try:
            if target_variable not in data.columns:
                raise ValueError(f"Target variable '{target_variable}' not found in data")

            # Prepare features and target
            feature_columns = [col for col in data.columns if col != target_variable]
            feature_data = data[feature_columns].select_dtypes(include=[np.number])
            target_data = data[target_variable]

            # Remove samples with missing target
            valid_mask = target_data.notna()
            target_data = target_data[valid_mask]
            feature_data = feature_data.loc[valid_mask]

            # Remove features with too many missing values (>50%)
            missing_threshold = len(feature_data) * 0.5
            valid_features = []
            for col in feature_data.columns:
                if feature_data[col].notna().sum() > missing_threshold:
                    valid_features.append(col)

            feature_data = feature_data[valid_features]

            # Fill remaining missing values with median
            feature_data = feature_data.fillna(feature_data.median())

            if feature_data.empty:
                raise ValueError("No valid features found for importance analysis")

            # Compute feature importance based on method
            if method == "mutual_info":
                selector = SelectKBest(
                    score_func=mutual_info_regression, k=min(n_features, len(valid_features))
                )
                selector.fit(feature_data, target_data)
                scores = selector.scores_

            elif method == "f_regression":
                selector = SelectKBest(
                    score_func=f_regression, k=min(n_features, len(valid_features))
                )
                selector.fit(feature_data, target_data)
                scores = selector.scores_

            elif method == "random_forest":
                rf = RandomForestRegressor(
                    n_estimators=100,
                    random_state=42,
                    n_jobs=-1,
                )
                rf.fit(feature_data, target_data)
                scores = rf.feature_importances_

            else:
                raise ValueError(f"Unknown feature importance method: {method}")

            # Create results DataFrame
            feature_scores = pd.DataFrame(
                {
                    "feature": valid_features,
                    "importance": scores,
                }
            )

            # Sort by importance (descending)
            feature_scores = feature_scores.sort_values("importance", ascending=False)
            feature_scores["rank"] = range(1, len(feature_scores) + 1)

            # Get top features
            top_features = feature_scores.head(n_features)["feature"].tolist()

            return FeatureImportanceResults(
                feature_scores=feature_scores,
                method=method,
                target_variable=target_variable,
                top_features=top_features,
            )

        except Exception as e:
            self.logger.error(f"Error in feature importance analysis: {e}")
            raise

    def compute_cross_correlation(
        self,
        series1: Union[pd.Series, np.ndarray],
        series2: Union[pd.Series, np.ndarray],
        max_lag: Optional[int] = None,
    ) -> CrossCorrelationResults:
        """
        Compute cross-correlation between two time series.

        Args:
            series1: First time series
            series2: Second time series
            max_lag: Maximum lag to compute

        Returns:
            CrossCorrelationResults object
        """
        try:
            # Convert to numpy arrays and clean
            if isinstance(series1, pd.Series):
                arr1 = series1.dropna().values
            else:
                arr1 = series1[~np.isnan(series1)]

            if isinstance(series2, pd.Series):
                arr2 = series2.dropna().values
            else:
                arr2 = series2[~np.isnan(series2)]

            # Ensure equal length
            min_len = min(len(arr1), len(arr2))
            arr1 = arr1[:min_len]
            arr2 = arr2[:min_len]

            if min_len < 10:
                raise ValueError("Insufficient data for cross-correlation analysis")

            # Set max_lag if not provided
            if max_lag is None:
                max_lag = min(min_len // 4, 50)

            # Normalize series (zero mean, unit variance)
            arr1 = (arr1 - np.mean(arr1)) / np.std(arr1)
            arr2 = (arr2 - np.mean(arr2)) / np.std(arr2)

            # Compute cross-correlation
            correlation_full = np.correlate(arr1, arr2, mode="full")
            correlation_full = correlation_full / min_len  # Normalize

            # Extract relevant lags
            mid = len(correlation_full) // 2
            start_idx = max(0, mid - max_lag)
            end_idx = min(len(correlation_full), mid + max_lag + 1)

            correlation_function = correlation_full[start_idx:end_idx]
            lags = np.arange(start_idx - mid, end_idx - mid)

            # Find maximum correlation and optimal lag
            max_idx = np.argmax(np.abs(correlation_function))
            max_correlation = correlation_function[max_idx]
            optimal_lag = lags[max_idx]

            # Compute confidence interval (95%)
            confidence_interval = 1.96 / np.sqrt(min_len)

            return CrossCorrelationResults(
                max_correlation=max_correlation,
                optimal_lag=optimal_lag,
                correlation_function=correlation_function,
                lags=lags,
                confidence_interval=confidence_interval,
            )

        except Exception as e:
            self.logger.error(f"Error in cross-correlation computation: {e}")
            raise

    def analyze_granger_causality(
        self,
        data: pd.DataFrame,
        variables: List[str],
        max_lag: int = 5,
    ) -> CausalAnalysisResults:
        """
        Perform Granger causality analysis.

        Args:
            data: DataFrame with time series data
            variables: List of variables to test for causality
            max_lag: Maximum lag for causality testing

        Returns:
            CausalAnalysisResults object
        """
        try:
            # Validate inputs
            missing_vars = [var for var in variables if var not in data.columns]
            if missing_vars:
                raise ValueError(f"Missing variables in data: {missing_vars}")

            # Get clean data
            clean_data = data[variables].dropna()

            if len(clean_data) < max_lag * 3:
                raise ValueError("Insufficient data for Granger causality analysis")

            granger_results = {}
            causal_graph = {var: [] for var in variables}
            causal_strength = {}

            # Test causality for each pair of variables
            for cause_var in variables:
                granger_results[cause_var] = {}

                for effect_var in variables:
                    if cause_var != effect_var:
                        # Prepare data for Granger test
                        y = clean_data[effect_var].values
                        x = clean_data[cause_var].values

                        # Simple Granger causality test using F-test
                        try:
                            f_stat, p_value = self._granger_causality_test(y, x, max_lag)
                            granger_results[cause_var][effect_var] = (f_stat, p_value)

                            # Determine causality
                            if p_value < self.significance_level:
                                causal_graph[cause_var].append(effect_var)
                                causal_strength[(cause_var, effect_var)] = 1 - p_value

                        except Exception as e:
                            self.logger.warning(
                                f"Granger test failed for {cause_var}->{effect_var}: {e}"
                            )
                            granger_results[cause_var][effect_var] = (np.nan, np.nan)

            return CausalAnalysisResults(
                granger_results=granger_results,
                causal_graph=causal_graph,
                causal_strength=causal_strength,
            )

        except Exception as e:
            self.logger.error(f"Error in Granger causality analysis: {e}")
            raise

    def create_correlation_plots(
        self,
        correlation_matrix: CorrelationMatrix,
        title: str = "Correlation Analysis",
    ) -> Dict[str, go.Figure]:
        """
        Create comprehensive correlation plots.

        Args:
            correlation_matrix: CorrelationMatrix object
            title: Base title for plots

        Returns:
            Dictionary of plot names -> plotly figures
        """
        try:
            plots = {}

            # 1. Correlation heatmap
            fig_heatmap = go.Figure(
                data=go.Heatmap(
                    z=correlation_matrix.correlation_matrix.values,
                    x=correlation_matrix.correlation_matrix.columns,
                    y=correlation_matrix.correlation_matrix.index,
                    colorscale="RdBu",
                    zmid=0,
                    text=np.round(correlation_matrix.correlation_matrix.values, 3),
                    texttemplate="%{text}",
                    textfont={"size": 10},
                    colorbar=dict(title="Correlation"),
                )
            )

            fig_heatmap.update_layout(
                title=f"{title} - Correlation Matrix",
                xaxis_title="Variables",
                yaxis_title="Variables",
                width=800,
                height=800,
            )
            plots["heatmap"] = fig_heatmap

            # 2. Correlation network (significant correlations only)
            if correlation_matrix.significant_pairs:
                # Create network data
                nodes = list(
                    set(
                        [pair[0] for pair in correlation_matrix.significant_pairs]
                        + [pair[1] for pair in correlation_matrix.significant_pairs]
                    )
                )

                # Create adjacency matrix for visualization
                node_positions = {node: i for i, node in enumerate(nodes)}

                fig_network = go.Figure()

                # Add edges (correlations)
                for var1, var2, corr, p_val in correlation_matrix.significant_pairs:
                    if abs(corr) > 0.3:  # Only show strong correlations
                        x0, y0 = node_positions[var1], 0
                        x1, y1 = node_positions[var2], 1

                        color = "red" if corr > 0 else "blue"
                        width = abs(corr) * 10

                        fig_network.add_trace(
                            go.Scatter(
                                x=[x0, x1, None],
                                y=[y0, y1, None],
                                mode="lines",
                                line=dict(color=color, width=width),
                                showlegend=False,
                                hovertemplate=f"{var1} ↔ {var2}<br>r={corr:.3f}, p={p_val:.3f}",
                            )
                        )

                # Add nodes
                fig_network.add_trace(
                    go.Scatter(
                        x=list(range(len(nodes))),
                        y=[0] * len(nodes),
                        mode="markers+text",
                        text=nodes,
                        textposition="bottom center",
                        marker=dict(size=20, color="lightblue"),
                        showlegend=False,
                        name="Variables (Level 1)",
                    )
                )

                fig_network.add_trace(
                    go.Scatter(
                        x=list(range(len(nodes))),
                        y=[1] * len(nodes),
                        mode="markers+text",
                        text=nodes,
                        textposition="top center",
                        marker=dict(size=20, color="lightgreen"),
                        showlegend=False,
                        name="Variables (Level 2)",
                    )
                )

                fig_network.update_layout(
                    title=f"{title} - Significant Correlations Network",
                    showlegend=False,
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                )
                plots["network"] = fig_network

            # 3. Top correlations bar chart
            if correlation_matrix.significant_pairs:
                # Sort by absolute correlation
                sorted_pairs = sorted(
                    correlation_matrix.significant_pairs,
                    key=lambda x: abs(x[2]),
                    reverse=True,
                )[
                    :15
                ]  # Top 15

                labels = [f"{pair[0]} ↔ {pair[1]}" for pair in sorted_pairs]
                values = [pair[2] for pair in sorted_pairs]
                colors = ["red" if v > 0 else "blue" for v in values]

                fig_bar = go.Figure(
                    data=go.Bar(
                        x=values,
                        y=labels,
                        orientation="h",
                        marker_color=colors,
                        text=[f"{v:.3f}" for v in values],
                        textposition="auto",
                    )
                )

                fig_bar.update_layout(
                    title=f"{title} - Top Correlations",
                    xaxis_title="Correlation Coefficient",
                    yaxis_title="Variable Pairs",
                    height=600,
                )
                plots["top_correlations"] = fig_bar

            return plots

        except Exception as e:
            self.logger.error(f"Error creating correlation plots: {e}")
            raise

    def _granger_causality_test(
        self, y: np.ndarray, x: np.ndarray, max_lag: int
    ) -> Tuple[float, float]:
        """
        Perform Granger causality test using F-statistic.

        Args:
            y: Effect variable (dependent)
            x: Cause variable (independent)
            max_lag: Maximum lag to include

        Returns:
            Tuple of (F-statistic, p-value)
        """
        try:
            from scipy.stats import f

            n = len(y)

            # Create lagged variables
            Y = y[max_lag:]
            X_restricted = np.column_stack([y[max_lag - i - 1 : n - i - 1] for i in range(max_lag)])
            X_unrestricted = np.column_stack(
                [
                    X_restricted,
                    np.column_stack([x[max_lag - i - 1 : n - i - 1] for i in range(max_lag)]),
                ]
            )

            # Add constant term
            X_restricted = np.column_stack([np.ones(len(Y)), X_restricted])
            X_unrestricted = np.column_stack([np.ones(len(Y)), X_unrestricted])

            # Fit restricted model (without x lags)
            try:
                beta_restricted = pinv(X_restricted.T @ X_restricted) @ X_restricted.T @ Y
                residuals_restricted = Y - X_restricted @ beta_restricted
                ssr_restricted = np.sum(residuals_restricted**2)
            except Exception:
                return np.nan, np.nan

            # Fit unrestricted model (with x lags)
            try:
                beta_unrestricted = pinv(X_unrestricted.T @ X_unrestricted) @ X_unrestricted.T @ Y
                residuals_unrestricted = Y - X_unrestricted @ beta_unrestricted
                ssr_unrestricted = np.sum(residuals_unrestricted**2)
            except Exception:
                return np.nan, np.nan

            # Compute F-statistic
            df_num = max_lag  # Number of restrictions
            df_den = len(Y) - X_unrestricted.shape[1]  # Degrees of freedom denominator

            if df_den <= 0 or ssr_unrestricted <= 0:
                return np.nan, np.nan

            f_stat = ((ssr_restricted - ssr_unrestricted) / df_num) / (ssr_unrestricted / df_den)
            p_value = 1 - f.cdf(f_stat, df_num, df_den)

            return f_stat, p_value

        except Exception:
            return np.nan, np.nan

    def generate_correlation_summary(
        self, data: pd.DataFrame, target_variable: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive correlation analysis summary.

        Args:
            data: DataFrame with numerical data
            target_variable: Optional target variable for feature importance

        Returns:
            Dictionary with all correlation analysis results
        """
        try:
            results = {}

            # Basic correlation matrix
            pearson_corr = self.compute_correlation_matrix(data, method="pearson")
            spearman_corr = self.compute_correlation_matrix(data, method="spearman")

            results["pearson_correlation"] = pearson_corr
            results["spearman_correlation"] = spearman_corr

            # Feature importance if target specified
            if target_variable and target_variable in data.columns:
                mutual_info = self.analyze_feature_importance(
                    data, target_variable, method="mutual_info"
                )
                rf_importance = self.analyze_feature_importance(
                    data, target_variable, method="random_forest"
                )

                results["mutual_info_importance"] = mutual_info
                results["random_forest_importance"] = rf_importance

            # Plots
            correlation_plots = self.create_correlation_plots(pearson_corr)
            results["plots"] = correlation_plots

            # Summary statistics
            results["summary"] = {
                "n_variables": len(data.select_dtypes(include=[np.number]).columns),
                "n_significant_correlations": len(pearson_corr.significant_pairs),
                "max_correlation": (
                    max([abs(pair[2]) for pair in pearson_corr.significant_pairs])
                    if pearson_corr.significant_pairs
                    else 0
                ),
                "sample_size": pearson_corr.sample_size,
            }

            return results

        except Exception as e:
            self.logger.error(f"Error generating correlation summary: {e}")
            raise
