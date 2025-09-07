# Requisitos para Implementação de UI de Mapas de Combustível

## INSTRUÇÕES CRÍTICAS - PADRÃO A04-STREAMLIT-PROFESSIONAL

### ⚠️ REGRAS OBRIGATÓRIAS (NUNCA VIOLAR)

1. **ZERO EMOJIS** - Não use NENHUM emoji no código
2. **ZERO CSS CUSTOMIZADO** - Use APENAS componentes nativos do Streamlit
3. **ZERO HTML CUSTOMIZADO** - Não use st.markdown com HTML
4. **PORTUGUÊS BRASIL** - Toda interface em português brasileiro

### ✅ COMPONENTES PERMITIDOS

Use APENAS estes componentes nativos do Streamlit:
- `st.title()`, `st.header()`, `st.subheader()` - Títulos
- `st.tabs()` - Navegação entre abas
- `st.columns()` - Layout em colunas
- `st.container()`, `st.expander()` - Containers
- `st.dataframe()`, `st.data_editor()` - Tabelas editáveis
- `st.number_input()`, `st.slider()` - Entrada numérica
- `st.selectbox()`, `st.radio()` - Seleções
- `st.button()`, `st.form()` - Ações e formulários
- `st.metric()` - Exibir métricas
- `st.plotly_chart()` - Gráficos 3D/heatmap

### ❌ PROIBIDO

- **NÃO USE** st.markdown com HTML/CSS
- **NÃO USE** emojis (🚗, ✅, ❌, etc)
- **NÃO USE** unsafe_allow_html=True
- **NÃO USE** CSS customizado
- **NÃO USE** Material Icons via HTML

## ESTRUTURA DE ARQUIVOS

### 1. Página de Mapas 2D (`src/ui/pages/fuel_maps_2d.py`)

```python
# ESTRUTURA OBRIGATÓRIA
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import plotly.graph_objects as go

# Importações do projeto
from src.data.fuel_maps_models import FuelMap2D
from src.data.fuel_maps_database import (
    get_fuel_maps_2d,
    create_fuel_map_2d,
    update_fuel_map_2d,
    delete_fuel_map_2d
)

# Título da página (SEM EMOJI)
st.title("Mapas de Injeção 2D")
st.caption("Configure mapas de injeção bidimensionais")

# Código da página...
```

### 2. Página de Mapas 3D (`src/ui/pages/fuel_maps_3d.py`)

```python
# ESTRUTURA OBRIGATÓRIA
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Título da página (SEM EMOJI)
st.title("Mapas de Injeção 3D")
st.caption("Configure mapas de injeção tridimensionais")

# Código da página...
```

## ESPECIFICAÇÃO FUNCIONAL

### Mapas 2D - Funcionalidades Obrigatórias

1. **Seleção de Veículo**
   ```python
   vehicles = get_all_vehicles()
   vehicle_options = {v["id"]: v["name"] for v in vehicles}
   selected_vehicle = st.selectbox(
       "Selecione o Veículo",
       options=list(vehicle_options.keys()),
       format_func=lambda x: vehicle_options[x]
   )
   ```

2. **Tipos de Mapas 2D** (usar st.selectbox)
   - Mapa Principal de Injeção (MAP) - 32 posições
   - Mapa Principal de Injeção (TPS) - 20 posições
   - Compensação por RPM - 32 posições
   - Compensação por Temperatura do Motor - 16 posições
   - Compensação por Temperatura do Ar - 9 posições
   - Compensação por Tensão de Bateria - 8 posições

3. **Editor de Tabela** (usar st.data_editor)
   ```python
   # Criar DataFrame com posições e valores
   df = pd.DataFrame({
       "Posição": range(1, num_positions + 1),
       "Eixo X": axis_values,
       "Valor": map_values
   })
   
   edited_df = st.data_editor(
       df,
       num_rows="fixed",
       use_container_width=True,
       column_config={
           "Posição": st.column_config.NumberColumn("Posição", disabled=True),
           "Eixo X": st.column_config.NumberColumn("Eixo X", format="%.1f"),
           "Valor": st.column_config.NumberColumn("Valor", format="%.2f")
       }
   )
   ```

4. **Visualização Gráfica** (usar plotly)
   ```python
   fig = go.Figure()
   fig.add_trace(go.Scatter(
       x=axis_values,
       y=map_values,
       mode='lines+markers',
       name='Mapa'
   ))
   fig.update_layout(
       title="Visualização do Mapa 2D",
       xaxis_title="Eixo X",
       yaxis_title="Valor",
       height=400
   )
   st.plotly_chart(fig, use_container_width=True)
   ```

