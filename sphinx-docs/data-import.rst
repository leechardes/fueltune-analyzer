=====================================
Tutorial: Importação de Dados FuelTech
=====================================

Este tutorial ensina como importar, validar e preparar dados FuelTech para análise. 
Você aprenderá desde o básico até técnicas avançadas para diferentes cenários.

.. note::
   **Duração estimada**: 15-20 minutos
   
   **Pré-requisitos**: 
   - FuelTune Analyzer instalado
   - Arquivo CSV FuelTech (ou arquivo de exemplo)

🎯 Objetivos do Tutorial
========================

Ao final deste tutorial, você saberá:

- ✅ Como preparar arquivos FuelTech para importação
- ✅ Diferentes métodos de importação (UI, API, programático)
- ✅ Como validar e corrigir problemas nos dados
- ✅ Otimizar importação de arquivos grandes
- ✅ Trabalhar com múltiplos arquivos e sessões

📁 Preparação dos Arquivos
==========================

Tipos de Arquivo Suportados
----------------------------

.. list-table::
   :widths: 20 30 50
   :header-rows: 1

   * - Formato
     - Extensão
     - Observações
   * - **CSV FuelTech**
     - `.csv`
     - Formato padrão (recomendado)
   * - **Excel FuelTech**
     - `.xlsx`, `.xls`
     - Deve ter dados na primeira aba
   * - **CSV Genérico**
     - `.csv`
     - Headers mapeados manualmente
   * - **ZIP/RAR**
     - `.zip`, `.rar`
     - Múltiplos arquivos compactados

Estrutura Esperada do CSV
--------------------------

**Headers Obrigatórios (português):**

.. code-block:: text

   TIME,RPM,MAP,LAMBDA,ENGINE_TEMP,THROTTLE_POS
   0.000,1000,50.2,0.85,85.5,15.2
   0.100,1050,51.8,0.87,85.6,16.8
   ...

**Headers Alternativos (inglês):**

.. code-block:: text

   Time,Engine_Speed,Manifold_Pressure,Lambda,Engine_Temperature,Throttle_Position
   0.000,1000,50.2,0.85,85.5,15.2
   ...

.. tip::
   **Verificação rápida**: Abra seu CSV em um editor de texto. 
   A primeira linha deve conter os nomes dos parâmetros separados por vírgula.

Verificação de Integridade
---------------------------

Antes de importar, verifique:

.. code-block:: bash

   # Contar linhas (Linux/macOS)
   wc -l arquivo.csv
   
   # Verificar encoding
   file -i arquivo.csv
   
   # Ver primeiras linhas
   head -5 arquivo.csv

**Problemas Comuns:**

- ❌ Arquivo vazio ou só com headers
- ❌ Encoding incorreto (deve ser UTF-8 ou Latin-1)
- ❌ Separador diferente de vírgula
- ❌ Valores com vírgula decimal (deve ser ponto)

🔧 Método 1: Importação via Interface
=====================================

Importação Básica
------------------

1. **Abra o FuelTune Analyzer**:

   .. code-block:: bash
   
      streamlit run app.py

2. **Acesse a página de Upload**:
   - Na sidebar esquerda → **📁 Upload de Dados**

3. **Selecione o arquivo**:
   - Arraste o arquivo CSV para a área de upload
   - Ou clique em "Browse files" e selecione

4. **Configure as opções**:
   
   .. list-table::
      :widths: 30 70
      :header-rows: 1

      * - Opção
        - Recomendação
      * - **Encoding**
        - Auto-detect (padrão) ou Latin-1 para FuelTech BR
      * - **Decimal Separator**
        - Ponto (.) - padrão internacional
      * - **Skip Rows**
        - 0 (padrão) ou 1 se houver linha extra
      * - **Validar Dados**
        - ✅ Sempre habilitado (recomendado)

5. **Clique em "Processar Arquivo"**

.. mermaid::

   flowchart TD
       START[Selecionar Arquivo] --> UPLOAD[Upload]
       UPLOAD --> DETECT[Auto-detecção de Formato]
       DETECT --> VALIDATE[Validação]
       VALIDATE --> SUCCESS[✅ Sucesso]
       VALIDATE --> ERROR[❌ Erro]
       ERROR --> FIX[Corrigir Problemas]
       FIX --> UPLOAD

Tratamento de Erros
-------------------

**Erro: "Formato não reconhecido"**

.. code-block:: text

   ❌ PROBLEMA: Headers não foram reconhecidos
   
   ✅ SOLUÇÃO:
   1. Verificar se primeira linha tem nomes das colunas
   2. Tentar encoding "Latin-1"
   3. Verificar separador (vírgula vs ponto-e-vírgula)

**Erro: "Dados insuficientes"**

