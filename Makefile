# =============================================
# FuelTune Streamlit - Professional Makefile
# =============================================
# Professional development and deployment automation
# Version: 1.0.0
# Author: FuelTune Development Team

# =============================================
# Shell Configuration
# =============================================
SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help install setup clean dev start stop restart status health
.PHONY: format black isort lint quality type test test-unit test-integration test-cov test-watch
.PHONY: docker-build docker-run docker-stop docker-clean docker-logs docker-shell
.PHONY: deploy-dev deploy-staging deploy-prod k8s-apply helm-install
.PHONY: docs docs-serve docs-clean db-migrate db-seed db-reset
.PHONY: version monitor logs backup venv install-dev

# =============================================
# Project Variables
# =============================================
PROJECT_NAME := fueltune-streamlit
VERSION := $(shell cat VERSION 2>/dev/null || echo "1.0.0")
PYTHON_VERSION := 3.12
VENV_DIR := venv
SRC_DIR := src
TESTS_DIR := tests
DOCS_DIR := docs

# =============================================
# Environment Detection
# =============================================
# Auto-detect virtual environment
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
PIP := $(shell command -v pip3 2>/dev/null || command -v pip 2>/dev/null)

# Check if we're in a virtual environment
INVENV := $(shell python -c 'import sys; print(1 if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix) else 0)' 2>/dev/null)

ifeq ($(INVENV), 1)
    PYTHON := python
    PIP := pip
else
    # Use venv if available
    ifneq (,$(wildcard $(VENV_DIR)/bin/activate))
        PYTHON := $(VENV_DIR)/bin/python
        PIP := $(VENV_DIR)/bin/pip
    endif
endif

# =============================================
# Color Configuration for Terminal Output
# =============================================
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[1;37m
BOLD := \033[1m
NC := \033[0m # No Color

# =============================================
# Utility Functions
# =============================================
define print_info
	@echo -e "$(BLUE)$(BOLD)[INFO]$(NC) $(1)"
endef

define print_success
	@echo -e "$(GREEN)$(BOLD)[SUCCESS]$(NC) $(1)"
endef

define print_warning
	@echo -e "$(YELLOW)$(BOLD)[WARNING]$(NC) $(1)"
endef

define print_error
	@echo -e "$(RED)$(BOLD)[ERROR]$(NC) $(1)"
endef

define print_section
	@echo -e "\n$(CYAN)$(BOLD)═══════════════════════════════════════════$(NC)"
	@echo -e "$(CYAN)$(BOLD) $(1)$(NC)"
	@echo -e "$(CYAN)$(BOLD)═══════════════════════════════════════════$(NC)\n"
endef

# =============================================
# Help Target - Show all available commands
# =============================================
help: ## Mostrar esta mensagem de ajuda
	@echo -e "$(PURPLE)$(BOLD)"
	@echo "    ███████╗██╗   ██╗███████╗██╗  ████████╗██╗   ██╗███╗   ██╗███████╗"
	@echo "    ██╔════╝██║   ██║██╔════╝██║  ╚══██╔══╝██║   ██║████╗  ██║██╔════╝"
	@echo "    █████╗  ██║   ██║█████╗  ██║     ██║   ██║   ██║██╔██╗ ██║█████╗  "
	@echo "    ██╔══╝  ██║   ██║██╔══╝  ██║     ██║   ██║   ██║██║╚██╗██║██╔══╝  "
	@echo "    ██║     ╚██████╔╝███████╗███████╗██║   ╚██████╔╝██║ ╚████║███████╗"
	@echo "    ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝"
	@echo -e "$(NC)"
	@echo -e "$(WHITE)$(BOLD)FuelTune Streamlit - Professional Makefile v$(VERSION)$(NC)"
	@echo -e "$(BLUE)Análise Profissional de Dados Automotivos$(NC)\n"
	
	@echo -e "$(CYAN)$(BOLD)📦 COMANDOS DE EXECUÇÃO:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(start|stop|restart|dev|status|health)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	
	@echo -e "\n$(CYAN)$(BOLD)⚡ COMANDOS DE QUALIDADE:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(format|black|isort|lint|quality|type)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	
	@echo -e "\n$(CYAN)$(BOLD)🧪 COMANDOS DE TESTE:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(test)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(PURPLE)%-15s$(NC) %s\n", $$1, $$2}'
	
	@echo -e "\n$(CYAN)$(BOLD)🐳 COMANDOS DOCKER:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(docker)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'
	
	@echo -e "\n$(CYAN)$(BOLD)🚀 COMANDOS DE DEPLOY:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(deploy|k8s|helm)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(RED)%-15s$(NC) %s\n", $$1, $$2}'
	
	@echo -e "\n$(CYAN)$(BOLD)🛠️  COMANDOS DE SETUP:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(install|setup|venv|clean)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(WHITE)%-15s$(NC) %s\n", $$1, $$2}'
	
	@echo -e "\n$(CYAN)$(BOLD)📚 COMANDOS UTILITÁRIOS:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(docs|db|version|monitor|logs|backup|help)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(NC) %s\n", $$1, $$2}'
	
	@echo -e "\n$(GREEN)$(BOLD)Exemplos de uso:$(NC)"
	@echo -e "  $(WHITE)make dev$(NC)          # Iniciar em modo desenvolvimento"
	@echo -e "  $(WHITE)make format$(NC)       # Formatar todo o código"
	@echo -e "  $(WHITE)make test$(NC)         # Executar todos os testes"
	@echo -e "  $(WHITE)make docker-run$(NC)   # Executar no Docker"

