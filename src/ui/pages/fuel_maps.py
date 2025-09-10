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
from src.core.fuel_maps import (  # Gerenciadores principais; Instâncias globais; Funções de compatibilidade (mantidas para transição suave)
    ConfigManager,
    PersistenceManager,
    SessionManager,
    UIComponents,
    calculate_2d_map_values,
    calculate_3d_map_values_universal,
    config_manager,
    create_default_2d_map,
    ensure_all_3d_maps_exist,
    ensure_all_maps_exist,
    format_value_3_decimals,
    get_all_maps,
    get_map_dimension,
    get_sorted_maps_for_display,
    get_vehicle_data_from_session,
    has_bank_selection,
    interpolate_3d_matrix,
    load_2d_map_data,
    load_3d_map_data,
    load_map_types_config,
    persistence_manager,
    save_2d_map_data,
    save_3d_map_data,
    session_manager,
    ui_components,
    validate_3d_map_values,
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


def render_unified_interface(
    all_maps: Dict[str, Any], vehicle_data: Dict[str, Any], vehicle_id: str
):
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
            map_labels = [info["display_name"] for _, info in sorted_maps]

            selected_index = st.selectbox(
                "Tipo de Mapa",
                range(len(map_options)),
                format_func=lambda i: map_labels[i],
                key="selected_unified_map_type",
                label_visibility="visible",
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
                "Bancada", ["A", "B"], key="selected_unified_bank", horizontal=True
            )
        else:
            bank_id = "shared"
            st.info("Mapa único para todo o motor")

    # Mostrar indicador de dimensão
    dimension = map_info["dimension"]

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
            "Modo de Visualização", view_options, key="unified_view_mode"
        )

        # Configurações avançadas
        with st.expander("Configurações Avançadas"):
            show_statistics = st.checkbox("Mostrar Estatísticas", value=True)
            auto_save = st.checkbox("Salvamento Automático", value=True)

            if dimension == "3D":
                interpolation_method = st.selectbox(
                    "Método de Interpolação",
                    ["linear", "cubic", "nearest"],
                    key="unified_interpolation_method",
                )

    # Área principal - renderização com abas
    map_config = all_maps[map_type]

    # Criar abas principais
    tab1, tab2, tab3 = st.tabs(["Editar", "Visualizar", "Importar/Exportar"])

    with tab1:
        render_edit_tab(
            map_type,
            map_config,
            vehicle_id,
            bank_id,
            vehicle_data,
            dimension,
            auto_save,
        )

    with tab2:
        render_visualize_tab(
            map_type,
            map_config,
            vehicle_id,
            bank_id,
            vehicle_data,
            dimension,
            show_statistics,
        )

    with tab3:
        render_import_export_tab(
            map_type, map_config, vehicle_id, bank_id, vehicle_data, dimension
        )


def render_edit_tab(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data: Dict[str, Any],
    dimension: str,
    auto_save: bool,
):
    """Renderiza a aba de edição com sub-abas Valores e Eixos."""

    st.write("Editor de dados do mapa")

    # Sub-abas dentro de Editar - agora 3 abas tanto para 2D quanto 3D
    subtab1, subtab2, subtab3 = st.tabs(["Valores", "Eixos", "Ferramentas"])

    with subtab1:
        if dimension == "3D":
            render_3d_values_editor(
                map_type, map_config, vehicle_id, bank_id, vehicle_data, auto_save
            )
        else:
            render_2d_values_editor(
                map_type, map_config, vehicle_id, bank_id, vehicle_data, auto_save
            )

    with subtab2:
        if dimension == "3D":
            render_3d_axes_editor(
                map_type, map_config, vehicle_id, bank_id, vehicle_data
            )
        else:
            render_2d_axes_editor(
                map_type, map_config, vehicle_id, bank_id, vehicle_data
            )

    with subtab3:
        # Ferramentas para ambos 2D e 3D
        render_tools(map_type, map_config, vehicle_id, bank_id, vehicle_data, dimension)


def render_visualize_tab(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data: Dict[str, Any],
    dimension: str,
    show_statistics: bool,
):
    """Renderiza a aba de visualização com gráficos."""

    if dimension == "3D":
        # Carregar dados e renderizar no layout comum (gráfico 3D)
        map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
        if map_data:
            rpm_axis = map_data.get("rpm_axis", [])
            map_axis = map_data.get("map_axis", [])
            values_matrix = np.array(map_data.get("values_matrix", []))

            rpm_enabled = map_data.get("rpm_enabled", [True] * len(rpm_axis))
            map_enabled = map_data.get("map_enabled", [True] * len(map_axis))

            render_3d_chart_view_for_visualize(
                rpm_axis,
                map_axis,
                values_matrix,
                rpm_enabled,
                map_enabled,
                map_type,
                map_config,
                show_statistics,
            )
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

            render_2d_chart_view(
                axis_values,
                values,
                enabled,
                map_type,
                map_config,
                axis_type,
                unit,
                show_statistics,
            )
        else:
            st.warning("Nenhum dado de mapa 2D encontrado")


def render_import_export_tab(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data: Dict[str, Any],
    dimension: str,
):
    """Renderiza a aba de importação/exportação."""

    # Sub-abas de importar/exportar
    subtab1, subtab2, subtab3, subtab4 = st.tabs(
        ["Copiar FTManager", "Colar FTManager", "Importar Dados", "Exportar Dados"]
    )

    with subtab1:
        render_ftmanager_copy(map_type, map_config, vehicle_id, bank_id, dimension)

    with subtab2:
        render_ftmanager_paste(map_type, map_config, vehicle_id, bank_id, dimension)

    with subtab3:
        render_data_import(map_type, map_config, vehicle_id, bank_id, dimension)

    with subtab4:
        render_data_export(map_type, map_config, vehicle_id, bank_id, dimension)


def render_by_dimension_3d(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data: Dict[str, Any],
    view_mode: str,
    show_statistics: bool,
    auto_save: bool,
):
    """Renderiza mapas 3D usando a lógica existente."""

    grid_size = map_config.get("grid_size", 32)

    # Carregar dados do mapa 3D
    map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)

    if map_data is None:
        st.warning("Mapa 3D não encontrado. Gerando padrão...")
        if persistence_manager.create_default_map(
            vehicle_id, map_type, bank_id, vehicle_data, grid_size
        ):
            map_data = persistence_manager.load_3d_map_data(
                vehicle_id, map_type, bank_id
            )
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
        render_3d_view(
            values_matrix, rpm_axis, map_axis, map_type, map_config, show_statistics
        )
    elif view_mode == "2D Heatmap":
        render_2d_view(
            values_matrix, rpm_axis, map_axis, map_type, map_config, show_statistics
        )
    else:  # Editor
        render_editor_view(
            values_matrix,
            rpm_axis,
            map_axis,
            rpm_enabled,
            map_enabled,
            map_type,
            map_config,
            vehicle_id,
            bank_id,
            vehicle_data,
            auto_save,
        )


def render_by_dimension_2d(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data: Dict[str, Any],
    view_mode: str,
    show_statistics: bool,
    auto_save: bool,
):
    """Renderiza mapas 2D com interface simplificada."""

    positions = map_config.get("positions", 32)
    axis_type = map_config.get("axis_type", "RPM")
    unit = map_config.get("unit", "ms")

    # Carregar dados do mapa 2D
    map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)

    if map_data is None:
        st.warning("Mapa 2D não encontrado. Gerando padrão...")
        # Criar mapa padrão usando o persistence manager
        if create_default_2d_map(
            vehicle_id, map_type, bank_id, vehicle_data, map_config
        ):
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
        render_2d_chart_view(
            axis_values,
            values,
            enabled,
            map_type,
            map_config,
            axis_type,
            unit,
            show_statistics,
        )
    else:  # Editor Linear
        render_2d_editor_view(
            axis_values,
            values,
            enabled,
            map_type,
            map_config,
            vehicle_id,
            bank_id,
            axis_type,
            unit,
            auto_save,
            vehicle_data,
        )


