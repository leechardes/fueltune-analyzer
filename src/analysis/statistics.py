"""
Advanced Statistical Analysis Module for FuelTune.

Provides comprehensive statistical analysis capabilities including
descriptive statistics, hypothesis testing, and distribution analysis
for automotive telemetry data.

Author: A04-ANALYSIS-SCIPY Agent
Created: 2025-01-02
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
from scipy.stats import (
    anderson,
    jarque_bera,
    normaltest,
    pearsonr,
    shapiro,
    spearmanr,
    ttest_1samp,
    ttest_ind,
    ttest_rel,
)

from ..data.cache import cached_analysis as cache_result
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class DescriptiveStats:
    """Container for descriptive statistics results."""

    count: int
    mean: float
    std: float
    min: float
    q25: float
    median: float
    q75: float
    max: float
    skewness: float
    kurtosis: float
    variance: float
    coefficient_of_variation: float
    range: float
    iqr: float
    mad: float  # Median Absolute Deviation
    sem: float  # Standard Error of Mean


@dataclass
class NormalityTestResults:
    """Results from normality testing."""

    shapiro_stat: float
    shapiro_p: float
    shapiro_normal: bool
    jarque_bera_stat: float
    jarque_bera_p: float
    jarque_bera_normal: bool
    anderson_stat: float
    anderson_critical_values: List[float]
    anderson_significance_levels: List[float]
    anderson_normal: bool
    dagostino_stat: float
    dagostino_p: float
    dagostino_normal: bool
    overall_normal: bool


@dataclass
class HypothesisTestResults:
    """Results from hypothesis testing."""

    test_name: str
    statistic: float
    p_value: float
    degrees_of_freedom: Optional[int]
    critical_value: Optional[float]
    confidence_level: float
    reject_null: bool
    effect_size: Optional[float]
    power: Optional[float]
    interpretation: str


@dataclass
class DistributionFitResults:
    """Results from distribution fitting."""

    distribution_name: str
    parameters: Dict[str, float]
    aic: float
    bic: float
    log_likelihood: float
    ks_statistic: float
    ks_p_value: float
    goodness_of_fit: float


class StatisticalAnalyzer:
    """Advanced statistical analysis for FuelTune telemetry data."""

    def __init__(self, alpha: float = 0.05):
        """
        Initialize statistical analyzer.

        Args:
            alpha: Significance level for hypothesis testing
        """
        self.alpha = alpha
        self.logger = logger

    def analyze(self, data: Union[pd.DataFrame, pd.Series]) -> Dict[str, Any]:
        """
        Standard analyze method for statistical analysis.

        Args:
            data: Input data (DataFrame or Series)

        Returns:
            Dictionary with comprehensive statistical analysis results
        """
        try:
            if isinstance(data, pd.DataFrame):
                # For DataFrame, analyze all numeric columns
                results = {}
                numeric_columns = data.select_dtypes(include=[np.number]).columns
                
                for col in numeric_columns:
                    results[col] = self.generate_statistical_summary(data[col], col)
                
                return results
            else:
                # For Series, direct analysis
                return self.generate_statistical_summary(data)
        except Exception as e:
            self.logger.error(f"Statistical analysis failed: {e}")
            return {"error": str(e)}

    @cache_result("analysis", ttl=3600)
    def compute_descriptive_stats(
        self, data: Union[pd.Series, np.ndarray], column_name: str = ""
    ) -> DescriptiveStats:
        """
        Compute comprehensive descriptive statistics.

        Args:
            data: Input data series
            column_name: Name of the data column

        Returns:
            DescriptiveStats object with all computed statistics
        """
        try:
            # Convert to pandas Series if needed
            if isinstance(data, np.ndarray):
                data = pd.Series(data)

            # Remove NaN values
            clean_data = data.dropna()

            if len(clean_data) < 2:
                raise ValueError("Insufficient data for statistical analysis")

            # Basic statistics
            count = len(clean_data)
            mean = float(clean_data.mean())
            std = float(clean_data.std(ddof=1))
            min_val = float(clean_data.min())
            max_val = float(clean_data.max())

            # Quantiles
            q25 = float(clean_data.quantile(0.25))
            median = float(clean_data.median())
            q75 = float(clean_data.quantile(0.75))

            # Advanced statistics
            skewness = float(stats.skew(clean_data))
            kurtosis = float(stats.kurtosis(clean_data))
            variance = float(clean_data.var(ddof=1))

            # Derived statistics
            cv = std / abs(mean) if mean != 0 else np.inf
            data_range = max_val - min_val
            iqr = q75 - q25
            # Calculate Median Absolute Deviation manually since pandas removed mad()
            mad = float(np.median(np.abs(clean_data - median)))
            sem = std / np.sqrt(count)  # Standard Error of Mean

            return DescriptiveStats(
                count=count,
                mean=mean,
                std=std,
                min=min_val,
                q25=q25,
                median=median,
                q75=q75,
                max=max_val,
                skewness=skewness,
                kurtosis=kurtosis,
                variance=variance,
                coefficient_of_variation=cv,
                range=data_range,
                iqr=iqr,
                mad=mad,
                sem=sem,
            )

        except Exception as e:
            self.logger.error(f"Error in descriptive statistics: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def test_normality(self, data: Union[pd.Series, np.ndarray]) -> NormalityTestResults:
        """
        Comprehensive normality testing using multiple methods.

        Args:
            data: Input data series

        Returns:
            NormalityTestResults with all test results
        """
        try:
            # Convert and clean data
            if isinstance(data, pd.Series):
                clean_data = data.dropna().values
            else:
                clean_data = data[~np.isnan(data)]

            if len(clean_data) < 3:
                raise ValueError("Insufficient data for normality testing")

            # Shapiro-Wilk test (best for small samples)
            if len(clean_data) <= 5000:
                shapiro_stat, shapiro_p = shapiro(clean_data)
            else:
                # Use subsample for large datasets
                subsample = np.random.choice(clean_data, size=5000, replace=False)
                shapiro_stat, shapiro_p = shapiro(subsample)

            shapiro_normal = shapiro_p > self.alpha

            # Jarque-Bera test
            jb_stat, jb_p = jarque_bera(clean_data)
            jb_normal = jb_p > self.alpha

            # Anderson-Darling test
            anderson_result = anderson(clean_data, dist="norm")
            anderson_stat = anderson_result.statistic
            anderson_critical = anderson_result.critical_values
            anderson_significance = anderson_result.significance_level
            # Use 5% critical value
            anderson_normal = anderson_stat < anderson_critical[2]

            # D'Agostino's normality test
            try:
                da_stat, da_p = normaltest(clean_data)
                da_normal = da_p > self.alpha
            except Exception:
                da_stat, da_p, da_normal = np.nan, np.nan, False

            # Overall assessment (majority rule)
            normal_count = sum([shapiro_normal, jb_normal, anderson_normal, da_normal])
            overall_normal = normal_count >= 2

            return NormalityTestResults(
                shapiro_stat=shapiro_stat,
                shapiro_p=shapiro_p,
                shapiro_normal=shapiro_normal,
                jarque_bera_stat=jb_stat,
                jarque_bera_p=jb_p,
                jarque_bera_normal=jb_normal,
                anderson_stat=anderson_stat,
                anderson_critical_values=anderson_critical.tolist(),
                anderson_significance_levels=anderson_significance.tolist(),
                anderson_normal=anderson_normal,
                dagostino_stat=da_stat,
                dagostino_p=da_p,
                dagostino_normal=da_normal,
                overall_normal=overall_normal,
            )

        except Exception as e:
            self.logger.error(f"Error in normality testing: {e}")
            raise

    def perform_t_test(
        self,
        data1: Union[pd.Series, np.ndarray],
        data2: Optional[Union[pd.Series, np.ndarray]] = None,
        test_type: str = "one_sample",
        expected_mean: float = 0.0,
        paired: bool = False,
        alternative: str = "two-sided",
    ) -> HypothesisTestResults:
        """
        Perform various t-tests.

        Args:
            data1: First data group
            data2: Second data group (for two-sample tests)
            test_type: Type of test ('one_sample', 'two_sample')
            expected_mean: Expected mean for one-sample test
            paired: Whether to perform paired t-test
            alternative: Alternative hypothesis ('two-sided', 'less', 'greater')

        Returns:
            HypothesisTestResults object
        """
        try:
            if test_type == "one_sample":
                clean_data = pd.Series(data1).dropna().values
                stat, p_value = ttest_1samp(clean_data, expected_mean)
                df = len(clean_data) - 1
                effect_size = (np.mean(clean_data) - expected_mean) / np.std(clean_data, ddof=1)

            elif test_type == "two_sample":
                if data2 is None:
                    raise ValueError("data2 required for two-sample test")

                clean_data1 = pd.Series(data1).dropna().values
                clean_data2 = pd.Series(data2).dropna().values

                if paired:
                    if len(clean_data1) != len(clean_data2):
                        raise ValueError("Paired data must have equal length")
                    stat, p_value = ttest_rel(clean_data1, clean_data2)
                    df = len(clean_data1) - 1
                    effect_size = (np.mean(clean_data1) - np.mean(clean_data2)) / np.std(
                        clean_data1 - clean_data2, ddof=1
                    )
                else:
                    stat, p_value = ttest_ind(clean_data1, clean_data2)
                    df = len(clean_data1) + len(clean_data2) - 2
                    pooled_std = np.sqrt(
                        (
                            (len(clean_data1) - 1) * np.var(clean_data1, ddof=1)
                            + (len(clean_data2) - 1) * np.var(clean_data2, ddof=1)
                        )
                        / df
                    )
                    effect_size = (np.mean(clean_data1) - np.mean(clean_data2)) / pooled_std

            else:
                raise ValueError(f"Unknown test type: {test_type}")

            # Adjust p-value for one-tailed tests
            if alternative != "two-sided":
                p_value = p_value / 2
                if alternative == "greater" and stat < 0:
                    p_value = 1 - p_value
                elif alternative == "less" and stat > 0:
                    p_value = 1 - p_value

            critical_value = stats.t.ppf(1 - self.alpha / 2, df)
            reject_null = p_value < self.alpha

            # Interpretation
            if reject_null:
                interpretation = f"Reject null hypothesis (p={p_value:.4f} < α={self.alpha})"
            else:
                interpretation = (
                    f"Fail to reject null hypothesis (p={p_value:.4f} ≥ α={self.alpha})"
                )

            return HypothesisTestResults(
                test_name=f"T-test ({test_type})",
                statistic=stat,
                p_value=p_value,
                degrees_of_freedom=df,
                critical_value=critical_value,
                confidence_level=1 - self.alpha,
                reject_null=reject_null,
                effect_size=effect_size,
                power=None,  # Would require additional calculation
                interpretation=interpretation,
            )

        except Exception as e:
            self.logger.error(f"Error in t-test: {e}")
            raise

    def perform_anova(
        self, groups: Dict[str, Union[pd.Series, np.ndarray]]
    ) -> HypothesisTestResults:
        """
        Perform one-way ANOVA.

        Args:
            groups: Dictionary of group name -> data

        Returns:
            HypothesisTestResults object
        """
        try:
            # Clean data and prepare for ANOVA
            clean_groups = {}
            for name, data in groups.items():
                clean_data = pd.Series(data).dropna().values
                if len(clean_data) < 2:
                    raise ValueError(f"Insufficient data in group {name}")
                clean_groups[name] = clean_data

            if len(clean_groups) < 2:
                raise ValueError("ANOVA requires at least 2 groups")

            # Perform ANOVA
            stat, p_value = stats.f_oneway(*clean_groups.values())

            # Calculate degrees of freedom
            k = len(clean_groups)  # number of groups
            n = sum(len(group) for group in clean_groups.values())  # total observations
            df_between = k - 1
            df_within = n - k

            # Effect size (eta-squared)
            ss_between = stat * df_between
            ss_total = ss_between + df_within
            eta_squared = ss_between / ss_total if ss_total > 0 else 0

            critical_value = stats.f.ppf(1 - self.alpha, df_between, df_within)
            reject_null = p_value < self.alpha

            interpretation = (
                f"ANOVA F({df_between},{df_within})={stat:.4f}, p={p_value:.4f}. "
                f"{'Reject' if reject_null else 'Fail to reject'} null hypothesis "
                f"of equal group means."
            )

            return HypothesisTestResults(
                test_name="One-way ANOVA",
                statistic=stat,
                p_value=p_value,
                degrees_of_freedom=df_between,
                critical_value=critical_value,
                confidence_level=1 - self.alpha,
                reject_null=reject_null,
                effect_size=eta_squared,
                power=None,
                interpretation=interpretation,
            )

        except Exception as e:
            self.logger.error(f"Error in ANOVA: {e}")
            raise

    @cache_result("analysis", ttl=3600)
    def fit_distributions(
        self, data: Union[pd.Series, np.ndarray], distributions: Optional[List[str]] = None
    ) -> List[DistributionFitResults]:
        """
        Fit multiple distributions to data and rank by goodness of fit.

        Args:
            data: Input data
            distributions: List of distribution names to fit

        Returns:
            List of DistributionFitResults sorted by goodness of fit
        """
        if distributions is None:
            distributions = ["norm", "lognorm", "gamma", "weibull_min", "expon", "beta"]

        try:
            # Clean data
            clean_data = pd.Series(data).dropna().values
            if len(clean_data) < 10:
                raise ValueError("Insufficient data for distribution fitting")

            results = []

            for dist_name in distributions:
                try:
                    # Get distribution object
                    dist = getattr(stats, dist_name)

                    # Fit distribution
                    params = dist.fit(clean_data)

                    # Calculate log-likelihood
                    log_likelihood = np.sum(dist.logpdf(clean_data, *params))

                    # Calculate AIC and BIC
                    k = len(params)  # number of parameters
                    n = len(clean_data)
                    aic = 2 * k - 2 * log_likelihood
                    bic = k * np.log(n) - 2 * log_likelihood

                    # Kolmogorov-Smirnov test
                    ks_stat, ks_p = stats.kstest(clean_data, dist.cdf, args=params)

                    # Goodness of fit score (lower is better)
                    goodness_of_fit = aic  # Using AIC as primary criterion

                    # Create parameter dictionary
                    param_names = (
                        dist.shapes.split(",") if hasattr(dist, "shapes") and dist.shapes else []
                    )
                    param_names.extend(["loc", "scale"])
                    param_dict = dict(zip(param_names, params))

                    results.append(
                        DistributionFitResults(
                            distribution_name=dist_name,
                            parameters=param_dict,
                            aic=aic,
                            bic=bic,
                            log_likelihood=log_likelihood,
                            ks_statistic=ks_stat,
                            ks_p_value=ks_p,
                            goodness_of_fit=goodness_of_fit,
                        )
                    )

                except Exception as e:
                    self.logger.warning(f"Failed to fit {dist_name}: {e}")
                    continue

            # Sort by goodness of fit (lower AIC is better)
            results.sort(key=lambda x: x.goodness_of_fit)

            return results

        except Exception as e:
            self.logger.error(f"Error in distribution fitting: {e}")
            raise

    def create_statistical_plots(
        self, data: Union[pd.Series, np.ndarray], column_name: str = "Data"
    ) -> Dict[str, go.Figure]:
        """
        Create comprehensive statistical plots.

        Args:
            data: Input data
            column_name: Name for plot titles

        Returns:
            Dictionary of plot names -> plotly figures
        """
        try:
            clean_data = pd.Series(data).dropna()

            plots = {}

            # 1. Histogram with normal distribution overlay
            fig_hist = go.Figure()
            fig_hist.add_trace(
                go.Histogram(
                    x=clean_data,
                    nbinsx=50,
                    name="Data",
                    opacity=0.7,
                    histnorm="probability density",
                )
            )

            # Add normal distribution overlay
            x_range = np.linspace(clean_data.min(), clean_data.max(), 100)
            normal_curve = stats.norm.pdf(x_range, clean_data.mean(), clean_data.std())
            fig_hist.add_trace(
                go.Scatter(
                    x=x_range,
                    y=normal_curve,
                    mode="lines",
                    name="Normal Fit",
                    line=dict(color="red", width=2),
                )
            )

            fig_hist.update_layout(
                title=f"Distribution of {column_name}",
                xaxis_title=column_name,
                yaxis_title="Density",
                showlegend=True,
            )
            plots["histogram"] = fig_hist

            # 2. Q-Q plot
            fig_qq = go.Figure()
            theoretical_quantiles, sample_quantiles = stats.probplot(clean_data, dist="norm")

            fig_qq.add_trace(
                go.Scatter(
                    x=theoretical_quantiles[0],
                    y=theoretical_quantiles[1],
                    mode="markers",
                    name="Q-Q Plot",
                    marker=dict(color="blue", size=4),
                )
            )

            # Add reference line
            min_q = min(theoretical_quantiles[0])
            max_q = max(theoretical_quantiles[0])
            fig_qq.add_trace(
                go.Scatter(
                    x=[min_q, max_q],
                    y=[
                        min_q * sample_quantiles[0] + sample_quantiles[1],
                        max_q * sample_quantiles[0] + sample_quantiles[1],
                    ],
                    mode="lines",
                    name="Reference Line",
                    line=dict(color="red", dash="dash"),
                )
            )

            fig_qq.update_layout(
                title=f"Q-Q Plot: {column_name}",
                xaxis_title="Theoretical Quantiles",
                yaxis_title="Sample Quantiles",
            )
            plots["qq_plot"] = fig_qq

            # 3. Box plot with outliers
            fig_box = go.Figure()
            fig_box.add_trace(
                go.Box(
                    y=clean_data,
                    name=column_name,
                    boxpoints="outliers",
                    jitter=0.3,
                    pointpos=-1.8,
                )
            )
            fig_box.update_layout(
                title=f"Box Plot: {column_name}",
                yaxis_title=column_name,
            )
            plots["box_plot"] = fig_box

            # 4. Violin plot
            fig_violin = go.Figure()
            fig_violin.add_trace(
                go.Violin(
                    y=clean_data,
                    name=column_name,
                    box_visible=True,
                    meanline_visible=True,
                )
            )
            fig_violin.update_layout(
                title=f"Violin Plot: {column_name}",
                yaxis_title=column_name,
            )
            plots["violin_plot"] = fig_violin

            return plots

        except Exception as e:
            self.logger.error(f"Error creating statistical plots: {e}")
            raise

    def generate_statistical_summary(
        self, data: Union[pd.Series, np.ndarray], column_name: str = "Data"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive statistical summary.

        Args:
            data: Input data
            column_name: Name of the data column

        Returns:
            Dictionary with all statistical analysis results
        """
        try:
            # Compute all analyses
            descriptive = self.compute_descriptive_stats(data, column_name)
            normality = self.test_normality(data)
            distributions = self.fit_distributions(data)
            plots = self.create_statistical_plots(data, column_name)

            return {
                "descriptive_statistics": descriptive,
                "normality_tests": normality,
                "distribution_fits": distributions[:3],  # Top 3 fits
                "plots": plots,
                "recommendations": self._generate_recommendations(descriptive, normality),
            }

        except Exception as e:
            self.logger.error(f"Error generating statistical summary: {e}")
            raise

    def _generate_recommendations(
        self, descriptive: DescriptiveStats, normality: NormalityTestResults
    ) -> List[str]:
        """Generate analysis recommendations based on results."""
        recommendations = []

        # Skewness recommendations
        if abs(descriptive.skewness) > 2:
            recommendations.append(
                f"Data is highly skewed ({descriptive.skewness:.2f}). "
                "Consider transformation or non-parametric methods."
            )
        elif abs(descriptive.skewness) > 0.5:
            recommendations.append(
                f"Data shows moderate skewness ({descriptive.skewness:.2f}). "
                "Monitor for impact on analyses."
            )

        # Kurtosis recommendations
        if abs(descriptive.kurtosis) > 3:
            recommendations.append(
                f"Data shows extreme kurtosis ({descriptive.kurtosis:.2f}). "
                "Check for outliers or heavy tails."
            )

        # Normality recommendations
        if not normality.overall_normal:
            recommendations.append(
                "Data is not normally distributed. Consider non-parametric tests "
                "or data transformation."
            )

        # Coefficient of variation
        if descriptive.coefficient_of_variation > 1:
            recommendations.append(
                f"High variability detected (CV={descriptive.coefficient_of_variation:.2f}). "
                "Data may be heteroscedastic."
            )

        # Outlier detection based on IQR
        outlier_threshold = 1.5 * descriptive.iqr
        if (descriptive.max - descriptive.q75) > outlier_threshold or (
            descriptive.q25 - descriptive.min
        ) > outlier_threshold:
            recommendations.append(
                "Potential outliers detected based on IQR method. " "Consider outlier analysis."
            )

        return recommendations
