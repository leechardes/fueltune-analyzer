# Sistema de Agentes de Documentação

**Versão:** 1.0.0  
**Última Atualização:** 2024-08-31  
**Versão do Template:** v1.0

## 🤖 Visão Geral

Este diretório contém agentes automatizados de documentação - instruções estruturadas que podem ser executadas por assistentes de IA (como Claude) para analisar, atualizar e manter a documentação do projeto.

## 📁 Estrutura do Diretório

```
agents/
├── README.md          # Este arquivo
├── pending/           # Tarefas aguardando execução
├── continuous/        # Tarefas recorrentes/agendadas
├── executed/          # Tarefas concluídas (arquivo)
└── reports/           # Relatórios e análises gerados
    ├── daily/         # Relatórios diários
    ├── weekly/        # Resumos semanais
    └── analysis/      # Relatórios de análise profunda
```

## 📋 Convenção de Nomenclatura dos Agentes

### Formato
```
[ACAO]-[ALVO]-[DATA].md
```

### Regras
1. **LETRAS MAIÚSCULAS** apenas
2. **Idioma inglês** apenas (para padronização)
3. **Hífens** como separadores
4. **Formato de data:** YYYYMMDD (opcional para tarefas contínuas)

### Exemplos
- `ANALYZE-CODE-STRUCTURE-20240831.md`
- `UPDATE-API-DOCUMENTATION.md` (contínuo)
- `GENERATE-CHANGELOG-20240831.md`
- `CHECK-DOCUMENTATION-COVERAGE.md` (contínuo)

## 🔄 Ciclo de Vida do Agente

### 1. Criação (Pendente)
Novos agentes são criados em `pending/` com instruções claras:
```markdown
# ANALYZE-PROJECT-20240831

## Objetivo
Analisar estrutura do projeto e gerar insights de documentação.

## Instruções
1. Escanear todos os arquivos fonte
2. Identificar funções não documentadas
3. Gerar relatório de cobertura

## Saída
Salvar relatório em: agents/reports/analysis/coverage-20240831.md
```

### 2. Execução
Agentes são executados por assistentes de IA ou scripts de automação:
- Manual: Copie o conteúdo do agente para o assistente de IA
- Automatizado: Script processa agentes pendentes

### 3. Conclusão (Executado)
Após execução, agentes são movidos para `executed/` com resultados:
- Instruções originais preservadas
- Timestamp de execução adicionado
- Resultados referenciados

### 4. Tarefas Contínuas
Tarefas em `continuous/` permanecem ativas e são executadas periodicamente:
- Sem data no nome do arquivo
- Cronograma de execução anotado no arquivo
- Resultados com timestamp nos relatórios

## 📊 Organização dos Relatórios

### Relatórios Diários
`reports/daily/YYYY-MM-DD.md`
- Resumo de execução
- Métricas coletadas
- Problemas encontrados

### Relatórios Semanais
`reports/weekly/YYYY-WW.md`
- Visão geral da semana
- Análise de tendências
- Recomendações

### Relatórios de Análise
`reports/analysis/[topico]-YYYYMMDD.md`
- Análises profundas
- Análise de cobertura
- Métricas de qualidade

## 🎯 Tipos Comuns de Agentes

### Agentes de Análise
- `ANALYZE-CODE-STRUCTURE` - Mapear organização do projeto
- `ANALYZE-DEPENDENCIES` - Verificar e documentar dependências
- `ANALYZE-API-ENDPOINTS` - Documentar todas as rotas da API
- `ANALYZE-TEST-COVERAGE` - Medir cobertura de testes

### Agentes de Atualização
- `UPDATE-README` - Atualizar conteúdo do README.md
- `UPDATE-CHANGELOG` - Adicionar mudanças recentes
- `UPDATE-VERSION` - Incrementar números de versão
- `UPDATE-API-DOCS` - Sincronizar documentação da API

### Agentes de Geração
- `GENERATE-ARCHITECTURE-DIAGRAM` - Criar diagramas do sistema
- `GENERATE-API-REFERENCE` - Construir documentação da API
- `GENERATE-USER-GUIDE` - Criar documentação do usuário
- `GENERATE-METRICS-REPORT` - Construir dashboard de métricas

