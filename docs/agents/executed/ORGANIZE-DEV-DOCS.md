# ORGANIZE-DEV-DOCS-20240904

## Objetivo
Eliminar a pasta `/docs/dev/` movendo todos os arquivos diretamente para `/docs/`, fazendo merge de duplicados e movendo documentos de agentes para `/docs/agents/`.

## Escopo
- **Diretório Alvo:** /home/lee/projects/fueltune-streamlit/docs/dev/
- **Ação:** Mover tudo para /docs/, merge de duplicados, eliminar pasta dev/
- **Prioridade:** ALTA
- **Tempo Estimado:** 15 minutos

## Contexto
A pasta `/docs/dev/` NÃO deve existir. Todo conteúdo deve estar diretamente em `/docs/` ou em `/docs/agents/` se for relacionado a agentes.

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
- ✅ Organização clara de documentação
- ✅ Estrutura de pastas padronizada

### Arquivos Identificados em /docs/dev/:
1. `ARCHITECTURE.md` - 1038 linhas (DUPLICADO - merge necessário com /docs/ARCHITECTURE.md de 5 linhas)
2. `DATA-DICTIONARY-COMPLETE.md` - Mover para /docs/
3. `DATA-DICTIONARY-REAL.md` - Mover para /docs/
4. `PROJECT-OVERVIEW.md` - Mover para /docs/
5. `PYTHON-CODE-STANDARDS.md` - Verificar se é de agente ou mover para /docs/
6. `TECHNICAL-SPEC-PYTHON.md` - Verificar se é de agente ou mover para /docs/

## Instruções Detalhadas

### FASE 1: ANÁLISE E BACKUP

1. **Criar backup dos arquivos atuais**
   ```bash
   # Criar timestamp
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   
   # Criar diretório de backup
   mkdir -p /tmp/docs_dev_backup_${TIMESTAMP}
   
   # Copiar arquivos para backup
   cp -r /home/lee/projects/fueltune-streamlit/docs/dev/* /tmp/docs_dev_backup_${TIMESTAMP}/
   cp /home/lee/projects/fueltune-streamlit/docs/ARCHITECTURE.md /tmp/docs_dev_backup_${TIMESTAMP}/ARCHITECTURE_root.md
   
   echo "Backup criado em: /tmp/docs_dev_backup_${TIMESTAMP}/"
   ```

2. **Analisar conteúdo dos arquivos duplicados**
   ```bash
   # Comparar ARCHITECTURE.md
   echo "=== ARCHITECTURE.md em /docs/ ===" 
   head -20 /home/lee/projects/fueltune-streamlit/docs/ARCHITECTURE.md
   
   echo "=== ARCHITECTURE.md em /docs/dev/ ==="
   head -20 /home/lee/projects/fueltune-streamlit/docs/dev/ARCHITECTURE.md
   ```

### FASE 2: IDENTIFICAR DOCUMENTOS DE AGENTES

1. **Verificar se são documentos de agentes**
   ```bash
   # Verificar PYTHON-CODE-STANDARDS.md
   head -50 /home/lee/projects/fueltune-streamlit/docs/dev/PYTHON-CODE-STANDARDS.md | grep -i "agent\|agente"
   
   # Verificar TECHNICAL-SPEC-PYTHON.md  
   head -50 /home/lee/projects/fueltune-streamlit/docs/dev/TECHNICAL-SPEC-PYTHON.md | grep -i "agent\|agente"
   
   # Se contiverem referências a agentes, mover para /docs/agents/documentation/
   # Caso contrário, mover para /docs/
   ```

### FASE 3: MERGE DE ARQUIVO DUPLICADO

1. **ARCHITECTURE.md**
   ```bash
   # O arquivo em /docs/dev/ é muito mais completo (1038 linhas vs 5 linhas)
   # Substituir o arquivo placeholder pelo completo
   
   # Remover arquivo placeholder
   rm /home/lee/projects/fueltune-streamlit/docs/ARCHITECTURE.md
   
   # Mover o arquivo completo para docs/
   mv /home/lee/projects/fueltune-streamlit/docs/dev/ARCHITECTURE.md \
      /home/lee/projects/fueltune-streamlit/docs/ARCHITECTURE.md
   
   echo "ARCHITECTURE.md consolidado (versão completa preservada)"
   ```

### FASE 4: MOVER TODOS OS ARQUIVOS PARA /docs/

1. **Mover arquivos restantes**
   ```bash
   # Mover dicionários de dados
   mv /home/lee/projects/fueltune-streamlit/docs/dev/DATA-DICTIONARY-COMPLETE.md \
      /home/lee/projects/fueltune-streamlit/docs/DATA-DICTIONARY-COMPLETE.md
      
   mv /home/lee/projects/fueltune-streamlit/docs/dev/DATA-DICTIONARY-REAL.md \
      /home/lee/projects/fueltune-streamlit/docs/DATA-DICTIONARY-REAL.md
   
   # Mover visão geral do projeto
   mv /home/lee/projects/fueltune-streamlit/docs/dev/PROJECT-OVERVIEW.md \
      /home/lee/projects/fueltune-streamlit/docs/PROJECT-OVERVIEW.md
   
   # Mover padrões e especificações (se não forem de agentes)
   # Se PYTHON-CODE-STANDARDS.md não for de agente:
   mv /home/lee/projects/fueltune-streamlit/docs/dev/PYTHON-CODE-STANDARDS.md \
      /home/lee/projects/fueltune-streamlit/docs/PYTHON-CODE-STANDARDS.md
   
   # Se TECHNICAL-SPEC-PYTHON.md não for de agente:
   mv /home/lee/projects/fueltune-streamlit/docs/dev/TECHNICAL-SPEC-PYTHON.md \
      /home/lee/projects/fueltune-streamlit/docs/TECHNICAL-SPEC-PYTHON.md
   
   # OU se forem de agentes, mover para agents/documentation/:
   # mv /home/lee/projects/fueltune-streamlit/docs/dev/PYTHON-CODE-STANDARDS.md \
   #    /home/lee/projects/fueltune-streamlit/docs/agents/documentation/
   ```

