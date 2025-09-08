# UPDATE-ALL-AGENTS-WITH-STANDARDS

## Objetivo
Atualizar TODOS os agentes existentes para incluir referências explícitas ao PYTHON-CODE-STANDARDS.md, garantindo que todo desenvolvimento siga rigorosamente os padrões estabelecidos e evitando retrabalho.

## Contexto
- Sistema com apenas 35% implementado necessita padrões rígidos
- Evitar retrabalho nos 65% faltantes é CRÍTICO
- Interface DEVE ser profissional (sem emojis)
- CSS DEVE ser adaptativo (temas claro/escuro)
- Performance e qualidade são obrigatórios

## 📚 Padrões de Código Obrigatórios
Este agente segue RIGOROSAMENTE os padrões definidos em:
- **`/docs/PYTHON-CODE-STANDARDS.md`**
- Seções específicas aplicáveis:
  - [Professional UI Standards] - Interface sem emojis
  - [CSS Adaptativo] - Temas claro/escuro
  - [Type Hints] - Type safety completo
  - [Error Handling] - Tratamento robusto
  - [Performance] - Otimização obrigatória

## Escopo
1. Atualizar agentes em `/docs/agents/pending/`
2. Atualizar agentes em `/docs/agents/completed/`
3. Adicionar seção de padrões em TODOS os agentes
4. Garantir conformidade com UI profissional

## Prioridade: CRÍTICA
## Tempo Estimado: 2 horas
## Complexidade: Média

## Tarefas

### 1. Identificar Todos os Agentes
```bash
# Listar todos os agentes pendentes
find /home/lee/projects/fueltune-streamlit/docs/agents/pending -name "*.md" -type f

# Listar todos os agentes completados
find /home/lee/projects/fueltune-streamlit/docs/agents/completed -name "*.md" -type f
```

### 2. Template de Seção de Padrões

Adicionar após a seção "## Contexto" ou "## Escopo" em cada agente:

```markdown
## 📚 Padrões de Código Obrigatórios
Este agente segue RIGOROSAMENTE os padrões definidos em:
- **`/docs/PYTHON-CODE-STANDARDS.md`**
- Seções específicas aplicáveis:
  - [Professional UI Standards] - Interface sem emojis
  - [CSS Adaptativo] - Temas claro/escuro  
  - [Type Hints] - Type safety completo
  - [Error Handling] - Tratamento robusto
  - [Performance] - Otimização obrigatória

### Requisitos Específicos:
- ❌ ZERO emojis na interface (usar Material Icons)
- ❌ ZERO cores hardcoded (#ffffff, #000000)
- ❌ ZERO uso de !important no CSS
- ✅ Variáveis CSS adaptativas obrigatórias
- ✅ Type hints 100% coverage
- ✅ Docstrings Google Style
- ✅ Performance < 1s para operações típicas
```

### 3. Atualizações Específicas por Agente

#### IMPLEMENT-MAP-EDITOR.md
Adicionar:
```markdown
### Padrões Específicos do Map Editor:
- Interface com AG-Grid profissional (sem emojis)
- Material Icons para ações (save, undo, redo)
- CSS adaptativo para visualização 3D
- Performance < 100ms para operações de célula
- Clipboard compatível com FTManager
```

#### IMPLEMENT-ANALYSIS-ENGINE.md
Adicionar:
```markdown
### Padrões Específicos da Analysis Engine:
- Numpy vectorization obrigatória
- Pandas optimized dtypes
- Memory-efficient chunking
- Confidence scores 0-1 normalizados
- Interface de sugestões sem emojis
```

#### IMPLEMENT-FTMANAGER-BRIDGE.md
Adicionar:
```markdown
### Padrões Específicos do FTManager Bridge:
- Detecção robusta de formato
- Zero perda de precisão numérica
- Feedback profissional ao usuário
- Cross-platform clipboard support
- Validação completa de dimensões
```

### 4. Remover Emojis dos Próprios Agentes

