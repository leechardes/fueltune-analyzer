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
    """Retorna valores padrão arredondados para o eixo baseado no tipo e número de posições."""
    if axis_type == "MAP":
        # Valores MAP arredondados de -1.0 a 2.5 bar
        values = np.linspace(-1.0, 2.5, positions)
        # Arredondar para 1 casa decimal
        return [round(v, 1) for v in values]
    elif axis_type == "TPS":
        # Valores TPS arredondados de 0 a 100%
        values = np.linspace(0, 100, positions)
        # Arredondar para inteiros
        return [round(v) for v in values]
    elif axis_type == "RPM":
        # Valores RPM arredondados de 500 a 8000
        values = np.linspace(500, 8000, positions)
        # Arredondar para múltiplos de 250
        return [round(v/250)*250 for v in values]
    elif axis_type == "TEMP":
        # Valores temperatura arredondados de -10 a 120°C
        values = np.linspace(-10, 120, positions)
        # Arredondar para múltiplos de 5
        return [round(v/5)*5 for v in values]
    elif axis_type == "AIR_TEMP":
        # Valores temperatura do ar arredondados de -20 a 60°C
        values = np.linspace(-20, 60, positions)
        # Arredondar para múltiplos de 5
        return [round(v/5)*5 for v in values]
    elif axis_type == "VOLTAGE":
        # Valores tensão arredondados de 8 a 16V
        values = np.linspace(8, 16, positions)
        # Arredondar para 0.5V
        return [round(v*2)/2 for v in values]
    else:
        return list(range(positions))

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

# Configurações no topo
st.subheader("Configuração do Mapa")

# Layout de configurações em colunas
config_col1, config_col2, config_col3, config_col4 = st.columns([2, 2, 1, 1])

with config_col1:
    # Seleção de veículo
    vehicles = load_vehicles()
    if vehicles:
        vehicle_options = {v["id"]: f"{v['name']} ({v['nickname']})" for v in vehicles}
        selected_vehicle_id = st.selectbox(
            "Veículo",
            options=list(vehicle_options.keys()),
            format_func=lambda x: vehicle_options[x],
            key="vehicle_selector"
        )
    else:
        st.error("Nenhum veículo encontrado no banco de dados")
        st.stop()

with config_col2:
    # Seleção de tipo de mapa
    selected_map_type = st.selectbox(
        "Tipo de Mapa 2D",
        options=list(MAP_TYPES_2D.keys()),
        format_func=lambda x: MAP_TYPES_2D[x]["name"],
        key="map_type_selector"
    )

with config_col3:
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
        st.info("Compartilhado")