def render_2d_chart_view(
    axis_values: List[float],
    values: List[float],
    enabled: List[bool],
    map_type: str,
    map_config: Dict[str, Any],
    axis_type: str,
    unit: str,
    show_statistics: bool,
):
    """Renderiza visualização em gráfico 2D."""

    st.header(f"Visualização 2D - {map_config.get('display_name', map_type)}")

    # Preparar dados para o gráfico (apenas valores habilitados)
    enabled_indices = [
        i
        for i, e in enumerate(enabled)
        if e and i < len(axis_values) and i < len(values)
    ]
    chart_axis = [axis_values[i] for i in enabled_indices]
    chart_values = [values[i] for i in enabled_indices]

    if not chart_axis or not chart_values:
        st.warning("Nenhum ponto habilitado para exibir")
        return

    # Criar gráfico com plotly
    import plotly.graph_objects as go

    fig = go.Figure()

    # Adicionar linha principal
    # Marcadores com gradiente RdYlBu (menor=vermelho, maior=azul), linha permanece vermelha
    cmin = min(chart_values)
    cmax = max(chart_values)
    if cmin == cmax:
        cmin -= 1e-9
        cmax += 1e-9
    # Cor de contorno do marcador conforme tema (preto no claro, branco no escuro)
    try:
        theme_base = st.get_option("theme.base")
    except Exception:
        theme_base = None
    outline_color = "#FFFFFF" if str(theme_base).lower() == "dark" else "#000000"
    fig.add_trace(
        go.Scatter(
            x=chart_axis,
            y=chart_values,
            mode="lines+markers",
            name=f"Valores {unit}",
            line=dict(color="red", width=2),
            marker=dict(
                size=9,
                color=chart_values,
                colorscale="RdYlBu",
                showscale=False,
                cmin=cmin,
                cmax=cmax,
                line=dict(width=1.5, color=outline_color),
            ),
        )
    )

    # Linha de corte em MAP=0 (faixa de turbo) quando aplicável
    try:
        if axis_type.upper() == "MAP" and any(x > 0 for x in chart_axis):
            cut_color = "#FFFFFF66" if str(theme_base).lower() == "dark" else "#00000066"
            shapes = list(fig.layout.shapes) if fig.layout.shapes else []
            shapes.append(
                dict(
                    type="line",
                    xref="x",
                    yref="paper",
                    x0=0,
                    x1=0,
                    y0=0,
                    y1=1,
                    line=dict(color=cut_color, width=2, dash="dash"),
                )
            )
            fig.update_layout(shapes=shapes)
    except Exception:
        pass

    # Configurar layout
    fig.update_layout(
        title=f"{map_config.get('display_name', map_type)} - Gráfico 2D",
        xaxis_title=f"{axis_type}",
        yaxis_title=f"Valores ({unit})",
        showlegend=True,
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Mostrar estatísticas se habilitado
    if show_statistics:
        render_2d_statistics(chart_values, unit)


def render_3d_chart_view_for_visualize(
    rpm_axis: List[float],
    map_axis: List[float],
    values_matrix: np.ndarray,
    rpm_enabled: List[bool],
    map_enabled: List[bool],
    map_type: str,
    map_config: Dict[str, Any],
    show_statistics: bool,
):
    """Renderiza visualização em gráfico 3D (Surface) no layout comum da aba Visualizar.
    Orientação: X = MAP (desc), Y = RPM (ordem original). Z no shape [len(Y)][len(X)].
    """
    import numpy as _np
    import plotly.graph_objects as go

    st.header(f"Visualização 3D - {map_config.get('display_name', map_type)}")

    # Filtrar por enabled
    active_rpm_indices = [i for i, e in enumerate(rpm_enabled) if e]
    active_map_indices = [i for i, e in enumerate(map_enabled) if e]
    if not active_rpm_indices or not active_map_indices:
        st.warning("Nenhum ponto habilitado para visualização")
        return

    rpm_axis_active = [rpm_axis[i] for i in active_rpm_indices]
    map_axis_active = [map_axis[i] for i in active_map_indices]
    values_active = values_matrix[_np.ix_(active_map_indices, active_rpm_indices)]  # [map][rpm]

    # Ordenar X (MAP) desc; Y (RPM) mantém ordem
    map_idx_sorted_desc = list(_np.argsort(_np.array(map_axis_active))[::-1])
    x_axis_plot = [map_axis_active[i] for i in map_idx_sorted_desc]
    y_axis_plot = rpm_axis_active

    # z deve ter shape [len(Y)][len(X)] => transpor e reordenar colunas conforme X
    z_trans = values_active.T  # [rpm][map]
    import numpy as np
    z_plot = z_trans[:, map_idx_sorted_desc]

    fig = go.Figure(
        data=[
            go.Surface(
                z=z_plot,
                x=x_axis_plot,
                y=y_axis_plot,
                colorscale="RdYlBu",
                showscale=False,
                hovertemplate=("<b>X:</b> %{x}<br>" "<b>Y:</b> %{y}<br>" "<extra></extra>"),
            )
        ]
    )
    fig.update_layout(
        scene=dict(
            xaxis_title="MAP (bar)",
            yaxis_title="RPM",
            zaxis_title="",
            zaxis=dict(visible=False),
            camera=dict(eye=dict(x=1.2, y=1.2, z=0.8)),
        ),
        height=600,
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Estatísticas (3D) se habilitado – usar matriz filtrada
    if show_statistics:
        render_3d_statistics(values_active, map_config)


def render_2d_editor_view(
    axis_values: List[float],
    values: List[float],
    enabled: List[bool],
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    axis_type: str,
    unit: str,
    auto_save: bool,
    vehicle_data: Dict[str, Any],
):
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
                    f"#{i+1}", value=enabled[i], key=f"2d_enabled_{i}"
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
                        key=f"2d_value_{i}",
                    )
                else:
                    st.write(f"{axis_type}: {axis_values[i]}")
                    st.write("(Desabilitado)")

        # Verificar alterações
        if new_values != values or new_enabled != enabled:
            values_changed = True
            st.success("Valores modificados")

            if auto_save:
                if save_2d_map_data_local(
                    vehicle_id, map_type, bank_id, axis_values, new_values, new_enabled
                ):
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


def render_2d_axis_config(
    axis_values: List[float],
    axis_type: str,
    vehicle_id: str,
    map_type: str,
    bank_id: str,
):
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
        st.info(
            "Funcionalidade de modificação de eixo 2D será implementada em versão futura"
        )


def render_2d_values_editor(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data: Dict[str, Any],
    auto_save: bool,
):
    """Renderiza editor de valores para mapas 2D."""

    # Carregar dados do mapa 2D
    map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)

    if map_data is None:
        st.warning("Mapa 2D não encontrado. Gerando padrão...")
        if create_default_2d_map(
            vehicle_id, map_type, bank_id, vehicle_data, map_config
        ):
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

    # Unificar layout com função comum: fornecer um render_editor_fn e callbacks
    # Filtrar apenas valores ativos
    active_indices = [i for i, e in enumerate(enabled) if e]
    active_axis = [axis_values[i] for i in active_indices]
    active_values = [values[i] for i in active_indices]

    import numpy as np
    import pandas as pd

    last_result: Dict[str, Any] = {}

    def render_editor_fn_2d():
        # Construir grid 1×N
        df_data: Dict[str, List[float]] = {}
        for axis_val, value in zip(active_axis, active_values):
            col_name = f"{axis_val:.0f}" if axis_type == "RPM" else f"{axis_val:.2f}"
            df_data[col_name] = [value]
        df = pd.DataFrame(df_data)
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
                    format=f"%.2f",
                )
                for col in df.columns
            },
            key=f"2d_values_editor_{map_type}_{bank_id}",
        )
        edited_values = edited_df.iloc[0].tolist()
        changed = edited_values != active_values
        res = {
            "matrix_display": [edited_values],
            "matrix_full_current": [edited_values],  # 2D como linha
            "x_labels": list(df.columns),
            "y_labels": [""],
            "changed": changed,
            # Referências para callbacks
            "_edited_values": edited_values,
            "_active_indices": active_indices,
            "_axis_values": axis_values,
            "_values": values,
            "_enabled": enabled,
        }
        last_result["res"] = res
        return res

    def _on_save_2d():
        res = last_result.get("res", {})
        new_values = res.get("_values", values).copy()
        new_edited_values = res.get("_edited_values", active_values)
        for idx, new_val in zip(res.get("_active_indices", active_indices), new_edited_values):
            new_values[idx] = new_val
        if save_2d_map_data(
            vehicle_id, map_type, bank_id, res.get("_axis_values", axis_values), new_values, res.get("_enabled", enabled), map_config
        ):
            st.success("Mapa salvo com sucesso!")
            st.rerun()
        else:
            st.error("Erro ao salvar mapa 2D")

    def _on_reset_2d():
        if create_default_2d_map(vehicle_id, map_type, bank_id, vehicle_data, map_config):
            st.success("Restaurado para valores padrão!")
            st.rerun()
        else:
            st.error("Falha ao restaurar padrão")

    def _on_validate_2d():
        res = last_result.get("res", {})
        edited_values = res.get("_edited_values", active_values)
        if all(map_config.get("min_value", 0) <= v <= map_config.get("max_value", 100) for v in edited_values):
            st.success("Todos os valores estão dentro dos limites!")
        else:
            st.error("Alguns valores estão fora dos limites permitidos!")

    render_values_layout_common(
        map_type=map_type,
        map_config=map_config,
        dimension="2D",
        render_editor_fn=render_editor_fn_2d,
        on_save=_on_save_2d,
        on_reset=_on_reset_2d,
        on_validate=_on_validate_2d,
        gradient_height=70,
    )


