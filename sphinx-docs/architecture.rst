==================
Arquitetura do Sistema
==================

Esta seção descreve a arquitetura completa do FuelTune Analyzer, incluindo padrões de design, 
organização de código, fluxo de dados e decisões arquiteturais. É essencial para desenvolvedores 
que queiram contribuir ou estender o sistema.

.. note::
   **Público-alvo**: Desenvolvedores, arquitetos de software, contribuidores
   
   **Pré-requisitos**: Conhecimento em Python, Streamlit, pandas, padrões de design

🏗️ Visão Geral da Arquitetura
=============================

O FuelTune Analyzer segue uma arquitetura em camadas com separação clara de responsabilidades, 
baseada nos princípios de Clean Architecture e Domain-Driven Design.

.. mermaid::

   graph TB
       subgraph "Presentation Layer"
           UI[Streamlit UI]
           API[REST API]
           CLI[Command Line]
       end
       
       subgraph "Application Layer"
           APP[Application Services]
           WORK[Workflow Manager]
           CACHE[Cache Manager]
       end
       
       subgraph "Domain Layer"
           MODELS[Domain Models]
           SERVICES[Domain Services]
           ANALYSIS[Analysis Engine]
       end
       
       subgraph "Infrastructure Layer"
           DB[Database]
           FILES[File System]
           EXTERN[External APIs]
       end
       
       UI --> APP
       API --> APP
       CLI --> APP
       APP --> SERVICES
       WORK --> SERVICES
       SERVICES --> MODELS
       ANALYSIS --> MODELS
       SERVICES --> DB
       SERVICES --> FILES
       APP --> EXTERN

## Princípios Arquiteturais

**1. Separation of Concerns**
   Cada módulo tem uma responsabilidade específica e bem definida

**2. Dependency Inversion**
   Dependências apontam para abstrações, não implementações concretas

**3. Single Responsibility**
   Classes e módulos têm uma única razão para mudar

**4. Open/Closed Principle**
   Extensível para novos recursos, fechado para modificações

**5. Interface Segregation**
   Interfaces pequenas e específicas para cada contexto

📦 Organização de Módulos
=========================

Estrutura de Diretórios
-----------------------

.. code-block:: text

   src/
   ├── data/                    # 📊 Camada de Dados
   │   ├── __init__.py
   │   ├── models.py           # Modelos de domínio
   │   ├── csv_parser.py       # Parser de arquivos
   │   ├── validators.py       # Validação de dados
   │   ├── normalizer.py       # Normalização
   │   ├── cache.py           # Sistema de cache
   │   ├── database.py        # Persistência
   │   └── quality.py         # Qualidade de dados
   │
   ├── analysis/               # 🔬 Camada de Análise
   │   ├── __init__.py
   │   ├── analysis.py        # Factory de analisadores
   │   ├── performance.py     # Análise de performance
   │   ├── statistics.py      # Análises estatísticas
   │   ├── correlation.py     # Análise de correlação
   │   ├── anomaly.py         # Detecção de anomalias
   │   ├── predictive.py      # Análises preditivas
   │   ├── time_series.py     # Análises temporais
   │   ├── fuel_efficiency.py # Eficiência combustível
   │   ├── dynamics.py        # Análises dinâmicas
   │   └── reports.py         # Geração de relatórios
   │
   ├── ui/                     # 🖥️ Camada de Interface
   │   ├── __init__.py
   │   ├── components/        # Componentes reutilizáveis
   │   │   ├── __init__.py
   │   │   ├── chart_builder.py
   │   │   ├── metric_card.py
   │   │   ├── session_selector.py
   │   │   └── session_state_manager.py
   │   └── pages/             # Páginas da aplicação
   │       ├── __init__.py
   │       ├── dashboard.py
   │       ├── upload.py
   │       ├── analysis.py
   │       ├── performance.py
   │       ├── consumption.py
   │       ├── reports.py
   │       └── imu.py
   │
   ├── integration/            # 🔗 Camada de Integração
   │   ├── __init__.py
   │   ├── workflow.py        # Gerenciamento de workflow
   │   ├── pipeline.py        # Pipeline de processamento
   │   ├── export_import.py   # Import/Export
   │   ├── notifications.py   # Sistema de notificações
   │   ├── plugins.py         # Sistema de plugins
   │   ├── events.py          # Sistema de eventos
   │   ├── background.py      # Processamento background
   │   ├── clipboard.py       # Integração clipboard
   │   └── integration_manager.py # Gerenciador central
   │
   └── utils/                  # 🛠️ Utilitários
       ├── __init__.py
       ├── logger.py          # Sistema de logging
       └── logging_config.py  # Configuração de logs

