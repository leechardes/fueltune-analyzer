#!/bin/bash
# FuelTune Streamlit - Script de Execução
# Script para executar a aplicação em diferentes modos

set -e  # Exit on any error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Variáveis padrão
DEFAULT_HOST="localhost"
DEFAULT_PORT="8503"
MODE="streamlit"

# Função para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se o ambiente virtual existe
check_venv() {
    if [ ! -d "venv" ]; then
        log_error "Ambiente virtual não encontrado!"
        log_info "Execute: ./scripts/setup.sh --full"
        exit 1
    fi

    if [ ! -f "venv/bin/activate" ]; then
        log_error "Ambiente virtual está corrompido!"
        log_info "Execute: ./scripts/setup.sh --venv"
        exit 1
    fi
}

# Ativar ambiente virtual
activate_venv() {
    log_info "Ativando ambiente virtual..."
    source venv/bin/activate
    log_success "Ambiente virtual ativado"
}

# Verificar dependências críticas
check_dependencies() {
    log_info "Verificando dependências críticas..."

    critical_modules=(
        "streamlit"
        "pandas"
        "numpy"
        "plotly"
        "sqlalchemy"
    )

    for module in "${critical_modules[@]}"; do
        if ! python -c "import $module" 2>/dev/null; then
            log_error "Módulo crítico não encontrado: $module"
            log_info "Execute: ./scripts/setup.sh --deps"
            exit 1
        fi
    done

    log_success "Dependências críticas OK"
}

# Carregar variáveis de ambiente
load_environment() {
    if [ -f ".env" ]; then
        log_info "Carregando variáveis de ambiente..."
        export $(cat .env | grep -v '^#' | xargs)
        log_success "Variáveis de ambiente carregadas"
    else
        log_warning "Arquivo .env não encontrado. Usando valores padrão."
    fi

    # Definir variáveis padrão se não existirem
    export FUELTUNE_HOST="${FUELTUNE_HOST:-$DEFAULT_HOST}"
    export FUELTUNE_PORT="${FUELTUNE_PORT:-$DEFAULT_PORT}"
    export FUELTUNE_DEBUG="${FUELTUNE_DEBUG:-false}"
    export FUELTUNE_LOG_LEVEL="${FUELTUNE_LOG_LEVEL:-INFO}"
}

# Executar Streamlit
run_streamlit() {
    local host="${1:-$FUELTUNE_HOST}"
    local port="${2:-$FUELTUNE_PORT}"
    local debug="${3:-$FUELTUNE_DEBUG}"

    log_info "Iniciando FuelTune Streamlit..."
    log_info "Host: $host"
    log_info "Porta: $port"
    log_info "Debug: $debug"

    if [ "$debug" = "true" ]; then
        export FUELTUNE_DEBUG=1
        log_warning "Modo debug ativado"
    fi

    python main.py --host "$host" --port "$port"
}

# Executar testes
run_tests() {
    local coverage="${1:-true}"
    local verbose="${2:-true}"

    log_info "Executando testes..."

    python main.py --test $([ "$coverage" = "false" ] && echo "--no-coverage")
}

# Gerar documentação
generate_docs() {
    log_info "Gerando documentação..."
    python main.py --docs
}

# Executar health check
run_health_check() {
    log_info "Verificando saúde do sistema..."
    python main.py --health-check
}

# Limpar sistema
clean_system() {
    log_info "Limpando sistema..."
    python main.py --clean
}

# Executar em modo desenvolvimento
run_development() {
    log_info "Executando em modo desenvolvimento..."

    export FUELTUNE_DEBUG=true
    export FUELTUNE_LOG_LEVEL=DEBUG
    export FUELTUNE_PRODUCTION=false
    export FUELTUNE_HEADLESS=false

    run_streamlit "localhost" "8503"
}

# Executar em modo produção
run_production() {
    log_info "Executando em modo produção..."

    export FUELTUNE_DEBUG=false
    export FUELTUNE_LOG_LEVEL=INFO
    export FUELTUNE_PRODUCTION=true
    export FUELTUNE_HEADLESS=true

    run_streamlit "${FUELTUNE_HOST:-0.0.0.0}" "${FUELTUNE_PORT:-8503}"
}

# Executar com Docker
run_docker() {
    log_info "Executando com Docker..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker não está instalado!"
        exit 1
    fi

    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile não encontrado!"
        exit 1
    fi

    # Build da imagem se necessário
    if ! docker images | grep -q "fueltune-streamlit"; then
        log_info "Construindo imagem Docker..."
        docker build -t fueltune-streamlit .
    fi

    # Executar container
    docker run -it --rm \
        -p "${FUELTUNE_PORT:-8503}:8503" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        fueltune-streamlit
}

