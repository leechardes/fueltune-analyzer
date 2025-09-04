#!/usr/bin/env python3
"""
Performance test script for analyze() methods.

Tests the performance of the newly implemented analyze() methods
in all analyzer classes to ensure they meet performance requirements.
"""

import time
import numpy as np
import pandas as pd
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import analyzers
from src.analysis.anomaly import AnomalyDetector
from src.analysis.correlation import CorrelationAnalyzer
from src.analysis.statistics import StatisticalAnalyzer
from src.analysis.time_series import TimeSeriesAnalyzer
from src.analysis.performance import PerformanceAnalyzer
from src.analysis.predictive import PredictiveAnalyzer


def create_test_data(size=1000):
    """Create test data for performance testing."""
    np.random.seed(42)
    
    return pd.DataFrame({
        'rpm': np.random.uniform(1000, 6000, size),
        'throttle': np.random.uniform(0, 100, size),
        'boost': np.random.uniform(-0.5, 2.5, size),
        'afr': np.random.uniform(10, 18, size),
        'iat': np.random.uniform(20, 80, size),
        'ect': np.random.uniform(80, 110, size),
        'vehicle_speed': np.random.uniform(0, 150, size),
        'time': np.arange(size)
    })


def test_analyzer_performance(analyzer_class, test_data, analyzer_name):
    """Test performance of an analyzer's analyze method."""
    try:
        analyzer = analyzer_class()
        
        start_time = time.time()
        result = analyzer.analyze(test_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Check if result is valid
        success = isinstance(result, dict) and len(result) > 0
        
        return {
            'analyzer': analyzer_name,
            'execution_time': execution_time,
            'success': success,
            'error': result.get('error') if isinstance(result, dict) else None
        }
        
    except Exception as e:
        return {
            'analyzer': analyzer_name,
            'execution_time': None,
            'success': False,
            'error': str(e)
        }


def run_performance_tests():
    """Run performance tests on all analyzers."""
    print("Running performance tests for analyze() methods...")
    print("=" * 60)
    
    # Create test data
    small_data = create_test_data(100)
    medium_data = create_test_data(1000)
    large_data = create_test_data(5000)
    
    # Define analyzers to test
    analyzers = [
        (AnomalyDetector, 'AnomalyDetector'),
        (CorrelationAnalyzer, 'CorrelationAnalyzer'),
        (StatisticalAnalyzer, 'StatisticalAnalyzer'),
        (TimeSeriesAnalyzer, 'TimeSeriesAnalyzer'),
        (PerformanceAnalyzer, 'PerformanceAnalyzer'),
        (PredictiveAnalyzer, 'PredictiveAnalyzer'),
    ]
    
    # Test each analyzer with different data sizes
    for data_size, data_name in [(small_data, 'Small (100 rows)'), 
                                 (medium_data, 'Medium (1000 rows)'), 
                                 (large_data, 'Large (5000 rows)')]:
        
        print(f"\nTesting with {data_name}:")
        print("-" * 40)
        
        results = []
        for analyzer_class, analyzer_name in analyzers:
            result = test_analyzer_performance(analyzer_class, data_size, analyzer_name)
            results.append(result)
            
            status = "✓ PASS" if result['success'] else "✗ FAIL"
            time_str = f"{result['execution_time']:.3f}s" if result['execution_time'] else "N/A"
            
            print(f"{analyzer_name:20} | {time_str:>8} | {status}")
            
            if result['error']:
                print(f"                     | Error: {result['error']}")
        
        # Calculate summary statistics
        successful_tests = [r for r in results if r['success']]
        if successful_tests:
            avg_time = sum(r['execution_time'] for r in successful_tests) / len(successful_tests)
            max_time = max(r['execution_time'] for r in successful_tests)
            print(f"\nSummary for {data_name}:")
            print(f"  Successful: {len(successful_tests)}/{len(results)}")
            print(f"  Average time: {avg_time:.3f}s")
            print(f"  Maximum time: {max_time:.3f}s")


def main():
    """Main function to run performance tests."""
    print("FuelTune Analysis Engine - Performance Test")
    print("Testing analyze() methods implementation")
    print("=" * 60)
    
    run_performance_tests()
    
    print("\n" + "=" * 60)
    print("Performance testing completed!")
    print("\nRecommendations:")
    print("- Methods should complete within 5 seconds for 1000 rows")
    print("- Methods should complete within 30 seconds for 5000 rows")
    print("- All methods should return valid dictionary results")


if __name__ == "__main__":
    main()