Responsabilidades por Camada
----------------------------

**Data Layer** (src/data/)
   - Parsing e validação de arquivos CSV
   - Modelos de domínio (TelemetryData, VehicleProfile)
   - Normalização e limpeza de dados
   - Persistência e cache
   - Qualidade e integridade dos dados

**Analysis Layer** (src/analysis/)
   - Algoritmos de análise especializados
   - Factory pattern para criação de analisadores
   - Cálculos de performance e eficiência
   - Análises estatísticas e preditivas
   - Geração de relatórios

**UI Layer** (src/ui/)
   - Interface Streamlit
   - Componentes reutilizáveis
   - Páginas especializadas
   - Gerenciamento de estado da UI
   - Visualizações interativas

**Integration Layer** (src/integration/)
   - Workflows de processamento
   - Import/Export de dados
   - Sistema de plugins e eventos
   - Integrações externas
   - Processamento em background

🏛️ Padrões Arquiteturais
========================

Factory Pattern
---------------

Usado para criação de analisadores especializados:

.. code-block:: python

   # src/analysis/analysis.py
   class AnalyzerFactory:
       _analyzers = {
           'performance': PerformanceAnalyzer,
           'statistics': StatisticalAnalyzer,
           'correlation': CorrelationAnalyzer,
           'anomaly': AnomalyDetector,
           'predictive': PredictiveAnalyzer,
       }
       
       @classmethod
       def create_analyzer(cls, analyzer_type: str) -> BaseAnalyzer:
           """Criar analisador específico."""
           if analyzer_type not in cls._analyzers:
               raise ValueError(f"Tipo de analisador desconhecido: {analyzer_type}")
           
           return cls._analyzers[analyzer_type]()
       
       @classmethod
       def register_analyzer(cls, name: str, analyzer_class: type):
           """Registrar novo tipo de analisador."""
           cls._analyzers[name] = analyzer_class

Repository Pattern
------------------

Para abstração de persistência:

.. code-block:: python

   # src/data/database.py
   from abc import ABC, abstractmethod
   
   class SessionRepository(ABC):
       @abstractmethod
       def save_session(self, data: TelemetryData) -> str:
           pass
       
       @abstractmethod
       def load_session(self, session_id: str) -> TelemetryData:
           pass
       
       @abstractmethod
       def find_sessions(self, criteria: dict) -> List[SessionMetadata]:
           pass
   
   class SQLiteSessionRepository(SessionRepository):
       def __init__(self, db_path: str):
           self.db_path = db_path
       
       def save_session(self, data: TelemetryData) -> str:
           # Implementação específica SQLite
           pass

Observer Pattern
----------------

Para sistema de eventos e notificações:

.. code-block:: python

   # src/integration/events.py
   from typing import Dict, List, Callable
   
   class EventBus:
       def __init__(self):
           self._observers: Dict[str, List[Callable]] = {}
       
       def subscribe(self, event_type: str, callback: Callable):
           """Inscrever observador para tipo de evento."""
           if event_type not in self._observers:
               self._observers[event_type] = []
           self._observers[event_type].append(callback)
       
       def emit(self, event_type: str, data: dict):
           """Emitir evento para todos os observadores."""
           if event_type in self._observers:
               for callback in self._observers[event_type]:
                   callback(data)

Strategy Pattern
----------------

Para diferentes estratégias de análise e exportação:

.. code-block:: python

   # src/integration/export_import.py
   from abc import ABC, abstractmethod
   
   class ExportStrategy(ABC):
       @abstractmethod
       def export(self, data: TelemetryData, filepath: str):
           pass
   
   class ExcelExportStrategy(ExportStrategy):
       def export(self, data: TelemetryData, filepath: str):
           # Exportação para Excel
           pass
   
   class PDFExportStrategy(ExportStrategy):
       def export(self, data: TelemetryData, filepath: str):
           # Exportação para PDF
           pass
   
   class ExportManager:
       def __init__(self):
           self.strategies = {
               'excel': ExcelExportStrategy(),
               'pdf': PDFExportStrategy(),
               'csv': CSVExportStrategy()
           }
       
       def export(self, format_type: str, data: TelemetryData, filepath: str):
           strategy = self.strategies.get(format_type)
           if not strategy:
               raise ValueError(f"Formato não suportado: {format_type}")
           return strategy.export(data, filepath)

