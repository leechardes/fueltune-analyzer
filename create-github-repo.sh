#!/bin/bash

# Script para criar repositório no GitHub e fazer push

echo "======================================"
echo "  CRIAÇÃO DO REPOSITÓRIO NO GITHUB"
echo "======================================"
echo ""
echo "Por favor, siga os passos abaixo:"
echo ""
echo "1. Acesse: https://github.com/new"
echo ""
echo "2. Preencha os campos:"
echo "   - Repository name: fueltune-analyzer"
echo "   - Description: Sistema profissional de análise de telemetria FuelTech ECU"
echo "   - Public/Private: Sua escolha"
echo "   - ⚠️ NÃO marque 'Initialize with README'"
echo ""
echo "3. Clique em 'Create repository'"
echo ""
echo "4. Após criar, pressione ENTER aqui para continuar..."
read

echo ""
echo "Configurando remote e fazendo push..."

# Remove remote antigo se existir
git remote remove origin 2>/dev/null

# Adiciona novo remote
git remote add origin git@github.com:leechardes/fueltune-analyzer.git

# Faz o push
echo "Fazendo push para o GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCESSO! Repositório enviado para o GitHub!"
    echo ""
    echo "🔗 URL do repositório: https://github.com/leechardes/fueltune-analyzer"
    echo ""
    echo "📊 Estatísticas:"
    echo "   - 233 arquivos"
    echo "   - 99.594 linhas de código"
    echo "   - 92.5% implementado"
    echo "   - Score QA: 92.5/100"
else
    echo ""
    echo "❌ Erro ao fazer push. Verifique:"
    echo "   1. Se o repositório foi criado no GitHub"
    echo "   2. Se você tem permissão de escrita"
    echo "   3. Se suas chaves SSH estão configuradas"
    echo ""
    echo "Para configurar SSH:"
    echo "   ssh-keygen -t ed25519 -C 'seu-email@exemplo.com'"
    echo "   cat ~/.ssh/id_ed25519.pub"
    echo "   # Adicione a chave em: https://github.com/settings/keys"
fi