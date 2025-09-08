#!/bin/bash

# =============================================
# FuelTune Makefile - Script de Demonstração
# =============================================
# Este script demonstra o uso do Makefile profissional

set -e

echo "🚗 FuelTune Streamlit - Demonstração do Makefile"
echo "=================================================="
echo

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 1. Mostrar ajuda
print_step "1. Mostrando ajuda do Makefile"
echo
make help
echo
read -p "Pressione Enter para continuar..."
echo

# 2. Mostrar versão
print_step "2. Verificando versão do projeto"
make version
echo
read -p "Pressione Enter para continuar..."
echo

# 3. Limpeza
print_step "3. Limpando arquivos temporários"
make clean
echo
read -p "Pressione Enter para continuar..."
echo

# 4. Verificar estrutura de qualidade
print_step "4. Demonstrando comandos de qualidade"
echo "Comandos disponíveis:"
echo "- make black    (formatação)"
echo "- make isort    (organizar imports)"
echo "- make lint     (análise de código)"
echo "- make type     (type checking)"
echo "- make quality  (todos os checks)"
echo
read -p "Pressione Enter para continuar..."
echo

# 5. Verificar comandos de teste
print_step "5. Demonstrando comandos de teste"
echo "Comandos disponíveis:"
echo "- make test           (todos os testes)"
echo "- make test-unit      (testes unitários)"
echo "- make test-integration (testes de integração)"
echo "- make test-cov       (com cobertura)"
echo "- make test-watch     (modo watch)"
echo
read -p "Pressione Enter para continuar..."
echo

# 6. Verificar comandos Docker
print_step "6. Demonstrando comandos Docker"
echo "Comandos disponíveis:"
echo "- make docker-build   (build da imagem)"
echo "- make docker-run     (executar container)"
echo "- make docker-compose-dev (stack completa)"
echo
read -p "Pressione Enter para continuar..."
echo

# 7. Verificar comandos de banco
print_step "7. Demonstrando comandos de banco"
echo "Comandos disponíveis:"
echo "- make db-migrate     (migrações)"
echo "- make db-seed        (dados de teste)"
echo "- make db-reset       (reset completo)"
echo

print_info "Executando migração de exemplo..."
make db-migrate
echo
read -p "Pressione Enter para continuar..."
echo

# 8. Demonstrar modo desenvolvimento
print_step "8. Modo de desenvolvimento"
echo "O comando 'make dev' inicia o Streamlit com:"
echo "- Hot reload ativado"
echo "- Debug mode habilitado"
echo "- Porta 8503"
echo "- Tema dark"
echo
print_info "Para testar: make dev (será executado em segundo plano)"
echo
read -p "Pressione Enter para continuar..."
echo

# 9. Workflows recomendados
print_step "9. Workflows Recomendados"
echo
echo "${YELLOW}📋 Workflow de Desenvolvimento Diário:${NC}"
echo "1. make setup          (setup inicial)"
echo "2. make dev            (iniciar desenvolvimento)"
echo "3. make format         (antes de commit)"
echo "4. make test           (antes de push)"
echo
echo "${YELLOW}📋 Workflow de CI/CD:${NC}"
echo "1. make ci             (pipeline completa)"
echo "2. make deploy-dev     (deploy desenvolvimento)"
echo "3. make deploy-prod    (deploy produção)"
echo
read -p "Pressione Enter para continuar..."
echo

# 10. Features especiais
print_step "10. Features Especiais do Makefile"
echo "✨ Auto-detecção de ambiente virtual"
echo "✨ Cores e formatação no terminal"
echo "✨ Tratamento de erros robusto"
echo "✨ Confirmações para operações críticas"
echo "✨ Progress feedback visual"
echo "✨ Compatibilidade cross-platform"
echo
read -p "Pressione Enter para finalizar..."
echo

print_success "Demonstração do Makefile concluída!"
print_info "Para ver todos os comandos: make help"
print_info "Para guia detalhado: cat MAKEFILE_GUIDE.md"
echo
echo "🚀 Happy coding com FuelTune!"
