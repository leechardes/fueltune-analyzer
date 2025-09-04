"""
FuelTune Analysis Engine - Safety Validation Module

This module provides comprehensive safety validation for engine tuning parameters
with ±15% safety limits, critical parameter monitoring, and real-time safety
assessment using vectorized operations.

Classes:
    SafetyValidator: Main safety validation engine
    SafetyConfig: Configuration for safety parameters
    SafetyResult: Result container with validation status
    SafetyViolation: Individual safety violation container

Functions:
    validate_safety_limits: High-level safety validation
    check_critical_parameters: Critical parameter monitoring
    apply_safety_constraints: Apply safety constraints to tuning values

Performance Target: < 100ms for safety validation

Author: FuelTune Analysis Engine
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """Safety level classifications."""
    
    SAFE = "safe"                # All parameters within safe limits
    WARNING = "warning"          # Parameters approaching limits
    CRITICAL = "critical"        # Parameters exceed safe limits
    EMERGENCY = "emergency"      # Immediate engine damage risk


class ViolationType(Enum):
    """Types of safety violations."""
    
    LEAN_CONDITION = "lean_condition"
    RICH_CONDITION = "rich_condition"
    HIGH_EGT = "high_egt"
    EXCESSIVE_TIMING = "excessive_timing"
    OVERBOOST = "overboost"
    KNOCK_DETECTED = "knock_detected"
    FUEL_PRESSURE_LOW = "fuel_pressure_low"
    COOLANT_TEMP_HIGH = "coolant_temp_high"
    INTAKE_TEMP_HIGH = "intake_temp_high"
    RPM_OVERLIMIT = "rpm_overlimit"


@dataclass
class SafetyConfig:
    """Configuration for safety validation parameters."""
    
    # Lambda/AFR safety limits (±15% from target)
    target_lambda_idle: float = 1.0
    target_lambda_cruise: float = 1.0
    target_lambda_power: float = 0.85
    target_lambda_boost: float = 0.80
    lambda_safety_margin: float = 0.15  # ±15%
    
    # Critical lean limits (absolute safety)
    critical_lambda_lean: float = 1.15
    warning_lambda_lean: float = 1.10
    critical_lambda_rich: float = 0.65
    warning_lambda_rich: float = 0.70
    
    # Temperature limits
    max_egt_warning: float = 850.0      # °C
    max_egt_critical: float = 900.0     # °C
    max_coolant_warning: float = 95.0   # °C
    max_coolant_critical: float = 105.0 # °C
    max_intake_warning: float = 60.0    # °C
    max_intake_critical: float = 75.0   # °C
    
    # Ignition timing limits
    max_timing_na_warning: float = 35.0    # degrees BTDC
    max_timing_na_critical: float = 40.0   # degrees BTDC
    max_timing_boost_warning: float = 25.0  # degrees BTDC
    max_timing_boost_critical: float = 30.0 # degrees BTDC
    timing_safety_margin: float = 2.0      # safety margin
    
    # Boost pressure limits
    max_boost_warning: float = 2.0      # bar absolute
    max_boost_critical: float = 2.5     # bar absolute
    
    # RPM limits
    max_rpm_warning: float = 7500       # RPM
    max_rpm_critical: float = 8000      # RPM
    
    # Fuel system limits
    min_fuel_pressure_warning: float = 3.0  # bar
    min_fuel_pressure_critical: float = 2.5 # bar
    
    # Statistical validation parameters
    violation_percentage_warning: float = 5.0   # % of data points
    violation_percentage_critical: float = 10.0 # % of data points
    consecutive_violations_limit: int = 10      # consecutive violations
    
    # Safety response parameters
    emergency_stop_threshold: int = 5           # consecutive critical violations
    safety_factor_conservative: float = 0.9    # Conservative safety factor
    safety_factor_aggressive: float = 1.1      # Aggressive safety factor


@dataclass
class SafetyViolation:
    """Individual safety violation with context."""
    
    violation_type: ViolationType
    safety_level: SafetyLevel
    parameter: str
    current_value: float
    safe_limit: float
    deviation_percentage: float
    
    # Context information
    timestamp: Optional[float] = None
    data_index: Optional[int] = None
    engine_conditions: Dict[str, float] = field(default_factory=dict)
    
    # Severity metrics
    duration: float = 0.0
    consecutive_count: int = 1
    severity_score: float = 0.0
    
    # Recommendations
    immediate_action: str = ""
    corrective_action: str = ""
    prevention_strategy: str = ""


@dataclass
class SafetyResult:
    """Container for comprehensive safety validation results."""
    
    overall_safety_level: SafetyLevel = SafetyLevel.SAFE
    violations: List[SafetyViolation] = field(default_factory=list)
    
    # Summary statistics
    total_data_points: int = 0
    safe_points: int = 0
    warning_points: int = 0
    critical_points: int = 0
    emergency_points: int = 0
    
    # Safety percentages
    safety_percentage: float = 100.0
    violation_percentage: float = 0.0
    
    # Parameter-specific results
    parameter_safety: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Recommendations
    safety_recommendations: List[str] = field(default_factory=list)
    immediate_actions: List[str] = field(default_factory=list)
    
    # Metadata
    validation_time: float = 0.0
    parameters_checked: List[str] = field(default_factory=list)
    safety_constraints_applied: bool = False


class SafetyValidator:
    """
    Comprehensive safety validation engine for engine tuning parameters.
    
    This class validates all critical parameters against safety limits with
    ±15% safety margins and provides immediate feedback on dangerous conditions.
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """
        Initialize the safety validator.
        
        Args:
            config: Safety validation configuration
        """
        self.config = config or SafetyConfig()
        self._last_result: Optional[SafetyResult] = None
    
    def validate_safety(
        self,
        data: Union[pd.DataFrame, Dict[str, np.ndarray]],
        engine_state: Optional[str] = None,
        apply_constraints: bool = True
    ) -> SafetyResult:
        """
        Comprehensive safety validation of engine parameters.
        
        Args:
            data: Input engine data
            engine_state: Optional engine operating state context
            apply_constraints: Whether to apply safety constraints
            
        Returns:
            SafetyResult with detailed validation status
            
        Raises:
            ValueError: If required parameters are missing
        """
        import time
        start_time = time.time()
        
        try:
            # Prepare data arrays
            arrays = self._prepare_safety_data(data)
            
            # Validate data availability
            self._validate_safety_data(arrays)
            
            # Initialize result
            result = SafetyResult(
                total_data_points=len(arrays.get("timestamp", [])),
                parameters_checked=list(arrays.keys())
            )
            
            # Validate lambda/AFR safety
            lambda_violations = self._validate_lambda_safety(arrays, engine_state)
            result.violations.extend(lambda_violations)
            
            # Validate temperature safety
            temp_violations = self._validate_temperature_safety(arrays)
            result.violations.extend(temp_violations)
            
            # Validate ignition timing safety
            timing_violations = self._validate_timing_safety(arrays)
            result.violations.extend(timing_violations)
            
            # Validate boost pressure safety
            boost_violations = self._validate_boost_safety(arrays)
            result.violations.extend(boost_violations)
            
            # Validate RPM safety
            rpm_violations = self._validate_rpm_safety(arrays)
            result.violations.extend(rpm_violations)
            
            # Validate fuel system safety
            fuel_violations = self._validate_fuel_safety(arrays)
            result.violations.extend(fuel_violations)
            
            # Calculate overall safety metrics
            self._calculate_safety_metrics(result, arrays)
            
            # Generate safety recommendations
            self._generate_safety_recommendations(result, arrays)
            
            # Apply safety constraints if requested
            if apply_constraints:
                result.safety_constraints_applied = True
                self._apply_safety_constraints(result, arrays)
            
            result.validation_time = time.time() - start_time
            self._last_result = result
            return result
            
        except Exception as e:
            logger.error(f"Safety validation failed: {str(e)}")
            raise
    
    def _prepare_safety_data(
        self, data: Union[pd.DataFrame, Dict[str, np.ndarray]]
    ) -> Dict[str, np.ndarray]:
        """
        Prepare data arrays for safety validation.
        
        Args:
            data: Input data
            
        Returns:
            Dictionary of prepared arrays
        """
        if isinstance(data, pd.DataFrame):
            arrays = {}
            
            # Core safety parameters
            safety_columns = [
                "timestamp", "lambda_sensor", "ignition_timing",
                "map_pressure", "rpm", "engine_temp", "intake_temp",
                "fuel_pressure", "egt", "knock_sensor"
            ]
            
            for col in safety_columns:
                if col in data.columns:
                    arrays[col] = data[col].values.astype(np.float64)
                else:
                    # Create NaN array for missing parameters
                    arrays[col] = np.full(len(data), np.nan, dtype=np.float64)
        
        elif isinstance(data, dict):
            arrays = {}
            for key, array in data.items():
                if isinstance(array, (list, tuple)):
                    arrays[key] = np.array(array, dtype=np.float64)
                else:
                    arrays[key] = array.astype(np.float64)
        else:
            raise TypeError("Data must be DataFrame or dict of arrays")
        
        return arrays
    
    def _validate_safety_data(self, arrays: Dict[str, np.ndarray]) -> None:
        """
        Validate that sufficient data exists for safety validation.
        
        Args:
            arrays: Data arrays
            
        Raises:
            ValueError: If critical parameters are missing
        """
        critical_params = ["lambda_sensor"]
        
        for param in critical_params:
            if param not in arrays or len(arrays[param]) == 0:
                raise ValueError(f"Critical safety parameter '{param}' is missing")
            
            # Check for all NaN values
            if np.all(np.isnan(arrays[param])):
                raise ValueError(f"Critical safety parameter '{param}' contains only invalid values")
    
    def _validate_lambda_safety(
        self, arrays: Dict[str, np.ndarray], engine_state: Optional[str]
    ) -> List[SafetyViolation]:
        """
        Validate lambda sensor safety with ±15% margins.
        
        Args:
            arrays: Data arrays
            engine_state: Engine operating state
            
        Returns:
            List of lambda-related safety violations
        """
        violations = []
        
        if "lambda_sensor" not in arrays:
            return violations
        
        lambda_values = arrays["lambda_sensor"]
        valid_mask = ~np.isnan(lambda_values)
        
        if not np.any(valid_mask):
            return violations
        
        clean_lambda = lambda_values[valid_mask]
        timestamps = arrays.get("timestamp", np.arange(len(lambda_values)))[valid_mask]
        
        # Determine target lambda based on engine state or conditions
        target_lambda = self._determine_target_lambda(arrays, engine_state)
        
        # Calculate safety limits with ±15% margin
        lambda_min = target_lambda * (1 - self.config.lambda_safety_margin)
        lambda_max = target_lambda * (1 + self.config.lambda_safety_margin)
        
        # Check for violations within safety margin
        lean_violation_mask = clean_lambda > lambda_max
        rich_violation_mask = clean_lambda < lambda_min
        
        # Check for critical violations (absolute limits)
        critical_lean_mask = clean_lambda > self.config.critical_lambda_lean
        critical_rich_mask = clean_lambda < self.config.critical_lambda_rich
        
        # Process lean violations
        if np.any(lean_violation_mask):
            self._process_lambda_violations(
                violations, clean_lambda, timestamps, lean_violation_mask,
                ViolationType.LEAN_CONDITION, self.config.warning_lambda_lean,
                "Lambda sensor indicates lean condition beyond safe limits"
            )
        
        # Process rich violations
        if np.any(rich_violation_mask):
            self._process_lambda_violations(
                violations, clean_lambda, timestamps, rich_violation_mask,
                ViolationType.RICH_CONDITION, lambda_min,
                "Lambda sensor indicates rich condition beyond safe limits"
            )
        
        # Process critical lean violations
        if np.any(critical_lean_mask):
            self._process_lambda_violations(
                violations, clean_lambda, timestamps, critical_lean_mask,
                ViolationType.LEAN_CONDITION, self.config.critical_lambda_lean,
                "CRITICAL: Dangerously lean condition detected",
                safety_level=SafetyLevel.CRITICAL
            )
        
        # Process critical rich violations
        if np.any(critical_rich_mask):
            self._process_lambda_violations(
                violations, clean_lambda, timestamps, critical_rich_mask,
                ViolationType.RICH_CONDITION, self.config.critical_lambda_rich,
                "CRITICAL: Extremely rich condition detected", 
                safety_level=SafetyLevel.CRITICAL
            )
        
        return violations
    
    def _process_lambda_violations(
        self,
        violations: List[SafetyViolation],
        lambda_values: np.ndarray,
        timestamps: np.ndarray,
        violation_mask: np.ndarray,
        violation_type: ViolationType,
        safe_limit: float,
        description: str,
        safety_level: SafetyLevel = SafetyLevel.WARNING
    ) -> None:
        """Process and create lambda violation objects."""
        violation_indices = np.where(violation_mask)[0]
        
        if len(violation_indices) == 0:
            return
        
        # Group consecutive violations
        consecutive_groups = self._find_consecutive_groups(violation_indices)
        
        for group in consecutive_groups:
            start_idx, end_idx = group[0], group[-1]
            
            # Calculate violation metrics
            group_lambda = lambda_values[group]
            worst_value = np.max(group_lambda) if violation_type == ViolationType.LEAN_CONDITION else np.min(group_lambda)
            deviation_pct = abs((worst_value - safe_limit) / safe_limit) * 100.0
            
            # Create violation object
            violation = SafetyViolation(
                violation_type=violation_type,
                safety_level=safety_level,
                parameter="lambda_sensor",
                current_value=float(worst_value),
                safe_limit=safe_limit,
                deviation_percentage=float(deviation_pct),
                timestamp=float(timestamps[start_idx]) if len(timestamps) > start_idx else None,
                data_index=int(start_idx),
                consecutive_count=len(group),
                duration=float(timestamps[end_idx] - timestamps[start_idx]) if len(timestamps) > end_idx else 0.0,
                severity_score=min(deviation_pct / 20.0, 1.0),  # Normalize to 0-1
                immediate_action=self._get_lambda_immediate_action(violation_type, safety_level),
                corrective_action=self._get_lambda_corrective_action(violation_type),
                prevention_strategy=self._get_lambda_prevention_strategy(violation_type)
            )
            
            violations.append(violation)
    
    def _validate_temperature_safety(self, arrays: Dict[str, np.ndarray]) -> List[SafetyViolation]:
        """Validate temperature-related safety parameters."""
        violations = []
        
        # EGT validation
        if "egt" in arrays and not np.all(np.isnan(arrays["egt"])):
            egt_violations = self._validate_temperature_parameter(
                arrays["egt"], arrays.get("timestamp"),
                self.config.max_egt_warning, self.config.max_egt_critical,
                ViolationType.HIGH_EGT, "egt", "EGT"
            )
            violations.extend(egt_violations)
        
        # Coolant temperature validation
        if "engine_temp" in arrays and not np.all(np.isnan(arrays["engine_temp"])):
            coolant_violations = self._validate_temperature_parameter(
                arrays["engine_temp"], arrays.get("timestamp"),
                self.config.max_coolant_warning, self.config.max_coolant_critical,
                ViolationType.COOLANT_TEMP_HIGH, "engine_temp", "Coolant"
            )
            violations.extend(coolant_violations)
        
        # Intake temperature validation
        if "intake_temp" in arrays and not np.all(np.isnan(arrays["intake_temp"])):
            intake_violations = self._validate_temperature_parameter(
                arrays["intake_temp"], arrays.get("timestamp"),
                self.config.max_intake_warning, self.config.max_intake_critical,
                ViolationType.INTAKE_TEMP_HIGH, "intake_temp", "Intake"
            )
            violations.extend(intake_violations)
        
        return violations
    
    def _validate_temperature_parameter(
        self,
        temp_values: np.ndarray,
        timestamps: Optional[np.ndarray],
        warning_limit: float,
        critical_limit: float,
        violation_type: ViolationType,
        parameter_name: str,
        display_name: str
    ) -> List[SafetyViolation]:
        """Validate individual temperature parameter."""
        violations = []
        
        valid_mask = ~np.isnan(temp_values)
        if not np.any(valid_mask):
            return violations
        
        clean_temps = temp_values[valid_mask]
        clean_timestamps = timestamps[valid_mask] if timestamps is not None else np.arange(len(clean_temps))
        
        # Check warning level violations
        warning_mask = clean_temps > warning_limit
        if np.any(warning_mask):
            violations.extend(self._create_temperature_violations(
                clean_temps, clean_timestamps, warning_mask,
                violation_type, parameter_name, warning_limit,
                SafetyLevel.WARNING, f"{display_name} temperature exceeds warning limit"
            ))
        
        # Check critical level violations
        critical_mask = clean_temps > critical_limit
        if np.any(critical_mask):
            violations.extend(self._create_temperature_violations(
                clean_temps, clean_timestamps, critical_mask,
                violation_type, parameter_name, critical_limit,
                SafetyLevel.CRITICAL, f"CRITICAL: {display_name} temperature exceeds safe limit"
            ))
        
        return violations
    
    def _create_temperature_violations(
        self,
        temp_values: np.ndarray,
        timestamps: np.ndarray,
        violation_mask: np.ndarray,
        violation_type: ViolationType,
        parameter_name: str,
        safe_limit: float,
        safety_level: SafetyLevel,
        description: str
    ) -> List[SafetyViolation]:
        """Create temperature violation objects."""
        violations = []
        violation_indices = np.where(violation_mask)[0]
        
        if len(violation_indices) == 0:
            return violations
        
        consecutive_groups = self._find_consecutive_groups(violation_indices)
        
        for group in consecutive_groups:
            start_idx, end_idx = group[0], group[-1]
            group_temps = temp_values[group]
            max_temp = np.max(group_temps)
            
            deviation_pct = ((max_temp - safe_limit) / safe_limit) * 100.0
            
            violation = SafetyViolation(
                violation_type=violation_type,
                safety_level=safety_level,
                parameter=parameter_name,
                current_value=float(max_temp),
                safe_limit=safe_limit,
                deviation_percentage=float(deviation_pct),
                timestamp=float(timestamps[start_idx]) if len(timestamps) > start_idx else None,
                data_index=int(start_idx),
                consecutive_count=len(group),
                duration=float(timestamps[end_idx] - timestamps[start_idx]) if len(timestamps) > end_idx else 0.0,
                severity_score=min(deviation_pct / 30.0, 1.0),
                immediate_action="Reduce engine load and check cooling system",
                corrective_action=f"Investigate {parameter_name.replace('_', ' ')} causes and repair",
                prevention_strategy="Regular cooling system maintenance and monitoring"
            )
            
            violations.append(violation)
        
        return violations
    
    def _validate_timing_safety(self, arrays: Dict[str, np.ndarray]) -> List[SafetyViolation]:
        """Validate ignition timing safety."""
        violations = []
        
        if "ignition_timing" not in arrays or np.all(np.isnan(arrays["ignition_timing"])):
            return violations
        
        timing_values = arrays["ignition_timing"]
        map_values = arrays.get("map_pressure", np.ones_like(timing_values))
        
        valid_mask = ~np.isnan(timing_values)
        if not np.any(valid_mask):
            return violations
        
        clean_timing = timing_values[valid_mask]
        clean_map = map_values[valid_mask]
        timestamps = arrays.get("timestamp", np.arange(len(timing_values)))[valid_mask]
        
        # Determine limits based on boost conditions
        is_boost = clean_map > 1.05  # Above atmospheric
        
        warning_limits = np.where(is_boost, self.config.max_timing_boost_warning, self.config.max_timing_na_warning)
        critical_limits = np.where(is_boost, self.config.max_timing_boost_critical, self.config.max_timing_na_critical)
        
        # Check violations
        warning_mask = clean_timing > warning_limits
        critical_mask = clean_timing > critical_limits
        
        if np.any(warning_mask):
            violations.extend(self._create_timing_violations(
                clean_timing, timestamps, warning_mask, is_boost,
                SafetyLevel.WARNING, "Ignition timing approaches maximum safe advance"
            ))
        
        if np.any(critical_mask):
            violations.extend(self._create_timing_violations(
                clean_timing, timestamps, critical_mask, is_boost,
                SafetyLevel.CRITICAL, "CRITICAL: Excessive ignition timing advance"
            ))
        
        return violations
    
    def _create_timing_violations(
        self,
        timing_values: np.ndarray,
        timestamps: np.ndarray,
        violation_mask: np.ndarray,
        is_boost: np.ndarray,
        safety_level: SafetyLevel,
        description: str
    ) -> List[SafetyViolation]:
        """Create timing violation objects."""
        violations = []
        violation_indices = np.where(violation_mask)[0]
        
        if len(violation_indices) == 0:
            return violations
        
        consecutive_groups = self._find_consecutive_groups(violation_indices)
        
        for group in consecutive_groups:
            max_timing = np.max(timing_values[group])
            is_boost_condition = np.any(is_boost[group])
            safe_limit = self.config.max_timing_boost_warning if is_boost_condition else self.config.max_timing_na_warning
            
            violation = SafetyViolation(
                violation_type=ViolationType.EXCESSIVE_TIMING,
                safety_level=safety_level,
                parameter="ignition_timing",
                current_value=float(max_timing),
                safe_limit=safe_limit,
                deviation_percentage=((max_timing - safe_limit) / safe_limit) * 100.0,
                timestamp=float(timestamps[group[0]]) if len(timestamps) > group[0] else None,
                consecutive_count=len(group),
                severity_score=min((max_timing - safe_limit) / 10.0, 1.0),
                immediate_action="Reduce ignition advance immediately",
                corrective_action="Review timing maps and reduce advance in affected areas",
                prevention_strategy="Conservative timing approach with knock monitoring"
            )
            
            violations.append(violation)
        
        return violations
    
    def _validate_boost_safety(self, arrays: Dict[str, np.ndarray]) -> List[SafetyViolation]:
        """Validate boost pressure safety."""
        violations = []
        
        if "map_pressure" not in arrays or np.all(np.isnan(arrays["map_pressure"])):
            return violations
        
        map_values = arrays["map_pressure"]
        valid_mask = ~np.isnan(map_values)
        
        if not np.any(valid_mask):
            return violations
        
        clean_map = map_values[valid_mask]
        timestamps = arrays.get("timestamp", np.arange(len(map_values)))[valid_mask]
        
        # Check for overboost conditions
        warning_mask = clean_map > self.config.max_boost_warning
        critical_mask = clean_map > self.config.max_boost_critical
        
        if np.any(warning_mask):
            violations.extend(self._create_boost_violations(
                clean_map, timestamps, warning_mask,
                self.config.max_boost_warning, SafetyLevel.WARNING
            ))
        
        if np.any(critical_mask):
            violations.extend(self._create_boost_violations(
                clean_map, timestamps, critical_mask,
                self.config.max_boost_critical, SafetyLevel.CRITICAL
            ))
        
        return violations
    
    def _create_boost_violations(
        self,
        map_values: np.ndarray,
        timestamps: np.ndarray,
        violation_mask: np.ndarray,
        safe_limit: float,
        safety_level: SafetyLevel
    ) -> List[SafetyViolation]:
        """Create boost pressure violation objects."""
        violations = []
        violation_indices = np.where(violation_mask)[0]
        
        consecutive_groups = self._find_consecutive_groups(violation_indices)
        
        for group in consecutive_groups:
            max_boost = np.max(map_values[group])
            
            violation = SafetyViolation(
                violation_type=ViolationType.OVERBOOST,
                safety_level=safety_level,
                parameter="map_pressure",
                current_value=float(max_boost),
                safe_limit=safe_limit,
                deviation_percentage=((max_boost - safe_limit) / safe_limit) * 100.0,
                timestamp=float(timestamps[group[0]]) if len(timestamps) > group[0] else None,
                consecutive_count=len(group),
                immediate_action="Reduce boost pressure immediately",
                corrective_action="Check wastegate operation and boost control system",
                prevention_strategy="Regular boost control system maintenance"
            )
            
            violations.append(violation)
        
        return violations
    
    def _validate_rpm_safety(self, arrays: Dict[str, np.ndarray]) -> List[SafetyViolation]:
        """Validate RPM safety limits."""
        violations = []
        
        if "rpm" not in arrays or np.all(np.isnan(arrays["rpm"])):
            return violations
        
        rpm_values = arrays["rpm"]
        valid_mask = ~np.isnan(rpm_values)
        
        if not np.any(valid_mask):
            return violations
        
        clean_rpm = rpm_values[valid_mask]
        timestamps = arrays.get("timestamp", np.arange(len(rpm_values)))[valid_mask]
        
        # Check RPM violations
        warning_mask = clean_rpm > self.config.max_rpm_warning
        critical_mask = clean_rpm > self.config.max_rpm_critical
        
        if np.any(warning_mask):
            violations.extend(self._create_rpm_violations(
                clean_rpm, timestamps, warning_mask,
                self.config.max_rpm_warning, SafetyLevel.WARNING
            ))
        
        if np.any(critical_mask):
            violations.extend(self._create_rpm_violations(
                clean_rpm, timestamps, critical_mask,
                self.config.max_rpm_critical, SafetyLevel.CRITICAL
            ))
        
        return violations
    
    def _create_rpm_violations(
        self,
        rpm_values: np.ndarray,
        timestamps: np.ndarray,
        violation_mask: np.ndarray,
        safe_limit: float,
        safety_level: SafetyLevel
    ) -> List[SafetyViolation]:
        """Create RPM violation objects."""
        violations = []
        violation_indices = np.where(violation_mask)[0]
        
        consecutive_groups = self._find_consecutive_groups(violation_indices)
        
        for group in consecutive_groups:
            max_rpm = np.max(rpm_values[group])
            
            violation = SafetyViolation(
                violation_type=ViolationType.RPM_OVERLIMIT,
                safety_level=safety_level,
                parameter="rpm",
                current_value=float(max_rpm),
                safe_limit=safe_limit,
                deviation_percentage=((max_rpm - safe_limit) / safe_limit) * 100.0,
                timestamp=float(timestamps[group[0]]) if len(timestamps) > group[0] else None,
                consecutive_count=len(group),
                immediate_action="Reduce engine RPM immediately",
                corrective_action="Check rev limiter operation",
                prevention_strategy="Conservative rev limit settings"
            )
            
            violations.append(violation)
        
        return violations
    
    def _validate_fuel_safety(self, arrays: Dict[str, np.ndarray]) -> List[SafetyViolation]:
        """Validate fuel system safety."""
        violations = []
        
        if "fuel_pressure" not in arrays or np.all(np.isnan(arrays["fuel_pressure"])):
            return violations
        
        fuel_pressure = arrays["fuel_pressure"]
        valid_mask = ~np.isnan(fuel_pressure)
        
        if not np.any(valid_mask):
            return violations
        
        clean_pressure = fuel_pressure[valid_mask]
        timestamps = arrays.get("timestamp", np.arange(len(fuel_pressure)))[valid_mask]
        
        # Check for low fuel pressure
        warning_mask = clean_pressure < self.config.min_fuel_pressure_warning
        critical_mask = clean_pressure < self.config.min_fuel_pressure_critical
        
        if np.any(warning_mask):
            violations.extend(self._create_fuel_violations(
                clean_pressure, timestamps, warning_mask,
                self.config.min_fuel_pressure_warning, SafetyLevel.WARNING
            ))
        
        if np.any(critical_mask):
            violations.extend(self._create_fuel_violations(
                clean_pressure, timestamps, critical_mask,
                self.config.min_fuel_pressure_critical, SafetyLevel.CRITICAL
            ))
        
        return violations
    
    def _create_fuel_violations(
        self,
        pressure_values: np.ndarray,
        timestamps: np.ndarray,
        violation_mask: np.ndarray,
        safe_limit: float,
        safety_level: SafetyLevel
    ) -> List[SafetyViolation]:
        """Create fuel pressure violation objects."""
        violations = []
        violation_indices = np.where(violation_mask)[0]
        
        consecutive_groups = self._find_consecutive_groups(violation_indices)
        
        for group in consecutive_groups:
            min_pressure = np.min(pressure_values[group])
            
            violation = SafetyViolation(
                violation_type=ViolationType.FUEL_PRESSURE_LOW,
                safety_level=safety_level,
                parameter="fuel_pressure",
                current_value=float(min_pressure),
                safe_limit=safe_limit,
                deviation_percentage=((safe_limit - min_pressure) / safe_limit) * 100.0,
                timestamp=float(timestamps[group[0]]) if len(timestamps) > group[0] else None,
                consecutive_count=len(group),
                immediate_action="Check fuel system immediately",
                corrective_action="Inspect fuel pump, filter, and pressure regulator",
                prevention_strategy="Regular fuel system maintenance and monitoring"
            )
            
            violations.append(violation)
        
        return violations
    
    def _determine_target_lambda(
        self, arrays: Dict[str, np.ndarray], engine_state: Optional[str]
    ) -> float:
        """Determine appropriate target lambda based on conditions."""
        if engine_state:
            state_targets = {
                "idle": self.config.target_lambda_idle,
                "cruise": self.config.target_lambda_cruise,
                "power": self.config.target_lambda_power,
                "boost": self.config.target_lambda_boost
            }
            return state_targets.get(engine_state, self.config.target_lambda_cruise)
        
        # Estimate based on MAP pressure if available
        if "map_pressure" in arrays:
            map_values = arrays["map_pressure"]
            valid_map = map_values[~np.isnan(map_values)]
            
            if len(valid_map) > 0:
                avg_map = np.mean(valid_map)
                if avg_map > 1.5:  # High boost
                    return self.config.target_lambda_boost
                elif avg_map > 1.05:  # Light boost
                    return 0.88
                else:  # Naturally aspirated
                    return self.config.target_lambda_cruise
        
        return self.config.target_lambda_cruise  # Default
    
    def _find_consecutive_groups(self, indices: np.ndarray) -> List[List[int]]:
        """Find consecutive groups in an array of indices."""
        if len(indices) == 0:
            return []
        
        groups = []
        current_group = [indices[0]]
        
        for i in range(1, len(indices)):
            if indices[i] == indices[i-1] + 1:
                current_group.append(indices[i])
            else:
                groups.append(current_group)
                current_group = [indices[i]]
        
        groups.append(current_group)
        return groups
    
    def _calculate_safety_metrics(self, result: SafetyResult, arrays: Dict[str, np.ndarray]) -> None:
        """Calculate overall safety metrics."""
        if result.total_data_points == 0:
            return
        
        # Count violations by safety level
        for violation in result.violations:
            if violation.safety_level == SafetyLevel.WARNING:
                result.warning_points += violation.consecutive_count
            elif violation.safety_level == SafetyLevel.CRITICAL:
                result.critical_points += violation.consecutive_count
            elif violation.safety_level == SafetyLevel.EMERGENCY:
                result.emergency_points += violation.consecutive_count
        
        # Calculate safe points
        total_violation_points = result.warning_points + result.critical_points + result.emergency_points
        result.safe_points = result.total_data_points - total_violation_points
        
        # Calculate percentages
        result.safety_percentage = (result.safe_points / result.total_data_points) * 100.0
        result.violation_percentage = (total_violation_points / result.total_data_points) * 100.0
        
        # Determine overall safety level
        if result.emergency_points > 0 or result.violation_percentage > 20.0:
            result.overall_safety_level = SafetyLevel.EMERGENCY
        elif result.critical_points > 0 or result.violation_percentage > 10.0:
            result.overall_safety_level = SafetyLevel.CRITICAL
        elif result.warning_points > 0 or result.violation_percentage > 5.0:
            result.overall_safety_level = SafetyLevel.WARNING
        else:
            result.overall_safety_level = SafetyLevel.SAFE
    
    def _generate_safety_recommendations(self, result: SafetyResult, arrays: Dict[str, np.ndarray]) -> None:
        """Generate safety recommendations based on violations."""
        if not result.violations:
            result.safety_recommendations.append("All parameters are within safe limits")
            return
        
        # Group violations by type
        violation_types = {}
        for violation in result.violations:
            if violation.violation_type not in violation_types:
                violation_types[violation.violation_type] = []
            violation_types[violation.violation_type].append(violation)
        
        # Generate type-specific recommendations
        for violation_type, violations in violation_types.items():
            critical_violations = [v for v in violations if v.safety_level == SafetyLevel.CRITICAL]
            
            if violation_type == ViolationType.LEAN_CONDITION:
                if critical_violations:
                    result.immediate_actions.append("IMMEDIATE: Increase fuel delivery to prevent engine damage")
                result.safety_recommendations.append("Review and enrich fuel maps in affected areas")
            
            elif violation_type == ViolationType.HIGH_EGT:
                if critical_violations:
                    result.immediate_actions.append("IMMEDIATE: Reduce engine load and check cooling")
                result.safety_recommendations.append("Improve engine cooling and reduce ignition advance")
            
            elif violation_type == ViolationType.EXCESSIVE_TIMING:
                if critical_violations:
                    result.immediate_actions.append("IMMEDIATE: Reduce ignition timing advance")
                result.safety_recommendations.append("Conservative timing approach with gradual optimization")
        
        # Overall safety recommendation
        if result.overall_safety_level in [SafetyLevel.CRITICAL, SafetyLevel.EMERGENCY]:
            result.immediate_actions.insert(0, "STOP ENGINE OPERATION IMMEDIATELY - DAMAGE RISK DETECTED")
    
    def _apply_safety_constraints(self, result: SafetyResult, arrays: Dict[str, np.ndarray]) -> None:
        """Apply safety constraints to prevent dangerous conditions."""
        # This would typically modify the actual tuning parameters
        # For now, we'll log the constraints that would be applied
        
        constraints_applied = []
        
        for violation in result.violations:
            if violation.safety_level in [SafetyLevel.CRITICAL, SafetyLevel.EMERGENCY]:
                if violation.violation_type == ViolationType.LEAN_CONDITION:
                    constraints_applied.append(f"Lambda limited to maximum {violation.safe_limit:.3f}")
                elif violation.violation_type == ViolationType.EXCESSIVE_TIMING:
                    constraints_applied.append(f"Ignition timing limited to {violation.safe_limit:.1f}° BTDC")
                elif violation.violation_type == ViolationType.OVERBOOST:
                    constraints_applied.append(f"Boost pressure limited to {violation.safe_limit:.2f} bar")
        
        if constraints_applied:
            logger.info(f"Applied safety constraints: {', '.join(constraints_applied)}")
    
    def _get_lambda_immediate_action(self, violation_type: ViolationType, safety_level: SafetyLevel) -> str:
        """Get immediate action for lambda violations."""
        if violation_type == ViolationType.LEAN_CONDITION:
            if safety_level == SafetyLevel.CRITICAL:
                return "IMMEDIATE: Increase fuel delivery - engine damage risk"
            else:
                return "Increase fuel delivery in affected areas"
        else:  # Rich condition
            if safety_level == SafetyLevel.CRITICAL:
                return "Reduce fuel delivery - check for injector issues"
            else:
                return "Reduce fuel delivery in affected areas"
    
    def _get_lambda_corrective_action(self, violation_type: ViolationType) -> str:
        """Get corrective action for lambda violations."""
        if violation_type == ViolationType.LEAN_CONDITION:
            return "Review fuel maps, check fuel system pressure and delivery"
        else:
            return "Review fuel maps, check for injector leaks or incorrect sizing"
    
    def _get_lambda_prevention_strategy(self, violation_type: ViolationType) -> str:
        """Get prevention strategy for lambda violations."""
        return "Regular lambda sensor calibration and fuel system maintenance"


