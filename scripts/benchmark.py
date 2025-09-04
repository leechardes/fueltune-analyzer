"""
Comprehensive Performance Benchmark Suite for FuelTune Streamlit

This script provides comprehensive benchmarking capabilities for testing
system performance, identifying bottlenecks, and validating performance targets.
"""

import time
import psutil
import pandas as pd
import numpy as np
import gc
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import logging
import sys
import tempfile
import os
from datetime import datetime
import tracemalloc
import io

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.performance.profiler import ProfilerManager, profile_function
from src.performance.optimizer import OptimizationEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Comprehensive benchmark result."""
    
    test_name: str
    success: bool
    execution_time: float
    memory_peak: float  # MB
    memory_delta: float  # MB
    cpu_percent: float
    throughput: Optional[float] = None  # Operations per second
    data_size: Optional[int] = None  # Size of data processed
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""
    
    suite_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    results: List[BenchmarkResult] = field(default_factory=list)
    system_info: Dict[str, Any] = field(default_factory=dict)
    performance_summary: Dict[str, Any] = field(default_factory=dict)


class FuelTuneBenchmark:
    """Comprehensive benchmark suite for FuelTune Streamlit."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize benchmark suite.
        
        Args:
            output_dir: Directory to save benchmark results
        """
        self.output_dir = output_dir or Path("benchmark_results")
        self.output_dir.mkdir(exist_ok=True)
        
        self.profiler = ProfilerManager(enable_memory_tracking=True)
        self.optimizer = OptimizationEngine()
        self.current_suite: Optional[BenchmarkSuite] = None
        
        # Performance targets (requirements from specs)
        self.performance_targets = {
            'csv_import_10k_lines': 2.0,  # < 2s for 10k lines
            'memory_usage_limit': 500.0,  # < 500MB
            'cache_hit_rate_target': 0.8,  # > 80%
            'response_time_target': 1.0,   # < 1s for typical operations
            'data_processing_throughput': 5000.0  # > 5k rows/second
        }
    
    def start_benchmark_suite(self, suite_name: str) -> None:
        """Start a new benchmark suite.
        
        Args:
            suite_name: Name of the benchmark suite
        """
        self.current_suite = BenchmarkSuite(
            suite_name=suite_name,
            start_time=datetime.now(),
            system_info=self._collect_system_info()
        )
        logger.info(f"Started benchmark suite: {suite_name}")
    
    def run_csv_import_benchmark(self, file_sizes: List[int] = None) -> List[BenchmarkResult]:
        """Benchmark CSV import performance.
        
        Args:
            file_sizes: List of file sizes (rows) to test
            
        Returns:
            List of benchmark results
        """
        if file_sizes is None:
            file_sizes = [1000, 5000, 10000, 50000, 100000]
        
        results = []
        
        for size in file_sizes:
            logger.info(f"Running CSV import benchmark for {size:,} rows")
            
            # Generate test CSV data
            test_data = self._generate_test_csv_data(size)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                test_data.to_csv(f.name, index=False)
                temp_file = Path(f.name)
            
            try:
                # Memory tracking
                tracemalloc.start()
                gc.collect()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                # Benchmark CSV reading and processing
                start_time = time.time()
                start_cpu = psutil.Process().cpu_percent()
                
                # Simulate CSV import with pandas operations
                df = pd.read_csv(temp_file)
                
                # Basic data processing operations
                df['calculated_afr'] = df['lambda_sensor'] * 14.7
                df['engine_load'] = df['throttle_position'] * df['map_pressure'] / 100
                df_summary = df.groupby('gear').agg({
                    'rpm': ['mean', 'max'],
                    'calculated_afr': ['mean', 'std']
                }).round(3)
                
                end_time = time.time()
                end_cpu = psutil.Process().cpu_percent()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                # Memory peak tracking
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                memory_peak = peak / 1024 / 1024  # MB
                
                execution_time = end_time - start_time
                throughput = size / execution_time if execution_time > 0 else 0
                
                # Determine success based on targets
                target_time = self.performance_targets['csv_import_10k_lines'] * (size / 10000)
                success = (
                    execution_time <= target_time and
                    memory_peak <= self.performance_targets['memory_usage_limit'] and
                    throughput >= self.performance_targets['data_processing_throughput']
                )
                
                result = BenchmarkResult(
                    test_name=f"csv_import_{size}_rows",
                    success=success,
                    execution_time=execution_time,
                    memory_peak=memory_peak,
                    memory_delta=end_memory - start_memory,
                    cpu_percent=(start_cpu + end_cpu) / 2,
                    throughput=throughput,
                    data_size=size,
                    metadata={
                        'target_time': target_time,
                        'rows_per_second': throughput,
                        'dataframe_shape': df.shape,
                        'summary_operations': len(df_summary)
                    }
                )
                
                results.append(result)
                logger.info(
                    f"CSV import {size:,} rows: {execution_time:.3f}s "
                    f"({throughput:.0f} rows/s) - {'PASS' if success else 'FAIL'}"
                )
                
            except Exception as e:
                logger.error(f"CSV import benchmark failed for {size} rows: {e}")
                result = BenchmarkResult(
                    test_name=f"csv_import_{size}_rows",
                    success=False,
                    execution_time=0.0,
                    memory_peak=0.0,
                    memory_delta=0.0,
                    cpu_percent=0.0,
                    data_size=size,
                    error_message=str(e)
                )
                results.append(result)
                
            finally:
                # Cleanup
                if temp_file.exists():
                    temp_file.unlink()
                gc.collect()
        
        if self.current_suite:
            self.current_suite.results.extend(results)
        
        return results
    
    def run_memory_stress_test(self) -> BenchmarkResult:
        """Run memory stress test to validate memory limits.
        
        Returns:
            Memory stress test result
        """
        logger.info("Running memory stress test")
        
        tracemalloc.start()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_time = time.time()
        
        try:
            # Create progressively larger datasets
            data_chunks = []
            chunk_size = 10000
            max_memory = self.performance_targets['memory_usage_limit']
            
            while True:
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                if current_memory > max_memory * 0.9:  # Stop at 90% of limit
                    logger.info(f"Stopping memory test at {current_memory:.1f}MB")
                    break
                
                # Create test data chunk
                chunk = pd.DataFrame({
                    'timestamp': np.random.random(chunk_size),
                    'rpm': np.random.randint(800, 8000, chunk_size),
                    'throttle_position': np.random.random(chunk_size) * 100,
                    'lambda_sensor': np.random.normal(0.85, 0.1, chunk_size),
                    'map_pressure': np.random.normal(1.0, 0.3, chunk_size)
                })
                
                data_chunks.append(chunk)
                
                # Perform some operations
                if len(data_chunks) > 1:
                    combined = pd.concat(data_chunks[-2:], ignore_index=True)
                    _ = combined.describe()
                
                # Check if we've reached practical limits
                if len(data_chunks) > 100:  # Safety limit
                    break
            
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_peak = peak / 1024 / 1024
            
            # Success if we stayed under memory limit
            success = memory_peak <= max_memory
            
            result = BenchmarkResult(
                test_name="memory_stress_test",
                success=success,
                execution_time=end_time - start_time,
                memory_peak=memory_peak,
                memory_delta=end_memory - start_memory,
                cpu_percent=psutil.Process().cpu_percent(),
                data_size=len(data_chunks) * chunk_size,
                metadata={
                    'max_chunks_processed': len(data_chunks),
                    'memory_limit': max_memory,
                    'chunk_size': chunk_size,
                    'peak_memory_mb': memory_peak
                }
            )
            
            logger.info(
                f"Memory stress test: {memory_peak:.1f}MB peak "
                f"({'PASS' if success else 'FAIL'})"
            )
            
        except Exception as e:
            logger.error(f"Memory stress test failed: {e}")
            result = BenchmarkResult(
                test_name="memory_stress_test",
                success=False,
                execution_time=0.0,
                memory_peak=0.0,
                memory_delta=0.0,
                cpu_percent=0.0,
                error_message=str(e)
            )
        
        if self.current_suite:
            self.current_suite.results.append(result)
        
        return result
    
    def run_caching_benchmark(self) -> BenchmarkResult:
        """Benchmark caching performance.
        
        Returns:
            Caching benchmark result
        """
        logger.info("Running caching performance benchmark")
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            # Test caching with the optimizer's intelligent cache
            cache = self.optimizer.intelligent_cache
            
            # Generate test functions to cache
            def expensive_operation(n: int) -> int:
                """Simulate expensive computation."""
                time.sleep(0.01)  # 10ms delay
                return sum(range(n))
            
            # Warm up cache with initial requests
            test_values = list(range(100, 200))
            warm_up_start = time.time()
            
            for value in test_values:
                cache_key = cache._generate_key(expensive_operation, (value,), {})
                found, result = cache.get(cache_key)
                
                if not found:
                    result = expensive_operation(value)
                    cache.set(cache_key, result)
            
            warm_up_time = time.time() - warm_up_start
            
            # Test cache hit performance
            cache_test_start = time.time()
            
            for _ in range(5):  # Run multiple iterations
                for value in test_values:
                    cache_key = cache._generate_key(expensive_operation, (value,), {})
                    found, result = cache.get(cache_key)
                    
                    if not found:  # Should not happen after warm-up
                        result = expensive_operation(value)
                        cache.set(cache_key, result)
            
            cache_test_time = time.time() - cache_test_start
            
            # Get cache metrics
            cache_metrics = cache.get_metrics()
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Success criteria
            success = (
                cache_metrics.hit_rate >= self.performance_targets['cache_hit_rate_target'] and
                cache_test_time < warm_up_time * 0.5  # Cache should be much faster
            )
            
            result = BenchmarkResult(
                test_name="caching_performance",
                success=success,
                execution_time=end_time - start_time,
                memory_peak=cache_metrics.memory_usage,
                memory_delta=end_memory - start_memory,
                cpu_percent=psutil.Process().cpu_percent(),
                throughput=cache_metrics.total_requests / (end_time - start_time),
                data_size=cache_metrics.total_requests,
                metadata={
                    'cache_hit_rate': cache_metrics.hit_rate,
                    'cache_size': cache_metrics.cache_size,
                    'total_requests': cache_metrics.total_requests,
                    'warm_up_time': warm_up_time,
                    'cached_test_time': cache_test_time,
                    'performance_improvement': (warm_up_time - cache_test_time) / warm_up_time * 100
                }
            )
            
            logger.info(
                f"Cache benchmark: {cache_metrics.hit_rate:.1%} hit rate "
                f"({'PASS' if success else 'FAIL'})"
            )
            
        except Exception as e:
            logger.error(f"Caching benchmark failed: {e}")
            result = BenchmarkResult(
                test_name="caching_performance",
                success=False,
                execution_time=0.0,
                memory_peak=0.0,
                memory_delta=0.0,
                cpu_percent=0.0,
                error_message=str(e)
            )
        
        if self.current_suite:
            self.current_suite.results.append(result)
        
        return result
    
    def run_concurrent_operations_benchmark(self, num_threads: int = 4) -> BenchmarkResult:
        """Benchmark concurrent operations performance.
        
        Args:
            num_threads: Number of concurrent threads to test
            
        Returns:
            Concurrent operations benchmark result
        """
        logger.info(f"Running concurrent operations benchmark with {num_threads} threads")
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            def data_processing_task(task_id: int) -> Dict[str, Any]:
                """Simulate data processing task."""
                # Generate test data
                data = pd.DataFrame({
                    'rpm': np.random.randint(800, 8000, 1000),
                    'throttle': np.random.random(1000) * 100,
                    'lambda': np.random.normal(0.85, 0.1, 1000)
                })
                
                # Perform calculations
                data['afr'] = data['lambda'] * 14.7
                data['load'] = data['throttle'] * np.random.random(1000)
                
                # Statistical operations
                stats = {
                    'task_id': task_id,
                    'mean_rpm': data['rpm'].mean(),
                    'max_afr': data['afr'].max(),
                    'std_load': data['load'].std(),
                    'row_count': len(data)
                }
                
                return stats
            
            # Run concurrent tasks
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [
                    executor.submit(data_processing_task, i) 
                    for i in range(num_threads * 2)  # 2x tasks per thread
                ]
                
                results_list = [future.result() for future in futures]
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            execution_time = end_time - start_time
            total_operations = len(results_list)
            throughput = total_operations / execution_time
            
            # Success if completed without errors and within reasonable time
            target_throughput = num_threads * 2  # At least 2 ops per second per thread
            success = (
                len(results_list) == num_threads * 2 and
                throughput >= target_throughput and
                execution_time < 10.0  # Should complete within 10 seconds
            )
            
            result = BenchmarkResult(
                test_name=f"concurrent_operations_{num_threads}_threads",
                success=success,
                execution_time=execution_time,
                memory_peak=end_memory,
                memory_delta=end_memory - start_memory,
                cpu_percent=psutil.Process().cpu_percent(),
                throughput=throughput,
                data_size=total_operations,
                metadata={
                    'num_threads': num_threads,
                    'total_tasks': total_operations,
                    'operations_per_second': throughput,
                    'average_time_per_task': execution_time / total_operations,
                    'target_throughput': target_throughput
                }
            )
            
            logger.info(
                f"Concurrent ops ({num_threads} threads): {throughput:.1f} ops/s "
                f"({'PASS' if success else 'FAIL'})"
            )
            
        except Exception as e:
            logger.error(f"Concurrent operations benchmark failed: {e}")
            result = BenchmarkResult(
                test_name=f"concurrent_operations_{num_threads}_threads",
                success=False,
                execution_time=0.0,
                memory_peak=0.0,
                memory_delta=0.0,
                cpu_percent=0.0,
                error_message=str(e)
            )
        
        if self.current_suite:
            self.current_suite.results.append(result)
        
        return result
    
    def run_full_benchmark_suite(self) -> BenchmarkSuite:
        """Run the complete benchmark suite.
        
        Returns:
            Complete benchmark results
        """
        self.start_benchmark_suite("FuelTune_Complete_Performance_Benchmark")
        
        logger.info("Starting full benchmark suite...")
        
        # CSV Import benchmarks
        self.run_csv_import_benchmark()
        
        # Memory stress test
        self.run_memory_stress_test()
        
        # Caching performance
        self.run_caching_benchmark()
        
        # Concurrent operations
        for num_threads in [2, 4, 8]:
            self.run_concurrent_operations_benchmark(num_threads)
        
        # Complete suite
        if self.current_suite:
            self.current_suite.end_time = datetime.now()
            self.current_suite.performance_summary = self._generate_performance_summary()
            
            # Save results
            self._save_benchmark_results(self.current_suite)
            
            logger.info("Full benchmark suite completed")
            return self.current_suite
        
        return None
    
    def _generate_test_csv_data(self, num_rows: int) -> pd.DataFrame:
        """Generate realistic test CSV data.
        
        Args:
            num_rows: Number of rows to generate
            
        Returns:
            Test DataFrame with FuelTech-like data
        """
        np.random.seed(42)  # For reproducible results
        
        data = {
            'TIME': np.linspace(0, num_rows * 0.1, num_rows),  # 0.1s intervals
            'RPM': np.random.randint(800, 8000, num_rows),
            'throttle_position': np.random.random(num_rows) * 100,
            'lambda_sensor': np.random.normal(0.85, 0.1, num_rows),
            'ignition_timing': np.random.normal(20, 5, num_rows),
            'map_pressure': np.random.normal(1.0, 0.3, num_rows),
            'engine_temp': np.random.normal(85, 10, num_rows),
            'gear': np.random.choice([1, 2, 3, 4, 5], num_rows),
            'two_step': np.random.choice([True, False], num_rows, p=[0.1, 0.9]),
            'launch_validated': np.random.choice([True, False], num_rows, p=[0.05, 0.95])
        }
        
        return pd.DataFrame(data)
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information for benchmark context.
        
        Returns:
            System information dictionary
        """
        try:
            return {
                'python_version': sys.version,
                'cpu_count': psutil.cpu_count(),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'memory_total': psutil.virtual_memory().total / 1024**3,  # GB
                'disk_space': psutil.disk_usage('/').total / 1024**3,  # GB
                'os_info': {
                    'system': os.name,
                    'platform': sys.platform
                },
                'benchmark_timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Could not collect complete system info: {e}")
            return {'error': str(e)}
    
    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary from benchmark results.
        
        Returns:
            Performance summary dictionary
        """
        if not self.current_suite or not self.current_suite.results:
            return {}
        
        results = self.current_suite.results
        
        # Overall statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        
        # Performance metrics
        avg_execution_time = np.mean([r.execution_time for r in results if r.execution_time > 0])
        max_memory_peak = max([r.memory_peak for r in results if r.memory_peak > 0])
        avg_throughput = np.mean([r.throughput for r in results if r.throughput])
        
        # Target compliance
        target_compliance = {
            'csv_import_10k': any(
                r.test_name == 'csv_import_10000_rows' and r.success 
                for r in results
            ),
            'memory_limit': max_memory_peak <= self.performance_targets['memory_usage_limit'],
            'cache_performance': any(
                r.test_name == 'caching_performance' and r.success
                for r in results
            )
        }
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': passed_tests / total_tests * 100,
            'avg_execution_time': avg_execution_time,
            'max_memory_peak': max_memory_peak,
            'avg_throughput': avg_throughput,
            'target_compliance': target_compliance,
            'performance_grade': self._calculate_performance_grade(target_compliance, passed_tests, total_tests)
        }
    
    def _calculate_performance_grade(self, compliance: Dict[str, bool], 
                                   passed: int, total: int) -> str:
        """Calculate overall performance grade.
        
        Args:
            compliance: Target compliance results
            passed: Number of passed tests
            total: Total number of tests
            
        Returns:
            Performance grade (A, B, C, D, F)
        """
        success_rate = passed / total if total > 0 else 0
        compliance_rate = sum(compliance.values()) / len(compliance) if compliance else 0
        
        overall_score = (success_rate * 0.6) + (compliance_rate * 0.4)
        
        if overall_score >= 0.9:
            return 'A'
        elif overall_score >= 0.8:
            return 'B'
        elif overall_score >= 0.7:
            return 'C'
        elif overall_score >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def _save_benchmark_results(self, suite: BenchmarkSuite) -> None:
        """Save benchmark results to JSON file.
        
        Args:
            suite: Benchmark suite to save
        """
        # Prepare data for JSON serialization
        suite_data = {
            'suite_name': suite.suite_name,
            'start_time': suite.start_time.isoformat(),
            'end_time': suite.end_time.isoformat() if suite.end_time else None,
            'system_info': suite.system_info,
            'performance_summary': suite.performance_summary,
            'results': []
        }
        
        for result in suite.results:
            result_data = {
                'test_name': result.test_name,
                'success': result.success,
                'execution_time': result.execution_time,
                'memory_peak': result.memory_peak,
                'memory_delta': result.memory_delta,
                'cpu_percent': result.cpu_percent,
                'throughput': result.throughput,
                'data_size': result.data_size,
                'error_message': result.error_message,
                'metadata': result.metadata
            }
            suite_data['results'].append(result_data)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(suite_data, f, indent=2)
        
        logger.info(f"Benchmark results saved to: {filepath}")
        
        # Also save a human-readable summary
        self._save_readable_summary(suite, self.output_dir / f"summary_{timestamp}.txt")
    
    def _save_readable_summary(self, suite: BenchmarkSuite, filepath: Path) -> None:
        """Save human-readable benchmark summary.
        
        Args:
            suite: Benchmark suite
            filepath: Path to save summary
        """
        with open(filepath, 'w') as f:
            f.write(f"FuelTune Streamlit Performance Benchmark Report\n")
            f.write(f"{'='*50}\n\n")
            
            f.write(f"Suite: {suite.suite_name}\n")
            f.write(f"Start Time: {suite.start_time}\n")
            if suite.end_time:
                duration = suite.end_time - suite.start_time
                f.write(f"End Time: {suite.end_time}\n")
                f.write(f"Duration: {duration}\n\n")
            
            # Performance Summary
            if suite.performance_summary:
                f.write("PERFORMANCE SUMMARY\n")
                f.write(f"-" * 20 + "\n")
                summary = suite.performance_summary
                f.write(f"Overall Grade: {summary.get('performance_grade', 'N/A')}\n")
                f.write(f"Tests Passed: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)} ")
                f.write(f"({summary.get('success_rate', 0):.1f}%)\n")
                f.write(f"Max Memory: {summary.get('max_memory_peak', 0):.1f} MB\n")
                f.write(f"Avg Execution Time: {summary.get('avg_execution_time', 0):.3f}s\n\n")
            
            # Individual Test Results
            f.write("DETAILED RESULTS\n")
            f.write(f"-" * 20 + "\n")
            
            for result in suite.results:
                status = "PASS" if result.success else "FAIL"
                f.write(f"[{status}] {result.test_name}\n")
                f.write(f"  Time: {result.execution_time:.3f}s\n")
                f.write(f"  Memory: {result.memory_peak:.1f}MB peak\n")
                f.write(f"  CPU: {result.cpu_percent:.1f}%\n")
                
                if result.throughput:
                    f.write(f"  Throughput: {result.throughput:.1f} ops/sec\n")
                
                if result.error_message:
                    f.write(f"  Error: {result.error_message}\n")
                
                f.write("\n")
        
        logger.info(f"Readable summary saved to: {filepath}")


def main():
    """Main entry point for benchmark script."""
    parser = argparse.ArgumentParser(description="FuelTune Streamlit Performance Benchmark")
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("benchmark_results"),
        help="Output directory for benchmark results"
    )
    parser.add_argument(
        "--test-type",
        choices=['full', 'csv', 'memory', 'cache', 'concurrent'],
        default='full',
        help="Type of benchmark to run"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Number of threads for concurrent tests"
    )
    parser.add_argument(
        "--verbose",
        action='store_true',
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create benchmark instance
    benchmark = FuelTuneBenchmark(output_dir=args.output_dir)
    
    logger.info(f"Starting FuelTune benchmark - Type: {args.test_type}")
    
    try:
        if args.test_type == 'full':
            suite = benchmark.run_full_benchmark_suite()
        elif args.test_type == 'csv':
            benchmark.start_benchmark_suite("CSV_Import_Benchmark")
            benchmark.run_csv_import_benchmark()
            suite = benchmark.current_suite
        elif args.test_type == 'memory':
            benchmark.start_benchmark_suite("Memory_Stress_Test")
            benchmark.run_memory_stress_test()
            suite = benchmark.current_suite
        elif args.test_type == 'cache':
            benchmark.start_benchmark_suite("Cache_Performance_Test")
            benchmark.run_caching_benchmark()
            suite = benchmark.current_suite
        elif args.test_type == 'concurrent':
            benchmark.start_benchmark_suite("Concurrent_Operations_Test")
            benchmark.run_concurrent_operations_benchmark(args.threads)
            suite = benchmark.current_suite
        
        if suite and suite.performance_summary:
            grade = suite.performance_summary.get('performance_grade', 'N/A')
            passed = suite.performance_summary.get('passed_tests', 0)
            total = suite.performance_summary.get('total_tests', 0)
            
            logger.info(f"Benchmark completed - Grade: {grade}, Passed: {passed}/{total}")
            
            # Exit with error code if performance is poor
            if grade in ['D', 'F']:
                sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()