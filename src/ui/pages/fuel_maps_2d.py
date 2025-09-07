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
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import plotly.graph_objects as go
import json

# Importações do projeto
try:
    from src.data.vehicle_database import get_all_vehicles, get_vehicle_by_id
    from src.data.fuel_maps_models import (
        create_default_main_fuel_2d_map,
        create_default_rpm_compensation_map,
        create_default_temp_compensation_map,
        MapDataValidator,
        MapInterpolator
    )
except ImportError:
    # Fallback para desenvolvimento
    pass

# Configuração da página
st.title("Mapas de Injeção 2D")
st.caption("Configure mapas de injeção bidimensionais")

# Constantes para tipos de mapas 2D
MAP_TYPES_2D = {
    "main_fuel_2d_map_32": {
        "name": "Mapa Principal de Injeção (MAP) - 32 posições",
        "positions": 32,
        "axis_type": "MAP",
        "unit": "ms",
        "min_value": 0.0,
        "max_value": 50.0,
        "description": "Mapa principal baseado na pressão MAP"
    },
    "main_fuel_2d_tps_20": {
        "name": "Mapa Principal de Injeção (TPS) - 20 posições",
        "positions": 20,
        "axis_type": "TPS",
        "unit": "ms",
        "min_value": 0.0,
        "max_value": 50.0,
        "description": "Mapa principal baseado na posição do acelerador"
    },
    "rpm_compensation_32": {
        "name": "Compensação por RPM - 32 posições",
        "positions": 32,
        "axis_type": "RPM",
        "unit": "%",
        "min_value": -100.0,
        "max_value": 100.0,
        "description": "Compensação baseada no RPM do motor"
    },
    "temp_compensation_16": {
        "name": "Compensação por Temperatura do Motor - 16 posições",
        "positions": 16,
        "axis_type": "TEMP",
        "unit": "%",
        "min_value": -100.0,
        "max_value": 100.0,
        "description": "Compensação baseada na temperatura do motor"
    },
    "air_temp_compensation_9": {
        "name": "Compensação por Temperatura do Ar - 9 posições",
        "positions": 9,
        "axis_type": "AIR_TEMP",
        "unit": "%",
        "min_value": -100.0,
        "max_value": 100.0,
        "description": "Compensação baseada na temperatura do ar"
    },
    "voltage_compensation_8": {
        "name": "Compensação por Tensão de Bateria - 8 posições",
        "positions": 8,
        "axis_type": "VOLTAGE",
        "unit": "%",
        "min_value": -100.0,
        "max_value": 100.0,
        "description": "Compensação baseada na tensão da bateria"
    }
}

def get_default_axis_values(axis_type: str, positions: int) -> List[float]:
    """Retorna valores padrão para o eixo baseado no tipo e número de posições."""
    if axis_type == "MAP":
        # Valores MAP de -1.0 a 2.0 bar
        return list(np.linspace(-1.0, 2.0, positions))
    elif axis_type == "TPS":
        # Valores TPS de 0 a 100%
        return list(np.linspace(0, 100, positions))
    elif axis_type == "RPM":
        # Valores RPM de 400 a 8000
        return list(np.linspace(400, 8000, positions))
    elif axis_type == "TEMP":
        # Valores temperatura de -10 a 120°C
        return list(np.linspace(-10, 120, positions))
    elif axis_type == "AIR_TEMP":
        # Valores temperatura do ar de -20 a 60°C
        return list(np.linspace(-20, 60, positions))
    elif axis_type == "VOLTAGE":
        # Valores tensão de 8 a 16V
        return list(np.linspace(8, 16, positions))
    else:
        return list(np.linspace(0, positions-1, positions))

def get_default_map_values(map_type: str, positions: int) -> List[float]:
    """Retorna valores padrão para o mapa baseado no tipo."""
    if "main_fuel" in map_type:
        # Valores de injeção típicos (5-15ms)
        return list(np.linspace(5.0, 15.0, positions))
    elif "compensation" in map_type:
        # Valores de compensação (0% inicial)
        return [0.0] * positions
    else:
        return [0.0] * positions

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
                  axis_values: List[float], map_values: List[float]) -> bool:
    """Salva dados do mapa no banco de dados (dummy por enquanto)."""
    try:
        # Aqui seria implementada a integração real com o banco
        st.session_state[f"saved_map_{vehicle_id}_{map_type}_{bank_id}"] = {
            "axis_values": axis_values,
            "map_values": map_values,
            "timestamp": pd.Timestamp.now()
        }
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return False

def load_map_data(vehicle_id: str, map_type: str, bank_id: str) -> Optional[Dict]:
    """Carrega dados do mapa do banco de dados (dummy por enquanto)."""
    try:
        key = f"saved_map_{vehicle_id}_{map_type}_{bank_id}"
        return st.session_state.get(key, None)
    except:
        return None

