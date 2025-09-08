# IMPLEMENT-MAP-EDITOR

## Objetivo
Implementar editor completo de mapas 2D/3D para tabelas de tunagem (fuel, ignition, boost)

## Escopo
- Editor de tabelas interativo com AG-Grid
- Visualização 3D com Plotly
- Operações de suavização e interpolação
- Sistema de versionamento (snapshots)
- Integração com FTManager via clipboard

## 📚 Padrões de Código Obrigatórios
Este agente segue RIGOROSAMENTE os padrões definidos em:
- **`/docs/PYTHON-CODE-STANDARDS.md`**
- Seções específicas aplicáveis:
  - [Professional UI Standards] - Interface sem emojis
  - [CSS Adaptativo] - Temas claro/escuro  
  - [Type Hints] - Type safety completo
  - [Error Handling] - Tratamento robusto
  - [Performance] - Otimização obrigatória
  - [Streamlit Best Practices] - Componentes profissionais

### Requisitos Específicos:
- ❌ ZERO emojis na interface (usar Material Icons)
- ❌ ZERO cores hardcoded (#ffffff, #000000)
- ❌ ZERO uso de !important no CSS
- ✅ Variáveis CSS adaptativas obrigatórias
- ✅ Type hints 100% coverage
- ✅ Docstrings Google Style
- ✅ Performance < 100ms para operações
- ✅ Plotly com temas adaptativos
- ✅ AG-Grid com styling profissional

## Prioridade: CRÍTICA MÁXIMA
## Tempo Estimado: 2-3 semanas
## Complexidade: Alta

## Tarefas

### Semana 1: Editor 2D Básico
1. Implementar grid editável com st-aggrid
2. Adicionar validação de valores
3. Implementar copy/paste de células
4. Criar operações básicas (increment/decrement)
5. Adicionar undo/redo

### Semana 2: Visualização 3D e Algoritmos
1. Implementar visualização 3D com Plotly
2. Adicionar algoritmo de suavização Gaussian
3. Implementar interpolação linear/cubic
4. Criar preview de mudanças
5. Adicionar heatmap overlay

### Semana 3: Integração e Polish
1. Implementar sistema de snapshots
2. Adicionar integração FTManager
3. Criar comparação A/B de mapas
4. Implementar atalhos de teclado
5. Testes e otimização

## Arquivos a Criar/Modificar

```
src/
├── maps/
│   ├── __init__.py
│   ├── editor.py          # Editor principal
│   ├── operations.py      # Operações de edição
│   ├── algorithms.py      # Suavização/Interpolação
│   ├── visualization.py   # Visualização 3D
│   ├── snapshots.py       # Versionamento
│   └── ftmanager.py       # Bridge FTManager
```

## Dependências
- streamlit-aggrid>=0.3.4
- plotly>=5.0
- scipy>=1.9 (para algoritmos)
- pyperclip>=1.8

## Critérios de Aceitação
- [ ] Editor permite edição célula por célula
- [ ] Visualização 3D rotacionável
- [ ] Suavização não distorce valores extremos
- [ ] Copy/paste compatível com FTManager
- [ ] Snapshots salvos no banco
- [ ] Performance < 100ms para operações

## Riscos
- AG-Grid pode ter limitações para grids grandes
- Performance da visualização 3D com muitos pontos
- Compatibilidade clipboard entre navegadores

---
*Agente crítico para funcionalidade core do sistema*