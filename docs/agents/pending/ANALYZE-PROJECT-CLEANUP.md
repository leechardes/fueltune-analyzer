# ANALYZE-PROJECT-CLEANUP Agent

## MISSÃO
Realizar análise profunda e completa da estrutura do projeto FuelTune Analyzer para identificar arquivos obsoletos, estruturas fora do padrão, redundâncias e oportunidades de limpeza e organização.

## ESCOPO DA ANÁLISE

### 1. Estrutura de Diretórios
- [ ] Verificar hierarquia de pastas
- [ ] Identificar pastas vazias
- [ ] Detectar pastas duplicadas ou redundantes
- [ ] Analisar consistência da estrutura
- [ ] Verificar pasta `/pages` na raiz vs `/src/ui/pages`

### 2. Arquivos na Raiz
- [ ] Listar todos os arquivos na raiz
- [ ] Identificar quais deveriam estar em subpastas
- [ ] Detectar arquivos temporários
- [ ] Verificar arquivos de configuração duplicados
- [ ] Scripts soltos que deveriam estar em `/scripts`

### 3. Bancos de Dados
- [ ] Localizar todos os arquivos `.db`, `.sqlite`, `.sql`
- [ ] Verificar se estão na pasta `/data`
- [ ] Identificar bancos temporários ou de teste
- [ ] Detectar bancos duplicados

### 4. Scripts e Utilitários
- [ ] Mapear todos os scripts `.sh`, `.py` fora de `/scripts`
- [ ] Identificar scripts obsoletos ou não utilizados
- [ ] Detectar scripts duplicados
- [ ] Scripts de teste que deveriam estar em `/tests`

### 5. Arquivos Temporários e Cache
- [ ] Buscar arquivos `.tmp`, `.temp`, `.backup`, `.bak`
- [ ] Identificar logs antigos
- [ ] Detectar arquivos de cache obsoletos
- [ ] Localizar arquivos gerados por IDEs

### 6. Documentação
- [ ] Verificar documentos duplicados
- [ ] Identificar docs obsoletos
- [ ] Detectar READMEs duplicados
- [ ] Analisar estrutura de `/docs`

### 7. Código Fonte
- [ ] Verificar estrutura de `/src`
- [ ] Identificar módulos não utilizados
- [ ] Detectar imports quebrados
- [ ] Localizar arquivos Python fora da estrutura padrão

### 8. Testes
- [ ] Verificar estrutura de `/tests`
- [ ] Identificar testes obsoletos
- [ ] Detectar fixtures não utilizadas

### 9. Configurações
- [ ] Mapear todos os arquivos de configuração
- [ ] Identificar configs duplicadas
- [ ] Verificar `.env` files
- [ ] Analisar arquivos de ambiente

### 10. Assets e Recursos
- [ ] Verificar pasta `/static`
- [ ] Identificar recursos não utilizados
- [ ] Detectar imagens/CSS/JS obsoletos

## CRITÉRIOS DE ANÁLISE

### Padrões Esperados
```
fueltune-streamlit/
├── src/                    # Código fonte principal
│   ├── analysis/          # Módulos de análise
│   ├── data/             # Processamento de dados
│   ├── integration/      # Integrações
│   ├── maps/            # Editor de mapas
│   ├── performance/     # Otimização
│   ├── ui/              # Interface
│   └── utils/           # Utilitários
├── tests/                 # Testes
├── docs/                  # Documentação
├── scripts/               # Scripts utilitários
├── data/                  # Bancos de dados
├── static/                # Assets estáticos
├── config/                # Configurações
└── [arquivos config raiz] # Apenas configs principais
```

### Flags de Problemas
- 🔴 **CRÍTICO**: Arquivos que quebram o sistema
- 🟡 **IMPORTANTE**: Estrutura fora do padrão
- 🟢 **SUGESTÃO**: Melhorias de organização
- ⚪ **INFO**: Observações gerais

## ANÁLISE A EXECUTAR