# Layout principal
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Configuração")
    
    # Seleção de veículo
    vehicles = load_vehicles()
    if vehicles:
        vehicle_options = {v["id"]: f"{v['name']} ({v['nickname']})" for v in vehicles}
        selected_vehicle_id = st.selectbox(
            "Selecione o Veículo",
            options=list(vehicle_options.keys()),
            format_func=lambda x: vehicle_options[x],
            key="vehicle_selector"
        )
    else:
        st.error("Nenhum veículo encontrado no banco de dados")
        st.stop()
    
    # Seleção de tipo de mapa
    selected_map_type = st.selectbox(
        "Tipo de Mapa 2D",
        options=list(MAP_TYPES_2D.keys()),
        format_func=lambda x: MAP_TYPES_2D[x]["name"],
        key="map_type_selector"
    )
    
    # Informações do mapa selecionado
    map_info = MAP_TYPES_2D[selected_map_type]
    st.info(f"**Posições:** {map_info['positions']}")
    st.info(f"**Eixo X:** {map_info['axis_type']}")
    st.info(f"**Unidade:** {map_info['unit']}")
    st.caption(map_info["description"])
    
    # Seleção de bancada (se aplicável)
    if "main_fuel" in selected_map_type:
        selected_bank = st.radio(
            "Bancada",
            options=["A", "B"],
            key="bank_selector"
        )
    else:
        selected_bank = None
        st.caption("Mapa compartilhado entre bancadas")

with col2:
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
                st.session_state[session_key] = {
                    "axis_values": loaded_data["axis_values"],
                    "map_values": loaded_data["map_values"]
                }
            else:
                # Criar dados padrão
                st.session_state[session_key] = {
                    "axis_values": get_default_axis_values(
                        map_info["axis_type"], 
                        map_info["positions"]
                    ),
                    "map_values": get_default_map_values(
                        selected_map_type, 
                        map_info["positions"]
                    )
                }
        
        current_data = st.session_state[session_key]
        
        # Criar DataFrame horizontal - os valores do eixo X como colunas
        # Primeira linha: valores do eixo X (editáveis)
        # Segunda linha: valores do mapa correspondentes
        
        # Criar dicionário com os valores do eixo X como chaves
        data_dict = {}
        for i, axis_val in enumerate(current_data["axis_values"]):
            # Usar string formatada como nome da coluna
            col_name = f"{axis_val:.1f}" if axis_val % 1 != 0 else str(int(axis_val))
            data_dict[col_name] = [current_data["map_values"][i]]
        
        # Criar DataFrame horizontal com uma única linha de valores
        df = pd.DataFrame(data_dict)
        
        # Configurar colunas dinamicamente
        column_config = {}
        for col in df.columns:
            column_config[col] = st.column_config.NumberColumn(
                col,  # O nome da coluna é o valor do eixo X
                format="%.3f",
                min_value=map_info["min_value"],
                max_value=map_info["max_value"],
                help=f"{map_info['axis_type']}: {col}, Valor em {map_info['unit']}"
            )
        
        # Editor de tabela horizontal
        st.write(f"**Editar valores do mapa** ({map_info['unit']})")
        st.caption(f"Eixo X: {map_info['axis_type']}")
        edited_df = st.data_editor(
            df,
            num_rows="fixed",
            use_container_width=True,
            column_config=column_config,
            key=f"data_editor_{session_key}"
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
                        edited_df["Eixo X"].tolist(),
                        edited_df["Valor"].tolist()
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
                st.session_state[session_key] = {
                    "axis_values": get_default_axis_values(
                        map_info["axis_type"], 
                        map_info["positions"]
                    ),
                    "map_values": get_default_map_values(
                        selected_map_type, 
                        map_info["positions"]
                    )
                }
                st.success("Valores padrão restaurados!")
                st.rerun()
    
    with tab2:
        st.caption("Visualização gráfica do mapa")
        
        if session_key in st.session_state:
            current_data = st.session_state[session_key]
            axis_values = current_data["axis_values"]
            map_values = current_data["map_values"]
            
            # Criar gráfico
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=axis_values,
                y=map_values,
                mode='lines+markers',
                name='Mapa',
                line=dict(width=2),
                marker=dict(size=6)
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
            
            with col_stats1:
                st.metric(
                    "Valor Mínimo",
                    f"{min(map_values):.3f} {map_info['unit']}"
                )
            
            with col_stats2:
                st.metric(
                    "Valor Máximo",
                    f"{max(map_values):.3f} {map_info['unit']}"
                )
            
            with col_stats3:
                st.metric(
                    "Valor Médio",
                    f"{np.mean(map_values):.3f} {map_info['unit']}"
                )
        
        else:
            st.info("Configure o mapa na aba 'Editar' para ver a visualização")
    
    with tab3:
        st.caption("Importar e exportar dados do mapa")
        
        col_import, col_export = st.columns(2)
        
        with col_import:
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
                    "axis_values": current_data["axis_values"],
                    "map_values": current_data["map_values"],
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
                
                # Exportar CSV
                export_df = pd.DataFrame({
                    "posicao": range(1, map_info["positions"] + 1),
                    "axis_x": current_data["axis_values"],
                    "value": current_data["map_values"]
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