🔄 Fluxo de Dados
================

Pipeline Principal
------------------

.. mermaid::

   flowchart TD
       UPLOAD[📁 Upload CSV] --> PARSE[🔍 Parse & Validate]
       PARSE --> NORMALIZE[⚙️ Normalize Data]
       NORMALIZE --> CACHE[💾 Cache Data]
       CACHE --> ANALYZE[🔬 Run Analysis]
       ANALYZE --> VISUALIZE[📊 Generate Charts]
       VISUALIZE --> EXPORT[📄 Export Results]
       
       PARSE -.-> ERRORS[❌ Handle Errors]
       NORMALIZE -.-> CLEAN[🧹 Data Cleaning]
       ANALYZE -.-> BACKGROUND[⚡ Background Tasks]

Fluxo Detalhado de Processamento
--------------------------------

.. code-block:: python

   # Fluxo típico de processamento
   def process_telemetry_file(filepath: str) -> ProcessingResult:
       """Pipeline completo de processamento."""
       
       # 1. Parsing e validação inicial
       parser = CSVParserFactory.create_parser(filepath)
       raw_data = parser.parse(filepath)
       
       # 2. Validação de dados
       validator = DataValidator()
       validation_result = validator.validate(raw_data)
       
       if not validation_result.is_valid:
           return ProcessingResult.error(validation_result.errors)
       
       # 3. Normalização e limpeza
       normalizer = DataNormalizer()
       clean_data = normalizer.normalize(raw_data)
       
       # 4. Criação do modelo de domínio
       telemetry_data = TelemetryData.from_dataframe(clean_data)
       
       # 5. Cache dos dados processados
       cache_manager = CacheManager()
       data_hash = cache_manager.store(telemetry_data)
       
       # 6. Análises automáticas
       analysis_results = {}
       for analysis_type in ['performance', 'statistics', 'anomaly']:
           analyzer = AnalyzerFactory.create_analyzer(analysis_type)
           analysis_results[analysis_type] = analyzer.analyze(telemetry_data)
       
       # 7. Notificação de conclusão
       event_bus = EventBus()
       event_bus.emit('processing_completed', {
           'data_hash': data_hash,
           'analysis_results': analysis_results
       })
       
       return ProcessingResult.success(telemetry_data, analysis_results)

Estado da Aplicação
-------------------

Gerenciamento de estado usando Streamlit Session State:

.. code-block:: python

   # src/ui/components/session_state_manager.py
   import streamlit as st
   from typing import Optional, Any
   
   class SessionStateManager:
       """Gerenciador centralizado do estado da sessão."""
       
       @staticmethod
       def get_current_data() -> Optional[TelemetryData]:
           """Obter dados atuais da sessão."""
           return st.session_state.get('current_telemetry_data')
       
       @staticmethod
       def set_current_data(data: TelemetryData):
           """Definir dados atuais da sessão."""
           st.session_state['current_telemetry_data'] = data
           st.session_state['data_loaded'] = True
           st.session_state['last_update'] = datetime.now()
       
       @staticmethod
       def get_analysis_results(analysis_type: str) -> Optional[dict]:
           """Obter resultados de análise específica."""
           results = st.session_state.get('analysis_results', {})
           return results.get(analysis_type)
       
       @staticmethod
       def set_analysis_results(analysis_type: str, results: dict):
           """Armazenar resultados de análise."""
           if 'analysis_results' not in st.session_state:
               st.session_state['analysis_results'] = {}
           st.session_state['analysis_results'][analysis_type] = results

🎨 Padrões de Design de Interface
================================

Component-Based Architecture
----------------------------

Interface construída com componentes reutilizáveis:

.. code-block:: python

   # src/ui/components/metric_card.py
   import streamlit as st
   from typing import Optional
   
   class MetricCard:
       """Componente reutilizável para exibir métricas."""
       
       @staticmethod
       def render(
           title: str,
           value: str,
           delta: Optional[str] = None,
           help_text: Optional[str] = None
       ):
           """Renderizar card de métrica."""
           col1, col2 = st.columns([3, 1])
           
           with col1:
               st.metric(
                   label=title,
                   value=value,
                   delta=delta,
                   help=help_text
               )
           
           with col2:
               if help_text:
                   st.info(help_text)

Page Pattern
------------

Cada página é uma classe com responsabilidades específicas:

