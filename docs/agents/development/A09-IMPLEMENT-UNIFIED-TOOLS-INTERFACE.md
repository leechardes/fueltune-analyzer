# A09 - IMPLEMENT UNIFIED TOOLS INTERFACE

## 📋 Objetivo
Implementar interface unificada de ferramentas de cálculo para mapas 2D e 3D, replicando a interface existente do fuel_maps_2d.py com adaptações para funcionar em ambas dimensões.

## ⚠️ IMPORTANTE - PADRÕES OBRIGATÓRIOS

### 1. Seguir Padrões de Desenvolvimento
**OBRIGATÓRIO**: Usar o arquivo `docs/agents/shared/STREAMLIT-DEVELOPMENT-STANDARDS.md` como guia de desenvolvimento.
- Verificar padrões de UI/UX
- Seguir convenções de código
- Manter consistência visual

### 2. Serviço em Execução
- **NÃO REINICIAR** o serviço - está rodando com hot-reload
- O servidor está ativo em `http://localhost:8503`
- Mudanças serão aplicadas automaticamente

## 🎯 Tarefas Detalhadas

### 1. Localização e Arquivo Alvo
**Arquivo a modificar**: `/Users/leechardes/Projetos/fueltune/fueltune-analyzer/src/ui/pages/fuel_maps.py`
**Função específica**: `render_tools()` (linha ~1131)

### 2. Estrutura da Interface a Implementar

```
┌─────────────────────────────────────────────────────────────┐
│ Configurações de Cálculo          │  Dados do Veículo      │
├───────────────────────────────────┼────────────────────────┤
│ • Estratégia de Tuning            │ Cilindrada: 1.9L       │
│ • Fator de Segurança              │ Cilindros: 4           │
│ • ☑ Considerar Boost              │ Vazão: 448 l/h         │
│ • ☑ Correção de Combustível       │ Combustível: Ethanol   │
│                                    │ Boost: 2.0 bar         │
└────────────────────────────────────┴────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                Preview dos Valores Calculados               │
├─────────────────────────────────────────────────────────────┤
│ [Gradiente Visual RdYlBu - Vermelho → Amarelo → Azul]      │
│ • 2D: DataFrame linha única (1x32)                         │
│ • 3D: DataFrame matriz (32x32)                             │
│                                                             │
│ Mínimo: X.XXX   Médio: X.XXX   Máximo: X.XXX              │
└─────────────────────────────────────────────────────────────┘

[✓ Aplicar Cálculo]              [📊 Preview Gráfico]
```

### 3. Código de Referência - fuel_maps_2d.py

#### Configurações de Cálculo (linhas 1352-1400):
```python
st.subheader("Configurações de Cálculo")

# Seleção de estratégia
strategy_names = list(STRATEGY_PRESETS.keys())
strategy_display = [STRATEGY_PRESETS[s]["name"] for s in strategy_names]
selected_idx = st.selectbox(
    "Estratégia de Tuning",
    range(len(strategy_names)),
    format_func=lambda x: f"{strategy_display[x]} - {STRATEGY_PRESETS[strategy_names[x]]['description']}",
    key=f"strategy_{session_key}",
)
selected_strategy = strategy_names[selected_idx]

# Fator de segurança
safety_factor = st.slider(
    "Fator de Segurança",
    min_value=0.8,
    max_value=1.2,
    value=1.0,
    step=0.01,
    key=f"safety_{session_key}",
    help="Ajuste fino dos valores calculados",
)

# Configurações específicas
st.write("**Configurações Específicas**")
col_check1, col_check2 = st.columns(2)

with col_check1:
    boost_enabled = st.checkbox(
        "Considerar Boost",
        value=True,
        key=f"boost_enabled_{session_key}",
        help="Considerar pressão de turbo nos cálculos"
    )

with col_check2:
    fuel_correction_enabled = st.checkbox(
        "Correção de Combustível",
        value=True,
        key=f"fuel_corr_{session_key}",
        help="Aplicar correção baseada no tipo de combustível"
    )
```

#### Dados do Veículo (linhas 1525-1555):
```python
st.subheader("Dados do Veículo")

# Obter dados do veículo da sessão
vehicle_data = get_vehicle_data_from_session()

# Primeira linha: Cilindrada, Cilindros, Vazão
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Cilindrada", f"{vehicle_data.get('displacement', 2.0):.1f}L")
with col2:
    st.metric("Cilindros", vehicle_data.get('cylinders', 4))
with col3:
    st.metric("Vazão", f"{vehicle_data.get('injector_flow', 250)} l/h")

# Segunda linha: Combustível, Boost
col4, col5 = st.columns(2)
with col4:
    st.metric("Combustível", vehicle_data.get('fuel_type', 'Flex'))
with col5:
    if vehicle_data.get('has_turbo', False):
        st.metric("Boost", f"{vehicle_data.get('max_boost', 1.0):.1f} bar")
```