Substituir emojis nos títulos e conteúdo dos agentes:
- 🚗 → [VEHICLE]
- 📊 → [CHART]
- ⚙️ → [SETTINGS]
- ✅ → [SUCCESS]
- ❌ → [ERROR]
- ⚠️ → [WARNING]
- 🔄 → [SYNC]
- 📁 → [FOLDER]

### 5. Validação de Conformidade

Para cada agente atualizado, verificar:
- [ ] Seção de padrões adicionada
- [ ] Referência ao PYTHON-CODE-STANDARDS.md
- [ ] Requisitos específicos listados
- [ ] Emojis removidos/substituídos
- [ ] Checklist de qualidade incluído

## Arquivos a Atualizar

```
docs/agents/pending/
├── IMPLEMENT-MAP-EDITOR.md
├── IMPLEMENT-ANALYSIS-ENGINE.md
├── IMPLEMENT-FTMANAGER-BRIDGE.md
├── COMPARE-AND-UPDATE-FEATURES.md
├── ORGANIZE-PROJECT-STRUCTURE.md
├── ORGANIZE-DEV-DOCS.md
└── MERGE-DUPLICATE-DOCS.md

docs/agents/executed/
└── [todos os agentes executados]
```

## Script de Automação

```python
import os
from pathlib import Path
import re

def update_agent_with_standards(file_path: Path) -> None:
    """Atualiza agente com referências aos padrões."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adicionar seção de padrões se não existir
    if "Padrões de Código Obrigatórios" not in content:
        standards_section = """
## 📚 Padrões de Código Obrigatórios
Este agente segue RIGOROSAMENTE os padrões definidos em:
- **`/docs/PYTHON-CODE-STANDARDS.md`**
- Seções específicas aplicáveis:
  - [Professional UI Standards] - Interface sem emojis
  - [CSS Adaptativo] - Temas claro/escuro
  - [Type Hints] - Type safety completo
  - [Error Handling] - Tratamento robusto
  - [Performance] - Otimização obrigatória
"""
        
        # Inserir após "## Escopo" ou "## Contexto"
        insertion_point = max(
            content.find("## Escopo"),
            content.find("## Contexto")
        )
        
        if insertion_point > 0:
            # Encontrar fim da seção
            next_section = content.find("\n## ", insertion_point + 1)
            if next_section > 0:
                content = (
                    content[:next_section] + 
                    "\n" + standards_section + 
                    content[next_section:]
                )
    
    # Salvar arquivo atualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Atualizado: {file_path.name}")

# Executar para todos os agentes
agents_dirs = [
    "/home/lee/projects/fueltune-streamlit/docs/agents/pending",
    "/home/lee/projects/fueltune-streamlit/docs/agents/executed"
]

for agents_dir in agents_dirs:
    if os.path.exists(agents_dir):
        for agent_file in Path(agents_dir).glob("*.md"):
            update_agent_with_standards(agent_file)
```

## Critérios de Aceitação
- [ ] TODOS os agentes têm seção de padrões
- [ ] TODOS referenciam PYTHON-CODE-STANDARDS.md
- [ ] Requisitos específicos por tipo de agente
- [ ] Zero emojis em interfaces (substituídos por texto/icons)
- [ ] Checklists de qualidade incluídos
- [ ] Padrões de UI profissional enforçados

## Resultado Esperado

Após execução, TODOS os agentes terão:
1. Referência clara ao PYTHON-CODE-STANDARDS.md
2. Requisitos específicos para sua área
3. Checklists de qualidade
4. Interface profissional sem emojis
5. Garantia de conformidade com padrões

## IMPORTANTE - Nomenclatura de Arquivos

**TODOS os arquivos criados devem usar MAIÚSCULAS:**
- Logs: `/docs/agents/executed/UPDATE-STANDARDS-LOG.md`
- Reports: `/docs/agents/reports/QA-REPORT-STANDARDS.md`
- NUNCA criar arquivos em minúsculas como `update-standards-log.md`

Isso garantirá que os 65% de funcionalidades faltantes sejam implementados CORRETAMENTE desde o início, evitando retrabalho.

---
*Agente crítico para garantir qualidade e consistência em TODO o desenvolvimento futuro*