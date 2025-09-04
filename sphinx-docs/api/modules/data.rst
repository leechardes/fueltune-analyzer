================
Módulo de Dados
================

O módulo :mod:`src.data` é responsável por todo o processamento, validação e modelagem dos dados 
de telemetria FuelTech. Este é o núcleo do sistema, fornecendo uma base sólida e confiável 
para todas as análises posteriores.

.. currentmodule:: src.data

Visão Geral
===========

O módulo de dados implementa uma arquitetura em camadas para garantir:

- **Robustez**: Validação rigorosa de dados de entrada
- **Performance**: Processamento otimizado para arquivos grandes
- **Flexibilidade**: Suporte a diferentes formatos e versões FuelTech
- **Confiabilidade**: Sistema de cache e recovery automático

.. mermaid::

   graph TD
       CSV[Arquivo CSV] --> PARSER[CSV Parser]
       PARSER --> VALIDATOR[Validators]
       VALIDATOR --> NORMALIZER[Normalizer]
       NORMALIZER --> MODELS[Data Models]
       MODELS --> CACHE[Cache System]
       MODELS --> DB[Database]

Módulos e Componentes
====================

CSV Parser
----------

.. automodule:: src.data.csv_parser
   :members:
   :undoc-members:
   :show-inheritance:

**Exemplo de Uso:**

.. code-block:: python

   from src.data.csv_parser import CSVParser, parse_fueltech_csv
   
   # Uso básico
   data = parse_fueltech_csv("telemetria.csv")
   
   # Uso avançado com configurações
   parser = CSVParser(
       encoding="latin-1",
       skip_malformed_lines=True,
       validate_on_load=True
   )
   data = parser.parse("telemetria.csv")
   
   # Processamento chunked para arquivos grandes
   for chunk in parser.parse_chunked("arquivo_grande.csv", chunk_size=5000):
       process_chunk(chunk)

Modelos de Dados
----------------

.. automodule:: src.data.models
   :members:
   :undoc-members:
   :show-inheritance:

**Modelos Principais:**

.. autoclass:: src.data.models.TelemetryData
   :members:
   :show-inheritance:

.. autoclass:: src.data.models.VehicleProfile
   :members:
   :show-inheritance:

.. autoclass:: src.data.models.SessionMetadata
   :members:
   :show-inheritance:

**Exemplo de Uso:**

.. code-block:: python

   from src.data.models import TelemetryData, VehicleProfile
   import pandas as pd
   
   # Criar perfil de veículo
   vehicle = VehicleProfile(
       name="Civic Si",
       engine="K20A",
       weight=1200.0,
       fuel_type="gasoline"
   )
   
   # Criar dados de telemetria
   telemetry = TelemetryData(
       data=df,
       vehicle_profile=vehicle,
       session_date="2024-09-03",
       track_name="Autódromo de Interlagos"
   )
   
   # Acessar estatísticas básicas
   stats = telemetry.basic_stats()
   print(f"RPM máximo: {stats['RPM']['max']}")

Validadores
-----------

.. automodule:: src.data.validators
   :members:
   :undoc-members:
   :show-inheritance:

**Schemas de Validação:**

.. code-block:: python

   from src.data.validators import FuelTechSchema, validate_telemetry_data
   import pandera as pa
   
   # Validação automática
   is_valid, errors = validate_telemetry_data(df)
   
   if not is_valid:
       for error in errors:
           print(f"Erro na coluna {error.column}: {error.message}")
   
   # Validação com schema customizado
   custom_schema = FuelTechSchema.with_custom_ranges({
       'RPM': {'max_value': 8000},
       'MAP': {'min_value': 50}
   })
   
   try:
       validated_data = custom_schema.validate(df)
   except pa.errors.SchemaError as e:
       handle_validation_error(e)

Normalizador
------------

.. automodule:: src.data.normalizer
   :members:
   :undoc-members:
   :show-inheritance:

**Exemplo de Normalização:**

