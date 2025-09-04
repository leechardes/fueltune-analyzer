"""
Data normalization and cleaning module for FuelTech data.

Handles data cleaning, outlier detection, missing value imputation,
and unit conversions for both 37-field and 64-field formats.

Author: A02-DATA-PANDAS Agent
Created: 2025-01-02
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class NormalizationError(Exception):
    """Exception raised during data normalization."""


class DataNormalizer:
    """
    Comprehensive data normalizer for FuelTech data.

    Features:
    - Outlier detection and handling
    - Missing value imputation
    - Unit conversions
    - Data smoothing and filtering
    - Statistical normalization
    """

    # Default value ranges for outlier detection
    FIELD_RANGES = {
        # Core engine parameters
        "time": (0, 86400),  # 0 to 24 hours
        "rpm": (0, 15000),
        "tps": (0, 100),
        "throttle_position": (0, 100),
        "ignition_timing": (-45, 60),
        "map": (-1.5, 5.0),
        # Lambda and fuel
        "closed_loop_target": (0.5, 1.5),
        "closed_loop_o2": (0.5, 1.5),
        "closed_loop_correction": (-50, 50),
        "o2_general": (0.5, 1.5),
        "ethanol_content": (0, 100),
        # Fuel system
        "fuel_temp": (-40, 150),
        "flow_bank_a": (0, 10000),
        "injection_phase_angle": (0, 720),
        "injector_duty_a": (0, 100),
        "injection_time_a": (0, 100),
        "fuel_pressure": (0, 10),
        "fuel_level": (0, 100),
        # Temperatures
        "engine_temp": (-40, 200),
        "air_temp": (-40, 150),
        # Electrical
        "oil_pressure": (0, 10),
        "battery_voltage": (8, 18),
        "ignition_dwell": (0, 20),
        "fan1_enrichment": (-50, 50),
        # Control
        "gear": (0, 8),
        "active_adjustment": (-100, 100),
        # Extended fields (v2.0)
        "total_consumption": (0, 1000),
        "average_consumption": (0, 50),
        "instant_consumption": (0, 500),
        "total_distance": (0, 10000),
        "range": (0, 2000),
        "estimated_power": (0, 2000),
        "estimated_torque": (0, 5000),
        "traction_speed": (0, 400),
        "acceleration_speed": (0, 400),
        "acceleration_distance": (0, 10000),
        "traction_control_slip": (0, 100),
        "traction_control_slip_rate": (0, 100),
        "delta_tps": (-500, 500),
        # IMU data
        "g_force_accel": (-5, 5),
        "g_force_lateral": (-5, 5),
        "g_force_accel_raw": (-10, 10),
        "g_force_lateral_raw": (-10, 10),
        "pitch_angle": (-90, 90),
        "pitch_rate": (-360, 360),
        "roll_angle": (-180, 180),
        "roll_rate": (-360, 360),
        "heading": (0, 360),
    }

    # Fields that should be smoothed (noisy sensors)
    SMOOTH_FIELDS = [
        "rpm",
        "map",
        "tps",
        "o2_general",
        "engine_temp",
        "air_temp",
        "g_force_accel",
        "g_force_lateral",
        "pitch_angle",
        "roll_angle",
    ]

    # Fields that should never be negative
    NON_NEGATIVE_FIELDS = [
        "time",
        "rpm",
        "tps",
        "throttle_position",
        "ethanol_content",
        "gear",
        "fuel_temp",
        "flow_bank_a",
        "injection_phase_angle",
        "injector_duty_a",
        "injection_time_a",
        "fuel_pressure",
        "fuel_level",
        "oil_pressure",
        "ignition_dwell",
        "total_consumption",
        "average_consumption",
        "instant_consumption",
        "total_distance",
        "range",
        "estimated_power",
        "estimated_torque",
        "traction_speed",
        "acceleration_speed",
        "acceleration_distance",
        "traction_control_slip",
        "traction_control_slip_rate",
    ]

    def __init__(self, outlier_method: str = "iqr", smoothing_window: int = 5):
        """
        Initialize data normalizer.

        Args:
            outlier_method: Method for outlier detection ('iqr', 'zscore', 'isolation')
            smoothing_window: Window size for rolling average smoothing
        """
        self.outlier_method = outlier_method
        self.smoothing_window = smoothing_window
        self.normalization_stats = {}

    def detect_outliers(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: Optional[str] = None,
    ) -> Dict[str, pd.Series]:
        """
        Detect outliers in specified columns.

        Args:
            df: Input DataFrame
            columns: Columns to check (default: all numeric columns)
            method: Detection method ('iqr', 'zscore', 'isolation')

        Returns:
            Dictionary mapping column names to boolean Series indicating outliers
        """
        if method is None:
            method = self.outlier_method

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        outliers = {}

        for col in columns:
            if col not in df.columns:
                continue

            series = df[col].dropna()
            if len(series) == 0:
                outliers[col] = pd.Series(False, index=df.index)
                continue

            if method == "iqr":
                outliers[col] = self._detect_outliers_iqr(df[col])
            elif method == "zscore":
                outliers[col] = self._detect_outliers_zscore(df[col])
            elif method == "isolation":
                outliers[col] = self._detect_outliers_isolation(df[col])
            elif method == "range":
                outliers[col] = self._detect_outliers_range(df[col], col)
            else:
                raise ValueError(f"Unknown outlier detection method: {method}")

        return outliers

    def _detect_outliers_iqr(self, series: pd.Series, factor: float = 1.5) -> pd.Series:
        """Detect outliers using Interquartile Range method."""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR

        return (series < lower_bound) | (series > upper_bound)

    def _detect_outliers_zscore(self, series: pd.Series, threshold: float = 2.5) -> pd.Series:
        """Detect outliers using Z-score method."""
        z_scores = np.abs(stats.zscore(series.dropna()))
        outlier_mask = pd.Series(False, index=series.index)
        outlier_mask.loc[series.dropna().index] = z_scores > threshold
        return outlier_mask

    def _detect_outliers_isolation(self, series: pd.Series) -> pd.Series:
        """Detect outliers using Isolation Forest (simplified version)."""
        try:
            from sklearn.ensemble import IsolationForest

            data = series.dropna().values.reshape(-1, 1)
            if len(data) < 10:
                return pd.Series(False, index=series.index)

            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            outlier_pred = iso_forest.fit_predict(data)

            outlier_mask = pd.Series(False, index=series.index)
            outlier_mask.loc[series.dropna().index] = outlier_pred == -1
            return outlier_mask

        except ImportError:
            logger.warning("scikit-learn not available, falling back to IQR method")
            return self._detect_outliers_iqr(series)

    def _detect_outliers_range(self, series: pd.Series, column_name: str) -> pd.Series:
        """Detect outliers based on expected value ranges."""
        if column_name not in self.FIELD_RANGES:
            return pd.Series(False, index=series.index)

        min_val, max_val = self.FIELD_RANGES[column_name]
        return (series < min_val) | (series > max_val)

    def handle_outliers(
        self, df: pd.DataFrame, outliers: Dict[str, pd.Series], method: str = "clip"
    ) -> pd.DataFrame:
        """
        Handle detected outliers.

        Args:
            df: Input DataFrame
            outliers: Dictionary of outlier masks
            method: Handling method ('clip', 'remove', 'interpolate')

        Returns:
            DataFrame with outliers handled
        """
        df_clean = df.copy()

        for col, outlier_mask in outliers.items():
            if not outlier_mask.any():
                continue

            outlier_count = outlier_mask.sum()
            logger.info(
                f"Handling {outlier_count} outliers in column '{col}' using method '{method}'"
            )

            if method == "clip":
                # Clip to percentile bounds
                lower_bound = df_clean[col].quantile(0.01)
                upper_bound = df_clean[col].quantile(0.99)
                df_clean[col] = df_clean[col].clip(lower=lower_bound, upper=upper_bound)

            elif method == "remove":
                # Mark outliers as NaN (to be handled by imputation)
                df_clean.loc[outlier_mask, col] = np.nan

            elif method == "interpolate":
                # Mark outliers as NaN and interpolate
                df_clean.loc[outlier_mask, col] = np.nan
                df_clean[col] = df_clean[col].interpolate(method="linear")

            elif method == "median":
                # Replace outliers with median
                median_val = df_clean[col].median()
                df_clean.loc[outlier_mask, col] = median_val

        return df_clean

    def handle_missing_values(
        self,
        df: pd.DataFrame,
        method: str = "interpolate",
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Handle missing values in the dataset.

        Args:
            df: Input DataFrame
            method: Imputation method ('interpolate', 'forward_fill', 'median', 'mean')
            columns: Columns to process (default: all numeric columns)

        Returns:
            DataFrame with missing values handled
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        df_clean = df.copy()

        for col in columns:
            if col not in df_clean.columns:
                continue

            missing_count = df_clean[col].isna().sum()
            if missing_count == 0:
                continue

            logger.info(
                f"Handling {missing_count} missing values in column '{col}' using method '{method}'"
            )

            if method == "interpolate":
                df_clean[col] = df_clean[col].interpolate(method="linear")
                # Fill remaining NaNs at the edges
                df_clean[col] = df_clean[col].bfill().ffill()

            elif method == "forward_fill":
                df_clean[col] = df_clean[col].ffill()

            elif method == "backward_fill":
                df_clean[col] = df_clean[col].bfill()

            elif method == "median":
                median_val = df_clean[col].median()
                df_clean[col] = df_clean[col].fillna(median_val)

            elif method == "mean":
                mean_val = df_clean[col].mean()
                df_clean[col] = df_clean[col].fillna(mean_val)

            elif method == "zero":
                df_clean[col] = df_clean[col].fillna(0)

        return df_clean

    def apply_smoothing(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        window: Optional[int] = None,
        method: str = "rolling_mean",
    ) -> pd.DataFrame:
        """
        Apply smoothing to noisy columns.

        Args:
            df: Input DataFrame
            columns: Columns to smooth (default: SMOOTH_FIELDS)
            window: Smoothing window size
            method: Smoothing method ('rolling_mean', 'exponential', 'savgol')

        Returns:
            DataFrame with smoothed data
        """
        if columns is None:
            columns = [col for col in self.SMOOTH_FIELDS if col in df.columns]

        if window is None:
            window = self.smoothing_window

        df_smooth = df.copy()

        for col in columns:
            if col not in df_smooth.columns:
                continue

            logger.debug(f"Smoothing column '{col}' using method '{method}' with window {window}")

            if method == "rolling_mean":
                df_smooth[col] = df_smooth[col].rolling(window=window, center=True).mean()
                # Fill NaNs at edges
                df_smooth[col] = df_smooth[col].bfill().ffill()

            elif method == "exponential":
                df_smooth[col] = df_smooth[col].ewm(span=window).mean()

            elif method == "savgol":
                try:
                    from scipy.signal import savgol_filter

                    if len(df_smooth[col].dropna()) >= window:
                        df_smooth[col] = savgol_filter(
                            df_smooth[col].dropna(),
                            window_length=window if window % 2 == 1 else window + 1,
                            polyorder=2,
                        )
                except ImportError:
                    logger.warning("SciPy not available for Savgol filter, using rolling mean")
                    df_smooth[col] = df_smooth[col].rolling(window=window, center=True).mean()
                    # Fill NaNs at edges
                    df_smooth[col] = df_smooth[col].bfill().ffill()

        return df_smooth

    def normalize_units(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize units and apply standard conversions.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with normalized units
        """
        df_norm = df.copy()

        # Convert temperature fields that might be in Fahrenheit
        temp_fields = ["engine_temp", "air_temp", "fuel_temp"]
        for field in temp_fields:
            if field in df_norm.columns:
                # Check if values look like Fahrenheit (> 100°C is unusual)
                max_temp = df_norm[field].max()
                if max_temp > 120:  # Likely Fahrenheit
                    logger.info(f"Converting {field} from Fahrenheit to Celsius")
                    df_norm[field] = (df_norm[field] - 32) * 5 / 9

        # Ensure non-negative fields are non-negative
        for field in self.NON_NEGATIVE_FIELDS:
            if field in df_norm.columns:
                negative_count = (df_norm[field] < 0).sum()
                if negative_count > 0:
                    logger.warning(
                        f"Setting {negative_count} negative values to 0 in column '{field}'"
                    )
                    df_norm[field] = df_norm[field].clip(lower=0)

        # Normalize percentage fields to 0-100 range
        percentage_fields = [
            "tps",
            "throttle_position",
            "injector_duty_a",
            "fuel_level",
            "ethanol_content",
            "traction_control_slip",
            "traction_control_slip_rate",
        ]
        for field in percentage_fields:
            if field in df_norm.columns:
                max_val = df_norm[field].max()
                if max_val >= 1 and max_val <= 1.1:  # Likely in 0-1 range
                    logger.info(f"Converting {field} from 0-1 to 0-100 range")
                    df_norm[field] = df_norm[field] * 100

        return df_norm

    def calculate_derived_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate derived fields from existing data.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with additional derived fields
        """
        df_derived = df.copy()

        # Calculate time delta
        if "time" in df_derived.columns:
            df_derived["time_delta"] = df_derived["time"].diff()
            df_derived["time_delta"] = df_derived["time_delta"].fillna(0.04)  # Default 25Hz

        # Calculate RPM rate of change
        if "rpm" in df_derived.columns:
            df_derived["rpm_rate"] = df_derived["rpm"].diff() / df_derived.get("time_delta", 0.04)
            df_derived["rpm_rate"] = df_derived["rpm_rate"].fillna(0)

        # Calculate engine load (approximation)
        if "map" in df_derived.columns and "rpm" in df_derived.columns:
            # Simple engine load calculation: MAP * RPM / 1000
            df_derived["engine_load"] = (df_derived["map"] * df_derived["rpm"]) / 1000

        # Calculate air/fuel ratio from lambda
        if "o2_general" in df_derived.columns:
            # AFR = Lambda * Stoichiometric AFR (14.7 for gasoline)
            df_derived["afr"] = df_derived["o2_general"] * 14.7

        # Calculate power estimation if torque and RPM available
        if "estimated_torque" in df_derived.columns and "rpm" in df_derived.columns:
            # Power (HP) = Torque (Nm) * RPM / 7121
            df_derived["power_calc"] = (df_derived["estimated_torque"] * df_derived["rpm"]) / 7121

        # Calculate total G-force magnitude
        if "g_force_accel" in df_derived.columns and "g_force_lateral" in df_derived.columns:
            df_derived["g_force_total"] = np.sqrt(
                df_derived["g_force_accel"] ** 2 + df_derived["g_force_lateral"] ** 2
            )

        return df_derived

    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        outlier_method: str = "clip",
        missing_method: str = "interpolate",
        apply_smoothing: bool = True,
        calculate_derived: bool = True,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Apply full normalization pipeline to DataFrame.

        Args:
            df: Input DataFrame
            outlier_method: How to handle outliers
            missing_method: How to handle missing values
            apply_smoothing: Whether to apply smoothing
            calculate_derived: Whether to calculate derived fields

        Returns:
            Tuple of (normalized DataFrame, normalization statistics)
        """
        logger.info("Starting data normalization pipeline")

        stats = {
            "original_shape": df.shape,
            "outliers_detected": {},
            "missing_values_handled": {},
            "columns_smoothed": [],
            "derived_fields_added": [],
            "processing_steps": [],
        }

        df_norm = df.copy()

        # Step 1: Normalize units
        stats["processing_steps"].append("unit_normalization")
        df_norm = self.normalize_units(df_norm)

        # Step 2: Detect and handle outliers
        stats["processing_steps"].append("outlier_detection")
        outliers = self.detect_outliers(df_norm, method="range")
        stats["outliers_detected"] = {
            col: mask.sum() for col, mask in outliers.items() if mask.sum() > 0
        }

        if any(stats["outliers_detected"].values()):
            stats["processing_steps"].append(f"outlier_handling_{outlier_method}")
            df_norm = self.handle_outliers(df_norm, outliers, method=outlier_method)

        # Step 3: Handle missing values
        missing_before = df_norm.isna().sum()
        missing_cols = missing_before[missing_before > 0]

        if len(missing_cols) > 0:
            stats["processing_steps"].append(f"missing_value_imputation_{missing_method}")
            stats["missing_values_handled"] = missing_cols.to_dict()
            df_norm = self.handle_missing_values(df_norm, method=missing_method)

        # Step 4: Apply smoothing
        if apply_smoothing:
            stats["processing_steps"].append("data_smoothing")
            smooth_cols = [col for col in self.SMOOTH_FIELDS if col in df_norm.columns]
            if smooth_cols:
                stats["columns_smoothed"] = smooth_cols
                df_norm = self.apply_smoothing(df_norm)

        # Step 5: Calculate derived fields
        if calculate_derived:
            stats["processing_steps"].append("derived_field_calculation")
            original_cols = set(df_norm.columns)
            df_norm = self.calculate_derived_fields(df_norm)
            new_cols = set(df_norm.columns) - original_cols
            stats["derived_fields_added"] = list(new_cols)

        stats["final_shape"] = df_norm.shape
        stats["normalization_complete"] = True

        # Store normalization stats for this session
        self.normalization_stats = stats

        logger.info(f"Normalization complete: {stats['original_shape']} -> {stats['final_shape']}")

        return df_norm, stats