# =============================================
# Environment Setup Commands
# =============================================

venv: ## Criar ambiente virtual
	$(call print_section,"Criando Ambiente Virtual")
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(call print_info,"Criando ambiente virtual..."); \
		python3 -m venv $(VENV_DIR); \
		$(call print_success,"Ambiente virtual criado com sucesso!"); \
	else \
		$(call print_warning,"Ambiente virtual já existe"); \
	fi

install: venv ## Instalar dependências de produção
	$(call print_section,"Instalando Dependências de Produção")
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(call print_success,"Dependências de produção instaladas!")

install-dev: venv ## Instalar dependências de desenvolvimento
	$(call print_section,"Instalando Dependências de Desenvolvimento")
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -r requirements-test.txt
	$(PIP) install -e .
	$(call print_success,"Dependências de desenvolvimento instaladas!")

setup: install-dev ## Setup completo do projeto
	$(call print_section,"Setup Completo do Projeto")
	@mkdir -p logs cache data/processed data/raw
	@if [ ! -f .env ]; then cp .env.example .env; fi
	$(call print_info,"Inicializando pre-commit hooks...")
	$(VENV_DIR)/bin/pre-commit install
	$(call print_info,"Executando verificações iniciais...")
	@make quality
	$(call print_success,"Setup completo finalizado!")

# =============================================
# Application Execution Commands
# =============================================

dev: ## Iniciar aplicação em modo desenvolvimento com auto-reload
	$(call print_section,"Iniciando FuelTune em Modo Desenvolvimento")
	$(call print_info,"Streamlit rodando em: http://localhost:8503")
	$(call print_warning,"Modo DEBUG ativado com hot-reload")
	@export PYTHONPATH="${PWD}/src:${PWD}:${PYTHONPATH}" && \
	export DEBUG=true && \
	$(PYTHON) -m streamlit run main.py \
		--server.port=8503 \
		--server.address=0.0.0.0 \
		--server.headless=true \
		--server.runOnSave=true \
		--server.allowRunOnSave=true \
		--theme.base=dark \
		--logger.level=debug

start: ## Iniciar aplicação em produção
	$(call print_section,"Iniciando FuelTune em Produção")
	@export PYTHONPATH="${PWD}/src:${PWD}:${PYTHONPATH}" && \
	export DEBUG=false && \
	$(PYTHON) -m streamlit run main.py \
		--server.port=8503 \
		--server.address=0.0.0.0 \
		--server.headless=true \
		--server.runOnSave=false

stop: ## Parar aplicação
	$(call print_info,"Parando aplicação FuelTune...")
	@pkill -f "streamlit run" || true
	$(call print_success,"Aplicação parada!")

restart: stop start ## Reiniciar aplicação

status: ## Verificar status da aplicação
	$(call print_info,"Verificando status da aplicação...")
	@ps aux | grep -E "(streamlit|fueltune)" | grep -v grep || echo "Nenhum processo encontrado"

health: ## Verificar saúde da aplicação
	$(call print_info,"Executando health check...")
	@curl -f http://localhost:8503/_stcore/health 2>/dev/null && \
		$(call print_success,"Aplicação está saudável!") || \
		$(call print_error,"Aplicação não está respondendo")

# =============================================
# Code Quality Commands  
# =============================================

