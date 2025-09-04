# ORGANIZE-PROJECT-STRUCTURE-20240904

## Objetivo
Reorganizar completamente a estrutura do projeto fueltune-streamlit seguindo os padrões estabelecidos de documentação e organização de código.

## Escopo
- **Diretório Base:** /home/lee/projects/fueltune-streamlit/
- **Ação:** Reorganização completa e limpeza
- **Prioridade:** ALTA
- **Tempo Estimado:** 30 minutos

## Contexto
O projeto possui múltiplos arquivos desorganizados na raiz, documentação dispersa, scripts misturados e arquivos duplicados/temporários que precisam ser limpos e organizados adequadamente.

## 📚 Padrões de Código Obrigatórios
Este agente segue RIGOROSAMENTE os padrões definidos em:
- **`/docs/PYTHON-CODE-STANDARDS.md`**
- Seções específicas aplicáveis:
  - [Professional UI Standards] - Interface sem emojis
  - [CSS Adaptativo] - Temas claro/escuro  
  - [Type Hints] - Type safety completo
  - [Error Handling] - Tratamento robusto
  - [Documentation Standards] - Documentação profissional

### Requisitos Específicos:
- ❌ ZERO emojis na interface (usar Material Icons)
- ❌ ZERO cores hardcoded (#ffffff, #000000)
- ❌ ZERO uso de !important no CSS
- ✅ Variáveis CSS adaptativas obrigatórias
- ✅ Type hints 100% coverage
- ✅ Docstrings Google Style
- ✅ Estrutura de projeto padronizada
- ✅ Organização clara de arquivos e pastas

## Instruções Detalhadas

### FASE 1: ANÁLISE E BACKUP

1. **Criar backup de segurança**
   ```bash
   # Criar timestamp para backup
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   
   # Criar lista de arquivos importantes antes da reorganização
   find . -maxdepth 1 -type f -name "*.md" > /tmp/backup_list_${TIMESTAMP}.txt
   find . -maxdepth 1 -type f -name "*.py" >> /tmp/backup_list_${TIMESTAMP}.txt
   ```

2. **Documentar estado inicial**
   - Contar total de arquivos na raiz
   - Listar todos os arquivos .md dispersos
   - Identificar arquivos duplicados

### FASE 2: ORGANIZAÇÃO DE DOCUMENTAÇÃO

1. **Mover documentos principais para /docs**
   ```bash
   # Documentos padrão que devem ir para /docs
   mv AUTHORS.md docs/
   mv CONTRIBUTING.md docs/
   mv SECURITY.md docs/
   
   # Documentos de release/versão
   mv RELEASE_NOTES_v1.0.0.md docs/
   
   # Documentos de agentes (mover para subpasta específica)
   mkdir -p docs/agents-docs
   mv MASTER-AGENT-STREAMLIT.md docs/agents-docs/
   mv QA-AGENT-PYTHON.md docs/agents-docs/
   
   # Documentos de projeto
   mv PROJETO_COMPLETO_SUMMARY.md docs/
   ```

2. **Manter na raiz apenas**
   - README.md (principal do projeto)
   - LICENSE
   - CHANGELOG.md (pode ficar na raiz ou docs - verificar preferência)

### FASE 3: ORGANIZAÇÃO DE SCRIPTS

1. **Scripts temporários e de teste**
   ```bash
   # Criar pasta para scripts temporários
   mkdir -p scripts/temp
   
   # Mover scripts de teste
   mv test_professional_theme.py scripts/temp/
   
   # Mover backups de código
   mv app_backup_sidebar.py scripts/temp/
   ```

2. **Scripts principais (já organizados)**
   - Verificar se todos em /scripts estão corretos
   - Documentar propósito de cada script

### FASE 4: LIMPEZA DE ARQUIVOS

1. **Remover duplicatas e arquivos desnecessários**
   ```bash
   # Remover pasta agents duplicada da raiz
   rm -rf agents/
   
   # Remover arquivos de banco de dados de teste
   rm -f test.db
   rm -f ":memory:"
   rm -f fueltech_data.db
   
   # Remover pasta com nome inválido
   rm -rf "invalid:"
   
   # Remover arquivo de versão errado
   rm -f "=1.3.0"
   ```

2. **Verificar e limpar cache**
   ```bash
   # Limpar cache se desnecessário
   # Verificar primeiro o conteúdo
   ls -la cache/
   # Se for apenas cache temporário, limpar
   rm -rf cache/*
   ```

### FASE 5: ORGANIZAÇÃO DE CONFIGURAÇÕES

1. **Arquivos de configuração**
   ```bash
   # Criar pasta de configurações se necessário
   mkdir -p config
   
   # Verificar se config.py deve ir para config/ ou src/
   # (manter na raiz se for configuração principal do app)
   ```

2. **Arquivos de ambiente e CI/CD**
   - .env.example (manter na raiz)
   - .gitignore (manter na raiz)
   - .coveragerc (manter na raiz)
   - .dockerignore (manter na raiz)
   - .pre-commit-config.yaml (manter na raiz)

### FASE 6: ORGANIZAÇÃO DE TESTES

1. **Consolidar arquivos de teste**
   ```bash
   # Mover configurações de teste se necessário
   # pytest.ini já está na raiz (OK)
   # tox.ini já está na raiz (OK)
   ```

2. **Limpar resultados de teste antigos**
   ```bash
   # Remover JSONs de pylint antigos se não forem mais necessários
   mkdir -p docs/qa-reports
   mv pylint_results.json docs/qa-reports/
   mv pylint_revalidation.json docs/qa-reports/
   ```

### FASE 7: LIMPEZA DE PASTAS EM /docs

1. **Remover ou reorganizar pastas não padrão**
   ```bash
   # Em /docs, verificar e reorganizar:
   # - dev/ e dev-guide/ (consolidar em uma só)
   # - user/ e user-guide/ (consolidar em uma só)
   # - executed/ (mover para agents/executed se for de agentes)
   
   # Consolidar guias de desenvolvimento
   mv docs/dev/* docs/dev-guide/ 2>/dev/null || true
   rmdir docs/dev 2>/dev/null || true
   
   # Consolidar guias de usuário
   mv docs/user/* docs/user-guide/ 2>/dev/null || true
   rmdir docs/user 2>/dev/null || true
   
   # Mover executed se for de agentes
   mv docs/executed docs/agents/ 2>/dev/null || true
   ```

### FASE 8: VALIDAÇÃO FINAL

1. **Verificar estrutura final**
   ```bash
   # Estrutura esperada na raiz:
   # - README.md
   # - LICENSE  
   # - CHANGELOG.md
   # - setup.py
   # - Makefile
   # - requirements*.txt
   # - pyproject.toml
   # - Configurações (.*rc, .env.example, etc)
   # - Pastas organizadas: app/, src/, docs/, scripts/, tests/, etc.
   ```

2. **Gerar relatório de reorganização**
   ```bash
   # Contar arquivos finais na raiz
   ls -la | wc -l
   
   # Verificar se todos os .md foram organizados
   find . -maxdepth 1 -name "*.md" -type f
   
   # Verificar estrutura de docs/
   tree docs/ -L 2
   ```

## Critérios de Sucesso

- [ ] Raiz do projeto com no máximo 15-20 arquivos
- [ ] Todos os documentos .md organizados em /docs (exceto README.md, LICENSE, CHANGELOG.md)
- [ ] Pasta /agents da raiz removida
- [ ] Scripts de teste/temporários em scripts/temp
- [ ] Arquivos duplicados e desnecessários removidos
- [ ] Estrutura /docs limpa e organizada
- [ ] Relatórios de QA movidos para local apropriado
- [ ] Nenhum arquivo de banco de dados de teste na raiz

## Saída Esperada

### Relatório de Execução
Salvar em: `docs/agents/reports/analysis/project-reorganization-20240904.md`

O relatório deve conter:
1. Lista de arquivos movidos (origem → destino)
2. Lista de arquivos removidos
3. Estatísticas antes/depois
4. Problemas encontrados
5. Recomendações adicionais

### Estrutura Final Esperada
```
fueltune-streamlit/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── setup.py
├── Makefile
├── app.py
├── config.py
├── requirements*.txt
├── pyproject.toml
├── .gitignore
├── .env.example
├── .*rc (configurações)
├── app/
├── src/
├── docs/
│   ├── README.md
│   ├── AUTHORS.md
│   ├── CONTRIBUTING.md
│   ├── SECURITY.md
│   ├── RELEASE_NOTES_v1.0.0.md
│   ├── agents/
│   ├── agents-docs/
│   ├── api/
│   ├── dev-guide/
│   ├── user-guide/
│   └── qa-reports/
├── scripts/
│   ├── temp/
│   └── [scripts existentes]
├── tests/
├── data/
├── static/
├── infrastructure/
├── k8s/
├── monitoring/
└── venv/
```

## Notas Importantes

1. **SEMPRE fazer backup antes de mover/remover arquivos importantes**
2. **Verificar dependências antes de mover arquivos Python**
3. **Não mover arquivos que possam quebrar imports ou paths**
4. **Documentar TODAS as mudanças realizadas**
5. **Se houver dúvida sobre um arquivo, consultar antes de mover**

## Comandos de Rollback (se necessário)

```bash
# Se algo der errado, usar o backup_list para restaurar
# Verificar git status para reverter mudanças se necessário
git status
git checkout -- [arquivo]
```

---

**Agente criado em:** 2024-09-04  
**Autor:** Sistema de Agentes Automatizados  
**Versão do Template:** 1.0