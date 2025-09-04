#!/bin/bash
# FuelTune Streamlit - Script de Setup Inicial
# Este script configura o ambiente de desenvolvimento e produção

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

echo -e "${BLUE}FuelTune Streamlit - Setup Inicial${NC}"
echo "========================================"

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

# Verificar se Python 3.8+ está instalado
check_python() {
    log_info "Verificando instalação do Python..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 não encontrado. Instale Python 3.8 ou superior."
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_success "Python $python_version encontrado"
    
    # Verificar versão mínima
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        log_success "Versão do Python é compatível (>=3.8)"
    else
        log_error "Python 3.8 ou superior é necessário. Versão atual: $python_version"
        exit 1
    fi
}

# Criar ambiente virtual
setup_venv() {
    log_info "Configurando ambiente virtual..."
    
    if [ -d "venv" ]; then
        log_warning "Ambiente virtual já existe. Removendo..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    log_success "Ambiente virtual criado"
    
    # Ativar ambiente virtual
    source venv/bin/activate
    log_success "Ambiente virtual ativado"
    
    # Atualizar pip
    log_info "Atualizando pip..."
    python -m pip install --upgrade pip
    log_success "pip atualizado"
}

# Instalar dependências
install_dependencies() {
    log_info "Instalando dependências..."
    
    if [ ! -f "requirements.txt" ]; then
        log_error "Arquivo requirements.txt não encontrado!"
        exit 1
    fi
    
    # Instalar dependências principais
    python -m pip install -r requirements.txt
    log_success "Dependências principais instaladas"
    
    # Instalar dependências de desenvolvimento se existirem
    if [ -f "requirements-dev.txt" ]; then
        python -m pip install -r requirements-dev.txt
        log_success "Dependências de desenvolvimento instaladas"
    fi
    
    # Instalar dependências de produção se existirem
    if [ -f "requirements-prod.txt" ]; then
        python -m pip install -r requirements-prod.txt
        log_success "Dependências de produção instaladas"
    fi
    
    # Instalar dependências de teste se existirem
    if [ -f "requirements-test.txt" ]; then
        python -m pip install -r requirements-test.txt
        log_success "Dependências de teste instaladas"
    fi
}