black: ## Formatar código com Black
	$(call print_info,"Formatando código com Black...")
	$(PYTHON) -m black $(SRC_DIR) $(TESTS_DIR) *.py
	$(call print_success,"Código formatado com Black!")

isort: ## Organizar imports com isort
	$(call print_info,"Organizando imports com isort...")
	$(PYTHON) -m isort $(SRC_DIR) $(TESTS_DIR) *.py
	$(call print_success,"Imports organizados!")

autoflake: ## Remover imports não utilizados
	$(call print_info,"Removendo imports não utilizados...")
	$(PYTHON) -m autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive $(SRC_DIR) $(TESTS_DIR)

format: autoflake isort black ## Formatar código completo (autoflake + isort + black)
	$(call print_success,"Formatação completa do código finalizada!")

lint: ## Executar linters (flake8 e pylint)
	$(call print_section,"Executando Linters")
	$(call print_info,"Executando flake8...")
	$(PYTHON) -m flake8 $(SRC_DIR) $(TESTS_DIR)
	$(call print_info,"Executando pylint...")
	$(PYTHON) -m pylint $(SRC_DIR) --output-format=colorized --reports=no
	$(call print_success,"Linting completo!")

type: ## Type checking com mypy
	$(call print_info,"Executando type checking com mypy...")
	$(PYTHON) -m mypy $(SRC_DIR) --config-file pyproject.toml
	$(call print_success,"Type checking completo!")

security: ## Verificações de segurança com bandit
	$(call print_info,"Executando verificações de segurança...")
	$(PYTHON) -m bandit -r $(SRC_DIR) -f json -o bandit-report.json
	$(PYTHON) -m bandit -r $(SRC_DIR)
	$(call print_success,"Verificações de segurança completas!")

quality: format lint type ## Executar todos os checks de qualidade
	$(call print_section,"Verificações de Qualidade Completas")
	$(call print_success,"Todas as verificações de qualidade passaram!")

# =============================================
# Testing Commands
# =============================================

test: ## Executar todos os testes
	$(call print_section,"Executando Todos os Testes")
	$(PYTHON) -m pytest $(TESTS_DIR) -v --tb=short
	$(call print_success,"Todos os testes executados!")

test-unit: ## Executar apenas testes unitários  
	$(call print_info,"Executando testes unitários...")
	$(PYTHON) -m pytest $(TESTS_DIR) -v -m "unit" --tb=short

test-integration: ## Executar apenas testes de integração
	$(call print_info,"Executando testes de integração...")
	$(PYTHON) -m pytest $(TESTS_DIR) -v -m "integration" --tb=short

test-cov: ## Executar testes com relatório de cobertura
	$(call print_section,"Executando Testes com Cobertura")
	$(PYTHON) -m pytest $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term --cov-report=xml
	$(call print_success,"Relatório de cobertura gerado em htmlcov/")

test-watch: ## Executar testes em modo watch
	$(call print_info,"Executando testes em modo watch (Ctrl+C para parar)...")
	$(PYTHON) -m pytest-watch $(TESTS_DIR) --verbose

# =============================================
# Docker Commands
# =============================================

docker-build: ## Build da imagem Docker
	$(call print_section,"Building Docker Image")
	docker build -t $(PROJECT_NAME):$(VERSION) -t $(PROJECT_NAME):latest .
	$(call print_success,"Imagem Docker criada!")

docker-run: docker-build ## Executar container Docker
	$(call print_section,"Executando Container Docker")
	docker run -d \
		--name $(PROJECT_NAME)-container \
		-p 8501:8501 \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/logs:/app/logs \
		$(PROJECT_NAME):latest
	$(call print_success,"Container executando em http://localhost:8501")

docker-stop: ## Parar containers Docker
	$(call print_info,"Parando containers...")
	docker stop $(PROJECT_NAME)-container || true
	docker rm $(PROJECT_NAME)-container || true

docker-clean: docker-stop ## Limpar imagens e containers Docker
	$(call print_info,"Limpando imagens e containers...")
	docker rmi $(PROJECT_NAME):latest $(PROJECT_NAME):$(VERSION) || true
	docker system prune -f

docker-logs: ## Ver logs do container
	$(call print_info,"Logs do container:")
	docker logs -f $(PROJECT_NAME)-container

docker-shell: ## Shell no container Docker
	$(call print_info,"Acessando shell do container...")
	docker exec -it $(PROJECT_NAME)-container /bin/bash

