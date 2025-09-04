"""
Dashboard Principal - FuelTune Analyzer.

Dashboard com métricas em tempo real, status do sistema,
tendências e últimas sessões carregadas.

Features:
- Cards de métricas principais
- Gráficos de tendência
- Status do sistema
- Últimas sessões
- Atualizações automáticas

Author: A03-UI-STREAMLIT Agent
Created: 2025-01-02
"""

import time
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import streamlit as st

try:
    # Tentar importação relativa primeiro (para quando chamado como módulo)
    from ...data.database import FuelTechCoreData, get_database
    from ...utils.logging_config import get_logger
    from ..components.chart_builder import (
        ChartBuilder,
        ChartConfig,
        SeriesData,
        create_rpm_vs_time_chart,
    )
    from ..components.metric_card import (
        MetricCard,
        create_engine_metrics,
        create_fuel_metrics,
        create_performance_metrics,
    )
    from ..components.session_selector import SessionSelector, get_available_sessions
except ImportError:
    # Fallback para importação absoluta (quando executado via st.navigation)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.data.database import FuelTechCoreData, get_database
    from src.utils.logging_config import get_logger
    from src.ui.components.chart_builder import (
        ChartBuilder,
        ChartConfig,
        SeriesData,
        create_rpm_vs_time_chart,
    )
    from src.ui.components.metric_card import (
        MetricCard,
        create_engine_metrics,
        create_fuel_metrics,
        create_performance_metrics,
    )
    from src.ui.components.session_selector import SessionSelector, get_available_sessions

logger = get_logger(__name__)


