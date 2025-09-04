============
Instalação
============

Este guia fornece instruções detalhadas para instalar o FuelTune Analyzer em diferentes 
sistemas operacionais e configurações. O processo é otimizado para ser simples e confiável.

.. note::
   **Requisitos mínimos:**
   
   - Python 3.11 ou superior
   - 4GB RAM (8GB recomendado)
   - 2GB espaço livre em disco
   - Conexão com internet (para download de dependências)

🐍 Instalação do Python
========================

Windows
-------

**Opção 1: Download Oficial (Recomendado)**

1. Acesse https://python.org/downloads/
2. Baixe Python 3.11+ para Windows
3. Execute o instalador **como administrador**
4. ✅ **IMPORTANTE**: Marque "Add Python to PATH"
5. Escolha "Customize installation"
6. Marque todas as opções extras
7. Clique "Install Now"

**Opção 2: Microsoft Store**

.. code-block:: powershell

   # Abra PowerShell como administrador
   winget install Python.Python.3.11

**Verificação:**

.. code-block:: powershell

   python --version
   # Deve mostrar: Python 3.11.x
   
   pip --version
   # Deve mostrar versão do pip

macOS
-----

**Opção 1: Homebrew (Recomendado)**

.. code-block:: bash

   # Instalar Homebrew se não tiver
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Instalar Python
   brew install python@3.11
   
   # Verificar instalação
   python3 --version

**Opção 2: Download Oficial**

1. Acesse https://python.org/downloads/
2. Baixe Python 3.11+ para macOS
3. Execute o instalador .pkg
4. Siga o assistente de instalação

Linux (Ubuntu/Debian)
----------------------

.. code-block:: bash

   # Atualizar repositórios
   sudo apt update && sudo apt upgrade -y
   
   # Instalar Python 3.11+
   sudo apt install python3.11 python3.11-pip python3.11-venv -y
   
   # Criar link simbólico (opcional)
   sudo ln -sf /usr/bin/python3.11 /usr/bin/python
   
   # Verificar instalação
   python --version
   pip --version

Linux (CentOS/RHEL/Fedora)
---------------------------

.. code-block:: bash

   # Fedora
   sudo dnf install python3.11 python3-pip python3-venv -y
   
   # CentOS/RHEL (habilitar EPEL primeiro)
   sudo yum install epel-release -y
   sudo yum install python311 python311-pip -y

📦 Instalação do FuelTune Analyzer
===================================

Método 1: Instalação Rápida
----------------------------

.. code-block:: bash

   # Criar diretório do projeto
   mkdir fueltune-analyzer
   cd fueltune-analyzer
   
   # Baixar repositório
   git clone https://github.com/fueltune/analyzer-streamlit.git .
   
   # Criar ambiente virtual
   python -m venv venv
   
   # Ativar ambiente virtual
   # Linux/macOS:
   source venv/bin/activate
   # Windows:
   venv\Scripts\activate
   
   # Instalar dependências
   pip install --upgrade pip
   pip install -r requirements.txt
   
   # Executar aplicação
   streamlit run app.py

.. tip::
   **Windows PowerShell**: Se encontrar erro ao ativar o ambiente virtual, execute:
   
   .. code-block:: powershell
   
      Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Método 2: Instalação com Docker
--------------------------------

**Pré-requisitos:**

- Docker Desktop (Windows/macOS) ou Docker Engine (Linux)

.. code-block:: bash

   # Baixar repositório
   git clone https://github.com/fueltune/analyzer-streamlit.git
   cd analyzer-streamlit
   
   # Build da imagem Docker
   docker build -t fueltune-analyzer .
   
   # Executar container
   docker run -p 8501:8501 fueltune-analyzer
   
   # Acessar aplicação
   # http://localhost:8501

**Docker Compose (Recomendado):**

.. code-block:: yaml

   # docker-compose.yml
   version: '3.8'
   services:
     fueltune:
       build: .
       ports:
         - "8501:8501"
       volumes:
         - "./data:/app/data"
         - "./logs:/app/logs"
       environment:
         - PYTHONPATH=/app
       restart: unless-stopped

.. code-block:: bash

   # Executar com Docker Compose
   docker-compose up -d

Método 3: Instalação para Desenvolvimento
------------------------------------------

.. code-block:: bash

   # Clone do repositório
   git clone https://github.com/fueltune/analyzer-streamlit.git
   cd analyzer-streamlit
   
   # Criar ambiente virtual
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   
   # Upgrade pip e instalar wheel
   pip install --upgrade pip wheel setuptools
   
   # Instalar dependências de desenvolvimento
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   pip install -r docs/requirements-docs.txt
   
   # Instalar pre-commit hooks
   pre-commit install
   
   # Executar testes para verificar instalação
   pytest tests/ -v
   
   # Executar aplicação
   streamlit run app.py

