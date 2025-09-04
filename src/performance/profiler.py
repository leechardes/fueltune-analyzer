"""
Advanced Performance Profiler for FuelTune Streamlit

This module provides comprehensive profiling capabilities for performance
monitoring, bottleneck identification, and optimization guidance.
"""

import cProfile
import pstats
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging
from contextlib import contextmanager
import tracemalloc
import linecache
import gc

logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """Comprehensive profiling result."""
    
    function_name: str
    execution_time: float
    memory_peak: float  # MB
    memory_current: float  # MB
    cpu_percent: float
    call_count: int
    cumulative_time: float
    per_call_time: float
    top_callers: List[str] = field(default_factory=list)
    memory_leaks: List[Dict[str, Any]] = field(default_factory=list)
    bottlenecks: List[str] = field(default_factory=list)


@dataclass
class SystemMetrics:
    """System resource metrics."""
    
    cpu_percent: float
    memory_percent: float
    memory_available: float  # GB
    disk_usage: float
    network_io: Dict[str, int]
    process_count: int
    timestamp: float


class ProfilerManager:
    """Advanced profiling manager with comprehensive analysis."""
    
    def __init__(self, enable_memory_tracking: bool = True):
        """Initialize profiler manager.
        
        Args:
            enable_memory_tracking: Enable detailed memory profiling
        """
        self.enable_memory_tracking = enable_memory_tracking
        self.profile_results: Dict[str, ProfileResult] = {}
        self.system_metrics: List[SystemMetrics] = []
        self._profiler: Optional[cProfile.Profile] = None
        self._start_time: float = 0.0
        self._memory_tracker = None
        
        if enable_memory_tracking:
            tracemalloc.start()
            
    def start_profiling(self, operation_name: str) -> None:
        """Start profiling an operation.
        
        Args:
            operation_name: Name identifier for the operation
        """
        logger.info(f"Starting profiling for: {operation_name}")
        
        self._profiler = cProfile.Profile()
        self._start_time = time.time()
        
        if self.enable_memory_tracking:
            gc.collect()  # Clean up before measuring
            self._memory_tracker = tracemalloc.take_snapshot()
            
        self._profiler.enable()
        
    def stop_profiling(self, operation_name: str) -> ProfileResult:
        """Stop profiling and generate results.
        
        Args:
            operation_name: Name identifier for the operation
            
        Returns:
            Comprehensive profiling results
        """
        if not self._profiler:
            raise ValueError("No active profiling session")
            
        self._profiler.disable()
        
        # Calculate timing
        execution_time = time.time() - self._start_time
        
        # Analyze profiling stats
        stats = pstats.Stats(self._profiler)
        stats.sort_stats('cumulative')
        
        # Get top functions
        top_functions = []
        for func_info, (call_count, total_time, cumulative_time, callers) in stats.stats.items():
            if cumulative_time > 0.001:  # Filter out trivial functions
                filename, line_num, func_name = func_info
                top_functions.append({
                    'function': f"{filename}:{line_num}({func_name})",
                    'calls': call_count,
                    'total_time': total_time,
                    'cumulative_time': cumulative_time,
                    'per_call': total_time / call_count if call_count > 0 else 0
                })
        
        # Sort by cumulative time
        top_functions.sort(key=lambda x: x['cumulative_time'], reverse=True)
        
        # Memory analysis
        memory_peak = 0.0
        memory_current = 0.0
        memory_leaks = []
        
        if self.enable_memory_tracking and self._memory_tracker:
            try:
                current_snapshot = tracemalloc.take_snapshot()
                top_stats = current_snapshot.compare_to(self._memory_tracker, 'lineno')
                
                for stat in top_stats[:10]:
                    memory_leaks.append({
                        'filename': stat.traceback.format()[0],
                        'size_diff': stat.size_diff,
                        'size': stat.size,
                        'count_diff': stat.count_diff
                    })
                
                # Get current memory usage
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_current = memory_info.rss / 1024 / 1024  # MB
                memory_peak = process.memory_percent()
                
            except Exception as e:
                logger.warning(f"Memory tracking error: {e}")
        
        # System metrics
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
        except:
            cpu_percent = 0.0
            
        # Identify bottlenecks
        bottlenecks = []
        for func in top_functions[:5]:
            if func['cumulative_time'] > execution_time * 0.1:  # >10% of total time
                bottlenecks.append(
                    f"Function '{func['function']}' took "
                    f"{func['cumulative_time']:.3f}s ({func['cumulative_time']/execution_time*100:.1f}%)"
                )
        
        # Create result
        result = ProfileResult(
            function_name=operation_name,
            execution_time=execution_time,
            memory_peak=memory_peak,
            memory_current=memory_current,
            cpu_percent=cpu_percent,
            call_count=sum(func['calls'] for func in top_functions),
            cumulative_time=sum(func['cumulative_time'] for func in top_functions),
            per_call_time=execution_time,
            top_callers=[func['function'] for func in top_functions[:10]],
            memory_leaks=memory_leaks,
            bottlenecks=bottlenecks
        )
        
        self.profile_results[operation_name] = result
        logger.info(f"Profiling completed for: {operation_name} ({execution_time:.3f}s)")
        
        return result
    
    @contextmanager
    def profile_context(self, operation_name: str):
        """Context manager for profiling operations.
        
        Args:
            operation_name: Name identifier for the operation
        """
        self.start_profiling(operation_name)
        try:
            yield
        finally:
            self.stop_profiling(operation_name)
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics.
        
        Returns:
            Current system resource metrics
        """
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available=memory.available / 1024**3,  # GB
                disk_usage=disk.percent,
                network_io=network_io,
                process_count=process_count,
                timestamp=time.time()
            )
            
            self.system_metrics.append(metrics)
            
            # Keep only last 1000 metrics
            if len(self.system_metrics) > 1000:
                self.system_metrics = self.system_metrics[-1000:]
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available=0.0,
                disk_usage=0.0,
                network_io={},
                process_count=0,
                timestamp=time.time()
            )
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends from collected data.
        
        Returns:
            Performance trend analysis
        """
        if len(self.system_metrics) < 2:
            return {'error': 'Insufficient data for trend analysis'}
        
        # CPU trend
        cpu_values = [m.cpu_percent for m in self.system_metrics[-100:]]
        cpu_trend = {
            'current': cpu_values[-1],
            'average': sum(cpu_values) / len(cpu_values),
            'peak': max(cpu_values),
            'trend': 'increasing' if cpu_values[-1] > cpu_values[-10] else 'stable'
        }
        
        # Memory trend
        memory_values = [m.memory_percent for m in self.system_metrics[-100:]]
        memory_trend = {
            'current': memory_values[-1],
            'average': sum(memory_values) / len(memory_values),
            'peak': max(memory_values),
            'trend': 'increasing' if memory_values[-1] > memory_values[-10] else 'stable'
        }
        
        # Performance warnings
        warnings = []
        if cpu_trend['current'] > 80:
            warnings.append('High CPU usage detected')
        if memory_trend['current'] > 85:
            warnings.append('High memory usage detected')
        if memory_trend['trend'] == 'increasing':
            warnings.append('Potential memory leak detected')
            
        return {
            'cpu_trend': cpu_trend,
            'memory_trend': memory_trend,
            'warnings': warnings,
            'data_points': len(self.system_metrics),
            'analysis_time': time.time()
        }
    
    def export_results(self, output_path: Path) -> None:
        """Export profiling results to JSON.
        
        Args:
            output_path: Path to save results
        """
        try:
            export_data = {
                'profile_results': {},
                'system_metrics': [],
                'analysis': self.analyze_performance_trends(),
                'export_time': time.time()
            }
            
            # Convert profile results to serializable format
            for name, result in self.profile_results.items():
                export_data['profile_results'][name] = {
                    'function_name': result.function_name,
                    'execution_time': result.execution_time,
                    'memory_peak': result.memory_peak,
                    'memory_current': result.memory_current,
                    'cpu_percent': result.cpu_percent,
                    'call_count': result.call_count,
                    'cumulative_time': result.cumulative_time,
                    'per_call_time': result.per_call_time,
                    'top_callers': result.top_callers,
                    'memory_leaks': result.memory_leaks,
                    'bottlenecks': result.bottlenecks
                }
            
            # Convert system metrics (last 100 entries)
            for metric in self.system_metrics[-100:]:
                export_data['system_metrics'].append({
                    'cpu_percent': metric.cpu_percent,
                    'memory_percent': metric.memory_percent,
                    'memory_available': metric.memory_available,
                    'disk_usage': metric.disk_usage,
                    'network_io': metric.network_io,
                    'process_count': metric.process_count,
                    'timestamp': metric.timestamp
                })
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            logger.info(f"Performance results exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")


def profile_function(operation_name: Optional[str] = None):
    """Decorator for automatic function profiling.
    
    Args:
        operation_name: Optional custom name for the operation
    
    Returns:
        Decorated function with profiling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            # Get or create profiler instance
            if not hasattr(wrapper, '_profiler'):
                wrapper._profiler = ProfilerManager()
            
            profiler = wrapper._profiler
            
            with profiler.profile_context(name):
                result = func(*args, **kwargs)
            
            # Log performance info
            profile_result = profiler.profile_results.get(name)
            if profile_result:
                logger.info(
                    f"Function '{name}' executed in {profile_result.execution_time:.3f}s "
                    f"(Memory: {profile_result.memory_current:.1f}MB)"
                )
            
            return result
        
        return wrapper
    return decorator


# Global profiler instance for application-wide use
global_profiler = ProfilerManager()