# RELATÓRIO DE ANÁLISE COMPARATIVA - LAYOUTS 2D vs 3D

**Data da Análise:** 2025-01-08  
**Arquivos Analisados:**  
- `/src/ui/pages/fuel_maps_2d.py` (28.351 tokens)  
- `/src/ui/pages/fuel_maps_3d.py` (arquivos de interface 3D)  

**Objetivo:** Identificar diferenças estruturais e funcionais entre os layouts das páginas de mapas 2D e 3D para padronização e correções.

---

## 1. ESTRUTURA GERAL

### Mapa 2D:
- **Linha 710:** `st.title("Mapas de Injeção 2D")`
- **Linha 711:** `st.caption("Configure mapas de injeção bidimensionais")`
- **Linha 1038:** `st.subheader("Configuração do Mapa")`
- **Linha 1076:** `st.subheader("Editor de Mapa")`
- **Sistema de abas:** `tab1, tab2, tab3 = st.tabs(["Editar", "Visualizar", "Importar/Exportar"])` (linha 1079)

### Mapa 3D:
- **Linha 38:** `st.title("Mapas de Injeção 3D")`
- **Linha 39:** `st.caption("Configure mapas de injeção tridimensionais")`
- **Linha 731:** `st.subheader("Configuração")`
- **Linha 769:** `st.subheader("Editor de Mapa 3D")`
- **Sistema de abas:** `tab1, tab2, tab3 = st.tabs(["Editar", "Visualizar", "Importar/Exportar"])` (linha 772)

### Diferenças:
- **Título das seções:** 2D usa "Configuração do Mapa" vs 3D usa apenas "Configuração"
- **Editor:** 2D usa "Editor de Mapa" vs 3D usa "Editor de Mapa 3D"
- **Estrutura idêntica de abas** mas implementação diferente

---

## 2. CABEÇALHO E CONFIGURAÇÃO

### Mapa 2D:
```python
# Linha 1041: Layout em 3 colunas
config_col1, config_col2, config_col3 = st.columns([3, 2, 2])

# Coluna 1: Seleção do tipo de mapa
with config_col1:
    selected_map_type = st.selectbox(
        "Tipo de Mapa 2D",
        options=list(MAP_TYPES_2D.keys()),
        format_func=lambda x: MAP_TYPES_2D[x]["name"],
        key="map_type_selector"
    )

# Coluna 2: Seleção de bancada
with config_col2:
    if "main_fuel" in selected_map_type:
        selected_bank = st.radio(
            "Bancada",
            options=["A", "B"],
            key="bank_selector",
            horizontal=True
        )

# Coluna 3: Informações do mapa
with config_col3:
    st.metric("Posições", map_info['positions'])
    st.caption(f"{map_info['axis_type']} / {map_info['unit']}")
```

### Mapa 3D:
```python
# Linha 733: Layout em 3 colunas
col_config1, col_config2, col_config3 = st.columns([2, 2, 1])

# Coluna 1: Seleção do tipo
with col_config1:
    selected_map_type = st.selectbox(
        "Tipo de Mapa 3D",
        options=list(MAP_TYPES_3D.keys()),
        format_func=lambda x: MAP_TYPES_3D[x]["name"],
        key="map_type_selector_3d"
    )

# Coluna 2: Bancada
with col_config2:
    if selected_map_type == "main_fuel_3d_map":
        selected_bank = st.radio(
            "Bancada",
            options=["A", "B"],
            key="bank_selector_3d",
            horizontal=True
        )

# Coluna 3: Informações
with col_config3:
    st.caption(f":material/grid_4x4: **Grade:** {map_info['grid_size']}x{map_info['grid_size']}")
    st.caption(f":material/straighten: **Eixos:** {map_info['x_axis_type']} x {map_info['y_axis_type']}")
    st.caption(f":material/straighten: **Unidade:** {map_info['unit']}")
```

