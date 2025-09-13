"""
Consumption Analysis Page - FuelTune Analyzer.

Página especializada em análise de consumo de combustível,
incluindo consumo instantâneo, médio, autonomia estimada
e comparações de economia.

Features:
- Análise de consumo instantâneo e médio
- Cálculos de autonomia e alcance
- Gráficos de eficiência em diferentes condições
- Comparação de economia por marcha/RPM
- Análise de fluxo de combustível
- Métricas de eficiência volumétrica

Author: A03-UI-STREAMLIT Agent
Created: 2025-01-02
"""

from typing import Dict, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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
    from src.ui.components.metric_card import MetricCard
    from src.ui.components.session_selector import SessionSelector
    from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def _ols_trendline_if_available(enable: bool = True, warn_key: str = "consumption_trend_warn"):
    """Retorna 'ols' se statsmodels estiver disponível e enable=True; caso contrário, None.
    Mostra um aviso uma única vez se não estiver disponível.
    """
    if not enable:
        return None
    try:
        import statsmodels.api  # type: ignore  # noqa: F401

        return "ols"
    except Exception:
        if not st.session_state.get(warn_key):
            st.info("Linha de tendência desativada: pacote 'statsmodels' não está instalado.")
            st.session_state[warn_key] = True
        return None


class ConsumptionAnalysisManager:
    """
    Gerenciador de análise de consumo.

    Responsável por:
    - Cálculos de consumo instantâneo e médio
    - Estimativas de autonomia e alcance
    - Análise de eficiência volumétrica
    - Comparações por condições operacionais
    - Visualizações especializadas em consumo
    """

    def __init__(self):
        self.db = get_database()
        self.metric_card = MetricCard()

        # Constantes para cálculos
        self.GASOLINE_DENSITY = 0.75  # kg/L
        self.GASOLINE_ENERGY_CONTENT = 44.5  # MJ/kg
        self.ETHANOL_DENSITY = 0.789  # kg/L
        self.ETHANOL_ENERGY_CONTENT = 29.7  # MJ/kg

    @st.cache_data(ttl=300)
    def load_consumption_data(_self, session_id: str) -> Optional[pd.DataFrame]:
        """
        Carregar dados de consumo da sessão.

        Args:
            session_id: ID da sessão

        Returns:
            DataFrame com dados de consumo ou None
        """
        try:
            _self.db.initialize_database()
            with _self.db.get_session() as db_session:
                # Buscar dados core
                core_query = (
                    db_session.query(FuelTechCoreData)
                    .filter(FuelTechCoreData.session_id == session_id)
                    .order_by(FuelTechCoreData.time)
                )

                core_data = core_query.all()

                # Extended data unificado na tabela core
                # Session is automatically closed by context manager

            if not core_data:
                return None

            # Converter dados core para DataFrame
            data_list = []
            for record in core_data:
                data_list.append(
                    {
                        "time": record.time,
                        "rpm": record.rpm,
                        "throttle_position": record.throttle_position,
                        "map": record.map,
                        "flow_bank_a": record.flow_bank_a,
                        "injection_time_a": record.injection_time_a,
                        "injector_duty_a": record.injector_duty_a,
                        "fuel_pressure": record.fuel_pressure,
                        "engine_temp": record.engine_temp,
                        "air_temp": record.air_temp,
                        "ethanol_content": record.ethanol_content,
                        "gear": record.gear,
                        "o2_general": record.o2_general,
                    }
                )

            df = pd.DataFrame(data_list)

            # Os campos estendidos já estão na tabela core após unificação
            for col in [
                "total_consumption",
                "average_consumption",
                "instant_consumption",
                "total_distance",
                "range",
                "traction_speed",
            ]:
                if hasattr(core_data[0], col):
                    df[col] = [getattr(r, col, None) for r in core_data]

            return df

        except Exception as e:
            logger.error(f"Erro ao carregar dados de consumo: {str(e)}")
            return None

    def calculate_consumption_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcular métricas de consumo.

        Args:
            df: DataFrame com dados

        Returns:
            Dicionário com métricas calculadas
        """
        metrics = {}

        if df.empty:
            return metrics

        try:
            # Métricas básicas de fluxo
            if "flow_bank_a" in df.columns and not df["flow_bank_a"].isnull().all():
                flow_data = df["flow_bank_a"].dropna()
                metrics["avg_flow_rate"] = flow_data.mean()
                metrics["max_flow_rate"] = flow_data.max()
                metrics["min_flow_rate"] = flow_data.min()

            # Métricas de tempo de injeção
            if "injection_time_a" in df.columns and not df["injection_time_a"].isnull().all():
                inj_data = df["injection_time_a"].dropna()
                metrics["avg_injection_time"] = inj_data.mean()
                metrics["max_injection_time"] = inj_data.max()

            # Duty cycle dos injetores
            if "injector_duty_a" in df.columns and not df["injector_duty_a"].isnull().all():
                duty_data = df["injector_duty_a"].dropna()
                metrics["avg_injector_duty"] = duty_data.mean()
                metrics["max_injector_duty"] = duty_data.max()

            # Consumo estimado baseado em flow_bank_a
            if "flow_bank_a" in df.columns and "time" in df.columns:
                flow_data = df.dropna(subset=["flow_bank_a", "time"])
                if not flow_data.empty:
                    # Calcular consumo total estimado (L/h -> L)
                    duration_hours = (flow_data["time"].max() - flow_data["time"].min()) / 3600
                    if duration_hours > 0:
                        total_consumption_est = flow_data["flow_bank_a"].mean() * duration_hours
                        metrics["estimated_total_consumption"] = total_consumption_est
                        metrics["session_duration_hours"] = duration_hours

            # Eficiência volumétrica estimada
            if (
                all(col in df.columns for col in ["rpm", "map", "flow_bank_a"])
                and not df[["rpm", "map", "flow_bank_a"]].isnull().all().any()
            ):
                valid_data = df.dropna(subset=["rpm", "map", "flow_bank_a"])
                if not valid_data.empty:
                    # Cálculo simplificado de eficiência volumétrica
                    # Baseado na relação entre flow real e teórico
                    theoretical_flow = valid_data["rpm"] * valid_data["map"] * 0.001
                    actual_flow = valid_data["flow_bank_a"]
                    volumetric_efficiency = (actual_flow / theoretical_flow * 100).mean()
                    metrics["avg_volumetric_efficiency"] = volumetric_efficiency

            # Análise por faixa de RPM
            if "rpm" in df.columns and "flow_bank_a" in df.columns:
                rpm_ranges = {
                    "idle": (0, 1500),
                    "low": (1500, 3000),
                    "mid": (3000, 5000),
                    "high": (5000, 8000),
                }

                for range_name, (rpm_min, rpm_max) in rpm_ranges.items():
                    range_data = df[(df["rpm"] >= rpm_min) & (df["rpm"] < rpm_max)]
                    if not range_data.empty and "flow_bank_a" in range_data.columns:
                        avg_flow = range_data["flow_bank_a"].mean()
                        metrics[f"avg_flow_{range_name}"] = avg_flow

        except Exception as e:
            logger.error(f"Erro no cálculo de métricas: {str(e)}")

        return metrics

    def render_consumption_overview(self, df: pd.DataFrame) -> None:
        """Renderizar overview de consumo."""
        st.markdown("### Overview de Consumo")

        metrics = self.calculate_consumption_metrics(df)

        if not metrics:
            st.warning("Dados insuficientes para calcular métricas de consumo")
            return

        # Cards de métricas principais
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            avg_flow = metrics.get("avg_flow_rate", 0)
            st.metric(
                "Fluxo Médio",
                f"{avg_flow:.1f}",
                help="Fluxo médio de combustível (L/h)",
            )

        with col2:
            max_flow = metrics.get("max_flow_rate", 0)
            st.metric(
                "Fluxo Máximo",
                f"{max_flow:.1f}",
                help="Pico de fluxo de combustível (L/h)",
            )

        with col3:
            avg_duty = metrics.get("avg_injector_duty", 0)
            st.metric(
                "Duty Cycle Médio",
                f"{avg_duty:.1f}%",
                help="Duty cycle médio dos injetores",
            )

        with col4:
            total_consumption = metrics.get("estimated_total_consumption", 0)
            st.metric(
                "Consumo Estimado",
                f"{total_consumption:.2f} L",
                help="Consumo total estimado na sessão",
            )

        # Métricas adicionais
        if metrics.get("avg_volumetric_efficiency"):
            col1, col2 = st.columns(2)

            with col1:
                vol_eff = metrics["avg_volumetric_efficiency"]
                st.metric(
                    "Eficiência Volumétrica",
                    f"{vol_eff:.1f}%",
                    help="Eficiência volumétrica estimada",
                )

            with col2:
                duration = metrics.get("session_duration_hours", 0)
                st.metric(
                    "Duração da Sessão",
                    f"{duration:.2f} h",
                    help="Duração total da sessão",
                )

    def render_consumption_charts(self, df: pd.DataFrame) -> None:
        """Renderizar gráficos de consumo."""
        st.markdown("### Gráficos de Consumo")

        if df.empty:
            st.warning("Nenhum dado disponível")
            return

        # Tabs para diferentes análises
        chart_tabs = st.tabs(
            [
                "Fluxo vs Tempo",
                "Duty Cycle",
                "Consumo por RPM",
                "Eficiência",
                "Performance",
            ]
        )

        with chart_tabs[0]:
            self.render_flow_vs_time(df)

        with chart_tabs[1]:
            self.render_duty_cycle_analysis(df)

        with chart_tabs[2]:
            self.render_consumption_by_rpm(df)

        with chart_tabs[3]:
            self.render_efficiency_analysis(df)

        with chart_tabs[4]:
            self.render_performance_consumption(df)

    def render_flow_vs_time(self, df: pd.DataFrame) -> None:
        """Renderizar gráfico de fluxo vs tempo."""
        if "time" not in df.columns or "flow_bank_a" not in df.columns:
            st.warning("Dados de fluxo ou tempo não disponíveis")
            return

        # Filtrar dados válidos
        valid_data = df.dropna(subset=["time", "flow_bank_a"])

        if valid_data.empty:
            st.warning("Nenhum dado válido de fluxo encontrado")
            return

        # Criar gráfico principal
        fig = go.Figure()

        # Linha de fluxo
        fig.add_trace(
            go.Scatter(
                x=valid_data["time"],
                y=valid_data["flow_bank_a"],
                mode="lines",
                name="Fluxo de Combustível",
                line=dict(color="blue", width=2),
                hovertemplate="Tempo: %{x:.1f}s<br>Fluxo: %{y:.1f} L/h<extra></extra>",
            )
        )

        # Adicionar linha de média
        avg_flow = valid_data["flow_bank_a"].mean()
        fig.add_hline(
            y=avg_flow,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Média: {avg_flow:.1f} L/h",
            annotation_position="top right",
        )

        # Layout
        fig.update_layout(
            title="Fluxo de Combustível vs Tempo",
            xaxis_title="Tempo (s)",
            yaxis_title="Fluxo (L/h)",
            height=400,
            showlegend=True,
        )

        st.plotly_chart(fig, width="stretch")

        # Adicionar gráfico de throttle para correlação
        if "throttle_position" in df.columns:
            col1, col2 = st.columns(2)

            with col1:
                # Correlation scatter
                correlation_data = df.dropna(subset=["throttle_position", "flow_bank_a"])
                if not correlation_data.empty:
                    fig_corr = px.scatter(
                        correlation_data,
                        x="throttle_position",
                        y="flow_bank_a",
                        title="Fluxo vs Throttle Position",
                        labels={
                            "throttle_position": "TPS (%)",
                            "flow_bank_a": "Fluxo (L/h)",
                        },
                        trendline=_ols_trendline_if_available(
                            True, warn_key="consumption_trend_corr"
                        ),
                    )
                    st.plotly_chart(fig_corr, width="stretch")

            with col2:
                # Estatísticas da correlação
                if not correlation_data.empty:
                    correlation = correlation_data["throttle_position"].corr(
                        correlation_data["flow_bank_a"]
                    )
                    st.metric("Correlação TPS-Fluxo", f"{correlation:.3f}")

                    # Análise por faixas de throttle
                    throttle_ranges = {
                        "Baixo (0-30%)": (0, 30),
                        "Médio (30-70%)": (30, 70),
                        "Alto (70-100%)": (70, 100),
                    }

                    st.markdown("**Consumo por Faixa de TPS:**")
                    for range_name, (tps_min, tps_max) in throttle_ranges.items():
                        range_data = correlation_data[
                            (correlation_data["throttle_position"] >= tps_min)
                            & (correlation_data["throttle_position"] <= tps_max)
                        ]
                        if not range_data.empty:
                            avg_flow_range = range_data["flow_bank_a"].mean()
                            st.write(f"- {range_name}: {avg_flow_range:.1f} L/h")

    def render_duty_cycle_analysis(self, df: pd.DataFrame) -> None:
        """Renderizar análise de duty cycle."""
        if "injector_duty_a" not in df.columns:
            st.warning("Dados de duty cycle não disponíveis")
            return

        valid_data = df.dropna(subset=["injector_duty_a"])

        if valid_data.empty:
            st.warning("Nenhum dado válido de duty cycle")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Histograma de duty cycle
            fig_hist = px.histogram(
                valid_data,
                x="injector_duty_a",
                nbins=30,
                title="Distribuição do Duty Cycle",
                labels={"injector_duty_a": "Duty Cycle (%)"},
                marginal="box",
            )
            st.plotly_chart(fig_hist, width="stretch")

        with col2:
            # Duty cycle vs RPM
            if "rpm" in df.columns:
                rpm_duty_data = df.dropna(subset=["rpm", "injector_duty_a"])
                if not rpm_duty_data.empty:
                    fig_rpm = px.scatter(
                        rpm_duty_data,
                        x="rpm",
                        y="injector_duty_a",
                        title="Duty Cycle vs RPM",
                        labels={"rpm": "RPM", "injector_duty_a": "Duty Cycle (%)"},
                        opacity=0.6,
                    )
                    st.plotly_chart(fig_rpm, width="stretch")

        # Análise de zones de duty cycle
        st.markdown("#### Análise por Zonas")

        duty_zones = {
            "Baixo (0-30%)": (0, 30),
            "Médio (30-60%)": (30, 60),
            "Alto (60-80%)": (60, 80),
            "Crítico (>80%)": (80, 100),
        }

        zone_stats = []
        total_points = len(valid_data)

        for zone_name, (duty_min, duty_max) in duty_zones.items():
            zone_data = valid_data[
                (valid_data["injector_duty_a"] >= duty_min)
                & (valid_data["injector_duty_a"] <= duty_max)
            ]

            count = len(zone_data)
            percentage = (count / total_points * 100) if total_points > 0 else 0

            zone_stats.append(
                {"Zona": zone_name, "Pontos": count, "Percentual": f"{percentage:.1f}%"}
            )

        zone_df = pd.DataFrame(zone_stats)
        st.dataframe(zone_df, width="stretch", hide_index=True)

        # Alerta para duty cycle alto
        max_duty = valid_data["injector_duty_a"].max()
        if max_duty > 80:
            st.warning(
                f"Duty cycle máximo de {max_duty:.1f}% detectado - possível limitação dos injetores"
            )

    def render_consumption_by_rpm(self, df: pd.DataFrame) -> None:
        """Renderizar análise de consumo por RPM."""
        if "rpm" not in df.columns or "flow_bank_a" not in df.columns:
            st.warning("Dados de RPM ou fluxo não disponíveis")
            return

        valid_data = df.dropna(subset=["rpm", "flow_bank_a"])

        if valid_data.empty:
            st.warning("Nenhum dado válido para análise RPM vs consumo")
            return

        # Criar bins de RPM
        rpm_bins = pd.cut(valid_data["rpm"], bins=10, precision=0)
        consumption_by_rpm = (
            valid_data.groupby(rpm_bins)["flow_bank_a"].agg(["mean", "std", "count"]).reset_index()
        )

        # Converter intervalo para string
        consumption_by_rpm["rpm_range"] = consumption_by_rpm["rpm"].astype(str)
        consumption_by_rpm["rpm_center"] = consumption_by_rpm["rpm"].apply(lambda x: x.mid)

        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de consumo médio por faixa de RPM
            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=consumption_by_rpm["rpm_range"],
                    y=consumption_by_rpm["mean"],
                    error_y=dict(type="data", array=consumption_by_rpm["std"]),
                    name="Consumo Médio",
                    marker_color="blue",
                )
            )

            fig.update_layout(
                title="Consumo Médio por Faixa de RPM",
                xaxis_title="Faixa de RPM",
                yaxis_title="Fluxo Médio (L/h)",
                height=400,
            )

            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, width="stretch")

        with col2:
            # Scatter plot com linha de tendência
            fig_scatter = px.scatter(
                valid_data.sample(min(1000, len(valid_data))),  # Sample para performance
                x="rpm",
                y="flow_bank_a",
                title="Consumo vs RPM (Scatter)",
                labels={"rpm": "RPM", "flow_bank_a": "Fluxo (L/h)"},
                trendline=_ols_trendline_if_available(True, warn_key="consumption_trend_rpm"),
                opacity=0.6,
            )
            st.plotly_chart(fig_scatter, width="stretch")

        # Análise estatística
        st.markdown("#### Estatísticas por Faixa de RPM")

        rpm_ranges = {
            "Marcha Lenta": (0, 1500),
            "Baixo RPM": (1500, 3000),
            "Médio RPM": (3000, 5000),
            "Alto RPM": (5000, 7000),
            "RPM Extremo": (7000, 15000),
        }

        range_analysis = []
        for range_name, (rpm_min, rpm_max) in rpm_ranges.items():
            range_data = valid_data[(valid_data["rpm"] >= rpm_min) & (valid_data["rpm"] <= rpm_max)]

            if not range_data.empty:
                range_analysis.append(
                    {
                        "Faixa": range_name,
                        "Pontos": len(range_data),
                        "Consumo Médio (L/h)": f"{range_data['flow_bank_a'].mean():.1f}",
                        "Consumo Máximo (L/h)": f"{range_data['flow_bank_a'].max():.1f}",
                        "Desvio Padrão": f"{range_data['flow_bank_a'].std():.1f}",
                    }
                )

        if range_analysis:
            analysis_df = pd.DataFrame(range_analysis)
            st.dataframe(analysis_df, width="stretch", hide_index=True)

    def render_efficiency_analysis(self, df: pd.DataFrame) -> None:
        """Renderizar análise de eficiência."""
        st.markdown("Análise de eficiência baseada em parâmetros disponíveis")

        if df.empty:
            st.warning("Nenhum dado disponível")
            return

        # Calcular métricas de eficiência
        efficiency_data = df.copy()

        # Eficiência de combustível (simplificada)
        if all(col in df.columns for col in ["flow_bank_a", "rpm", "map"]):
            valid_data = efficiency_data.dropna(subset=["flow_bank_a", "rpm", "map"])

            if not valid_data.empty:
                # BSFC estimado (Brake Specific Fuel Consumption)
                # Fórmula simplificada baseada em fluxo, RPM e carga (MAP)
                power_estimate = (valid_data["rpm"] * valid_data["map"]) / 1000
                bsfc_estimate = valid_data["flow_bank_a"] / power_estimate.replace(0, np.nan)

                efficiency_data.loc[valid_data.index, "bsfc_estimate"] = bsfc_estimate
                efficiency_data.loc[valid_data.index, "power_estimate"] = power_estimate

        # Análise de Lambda (AFR)
        if "o2_general" in df.columns:
            lambda_data = efficiency_data.dropna(subset=["o2_general"])

            if not lambda_data.empty:
                # Calcular AFR assumindo gasolina (stoich = 14.7)
                afr = lambda_data["o2_general"] * 14.7
                efficiency_data.loc[lambda_data.index, "afr"] = afr

        # Gráficos de eficiência
        col1, col2 = st.columns(2)

        with col1:
            if "bsfc_estimate" in efficiency_data.columns:
                bsfc_valid = efficiency_data.dropna(subset=["bsfc_estimate"])
                if not bsfc_valid.empty:
                    fig_bsfc = px.histogram(
                        bsfc_valid,
                        x="bsfc_estimate",
                        nbins=30,
                        title="Distribuição BSFC Estimado",
                        labels={"bsfc_estimate": "BSFC (L/h/kW)"},
                    )
                    st.plotly_chart(fig_bsfc, width="stretch")

        with col2:
            if "afr" in efficiency_data.columns:
                afr_valid = efficiency_data.dropna(subset=["afr"])
                if not afr_valid.empty:
                    fig_afr = px.histogram(
                        afr_valid,
                        x="afr",
                        nbins=30,
                        title="Distribuição AFR",
                        labels={"afr": "Air-Fuel Ratio"},
                    )

                    # Adicionar linha stoichiometric
                    fig_afr.add_vline(
                        x=14.7,
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Stoichiometric (14.7)",
                    )

                    st.plotly_chart(fig_afr, width="stretch")

        # Métricas de eficiência
        if "bsfc_estimate" in efficiency_data.columns or "afr" in efficiency_data.columns:
            st.markdown("#### Métricas de Eficiência")

            col1, col2, col3 = st.columns(3)

            with col1:
                if "bsfc_estimate" in efficiency_data.columns:
                    bsfc_avg = efficiency_data["bsfc_estimate"].mean()
                    st.metric("BSFC Médio", f"{bsfc_avg:.2f} L/h/kW")

            with col2:
                if "afr" in efficiency_data.columns:
                    afr_avg = efficiency_data["afr"].mean()
                    st.metric("AFR Médio", f"{afr_avg:.1f}")

            with col3:
                if "o2_general" in efficiency_data.columns:
                    lambda_avg = efficiency_data["o2_general"].mean()
                    st.metric("Lambda Médio", f"{lambda_avg:.3f}")

    def render_performance_consumption(self, df: pd.DataFrame) -> None:
        """Renderizar análise de consumo vs performance."""
        st.markdown("Relação entre consumo e parâmetros de performance")

        if df.empty:
            st.warning("Nenhum dado disponível")
            return

        # Análise de consumo vs carga
        if all(col in df.columns for col in ["flow_bank_a", "throttle_position", "map"]):
            valid_data = df.dropna(subset=["flow_bank_a", "throttle_position", "map"])

            if not valid_data.empty:
                # Criar índice de carga combinado
                load_index = (valid_data["throttle_position"] * valid_data["map"]) / 100
                consumption_vs_load = pd.DataFrame(
                    {"load_index": load_index, "consumption": valid_data["flow_bank_a"]}
                )

                col1, col2 = st.columns(2)

                with col1:
                    # Scatter plot consumo vs carga
                    fig_load = px.scatter(
                        consumption_vs_load.sample(min(1000, len(consumption_vs_load))),
                        x="load_index",
                        y="consumption",
                        title="Consumo vs Índice de Carga",
                        labels={
                            "load_index": "Índice de Carga (TPS × MAP / 100)",
                            "consumption": "Consumo (L/h)",
                        },
                        trendline=_ols_trendline_if_available(
                            True, warn_key="consumption_trend_load"
                        ),
                        opacity=0.6,
                    )
                    st.plotly_chart(fig_load, width="stretch")

                with col2:
                    # Análise por faixas de carga
                    load_ranges = {
                        "Baixa Carga": (0, 1),
                        "Carga Média": (1, 2),
                        "Alta Carga": (2, 4),
                        "Carga Extrema": (4, 10),
                    }

                    load_analysis = []
                    for range_name, (load_min, load_max) in load_ranges.items():
                        range_data = consumption_vs_load[
                            (consumption_vs_load["load_index"] >= load_min)
                            & (consumption_vs_load["load_index"] <= load_max)
                        ]

                        if not range_data.empty:
                            load_analysis.append(
                                {
                                    "Faixa": range_name,
                                    "Pontos": len(range_data),
                                    "Consumo Médio": f"{range_data['consumption'].mean():.1f} L/h",
                                    "Consumo Máximo": f"{range_data['consumption'].max():.1f} L/h",
                                }
                            )

                    if load_analysis:
                        load_df = pd.DataFrame(load_analysis)
                        st.dataframe(load_df, width="stretch", hide_index=True)

        # Análise por marcha
        if "gear" in df.columns and "flow_bank_a" in df.columns:
            gear_data = df.dropna(subset=["gear", "flow_bank_a"])

            if not gear_data.empty:
                st.markdown("#### Consumo por Marcha")

                gear_consumption = (
                    gear_data.groupby("gear")["flow_bank_a"]
                    .agg(["mean", "std", "count"])
                    .reset_index()
                )

                fig_gear = px.bar(
                    gear_consumption,
                    x="gear",
                    y="mean",
                    error_y="std",
                    title="Consumo Médio por Marcha",
                    labels={"gear": "Marcha", "mean": "Consumo Médio (L/h)"},
                )

                st.plotly_chart(fig_gear, width="stretch")


def render_consumption_page() -> None:
    """
    Renderizar página de análise de consumo.

    Esta é a função principal que deve ser chamada para exibir a página de consumo.
    """
    st.set_page_config(
        page_title="Análise de Consumo - FuelTune Analyzer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Título da página
    st.title("FuelTune Analyzer - Análise de Consumo")
    st.markdown("Análise detalhada de consumo de combustível e eficiência")
    st.markdown("---")

    # Inicializar manager
    consumption_manager = ConsumptionAnalysisManager()

    # Sidebar para seleção de sessão
    with st.sidebar:
        st.header("Análise de Consumo")

        selector = SessionSelector(key_prefix="consumption", show_preview=True, show_filters=False)
        selected_session = selector.render_selector()

        if selected_session:
            st.markdown("---")
            st.markdown("### Configurações")

            # Tipo de combustível para cálculos
            fuel_type = st.selectbox(
                "Tipo de Combustível:",
                ["Gasolina", "Etanol", "E85", "Flex"],
                help="Tipo de combustível para cálculos de eficiência",
            )

            # Parâmetros do motor
            with st.expander("Parâmetros do Motor"):
                engine_displacement = st.number_input(
                    "Cilindrada (L):",
                    min_value=0.5,
                    max_value=10.0,
                    value=2.0,
                    step=0.1,
                )

                num_cylinders = st.number_input(
                    "Número de Cilindros:", min_value=1, max_value=12, value=4
                )

                injector_flow = st.number_input(
                    "Fluxo Injetor (cc/min):", min_value=100, max_value=2000, value=550
                )

    # Conteúdo principal
    if selected_session:
        try:
            # Carregar dados
            with st.spinner("Carregando dados de consumo..."):
                df = consumption_manager.load_consumption_data(selected_session.id)

            if df is None or df.empty:
                st.error("Nenhum dado de consumo encontrado para esta sessão")
                st.info("Certifique-se de que a sessão contém dados de fluxo de combustível")
                return

            # Overview de consumo
            consumption_manager.render_consumption_overview(df)

            st.markdown("---")

            # Gráficos de análise
            consumption_manager.render_consumption_charts(df)

        except Exception as e:
            logger.error(f"Erro na análise de consumo: {str(e)}")
            st.error(f"Erro ao processar dados de consumo: {str(e)}")

            if st.session_state.get("debug_mode", False):
                st.exception(e)

    else:
        # Instruções quando nenhuma sessão está selecionada
        st.info(
            """
        **Selecione uma sessão de dados na barra lateral para análise de consumo.**

        ### Análises Disponíveis:
        - **Fluxo de Combustível**: Análise temporal do consumo
        - **Duty Cycle**: Análise do duty cycle dos injetores
        - **Consumo por RPM**: Consumo em diferentes faixas de rotação
        - **Eficiência**: BSFC, AFR e eficiência volumétrica
        - **Performance**: Relação consumo vs performance

        ### Campos Necessários:
        - **flow_bank_a**: Fluxo de combustível (obrigatório)
        - **injection_time_a**: Tempo de injeção
        - **injector_duty_a**: Duty cycle dos injetores
        - **o2_general**: Sensor lambda para cálculos AFR
        - **rpm, throttle_position, map**: Para análises de eficiência

        ### Dica:
        Configure o tipo de combustível na barra lateral para cálculos mais precisos.
        """
        )


if __name__ == "__main__":
    # Executar página de consumo diretamente
    render_consumption_page()