def render_2d_axes_editor(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data: Dict[str, Any],
):
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
            "Ativo": enabled,
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
                    format="%.0f" if axis_type == "RPM" else "%.2f",
                ),
                "Ativo": st.column_config.CheckboxColumn(),
            },
            key=f"2d_axis_editor_{map_type}_{bank_id}",
        )

        # Botão de salvar
        if st.button(":material/save: Salvar Eixo", key=f"save_axis_2d_{map_type}"):
            new_axis_values = edited_axis_df[f"{axis_type}"].tolist()
            new_enabled = edited_axis_df["Ativo"].tolist()

            # Carregar valores atuais do mapa
            values = map_data.get("values", [])

            # Salvar mudanças
            if save_2d_map_data(
                vehicle_id,
                map_type,
                bank_id,
                new_axis_values,
                values,
                new_enabled,
                map_config,
            ):
                st.success("Eixo salvo com sucesso!")
                st.rerun()


def render_3d_values_editor(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data: Dict[str, Any],
    auto_save: bool,
):
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

        # Layout unificado: fornecer função que renderiza o editor e retorna EditorResult
        def render_editor_fn_3d():
            return render_editor_view(
                values_matrix,
                rpm_axis,
                map_axis,
                rpm_enabled,
                map_enabled,
                map_type,
                map_config,
                vehicle_id,
                bank_id,
                vehicle_data,
                auto_save,
            )

        def _on_save_3d(res: Optional[Dict[str, Any]] = None):
            src = res or {}
            matrix_full = np.array(src.get("matrix_full_current", values_matrix))
            ok = save_map_data(
                vehicle_id,
                map_type,
                bank_id,
                rpm_axis,
                map_axis,
                rpm_enabled,
                map_enabled,
                matrix_full,
            )
            if ok:
                st.success("Mapa 3D salvo com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao salvar mapa 3D")

        def _on_reset_3d():
            ok = persistence_manager.create_default_map(
                vehicle_id, map_type, bank_id, vehicle_data, map_config.get("grid_size", 32)
            )
            if ok:
                st.success("Mapa 3D restaurado para padrão!")
                st.rerun()
            else:
                st.error("Falha ao restaurar mapa 3D")

        def _on_validate_3d(res: Optional[Dict[str, Any]] = None):
            src = res or {}
            matrix_full = np.array(src.get("matrix_full_current", values_matrix))
            valid, messages = validate_3d_map_values(matrix_full, map_type)
            if valid:
                st.success("Matriz válida (sem erros)")
                for w in messages:
                    st.warning(w)
            else:
                if messages:
                    for err in messages:
                        st.error(err)
                else:
                    st.error("Matriz inválida")

        render_values_layout_common(
            map_type=map_type,
            map_config=map_config,
            dimension="3D",
            render_editor_fn=render_editor_fn_3d,
            on_save=_on_save_3d,
            on_reset=_on_reset_3d,
            on_validate=_on_validate_3d,
        )


def render_3d_axes_editor(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data: Dict[str, Any],
):
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
                "Ativo": rpm_enabled,
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
                        min_value=0, max_value=15000, step=100, format="%.0f"
                    ),
                    "Ativo": st.column_config.CheckboxColumn(),
                },
                height=400,
                key=f"3d_rpm_axis_editor_{map_type}_{bank_id}",
            )

            # Botão de salvar
            if st.button(":material/save: Salvar RPM", key=f"save_rpm_3d_{map_type}"):
                new_rpm_axis = edited_rpm_df["RPM"].tolist()
                new_rpm_enabled = edited_rpm_df["Ativo"].tolist()

                if persistence_manager.save_3d_map_data(
                    vehicle_id,
                    map_type,
                    bank_id,
                    new_rpm_axis,
                    map_axis,
                    new_rpm_enabled,
                    map_enabled,
                    np.array(map_data.get("values_matrix", [])),
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
                "Ativo": map_enabled,
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
                        min_value=-1.0, max_value=5.0, step=0.1, format="%.2f bar"
                    ),
                    "Ativo": st.column_config.CheckboxColumn(),
                },
                height=400,
                key=f"3d_map_axis_editor_{map_type}_{bank_id}",
            )

            # Botão de salvar
            if st.button(":material/save: Salvar MAP", key=f"save_map_3d_{map_type}"):
                new_map_axis = edited_map_df["MAP"].tolist()
                new_map_enabled = edited_map_df["Ativo"].tolist()

                if persistence_manager.save_3d_map_data(
                    vehicle_id,
                    map_type,
                    bank_id,
                    rpm_axis,
                    new_map_axis,
                    rpm_enabled,
                    new_map_enabled,
                    np.array(map_data.get("values_matrix", [])),
                ):
                    st.success("Eixo MAP salvo!")
                    st.rerun()
                else:
                    st.error("Falha ao salvar eixo MAP")


def render_ftmanager_copy(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    dimension: str,
):
    """Renderiza funcionalidade de copiar para FTManager."""

    st.subheader("Copiar para FTManager")
    st.caption("Use o botão de copiar no bloco abaixo.")

    # Mostrar valores em formato copiável, padronizando layout para 2D e 3D
    if dimension == "2D":
        map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
        if map_data:
            values = map_data.get("values", [])
            formatted = "\t".join([f"{v:.3f}" for v in values])
            st.code(formatted, language="text")
    else:
        # 3D: carregar matriz e exibir como grade TSV (linhas=RPM desc; colunas=MAP)
        map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
        if map_data:
            import numpy as _np
            rpm_axis = map_data.get("rpm_axis", [])
            map_axis = map_data.get("map_axis", [])
            values_matrix = _np.array(map_data.get("values_matrix", []), dtype=float)
            rpm_enabled = map_data.get("rpm_enabled", [True] * len(rpm_axis))
            map_enabled = map_data.get("map_enabled", [True] * len(map_axis))

            active_rpm_indices = [i for i, e in enumerate(rpm_enabled) if e]
            active_map_indices = [i for i, e in enumerate(map_enabled) if e]

            # Matriz de exibição como no editor: linhas = RPM (reverso), colunas = MAP
            active_rpm_indices_reversed = list(reversed(active_rpm_indices))
            values_lines = []
            for rpm_idx in active_rpm_indices_reversed:
                row_vals = []
                for map_idx in active_map_indices:
                    if map_idx < values_matrix.shape[0] and rpm_idx < values_matrix.shape[1]:
                        row_vals.append(f"{values_matrix[map_idx, rpm_idx]:.3f}")
                    else:
                        row_vals.append("")
                values_lines.append("\t".join(row_vals))
            formatted = "\n".join(values_lines)
            st.code(formatted, language="text")


def render_ftmanager_paste(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    dimension: str,
):
    """Renderiza funcionalidade de colar do FTManager."""

    st.subheader("Colar do FTManager")

    paste_data = st.text_area(
        "Cole os valores do FTManager aqui:",
        height=150,
        key=f"paste_{map_type}_{bank_id}",
    )

    if st.button(":material/content_paste: Aplicar Valores", key=f"apply_paste_{map_type}"):
        if paste_data:
            try:
                # Parse dos valores colados
                values = [float(v) for v in paste_data.replace(",", ".").split()]
                st.success(f"Aplicados {len(values)} valores!")
            except:
                st.error("Formato inválido. Verifique os valores colados.")