### Diferenças:
- **Proporções das colunas:** 2D usa `[3, 2, 2]` vs 3D usa `[2, 2, 1]`
- **Exibição de informações:** 2D usa `st.metric()` vs 3D usa `st.caption()` com ícones Material
- **Keys únicos:** 2D usa `"map_type_selector"` vs 3D usa `"map_type_selector_3d"`

---

## 3. EDITOR DE VALORES

### Mapa 2D - Sistema de Tabela Horizontal:
```python
# Linha 1475-1500: Criação do DataFrame horizontal
active_axis_values = get_active_values(current_data["axis_values"], axis_enabled)
active_map_values = get_active_values(current_data["map_values"], axis_enabled)

# Criar dicionário com valores do eixo X como chaves
data_dict = {}
for i, axis_val in enumerate(active_axis_values):
    col_name = format_value_3_decimals(axis_val)
    data_dict[col_name] = [active_map_values[i] if i < len(active_map_values) else 0.0]

df = pd.DataFrame(data_dict)

# Linha 1536: Visualização com gradiente
st.dataframe(styled_df, use_container_width=True, hide_index=True)

# Linha 1543: Editor funcional
edited_df = st.data_editor(
    df,
    num_rows="fixed",
    use_container_width=True,
    column_config=column_config,
    key=f"data_editor_{session_key}",
    hide_index=True
)
```

### Mapa 3D - Sistema de Matriz:
```python
# Linha 901-963: Criação da matriz pivotada
matrix = current_data["values_matrix"]

# Filtrar apenas posições ativas
active_rpm_indices = [i for i, enabled in enumerate(rpm_enabled[:grid_size]) if enabled]
active_map_indices = [i for i, enabled in enumerate(map_enabled[:grid_size]) if enabled]

# Criar matriz filtrada
filtered_matrix = []
for rpm_idx in active_rpm_indices_reversed:
    row = []
    for map_idx in active_map_indices:
        if rpm_idx < len(matrix) and map_idx < len(matrix[rpm_idx]):
            row.append(matrix[rpm_idx][map_idx])
        else:
            row.append(0.0)
    filtered_matrix.append(row)

# DataFrame de matriz
matrix_df = pd.DataFrame(
    filtered_matrix,
    columns=column_names,
    index=[f"{int(rpm)}" for rpm in active_rpm_values_reversed]
)

# Linha 968: Editor de matriz
edited_matrix_df = st.data_editor(
    matrix_df,
    use_container_width=True,
    column_config={...},
    key=f"matrix_editor_{session_key}"
)
```

### Diferenças Críticas:
1. **2D usa tabela horizontal** (1 linha × N colunas) vs **3D usa matriz** (N linhas × N colunas)
2. **2D tem visualização separada** com gradiente vs **3D integra edição e visualização**
3. **2D usa índice oculto** vs **3D usa índice com valores RPM**
4. **Keys diferentes:** `data_editor_{session_key}` vs `matrix_editor_{session_key}`

---

## 4. CALCULADOR AUTOMÁTICO

### Mapa 2D - Modal Completo:
```python
# Linha 1127-1132: Ativação do calculador
if st.button(":material/calculate: Calcular Valores Automáticos", key=f"auto_calc_btn_{session_key}", type="secondary", use_container_width=True):
    st.session_state[f"show_calculator_{session_key}"] = True
    st.rerun()

# Modal/Dialog do calculador automático
if st.session_state.get(f"show_calculator_{session_key}", False):
    with st.container():
        st.markdown("### Calculador Automático de Mapas")
        st.markdown("---")
        
        # Layout em colunas para configurações
        calc_col1, calc_col2 = st.columns([2, 1])
        
        with calc_col1:
            st.subheader("Configurações de Cálculo")
            # Seleção de estratégia, fator de segurança, etc.
        
        with calc_col2:
            st.subheader("Dados do Veículo")
            # Métricas do veículo
```

