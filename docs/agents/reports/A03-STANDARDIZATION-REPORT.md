# A03 - RELATÓRIO DE PADRONIZAÇÃO FUEL MAPS

## 📊 Resumo Executivo

### Situação Atual
- **fuel_maps_3d.py**: Interface robusta com 3 tabs, configuração JSON externa e sistema enable/disable para eixos
- **fuel_maps_2d.py**: Interface funcional com 3 tabs, configuração hardcoded e sistema de enable/disable parcialmente implementado

### Proposta de Padronização
Padronizar a navegação e estrutura de interface mantendo as especificidades técnicas de cada tipo de mapa, utilizando o modelo 3D como referência para a estrutura de tabs e fluxo de dados.

### Impactos Esperados
- Interface consistente entre módulos 2D e 3D
- Redução da curva de aprendizado dos usuários
- Código mais maintível e extensível
- Melhor experiência do usuário (UX)

---

## 📋 Análise Detalhada - fuel_maps_3d.py (Referência)

### ESTRUTURA DE TABS:
- **Tab 1: "Editar"**
  - Sub-tabs: "Matriz de Valores" e "Eixos"
  - Editor de matriz 32x32 com gradiente de cores
  - Configuração de eixos X (RPM) e Y (MAP) com enable/disable
  - Sistema de 32 posições para cada eixo
  - Operações: Suavizar, Aplicar Gradiente, Resetar Matriz
  - Formulário de salvar com descrição

- **Tab 2: "Visualizar"**
  - Gráfico 3D Surface com plotly
  - Gráfico de contorno 2D
  - Estatísticas da matriz (min, max, média, desvio padrão)
  - Visualização usando apenas valores ativos dos eixos

- **Tab 3: "Importar/Exportar"**
  - Seção "Copiar para FTManager" com formato TAB
  - Seção "Colar do FTManager" com parsing inteligente
  - Importação: JSON e CSV
  - Exportação: JSON e CSV
  - Validação de formatos e dimensões

### COMPONENTES DE INTERFACE:
- `st.selectbox()` para tipo de mapa
- `st.radio()` para bancada (horizontal)
- `st.metric()` para informações do mapa
- `st.data_editor()` para edição de tabelas
- `st.text_area()` para copiar/colar FTManager
- `st.plotly_chart()` para visualizações
- `st.download_button()` para exportar
- `st.file_uploader()` para importar

### SISTEMA DE CONFIGURAÇÃO:
- **Arquivo JSON externo**: `/config/map_types_3d.json`
- Configuração centralizada de tipos de mapa
- Parâmetros: name, grid_size, x_axis_type, y_axis_type, unit, min_value, max_value, description
- Sistema de fallback para valores padrão

### FLUXO DE DADOS:
1. Carregamento de configuração JSON
2. Inicialização de dados no session_state
3. Tentativa de carregamento de dados salvos
4. Criação de dados padrão se necessário
5. Edição através de data_editor
6. Validação contínua
7. Salvamento em JSON + session_state
8. Exportação em múltiplos formatos

### SISTEMA ENABLE/DISABLE:
- **RPM**: 32 posições, 24 ativas por padrão
- **MAP**: 32 posições, 21 ativas por padrão
- Sistema robusto de filtros para usar apenas posições ativas
- Compatibilidade com dados antigos sem enable/disable

---

## 📋 Análise Detalhada - fuel_maps_2d.py (Atual)

### ESTRUTURA ATUAL:
- **Tab 1: "Editar"**
  - Expander para configurar eixos com enable/disable
  - Editor horizontal de valores com gradiente de cores
  - Integração FTManager (copiar/colar)
  - Formulário de salvar com descrição

- **Tab 2: "Visualizar"**
  - Gráfico 2D com linha e markers coloridos
  - Estatísticas básicas (min, max, média)

- **Tab 3: "Importar/Exportar"**
  - Importação: JSON e CSV
  - Exportação: JSON e CSV
  - Sem seção dedicada para FTManager

### CONFIGURAÇÃO ATUAL:
- **Dicionário hardcoded**: `MAP_TYPES_2D` no código
- 6 tipos diferentes de mapas 2D
- Parâmetros: name, positions, axis_type, unit, min_value, max_value, description
- Sem sistema de fallback centralizado

### FUNCIONALIDADES ÚNICAS:
- Suporte a múltiplos tamanhos de mapa (8, 9, 16, 20, 32 posições)
- Sistema de enable/disable em expander
- Editor horizontal com gradiente visual
- Tipos específicos: TPS, TEMP, AIR_TEMP, VOLTAGE
- Copiar/colar FTManager com JavaScript nativo

### DIFERENÇAS NA MANIPULAÇÃO:
- **Dados lineares**: Array unidimensional vs matriz 2D
- **Visualização horizontal**: Tabela horizontal vs editor de matriz
- **Eixos variáveis**: Diferentes quantidades de posições por tipo
- **Sem sub-tabs**: Estrutura mais plana na aba Editar

