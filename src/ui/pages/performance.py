"""
Performance Metrics Page - FuelTune Analyzer.

Página especializada em métricas de performance do motor,
incluindo curvas de potência/torque, análise de aceleração,
boost analysis e comparação com targets.

Features:
- Curvas de potência e torque estimadas
- Análise de aceleração e tempos de resposta
- Boost analysis e controle de pressão
- Comparação com valores target
- Métricas de eficiência volumétrica
- Análise de knock e detonação

Author: A03-UI-STREAMLIT Agent
Created: 2025-01-02
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

try:
    # Tentar importação relativa primeiro (para quando chamado como módulo)
    from ...data.database import FuelTechCoreData, FuelTechExtendedData, get_database
    from ...utils.logging_config import get_logger
    from ..components.metric_card import MetricCard
    from ..components.session_selector import SessionSelector
except ImportError:
    # Fallback para importação absoluta (quando executado via st.navigation)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.data.database import FuelTechCoreData, FuelTechExtendedData, get_database
    from src.utils.logging_config import get_logger
    from src.ui.components.metric_card import MetricCard
    from src.ui.components.session_selector import SessionSelector

logger = get_logger(__name__)


class PerformanceAnalysisManager:
    """
    Gerenciador de análise de performance.

    Responsável por:
    - Cálculo de potência e torque estimados
    - Análise de curvas de performance
    - Métricas de aceleração
    - Análise de boost/pressão
    - Comparação com targets
    - Detecção de knock
    """

    def __init__(self):
        self.db = get_database()
        self.metric_card = MetricCard()

    @st.cache_data(ttl=300)
    def load_performance_data(_self, session_id: str) -> Optional[pd.DataFrame]:
        """Carregar dados de performance da sessão."""
        try:
            _self.db.initialize_database()
            with _self.db.get_session() as db_session:
                # Buscar dados core e extended
                core_query = (
                    db_session.query(FuelTechCoreData)
                    .filter(FuelTechCoreData.session_id == session_id)
                    .order_by(FuelTechCoreData.time)
                )

                extended_query = (
                    db_session.query(FuelTechExtendedData)
                    .filter(FuelTechExtendedData.session_id == session_id)
                    .order_by(FuelTechExtendedData.time)
                )

                core_data = core_query.all()
                extended_data = extended_query.all()
                # Session is automatically closed by context manager

            if not core_data:
                return None

            # Converter core data
            data_list = []
            for record in core_data:
                data_list.append(
                    {
                        "time": record.time,
                        "rpm": record.rpm,
                        "throttle_position": record.throttle_position,
                        "map": record.map,
                        "ignition_timing": record.ignition_timing,
                        "o2_general": record.o2_general,
                        "engine_temp": record.engine_temp,
                        "flow_bank_a": record.flow_bank_a,
                        "injection_time_a": record.injection_time_a,
                        "fuel_pressure": record.fuel_pressure,
                        "ethanol_content": record.ethanol_content,
                    }
                )

            df = pd.DataFrame(data_list)

            # Adicionar dados extended se disponíveis
            if extended_data:
                extended_dict = {}
                for record in extended_data:
                    extended_dict[record.time] = {
                        "estimated_power": record.estimated_power,
                        "estimated_torque": record.estimated_torque,
                        "acceleration_speed": record.acceleration_speed,
                        "traction_speed": record.traction_speed,
                    }

                for col in [
                    "estimated_power",
                    "estimated_torque",
                    "acceleration_speed",
                    "traction_speed",
                ]:
                    df[col] = df["time"].map(lambda t: extended_dict.get(t, {}).get(col))

            # Calcular métricas derivadas
            df = _self.calculate_performance_metrics(df)

            return df

        except Exception as e:
            logger.error(f"Erro ao carregar dados de performance: {str(e)}")
            return None

    def calculate_performance_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular métricas de performance derivadas."""
        if df.empty:
            return df

        try:
            # Estimar potência baseada em RPM, MAP e fluxo
            if all(col in df.columns for col in ["rpm", "map", "flow_bank_a"]):
                # Fórmula simplificada: Power ∝ RPM × MAP × Flow
                power_factor = df["rpm"] * df["map"] * df["flow_bank_a"].fillna(0)
                # Normalizar para HP estimado (fator de conversão empírico)
                df["power_estimate"] = power_factor / 1000

            # Estimar torque: Torque = Power / (RPM * 2π / 60) * 9549
            if "power_estimate" in df.columns and "rpm" in df.columns:
                df["torque_estimate"] = df["power_estimate"] * 9549 / df["rpm"]
                df["torque_estimate"] = df["torque_estimate"].fillna(0)

            # Calcular load factor (carga do motor)
            if "throttle_position" in df.columns and "map" in df.columns:
                df["load_factor"] = (df["throttle_position"].fillna(0) * df["map"].fillna(1)) / 100

            # Calcular boost (MAP - 1 atm)
            if "map" in df.columns:
                df["boost"] = df["map"] - 1.0
                df["boost"] = df["boost"].clip(lower=0)  # Boost não pode ser negativo

            # Estimar BMEP (Brake Mean Effective Pressure)
            if "torque_estimate" in df.columns:
                # BMEP = Torque * 4π / displacement (assumindo 2L)
                displacement = 2.0  # L
                df["bmep"] = df["torque_estimate"] * 4 * np.pi / displacement / 1000  # kPa

            # Calcular eficiência térmica estimada
            if all(col in df.columns for col in ["power_estimate", "flow_bank_a"]):
                # Efficiency = Power / (Flow * Energy_content)
                fuel_energy = 44.5 * 1000 / 3600  # MJ/L -> kJ/s per L/h
                df["thermal_efficiency"] = (
                    (df["power_estimate"] * 0.746)
                    / (df["flow_bank_a"].fillna(1) * fuel_energy)
                    * 100
                )
                df["thermal_efficiency"] = df["thermal_efficiency"].clip(
                    0, 50
                )  # Limitar a valores realistas

            # Detectar knock baseado em timing vs RPM/Load
            if all(col in df.columns for col in ["ignition_timing", "load_factor", "rpm"]):
                # Timing muito retardado para alta carga pode indicar knock
                expected_timing = 35 - df["load_factor"] * 15  # Timing esperado
                timing_retard = expected_timing - df["ignition_timing"].fillna(0)
                df["possible_knock"] = timing_retard > 10  # Mais de 10° de retardo

        except Exception as e:
            logger.error(f"Erro no cálculo de métricas de performance: {str(e)}")

        return df

    def render_performance_overview(self, df: pd.DataFrame) -> None:
        """Renderizar overview de performance."""
        st.markdown("### Overview de Performance")

        if df.empty:
            st.warning("Nenhum dado de performance disponível")
            return

        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if "power_estimate" in df.columns:
                max_power = df["power_estimate"].max()
                avg_power = df["power_estimate"].mean()
                max_cv = max_power * 1.01387
                avg_cv = avg_power * 1.01387
                st.metric(
                    "Potência Máxima",
                    f"{max_cv:.0f} CV",
                    delta=f"Média: {avg_cv:.0f} CV",
                )
            else:
                st.metric("Potência", "N/A")

        with col2:
            if "torque_estimate" in df.columns:
                max_torque = df["torque_estimate"].max()
                avg_torque = df["torque_estimate"].mean()
                st.metric(
                    "Torque Máximo",
                    f"{max_torque:.0f} Nm",
                    delta=f"Média: {avg_torque:.0f} Nm",
                )
            else:
                st.metric("Torque", "N/A")

        with col3:
            if "boost" in df.columns:
                max_boost = df["boost"].max()
                avg_boost = df["boost"].mean()
                st.metric(
                    "Boost Máximo",
                    f"{max_boost:.2f} bar",
                    delta=f"Média: {avg_boost:.2f} bar",
                )
            else:
                st.metric("Boost", "N/A")

        with col4:
            if "thermal_efficiency" in df.columns:
                avg_efficiency = df["thermal_efficiency"].mean()
                max_efficiency = df["thermal_efficiency"].max()
                st.metric(
                    "Eficiência Térmica",
                    f"{avg_efficiency:.1f}%",
                    delta=f"Máx: {max_efficiency:.1f}%",
                )
            else:
                st.metric("Eficiência", "N/A")

        # Alertas de performance
        alerts = self.check_performance_alerts(df)
        if alerts:
            st.markdown("#### Alertas de Performance")
            for alert in alerts:
                if alert["severity"] == "high":
                    st.error(f"{alert['message']}")
                elif alert["severity"] == "medium":
                    st.warning(f"{alert['message']}")
                else:
                    st.info(f"{alert['message']}")

    def check_performance_alerts(self, df: pd.DataFrame) -> List[Dict]:
        """Verificar alertas de performance."""
        alerts = []

        try:
            # Verificar knock
            if "possible_knock" in df.columns:
                knock_events = df["possible_knock"].sum()
                if knock_events > 0:
                    knock_pct = (knock_events / len(df)) * 100
                    alerts.append(
                        {
                            "severity": "high",
                            "message": f"Possível knock detectado em {knock_pct:.1f}% dos pontos",
                        }
                    )

            # Verificar superaquecimento
            if "engine_temp" in df.columns:
                max_temp = df["engine_temp"].max()
                if max_temp > 105:
                    alerts.append(
                        {
                            "severity": "high",
                            "message": f"Temperatura do motor muito alta: {max_temp:.1f}°C",
                        }
                    )

            # Verificar lambda (AFR)
            if "o2_general" in df.columns:
                avg_lambda = df["o2_general"].mean()
                if avg_lambda < 0.75:
                    alerts.append(
                        {
                            "severity": "medium",
                            "message": f"Lambda muito rica: {avg_lambda:.2f} (risco de danos)",
                        }
                    )
                elif avg_lambda > 1.1:
                    alerts.append(
                        {
                            "severity": "medium",
                            "message": f"Lambda muito pobre: {avg_lambda:.2f} (perda de potência)",
                        }
                    )

            # Verificar boost
            if "boost" in df.columns:
                max_boost = df["boost"].max()
                if max_boost > 2.5:
                    alerts.append(
                        {
                            "severity": "medium",
                            "message": f"Boost muito alto: {max_boost:.2f} bar",
                        }
                    )

        except Exception as e:
            logger.error(f"Erro na verificação de alertas: {str(e)}")

        return alerts

    def render_power_torque_curves(self, df: pd.DataFrame) -> None:
        """Renderizar curvas de potência e torque."""
        st.markdown("### Curvas de Potência e Torque")

        if not any(col in df.columns for col in ["power_estimate", "torque_estimate"]):
            st.warning("Dados de potência/torque não disponíveis")
            return

        # Filtrar dados válidos e agrupar por RPM para suavizar
        valid_data = df.dropna(subset=["rpm"]).copy()

        if valid_data.empty:
            st.warning("Dados insuficientes")
            return

        # Agrupar por faixas de RPM para suavizar
        valid_data["rpm_bin"] = pd.cut(valid_data["rpm"], bins=20).apply(lambda x: x.mid)
        grouped = (
            valid_data.groupby("rpm_bin")
            .agg({"power_estimate": "mean", "torque_estimate": "mean"})
            .reset_index()
        )

        # Criar subplot com eixo Y duplo
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Curva de potência
        if "power_estimate" in grouped.columns:
            fig.add_trace(
                go.Scatter(
                    x=grouped["rpm_bin"],
                    y=grouped["power_estimate"],
                    name="Potência (CV)",
                    line=dict(color="red", width=3),
                    hovertemplate="RPM: %{x:.0f}<br>Potência: %{y:.1f} CV<extra></extra>",
                ),
                secondary_y=False,
            )

        # Curva de torque
        if "torque_estimate" in grouped.columns:
            fig.add_trace(
                go.Scatter(
                    x=grouped["rpm_bin"],
                    y=grouped["torque_estimate"],
                    name="Torque (Nm)",
                    line=dict(color="blue", width=3),
                    hovertemplate="RPM: %{x:.0f}<br>Torque: %{y:.1f} Nm<extra></extra>",
                ),
                secondary_y=True,
            )

        # Configurar layout
        fig.update_xaxes(title_text="RPM")
        fig.update_yaxes(title_text="Potência (CV)", secondary_y=False, color="red")
        fig.update_yaxes(title_text="Torque (Nm)", secondary_y=True, color="blue")

        fig.update_layout(
            title="Curvas de Potência e Torque vs RPM",
            height=500,
            hovermode="x unified",
        )

        st.plotly_chart(fig, width='stretch')

    def render_boost_analysis(self, df: pd.DataFrame) -> None:
        """Renderizar análise de boost."""
        st.markdown("### Análise de Boost")

        if "boost" not in df.columns:
            st.warning("Dados de boost não disponíveis")
            return

        boost_data = df["boost"].dropna()

        if boost_data.empty:
            st.warning("Nenhum dado válido de boost")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Histograma de boost
            fig_hist = px.histogram(
                x=boost_data,
                nbins=30,
                title="Distribuição de Boost",
                labels={"x": "Boost (bar)"},
                marginal="box",
            )
            st.plotly_chart(fig_hist, width='stretch')

        with col2:
            # Boost vs RPM
            if "rpm" in df.columns:
                boost_rpm_data = df.dropna(subset=["boost", "rpm"])
                if not boost_rpm_data.empty:
                    fig_boost_rpm = px.scatter(
                        boost_rpm_data.sample(min(1000, len(boost_rpm_data))),
                        x="rpm",
                        y="boost",
                        title="Boost vs RPM",
                        labels={"rpm": "RPM", "boost": "Boost (bar)"},
                        opacity=0.6,
                        trendline="ols",
                    )
                    st.plotly_chart(fig_boost_rpm, width='stretch')

    def render_efficiency_metrics(self, df: pd.DataFrame) -> None:
        """Renderizar métricas de eficiência."""
        st.markdown("### Métricas de Eficiência")

        efficiency_cols = ["thermal_efficiency", "bmep", "load_factor"]
        available_cols = [col for col in efficiency_cols if col in df.columns]

        if not available_cols:
            st.warning("Dados de eficiência não disponíveis")
            return

        # Tabs para diferentes análises
        eff_tabs = st.tabs(["Eficiência Térmica", "BMEP", "Load Factor"])

        with eff_tabs[0]:
            if "thermal_efficiency" in df.columns:
                eff_data = df["thermal_efficiency"].dropna()
                if not eff_data.empty:
                    col1, col2 = st.columns(2)

                    with col1:
                        fig_eff = px.histogram(
                            x=eff_data,
                            nbins=30,
                            title="Distribuição de Eficiência Térmica",
                            labels={"x": "Eficiência (%)"},
                        )
                        st.plotly_chart(fig_eff, width='stretch')

                    with col2:
                        st.markdown("**Estatísticas:**")
                        st.metric("Média", f"{eff_data.mean():.1f}%")
                        st.metric("Máxima", f"{eff_data.max():.1f}%")
                        st.metric("Desvio", f"{eff_data.std():.1f}%")

        with eff_tabs[1]:
            if "bmep" in df.columns:
                bmep_data = df["bmep"].dropna()
                if not bmep_data.empty:
                    fig_bmep = px.line(
                        x=df.index,
                        y=bmep_data,
                        title="BMEP vs Tempo",
                        labels={"x": "Tempo", "y": "BMEP (bar)"},
                    )
                    st.plotly_chart(fig_bmep, width='stretch')

        with eff_tabs[2]:
            if "load_factor" in df.columns:
                load_data = df["load_factor"].dropna()
                if not load_data.empty:
                    fig_load = px.scatter(
                        df.sample(min(1000, len(df))),
                        x="load_factor",
                        y="power_estimate" if "power_estimate" in df.columns else "rpm",
                        title="Load Factor vs Performance",
                        opacity=0.6,
                    )
                    st.plotly_chart(fig_load, width='stretch')


