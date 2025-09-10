"""
Metric Card Component para FuelTune Analyzer.

Componente reutilizável para exibir métricas com valores e indicadores visuais.
Suporte a dark mode, tooltips e animações.

Author: A03-UI-STREAMLIT Agent
Created: 2025-01-02
"""

from dataclasses import dataclass
from typing import Literal, Optional, Union

import plotly.graph_objects as go
import streamlit as st


@dataclass
class MetricData:
    """Estrutura de dados para métricas."""

    value: Union[int, float, str]
    label: str
    unit: str = ""
    delta: Optional[float] = None
    delta_color: Literal["normal", "inverse"] = "normal"
    format: Optional[str] = None
    help_text: Optional[str] = None


class MetricCard:
    """
    Componente de card de métricas reutilizável.

    Características:
    - Suporte a valores numéricos e texto
    - Indicadores de variação (delta)
    - Tooltips informativos
    - Formatação customizada
    - Suporte a temas
    """

    def __init__(
        self,
        width: str = "100%",
        height: str = "auto",
        border_radius: str = "0.5rem",
        theme: Literal["light", "dark", "auto"] = "auto",
    ):
        """
        Inicializar componente de metric card.

        Args:
            width: Largura do card
            height: Altura do card
            border_radius: Raio da borda
            theme: Tema do card (light/dark/auto)
        """
        self.width = width
        self.height = height
        self.border_radius = border_radius
        self.theme = theme

    def render_single(self, metric: MetricData, container: Optional[st.container] = None) -> None:
        """
        Renderizar um único card de métrica.

        Args:
            metric: Dados da métrica
            container: Container específico (opcional)
        """
        target_container = container or st.container()

        with target_container:
            # Aplicar formatação se especificada
            formatted_value = self._format_value(metric.value, metric.format)

            # Renderizar métrica com Streamlit nativo
            st.metric(
                label=metric.label,
                value=f"{formatted_value} {metric.unit}".strip(),
                delta=metric.delta if metric.delta is not None else None,
                delta_color=metric.delta_color,
                help=metric.help_text,
            )

    def render_row(self, metrics: list[MetricData], columns: Optional[int] = None) -> None:
        """
        Renderizar uma linha de cards de métricas.

        Args:
            metrics: Lista de métricas
            columns: Número de colunas (auto se None)
        """
        if not metrics:
            return

        num_cols = columns or len(metrics)
        cols = st.columns(num_cols)

        for idx, metric in enumerate(metrics):
            if idx < len(cols):
                with cols[idx]:
                    self.render_single(metric)

    def render_grid(self, metrics: list[list[MetricData]], equal_width: bool = True) -> None:
        """
        Renderizar uma grade de cards de métricas.

        Args:
            metrics: Lista de listas de métricas (linhas x colunas)
            equal_width: Se as colunas devem ter largura igual
        """
        for row in metrics:
            if equal_width:
                self.render_row(row)
            else:
                # Larguras proporcionais baseadas no número de métricas
                cols = st.columns(len(row))
                for idx, metric in enumerate(row):
                    with cols[idx]:
                        self.render_single(metric)

    def render_comparison(
        self,
        current: MetricData,
        previous: MetricData,
        comparison_label: str = "vs Anterior",
    ) -> None:
        """
        Renderizar comparação entre duas métricas.

        Args:
            current: Métrica atual
            previous: Métrica anterior
            comparison_label: Label da comparação
        """
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**{current.label} - Atual**")
            self.render_single(current)

        with col2:
            st.markdown(f"**{previous.label} - {comparison_label}**")
            self.render_single(previous)

        # Calcular diferença se ambos são numéricos
        if isinstance(current.value, (int, float)) and isinstance(previous.value, (int, float)):
            diff = current.value - previous.value
            diff_pct = (diff / previous.value * 100) if previous.value != 0 else 0

            st.markdown(
                f"""
            **Diferença**: {diff:+.2f} {current.unit} ({diff_pct:+.1f}%)
            """
            )

    def render_sparkline(
        self,
        metric: MetricData,
        trend_data: list[float],
        trend_label: str = "Tendência",
    ) -> None:
        """
        Renderizar métrica com mini gráfico de tendência.

        Args:
            metric: Dados da métrica
            trend_data: Dados da tendência
            trend_label: Label da tendência
        """
        col1, col2 = st.columns([2, 1])

        with col1:
            self.render_single(metric)

        with col2:
            if trend_data and len(trend_data) > 1:
                # Criar sparkline simples
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        y=trend_data,
                        mode="lines",
                        line=dict(width=2, color="#1f77b4"),
                        showlegend=False,
                    )
                )

                fig.update_layout(
                    height=80,
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )

                st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
            else:
                st.markdown(f"*{trend_label} indisponível*")

    def render_gauge(
        self,
        metric: MetricData,
        min_value: float,
        max_value: float,
        target_value: Optional[float] = None,
        danger_zones: Optional[list[tuple[float, float]]] = None,
    ) -> None:
        """
        Renderizar métrica como gauge/medidor.

        Args:
            metric: Dados da métrica
            min_value: Valor mínimo
            max_value: Valor máximo
            target_value: Valor alvo (opcional)
            danger_zones: Zonas de perigo [(min, max), ...]
        """
        if not isinstance(metric.value, (int, float)):
            st.error("Gauge requer valor numérico")
            return

        # Criar gauge
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=float(metric.value),
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": metric.label},
                delta={
                    "reference": (target_value if target_value else (max_value + min_value) / 2)
                },
                gauge={
                    "axis": {"range": [min_value, max_value]},
                    "bar": {"color": "darkblue"},
                    "steps": [{"range": [min_value, max_value], "color": "lightgray"}],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": target_value if target_value else max_value,
                    },
                },
            )
        )

        # Adicionar zonas de perigo
        if danger_zones:
            for danger_min, danger_max in danger_zones:
                fig.add_shape(
                    type="rect",
                    x0=0,
                    x1=1,
                    y0=danger_min,
                    y1=danger_max,
                    fillcolor="red",
                    opacity=0.2,
                    layer="below",
                    line_width=0,
                )

        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, width='stretch')

    def _format_value(self, value: Union[int, float, str], format_str: Optional[str]) -> str:
        """
        Formatar valor de acordo com especificação.

        Args:
            value: Valor a ser formatado
            format_str: String de formatação (ex: '.2f', '.0f', etc.)

        Returns:
            Valor formatado como string
        """
        if format_str is None:
            return str(value)

        if isinstance(value, (int, float)):
            try:
                return f"{value:{format_str}}"
            except (ValueError, TypeError):
                return str(value)

        return str(value)