---

## 📊 Tabela Comparativa Completa

| Funcionalidade | 3D (Referência) | 2D (Atual) | 2D (Proposto) | Observações |
|----------------|-----------------|------------|---------------|-------------|
| **ESTRUTURA DE NAVEGAÇÃO** |
| Quantidade de tabs | 3 tabs | 3 tabs | 3 tabs | ✅ Já padronizado |
| Nomes das tabs | Editar, Visualizar, Importar/Exportar | Editar, Visualizar, Importar/Exportar | Manter igual | ✅ Já consistente |
| Sub-tabs na aba Editar | "Matriz de Valores", "Eixos" | Sem sub-tabs | Adicionar "Valores", "Eixos" | 🔄 Padronizar estrutura |
| **CONFIGURAÇÃO DE TIPOS** |
| Sistema de config | JSON externo | Hardcoded | Híbrido (JSON + fallback) | 🔄 Migrar para JSON |
| Arquivo de config | `map_types_3d.json` | Não tem | `map_types_2d.json` | ➕ Criar arquivo |
| Fallback | Sim | Sim | Sim | ✅ Manter |
| **SISTEMA DE EIXOS** |
| Enable/disable | Completo | Parcial | Completo | 🔄 Melhorar implementação |
| Editor de eixos | Tab dedicada | Expander | Tab dedicada | 🔄 Mover para tab |
| Posições fixas | 32x32 | Variável | Manter variável | ✅ Preservar flexibilidade |
| **EDIÇÃO DE VALORES** |
| Tipo de editor | Matriz 2D | Linha horizontal | Manter horizontal | ✅ Adequado para 2D |
| Gradiente visual | Sim | Sim | Sim | ✅ Já implementado |
| Formatação | 3 casas decimais | 3 casas decimais | 3 casas decimais | ✅ Já padronizado |
| **INTEGRAÇÃO FTMANAGER** |
| Localização | Tab dedicada | Inline na edição | Tab dedicada | 🔄 Mover para tab Importar/Exportar |
| Formato | TAB separado | TAB separado | TAB separado | ✅ Já consistente |
| Copiar/colar | Completo | Completo | Completo | ✅ Já implementado |
| **VISUALIZAÇÃO** |
| Tipo de gráfico | 3D Surface + Contorno | 2D Linha + Markers | Manter 2D | ✅ Adequado para dados |
| Estatísticas | 4 métricas | 3 métricas | 4 métricas | ➕ Adicionar desvio padrão |
| **IMPORT/EXPORT** |
| Formatos | JSON, CSV | JSON, CSV | JSON, CSV | ✅ Já consistente |
| Validação | Completa | Completa | Completa | ✅ Já implementado |
| Metadados | Completos | Completos | Completos | ✅ Já consistente |

---

## 🎯 Recomendações Específicas de Implementação

### 1. REESTRUTURAÇÃO DE TABS (Prioridade Alta)
```
Tab "Editar":
├── Sub-tab "Valores" (atual editor horizontal)
└── Sub-tab "Eixos" (mover do expander atual)

Tab "Visualizar": (manter atual)

Tab "Importar/Exportar":
├── Seção "Copiar para FTManager" (mover da aba Editar)
├── Seção "Colar do FTManager" (mover da aba Editar)  
├── Seção "Importar Dados" (manter atual)
└── Seção "Exportar Dados" (manter atual)
```

### 2. SISTEMA DE CONFIGURAÇÃO (Prioridade Média)
```json
// Criar: /config/map_types_2d.json
{
  "main_fuel_2d_map_32": {
    "name": "Mapa Principal de Injeção (MAP) - 32 posições",
    "positions": 32,
    "axis_type": "MAP", 
    "unit": "ms",
    "min_value": 0.0,
    "max_value": 50.0,
    "description": "Mapa principal baseado na pressão MAP",
    "default_enabled_count": 21
  }
  // ... outros tipos
}
```

### 3. MELHORIAS NO SISTEMA ENABLE/DISABLE (Prioridade Média)
- Mover editor de eixos para sub-tab dedicada
- Implementar lógica de posições ativas mais robusta
- Adicionar botão "Aplicar Valores Ativos" na tab de eixos
- Compatibilidade com dados salvos antigos

### 4. PADRONIZAÇÃO DE ESTATÍSTICAS (Prioridade Baixa)
- Adicionar métrica "Desvio Padrão" na visualização
- Usar mesmo formato de exibição (3 casas decimais)
- Manter layout em 4 colunas igual ao 3D

### 5. ORGANIZAÇÃO DO CÓDIGO (Prioridade Baixa)
- Extrair função `load_map_types_config()` para arquivo comum
- Padronizar nomes de variáveis entre arquivos
- Unificar sistema de session_keys
- Comentários consistentes

---

## 📋 Plano de Implementação

