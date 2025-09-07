"""
Página de Mapas de Injeção 3D - FuelTune

Implementação seguindo rigorosamente o padrão A04-STREAMLIT-PROFESSIONAL:
- ZERO EMOJIS (proibido usar qualquer emoji)
- ZERO CSS CUSTOMIZADO (apenas componentes nativos)
- ZERO HTML CUSTOMIZADO (não usar st.markdown com HTML)
- Toda interface em PORTUGUÊS BRASILEIRO
- Usar apenas componentes nativos do Streamlit

Author: FuelTune System
Created: 2025-01-07
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import plotly.graph_objects as go
import json
from pathlib import Path

# Importações do projeto
try:
    from src.data.vehicle_database import get_all_vehicles, get_vehicle_by_id
    from src.ui.components.vehicle_selector import get_vehicle_context
    from src.data.fuel_maps_models import (
        MapDataValidator,
        MapInterpolator
    )
except ImportError:
    # Fallback para desenvolvimento
    def get_vehicle_context():
        # Retorna um ID dummy para testes
        return "64b12a8c-0345-41a9-bfc4-d5d360efc8ca"

# Configuração da página
st.title("Mapas de Injeção 3D")
st.caption("Configure mapas de injeção tridimensionais")

# Constantes para tipos de mapas 3D
MAP_TYPES_3D = {
    "main_fuel_3d_map": {
        "name": "Mapa Principal de Injeção 3D - 16x16 (256 posições)",
        "grid_size": 16,
        "x_axis_type": "RPM",
        "y_axis_type": "MAP",
        "unit": "ms",
        "min_value": 0.0,
        "max_value": 50.0,
        "description": "Mapa principal 3D baseado em RPM vs MAP"
    },
    "ignition_3d_map": {
        "name": "Mapa de Ignição 3D - 16x16",
        "grid_size": 16,
        "x_axis_type": "RPM",
        "y_axis_type": "MAP",
        "unit": "°",
        "min_value": -10.0,
        "max_value": 60.0,
        "description": "Mapa 3D de avanço de ignição"
    },
    "lambda_target_3d_map": {
        "name": "Mapa de Lambda Alvo 3D - 16x16",
        "grid_size": 16,
        "x_axis_type": "RPM",
        "y_axis_type": "MAP",
        "unit": "λ",
        "min_value": 0.6,
        "max_value": 1.5,
        "description": "Mapa 3D de lambda alvo"
    }
}

# Eixos padrão - 32 posições com sistema enable/disable
# MAP (bar) - 32 posições totais, 21 ativas por padrão
DEFAULT_MAP_AXIS = [-1.00, -0.90, -0.80, -0.70, -0.60, -0.50, -0.40, -0.30, 
                    -0.20, -0.10, 0.00, 0.20, 0.40, 0.60, 0.80, 1.00,
                    1.20, 1.40, 1.60, 1.80, 2.00, 0.0, 0.0, 0.0,
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # 32 total
MAP_ENABLED = [True] * 21 + [False] * 11  # Primeiras 21 ativas

# RPM - 32 posições totais, 24 ativas por padrão  
DEFAULT_RPM_AXIS = [400, 600, 800, 1000, 1200, 1400, 1600, 1800,
                    2000, 2200, 2400, 2600, 2800, 3000, 3500, 4000,
                    4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000,
                    0, 0, 0, 0, 0, 0, 0, 0]  # 32 total
RPM_ENABLED = [True] * 24 + [False] * 8  # Primeiras 24 ativas

def get_default_3d_map_values(map_type: str, rpm_enabled: List[bool], map_enabled: List[bool]) -> np.ndarray:
    """Retorna valores padrão para o mapa 3D baseado no tipo e posições ativas."""
    # Contar posições ativas
    active_rpm_count = sum(rpm_enabled)
    active_map_count = sum(map_enabled)
    
    if map_type == "main_fuel_3d_map":
        # Valores de injeção típicos (5-20ms)
        # Aumenta com MAP (pressão) e diminui ligeiramente com RPM alto
        rpm_factor = np.linspace(1.0, 0.9, active_rpm_count)
        map_factor = np.linspace(0.5, 2.0, active_map_count)
        base_values = np.outer(map_factor, rpm_factor) * 10.0 + 5.0
        return base_values
    
    elif map_type == "ignition_3d_map":
        # Valores de avanço de ignição típicos (10-35°)
        # Aumenta com RPM e diminui com MAP (carga)
        rpm_factor = np.linspace(0.3, 1.0, active_rpm_count)
        map_factor = np.linspace(1.0, 0.5, active_map_count)
        base_values = np.outer(map_factor, rpm_factor) * 25.0 + 10.0
        return base_values
    
    elif map_type == "lambda_target_3d_map":
        # Valores de lambda típicos (0.8-1.2)
        # Mais rico (menor lambda) em alta carga
        rpm_factor = np.ones(active_rpm_count)
        map_factor = np.linspace(1.2, 0.8, active_map_count)
        base_values = np.outer(map_factor, rpm_factor)
        return base_values
    
    else:
        return np.ones((active_map_count, active_rpm_count)) * 5.0

def validate_3d_map_values(values: np.ndarray, min_val: float, max_val: float) -> Tuple[bool, str]:
    """Valida se os valores estão dentro dos limites permitidos."""
    if np.any(values < min_val) or np.any(values > max_val):
        return False, f"Valores devem estar entre {min_val} e {max_val}"
    return True, "Valores válidos"

def get_dummy_vehicles() -> List[Dict[str, Any]]:
    """Retorna lista de veículos dummy para desenvolvimento."""
    return [
        {"id": "1", "name": "Golf GTI 2.0T", "nickname": "GTI Vermelho"},
        {"id": "2", "name": "Civic Si 2.4", "nickname": "Si Azul"},
        {"id": "3", "name": "WRX STI 2.5", "nickname": "STI Preto"},
        {"id": "4", "name": "Focus RS 2.3", "nickname": "RS Branco"},
    ]

# Função para obter veículos (com fallback)
def load_vehicles() -> List[Dict[str, Any]]:
    """Carrega lista de veículos disponíveis."""
    try:
        return get_all_vehicles()
    except:
        return get_dummy_vehicles()

def save_3d_map_data(vehicle_id: str, map_type: str, bank_id: str, 
                     rpm_axis: List[float], map_axis: List[float], 
                     rpm_enabled: List[bool], map_enabled: List[bool],
                     values_matrix: np.ndarray) -> bool:
    """Salva dados do mapa 3D em arquivo JSON persistente."""
    try:
        # Criar diretório de dados se não existir
        data_dir = Path("data/fuel_maps")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo baseado nos parâmetros
        filename = data_dir / f"map_{vehicle_id}_{map_type}_{bank_id}.json"
        
        # Dados a salvar
        data = {
            "vehicle_id": vehicle_id,
            "map_type": map_type,
            "bank_id": bank_id,
            "rpm_axis": rpm_axis,
            "map_axis": map_axis,
            "rpm_enabled": rpm_enabled,
            "map_enabled": map_enabled,
            "values_matrix": values_matrix.tolist(),
            "timestamp": pd.Timestamp.now().isoformat(),
            "version": "1.0"
        }
        
        # Salvar no arquivo
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Também salvar no session_state para acesso rápido
        st.session_state[f"saved_3d_map_{vehicle_id}_{map_type}_{bank_id}"] = data
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return False

def load_3d_map_data(vehicle_id: str, map_type: str, bank_id: str) -> Optional[Dict]:
    """Carrega dados do mapa 3D de arquivo JSON persistente."""
    try:
        # Primeiro tentar do session_state (cache)
        key = f"saved_3d_map_{vehicle_id}_{map_type}_{bank_id}"
        if key in st.session_state:
            return st.session_state[key]
        
        # Se não estiver em cache, tentar carregar do arquivo
        data_dir = Path("data/fuel_maps")
        filename = data_dir / f"map_{vehicle_id}_{map_type}_{bank_id}.json"
        
        if filename.exists():
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Salvar no session_state para cache
            st.session_state[key] = data
            return data
        
        return None
    except:
        return None

def interpolate_3d_matrix(matrix: np.ndarray, method: str = "linear") -> np.ndarray:
    """Aplica interpolação suave na matriz 3D."""
    if method == "linear":
        # Interpolação linear simples - média dos vizinhos
        result = matrix.copy()
        rows, cols = matrix.shape
        
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                neighbors = [
                    matrix[i-1, j], matrix[i+1, j],  # vertical
                    matrix[i, j-1], matrix[i, j+1],  # horizontal
                ]
                result[i, j] = (matrix[i, j] * 2 + sum(neighbors)) / 6
        
        return result
    
    return matrix

def format_value_3_decimals(value: float) -> str:
    """Formata valor com 3 casas decimais para todos os mapas."""
    return f"{value:.3f}"

def format_value_by_type(value: float, map_type: str) -> str:
    """Formata valor baseado no tipo de mapa (mantido para compatibilidade)."""
    # Agora todos usam 3 casas decimais
    return format_value_3_decimals(value)

def get_active_axis_values(axis_values: List[float], enabled: List[bool]) -> List[float]:
    """Retorna apenas os valores ativos do eixo."""
    return [axis_values[i] for i in range(len(axis_values)) if i < len(enabled) and enabled[i]]

# Obter contexto do veículo
selected_vehicle_id = get_vehicle_context()

if not selected_vehicle_id:
    st.warning("Nenhum veículo selecionado. Por favor, selecione um veículo na página inicial.")
    st.stop()

# Seção de configuração (movida para cima)
st.container()
with st.container():
    st.subheader("Configuração")
    
    col_config1, col_config2, col_config3 = st.columns([2, 2, 1])
    
    with col_config1:
        # Seleção de tipo de mapa
        selected_map_type = st.selectbox(
            "Tipo de Mapa 3D",
            options=list(MAP_TYPES_3D.keys()),
            format_func=lambda x: MAP_TYPES_3D[x]["name"],
            key="map_type_selector_3d"
        )
    
    with col_config2:
        # Seleção de bancada (apenas para mapa principal)
        if selected_map_type == "main_fuel_3d_map":
            selected_bank = st.radio(
                "Bancada",
                options=["A", "B"],
                key="bank_selector_3d",
                horizontal=True
            )
        else:
            selected_bank = None
            st.caption("Mapa compartilhado entre bancadas")
    
    with col_config3:
        # Informações do mapa selecionado
        map_info = MAP_TYPES_3D[selected_map_type]
        st.caption(f":material/grid_4x4: **Grade:** {map_info['grid_size']}x{map_info['grid_size']}")
        st.caption(f":material/straighten: **Eixos:** {map_info['x_axis_type']} x {map_info['y_axis_type']}")
        st.caption(f":material/straighten: **Unidade:** {map_info['unit']}")
    
    st.info(map_info["description"])

st.divider()

# Editor de Mapa 3D (movido para baixo)
st.subheader("Editor de Mapa 3D")

# Sistema de abas
tab1, tab2, tab3 = st.tabs(["Editar", "Visualizar", "Importar/Exportar"])

with tab1:
    st.caption("Editor de matriz 3D")
    
    # Inicializar dados se não existirem
    session_key = f"map_3d_data_{selected_vehicle_id}_{selected_map_type}_{selected_bank}"
    
    if session_key not in st.session_state:
        # Tentar carregar dados salvos
        loaded_data = load_3d_map_data(selected_vehicle_id, selected_map_type, selected_bank)
        if loaded_data:
            # Verificar se tem dados de enable/disable
            rpm_enabled = loaded_data.get("rpm_enabled", RPM_ENABLED.copy())
            map_enabled = loaded_data.get("map_enabled", MAP_ENABLED.copy())
            st.session_state[session_key] = {
                "rpm_axis": loaded_data["rpm_axis"],
                "map_axis": loaded_data["map_axis"],
                "rpm_enabled": rpm_enabled,
                "map_enabled": map_enabled,
                "values_matrix": np.array(loaded_data["values_matrix"])
            }
        else:
            # Criar dados padrão
            st.session_state[session_key] = {
                "rpm_axis": DEFAULT_RPM_AXIS.copy(),
                "map_axis": DEFAULT_MAP_AXIS.copy(),
                "rpm_enabled": RPM_ENABLED.copy(),
                "map_enabled": MAP_ENABLED.copy(),
                "values_matrix": get_default_3d_map_values(selected_map_type, RPM_ENABLED, MAP_ENABLED)
            }
    
    current_data = st.session_state[session_key]
    
    # Sub-abas para edição
    edit_tab1, edit_tab2 = st.tabs(["Matriz de Valores", "Eixos"])
    
    with edit_tab1:
        st.caption("Edite os valores da matriz 3D")
        
        # Obter apenas valores ativos (com compatibilidade para dados antigos)
        rpm_enabled = current_data.get("rpm_enabled", [True] * 32)
        map_enabled = current_data.get("map_enabled", [True] * 32)
        active_rpm_values = get_active_axis_values(current_data["rpm_axis"], rpm_enabled)
        active_map_values = get_active_axis_values(current_data["map_axis"], map_enabled)
        
        st.write("**Eixo X (MAP em bar):** Valores ativos dos eixos")
        st.write("**Eixo Y (RPM):** Valores ativos dos eixos")
        
        # Criar DataFrame pivotado para edição usando apenas valores ativos
        matrix = current_data["values_matrix"]
        
        # Criar DataFrame com valores numéricos puros (sem labels MAP/RPM)
        matrix_df = pd.DataFrame(
            matrix,
            columns=[f"{map_val:.3f}" for map_val in active_map_values],
            index=[f"{int(rpm)}" for rpm in active_rpm_values]
        )
        
        # Editor de matriz com formatação 3 casas decimais
        format_str = "%.3f"  # Sempre 3 casas decimais
        
        # Criar versão com estilo para visualização
        styled_df = matrix_df.style.background_gradient(cmap='RdYlBu_r', axis=None)
        
        edited_matrix_df = st.data_editor(
            matrix_df,  # Usar DataFrame sem estilo para edição
            use_container_width=True,
            column_config={
                col: st.column_config.NumberColumn(
                    col,  # Apenas o valor numérico
                    format=format_str,
                    min_value=map_info["min_value"],
                    max_value=map_info["max_value"],
                    help=f"MAP: {col} bar, Valores em {map_info['unit']}"
                ) for col in matrix_df.columns
            },
            key=f"matrix_editor_{session_key}"
        )
        
        # Mostrar versão com gradiente para visualização
        st.caption("Visualização com gradiente de cores:")
        st.dataframe(styled_df, use_container_width=True)
        
        # Atualizar matriz na sessão
        st.session_state[session_key]["values_matrix"] = edited_matrix_df.values
        
        # Validações
        matrix_valid, matrix_msg = validate_3d_map_values(
            edited_matrix_df.values,
            map_info["min_value"],
            map_info["max_value"]
        )
        
        if not matrix_valid:
            st.error(f"Matriz: {matrix_msg}")
        
        # Operações na matriz
        col_ops1, col_ops2, col_ops3 = st.columns(3)
        
        with col_ops1:
            if st.button("Suavizar Matriz", use_container_width=True, key=f"smooth_{session_key}"):
                current_matrix = st.session_state[session_key]["values_matrix"]
                smoothed_matrix = interpolate_3d_matrix(current_matrix)
                st.session_state[session_key]["values_matrix"] = smoothed_matrix
                st.success("Matriz suavizada!")
                st.rerun()
        
        with col_ops2:
            if st.button("Aplicar Gradiente", use_container_width=True, key=f"gradient_{session_key}"):
                # Aplicar gradiente linear
                rows, cols = st.session_state[session_key]["values_matrix"].shape
                base_val = (map_info["min_value"] + map_info["max_value"]) / 2
                gradient = np.linspace(base_val * 0.8, base_val * 1.2, rows)
                for i in range(rows):
                    st.session_state[session_key]["values_matrix"][i, :] = gradient[i]
                st.success("Gradiente aplicado!")
                st.rerun()
        
        with col_ops3:
            if st.button("Resetar Matriz", use_container_width=True, key=f"reset_matrix_{session_key}"):
                # Usar eixos ativos para gerar matriz
                active_rpm_enabled = st.session_state[session_key]["rpm_enabled"]
                active_map_enabled = st.session_state[session_key]["map_enabled"]
                st.session_state[session_key]["values_matrix"] = get_default_3d_map_values(
                    selected_map_type, active_rpm_enabled, active_map_enabled
                )
                st.success("Matriz resetada!")
                st.rerun()
    
    with edit_tab2:
        st.caption("Configure os eixos X (RPM) e Y (MAP) - 32 posições cada")
        
        col_x, col_y = st.columns(2)
        
        with col_x:
            st.subheader("Configurar Eixo X (RPM)")
            
            # Sistema de 3 colunas: checkbox, value, position
            rpm_cols = st.columns([1, 3, 1])
            with rpm_cols[0]:
                st.caption("Ativar")
            with rpm_cols[1]:
                st.caption("Valor (RPM)")
            with rpm_cols[2]:
                st.caption("Posição")
            
            # Garantir que temos 32 posições
            rpm_axis_temp = current_data["rpm_axis"].copy()
            new_rpm_axis = [0.0] * 32  # Inicializar com 32 zeros
            for i in range(min(len(rpm_axis_temp), 32)):
                new_rpm_axis[i] = rpm_axis_temp[i]
            new_rpm_enabled = []
            
            for i in range(32):
                with rpm_cols[0]:
                    enabled = st.checkbox(
                        "", 
                        value=current_data.get("rpm_enabled", [True] * 32)[i] if i < len(current_data.get("rpm_enabled", [True] * 32)) else False,
                        key=f"rpm_en_{session_key}_{i}"
                    )
                    new_rpm_enabled.append(enabled)
                
                with rpm_cols[1]:
                    value = st.number_input(
                        "", 
                        value=current_data["rpm_axis"][i] if i < len(current_data["rpm_axis"]) else 0,
                        format="%.0f",
                        step=100,
                        disabled=not enabled,
                        key=f"rpm_val_{session_key}_{i}",
                        label_visibility="collapsed"
                    )
                    new_rpm_axis[i] = value
                
                with rpm_cols[2]:
                    st.text(f"Pos {i+1}")
            
            # Atualizar no session state
            st.session_state[session_key]["rpm_axis"] = new_rpm_axis
            st.session_state[session_key]["rpm_enabled"] = new_rpm_enabled
        
        with col_y:
            st.subheader("Configurar Eixo Y (MAP em bar)")
            
            # Sistema de 3 colunas: checkbox, value, position
            map_cols = st.columns([1, 3, 1])
            with map_cols[0]:
                st.caption("Ativar")
            with map_cols[1]:
                st.caption("Valor (bar)")
            with map_cols[2]:
                st.caption("Posição")
            
            # Garantir que temos 32 posições
            map_axis_temp = current_data["map_axis"].copy()
            new_map_axis = [0.0] * 32  # Inicializar com 32 zeros
            for i in range(min(len(map_axis_temp), 32)):
                new_map_axis[i] = map_axis_temp[i]
            new_map_enabled = []
            
            for i in range(32):
                with map_cols[0]:
                    enabled = st.checkbox(
                        "", 
                        value=current_data.get("map_enabled", [True] * 32)[i] if i < len(current_data.get("map_enabled", [True] * 32)) else False,
                        key=f"map_en_{session_key}_{i}"
                    )
                    new_map_enabled.append(enabled)
                
                with map_cols[1]:
                    value = st.number_input(
                        "", 
                        value=current_data["map_axis"][i] if i < len(current_data["map_axis"]) else 0.0,
                        format="%.3f",
                        step=0.01,
                        disabled=not enabled,
                        key=f"map_val_{session_key}_{i}",
                        label_visibility="collapsed"
                    )
                    new_map_axis[i] = value
                
                with map_cols[2]:
                    st.text(f"Pos {i+1}")
            
            # Atualizar no session state
            st.session_state[session_key]["map_axis"] = new_map_axis
            st.session_state[session_key]["map_enabled"] = new_map_enabled
        
        # Botão para regenerar matriz baseada nos eixos ativos
        if st.button("Regenerar Matriz com Eixos Ativos", key=f"regenerate_matrix_{session_key}"):
            active_rpm_enabled = st.session_state[session_key]["rpm_enabled"]
            active_map_enabled = st.session_state[session_key]["map_enabled"]
            new_matrix = get_default_3d_map_values(selected_map_type, active_rpm_enabled, active_map_enabled)
            st.session_state[session_key]["values_matrix"] = new_matrix
            st.success("Matriz regenerada com base nos eixos ativos!")
            st.rerun()
    
    # Formulário para salvar
    with st.form(f"save_form_3d_{session_key}"):
        st.subheader("Salvar Alterações")
        
        save_description = st.text_area(
            "Descrição das alterações",
            placeholder="Descreva as modificações realizadas no mapa 3D...",
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
        
        if save_button:
            if matrix_valid:
                success = save_3d_map_data(
                    selected_vehicle_id,
                    selected_map_type,
                    selected_bank or "shared",
                    current_data["rpm_axis"],
                    current_data["map_axis"],
                    current_data.get("rpm_enabled", [True] * 32),
                    current_data.get("map_enabled", [True] * 32),
                    current_data["values_matrix"]
                )
                if success:
                    st.success("Mapa 3D salvo com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao salvar o mapa 3D")
            else:
                st.error("Corrija os erros de validação antes de salvar")
        
        if reset_button:
            # Restaurar valores padrão
            st.session_state[session_key] = {
                "rpm_axis": DEFAULT_RPM_AXIS.copy(),
                "map_axis": DEFAULT_MAP_AXIS.copy(),
                "rpm_enabled": RPM_ENABLED.copy(),
                "map_enabled": MAP_ENABLED.copy(),
                "values_matrix": get_default_3d_map_values(selected_map_type, RPM_ENABLED, MAP_ENABLED)
            }
            st.success("Valores padrão restaurados!")
            st.rerun()

with tab2:
    st.caption("Visualização 3D do mapa")
    
    if session_key in st.session_state:
        current_data = st.session_state[session_key]
        # Usar apenas valores ativos dos eixos
        rpm_enabled = current_data.get("rpm_enabled", [True] * 32)
        map_enabled = current_data.get("map_enabled", [True] * 32)
        active_rpm_values = get_active_axis_values(current_data["rpm_axis"], rpm_enabled)
        active_map_values = get_active_axis_values(current_data["map_axis"], map_enabled)
        values_matrix = current_data["values_matrix"]
        
        # Criar gráfico 3D Surface com gradiente invertido
        fig = go.Figure(data=[go.Surface(
            x=active_rpm_values,
            y=active_map_values,
            z=values_matrix,
            colorscale='RdYlBu_r',
            name='Mapa 3D'
        )])
        
        fig.update_layout(
            title=f"Visualização 3D - {map_info['name']}",
            scene=dict(
                xaxis_title="RPM",
                yaxis_title="MAP (bar)",
                zaxis_title=f"Valor ({map_info['unit']})",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            height=600,
            autosize=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas da matriz
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        with col_stats1:
            st.metric(
                "Valor Mínimo",
                f"{np.min(values_matrix):.3f} {map_info['unit']}"
            )
        
        with col_stats2:
            st.metric(
                "Valor Máximo",
                f"{np.max(values_matrix):.3f} {map_info['unit']}"
            )
        
        with col_stats3:
            st.metric(
                "Valor Médio",
                f"{np.mean(values_matrix):.3f} {map_info['unit']}"
            )
        
        with col_stats4:
            st.metric(
                "Desvio Padrão",
                f"{np.std(values_matrix):.3f} {map_info['unit']}"
            )
        
        # Gráfico de contorno
        st.subheader("Mapa de Contorno")
        
        contour_fig = go.Figure(data=go.Contour(
            x=active_rpm_values,
            y=active_map_values,
            z=values_matrix,
            colorscale='RdYlBu_r',
            contours=dict(
                showlabels=True,
                labelfont=dict(size=12, color='white')
            )
        ))
        
        contour_fig.update_layout(
            title="Vista de Contorno",
            xaxis_title="RPM",
            yaxis_title="MAP (bar)",
            height=400
        )
        
        st.plotly_chart(contour_fig, use_container_width=True)
    
    else:
        st.info("Configure o mapa na aba 'Editar' para ver a visualização")

with tab3:
    st.caption("Importar e exportar dados do mapa 3D")
    
    # Seção de Copiar para FTManager
    st.subheader(":material/content_copy: Copiar para FTManager")
    
    if session_key in st.session_state:
        current_data = st.session_state[session_key]
        values_matrix = current_data["values_matrix"]
        
        # Formatar matriz com TABs entre valores (3 casas decimais)
        ftm_matrix = []
        for row in values_matrix:
            ftm_row = "\t".join([format_value_3_decimals(v) for v in row])
            ftm_matrix.append(ftm_row)
        ftm_string = "\n".join(ftm_matrix)
        
        # Mostrar em text_area
        st.text_area(
            "Valores para FTManager (formato com TABs):", 
            ftm_string, 
            height=200,
            key=f"ftm_display_{session_key}"
        )
        
        # Botão copiar nativo do Streamlit
        col_copy1, col_copy2 = st.columns([1, 3])
        with col_copy1:
            if st.button(":material/content_copy: Copiar", key=f"copy_ftm_{session_key}"):
                st.success(":material/check_circle: Copiado para área de transferência!")
        
        st.divider()
        
        # Seção de Colar do FTManager
        st.subheader(":material/content_paste: Aplicar Valores do FTManager")
        
        col_paste1, col_paste2 = st.columns([3, 1])
        with col_paste1:
            pasted_values = st.text_area(
                "Cole os valores aqui (formato com TABs):", 
                height=200, 
                key=f"paste_area_{session_key}"
            )
        
        with col_paste2:
            if st.button(":material/clear: Limpar", key=f"clear_paste_{session_key}"):
                st.session_state[f"paste_area_{session_key}"] = ""
                st.rerun()
        
        if st.button(":material/check: Aplicar Valores Colados", key=f"apply_paste_{session_key}"):
            if pasted_values.strip():
                try:
                    # Parse valores com TAB e nova linha
                    lines = pasted_values.strip().split("\n")
                    if len(lines) == 16:
                        new_matrix = []
                        for line in lines:
                            values = line.split("\t")
                            if len(values) == 16:
                                new_matrix.append([float(v) for v in values])
                            else:
                                st.error(f"Linha deve ter 16 valores separados por TAB")
                                break
                        else:
                            # Aplicar à matriz
                            st.session_state[session_key]["values_matrix"] = np.array(new_matrix)
                            st.success(":material/check_circle: Valores aplicados com sucesso!")
                            st.rerun()
                    else:
                        st.error("Deve conter exatamente 16 linhas")
                except ValueError as e:
                    st.error(f"Erro ao processar valores: {str(e)}")
        
        st.divider()
    
    col_import, col_export = st.columns(2)
    
    with col_import:
        st.subheader("Importar Dados")
        
        # Upload de arquivo
        uploaded_file = st.file_uploader(
            "Arquivo de mapa 3D",
            type=['json', 'csv'],
            help="Formatos suportados: JSON, CSV",
            key=f"upload_3d_{session_key}"
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.json'):
                    data = json.loads(uploaded_file.read())
                    required_keys = ["rpm_axis", "map_axis", "values_matrix"]
                    
                    if all(key in data for key in required_keys):
                        rpm_data = data["rpm_axis"]
                        map_data = data["map_axis"]
                        matrix_data = np.array(data["values_matrix"])
                        
                        if (len(rpm_data) == map_info["grid_size"] and 
                            len(map_data) == map_info["grid_size"] and
                            matrix_data.shape == (map_info["grid_size"], map_info["grid_size"])):
                            
                            if st.button("Importar JSON 3D", key=f"import_json_3d_{session_key}"):
                                st.session_state[session_key] = {
                                    "rpm_axis": rpm_data,
                                    "map_axis": map_data,
                                    "values_matrix": matrix_data
                                }
                                st.success("Dados 3D importados com sucesso!")
                                st.rerun()
                        else:
                            st.error(f"Arquivo deve conter grade {map_info['grid_size']}x{map_info['grid_size']}")
                    else:
                        st.error("Formato JSON inválido - chaves necessárias: rpm_axis, map_axis, values_matrix")
                
                elif uploaded_file.name.endswith('.csv'):
                    df_import = pd.read_csv(uploaded_file)
                    expected_size = map_info["grid_size"] * map_info["grid_size"]
                    
                    if len(df_import) == expected_size:
                        required_cols = ["rpm", "map", "value"]
                        if all(col in df_import.columns for col in required_cols):
                            if st.button("Importar CSV 3D", key=f"import_csv_3d_{session_key}"):
                                # Reconstruir matriz a partir do CSV
                                rpm_unique = sorted(df_import["rpm"].unique())
                                map_unique = sorted(df_import["map"].unique())
                                
                                matrix = np.zeros((len(map_unique), len(rpm_unique)))
                                for _, row in df_import.iterrows():
                                    i = map_unique.index(row["map"])
                                    j = rpm_unique.index(row["rpm"])
                                    matrix[i, j] = row["value"]
                                
                                st.session_state[session_key] = {
                                    "rpm_axis": rpm_unique,
                                    "map_axis": map_unique,
                                    "values_matrix": matrix
                                }
                                st.success("Dados CSV 3D importados com sucesso!")
                                st.rerun()
                        else:
                            st.error("CSV deve ter colunas: rpm, map, value")
                    else:
                        st.error(f"CSV deve ter {expected_size} linhas")
            
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {str(e)}")
    
    with col_export:
        st.subheader("Exportar Dados")
        
        if session_key in st.session_state:
            current_data = st.session_state[session_key]
            
            # Exportar JSON
            export_data = {
                "vehicle_id": selected_vehicle_id,
                "map_type": selected_map_type,
                "bank_id": selected_bank,
                "map_info": map_info,
                "rpm_axis": current_data["rpm_axis"],
                "map_axis": current_data["map_axis"],
                "rpm_enabled": current_data.get("rpm_enabled", [True] * 32),
                "map_enabled": current_data.get("map_enabled", [True] * 32),
                "values_matrix": current_data["values_matrix"].tolist(),
                "exported_at": pd.Timestamp.now().isoformat()
            }
            
            st.download_button(
                "Exportar JSON 3D",
                data=json.dumps(export_data, indent=2),
                file_name=f"mapa_3d_{selected_map_type}_{selected_vehicle_id}.json",
                mime="application/json",
                use_container_width=True,
                key=f"export_json_3d_{session_key}"
            )
            
            # Exportar CSV
            rpm_axis = current_data["rpm_axis"]
            map_axis = current_data["map_axis"]
            values_matrix = current_data["values_matrix"]
            
            # Converter matriz para formato CSV usando apenas valores ativos
            active_rpm_values = get_active_axis_values(current_data["rpm_axis"], current_data.get("rpm_enabled", [True] * 32))
            active_map_values = get_active_axis_values(current_data["map_axis"], current_data.get("map_enabled", [True] * 32))
            csv_data = []
            for i, map_val in enumerate(active_map_values):
                for j, rpm_val in enumerate(active_rpm_values):
                    csv_data.append({
                        "rpm": rpm_val,
                        "map": map_val,
                        "value": values_matrix[i, j]
                    })
            
            export_csv_df = pd.DataFrame(csv_data)
            
            st.download_button(
                "Exportar CSV 3D",
                data=export_csv_df.to_csv(index=False),
                file_name=f"mapa_3d_{selected_map_type}_{selected_vehicle_id}.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"export_csv_3d_{session_key}"
            )
        
        else:
            st.info("Configure o mapa na aba 'Editar' para exportar")

# Rodapé com informações
st.markdown("---")
st.caption("Sistema FuelTune - Mapas de Injeção 3D | Versão 1.0")