### Agentes de Validação
- `VALIDATE-LINKS` - Verificar todos os links da documentação
- `VALIDATE-EXAMPLES` - Testar exemplos de código
- `VALIDATE-VERSIONS` - Verificar consistência de versões
- `VALIDATE-FORMATTING` - Verificar formatação markdown

## 🚀 Como Usar

### Criando um Novo Agente

1. **Determine tipo e escopo**
   ```
   Ação: ANALYZE
   Alvo: API-ENDPOINTS
   Data: 20240831
   ```

2. **Crie arquivo em pending/**
   ```
   agents/pending/ANALYZE-API-ENDPOINTS-20240831.md
   ```

3. **Escreva instruções claras**
   ```markdown
   # ANALYZE-API-ENDPOINTS-20240831
   
   ## Objetivo
   Documentar todos os endpoints da API no projeto.
   
   ## Escopo
   - Fonte: /src/api/
   - Framework: FastAPI
   - Saída: Atualização do API.md
   
   ## Instruções
   1. Listar todos os endpoints
   2. Documentar parâmetros
   3. Incluir exemplos
   4. Anotar autenticação
   ```

### Executando um Agente

#### Execução Manual
```bash
# 1. Ver agentes pendentes
ls agents/pending/

# 2. Ler instruções do agente
cat agents/pending/NOME-DO-AGENTE.md

# 3. Copiar para assistente IA e executar

# 4. Mover para executados
mv agents/pending/NOME-DO-AGENTE.md agents/executed/

# 5. Salvar relatório
echo "resultados" > agents/reports/analysis/NOME-RELATORIO.md
```

#### Execução Automatizada
```bash
# Executar automação de documentação
/srv/projects/shared/scripts/run-doc-agents.sh
```

## 📈 Métricas e KPIs

Acompanhar em `reports/analysis/metrics-YYYYMMDD.md`:

- **Cobertura:** % do código documentado
- **Atualização:** Dias desde última atualização
- **Completude:** Seções obrigatórias presentes
- **Qualidade:** Pontuação de clareza e exemplos
- **Automação:** % de tarefas automatizadas

## 🔧 Manutenção

### Diária
- Verificar `pending/` para novas tarefas
- Executar agentes prioritários

### Semanal
- Revisar tarefas `continuous/`
- Gerar relatório semanal
- Arquivar agentes executados antigos

### Mensal
- Analisar tendências
- Atualizar templates de agentes
- Otimizar tarefas contínuas

## 🔗 Integração

### Com CI/CD
```yaml
# .github/workflows/docs.yml
- name: Executar Agentes de Documentação
  run: ./scripts/run-doc-agents.sh
```

### Com Git Hooks
```bash
# .git/hooks/pre-commit
./scripts/check-docs-updated.sh
```

### Com Cron Jobs
```bash
# Diariamente às 3h
0 3 * * * /srv/projects/shared/scripts/run-doc-agents.sh
```

## 📝 Melhores Práticas

1. **Objetivos Claros** - Cada agente tem um objetivo específico
2. **Saídas Mensuráveis** - Defina critérios de sucesso
3. **Atualizações Incrementais** - Melhorias pequenas e frequentes
4. **Controle de Versão** - Rastreie todas as mudanças
5. **Revisões Regulares** - Audite eficácia dos agentes

## 🆘 Resolução de Problemas

### Agente Não Executando
- Verifique convenção de nomenclatura
- Verifique clareza das instruções
- Garanta permissões adequadas

### Relatórios Não Gerados
- Verifique caminho de saída especificado
- Verifique permissões de escrita
- Revise logs de execução

### Tarefas Contínuas Não Rodando
- Verifique configuração de agendamento
- Verifique scripts de automação
- Revise logs de erro

## 📚 Recursos Adicionais

- [Documentação Principal](../README.md)
- [Padrões Inoveon](/srv/projects/shared/docs/STANDARDS.md)
- [Guia de Automação](/srv/projects/shared/docs/agents/README.md)

---

*Este é parte do sistema automatizado de documentação da Inoveon.*  
*Template: /srv/projects/shared/scripts/docs-templates/agents-README.md*