def render_data_import(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    dimension: str,
):
    """Renderiza importação de dados."""

    st.subheader("Importar Dados")

    import_option = st.radio(
        "Fonte de importação:",
        ["Arquivo JSON", "Arquivo CSV", "Outro Veículo"],
        key=f"import_source_{map_type}",
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
            if st.button(":material/content_copy: Copiar Mapa"):
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
            {"id": "3", "name": "Veículo 3"},
        ]


def render_data_export(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    dimension: str,
):
    """Renderiza exportação de dados."""

    st.subheader("Exportar Dados")

    export_format = st.radio(
        "Formato de exportação:",
        ["JSON", "CSV", "Texto"],
        key=f"export_format_{map_type}",
        horizontal=True,
    )

    if st.button(":material/download: Baixar Mapa", key=f"download_{map_type}"):
        # Carregar dados conforme dimensão
        if dimension == "2D":
            map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
        else:
            map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)

        if not map_data:
            st.error("Dados do mapa não encontrados para exportação")
            return

        if export_format == "JSON":
            import json
            st.download_button(
                ":material/download: Baixar JSON",
                json.dumps(map_data, indent=2, ensure_ascii=False),
                f"{map_type}_{vehicle_id}.json",
                "application/json",
            )
        elif export_format == "CSV":
            import io, csv
            buf = io.StringIO()
            writer = csv.writer(buf)
            if dimension == "2D":
                axis_values = map_data.get("axis_values", [])
                values = map_data.get("values", [])
                enabled = map_data.get("enabled", [True] * len(values))
                # Cabeçalho
                writer.writerow(["axis", "value", "enabled"])
                for a, v, e in zip(axis_values, values, enabled):
                    writer.writerow([a, f"{float(v):.3f}", int(bool(e))])
            else:
                import numpy as _np
                rpm_axis = map_data.get("rpm_axis", [])
                map_axis = map_data.get("map_axis", [])
                values_matrix = _np.array(map_data.get("values_matrix", []), dtype=float)
                rpm_enabled = map_data.get("rpm_enabled", [True] * len(rpm_axis))
                map_enabled = map_data.get("map_enabled", [True] * len(map_axis))
                active_rpm_indices = [i for i, e in enumerate(rpm_enabled) if e]
                active_map_indices = [i for i, e in enumerate(map_enabled) if e]
                # Cabeçalho: primeira célula vazia + MAP ativos
                header = ["RPM\\MAP"] + [f"{map_axis[i]:.2f}" for i in active_map_indices]
                writer.writerow(header)
                # Linhas: RPM (desc) + valores por MAP
                for rpm_idx in reversed(active_rpm_indices):
                    row = [int(rpm_axis[rpm_idx])]
                    for map_idx in active_map_indices:
                        if map_idx < values_matrix.shape[0] and rpm_idx < values_matrix.shape[1]:
                            row.append(f"{values_matrix[map_idx, rpm_idx]:.3f}")
                        else:
                            row.append("")
                    writer.writerow(row)

            data = buf.getvalue()
            st.download_button(
                ":material/download: Baixar CSV",
                data,
                f"{map_type}_{vehicle_id}.csv",
                "text/csv",
            )
        else:  # Texto
            if dimension == "2D":
                values = map_data.get("values", [])
                formatted = "\t".join([f"{float(v):.3f}" for v in values])
            else:
                import numpy as _np
                rpm_axis = map_data.get("rpm_axis", [])
                map_axis = map_data.get("map_axis", [])
                values_matrix = _np.array(map_data.get("values_matrix", []), dtype=float)
                rpm_enabled = map_data.get("rpm_enabled", [True] * len(rpm_axis))
                map_enabled = map_data.get("map_enabled", [True] * len(map_axis))
                active_rpm_indices = [i for i, e in enumerate(rpm_enabled) if e]
                active_map_indices = [i for i, e in enumerate(map_enabled) if e]
                # Linhas RPM desc, colunas MAP ativos; valores TSV
                lines = []
                for rpm_idx in reversed(active_rpm_indices):
                    row_vals = []
                    for map_idx in active_map_indices:
                        if map_idx < values_matrix.shape[0] and rpm_idx < values_matrix.shape[1]:
                            row_vals.append(f"{values_matrix[map_idx, rpm_idx]:.3f}")
                        else:
                            row_vals.append("")
                    lines.append("\t".join(row_vals))
                formatted = "\n".join(lines)

            st.download_button(
                ":material/download: Baixar Texto",
                formatted,
                f"{map_type}_{vehicle_id}.txt",
                "text/plain",
            )


# Funções auxiliares implementadas usando o sistema de persistência
def load_2d_map_data_local(
    vehicle_id: str, map_type: str, bank_id: str
) -> Optional[Dict[str, Any]]:
    """Carrega dados de mapa 2D."""
    return load_2d_map_data(vehicle_id, map_type, bank_id)


def save_2d_map_data_local(
    vehicle_id: str,
    map_type: str,
    bank_id: str,
    axis_values: List[float],
    values: List[float],
    enabled: List[bool],
) -> bool:
    """Salva dados de mapa 2D usando o persistence manager."""
    try:
        return save_2d_map_data(
            vehicle_id, map_type, bank_id, axis_values, values, enabled
        )
    except Exception as e:
        logger.error(f"Erro ao salvar mapa 2D: {e}")
        return False


def validate_2d_map(
    axis_values: List[float],
    values: List[float],
    enabled: List[bool],
    map_config: Dict[str, Any],
) -> List[str]:
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
            errors.append(
                f"Valor na posição {i+1} fora dos limites ({min_val}-{max_val}): {value}"
            )

    # Verificar ordem crescente do eixo (para alguns tipos)
    axis_type = map_config.get("axis_type", "")
    if axis_type in ["RPM", "TPS", "TEMP", "VOLTAGE"]:
        for i in range(1, len(axis_values)):
            if axis_values[i] < axis_values[i - 1]:
                errors.append(f"Eixo {axis_type} deve estar em ordem crescente")
                break

    return errors


def restore_2d_default_map(
    vehicle_id: str, map_type: str, bank_id: str, map_config: Dict[str, Any]
) -> bool:
    """Restaura mapa 2D para valores padrão."""
    try:
        # Criar novo mapa padrão usando o persistence manager
        return create_default_2d_map(vehicle_id, map_type, bank_id, {}, map_config)
    except Exception as e:
        logger.error(f"Erro ao restaurar mapa 2D padrão: {e}")
        return False


