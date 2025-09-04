"""
Advanced Performance Optimizer for FuelTune Streamlit

This module provides intelligent performance optimization with automatic
bottleneck detection, caching improvements, and resource management.
"""

import gc
import threading
import time
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging
import psutil
import streamlit as st
import pandas as pd
import numpy as np
from functools import lru_cache, wraps
import pickle
import hashlib
from concurrent.futures import ThreadPoolExecutor
import asyncio
import weakref

logger = logging.getLogger(__name__)


@dataclass 
class OptimizationResult:
    """Result of optimization operation."""
    
    optimization_type: str
    success: bool
    performance_gain: float  # Percentage improvement
    memory_saved: float  # MB
    execution_time_before: float
    execution_time_after: float
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    applied_optimizations: List[str] = field(default_factory=list)


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    
    hit_rate: float
    miss_rate: float
    total_requests: int
    cache_size: int
    memory_usage: float  # MB
    evictions: int
    average_access_time: float


class IntelligentCache:
    """Advanced caching system with analytics and optimization."""
    
    def __init__(self, max_size: int = 1000, ttl: Optional[int] = None):
        """Initialize intelligent cache.
        
        Args:
            max_size: Maximum number of cached items
            ttl: Time-to-live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Any] = {}
        self._access_times: Dict[str, float] = {}
        self._creation_times: Dict[str, float] = {}
        self._access_counts: Dict[str, int] = {}
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._lock = threading.RLock()
        
    def _generate_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function and arguments."""
        key_data = f"{func.__module__}.{func.__name__}"
        if args:
            key_data += f"_args_{hash(args)}"
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_data += f"_kwargs_{hash(tuple(sorted_kwargs))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if not self.ttl:
            return False
        return time.time() - self._creation_times.get(key, 0) > self.ttl
    
    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._cache:
            return
            
        # Find LRU item
        lru_key = min(self._access_times.keys(), key=self._access_times.get)
        
        # Remove from all tracking
        del self._cache[lru_key]
        del self._access_times[lru_key]
        del self._creation_times[lru_key]
        del self._access_counts[lru_key]
        
        self._evictions += 1
        logger.debug(f"Evicted cache key: {lru_key}")
    
    def get(self, key: str) -> Tuple[bool, Any]:
        """Get item from cache.
        
        Returns:
            Tuple of (found, value)
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return False, None
                
            if self._is_expired(key):
                self.invalidate(key)
                self._misses += 1
                return False, None
                
            # Update access tracking
            self._access_times[key] = time.time()
            self._access_counts[key] = self._access_counts.get(key, 0) + 1
            self._hits += 1
            
            return True, self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Set item in cache."""
        with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                self._evict_lru()
            
            current_time = time.time()
            self._cache[key] = value
            self._access_times[key] = current_time
            self._creation_times[key] = current_time
            self._access_counts[key] = 1
    
    def invalidate(self, key: str) -> bool:
        """Invalidate specific cache entry."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._access_times[key]
                del self._creation_times[key]
                del self._access_counts[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._creation_times.clear()
            self._access_counts.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def get_metrics(self) -> CacheMetrics:
        """Get comprehensive cache metrics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            miss_rate = self._misses / total_requests if total_requests > 0 else 0.0
            
            # Estimate memory usage
            cache_size_bytes = 0
            try:
                cache_size_bytes = sum(
                    len(pickle.dumps(value)) for value in self._cache.values()
                )
            except:
                pass
                
            return CacheMetrics(
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                total_requests=total_requests,
                cache_size=len(self._cache),
                memory_usage=cache_size_bytes / 1024 / 1024,  # MB
                evictions=self._evictions,
                average_access_time=0.0  # Would need timing for this
            )


