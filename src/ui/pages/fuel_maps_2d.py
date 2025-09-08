"""
Página de Mapas de Injeção 2D - FuelTune

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
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import plotly.graph_objects as go
import json

# Importações do projeto
try:
    from src.data.vehicle_database import get_all_vehicles, get_vehicle_by_id
    from src.ui.components.vehicle_selector import get_vehicle_context
    from src.data.fuel_maps_models import (
        create_default_main_fuel_2d_map,
        create_default_rpm_compensation_map,
        create_default_temp_compensation_map,
        MapDataValidator,
        MapInterpolator
    )
except ImportError:
    # Fallback para desenvolvimento
    def get_vehicle_context():
        # Retorna um ID dummy para testes
        return "64b12a8c-0345-41a9-bfc4-d5d360efc8ca"
    pass

# Configuração da página
st.title("Mapas de Injeção 2D")
st.caption("Configure mapas de injeção bidimensionais")

# Carregar configuração de tipos de mapas 2D do arquivo externo
def load_map_types_config():
    """Carrega a configuração de tipos de mapas do arquivo JSON."""
    config_path = Path("config/map_types_2d.json")
    
    # Se o arquivo não existir, usar configuração padrão
    if not config_path.exists():
        return {
            "main_fuel_2d_map_32": {
                "name": "Mapa Principal de Injeção (MAP) - 32 posições",
                "positions": 32,
                "axis_type": "MAP",
                "unit": "ms",
                "min_value": 0.0,
                "max_value": 50.0,
                "description": "Mapa principal de combustível baseado na pressão MAP",
                "default_enabled_count": 21
            },
            "tps_correction_2d": {
                "name": "Correção por TPS",
                "positions": 32,
                "axis_type": "TPS",
                "unit": "%",
                "min_value": -50.0,
                "max_value": 50.0,
                "description": "Correção de combustível baseada no TPS",
                "default_enabled_count": 16
            },
            "temp_correction_2d": {
                "name": "Correção por Temperatura",
                "positions": 32,
                "axis_type": "TEMP",
                "unit": "%",
                "min_value": -30.0,
                "max_value": 30.0,
                "description": "Correção baseada na temperatura do motor",
                "default_enabled_count": 12
            }
        }
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Erro ao carregar configuração: {e}. Usando valores padrão.")
        return load_map_types_config.__defaults__[0]

# Carregar configuração de tipos de mapas
MAP_TYPES_2D = load_map_types_config()

def get_default_axis_values(axis_type: str, positions: int) -> List[float]:
    """Retorna valores padrão para 32 posições com sistema enable/disable."""
    if axis_type == "MAP":
        # Valores MAP para 32 posições: -1.00 a 2.00 bar (21 ativas) + zeros
        return [-1.00, -0.90, -0.80, -0.70, -0.60, -0.50, -0.40, -0.30, 
                -0.20, -0.10, 0.00, 0.20, 0.40, 0.60, 0.80, 1.00,
                1.20, 1.40, 1.60, 1.80, 2.00, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    elif axis_type == "TPS":
        # TPS para 20 posições: 0 a 100%
        if positions == 20:
            return list(np.linspace(0, 100, 20))
        else:
            return list(np.linspace(0, 100, positions))
    elif axis_type == "RPM":
        # RPM para 32 posições: 400 a 8000 RPM (24 ativas) + zeros  
        return [400, 600, 800, 1000, 1200, 1400, 1600, 1800,
                2000, 2200, 2400, 2600, 2800, 3000, 3500, 4000,
                4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000,
                0, 0, 0, 0, 0, 0, 0, 0]
    elif axis_type == "TEMP":
        # Temperatura para 16 posições
        return list(np.linspace(-10, 120, positions))
    elif axis_type == "AIR_TEMP":
        # Temperatura do ar para 9 posições
        return list(np.linspace(-20, 60, positions))
    elif axis_type == "VOLTAGE":
        # Tensão para 8 posições
        return list(np.linspace(8, 16, positions))
    else:
        return [0.0] * positions

def get_default_enabled_positions(axis_type: str, positions: int, map_type_key: str = None) -> List[bool]:
    """Retorna posições habilitadas por padrão."""
    # Usar configuração do JSON se disponível
    if map_type_key and map_type_key in MAP_TYPES_2D:
        default_count = MAP_TYPES_2D[map_type_key].get("default_enabled_count", positions)
        return [True] * min(default_count, positions) + [False] * max(0, positions - default_count)
    
    # Fallback para lógica anterior
    if axis_type == "MAP" and positions == 32:
        return [True] * 21 + [False] * 11  # Primeiras 21 ativas
    elif axis_type == "RPM" and positions == 32:
        return [True] * 24 + [False] * 8   # Primeiras 24 ativas
    else:
        return [True] * positions  # Todas ativas para outros tipos

def get_active_values(values: List[float], enabled: List[bool]) -> List[float]:
    """Retorna apenas os valores ativos."""
    return [values[i] for i in range(len(values)) if i < len(enabled) and enabled[i]]

def get_default_map_values(map_type: str, axis_type: str, positions: int) -> List[float]:
    """Retorna valores padrão para o mapa baseado no tipo e posições ativas."""
    enabled = get_default_enabled_positions(axis_type, positions)
    active_count = sum(enabled)
    
    if "main_fuel" in map_type:
        # Valores de injeção típicos (5-15ms)
        return list(np.linspace(5.0, 15.0, active_count))
    elif "compensation" in map_type:
        # Valores de compensação (0% inicial)
        return [0.0] * active_count
    else:
        return [0.0] * active_count

def format_value_3_decimals(value: float) -> str:
    """Formata valor com 3 casas decimais."""
    return f"{value:.3f}"

def validate_map_values(values: List[float], min_val: float, max_val: float) -> Tuple[bool, str]:
    """Valida se os valores estão dentro dos limites permitidos."""
    for i, val in enumerate(values):
        if val < min_val or val > max_val:
            return False, f"Valor na posição {i+1} ({val}) está fora do limite ({min_val} a {max_val})"
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

def save_map_data(vehicle_id: str, map_type: str, bank_id: str, 
                  axis_values: List[float], map_values: List[float],
                  axis_enabled: List[bool] = None) -> bool:
    """Salva dados do mapa em arquivo JSON persistente."""
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
            "axis_values": axis_values,
            "map_values": map_values,
            "axis_enabled": axis_enabled,
            "timestamp": pd.Timestamp.now().isoformat(),
            "version": "1.0"
        }
        
        # Salvar em arquivo JSON
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Também salvar no session_state para acesso rápido
        st.session_state[f"saved_map_{vehicle_id}_{map_type}_{bank_id}"] = data
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return False

def load_map_data(vehicle_id: str, map_type: str, bank_id: str) -> Optional[Dict]:
    """Carrega dados do mapa de arquivo JSON persistente."""
    try:
        # Primeiro tentar do session_state (cache)
        key = f"saved_map_{vehicle_id}_{map_type}_{bank_id}"
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
    except Exception as e:
        print(f"Erro ao carregar mapa: {e}")
        return None

# Obter veículo do contexto global (sidebar)
selected_vehicle_id = get_vehicle_context()

if not selected_vehicle_id:
    st.warning("Selecione um veículo no menu lateral para configurar os mapas de injeção")
    st.stop()

# Obter informações do veículo selecionado
vehicles = load_vehicles()
if vehicles:
    vehicle_data = next((v for v in vehicles if v["id"] == selected_vehicle_id), None)
    if vehicle_data:
        st.info(f"Veículo Ativo: **{vehicle_data['name']}** ({vehicle_data['nickname']})")
    else:
        st.warning("Veículo não encontrado")
else:
    # Usar dados dummy se não houver veículos
    st.info("Veículo Ativo: **Honda Civic** (Teste)")

# Configurações no topo
st.subheader("Configuração do Mapa")

# Layout de configurações em colunas (agora com 3 colunas, sem seletor de veículo)
config_col1, config_col2, config_col3 = st.columns([3, 2, 2])

with config_col1:
    # Seleção de tipo de mapa
    selected_map_type = st.selectbox(
        "Tipo de Mapa 2D",
        options=list(MAP_TYPES_2D.keys()),
        format_func=lambda x: MAP_TYPES_2D[x]["name"],
        key="map_type_selector"
    )
    # Informações do mapa
    map_info = MAP_TYPES_2D[selected_map_type]

with config_col2:
    # Seleção de bancada (se aplicável)
    if "main_fuel" in selected_map_type:
        selected_bank = st.radio(
            "Bancada",
            options=["A", "B"],
            key="bank_selector",
            horizontal=True
        )
    else:
        selected_bank = None
        st.info("Mapa Compartilhado")

with config_col3:
    # Informações do mapa
    st.metric("Posições", map_info['positions'])
    st.caption(f"{map_info['axis_type']} / {map_info['unit']}")

# Linha divisória
st.divider()

# Editor de Mapa embaixo
st.subheader("Editor de Mapa")

# Sistema de abas
tab1, tab2, tab3 = st.tabs(["Editar", "Visualizar", "Importar/Exportar"])
    
with tab1:
    st.caption("Editor de dados do mapa")
        
    # Inicializar dados se não existirem
    session_key = f"map_data_{selected_vehicle_id}_{selected_map_type}_{selected_bank}"
    
    if session_key not in st.session_state:
        # Tentar carregar dados salvos
        loaded_data = load_map_data(selected_vehicle_id, selected_map_type, selected_bank)
        if loaded_data:
            # Verificar se tem dados enable/disable
            axis_enabled = loaded_data.get("axis_enabled")
            if axis_enabled is None:
                axis_enabled = get_default_enabled_positions(map_info["axis_type"], map_info["positions"], selected_map_type)
            st.session_state[session_key] = {
                "axis_values": loaded_data["axis_values"],
                "map_values": loaded_data["map_values"],
                "axis_enabled": axis_enabled
            }
        else:
            # Criar dados padrão
            axis_enabled = get_default_enabled_positions(map_info["axis_type"], map_info["positions"], selected_map_type)
            st.session_state[session_key] = {
                "axis_values": get_default_axis_values(
                    map_info["axis_type"], 
                    map_info["positions"]
                ),
                "map_values": get_default_map_values(
                    selected_map_type, 
                    map_info["axis_type"],
                    map_info["positions"]
                ),
                "axis_enabled": axis_enabled
            }
    
    current_data = st.session_state[session_key]
    
    # Sub-abas para edição
    edit_tab1, edit_tab2 = st.tabs(["Valores", "Eixos"])
    
    with edit_tab1:
        st.caption("Edite os valores do mapa usando layout horizontal")
    
    
        # Criar DataFrame horizontal usando apenas valores ativos
        active_axis_values = current_data["axis_values"]  # Já filtrados
        active_map_values = current_data["map_values"]    # Já filtrados
        
        st.write(f"**Eixo X ({map_info['axis_type']}):** Valores numéricos")
        st.caption(f"Total de {len(active_axis_values)} posições ativas")
        
        # Criar dicionário com os valores do eixo X como chaves (apenas valores numéricos)
        data_dict = {}
        for i, axis_val in enumerate(active_axis_values):
            # Usar formatação 3 casas decimais para colunas
            col_name = format_value_3_decimals(axis_val)
            data_dict[col_name] = [active_map_values[i] if i < len(active_map_values) else 0.0]
        
        # Criar DataFrame horizontal com uma única linha de valores
        df = pd.DataFrame(data_dict)
        
        # Configurar colunas dinamicamente com formatação 3 casas decimais
        column_config = {}
        value_format = "%.3f"  # Sempre 3 casas decimais
            
        for col in df.columns:
            column_config[col] = st.column_config.NumberColumn(
                col,  # Valor numérico puro
                format=value_format,
                min_value=map_info["min_value"],
                max_value=map_info["max_value"],
                help=f"{map_info['axis_type']}: {col}, Valor em {map_info['unit']}"
            )
        
        # Editor de tabela horizontal com gradiente de cores
        st.write(f"**Editar valores do mapa** ({map_info['unit']})")
        st.caption(f"Valores com 3 casas decimais - Total: {len(df.columns)} valores")
        
        # Aplicar formatação de 3 casas decimais ao DataFrame para exibição
        formatted_df = df.copy()
        for col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(lambda x: round(x, 3))
        
        # Aplicar estilo com gradiente de cores na linha de valores
        styled_df = formatted_df.style.background_gradient(
            cmap='RdYlBu',  # Red-Yellow-Blue (vermelho para valores baixos, azul para altos)
            axis=1,  # Aplicar gradiente ao longo das colunas (horizontal)
            vmin=min(formatted_df.iloc[0].values),  # Usar valores reais do DataFrame
            vmax=max(formatted_df.iloc[0].values),  # Usar valores reais do DataFrame
            subset=None  # Aplicar a todas as células
        )
        
        # Adicionar formato de exibição com 3 casas decimais
        styled_df = styled_df.format("{:.3f}")
        
        # Usar st.dataframe com estilo para mostrar cores
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Editor de dados (sem cores mas funcional)
        st.caption("Clique nos valores abaixo para editar:")
        edited_df = st.data_editor(
            df,
            num_rows="fixed",
            use_container_width=True,
            column_config=column_config,
            key=f"data_editor_{session_key}",
            hide_index=True
        )
        
        # Atualizar dados na sessão
        # Manter os valores do eixo X originais (não editáveis nesta versão)
        st.session_state[session_key]["axis_values"] = current_data["axis_values"]
        # Extrair os valores editados do mapa
        new_values = []
        for col in df.columns:
            new_values.append(edited_df[col].iloc[0])
        st.session_state[session_key]["map_values"] = new_values
    
    
        # Validações
        axis_valid, axis_msg = validate_map_values(
            current_data["axis_values"], 
            -1000, 10000  # Validação genérica ampla
        )
        values_valid, values_msg = validate_map_values(
            new_values,
            map_info["min_value"],
            map_info["max_value"]
        )
        
        if not axis_valid:
            st.error(f"Eixo X: {axis_msg}")
        if not values_valid:
            st.error(f"Valores: {values_msg}")
        
        # Formulário para salvar
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
            
            if save_button:
                if axis_valid and values_valid:
                    success = save_map_data(
                        selected_vehicle_id,
                        selected_map_type,
                        selected_bank or "shared",
                        current_data["axis_values"],
                        new_values,
                        current_data.get("axis_enabled")
                    )
                    if success:
                        st.success("Mapa salvo com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar o mapa")
                else:
                    st.error("Corrija os erros de validação antes de salvar")
            
            if reset_button:
                # Restaurar valores padrão
                axis_enabled = get_default_enabled_positions(map_info["axis_type"], map_info["positions"], selected_map_type)
                st.session_state[session_key] = {
                    "axis_values": get_default_axis_values(
                        map_info["axis_type"], 
                        map_info["positions"]
                    ),
                    "map_values": get_default_map_values(
                        selected_map_type,
                        map_info["axis_type"], 
                        map_info["positions"]
                    ),
                    "axis_enabled": axis_enabled
                }
                st.success("Valores padrão restaurados!")
                st.rerun()
    
    with edit_tab2:
        st.caption("Configure os eixos com sistema enable/disable")
        
        # Configurar eixos com checkboxes
        st.write(f"**Configurar Eixo X ({map_info['axis_type']})** - {map_info['positions']} posições")
        st.caption("Use os checkboxes para ativar/desativar cada posição")
        
        # Garantir que temos o número correto de posições
        axis_values_temp = current_data["axis_values"].copy()
        total_positions = map_info["positions"]
        axis_values = [0.0] * total_positions
        for i in range(min(len(axis_values_temp), total_positions)):
            axis_values[i] = axis_values_temp[i]
        
        axis_enabled_values = current_data.get("axis_enabled", [True] * total_positions)
        
        # Determinar formato baseado no tipo de eixo
        if map_info["axis_type"] == "MAP":
            step = 0.01
            format_str = "%.3f"
        elif map_info["axis_type"] in ["VOLTAGE"]:
            step = 0.1
            format_str = "%.3f"
        else:
            step = 1.0 if map_info["axis_type"] in ["RPM", "TPS"] else 5.0
            format_str = "%.3f"
        
        # Criar DataFrame para edição
        axis_df = pd.DataFrame({
            "Ativo": axis_enabled_values[:total_positions],
            "Posição": [f"Pos {i+1}" for i in range(total_positions)],
            f"{map_info['axis_type']}": axis_values
        })
        
        # Editor de tabela
        edited_axis_df = st.data_editor(
            axis_df,
            column_config={
                "Ativo": st.column_config.CheckboxColumn(
                    "Ativo",
                    help="Marque para ativar esta posição",
                    default=False,
                    width="small"
                ),
                "Posição": st.column_config.TextColumn(
                    "Posição",
                    disabled=True,
                    width="small"
                ),
                f"{map_info['axis_type']}": st.column_config.NumberColumn(
                    f"{map_info['axis_type']}",
                    help=f"Valor do {map_info['axis_type']}",
                    format=format_str,
                    step=step,
                    width="medium"
                )
            },
            hide_index=True,
            use_container_width=True,
            height=400,
            key=f"axis_editor_{session_key}"
        )
        
        # Extrair valores editados
        new_axis_values = edited_axis_df[f"{map_info['axis_type']}"].tolist()
        new_axis_enabled = edited_axis_df["Ativo"].tolist()
        
        # Atualizar dados na sessão
        st.session_state[session_key]["axis_values"] = new_axis_values
        st.session_state[session_key]["axis_enabled"] = new_axis_enabled
        
        # Botão para aplicar apenas valores ativos
        if st.button("Aplicar Valores Ativos", key=f"apply_active_{session_key}"):
            # Filtrar apenas valores ativos
            active_axis = get_active_values(new_axis_values, new_axis_enabled)
            active_map = get_active_values(
                st.session_state[session_key]["map_values"] if len(st.session_state[session_key]["map_values"]) >= len(active_axis) else 
                get_default_map_values(selected_map_type, map_info["axis_type"], map_info["positions"])[:len(active_axis)],
                new_axis_enabled
            )
            
            # Garantir que temos valores de mapa suficientes
            while len(active_map) < len(active_axis):
                active_map.append(0.0)
            
            st.session_state[session_key]["axis_values"] = active_axis
            st.session_state[session_key]["map_values"] = active_map[:len(active_axis)]
            st.success(f"Aplicados {len(active_axis)} valores ativos!")
            st.rerun()
    
with tab2:
    st.caption("Visualização gráfica do mapa")
    
    if session_key in st.session_state:
        current_data = st.session_state[session_key]
        axis_values = current_data["axis_values"]
        map_values = current_data["map_values"]
        
        # Criar gráfico com gradiente de cores
        fig = go.Figure()
        
        # Normalizar valores para escala de cores
        min_val = min(map_values)
        max_val = max(map_values)
        norm_values = [(v - min_val) / (max_val - min_val) if max_val > min_val else 0.5 
                      for v in map_values]
        
        fig.add_trace(go.Scatter(
            x=axis_values,
            y=map_values,
            mode='lines+markers',
            name='Mapa',
            line=dict(
                width=3,
                color='rgba(100, 100, 100, 0.7)'  # Linha cinza semi-transparente
            ),
            marker=dict(
                size=10,
                color=map_values,  # Usar valores para colorir
                colorscale='RdYlBu',  # Red-Yellow-Blue (vermelho para baixo, azul para alto)
                cmin=min(map_values),  # Usar valores reais
                cmax=max(map_values),  # Usar valores reais
                showscale=True,
                colorbar=dict(
                    title=map_info["unit"],
                    tickmode='linear',
                    tick0=map_info["min_value"],
                    dtick=(map_info["max_value"] - map_info["min_value"]) / 10
                ),
                line=dict(width=1, color='white')
            )
        ))
        
        fig.update_layout(
            title=f"Visualização - {map_info['name']}",
            xaxis_title=f"Eixo X ({map_info['axis_type']})",
            yaxis_title=f"Valor ({map_info['unit']})",
            height=500,
            showlegend=False,
            hovermode='closest'
        )
        
        # Configurar grid
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas do mapa
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        # Formatação sempre com 3 casas decimais
        decimal_places = 3
        
        with col_stats1:
            st.metric(
                "Valor Mínimo",
                f"{min(map_values):.{decimal_places}f} {map_info['unit']}"
            )
        
        with col_stats2:
            st.metric(
                "Valor Máximo",
                f"{max(map_values):.{decimal_places}f} {map_info['unit']}"
            )
        
        with col_stats3:
            st.metric(
                "Valor Médio",
                f"{np.mean(map_values):.{decimal_places}f} {map_info['unit']}"
            )
        
        # Adicionar linha com desvio padrão
        col_stats4, col_stats5, col_stats6 = st.columns(3)
        
        with col_stats4:
            st.metric(
                "Desvio Padrão",
                f"{np.std(map_values):.{decimal_places}f} {map_info['unit']}"
            )
        
        with col_stats5:
            st.metric(
                "Amplitude",
                f"{max(map_values) - min(map_values):.{decimal_places}f} {map_info['unit']}"
            )
        
        with col_stats6:
            st.metric(
                "Total de Pontos",
                f"{len(map_values)}"
            )
    
    else:
        st.info("Configure o mapa na aba 'Editar' para ver a visualização")
    
with tab3:
    st.caption("Importar e exportar dados do mapa")
    
    # Seções organizadas
    section_tabs = st.tabs(["Copiar FTManager", "Colar FTManager", "Importar Dados", "Exportar Dados"])
    
    with section_tabs[0]:  # Copiar para FTManager
        st.subheader("Copiar para FTManager")
        
        if session_key in st.session_state:
            current_data = st.session_state[session_key]
            
            st.caption("Copie os valores formatados para colar no FTManager")
            
            # Gerar string para copiar (formato FTManager com 3 casas decimais)
            ftm_values = []
            for val in current_data["map_values"]:
                # Formatar valor com vírgula como separador decimal (3 casas)
                formatted = f"{val:.3f}".replace('.', ',')
                ftm_values.append(formatted)
            
            # Criar string com TAB entre valores (formato FTManager)
            ftm_string = "\t".join(ftm_values)
            
            # Área de texto para copiar
            text_area_copy = st.text_area(
                "Valores formatados para FTManager",
                value=ftm_string,
                height=100,
                key=f"copy_ftm_{session_key}",
                help="Valores separados por TAB, prontos para FTManager"
            )
            
            # Botão para copiar para área de transferência
            if st.button("Copiar para Área de Transferência", key=f"copy_clipboard_{session_key}", use_container_width=True):
                # Usar componente HTML com JavaScript para copiar
                # Escapar tabs para JavaScript
                ftm_string_js = ftm_string.replace('\\', '\\\\').replace('\t', '\\t').replace('`', '\\`')
                components.html(
                    f"""
                    <script>
                    const text = "{ftm_string_js}";
                    navigator.clipboard.writeText(text).then(function() {{
                        console.log('Copiado para área de transferência');
                    }}, function(err) {{
                        console.error('Erro ao copiar: ', err);
                    }});
                    </script>
                    """,
                    height=0
                )
                st.success("Valores copiados para a área de transferência!")
        else:
            st.info("Configure o mapa na aba 'Editar' para copiar valores")
    
    with section_tabs[1]:  # Colar do FTManager
        st.subheader("Colar do FTManager")
        
        st.caption("Cole os valores copiados do FTManager")
        
        # Área para colar valores do FTManager
        paste_text = st.text_area(
            "Cole os valores aqui",
            placeholder="Cole aqui os valores copiados do FTManager...",
            height=100,
            key=f"paste_ftm_{session_key}",
            help="Aceita valores separados por TAB, espaços ou ponto-e-vírgula"
        )
        
        # Botões em duas colunas
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button("Aplicar Valores", key=f"apply_paste_{session_key}", use_container_width=True):
                if paste_text:
                    try:
                        # Processar valores colados - aceitar TAB, espaços ou ponto-e-vírgula
                        # Substituir tabs e ponto-e-vírgula por espaços
                        normalized_text = paste_text.replace('\t', ' ').replace(';', ' ')
                        # Remover espaços extras e dividir
                        values_str = normalized_text.strip().split()
                        # Converter vírgulas para pontos e para float
                        new_values = [float(v.replace(',', '.')) for v in values_str]
                        
                        # Verificar quantidade de valores
                        if session_key in st.session_state:
                            current_positions = len(st.session_state[session_key]["axis_values"])
                            if len(new_values) == current_positions:
                                # Aplicar valores
                                st.session_state[session_key]["map_values"] = new_values
                                st.success(f"Aplicados {len(new_values)} valores com sucesso!")
                                st.rerun()
                            else:
                                st.error(f"Esperados {current_positions} valores, mas foram colados {len(new_values)}")
                        else:
                            st.error("Configure o mapa primeiro na aba 'Editar'")
                    except Exception as e:
                        st.error(f"Erro ao processar valores: {e}")
                else:
                    st.warning("Cole os valores primeiro")
        
        with btn_col2:
            if st.button("Limpar", key=f"clear_paste_{session_key}", use_container_width=True):
                # Limpar a área de texto
                st.session_state[f"paste_ftm_{session_key}"] = ""
                st.rerun()
    
    with section_tabs[2]:  # Importar Dados
        st.subheader("Importar Dados")
        
        # Upload de arquivo
        uploaded_file = st.file_uploader(
            "Arquivo de mapa",
            type=['json', 'csv'],
            help="Formatos suportados: JSON, CSV",
            key=f"upload_{session_key}"
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.json'):
                    data = json.loads(uploaded_file.read())
                    if "axis_values" in data and "map_values" in data:
                        if (len(data["axis_values"]) == map_info["positions"] and 
                            len(data["map_values"]) == map_info["positions"]):
                            
                            if st.button("Importar JSON", key=f"import_json_{session_key}"):
                                st.session_state[session_key] = {
                                    "axis_values": data["axis_values"],
                                    "map_values": data["map_values"]
                                }
                                st.success("Dados importados com sucesso!")
                                st.rerun()
                        else:
                            st.error(f"Arquivo deve conter {map_info['positions']} valores")
                    else:
                        st.error("Formato JSON inválido")
                
                elif uploaded_file.name.endswith('.csv'):
                    df_import = pd.read_csv(uploaded_file)
                    if len(df_import) == map_info["positions"]:
                        required_cols = ["axis_x", "value"]
                        if all(col in df_import.columns for col in required_cols):
                            if st.button("Importar CSV", key=f"import_csv_{session_key}"):
                                st.session_state[session_key] = {
                                    "axis_values": df_import["axis_x"].tolist(),
                                    "map_values": df_import["value"].tolist()
                                }
                                st.success("Dados importados com sucesso!")
                                st.rerun()
                        else:
                            st.error("CSV deve ter colunas: axis_x, value")
                    else:
                        st.error(f"CSV deve ter {map_info['positions']} linhas")
            
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {str(e)}")
    
    with section_tabs[3]:  # Exportar Dados
        st.subheader("Exportar Dados")
        
        if session_key in st.session_state:
            current_data = st.session_state[session_key]
            
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                # Exportar JSON
                export_data = {
                    "vehicle_id": selected_vehicle_id,
                    "map_type": selected_map_type,
                    "bank_id": selected_bank,
                    "map_info": map_info,
                    "axis_values": current_data["axis_values"],
                    "map_values": current_data["map_values"],
                    "axis_enabled": current_data.get("axis_enabled"),
                    "exported_at": pd.Timestamp.now().isoformat()
                }
                
                st.download_button(
                    "Exportar JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"mapa_2d_{selected_map_type}_{selected_vehicle_id}.json",
                    mime="application/json",
                    use_container_width=True,
                    key=f"export_json_{session_key}"
                )
            
            with col_export2:
                # Exportar CSV - usar apenas o tamanho real dos dados habilitados
                # Garantir que ambos os arrays tenham o mesmo tamanho
                axis_values = current_data.get("axis_values", [])
                map_values = current_data.get("map_values", [])
                
                # Usar o menor tamanho para evitar erro
                num_values = min(len(axis_values), len(map_values))
                
                if num_values > 0:
                    export_df = pd.DataFrame({
                        "posicao": range(1, num_values + 1),
                        "axis_x": axis_values[:num_values],
                        "value": map_values[:num_values]
                    })
                else:
                    # DataFrame vazio se não houver dados
                    export_df = pd.DataFrame({
                        "posicao": [],
                        "axis_x": [],
                        "value": []
                    })
                
                st.download_button(
                    "Exportar CSV",
                    data=export_df.to_csv(index=False),
                    file_name=f"mapa_2d_{selected_map_type}_{selected_vehicle_id}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key=f"export_csv_{session_key}"
                )
        
        else:
            st.info("Configure o mapa na aba 'Editar' para exportar")

# Rodapé com informações
st.markdown("---")
st.caption("Sistema FuelTune - Mapas de Injeção 2D | Versão 1.0")