with config_col4:
    # Informações do mapa
    map_info = MAP_TYPES_2D[selected_map_type]
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
    
    # Expander para editar valores do eixo X
    with st.expander("⚙️ Configurar Eixo X"):
        st.write(f"**Editar valores do eixo X** ({map_info['axis_type']})")
        st.caption("Deixe vazio ou coloque 0 para desabilitar uma posição")
        
        # Criar colunas para os inputs
        num_cols = min(4, map_info["positions"])  # Máximo 4 colunas por linha
        cols = st.columns(num_cols)
        
        new_axis_values = []
        enabled_positions = []
        
        for i in range(map_info["positions"]):
            col_idx = i % num_cols
            with cols[col_idx]:
                # Container para cada posição
                container = st.container()
                with container:
                    # Checkbox para habilitar/desabilitar
                    current_value = current_data["axis_values"][i] if i < len(current_data["axis_values"]) else None
                    is_enabled = st.checkbox(
                        f"Pos {i+1}",
                        value=(current_value is not None and current_value != 0),
                        key=f"enable_{session_key}_{i}"
                    )
                    
                    if is_enabled:
                        value = st.number_input(
                            f"Valor",
                            value=float(current_value) if current_value else 0.0,
                            step=0.1 if map_info["axis_type"] in ["MAP", "VOLTAGE"] else 1.0,
                            key=f"axis_input_{session_key}_{i}",
                            label_visibility="collapsed"
                        )
                        new_axis_values.append(value)
                        enabled_positions.append(i)
                    else:
                        # Posição desabilitada
                        st.caption("Desabilitado")
        
        # Botão para aplicar e ordenar
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Aplicar e Ordenar", key=f"apply_axis_{session_key}", use_container_width=True):
                if new_axis_values:  # Só processar se houver valores habilitados
                    # Pegar apenas os valores correspondentes às posições habilitadas
                    enabled_map_values = [current_data["map_values"][i] for i in enabled_positions 
                                        if i < len(current_data["map_values"])]
                    
                    # Criar pares (eixo, valor) para manter correspondência
                    pairs = list(zip(new_axis_values, enabled_map_values))
                    # Ordenar por valores do eixo X
                    pairs.sort(key=lambda x: x[0])
                    # Separar novamente
                    sorted_axis = [p[0] for p in pairs]
                    sorted_values = [p[1] for p in pairs]
                    # Atualizar session state com apenas valores habilitados
                    st.session_state[session_key]["axis_values"] = sorted_axis
                    st.session_state[session_key]["map_values"] = sorted_values
                    st.rerun()
                else:
                    st.warning("Habilite pelo menos uma posição!")
        
        with col2:
            if st.button("Restaurar Todas", key=f"restore_all_{session_key}", use_container_width=True):
                # Restaurar valores padrão completos
                st.session_state[session_key]["axis_values"] = get_default_axis_values(
                    map_info["axis_type"], 
                    map_info["positions"]
                )
                st.session_state[session_key]["map_values"] = get_default_map_values(
                    selected_map_type, 
                    map_info["positions"]
                )
                st.rerun()
    
    # Criar DataFrame horizontal - os valores do eixo X como colunas
    # Criar dicionário com os valores do eixo X como chaves
    data_dict = {}
    for i, axis_val in enumerate(current_data["axis_values"]):
        # Usar string formatada como nome da coluna
        col_name = f"{axis_val:.1f}" if axis_val % 1 != 0 else str(int(axis_val))
        data_dict[col_name] = [current_data["map_values"][i]]
    
    # Criar DataFrame horizontal com uma única linha de valores
    df = pd.DataFrame(data_dict)
    
    # Configurar colunas dinamicamente com formato apropriado
    column_config = {}
    # Definir formato baseado no tipo de dado
    if map_info["unit"] == "ms":  # Tempo de injeção
        value_format = "%.3f"  # Máximo 3 casas decimais
    elif map_info["unit"] == "%":  # Percentual (TPS, compensações)
        value_format = "%.1f"  # 1 casa decimal
    else:
        value_format = "%.2f"  # Padrão 2 casas
        
    for col in df.columns:
        column_config[col] = st.column_config.NumberColumn(
            col,  # O nome da coluna é o valor do eixo X
            format=value_format,
            min_value=map_info["min_value"],
            max_value=map_info["max_value"],
            help=f"{map_info['axis_type']}: {col}, Valor em {map_info['unit']}"
        )
    
    # Editor de tabela horizontal com gradiente de cores
    st.write(f"**Editar valores do mapa** ({map_info['unit']})")
    st.caption(f"Eixo X: {map_info['axis_type']}")
    
    # Aplicar formatação de decimais ao DataFrame para exibição
    formatted_df = df.copy()
    for col in formatted_df.columns:
        if map_info["unit"] == "ms":  # Tempo de injeção
            formatted_df[col] = formatted_df[col].apply(lambda x: round(x, 3))
        elif map_info["unit"] == "%":  # Percentual
            formatted_df[col] = formatted_df[col].apply(lambda x: round(x, 1))
        else:
            formatted_df[col] = formatted_df[col].apply(lambda x: round(x, 2))
    
    # Aplicar estilo com gradiente de cores na linha de valores
    styled_df = formatted_df.style.background_gradient(
        cmap='RdYlBu',  # Red-Yellow-Blue (vermelho para valores baixos, azul para altos)
        axis=1,  # Aplicar gradiente ao longo das colunas (horizontal)
        vmin=min(formatted_df.iloc[0].values),  # Usar valores reais do DataFrame
        vmax=max(formatted_df.iloc[0].values),  # Usar valores reais do DataFrame
        subset=None  # Aplicar a todas as células
    )
    
    # Adicionar formato de exibição
    if map_info["unit"] == "ms":
        styled_df = styled_df.format("{:.3f}")
    elif map_info["unit"] == "%":
        styled_df = styled_df.format("{:.1f}")
    else:
        styled_df = styled_df.format("{:.2f}")
    
    # Usar st.dataframe com estilo para mostrar cores
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Botões de copiar/colar compatível com FTManager
    st.write("**Integração com FTManager**")
    col_copy_paste1, col_copy_paste2 = st.columns(2)
    
    with col_copy_paste1:
        st.caption("Copiar valores para FTManager")
        
        # Gerar string para copiar (formato FTManager)
        ftm_values = []
        for val in current_data["map_values"]:
            # Formatar valor com vírgula como separador decimal
            if map_info["unit"] == "ms":
                formatted = f"{val:.3f}".replace('.', ',')
            elif map_info["unit"] == "%":
                formatted = f"{val:.1f}".replace('.', ',')
            else:
                formatted = f"{val:.2f}".replace('.', ',')
            ftm_values.append(formatted)
        
        # Criar string com TAB entre valores (formato FTManager)
        ftm_string = "\t".join(ftm_values)
        
        # Área de texto para copiar
        text_area_copy = st.text_area(
            "Valores formatados",
            value=ftm_string,
            height=60,
            key=f"copy_ftm_{session_key}",
            help="Valores separados por TAB, prontos para FTManager",
            label_visibility="collapsed"
        )
        
        # Botão para copiar para área de transferência
        if st.button("📋 Copiar para Área de Transferência", key=f"copy_clipboard_{session_key}", use_container_width=True):
            # Usar componente HTML com JavaScript para copiar
            components.html(
                f"""
                <script>
                const text = `{ftm_string}`;
                navigator.clipboard.writeText(text).then(function() {{
                    console.log('Copiado para área de transferência');
                }}, function(err) {{
                    console.error('Erro ao copiar: ', err);
                }});
                </script>
                """,
                height=0
            )
            st.success("✅ Valores copiados para a área de transferência!")
    
    with col_copy_paste2:
        st.caption("Colar valores do FTManager")
        
        # Área para colar valores do FTManager
        paste_text = st.text_area(
            "Cole os valores aqui",
            placeholder="Cole aqui os valores copiados do FTManager...",
            height=60,
            key=f"paste_ftm_{session_key}",
            help="Aceita valores separados por TAB, espaços ou ponto-e-vírgula",
            label_visibility="collapsed"
        )
        
        # Botões em duas colunas
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button("✅ Aplicar Valores", key=f"apply_paste_{session_key}", use_container_width=True):
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
                        current_positions = len(current_data["axis_values"])
                        if len(new_values) == current_positions:
                            # Aplicar valores
                            st.session_state[session_key]["map_values"] = new_values
                            st.success(f"Aplicados {len(new_values)} valores com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"Esperados {current_positions} valores, mas foram colados {len(new_values)}")
                    except Exception as e:
                        st.error(f"Erro ao processar valores: {e}")
                else:
                    st.warning("Cole os valores primeiro")
        
        with btn_col2:
            if st.button("🗑️ Limpar", key=f"clear_paste_{session_key}", use_container_width=True):
                # Limpar a área de texto
                st.session_state[f"paste_ftm_{session_key}"] = ""
                st.rerun()
    
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
                    new_values
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
        
        # Formatação de decimais baseada no tipo de unidade
        if map_info["unit"] == "ms":
            decimal_places = 3
        elif map_info["unit"] == "%":
            decimal_places = 1
        else:
            decimal_places = 2
        
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
            
            # Exportar CSV - usar apenas o tamanho real dos dados habilitados
            num_values = len(current_data["axis_values"])
            export_df = pd.DataFrame({
                "posicao": range(1, num_values + 1),
                "axis_x": current_data["axis_values"][:num_values],
                "value": current_data["map_values"][:num_values]
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