docker-compose-dev: ## Executar stack completa de desenvolvimento
	$(call print_section,"Iniciando Stack de Desenvolvimento")
	docker-compose up -d
	$(call print_success,"Stack de desenvolvimento iniciada!")
	$(call print_info,"FuelTune: http://localhost:8501")
	$(call print_info,"pgAdmin: http://localhost:5050")
	$(call print_info,"Redis Insight: http://localhost:8001")
	$(call print_info,"Prometheus: http://localhost:9090")
	$(call print_info,"Grafana: http://localhost:3000")

docker-compose-stop: ## Parar stack de desenvolvimento
	$(call print_info,"Parando stack de desenvolvimento...")
	docker-compose down

# =============================================
# Documentation Commands
# =============================================

docs: ## Build da documentação
	$(call print_section,"Construindo Documentação")
	@if [ -d "$(DOCS_DIR)" ]; then \
		cd $(DOCS_DIR) && $(PYTHON) -m sphinx.cmd.build -b html . _build/html; \
		$(call print_success,"Documentação construída em docs/_build/html/"); \
	else \
		$(call print_warning,"Diretório docs não encontrado"); \
	fi

docs-serve: docs ## Servir documentação localmente
	$(call print_info,"Servindo documentação em http://localhost:8000")
	@cd $(DOCS_DIR)/_build/html && $(PYTHON) -m http.server 8000

docs-clean: ## Limpar build da documentação
	$(call print_info,"Limpando build da documentação...")
	@rm -rf $(DOCS_DIR)/_build/ || true

# =============================================
# Database Commands
# =============================================

db-migrate: ## Executar migrações do banco de dados
	$(call print_info,"Executando migrações do banco...")
	@$(PYTHON) -c "import sqlite3; import os; os.makedirs('data', exist_ok=True); conn = sqlite3.connect('data/fueltune.db'); conn.execute('CREATE TABLE IF NOT EXISTS migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'); conn.commit(); conn.close(); print('Migrações executadas com sucesso!')"

db-seed: ## Popular banco com dados de teste
	$(call print_info,"Populando banco com dados de teste...")
	@$(PYTHON) -c "import pandas as pd; import sqlite3; import numpy as np; np.random.seed(42); dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='H'); data = {'timestamp': dates, 'rpm': np.random.normal(3000, 500, len(dates)), 'map': np.random.normal(100, 20, len(dates)), 'throttle': np.random.normal(50, 25, len(dates)), 'afr': np.random.normal(14.7, 1.2, len(dates)), 'fuel_flow': np.random.normal(15, 5, len(dates))}; df = pd.DataFrame(data); conn = sqlite3.connect('data/fueltune.db'); df.to_sql('telemetry_data', conn, if_exists='replace', index=False); conn.close(); print(f'Banco populado com {len(df)} registros de teste!')"

db-reset: ## Reset completo do banco de dados
	$(call print_warning,"ATENÇÃO: Isso irá apagar todos os dados!")
	@read -p "Tem certeza? (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -f data/*.db; \
		$(call print_info,"Banco de dados resetado!"); \
		make db-migrate; \
	else \
		$(call print_info,"Operação cancelada"); \
	fi

# =============================================
# Deployment Commands
# =============================================

deploy-dev: ## Deploy para ambiente de desenvolvimento
	$(call print_section,"Deploy para Desenvolvimento")
	$(call print_info,"Executando deploy para DEV...")
	@export ENV=development && make docker-compose-dev
	$(call print_success,"Deploy DEV completo!")

deploy-staging: ## Deploy para ambiente de staging
	$(call print_section,"Deploy para Staging")
	$(call print_info,"Executando deploy para STAGING...")
	@export ENV=staging && docker-compose -f docker-compose.prod.yml up -d
	$(call print_success,"Deploy STAGING completo!")

deploy-prod: ## Deploy para produção
	$(call print_section,"Deploy para Produção")
	$(call print_warning,"⚠️  DEPLOY DE PRODUÇÃO ⚠️")
	@read -p "Confirma deploy para PRODUÇÃO? (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		export ENV=production && docker-compose -f docker-compose.prod.yml up -d; \
		$(call print_success,"Deploy PRODUÇÃO completo!"); \
	else \
		$(call print_info,"Deploy cancelado"); \
	fi

k8s-apply: ## Aplicar manifests Kubernetes
	$(call print_info,"Aplicando manifests Kubernetes...")
	@if [ -d "k8s" ]; then \
		kubectl apply -f k8s/; \
		$(call print_success,"Manifests K8s aplicados!"); \
	else \
		$(call print_error,"Diretório k8s não encontrado"); \
	fi

