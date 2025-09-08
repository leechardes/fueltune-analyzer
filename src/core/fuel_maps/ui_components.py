"""
Componentes UI reutilizáveis para mapas de combustível 3D.
Funções para renderizar gráficos, editores e interfaces complexas.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

try:
    import streamlit as st
except ImportError:
    # Mock do Streamlit para testes
    class MockStreamlit:
        @staticmethod
        def subheader(text): print(f"## {text}")
        @staticmethod 
        def write(text): print(text)
        @staticmethod
        def columns(n): return [None] * n
        @staticmethod
        def metric(label, value, **kwargs): print(f"{label}: {value}")
        @staticmethod
        def selectbox(label, options, **kwargs): return options[0] if options else None
        @staticmethod
        def checkbox(label, **kwargs): return kwargs.get('value', False)
        @staticmethod
        def number_input(label, **kwargs): return kwargs.get('value', 0.0)
        @staticmethod
        def button(label, **kwargs): return False
        @staticmethod
        def slider(label, **kwargs): return kwargs.get('value', 0.0)
        @staticmethod
        def expander(label, **kwargs): return MockStreamlit()
        @staticmethod
        def dataframe(df, **kwargs): print("DataFrame displayed")
        @staticmethod
        def success(text): print(f"✅ {text}")
        @staticmethod
        def warning(text): print(f"⚠️  {text}")
        @staticmethod
        def error(text): print(f"❌ {text}")
        def __enter__(self): return self
        def __exit__(self, *args): pass
    st = MockStreamlit()

from .models import Map3DData, MapConfig
from .utils import format_value_3_decimals, calculate_matrix_statistics

logger = logging.getLogger(__name__)

class UIComponents:
    """Componentes UI reutilizáveis para mapas 3D."""

    @staticmethod
    def render_3d_surface_plot(
        data_matrix: np.ndarray,
        rpm_axis: List[float],
        map_axis: List[float],
        map_type: str,
        title: Optional[str] = None
    ):
        """Renderiza gráfico de superfície 3D."""
        try:
            if go is None:
                print("⚠️ Plotly não disponível - gráfico 3D não pode ser renderizado")
                return None
            # Configurar título e unidades baseado no tipo
            type_config = {
                "main_fuel_3d_map": {"title": "Mapa de Injeção 3D", "unit": "ms", "colorscale": "Viridis"},
                "lambda_target_3d_map": {"title": "Mapa Lambda 3D", "unit": "λ", "colorscale": "RdYlBu"},
                "ignition_3d_map": {"title": "Mapa Ignição 3D", "unit": "°", "colorscale": "Plasma"},
                "afr_target_3d_map": {"title": "Mapa AFR 3D", "unit": "AFR", "colorscale": "Cividis"},
            }
            
            config = type_config.get(map_type, {
                "title": "Mapa 3D", 
                "unit": "", 
                "colorscale": "Viridis"
            })
            
            plot_title = title or config["title"]
            unit = config["unit"]
            colorscale = config["colorscale"]

            # Criar figura 3D
            fig = go.Figure(data=[
                go.Surface(
                    z=data_matrix,
                    x=rpm_axis,
                    y=map_axis,
                    colorscale=colorscale,
                    colorbar=dict(title=f"Valor ({unit})"),
                    hovertemplate=(
                        "<b>RPM:</b> %{x:.0f}<br>"
                        "<b>MAP:</b> %{y:.3f} bar<br>"
                        "<b>Valor:</b> %{z:.3f} " + unit + "<br>"
                        "<extra></extra>"
                    )
                )
            ])

            # Layout do gráfico
            fig.update_layout(
                title=plot_title,
                scene=dict(
                    xaxis_title="RPM",
                    yaxis_title="MAP (bar)",
                    zaxis_title=f"Valor ({unit})",
                    camera=dict(
                        eye=dict(x=1.2, y=1.2, z=0.8)
                    )
                ),
                width=800,
                height=600,
                margin=dict(l=0, r=0, t=50, b=0)
            )

            return fig

        except Exception as e:
            logger.error(f"Erro ao renderizar gráfico 3D: {e}")
            # Retornar figura vazia em caso de erro
            return go.Figure()

    @staticmethod
    def render_2d_heatmap(
        data_matrix: np.ndarray,
        rpm_axis: List[float],
        map_axis: List[float],
        map_type: str,
        title: Optional[str] = None
    ):
        """Renderiza mapa de calor 2D."""
        try:
            if go is None:
                print("⚠️ Plotly não disponível - heatmap não pode ser renderizado")
                return None
            type_config = {
                "main_fuel_3d_map": {"title": "Mapa de Injeção (Heatmap)", "unit": "ms"},
                "lambda_target_3d_map": {"title": "Mapa Lambda (Heatmap)", "unit": "λ"},
                "ignition_3d_map": {"title": "Mapa Ignição (Heatmap)", "unit": "°"},
                "afr_target_3d_map": {"title": "Mapa AFR (Heatmap)", "unit": "AFR"},
            }
            
            config = type_config.get(map_type, {"title": "Mapa 2D", "unit": ""})
            plot_title = title or config["title"]
            unit = config["unit"]

            fig = go.Figure(data=go.Heatmap(
                z=data_matrix,
                x=[f"{rpm:.0f}" for rpm in rpm_axis],
                y=[f"{map_val:.3f}" for map_val in map_axis],
                colorscale='Viridis',
                colorbar=dict(title=f"Valor ({unit})"),
                hovertemplate=(
                    "<b>RPM:</b> %{x}<br>"
                    "<b>MAP:</b> %{y} bar<br>"
                    "<b>Valor:</b> %{z:.3f} " + unit + "<br>"
                    "<extra></extra>"
                )
            ))

            fig.update_layout(
                title=plot_title,
                xaxis_title="RPM",
                yaxis_title="MAP (bar)",
                width=700,
                height=500
            )

            return fig

        except Exception as e:
            logger.error(f"Erro ao renderizar heatmap: {e}")
            return go.Figure()

    @staticmethod
    def render_matrix_editor(
        data_matrix: np.ndarray,
        enabled_matrix: List[List[bool]],
        rpm_axis: List[float],
        map_axis: List[float],
        map_type: str,
        key_prefix: str = "matrix_editor"
    ) -> Tuple[np.ndarray, bool]:
        """Renderiza editor interativo de matriz."""
        try:
            st.subheader("Editor de Matriz")
            
            # Informações da matriz
            stats = calculate_matrix_statistics(data_matrix)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Mínimo", format_value_3_decimals(stats["min"]))
            with col2:
                st.metric("Máximo", format_value_3_decimals(stats["max"]))
            with col3:
                st.metric("Média", format_value_3_decimals(stats["mean"]))
            with col4:
                st.metric("Desvio", format_value_3_decimals(stats["std"]))
            
            # Opções de edição
            st.write("**Opções de Edição:**")
            
            col1, col2 = st.columns(2)
            with col1:
                edit_mode = st.selectbox(
                    "Modo de Edição",
                    ["Visualizar", "Editar Célula", "Aplicar Fator", "Suavizar"],
                    key=f"{key_prefix}_edit_mode"
                )
            
            with col2:
                show_enabled = st.checkbox(
                    "Mostrar apenas células ativas",
                    value=True,
                    key=f"{key_prefix}_show_enabled"
                )
            
            modified = False
            result_matrix = data_matrix.copy()
            
            if edit_mode == "Editar Célula":
                # Editor de célula individual
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    edit_row = st.selectbox(
                        "Linha (MAP)",
                        range(len(map_axis)),
                        format_func=lambda x: f"{x}: {format_value_3_decimals(map_axis[x])} bar",
                        key=f"{key_prefix}_edit_row"
                    )
                
                with col2:
                    edit_col = st.selectbox(
                        "Coluna (RPM)",
                        range(len(rpm_axis)),
                        format_func=lambda x: f"{x}: {rpm_axis[x]:.0f} RPM",
                        key=f"{key_prefix}_edit_col"
                    )
                
                with col3:
                    if (edit_row < len(enabled_matrix) and 
                        edit_col < len(enabled_matrix[edit_row]) and
                        enabled_matrix[edit_row][edit_col]):
                        
                        current_value = data_matrix[edit_row, edit_col]
                        new_value = st.number_input(
                            "Novo Valor",
                            value=float(current_value),
                            format="%.3f",
                            key=f"{key_prefix}_edit_value"
                        )
                        
                        if st.button("Aplicar", key=f"{key_prefix}_apply_edit"):
                            result_matrix[edit_row, edit_col] = new_value
                            modified = True
                            st.success(f"Valor alterado: {format_value_3_decimals(current_value)} → {format_value_3_decimals(new_value)}")
                    else:
                        st.warning("Célula desabilitada")
            
            elif edit_mode == "Aplicar Fator":
                col1, col2 = st.columns(2)
                
                with col1:
                    factor = st.number_input(
                        "Fator Multiplicativo",
                        min_value=0.1,
                        max_value=3.0,
                        value=1.0,
                        step=0.1,
                        key=f"{key_prefix}_factor"
                    )
                
                with col2:
                    apply_to = st.selectbox(
                        "Aplicar a:",
                        ["Toda matriz", "Apenas células ativas", "Região selecionada"],
                        key=f"{key_prefix}_apply_to"
                    )
                
                if st.button("Aplicar Fator", key=f"{key_prefix}_apply_factor"):
                    if apply_to == "Toda matriz":
                        result_matrix = data_matrix * factor
                    elif apply_to == "Apenas células ativas":
                        for i in range(len(enabled_matrix)):
                            for j in range(len(enabled_matrix[i])):
                                if enabled_matrix[i][j]:
                                    result_matrix[i, j] = data_matrix[i, j] * factor
                    
                    modified = True
                    st.success(f"Fator {factor} aplicado com sucesso")
            
            elif edit_mode == "Suavizar":
                col1, col2 = st.columns(2)
                
                with col1:
                    smooth_factor = st.slider(
                        "Intensidade da Suavização",
                        min_value=0.1,
                        max_value=1.0,
                        value=0.3,
                        key=f"{key_prefix}_smooth"
                    )
                
                with col2:
                    if st.button("Aplicar Suavização", key=f"{key_prefix}_apply_smooth"):
                        # Implementação básica de suavização
                        from .utils import smooth_matrix
                        result_matrix = smooth_matrix(data_matrix)
                        modified = True
                        st.success("Suavização aplicada")
            
            # Mostrar tabela de dados (limitada para performance)
            if st.expander("Visualizar Dados da Matriz", expanded=False):
                display_matrix = result_matrix.copy()
                
                # Aplicar máscara se requested
                if show_enabled:
                    for i in range(len(enabled_matrix)):
                        for j in range(len(enabled_matrix[i])):
                            if not enabled_matrix[i][j]:
                                display_matrix[i, j] = np.nan
                
                # Criar DataFrame para exibição
                if pd is None:
                    st.write("Pandas não disponível - tabela não pode ser renderizada")
                    return result_matrix, modified
                    
                df = pd.DataFrame(
                    display_matrix,
                    index=[f"MAP_{i}_{format_value_3_decimals(map_axis[i])}" for i in range(len(map_axis))],
                    columns=[f"RPM_{i}_{rpm_axis[i]:.0f}" for i in range(len(rpm_axis))]
                )
                
                # Mostrar apenas primeiras/últimas linhas se muito grande
                if len(df) > 10:
                    st.write("Primeiras 5 linhas:")
                    st.dataframe(df.head(5), use_container_width=True)
                    st.write("Últimas 5 linhas:")
                    st.dataframe(df.tail(5), use_container_width=True)
                else:
                    st.dataframe(df, use_container_width=True)
            
            return result_matrix, modified

        except Exception as e:
            logger.error(f"Erro no editor de matriz: {e}")
            return data_matrix, False

    @staticmethod
    def render_axis_config(
        axis_values: List[float],
        axis_type: str,
        enabled: List[bool],
        key_prefix: str = "axis_config"
    ) -> Tuple[List[float], List[bool], bool]:
        """Renderiza configuração de eixo."""
        try:
            st.subheader(f"Configuração Eixo {axis_type}")
            
            modified = False
            result_values = axis_values.copy()
            result_enabled = enabled.copy()
            
            # Informações básicas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pontos Totais", len(axis_values))
            with col2:
                active_count = sum(enabled)
                st.metric("Pontos Ativos", active_count)
            with col3:
                if len(axis_values) > 1:
                    span = axis_values[-1] - axis_values[0]
                    st.metric("Intervalo", f"{span:.2f}")
            
            # Opções de configuração
            config_mode = st.selectbox(
                "Modo de Configuração",
                ["Visualizar", "Editar Manual", "Gerar Automático", "Habilitar/Desabilitar"],
                key=f"{key_prefix}_{axis_type}_mode"
            )
            
            if config_mode == "Editar Manual":
                st.write("**Editar Valores Manualmente:**")
                
                # Mostrar apenas alguns valores para edição (evitar UI muito carregada)
                num_values = len(axis_values)
                edit_indices = [0, num_values//4, num_values//2, 3*num_values//4, num_values-1]
                edit_indices = [i for i in edit_indices if i < num_values]
                
                for idx in edit_indices:
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"Posição {idx}:")
                    
                    with col2:
                        new_value = st.number_input(
                            f"Valor",
                            value=float(axis_values[idx]),
                            format="%.3f",
                            key=f"{key_prefix}_{axis_type}_val_{idx}",
                            label_visibility="collapsed"
                        )
                        
                        if new_value != axis_values[idx]:
                            result_values[idx] = new_value
                            modified = True
                    
                    with col3:
                        result_enabled[idx] = st.checkbox(
                            "Ativo",
                            value=enabled[idx],
                            key=f"{key_prefix}_{axis_type}_en_{idx}"
                        )
                        
                        if result_enabled[idx] != enabled[idx]:
                            modified = True
            
            elif config_mode == "Gerar Automático":
                st.write("**Gerar Valores Automaticamente:**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    start_val = st.number_input(
                        f"Valor Inicial ({axis_type})",
                        value=float(axis_values[0]) if axis_values else 0.0,
                        key=f"{key_prefix}_{axis_type}_start"
                    )
                
                with col2:
                    end_val = st.number_input(
                        f"Valor Final ({axis_type})",
                        value=float(axis_values[-1]) if axis_values else 100.0,
                        key=f"{key_prefix}_{axis_type}_end"
                    )
                
                with col3:
                    spacing = st.selectbox(
                        "Espaçamento",
                        ["Linear", "Logarítmico"],
                        key=f"{key_prefix}_{axis_type}_spacing"
                    )
                
                if st.button(f"Gerar Eixo {axis_type}", key=f"{key_prefix}_{axis_type}_generate"):
                    from .utils import generate_linear_axis, generate_logarithmic_axis
                    
                    if spacing == "Linear":
                        result_values = generate_linear_axis(start_val, end_val, len(axis_values))
                    else:
                        result_values = generate_logarithmic_axis(start_val, end_val, len(axis_values))
                    
                    modified = True
                    st.success(f"Eixo {axis_type} gerado automaticamente")
            
            elif config_mode == "Habilitar/Desabilitar":
                st.write("**Configurar Pontos Ativos:**")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Habilitar Todos", key=f"{key_prefix}_{axis_type}_enable_all"):
                        result_enabled = [True] * len(enabled)
                        modified = True
                
                with col2:
                    if st.button(f"Desabilitar Todos", key=f"{key_prefix}_{axis_type}_disable_all"):
                        result_enabled = [False] * len(enabled)
                        modified = True
                
                # Range de habilitação
                range_start = st.slider(
                    f"Habilitar do índice",
                    0, len(axis_values)-1, 0,
                    key=f"{key_prefix}_{axis_type}_range_start"
                )
                range_end = st.slider(
                    f"Até o índice",
                    range_start, len(axis_values)-1, len(axis_values)-1,
                    key=f"{key_prefix}_{axis_type}_range_end"
                )
                
                if st.button(f"Aplicar Range", key=f"{key_prefix}_{axis_type}_apply_range"):
                    for i in range(len(result_enabled)):
                        result_enabled[i] = range_start <= i <= range_end
                    modified = True
                    st.success(f"Range aplicado: {range_start} a {range_end}")
            
            # Visualização dos valores
            if st.expander(f"Visualizar Valores {axis_type}", expanded=False):
                display_data = []
                for i, (val, en) in enumerate(zip(result_values, result_enabled)):
                    display_data.append({
                        "Índice": i,
                        f"Valor ({axis_type})": format_value_3_decimals(val),
                        "Ativo": "✅" if en else "❌"
                    })
                
                if pd is not None:
                    df = pd.DataFrame(display_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    # Fallback para exibir dados sem pandas
                    for item in display_data:
                        st.write(f"{item['Índice']}: {item[f'Valor ({axis_type})']}{'' if item['Ativo'] == '✅' else ' (inativo)'}")
            
            return result_values, result_enabled, modified

        except Exception as e:
            logger.error(f"Erro na configuração do eixo: {e}")
            return axis_values, enabled, False

    @staticmethod
    def render_map_comparison(
        matrix1: np.ndarray,
        matrix2: np.ndarray,
        labels: Tuple[str, str],
        rpm_axis: List[float],
        map_axis: List[float]
    ):
        """Renderiza comparação entre dois mapas."""
        try:
            st.subheader("Comparação de Mapas")
            
            col1, col2 = st.columns(2)
            
            # Estatísticas comparativas
            stats1 = calculate_matrix_statistics(matrix1)
            stats2 = calculate_matrix_statistics(matrix2)
            
            with col1:
                st.write(f"**{labels[0]}**")
                st.write(f"Média: {format_value_3_decimals(stats1['mean'])}")
                st.write(f"Min/Max: {format_value_3_decimals(stats1['min'])} / {format_value_3_decimals(stats1['max'])}")
            
            with col2:
                st.write(f"**{labels[1]}**")
                st.write(f"Média: {format_value_3_decimals(stats2['mean'])}")
                st.write(f"Min/Max: {format_value_3_decimals(stats2['min'])} / {format_value_3_decimals(stats2['max'])}")
            
            # Matriz de diferenças
            diff_matrix = matrix2 - matrix1
            diff_stats = calculate_matrix_statistics(diff_matrix)
            
            st.write("**Diferenças:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Diferença Média", format_value_3_decimals(diff_stats['mean']))
            with col2:
                st.metric("Diferença Máxima", format_value_3_decimals(diff_stats['max']))
            with col3:
                st.metric("Diferença Mínima", format_value_3_decimals(diff_stats['min']))
            
            # Heatmap das diferenças
            diff_fig = UIComponents.render_2d_heatmap(
                diff_matrix, rpm_axis, map_axis, "comparison",
                title=f"Diferenças: {labels[1]} - {labels[0]}"
            )
            st.plotly_chart(diff_fig, use_container_width=True)

        except Exception as e:
            logger.error(f"Erro na comparação de mapas: {e}")
            st.error("Erro ao renderizar comparação de mapas")

# Instância global para conveniência
ui_components = UIComponents()