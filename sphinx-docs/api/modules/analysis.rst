==================
Módulo de Análise
==================

O módulo :mod:`src.analysis` contém todos os algoritmos e ferramentas especializadas para análise 
de dados de telemetria automotiva. Implementa 9 módulos especializados que cobrem desde análises 
básicas de performance até modelos preditivos avançados.

.. currentmodule:: src.analysis

Visão Geral
===========

O sistema de análise segue uma arquitetura modular e extensível:

- **Modularidade**: Cada tipo de análise é um módulo independente
- **Consistência**: Interface comum para todos os analisadores
- **Performance**: Algoritmos otimizados para processamento em lote
- **Extensibilidade**: Fácil adição de novos tipos de análise

.. mermaid::

   graph TD
       DATA[Dados de Telemetria] --> FACTORY[Analyzer Factory]
       FACTORY --> PERF[Performance Analysis]
       FACTORY --> STATS[Statistical Analysis]
       FACTORY --> TIMESERIES[Time Series Analysis]
       FACTORY --> CORR[Correlation Analysis]
       FACTORY --> ANOMALY[Anomaly Detection]
       FACTORY --> PREDICT[Predictive Analysis]
       FACTORY --> DYNAMIC[Dynamic Analysis]
       FACTORY --> FUEL[Fuel Efficiency Analysis]
       FACTORY --> REPORTS[Report Generation]
       
       PERF --> RESULTS[Analysis Results]
       STATS --> RESULTS
       TIMESERIES --> RESULTS
       CORR --> RESULTS
       ANOMALY --> RESULTS
       PREDICT --> RESULTS
       DYNAMIC --> RESULTS
       FUEL --> RESULTS
       REPORTS --> RESULTS

Analyzer Factory
================

.. automodule:: src.analysis.analysis
   :members:
   :undoc-members:
   :show-inheritance:

**Factory Pattern:**

.. code-block:: python

   from src.analysis import AnalyzerFactory
   
   # Criar analisador específico
   perf_analyzer = AnalyzerFactory.create_analyzer("performance")
   stats_analyzer = AnalyzerFactory.create_analyzer("statistics")
   
   # Listar analisadores disponíveis
   available_analyzers = AnalyzerFactory.list_analyzers()
   print("Analisadores disponíveis:", available_analyzers)
   
   # Executar múltiplas análises
   results = {}
   for analyzer_type in ['performance', 'statistics', 'correlation']:
       analyzer = AnalyzerFactory.create_analyzer(analyzer_type)
       results[analyzer_type] = analyzer.analyze(data)

Performance Analysis
====================

.. automodule:: src.analysis.performance
   :members:
   :undoc-members:
   :show-inheritance:

**Análises de Performance:**

.. code-block:: python

   from src.analysis.performance import PerformanceAnalyzer
   
   analyzer = PerformanceAnalyzer()
   
   # Análise completa de performance
   perf_results = analyzer.analyze(telemetry_data)
   
   print("Resultados de Performance:")
   print(f"Potência máxima: {perf_results.max_power:.1f} HP")
   print(f"Torque máximo: {perf_results.max_torque:.1f} Nm")
   print(f"RPM de potência máxima: {perf_results.peak_power_rpm:.0f}")
   
   # Calcular curvas de potência e torque
   power_curve = analyzer.calculate_power_curve(
       data=telemetry_data,
       rpm_bins=range(1000, 8000, 100)
   )
   
   # Análise de aceleração
   accel_analysis = analyzer.analyze_acceleration(
       data=telemetry_data,
       speed_intervals=[(0, 100), (100, 200)]  # 0-100, 100-200 km/h
   )
   
   print(f"0-100 km/h: {accel_analysis['0-100']:.2f}s")

**Métricas Disponíveis:**

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Métrica
     - Descrição
   * - **max_power**
     - Potência máxima calculada (HP/CV/kW)
   * - **max_torque**
     - Torque máximo (Nm/lb-ft)
   * - **power_curve**
     - Curva de potência por RPM
   * - **torque_curve**
     - Curva de torque por RPM
   * - **acceleration_times**
     - Tempos de aceleração (0-100, 100-200, etc.)
   * - **quarter_mile**
     - Tempo e velocidade final em 1/4 de milha
   * - **power_to_weight**
     - Relação potência/peso
   * - **thermal_efficiency**
     - Eficiência térmica do motor

Statistical Analysis
====================

.. automodule:: src.analysis.statistics
   :members:
   :undoc-members:
   :show-inheritance:

**Análises Estatísticas:**