### Mapa 3D - Layout Integrado:
```python
# Linha 1028: Botão para calculador
if st.button(":material/calculate: Calculador Automático 3D", key=f"open_calculator_{session_key}", use_container_width=True, type="primary"):
    st.session_state[f"show_calculator_{session_key}"] = True

# Modal integrado
if st.session_state.get(f"show_calculator_{session_key}", False):
    with st.container():
        st.markdown("### 🔧 Calculador Automático 3D")
        st.caption("Calcule valores baseados nos dados do veículo")
    
        # Layout em 3 colunas
        col_calc1, col_calc2, col_calc3 = st.columns([2, 1, 2])
```

### Diferenças:
- **Botão 2D:** `type="secondary"` vs **3D:** `type="primary"`
- **Layout 2D:** `[2, 1]` vs **3D:** `[2, 1, 2]`
- **Título 2D:** Mais limpo vs **3D:** Com emoji
- **2D tem configurações específicas** por tipo de mapa vs **3D mais genérico**

---

## 5. OPERAÇÕES E AÇÕES

### Mapa 2D - Formulário de Salvamento:
```python
# Linha 1615: Formulário estruturado
with st.form(f"save_form_{session_key}"):
    st.subheader("Salvar Alterações")
    
    save_description = st.text_area(
        "Descrição das alterações",
        placeholder="Descreva as modificações realizadas no mapa...",
        key=f"save_desc_{session_key}"
    )
    
    col_save1, col_save2 = st.columns(2)
    
    with col_save1:
        save_button = st.form_submit_button(
            "Salvar Mapa",
            type="primary",
            use_container_width=True
        )
    
    with col_save2:
        reset_button = st.form_submit_button(
            "Restaurar Padrão",
            use_container_width=True
        )
```

### Mapa 3D - Seção Separada:
```python
# Linha 1485: Seção de salvamento
st.subheader("Salvar Alterações")

# Descrição opcional
save_description = st.text_area(
    "Descrição das alterações (opcional)",
    placeholder="Ex: Ajuste de boost, correção de AFR...",
    key=f"save_desc_{session_key}"
)

# Botões sem formulário
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    if st.button(":material/save: Salvar Mapa 3D", key=f"save_3d_{session_key}", type="primary"):
        # Lógica de salvamento
```

### Diferenças:
- **2D usa st.form()** para agrupar ações vs **3D usa botões individuais**
- **2D tem reset integrado** vs **3D não tem botão de reset visível**
- **Layout:** 2D usa 2 colunas vs 3D usa 3 colunas

---

## 6. ESTILOS E FORMATAÇÃO

### Ambas as páginas usam:
- **Formatação:** 3 casas decimais (`format_value_3_decimals()`)
- **Gradiente:** `cmap='RdYlBu'` (Red-Yellow-Blue)
- **Ícones:** Material icons (`:material/calculate:`)
- **Validação:** Valores mínimos e máximos

### Diferenças sutis:
- **2D:** Estilo mais limpo, sem emojis desnecessários
- **3D:** Uso ocasional de emojis em títulos
- **2D:** Feedback com `st.balloons()` no salvamento
- **3D:** Feedback mais direto com `st.success()`

---

## 7. CÓDIGO ESPECÍFICO A CORRIGIR

### Problema Principal - Inconsistência no Título das Seções:

**fuel_maps_2d.py - Linha 1038:**
```python
st.subheader("Configuração do Mapa")
```

**fuel_maps_3d.py - Linha 731:**
```python
st.subheader("Configuração")  # CORRIGIR PARA: "Configuração do Mapa"
```

### Problema - Layout das Colunas de Configuração:

**fuel_maps_2d.py - Linha 1041:**
```python
config_col1, config_col2, config_col3 = st.columns([3, 2, 2])
```

**fuel_maps_3d.py - Linha 733:**
```python
col_config1, col_config2, col_config3 = st.columns([2, 2, 1])  # CORRIGIR PROPORÇÕES
```

### Problema - Exibição de Informações do Mapa:

**fuel_maps_2d.py - Linha 1069:**
```python
st.metric("Posições", map_info['positions'])
st.caption(f"{map_info['axis_type']} / {map_info['unit']}")
```

**fuel_maps_3d.py - Linha 760:**
```python
st.caption(f":material/grid_4x4: **Grade:** {map_info['grid_size']}x{map_info['grid_size']}")
# FALTA CONSISTÊNCIA NO FORMATO
```