# Funções utilitárias para criação rápida de métricas
def create_engine_metrics(
    rpm: int, throttle: float, temp: float, lambda_val: float
) -> list[MetricData]:
    """Criar métricas básicas do motor."""
    return [
        MetricData(value=rpm, label="RPM", format=".0f"),
        MetricData(value=throttle, label="TPS", unit="%", format=".1f"),
        MetricData(value=temp, label="Temp Motor", unit="°C", format=".1f"),
        MetricData(value=lambda_val, label="Lambda", format=".3f"),
    ]


def create_fuel_metrics(flow: float, pressure: float, injection_time: float) -> list[MetricData]:
    """Criar métricas do sistema de combustível."""
    return [
        MetricData(value=flow, label="Fluxo", unit="L/h", format=".2f"),
        MetricData(value=pressure, label="Pressão", unit="bar", format=".2f"),
        MetricData(value=injection_time, label="Tempo Inj.", unit="ms", format=".2f"),
    ]


def create_performance_metrics(power: int, torque: int, efficiency: float) -> list[MetricData]:
    """Criar métricas de performance."""
    return [
        MetricData(value=power * 1.01387, label="Potência", unit="CV", format=".0f"),
        MetricData(value=torque, label="Torque", unit="Nm", format=".0f"),
        MetricData(value=efficiency, label="Eficiência", unit="%", format=".1f"),
    ]


if __name__ == "__main__":
    # Exemplo de uso
    card = MetricCard()

    # Teste métrica simples
    test_metric = MetricData(
        value=3500, label="RPM", delta=150, help_text="Rotações por minuto do motor"
    )

    card.render_single(test_metric)