helm-install: ## Instalar com Helm
	$(call print_info,"Instalando com Helm...")
	@if [ -d "infrastructure/helm" ]; then \
		helm upgrade --install $(PROJECT_NAME) infrastructure/helm/; \
		$(call print_success,"Helm chart instalado!"); \
	else \
		$(call print_error,"Helm charts não encontrados"); \
	fi

# =============================================
# Utility Commands
# =============================================

clean: ## Limpar arquivos temporários e cache
	$(call print_section,"Limpando Arquivos Temporários")
	$(call print_info,"Removendo arquivos de cache e temporários...")
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache .mypy_cache .coverage htmlcov/ dist/ build/
	@rm -f *.log bandit-report.json pylint-report.json
	$(call print_success,"Limpeza completa!")

version: ## Mostrar versão do projeto
	@echo -e "$(PURPLE)$(BOLD)FuelTune Streamlit v$(VERSION)$(NC)"
	@echo -e "$(BLUE)Python: $(shell $(PYTHON) --version)$(NC)"
	@echo -e "$(BLUE)Streamlit: $(shell $(PYTHON) -m streamlit version 2>/dev/null || echo 'Não instalado')$(NC)"

logs: ## Ver logs da aplicação
	$(call print_info,"Logs da aplicação:")
	@tail -f logs/*.log 2>/dev/null || echo "Nenhum arquivo de log encontrado"

monitor: ## Abrir ferramentas de monitoramento
	$(call print_info,"Abrindo ferramentas de monitoramento...")
	@echo "Grafana: http://localhost:3000 (admin/admin123)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Application: http://localhost:8501"

backup: ## Backup de dados importantes
	$(call print_info,"Criando backup dos dados...")
	@mkdir -p backups
	@tar -czf backups/fueltune-backup-$(shell date +%Y%m%d_%H%M%S).tar.gz data/ logs/ config/
	$(call print_success,"Backup criado em backups/")

# =============================================
# Special Targets
# =============================================

# Check if we're in a virtual environment
check-venv:
	@if [ "$(INVENV)" != "1" ] && [ ! -f "$(VENV_DIR)/bin/activate" ]; then \
		$(call print_error,"Ambiente virtual não encontrado!"); \
		$(call print_info,"Execute: make venv && source venv/bin/activate"); \
		exit 1; \
	fi

# Pre-flight check before important operations
pre-flight: check-venv
	$(call print_info,"Executando verificações pre-flight...")
	@$(PYTHON) --version
	@$(PIP) --version

# Notification after long operations
notify:
	@command -v notify-send >/dev/null 2>&1 && \
		notify-send "FuelTune" "Operação concluída!" || true

# =============================================
# Development Workflow Shortcuts
# =============================================

ci: format lint test ## Pipeline completa de CI (format + lint + test)
	$(call print_success,"Pipeline de CI executada com sucesso!")

quick-check: format lint ## Verificação rápida (format + lint)
	$(call print_success,"Verificação rápida completa!")

full-test: clean test-cov quality ## Suite completa de testes e qualidade
	$(call print_success,"Suite completa de testes executada!")

dev-setup: setup docker-compose-dev ## Setup completo para desenvolvimento
	$(call print_success,"Ambiente de desenvolvimento pronto!")

# =============================================
# Performance and Profiling
# =============================================

profile: ## Profile da aplicação
	$(call print_info,"Executando profiling da aplicação...")
	$(PYTHON) -m cProfile -o profile.stats -m streamlit run app.py &
	@sleep 10
	@pkill -f "streamlit run" || true
	$(PYTHON) -c "import pstats; p=pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

benchmark: ## Benchmark da aplicação
	$(call print_info,"Executando benchmark...")
	@echo "Implementar benchmark específico para FuelTune"

# =============================================
# Dependency Management
# =============================================

update-deps: ## Atualizar dependências
	$(call print_info,"Atualizando dependências...")
	$(PIP) install --upgrade pip
	$(PIP) install -U -r requirements-dev.txt
	$(call print_success,"Dependências atualizadas!")

check-deps: ## Verificar dependências desatualizadas
	$(call print_info,"Verificando dependências desatualizadas...")
	$(PIP) list --outdated

security-check: ## Verificar vulnerabilidades de segurança
	$(call print_info,"Verificando vulnerabilidades...")
	$(PIP) install safety
	$(PYTHON) -m safety check

# =============================================
# End of Makefile
# =============================================