.. code-block:: python

   from src.data.normalizer import DataNormalizer
   
   normalizer = DataNormalizer()
   
   # Normalizar dados brutos
   normalized_data = normalizer.normalize(raw_data)
   
   # Aplicar filtros específicos
   filtered_data = normalizer.apply_filters(
       data=normalized_data,
       filters={
           'rpm_range': (1000, 7000),
           'remove_outliers': True,
           'smooth_noise': True
       }
   )
   
   # Reamostrar dados (útil para análises temporais)
   resampled = normalizer.resample(
       data=filtered_data,
       frequency='1S',  # 1 segundo
       method='interpolate'
   )

Sistema de Cache
----------------

.. automodule:: src.data.cache
   :members:
   :undoc-members:
   :show-inheritance:

**Exemplo de Cache:**

.. code-block:: python

   from src.data.cache import DataCache, cache_analysis_result
   
   # Usar decorador para cache automático
   @cache_analysis_result(ttl=3600)  # 1 hora
   def expensive_analysis(data: pd.DataFrame) -> dict:
       # Análise computacionalmente custosa
       return complex_calculation(data)
   
   # Usar cache manualmente
   cache = DataCache()
   
   # Verificar se resultado existe
   if cache.exists("analysis_results", data_hash):
       results = cache.get("analysis_results", data_hash)
   else:
       results = perform_analysis(data)
       cache.set("analysis_results", data_hash, results, ttl=1800)

Banco de Dados
--------------

.. automodule:: src.data.database
   :members:
   :undoc-members:
   :show-inheritance:

**Exemplo de Persistência:**

.. code-block:: python

   from src.data.database import DatabaseManager, SessionRepository
   
   # Configurar conexão
   db = DatabaseManager("sqlite:///fueltune.db")
   
   # Repository pattern para sessões
   session_repo = SessionRepository(db)
   
   # Salvar sessão
   session_id = session_repo.save_session(
       telemetry_data=data,
       metadata={
           'vehicle': 'Civic Si',
           'track': 'Interlagos',
           'date': '2024-09-03'
       }
   )
   
   # Buscar sessões
   sessions = session_repo.find_sessions(
       vehicle='Civic Si',
       date_range=('2024-09-01', '2024-09-30')
   )
   
   # Carregar dados da sessão
   loaded_data = session_repo.load_session(session_id)

Qualidade de Dados
-------------------

.. automodule:: src.data.quality
   :members:
   :undoc-members:
   :show-inheritance:

**Análise de Qualidade:**

.. code-block:: python

   from src.data.quality import DataQualityAnalyzer
   
   analyzer = DataQualityAnalyzer()
   
   # Análise completa de qualidade
   quality_report = analyzer.analyze_quality(data)
   
   print("Relatório de Qualidade:")
   print(f"Completude: {quality_report.completeness:.2%}")
   print(f"Consistência: {quality_report.consistency:.2%}")
   print(f"Outliers detectados: {quality_report.outliers_count}")
   
   # Obter sugestões de melhoria
   suggestions = analyzer.get_improvement_suggestions(data)
   for suggestion in suggestions:
       print(f"- {suggestion.description}")

Configurações e Constantes
===========================

**Limites de Segurança FuelTech:**

.. code-block:: python

   from src.data.constants import FUELTECH_LIMITS, PORTUGUESE_FIELD_MAPPING
   
   # Verificar limites de RPM
   rpm_limits = FUELTECH_LIMITS['RPM']
   print(f"RPM mínimo: {rpm_limits['min']}")
   print(f"RPM máximo: {rpm_limits['max']}")
   
   # Mapeamento de campos portugueses
   portuguese_name = PORTUGUESE_FIELD_MAPPING.get('ENGINE_TEMP', 'Temperatura do Motor')

**Configurações de Parsing:**