class DashboardManager:
    """
    Gerenciador do dashboard principal.

    Responsável por:
    - Carregamento de dados em tempo real
    - Cálculo de métricas agregadas
    - Cache inteligente
    - Atualizações automáticas
    """

    def __init__(self):
        self.db = get_database()
        self.metric_card = MetricCard()

    @st.cache_data(ttl=30)  # Cache por 30 segundos
    def get_system_status(_self) -> Dict[str, Any]:
        """Obter status do sistema."""
        try:
            _self.db.initialize_database()
            sessions = get_available_sessions()

            total_sessions = len(sessions)
            completed_sessions = len([s for s in sessions if s["status"] == "completed"])
            total_records = sum(s["records"] for s in sessions)

            # Calcular estatísticas de qualidade
            quality_scores = [
                s["quality_score"] for s in sessions if s["quality_score"] is not None
            ]
            avg_quality = np.mean(quality_scores) if quality_scores else 0

            # Status do sistema
            system_health = (
                "Excelente" if avg_quality >= 90 else "Bom" if avg_quality >= 70 else "Regular"
            )

            return {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "processing_sessions": total_sessions - completed_sessions,
                "total_records": total_records,
                "avg_quality": avg_quality,
                "system_health": system_health,
                "last_update": datetime.now(),
            }
        except Exception as e:
            logger.error(f"Erro ao obter status do sistema: {str(e)}")
            return {
                "total_sessions": 0,
                "completed_sessions": 0,
                "processing_sessions": 0,
                "total_records": 0,
                "avg_quality": 0,
                "system_health": "Offline",
                "last_update": datetime.now(),
            }

    @st.cache_data(ttl=60)  # Cache por 1 minuto
    def get_latest_session_data(
        _self, session_id: str, limit: int = 1000
    ) -> Optional[pd.DataFrame]:
        """Obter dados da sessão mais recente."""
        try:
            _self.db.initialize_database()
            with _self.db.get_session() as db_session:
                # Buscar dados mais recentes
                core_data = (
                    db_session.query(FuelTechCoreData)
                    .filter(FuelTechCoreData.session_id == session_id)
                    .order_by(FuelTechCoreData.time.desc())
                    .limit(limit)
                    .all()
                )
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
                        "throttle_position": record.throttle_position,
                        "map": record.map,
                        "o2_general": record.o2_general,
                        "engine_temp": record.engine_temp,
                        "fuel_pressure": record.fuel_pressure,
                        "battery_voltage": record.battery_voltage,
                        "ignition_timing": record.ignition_timing,
                    }
                )

            df = pd.DataFrame(data_list)
            return df.sort_values("time")  # Ordenar por tempo

        except Exception as e:
            logger.error(f"Erro ao carregar dados da sessão: {str(e)}")
            return None

    @st.cache_data(ttl=120)  # Cache por 2 minutos
    def calculate_session_statistics(_self, session_id: str) -> Dict[str, float]:
        """Calcular estatísticas da sessão."""
        try:
            df = _self.get_latest_session_data(session_id)

            if df is None or df.empty:
                return {}

            stats = {
                "avg_rpm": df["rpm"].mean(),
                "max_rpm": df["rpm"].max(),
                "min_rpm": df["rpm"].min(),
                "avg_throttle": (
                    df["throttle_position"].mean() if "throttle_position" in df else 0
                ),
                "max_throttle": (df["throttle_position"].max() if "throttle_position" in df else 0),
                "avg_map": df["map"].mean() if "map" in df else 0,
                "max_map": df["map"].max() if "map" in df else 0,
                "avg_lambda": df["o2_general"].mean() if "o2_general" in df else 0,
                "avg_temp": df["engine_temp"].mean() if "engine_temp" in df else 0,
                "max_temp": df["engine_temp"].max() if "engine_temp" in df else 0,
                "avg_fuel_pressure": (df["fuel_pressure"].mean() if "fuel_pressure" in df else 0),
                "avg_battery": (df["battery_voltage"].mean() if "battery_voltage" in df else 0),
                "avg_timing": (df["ignition_timing"].mean() if "ignition_timing" in df else 0),
                "session_duration": (df["time"].max() - df["time"].min() if len(df) > 1 else 0),
                "data_points": len(df),
            }

            # Calcular estimativas de performance
            if "rpm" in df and "map" in df:
                # Estimativa simples de potência baseada em RPM e MAP
                power_estimate = (df["rpm"] * df["map"] * 0.001).mean()
                stats["estimated_power"] = power_estimate

            return stats

        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {str(e)}")
            return {}

    def render_system_overview(self) -> None:
        """Renderizar overview do sistema."""
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2; font-size: 1.5rem;">dashboard</i>
            <h3 style="margin: 0; color: #1976D2;">Status do Sistema</h3>
        </div>
        """, unsafe_allow_html=True)

        status = self.get_system_status()

        # Métricas do sistema
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Sessões Totais",
                status["total_sessions"],
                delta=None,
                help="Total de sessões importadas",
            )

        with col2:
            completion_rate = (
                (status["completed_sessions"] / status["total_sessions"] * 100)
                if status["total_sessions"] > 0
                else 0
            )
            st.metric(
                "Sessões Completas",
                f"{status['completed_sessions']} ({completion_rate:.1f}%)",
                delta=None,
                help="Sessões processadas com sucesso",
            )

        with col3:
            st.metric(
                "Pontos de Dados",
                f"{status['total_records']:,}",
                delta=None,
                help="Total de pontos de telemetria",
            )

        with col4:
            quality_color = "normal" if status["avg_quality"] >= 70 else "inverse"
            st.metric(
                "Qualidade Média",
                f"{status['avg_quality']:.1f}%",
                delta=None,
                delta_color=quality_color,
                help="Qualidade média dos dados",
            )

        # Status de saúde do sistema
        col1, col2 = st.columns([3, 1])

        with col1:
            health_color_map = {
                "Excelente": ("check_circle", "#4CAF50"),
                "Bom": ("warning", "#FF9800"),
                "Regular": ("info", "#2196F3"),
                "Offline": ("error", "#F44336"),
            }

            icon_name, icon_color = health_color_map.get(status['system_health'], ("help", "#757575"))
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <strong style="color: var(--text-color);">Status:</strong>
                <i class="material-icons" style="color: {icon_color}; font-size: 1.2rem;">{icon_name}</i>
                <span style="color: var(--text-color);">{status['system_health']}</span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"**Última Atualização:** {status['last_update'].strftime('%H:%M:%S')}")

    def render_latest_session_metrics(self, session_id: str) -> None:
        """Renderizar métricas da sessão mais recente."""
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2; font-size: 1.5rem;">analytics</i>
            <h3 style="margin: 0; color: #1976D2;">Métricas da Sessão Atual</h3>
        </div>
        """, unsafe_allow_html=True)

        stats = self.calculate_session_statistics(session_id)

        if not stats:
            st.warning("Dados da sessão não encontrados.")
            return

        # Métricas do motor
        engine_metrics = create_engine_metrics(
            rpm=int(stats.get("avg_rpm", 0)),
            throttle=stats.get("avg_throttle", 0),
            temp=stats.get("avg_temp", 0),
            lambda_val=stats.get("avg_lambda", 0),
        )

        self.metric_card.render_row(engine_metrics)

        # Métricas do combustível
        fuel_metrics = create_fuel_metrics(
            flow=stats.get("avg_fuel_pressure", 0) * 10,  # Estimativa
            pressure=stats.get("avg_fuel_pressure", 0),
            injection_time=stats.get("avg_timing", 0),
        )

        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2; font-size: 1.5rem;">local_gas_station</i>
            <h3 style="margin: 0; color: #1976D2;">Sistema de Combustível</h3>
        </div>
        """, unsafe_allow_html=True)
        self.metric_card.render_row(fuel_metrics)

        # Métricas de performance
        performance_metrics = create_performance_metrics(
            power=int(stats.get("estimated_power", 0)),
            torque=int(stats.get("estimated_power", 0) * 1.5),  # Estimativa
            efficiency=75.0,  # Placeholder
        )

        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2; font-size: 1.5rem;">speed</i>
            <h3 style="margin: 0; color: #1976D2;">Performance</h3>
        </div>
        """, unsafe_allow_html=True)
        self.metric_card.render_row(performance_metrics)

    def render_realtime_charts(self, session_id: str) -> None:
        """Renderizar gráficos em tempo real."""
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2; font-size: 1.5rem;">trending_up</i>
            <h3 style="margin: 0; color: #1976D2;">Tendências em Tempo Real</h3>
        </div>
        """, unsafe_allow_html=True)

        df = self.get_latest_session_data(session_id, limit=500)

        if df is None or df.empty:
            st.warning("Dados não disponíveis para gráficos.")
            return

        # Gráfico RPM vs Tempo
        col1, col2 = st.columns(2)

        with col1:
            if "time" in df and "rpm" in df:
                rpm_chart = create_rpm_vs_time_chart(
                    time_data=df["time"].tolist(),
                    rpm_data=df["rpm"].tolist(),
                    title="RPM vs Tempo",
                )
                rpm_chart.render(key="dashboard_rpm_chart")

        with col2:
            # Gráfico de Throttle Position
            if "time" in df and "throttle_position" in df:
                throttle_config = ChartConfig(
                    title="Throttle Position",
                    x_label="Tempo (s)",
                    y_label="TPS (%)",
                    height=300,
                )

                throttle_builder = ChartBuilder(throttle_config)
                throttle_series = [
                    SeriesData(
                        x=df["time"].tolist(),
                        y=df["throttle_position"].fillna(0).tolist(),
                        name="Throttle",
                        color="#ff7f0e",
                    )
                ]

                throttle_builder.create_line_chart(throttle_series)
                throttle_builder.render(key="dashboard_throttle_chart")

        # Gráfico MAP vs Lambda
        col1, col2 = st.columns(2)

        with col1:
            if "map" in df and "time" in df:
                map_config = ChartConfig(
                    title="Manifold Pressure",
                    x_label="Tempo (s)",
                    y_label="MAP (bar)",
                    height=300,
                )

                map_builder = ChartBuilder(map_config)
                map_series = [
                    SeriesData(
                        x=df["time"].tolist(),
                        y=df["map"].fillna(0).tolist(),
                        name="MAP",
                        color="#2ca02c",
                    )
                ]

                map_builder.create_line_chart(map_series)
                map_builder.render(key="dashboard_map_chart")

        with col2:
            if "o2_general" in df and "time" in df:
                lambda_config = ChartConfig(
                    title="Lambda Sensor",
                    x_label="Tempo (s)",
                    y_label="Lambda (λ)",
                    height=300,
                )

                lambda_builder = ChartBuilder(lambda_config)
                lambda_series = [
                    SeriesData(
                        x=df["time"].tolist(),
                        y=df["o2_general"].fillna(0.85).tolist(),
                        name="Lambda",
                        color="#d62728",
                    )
                ]

                lambda_builder.create_line_chart(lambda_series)
                lambda_builder.render(key="dashboard_lambda_chart")

    def render_recent_sessions(self) -> None:
        """Renderizar sessões recentes."""
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2; font-size: 1.5rem;">history</i>
            <h3 style="margin: 0; color: #1976D2;">Sessões Recentes</h3>
        </div>
        """, unsafe_allow_html=True)

        sessions = get_available_sessions()

        if not sessions:
            st.info("Nenhuma sessão encontrada. Importe dados primeiro.")
            return

        # Mostrar últimas 5 sessões
        recent_sessions = sorted(sessions, key=lambda x: x["created_at"], reverse=True)[:5]

        for session in recent_sessions:
            with st.expander(f"{session['name']}", expanded=False):
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                    <i class="material-icons" style="color: #1976D2;">folder</i>
                    <strong style="color: var(--text-color);">{session['name']}</strong>
                </div>
                """, unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Pontos", f"{session['records']:,}")

                with col2:
                    duration = session.get("duration")
                    duration_str = f"{duration:.1f}s" if duration else "N/A"
                    st.metric("Duração", duration_str)

                with col3:
                    quality = session.get("quality_score")
                    quality_str = f"{quality:.1f}%" if quality else "N/A"
                    st.metric("Qualidade", quality_str)

                with col4:
                    status_icon = "check_circle" if session["status"] == "completed" else "schedule"
                    status_color = "#4CAF50" if session["status"] == "completed" else "#FF9800"
                    
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <strong style="color: var(--text-color);">Status:</strong>
                        <i class="material-icons" style="color: {status_color}; font-size: 1.1rem;">{status_icon}</i>
                        <span style="color: {status_color};">{session['status'].title()}</span>
                    </div>
                    """, unsafe_allow_html=True)

                # Botão para abrir sessão
                if st.button(f"Abrir {session['name']}", key=f"open_{session['id']}"):
                    st.session_state["selected_session_id"] = session["id"]
                    st.rerun()


