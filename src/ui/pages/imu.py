"""
IMU Telemetry Page - FuelTune Analyzer.

Página especializada em análise de dados IMU (Inertial Measurement Unit),
incluindo visualização 3D de pitch/roll/yaw, G-forces em tempo real,
análise de dirigibilidade e mapas de calor de forças.

Features:
- Visualização 3D de pitch, roll e yaw
- Análise de G-forces longitudinal e lateral
- Mapas de calor de forças dinâmicas
- Análise de dirigibilidade e tração
- Correlação com parâmetros do motor
- Detecção de eventos de aceleração/frenagem

Author: A03-UI-STREAMLIT Agent
Created: 2025-01-02
"""

from typing import Dict, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

try:
    # Tentar importação relativa primeiro (para quando chamado como módulo)
    from ...data.database import FuelTechExtendedData, get_database
    from ...utils.logging_config import get_logger
    from ..components.metric_card import MetricCard
    from ..components.session_selector import SessionSelector
except ImportError:
    # Fallback para importação absoluta (quando executado via st.navigation)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.data.database import FuelTechExtendedData, get_database
    from src.utils.logging_config import get_logger
    from src.ui.components.metric_card import MetricCard
    from src.ui.components.session_selector import SessionSelector

logger = get_logger(__name__)


class IMUAnalysisManager:
    """
    Gerenciador de análise de dados IMU.

    Responsável por:
    - Carregamento de dados IMU e G-forces
    - Visualizações 3D de atitude do veículo
    - Análise de forças dinâmicas
    - Correlação com parâmetros do motor
    - Detecção de eventos críticos
    - Mapas de calor de dirigibilidade
    """

    def __init__(self):
        self.db = get_database()
        self.metric_card = MetricCard()

    @st.cache_data(ttl=300)
    def load_imu_data(_self, session_id: str) -> Optional[pd.DataFrame]:
        """
        Carregar dados IMU da sessão.

        Args:
            session_id: ID da sessão

        Returns:
            DataFrame com dados IMU ou None
        """
        try:
            _self.db.initialize_database()
            with _self.db.get_session() as db_session:
                # Buscar dados extended que contém informações IMU
                extended_query = (
                    db_session.query(FuelTechExtendedData)
                    .filter(FuelTechExtendedData.session_id == session_id)
                    .order_by(FuelTechExtendedData.time)
                )

                extended_data = extended_query.all()
                # Session is automatically closed by context manager

            if not extended_data:
                return None

            # Converter para DataFrame
            data_list = []
            for record in extended_data:
                data_list.append(
                    {
                        "time": record.time,
                        "g_force_accel": record.g_force_accel,
                        "g_force_lateral": record.g_force_lateral,
                        "g_force_accel_raw": record.g_force_accel_raw,
                        "g_force_lateral_raw": record.g_force_lateral_raw,
                        "pitch_angle": record.pitch_angle,
                        "pitch_rate": record.pitch_rate,
                        "roll_angle": record.roll_angle,
                        "roll_rate": record.roll_rate,
                        "heading": record.heading,
                        "traction_speed": record.traction_speed,
                        "acceleration_speed": record.acceleration_speed,
                        "traction_control_slip": record.traction_control_slip,
                        "traction_control_slip_rate": record.traction_control_slip_rate,
                    }
                )

            df = pd.DataFrame(data_list)

            # Calcular dados derivados
            df = _self.calculate_derived_imu_data(df)

            return df

        except Exception as e:
            logger.error(f"Erro ao carregar dados IMU: {str(e)}")
            return None

    def calculate_derived_imu_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcular dados derivados dos dados IMU.

        Args:
            df: DataFrame com dados IMU básicos

        Returns:
            DataFrame com dados derivados adicionados
        """
        if df.empty:
            return df

        try:
            # Calcular G-force resultante
            if "g_force_accel" in df.columns and "g_force_lateral" in df.columns:
                df["g_force_resultant"] = np.sqrt(
                    df["g_force_accel"].fillna(0) ** 2 + df["g_force_lateral"].fillna(0) ** 2
                )

            # Calcular ângulo de deriva estimado
            if "g_force_lateral" in df.columns and "traction_speed" in df.columns:
                # Simplificado: ângulo baseado em força lateral e velocidade
                df["slip_angle_estimate"] = np.degrees(
                    np.arctan(df["g_force_lateral"].fillna(0) / 9.81 * 0.1)
                )

            # Detectar eventos de aceleração/frenagem
            if "g_force_accel" in df.columns:
                df["acceleration_event"] = df["g_force_accel"] > 0.3
                df["braking_event"] = df["g_force_accel"] < -0.3

            # Detectar curvas (força lateral alta)
            if "g_force_lateral" in df.columns:
                df["cornering_event"] = np.abs(df["g_force_lateral"]) > 0.3

            # Calcular variação de atitude
            for angle_col in ["pitch_angle", "roll_angle"]:
                if angle_col in df.columns:
                    df[f"{angle_col}_variation"] = df[angle_col].rolling(window=10).std()

            # Índice de estabilidade (combinação de variações)
            stability_factors = []
            for col in ["pitch_angle_variation", "roll_angle_variation"]:
                if col in df.columns:
                    stability_factors.append(df[col].fillna(0))

            if stability_factors:
                df["stability_index"] = np.mean(stability_factors, axis=0)
                df["stability_index"] = 100 - (df["stability_index"] * 10)  # Inverter e escalar
                df["stability_index"] = df["stability_index"].clip(0, 100)

        except Exception as e:
            logger.error(f"Erro no cálculo de dados derivados: {str(e)}")

        return df

    def calculate_imu_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcular métricas dos dados IMU.

        Args:
            df: DataFrame com dados IMU

        Returns:
            Dicionário com métricas calculadas
        """
        metrics = {}

        if df.empty:
            return metrics

        try:
            # Métricas de G-force
            g_force_cols = ["g_force_accel", "g_force_lateral", "g_force_resultant"]
            for col in g_force_cols:
                if col in df.columns and not df[col].isnull().all():
                    data = df[col].dropna()
                    metrics[f"{col}_max"] = data.max()
                    metrics[f"{col}_min"] = data.min()
                    metrics[f"{col}_avg"] = data.mean()
                    metrics[f"{col}_std"] = data.std()

            # Métricas de ângulos
            angle_cols = ["pitch_angle", "roll_angle", "heading"]
            for col in angle_cols:
                if col in df.columns and not df[col].isnull().all():
                    data = df[col].dropna()
                    metrics[f"{col}_max"] = data.max()
                    metrics[f"{col}_min"] = data.min()
                    metrics[f"{col}_range"] = data.max() - data.min()

            # Métricas de eventos
            event_cols = ["acceleration_event", "braking_event", "cornering_event"]
            for col in event_cols:
                if col in df.columns:
                    metrics[f"{col}_count"] = df[col].sum()
                    metrics[f"{col}_percentage"] = (df[col].sum() / len(df)) * 100

            # Métricas de estabilidade
            if "stability_index" in df.columns:
                stability_data = df["stability_index"].dropna()
                if not stability_data.empty:
                    metrics["avg_stability"] = stability_data.mean()
                    metrics["min_stability"] = stability_data.min()

            # Métricas de tração
            if "traction_control_slip" in df.columns:
                slip_data = df["traction_control_slip"].dropna()
                if not slip_data.empty:
                    metrics["avg_slip"] = slip_data.mean()
                    metrics["max_slip"] = slip_data.max()

        except Exception as e:
            logger.error(f"Erro no cálculo de métricas IMU: {str(e)}")

        return metrics

    def render_imu_overview(self, df: pd.DataFrame) -> None:
        """Renderizar overview dos dados IMU."""
        st.markdown("### Overview IMU & G-Forces")

        metrics = self.calculate_imu_metrics(df)

        if not metrics:
            st.warning("Dados IMU insuficientes para calcular métricas")
            return

        # Cards de métricas principais
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            max_g_accel = metrics.get("g_force_accel_max", 0)
            st.metric(
                "Max G Longitudinal",
                f"{max_g_accel:.2f}g",
                help="Máxima aceleração longitudinal",
            )

        with col2:
            max_g_lateral = metrics.get("g_force_lateral_max", 0)
            st.metric(
                "Max G Lateral",
                f"{max_g_lateral:.2f}g",
                help="Máxima força lateral (curvas)",
            )

        with col3:
            max_g_resultant = metrics.get("g_force_resultant_max", 0)
            st.metric(
                "Max G Resultante",
                f"{max_g_resultant:.2f}g",
                help="Máxima força resultante combinada",
            )

        with col4:
            avg_stability = metrics.get("avg_stability", 0)
            st.metric(
                "Índice Estabilidade",
                f"{avg_stability:.1f}%",
                help="Índice médio de estabilidade do veículo",
            )

        # Métricas de ângulos
        st.markdown("#### Atitude do Veículo")
        col1, col2, col3 = st.columns(3)

        with col1:
            pitch_range = metrics.get("pitch_angle_range", 0)
            st.metric(
                "Variação Pitch",
                f"{pitch_range:.1f}°",
                help="Variação do ângulo de pitch (cabrar/picar)",
            )

        with col2:
            roll_range = metrics.get("roll_angle_range", 0)
            st.metric(
                "Variação Roll",
                f"{roll_range:.1f}°",
                help="Variação do ângulo de roll (inclinação lateral)",
            )

        with col3:
            heading_range = metrics.get("heading_range", 0)
            st.metric(
                "Variação Heading",
                f"{heading_range:.1f}°",
                help="Variação do heading (direção)",
            )

    def render_3d_attitude_visualization(self, df: pd.DataFrame) -> None:
        """Renderizar visualização 3D da atitude do veículo."""
        st.markdown("### Visualização 3D da Atitude")

        required_cols = ["pitch_angle", "roll_angle", "heading"]
        missing_cols = [
            col for col in required_cols if col not in df.columns or df[col].isnull().all()
        ]

        if missing_cols:
            st.warning(f"Dados de atitude não disponíveis: {', '.join(missing_cols)}")
            return

        # Filtrar dados válidos
        attitude_data = df.dropna(subset=required_cols)

        if attitude_data.empty:
            st.warning("Nenhum dado válido de atitude encontrado")
            return

        # Sample dos dados para performance (máximo 1000 pontos)
        if len(attitude_data) > 1000:
            sample_indices = np.linspace(0, len(attitude_data) - 1, 1000, dtype=int)
            attitude_data = attitude_data.iloc[sample_indices]

        col1, col2 = st.columns(2)

        with col1:
            # Gráfico 3D de trajetória
            fig_3d = go.Figure(
                data=[
                    go.Scatter3d(
                        x=attitude_data["pitch_angle"],
                        y=attitude_data["roll_angle"],
                        z=attitude_data["heading"],
                        mode="markers+lines",
                        marker=dict(
                            size=3,
                            color=attitude_data.index,
                            colorscale="Viridis",
                            colorbar=dict(title="Tempo"),
                            opacity=0.8,
                        ),
                        line=dict(width=2),
                        name="Trajetória 3D",
                        hovertemplate="Pitch: %{x:.1f}°<br>Roll: %{y:.1f}°<br>Heading: %{z:.1f}°<extra></extra>",
                    )
                ]
            )

            fig_3d.update_layout(
                title="Atitude do Veículo em 3D",
                scene=dict(
                    xaxis_title="Pitch (°)",
                    yaxis_title="Roll (°)",
                    zaxis_title="Heading (°)",
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
                ),
                height=500,
            )

            st.plotly_chart(fig_3d, width='stretch')

        with col2:
            # Gráfico polar de heading
            fig_polar = go.Figure()

            # Converter heading para radianos
            heading_rad = np.radians(attitude_data["heading"])

            fig_polar.add_trace(
                go.Scatterpolar(
                    r=np.ones(len(heading_rad)),
                    theta=attitude_data["heading"],
                    mode="markers",
                    marker=dict(color=attitude_data.index, colorscale="Plasma", size=4),
                    name="Direção",
                    hovertemplate="Heading: %{theta}°<extra></extra>",
                )
            )

            fig_polar.update_layout(
                title="Distribuição de Heading",
                polar=dict(
                    angularaxis=dict(direction="clockwise", rotation=90),
                    radialaxis=dict(visible=False),
                ),
                height=500,
            )

            st.plotly_chart(fig_polar, width='stretch')

    def render_g_force_analysis(self, df: pd.DataFrame) -> None:
        """Renderizar análise de G-forces."""
        st.markdown("### Análise de G-Forces")

        g_force_cols = ["g_force_accel", "g_force_lateral"]
        available_cols = [
            col for col in g_force_cols if col in df.columns and not df[col].isnull().all()
        ]

        if not available_cols:
            st.warning("Dados de G-force não disponíveis")
            return

        # Tabs para diferentes análises
        g_tabs = st.tabs(
            [
                "Séries Temporais",
                "Mapa de Forças",
                "Distribuições",
                "Eventos",
            ]
        )

        with g_tabs[0]:
            self.render_g_force_time_series(df)

        with g_tabs[1]:
            self.render_g_force_map(df)

        with g_tabs[2]:
            self.render_g_force_distributions(df)

        with g_tabs[3]:
            self.render_g_force_events(df)

    def render_g_force_time_series(self, df: pd.DataFrame) -> None:
        """Renderizar séries temporais de G-forces."""
        if "time" not in df.columns:
            st.warning("Dados de tempo não disponíveis")
            return

        # Criar subplot com múltiplos eixos Y
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            subplot_titles=[
                "G-Force Longitudinal",
                "G-Force Lateral",
                "G-Force Resultante",
            ],
            vertical_spacing=0.08,
        )

        # G-force longitudinal
        if "g_force_accel" in df.columns:
            valid_data = df.dropna(subset=["time", "g_force_accel"])
            fig.add_trace(
                go.Scatter(
                    x=valid_data["time"],
                    y=valid_data["g_force_accel"],
                    name="G Longitudinal",
                    line=dict(color="blue"),
                    hovertemplate="Tempo: %{x:.1f}s<br>G-Force: %{y:.2f}g<extra></extra>",
                ),
                row=1,
                col=1,
            )

        # G-force lateral
        if "g_force_lateral" in df.columns:
            valid_data = df.dropna(subset=["time", "g_force_lateral"])
            fig.add_trace(
                go.Scatter(
                    x=valid_data["time"],
                    y=valid_data["g_force_lateral"],
                    name="G Lateral",
                    line=dict(color="red"),
                    hovertemplate="Tempo: %{x:.1f}s<br>G-Force: %{y:.2f}g<extra></extra>",
                ),
                row=2,
                col=1,
            )

        # G-force resultante
        if "g_force_resultant" in df.columns:
            valid_data = df.dropna(subset=["time", "g_force_resultant"])
            fig.add_trace(
                go.Scatter(
                    x=valid_data["time"],
                    y=valid_data["g_force_resultant"],
                    name="G Resultante",
                    line=dict(color="green"),
                    hovertemplate="Tempo: %{x:.1f}s<br>G-Force: %{y:.2f}g<extra></extra>",
                ),
                row=3,
                col=1,
            )

        # Layout
        fig.update_layout(height=600, title_text="G-Forces vs Tempo", showlegend=True)

        fig.update_xaxes(title_text="Tempo (s)", row=3, col=1)
        fig.update_yaxes(title_text="G-Force (g)", row=1, col=1)
        fig.update_yaxes(title_text="G-Force (g)", row=2, col=1)
        fig.update_yaxes(title_text="G-Force (g)", row=3, col=1)

        st.plotly_chart(fig, width='stretch')

    def render_g_force_map(self, df: pd.DataFrame) -> None:
        """Renderizar mapa de calor de G-forces."""
        required_cols = ["g_force_accel", "g_force_lateral"]

        if not all(col in df.columns for col in required_cols):
            st.warning("Dados de G-force longitudinal e lateral necessários")
            return

        valid_data = df.dropna(subset=required_cols)

        if valid_data.empty:
            st.warning("Nenhum dado válido de G-force encontrado")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Scatter plot G-lateral vs G-longitudinal
            fig_scatter = px.scatter(
                valid_data.sample(min(2000, len(valid_data))),  # Sample para performance
                x="g_force_accel",
                y="g_force_lateral",
                title="Mapa de G-Forces",
                labels={
                    "g_force_accel": "G-Force Longitudinal (g)",
                    "g_force_lateral": "G-Force Lateral (g)",
                },
                opacity=0.6,
                color_discrete_sequence=["blue"],
            )

            # Adicionar círculos de referência
            theta = np.linspace(0, 2 * np.pi, 100)
            for g_level in [0.5, 1.0, 1.5]:
                x_circle = g_level * np.cos(theta)
                y_circle = g_level * np.sin(theta)

                fig_scatter.add_trace(
                    go.Scatter(
                        x=x_circle,
                        y=y_circle,
                        mode="lines",
                        name=f"{g_level}g",
                        line=dict(dash="dash", color="gray", width=1),
                        showlegend=True,
                    )
                )

            # Adicionar linhas de referência
            fig_scatter.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)
            fig_scatter.add_vline(x=0, line_dash="solid", line_color="black", line_width=1)

            fig_scatter.update_layout(height=500)
            st.plotly_chart(fig_scatter, width='stretch')

        with col2:
            # Heatmap 2D das G-forces
            # Criar bins para o heatmap
            x_bins = np.linspace(
                valid_data["g_force_accel"].min(), valid_data["g_force_accel"].max(), 20
            )
            y_bins = np.linspace(
                valid_data["g_force_lateral"].min(),
                valid_data["g_force_lateral"].max(),
                20,
            )

            # Calcular densidade
            H, x_edges, y_edges = np.histogram2d(
                valid_data["g_force_accel"],
                valid_data["g_force_lateral"],
                bins=[x_bins, y_bins],
            )

            fig_heatmap = go.Figure(
                data=go.Heatmap(
                    z=H.T,
                    x=x_edges[:-1],
                    y=y_edges[:-1],
                    colorscale="Hot",
                    hovertemplate="G-Accel: %{x:.2f}g<br>G-Lateral: %{y:.2f}g<br>Densidade: %{z}<extra></extra>",
                )
            )

            fig_heatmap.update_layout(
                title="Densidade de G-Forces",
                xaxis_title="G-Force Longitudinal (g)",
                yaxis_title="G-Force Lateral (g)",
                height=500,
            )

            st.plotly_chart(fig_heatmap, width='stretch')

    def render_g_force_distributions(self, df: pd.DataFrame) -> None:
        """Renderizar distribuições de G-forces."""
        g_force_cols = ["g_force_accel", "g_force_lateral", "g_force_resultant"]
        available_cols = [
            col for col in g_force_cols if col in df.columns and not df[col].isnull().all()
        ]

        if not available_cols:
            st.warning("Nenhum dado de G-force disponível")
            return

        # Seletor de variável
        selected_var = st.selectbox("Selecione G-Force:", available_cols)

        if selected_var and selected_var in df.columns:
            valid_data = df[selected_var].dropna()

            col1, col2 = st.columns(2)

            with col1:
                # Histograma
                fig_hist = px.histogram(
                    x=valid_data,
                    nbins=50,
                    title=f"Distribuição - {selected_var}",
                    labels={"x": f"{selected_var} (g)"},
                    marginal="box",
                )
                st.plotly_chart(fig_hist, width='stretch')

            with col2:
                # Estatísticas
                st.markdown(f"#### Estatísticas - {selected_var}")

                col_a, col_b = st.columns(2)

                with col_a:
                    st.metric("Média", f"{valid_data.mean():.3f}g")
                    st.metric("Máximo", f"{valid_data.max():.3f}g")

                with col_b:
                    st.metric("Desvio Padrão", f"{valid_data.std():.3f}g")
                    st.metric("Mínimo", f"{valid_data.min():.3f}g")

                # Percentis
                st.markdown("**Percentis:**")
                percentiles = [50, 90, 95, 99]
                for p in percentiles:
                    value = np.percentile(valid_data, p)
                    st.write(f"- {p}%: {value:.3f}g")

    def render_g_force_events(self, df: pd.DataFrame) -> None:
        """Renderizar análise de eventos de G-force."""
        event_cols = ["acceleration_event", "braking_event", "cornering_event"]
        available_events = [col for col in event_cols if col in df.columns]

        if not available_events:
            st.warning("Eventos de G-force não calculados")
            return

        # Estatísticas de eventos
        col1, col2, col3 = st.columns(3)

        with col1:
            if "acceleration_event" in df.columns:
                accel_count = df["acceleration_event"].sum()
                accel_pct = (accel_count / len(df)) * 100
                st.metric(
                    "Eventos de Aceleração",
                    f"{accel_count}",
                    delta=f"{accel_pct:.1f}% do tempo",
                )

        with col2:
            if "braking_event" in df.columns:
                brake_count = df["braking_event"].sum()
                brake_pct = (brake_count / len(df)) * 100
                st.metric(
                    "Eventos de Frenagem",
                    f"{brake_count}",
                    delta=f"{brake_pct:.1f}% do tempo",
                )

        with col3:
            if "cornering_event" in df.columns:
                corner_count = df["cornering_event"].sum()
                corner_pct = (corner_count / len(df)) * 100
                st.metric(
                    "Eventos de Curva",
                    f"{corner_count}",
                    delta=f"{corner_pct:.1f}% do tempo",
                )

        # Timeline de eventos
        if "time" in df.columns:
            st.markdown("#### Timeline de Eventos")

            fig_events = go.Figure()

            y_offset = 0
            colors = {
                "acceleration_event": "green",
                "braking_event": "red",
                "cornering_event": "blue",
            }

            for event_col in available_events:
                if event_col in df.columns:
                    event_data = df[df[event_col] == True]

                    if not event_data.empty:
                        fig_events.add_trace(
                            go.Scatter(
                                x=event_data["time"],
                                y=[y_offset] * len(event_data),
                                mode="markers",
                                name=event_col.replace("_", " ").title(),
                                marker=dict(
                                    color=colors.get(event_col, "gray"),
                                    size=8,
                                    symbol="diamond",
                                ),
                                hovertemplate=f"{event_col}: %{{x:.1f}}s<extra></extra>",
                            )
                        )

                    y_offset += 1

            fig_events.update_layout(
                title="Timeline de Eventos de G-Force",
                xaxis_title="Tempo (s)",
                yaxis_title="Tipo de Evento",
                height=300,
                yaxis=dict(
                    tickmode="array",
                    tickvals=list(range(len(available_events))),
                    ticktext=[col.replace("_", " ").title() for col in available_events],
                ),
            )

            st.plotly_chart(fig_events, width='stretch')

    def render_traction_analysis(self, df: pd.DataFrame) -> None:
        """Renderizar análise de tração."""
        st.markdown("### Análise de Tração e Controle")

        traction_cols = ["traction_control_slip", "traction_control_slip_rate"]
        available_cols = [
            col for col in traction_cols if col in df.columns and not df[col].isnull().all()
        ]

        if not available_cols:
            st.warning("Dados de controle de tração não disponíveis")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Análise de slip
            if "traction_control_slip" in df.columns:
                slip_data = df["traction_control_slip"].dropna()

                if not slip_data.empty:
                    fig_slip = px.histogram(
                        x=slip_data,
                        nbins=30,
                        title="Distribuição de Slip de Tração",
                        labels={"x": "Slip (%)"},
                    )
                    st.plotly_chart(fig_slip, width='stretch')

        with col2:
            # Slip vs velocidade
            if all(col in df.columns for col in ["traction_control_slip", "traction_speed"]):
                valid_data = df.dropna(subset=["traction_control_slip", "traction_speed"])

                if not valid_data.empty:
                    fig_slip_speed = px.scatter(
                        valid_data.sample(min(1000, len(valid_data))),
                        x="traction_speed",
                        y="traction_control_slip",
                        title="Slip vs Velocidade de Tração",
                        labels={
                            "traction_speed": "Velocidade (km/h)",
                            "traction_control_slip": "Slip (%)",
                        },
                        opacity=0.6,
                    )
                    st.plotly_chart(fig_slip_speed, width='stretch')

        # Métricas de tração
        metrics = self.calculate_imu_metrics(df)

        col1, col2, col3 = st.columns(3)

        with col1:
            avg_slip = metrics.get("avg_slip", 0)
            st.metric("Slip Médio", f"{avg_slip:.1f}%")

        with col2:
            max_slip = metrics.get("max_slip", 0)
            st.metric("Slip Máximo", f"{max_slip:.1f}%")

        with col3:
            if "traction_speed" in df.columns:
                avg_speed = df["traction_speed"].mean()
                st.metric("Velocidade Média", f"{avg_speed:.1f} km/h")