.. code-block:: text

   ❌ PROBLEMA: Arquivo muito pequeno ou sem dados válidos
   
   ✅ SOLUÇÃO:
   1. Mínimo 50 linhas de dados necessárias
   2. Verificar se colunas TIME, RPM, MAP existem
   3. Conferir se dados não estão todos zerados

**Erro: "Validação falhou"**

.. code-block:: text

   ❌ PROBLEMA: Valores fora dos limites esperados
   
   ✅ SOLUÇÃO:
   1. Revisar relatório de validação
   2. Decidir se aceitar com avisos
   3. Limpar dados manualmente se necessário

Importação com Configurações Avançadas
---------------------------------------

.. code-block:: python

   # Configuração para importação avançada
   import_settings = {
       'encoding': 'latin-1',
       'decimal_separator': '.',
       'thousands_separator': '',
       'skip_rows': 0,
       'max_rows': None,  # Importar tudo
       'columns': None,   # Todas as colunas
       'validate': True,
       'clean_data': True,
       'interpolate_missing': True,
       'remove_outliers': False,
       'chunk_size': 10000
   }

📊 Método 2: Importação Programática
====================================

Importação Básica via Python
-----------------------------

.. code-block:: python

   from src.data.csv_parser import parse_fueltech_csv
   from src.data.validators import validate_telemetry_data
   
   # Importação simples
   data = parse_fueltech_csv("caminho/para/arquivo.csv")
   
   # Verificar resultado
   print(f"Dados carregados: {len(data)} linhas")
   print(f"Colunas: {list(data.columns)}")
   print(f"Período: {data['TIME'].min():.1f}s - {data['TIME'].max():.1f}s")

Importação com Validação
------------------------

.. code-block:: python

   from src.data.csv_parser import CSVParser
   from src.data.validators import FuelTechValidator
   
   # Parser personalizado
   parser = CSVParser(
       encoding='latin-1',
       validate_on_load=True,
       skip_malformed_lines=True,
       interpolate_missing=True
   )
   
   try:
       # Carregar e validar
       data = parser.parse("arquivo.csv")
       
       # Validação adicional
       validator = FuelTechValidator()
       is_valid, errors = validator.validate(data)
       
       if is_valid:
           print("✅ Dados válidos!")
       else:
           print("⚠️ Problemas encontrados:")
           for error in errors:
               print(f"  - {error}")
               
   except Exception as e:
       print(f"❌ Erro na importação: {e}")

Importação de Arquivos Grandes
-------------------------------

.. code-block:: python

   from src.data.csv_parser import parse_chunked
   from src.data.cache import DataCache
   
   # Processamento chunked para arquivos >100MB
   cache = DataCache()
   processed_chunks = []
   
   for chunk_num, chunk in enumerate(parse_chunked("arquivo_grande.csv", chunk_size=5000)):
       print(f"Processando chunk {chunk_num + 1}...")
       
       # Processar chunk
       processed_chunk = process_data_chunk(chunk)
       processed_chunks.append(processed_chunk)
       
       # Cache intermediário
       cache.set(f"chunk_{chunk_num}", chunk.to_dict())
   
   # Concatenar todos os chunks
   complete_data = pd.concat(processed_chunks, ignore_index=True)
   print(f"✅ Arquivo completo: {len(complete_data)} linhas")

🗂️ Método 3: Importação de Múltiplos Arquivos
==============================================

Importação em Lote
-------------------

.. code-block:: python

   from pathlib import Path
   from src.data.batch_importer import BatchImporter
   
   # Configurar importador em lote
   batch_importer = BatchImporter(
       source_directory="data/raw_files/",
       output_directory="data/processed/",
       file_pattern="*.csv",
       parallel_processing=True,
       max_workers=4
   )
   
   # Executar importação
   results = batch_importer.process_all()
   
   # Relatório de resultados
   print(f"Arquivos processados: {results.success_count}")
   print(f"Arquivos com erro: {results.error_count}")
   
   for error in results.errors:
       print(f"❌ {error.filename}: {error.message}")

Comparação de Sessões
---------------------

.. code-block:: python

   from src.data.session_manager import SessionManager
   
   # Gerenciador de sessões
   session_mgr = SessionManager()
   
   # Importar múltiplas sessões
   sessions = {}
   files = ["sessao1.csv", "sessao2.csv", "sessao3.csv"]
   
   for file in files:
       session_name = Path(file).stem
       data = parse_fueltech_csv(file)
       
       # Adicionar metadados
       metadata = {
           'vehicle': 'Civic Si',
           'date': '2024-09-03',
           'track': 'Interlagos',
           'driver': 'Piloto A'
       }
       
       session_id = session_mgr.create_session(
           name=session_name,
           data=data,
           metadata=metadata
       )
       
       sessions[session_name] = session_id
   
   # Listar sessões criadas
   for name, session_id in sessions.items():
       session = session_mgr.get_session(session_id)
       print(f"📊 {name}: {len(session.data)} pontos")

