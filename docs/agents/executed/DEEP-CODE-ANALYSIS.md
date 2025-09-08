# DEEP-CODE-ANALYSIS Agent

## MISSÃO
Realizar análise profunda e completa do código para identificar:
1. Arquivos Python duplicados ou conflitantes (app.py vs main.py)
2. Arquivos não utilizados (dead code)
3. Pastas vazias
4. Dependências não importadas
5. Imports quebrados
6. Estrutura real de uso do projeto

## ESCOPO DA ANÁLISE

### 1. Arquivos Python na Raiz
- [ ] Analisar app.py vs main.py - qual é usado?
- [ ] Identificar outros .py na raiz
- [ ] Verificar qual é o entry point real
- [ ] Detectar scripts de teste/desenvolvimento

### 2. Análise de Imports
- [ ] Mapear todos os imports do projeto
- [ ] Criar grafo de dependências
- [ ] Identificar módulos órfãos (sem imports)
- [ ] Detectar imports circulares
- [ ] Localizar imports quebrados

### 3. Análise de Uso
- [ ] Rastrear chamadas de funções
- [ ] Identificar código morto
- [ ] Detectar funções/classes não utilizadas
- [ ] Mapear fluxo de execução

### 4. Pastas e Estrutura
- [ ] Identificar pastas vazias
- [ ] Detectar pastas com apenas __init__.py
- [ ] Verificar pastas não referenciadas
- [ ] Analisar estrutura de módulos

### 5. Arquivos de Configuração
- [ ] Verificar configs duplicadas
- [ ] Identificar configs não utilizadas
- [ ] Detectar arquivos obsoletos

## METODOLOGIA DE ANÁLISE

### Fase 1: Mapeamento de Entry Points
```python
def find_entry_points():
    """Identifica pontos de entrada da aplicação"""
    entry_points = []
    
    # Verificar app.py
    if exists('app.py'):
        check_streamlit_run('app.py')
        
    # Verificar main.py
    if exists('main.py'):
        check_if_main('main.py')
        
    # Verificar scripts na raiz
    for file in glob('*.py'):
        check_executable(file)
        
    return entry_points
```

### Fase 2: Construir Grafo de Dependências
```python
def build_dependency_graph():
    """Constrói grafo completo de dependências"""
    graph = {}
    
    for file in all_python_files:
        imports = extract_imports(file)
        functions = extract_functions(file)
        classes = extract_classes(file)
        
        graph[file] = {
            'imports': imports,
            'exports': functions + classes,
            'imported_by': [],
            'calls': [],
            'called_by': []
        }
        
    return graph
```

### Fase 3: Análise de Uso Real
```python
def analyze_usage():
    """Analisa uso real de cada arquivo/módulo"""
    usage = {}
    
    # Começar pelo entry point
    entry = find_main_entry()
    
    # Traversar grafo de dependências
    visited = set()
    queue = [entry]
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
            
        visited.add(current)
        # Adicionar dependências à fila
        deps = get_dependencies(current)
        queue.extend(deps)
        
    # Marcar não visitados como não utilizados
    unused = all_files - visited
    
    return usage, unused
```

### Fase 4: Detectar Código Morto
```python
def detect_dead_code():
    """Detecta código não utilizado"""
    dead_code = {
        'files': [],
        'functions': [],
        'classes': [],
        'imports': []
    }
    
    # Arquivos sem imports
    # Funções nunca chamadas
    # Classes nunca instanciadas
    # Imports não utilizados
    
    return dead_code
```

## ANÁLISES ESPECÍFICAS

### app.py vs main.py
```python
# Verificar qual é realmente usado
- Streamlit run app.py?
- Python main.py?
- Imports entre eles?
- Funcionalidades duplicadas?
```

### Scripts na Raiz
```python
# Identificar propósito
- config.py - configuração?
- setup.py - instalação?
- performance_test.py - teste?
```

### Pastas Vazias
```bash
# Localizar e listar
find . -type d -empty
find . -type d -exec sh -c 'ls -A "$1" | wc -l | grep -q "^0$"' _ {} \;
```