### **FASE 1**: Reestruturação de Interface (1-2 dias)
1. ✅ Analisar estrutura atual completa
2. 🔄 Criar sub-tabs na aba "Editar"
   - Mover editor de valores para sub-tab "Valores"  
   - Mover configuração de eixos para sub-tab "Eixos"
3. 🔄 Reorganizar aba "Importar/Exportar"
   - Mover seções FTManager da aba "Editar"
   - Reorganizar layout das seções
4. ✅ Testar navegação e funcionalidades

### **FASE 2**: Sistema de Configuração (1 dia)
1. 🔄 Criar arquivo `/config/map_types_2d.json`
2. 🔄 Implementar função `load_map_types_config()`
3. 🔄 Migrar dicionário hardcoded para JSON
4. 🔄 Implementar sistema de fallback
5. ✅ Testar compatibilidade com dados existentes

### **FASE 3**: Refinamentos e Testes (1 dia)
1. 🔄 Adicionar métrica "Desvio Padrão"
2. 🔄 Melhorar sistema enable/disable
3. 🔄 Padronizar comentários e variáveis
4. ✅ Testes extensivos de todas as funcionalidades
5. ✅ Verificar compatibilidade com dados salvos

---

## ❓ Questões para Decisão

### 🔍 **CRÍTICAS** (Necessitam decisão antes da implementação):

- **[DECIDIR]** Sistema de Configuração:
  - ❓ Migrar completamente para JSON ou manter híbrido?
  - ❓ Criar arquivo único `map_types.json` ou separar 2d/3d?
  - **Recomendação**: Manter separado para facilitar manutenção

- **[DECIDIR]** Compatibilidade com dados existentes:
  - ❓ Como tratar mapas salvos sem enable/disable?
  - ❓ Migração automática ou manual?
  - **Recomendação**: Migração automática com fallback

### 🔍 **IMPORTANTES** (Podem ser decididas durante implementação):

- **[DECIDIR]** Layout da aba FTManager:
  - ❓ Manter copiar/colar lado a lado ou empilhado?
  - **Recomendação**: Manter lado a lado (mais compacto)

- **[DECIDIR]** Nomes das sub-tabs:
  - ❓ "Valores"/"Eixos" ou "Matriz de Valores"/"Configurar Eixos"?
  - **Recomendação**: Nomes curtos ("Valores"/"Eixos")

### 🔍 **OPCIONAIS** (Podem ficar para versão futura):

- **[AVALIAR]** Unificação de funções comuns:
  - ❓ Criar módulo compartilhado para funções iguais?
  - **Recomendação**: Sim, mas em versão futura

- **[AVALIAR]** Melhorias visuais:
  - ❓ Adicionar ícones nas tabs igual ao 3D?
  - **Recomendação**: Sim, seguir padrão 3D

---

## 🎯 Métricas de Sucesso

### ✅ **INTERFACE CONSISTENTE**
- [ ] Mesma estrutura de tabs (3 tabs)
- [ ] Sub-tabs na aba "Editar" 
- [ ] FTManager na aba "Importar/Exportar"
- [ ] Layout e componentes similares

### ✅ **FUNCIONALIDADES PRESERVADAS**
- [ ] Todos os tipos de mapa 2D funcionando
- [ ] Sistema enable/disable operacional
- [ ] Copiar/colar FTManager funcionando
- [ ] Import/export em JSON e CSV

### ✅ **CÓDIGO MAIS MAINTÍVEL**
- [ ] Configuração externa em JSON
- [ ] Sistema de fallback robusto
- [ ] Compatibilidade com dados antigos
- [ ] Comentários padronizados

### ✅ **UX MELHORADA**
- [ ] Navegação intuitiva
- [ ] Fluxo consistente entre 2D e 3D
- [ ] Feedback visual adequado
- [ ] Performance mantida

### ✅ **DOCUMENTAÇÃO ATUALIZADA**
- [ ] README atualizado com nova estrutura
- [ ] Comentários inline revisados
- [ ] Documentação de configuração JSON

---

## 🔧 Tratamento de Conflitos Identificados

### **CONFLITO**: Diferenças nos tipos de dados
**Problema**: 3D usa matriz 32x32, 2D usa arrays variáveis
**Solução**: Manter estruturas específicas, padronizar apenas interface

### **CONFLITO**: Sistema de enable/disable
**Problema**: Implementações diferentes entre 2D e 3D  
**Solução**: Adotar modelo 3D como referência, adaptar para arrays 1D

### **CONFLITO**: Configuração hardcoded vs JSON
**Problema**: 2D tem configuração no código, 3D usa JSON
**Solução**: Migrar 2D para JSON mantendo fallback no código

### **CONFLITO**: Layout de edição
**Problema**: 3D usa matriz, 2D usa linha horizontal
**Solução**: Manter layouts específicos, padronizar navegação e fluxo

---

**Relatório gerado em:** 2025-01-18
**Agente:** A03-FUEL-MAPS-STANDARDIZATION  
**Status:** Completo - Pronto para implementação
**Próximos passos:** Executar Fase 1 do plano de implementação