🔍 Validação e Limpeza de Dados
===============================

Validação Automática
---------------------

.. code-block:: python

   from src.data.validators import comprehensive_validation
   from src.data.quality import DataQualityAnalyzer
   
   # Validação completa
   validation_report = comprehensive_validation(data)
   
   print("📋 RELATÓRIO DE VALIDAÇÃO")
   print(f"Status geral: {'✅ PASS' if validation_report.passed else '❌ FAIL'}")
   print(f"Completude: {validation_report.completeness:.1%}")
   print(f"Consistência: {validation_report.consistency:.1%}")
   
   # Detalhes por coluna
   for column, status in validation_report.column_status.items():
       icon = "✅" if status.valid else "⚠️"
       print(f"{icon} {column}: {status.message}")
   
   # Qualidade dos dados
   quality_analyzer = DataQualityAnalyzer()
   quality_report = quality_analyzer.analyze(data)
   
   if quality_report.outliers_count > 0:
       print(f"⚠️ {quality_report.outliers_count} outliers detectados")
       print("Colunas afetadas:", quality_report.outlier_columns)

Limpeza Automática
-------------------

.. code-block:: python

   from src.data.cleaning import DataCleaner
   
   # Limpador automático
   cleaner = DataCleaner(
       remove_duplicates=True,
       interpolate_missing=True,
       remove_outliers=True,
       smooth_noise=False,
       outlier_method='z_score',
       outlier_threshold=3.0
   )
   
   # Dados originais
   print(f"Dados originais: {len(data)} linhas")
   
   # Aplicar limpeza
   cleaned_data = cleaner.clean(data)
   
   # Relatório de limpeza
   cleaning_report = cleaner.get_cleaning_report()
   print(f"Dados limpos: {len(cleaned_data)} linhas")
   print(f"Duplicatas removidas: {cleaning_report.duplicates_removed}")
   print(f"Valores interpolados: {cleaning_report.values_interpolated}")
   print(f"Outliers removidos: {cleaning_report.outliers_removed}")

Limpeza Manual
--------------

.. code-block:: python

   # Remoção manual de outliers
   def remove_manual_outliers(data, column, min_val, max_val):
       """Remove outliers baseado em limites manuais."""
       before_count = len(data)
       data = data[(data[column] >= min_val) & (data[column] <= max_val)]
       after_count = len(data)
       
       print(f"🧹 {column}: removidas {before_count - after_count} linhas")
       return data
   
   # Aplicar filtros manuais
   data = remove_manual_outliers(data, 'RPM', 500, 8500)
   data = remove_manual_outliers(data, 'MAP', 10, 300)
   data = remove_manual_outliers(data, 'LAMBDA', 0.5, 1.5)

📊 Visualização Pós-Importação
==============================

Verificação Visual Rápida
--------------------------

.. code-block:: python

   import plotly.express as px
   from src.ui.components import create_quick_overview
   
   # Gráficos de verificação
   fig_rpm = px.line(data, x='TIME', y='RPM', title='RPM vs Tempo')
   fig_map = px.line(data, x='TIME', y='MAP', title='MAP vs Tempo')
   
   # Overview automático
   overview = create_quick_overview(data)
   print(overview)

Estatísticas Básicas
--------------------

.. code-block:: python

   # Estatísticas descritivas
   stats = data.describe()
   print("📊 ESTATÍSTICAS DOS DADOS IMPORTADOS")
   print(stats.round(2))
   
   # Informações específicas
   print(f"\n🎯 INFORMAÇÕES DA SESSÃO:")
   print(f"Duração: {data['TIME'].max():.1f} segundos")
   print(f"RPM máximo: {data['RPM'].max():.0f}")
   print(f"MAP máximo: {data['MAP'].max():.1f} kPa")
   print(f"Temperatura máxima: {data['ENGINE_TEMP'].max():.1f}°C")

🔧 Resolução de Problemas Comuns
================================

Problemas de Encoding
---------------------

.. code-block:: python

   # Detectar encoding automaticamente
   import chardet
   
   def detect_encoding(filepath):
       with open(filepath, 'rb') as file:
           raw_data = file.read()
           result = chardet.detect(raw_data)
           return result['encoding']
   
   # Uso
   encoding = detect_encoding("arquivo.csv")
   print(f"Encoding detectado: {encoding}")
   
   # Forçar encoding específico
   data = parse_fueltech_csv("arquivo.csv", encoding='latin-1')

Problemas de Separador
----------------------