def render_3d_view(
    values_matrix: np.ndarray,
    x_axis: List[float],
    y_axis: List[float],
    map_type: str,
    map_config: Dict[str, Any],
    show_statistics: bool,
):
    """Visualização 3D estilo superfície, recebendo matriz z com shape [len(y_axis)][len(x_axis)]."""
    st.header("Visualização 3D")
    # z deve ter dimensões [len(y_axis)][len(x_axis)]
    z = values_matrix
    fig = go.Figure(
        data=[
            go.Surface(
                z=z,
                x=x_axis,
                y=y_axis,
                colorscale="RdYlBu",
                showscale=False,
                hovertemplate=(
                    "<b>X:</b> %{x}<br>" "<b>Y:</b> %{y}<br>" "<extra></extra>"
                ),
            )
        ]
    )
    fig.update_layout(
        scene=dict(
            xaxis_title="MAP (bar)",
            yaxis_title="RPM",
            zaxis_title="",
            zaxis=dict(visible=False),
            camera=dict(eye=dict(x=1.2, y=1.2, z=0.8)),
        ),
        height=600,
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_2d_view(
    values_matrix: np.ndarray,
    x_axis: List[float],
    y_axis: List[float],
    map_type: str,
    map_config: Dict[str, Any],
    show_statistics: bool,
):
    """Visualização 2D em heatmap recebendo z com shape [len(y_axis)][len(x_axis)] (sem colorbar)."""
    st.header("Visualização 2D (Heatmap)")
    z = values_matrix
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=[f"{x:.3f}" if isinstance(x, float) else str(x) for x in x_axis],
            y=[f"{y:.0f}" if isinstance(y, (int, float)) else str(y) for y in y_axis],
            colorscale="RdYlBu",
            showscale=False,
            hovertemplate=("<b>X:</b> %{x}<br>" "<b>Y:</b> %{y}<br>" "<extra></extra>"),
        )
    )
    fig.update_layout(
        xaxis_title="MAP (bar)",
        yaxis_title="RPM",
        height=500,
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_editor_view(
    values_matrix: np.ndarray,
    rpm_axis: List[float],
    map_axis: List[float],
    rpm_enabled: List[bool],
    map_enabled: List[bool],
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data: Dict[str, Any],
    auto_save: bool,
):
    """Renderiza o grid do editor 3D e retorna dados úteis ao chamador."""

    # Editor de matriz 3D com duas visualizações
    import numpy as np
    import pandas as pd

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
        hide_index=True,
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

    # Criar DataFrame para visualização (gradiente será renderizado pelo chamador)
    display_df = pd.DataFrame(
        filtered_matrix,
        columns=[f"{map_val:.2f}" for map_val in active_map_values],
        index=[f"{int(rpm)}" for rpm in active_rpm_values_reversed],
    )

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
                        modified_matrix[map_idx][rpm_idx] = edited_matrix_df.values[i][
                            j
                        ]

        # Salvar automaticamente se habilitado
        if auto_save:
            save_map_data(
                vehicle_id,
                map_type,
                bank_id,
                rpm_axis,
                map_axis,
                rpm_enabled,
                map_enabled,
                modified_matrix,
            )
            st.success("Salvo automaticamente")

    # Estatísticas removidas aqui; layout comum exibirá métricas

    # Retornar dados úteis ao chamador (para renderização unificada)
    try:
        return {
            "matrix_display": display_df.values.tolist(),
            "matrix_full_current": modified_matrix if matrix_changed else values_matrix,
            "x_labels": [f"{mv:.2f}" for mv in active_map_values],
            "y_labels": [f"{int(rv)}" for rv in active_rpm_values_reversed],
            "rpm_axis": rpm_axis,
            "map_axis": map_axis,
            "rpm_enabled": rpm_enabled,
            "map_enabled": map_enabled,
            "changed": bool(matrix_changed),
        }
    except Exception:
        return None


def render_tools(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data: Dict[str, Any],
    dimension: str,
):
    """Renderiza ferramentas avançadas unificadas para 2D e 3D."""

    # Ações específicas por tipo antes das configurações gerais
    if dimension == "3D" and map_type in ("ve_3d_map", "ve_table_3d_map"):
        st.subheader("Ferramentas de VE 3D")
        st.caption(
            "Regenera a malha VE 3D com base nos eixos atuais (como no painel de referência)"
        )
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button(
                ":material/refresh: Recalcular VE 3D pelos eixos", key=f"regen_ve3d_{vehicle_id}_{bank_id}"
            ):
                if map_type == "ve_table_3d_map":
                    ok = persistence_manager.regenerate_ve_table_3d_map(
                        vehicle_id, bank_id
                    )
                else:
                    ok = persistence_manager.regenerate_ve_3d_map(vehicle_id, bank_id)
                if ok:
                    st.success("VE 3D recalculado e salvo com sucesso")
                    st.rerun()
                else:
                    st.error("Falha ao recalcular VE 3D")
        with col_btn2:
            st.info(
                "Use também 'Aplicar Cálculo' abaixo para salvar a prévia calculada"
            )
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
        },
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
            index=1,  # Balanceada por padrão
        )

        # Fator de segurança
        safety_factor = st.slider(
            "Fator de Segurança",
            min_value=0.8,
            max_value=1.2,
            value=STRATEGY_PRESETS[selected_strategy]["safety_factor"],
            step=0.01,
            key=f"safety_factor_{dimension}_{map_type}_{bank_id}",
            help="Ajuste fino dos valores calculados",
        )

        # Controles específicos por mapa (helper comum)
        st.write("**Configurações Específicas**")
        _spec = render_specific_controls_for_map(
            map_type=map_type,
            dimension=dimension,
            selected_strategy=selected_strategy,
            safety_factor=safety_factor,
            bank_id=bank_id,
        )
        boost_enabled = _spec["boost_enabled"]
        fuel_correction_enabled = _spec["fuel_correction_enabled"]
        regulator_11 = _spec["regulator_11"]
        cl_factor_value = _spec["cl_factor_value"]
        ref_rpm_value = _spec.get("ref_rpm")
        map_ref_value = None
        if dimension == "2D" and map_type == "main_fuel_rpm_2d_map":
            map_ref_value = st.number_input(
                "MAP de referência (bar)",
                min_value=-1.0,
                max_value=5.0,
                value=0.0,
                step=0.1,
                key=f"mapref_{dimension}_{map_type}_{bank_id}",
                help="MAP usado para colapsar o cálculo 3D no 2D por RPM",
            )

    # SEÇÃO 2: Dados do Veículo (coluna direita)
    with calc_col2:
        st.subheader("Dados do Veículo")
        render_vehicle_info_metrics(vehicle_data_session)

    st.markdown("---")

    # SEÇÃO 3: Preview dos Valores Calculados
    st.subheader("Preview dos Valores Calculados")
    show_debug = st.checkbox(
        "Mostrar debug",
        value=False,
        key=f"show_debug_{dimension}_{map_type}_{bank_id}",
        help="Exibe/oculta informações detalhadas do cálculo",
    )

    try:
        # Calcular valores baseado na dimensão
        # Preparar dados do veículo com configuração do regulador
        calc_vehicle = dict(vehicle_data_session)
        calc_vehicle["regulator_1_1"] = regulator_11
        if dimension == "2D":
            prev = compute_preview_2d(
                map_type,
                map_config,
                vehicle_id,
                bank_id,
                calc_vehicle,
                selected_strategy,
                safety_factor,
                fuel_correction_enabled,
                consider_boost=boost_enabled,
                regulator_11=regulator_11,
                ref_rpm=ref_rpm_value,
                map_ref=map_ref_value,
            )
            if prev:
                axis_values = prev["axis_values"]
                enabled = prev["enabled"]
                preview_values = prev["preview_values"]
                unit = prev["unit"]
                st.write(f"**Preview dos valores calculados** ({unit})")
                render_preview_table_common(prev, "2D")
        else:
            prev3 = compute_preview_3d(
                map_type,
                map_config,
                vehicle_id,
                bank_id,
                calc_vehicle,
                selected_strategy,
                safety_factor,
                boost_enabled,
                fuel_correction_enabled,
                regulator_11,
                cl_factor_value,
            )
            if prev3:
                rpm_axis = prev3["rpm_axis"]
                map_axis = prev3["map_axis"]
                rpm_enabled = prev3["rpm_enabled"]
                map_enabled = prev3["map_enabled"]
                calculated_matrix = prev3["matrix"]
                unit = prev3["unit"]
                st.write(f"**Preview dos valores calculados** ({unit})")
                render_preview_table_common(prev3, "3D")
                # Preparar listas ativas para uso no preview gráfico
                active_rpm_indices = [i for i, e in enumerate(rpm_enabled) if e]
                active_map_indices = [i for i, e in enumerate(map_enabled) if e]
                active_rpm_values = [rpm_axis[i] for i in active_rpm_indices]
                active_map_values = [map_axis[i] for i in active_map_indices]

                if show_debug:
                    st.write(f"- calculated_matrix shape: {calculated_matrix.shape}")
                    st.write(
                        f"- Min: {calculated_matrix.min():.3f}, Max: {calculated_matrix.max():.3f}"
                    )
                    st.write(f"- Valores únicos: {len(np.unique(calculated_matrix))}")
                    st.write(
                        f"- Amostra [0,0]: {calculated_matrix[0,0]:.3f}, [0,1]: {calculated_matrix[0,1]:.3f}"
                    )
                    st.divider()

                # Filtrar apenas valores ativos
                active_rpm_indices = [
                    i for i, enabled in enumerate(rpm_enabled) if enabled
                ]
                active_map_indices = [
                    i for i, enabled in enumerate(map_enabled) if enabled
                ]
                active_rpm_values = [rpm_axis[i] for i in active_rpm_indices]
                active_map_values = [map_axis[i] for i in active_map_indices]

                # Criar matriz filtrada para preview
                # NOTA: calculated_matrix é indexada como [map_idx][rpm_idx]
                # Queremos mostrar RPM nas linhas (reverso) e MAP nas colunas

                if show_debug:
                    st.write("DEBUG - Criação da preview_matrix:")
                    st.write(
                        f"- active_rpm_indices: {active_rpm_indices[:5]}... ({len(active_rpm_indices)} total)"
                    )
                    st.write(
                        f"- active_map_indices: {active_map_indices[:5]}... ({len(active_map_indices)} total)"
                    )

                # A visualização do preview e métricas já foram renderizadas pelo helper

    except Exception as e:
        st.error(f"Erro ao calcular preview: {e}")
        return

    st.markdown("---")

    # SEÇÃO 4: Botões de Ação
    action_col1, action_col2 = st.columns(2)

    with action_col1:
        if st.button(
            ":material/check: Aplicar Cálculo",
            type="primary",
            use_container_width=True,
            key=f"apply_{dimension}_{map_type}_{bank_id}",
        ):
            try:
                if dimension == "2D":
                    # Salvar valores 2D
                    if save_2d_map_data(
                        vehicle_id,
                        map_type,
                        bank_id,
                        axis_values,
                        preview_values,
                        enabled,
                        map_config,
                    ):
                        st.success("Valores aplicados com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar valores")
                else:
                    # Salvar matriz 3D
                    if save_map_data(
                        vehicle_id,
                        map_type,
                        bank_id,
                        rpm_axis,
                        map_axis,
                        rpm_enabled,
                        map_enabled,
                        calculated_matrix,
                    ):
                        st.success("Valores aplicados com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar valores")
            except Exception as e:
                st.error(f"Erro ao aplicar cálculo: {e}")

    # Botão de preview (aciona renderização em largura total abaixo)
    with action_col2:
        do_preview = st.button(
            ":material/analytics: Preview Gráfico",
            use_container_width=True,
            key=f"preview_{dimension}_{map_type}_{bank_id}",
        )

    if do_preview:
        st.markdown("---")
        st.subheader("Preview Gráfico (Antes × Depois)")
        col_before, col_after = st.columns(2)
        try:
            if dimension == "2D":
                axis_type = map_config.get("axis_type", "RPM")
                # Antes (valores salvos)
                map2d = load_2d_map_data_local(vehicle_id, map_type, bank_id)
                if map2d:
                    before_axis = map2d.get("axis_values", [])
                    before_vals = map2d.get("values", [])
                    before_enabled = map2d.get("enabled", [True] * len(before_vals))
                    with col_before:
                        st.caption("Antes (salvo)")
                        render_2d_line_chart_inline(
                            before_axis,
                            before_vals,
                            before_enabled,
                            axis_type,
                            unit,
                            key=f"prev2d_before_{map_type}_{bank_id}"
                        )
                # Depois (prévia calculada)
                with col_after:
                    st.caption("Depois (prévia)")
                    render_2d_line_chart_inline(
                        axis_values,
                        preview_values,
                        enabled,
                        axis_type,
                        unit,
                        key=f"prev2d_after_{map_type}_{bank_id}"
                    )
            else:
                # 3D antes (salvo)
                map3d = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
                if map3d:
                    before_rpm = map3d.get("rpm_axis", [])
                    before_map = map3d.get("map_axis", [])
                    before_matrix = np.array(map3d.get("values_matrix", []))
                    before_rpm_enabled = map3d.get("rpm_enabled", [True] * len(before_rpm))
                    before_map_enabled = map3d.get("map_enabled", [True] * len(before_map))
                    with col_before:
                        st.caption("Antes (salvo)")
                        render_3d_surface_inline(
                            before_rpm,
                            before_map,
                            before_matrix,
                            before_rpm_enabled,
                            before_map_enabled,
                            key=f"prev3d_before_{map_type}_{bank_id}"
                        )
                # 3D depois (prévia)
                with col_after:
                    st.caption("Depois (prévia)")
                    render_3d_surface_inline(
                        rpm_axis,
                        map_axis,
                        np.array(calculated_matrix),
                        rpm_enabled,
                        map_enabled,
                        key=f"prev3d_after_{map_type}_{bank_id}"
                    )
        except Exception as e:
            st.error(f"Erro ao gerar gráfico: {e}")