# Menu de opções
show_menu() {
    echo
    echo -e "${BLUE}FuelTune Streamlit - Opções de Execução${NC}"
    echo "================================================"
    echo "1) Executar Streamlit (padrão)"
    echo "2) Executar em modo desenvolvimento"
    echo "3) Executar em modo produção"
    echo "4) Executar testes"
    echo "5) Gerar documentação"
    echo "6) Verificar saúde do sistema"
    echo "7) Limpar sistema"
    echo "8) Executar com Docker"
    echo "9) Executar comando customizado"
    echo "0) Sair"
    echo
}

# Executar comando customizado
run_custom() {
    echo -e "${BLUE}Comandos disponíveis:${NC}"
    echo "  main.py --help                 - Ajuda completa"
    echo "  main.py --streamlit            - Executar Streamlit"
    echo "  main.py --test                 - Executar testes"
    echo "  main.py --docs                 - Gerar documentação"
    echo "  main.py --health-check         - Verificar saúde"
    echo "  main.py --setup                - Setup inicial"
    echo "  main.py --clean                - Limpar sistema"
    echo

    read -p "Digite o comando (sem 'python'): " custom_cmd

    if [ -n "$custom_cmd" ]; then
        log_info "Executando: python $custom_cmd"
        python $custom_cmd
    else
        log_warning "Comando vazio, cancelando."
    fi
}

# Verificar pré-requisitos
check_prerequisites() {
    check_venv
    activate_venv
    check_dependencies
    load_environment
}

# Mostrar informações do sistema
show_system_info() {
    echo -e "${BLUE}FuelTune Streamlit${NC}"
    echo "=================="

    if [ -f "config.py" ]; then
        version=$(python -c "from config import config; print(config.APP_VERSION)" 2>/dev/null || echo "Unknown")
        echo "Versão: $version"
    fi

    echo "Diretório: $PROJECT_DIR"
    echo "Python: $(python --version 2>&1)"
    echo "Ambiente: $([ -n "$VIRTUAL_ENV" ] && echo "Virtual Environment" || echo "System")"
    echo
}

# Função principal
main() {
    # Verificar pré-requisitos
    check_prerequisites

    if [ $# -eq 0 ]; then
        # Modo interativo
        show_system_info

        while true; do
            show_menu
            read -p "Escolha uma opção: " choice

            case $choice in
                1) run_streamlit; break ;;
                2) run_development; break ;;
                3) run_production; break ;;
                4) run_tests; break ;;
                5) generate_docs; break ;;
                6) run_health_check ;;
                7) clean_system ;;
                8) run_docker; break ;;
                9) run_custom ;;
                0) log_info "Saindo..."; exit 0 ;;
                *) log_error "Opção inválida!" ;;
            esac
        done
    else
        # Modo command line
        case "$1" in
            --streamlit|streamlit)
                shift
                run_streamlit "$@"
                ;;
            --dev|development)
                run_development
                ;;
            --prod|production)
                run_production
                ;;
            --test|test)
                shift
                run_tests "$@"
                ;;
            --docs|docs)
                generate_docs
                ;;
            --health|health-check)
                run_health_check
                ;;
            --clean|clean)
                clean_system
                ;;
            --docker|docker)
                run_docker
                ;;
            --custom)
                shift
                if [ -n "$1" ]; then
                    python main.py "$@"
                else
                    run_custom
                fi
                ;;
            --help|help)
                echo "Uso: $0 [opção] [argumentos...]"
                echo
                echo "Opções:"
                echo "  --streamlit [host] [port]   Executar Streamlit"
                echo "  --dev                       Modo desenvolvimento"
                echo "  --prod                      Modo produção"
                echo "  --test [options]            Executar testes"
                echo "  --docs                      Gerar documentação"
                echo "  --health                    Verificar saúde"
                echo "  --clean                     Limpar sistema"
                echo "  --docker                    Executar com Docker"
                echo "  --custom [cmd]              Comando customizado"
                echo "  --help                      Mostrar esta ajuda"
                echo
                echo "Exemplos:"
                echo "  $0                          Modo interativo"
                echo "  $0 --streamlit             Streamlit padrão"
                echo "  $0 --streamlit 0.0.0.0 8080   Streamlit em 0.0.0.0:8080"
                echo "  $0 --dev                   Desenvolvimento"
                echo "  $0 --prod                  Produção"
                echo "  $0 --test                  Testes com cobertura"
                echo "  $0 --custom --version      Mostrar versão"
                ;;
            *)
                log_error "Opção desconhecida: $1"
                echo "Use --help para ver opções disponíveis"
                exit 1
                ;;
        esac
    fi
}

# Trap para cleanup
cleanup() {
    log_info "Limpeza durante saída..."
    # Cleanup específico pode ser adicionado aqui
}

trap cleanup EXIT

# Executar função principal
main "$@"