.. code-block:: python

   from src.analysis.statistics import StatisticalAnalyzer
   
   analyzer = StatisticalAnalyzer()
   
   # Estatísticas descritivas
   desc_stats = analyzer.descriptive_statistics(telemetry_data)
   
   for parameter, stats in desc_stats.items():
       print(f"{parameter}:")
       print(f"  Média: {stats.mean:.2f}")
       print(f"  Mediana: {stats.median:.2f}")
       print(f"  Desvio padrão: {stats.std:.2f}")
       print(f"  Min/Max: {stats.min:.2f}/{stats.max:.2f}")
   
   # Análise de distribuição
   dist_analysis = analyzer.distribution_analysis(
       data=telemetry_data,
       parameters=['RPM', 'MAP', 'LAMBDA']
   )
   
   # Testes estatísticos
   normality_tests = analyzer.test_normality(telemetry_data)
   for param, result in normality_tests.items():
       print(f"{param} é normal: {result.is_normal}")
       print(f"P-value: {result.p_value:.4f}")
   
   # Intervalos de confiança
   confidence_intervals = analyzer.confidence_intervals(
       data=telemetry_data,
       confidence=0.95
   )

Time Series Analysis
====================

.. automodule:: src.analysis.time_series
   :members:
   :undoc-members:
   :show-inheritance:

**Análises Temporais:**

.. code-block:: python

   from src.analysis.time_series import TimeSeriesAnalyzer
   
   analyzer = TimeSeriesAnalyzer()
   
   # Detecção de tendências
   trends = analyzer.detect_trends(
       data=telemetry_data,
       parameters=['ENGINE_TEMP', 'MAP', 'LAMBDA']
   )
   
   for param, trend in trends.items():
       print(f"{param}: tendência {trend.direction} ({trend.strength})")
   
   # Análise de sazonalidade
   seasonality = analyzer.analyze_seasonality(
       data=telemetry_data,
       parameter='RPM',
       period=1000  # Ciclos do motor
   )
   
   # Decomposição da série temporal
   decomposition = analyzer.decompose_series(
       data=telemetry_data['MAP'],
       model='multiplicative'
   )
   
   # Autocorrelação
   autocorr = analyzer.calculate_autocorrelation(
       data=telemetry_data['RPM'],
       max_lags=100
   )

Correlation Analysis
====================

.. automodule:: src.analysis.correlation
   :members:
   :undoc-members:
   :show-inheritance:

**Análises de Correlação:**

.. code-block:: python

   from src.analysis.correlation import CorrelationAnalyzer
   
   analyzer = CorrelationAnalyzer()
   
   # Matriz de correlação
   correlation_matrix = analyzer.correlation_matrix(
       data=telemetry_data,
       method='pearson'  # 'pearson', 'spearman', 'kendall'
   )
   
   # Encontrar correlações mais fortes
   strong_correlations = analyzer.find_strong_correlations(
       correlation_matrix,
       threshold=0.7
   )
   
   for corr in strong_correlations:
       print(f"{corr.param1} ↔ {corr.param2}: {corr.value:.3f}")
   
   # Análise de correlação parcial
   partial_corr = analyzer.partial_correlation(
       data=telemetry_data,
       target='MAP',
       control_vars=['RPM', 'THROTTLE_POS']
   )
   
   # Correlação cruzada (cross-correlation)
   cross_corr = analyzer.cross_correlation(
       x=telemetry_data['THROTTLE_POS'],
       y=telemetry_data['MAP'],
       max_lags=50
   )

Anomaly Detection
=================

.. automodule:: src.analysis.anomaly
   :members:
   :undoc-members:
   :show-inheritance:

**Detecção de Anomalias:**

.. code-block:: python

   from src.analysis.anomaly import AnomalyDetector
   
   detector = AnomalyDetector()
   
   # Detecção usando múltiplos algoritmos
   anomalies = detector.detect_anomalies(
       data=telemetry_data,
       methods=['isolation_forest', 'local_outlier', 'z_score']
   )
   
   print(f"Anomalias detectadas: {len(anomalies)}")
   for anomaly in anomalies:
       print(f"Linha {anomaly.index}: {anomaly.description}")
       print(f"  Método: {anomaly.detection_method}")
       print(f"  Severidade: {anomaly.severity}")
   
   # Detecção de knock (batida de pino)
   knock_detection = detector.detect_engine_knock(
       data=telemetry_data,
       knock_threshold=5.0
   )
   
   # Detecção de mistura pobre
   lean_conditions = detector.detect_lean_conditions(
       data=telemetry_data,
       lambda_threshold=1.1
   )
   
   # Detecção de superaquecimento
   overheat_events = detector.detect_overheating(
       data=telemetry_data,
       temp_threshold=105  # °C
   )