.. code-block:: python

   from src.data.config import ParsingConfig
   
   config = ParsingConfig(
       default_encoding='latin-1',
       max_file_size_mb=100,
       chunk_size=5000,
       validation_enabled=True,
       cache_enabled=True
   )

Tratamento de Erros
===================

**Exceções Personalizadas:**

.. code-block:: python

   from src.data.exceptions import (
       DataValidationError,
       ParsingError,
       CacheError
   )
   
   try:
       data = parse_fueltech_csv("arquivo.csv")
   except ParsingError as e:
       print(f"Erro no parsing: {e.message}")
       print(f"Linha: {e.line_number}")
   except DataValidationError as e:
       print(f"Erro de validação: {e.validation_errors}")

**Logging e Diagnósticos:**

.. code-block:: python

   import logging
   from src.data import enable_debug_logging
   
   # Ativar logging detalhado
   enable_debug_logging()
   
   # Logs automáticos durante processamento
   logger = logging.getLogger('src.data')
   logger.info("Iniciando processamento de dados")

Performance e Otimizações
=========================

**Benchmarks Típicos:**

.. list-table::
   :widths: 30 20 25 25
   :header-rows: 1

   * - Operação
     - Tamanho do Arquivo
     - Tempo Médio
     - Memória Pico
   * - Parsing CSV
     - 10MB (10k linhas)
     - 0.5s
     - 50MB
   * - Parsing CSV
     - 100MB (100k linhas)  
     - 3.2s
     - 200MB
   * - Validação Completa
     - 10k linhas
     - 0.8s
     - 30MB
   * - Cache Write/Read
     - 10k linhas
     - 0.1s / 0.05s
     - 15MB

**Dicas de Performance:**

.. code-block:: python

   # Use chunked processing para arquivos grandes
   for chunk in parse_chunked("arquivo_grande.csv", chunk_size=10000):
       process_chunk(chunk)
   
   # Enable cache para análises repetitivas
   config = ParsingConfig(cache_enabled=True)
   
   # Use specific column selection
   data = parse_fueltech_csv("arquivo.csv", columns=['TIME', 'RPM', 'MAP'])
   
   # Optimize memory usage
   data = optimize_dtypes(data)  # Converte para tipos mais eficientes

Testes e Validação
==================

**Executar Testes:**

.. code-block:: bash

   # Testes unitários do módulo de dados
   pytest tests/unit/test_data/ -v
   
   # Testes de integração
   pytest tests/integration/test_data_integration.py -v
   
   # Testes de performance
   pytest tests/performance/test_data_performance.py -v

**Coverage Report:**

.. code-block:: bash

   # Gerar relatório de cobertura
   pytest --cov=src.data tests/ --cov-report=html
   
   # Visualizar no browser
   open htmlcov/index.html

Extensibilidade
===============

**Criando Validadores Customizados:**

.. code-block:: python

   from src.data.validators import BaseValidator
   import pandera as pa
   
   class CustomValidator(BaseValidator):
       def create_schema(self) -> pa.DataFrameSchema:
           return pa.DataFrameSchema({
               'CUSTOM_FIELD': pa.Column(
                   float,
                   checks=[
                       pa.Check.between(0, 1000),
                       pa.Check(lambda x: x.std() < 50, element_wise=False)
                   ]
               )
           })

**Adicionando Novos Formatos:**

.. code-block:: python

   from src.data.csv_parser import BaseParser
   
   class CustomFormatParser(BaseParser):
       def parse(self, filepath: str) -> pd.DataFrame:
           # Implementar parsing customizado
           return custom_parsing_logic(filepath)
   
   # Registrar novo parser
   register_parser("custom_format", CustomFormatParser)

.. note::
   Para mais detalhes sobre extensibilidade, consulte o :doc:`../../dev-guide/contributing`.

----

**Módulos Relacionados:**
   - :doc:`analysis` - Módulos de análise que utilizam estes dados
   - :doc:`ui` - Interface que exibe os dados processados
   - :doc:`integration` - Exportação e workflow dos dados