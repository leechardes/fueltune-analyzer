=================
Referência da API
=================

Esta seção contém a documentação completa da API do FuelTune Analyzer, incluindo todos os módulos, 
classes, funções e métodos disponíveis para desenvolvedores.

.. note::
   A documentação da API é gerada automaticamente a partir dos docstrings do código fonte 
   usando Sphinx AutoAPI. Todas as funções e classes públicas estão documentadas com 
   exemplos de uso, parâmetros e valores de retorno.

Visão Geral dos Módulos
=======================

O FuelTune Analyzer está organizado em quatro módulos principais:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Módulo
     - Descrição
   * - **data**
     - Processamento, validação e modelagem de dados FuelTech
   * - **analysis**
     - Módulos especializados de análise estatística e performance
   * - **ui**
     - Componentes de interface Streamlit e páginas
   * - **integration**
     - Sistema de workflow, exportação e plugins
   * - **utils**
     - Utilitários de logging e configuração

🗂️ Estrutura dos Módulos
========================

.. mermaid::

   graph TD
       API[API FuelTune] --> DATA[data]
       API --> ANALYSIS[analysis]
       API --> UI[ui]
       API --> INTEGRATION[integration]
       API --> UTILS[utils]
       
       DATA --> PARSER[csv_parser]
       DATA --> MODELS[models]
       DATA --> VALIDATORS[validators]
       DATA --> CACHE[cache]
       DATA --> DB[database]
       
       ANALYSIS --> PERF[performance]
       ANALYSIS --> STATS[statistics]
       ANALYSIS --> TIMESERIES[time_series]
       ANALYSIS --> CORR[correlation]
       ANALYSIS --> ANOMALY[anomaly]
       
       UI --> COMPONENTS[components]
       UI --> PAGES[pages]
       
       INTEGRATION --> EXPORT[export_import]
       INTEGRATION --> WORKFLOW[workflow]
       INTEGRATION --> PIPELINE[pipeline]

📋 Referência Completa por Módulo
=================================

.. toctree::
   :maxdepth: 3
   :caption: Módulos de Dados
   
   modules/data
   modules/models
   modules/validators

.. toctree::
   :maxdepth: 3
   :caption: Módulos de Análise
   
   modules/analysis
   modules/statistics
   modules/performance

.. toctree::
   :maxdepth: 3
   :caption: Interface do Usuário
   
   modules/ui
   modules/components
   modules/pages

.. toctree::
   :maxdepth: 3
   :caption: Integração e Workflow
   
   modules/integration
   modules/workflow
   modules/export

.. toctree::
   :maxdepth: 2
   :caption: Utilitários
   
   modules/utils

🔍 Busca Rápida
===============

**Classes Principais:**

* :py:class:`src.data.models.TelemetryData` - Modelo principal de dados de telemetria
* :py:class:`src.data.csv_parser.CSVParser` - Parser de arquivos CSV FuelTech
* :py:class:`src.analysis.performance.PerformanceAnalyzer` - Análise de performance
* :py:class:`src.analysis.statistics.StatisticalAnalyzer` - Análises estatísticas
* :py:class:`src.integration.workflow.WorkflowManager` - Gerenciamento de workflow

**Funções Principais:**

* :py:func:`src.data.csv_parser.parse_fueltech_csv` - Função principal de parsing
* :py:func:`src.analysis.performance.calculate_power` - Cálculo de potência
* :py:func:`src.analysis.statistics.descriptive_stats` - Estatísticas descritivas
* :py:func:`src.integration.export_import.export_to_excel` - Exportação para Excel

📖 Convenções de Documentação
=============================

