#!/usr/bin/env python3
"""
Teste de performance do ANALYSIS-ENGINE
"""
import time
import tracemalloc
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analysis.analysis import AnalysisEngine

def generate_test_data(num_points: int) -> pd.DataFrame:
    """Generate test data with 10k points."""
    np.random.seed(42)
    
    # Generate time series
    timestamps = pd.date_range('2023-01-01', periods=num_points, freq='1S')
    
    # Generate realistic engine data
    base_rpm = 1200 + np.random.normal(0, 200, num_points)
    base_rpm = np.clip(base_rpm, 600, 6000)
    
    throttle = np.random.beta(2, 5, num_points) * 100
    
    # Generate related parameters
    data = pd.DataFrame({
        'timestamp': timestamps,
        'rpm': base_rpm,
        'throttle_position': throttle,
        'engine_load': throttle * 0.8 + np.random.normal(0, 5, num_points),
        'intake_air_temp': 25 + np.random.normal(0, 10, num_points),
        'coolant_temp': 85 + np.random.normal(0, 15, num_points),
        'fuel_flow': base_rpm * 0.001 + throttle * 0.0005 + np.random.normal(0, 0.1, num_points),
        'lambda_1': 1.0 + np.random.normal(0, 0.05, num_points),
        'manifold_pressure': 100 + throttle * 0.5 + np.random.normal(0, 10, num_points),
        'ignition_timing': 15 + throttle * 0.1 + np.random.normal(0, 2, num_points),
        'vehicle_speed': throttle * 1.8 + np.random.normal(0, 10, num_points)
    })
    
    return data

def test_performance():
    """Test performance with 10k data points."""
    print("Iniciando teste de performance...")
    
    # Start memory tracking
    tracemalloc.start()
    
    # Generate test data
    print("Gerando dados de teste (10k pontos)...")
    test_data = generate_test_data(10000)
    print(f"Dados gerados: {len(test_data)} pontos")
    
    # Initialize analysis engine
    engine = AnalysisEngine()
    
    # Measure analysis time
    start_time = time.time()
    
    try:
        # Run analysis
        result = engine.analyze(test_data, analysis_type='comprehensive')
        analysis_time = time.time() - start_time
        
        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Results
        print("\n=== RESULTADOS DO TESTE DE PERFORMANCE ===")
        print(f"Tempo de análise: {analysis_time:.3f}s")
        print(f"Uso de memória atual: {current / 1024 / 1024:.1f}MB")
        print(f"Pico de memória: {peak / 1024 / 1024:.1f}MB")
        print(f"Dados processados: {len(test_data)} pontos")
        
        # Performance criteria
        time_ok = analysis_time < 1.0
        memory_ok = peak < 500 * 1024 * 1024  # 500MB
        
        print("\n=== CRITÉRIOS ===")
        print(f"Tempo < 1s: {'✓' if time_ok else '✗'} ({analysis_time:.3f}s)")
        print(f"Memória < 500MB: {'✓' if memory_ok else '✗'} ({peak / 1024 / 1024:.1f}MB)")
        
        return time_ok and memory_ok, analysis_time, peak / 1024 / 1024
        
    except Exception as e:
        tracemalloc.stop()
        print(f"\nERRO durante análise: {e}")
        return False, 999, 999

if __name__ == "__main__":
    success, time_taken, memory_used = test_performance()
    print(f"\nResultado: {'PASSOU' if success else 'FALHOU'}")