def render_3d_statistics(values_matrix: np.ndarray, map_config: Dict[str, Any]):
    """Renderiza estatísticas do mapa."""
    from src.core.fuel_maps.utils import calculate_matrix_statistics

    stats = calculate_matrix_statistics(values_matrix)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Mínimo", format_value_3_decimals(stats["min"]), delta=None)
    with col2:
        st.metric("Máximo", format_value_3_decimals(stats["max"]), delta=None)
    with col3:
        st.metric("Média", format_value_3_decimals(stats["mean"]), delta=None)
    with col4:
        st.metric("Desvio Padrão", format_value_3_decimals(stats["std"]), delta=None)

def render_values_layout_common(
    map_type: str,
    map_config: Dict[str, Any],
    dimension: str,
    render_editor_fn,
    on_save,
    on_reset,
    on_validate,
    gradient_height: Optional[int] = None,
):
    # Subtítulo sutil com tipo/unidade/grade (se 3D)
    grid_shape = None
    if dimension == "3D":
        # grid_shape será inferida dos labels após o editor
        pass
    render_map_info_header(map_type, map_config, dimension, grid_shape)

    # Valores Editáveis (editor renderiza o grid e retorna dados)
    st.write("**Valores Editáveis:**")
    editor_result = render_editor_fn()

    # Visualização com Gradiente e Métricas
    if isinstance(editor_result, dict):
        unit = map_config.get("unit", "")
        matrix_display = editor_result.get("matrix_display")
        x_labels = editor_result.get("x_labels")
        y_labels = editor_result.get("y_labels")
        if matrix_display and x_labels is not None and y_labels is not None:
            if dimension == "2D":
                render_gradient_table(
                    matrix_display,
                    x_labels,
                    y_labels,
                    unit,
                    height=gradient_height,
                    columns_name=map_config.get("axis_type", "Eixo"),
                    index_name=unit,
                )
            else:
                render_gradient_table(
                    matrix_display,
                    x_labels,
                    y_labels,
                    unit,
                    height=gradient_height,
                    columns_name="MAP (bar)",
                    index_name="RPM",
                )

        # Métricas (sem título)
        if dimension == "2D":
            # matrix_display é 1×N
            row = matrix_display[0] if matrix_display else []
            render_2d_statistics(row, unit)
        else:
            # 3D: usar estatísticas do mapa (sem título)
            full = editor_result.get("matrix_full_current")
            if full is not None:
                render_3d_statistics(np.array(full), map_config)

        # Ações com Material Icons: passar o resultado ao callback quando útil
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(":material/save: Salvar", key=f"save_common_{map_type}"):
                on_save(editor_result)
        with col2:
            if st.button(":material/refresh: Restaurar Padrão", key=f"reset_common_{map_type}"):
                on_reset()
        with col3:
            if st.button(":material/analytics: Validar", key=f"validate_common_{map_type}"):
                on_validate(editor_result)


# Helpers reutilizáveis (info, gradiente, ações)
def render_map_info_header(
    map_type: str, map_config: Dict[str, Any], dimension: str, grid_shape=None
):
    name = map_config.get("display_name") or map_config.get("name", map_type)
    unit = map_config.get("unit", "")
    if dimension == "3D" and grid_shape:
        # grid_shape esperado como (map_count, rpm_count)
        st.info(
            f"Tipo de Mapa: {name} | Unidade: {unit} | Grade: MAP×RPM = {grid_shape[0]}×{grid_shape[1]}"
        )
    else:
        # Para 2D, usar subtítulo sutil
        st.caption(f"Tipo de Mapa: {name} | Unidade: {unit}")