#### Preview dos Valores (linhas 1557-1690):
```python
st.subheader("Preview dos Valores Calculados")

# Para 2D - criar DataFrame linha única
preview_df = pd.DataFrame([column_headers])
styled_df = preview_df.style.background_gradient(cmap="RdYlBu", axis=1).format("{:.3f}")

st.write(f"**Preview dos valores calculados** ({unit})")
st.caption(f"Valores com 3 casas decimais - Total: {len(preview_values)} valores")
st.dataframe(styled_df, use_container_width=True)

# Estatísticas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Mínimo", f"{min(preview_values):.3f} {unit}")
with col2:
    st.metric("Médio", f"{np.mean(preview_values):.3f} {unit}")
with col3:
    st.metric("Máximo", f"{max(preview_values):.3f} {unit}")
```

#### Botões de Ação (linhas 1695-1750):
```python
action_col1, action_col2 = st.columns(2)

with action_col1:
    if st.button("✓ Aplicar Cálculo", type="primary", use_container_width=True):
        # Para 2D
        st.session_state[session_key]["map_values"] = preview_values
        st.success("Valores calculados aplicados com sucesso!")
        st.rerun()

with action_col2:
    if st.button("📊 Preview Gráfico", use_container_width=True):
        # Mostrar gráfico comparativo
        fig = go.Figure()
        # ... código do gráfico ...
        st.plotly_chart(fig, use_container_width=True)
```

### 4. Código de Referência - fuel_maps_3d.py.backup

#### Preview 3D (linhas 1600-1630):
```python
# Para 3D - criar DataFrame matriz
preview_matrix_df = pd.DataFrame(
    calculated_matrix,
    columns=[f"{map_val:.2f}" for map_val in active_map_values],
    index=[f"{int(rpm)}" for rpm in active_rpm_values_reversed]
)

styled_df = preview_matrix_df.style.background_gradient(
    cmap="RdYlBu", axis=None
).format("{:.3f}")

st.dataframe(styled_df, use_container_width=True)
```

#### Gráfico 3D (linhas 1705-1730):
```python
if st.button("📊 Preview Gráfico"):
    fig = go.Figure(data=[go.Surface(
        z=calculated_matrix,
        x=map_axis,
        y=rpm_axis,
        colorscale="RdYlBu"
    )])
    
    fig.update_layout(
        title="Preview 3D dos Valores Calculados",
        scene=dict(
            xaxis_title="MAP (bar)",
            yaxis_title="RPM",
            zaxis_title=f"Valor ({unit})"
        ),
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
```

## 🔧 Implementação Passo a Passo

### PASSO 1: Substituir função render_tools()

Localização: `src/ui/pages/fuel_maps.py`, linha ~1131

**REMOVER** o código atual genérico e **SUBSTITUIR** por:

```python
def render_tools(map_type: str, map_config: Dict[str, Any], vehicle_id: str, 
                 bank_id: str, vehicle_data: Dict[str, Any], dimension: str):
    """Renderiza ferramentas avançadas unificadas para 2D e 3D."""
    
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    
    # Importar funções necessárias
    from src.core.fuel_maps import (
        get_vehicle_data_from_session,
        calculate_map_values_universal,  # Para 2D
        calculate_3d_map_values_universal  # Para 3D
    )
    
    # Obter dados do veículo da sessão
    vehicle_data = get_vehicle_data_from_session()
    
    # Duas colunas principais
    calc_col1, calc_col2 = st.columns(2)
    
    with calc_col1:
        # [IMPLEMENTAR Configurações de Cálculo aqui]
    
    with calc_col2:
        # [IMPLEMENTAR Dados do Veículo aqui]
    
    # [IMPLEMENTAR Preview dos Valores aqui]
    # Usar if dimension == "2D" para diferenciar
    
    # [IMPLEMENTAR Botões de Ação aqui]
```

### PASSO 2: Implementar Configurações de Cálculo

```python
with calc_col1:
    st.subheader("Configurações de Cálculo")
    
    # Estratégias disponíveis
    STRATEGY_PRESETS = {
        "conservative": {"name": "Conservador", "description": "Valores seguros de fábrica"},
        "balanced": {"name": "Balanceado", "description": "Valores típicos de fábrica"},
        "aggressive": {"name": "Agressivo", "description": "Performance orientada"},
        "economy": {"name": "Econômico", "description": "Foco em economia"},
        "sport": {"name": "Esportivo", "description": "Máxima performance"}
    }
    
    # Implementar selectbox, slider e checkboxes
```