🔧 Configuração Inicial
========================

Arquivo de Configuração
------------------------

Crie um arquivo `.env` na raiz do projeto:

.. code-block:: bash

   # Copiar template de configuração
   cp .env.example .env

Edite o arquivo `.env` com suas configurações:

.. code-block:: bash

   # Configurações básicas
   DEBUG=false
   LOG_LEVEL=INFO
   
   # Configurações do banco de dados
   DATABASE_URL=sqlite:///fueltune.db
   
   # Configurações de cache
   CACHE_ENABLED=true
   CACHE_TTL=3600
   
   # Configurações de performance
   MAX_FILE_SIZE_MB=100
   CHUNK_SIZE=5000
   
   # Configurações de análise
   DEFAULT_ANALYSIS_TYPES=performance,statistics,correlation
   ENABLE_PREDICTIVE_ANALYSIS=true
   
   # Configurações de UI
   THEME=light
   LANGUAGE=pt_BR

Configuração do Banco de Dados
-------------------------------

**SQLite (Padrão - Recomendado para uso local):**

.. code-block:: python

   # Já configurado por padrão
   DATABASE_URL=sqlite:///fueltune.db

**PostgreSQL (Recomendado para produção):**

.. code-block:: bash

   # Instalar dependências adicionais
   pip install psycopg2-binary
   
   # Configurar no .env
   DATABASE_URL=postgresql://usuario:senha@localhost:5432/fueltune

.. code-block:: bash

   # Criar banco PostgreSQL
   sudo -u postgres createuser fueltune
   sudo -u postgres createdb fueltune -O fueltune
   sudo -u postgres psql -c "ALTER USER fueltune PASSWORD 'sua_senha';"

**Inicializar Banco:**

.. code-block:: bash

   # Executar migrações
   python -m alembic upgrade head

Configuração de Logging
------------------------

.. code-block:: bash

   # Criar diretório de logs
   mkdir logs
   
   # Configurar permissões (Linux/macOS)
   chmod 755 logs

O sistema criará automaticamente:

- `logs/fueltune.log` - Log principal
- `logs/error.log` - Logs de erro
- `logs/performance.log` - Métricas de performance

🧪 Verificação da Instalação
=============================

Testes Automáticos
-------------------

.. code-block:: bash

   # Executar todos os testes
   pytest tests/ -v
   
   # Testes específicos
   pytest tests/unit/ -v              # Testes unitários
   pytest tests/integration/ -v       # Testes de integração
   pytest tests/ui/ -v                # Testes de interface
   
   # Testes de performance
   pytest tests/performance/ -v
   
   # Gerar relatório de cobertura
   pytest --cov=src tests/ --cov-report=html
   open htmlcov/index.html

Verificação Manual
------------------

.. code-block:: python

   # Teste básico de importação
   python -c "
   from src.data.csv_parser import parse_fueltech_csv
   from src.analysis import AnalyzerFactory
   from src.ui.components import ChartBuilder
   print('✅ Todas as importações funcionando!')
   "

Teste com Dados de Exemplo
---------------------------

.. code-block:: bash

   # Baixar dados de exemplo
   wget https://github.com/fueltune/sample-data/raw/main/example.csv
   
   # Ou criar arquivo de teste
   python scripts/create_sample_data.py

.. code-block:: python

   # Executar teste completo
   from src.data.csv_parser import parse_fueltech_csv
   from src.analysis import AnalyzerFactory
   
   # Carregar dados
   data = parse_fueltech_csv("example.csv")
   print(f"✅ Dados carregados: {len(data)} linhas")
   
   # Testar análise
   analyzer = AnalyzerFactory.create_analyzer("performance")
   results = analyzer.analyze(data)
   print(f"✅ Análise concluída: {results['max_power']:.1f} HP")

🚀 Primeira Execução
====================

.. code-block:: bash

   # Ativar ambiente virtual
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   
   # Executar aplicação
   streamlit run app.py
   
   # Abrir navegador automaticamente
   # http://localhost:8501

**Interface Inicial:**

1. **Upload de Arquivo**: Faça upload de um arquivo CSV FuelTech
2. **Configuração**: Ajuste parâmetros de análise
3. **Análise**: Execute análises automaticamente
4. **Visualização**: Explore gráficos interativos
5. **Exportação**: Baixe relatórios em PDF/Excel

🛠️ Troubleshooting
==================

Problemas Comuns
-----------------

**Erro: "streamlit: command not found"**

