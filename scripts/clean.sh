#!/bin/bash
# FuelTune Streamlit - Script de Limpeza
# Script para limpar caches, temporários e arquivos desnecessários

set -e  # Exit on any error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_clean() {
    echo -e "${PURPLE}[CLEAN]${NC} $1"
}

# Ativar ambiente virtual se existir
activate_venv() {
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        log_info "Ativando ambiente virtual..."
        source venv/bin/activate
    fi
}

# Limpar cache Python
clean_python_cache() {
    log_info "Limpando cache Python..."
    
    # __pycache__ directories
    find . -type d -name "__pycache__" -not -path "./venv/*" | while read -r dir; do
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            log_clean "Removido: $dir"
        fi
    done
    
    # .pyc files
    find . -name "*.pyc" -not -path "./venv/*" | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Removido: $file"
        fi
    done
    
    # .pyo files
    find . -name "*.pyo" -not -path "./venv/*" | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Removido: $file"
        fi
    done
    
    log_success "Cache Python limpo"
}

# Limpar cache de testes
clean_test_cache() {
    log_info "Limpando cache de testes..."
    
    # pytest cache
    if [ -d ".pytest_cache" ]; then
        rm -rf ".pytest_cache"
        log_clean "Removido: .pytest_cache"
    fi
    
    # coverage files
    if [ -f ".coverage" ]; then
        rm -f ".coverage"
        log_clean "Removido: .coverage"
    fi
    
    # coverage XML
    if [ -f "coverage.xml" ]; then
        rm -f "coverage.xml"
        log_clean "Removido: coverage.xml"
    fi
    
    # HTML coverage report
    if [ -d "htmlcov" ]; then
        rm -rf "htmlcov"
        log_clean "Removido: htmlcov/"
    fi
    
    # Test databases
    find . -name "test*.db" -not -path "./venv/*" | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Removido: $file"
        fi
    done
    
    log_success "Cache de testes limpo"
}

# Limpar cache MyPy
clean_mypy_cache() {
    log_info "Limpando cache MyPy..."
    
    if [ -d ".mypy_cache" ]; then
        rm -rf ".mypy_cache"
        log_clean "Removido: .mypy_cache"
    fi
    
    log_success "Cache MyPy limpo"
}

# Limpar arquivos de log antigos
clean_old_logs() {
    log_info "Limpando logs antigos..."
    
    if [ ! -d "logs" ]; then
        log_warning "Diretório logs/ não encontrado"
        return
    fi
    
    # Logs mais antigos que 7 dias
    find logs/ -name "*.log*" -mtime +7 | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Log antigo removido: $file"
        fi
    done
    
    # Arquivos de log vazios
    find logs/ -name "*.log" -size 0 | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Log vazio removido: $file"
        fi
    done
    
    log_success "Logs antigos limpos"
}

# Limpar cache da aplicação
clean_app_cache() {
    log_info "Limpando cache da aplicação..."
    
    # Usar Python para limpar cache interno se possível
    if python -c "
import sys
sys.path.insert(0, 'src')
try:
    from src.data.cache import get_cache_manager
    cache = get_cache_manager()
    cache.clear_all()
    print('Cache da aplicação limpo via Python')
except Exception as e:
    print(f'Erro ao limpar cache via Python: {e}')
    " 2>/dev/null; then
        log_success "Cache da aplicação limpo via Python"
    fi
    
    # Limpar diretório cache físico
    if [ -d "cache" ]; then
        find cache/ -type f -name "*" | while read -r file; do
            if [ -f "$file" ]; then
                rm -f "$file"
                log_clean "Cache removido: $file"
            fi
        done
        log_success "Diretório cache limpo"
    fi
}

# Limpar arquivos temporários
clean_temp_files() {
    log_info "Limpando arquivos temporários..."
    
    # Temporary files
    find . -name "*.tmp" -not -path "./venv/*" | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Removido: $file"
        fi
    done
    
    # Backup files
    find . -name "*.bak" -not -path "./venv/*" | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Removido: $file"
        fi
    done
    
    # Editor temporary files
    find . -name "*~" -not -path "./venv/*" | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Removido: $file"
        fi
    done
    
    # .DS_Store files (macOS)
    find . -name ".DS_Store" -not -path "./venv/*" | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Removido: $file"
        fi
    done
    
    # Thumbs.db files (Windows)
    find . -name "Thumbs.db" -not -path "./venv/*" | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Removido: $file"
        fi
    done
    
    log_success "Arquivos temporários limpos"
}