Predictive Analysis
===================

.. automodule:: src.analysis.predictive
   :members:
   :undoc-members:
   :show-inheritance:

**Análises Preditivas:**

.. code-block:: python

   from src.analysis.predictive import PredictiveAnalyzer
   
   analyzer = PredictiveAnalyzer()
   
   # Modelo de previsão de consumo
   consumption_model = analyzer.build_consumption_model(
       training_data=telemetry_data,
       features=['RPM', 'MAP', 'THROTTLE_POS', 'LAMBDA']
   )
   
   # Prever consumo futuro
   future_consumption = consumption_model.predict(
       new_data=test_data,
       horizon=1000  # próximas 1000 amostras
   )
   
   # Modelo de previsão de temperatura
   temp_model = analyzer.build_temperature_model(
       data=telemetry_data,
       model_type='lstm'  # 'linear', 'polynomial', 'lstm'
   )
   
   # Detecção precoce de problemas
   early_warnings = analyzer.predict_potential_issues(
       data=telemetry_data,
       look_ahead=500
   )
   
   for warning in early_warnings:
       print(f"Alerta: {warning.issue_type}")
       print(f"Probabilidade: {warning.probability:.2%}")
       print(f"Tempo estimado: {warning.time_to_issue:.0f}s")

Dynamic Analysis
================

.. automodule:: src.analysis.dynamics
   :members:
   :undoc-members:
   :show-inheritance:

**Análises de Dinâmica:**

.. code-block:: python

   from src.analysis.dynamics import DynamicAnalyzer
   
   analyzer = DynamicAnalyzer()
   
   # Análise de resposta do motor
   throttle_response = analyzer.analyze_throttle_response(
       data=telemetry_data,
       response_time_threshold=0.5  # segundos
   )
   
   print(f"Tempo de resposta médio: {throttle_response.mean_response_time:.3f}s")
   
   # Análise de transientes
   transient_analysis = analyzer.analyze_transients(
       data=telemetry_data,
       parameters=['MAP', 'LAMBDA', 'IGNITION_TIMING']
   )
   
   # Análise de estabilidade
   stability_metrics = analyzer.calculate_stability(
       data=telemetry_data,
       steady_state_threshold=0.02  # 2% de variação
   )
   
   # Análise de harmônicos
   harmonic_analysis = analyzer.harmonic_analysis(
       data=telemetry_data['MAP'],
       fundamental_freq=analyzer.estimate_fundamental_frequency(
           telemetry_data['RPM']
       )
   )

Fuel Efficiency Analysis
========================

.. automodule:: src.analysis.fuel_efficiency
   :members:
   :undoc-members:
   :show-inheritance:

**Análise de Eficiência de Combustível:**

.. code-block:: python

   from src.analysis.fuel_efficiency import FuelEfficiencyAnalyzer
   
   analyzer = FuelEfficiencyAnalyzer()
   
   # Análise completa de consumo
   efficiency_analysis = analyzer.analyze_fuel_efficiency(
       data=telemetry_data,
       fuel_flow_column='FUEL_FLOW',
       speed_column='VEHICLE_SPEED'
   )
   
   print("Eficiência de Combustível:")
   print(f"Consumo médio: {efficiency_analysis.avg_consumption:.2f} L/100km")
   print(f"Consumo mínimo: {efficiency_analysis.best_efficiency:.2f} L/100km")
   print(f"BSFC médio: {efficiency_analysis.bsfc_avg:.0f} g/kWh")
   
   # Mapa de eficiência
   efficiency_map = analyzer.create_efficiency_map(
       data=telemetry_data,
       rpm_bins=range(1000, 8000, 200),
       load_bins=range(0, 100, 10)
   )
   
   # Análise por faixas de RPM
   rpm_efficiency = analyzer.analyze_by_rpm_ranges(
       data=telemetry_data,
       rpm_ranges=[(1000, 2000), (2000, 4000), (4000, 6000), (6000, 8000)]
   )

Report Generation
=================

.. automodule:: src.analysis.reports
   :members:
   :undoc-members:
   :show-inheritance:

**Geração de Relatórios:**

.. code-block:: python

   from src.analysis.reports import ReportGenerator
   
   generator = ReportGenerator()
   
   # Relatório completo de análise
   full_report = generator.generate_full_report(
       data=telemetry_data,
       analyses=['performance', 'statistics', 'anomalies'],
       include_charts=True,
       format='pdf'  # 'pdf', 'html', 'docx'
   )
   
   # Relatório executivo
   executive_summary = generator.generate_executive_summary(
       analysis_results=all_results,
       key_findings=['max_power', 'fuel_efficiency', 'anomaly_count']
   )
   
   # Relatório técnico detalhado
   technical_report = generator.generate_technical_report(
       data=telemetry_data,
       analysis_results=all_results,
       include_raw_data=False,
       include_methodology=True
   )
   
   # Salvar relatórios
   generator.save_report(full_report, "relatorio_completo.pdf")
   generator.save_report(executive_summary, "sumario_executivo.html")