.. code-block:: bash

   # Verificar se ambiente virtual está ativo
   which python
   
   # Reinstalar streamlit
   pip uninstall streamlit
   pip install streamlit>=1.29.0
   
   # Verificar PATH
   export PATH="$HOME/.local/bin:$PATH"  # Linux/macOS

**Erro: "No module named 'src'"**

.. code-block:: bash

   # Verificar PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   
   # Ou executar de dentro do diretório
   cd fueltune-analyzer
   python -m streamlit run app.py

**Erro: "Permission denied" (Linux/macOS)**

.. code-block:: bash

   # Verificar permissões
   chmod +x app.py
   
   # Verificar propriedade dos arquivos
   sudo chown -R $(whoami):$(whoami) .

**Erro: "Port 8501 already in use"**

.. code-block:: bash

   # Usar porta diferente
   streamlit run app.py --server.port 8502
   
   # Ou matar processo existente
   lsof -ti:8501 | xargs kill -9

**Erro: "SQLite database locked"**

.. code-block:: bash

   # Remover lock do banco
   rm fueltune.db-wal fueltune.db-shm
   
   # Ou usar PostgreSQL para produção

Problemas de Performance
------------------------

**Lentidão no processamento:**

.. code-block:: bash

   # Verificar configurações
   echo $CHUNK_SIZE     # Deve ser 5000-10000
   echo $CACHE_ENABLED  # Deve ser true
   
   # Aumentar limite de memória Python
   export PYTHONMAXMEMORY=2048m

**Erro de memória:**

.. code-block:: bash

   # Reduzir chunk_size no .env
   CHUNK_SIZE=2000
   
   # Ou processar arquivo em partes menores
   split -l 10000 arquivo_grande.csv arquivo_parte_

Logs e Diagnósticos
--------------------

.. code-block:: bash

   # Verificar logs
   tail -f logs/fueltune.log
   tail -f logs/error.log
   
   # Habilitar debug
   export DEBUG=true
   export LOG_LEVEL=DEBUG
   
   # Executar com verbose
   streamlit run app.py --logger.level debug

🔄 Atualizações
===============

Atualização Manual
-------------------

.. code-block:: bash

   # Fazer backup dos dados
   cp fueltune.db fueltune.db.backup
   
   # Atualizar código
   git pull origin main
   
   # Atualizar dependências
   pip install --upgrade -r requirements.txt
   
   # Executar migrações
   python -m alembic upgrade head
   
   # Reiniciar aplicação

Atualização Automática
-----------------------

.. code-block:: bash

   # Script de atualização
   chmod +x scripts/update.sh
   ./scripts/update.sh

O script executa automaticamente:

1. Backup do banco de dados
2. Download das atualizações
3. Instalação de novas dependências
4. Execução de migrações
5. Testes básicos
6. Reinicialização do serviço

📋 Checklist de Instalação
===========================

.. raw:: html

   <div class="feature-grid">
      <div class="feature-card">
         <h3>✅ Pré-requisitos</h3>
         <ul>
            <li>☐ Python 3.11+ instalado</li>
            <li>☐ Git instalado</li>
            <li>☐ 4GB+ RAM disponível</li>
            <li>☐ 2GB+ espaço em disco</li>
         </ul>
      </div>
      <div class="feature-card">
         <h3>✅ Instalação</h3>
         <ul>
            <li>☐ Repositório clonado</li>
            <li>☐ Ambiente virtual criado</li>
            <li>☐ Dependências instaladas</li>
            <li>☐ Arquivo .env configurado</li>
         </ul>
      </div>
      <div class="feature-card">
         <h3>✅ Configuração</h3>
         <ul>
            <li>☐ Banco de dados inicializado</li>
            <li>☐ Logs configurados</li>
            <li>☐ Testes executados com sucesso</li>
            <li>☐ Aplicação executando</li>
         </ul>
      </div>
   </div>

🆘 Suporte
==========

**Se encontrar problemas:**

1. 📚 Consulte a :doc:`../user-guide/usage` 
2. 🔍 Verifique os :doc:`../dev-guide/troubleshooting`
3. 🐛 Reporte bugs no `GitHub Issues <https://github.com/fueltune/analyzer-streamlit/issues>`_
4. 💬 Peça ajuda no `Discord <https://discord.gg/fueltune>`_
5. 📧 Entre em contato: support@fueltune.com

**Informações úteis para suporte:**

.. code-block:: bash

   # Coletar informações do sistema
   python --version
   streamlit version
   pip list > installed_packages.txt
   
   # Informações do sistema
   uname -a  # Linux/macOS
   systeminfo  # Windows

----

**Próximos passos:**
   - :doc:`getting-started` - Primeiros passos após instalação
   - :doc:`configuration` - Configuração avançada
   - :doc:`usage` - Guia de uso completo