# Limpar arquivos de build
clean_build_files() {
    log_info "Limpando arquivos de build..."
    
    # Build directories
    build_dirs=("build" "dist" "*.egg-info")
    
    for pattern in "${build_dirs[@]}"; do
        find . -name "$pattern" -not -path "./venv/*" -type d | while read -r dir; do
            if [ -d "$dir" ]; then
                rm -rf "$dir"
                log_clean "Removido: $dir"
            fi
        done
    done
    
    # Wheel files
    find . -name "*.whl" -not -path "./venv/*" | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Removido: $file"
        fi
    done
    
    log_success "Arquivos de build limpos"
}

# Limpar documentação gerada
clean_docs() {
    log_info "Limpando documentação gerada..."
    
    if [ -d "docs/_build" ]; then
        rm -rf "docs/_build"
        log_clean "Removido: docs/_build"
    fi
    
    if [ -d "docs/api/_autosummary" ]; then
        rm -rf "docs/api/_autosummary"
        log_clean "Removido: docs/api/_autosummary"
    fi
    
    log_success "Documentação gerada limpa"
}

# Limpar exports antigos
clean_old_exports() {
    log_info "Limpando exports antigos..."
    
    if [ ! -d "data/exports" ]; then
        log_warning "Diretório data/exports não encontrado"
        return
    fi
    
    # Exports mais antigos que 30 dias
    find data/exports/ -name "*" -mtime +30 | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            log_clean "Export antigo removido: $file"
        fi
    done
    
    log_success "Exports antigos limpos"
}

# Otimizar banco de dados SQLite
optimize_database() {
    log_info "Otimizando banco de dados..."
    
    db_files=("fueltech_data.db" "test.db")
    
    for db_file in "${db_files[@]}"; do
        if [ -f "$db_file" ]; then
            log_info "Otimizando $db_file..."
            
            # Execute VACUUM to optimize SQLite database
            if command -v sqlite3 &> /dev/null; then
                sqlite3 "$db_file" "VACUUM;"
                log_clean "Banco otimizado: $db_file"
            else
                log_warning "sqlite3 não disponível para otimizar $db_file"
            fi
        fi
    done
    
    log_success "Banco de dados otimizado"
}

# Verificar espaço recuperado
show_space_summary() {
    log_info "Verificando espaço em disco..."
    
    # Mostrar tamanho do projeto
    project_size=$(du -sh . 2>/dev/null | cut -f1 || echo "N/A")
    venv_size=$(du -sh venv 2>/dev/null | cut -f1 || echo "N/A")
    
    echo
    echo -e "${BLUE}=== RESUMO DE ESPAÇO ===${NC}"
    echo -e "${BLUE}Tamanho total do projeto:${NC} $project_size"
    echo -e "${BLUE}Tamanho do ambiente virtual:${NC} $venv_size"
    
    if [ -d "logs" ]; then
        logs_size=$(du -sh logs 2>/dev/null | cut -f1 || echo "N/A")
        echo -e "${BLUE}Tamanho dos logs:${NC} $logs_size"
    fi
    
    if [ -d "data" ]; then
        data_size=$(du -sh data 2>/dev/null | cut -f1 || echo "N/A")
        echo -e "${BLUE}Tamanho dos dados:${NC} $data_size"
    fi
    
    echo
}

# Menu de opções
show_menu() {
    echo
    echo -e "${BLUE}FuelTune Streamlit - Opções de Limpeza${NC}"
    echo "======================================"
    echo "1) Limpeza completa (recomendado)"
    echo "2) Apenas cache Python"
    echo "3) Apenas cache de testes"
    echo "4) Apenas logs antigos"
    echo "5) Apenas arquivos temporários"
    echo "6) Apenas cache da aplicação"
    echo "7) Apenas arquivos de build"
    echo "8) Otimizar banco de dados"
    echo "9) Limpeza suave (mantém dados importantes)"
    echo "10) Limpeza profunda (remove tudo que pode ser regenerado)"
    echo "0) Sair"
    echo
}