def render_gradient_table(
    values,
    x_labels,
    y_labels,
    unit: str,
    height: Optional[int] = None,
    *,
    columns_name: Optional[str] = None,
    index_name: Optional[str] = None,
):
    import pandas as _pd
    import numpy as _np
    try:
        df = _pd.DataFrame(values, columns=x_labels, index=y_labels)
        # Formatar apenas colunas numéricas para evitar erro de formatação com strings
        numeric_cols = [c for c in df.columns if _np.issubdtype(df[c].dtype, _np.number)]
        styled = df.style.background_gradient(cmap="RdYlBu", axis=None)
        if numeric_cols:
            styled = styled.format({c: "{:.3f}" for c in numeric_cols})
        # Título no mesmo padrão de "Valores Editáveis:"
        st.write("**Visualização com Gradiente:**")
        if height is not None:
            st.dataframe(styled, use_container_width=True, height=height, hide_index=True)
        else:
            st.dataframe(styled, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"Falha ao renderizar gradiente: {e}")


def render_action_buttons(on_save, on_reset, on_validate, key: str = "actions"):
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(":material/save: Salvar", key=f"{key}_save"):
            on_save()
    with col2:
        if st.button(":material/refresh: Restaurar Padrão", key=f"{key}_reset"):
            on_reset()
    with col3:
        if st.button(":material/analytics: Validar", key=f"{key}_validate"):
            on_validate()


def render_vehicle_info_metrics(vehicle_data_session: Dict[str, Any]):
    """Exibe métricas comuns do veículo (usado em 2D e 3D)."""
    # Primeira linha: Cilindrada, Cilindros, Vazão (lb/h)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cilindrada", f"{vehicle_data_session.get('displacement', 2.0):.1f}L")
    with col2:
        st.metric("Cilindros", vehicle_data_session.get('cylinders', 4))
    with col3:
        flow_lbs = vehicle_data_session.get('injector_flow_lbs') or 0.0
        st.metric("Vazão Total (lb/h)", f"{flow_lbs:.1f} lb/h")

    # Segunda linha: Combustível, Boost/Aspiração
    col4, col5 = st.columns(2)
    with col4:
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


def render_2d_line_chart_inline(
    axis_values: List[float],
    values: List[float],
    enabled: List[bool],
    axis_type: str,
    unit: str,
    *,
    key: Optional[str] = None,
):
    import plotly.graph_objects as go
    # Filtrar habilitados
    enabled_indices = [i for i, e in enumerate(enabled) if e and i < len(axis_values) and i < len(values)]
    chart_axis = [axis_values[i] for i in enabled_indices]
    chart_values = [values[i] for i in enabled_indices]
    if not chart_axis or not chart_values:
        st.warning("Nenhum ponto habilitado para exibir")
        return
    fig = go.Figure()
    cmin = min(chart_values)
    cmax = max(chart_values)
    if cmin == cmax:
        cmin -= 1e-9
        cmax += 1e-9
    try:
        theme_base = st.get_option("theme.base")
    except Exception:
        theme_base = None
    outline_color = "#FFFFFF" if str(theme_base).lower() == "dark" else "#000000"
    fig.add_trace(
        go.Scatter(
            x=chart_axis,
            y=chart_values,
            mode="lines+markers",
            name=f"Valores {unit}",
            line=dict(color="red", width=2),
            marker=dict(
                size=9,
                color=chart_values,
                colorscale="RdYlBu",
                showscale=False,
                cmin=cmin,
                cmax=cmax,
                line=dict(width=1.5, color=outline_color),
            ),
        )
    )
    # Linha de corte MAP=0
    try:
        if axis_type.upper() == "MAP" and any(x > 0 for x in chart_axis):
            cut_color = "#FFFFFF66" if str(theme_base).lower() == "dark" else "#00000066"
            shapes = list(fig.layout.shapes) if fig.layout.shapes else []
            shapes.append(dict(type="line", xref="x", yref="paper", x0=0, x1=0, y0=0, y1=1, line=dict(color=cut_color, width=2, dash="dash")))
            fig.update_layout(shapes=shapes)
    except Exception:
        pass
    fig.update_layout(xaxis_title=f"{axis_type}", yaxis_title=f"Valores ({unit})", height=400)
    st.plotly_chart(fig, use_container_width=True, key=key)


def render_3d_surface_inline(
    rpm_axis: List[float],
    map_axis: List[float],
    values_matrix: np.ndarray,
    rpm_enabled: List[bool],
    map_enabled: List[bool],
    *,
    key: Optional[str] = None,
):
    import numpy as _np
    import plotly.graph_objects as go
    # Filtrar por enabled
    active_rpm_indices = [i for i, e in enumerate(rpm_enabled) if e]
    active_map_indices = [i for i, e in enumerate(map_enabled) if e]
    if not active_rpm_indices or not active_map_indices:
        st.warning("Nenhum ponto habilitado para visualização")
        return
    rpm_axis_active = [rpm_axis[i] for i in active_rpm_indices]
    map_axis_active = [map_axis[i] for i in active_map_indices]
    values_active = values_matrix[_np.ix_(active_map_indices, active_rpm_indices)]  # [map][rpm]
    # Ordenar X (MAP) desc; Y (RPM) mantém ordem
    map_idx_sorted_desc = list(_np.argsort(_np.array(map_axis_active))[::-1])
    x_axis_plot = [map_axis_active[i] for i in map_idx_sorted_desc]
    y_axis_plot = rpm_axis_active
    z_plot = values_active.T[:, map_idx_sorted_desc]
    fig = go.Figure(data=[go.Surface(z=z_plot, x=x_axis_plot, y=y_axis_plot, colorscale="RdYlBu")])
    fig.update_layout(scene=dict(xaxis_title="MAP (bar)", yaxis_title="RPM", zaxis_title="", zaxis=dict(visible=False), camera=dict(eye=dict(x=1.2, y=1.2, z=0.8))), height=600, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True, key=key)


# ===== Ferramentas: helpers comuns =====
def render_specific_controls_for_map(
    map_type: str,
    dimension: str,
    selected_strategy: str,
    safety_factor: float,
    bank_id: str,
):
    """Renderiza controles específicos do mapa e retorna flags/valores.

    Retorna dict com:
      - boost_enabled, fuel_correction_enabled, regulator_11, cl_factor_value
    """
    show_injection_controls_3d = dimension == "3D" and map_type == "main_fuel_3d_map"
    show_injection_controls_2d = dimension == "2D" and map_type == "main_fuel_2d_map"
    col_check1, col_check2 = st.columns(2)
    with col_check1:
        boost_enabled = st.checkbox(
            "Aplicar pressão de admissão (MAP) no PW",
            value=True,
            key=f"boost_enabled_{dimension}_{map_type}_{bank_id}",
            help="Considera a pressão absoluta do ar (P_abs) no cálculo. Com boost, a massa de ar por admissão aumenta e o PW tende a subir. Desative para simular PW em regime atmosférico (P_abs=1,0 bar).",
        ) if (show_injection_controls_3d or show_injection_controls_2d) else False
    with col_check2:
        fuel_correction_enabled = st.checkbox(
            "Correção de Combustível",
            value=True,
            key=f"fuel_corr_{dimension}_{map_type}_{bank_id}",
            help="ON: usa AFR estequiométrico do combustível (ex.: Etanol 9.0). OFF: usa 14.7 (gasolina) para isolar variações.",
        ) if (show_injection_controls_3d or show_injection_controls_2d) else False

    regulator_11 = True
    if show_injection_controls_3d or show_injection_controls_2d:
        regulator_11 = st.checkbox(
            "Considerar pressão de turbo (1:1) no combustível",
            value=True,
            key=f"reg11_{dimension}_{map_type}_{bank_id}",
            help="ON: ΔP constante (P_base). OFF: ΔP = P_base − MAP_rel (fluxo cai em boost e o PW tende a subir).",
        )

    cl_factor_value = safety_factor if (dimension == "3D" and map_type == "lambda_target_3d_map") else 1.0
    ref_rpm = None
    if show_injection_controls_2d:
        ref_rpm = st.number_input(
            "RPM de referência",
            min_value=600,
            max_value=12000,
            value=3000,
            step=100,
            key=f"refrpm_{dimension}_{map_type}_{bank_id}",
            help="RPM usado para colapsar o cálculo 3D no 2D",
        )
    return {
        "boost_enabled": boost_enabled,
        "fuel_correction_enabled": fuel_correction_enabled,
        "regulator_11": regulator_11,
        "cl_factor_value": cl_factor_value,
        "ref_rpm": ref_rpm,
    }