**Docstring Format**
   Utilizamos o formato Google Docstring para todas as funções e classes:

   .. code-block:: python

      def example_function(param1: str, param2: int = 10) -> bool:
          """Função de exemplo para demonstrar formato de docstring.
          
          Esta função demonstra como documentamos todas as funções da API
          seguindo o padrão Google Docstring.
          
          Args:
              param1: Descrição do primeiro parâmetro
              param2: Descrição do segundo parâmetro com valor padrão
              
          Returns:
              True se a operação foi bem-sucedida, False caso contrário
              
          Raises:
              ValueError: Se param1 for uma string vazia
              TypeError: Se param2 não for um inteiro
              
          Examples:
              >>> example_function("teste", 20)
              True
              
              >>> example_function("", 5)
              ValueError: param1 não pode ser vazio
          """
          if not param1:
              raise ValueError("param1 não pode ser vazio")
          return True

**Type Hints**
   Todas as funções incluem type hints completos para melhor IDE support:

   .. code-block:: python

      from typing import List, Dict, Optional, Union
      import pandas as pd
      
      def process_data(
          data: pd.DataFrame,
          columns: List[str],
          config: Optional[Dict[str, Union[str, int]]] = None
      ) -> pd.DataFrame:
          """Processa dados com type hints completos."""
          pass

**Exemplos de Uso**
   Cada função inclui exemplos práticos de uso:

   .. code-block:: python

      # Exemplo básico
      from src.data.csv_parser import parse_fueltech_csv
      
      # Carregar dados FuelTech
      data = parse_fueltech_csv("caminho/para/arquivo.csv")
      
      # Exemplo com configurações
      data = parse_fueltech_csv(
          "arquivo.csv",
          encoding="latin-1",
          skip_rows=1,
          validate=True
      )

🎯 Padrões de Design
===================

**Factory Pattern**
   Usado para criação de analisadores especializados:

   .. code-block:: python

      from src.analysis import AnalyzerFactory
      
      # Criar analisador de performance
      analyzer = AnalyzerFactory.create_analyzer("performance")
      
      # Executar análise
      results = analyzer.analyze(data)

**Strategy Pattern**
   Implementado para diferentes tipos de exportação:

   .. code-block:: python

      from src.integration.export_import import ExportStrategy
      
      # Estratégia Excel
      excel_exporter = ExportStrategy.create("excel")
      excel_exporter.export(data, "output.xlsx")
      
      # Estratégia CSV
      csv_exporter = ExportStrategy.create("csv")
      csv_exporter.export(data, "output.csv")

**Observer Pattern**
   Usado para notificações de workflow:

   .. code-block:: python

      from src.integration.workflow import WorkflowManager
      
      workflow = WorkflowManager()
      
      # Registrar observador
      workflow.register_observer("data_loaded", callback_function)
      
      # Executar workflow
      workflow.execute_pipeline(data)

⚠️ Notas Importantes
===================

**Compatibilidade de Versão**
   - Python 3.11+ obrigatório
   - Streamlit 1.29+ recomendado
   - Pandas 2.0+ para melhor performance

**Performance**
   - Processamento otimizado para arquivos grandes (10k+ linhas)
   - Uso de chunked processing para economia de memória
   - Cache inteligente para análises repetitivas

**Segurança**
   - Validação rigorosa de entrada de dados
   - Sanitização de parâmetros SQL
   - Verificação de limites de segurança FuelTech

**Thread Safety**
   - Módulos de análise são thread-safe
   - Cache implementa locks para acesso concorrente
   - UI components são single-threaded (Streamlit)

📚 Recursos Adicionais
=====================

**Código Fonte**
   - `GitHub Repository <https://github.com/fueltune/analyzer-streamlit>`_
   - `Issue Tracker <https://github.com/fueltune/analyzer-streamlit/issues>`_
   - `Pull Requests <https://github.com/fueltune/analyzer-streamlit/pulls>`_

**Comunidade**
   - `Discord Server <https://discord.gg/fueltune>`_
   - `Stack Overflow Tag <https://stackoverflow.com/questions/tagged/fueltune>`_
   - `Email Support <mailto:support@fueltune.com>`_

.. note::
   Esta documentação da API é atualizada automaticamente a cada release. 
   Para a versão mais recente, visite sempre a documentação online.

----

**Última atualização:** |today|