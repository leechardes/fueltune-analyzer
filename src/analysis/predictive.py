"""
Predictive Analysis Module for FuelTune.

Provides predictive analytics including failure prediction, maintenance
scheduling, performance degradation forecasting, and consumption prediction
using machine learning techniques.

Author: A04-ANALYSIS-SCIPY Agent
Created: 2025-01-02
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ..data.cache import cached_analysis as cache_result
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class FailurePredictionResults:
    """Results from failure prediction analysis."""

    failure_probability: Dict[str, float]  # component -> probability
    risk_factors: Dict[str, List[Tuple[str, float]]]  # component -> [(factor, importance)]
    maintenance_alerts: List[Dict[str, Any]]  # [{component, severity, days_until, description}]
    health_scores: Dict[str, float]  # component -> health score (0-100)
    trend_analysis: Dict[str, float]  # component -> trend slope


@dataclass
class MaintenanceSchedule:
    """Results from maintenance scheduling analysis."""

    scheduled_maintenance: List[Dict[str, Any]]  # maintenance items with dates
    predictive_maintenance: List[Dict[str, Any]]  # condition-based maintenance
    cost_analysis: Dict[str, float]  # maintenance costs and savings
    maintenance_calendar: pd.DataFrame  # date, item, type, priority
    optimization_suggestions: List[str]


@dataclass
class PerformanceDegradation:
    """Results from performance degradation analysis."""

    degradation_trends: Dict[str, np.ndarray]  # parameter -> trend values
    degradation_rates: Dict[str, float]  # parameter -> rate per unit time
    performance_forecast: pd.DataFrame  # future performance predictions
    degradation_causes: Dict[str, List[str]]  # parameter -> likely causes
    intervention_points: Dict[str, float]  # parameter -> time until intervention needed


@dataclass
class ConsumptionForecast:
    """Results from fuel consumption forecasting."""

    forecast_values: np.ndarray
    forecast_confidence_intervals: np.ndarray
    seasonal_patterns: Dict[str, float]
    consumption_drivers: List[Tuple[str, float]]  # factor, influence
    efficiency_projections: Dict[str, float]  # scenario -> consumption
    cost_projections: Dict[str, float]  # scenario -> cost


class PredictiveAnalyzer:
    """Advanced predictive analysis for FuelTune telemetry data."""

    def __init__(self, prediction_horizon_days: int = 30):
        """
        Initialize predictive analyzer.

        Args:
            prediction_horizon_days: Days ahead to predict
        """
        self.prediction_horizon = prediction_horizon_days
        self.logger = logger

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Standard analyze method for predictive analysis.

        Args:
            data: Input DataFrame with telemetry data

        Returns:
            Dictionary with comprehensive predictive analysis results
        """
        try:
            results = {}

            # Failure prediction
            try:
                failure_results = self.predict_failures(data)
                results["failure_prediction"] = failure_results
            except Exception as e:
                self.logger.warning(f"Failure prediction failed: {e}")

            # Maintenance scheduling
            try:
                maintenance = self.schedule_maintenance(data)
                results["maintenance_schedule"] = maintenance
            except Exception as e:
                self.logger.warning(f"Maintenance scheduling failed: {e}")

            # Performance degradation analysis
            try:
                degradation = self.analyze_performance_degradation(data)
                results["performance_degradation"] = degradation
            except Exception as e:
                self.logger.warning(f"Performance degradation analysis failed: {e}")

            # Consumption forecasting if fuel data available
            fuel_cols = [col for col in data.columns if "fuel" in col.lower()]
            if fuel_cols:
                try:
                    consumption = self.forecast_consumption(data, consumption_col=fuel_cols[0])
                    results["consumption_forecast"] = consumption
                except Exception as e:
                    self.logger.warning(f"Consumption forecasting failed: {e}")

            if not results:
                results["warning"] = "No predictive analysis could be performed"
                results["available_columns"] = list(data.columns)

            return results

        except Exception as e:
            self.logger.error(f"Predictive analysis failed: {e}")
            return {"error": str(e)}

    @cache_result("analysis", ttl=7200)  # Cache for 2 hours
    def predict_failures(
        self,
        data: pd.DataFrame,
        component_columns: Optional[Dict[str, List[str]]] = None,
    ) -> FailurePredictionResults:
        """
        Predict component failures using anomaly detection and trend analysis.

        Args:
            data: DataFrame with sensor data
            component_columns: Dictionary mapping components to their sensor columns

        Returns:
            FailurePredictionResults object
        """
        try:
            if component_columns is None:
                # Default component mapping
                component_columns = {
                    "engine": ["engine_rpm", "engine_load", "coolant_temp", "oil_pressure"],
                    "transmission": ["gear", "transmission_temp"],
                    "fuel_system": ["fuel_pressure", "fuel_flow_rate", "fuel_temp"],
                    "exhaust": ["lambda_sensor", "exhaust_temp"],
                    "electrical": ["battery_voltage", "alternator_output"],
                }

            failure_probability = {}
            risk_factors = {}
            health_scores = {}
            trend_analysis = {}
            maintenance_alerts = []

            for component, columns in component_columns.items():
                # Get available columns for this component
                available_columns = [col for col in columns if col in data.columns]

                if not available_columns:
                    # No data available for this component
                    failure_probability[component] = 0.0
                    risk_factors[component] = []
                    health_scores[component] = 100.0
                    trend_analysis[component] = 0.0
                    continue

                # Extract component data
                component_data = data[available_columns].dropna()

                if len(component_data) < 10:
                    # Insufficient data
                    failure_probability[component] = 0.0
                    risk_factors[component] = []
                    health_scores[component] = 100.0
                    trend_analysis[component] = 0.0
                    continue

                # Anomaly detection to identify abnormal patterns
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(component_data)

                # Use Isolation Forest for anomaly detection
                iso_forest = IsolationForest(contamination=0.1, random_state=42, n_jobs=-1)
                anomaly_scores = iso_forest.fit_predict(scaled_data)

                # Calculate failure probability based on anomaly rate
                anomaly_rate = np.sum(anomaly_scores == -1) / len(anomaly_scores)
                base_failure_prob = min(anomaly_rate * 10, 0.95)  # Scale and cap

                # Trend analysis for each parameter
                component_trends = {}
                component_risk_factors = []

                for col in available_columns:
                    values = component_data[col].values
                    time_indices = np.arange(len(values))

                    # Linear trend
                    if len(values) > 5:
                        slope, intercept, r_value, p_value, std_err = stats.linregress(
                            time_indices, values
                        )
                        component_trends[col] = slope

                        # Determine if trend is concerning
                        if abs(r_value) > 0.3 and p_value < 0.05:
                            # Significant trend detected
                            trend_concern = abs(slope) * len(values)  # Projected change
                            component_risk_factors.append((col, trend_concern))

                # Overall trend for component
                trend_slopes = list(component_trends.values())
                avg_trend = np.mean([abs(slope) for slope in trend_slopes]) if trend_slopes else 0

                # Adjust failure probability based on trends
                trend_multiplier = 1 + (avg_trend * 0.1)
                adjusted_failure_prob = min(base_failure_prob * trend_multiplier, 0.95)

                # Health score (inverse of failure probability)
                health_score = max(0, 100 * (1 - adjusted_failure_prob))

                # Store results
                failure_probability[component] = adjusted_failure_prob
                risk_factors[component] = sorted(
                    component_risk_factors, key=lambda x: x[1], reverse=True
                )[:5]
                health_scores[component] = health_score
                trend_analysis[component] = avg_trend

                # Generate maintenance alerts
                if adjusted_failure_prob > 0.7:
                    severity = "Critical"
                    days_until = max(1, int((1 - adjusted_failure_prob) * 30))
                elif adjusted_failure_prob > 0.4:
                    severity = "High"
                    days_until = max(7, int((1 - adjusted_failure_prob) * 60))
                elif adjusted_failure_prob > 0.2:
                    severity = "Medium"
                    days_until = max(30, int((1 - adjusted_failure_prob) * 90))
                else:
                    continue  # No alert needed

                maintenance_alerts.append(
                    {
                        "component": component,
                        "severity": severity,
                        "days_until": days_until,
                        "description": f"{component.title()} shows {severity.lower()} failure risk",
                        "probability": adjusted_failure_prob,
                    }
                )

            # Sort alerts by severity and probability
            severity_order = {"Critical": 3, "High": 2, "Medium": 1}
            maintenance_alerts.sort(
                key=lambda x: (severity_order.get(x["severity"], 0), x["probability"]), reverse=True
            )

            return FailurePredictionResults(
                failure_probability=failure_probability,
                risk_factors=risk_factors,
                maintenance_alerts=maintenance_alerts,
                health_scores=health_scores,
                trend_analysis=trend_analysis,
            )

        except Exception as e:
            self.logger.error(f"Error in failure prediction: {e}")
            raise

    @cache_result("analysis", ttl=7200)
    def forecast_consumption(
        self,
        data: pd.DataFrame,
        consumption_col: str = "fuel_flow_rate",
        feature_cols: Optional[List[str]] = None,
    ) -> ConsumptionForecast:
        """
        Forecast fuel consumption using machine learning.

        Args:
            data: DataFrame with historical consumption data
            consumption_col: Column name for fuel consumption
            feature_cols: Optional list of feature columns

        Returns:
            ConsumptionForecast object
        """
        try:
            if consumption_col not in data.columns:
                raise ValueError(f"Consumption column '{consumption_col}' not found")

            # Prepare features
            if feature_cols is None:
                # Auto-select numeric features
                numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
                feature_cols = [col for col in numeric_cols if col != consumption_col][
                    :10
                ]  # Limit features

            available_features = [col for col in feature_cols if col in data.columns]

            if not available_features:
                raise ValueError("No suitable feature columns found")

            # Clean data
            clean_data = data[[consumption_col] + available_features].dropna()

            if len(clean_data) < 20:
                raise ValueError("Insufficient data for consumption forecasting")

            # Prepare training data
            X = clean_data[available_features].values
            y = clean_data[consumption_col].values

            # Add time-based features if we have enough data
            if len(clean_data) > 50:
                time_index = np.arange(len(clean_data)).reshape(-1, 1)
                X = np.column_stack([X, time_index])
                available_features = available_features + ["time_index"]

            # Split data for validation
            test_size = min(0.2, 0.3)  # Use less for small datasets
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train ensemble model
            models = [
                ("rf", RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)),
                ("lr", LinearRegression()),
            ]

            predictions = []
            model_scores = []

            for name, model in models:
                try:
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    score = r2_score(y_test, y_pred)
                    predictions.append(y_pred)
                    model_scores.append(max(0, score))  # Ensure non-negative
                except Exception as e:
                    self.logger.warning(f"Model {name} failed: {e}")
                    continue

            if not predictions:
                raise ValueError("All forecasting models failed")

            # Weighted ensemble prediction
            if len(predictions) > 1 and sum(model_scores) > 0:
                weights = np.array(model_scores) / sum(model_scores)
                ensemble_pred = np.average(predictions, axis=0, weights=weights)
            else:
                ensemble_pred = predictions[0]

            # Generate forecast for prediction horizon
            forecast_steps = min(
                self.prediction_horizon, len(clean_data) // 4
            )  # Limit forecast horizon

            # Use last known values as starting point
            last_values = X[-1:].copy()
            forecasts = []

            # Simple approach: use best performing model for forecasting
            best_model_idx = np.argmax(model_scores) if model_scores else 0
            best_model = models[best_model_idx][1]

            for step in range(forecast_steps):
                # Predict next value
                last_scaled = scaler.transform(last_values)
                next_pred = best_model.predict(last_scaled)[0]
                forecasts.append(next_pred)

                # Update features for next prediction (simplified)
                if len(available_features) > 1:
                    # Increment time index if present
                    if "time_index" in available_features:
                        time_idx = available_features.index("time_index")
                        last_values[0, time_idx] += 1

                    # Use predicted value to update dependent features (simple assumption)
                    last_values[0, 0] = next_pred  # Update first feature with prediction

            forecast_values = np.array(forecasts)

            # Calculate confidence intervals (simplified)
            residuals = y_test - ensemble_pred
            residual_std = np.std(residuals)
            confidence_intervals = np.column_stack(
                [
                    forecast_values - 1.96 * residual_std,
                    forecast_values + 1.96 * residual_std,
                ]
            )

            # Analyze seasonal patterns (simplified)
            seasonal_patterns = {}
            if len(clean_data) > 24:  # Need sufficient data
                # Simple seasonal analysis
                consumption_values = clean_data[consumption_col].values

                # Weekly pattern (assume 7-point cycle)
                if len(consumption_values) >= 14:
                    weekly_cycle = len(consumption_values) // 7
                    if weekly_cycle > 0:
                        weekly_avg = np.mean(
                            consumption_values[: weekly_cycle * 7].reshape(-1, 7), axis=0
                        )
                        seasonal_patterns["weekly"] = float(np.std(weekly_avg))

                # Daily pattern (assume 24-point cycle)
                if len(consumption_values) >= 48:
                    daily_cycle = len(consumption_values) // 24
                    if daily_cycle > 0:
                        daily_avg = np.mean(
                            consumption_values[: daily_cycle * 24].reshape(-1, 24), axis=0
                        )
                        seasonal_patterns["daily"] = float(np.std(daily_avg))

            # Identify consumption drivers
            consumption_drivers = []
            if len(available_features) > 0 and len(models) > 0:
                # Use Random Forest feature importance if available
                rf_model = next((m for name, m in models if name == "rf"), None)
                if rf_model and hasattr(rf_model, "feature_importances_"):
                    importance_scores = rf_model.feature_importances_
                    for i, feature in enumerate(available_features[: len(importance_scores)]):
                        if importance_scores[i] > 0.01:  # Threshold for relevance
                            consumption_drivers.append((feature, float(importance_scores[i])))

                    consumption_drivers.sort(key=lambda x: x[1], reverse=True)

            # Generate efficiency projections
            current_avg_consumption = np.mean(y_train)
            efficiency_projections = {
                "current": current_avg_consumption,
                "optimistic": current_avg_consumption * 0.9,  # 10% improvement
                "pessimistic": current_avg_consumption * 1.1,  # 10% degradation
                "forecast_avg": (
                    np.mean(forecast_values)
                    if len(forecast_values) > 0
                    else current_avg_consumption
                ),
            }

            # Cost projections (simplified)
            fuel_price_per_unit = 1.5  # Default price
            cost_projections = {
                scenario: consumption * fuel_price_per_unit * forecast_steps
                for scenario, consumption in efficiency_projections.items()
            }

            return ConsumptionForecast(
                forecast_values=forecast_values,
                forecast_confidence_intervals=confidence_intervals,
                seasonal_patterns=seasonal_patterns,
                consumption_drivers=consumption_drivers,
                efficiency_projections=efficiency_projections,
                cost_projections=cost_projections,
            )

        except Exception as e:
            self.logger.error(f"Error in consumption forecasting: {e}")
            raise

    def create_predictive_plots(
        self,
        failure_prediction: Optional[FailurePredictionResults] = None,
        consumption_forecast: Optional[ConsumptionForecast] = None,
        title: str = "Predictive Analysis",
    ) -> Dict[str, go.Figure]:
        """
        Create comprehensive predictive analysis plots.

        Args:
            failure_prediction: Failure prediction results
            consumption_forecast: Consumption forecast results
            title: Base title for plots

        Returns:
            Dictionary of plot names -> plotly figures
        """
        try:
            plots = {}

            # 1. Component health dashboard
            if failure_prediction:
                fig_health = go.Figure()

                components = list(failure_prediction.health_scores.keys())
                health_scores = list(failure_prediction.health_scores.values())
                failure_probs = [
                    failure_prediction.failure_probability[comp] * 100 for comp in components
                ]

                # Health scores bar chart
                fig_health.add_trace(
                    go.Bar(
                        x=components,
                        y=health_scores,
                        name="Health Score",
                        marker_color="green",
                        yaxis="y",
                    )
                )

                # Failure probability line
                fig_health.add_trace(
                    go.Scatter(
                        x=components,
                        y=failure_probs,
                        mode="lines+markers",
                        name="Failure Probability (%)",
                        line=dict(color="red", width=2),
                        marker=dict(size=8),
                        yaxis="y2",
                    )
                )

                fig_health.update_layout(
                    title=f"{title} - Component Health Dashboard",
                    xaxis_title="Components",
                    yaxis=dict(title="Health Score", range=[0, 100]),
                    yaxis2=dict(
                        title="Failure Probability (%)",
                        overlaying="y",
                        side="right",
                        range=[0, 100],
                    ),
                    showlegend=True,
                )
                plots["component_health"] = fig_health

                # Maintenance alerts timeline
                if failure_prediction.maintenance_alerts:
                    fig_alerts = go.Figure()

                    for alert in failure_prediction.maintenance_alerts:
                        severity_colors = {"Critical": "red", "High": "orange", "Medium": "yellow"}
                        color = severity_colors.get(alert["severity"], "blue")

                        fig_alerts.add_trace(
                            go.Scatter(
                                x=[alert["days_until"]],
                                y=[alert["component"]],
                                mode="markers",
                                marker=dict(
                                    size=20,
                                    color=color,
                                    symbol="diamond",
                                ),
                                name=f'{alert["severity"]} Alert',
                                text=alert["description"],
                                textposition="middle right",
                            )
                        )

                    fig_alerts.update_layout(
                        title=f"{title} - Maintenance Alerts Timeline",
                        xaxis_title="Days Until Maintenance",
                        yaxis_title="Components",
                        showlegend=False,
                    )
                    plots["maintenance_alerts"] = fig_alerts

            # 2. Consumption forecast
            if consumption_forecast:
                fig_forecast = go.Figure()

                # Historical baseline (simplified)
                historical_steps = len(consumption_forecast.forecast_values)
                historical_x = list(range(-historical_steps, 0))

                # Use mean of forecast for historical approximation
                historical_y = [np.mean(consumption_forecast.forecast_values)] * historical_steps

                # Historical data
                fig_forecast.add_trace(
                    go.Scatter(
                        x=historical_x,
                        y=historical_y,
                        mode="lines",
                        name="Historical",
                        line=dict(color="blue", width=2),
                    )
                )

                # Forecast
                forecast_x = list(range(len(consumption_forecast.forecast_values)))
                fig_forecast.add_trace(
                    go.Scatter(
                        x=forecast_x,
                        y=consumption_forecast.forecast_values,
                        mode="lines+markers",
                        name="Forecast",
                        line=dict(color="red", width=2, dash="dash"),
                        marker=dict(size=6),
                    )
                )

                # Confidence intervals
                if len(consumption_forecast.forecast_confidence_intervals) > 0:
                    fig_forecast.add_trace(
                        go.Scatter(
                            x=forecast_x,
                            y=consumption_forecast.forecast_confidence_intervals[:, 1],
                            mode="lines",
                            line=dict(width=0),
                            showlegend=False,
                        )
                    )

                    fig_forecast.add_trace(
                        go.Scatter(
                            x=forecast_x,
                            y=consumption_forecast.forecast_confidence_intervals[:, 0],
                            mode="lines",
                            line=dict(width=0),
                            fill="tonexty",
                            fillcolor="rgba(255, 0, 0, 0.2)",
                            name="95% Confidence Interval",
                        )
                    )

                fig_forecast.update_layout(
                    title=f"{title} - Fuel Consumption Forecast",
                    xaxis_title="Time Steps",
                    yaxis_title="Fuel Consumption",
                    hovermode="x unified",
                )
                plots["consumption_forecast"] = fig_forecast

                # Consumption drivers
                if consumption_forecast.consumption_drivers:
                    drivers_data = consumption_forecast.consumption_drivers[:8]  # Top 8

                    fig_drivers = go.Figure(
                        data=go.Bar(
                            x=[driver[1] for driver in drivers_data],
                            y=[driver[0] for driver in drivers_data],
                            orientation="h",
                            marker_color="lightblue",
                        )
                    )

                    fig_drivers.update_layout(
                        title=f"{title} - Consumption Drivers",
                        xaxis_title="Importance Score",
                        yaxis_title="Factors",
                    )
                    plots["consumption_drivers"] = fig_drivers

            return plots

        except Exception as e:
            self.logger.error(f"Error creating predictive plots: {e}")
            raise

    def generate_predictive_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive predictive analysis summary.

        Args:
            data: DataFrame with vehicle/engine data

        Returns:
            Dictionary with all predictive analysis results
        """
        try:
            results = {}

            # Failure Prediction
            try:
                failure_results = self.predict_failures(data)
                results["failure_prediction"] = failure_results
            except Exception as e:
                self.logger.warning(f"Failure prediction failed: {e}")

            # Consumption Forecasting
            try:
                consumption_results = self.forecast_consumption(data)
                results["consumption_forecast"] = consumption_results
            except Exception as e:
                self.logger.warning(f"Consumption forecasting failed: {e}")

            # Create plots
            plots = self.create_predictive_plots(
                failure_prediction=results.get("failure_prediction"),
                consumption_forecast=results.get("consumption_forecast"),
            )
            results["plots"] = plots

            # Summary statistics
            summary_stats = {}

            if "failure_prediction" in results:
                fp = results["failure_prediction"]
                summary_stats["avg_component_health"] = np.mean(list(fp.health_scores.values()))
                summary_stats["critical_alerts"] = len(
                    [a for a in fp.maintenance_alerts if a["severity"] == "Critical"]
                )
                summary_stats["components_at_risk"] = len(
                    [p for p in fp.failure_probability.values() if p > 0.3]
                )

            if "consumption_forecast" in results:
                cf = results["consumption_forecast"]
                if len(cf.forecast_values) > 0:
                    summary_stats["forecast_trend"] = (
                        "increasing"
                        if cf.forecast_values[-1] > cf.forecast_values[0]
                        else "decreasing"
                    )
                    summary_stats["forecast_change_percent"] = (
                        ((cf.forecast_values[-1] - cf.forecast_values[0]) / cf.forecast_values[0])
                        * 100
                        if cf.forecast_values[0] != 0
                        else 0
                    )

            results["summary_stats"] = summary_stats

            return results

        except Exception as e:
            self.logger.error(f"Error generating predictive summary: {e}")
            raise
