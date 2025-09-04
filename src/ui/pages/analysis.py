"""
Data Analysis Page - FuelTune Analyzer.

Página de análise de dados com visualizações interativas,
tabela interativa com filtros, comparação entre sessões
e estatísticas detalhadas.

Features:
- Tabela interativa com filtros avançados
- Gráficos plotly dinâmicos e interativos
- Comparação entre sessões
- Estatísticas detalhadas
- Export de dados filtrados
- Análise temporal

Author: A03-UI-STREAMLIT Agent
Created: 2025-01-02
"""

from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

try:
    # Tentar importação relativa primeiro (para quando chamado como módulo)
    from ...data.database import FuelTechCoreData, get_database
    from ...utils.logging_config import get_logger
    from ..components.metric_card import MetricCard
    from ..components.session_selector import SessionSelector
except ImportError:
    # Fallback para importação absoluta (quando executado via st.navigation)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.data.database import FuelTechCoreData, get_database
    from src.utils.logging_config import get_logger
    from src.ui.components.metric_card import MetricCard
    from src.ui.components.session_selector import SessionSelector

logger = get_logger(__name__)


class DataAnalysisManager:
    """
    Gerenciador de análise de dados.

    Responsável por:
    - Carregamento e filtragem de dados
    - Geração de visualizações interativas
    - Cálculos estatísticos avançados
    - Comparação entre sessões
    - Export de dados
    """

    def __init__(self):
        self.db = get_database()
        self.metric_card = MetricCard()

    @st.cache_data(ttl=300)
    def load_session_data(
        _self, session_id: str, limit: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """
        Carregar dados completos da sessão.

        Args:
            session_id: ID da sessão
            limit: Limite de registros (None para todos)

        Returns:
            DataFrame com os dados ou None
        """
        try:
            _self.db.initialize_database()
            with _self.db.get_session() as db_session:
                query = (
                    db_session.query(FuelTechCoreData)
                    .filter(FuelTechCoreData.session_id == session_id)
                    .order_by(FuelTechCoreData.time)
                )

                if limit:
                    query = query.limit(limit)

                core_data = query.all()
                # Session is automatically closed by context manager

            if not core_data:
                return None

            # Converter para DataFrame
            data_list = []
            for record in core_data:
                data_list.append(
                    {
                        "time": record.time,
                        "rpm": record.rpm,
                        "tps": record.tps,
                        "throttle_position": record.throttle_position,
                        "ignition_timing": record.ignition_timing,
                        "map": record.map,
                        "closed_loop_target": record.closed_loop_target,
                        "closed_loop_o2": record.closed_loop_o2,
                        "closed_loop_correction": record.closed_loop_correction,
                        "o2_general": record.o2_general,
                        "ethanol_content": record.ethanol_content,
                        "two_step": record.two_step,
                        "launch_validated": record.launch_validated,
                        "gear": record.gear,
                        "fuel_temp": record.fuel_temp,
                        "flow_bank_a": record.flow_bank_a,
                        "injection_phase_angle": record.injection_phase_angle,
                        "injector_duty_a": record.injector_duty_a,
                        "injection_time_a": record.injection_time_a,
                        "fuel_pressure": record.fuel_pressure,
                        "fuel_level": record.fuel_level,
                        "engine_temp": record.engine_temp,
                        "air_temp": record.air_temp,
                        "oil_pressure": record.oil_pressure,
                        "battery_voltage": record.battery_voltage,
                        "ignition_dwell": record.ignition_dwell,
                        "fan1_enrichment": record.fan1_enrichment,
                        "engine_sync": record.engine_sync,
                        "decel_cutoff": record.decel_cutoff,
                        "engine_cranking": record.engine_cranking,
                        "idle": record.idle,
                        "first_pulse_cranking": record.first_pulse_cranking,
                        "accel_decel_injection": record.accel_decel_injection,
                        "active_adjustment": record.active_adjustment,
                        "fan1": record.fan1,
                        "fan2": record.fan2,
                        "fuel_pump": record.fuel_pump,
                    }
                )

            return pd.DataFrame(data_list)

        except Exception as e:
            logger.error(f"Erro ao carregar dados da sessão: {str(e)}")
            return None

    def render_data_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Renderizar filtros para os dados."""
        st.markdown("### Filtros de Dados")

        with st.expander("Filtros Avançados", expanded=True):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                # Filtro de tempo
                if "time" in df.columns and not df["time"].empty:
                    time_min, time_max = float(df["time"].min()), float(df["time"].max())
                    time_range = st.slider(
                        "Intervalo de Tempo (s)",
                        min_value=time_min,
                        max_value=time_max,
                        value=(time_min, time_max),
                        step=0.1,
                    )
                else:
                    time_range = None

            with col2:
                # Filtro de RPM
                if "rpm" in df.columns and not df["rpm"].empty:
                    rpm_min, rpm_max = int(df["rpm"].min()), int(df["rpm"].max())
                    rpm_range = st.slider(
                        "RPM",
                        min_value=rpm_min,
                        max_value=rpm_max,
                        value=(rpm_min, rpm_max),
                        step=100,
                    )
                else:
                    rpm_range = None

            with col3:
                # Filtro de TPS
                if "throttle_position" in df.columns and not df["throttle_position"].isnull().all():
                    tps_min = (
                        float(df["throttle_position"].min())
                        if not df["throttle_position"].isnull().all()
                        else 0.0
                    )
                    tps_max = (
                        float(df["throttle_position"].max())
                        if not df["throttle_position"].isnull().all()
                        else 100.0
                    )
                    tps_range = st.slider(
                        "Throttle Position (%)",
                        min_value=tps_min,
                        max_value=tps_max,
                        value=(tps_min, tps_max),
                        step=1.0,
                    )
                else:
                    tps_range = None

            with col4:
                # Filtro de MAP
                if "map" in df.columns and not df["map"].isnull().all():
                    map_min = float(df["map"].min()) if not df["map"].isnull().all() else 0.0
                    map_max = float(df["map"].max()) if not df["map"].isnull().all() else 3.0
                    map_range = st.slider(
                        "MAP (bar)",
                        min_value=map_min,
                        max_value=map_max,
                        value=(map_min, map_max),
                        step=0.1,
                    )
                else:
                    map_range = None

            # Filtros boolean
            col1, col2 = st.columns(2)

            with col1:
                # Filtros de estado
                show_two_step_only = st.checkbox("Apenas com Two-Step ativo")
                show_launch_only = st.checkbox("Apenas Launch Validated")

            with col2:
                # Filtros de marcha
                if "gear" in df.columns and not df["gear"].isnull().all():
                    available_gears = sorted(df["gear"].dropna().unique())
                    selected_gears = st.multiselect(
                        "Marchas:",
                        available_gears,
                        default=available_gears,
                        help="Selecione as marchas para incluir",
                    )
                else:
                    selected_gears = None

        # Aplicar filtros
        filtered_df = df.copy()

        if time_range:
            filtered_df = filtered_df[
                (filtered_df["time"] >= time_range[0]) & (filtered_df["time"] <= time_range[1])
            ]

        if rpm_range:
            filtered_df = filtered_df[
                (filtered_df["rpm"] >= rpm_range[0]) & (filtered_df["rpm"] <= rpm_range[1])
            ]

        if tps_range and "throttle_position" in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df["throttle_position"] >= tps_range[0])
                & (filtered_df["throttle_position"] <= tps_range[1])
            ]

        if map_range and "map" in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df["map"] >= map_range[0]) & (filtered_df["map"] <= map_range[1])
            ]

        if show_two_step_only and "two_step" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["two_step"] == "ON"]

        if show_launch_only and "launch_validated" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["launch_validated"] == "ON"]

        if selected_gears and "gear" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["gear"].isin(selected_gears)]

        # Mostrar estatísticas do filtro
        if len(filtered_df) != len(df):
            st.info(
                f"Filtro aplicado: {len(filtered_df):,} de {len(df):,} registros ({len(filtered_df)/len(df)*100:.1f}%)"
            )

        return filtered_df

    def render_data_table(self, df: pd.DataFrame) -> None:
        """Renderizar tabela interativa dos dados."""
        st.markdown("### Tabela de Dados")

        # Configurações da tabela
        with st.expander("Configurações da Tabela"):
            col1, col2, col3 = st.columns(3)

            with col1:
                show_all_columns = st.checkbox("Mostrar todas as colunas", value=False)

            with col2:
                max_rows = st.selectbox("Linhas por página:", [100, 500, 1000, 5000], index=0)

            with col3:
                decimal_places = st.selectbox("Casas decimais:", [1, 2, 3], index=1)

        # Selecionar colunas para exibição
        if show_all_columns:
            display_columns = df.columns.tolist()
        else:
            # Colunas essenciais
            essential_columns = [
                "time",
                "rpm",
                "throttle_position",
                "map",
                "o2_general",
                "engine_temp",
                "ignition_timing",
                "fuel_pressure",
                "battery_voltage",
            ]
            display_columns = [col for col in essential_columns if col in df.columns]

        # Preparar dados para exibição
        display_df = df[display_columns].head(max_rows).copy()

        # Formatar números
        numeric_columns = display_df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            display_df[col] = display_df[col].round(decimal_places)

        # Exibir tabela
        st.dataframe(display_df, width='stretch', hide_index=True, height=400)

        # Estatísticas básicas
        if st.checkbox("Mostrar estatísticas descritivas"):
            st.markdown("#### Estatísticas Descritivas")

            stats_df = display_df.describe()
            st.dataframe(stats_df, width='stretch')

    def render_interactive_charts(self, df: pd.DataFrame) -> None:
        """Renderizar gráficos interativos."""
        st.markdown("### Visualizações Interativas")

        # Seletor de tipo de gráfico
        chart_tabs = st.tabs(
            [
                "Séries Temporais",
                "Correlações",
                "Distribuições",
                "Scatter Plots",
                "Comparações",
            ]
        )

        with chart_tabs[0]:
            self.render_time_series_charts(df)

        with chart_tabs[1]:
            self.render_correlation_analysis(df)

        with chart_tabs[2]:
            self.render_distribution_charts(df)

        with chart_tabs[3]:
            self.render_scatter_analysis(df)

        with chart_tabs[4]:
            self.render_comparison_charts(df)

    def render_time_series_charts(self, df: pd.DataFrame) -> None:
        """Renderizar gráficos de séries temporais."""
        if "time" not in df.columns:
            st.warning("Campo 'time' não encontrado nos dados")
            return

        # Seletor de variáveis
        col1, col2 = st.columns(2)

        with col1:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            numeric_columns = [col for col in numeric_columns if col != "time"]

            primary_vars = st.multiselect(
                "Variáveis Primárias:",
                numeric_columns,
                default=["rpm"] if "rpm" in numeric_columns else numeric_columns[:1],
                help="Variáveis para eixo Y esquerdo",
            )

        with col2:
            secondary_vars = st.multiselect(
                "Variáveis Secundárias:",
                numeric_columns,
                default=(["throttle_position"] if "throttle_position" in numeric_columns else []),
                help="Variáveis para eixo Y direito",
            )

        if primary_vars or secondary_vars:
            # Criar subplot com eixo Y duplo
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Cores para as linhas
            colors = px.colors.qualitative.Set1
            color_idx = 0

            # Adicionar variáveis primárias
            for var in primary_vars:
                if var in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df["time"],
                            y=df[var],
                            name=var,
                            line=dict(color=colors[color_idx % len(colors)]),
                            yaxis="y",
                        ),
                        secondary_y=False,
                    )
                    color_idx += 1

            # Adicionar variáveis secundárias
            for var in secondary_vars:
                if var in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df["time"],
                            y=df[var],
                            name=f"{var} (2º eixo)",
                            line=dict(color=colors[color_idx % len(colors)], dash="dash"),
                            yaxis="y2",
                        ),
                        secondary_y=True,
                    )
                    color_idx += 1

            # Configurar layout
            fig.update_layout(
                title="Séries Temporais",
                xaxis_title="Tempo (s)",
                height=500,
                hovermode="x unified",
            )

            fig.update_yaxes(title_text="Primário", secondary_y=False)
            fig.update_yaxes(title_text="Secundário", secondary_y=True)

            st.plotly_chart(fig, width='stretch')

    def render_correlation_analysis(self, df: pd.DataFrame) -> None:
        """Renderizar análise de correlação."""
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if len(numeric_columns) < 2:
            st.warning("Dados insuficientes para análise de correlação")
            return

        # Calcular matriz de correlação
        correlation_matrix = df[numeric_columns].corr()

        # Heatmap de correlação
        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            title="Matriz de Correlação",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
        )

        fig.update_layout(height=600)
        st.plotly_chart(fig, width='stretch')

        # Top correlações
        st.markdown("#### Correlações Mais Fortes")

        # Extrair pares de correlação
        correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                var1 = correlation_matrix.columns[i]
                var2 = correlation_matrix.columns[j]
                corr_value = correlation_matrix.iloc[i, j]
                correlations.append((var1, var2, corr_value))

        # Ordenar por valor absoluto
        correlations.sort(key=lambda x: abs(x[2]), reverse=True)

        # Mostrar top 10
        top_correlations = correlations[:10]

        for var1, var2, corr_value in top_correlations:
            col1, col2 = st.columns([3, 1])

            with col1:
                strength = (
                    "Forte"
                    if abs(corr_value) > 0.7
                    else "Moderada" if abs(corr_value) > 0.5 else "Fraca"
                )
                direction = "Positiva" if corr_value > 0 else "Negativa"
                st.write(f"**{var1}** ↔ **{var2}**: {strength}, {direction}")

            with col2:
                st.metric("Correlação", f"{corr_value:.3f}")

    def render_distribution_charts(self, df: pd.DataFrame) -> None:
        """Renderizar gráficos de distribuição."""
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_columns:
            st.warning("Nenhuma coluna numérica encontrada")
            return

        # Seletor de variável
        selected_var = st.selectbox("Selecione uma variável:", numeric_columns)

        if selected_var and selected_var in df.columns:
            col1, col2 = st.columns(2)

            with col1:
                # Histograma
                fig = px.histogram(
                    df,
                    x=selected_var,
                    nbins=50,
                    title=f"Histograma - {selected_var}",
                    marginal="box",
                )
                st.plotly_chart(fig, width='stretch')

            with col2:
                # Box plot
                fig = px.box(df, y=selected_var, title=f"Box Plot - {selected_var}")
                st.plotly_chart(fig, width='stretch')

            # Estatísticas da distribuição
            st.markdown(f"#### Estatísticas - {selected_var}")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Média", f"{df[selected_var].mean():.2f}")

            with col2:
                st.metric("Mediana", f"{df[selected_var].median():.2f}")

            with col3:
                st.metric("Desvio Padrão", f"{df[selected_var].std():.2f}")

            with col4:
                st.metric(
                    "Coef. Variação",
                    f"{df[selected_var].std()/df[selected_var].mean()*100:.1f}%",
                )

    def render_scatter_analysis(self, df: pd.DataFrame) -> None:
        """Renderizar análise de scatter plots."""
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if len(numeric_columns) < 2:
            st.warning("Dados insuficientes para scatter plots")
            return

        col1, col2, col3 = st.columns(3)

        with col1:
            x_var = st.selectbox("Eixo X:", numeric_columns, index=0)

        with col2:
            y_var = st.selectbox(
                "Eixo Y:", numeric_columns, index=1 if len(numeric_columns) > 1 else 0
            )

        with col3:
            color_var = st.selectbox(
                "Cor por:",
                ["Nenhum"] + numeric_columns,
                help="Variável para colorir os pontos",
            )

        if x_var and y_var and x_var != y_var:
            # Criar scatter plot
            fig = px.scatter(
                df,
                x=x_var,
                y=y_var,
                color=color_var if color_var != "Nenhum" else None,
                title=f"{y_var} vs {x_var}",
                trendline="ols" if st.checkbox("Linha de tendência") else None,
                opacity=0.6,
            )

            fig.update_layout(height=500)
            st.plotly_chart(fig, width='stretch')

            # Estatísticas da relação
            if st.checkbox("Mostrar estatísticas da relação"):
                correlation = df[x_var].corr(df[y_var])

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Correlação", f"{correlation:.3f}")

                with col2:
                    r_squared = correlation**2
                    st.metric("R²", f"{r_squared:.3f}")

    def render_comparison_charts(self, df: pd.DataFrame) -> None:
        """Renderizar gráficos de comparação."""
        st.markdown("Selecione diferentes condições para comparar:")

        # Opções de agrupamento
        grouping_options = []

        # Campos boolean/categóricos
        for col in df.columns:
            if df[col].dtype == "object" or df[col].nunique() <= 10:
                if not df[col].isnull().all():
                    grouping_options.append(col)

        if not grouping_options:
            st.warning("Nenhum campo categórico encontrado para agrupamento")
            return

        col1, col2 = st.columns(2)

        with col1:
            group_by = st.selectbox("Agrupar por:", grouping_options)

        with col2:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            analyze_var = st.selectbox("Variável para análise:", numeric_columns)

        if group_by and analyze_var:
            # Box plot comparativo
            fig = px.box(df, x=group_by, y=analyze_var, title=f"{analyze_var} por {group_by}")

            st.plotly_chart(fig, width='stretch')

            # Estatísticas por grupo
            grouped_stats = df.groupby(group_by)[analyze_var].agg(
                ["count", "mean", "std", "min", "max"]
            )

            st.markdown("#### Estatísticas por Grupo")
            st.dataframe(grouped_stats, width='stretch')

    def render_export_section(self, df: pd.DataFrame) -> None:
        """Renderizar seção de export."""
        st.markdown("### Export de Dados")

        with st.expander("Opções de Export", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                export_format = st.selectbox("Formato:", ["CSV", "Excel", "JSON"])
                include_index = st.checkbox("Incluir índice", value=False)

            with col2:
                filename = st.text_input("Nome do arquivo:", value="fueltech_analysis")
                compression = st.selectbox("Compressão:", ["Nenhuma", "ZIP", "GZIP"])

            # Botão de export
            if st.button("Download Dados Filtrados"):
                try:
                    if export_format == "CSV":
                        csv_data = df.to_csv(index=include_index)
                        st.download_button(
                            label="Download CSV",
                            data=csv_data,
                            file_name=f"{filename}.csv",
                            mime="text/csv",
                        )

                    elif export_format == "Excel":
                        # Para Excel, precisaríamos usar io.BytesIO
                        st.info("Export Excel será implementado em breve")

                    elif export_format == "JSON":
                        json_data = df.to_json(orient="records", indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_data,
                            file_name=f"{filename}.json",
                            mime="application/json",
                        )

                except Exception as e:
                    st.error(f"Erro no export: {str(e)}")


def render_analysis_page() -> None:
    """
    Renderizar página de análise de dados.

    Esta é a função principal que deve ser chamada para exibir a página de análise.
    """
    st.set_page_config(
        page_title="Análise de Dados - FuelTune Analyzer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Título da página
    st.title("FuelTune Analyzer - Análise de Dados")
    st.markdown("Análise interativa e visualização de dados de telemetria")
    st.markdown("---")

    # Inicializar manager
    analysis_manager = DataAnalysisManager()

    # Sidebar para seleção de sessão
    with st.sidebar:
        st.header("Seleção de Sessão")

        selector = SessionSelector(key_prefix="analysis", show_preview=True, show_filters=True)
        selected_session = selector.render_selector()

        if selected_session:
            st.markdown("---")
            st.markdown("### Configurações")

            # Limite de dados para performance
            data_limit = st.selectbox(
                "Limite de dados:",
                [1000, 5000, 10000, 50000, None],
                index=2,
                format_func=lambda x: f"{x:,} registros" if x else "Todos os dados",
                help="Limite para melhor performance",
            )

            # Opções de cache
            if st.button("Limpar Cache"):
                st.cache_data.clear()
                st.success("Cache limpo!")

    # Conteúdo principal
    if selected_session:
        try:
            # Carregar dados
            with st.spinner("Carregando dados da sessão..."):
                df = analysis_manager.load_session_data(selected_session.id, limit=data_limit)

            if df is None or df.empty:
                st.error("Nenhum dado encontrado para esta sessão")
                return

            # Informações básicas da sessão
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Registros", f"{len(df):,}")

            with col2:
                duration = df["time"].max() - df["time"].min() if "time" in df else 0
                st.metric("Duração", f"{duration:.1f}s")

            with col3:
                sample_rate = len(df) / duration if duration > 0 else 0
                st.metric("Taxa Amostragem", f"{sample_rate:.1f} Hz")

            with col4:
                memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024
                st.metric("Memória", f"{memory_usage:.1f} MB")

            st.markdown("---")

            # Aplicar filtros
            filtered_df = analysis_manager.render_data_filters(df)

            st.markdown("---")

            # Tabs principais
            main_tabs = st.tabs(["Tabela de Dados", "Visualizações", "Export"])

            with main_tabs[0]:
                analysis_manager.render_data_table(filtered_df)

            with main_tabs[1]:
                analysis_manager.render_interactive_charts(filtered_df)

            with main_tabs[2]:
                analysis_manager.render_export_section(filtered_df)

        except Exception as e:
            logger.error(f"Erro na análise: {str(e)}")
            st.error(f"Erro ao processar dados: {str(e)}")

            if st.session_state.get("debug_mode", False):
                st.exception(e)

    else:
        # Instruções quando nenhuma sessão está selecionada
        st.info(
            """
        **Selecione uma sessão de dados na barra lateral para começar a análise.**

        ### Recursos Disponíveis:
        - **Tabela Interativa**: Visualize e filtre dados tabulares
        - **Gráficos Dinâmicos**: Séries temporais, correlações, distribuições
        - **Filtros Avançados**: Filtre por tempo, RPM, throttle, MAP e mais
        - **Export de Dados**: Baixe dados filtrados em CSV, Excel ou JSON
        - **Análise Estatística**: Correlações, distribuições e comparações

        ### Dica:
        Use os filtros para focar em partes específicas dos dados, como:
        - Condições de alta carga (TPS > 80%)
        - Faixas específicas de RPM
        - Momentos com two-step ativo
        - Análise por marcha
        """
        )


if __name__ == "__main__":
    # Executar página de análise diretamente
    render_analysis_page()
