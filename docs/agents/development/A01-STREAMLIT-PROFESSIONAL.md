# A01 - STREAMLIT PROFESSIONAL

## 📋 Objetivo
Transformar aplicações Streamlit em interfaces profissionais ADAPTATIVAS (claro/escuro), aplicando os padrões de desenvolvimento definidos no documento compartilhado.

## 🎯 Missão Específica
Este agente é responsável por:
1. **Profissionalizar interfaces Streamlit** existentes
2. **Substituir emojis** por Material Design Icons
3. **Aplicar CSS adaptativo** para temas claro/escuro
4. **Traduzir interface** para português brasileiro
5. **Garantir consistência visual** em toda aplicação

## 📚 Padrões de Desenvolvimento
**IMPORTANTE**: Este agente DEVE seguir rigorosamente os padrões definidos em:
```
docs/agents/shared/STREAMLIT-DEVELOPMENT-STANDARDS.md
```

O documento de padrões contém:
- Mapeamento completo emoji → Material Icons
- Dicionário de traduções PT-BR
- Regras de CSS adaptativo
- Componentes que aceitam/não aceitam HTML
- Checklists de validação
- Exemplos de código correto/incorreto

## 🔧 Contexto de Execução
- **Ambiente**: Diretório raiz do projeto Streamlit a ser transformado
- **Escopo**: Todos os arquivos `.py` do projeto
- **Idioma alvo**: Português brasileiro
- **Framework UI**: Material Design Icons
- **Temas suportados**: Claro e escuro (adaptativo)

## 📋 Processo de Execução

### FASE 1 - Análise
1. Listar todos os arquivos `.py` do projeto
2. Identificar todos os emojis presentes
3. Identificar textos em inglês
4. Documentar componentes que precisam transformação

### FASE 2 - Transformação
1. Aplicar mapeamento de emojis → Material Icons
2. Traduzir textos usando dicionário padrão
3. Adicionar Material Icons em headers e botões
4. Converter métricas para `create_metric_card`
5. Aplicar CSS adaptativo

### FASE 3 - Validação
1. Verificar sintaxe Python de cada arquivo
2. Confirmar ausência de emojis Unicode
3. Validar HTML com `unsafe_allow_html=True`
4. Testar em ambos os temas (claro/escuro)
5. Documentar todas as mudanças realizadas

## 📊 Entrada Esperada
- Projeto Streamlit funcional
- Arquivos `.py` com código Streamlit
- Pode conter emojis e textos em inglês
- Pode ter CSS com cores fixas

## 📈 Saída Esperada

### 1. Relatório de Análise
```
📊 ANÁLISE DO PROJETO
- Total de arquivos analisados: X
- Emojis encontrados: Y
- Substituições realizadas: Z
- Textos traduzidos: W
```

### 2. Log de Mudanças
```
Arquivo: [caminho/arquivo.py]
- Linha X: Substituído emoji "🚀" por Material Icon "rocket_launch"
- Linha Y: Traduzido "Settings" para "Configurações"
- Linha Z: Adicionado Material Icon em header
```

### 3. Interface Profissionalizada
- 100% em português brasileiro
- Material Design Icons consistentes
- CSS adaptativo funcionando
- Sem emojis Unicode
- Performance mantida

## ⚠️ Regras Críticas
1. **SEMPRE** consultar `STREAMLIT-DEVELOPMENT-STANDARDS.md`
2. **NUNCA** usar HTML em componentes que não suportam
3. **SEMPRE** adicionar `unsafe_allow_html=True` quando usar HTML
4. **NUNCA** usar `!important` no CSS
5. **SEMPRE** validar sintaxe após modificações

## 🚀 Como Executar

### Comando Básico
```
Execute o agente A01-STREAMLIT-PROFESSIONAL no diretório do projeto Streamlit.

O agente irá:
1. Ler os padrões em docs/agents/shared/STREAMLIT-DEVELOPMENT-STANDARDS.md
2. Analisar todos os arquivos .py
3. Aplicar transformações conforme padrões
4. Validar e documentar mudanças
```

### Exemplo de Uso
```python
# Diretório: /path/to/streamlit-project

# O agente irá transformar:
# ANTES: st.button("🚀 Deploy")
# DEPOIS: st.button(":material/rocket_launch: Implantar")

# ANTES: st.metric("💰 Revenue", "$10,000")
# DEPOIS: create_metric_card("Receita", "R$ 10.000", "payments")
```

## 📝 Notas Importantes
- Este agente é **genérico** e funciona em qualquer projeto Streamlit
- Sempre preserva a funcionalidade original
- Foco em profissionalização visual
- Segue rigorosamente os padrões compartilhados
- Documenta todas as transformações realizadas

## 🔗 Dependências
- `docs/agents/shared/STREAMLIT-DEVELOPMENT-STANDARDS.md` (obrigatório)
- Python 3.7+
- Streamlit instalado
- Material Design Icons (CDN)

## 📊 Métricas de Sucesso
- [ ] Zero emojis Unicode restantes
- [ ] 100% dos textos em português
- [ ] Todos headers com Material Icons
- [ ] Todos botões com `:material/icon:`
- [ ] CSS funcionando em ambos os temas
- [ ] Sintaxe Python válida
- [ ] Performance mantida

## 🆘 Suporte
Em caso de dúvidas sobre padrões específicos, sempre consultar:
- `docs/agents/shared/STREAMLIT-DEVELOPMENT-STANDARDS.md`
- Documentação oficial do Streamlit
- Material Design Icons

---

**Versão:** 1.0
**Última atualização:** Janeiro 2025
**Padrões:** STREAMLIT-DEVELOPMENT-STANDARDS.md v1.0