def render_performance_page() -> None:
    """Renderizar página de análise de performance."""
    st.set_page_config(
        page_title="Performance - FuelTune Analyzer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("FuelTune Analyzer - Análise de Performance")
    st.markdown("Análise detalhada de métricas de performance do motor")
    st.markdown("---")

    # Inicializar manager
    perf_manager = PerformanceAnalysisManager()

    # Sidebar
    with st.sidebar:
        st.header("Performance")

        selector = SessionSelector(key_prefix="performance", show_preview=True)
        selected_session = selector.render_selector()

    # Conteúdo principal
    if selected_session:
        try:
            with st.spinner("Carregando dados de performance..."):
                df = perf_manager.load_performance_data(selected_session.id)

            if df is None or df.empty:
                st.error("Nenhum dado de performance encontrado")
                return

            # Overview
            perf_manager.render_performance_overview(df)

            st.markdown("---")

            # Curvas de potência e torque
            perf_manager.render_power_torque_curves(df)

            st.markdown("---")

            # Análise de boost
            perf_manager.render_boost_analysis(df)

            st.markdown("---")

            # Métricas de eficiência
            perf_manager.render_efficiency_metrics(df)

        except Exception as e:
            logger.error(f"Erro na análise de performance: {str(e)}")
            st.error(f"Erro: {str(e)}")

    else:
        st.info("Selecione uma sessão para análise de performance.")


if __name__ == "__main__":
    render_performance_page()