### FASE 5: REMOVER PASTA DEV

1. **Remover pasta dev completamente**
   ```bash
   # Verificar se está vazia
   ls -la /home/lee/projects/fueltune-streamlit/docs/dev/
   
   # Remover pasta dev (deve estar vazia)
   rmdir /home/lee/projects/fueltune-streamlit/docs/dev/
   
   # Confirmar remoção
   echo "Pasta dev/ removida com sucesso"
   ```

### FASE 6: VALIDAÇÃO E RELATÓRIO

1. **Validar nova estrutura**
   ```bash
   echo "=== Nova Estrutura de /docs (apenas pastas) ==="
   find /home/lee/projects/fueltune-streamlit/docs -type d -maxdepth 1 | sort
   
   echo -e "\n=== Arquivos .md em /docs/ ==="
   ls -1 /home/lee/projects/fueltune-streamlit/docs/*.md | xargs basename -a | sort
   
   echo -e "\n=== Verificar que dev/ não existe mais ==="
   ls -la /home/lee/projects/fueltune-streamlit/docs/ | grep "^d" | grep -v "\."
   ```

2. **Gerar relatório de reorganização**
   ```bash
   REPORT_FILE="/home/lee/projects/fueltune-streamlit/docs/agents/reports/analysis/dev-docs-reorganization-20240904.md"
   
   cat > $REPORT_FILE << 'EOF'
# Relatório de Reorganização - Documentação de Desenvolvimento
**Data:** 04 de Setembro de 2024
**Agente:** ORGANIZE-DEV-DOCS-20240904

## Resumo Executivo
Eliminação completa da pasta `/docs/dev/` movendo todos os arquivos diretamente para `/docs/` e fazendo merge de duplicados.

## Ações Realizadas

### 1. Merge de Arquivo Duplicado
- `ARCHITECTURE.md`: Versão completa (1038 linhas) substituiu versão placeholder (5 linhas)

### 2. Arquivos Movidos para /docs/
- `DATA-DICTIONARY-COMPLETE.md` - Dicionário de dados completo
- `DATA-DICTIONARY-REAL.md` - Dicionário de dados real
- `PROJECT-OVERVIEW.md` - Visão geral do projeto
- `PYTHON-CODE-STANDARDS.md` - Padrões de código (ou /docs/agents/documentation/ se for de agente)
- `TECHNICAL-SPEC-PYTHON.md` - Especificação técnica (ou /docs/agents/documentation/ se for de agente)

### 3. Limpeza
- Pasta `/docs/dev/` COMPLETAMENTE REMOVIDA

## Estrutura Final

```
docs/
├── agents/           # Sistema de agentes
│   └── documentation/  # Documentação de agentes
├── qa-reports/       # Relatórios de qualidade
├── user/            # Documentação do usuário
├── ARCHITECTURE.md  # Arquitetura completa (merge feito)
├── DATA-DICTIONARY-COMPLETE.md
├── DATA-DICTIONARY-REAL.md
├── PROJECT-OVERVIEW.md
├── PYTHON-CODE-STANDARDS.md
├── TECHNICAL-SPEC-PYTHON.md
└── [outros .md existentes]
```

Nota: Pasta dev/ NÃO EXISTE MAIS!

## Benefícios

1. **Eliminação de duplicatas** - ARCHITECTURE.md consolidado
2. **Melhor organização** - Documentos agrupados por tipo
3. **Navegação facilitada** - Estrutura mais intuitiva
4. **Índices criados** - READMEs nas novas pastas

## Backup

Backup completo criado em: `/tmp/docs_dev_backup_[TIMESTAMP]/`

---
*Reorganização concluída com sucesso*
EOF
   
   echo "Relatório gerado em: $REPORT_FILE"
   ```

## Critérios de Sucesso

- [ ] Pasta `/docs/dev/` COMPLETAMENTE REMOVIDA
- [ ] ARCHITECTURE.md consolidado (versão completa de 1038 linhas preservada)
- [ ] Todos os arquivos movidos diretamente para `/docs/`
- [ ] Documentos de agentes (se houver) movidos para `/docs/agents/documentation/`
- [ ] Nenhuma perda de documentação
- [ ] Estrutura simplificada sem criar novas pastas
- [ ] Relatório de reorganização gerado

## Notas Importantes

1. **Backup obrigatório** antes de qualquer operação
2. **Verificar conteúdo** antes de substituir arquivos
3. **Preservar versão mais completa** em caso de duplicatas
4. **Criar índices** (README.md) nas novas pastas
5. **Documentar todas as mudanças** no relatório

## Rollback (se necessário)

```bash
# Em caso de problemas, restaurar do backup
TIMESTAMP="[inserir_timestamp_do_backup]"
cp -r /tmp/docs_dev_backup_${TIMESTAMP}/* /home/lee/projects/fueltune-streamlit/docs/dev/
```

---

**Agente criado em:** 2024-09-04  
**Autor:** Sistema de Agentes Automatizados  
**Versão:** 1.0