.. code-block:: python

   # src/ui/pages/dashboard.py
   import streamlit as st
   from abc import ABC, abstractmethod
   
   class BasePage(ABC):
       """Classe base para todas as páginas."""
       
       def __init__(self, title: str):
           self.title = title
       
       def render(self):
           """Renderizar página completa."""
           st.title(self.title)
           self.render_sidebar()
           self.render_content()
       
       @abstractmethod
       def render_content(self):
           """Renderizar conteúdo específico da página."""
           pass
       
       def render_sidebar(self):
           """Renderizar sidebar (pode ser sobrescrito)."""
           pass
   
   class DashboardPage(BasePage):
       def __init__(self):
           super().__init__("📊 Dashboard")
       
       def render_content(self):
           data = SessionStateManager.get_current_data()
           if not data:
               st.warning("Nenhum dado carregado. Faça upload de um arquivo.")
               return
           
           self.render_metrics(data)
           self.render_charts(data)
       
       def render_metrics(self, data: TelemetryData):
           # Renderizar métricas principais
           pass
       
       def render_charts(self, data: TelemetryData):
           # Renderizar gráficos
           pass

🔧 Sistema de Configuração
==========================

Configuração Hierárquica
------------------------

.. code-block:: python

   # config.py
   from dataclasses import dataclass
   from typing import Optional
   import os
   
   @dataclass
   class DatabaseConfig:
       url: str = "sqlite:///fueltune.db"
       echo: bool = False
       pool_size: int = 5
   
   @dataclass
   class CacheConfig:
       enabled: bool = True
       ttl: int = 3600  # 1 hora
       max_size_mb: int = 500
   
   @dataclass
   class AnalysisConfig:
       auto_analysis: bool = True
       default_types: list = None
       parallel_processing: bool = True
       max_workers: int = 4
       
       def __post_init__(self):
           if self.default_types is None:
               self.default_types = ['performance', 'statistics', 'anomaly']
   
   @dataclass
   class AppConfig:
       debug: bool = False
       log_level: str = "INFO"
       database: DatabaseConfig = DatabaseConfig()
       cache: CacheConfig = CacheConfig()
       analysis: AnalysisConfig = AnalysisConfig()
       
       @classmethod
       def from_env(cls) -> 'AppConfig':
           """Criar configuração a partir de variáveis de ambiente."""
           return cls(
               debug=os.getenv('DEBUG', 'false').lower() == 'true',
               log_level=os.getenv('LOG_LEVEL', 'INFO'),
               database=DatabaseConfig(
                   url=os.getenv('DATABASE_URL', 'sqlite:///fueltune.db')
               ),
               cache=CacheConfig(
                   enabled=os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
                   ttl=int(os.getenv('CACHE_TTL', '3600'))
               )
           )

Injeção de Dependências
-----------------------

.. code-block:: python

   # src/utils/container.py
   from typing import Dict, Any, TypeVar, Type
   
   T = TypeVar('T')
   
   class Container:
       """Container de injeção de dependências."""
       
       def __init__(self):
           self._services: Dict[str, Any] = {}
           self._singletons: Dict[str, Any] = {}
       
       def register(self, interface: Type[T], implementation: Type[T], singleton: bool = True):
           """Registrar implementação para interface."""
           key = interface.__name__
           self._services[key] = implementation
           if singleton and key not in self._singletons:
               self._singletons[key] = implementation()
       
       def resolve(self, interface: Type[T]) -> T:
           """Resolver implementação para interface."""
           key = interface.__name__
           
           if key in self._singletons:
               return self._singletons[key]
           
           if key in self._services:
               return self._services[key]()
           
           raise ValueError(f"Serviço não registrado: {key}")

📊 Monitoramento e Observabilidade
==================================

Sistema de Logging
------------------

.. code-block:: python

   # src/utils/logging_config.py
   import logging
   import sys
   from pathlib import Path
   
   def setup_logging(log_level: str = "INFO", log_dir: Path = Path("logs")):
       """Configurar sistema de logging."""
       
       # Criar diretório de logs
       log_dir.mkdir(exist_ok=True)
       
       # Configurar formatters
       formatter = logging.Formatter(
           '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
       )
       
       # Logger principal
       logger = logging.getLogger('fueltune')
       logger.setLevel(getattr(logging, log_level.upper()))
       
       # Handler para arquivo
       file_handler = logging.FileHandler(log_dir / 'fueltune.log')
       file_handler.setFormatter(formatter)
       logger.addHandler(file_handler)
       
       # Handler para console
       console_handler = logging.StreamHandler(sys.stdout)
       console_handler.setFormatter(formatter)
       logger.addHandler(console_handler)
       
       # Logger específico para erros
       error_logger = logging.getLogger('fueltune.errors')
       error_handler = logging.FileHandler(log_dir / 'errors.log')
       error_handler.setFormatter(formatter)
       error_handler.setLevel(logging.ERROR)
       error_logger.addHandler(error_handler)