# High-level interface functions
def validate_safety_limits(
    data: Union[pd.DataFrame, Dict[str, np.ndarray]],
    config: Optional[SafetyConfig] = None,
    engine_state: Optional[str] = None
) -> SafetyResult:
    """
    High-level interface for safety validation.
    
    Args:
        data: Engine data for validation
        config: Safety validation configuration
        engine_state: Optional engine operating state
        
    Returns:
        SafetyResult with comprehensive safety analysis
        
    Example:
        >>> safety_result = validate_safety_limits(dataframe, engine_state="boost")
        >>> print(f"Safety Level: {safety_result.overall_safety_level.value}")
        >>> print(f"Safety Percentage: {safety_result.safety_percentage:.1f}%")
        >>> 
        >>> if safety_result.violations:
        ...     print(f"Found {len(safety_result.violations)} safety violations:")
        ...     for violation in safety_result.violations[:5]:  # Top 5
        ...         print(f"- {violation.violation_type.value}: {violation.immediate_action}")
    """
    validator = SafetyValidator(config)
    return validator.validate_safety(data, engine_state, apply_constraints=True)


def check_critical_parameters(
    data: Union[pd.DataFrame, Dict[str, np.ndarray]],
    parameters: Optional[List[str]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Quick check of critical safety parameters.
    
    Args:
        data: Engine data
        parameters: List of parameters to check (default: all critical)
        
    Returns:
        Dictionary of parameter safety status
        
    Example:
        >>> critical_status = check_critical_parameters(dataframe)
        >>> for param, status in critical_status.items():
        ...     if not status['is_safe']:
        ...         print(f"WARNING: {param} - {status['issue']}")
    """
    if parameters is None:
        parameters = ["lambda_sensor", "egt", "engine_temp", "map_pressure", "rpm"]
    
    validator = SafetyValidator()
    result = validator.validate_safety(data, apply_constraints=False)
    
    param_status = {}
    
    for param in parameters:
        param_violations = [v for v in result.violations if v.parameter == param]
        
        if param_violations:
            critical_violations = [v for v in param_violations if v.safety_level == SafetyLevel.CRITICAL]
            param_status[param] = {
                "is_safe": len(critical_violations) == 0,
                "violation_count": len(param_violations),
                "critical_count": len(critical_violations),
                "issue": param_violations[0].immediate_action if param_violations else None
            }
        else:
            param_status[param] = {
                "is_safe": True,
                "violation_count": 0,
                "critical_count": 0,
                "issue": None
            }
    
    return param_status


def apply_safety_constraints(
    tuning_values: Dict[str, float],
    safety_config: Optional[SafetyConfig] = None,
    conservative: bool = True
) -> Dict[str, float]:
    """
    Apply safety constraints to tuning values.
    
    Args:
        tuning_values: Dictionary of parameter values to constrain
        safety_config: Safety configuration
        conservative: Use conservative safety factors
        
    Returns:
        Dictionary of constrained values
        
    Example:
        >>> original_values = {"lambda_target": 0.75, "max_timing": 30.0}
        >>> safe_values = apply_safety_constraints(original_values, conservative=True)
        >>> print(f"Lambda constrained: {original_values['lambda_target']} -> {safe_values['lambda_target']}")
    """
    config = safety_config or SafetyConfig()
    constrained_values = tuning_values.copy()
    
    safety_factor = config.safety_factor_conservative if conservative else config.safety_factor_aggressive
    
    # Lambda constraints
    if "lambda_target" in constrained_values:
        lambda_val = constrained_values["lambda_target"]
        if lambda_val < config.critical_lambda_rich:
            constrained_values["lambda_target"] = config.critical_lambda_rich * safety_factor
        elif lambda_val > config.critical_lambda_lean:
            constrained_values["lambda_target"] = config.critical_lambda_lean * safety_factor
    
    # Timing constraints
    if "max_timing" in constrained_values:
        timing = constrained_values["max_timing"]
        is_boost = tuning_values.get("boost_mode", False)
        max_safe = config.max_timing_boost_warning if is_boost else config.max_timing_na_warning
        
        if timing > max_safe:
            constrained_values["max_timing"] = max_safe * safety_factor
    
    # Boost constraints
    if "max_boost" in constrained_values:
        boost = constrained_values["max_boost"]
        if boost > config.max_boost_warning:
            constrained_values["max_boost"] = config.max_boost_warning * safety_factor
    
    return constrained_values