### Problema - Formulário de Salvamento:

**3D não usa st.form() como o 2D - Linha 1615 do 2D vs implementação solta do 3D**

---

## 8. PLANO DE CORREÇÃO PRIORITÁRIO

### 1. **CRÍTICO - Padronizar Títulos e Seções**
```python
# EM fuel_maps_3d.py linha 731, ALTERAR DE:
st.subheader("Configuração")
# PARA:
st.subheader("Configuração do Mapa")
```

### 2. **ALTO - Uniformizar Layout de Configuração**
```python
# EM fuel_maps_3d.py linha 733, ALTERAR DE:
col_config1, col_config2, col_config3 = st.columns([2, 2, 1])
# PARA:
config_col1, config_col2, config_col3 = st.columns([3, 2, 2])
```

### 3. **ALTO - Padronizar Exibição de Informações**
```python
# EM fuel_maps_3d.py linha 760, SUBSTITUIR:
st.caption(f":material/grid_4x4: **Grade:** {map_info['grid_size']}x{map_info['grid_size']}")
st.caption(f":material/straighten: **Eixos:** {map_info['x_axis_type']} x {map_info['y_axis_type']}")
st.caption(f":material/straighten: **Unidade:** {map_info['unit']}")

# POR:
st.metric("Grade", f"{map_info['grid_size']}x{map_info['grid_size']}")
st.caption(f"{map_info['x_axis_type']} x {map_info['y_axis_type']} / {map_info['unit']}")
```

### 4. **MÉDIO - Implementar Formulário de Salvamento Estruturado no 3D**
```python
# Substituir botões soltos por st.form() como no 2D
with st.form(f"save_form_3d_{session_key}"):
    st.subheader("Salvar Alterações")
    
    save_description = st.text_area(
        "Descrição das alterações",
        placeholder="Descreva as modificações realizadas no mapa...",
        key=f"save_desc_3d_{session_key}"
    )
    
    col_save1, col_save2 = st.columns(2)
    
    with col_save1:
        save_button = st.form_submit_button(
            "Salvar Mapa 3D",
            type="primary",
            use_container_width=True
        )
    
    with col_save2:
        reset_button = st.form_submit_button(
            "Restaurar Padrão",
            use_container_width=True
        )
```

### 5. **BAIXO - Padronizar Keys de Session State**
```python
# Garantir que todas as keys sigam o padrão:
# 2D: f"data_editor_{session_key}"
# 3D: f"matrix_editor_3d_{session_key}"
```

### 6. **BAIXO - Uniformizar Feedback Visual**
```python
# Adicionar st.balloons() no salvamento do 3D como no 2D
if success:
    st.success("Mapa 3D salvo com sucesso!")
    st.balloons()  # ADICIONAR ESTA LINHA
    time.sleep(0.5)
    st.rerun()
```

---

## 9. RESUMO EXECUTIVO

### Principais Descobertas:
1. **Estrutura Geral:** Ambas seguem padrão similar com título → configuração → abas
2. **Diferenças Críticas:** Layout de configuração e sistema de salvamento inconsistentes
3. **Editor de Valores:** 2D usa tabela horizontal, 3D usa matriz - **CORRETO por design**
4. **Calculador:** Funcionalidades similares mas layouts diferentes
5. **Formatação:** Ambas usam 3 casas decimais e mesmo esquema de cores

### Impacto das Correções:
- **Experiência do Usuário:** Mais consistente entre páginas
- **Manutenibilidade:** Padrões uniformes facilitam atualizações
- **Visual:** Interface mais profissional e padronizada
- **Funcionalidade:** Formulários estruturados melhoram UX

### Próximos Passos:
1. Implementar correções prioritárias (1-3)
2. Testar funcionalidades após alterações
3. Validar consistência visual entre páginas
4. Documentar padrões estabelecidos

---

**Relatório gerado em:** 2025-01-08  
**Autor:** Sistema de Análise Automatizada  
**Versão:** 1.0