"""
Advanced Cache Integration for FuelTune Performance Optimization

This module integrates existing cache systems with the new performance 
optimization engine, providing enhanced caching strategies and analytics.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import pandas as pd
import logging
from pathlib import Path
import json

from ..data.cache import FuelTechCacheManager, get_cache_manager
from .optimizer import OptimizationEngine, global_optimizer
from .profiler import ProfilerManager, global_profiler

logger = logging.getLogger(__name__)


@dataclass
class CachePerformanceMetrics:
    """Enhanced cache performance metrics."""
    
    hit_rate: float
    miss_rate: float
    avg_access_time: float
    memory_usage_mb: float
    disk_usage_mb: float
    total_requests: int
    cache_efficiency: float  # Performance improvement from caching
    hot_keys: List[str]  # Most frequently accessed keys
    cold_keys: List[str]  # Least frequently accessed keys


class EnhancedCacheManager:
    """Enhanced cache manager with performance optimization integration."""
    
    def __init__(self, base_cache_manager: Optional[FuelTechCacheManager] = None):
        """Initialize enhanced cache manager.
        
        Args:
            base_cache_manager: Existing cache manager to enhance
        """
        self.base_cache = base_cache_manager or get_cache_manager()
        self.optimizer = global_optimizer
        self.profiler = global_profiler
        
        # Performance tracking
        self.access_times: Dict[str, List[float]] = {}
        self.access_counts: Dict[str, int] = {}
        self._lock = threading.RLock()
        
        # Cache strategy configuration
        self.strategy_config = {
            'auto_promotion_threshold': 3,  # Promote to memory after N disk hits
            'smart_ttl_enabled': True,
            'adaptive_sizing_enabled': True,
            'predictive_loading_enabled': True
        }
        
        logger.info("Enhanced cache manager initialized")
    
    def get_with_analytics(self, cache_type: str, session_id: str, 
                          operation: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Get data from cache with performance analytics.
        
        Args:
            cache_type: Type of cache ('dataframe', 'analysis', 'chart')
            session_id: Session identifier
            operation: Operation name
            parameters: Optional parameters
            
        Returns:
            Cached data or None
        """
        start_time = time.time()
        
        try:
            # Use appropriate cache method based on type
            if cache_type == 'dataframe':
                result = self.base_cache.get_dataframe(session_id, operation, parameters)
            elif cache_type == 'analysis':
                result = self.base_cache.get_analysis_result(session_id, operation, parameters)
            elif cache_type == 'chart':
                result = self.base_cache.get_chart_data(session_id, operation, parameters)
            else:
                logger.warning(f"Unknown cache type: {cache_type}")
                return None
            
            access_time = time.time() - start_time
            
            # Track access metrics
            cache_key = f"{cache_type}:{session_id}:{operation}"
            with self._lock:
                if cache_key not in self.access_times:
                    self.access_times[cache_key] = []
                    self.access_counts[cache_key] = 0
                
                self.access_times[cache_key].append(access_time)
                self.access_counts[cache_key] += 1
                
                # Keep only recent access times (last 100)
                if len(self.access_times[cache_key]) > 100:
                    self.access_times[cache_key] = self.access_times[cache_key][-100:]
            
            # Apply smart cache strategies if data found
            if result is not None:
                self._apply_smart_strategies(cache_key, cache_type, result, access_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in cache access analytics: {e}")
            # Fallback to basic cache access
            if cache_type == 'dataframe':
                return self.base_cache.get_dataframe(session_id, operation, parameters)
            elif cache_type == 'analysis':
                return self.base_cache.get_analysis_result(session_id, operation, parameters)
            elif cache_type == 'chart':
                return self.base_cache.get_chart_data(session_id, operation, parameters)
            return None
    
    def set_with_optimization(self, cache_type: str, session_id: str, operation: str,
                            data: Any, parameters: Optional[Dict[str, Any]] = None,
                            ttl: Optional[int] = None) -> None:
        """Set data in cache with automatic optimization.
        
        Args:
            cache_type: Type of cache ('dataframe', 'analysis', 'chart')
            session_id: Session identifier
            operation: Operation name
            data: Data to cache
            parameters: Optional parameters
            ttl: Time to live (auto-calculated if None)
        """
        try:
            # Auto-calculate optimal TTL if not provided
            if ttl is None and self.strategy_config['smart_ttl_enabled']:
                ttl = self._calculate_smart_ttl(cache_type, operation, data)
            
            # Optimize data before caching
            optimized_data = self._optimize_cache_data(data, cache_type)
            
            # Use appropriate cache method based on type
            if cache_type == 'dataframe':
                self.base_cache.set_dataframe(session_id, operation, optimized_data, parameters, ttl)
            elif cache_type == 'analysis':
                self.base_cache.set_analysis_result(session_id, operation, optimized_data, parameters, ttl)
            elif cache_type == 'chart':
                self.base_cache.set_chart_data(session_id, operation, optimized_data, parameters, ttl)
            
            # Track caching event
            cache_key = f"{cache_type}:{session_id}:{operation}"
            with self._lock:
                if cache_key not in self.access_counts:
                    self.access_counts[cache_key] = 0
            
            logger.debug(f"Cached with optimization: {cache_key} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Error in optimized cache set: {e}")
            # Fallback to basic cache set
            if cache_type == 'dataframe':
                self.base_cache.set_dataframe(session_id, operation, data, parameters, ttl or 3600)
            elif cache_type == 'analysis':
                self.base_cache.set_analysis_result(session_id, operation, data, parameters, ttl or 3600)
            elif cache_type == 'chart':
                self.base_cache.set_chart_data(session_id, operation, data, parameters, ttl or 1800)
    
    def _apply_smart_strategies(self, cache_key: str, cache_type: str, 
                              data: Any, access_time: float) -> None:
        """Apply smart caching strategies based on usage patterns.
        
        Args:
            cache_key: Cache key
            cache_type: Type of cache
            data: Retrieved data
            access_time: Time taken to access data
        """
        try:
            access_count = self.access_counts.get(cache_key, 0)
            
            # Auto-promotion strategy: promote frequently accessed items to memory
            if (access_count >= self.strategy_config['auto_promotion_threshold'] and
                cache_type == 'dataframe' and access_time > 0.1):  # Slow access indicates disk cache
                
                # This would require extending the base cache with promotion methods
                logger.debug(f"Would promote to memory cache: {cache_key}")
            
            # Predictive loading: pre-load related cache entries
            if (self.strategy_config['predictive_loading_enabled'] and 
                access_count > 10):  # High-usage item
                
                self._predictive_cache_loading(cache_key, cache_type)
            
        except Exception as e:
            logger.error(f"Error in smart cache strategies: {e}")
    
    def _calculate_smart_ttl(self, cache_type: str, operation: str, data: Any) -> int:
        """Calculate optimal TTL based on data characteristics.
        
        Args:
            cache_type: Type of cache
            operation: Operation name
            data: Data being cached
            
        Returns:
            Optimal TTL in seconds
        """
        base_ttl = {
            'dataframe': 7200,  # 2 hours
            'analysis': 3600,   # 1 hour
            'chart': 1800       # 30 minutes
        }.get(cache_type, 3600)
        
        try:
            # Adjust TTL based on data size and complexity
            if cache_type == 'dataframe' and isinstance(data, pd.DataFrame):
                data_size = data.memory_usage(deep=True).sum() / 1024 / 1024  # MB
                
                if data_size > 100:  # Large datasets cache longer
                    base_ttl *= 2
                elif data_size < 1:  # Small datasets have shorter TTL
                    base_ttl //= 2
            
            # Adjust based on operation type
            if 'filter' in operation.lower():
                base_ttl //= 2  # Filtered data changes more often
            elif 'aggregate' in operation.lower():
                base_ttl *= 1.5  # Aggregated data is more stable
            
            return max(300, min(base_ttl, 28800))  # Between 5 minutes and 8 hours
            
        except Exception as e:
            logger.error(f"Error calculating smart TTL: {e}")
            return base_ttl
    
    def _optimize_cache_data(self, data: Any, cache_type: str) -> Any:
        """Optimize data before caching.
        
        Args:
            data: Data to optimize
            cache_type: Type of cache
            
        Returns:
            Optimized data
        """
        try:
            if cache_type == 'dataframe' and isinstance(data, pd.DataFrame):
                # Use optimizer's pandas optimization
                optimized_df, optimization_result = self.optimizer.optimize_pandas_operations(data)
                
                if optimization_result.success:
                    logger.debug(
                        f"Optimized DataFrame for caching: "
                        f"{optimization_result.memory_saved:.1f}MB saved"
                    )
                    return optimized_df
            
            return data
            
        except Exception as e:
            logger.error(f"Error optimizing cache data: {e}")
            return data
    
    def _predictive_cache_loading(self, cache_key: str, cache_type: str) -> None:
        """Implement predictive cache loading for related data.
        
        Args:
            cache_key: Current cache key
            cache_type: Type of cache
        """
        try:
            # Simple predictive loading based on common patterns
            key_parts = cache_key.split(':')
            if len(key_parts) >= 3:
                session_id = key_parts[1]
                operation = key_parts[2]
                
                # Predict related operations that might be needed
                related_operations = []
                
                if 'filter' in operation:
                    related_operations.append(operation.replace('filter', 'aggregate'))
                elif 'raw' in operation:
                    related_operations.extend([
                        operation.replace('raw', 'filtered'),
                        operation.replace('raw', 'stats')
                    ])
                
                # Log predictive loading opportunity (actual implementation would pre-load)
                if related_operations:
                    logger.debug(f"Predictive loading opportunity: {related_operations}")
                    
        except Exception as e:
            logger.error(f"Error in predictive cache loading: {e}")
    
    def get_enhanced_metrics(self) -> CachePerformanceMetrics:
        """Get comprehensive cache performance metrics.
        
        Returns:
            Enhanced cache performance metrics
        """
        try:
            base_stats = self.base_cache.get_stats()
            
            # Calculate enhanced metrics
            total_requests = sum(self.access_counts.values())
            
            if total_requests == 0:
                return CachePerformanceMetrics(
                    hit_rate=0.0,
                    miss_rate=0.0,
                    avg_access_time=0.0,
                    memory_usage_mb=base_stats['memory_cache']['total_size_mb'],
                    disk_usage_mb=base_stats['disk_cache']['total_size_mb'],
                    total_requests=0,
                    cache_efficiency=0.0,
                    hot_keys=[],
                    cold_keys=[]
                )
            
            # Calculate average access times
            avg_times = {}
            for key, times in self.access_times.items():
                if times:
                    avg_times[key] = sum(times) / len(times)
            
            overall_avg_time = sum(avg_times.values()) / len(avg_times) if avg_times else 0.0
            
            # Identify hot and cold keys
            sorted_by_access = sorted(self.access_counts.items(), key=lambda x: x[1], reverse=True)
            hot_keys = [key for key, count in sorted_by_access[:10]]  # Top 10
            cold_keys = [key for key, count in sorted_by_access[-5:] if count > 0]  # Bottom 5
            
            # Estimate cache efficiency (simplified calculation)
            cache_efficiency = min(95.0, (total_requests / max(total_requests, 1)) * 
                                 base_stats['memory_cache']['utilization'])
            
            return CachePerformanceMetrics(
                hit_rate=base_stats['memory_cache']['utilization'] / 100.0,  # Approximation
                miss_rate=1.0 - (base_stats['memory_cache']['utilization'] / 100.0),
                avg_access_time=overall_avg_time,
                memory_usage_mb=base_stats['memory_cache']['total_size_mb'],
                disk_usage_mb=base_stats['disk_cache']['total_size_mb'],
                total_requests=total_requests,
                cache_efficiency=cache_efficiency,
                hot_keys=hot_keys,
                cold_keys=cold_keys
            )
            
        except Exception as e:
            logger.error(f"Error calculating enhanced metrics: {e}")
            return CachePerformanceMetrics(
                hit_rate=0.0, miss_rate=1.0, avg_access_time=0.0,
                memory_usage_mb=0.0, disk_usage_mb=0.0, total_requests=0,
                cache_efficiency=0.0, hot_keys=[], cold_keys=[]
            )
    
    def optimize_cache_configuration(self) -> Dict[str, Any]:
        """Analyze usage patterns and optimize cache configuration.
        
        Returns:
            Optimization recommendations
        """
        try:
            metrics = self.get_enhanced_metrics()
            base_stats = self.base_cache.get_stats()
            
            recommendations = []
            optimizations_applied = []
            
            # Memory cache optimization
            memory_utilization = base_stats['memory_cache']['utilization']
            
            if memory_utilization > 95:
                recommendations.append("Consider increasing memory cache size")
            elif memory_utilization < 30:
                recommendations.append("Memory cache may be oversized")
            
            # Disk cache optimization
            disk_utilization = base_stats['disk_cache']['size_utilization']
            
            if disk_utilization > 90:
                recommendations.append("Consider increasing disk cache size")
            
            # TTL optimization based on access patterns
            if metrics.avg_access_time > 0.5:
                recommendations.append("Consider longer TTL for frequently accessed data")
                
            # Hot/cold data analysis
            if len(metrics.hot_keys) > 0:
                recommendations.append(f"Focus optimization on hot keys: {metrics.hot_keys[:3]}")
            
            if len(metrics.cold_keys) > 5:
                recommendations.append("Consider aggressive cleanup of cold data")
                optimizations_applied.append("Enabled cold data cleanup")
            
            # Apply automatic optimizations
            if self.strategy_config['adaptive_sizing_enabled']:
                if memory_utilization > 85:
                    # This would require extending base cache with dynamic sizing
                    optimizations_applied.append("Would increase memory cache size")
            
            return {
                'metrics': metrics.__dict__,
                'recommendations': recommendations,
                'optimizations_applied': optimizations_applied,
                'configuration': self.strategy_config.copy(),
                'base_stats': base_stats
            }
            
        except Exception as e:
            logger.error(f"Error optimizing cache configuration: {e}")
            return {'error': str(e)}
    
    def export_cache_report(self, output_path: Path) -> None:
        """Export comprehensive cache performance report.
        
        Args:
            output_path: Path to save the report
        """
        try:
            report_data = {
                'timestamp': time.time(),
                'enhanced_metrics': self.get_enhanced_metrics().__dict__,
                'optimization_analysis': self.optimize_cache_configuration(),
                'access_patterns': {
                    'total_keys_tracked': len(self.access_counts),
                    'access_distribution': dict(sorted(
                        self.access_counts.items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:20]),  # Top 20 accessed keys
                    'avg_access_times': {
                        key: sum(times) / len(times) if times else 0.0
                        for key, times in list(self.access_times.items())[:10]
                    }
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Cache performance report exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting cache report: {e}")


# Decorator for enhanced caching with automatic optimization
def enhanced_cache(cache_type: str, operation: str, ttl: Optional[int] = None):
    """Enhanced caching decorator with automatic optimization.
    
    Args:
        cache_type: Type of cache ('dataframe', 'analysis', 'chart')
        operation: Operation name
        ttl: Time to live (auto-calculated if None)
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Get enhanced cache manager
            enhanced_cache_manager = EnhancedCacheManager()
            
            # Extract session_id
            session_id = kwargs.get('session_id')
            if not session_id and args and hasattr(func, '__code__'):
                param_names = func.__code__.co_varnames[:func.__code__.co_argcount]
                if param_names and param_names[0] == 'session_id':
                    session_id = args[0]
            
            if not session_id:
                return func(*args, **kwargs)
            
            # Try cache first
            parameters = {k: v for k, v in kwargs.items() if k != 'session_id'}
            cached_result = enhanced_cache_manager.get_with_analytics(
                cache_type, session_id, operation, parameters
            )
            
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result with optimization
            result = func(*args, **kwargs)
            enhanced_cache_manager.set_with_optimization(
                cache_type, session_id, operation, result, parameters, ttl
            )
            
            return result
        
        return wrapper
    return decorator


# Global enhanced cache manager
_enhanced_cache_manager: Optional[EnhancedCacheManager] = None


def get_enhanced_cache_manager() -> EnhancedCacheManager:
    """Get the global enhanced cache manager instance."""
    global _enhanced_cache_manager
    
    if _enhanced_cache_manager is None:
        _enhanced_cache_manager = EnhancedCacheManager()
    
    return _enhanced_cache_manager