#!/bin/bash

echo "Criando repositório fueltune-analyzer no GitHub..."
echo "Você precisará fornecer sua senha do GitHub ou Personal Access Token"
echo ""

curl -X POST https://api.github.com/user/repos \
  -H "Accept: application/vnd.github.v3+json" \
  -u leechardes \
  -d '{"name":"fueltune-analyzer","description":"Sistema profissional de análise de telemetria FuelTech ECU - 92.5% implementado","public":true}'

echo ""
echo "Se o repositório foi criado com sucesso, executando push..."

git remote set-url origin git@github.com:leechardes/fueltune-analyzer.git
git push -u origin main

echo ""
echo "Processo concluído!"
echo "URL: https://github.com/leechardes/fueltune-analyzer"