### PASSO 3: Implementar Dados do Veículo

```python
with calc_col2:
    st.subheader("Dados do Veículo")
    
    # Usar vehicle_data obtido da sessão
    # Criar métricas em grid 3x2
```

### PASSO 4: Implementar Preview Diferenciado

```python
st.subheader("Preview dos Valores Calculados")

# Calcular valores baseado na dimensão
if dimension == "2D":
    # Carregar dados 2D atuais
    map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
    axis_values = map_data.get("axis_values", [])
    
    # Calcular valores
    preview_values = calculate_map_values_universal(...)
    
    # Criar DataFrame linha única
    preview_df = pd.DataFrame([preview_values])
    
else:  # 3D
    # Carregar dados 3D atuais
    map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
    rpm_axis = map_data.get("rpm_axis", [])
    map_axis = map_data.get("map_axis", [])
    
    # Calcular matriz
    calculated_matrix = calculate_3d_map_values_universal(...)
    
    # Criar DataFrame matriz
    preview_df = pd.DataFrame(calculated_matrix, 
                            columns=[f"{m:.2f}" for m in map_axis],
                            index=[f"{int(r)}" for r in reversed(rpm_axis)])

# Aplicar gradiente
styled_df = preview_df.style.background_gradient(cmap="RdYlBu").format("{:.3f}")
st.dataframe(styled_df, use_container_width=True)

# Estatísticas
# [Implementar métricas min/médio/max]
```

### PASSO 5: Implementar Botões de Ação

```python
action_col1, action_col2 = st.columns(2)

with action_col1:
    if st.button("✓ Aplicar Cálculo", type="primary", use_container_width=True,
                 key=f"apply_{map_type}_{bank_id}"):
        if dimension == "2D":
            # Salvar valores 2D
            save_2d_map_data(vehicle_id, map_type, bank_id, 
                           axis_values, preview_values, enabled, map_config)
        else:
            # Salvar matriz 3D
            persistence_manager.save_3d_map_data(vehicle_id, map_type, bank_id,
                                               rpm_axis, map_axis, rpm_enabled, 
                                               map_enabled, calculated_matrix)
        st.success("Valores aplicados com sucesso!")
        st.rerun()

with action_col2:
    if st.button("📊 Preview Gráfico", use_container_width=True,
                 key=f"preview_{map_type}_{bank_id}"):
        if dimension == "2D":
            # Gráfico de linha
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=axis_values, y=preview_values, 
                                    mode='lines+markers', name='Calculado'))
            # Configurar layout
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Gráfico 3D Surface
            fig = go.Figure(data=[go.Surface(z=calculated_matrix, 
                                            x=map_axis, y=rpm_axis)])
            # Configurar layout 3D
            st.plotly_chart(fig, use_container_width=True)
```

## ✅ Checklist de Validação

- [ ] Interface idêntica para 2D e 3D (exceto preview)
- [ ] Dados do veículo vindos da sessão
- [ ] Preview com gradiente RdYlBu
- [ ] Estatísticas min/médio/max funcionando
- [ ] Botão Aplicar salvando corretamente
- [ ] Botão Preview mostrando gráfico apropriado
- [ ] Sem erros no console
- [ ] Hot-reload funcionando (sem reiniciar serviço)
- [ ] Seguindo padrões do STREAMLIT-DEVELOPMENT-STANDARDS.md

## 🚀 Como Executar

1. Abrir o arquivo `src/ui/pages/fuel_maps.py`
2. Localizar a função `render_tools()` (linha ~1131)
3. Substituir completamente o conteúdo da função
4. Implementar cada seção conforme especificado
5. Testar no navegador (http://localhost:8503)
6. Verificar funcionalidade para mapas 2D e 3D

## 🎯 Resultado Esperado

- Interface de ferramentas profissional e unificada
- Mesma experiência para usuário em 2D e 3D
- Preview visual com gradiente de cores
- Cálculos funcionais baseados em estratégias
- Integração perfeita com estrutura existente

## ⚠️ Atenção Especial

1. **NÃO modificar** outras funções além de `render_tools()`
2. **NÃO mexer** na aba "Eixos" ou "Valores"
3. **MANTER** compatibilidade com estrutura de dados existente
4. **USAR** funções do core já existentes (não recriar)
5. **SEGUIR** padrões visuais do projeto

---

**Versão:** 1.0
**Data:** Janeiro 2025
**Status:** Pronto para execução
**Tipo:** Implementação de Interface
**Prioridade:** Alta