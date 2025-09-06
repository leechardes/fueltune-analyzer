#!/bin/bash

# Script para configurar sudo sem senha para o usuário
# ATENÇÃO: Este script precisa ser executado com privilégios de root

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Este script precisa ser executado como root!${NC}"
    echo ""
    echo "Opções para executar:"
    echo ""
    echo "1. Se você tem acesso root:"
    echo "   ${YELLOW}su -${NC}"
    echo "   ${YELLOW}/home/lee/projects/fueltune-streamlit/enable-sudo-nopasswd.sh${NC}"
    echo ""
    echo "2. Se você tem sudo (vai pedir senha uma última vez):"
    echo "   ${YELLOW}sudo /home/lee/projects/fueltune-streamlit/enable-sudo-nopasswd.sh${NC}"
    echo ""
    echo "3. Peça ao administrador do sistema para executar este script"
    exit 1
fi

echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}  Configurador de Sudo NoPassword${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""

# Detectar usuário atual (quem chamou o sudo)
if [ -n "$SUDO_USER" ]; then
    TARGET_USER="$SUDO_USER"
else
    # Se não foi via sudo, perguntar
    echo "Digite o nome do usuário para liberar (padrão: lee):"
    read -r INPUT_USER
    TARGET_USER="${INPUT_USER:-lee}"
fi

echo -e "${YELLOW}Configurando sudo sem senha para o usuário: $TARGET_USER${NC}"

# Criar arquivo de configuração no sudoers.d (mais seguro que editar sudoers diretamente)
SUDOERS_FILE="/etc/sudoers.d/nopasswd-$TARGET_USER"

# Backup se o arquivo já existir
if [ -f "$SUDOERS_FILE" ]; then
    cp "$SUDOERS_FILE" "$SUDOERS_FILE.backup.$(date +%Y%m%d-%H%M%S)"
    echo -e "${YELLOW}Backup criado do arquivo existente${NC}"
fi

# Menu de opções
echo ""
echo "Escolha o nível de acesso:"
echo "1) Acesso TOTAL sem senha (todos os comandos)"
echo "2) Apenas comandos de instalação (apt, apt-get, snap, dpkg)"
echo "3) Comandos específicos (apt, apt-get, gh, docker)"
echo "4) Personalizado (você define os comandos)"
echo ""
echo -n "Opção (1-4): "
read -r OPTION

case $OPTION in
    1)
        echo "$TARGET_USER ALL=(ALL) NOPASSWD: ALL" > "$SUDOERS_FILE"
        echo -e "${GREEN}✓ Configurado acesso TOTAL sem senha${NC}"
        ;;
    2)
        echo "$TARGET_USER ALL=(ALL) NOPASSWD: /usr/bin/apt, /usr/bin/apt-get, /usr/bin/snap, /usr/bin/dpkg" > "$SUDOERS_FILE"
        echo -e "${GREEN}✓ Configurado acesso para comandos de instalação${NC}"
        ;;
    3)
        cat > "$SUDOERS_FILE" << EOF
# Comandos de gerenciamento de pacotes
$TARGET_USER ALL=(ALL) NOPASSWD: /usr/bin/apt
$TARGET_USER ALL=(ALL) NOPASSWD: /usr/bin/apt-get
$TARGET_USER ALL=(ALL) NOPASSWD: /usr/bin/snap
$TARGET_USER ALL=(ALL) NOPASSWD: /usr/bin/dpkg

# GitHub CLI
$TARGET_USER ALL=(ALL) NOPASSWD: /usr/bin/gh
$TARGET_USER ALL=(ALL) NOPASSWD: /snap/bin/gh

# Docker (se instalado)
$TARGET_USER ALL=(ALL) NOPASSWD: /usr/bin/docker
$TARGET_USER ALL=(ALL) NOPASSWD: /usr/bin/docker-compose

# Gerenciamento de serviços
$TARGET_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl
$TARGET_USER ALL=(ALL) NOPASSWD: /usr/sbin/service
EOF
        echo -e "${GREEN}✓ Configurado acesso para comandos específicos${NC}"
        ;;
    4)
        echo "Digite os caminhos completos dos comandos (um por linha, termine com linha vazia):"
        echo "Exemplo: /usr/bin/apt"
        echo ""
        
        echo "# Custom sudo permissions for $TARGET_USER" > "$SUDOERS_FILE"
        while IFS= read -r cmd; do
            [ -z "$cmd" ] && break
            echo "$TARGET_USER ALL=(ALL) NOPASSWD: $cmd" >> "$SUDOERS_FILE"
            echo "  Adicionado: $cmd"
        done
        echo -e "${GREEN}✓ Configuração personalizada aplicada${NC}"
        ;;
    *)
        echo -e "${RED}Opção inválida!${NC}"
        rm -f "$SUDOERS_FILE"
        exit 1
        ;;
esac

# Definir permissões corretas (importante para segurança)
chmod 0440 "$SUDOERS_FILE"

# Validar o arquivo sudoers
echo ""
echo "Validando configuração..."
if visudo -c -f "$SUDOERS_FILE"; then
    echo -e "${GREEN}✓ Configuração validada com sucesso!${NC}"
else
    echo -e "${RED}✗ Erro na configuração! Removendo arquivo...${NC}"
    rm -f "$SUDOERS_FILE"
    exit 1
fi

echo ""
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}    CONFIGURAÇÃO CONCLUÍDA!${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""
echo "Usuário $TARGET_USER agora pode usar sudo sem senha para:"
case $OPTION in
    1) echo "  - TODOS os comandos" ;;
    2) echo "  - Comandos de instalação (apt, apt-get, snap, dpkg)" ;;
    3) echo "  - Comandos específicos (apt, gh, docker, systemctl)" ;;
    4) echo "  - Comandos personalizados configurados" ;;
esac
echo ""
echo "Para testar, execute como $TARGET_USER:"
echo -e "  ${YELLOW}sudo apt update${NC}"
echo ""
echo "Para reverter esta configuração:"
echo -e "  ${YELLOW}sudo rm $SUDOERS_FILE${NC}"
echo ""

# Se executado via sudo, trocar para o usuário e testar
if [ -n "$SUDO_USER" ]; then
    echo "Testando configuração..."
    su - "$SUDO_USER" -c "sudo -n echo '✓ Teste bem-sucedido: sudo funcionando sem senha!'" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Configuração testada e funcionando!${NC}"
    else
        echo -e "${YELLOW}⚠ Teste automático falhou, mas configuração foi aplicada${NC}"
    fi
fi

echo ""
echo "Script finalizado com sucesso!"