# Criar diretórios necessários
create_directories() {
    log_info "Criando estrutura de diretórios..."
    
    directories=(
        "logs"
        "cache"
        "data/raw"
        "data/processed" 
        "data/exports"
        "data/samples"
        "docs/_build"
        "tests/fixtures/data"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_success "Diretório criado: $dir"
    done
}

# Configurar arquivo de ambiente
setup_environment() {
    log_info "Configurando arquivo de ambiente..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "Arquivo .env criado a partir do exemplo"
        else
            # Criar .env básico
            cat > .env << EOF
# FuelTune Streamlit Configuration
FUELTUNE_DEBUG=false
FUELTUNE_LOG_LEVEL=INFO
FUELTUNE_PORT=8501
FUELTUNE_HOST=localhost
FUELTUNE_HEADLESS=false
FUELTUNE_PRODUCTION=false

# Database
DATABASE_URL=sqlite:///fueltech_data.db

# Cache
CACHE_TTL_HOURS=24
CACHE_MAX_SIZE_MB=512

# Logging
LOG_FILE=logs/fueltune.log
LOG_ROTATION_SIZE=10MB
LOG_BACKUP_COUNT=5
EOF
            log_success "Arquivo .env básico criado"
        fi
    else
        log_warning "Arquivo .env já existe"
    fi
}

# Instalar pre-commit hooks
setup_precommit() {
    log_info "Configurando pre-commit hooks..."
    
    if [ -f ".pre-commit-config.yaml" ]; then
        if command -v pre-commit &> /dev/null; then
            pre-commit install
            log_success "Pre-commit hooks instalados"
        else
            log_warning "pre-commit não instalado. Instalando..."
            python -m pip install pre-commit
            pre-commit install
            log_success "Pre-commit hooks instalados"
        fi
    else
        log_warning "Arquivo .pre-commit-config.yaml não encontrado"
    fi
}

# Executar testes básicos
run_basic_tests() {
    log_info "Executando testes básicos..."
    
    # Testar imports principais
    python -c "
import sys
sys.path.insert(0, 'src')

try:
    from config import config
    print('✅ Config OK')
    
    from src.utils.logger import get_logger
    print('✅ Logger OK')
    
    from src.data.database import get_database
    print('✅ Database OK')
    
    from src.data.cache import get_cache_manager
    print('✅ Cache OK')
    
    print('SUCCESS: Imports básicos funcionando')
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
    "
    
    if [ $? -eq 0 ]; then
        log_success "Testes básicos passaram"
    else
        log_error "Testes básicos falharam"
        exit 1
    fi
}

# Executar health check
run_health_check() {
    log_info "Executando verificação de saúde..."
    
    if python main.py --health-check; then
        log_success "Sistema está saudável"
    else
        log_warning "Sistema tem alguns problemas, mas pode funcionar"
    fi
}

# Menu de opções
show_menu() {
    echo
    echo -e "${BLUE}Opções de Setup:${NC}"
    echo "1) Setup completo (recomendado)"
    echo "2) Apenas ambiente virtual"
    echo "3) Apenas dependências"
    echo "4) Apenas configuração"
    echo "5) Setup de desenvolvimento"
    echo "6) Setup de produção"
    echo "7) Sair"
    echo
}

# Setup completo
setup_full() {
    log_info "Executando setup completo..."
    
    check_python
    setup_venv
    install_dependencies
    create_directories
    setup_environment
    setup_precommit
    run_basic_tests
    run_health_check
    
    log_success "Setup completo concluído!"
}

# Setup de desenvolvimento
setup_development() {
    log_info "Executando setup de desenvolvimento..."
    
    check_python
    setup_venv
    install_dependencies
    create_directories
    setup_environment
    setup_precommit
    
    # Configurar para desenvolvimento
    sed -i 's/FUELTUNE_DEBUG=false/FUELTUNE_DEBUG=true/' .env
    sed -i 's/FUELTUNE_LOG_LEVEL=INFO/FUELTUNE_LOG_LEVEL=DEBUG/' .env
    
    run_basic_tests
    
    log_success "Setup de desenvolvimento concluído!"
}

# Setup de produção
setup_production() {
    log_info "Executando setup de produção..."
    
    check_python
    setup_venv
    install_dependencies
    create_directories
    setup_environment
    
    # Configurar para produção
    sed -i 's/FUELTUNE_DEBUG=true/FUELTUNE_DEBUG=false/' .env
    sed -i 's/FUELTUNE_LOG_LEVEL=DEBUG/FUELTUNE_LOG_LEVEL=INFO/' .env
    sed -i 's/FUELTUNE_PRODUCTION=false/FUELTUNE_PRODUCTION=true/' .env
    sed -i 's/FUELTUNE_HEADLESS=false/FUELTUNE_HEADLESS=true/' .env
    
    run_basic_tests
    run_health_check
    
    log_success "Setup de produção concluído!"
}

# Função principal
main() {
    if [ $# -eq 0 ]; then
        # Modo interativo
        while true; do
            show_menu
            read -p "Escolha uma opção: " choice
            
            case $choice in
                1) setup_full; break ;;
                2) check_python; setup_venv; break ;;
                3) install_dependencies; break ;;
                4) create_directories; setup_environment; break ;;
                5) setup_development; break ;;
                6) setup_production; break ;;
                7) log_info "Saindo..."; exit 0 ;;
                *) log_error "Opção inválida!" ;;
            esac
        done
    else
        # Modo command line
        case "$1" in
            --full|full) setup_full ;;
            --dev|development) setup_development ;;
            --prod|production) setup_production ;;
            --venv|venv) check_python; setup_venv ;;
            --deps|dependencies) install_dependencies ;;
            --config|config) create_directories; setup_environment ;;
            --test|test) run_basic_tests ;;
            --health|health-check) run_health_check ;;
            --help|help)
                echo "Uso: $0 [opção]"
                echo "Opções:"
                echo "  --full          Setup completo"
                echo "  --dev           Setup desenvolvimento"
                echo "  --prod          Setup produção"
                echo "  --venv          Apenas ambiente virtual"
                echo "  --deps          Apenas dependências"
                echo "  --config        Apenas configuração"
                echo "  --test          Apenas testes básicos"
                echo "  --health        Verificação de saúde"
                echo "  --help          Mostrar esta ajuda"
                ;;
            *) 
                log_error "Opção desconhecida: $1"
                echo "Use --help para ver opções disponíveis"
                exit 1 
                ;;
        esac
    fi
    
    echo
    echo -e "${GREEN}Setup concluído!${NC}"
    echo
    echo "Para iniciar a aplicação:"
    echo "  ./venv/bin/python main.py"
    echo
    echo "Ou usar o script de execução:"
    echo "  ./scripts/run.sh"
    echo
}

# Executar função principal
main "$@"