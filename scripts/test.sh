#!/bin/bash
# FuelTune Streamlit - Script de Testes
# Script completo para executar todos os tipos de testes

set -e  # Exit on any error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Diretório do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

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

log_test() {
    echo -e "${PURPLE}[TEST]${NC} $1"
}

log_section() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# Ativar ambiente virtual se existir
activate_venv() {
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        log_info "Ativando ambiente virtual..."
        source venv/bin/activate
        log_success "Ambiente virtual ativado"
    else
        log_warning "Ambiente virtual não encontrado. Usando Python do sistema."
    fi
}

# Verificar dependências de teste
check_test_dependencies() {
    log_info "Verificando dependências de teste..."
    
    test_modules=(
        "pytest"
        "pytest-cov"
        "pytest-mock"
        "black"
        "isort"
        "flake8"
        "mypy"
    )
    
    missing_modules=()
    
    for module in "${test_modules[@]}"; do
        if ! python -c "import $module" 2>/dev/null; then
            missing_modules+=("$module")
        fi
    done
    
    if [ ${#missing_modules[@]} -ne 0 ]; then
        log_warning "Módulos de teste não encontrados: ${missing_modules[*]}"
        log_info "Instalando módulos faltantes..."
        python -m pip install "${missing_modules[@]}"
        log_success "Módulos de teste instalados"
    else
        log_success "Todas as dependências de teste estão disponíveis"
    fi
}

# Executar testes unitários
run_unit_tests() {
    log_section "EXECUTANDO TESTES UNITÁRIOS"
    
    if [ ! -d "tests/unit" ]; then
        log_warning "Diretório tests/unit não encontrado"
        return 1
    fi
    
    pytest_args=(
        "tests/unit/"
        "-v"
        "--tb=short"
        "--strict-markers"
        "--disable-warnings"
    )
    
    if [ "$COVERAGE" = "true" ]; then
        pytest_args+=(
            "--cov=src"
            "--cov-report=html:htmlcov"
            "--cov-report=term-missing"
            "--cov-report=xml:coverage.xml"
            "--cov-fail-under=75"
        )
    fi
    
    if [ "$PARALLEL" = "true" ] && command -v pytest-xdist &> /dev/null; then
        pytest_args+=("-n" "auto")
    fi
    
    log_test "Comando: python -m pytest ${pytest_args[*]}"
    
    if python -m pytest "${pytest_args[@]}"; then
        log_success "Testes unitários passaram ✅"
        return 0
    else
        log_error "Testes unitários falharam ❌"
        return 1
    fi
}

# Executar testes de integração
run_integration_tests() {
    log_section "EXECUTANDO TESTES DE INTEGRAÇÃO"
    
    if [ ! -d "tests/integration" ]; then
        log_warning "Diretório tests/integration não encontrado"
        return 1
    fi
    
    pytest_args=(
        "tests/integration/"
        "-v"
        "--tb=short"
        "-m" "not slow"  # Pular testes marcados como lentos por padrão
    )
    
    if [ "$SLOW_TESTS" = "true" ]; then
        pytest_args=("${pytest_args[@]}" "-m" "slow")
    fi
    
    log_test "Comando: python -m pytest ${pytest_args[*]}"
    
    if python -m pytest "${pytest_args[@]}"; then
        log_success "Testes de integração passaram ✅"
        return 0
    else
        log_error "Testes de integração falharam ❌"
        return 1
    fi
}

# Executar testes de UI (se existirem)
run_ui_tests() {
    log_section "EXECUTANDO TESTES DE UI"
    
    if [ ! -d "tests/ui" ]; then
        log_warning "Diretório tests/ui não encontrado"
        return 1
    fi
    
    pytest_args=(
        "tests/ui/"
        "-v"
        "--tb=short"
    )
    
    log_test "Comando: python -m pytest ${pytest_args[*]}"
    
    if python -m pytest "${pytest_args[@]}"; then
        log_success "Testes de UI passaram ✅"
        return 0
    else
        log_error "Testes de UI falharam ❌"
        return 1
    fi
}

# Executar testes E2E (se existirem)
run_e2e_tests() {
    log_section "EXECUTANDO TESTES E2E"
    
    if [ ! -d "tests/e2e" ]; then
        log_warning "Diretório tests/e2e não encontrado"
        return 1
    fi
    
    pytest_args=(
        "tests/e2e/"
        "-v"
        "--tb=short"
        "-s"  # Não capturar output para testes E2E
    )
    
    log_test "Comando: python -m pytest ${pytest_args[*]}"
    
    if python -m pytest "${pytest_args[@]}"; then
        log_success "Testes E2E passaram ✅"
        return 0
    else
        log_error "Testes E2E falharam ❌"
        return 1
    fi
}

# Executar linting (Black)
run_black_check() {
    log_section "VERIFICANDO FORMATAÇÃO COM BLACK"
    
    if command -v black &> /dev/null; then
        if [ "$FIX" = "true" ]; then
            log_info "Aplicando formatação Black..."
            if black src/ tests/ --line-length 100; then
                log_success "Formatação Black aplicada ✅"
            else
                log_error "Erro ao aplicar formatação Black ❌"
                return 1
            fi
        else
            log_info "Verificando formatação Black..."
            if black src/ tests/ --check --diff --line-length 100; then
                log_success "Formatação Black está OK ✅"
            else
                log_error "Formatação Black precisa ser corrigida ❌"
                log_info "Execute: black src/ tests/ --line-length 100"
                return 1
            fi
        fi
    else
        log_warning "Black não está instalado"
        return 1
    fi
}

# Executar import sorting (isort)
run_isort_check() {
    log_section "VERIFICANDO ORDENAÇÃO DE IMPORTS COM ISORT"
    
    if command -v isort &> /dev/null; then
        if [ "$FIX" = "true" ]; then
            log_info "Aplicando ordenação isort..."
            if isort src/ tests/ --profile black; then
                log_success "Ordenação isort aplicada ✅"
            else
                log_error "Erro ao aplicar ordenação isort ❌"
                return 1
            fi
        else
            log_info "Verificando ordenação isort..."
            if isort src/ tests/ --check-only --diff --profile black; then
                log_success "Ordenação isort está OK ✅"
            else
                log_error "Ordenação isort precisa ser corrigida ❌"
                log_info "Execute: isort src/ tests/ --profile black"
                return 1
            fi
        fi
    else
        log_warning "isort não está instalado"
        return 1
    fi
}

# Executar linting (Flake8)
run_flake8_check() {
    log_section "VERIFICANDO CÓDIGO COM FLAKE8"
    
    if command -v flake8 &> /dev/null; then
        log_info "Executando Flake8..."
        
        if flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503; then
            log_success "Linting Flake8 passou ✅"
        else
            log_error "Linting Flake8 encontrou problemas ❌"
            return 1
        fi
    else
        log_warning "Flake8 não está instalado"
        return 1
    fi
}

# Executar verificação de tipos (MyPy)
run_mypy_check() {
    log_section "VERIFICANDO TIPOS COM MYPY"
    
    if command -v mypy &> /dev/null; then
        log_info "Executando MyPy..."
        
        # Criar arquivo mypy.ini se não existir
        if [ ! -f "mypy.ini" ]; then
            cat > mypy.ini << EOF
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-tests.*]
ignore_errors = True

[mypy-pandas.*]
ignore_missing_imports = True

[mypy-numpy.*]
ignore_missing_imports = True

[mypy-plotly.*]
ignore_missing_imports = True

[mypy-streamlit.*]
ignore_missing_imports = True
EOF
        fi
        
        if mypy src/; then
            log_success "Verificação MyPy passou ✅"
        else
            log_error "MyPy encontrou problemas de tipos ❌"
            return 1
        fi
    else
        log_warning "MyPy não está instalado"
        return 1
    fi
}

# Executar verificação de segurança (Bandit)
run_security_check() {
    log_section "VERIFICAÇÃO DE SEGURANÇA"
    
    if command -v bandit &> /dev/null; then
        log_info "Executando Bandit..."
        
        if bandit -r src/ -f json -o bandit-report.json; then
            log_success "Verificação de segurança passou ✅"
        else
            log_warning "Bandit encontrou possíveis problemas de segurança ⚠️"
            log_info "Verifique bandit-report.json para detalhes"
            # Não retornar erro para não falhar o pipeline
        fi
    else
        log_warning "Bandit não está instalado"
        log_info "Para instalar: pip install bandit"
    fi
}

# Executar todos os testes
run_all_tests() {
    log_section "EXECUTANDO TODOS OS TESTES"
    
    local results=()
    local total_tests=0
    local passed_tests=0
    
    # Testes unitários
    total_tests=$((total_tests + 1))
    if run_unit_tests; then
        results+=("Unit Tests: ✅ PASS")
        passed_tests=$((passed_tests + 1))
    else
        results+=("Unit Tests: ❌ FAIL")
    fi
    
    # Testes de integração
    total_tests=$((total_tests + 1))
    if run_integration_tests; then
        results+=("Integration Tests: ✅ PASS")
        passed_tests=$((passed_tests + 1))
    else
        results+=("Integration Tests: ❌ FAIL")
    fi
    
    # Testes de UI (opcional)
    if [ -d "tests/ui" ]; then
        total_tests=$((total_tests + 1))
        if run_ui_tests; then
            results+=("UI Tests: ✅ PASS")
            passed_tests=$((passed_tests + 1))
        else
            results+=("UI Tests: ❌ FAIL")
        fi
    fi
    
    # Testes E2E (opcional)
    if [ -d "tests/e2e" ] && [ "$E2E" = "true" ]; then
        total_tests=$((total_tests + 1))
        if run_e2e_tests; then
            results+=("E2E Tests: ✅ PASS")
            passed_tests=$((passed_tests + 1))
        else
            results+=("E2E Tests: ❌ FAIL")
        fi
    fi
    
    # Mostrar resultados
    log_section "RESULTADOS DOS TESTES"
    for result in "${results[@]}"; do
        echo -e "${CYAN}$result${NC}"
    done
    
    echo
    log_info "Testes passaram: $passed_tests/$total_tests"
    
    if [ $passed_tests -eq $total_tests ]; then
        log_success "TODOS OS TESTES PASSARAM! 🎉"
        return 0
    else
        log_error "ALGUNS TESTES FALHARAM! ⚠️"
        return 1
    fi
}

# Executar verificações de código
run_code_checks() {
    log_section "VERIFICAÇÕES DE QUALIDADE DE CÓDIGO"
    
    local results=()
    local total_checks=0
    local passed_checks=0
    
    # Black
    total_checks=$((total_checks + 1))
    if run_black_check; then
        results+=("Black (Formatação): ✅ PASS")
        passed_checks=$((passed_checks + 1))
    else
        results+=("Black (Formatação): ❌ FAIL")
    fi
    
    # isort
    total_checks=$((total_checks + 1))
    if run_isort_check; then
        results+=("isort (Imports): ✅ PASS")
        passed_checks=$((passed_checks + 1))
    else
        results+=("isort (Imports): ❌ FAIL")
    fi
    
    # Flake8
    total_checks=$((total_checks + 1))
    if run_flake8_check; then
        results+=("Flake8 (Linting): ✅ PASS")
        passed_checks=$((passed_checks + 1))
    else
        results+=("Flake8 (Linting): ❌ FAIL")
    fi
    
    # MyPy
    if [ "$TYPE_CHECK" = "true" ]; then
        total_checks=$((total_checks + 1))
        if run_mypy_check; then
            results+=("MyPy (Tipos): ✅ PASS")
            passed_checks=$((passed_checks + 1))
        else
            results+=("MyPy (Tipos): ❌ FAIL")
        fi
    fi
    
    # Security
    if [ "$SECURITY_CHECK" = "true" ]; then
        total_checks=$((total_checks + 1))
        if run_security_check; then
            results+=("Bandit (Segurança): ✅ PASS")
            passed_checks=$((passed_checks + 1))
        else
            results+=("Bandit (Segurança): ⚠️ WARNING")
            passed_checks=$((passed_checks + 1))  # Não falhar por segurança
        fi
    fi
    
    # Mostrar resultados
    log_section "RESULTADOS DAS VERIFICAÇÕES"
    for result in "${results[@]}"; do
        echo -e "${CYAN}$result${NC}"
    done
    
    echo
    log_info "Verificações passaram: $passed_checks/$total_checks"
    
    if [ $passed_checks -eq $total_checks ]; then
        log_success "TODAS AS VERIFICAÇÕES PASSARAM! 🎉"
        return 0
    else
        log_error "ALGUMAS VERIFICAÇÕES FALHARAM! ⚠️"
        return 1
    fi
}

# Mostrar menu
show_menu() {
    echo
    echo -e "${BLUE}FuelTune Streamlit - Opções de Teste${NC}"
    echo "====================================="
    echo "1) Todos os testes + verificações"
    echo "2) Apenas testes"
    echo "3) Apenas verificações de código"
    echo "4) Testes unitários"
    echo "5) Testes de integração"
    echo "6) Formatação (Black + isort)"
    echo "7) Linting (Flake8)"
    echo "8) Verificação de tipos (MyPy)"
    echo "9) Verificação de segurança"
    echo "0) Sair"
    echo
}

# Função principal
main() {
    # Configuração padrão
    export COVERAGE="${COVERAGE:-true}"
    export PARALLEL="${PARALLEL:-true}"
    export FIX="${FIX:-false}"
    export TYPE_CHECK="${TYPE_CHECK:-false}"
    export SECURITY_CHECK="${SECURITY_CHECK:-false}"
    export SLOW_TESTS="${SLOW_TESTS:-false}"
    export E2E="${E2E:-false}"
    
    # Ativar ambiente virtual
    activate_venv
    
    # Verificar dependências
    check_test_dependencies
    
    if [ $# -eq 0 ]; then
        # Modo interativo
        while true; do
            show_menu
            read -p "Escolha uma opção: " choice
            
            case $choice in
                1)
                    run_all_tests && run_code_checks
                    break
                    ;;
                2) run_all_tests; break ;;
                3) run_code_checks; break ;;
                4) run_unit_tests; break ;;
                5) run_integration_tests; break ;;
                6) 
                    export FIX=true
                    run_black_check && run_isort_check
                    break
                    ;;
                7) run_flake8_check; break ;;
                8) 
                    export TYPE_CHECK=true
                    run_mypy_check
                    break
                    ;;
                9)
                    export SECURITY_CHECK=true
                    run_security_check
                    break
                    ;;
                0) log_info "Saindo..."; exit 0 ;;
                *) log_error "Opção inválida!" ;;
            esac
        done
    else
        # Modo command line
        case "$1" in
            --all|all)
                run_all_tests && run_code_checks
                ;;
            --tests|tests)
                run_all_tests
                ;;
            --checks|checks)
                run_code_checks
                ;;
            --unit|unit)
                run_unit_tests
                ;;
            --integration|integration)
                run_integration_tests
                ;;
            --ui|ui)
                run_ui_tests
                ;;
            --e2e|e2e)
                export E2E=true
                run_e2e_tests
                ;;
            --format|format)
                export FIX=true
                run_black_check && run_isort_check
                ;;
            --lint|lint)
                run_flake8_check
                ;;
            --types|types)
                export TYPE_CHECK=true
                run_mypy_check
                ;;
            --security|security)
                export SECURITY_CHECK=true
                run_security_check
                ;;
            --fix|fix)
                export FIX=true
                run_black_check && run_isort_check
                ;;
            --help|help)
                echo "Uso: $0 [opção]"
                echo
                echo "Opções:"
                echo "  --all           Todos os testes + verificações"
                echo "  --tests         Apenas testes"
                echo "  --checks        Apenas verificações de código"
                echo "  --unit          Testes unitários"
                echo "  --integration   Testes de integração"
                echo "  --ui            Testes de UI"
                echo "  --e2e           Testes E2E"
                echo "  --format        Verificar formatação"
                echo "  --lint          Linting com Flake8"
                echo "  --types         Verificação de tipos"
                echo "  --security      Verificação de segurança"
                echo "  --fix           Corrigir formatação"
                echo "  --help          Mostrar esta ajuda"
                echo
                echo "Variáveis de ambiente:"
                echo "  COVERAGE=false          Desabilitar cobertura"
                echo "  PARALLEL=false          Desabilitar testes paralelos"
                echo "  TYPE_CHECK=true         Habilitar verificação de tipos"
                echo "  SECURITY_CHECK=true     Habilitar verificação de segurança"
                echo "  SLOW_TESTS=true         Incluir testes lentos"
                echo "  E2E=true                Incluir testes E2E"
                echo "  FIX=true                Auto-fix problemas"
                ;;
            *)
                log_error "Opção desconhecida: $1"
                echo "Use --help para ver opções disponíveis"
                exit 1
                ;;
        esac
    fi
}

# Executar função principal
main "$@"