.. code-block:: python

   # Detectar separador automaticamente
   def detect_separator(filepath):
       with open(filepath, 'r') as file:
           first_line = file.readline()
           if ';' in first_line:
               return ';'
           elif ',' in first_line:
               return ','
           elif '\t' in first_line:
               return '\t'
           return ','
   
   # Parser com separador customizado
   separator = detect_separator("arquivo.csv")
   data = pd.read_csv("arquivo.csv", sep=separator)

Dados Corrompidos
-----------------

.. code-block:: python

   # Carregar com tratamento de erros
   def safe_load_csv(filepath):
       try:
           # Primeira tentativa - configuração padrão
           return pd.read_csv(filepath)
       except UnicodeDecodeError:
           # Segunda tentativa - encoding latin-1
           return pd.read_csv(filepath, encoding='latin-1')
       except pd.errors.ParserError:
           # Terceira tentativa - ignorar linhas problemáticas
           return pd.read_csv(filepath, error_bad_lines=False)
       except Exception as e:
           print(f"❌ Falha na importação: {e}")
           return None
   
   data = safe_load_csv("arquivo_problema.csv")

📈 Otimização de Performance
============================

Importação Rápida
------------------

.. code-block:: python

   # Configurações otimizadas para arquivos grandes
   optimal_config = {
       'engine': 'c',           # Engine C é mais rápido
       'low_memory': False,     # Carrega tudo na memória
       'dtype': {               # Especificar tipos de dados
           'TIME': 'float32',
           'RPM': 'uint16',
           'MAP': 'float32',
           'LAMBDA': 'float32'
       },
       'usecols': [             # Carregar apenas colunas necessárias
           'TIME', 'RPM', 'MAP', 'LAMBDA', 'ENGINE_TEMP'
       ]
   }
   
   # Aplicar configurações
   data = pd.read_csv("arquivo.csv", **optimal_config)

Monitoramento de Performance
----------------------------

.. code-block:: python

   import time
   import psutil
   
   def benchmark_import(filepath):
       """Benchmark de importação com métricas."""
       start_time = time.time()
       start_memory = psutil.Process().memory_info().rss / 1024 / 1024
       
       # Importar dados
       data = parse_fueltech_csv(filepath)
       
       end_time = time.time()
       end_memory = psutil.Process().memory_info().rss / 1024 / 1024
       
       # Métricas
       duration = end_time - start_time
       memory_used = end_memory - start_memory
       rows_per_second = len(data) / duration
       
       print(f"📊 BENCHMARK DE IMPORTAÇÃO")
       print(f"Tempo: {duration:.2f}s")
       print(f"Memória: {memory_used:.1f} MB")
       print(f"Velocidade: {rows_per_second:.0f} linhas/s")
       
       return data

✅ Checklist de Importação
==========================

.. raw:: html

   <div class="feature-grid">
      <div class="feature-card">
         <h3>✅ Pré-importação</h3>
         <ul>
            <li>☐ Arquivo é CSV válido</li>
            <li>☐ Headers estão corretos</li>
            <li>☐ Encoding verificado</li>
            <li>☐ Tamanho do arquivo adequado</li>
         </ul>
      </div>
      <div class="feature-card">
         <h3>✅ Durante Importação</h3>
         <ul>
            <li>☐ Configurações apropriadas</li>
            <li>☐ Validação habilitada</li>
            <li>☐ Progresso monitorado</li>
            <li>☐ Erros tratados</li>
         </ul>
      </div>
      <div class="feature-card">
         <h3>✅ Pós-importação</h3>
         <ul>
            <li>☐ Dados validados</li>
            <li>☐ Estatísticas verificadas</li>
            <li>☐ Visualização básica</li>
            <li>☐ Backup dos dados</li>
         </ul>
      </div>
   </div>

📚 Próximos Passos
==================

Agora que você domina a importação:

1. **📊 Análise**: :doc:`analysis-workflow` - Workflow completo de análise
2. **🎨 Visualização**: :doc:`custom-analysis` - Gráficos e análises customizadas  
3. **📄 Relatórios**: :doc:`export-results` - Exportação e relatórios

**Scripts Úteis:**

.. code-block:: bash

   # Download de exemplos
   ./scripts/download_examples.sh
   
   # Validação em lote
   python scripts/batch_validate.py data/raw/
   
   # Conversão de formatos
   python scripts/convert_formats.py input.xlsx output.csv

.. note::
   **💡 Dica**: Mantenha sempre uma cópia backup dos dados originais 
   antes de aplicar qualquer limpeza ou transformação!

----

**Parabéns!** 🎉 Você agora domina a importação de dados FuelTech. 
Continue com o próximo tutorial para aprender workflows de análise completos.