Configuração e Customização
============================

**Configurações de Análise:**

.. code-block:: python

   from src.analysis.config import AnalysisConfig
   
   # Configuração global
   config = AnalysisConfig(
       default_confidence_level=0.95,
       outlier_detection_method='z_score',
       outlier_threshold=3.0,
       performance_units='metric',  # 'metric' ou 'imperial'
       temperature_units='celsius',
       enable_caching=True,
       max_cache_size_mb=500
   )
   
   # Aplicar configuração
   AnalysisConfig.set_global_config(config)

**Análises Customizadas:**

.. code-block:: python

   from src.analysis import BaseAnalyzer
   
   class CustomAnalyzer(BaseAnalyzer):
       def __init__(self):
           super().__init__()
           self.name = "custom_analysis"
       
       def analyze(self, data: pd.DataFrame) -> dict:
           # Implementar análise customizada
           results = self.perform_custom_analysis(data)
           
           return {
               'type': self.name,
               'results': results,
               'metadata': self.get_analysis_metadata()
           }
       
       def perform_custom_analysis(self, data: pd.DataFrame):
           # Sua lógica de análise aqui
           return custom_calculation(data)
   
   # Registrar novo analisador
   AnalyzerFactory.register_analyzer("custom", CustomAnalyzer)

Performance e Otimizações
=========================

**Benchmarks de Performance:**

.. list-table::
   :widths: 25 20 25 30
   :header-rows: 1

   * - Análise
     - Tamanho dos Dados
     - Tempo Médio
     - Uso de Memória
   * - Performance
     - 10k pontos
     - 0.3s
     - 25MB
   * - Statistical
     - 10k pontos
     - 0.2s
     - 15MB
   * - Correlation
     - 10k pontos
     - 0.5s
     - 30MB
   * - Anomaly Detection
     - 10k pontos
     - 1.2s
     - 40MB
   * - Predictive
     - 10k pontos
     - 2.5s
     - 60MB

**Otimizações Recomendadas:**

.. code-block:: python

   # Use análise em paralelo para múltiplos datasets
   from concurrent.futures import ThreadPoolExecutor
   
   def analyze_multiple_sessions(sessions: List[TelemetryData]):
       with ThreadPoolExecutor(max_workers=4) as executor:
           futures = []
           for session in sessions:
               analyzer = AnalyzerFactory.create_analyzer("performance")
               future = executor.submit(analyzer.analyze, session)
               futures.append(future)
           
           results = [future.result() for future in futures]
       return results
   
   # Enable caching para análises repetitivas
   from src.analysis.cache import enable_analysis_caching
   enable_analysis_caching(ttl=3600)  # 1 hora
   
   # Use subset de colunas quando possível
   analyzer.analyze(data[['TIME', 'RPM', 'MAP', 'LAMBDA']])

Integração com Visualizações
=============================

**Preparação de Dados para Plotly:**

.. code-block:: python

   from src.analysis.visualization import prepare_for_plotting
   
   # Preparar dados de performance para gráfico
   plot_data = prepare_for_plotting(
       analysis_results=perf_results,
       chart_type='power_curve'
   )
   
   # Gerar configuração de gráfico
   chart_config = {
       'data': plot_data,
       'layout': {
           'title': 'Curva de Potência vs RPM',
           'xaxis': {'title': 'RPM'},
           'yaxis': {'title': 'Potência (HP)'}
       }
   }

**Exportação para Dashboard:**

.. code-block:: python

   # Formatar resultados para Streamlit
   dashboard_data = analyzer.format_for_dashboard(analysis_results)
   
   # Métricas principais
   st.metric("Potência Máxima", f"{dashboard_data['max_power']:.1f} HP")
   st.metric("Torque Máximo", f"{dashboard_data['max_torque']:.1f} Nm")
   
   # Gráficos interativos
   st.plotly_chart(dashboard_data['power_curve_chart'])

.. note::
   Para exemplos completos de integração com a UI, consulte :doc:`../ui/index`.

----

**Módulos Relacionados:**
   - :doc:`data` - Dados processados utilizados pelas análises
   - :doc:`ui` - Interface para visualização dos resultados
   - :doc:`integration` - Exportação e workflow dos resultados