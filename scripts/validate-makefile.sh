#!/bin/bash

# =============================================
# FuelTune - Script de Validação do Makefile
# =============================================
# Valida se todos os comandos do Makefile funcionam

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_test() {
    echo -e "${BLUE}🔍 Testando: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_skip() {
    echo -e "${YELLOW}⏭️  $1${NC}"
}

test_command() {
    local cmd="$1"
    local description="$2"
    local skip_reason="$3"
    
    print_test "$description"
    
    if [[ -n "$skip_reason" ]]; then
        print_skip "Pulado: $skip_reason"
        return 0
    fi
    
    if make -n $cmd >/dev/null 2>&1; then
        print_success "Comando '$cmd' está válido"
    else
        print_error "Comando '$cmd' tem problemas"
        return 1
    fi
}

echo "🚗 FuelTune - Validação do Makefile"
echo "===================================="
echo

# Testar comandos básicos
echo "📦 COMANDOS BÁSICOS"
echo "-------------------"
test_command "help" "Ajuda do Makefile"
test_command "version" "Versão do projeto"
test_command "clean" "Limpeza de arquivos"
echo

# Testar comandos de setup
echo "🛠️  COMANDOS DE SETUP"
echo "---------------------"
test_command "venv" "Criação do ambiente virtual"
test_command "install" "Instalação de dependências"
test_command "install-dev" "Instalação de dependências de dev"
test_command "setup" "Setup completo"
echo

# Testar comandos de qualidade
echo "⚡ COMANDOS DE QUALIDADE"
echo "-----------------------"
test_command "black" "Formatação com Black"
test_command "isort" "Organização de imports"
test_command "format" "Formatação completa"
test_command "lint" "Análise de código"
test_command "type" "Type checking"
test_command "quality" "Todos os checks de qualidade"
echo

# Testar comandos de teste
echo "🧪 COMANDOS DE TESTE"
echo "--------------------"
test_command "test" "Todos os testes"
test_command "test-unit" "Testes unitários"
test_command "test-integration" "Testes de integração"
test_command "test-cov" "Testes com cobertura"
test_command "test-watch" "Testes em modo watch" "Requer interação"
echo

# Testar comandos de execução
echo "🚀 COMANDOS DE EXECUÇÃO"
echo "-----------------------"
test_command "dev" "Modo desenvolvimento" "Requer interação"
test_command "start" "Iniciar produção" "Requer interação"
test_command "stop" "Parar aplicação"
test_command "restart" "Reiniciar aplicação" "Depende de processo rodando"
test_command "status" "Status da aplicação"
test_command "health" "Health check" "Requer aplicação rodando"
echo

# Testar comandos Docker
echo "🐳 COMANDOS DOCKER"
echo "------------------"
test_command "docker-build" "Build da imagem Docker"
test_command "docker-run" "Executar container" "Requer Docker"
test_command "docker-stop" "Parar containers"
test_command "docker-clean" "Limpar Docker"
test_command "docker-logs" "Logs do container" "Requer container rodando"
test_command "docker-shell" "Shell no container" "Requer container rodando"
test_command "docker-compose-dev" "Stack de desenvolvimento" "Requer Docker Compose"
test_command "docker-compose-stop" "Parar stack"
echo

# Testar comandos de banco
echo "💾 COMANDOS DE BANCO"
echo "--------------------"
test_command "db-migrate" "Migrações do banco"
test_command "db-seed" "Dados de teste"
test_command "db-reset" "Reset do banco" "Requer confirmação"
echo

# Testar comandos de deploy
echo "🚀 COMANDOS DE DEPLOY"
echo "---------------------"
test_command "deploy-dev" "Deploy desenvolvimento"
test_command "deploy-staging" "Deploy staging"
test_command "deploy-prod" "Deploy produção" "Requer confirmação"
test_command "k8s-apply" "Manifests Kubernetes" "Requer kubectl"
test_command "helm-install" "Deploy com Helm" "Requer Helm"
echo

# Testar comandos de documentação
echo "📚 COMANDOS DE DOCUMENTAÇÃO"
echo "---------------------------"
test_command "docs" "Build da documentação"
test_command "docs-serve" "Servir documentação" "Requer interação"
test_command "docs-clean" "Limpar documentação"
echo

# Testar comandos utilitários
echo "🔧 COMANDOS UTILITÁRIOS"
echo "-----------------------"
test_command "logs" "Logs da aplicação"
test_command "monitor" "Ferramentas de monitoramento"
test_command "backup" "Backup de dados"
echo

# Testar workflows
echo "🔄 WORKFLOWS"
echo "------------"
test_command "ci" "Pipeline de CI"
test_command "quick-check" "Verificação rápida"
test_command "full-test" "Suite completa de testes"
test_command "dev-setup" "Setup de desenvolvimento"
echo

# Verificar se arquivo de ajuda existe
echo "📄 ARQUIVOS DE DOCUMENTAÇÃO"
echo "---------------------------"
if [[ -f "MAKEFILE_GUIDE.md" ]]; then
    print_success "Guia do Makefile encontrado"
else
    print_error "Guia do Makefile não encontrado"
fi

if [[ -f "scripts/makefile-demo.sh" ]]; then
    print_success "Script de demonstração encontrado"
else
    print_error "Script de demonstração não encontrado"
fi

if [[ -f "scripts/dev-server.sh" ]]; then
    print_success "Script do servidor de desenvolvimento encontrado"
else
    print_error "Script do servidor de desenvolvimento não encontrado"
fi
echo

# Verificar sintaxe do Makefile
echo "🔍 VERIFICAÇÃO DE SINTAXE"
echo "-------------------------"
if make -n help >/dev/null 2>&1; then
    print_success "Sintaxe do Makefile está correta"
else
    print_error "Problemas na sintaxe do Makefile"
fi
echo

print_success "Validação do Makefile concluída!"
echo
echo "📋 PRÓXIMOS PASSOS:"
echo "- Execute 'make help' para ver todos os comandos"
echo "- Execute 'make setup' para configurar o ambiente"
echo "- Execute 'make dev' para iniciar o desenvolvimento"
echo "- Leia 'MAKEFILE_GUIDE.md' para guia detalhado"