### Fase 1: Mapeamento Completo
```python
def map_project_structure():
    """Mapeia toda a estrutura do projeto"""
    structure = {
        'root_files': [],
        'directories': {},
        'file_types': {},
        'duplicates': [],
        'empty_dirs': [],
        'large_files': []
    }
    return structure
```

### Fase 2: Análise de Padrões
```python
def analyze_patterns():
    """Analisa padrões e inconsistências"""
    issues = {
        'naming_violations': [],
        'structure_violations': [],
        'obsolete_files': [],
        'misplaced_files': []
    }
    return issues
```

### Fase 3: Detecção de Problemas
```python
def detect_issues():
    """Detecta problemas específicos"""
    problems = {
        'broken_imports': [],
        'unused_modules': [],
        'duplicate_functionality': [],
        'temp_files': []
    }
    return problems
```

### Fase 4: Geração de Relatório
```python
def generate_report():
    """Gera relatório detalhado"""
    report = {
        'summary': {},
        'critical_issues': [],
        'recommendations': [],
        'action_plan': []
    }
    return report
```

## FORMATO DO RELATÓRIO

```markdown
# RELATÓRIO DE ANÁLISE DE LIMPEZA DO PROJETO

## RESUMO EXECUTIVO
- Total de arquivos: X
- Total de pastas: Y
- Tamanho do projeto: Z MB
- Issues encontradas: N

## PROBLEMAS CRÍTICOS
### 🔴 Arquivos que precisam ação imediata
- arquivo.py: [razão]

## ESTRUTURA FORA DO PADRÃO
### 🟡 Elementos que violam a estrutura esperada
- /pages/: Deveria estar em /src/ui/pages

## ARQUIVOS OBSOLETOS
### Identificados como não utilizados
- script_old.py: Último uso em [data]

## RECOMENDAÇÕES DE LIMPEZA
### Ações sugeridas por prioridade
1. Mover X para Y
2. Deletar arquivo Z
3. Renomear A para B

## PLANO DE AÇÃO
### Comandos a executar (em ordem)
```bash
# 1. Mover arquivos
mv arquivo.py src/modulo/

# 2. Deletar obsoletos
rm -f arquivo_obsoleto.py

# 3. Organizar estrutura
mkdir -p src/novo_modulo
```
```

## CHECKLIST DE VALIDAÇÃO

- [ ] Todos os diretórios foram analisados
- [ ] Arquivos na raiz foram revisados
- [ ] Bancos de dados foram localizados
- [ ] Scripts foram mapeados
- [ ] Padrões foram verificados
- [ ] Duplicatas foram identificadas
- [ ] Relatório foi gerado
- [ ] Plano de ação foi criado

## EXCEÇÕES E IGNORADOS

### Não analisar:
- `.git/`
- `.venv/`, `venv/`, `env/`
- `__pycache__/`
- `*.pyc`, `*.pyo`
- `.idea/`, `.vscode/`
- `node_modules/` (se houver)

### Manter sempre:
- `README.md` (raiz)
- `requirements.txt`
- `.gitignore`
- `pyproject.toml`
- `setup.py`
- `Makefile`

## MÉTRICAS DE SUCESSO

- Zero arquivos críticos fora do lugar
- Estrutura 100% padronizada
- Sem duplicatas desnecessárias
- Sem arquivos temporários
- Documentação organizada
- Código fonte bem estruturado

## NOTAS IMPORTANTES

⚠️ **Este agente APENAS ANALISA, não modifica nada**
⚠️ **Todas as ações serão executadas por EXECUTE-PROJECT-CLEANUP**
⚠️ **Backup recomendado antes de executar limpeza**

## COMANDO DE EXECUÇÃO

```bash
# Para executar a análise
python analyze_cleanup.py

# Para gerar relatório
python analyze_cleanup.py --report > cleanup_report.md
```

## STATUS
**PENDENTE** - Aguardando execução

---
*Agente de análise para limpeza e organização do projeto FuelTune Analyzer*