### Mapas 3D - Funcionalidades Obrigatórias

1. **Tipos de Mapas 3D** (usar st.selectbox)
   - Mapa Principal de Injeção 3D - 16x16 (256 posições)
   - Mapa de Ignição 3D - 16x16
   - Mapa de Lambda Alvo 3D - 16x16

2. **Editor de Tabela 3D** (usar st.data_editor com pivô)
   ```python
   # Criar matriz de valores
   matrix_df = pd.DataFrame(
       map_values.reshape(16, 16),
       columns=[f"RPM_{rpm}" for rpm in rpm_axis],
       index=[f"MAP_{map_val}" for map_val in map_axis]
   )
   
   edited_matrix = st.data_editor(
       matrix_df,
       use_container_width=True
   )
   ```

3. **Visualização 3D** (usar plotly surface)
   ```python
   fig = go.Figure(data=[go.Surface(
       x=rpm_axis,
       y=map_axis,
       z=map_values.reshape(16, 16)
   )])
   fig.update_layout(
       title="Mapa 3D de Injeção",
       scene=dict(
           xaxis_title="RPM",
           yaxis_title="MAP (kPa)",
           zaxis_title="Tempo (ms)"
       ),
       height=600
   )
   st.plotly_chart(fig, use_container_width=True)
   ```

## BANCO DE DADOS

### Criar arquivo `src/data/fuel_maps_database.py`

```python
from typing import List, Dict, Optional
from src.data.database import get_database

def get_fuel_maps_2d(vehicle_id: str, map_type: str) -> List[Dict]:
    """Buscar mapas 2D do veículo."""
    # Implementar busca no banco
    pass

def create_fuel_map_2d(map_data: Dict) -> str:
    """Criar novo mapa 2D."""
    # Implementar criação
    pass

def update_fuel_map_2d(map_id: str, map_data: Dict) -> bool:
    """Atualizar mapa 2D."""
    # Implementar atualização
    pass

# Similar para mapas 3D
```

## VALIDAÇÕES OBRIGATÓRIAS

1. **Validar limites de valores**
   - Tempo de injeção: 0-50ms
   - MAP: 0-500 kPa
   - RPM: 0-20000
   - Lambda: 0.6-1.5
   - Compensação: -100% a +100%

2. **Validar consistência dos eixos**
   - Valores do eixo devem ser crescentes
   - Não pode haver valores duplicados no eixo

3. **Validar tamanho do mapa**
   - Cada tipo tem tamanho fixo (8, 9, 16, 20, 32 posições)

## EXEMPLO DE IMPLEMENTAÇÃO CORRETA

```python
import streamlit as st
import pandas as pd
import numpy as np

# CORRETO - Sem emojis, sem HTML
st.title("Mapas de Injeção 2D")
st.caption("Configure os mapas de injeção do veículo")

# CORRETO - Uso de tabs nativas
tab1, tab2, tab3 = st.tabs(["Editar", "Visualizar", "Importar/Exportar"])

with tab1:
    # CORRETO - Layout com colunas
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # CORRETO - Componentes nativos
        vehicle = st.selectbox("Veículo", ["Golf GTI", "Civic Si"])
        map_type = st.selectbox("Tipo de Mapa", ["MAP 32 pos", "TPS 20 pos"])
        bank = st.radio("Bancada", ["A", "B"])
    
    with col2:
        # CORRETO - Data editor nativo
        df = pd.DataFrame({
            "Posição": range(1, 33),
            "MAP (kPa)": np.linspace(0, 250, 32),
            "Tempo (ms)": np.ones(32) * 5.0
        })
        
        edited = st.data_editor(df, use_container_width=True)

# INCORRETO - NUNCA FAZER
# st.markdown("<h1>🚗 Mapas</h1>", unsafe_allow_html=True)  # PROIBIDO
# st.write("✅ Salvo com sucesso!")  # PROIBIDO - tem emoji
```

## CHECKLIST DE VALIDAÇÃO

Antes de entregar o código, verifique:

- [ ] ZERO emojis no código
- [ ] ZERO uso de st.markdown com HTML
- [ ] ZERO CSS customizado
- [ ] APENAS componentes nativos do Streamlit
- [ ] Toda interface em português brasileiro
- [ ] Validações de dados implementadas
- [ ] Integração com banco de dados funcionando
- [ ] Compatível com tema claro e escuro
- [ ] Código limpo e bem organizado
- [ ] Sem imports desnecessários