def compute_preview_2d(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data_session: Dict[str, Any],
    selected_strategy: str,
    safety_factor: float,
    fuel_correction_enabled: bool,
    *,
    consider_boost: bool = True,
    regulator_11: bool = True,
    ref_rpm: Optional[float] = None,
    map_ref: Optional[float] = None,
):
    import pandas as pd
    from src.core.fuel_maps.calculations import calculate_map_values_universal
    map_data = load_2d_map_data_local(vehicle_id, map_type, bank_id)
    if not map_data:
        return None
    axis_values = map_data.get("axis_values", [])
    enabled = map_data.get("enabled", [True] * len(axis_values))
    # Para main_fuel_2d_map, usar cálculo realista com VE/λ/ΔP colapsando 3D por RPM de referência
    if map_type == "main_fuel_2d_map":
        # Determinar RPM de referência: usar ref_rpm se fornecido, senão mediana dos eixos 3D (se existirem) ou 3000
        rrpm = ref_rpm
        if rrpm is None:
            m3d = persistence_manager.load_3d_map_data(vehicle_id, "main_fuel_3d_map", bank_id) or \
                  persistence_manager.load_3d_map_data(vehicle_id, "ve_3d_map", bank_id)
            if m3d and m3d.get("rpm_axis"):
                arr = [v for v, e in zip(m3d.get("rpm_axis", []), [True]*len(m3d.get("rpm_axis", [])))]
                rrpm = float(arr[len(arr)//2]) if arr else 3000.0
            else:
                rrpm = 3000.0
        preview_values_all = calculate_map_values_universal(
            map_type,
            axis_values,
            vehicle_data_session,
            selected_strategy,
            safety_factor,
            apply_fuel_corr=fuel_correction_enabled,
            consider_boost=consider_boost,
            regulator_11=regulator_11,
            ref_rpm=rrpm,
        )
    elif map_type == "main_fuel_rpm_2d_map":
        mref = map_ref
        if mref is None:
            # inferir mediana dos MAPs do 3D
            m3d = persistence_manager.load_3d_map_data(vehicle_id, "main_fuel_3d_map", bank_id) or \
                  persistence_manager.load_3d_map_data(vehicle_id, "ve_3d_map", bank_id)
            if m3d and m3d.get("map_axis"):
                arr = m3d.get("map_axis", [])
                mref = float(arr[len(arr)//2]) if arr else 0.0
            else:
                mref = 0.0
        preview_values_all = calculate_map_values_universal(
            map_type,
            axis_values,
            vehicle_data_session,
            selected_strategy,
            safety_factor,
            apply_fuel_corr=fuel_correction_enabled,
            consider_boost=consider_boost,
            regulator_11=regulator_11,
            map_ref=mref,
        )
    else:
        preview_values_all = calculate_map_values_universal(
            map_type,
            axis_values,
            vehicle_data_session,
            selected_strategy,
            safety_factor,
            apply_fuel_corr=fuel_correction_enabled,
        )
    column_headers = {}
    filtered_preview_values = []
    for i, (axis_val, enabled_flag) in enumerate(zip(axis_values, enabled)):
        if enabled_flag:
            header = f"{axis_val:.1f}"
            column_headers[header] = preview_values_all[i]
            filtered_preview_values.append(preview_values_all[i])
    preview_df = pd.DataFrame([column_headers])
    unit = map_config.get("unit", "ms")
    return {
        "axis_values": axis_values,
        "enabled": enabled,
        "preview_df": preview_df,
        "preview_values": filtered_preview_values,
        "unit": unit,
        "axis_type": map_config.get("axis_type", "Eixo"),
    }


def compute_preview_3d(
    map_type: str,
    map_config: Dict[str, Any],
    vehicle_id: str,
    bank_id: str,
    vehicle_data_session: Dict[str, Any],
    selected_strategy: str,
    safety_factor: float,
    boost_enabled: bool,
    fuel_correction_enabled: bool,
    regulator_11: bool,
    cl_factor_value: float,
):
    import numpy as np
    map_data = persistence_manager.load_3d_map_data(vehicle_id, map_type, bank_id)
    if not map_data:
        return None
    rpm_axis = map_data.get("rpm_axis", [])
    map_axis = map_data.get("map_axis", [])
    rpm_enabled = map_data.get("rpm_enabled", [True] * len(rpm_axis))
    map_enabled = map_data.get("map_enabled", [True] * len(map_axis))

    if map_type == "ve_3d_map":
        from src.core.fuel_maps.calculations import generate_ve_3d_matrix
        calculated_matrix = generate_ve_3d_matrix(rpm_axis, map_axis)
        unit = "VE"
    else:
        from src.core.fuel_maps.calculations import calculate_3d_map_values_universal
        kwargs = dict(
            strategy=selected_strategy,
            safety_factor=safety_factor,
            consider_boost=boost_enabled,
            apply_fuel_corr=fuel_correction_enabled,
            cl_factor=cl_factor_value,
        )
        # Preparar VE e AFR se necessário é feito internamente pela função universal
        calculated_matrix = calculate_3d_map_values_universal(
            map_type, rpm_axis, map_axis, dict(vehicle_data_session), **kwargs
        )
        unit = map_config.get("unit", "ms")

    return {
        "rpm_axis": rpm_axis,
        "map_axis": map_axis,
        "rpm_enabled": rpm_enabled,
        "map_enabled": map_enabled,
        "matrix": calculated_matrix,
        "unit": unit,
        "axis_type": map_config.get("axis_type", "Eixo"),
    }


def render_preview_table_common(preview_obj: Dict[str, Any], dimension: str):
    import pandas as pd
    import numpy as np
    if dimension == "2D":
        df = preview_obj.get("preview_df")
        if df is not None:
            axis_type = preview_obj.get("axis_type", "Eixo")
            unit = preview_obj.get("unit", "")
            df2 = df.copy()
            df2.insert(0, axis_type, [unit])
            styled = df2.style.background_gradient(cmap="RdYlBu", axis=1)
            # Formatar apenas colunas numéricas
            numeric_cols = [
                c for c in df2.columns if np.issubdtype(df2[c].dtype, np.number)
            ]
            if numeric_cols:
                styled = styled.format({c: "{:.2f}" for c in numeric_cols})
            styled = styled.set_table_styles([
                {"selector": "th", "props": [("min-width", "36px"), ("max-width", "36px"), ("padding", "0 4px"), ("font-size", "11px")]},
                {"selector": "td", "props": [("min-width", "36px"), ("max-width", "36px"), ("padding", "0 4px"), ("font-size", "11px")]},
            ])
            st.dataframe(styled, use_container_width=True, height=70)
    else:
        # 3D: construir DataFrame linhas=RPM desc; colunas=MAP ativos
        rpm_axis = preview_obj.get("rpm_axis", [])
        map_axis = preview_obj.get("map_axis", [])
        rpm_enabled = preview_obj.get("rpm_enabled", [True] * len(rpm_axis))
        map_enabled = preview_obj.get("map_enabled", [True] * len(map_axis))
        matrix = np.array(preview_obj.get("matrix"))
        active_rpm_indices = [i for i, e in enumerate(rpm_enabled) if e]
        active_map_indices = [i for i, e in enumerate(map_enabled) if e]
        rows = []
        for rpm_idx in reversed(active_rpm_indices):
            row = []
            for map_idx in active_map_indices:
                if map_idx < matrix.shape[0] and rpm_idx < matrix.shape[1]:
                    row.append(matrix[map_idx, rpm_idx])
                else:
                    row.append(np.nan)
            rows.append(row)
        df = pd.DataFrame(rows, columns=[f"{map_axis[i]:.2f}" for i in active_map_indices], index=[f"{int(rpm_axis[i])}" for i in reversed(active_rpm_indices)])
        styled = df.style.background_gradient(cmap="RdYlBu", axis=None)
        numeric_cols = [c for c in df.columns if np.issubdtype(df[c].dtype, np.number)]
        if numeric_cols:
            styled = styled.format({c: "{:.3f}" for c in numeric_cols})
        st.dataframe(styled, use_container_width=True, hide_index=True)


def save_map_data(
    vehicle_id: str,
    map_type: str,
    bank_id: str,
    rpm_axis: List[float],
    map_axis: List[float],
    rpm_enabled: List[bool],
    map_enabled: List[bool],
    values_matrix: np.ndarray,
) -> bool:
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
            values_matrix=values_matrix,
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