## RELATÓRIO ESPERADO

```markdown
# ANÁLISE PROFUNDA DE CÓDIGO - FUELTUNE

## RESUMO EXECUTIVO
- Entry point principal: [app.py ou main.py]
- Arquivos Python na raiz: X
- Arquivos não utilizados: Y
- Pastas vazias: Z
- Código morto identificado: N linhas

## CONFLITOS IDENTIFICADOS

### app.py vs main.py
- **app.py**: [propósito, tamanho, imports]
- **main.py**: [propósito, tamanho, imports]
- **Recomendação**: [manter qual, deletar qual]

### Scripts na Raiz
1. arquivo.py - [usado/não usado] - [mover para.../deletar]
2. outro.py - [usado/não usado] - [ação]

## CÓDIGO NÃO UTILIZADO

### Arquivos Órfãos (sem imports)
- src/modulo/arquivo.py - nunca importado
- tests/old_test.py - teste obsoleto

### Funções Mortas
- função_x em arquivo.py:123 - nunca chamada
- método_y em classe.py:456 - não utilizado

### Imports Não Utilizados
- arquivo.py: import unused_module (linha 10)

## PASTAS VAZIAS
- /path/to/empty/folder1
- /path/to/empty/folder2

## ESTRUTURA DE DEPENDÊNCIAS
```
app.py (entry point)
├── src/ui/pages/dashboard.py
│   ├── src/data/database.py
│   └── src/analysis/performance.py
└── src/integration/manager.py
```

## RECOMENDAÇÕES DE LIMPEZA

### DELETAR (não utilizados)
1. main.py - duplicado com app.py
2. old_script.py - código obsoleto
3. /empty_folder/ - pasta vazia

### MOVER (mal localizados)
1. performance_test.py → tests/
2. config.py → src/config/

### REFATORAR (problemas)
1. Remover imports não utilizados
2. Deletar funções mortas
3. Limpar código comentado

## MÉTRICAS
- Arquivos analisados: X
- Linhas de código: Y
- Imports totais: Z
- Taxa de uso: N%
- Código morto: M%
```

## FERRAMENTAS DE ANÁLISE

### AST (Abstract Syntax Tree)
```python
import ast
import os

def analyze_file(filepath):
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())
    
    # Extrair imports
    imports = [node for node in ast.walk(tree) 
               if isinstance(node, (ast.Import, ast.ImportFrom))]
    
    # Extrair funções
    functions = [node for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef)]
    
    # Extrair classes
    classes = [node for node in ast.walk(tree)
               if isinstance(node, ast.ClassDef)]
    
    return {
        'imports': imports,
        'functions': functions,
        'classes': classes
    }
```

### Verificação de Uso
```python
def check_usage(name, all_files):
    """Verifica se nome é usado em algum arquivo"""
    used = False
    for file in all_files:
        with open(file, 'r') as f:
            content = f.read()
            if name in content:
                used = True
                break
    return used
```

## CHECKLIST DE VALIDAÇÃO

- [ ] Identificado entry point principal
- [ ] Mapeados todos os imports
- [ ] Construído grafo de dependências
- [ ] Detectado código não utilizado
- [ ] Identificadas pastas vazias
- [ ] Analisados conflitos app.py/main.py
- [ ] Geradas recomendações de limpeza
- [ ] Calculadas métricas de uso

## CRITÉRIOS DE DECISÃO

### Para DELETAR arquivo:
- Não é importado por nenhum outro
- Não é entry point
- Não tem testes associados
- Não é documentação

### Para MOVER arquivo:
- Está na localização errada
- Pertence a outro módulo
- É script de teste/utility

### Para MANTER arquivo:
- É usado ativamente
- É entry point
- É configuração essencial
- É documentação importante

## NOTAS IMPORTANTES

⚠️ **Este agente APENAS ANALISA, não modifica nada**
⚠️ **Verificar manualmente antes de deletar**
⚠️ **Considerar histórico git antes de remover**

## STATUS
**PENDENTE** - Aguardando execução

---
*Agente de análise profunda de código para identificar arquivos não utilizados e estrutura real*