def normalize_fueltech_data(
    df: pd.DataFrame,
    outlier_method: str = "clip",
    missing_method: str = "interpolate",
    smoothing: bool = True,
    derived_fields: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Convenience function to normalize FuelTech data.

    Args:
        df: Input DataFrame
        outlier_method: Outlier handling method
        missing_method: Missing value handling method
        smoothing: Apply smoothing to noisy fields
        derived_fields: Calculate derived fields

    Returns:
        Tuple of (normalized DataFrame, statistics)
    """
    normalizer = DataNormalizer()

    return normalizer.normalize_dataframe(
        df=df,
        outlier_method=outlier_method,
        missing_method=missing_method,
        apply_smoothing=smoothing,
        calculate_derived=derived_fields,
    )


if __name__ == "__main__":
    # Example usage
    import pandas as pd

    # Create sample data with issues
    sample_data = pd.DataFrame(
        {
            "time": [0.0, 0.04, 0.08, 0.12, 0.16],
            "rpm": [1000, 2000, 15000, 2500, 3000],  # One outlier
            "tps": [0.0, 25.0, np.nan, 75.0, 100.0],  # One missing value
            "map": [-0.5, 0.0, 0.5, 1.0, 1.5],
            "engine_temp": [85.0, 86.0, 87.0, 200.0, 88.0],  # One outlier
        }
    )

    print("Original data:")
    print(sample_data)

    # Normalize the data
    normalized_df, stats = normalize_fueltech_data(sample_data)

    print("\nNormalized data:")
    print(normalized_df)

    print("\nNormalization statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")
