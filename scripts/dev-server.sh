#!/bin/bash

# =============================================
# FuelTune - Script de Servidor de Desenvolvimento
# =============================================
# Script otimizado para desenvolvimento local

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Configurações
PORT=${PORT:-8503}
HOST=${HOST:-0.0.0.0}
DEBUG=${DEBUG:-true}

print_banner() {
    echo -e "${PURPLE}"
    echo "    ███████╗██╗   ██╗███████╗██╗  ████████╗██╗   ██╗███╗   ██╗███████╗"
    echo "    ██╔════╝██║   ██║██╔════╝██║  ╚══██╔══╝██║   ██║████╗  ██║██╔════╝"
    echo "    █████╗  ██║   ██║█████╗  ██║     ██║   ██║   ██║██╔██╗ ██║█████╗  "
    echo "    ██╔══╝  ██║   ██║██╔══╝  ██║     ██║   ██║   ██║██║╚██╗██║██╔══╝  "
    echo "    ██║     ╚██████╔╝███████╗███████╗██║   ╚██████╔╝██║ ╚████║███████╗"
    echo "    ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝"
    echo -e "${NC}"
    echo -e "${WHITE}FuelTune Streamlit - Servidor de Desenvolvimento${NC}"
    echo -e "${BLUE}Análise Profissional de Dados Automotivos${NC}"
    echo
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se o Python está disponível
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD=python3
    elif command -v python &> /dev/null; then
        PYTHON_CMD=python
    else
        print_error "Python não encontrado!"
        exit 1
    fi

    print_info "Usando: $($PYTHON_CMD --version)"
}

# Verificar se o Streamlit está instalado
check_streamlit() {
    if ! $PYTHON_CMD -c "import streamlit" 2>/dev/null; then
        print_error "Streamlit não está instalado!"
        print_info "Execute: pip install streamlit"
        exit 1
    fi

    local version=$($PYTHON_CMD -c "import streamlit; print(streamlit.__version__)" 2>/dev/null)
    print_info "Streamlit versão: $version"
}

# Verificar estrutura do projeto
check_project_structure() {
    if [[ ! -f "app.py" ]] && [[ ! -f "main.py" ]]; then
        print_error "Arquivo principal não encontrado (app.py ou main.py)!"
        exit 1
    fi

    # Criar diretórios necessários
    mkdir -p data logs cache

    print_info "Estrutura do projeto verificada"
}

# Configurar variáveis de ambiente
setup_environment() {
    export PYTHONPATH="${PWD}/src:${PWD}:${PYTHONPATH}"
    export DEBUG=$DEBUG
    export LOG_LEVEL=${LOG_LEVEL:-DEBUG}
    export STREAMLIT_SERVER_PORT=$PORT
    export STREAMLIT_SERVER_ADDRESS=$HOST

    # Configuração do Streamlit
    mkdir -p ~/.streamlit
    cat > ~/.streamlit/config.toml << EOF
[server]
port = $PORT
address = "$HOST"
headless = true
runOnSave = true
allowRunOnSave = true
maxUploadSize = 1028
maxMessageSize = 1028
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
showErrorDetails = true

[theme]
base = "dark"
primaryColor = "#FF6B35"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"

[logger]
level = "debug"
messageFormat = "%(asctime)s %(levelname)s: %(message)s"

[client]
showErrorDetails = true
toolbarMode = "auto"
EOF

    print_info "Ambiente configurado"
}

# Função para cleanup ao sair
cleanup() {
    print_info "Parando servidor..."
    pkill -f "streamlit run" 2>/dev/null || true
    print_success "Servidor parado"
}

# Trap para cleanup
trap cleanup EXIT INT TERM

# Função principal
main() {
    print_banner

    print_info "Iniciando servidor de desenvolvimento..."
    echo

    # Verificações
    check_python
    check_streamlit
    check_project_structure
    setup_environment

    echo
    print_success "🚀 Iniciando FuelTune Streamlit..."
    print_info "📍 URL: http://$HOST:$PORT"
    print_info "🔧 Modo: Desenvolvimento (DEBUG=$DEBUG)"
    print_info "📁 Diretório: $(pwd)"
    print_warning "⚠️  Hot-reload ativado - arquivos serão monitorados"
    echo

    # Determinar arquivo principal
    if [[ -f "app.py" ]]; then
        APP_FILE="app.py"
    else
        APP_FILE="main.py"
    fi

    print_info "📄 Executando: $APP_FILE"
    echo
    print_info "Para parar o servidor: Ctrl+C"
    echo

    # Iniciar Streamlit
    $PYTHON_CMD -m streamlit run $APP_FILE \
        --server.port=$PORT \
        --server.address=$HOST \
        --server.headless=true \
        --server.runOnSave=true \
        --server.allowRunOnSave=true \
        --theme.base=dark \
        --logger.level=debug \
        --browser.gatherUsageStats=false
}

# Executar função principal
main "$@"