Métricas de Performance
----------------------

.. code-block:: python

   # src/utils/metrics.py
   import time
   import functools
   from typing import Dict, Any
   
   class PerformanceMetrics:
       """Coletor de métricas de performance."""
       
       def __init__(self):
           self.metrics: Dict[str, Any] = {}
       
       def time_function(self, func_name: str):
           """Decorator para medir tempo de execução."""
           def decorator(func):
               @functools.wraps(func)
               def wrapper(*args, **kwargs):
                   start_time = time.time()
                   result = func(*args, **kwargs)
                   end_time = time.time()
                   
                   execution_time = end_time - start_time
                   self.record_metric(f"{func_name}_execution_time", execution_time)
                   
                   return result
               return wrapper
           return decorator
       
       def record_metric(self, name: str, value: Any):
           """Registrar métrica."""
           if name not in self.metrics:
               self.metrics[name] = []
           self.metrics[name].append({
               'value': value,
               'timestamp': time.time()
           })

🔐 Segurança e Validação
=======================

Validação de Entrada
--------------------

.. code-block:: python

   # src/data/validators.py
   import pandera as pa
   from pandera import DataFrameSchema, Column, Check
   
   class SecurityValidator:
       """Validador de segurança para entrada de dados."""
       
       @staticmethod
       def validate_file_upload(file_content: bytes, max_size_mb: int = 100) -> bool:
           """Validar arquivo de upload."""
           
           # Verificar tamanho
           if len(file_content) > max_size_mb * 1024 * 1024:
               raise ValueError(f"Arquivo muito grande (max {max_size_mb}MB)")
           
           # Verificar conteúdo malicioso
           suspicious_patterns = [b'<script', b'javascript:', b'<?php']
           for pattern in suspicious_patterns:
               if pattern in file_content.lower():
                   raise ValueError("Conteúdo suspeito detectado")
           
           return True
       
       @staticmethod
       def sanitize_filename(filename: str) -> str:
           """Sanitizar nome do arquivo."""
           import re
           # Remove caracteres perigosos
           safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
           return safe_filename[:100]  # Limitar tamanho

Controle de Acesso
------------------

.. code-block:: python

   # src/utils/auth.py
   from enum import Enum
   from typing import Set
   
   class Permission(Enum):
       READ_DATA = "read_data"
       WRITE_DATA = "write_data"
       EXPORT_DATA = "export_data"
       ADMIN_ACCESS = "admin_access"
   
   class User:
       def __init__(self, username: str, permissions: Set[Permission]):
           self.username = username
           self.permissions = permissions
       
       def has_permission(self, permission: Permission) -> bool:
           return permission in self.permissions

📈 Escalabilidade e Performance
==============================

Processamento Paralelo
----------------------

.. code-block:: python

   # src/analysis/parallel.py
   from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
   from typing import List, Callable, Any
   
   class ParallelProcessor:
       """Processador paralelo para análises."""
       
       def __init__(self, max_workers: int = 4):
           self.max_workers = max_workers
       
       def process_parallel(
           self, 
           tasks: List[Callable],
           use_processes: bool = False
       ) -> List[Any]:
           """Processar tarefas em paralelo."""
           
           executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
           
           with executor_class(max_workers=self.max_workers) as executor:
               futures = [executor.submit(task) for task in tasks]
               results = [future.result() for future in futures]
           
           return results

Cache Distribuído
-----------------

.. code-block:: python

   # src/data/cache.py
   import redis
   import pickle
   from typing import Optional, Any
   
   class DistributedCache:
       """Cache distribuído usando Redis."""
       
       def __init__(self, redis_url: str = "redis://localhost:6379"):
           self.client = redis.from_url(redis_url)
       
       def get(self, key: str) -> Optional[Any]:
           """Obter valor do cache."""
           data = self.client.get(key)
           if data:
               return pickle.loads(data)
           return None
       
       def set(self, key: str, value: Any, ttl: int = 3600):
           """Armazenar valor no cache."""
           data = pickle.dumps(value)
           self.client.setex(key, ttl, data)