def render_imu_page() -> None:
    """
    Renderizar página de análise IMU.

    Esta é a função principal que deve ser chamada para exibir a página IMU.
    """
    st.set_page_config(
        page_title="IMU Telemetry - FuelTune Analyzer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Título da página
    st.title("FuelTune Analyzer - IMU & Telemetria")
    st.markdown("Análise de dados inerciais, G-forces e dinâmica do veículo")
    st.markdown("---")

    # Inicializar manager
    imu_manager = IMUAnalysisManager()

    # Sidebar para seleção de sessão
    with st.sidebar:
        st.header("Dados IMU")

        selector = SessionSelector(key_prefix="imu", show_preview=True, show_filters=False)
        selected_session = selector.render_selector()

        if selected_session:
            st.markdown("---")
            st.markdown("### Configurações")

            # Filtros de G-force
            with st.expander("Filtros G-Force"):
                min_g_threshold = st.slider(
                    "Threshold mínimo (g):",
                    min_value=0.1,
                    max_value=2.0,
                    value=0.3,
                    step=0.1,
                    help="Valor mínimo para detectar eventos",
                )

                smooth_data = st.checkbox(
                    "Suavizar dados", value=True, help="Aplicar filtro passa-baixa"
                )

            # Configurações de visualização
            with st.expander("Visualização"):
                show_raw_data = st.checkbox("Mostrar dados brutos", value=False)
                sample_rate = st.selectbox(
                    "Taxa de amostragem:",
                    [100, 200, 500, 1000, 2000],
                    index=2,
                    help="Pontos máximos para gráficos",
                )

    # Conteúdo principal
    if selected_session:
        try:
            # Carregar dados IMU
            with st.spinner("Carregando dados IMU..."):
                df = imu_manager.load_imu_data(selected_session.id)

            if df is None or df.empty:
                st.error("Nenhum dado IMU encontrado para esta sessão")
                st.info(
                    """
                **Dados IMU disponíveis apenas para:**
                - Sessões com formato v2.0 (64 campos)
                - Dados extended do FuelTech
                - Campos: g_force_accel, g_force_lateral, pitch_angle, roll_angle, etc.
                """
                )
                return

            # Aplicar filtros se configurados
            if not show_raw_data and smooth_data:
                # Aplicar suavização simples
                for col in ["g_force_accel", "g_force_lateral"]:
                    if col in df.columns:
                        df[col] = df[col].rolling(window=5, center=True).mean()

            # Overview IMU
            imu_manager.render_imu_overview(df)

            st.markdown("---")

            # Visualização 3D da atitude
            imu_manager.render_3d_attitude_visualization(df)

            st.markdown("---")

            # Análise de G-forces
            imu_manager.render_g_force_analysis(df)

            st.markdown("---")

            # Análise de tração
            imu_manager.render_traction_analysis(df)

        except Exception as e:
            logger.error(f"Erro na análise IMU: {str(e)}")
            st.error(f"Erro ao processar dados IMU: {str(e)}")

            if st.session_state.get("debug_mode", False):
                st.exception(e)

    else:
        # Instruções quando nenhuma sessão está selecionada
        st.info(
            """
        **Selecione uma sessão de dados na barra lateral para análise IMU.**

        ### Recursos Disponíveis:
        - **G-Forces**: Análise de forças longitudinais e laterais
        - **Atitude 3D**: Visualização de pitch, roll e yaw
        - **Mapas de Calor**: Densidade de forças dinâmicas
        - **Controle de Tração**: Análise de slip e estabilidade
        - **Detecção de Eventos**: Aceleração, frenagem, curvas

        ### Dados Necessários (Formato v2.0):
        - **g_force_accel**: Força longitudinal (g)
        - **g_force_lateral**: Força lateral (g)
        - **pitch_angle**: Ângulo de pitch (°)
        - **roll_angle**: Ângulo de roll (°)
        - **heading**: Direção/yaw (°)
        - **traction_control_slip**: Controle de tração (%)

        ### Dica:
        Use os filtros na barra lateral para ajustar thresholds de detecção de eventos
        e configurar a suavização dos dados para melhor visualização.
        """
        )


if __name__ == "__main__":
    # Executar página IMU diretamente
    render_imu_page()