# Limpeza completa
clean_all() {
    log_info "Executando limpeza completa..."
    
    clean_python_cache
    clean_test_cache
    clean_mypy_cache
    clean_old_logs
    clean_app_cache
    clean_temp_files
    clean_build_files
    clean_docs
    clean_old_exports
    optimize_database
    
    log_success "Limpeza completa concluída!"
}

# Limpeza suave
clean_soft() {
    log_info "Executando limpeza suave..."
    
    clean_python_cache
    clean_test_cache
    clean_temp_files
    clean_old_logs
    
    log_success "Limpeza suave concluída!"
}

# Limpeza profunda
clean_deep() {
    log_info "Executando limpeza profunda..."
    
    clean_python_cache
    clean_test_cache
    clean_mypy_cache
    clean_old_logs
    clean_app_cache
    clean_temp_files
    clean_build_files
    clean_docs
    clean_old_exports
    
    # Limpar também o banco de desenvolvimento (cuidado!)
    if [ -f "fueltech_data.db" ]; then
        read -p "Remover banco de dados de desenvolvimento? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -f "fueltech_data.db"
            log_clean "Banco de dados de desenvolvimento removido"
        fi
    fi
    
    # Limpar todo o cache
    if [ -d "cache" ]; then
        read -p "Remover todo o diretório cache? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf cache/*
            log_clean "Todo o cache removido"
        fi
    fi
    
    log_success "Limpeza profunda concluída!"
}

# Função principal
main() {
    echo -e "${BLUE}FuelTune Streamlit - Limpeza do Sistema${NC}"
    echo "========================================"
    
    # Ativar ambiente virtual
    activate_venv
    
    if [ $# -eq 0 ]; then
        # Modo interativo
        while true; do
            show_menu
            read -p "Escolha uma opção: " choice
            
            case $choice in
                1) clean_all; show_space_summary; break ;;
                2) clean_python_cache; break ;;
                3) clean_test_cache; break ;;
                4) clean_old_logs; break ;;
                5) clean_temp_files; break ;;
                6) clean_app_cache; break ;;
                7) clean_build_files; break ;;
                8) optimize_database; break ;;
                9) clean_soft; show_space_summary; break ;;
                10) clean_deep; show_space_summary; break ;;
                0) log_info "Saindo..."; exit 0 ;;
                *) log_error "Opção inválida!" ;;
            esac
        done
    else
        # Modo command line
        case "$1" in
            --all|all)
                clean_all
                show_space_summary
                ;;
            --python|python)
                clean_python_cache
                ;;
            --test|test)
                clean_test_cache
                ;;
            --logs|logs)
                clean_old_logs
                ;;
            --temp|temp)
                clean_temp_files
                ;;
            --cache|cache)
                clean_app_cache
                ;;
            --build|build)
                clean_build_files
                ;;
            --docs|docs)
                clean_docs
                ;;
            --db|database)
                optimize_database
                ;;
            --soft|soft)
                clean_soft
                show_space_summary
                ;;
            --deep|deep)
                clean_deep
                show_space_summary
                ;;
            --space|space)
                show_space_summary
                ;;
            --help|help)
                echo "Uso: $0 [opção]"
                echo
                echo "Opções:"
                echo "  --all           Limpeza completa"
                echo "  --python        Cache Python"
                echo "  --test          Cache de testes"
                echo "  --logs          Logs antigos"
                echo "  --temp          Arquivos temporários"
                echo "  --cache         Cache da aplicação"
                echo "  --build         Arquivos de build"
                echo "  --docs          Documentação gerada"
                echo "  --db            Otimizar banco de dados"
                echo "  --soft          Limpeza suave"
                echo "  --deep          Limpeza profunda"
                echo "  --space         Mostrar resumo de espaço"
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
    log_success "Operação de limpeza concluída!"
}

# Executar função principal
main "$@"