🧪 Testabilidade
===============

Arquitetura Orientada a Testes
------------------------------

.. code-block:: python

   # tests/unit/test_analysis.py
   import pytest
   from unittest.mock import Mock, patch
   from src.analysis.performance import PerformanceAnalyzer
   
   class TestPerformanceAnalyzer:
       """Testes para analisador de performance."""
       
       def setup_method(self):
           """Configurar cada teste."""
           self.analyzer = PerformanceAnalyzer()
           self.mock_data = self.create_mock_telemetry_data()
       
       def create_mock_telemetry_data(self):
           """Criar dados mock para testes."""
           # Implementar criação de dados de teste
           pass
       
       def test_calculate_max_power(self):
           """Testar cálculo de potência máxima."""
           result = self.analyzer.calculate_max_power(self.mock_data)
           assert result > 0
           assert isinstance(result, float)
       
       @patch('src.data.cache.CacheManager')
       def test_analysis_with_cache(self, mock_cache):
           """Testar análise com cache mockado."""
           mock_cache.return_value.get.return_value = None
           result = self.analyzer.analyze(self.mock_data)
           assert result is not None
           mock_cache.return_value.set.assert_called_once()

Integration Testing
-------------------

.. code-block:: python

   # tests/integration/test_full_pipeline.py
   import pytest
   from pathlib import Path
   from src.data.csv_parser import parse_fueltech_csv
   from src.analysis import AnalyzerFactory
   
   class TestFullPipeline:
       """Testes de integração do pipeline completo."""
       
       def test_complete_workflow(self):
           """Testar workflow completo do upload à análise."""
           
           # Carregar dados de teste
           test_file = Path("tests/fixtures/sample_data.csv")
           data = parse_fueltech_csv(str(test_file))
           
           # Executar análises
           analyzer = AnalyzerFactory.create_analyzer("performance")
           results = analyzer.analyze(data)
           
           # Verificar resultados
           assert 'max_power' in results
           assert results['max_power'] > 0

📚 Documentação da Arquitetura
==============================

ADRs (Architecture Decision Records)
------------------------------------

Decisões arquiteturais importantes são documentadas como ADRs:

.. code-block:: markdown

   # ADR-001: Escolha do Streamlit como Framework de UI
   
   ## Status
   Aceito
   
   ## Contexto
   Necessitamos de um framework para criar interface web interativa
   para análise de dados, com foco em prototipagem rápida.
   
   ## Decisão
   Usar Streamlit como framework principal de UI.
   
   ## Consequências
   - **Positivas**: Desenvolvimento rápido, integração com pandas/plotly
   - **Negativas**: Limitações de customização, single-threaded

Diagramas C4
------------

Documentação visual usando diagramas C4:

.. mermaid::

   C4Context
       title System Context Diagram for FuelTune Analyzer
       
       Person(user, "Engine Tuner", "Professional who analyzes telemetry data")
       System(fueltune, "FuelTune Analyzer", "Analyzes FuelTech telemetry data")
       System_Ext(fueltech, "FuelTech ECU", "Generates telemetry CSV files")
       System_Ext(dyno, "Dynamometer", "Provides additional performance data")
       
       Rel(user, fueltune, "Uses")
       Rel(fueltune, fueltech, "Imports data from")
       Rel(fueltune, dyno, "Correlates with")

🔄 Evolução da Arquitetura
==========================

Roadmap Arquitetural
--------------------

**Versão 2.1 (Q1 2025)**
   - Microservices para análises pesadas
   - API REST completa
   - Cache distribuído

**Versão 2.2 (Q2 2025)**
   - Sistema de plugins extensível
   - Processamento real-time
   - Machine Learning pipeline

**Versão 3.0 (Q4 2025)**
   - Arquitetura cloud-native
   - Multi-tenancy
   - Auto-scaling

Refatorações Planejadas
----------------------

1. **Extração de Domain Models**
   - Separar lógica de negócio dos DTOs
   - Implementar rich domain models

2. **Event-Driven Architecture**
   - Migrar para arquitetura baseada em eventos
   - Implementar CQRS para queries complexas

3. **Modularização**
   - Extrair análises para módulos independentes
   - Plugin system para extensões customizadas

----

Esta arquitetura fornece uma base sólida e extensível para o FuelTune Analyzer, 
balanceando simplicidade, performance e facilidade de manutenção. 

Para contribuir com melhorias arquiteturais, consulte o :doc:`contributing`.