class OptimizationEngine:
    """Intelligent performance optimization engine."""
    
    def __init__(self):
        """Initialize optimization engine."""
        self.intelligent_cache = IntelligentCache(max_size=2000, ttl=3600)
        self.optimization_history: List[OptimizationResult] = []
        self._memory_monitor_active = False
        self._optimization_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
    def smart_cache_decorator(self, ttl: Optional[int] = None):
        """Advanced caching decorator with intelligent optimization.
        
        Args:
            ttl: Time-to-live override for this function
        """
        def decorator(func: Callable) -> Callable:
            cache = self.intelligent_cache
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = cache._generate_key(func, args, kwargs)
                
                # Try cache first
                found, cached_result = cache.get(cache_key)
                if found:
                    return cached_result
                
                # Execute function and cache result
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Only cache if execution took significant time
                if execution_time > 0.1:  # 100ms threshold
                    cache.set(cache_key, result)
                    logger.debug(f"Cached result for {func.__name__} (took {execution_time:.3f}s)")
                
                return result
            
            return wrapper
        return decorator
    
    def optimize_pandas_operations(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, OptimizationResult]:
        """Optimize pandas DataFrame operations.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Optimized DataFrame and optimization results
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        optimized_df = df.copy()
        applied_optimizations = []
        
        # Optimize data types
        initial_memory = optimized_df.memory_usage(deep=True).sum()
        
        # Convert object columns to category if beneficial
        for col in optimized_df.select_dtypes(include=['object']):
            unique_ratio = optimized_df[col].nunique() / len(optimized_df)
            if unique_ratio < 0.5:  # Less than 50% unique values
                optimized_df[col] = optimized_df[col].astype('category')
                applied_optimizations.append(f"Converted '{col}' to category")
        
        # Optimize numeric types
        for col in optimized_df.select_dtypes(include=['int64']):
            col_min, col_max = optimized_df[col].min(), optimized_df[col].max()
            if col_min >= 0:
                if col_max < 256:
                    optimized_df[col] = optimized_df[col].astype('uint8')
                    applied_optimizations.append(f"Converted '{col}' to uint8")
                elif col_max < 65536:
                    optimized_df[col] = optimized_df[col].astype('uint16')
                    applied_optimizations.append(f"Converted '{col}' to uint16")
            else:
                if col_min >= -128 and col_max <= 127:
                    optimized_df[col] = optimized_df[col].astype('int8')
                    applied_optimizations.append(f"Converted '{col}' to int8")
                elif col_min >= -32768 and col_max <= 32767:
                    optimized_df[col] = optimized_df[col].astype('int16')
                    applied_optimizations.append(f"Converted '{col}' to int16")
        
        # Optimize float types
        for col in optimized_df.select_dtypes(include=['float64']):
            if optimized_df[col].between(-3.4e38, 3.4e38).all():
                optimized_df[col] = optimized_df[col].astype('float32')
                applied_optimizations.append(f"Converted '{col}' to float32")
        
        # Calculate improvements
        final_memory = optimized_df.memory_usage(deep=True).sum()
        memory_reduction = (initial_memory - final_memory) / 1024 / 1024  # MB
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        result = OptimizationResult(
            optimization_type="pandas_dtype_optimization",
            success=len(applied_optimizations) > 0,
            performance_gain=memory_reduction / (initial_memory / 1024 / 1024) * 100,
            memory_saved=memory_reduction,
            execution_time_before=0.0,
            execution_time_after=end_time - start_time,
            recommendations=[
                "Use categorical data types for repeated strings",
                "Consider using smaller numeric types when appropriate",
                "Regular memory profiling for large datasets"
            ],
            applied_optimizations=applied_optimizations
        )
        
        self.optimization_history.append(result)
        return optimized_df, result
    
    def optimize_streamlit_caching(self) -> OptimizationResult:
        """Optimize Streamlit caching configuration.
        
        Returns:
            Optimization results
        """
        start_time = time.time()
        applied_optimizations = []
        recommendations = []
        
        # Analyze current cache metrics
        cache_metrics = self.intelligent_cache.get_metrics()
        
        # Recommendations based on cache performance
        if cache_metrics.hit_rate < 0.7:
            recommendations.append(
                f"Low cache hit rate ({cache_metrics.hit_rate:.2%}). "
                "Consider increasing cache size or TTL."
            )
        
        if cache_metrics.memory_usage > 1000:  # > 1GB
            recommendations.append(
                f"High cache memory usage ({cache_metrics.memory_usage:.1f}MB). "
                "Consider reducing cache size or implementing more aggressive eviction."
            )
        
        # Automatic optimizations
        if cache_metrics.hit_rate < 0.5 and cache_metrics.cache_size < 5000:
            # Increase cache size for low hit rates
            old_size = self.intelligent_cache.max_size
            self.intelligent_cache.max_size = min(old_size * 2, 5000)
            applied_optimizations.append(
                f"Increased cache size from {old_size} to {self.intelligent_cache.max_size}"
            )
        
        # Clear expired entries
        cleared_count = self._clear_expired_cache_entries()
        if cleared_count > 0:
            applied_optimizations.append(f"Cleared {cleared_count} expired cache entries")
        
        execution_time = time.time() - start_time
        
        result = OptimizationResult(
            optimization_type="streamlit_cache_optimization",
            success=len(applied_optimizations) > 0,
            performance_gain=cache_metrics.hit_rate * 100,
            memory_saved=0.0,
            execution_time_before=0.0,
            execution_time_after=execution_time,
            recommendations=recommendations,
            applied_optimizations=applied_optimizations
        )
        
        self.optimization_history.append(result)
        return result
    
    def memory_cleanup(self) -> OptimizationResult:
        """Perform intelligent memory cleanup.
        
        Returns:
            Cleanup results
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        applied_optimizations = []
        
        # Force garbage collection
        collected = gc.collect()
        if collected > 0:
            applied_optimizations.append(f"Garbage collected {collected} objects")
        
        # Clear unused DataFrame references
        if hasattr(st.session_state, '_dataframes'):
            cleared_dfs = len(st.session_state._dataframes)
            st.session_state._dataframes.clear()
            applied_optimizations.append(f"Cleared {cleared_dfs} DataFrame references")
        
        # Clean up expired cache entries
        cleared_cache = self._clear_expired_cache_entries()
        if cleared_cache > 0:
            applied_optimizations.append(f"Cleared {cleared_cache} expired cache entries")
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        memory_freed = start_memory - end_memory
        
        result = OptimizationResult(
            optimization_type="memory_cleanup",
            success=memory_freed > 0,
            performance_gain=0.0,
            memory_saved=memory_freed,
            execution_time_before=0.0,
            execution_time_after=end_time - start_time,
            recommendations=[
                "Schedule regular memory cleanup",
                "Monitor for memory leaks in long-running sessions",
                "Use context managers for large data operations"
            ],
            applied_optimizations=applied_optimizations
        )
        
        self.optimization_history.append(result)
        return result
    
    def start_continuous_monitoring(self) -> None:
        """Start continuous performance monitoring thread."""
        if self._memory_monitor_active:
            return
        
        self._memory_monitor_active = True
        self._stop_monitoring.clear()
        
        self._optimization_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._optimization_thread.start()
        logger.info("Started continuous performance monitoring")
    
    def stop_continuous_monitoring(self) -> None:
        """Stop continuous monitoring."""
        self._stop_monitoring.set()
        self._memory_monitor_active = False
        
        if self._optimization_thread:
            self._optimization_thread.join(timeout=5.0)
        
        logger.info("Stopped continuous performance monitoring")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_monitoring.is_set():
            try:
                # Check memory usage
                memory_percent = psutil.virtual_memory().percent
                
                # Trigger cleanup if memory usage is high
                if memory_percent > 85:
                    logger.warning(f"High memory usage detected: {memory_percent:.1f}%")
                    self.memory_cleanup()
                
                # Optimize caching periodically
                cache_metrics = self.intelligent_cache.get_metrics()
                if cache_metrics.total_requests > 100 and cache_metrics.hit_rate < 0.5:
                    self.optimize_streamlit_caching()
                
                # Sleep for monitoring interval
                self._stop_monitoring.wait(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self._stop_monitoring.wait(60)  # Wait longer on error
    
    def _clear_expired_cache_entries(self) -> int:
        """Clear expired cache entries.
        
        Returns:
            Number of cleared entries
        """
        cleared_count = 0
        with self.intelligent_cache._lock:
            expired_keys = []
            for key in list(self.intelligent_cache._cache.keys()):
                if self.intelligent_cache._is_expired(key):
                    expired_keys.append(key)
            
            for key in expired_keys:
                self.intelligent_cache.invalidate(key)
                cleared_count += 1
        
        return cleared_count
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB.
        
        Returns:
            Memory usage in MB
        """
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get comprehensive optimization summary.
        
        Returns:
            Optimization performance summary
        """
        if not self.optimization_history:
            return {'error': 'No optimization history available'}
        
        # Aggregate results by type
        by_type = {}
        total_memory_saved = 0.0
        total_successful = 0
        
        for result in self.optimization_history:
            if result.optimization_type not in by_type:
                by_type[result.optimization_type] = []
            by_type[result.optimization_type].append(result)
            
            if result.success:
                total_successful += 1
                total_memory_saved += result.memory_saved
        
        # Cache metrics
        cache_metrics = self.intelligent_cache.get_metrics()
        
        return {
            'total_optimizations': len(self.optimization_history),
            'successful_optimizations': total_successful,
            'success_rate': total_successful / len(self.optimization_history),
            'total_memory_saved': total_memory_saved,
            'optimizations_by_type': {
                opt_type: len(results) for opt_type, results in by_type.items()
            },
            'cache_metrics': {
                'hit_rate': cache_metrics.hit_rate,
                'cache_size': cache_metrics.cache_size,
                'memory_usage': cache_metrics.memory_usage,
                'total_requests': cache_metrics.total_requests
            },
            'monitoring_active': self._memory_monitor_active,
            'last_optimization': self.optimization_history[-1].optimization_type if self.optimization_history else None
        }


# Global optimization engine instance
global_optimizer = OptimizationEngine()