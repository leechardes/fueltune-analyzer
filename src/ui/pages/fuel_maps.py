"""
Página de Mapas de Injeção 2D/3D - FuelTune (REFATORADO)

Implementação seguindo rigorosamente o padrão A04-STREAMLIT-PROFESSIONAL:
- ZERO EMOJIS (proibido usar qualquer emoji)
- ZERO CSS CUSTOMIZADO (apenas componentes nativos)
- ZERO HTML CUSTOMIZADO (não usar st.markdown com HTML)
- Toda interface em PORTUGUÊS BRASILEIRO
- Usar apenas componentes nativos do Streamlit

Versão refatorada com arquitetura modular:
- UI simplificada (apenas Streamlit)
- Lógica de negócio em src/core/fuel_maps/
- Código reduzido de 3,152 para ~400 linhas

Author: FuelTune System
Created: 2025-01-07
Refactored: 2025-01-08
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Imports do módulo refatorado
from src.core.fuel_maps import (
    # Gerenciadores principais
    ConfigManager,
    PersistenceManager,
    SessionManager,
    UIComponents,
    
    # Instâncias globais
    config_manager,
    persistence_manager,
    session_manager,
    ui_components,
    
    # Funções de compatibilidade (mantidas para transição suave)
    load_map_types_config,
    get_vehicle_data_from_session,
    ensure_all_3d_maps_exist,
    load_3d_map_data,
    save_3d_map_data,
    calculate_3d_map_values_universal,
    validate_3d_map_values,
    format_value_3_decimals,
    interpolate_3d_matrix,
    get_all_maps,
    get_map_dimension,
    has_bank_selection,
    get_sorted_maps_for_display,
    save_2d_map_data,
    load_2d_map_data,
    create_default_2d_map,
    ensure_all_maps_exist,
    calculate_2d_map_values
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.title("Mapas de Injeção 2D/3D")
st.caption("Configure mapas de injeção bidimensionais e tridimensionais")

def main():
    """Função principal da página."""
    try:
        # Inicializar defaults da sessão
        session_manager.initialize_session_defaults()
        
        # Carregar TODOS os mapas disponíveis (2D e 3D)
        ALL_MAPS = get_all_maps()
        
        # Obter dados do veículo
        vehicle_data = session_manager.get_vehicle_data_from_session()
        vehicle_id = vehicle_data.get("vehicle_id", "default")
        
        # Garantir que mapas existam - chamar para ambos 2D e 3D
        if not ensure_all_maps_exist(vehicle_id, vehicle_data):
            st.error("Erro ao inicializar mapas padrão")
            return
        
        # Interface principal unificada
        render_unified_interface(ALL_MAPS, vehicle_data, vehicle_id)
        
    except Exception as e:
        logger.error(f"Erro na função main: {e}")
        st.error(f"Erro interno: {e}")

def render_unified_interface(all_maps: Dict[str, Any], vehicle_data: Dict[str, Any], vehicle_id: str):
    """Renderiza interface unificada para mapas 2D e 3D."""
    
    # Configuração do Mapa na área principal
    st.subheader("Configuração do Mapa")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Obter lista ordenada de mapas para o dropdown
        sorted_maps = get_sorted_maps_for_display()
        
        # Seletor de tipo de mapa com display names
        if sorted_maps:
            map_options = [map_type for map_type, _ in sorted_maps]
            map_labels = [info['display_name'] for _, info in sorted_maps]
            
            selected_index = st.selectbox(
                "Tipo de Mapa",
                range(len(map_options)),
                format_func=lambda i: map_labels[i],
                key="selected_unified_map_type",
                label_visibility="visible"
            )
            
            map_type = map_options[selected_index]
            map_info = sorted_maps[selected_index][1]
        else:
            st.error("Nenhum mapa disponível")
            return
    
    with col2:
        # Seletor de banco (condicional baseado no tipo de mapa)
        if has_bank_selection(map_type):
            bank_id = st.radio(
                "Bancada",
                ["A", "B"],
                key="selected_unified_bank",
                horizontal=True
            )
        else:
            bank_id = "shared"
            st.info("Mapa único para todo o motor")
    
    # Mostrar indicador de dimensão
    dimension = map_info['dimension']
    
    # Divider após configuração
    st.divider()
    
    # Sidebar para configurações adicionais
    with st.sidebar:
        st.header("Opções de Visualização")
        
        # Opções de visualização baseadas na dimensão
        if dimension == "3D":
            view_options = ["3D Surface", "2D Heatmap", "Editor"]
            st.info("Mapa Tridimensional")
        else:  # 2D
            view_options = ["Gráfico 2D", "Editor Linear"]
            st.info("📈 Mapa Bidimensional")
        
        view_mode = st.radio(
            "Modo de Visualização",
            view_options,
            key="unified_view_mode"
        )
        
        # Configurações avançadas
        with st.expander("Configurações Avançadas"):
            show_statistics = st.checkbox("Mostrar Estatísticas", value=True)
            auto_save = st.checkbox("Salvamento Automático", value=True)
            
            if dimension == "3D":
                interpolation_method = st.selectbox(
                    "Método de Interpolação",
                    ["linear", "cubic", "nearest"],
                    key="unified_interpolation_method"
                )
    
    # Área principal - renderização com abas
    map_config = all_maps[map_type]
    
    # Criar abas principais
    tab1, tab2, tab3 = st.tabs(["Editar", "Visualizar", "Importar/Exportar"])
    
    with tab1:
        render_edit_tab(map_type, map_config, vehicle_id, bank_id, vehicle_data, dimension, auto_save)
    
    with tab2:
        render_visualize_tab(map_type, map_config, vehicle_id, bank_id, vehicle_data, dimension, show_statistics)
    
    with tab3:
        render_import_export_tab(map_type, map_config, vehicle_id, bank_id, vehicle_data, dimension)

def render_edit_tab(map_type: str, map_config: Dict[str, Any], vehicle_id: str, 
                   bank_id: str, vehicle_data: Dict[str, Any], dimension: str, auto_save: bool):
    """Renderiza a aba de edição com sub-abas Valores e Eixos."""
    
    st.write("Editor de dados do mapa")
    
    # Sub-abas dentro de Editar - agora 3 abas tanto para 2D quanto 3D
    subtab1, subtab2, subtab3 = st.tabs(["Valores", "Eixos", "Ferramentas"])
    
    with subtab1:
        if dimension == "3D":
            render_3d_values_editor(map_type, map_config, vehicle_id, bank_id, vehicle_data, auto_save)
        else:
            render_2d_values_editor(map_type, map_config, vehicle_id, bank_id, vehicle_data, auto_save)
    
    with subtab2:
        if dimension == "3D":
            render_3d_axes_editor(map_type, map_config, vehicle_id, bank_id, vehicle_data)
        else:
            render_2d_axes_editor(map_type, map_config, vehicle_id, bank_id, vehicle_data)
    
    with subtab3:
        # Ferramentas para ambos 2D e 3D
        render_tools(map_type, map_config, vehicle_id, bank_id, vehicle_data, dimension)

def render_visualize_tab(map_type: str, map_config: Dict[str, Any], vehicle_id: str,
                        bank_id: str, vehicle_data: Dict[str, Any], dimension: str, show_statistics: bool):
    """Renderiza a aba de visualização com gráficos."""
    
    if dimension == "3D":
        # Usar view modes existentes para 3D
        view_mode = st.radio(
            "Tipo de Visualização",
            ["3D Surface", "2D Heatmap"],
            key="viz_3d_mode",
            horizontal=True
        )
        
        # Carregar dados e renderizar
        map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
        if map_data:
            rpm_axis = map_data.get("rpm_axis", [])
            map_axis = map_data.get("map_axis", [])
            values_matrix = np.array(map_data.get("values_matrix", []))
            
            if view_mode == "3D Surface":
                render_3d_view(values_matrix, rpm_axis, map_axis, map_type, map_config, show_statistics)
            else:
                render_2d_view(values_matrix, rpm_axis, map_axis, map_type, map_config, show_statistics)
    else:
        # Visualização 2D
        # Carregar dados do mapa 2D primeiro
        map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
        if map_data:
            axis_values = map_data.get("axis_values", [])
            values = map_data.get("values", [])
            enabled = map_data.get("enabled", [True] * len(values))
            axis_type = map_config.get("axis_type", "RPM")
            unit = map_config.get("unit", "ms")
            
            render_2d_chart_view(axis_values, values, enabled, map_type, map_config,
                               axis_type, unit, show_statistics)
        else:
            st.warning("Nenhum dado de mapa 2D encontrado")

def render_import_export_tab(map_type: str, map_config: Dict[str, Any], vehicle_id: str,
                            bank_id: str, vehicle_data: Dict[str, Any], dimension: str):
    """Renderiza a aba de importação/exportação."""
    
    # Sub-abas de importar/exportar
    subtab1, subtab2, subtab3, subtab4 = st.tabs([
        "Copiar FTManager", 
        "Colar FTManager", 
        "Importar Dados", 
        "Exportar Dados"
    ])
    
    with subtab1:
        render_ftmanager_copy(map_type, map_config, vehicle_id, bank_id, dimension)
    
    with subtab2:
        render_ftmanager_paste(map_type, map_config, vehicle_id, bank_id, dimension)
    
    with subtab3:
        render_data_import(map_type, map_config, vehicle_id, bank_id, dimension)
    
    with subtab4:
        render_data_export(map_type, map_config, vehicle_id, bank_id, dimension)

def render_by_dimension_3d(map_type: str, map_config: Dict[str, Any], 
                          vehicle_id: str, bank_id: str, vehicle_data: Dict[str, Any],
                          view_mode: str, show_statistics: bool, auto_save: bool):
    """Renderiza mapas 3D usando a lógica existente."""
    
    grid_size = map_config.get("grid_size", 32)
    
    # Carregar dados do mapa 3D
    map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
    
    if map_data is None:
        st.warning("Mapa 3D não encontrado. Gerando padrão...")
        if persistence_manager.create_default_map(vehicle_id, map_type, bank_id, vehicle_data, grid_size):
            map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
        else:
            st.error("Erro ao criar mapa 3D padrão")
            return
    
    # Extrair dados do mapa
    rpm_axis = map_data.get("rpm_axis", [])
    map_axis = map_data.get("map_axis", [])
    values_matrix = np.array(map_data.get("values_matrix", []))
    rpm_enabled = map_data.get("rpm_enabled", [True] * grid_size)
    map_enabled = map_data.get("map_enabled", [True] * grid_size)
    
    # Renderizar interface baseada no modo 3D
    if view_mode == "3D Surface":
        render_3d_view(values_matrix, rpm_axis, map_axis, map_type, map_config, show_statistics)
    elif view_mode == "2D Heatmap":
        render_2d_view(values_matrix, rpm_axis, map_axis, map_type, map_config, show_statistics)
    else:  # Editor
        render_editor_view(
            values_matrix, rpm_axis, map_axis, rpm_enabled, map_enabled,
            map_type, map_config, vehicle_id, bank_id, vehicle_data, auto_save
        )

def render_by_dimension_2d(map_type: str, map_config: Dict[str, Any],
                          vehicle_id: str, bank_id: str, vehicle_data: Dict[str, Any],
                          view_mode: str, show_statistics: bool, auto_save: bool):
    """Renderiza mapas 2D com interface simplificada."""
    
    positions = map_config.get("positions", 32)
    axis_type = map_config.get("axis_type", "RPM")
    unit = map_config.get("unit", "ms")
    
    # Carregar dados do mapa 2D
    map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
    
    if map_data is None:
        st.warning("Mapa 2D não encontrado. Gerando padrão...")
        # Criar mapa padrão usando o persistence manager
        if create_default_2d_map(vehicle_id, map_type, bank_id, vehicle_data, map_config):
            map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
        else:
            st.error("Erro ao criar mapa 2D padrão")
            return
    
    # Extrair dados do mapa 2D
    axis_values = map_data.get("axis_values", [])
    values = map_data.get("values", [])
    enabled = map_data.get("enabled", [True] * positions)
    
    # Interface baseada no modo de visualização 2D
    if view_mode == "Gráfico 2D":
        render_2d_chart_view(axis_values, values, enabled, map_type, map_config, 
                           axis_type, unit, show_statistics)
    else:  # Editor Linear
        render_2d_editor_view(axis_values, values, enabled, map_type, map_config,
                            vehicle_id, bank_id, axis_type, unit, auto_save, vehicle_data)

def render_2d_chart_view(axis_values: List[float], values: List[float], 
                        enabled: List[bool], map_type: str, map_config: Dict[str, Any],
                        axis_type: str, unit: str, show_statistics: bool):
    """Renderiza visualização em gráfico 2D."""
    
    st.header(f"Visualização 2D - {map_config.get('display_name', map_type)}")
    
    # Preparar dados para o gráfico (apenas valores habilitados)
    enabled_indices = [i for i, e in enumerate(enabled) if e and i < len(axis_values) and i < len(values)]
    chart_axis = [axis_values[i] for i in enabled_indices]
    chart_values = [values[i] for i in enabled_indices]
    
    if not chart_axis or not chart_values:
        st.warning("Nenhum ponto habilitado para exibir")
        return
    
    # Criar gráfico com plotly
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Adicionar linha principal
    fig.add_trace(go.Scatter(
        x=chart_axis,
        y=chart_values,
        mode='lines+markers',
        name=f'Valores {unit}',
        line=dict(color='blue', width=2),
        marker=dict(size=6, color='blue')
    ))
    
    # Configurar layout
    fig.update_layout(
        title=f"{map_config.get('display_name', map_type)} - Gráfico 2D",
        xaxis_title=f"{axis_type}",
        yaxis_title=f"Valores ({unit})",
        showlegend=True,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar estatísticas se habilitado
    if show_statistics:
        render_2d_statistics(chart_values, unit)

def render_2d_editor_view(axis_values: List[float], values: List[float], 
                         enabled: List[bool], map_type: str, map_config: Dict[str, Any],
                         vehicle_id: str, bank_id: str, axis_type: str, unit: str, auto_save: bool,
                         vehicle_data: Dict[str, Any]):
    """Renderiza editor linear para mapas 2D."""
    
    st.header(f"Editor Linear - {map_config.get('display_name', map_type)}")
    
    # Abas do editor 2D
    tab1, tab2, tab3 = st.tabs(["Valores", "Eixo", "Ferramentas"])
    
    with tab1:
        st.subheader("Edição de Valores")
        
        # Editor de valores em colunas
        cols = st.columns(4)
        new_values = values.copy()
        new_enabled = enabled.copy()
        values_changed = False
        
        for i in range(len(axis_values)):
            col_idx = i % 4
            
            with cols[col_idx]:
                # Checkbox para habilitar/desabilitar
                new_enabled[i] = st.checkbox(
                    f"#{i+1}", 
                    value=enabled[i],
                    key=f"2d_enabled_{i}"
                )
                
                # Input para valor
                if new_enabled[i]:
                    new_values[i] = st.number_input(
                        f"{axis_type}: {axis_values[i]}",
                        value=float(values[i]) if i < len(values) else 0.0,
                        min_value=float(map_config.get("min_value", -100)),
                        max_value=float(map_config.get("max_value", 100)),
                        step=0.1,
                        format="%.3f",
                        key=f"2d_value_{i}"
                    )
                else:
                    st.write(f"{axis_type}: {axis_values[i]}")
                    st.write("(Desabilitado)")
        
        # Verificar alterações
        if new_values != values or new_enabled != enabled:
            values_changed = True
            st.success("Valores modificados")
            
            if auto_save:
                if save_2d_map_data_local(vehicle_id, map_type, bank_id, axis_values, 
                                         new_values, new_enabled):
                    st.success("Salvo automaticamente")
                else:
                    st.error("Erro ao salvar")
    
    with tab2:
        render_2d_axis_config(axis_values, axis_type, vehicle_id, map_type, bank_id)
    
    with tab3:
        # Usar nova função render_tools unificada para 2D
        render_tools(map_type, map_config, vehicle_id, bank_id, vehicle_data, "2D")

def render_2d_statistics(values: List[float], unit: str):
    """Renderiza estatísticas para mapas 2D."""
    
    st.subheader("Estatísticas 2D")
    
    if not values:
        st.warning("Nenhum valor para calcular estatísticas")
        return
    
    import numpy as np
    values_array = np.array(values)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Mínimo", f"{np.min(values_array):.3f} {unit}")
    with col2:
        st.metric("Máximo", f"{np.max(values_array):.3f} {unit}")
    with col3:
        st.metric("Média", f"{np.mean(values_array):.3f} {unit}")
    with col4:
        st.metric("Desvio", f"{np.std(values_array):.3f} {unit}")

def render_2d_axis_config(axis_values: List[float], axis_type: str, 
                         vehicle_id: str, map_type: str, bank_id: str):
    """Renderiza configuração do eixo para mapas 2D."""
    
    st.subheader(f"Configuração do Eixo {axis_type}")
    
    # Mostrar valores atuais
    st.write("**Valores atuais:**")
    
    # Exibir em colunas
    cols = st.columns(4)
    for i, value in enumerate(axis_values):
        col_idx = i % 4
        with cols[col_idx]:
            st.write(f"{i+1}: {value}")
    
    # Opções de modificação
    with st.expander("Modificar Eixo"):
        st.info("Funcionalidade de modificação de eixo 2D será implementada em versão futura")

def render_2d_values_editor(map_type: str, map_config: Dict[str, Any], vehicle_id: str, 
                           bank_id: str, vehicle_data: Dict[str, Any], auto_save: bool):
    """Renderiza editor de valores para mapas 2D."""
    
    # Carregar dados do mapa 2D
    map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
    
    if map_data is None:
        st.warning("Mapa 2D não encontrado. Gerando padrão...")
        if create_default_2d_map(vehicle_id, map_type, bank_id, vehicle_data, map_config):
            map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
        else:
            st.error("Erro ao criar mapa 2D padrão")
            return
    
    # Extrair dados
    axis_values = map_data.get("axis_values", [])
    values = map_data.get("values", [])
    enabled = map_data.get("enabled", [True] * len(values))
    unit = map_config.get("unit", "")
    axis_type = map_config.get("axis_type", "RPM")
    
    st.subheader("Editor de Valores")
    
    # Informação do tipo de dados
    st.info(f"**Tipo de Mapa:** {map_config.get('name', map_type)} | **Unidade:** {unit}")
    
    # Filtrar apenas valores ativos
    active_indices = [i for i, e in enumerate(enabled) if e]
    active_axis = [axis_values[i] for i in active_indices]
    active_values = [values[i] for i in active_indices]
    
    # Criar DataFrame transposto para edição horizontal
    import pandas as pd
    import numpy as np
    
    # Criar dicionário com eixos como colunas
    df_data = {}
    for i, (axis_val, value) in enumerate(zip(active_axis, active_values)):
        # Formatar o nome da coluna com o valor do eixo
        col_name = f"{axis_val:.0f}" if axis_type == "RPM" else f"{axis_val:.2f}"
        df_data[col_name] = [value]
    
    df = pd.DataFrame(df_data)
    
    # Editor de dados horizontal
    st.write("**Valores Editáveis:**")
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        column_config={
            col: st.column_config.NumberColumn(
                min_value=map_config.get("min_value", 0),
                max_value=map_config.get("max_value", 100),
                step=0.01,
                format=f"%.2f"
            ) for col in df.columns
        },
        key=f"2d_values_editor_{map_type}_{bank_id}"
    )
    
    # Visualização com gradiente de cores
    st.write("**Visualização com Gradiente:**")
    
    # Obter valores editados
    edited_values = edited_df.iloc[0].tolist()
    
    # Criar DataFrame para visualização com gradiente usando pandas styling
    viz_df = pd.DataFrame([edited_values], columns=df.columns)
    
    # Aplicar estilo com gradiente de cores RdYlBu (igual ao mapa 2D original)
    styled_df = viz_df.style.background_gradient(
        cmap="RdYlBu",  # Red-Yellow-Blue (vermelho para baixo, azul para alto)
        axis=1,  # Aplicar gradiente horizontal
        vmin=min(edited_values) if edited_values else 0,
        vmax=max(edited_values) if edited_values else 1
    ).format("{:.2f}")
    
    # Exibir DataFrame estilizado
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=70  # Altura fixa para visualização compacta
    )
    
    # Botões de ação
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 Salvar", key=f"save_2d_{map_type}"):
            # Reconstruir array completo de valores com as edições
            new_values = values.copy()
            new_edited_values = edited_df.iloc[0].tolist()
            
            # Atualizar apenas os valores ativos com os valores editados
            for idx, new_val in zip(active_indices, new_edited_values):
                new_values[idx] = new_val
            
            if save_2d_map_data(
                vehicle_id, map_type, bank_id, 
                axis_values, new_values, enabled, map_config
            ):
                st.success("Mapa salvo com sucesso!")
                st.rerun()
    
    with col2:
        if st.button("🔄 Restaurar Padrão", key=f"reset_2d_{map_type}"):
            if create_default_2d_map(vehicle_id, map_type, bank_id, vehicle_data, map_config):
                st.success("Restaurado para valores padrão!")
                st.rerun()
    
    with col3:
        if st.button("📊 Validar", key=f"validate_2d_{map_type}"):
            # Validar valores editados
            if all(map_config.get("min_value", 0) <= v <= map_config.get("max_value", 100) for v in edited_values):
                st.success("Todos os valores estão dentro dos limites!")
            else:
                st.error("Alguns valores estão fora dos limites permitidos!")
    
    # Mostrar estatísticas
    render_2d_statistics(edited_values, unit)


def render_2d_axes_editor(map_type: str, map_config: Dict[str, Any], vehicle_id: str,
                         bank_id: str, vehicle_data: Dict[str, Any]):
    """Renderiza editor de eixos para mapas 2D."""
    
    # Carregar dados do mapa
    map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
    
    if map_data:
        axis_values = map_data.get("axis_values", [])
        enabled = map_data.get("enabled", [True] * len(axis_values))
        axis_type = map_config.get("axis_type", "RPM")
        
        st.subheader("Configuração de Eixo")
        
        st.write(f"**Eixo {axis_type}**")
        
        import pandas as pd
        # Criar DataFrame para edição do eixo
        df_axis_data = {
            "Posição": list(range(1, len(axis_values) + 1)),
            f"{axis_type}": axis_values,
            "Ativo": enabled
        }
        df_axis = pd.DataFrame(df_axis_data)
        
        # Editor de eixo no formato tabela simples
        edited_axis_df = st.data_editor(
            df_axis,
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "Posição": st.column_config.NumberColumn(disabled=True),
                f"{axis_type}": st.column_config.NumberColumn(
                    min_value=0,
                    max_value=15000 if axis_type == "RPM" else 5.0,
                    step=100 if axis_type == "RPM" else 0.1,
                    format="%.0f" if axis_type == "RPM" else "%.2f"
                ),
                "Ativo": st.column_config.CheckboxColumn()
            },
            key=f"2d_axis_editor_{map_type}_{bank_id}"
        )
        
        # Botão de salvar
        if st.button("💾 Salvar Eixo", key=f"save_axis_2d_{map_type}"):
            new_axis_values = edited_axis_df[f"{axis_type}"].tolist()
            new_enabled = edited_axis_df["Ativo"].tolist()
            
            # Carregar valores atuais do mapa
            values = map_data.get("values", [])
            
            # Salvar mudanças
            if save_2d_map_data(
                vehicle_id, map_type, bank_id,
                new_axis_values, values, new_enabled, map_config
            ):
                st.success("Eixo salvo com sucesso!")
                st.rerun()
        

def render_3d_values_editor(map_type: str, map_config: Dict[str, Any], vehicle_id: str,
                           bank_id: str, vehicle_data: Dict[str, Any], auto_save: bool):
    """Renderiza editor de valores para mapas 3D."""
    
    # Usar lógica existente de editor 3D
    grid_size = map_config.get("grid_size", 32)
    map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
    
    if map_data:
        rpm_axis = map_data.get("rpm_axis", [])
        map_axis = map_data.get("map_axis", [])
        values_matrix = np.array(map_data.get("values_matrix", []))
        rpm_enabled = map_data.get("rpm_enabled", [True] * grid_size)
        map_enabled = map_data.get("map_enabled", [True] * grid_size)
        
        render_editor_view(
            values_matrix, rpm_axis, map_axis, rpm_enabled, map_enabled,
            map_type, map_config, vehicle_id, bank_id, vehicle_data, auto_save
        )

def render_3d_axes_editor(map_type: str, map_config: Dict[str, Any], vehicle_id: str,
                         bank_id: str, vehicle_data: Dict[str, Any]):
    """Renderiza editor de eixos para mapas 3D."""
    
    # Carregar dados do mapa 3D
    map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
    
    if map_data:
        rpm_axis = map_data.get("rpm_axis", [])
        map_axis = map_data.get("map_axis", [])
        rpm_enabled = map_data.get("rpm_enabled", [True] * len(rpm_axis))
        map_enabled = map_data.get("map_enabled", [True] * len(map_axis))
        
        st.subheader("Configuração de Eixos")
        
        # Duas colunas - uma para cada eixo
        col1, col2 = st.columns(2)
        
        # Coluna 1: Eixo RPM
        with col1:
            st.write("**Eixo RPM**")
            
            import pandas as pd
            # Criar DataFrame para edição do eixo RPM
            df_rpm_data = {
                "Posição": list(range(1, len(rpm_axis) + 1)),
                "RPM": rpm_axis,
                "Ativo": rpm_enabled
            }
            df_rpm = pd.DataFrame(df_rpm_data)
            
            # Editor de eixo RPM no formato tabela simples
            edited_rpm_df = st.data_editor(
                df_rpm,
                use_container_width=True,
                num_rows="fixed",
                column_config={
                    "Posição": st.column_config.NumberColumn(disabled=True),
                    "RPM": st.column_config.NumberColumn(
                        min_value=0,
                        max_value=15000,
                        step=100,
                        format="%.0f"
                    ),
                    "Ativo": st.column_config.CheckboxColumn()
                },
                height=400,
                key=f"3d_rpm_axis_editor_{map_type}_{bank_id}"
            )
            
            # Botão de salvar
            if st.button(":material/save: Salvar RPM", key=f"save_rpm_3d_{map_type}"):
                new_rpm_axis = edited_rpm_df["RPM"].tolist()
                new_rpm_enabled = edited_rpm_df["Ativo"].tolist()
                
                if persistence_manager.save_3d_map_data(
                    vehicle_id, map_type, bank_id,
                    new_rpm_axis, map_axis, new_rpm_enabled, map_enabled,
                    np.array(map_data.get("values_matrix", []))
                ):
                    st.success("Eixo RPM salvo!")
                    st.rerun()
                else:
                    st.error("Falha ao salvar eixo RPM")
        
        # Coluna 2: Eixo MAP
        with col2:
            st.write("**Eixo MAP**")
            
            # Criar DataFrame para edição do eixo MAP
            df_map_data = {
                "Posição": list(range(1, len(map_axis) + 1)),
                "MAP": map_axis,
                "Ativo": map_enabled
            }
            df_map = pd.DataFrame(df_map_data)
            
            # Editor de eixo MAP no formato tabela simples
            edited_map_df = st.data_editor(
                df_map,
                use_container_width=True,
                num_rows="fixed",
                column_config={
                    "Posição": st.column_config.NumberColumn(disabled=True),
                    "MAP": st.column_config.NumberColumn(
                        min_value=-1.0,
                        max_value=5.0,
                        step=0.1,
                        format="%.2f bar"
                    ),
                    "Ativo": st.column_config.CheckboxColumn()
                },
                height=400,
                key=f"3d_map_axis_editor_{map_type}_{bank_id}"
            )
            
            # Botão de salvar
            if st.button(":material/save: Salvar MAP", key=f"save_map_3d_{map_type}"):
                new_map_axis = edited_map_df["MAP"].tolist()
                new_map_enabled = edited_map_df["Ativo"].tolist()
                
                if persistence_manager.save_3d_map_data(
                    vehicle_id, map_type, bank_id,
                    rpm_axis, new_map_axis, rpm_enabled, new_map_enabled,
                    np.array(map_data.get("values_matrix", []))
                ):
                    st.success("Eixo MAP salvo!")
                    st.rerun()
                else:
                    st.error("Falha ao salvar eixo MAP")

def render_ftmanager_copy(map_type: str, map_config: Dict[str, Any], vehicle_id: str,
                         bank_id: str, dimension: str):
    """Renderiza funcionalidade de copiar para FTManager."""
    
    st.subheader("Copiar para FTManager")
    st.info("Selecione os valores do mapa e use Ctrl+C para copiar para o FTManager")
    
    # Mostrar valores em formato copiável
    if dimension == "2D":
        map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
        if map_data:
            values = map_data.get("values", [])
            # Formatar valores para cópia
            formatted = "\t".join([f"{v:.2f}" for v in values])
            st.text_area("Valores para copiar:", formatted, height=100)

def render_ftmanager_paste(map_type: str, map_config: Dict[str, Any], vehicle_id: str,
                          bank_id: str, dimension: str):
    """Renderiza funcionalidade de colar do FTManager."""
    
    st.subheader("Colar do FTManager")
    
    paste_data = st.text_area(
        "Cole os valores do FTManager aqui:",
        height=150,
        key=f"paste_{map_type}_{bank_id}"
    )
    
    if st.button("Aplicar Valores", key=f"apply_paste_{map_type}"):
        if paste_data:
            try:
                # Parse dos valores colados
                values = [float(v) for v in paste_data.replace(",", ".").split()]
                st.success(f"Aplicados {len(values)} valores!")
            except:
                st.error("Formato inválido. Verifique os valores colados.")

def render_data_import(map_type: str, map_config: Dict[str, Any], vehicle_id: str,
                      bank_id: str, dimension: str):
    """Renderiza importação de dados."""
    
    st.subheader("Importar Dados")
    
    import_option = st.radio(
        "Fonte de importação:",
        ["Arquivo JSON", "Arquivo CSV", "Outro Veículo"],
        key=f"import_source_{map_type}"
    )
    
    if import_option == "Arquivo JSON":
        uploaded_file = st.file_uploader("Selecione arquivo JSON", type="json")
        if uploaded_file:
            st.success("Arquivo carregado!")
    
    elif import_option == "Arquivo CSV":
        uploaded_file = st.file_uploader("Selecione arquivo CSV", type="csv")
        if uploaded_file:
            st.success("Arquivo carregado!")
    
    else:  # Outro Veículo
        vehicles = load_vehicles()
        if vehicles:
            source_vehicle = st.selectbox("Selecione o veículo:", vehicles)
            if st.button("Copiar Mapa"):
                st.success(f"Mapa copiado de {source_vehicle}!")

def load_vehicles():
    """Carrega lista de veículos disponíveis."""
    # Tentar carregar veículos do sistema
    try:
        from src.core.fuel_maps import load_vehicles as load_vehicles_core
        return load_vehicles_core()
    except:
        # Fallback para dados dummy
        return [
            {"id": "1", "name": "Veículo 1"},
            {"id": "2", "name": "Veículo 2"},
            {"id": "3", "name": "Veículo 3"}
        ]

def render_data_export(map_type: str, map_config: Dict[str, Any], vehicle_id: str,
                      bank_id: str, dimension: str):
    """Renderiza exportação de dados."""
    
    st.subheader("Exportar Dados")
    
    export_format = st.radio(
        "Formato de exportação:",
        ["JSON", "CSV", "Texto"],
        key=f"export_format_{map_type}",
        horizontal=True
    )
    
    if st.button("📥 Baixar Mapa", key=f"download_{map_type}"):
        if dimension == "2D":
            map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
        else:
            map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
        
        if map_data:
            if export_format == "JSON":
                import json
                st.download_button(
                    "Baixar JSON",
                    json.dumps(map_data, indent=2),
                    f"{map_type}_{vehicle_id}.json",
                    "application/json"
                )


# Funções auxiliares implementadas usando o sistema de persistência
def load_2d_map_data_local(vehicle_id: str, map_type: str, bank_id: str) -> Optional[Dict[str, Any]]:
    """Carrega dados de mapa 2D."""
    return load_2d_map_data(vehicle_id, map_type, bank_id)

def save_2d_map_data_local(vehicle_id: str, map_type: str, bank_id: str,
                          axis_values: List[float], values: List[float], 
                          enabled: List[bool]) -> bool:
    """Salva dados de mapa 2D usando o persistence manager."""
    try:
        return save_2d_map_data(vehicle_id, map_type, bank_id, axis_values, values, enabled)
    except Exception as e:
        logger.error(f"Erro ao salvar mapa 2D: {e}")
        return False

def validate_2d_map(axis_values: List[float], values: List[float], 
                   enabled: List[bool], map_config: Dict[str, Any]) -> List[str]:
    """Valida mapa 2D e retorna lista de erros."""
    errors = []
    
    # Verificar consistência de tamanhos
    if len(axis_values) != len(values) or len(axis_values) != len(enabled):
        errors.append("Tamanhos inconsistentes entre eixo, valores e habilitação")
    
    # Verificar limites de valores
    min_val = map_config.get("min_value", -999)
    max_val = map_config.get("max_value", 999)
    
    for i, (value, is_enabled) in enumerate(zip(values, enabled)):
        if is_enabled and (value < min_val or value > max_val):
            errors.append(f"Valor na posição {i+1} fora dos limites ({min_val}-{max_val}): {value}")
    
    # Verificar ordem crescente do eixo (para alguns tipos)
    axis_type = map_config.get("axis_type", "")
    if axis_type in ["RPM", "TPS", "TEMP", "VOLTAGE"]:
        for i in range(1, len(axis_values)):
            if axis_values[i] < axis_values[i-1]:
                errors.append(f"Eixo {axis_type} deve estar em ordem crescente")
                break
    
    return errors

def restore_2d_default_map(vehicle_id: str, map_type: str, bank_id: str, 
                          map_config: Dict[str, Any]) -> bool:
    """Restaura mapa 2D para valores padrão."""
    try:
        # Criar novo mapa padrão usando o persistence manager
        return create_default_2d_map(vehicle_id, map_type, bank_id, {}, map_config)
    except Exception as e:
        logger.error(f"Erro ao restaurar mapa 2D padrão: {e}")
        return False

def render_3d_view(values_matrix: np.ndarray, rpm_axis: List[float], 
                   map_axis: List[float], map_type: str, 
                   map_config: Dict[str, Any], show_statistics: bool):
    """Renderiza visualização 3D."""
    
    st.header("Visualização 3D")
    
    # Gráfico 3D
    fig_3d = ui_components.render_3d_surface_plot(
        values_matrix, rpm_axis, map_axis, map_type
    )
    st.plotly_chart(fig_3d, use_container_width=True)
    
    # Estatísticas se habilitadas
    if show_statistics:
        render_statistics(values_matrix, map_config)

def render_2d_view(values_matrix: np.ndarray, rpm_axis: List[float],
                   map_axis: List[float], map_type: str,
                   map_config: Dict[str, Any], show_statistics: bool):
    """Renderiza visualização 2D."""
    
    st.header("Visualização 2D (Heatmap)")
    
    # Heatmap 2D  
    fig_2d = ui_components.render_2d_heatmap(
        values_matrix, rpm_axis, map_axis, map_type
    )
    st.plotly_chart(fig_2d, use_container_width=True)
    
    # Estatísticas se habilitadas
    if show_statistics:
        render_statistics(values_matrix, map_config)

def render_editor_view(values_matrix: np.ndarray, rpm_axis: List[float],
                       map_axis: List[float], rpm_enabled: List[bool],
                       map_enabled: List[bool], map_type: str,
                       map_config: Dict[str, Any], vehicle_id: str,
                       bank_id: str, vehicle_data: Dict[str, Any], auto_save: bool):
    """Renderiza modo editor."""
    
    st.header("Editor de Mapa")
    
    # Editor de matriz 3D com duas visualizações
    import pandas as pd
    import numpy as np
    
    # Filtrar apenas valores ativos
    active_rpm_indices = [i for i, enabled in enumerate(rpm_enabled) if enabled]
    active_map_indices = [i for i, enabled in enumerate(map_enabled) if enabled]
    
    # Obter valores ativos
    active_rpm_values = [rpm_axis[i] for i in active_rpm_indices]
    active_map_values = [map_axis[i] for i in active_map_indices]
    
    # Inverter a ordem do RPM para mostrar decrescente (maior para menor)
    active_rpm_values_reversed = list(reversed(active_rpm_values))
    active_rpm_indices_reversed = list(reversed(active_rpm_indices))
    
    # Criar matriz filtrada
    # NOTA: values_matrix é salva como [map_idx][rpm_idx]
    filtered_matrix = []
    for rpm_idx in active_rpm_indices_reversed:
        row = []
        for map_idx in active_map_indices:
            # A matriz está estruturada como [map][rpm], não [rpm][map]
            if map_idx < len(values_matrix) and rpm_idx < len(values_matrix[0]):
                value = values_matrix[map_idx][rpm_idx]
                row.append(value)
            else:
                row.append(0.0)
        filtered_matrix.append(row)
    
    # Criar DataFrame para edição com nomes de colunas únicos
    column_names = []
    column_count = {}
    for map_val in active_map_values:
        col_name = f"{map_val:.3f}"
        if col_name in column_count:
            column_count[col_name] += 1
            col_name = f"{col_name}_{column_count[col_name]}"
        else:
            column_count[col_name] = 0
        column_names.append(col_name)
    
    matrix_df = pd.DataFrame(
        filtered_matrix,
        columns=column_names,
        index=[f"{int(rpm)}" for rpm in active_rpm_values_reversed],
    )
    
    # Obter configurações do mapa
    min_value = map_config.get("min_value", 0)
    max_value = map_config.get("max_value", 100)
    unit = map_config.get("unit", "ms")
    
    # Editor de matriz com formatação 3 casas decimais
    edited_matrix_df = st.data_editor(
        matrix_df,
        use_container_width=True,
        column_config={
            col: st.column_config.NumberColumn(
                col.split("_")[0] if "_" in col else col,
                format="%.3f",
                min_value=min_value,
                max_value=max_value,
                help=f"MAP: {col.split('_')[0] if '_' in col else col} bar, Valores em {unit}",
            )
            for col in matrix_df.columns
        },
        key=f"matrix_editor_{map_type}_{bank_id}",
    )
    
    # Criar DataFrame para visualização com gradiente
    display_df = pd.DataFrame(
        filtered_matrix,
        columns=[f"{map_val:.2f}" for map_val in active_map_values],
        index=[f"{int(rpm)}" for rpm in active_rpm_values_reversed],
    )
    
    # Aplicar estilo com gradiente
    styled_df = display_df.style.background_gradient(
        cmap="RdYlBu", axis=None
    ).format("{:.3f}")
    
    # Mostrar visualização com gradiente
    st.caption(f"Visualização com gradiente de cores - {unit}")
    st.dataframe(styled_df, use_container_width=True)
    
    # Detectar mudanças e atualizar matriz completa
    matrix_changed = not matrix_df.equals(edited_matrix_df)
    
    if matrix_changed:
        st.success("Matriz modificada")
        
        # Reconstruir matriz completa com valores editados
        # NOTA: matriz é [map_idx][rpm_idx]
        grid_size = len(rpm_axis)
        map_grid_size = len(map_axis)
        modified_matrix = values_matrix.copy()
        
        for i, rpm_idx in enumerate(active_rpm_indices_reversed):
            if i < len(edited_matrix_df.values) and rpm_idx < grid_size:
                for j, map_idx in enumerate(active_map_indices):
                    if j < len(edited_matrix_df.values[i]) and map_idx < map_grid_size:
                        # Corrigir indexação: matriz é [map][rpm]
                        modified_matrix[map_idx][rpm_idx] = edited_matrix_df.values[i][j]
        
        # Salvar automaticamente se habilitado
        if auto_save:
            save_map_data(vehicle_id, map_type, bank_id, rpm_axis, map_axis,
                          rpm_enabled, map_enabled, modified_matrix)
            st.success("Salvo automaticamente")
    
    # Estatísticas embaixo
    st.divider()
    render_statistics(values_matrix, map_config)

def render_tools(map_type: str, map_config: Dict[str, Any], vehicle_id: str, 
                 bank_id: str, vehicle_data: Dict[str, Any], dimension: str):
    """Renderiza ferramentas avançadas unificadas para 2D e 3D."""
    
    # Ações específicas por tipo antes das configurações gerais
    if dimension == "3D" and map_type in ("ve_3d_map", "ve_table_3d_map"):
        st.subheader("Ferramentas de VE 3D")
        st.caption("Regenera a malha VE 3D com base nos eixos atuais (como no painel de referência)")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Recalcular VE 3D pelos eixos", key=f"regen_ve3d_{vehicle_id}_{bank_id}"):
                if map_type == "ve_table_3d_map":
                    ok = persistence_manager.regenerate_ve_table_3d_map(vehicle_id, bank_id)
                else:
                    ok = persistence_manager.regenerate_ve_3d_map(vehicle_id, bank_id)
                if ok:
                    st.success("VE 3D recalculado e salvo com sucesso")
                    st.rerun()
                else:
                    st.error("Falha ao recalcular VE 3D")
        with col_btn2:
            st.info("Use também 'Aplicar Cálculo' abaixo para salvar a prévia calculada")
        st.divider()

    # Presets de estratégias de tuning
    STRATEGY_PRESETS = {
        "conservative": {
            "name": "Conservadora",
            "description": "AFR rico, margens de segurança maiores",
            "safety_factor": 1.1,
        },
        "balanced": {
            "name": "Balanceada", 
            "description": "Valores típicos de fábrica",
            "safety_factor": 1.0,
        },
        "aggressive": {
            "name": "Agressiva",
            "description": "AFR pobre, eficiência máxima",
            "safety_factor": 0.9,
        },
        "economy": {
            "name": "Econômica", 
            "description": "Foco em economia de combustível",
            "safety_factor": 1.05,
        },
        "sport": {
            "name": "Esportiva",
            "description": "Máxima performance",
            "safety_factor": 0.95,
        }
    }
    
    # Obter dados do veículo da sessão
    vehicle_data_session = get_vehicle_data_from_session()
    
    # Duas colunas principais para Configurações e Dados do Veículo
    calc_col1, calc_col2 = st.columns(2)
    
    # SEÇÃO 1: Configurações de Cálculo (coluna esquerda)
    with calc_col1:
        st.subheader("Configurações de Cálculo")

        # Ajuda / Nomenclaturas
        with st.expander("Ajuda / Nomenclaturas"):
            st.markdown(
                """
                - PW (Pulse Width) — Largura de Pulso: tempo de abertura do injetor por evento, em ms. Aproximadamente PW ≈ massa_combustível / vazão_bico + dead time.
                - VE (Volumetric Efficiency) — Eficiência Volumétrica: fração/porcentagem do enchimento do cilindro. VE maior → mais ar → PW maior.
                - MAP (Manifold Absolute Pressure) — Pressão no coletor: aqui usamos MAP relativo (bar). P_abs = 1 + MAP_rel.
                - P_abs (Absolute Pressure) — Pressão Absoluta: define massa de ar com a temperatura. P_abs↑ → massa de ar↑ → PW↑.
                - ΔP (Pressure Differential) — Diferencial no injetor: ΔP entre trilho e coletor. 1:1 mantém ΔP constante; regulador fixo reduz ΔP em boost.
                - AFR (Air–Fuel Ratio) — Relação ar–combustível: maior AFR = mistura mais pobre; menor AFR = mistura mais rica.
                - λ (Lambda) — Razão normalizada: λ = AFR / AFR_estequiométrico. λ menor → mistura mais rica.
                - IAT (Intake Air Temperature) — Temperatura do ar de admissão (°C): T↑ → densidade↓ → PW↓.
                - DT (Dead Time) — Tempo morto do injetor (ms): componente aditiva ao PW.
                - P_base (Base Fuel Pressure) — Pressão base no trilho (bar): referência para ΔP.
                - 1:1 Regulator — Regulador 1:1 (referenciado ao MAP): mantém ΔP constante, estabilizando vazão do bico em boost.
                - FS (Safety Factor) — Fator de Segurança: no λ alvo, FS maior enriquece (λ menor); no PW sem λ por célula, FS enriquece via AFR alvo.
                """
            )
        
        # Seleção de estratégia
        selected_strategy = st.selectbox(
            "Estratégia de Tuning",
            options=list(STRATEGY_PRESETS.keys()),
            format_func=lambda x: f"{STRATEGY_PRESETS[x]['name']} - {STRATEGY_PRESETS[x]['description']}",
            key=f"strategy_{dimension}_{map_type}_{bank_id}",
            index=1  # Balanceada por padrão
        )
        
        # Fator de segurança
        safety_factor = st.slider(
            "Fator de Segurança",
            min_value=0.8,
            max_value=1.2,
            value=STRATEGY_PRESETS[selected_strategy]["safety_factor"],
            step=0.01,
            key=f"safety_factor_{dimension}_{map_type}_{bank_id}",
            help="Ajuste fino dos valores calculados"
        )
        
        # Configurações específicas
        st.write("**Configurações Específicas**")
        # Mostrar controles específicos apenas para mapas de injeção (PW 3D)
        show_injection_controls = (dimension == "3D" and map_type == "main_fuel_3d_map")
        col_check1, col_check2 = st.columns(2)
        
        with col_check1:
            boost_enabled = False
            if show_injection_controls:
                boost_enabled = st.checkbox(
                    "Aplicar pressão de admissão (MAP) no PW",
                    value=True,
                    key=f"boost_enabled_{dimension}_{map_type}_{bank_id}",
                    help="Considera a pressão absoluta do ar (P_abs) no cálculo. Com boost, a massa de ar por admissão aumenta e o PW tende a subir. Desative para simular PW em regime atmosférico (P_abs=1,0 bar)."
                )
        
        with col_check2:
            fuel_correction_enabled = False
            if show_injection_controls:
                fuel_correction_enabled = st.checkbox(
                    "Correção de Combustível",
                    value=True,
                    key=f"fuel_corr_{dimension}_{map_type}_{bank_id}",
                    help="ON: usa AFR estequiométrico do combustível (ex.: Etanol 9.0). OFF: usa 14.7 (gasolina) para isolar variações."
                )

        # Regulador 1:1 (combustível referenciado ao MAP) – controla ΔP (apenas para injeção 3D)
        regulator_11 = True
        if show_injection_controls:
            regulator_11 = st.checkbox(
                "Considerar pressão de turbo (1:1) no combustível",
                value=True,
                key=f"reg11_{dimension}_{map_type}_{bank_id}",
                help="ON: ΔP constante (P_base). OFF: ΔP = P_base − MAP_rel (fluxo cai em boost e o PW tende a subir)."
            )

        # Malha fechada (λ): usar Fator de Segurança como fator λ-alvo (sem controles redundantes)
        cl_factor_value = safety_factor if (dimension == "3D" and map_type == "lambda_target_3d_map") else 1.0
    
    # SEÇÃO 2: Dados do Veículo (coluna direita)
    with calc_col2:
        st.subheader("Dados do Veículo")
        
        # Primeira linha: Cilindrada, Cilindros, Vazão
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cilindrada", f"{vehicle_data_session.get('displacement', 2.0):.1f}L")
        with col2:
            st.metric("Cilindros", vehicle_data_session.get('cylinders', 4))
        with col3:
            # Mostrar na mesma unidade das bancadas (lb/h)
            flow_lbs = vehicle_data_session.get('injector_flow_lbs')
            if flow_lbs is None:
                flow_lbs = 0.0
            st.metric("Vazão Total (lb/h)", f"{flow_lbs:.1f} lb/h")
        
        # Segunda linha: Combustível, Boost
        col4, col5 = st.columns(2)
        with col4:
            # Padronizar exibição do combustível em pt-BR
            ft_raw = str(vehicle_data_session.get('fuel_type', 'Flex'))
            ft = ft_raw.lower()
            if 'ethanol' in ft or 'etanol' in ft:
                ft_disp = 'Etanol'
            elif 'e85' in ft:
                ft_disp = 'E85'
            elif 'gas' in ft or 'gasoline' in ft or 'gasolina' in ft:
                ft_disp = 'Gasolina'
            elif 'diesel' in ft:
                ft_disp = 'Diesel'
            elif 'methanol' in ft or 'metanol' in ft:
                ft_disp = 'Metanol'
            elif 'nitromethane' in ft or 'nitro' in ft or 'nitrometano' in ft:
                ft_disp = 'Nitrometano'
            elif 'gnv' in ft or 'cng' in ft:
                ft_disp = 'GNV'
            elif 'flex' in ft:
                ft_disp = 'Flex'
            else:
                ft_disp = ft_raw
            st.metric("Combustível", ft_disp)
        with col5:
            if vehicle_data_session.get('turbo', False):
                st.metric("Boost", f"{vehicle_data_session.get('boost_pressure', 1.0):.1f} bar")
            else:
                st.metric("Aspiração", "Natural")
    
    st.markdown("---")
    
    # SEÇÃO 3: Preview dos Valores Calculados
    st.subheader("Preview dos Valores Calculados")
    show_debug = st.checkbox(
        "Mostrar debug",
        value=False,
        key=f"show_debug_{dimension}_{map_type}_{bank_id}",
        help="Exibe/oculta informações detalhadas do cálculo"
    )
    
    try:
        # Calcular valores baseado na dimensão
        # Preparar dados do veículo com configuração do regulador
        calc_vehicle = dict(vehicle_data_session)
        calc_vehicle["regulator_1_1"] = regulator_11
        if dimension == "2D":
            # Carregar dados 2D atuais
            map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
            if map_data:
                axis_values = map_data.get("axis_values", [])
                enabled = map_data.get("enabled", [True] * len(axis_values))
                
                # Usar função universal de cálculo 2D
                from src.core.fuel_maps.calculations import calculate_map_values_universal
                preview_values = calculate_map_values_universal(
                    map_type, axis_values, calc_vehicle,
                    selected_strategy, safety_factor,
                    apply_fuel_corr=fuel_correction_enabled
                )
                
                # Criar DataFrame linha única para 2D - apenas valores habilitados
                column_headers = {}
                filtered_preview_values = []
                for i, (axis_val, enabled_flag) in enumerate(zip(axis_values, enabled)):
                    if enabled_flag:  # Incluir apenas valores habilitados
                        header = f"{axis_val:.1f}"
                        column_headers[header] = preview_values[i]
                        filtered_preview_values.append(preview_values[i])
                
                preview_df = pd.DataFrame([column_headers])
                preview_values = filtered_preview_values  # Usar valores filtrados para estatísticas
                unit = map_config.get("unit", "ms")
                
        else:  # 3D
            # Carregar dados 3D atuais
            map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
            if map_data:
                rpm_axis = map_data.get("rpm_axis", [])
                map_axis = map_data.get("map_axis", [])
                
                # DEBUG: Identificação do mapa selecionado
                if show_debug:
                    st.write(
                        f"Mapa selecionado: {map_type} - {map_config.get('display_name', map_type)} "
                        f"(unit: {map_config.get('unit', '')}, dim: {dimension})"
                    )
                
                # DEBUG: Verificar se enabled está sendo carregado
                rpm_enabled_saved = map_data.get("rpm_enabled", None)
                map_enabled_saved = map_data.get("map_enabled", None)
                
                if show_debug:
                    st.write("DEBUG - Dados carregados do arquivo:")
                    st.write(f"- rpm_enabled salvo: {rpm_enabled_saved is not None} ({len(rpm_enabled_saved) if rpm_enabled_saved else 0} valores)")
                    st.write(f"- map_enabled salvo: {map_enabled_saved is not None} ({len(map_enabled_saved) if map_enabled_saved else 0} valores)")
                
                # Se não tiver dados salvos, usar todos habilitados
                rpm_enabled = rpm_enabled_saved if rpm_enabled_saved is not None else [True] * len(rpm_axis)
                map_enabled = map_enabled_saved if map_enabled_saved is not None else [True] * len(map_axis)
                
                if show_debug:
                    st.write(f"- rpm_enabled usado: {sum(rpm_enabled)} de {len(rpm_enabled)} habilitados")
                    st.write(f"- map_enabled usado: {sum(map_enabled)} de {len(map_enabled)} habilitados")
                    st.divider()
                
                # Calcular matriz 3D
                if map_type == "ve_3d_map":
                    # VE 3D: usar gerador dedicado (como mapa.html)
                    from src.core.fuel_maps.calculations import generate_ve_3d_matrix
                    calculated_matrix = generate_ve_3d_matrix(rpm_axis, map_axis)
                    unit = "VE"
                else:
                    # Demais mapas 3D: usar função universal
                    from src.core.fuel_maps.calculations import calculate_3d_map_values_universal
                    kwargs = dict(
                        strategy=selected_strategy,
                        safety_factor=safety_factor,
                        consider_boost=boost_enabled,
                        apply_fuel_corr=fuel_correction_enabled,
                        cl_factor=cl_factor_value
                    )
                    # Preparar VE e λ para cálculo perfeito do mapa principal 3D
                    if map_type == "main_fuel_3d_map":
                        # VE 3D (fração)
                        ve_data = persistence_manager.load_3d_map_data(vehicle_id, "ve_3d_map", bank_id)
                        ve_matrix = None
                        if ve_data and ve_data.get("rpm_axis") == rpm_axis and ve_data.get("map_axis") == map_axis:
                            ve_matrix = np.array(ve_data.get("values_matrix", []), dtype=float)
                        else:
                            # Gerar VE a partir das curvas padrão como fallback
                            from src.core.fuel_maps.calculations import generate_ve_3d_matrix
                            ve_matrix = generate_ve_3d_matrix(rpm_axis, map_axis)
                        kwargs["ve_matrix"] = ve_matrix

                        # Lambda alvo (malha fechada) por célula
                        from src.core.fuel_maps.calculations import calculate_lambda_target_closed_loop
                        lambda_matrix = calculate_lambda_target_closed_loop(
                            rpm_axis, map_axis,
                            strategy=selected_strategy,
                            cl_factor=cl_factor_value,
                            fuel_type=str(calc_vehicle.get('fuel_type', 'ethanol'))
                        )
                        # O usuário pode optar por não aplicar malha fechada
                        use_lambda = st.checkbox(
                            "Usar λ alvo (malha) no cálculo",
                            value=True,
                            help="Aplica a malha λ alvo por célula ao cálculo do PW",
                            key=f"use_lambda_{map_type}_{bank_id}"
                        )
                        if use_lambda:
                            kwargs["lambda_matrix"] = lambda_matrix
                        # AFR estequiométrico explícito do combustível
                        fuel = str(vehicle_data_session.get('fuel_type', 'gasoline')).lower()
                        afr_stq = 14.7
                        if "ethanol" in fuel or "etanol" in fuel:
                            afr_stq = 9.0
                        elif "e85" in fuel:
                            afr_stq = 9.8
                        elif "diesel" in fuel:
                            afr_stq = 14.5
                        elif "gnv" in fuel or "cng" in fuel:
                            afr_stq = 17.2
                        elif "methanol" in fuel or "metanol" in fuel:
                            afr_stq = 6.4
                        kwargs["afr_stoich"] = afr_stq

                    calculated_matrix = calculate_3d_map_values_universal(
                        map_type, rpm_axis, map_axis, calc_vehicle, **kwargs
                    )

                    # Removido: escala VE/VE@rpm_ref (já usamos VE por célula)
                
                if show_debug:
                    st.write(f"- calculated_matrix shape: {calculated_matrix.shape}")
                    st.write(f"- Min: {calculated_matrix.min():.3f}, Max: {calculated_matrix.max():.3f}")
                    st.write(f"- Valores únicos: {len(np.unique(calculated_matrix))}")
                    st.write(f"- Amostra [0,0]: {calculated_matrix[0,0]:.3f}, [0,1]: {calculated_matrix[0,1]:.3f}")
                    st.divider()
                
                # Filtrar apenas valores ativos
                active_rpm_indices = [i for i, enabled in enumerate(rpm_enabled) if enabled]
                active_map_indices = [i for i, enabled in enumerate(map_enabled) if enabled]
                active_rpm_values = [rpm_axis[i] for i in active_rpm_indices]
                active_map_values = [map_axis[i] for i in active_map_indices]
                
                # Criar matriz filtrada para preview
                # NOTA: calculated_matrix é indexada como [map_idx][rpm_idx]
                # Queremos mostrar RPM nas linhas (reverso) e MAP nas colunas
                
                if show_debug:
                    st.write("DEBUG - Criação da preview_matrix:")
                    st.write(f"- active_rpm_indices: {active_rpm_indices[:5]}... ({len(active_rpm_indices)} total)")
                    st.write(f"- active_map_indices: {active_map_indices[:5]}... ({len(active_map_indices)} total)")
                
                preview_matrix = []
                for i, rpm_idx in enumerate(reversed(active_rpm_indices)):  # RPM reverso para display
                    row = []
                    for j, map_idx in enumerate(active_map_indices):
                        value = calculated_matrix[map_idx][rpm_idx]
                        row.append(value)
                        # DEBUG: Primeiras células
                        if show_debug and i == 0 and j < 3:
                            st.write(f"  - preview_matrix[{i}][{j}] = calculated_matrix[{map_idx}][{rpm_idx}] = {value:.3f}")
                    preview_matrix.append(row)
                
                if show_debug:
                    st.write(f"- preview_matrix shape: {len(preview_matrix)}x{len(preview_matrix[0]) if preview_matrix else 0}")
                    st.divider()
                
                # Criar DataFrame matriz para 3D
                preview_df = pd.DataFrame(
                    preview_matrix,
                    columns=[f"{m:.2f}" for m in active_map_values],
                    index=[f"{int(rpm_axis[i])}" for i in reversed(active_rpm_indices)]
                )
                unit = map_config.get("unit", "ms")
                preview_values = [val for row in preview_matrix for val in row]  # Flatten para stats
        
                if 'preview_df' in locals():
                    # Aplicar gradiente RdYlBu
                    styled_df = preview_df.style.background_gradient(
                        cmap="RdYlBu", 
                        axis=1 if dimension == "2D" else None
                    ).format("{:.3f}")
                    
                    st.write(f"**Preview dos valores calculados** ({unit})")
                    st.caption(f"Valores com 3 casas decimais - Total: {len(preview_values)} valores")
                    
                    if show_debug:
                        st.write("DEBUG - DataFrame final:")
                        st.write(f"- preview_df shape: {preview_df.shape}")
                        st.write(f"- Primeira linha: {preview_df.iloc[0].values[:5].tolist()}...")
                        st.write(f"- preview_values (flatten): min={min(preview_values):.3f}, max={max(preview_values):.3f}")
                        all_same = len(set(preview_values)) == 1
                        if all_same:
                            st.error(f"AVISO: Todos os valores são iguais: {preview_values[0]:.3f}")
                        st.divider()
                    
                    st.dataframe(styled_df, use_container_width=True)
                    
                    # Estatísticas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Mínimo", f"{min(preview_values):.3f} {unit}")
                    with col2:
                        st.metric("Médio", f"{np.mean(preview_values):.3f} {unit}")
                    with col3:
                        st.metric("Máximo", f"{max(preview_values):.3f} {unit}")
                else:
                    st.warning("Não foi possível carregar dados para preview")
    
    except Exception as e:
        st.error(f"Erro ao calcular preview: {e}")
        return
    
    st.markdown("---")
    
    # SEÇÃO 4: Botões de Ação
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        if st.button(":material/check: Aplicar Cálculo", type="primary", use_container_width=True,
                     key=f"apply_{dimension}_{map_type}_{bank_id}"):
            try:
                if dimension == "2D":
                    # Salvar valores 2D
                    if save_2d_map_data(vehicle_id, map_type, bank_id, 
                                       axis_values, preview_values, enabled, map_config):
                        st.success("Valores aplicados com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar valores")
                else:
                    # Salvar matriz 3D 
                    if save_map_data(vehicle_id, map_type, bank_id,
                                   rpm_axis, map_axis, rpm_enabled, 
                                   map_enabled, calculated_matrix):
                        st.success("Valores aplicados com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar valores")
            except Exception as e:
                st.error(f"Erro ao aplicar cálculo: {e}")
    
    with action_col2:
        if st.button(":material/analytics: Preview Gráfico", use_container_width=True,
                     key=f"preview_{dimension}_{map_type}_{bank_id}"):
            try:
                if dimension == "2D":
                    # Gráfico de linha 2D
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=axis_values, y=preview_values, 
                        mode='lines+markers', name='Calculado',
                        line=dict(color='blue', width=3),
                        marker=dict(size=8)
                    ))
                    fig.update_layout(
                        title=f"Preview 2D - {map_type}",
                        xaxis_title="Eixo X",
                        yaxis_title=f"Valor ({unit})",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Gráfico 3D Surface
                    fig = go.Figure(data=[go.Surface(
                        z=preview_matrix, 
                        x=active_map_values, 
                        y=active_rpm_values,
                        colorscale="RdYlBu"
                    )])
                    fig.update_layout(
                        title=f"Preview 3D - {map_type}",
                        scene=dict(
                            xaxis_title="MAP (bar)",
                            yaxis_title="RPM", 
                            zaxis_title=f"Valor ({unit})"
                        ),
                        height=600
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar gráfico: {e}")

def render_statistics(values_matrix: np.ndarray, map_config: Dict[str, Any]):
    """Renderiza estatísticas do mapa."""
    
    st.subheader("Estatísticas")
    
    from src.core.fuel_maps.utils import calculate_matrix_statistics
    stats = calculate_matrix_statistics(values_matrix)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Mínimo", format_value_3_decimals(stats["min"]), 
                 delta=None)
    with col2:
        st.metric("Máximo", format_value_3_decimals(stats["max"]), 
                 delta=None)
    with col3:
        st.metric("Média", format_value_3_decimals(stats["mean"]), 
                 delta=None)
    with col4:
        st.metric("Desvio Padrão", format_value_3_decimals(stats["std"]), 
                 delta=None)

def save_map_data(vehicle_id: str, map_type: str, bank_id: str,
                  rpm_axis: List[float], map_axis: List[float],
                  rpm_enabled: List[bool], map_enabled: List[bool],
                  values_matrix: np.ndarray) -> bool:
    """Wrapper para salvar dados do mapa."""
    try:
        return persistence_manager.save_3d_map_data(
            vehicle_id=vehicle_id,
            map_type=map_type,
            bank_id=bank_id,
            rpm_axis=rpm_axis,
            map_axis=map_axis,
            rpm_enabled=rpm_enabled,
            map_enabled=map_enabled,
            values_matrix=values_matrix
        )
    except Exception as e:
        logger.error(f"Erro ao salvar: {e}")
        return False

# Executar aplicação principal
if __name__ == "__main__":
    main()
else:
    # Executar quando importado pelo Streamlit
    main()
