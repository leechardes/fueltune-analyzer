"""
FuelTune Performance Module

This module provides comprehensive performance monitoring, profiling,
and optimization tools for the FuelTune Streamlit application.

Classes:
    ProfilerManager: System-wide performance profiling
    OptimizationEngine: Automatic performance optimization
    PerformanceMonitor: Real-time monitoring dashboard

Functions:
    profile_function: Decorator for function-level profiling
    benchmark_operation: Performance benchmarking utilities
    get_system_metrics: System resource monitoring

Author: FuelTune Development Team
Version: 1.0.0
"""

from .profiler import ProfilerManager, profile_function
from .optimizer import OptimizationEngine
from .monitor import PerformanceMonitor

__all__ = [
    "ProfilerManager",
    "profile_function", 
    "OptimizationEngine",
    "PerformanceMonitor"
]