def render_dashboard_page() -> None:
    """
    Renderizar página principal do dashboard.

    Esta é a função principal que deve ser chamada para exibir o dashboard.
    """
    st.set_page_config(
        page_title="Dashboard - FuelTune Analyzer",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Professional CSS
    st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
    .material-icons {
        font-family: 'Material Icons';
        font-weight: normal;
        font-style: normal;
        display: inline-block;
        line-height: 1;
        text-transform: none;
        letter-spacing: normal;
        word-wrap: normal;
        white-space: nowrap;
        direction: ltr;
    }
    </style>
    """, unsafe_allow_html=True)

    # Título da página
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
        <i class="material-icons" style="font-size: 3rem; color: #1976D2;">dashboard</i>
        <div>
            <h1 style="margin: 0; color: #1976D2;">FuelTune Analyzer - Dashboard</h1>
            <p style="margin: 0.25rem 0 0 0; color: #6C757D;">Monitor e analise dados automotivos em tempo real</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Inicializar manager
    dashboard = DashboardManager()

    # Sidebar para controles
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2;">settings</i>
            <h3 style="margin: 0;">Controles</h3>
        </div>
        """, unsafe_allow_html=True)

        # Seletor de sessão
        selector = SessionSelector(key_prefix="dashboard", show_preview=False, show_filters=False)
        selected_session = selector.render_selector()

        # Auto-refresh
        auto_refresh = st.checkbox("Atualização Automática", value=False)
        if auto_refresh:
            st.markdown("<i class='material-icons' style='color: #4CAF50; font-size: 1rem; margin-left: 0.5rem;'>sync</i>", unsafe_allow_html=True)
        if auto_refresh:
            refresh_interval = st.slider("Intervalo (s)", 5, 60, 10)

        # Botão de refresh manual
        if st.button("Atualizar Agora"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #1976D2;'>refresh</i>", unsafe_allow_html=True)
            st.cache_data.clear()
            st.rerun()

    # Auto-refresh logic
    if auto_refresh and "last_refresh" in st.session_state:
        time_since_refresh = time.time() - st.session_state["last_refresh"]
        if time_since_refresh >= refresh_interval:
            st.session_state["last_refresh"] = time.time()
            st.rerun()
    elif auto_refresh:
        st.session_state["last_refresh"] = time.time()

    # Conteúdo principal
    try:
        # Status do sistema
        dashboard.render_system_overview()

        st.markdown("---")

        # Se há sessão selecionada, mostrar métricas e gráficos
        if selected_session:
            col1, col2 = st.columns([2, 1])

            with col1:
                dashboard.render_latest_session_metrics(selected_session.id)
                st.markdown("---")
                dashboard.render_realtime_charts(selected_session.id)

            with col2:
                dashboard.render_recent_sessions()
        else:
            # Se não há sessão, mostrar apenas sessões recentes
            dashboard.render_recent_sessions()

            st.info("Selecione uma sessão na barra lateral para ver métricas detalhadas.")

    except Exception as e:
        logger.error(f"Erro no dashboard: {str(e)}")
        st.error(f"Erro ao carregar dashboard: {str(e)}")

        # Mostrar informações de debug se em desenvolvimento
        if st.session_state.get("debug_mode", False):
            st.exception(e)


if __name__ == "__main__":
    # Executar dashboard diretamente
    render_dashboard_page()
