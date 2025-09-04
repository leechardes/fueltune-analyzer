"""
Chart Builder Component para FuelTune Analyzer.

Builder de gráficos padronizado usando Plotly com suporte a:
- Múltiplos tipos de gráfico
- Themes responsivos
- Interatividade avançada
- Export automático

Author: A03-UI-STREAMLIT Agent
Created: 2025-01-02
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


@dataclass
class ChartConfig:
    """Configuração para gráficos."""

    title: str
    x_label: str = ""
    y_label: str = ""
    theme: Literal["plotly", "plotly_white", "plotly_dark", "presentation"] = "plotly_white"
    height: int = 400
    width: Optional[int] = None
    show_legend: bool = True
    show_grid: bool = True
    animation: bool = False


@dataclass
class SeriesData:
    """Dados de uma série para gráfico."""

    x: List[Union[int, float, str]]
    y: List[Union[int, float]]
    name: str
    color: Optional[str] = None
    line_width: int = 2
    marker_size: int = 6
    opacity: float = 1.0
    secondary_y: bool = False


class ChartBuilder:
    """
    Builder de gráficos padronizado para FuelTune Analyzer.

    Características:
    - Suporte a múltiplos tipos de gráfico
    - Configuração padronizada
    - Themes responsivos
    - Interatividade avançada
    - Export automático
    """

    def __init__(self, config: ChartConfig):
        """
        Inicializar chart builder.

        Args:
            config: Configuração do gráfico
        """
        self.config = config
        self.fig = None

    def create_line_chart(
        self,
        series_data: List[SeriesData],
        smooth_lines: bool = False,
        fill_area: bool = False,
    ) -> go.Figure:
        """
        Criar gráfico de linhas.

        Args:
            series_data: Lista de séries de dados
            smooth_lines: Se as linhas devem ser suavizadas
            fill_area: Se deve preencher área sob a curva

        Returns:
            Figura do Plotly
        """
        # Verificar se há séries com eixo Y secundário
        has_secondary = any(s.secondary_y for s in series_data)

        if has_secondary:
            self.fig = make_subplots(specs=[[{"secondary_y": True}]])
        else:
            self.fig = go.Figure()

        for series in series_data:
            line_shape = "spline" if smooth_lines else "linear"
            fill_mode = "tonexty" if fill_area else None

            trace = go.Scatter(
                x=series.x,
                y=series.y,
                name=series.name,
                line=dict(color=series.color, width=series.line_width, shape=line_shape),
                marker=dict(size=series.marker_size),
                opacity=series.opacity,
                fill=fill_mode,
            )

            if has_secondary and series.secondary_y:
                self.fig.add_trace(trace, secondary_y=True)
            else:
                self.fig.add_trace(trace)

        self._apply_layout()
        return self.fig

    def create_scatter_chart(
        self,
        series_data: List[SeriesData],
        trendline: bool = False,
        bubble_size: Optional[List[float]] = None,
    ) -> go.Figure:
        """
        Criar gráfico de dispersão.

        Args:
            series_data: Lista de séries de dados
            trendline: Se deve mostrar linha de tendência
            bubble_size: Tamanhos dos pontos (para bubble chart)

        Returns:
            Figura do Plotly
        """
        self.fig = go.Figure()

        for i, series in enumerate(series_data):
            sizes = bubble_size if bubble_size else [series.marker_size] * len(series.x)

            self.fig.add_trace(
                go.Scatter(
                    x=series.x,
                    y=series.y,
                    name=series.name,
                    mode="markers",
                    marker=dict(
                        color=series.color,
                        size=sizes,
                        opacity=series.opacity,
                        line=dict(width=1, color="white"),
                    ),
                )
            )

            # Adicionar linha de tendência
            if trendline and len(series.x) > 1:
                z = np.polyfit(series.x, series.y, 1)
                p = np.poly1d(z)
                trend_x = [min(series.x), max(series.x)]
                trend_y = [p(x) for x in trend_x]

                self.fig.add_trace(
                    go.Scatter(
                        x=trend_x,
                        y=trend_y,
                        name=f"Tendência {series.name}",
                        line=dict(dash="dash", color=series.color),
                        showlegend=False,
                    )
                )

        self._apply_layout()
        return self.fig

    def create_bar_chart(
        self,
        categories: List[str],
        values: List[List[float]],
        series_names: List[str],
        orientation: Literal["vertical", "horizontal"] = "vertical",
        stacked: bool = False,
    ) -> go.Figure:
        """
        Criar gráfico de barras.

        Args:
            categories: Categorias do eixo X
            values: Valores para cada série
            series_names: Nomes das séries
            orientation: Orientação das barras
            stacked: Se as barras devem ser empilhadas

        Returns:
            Figura do Plotly
        """
        self.fig = go.Figure()

        colors = px.colors.qualitative.Set3

        for i, (vals, name) in enumerate(zip(values, series_names)):
            if orientation == "horizontal":
                trace = go.Bar(
                    y=categories,
                    x=vals,
                    name=name,
                    marker_color=colors[i % len(colors)],
                    orientation="h",
                )
            else:
                trace = go.Bar(
                    x=categories,
                    y=vals,
                    name=name,
                    marker_color=colors[i % len(colors)],
                )

            self.fig.add_trace(trace)

        if stacked:
            self.fig.update_layout(barmode="stack")
        else:
            self.fig.update_layout(barmode="group")

        self._apply_layout()
        return self.fig

    def create_heatmap(
        self,
        z_values: List[List[float]],
        x_labels: Optional[List[str]] = None,
        y_labels: Optional[List[str]] = None,
        colorscale: str = "RdYlBu_r",
        show_values: bool = True,
    ) -> go.Figure:
        """
        Criar mapa de calor.

        Args:
            z_values: Matriz de valores
            x_labels: Labels do eixo X
            y_labels: Labels do eixo Y
            colorscale: Escala de cores
            show_values: Se deve mostrar valores nas células

        Returns:
            Figura do Plotly
        """
        self.fig = go.Figure(
            data=go.Heatmap(
                z=z_values,
                x=x_labels,
                y=y_labels,
                colorscale=colorscale,
                text=z_values if show_values else None,
                texttemplate="%{text:.2f}" if show_values else None,
                textfont={"size": 10},
                hoverongaps=False,
            )
        )

        self._apply_layout()
        return self.fig

    def create_3d_scatter(
        self,
        x: List[float],
        y: List[float],
        z: List[float],
        colors: Optional[List[float]] = None,
        sizes: Optional[List[float]] = None,
        labels: Optional[List[str]] = None,
    ) -> go.Figure:
        """
        Criar gráfico de dispersão 3D.

        Args:
            x: Valores do eixo X
            y: Valores do eixo Y
            z: Valores do eixo Z
            colors: Valores para colorir pontos
            sizes: Tamanhos dos pontos
            labels: Labels dos pontos

        Returns:
            Figura do Plotly
        """
        self.fig = go.Figure(
            data=[
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="markers",
                    marker=dict(
                        size=sizes if sizes else 5,
                        color=colors if colors else "blue",
                        colorscale="Viridis" if colors else None,
                        opacity=0.8,
                        showscale=True if colors else False,
                    ),
                    text=labels,
                    hovertemplate="X: %{x}<br>Y: %{y}<br>Z: %{z}<br>%{text}<extra></extra>",
                )
            ]
        )

        self.fig.update_layout(
            scene=dict(
                xaxis_title=self.config.x_label,
                yaxis_title=self.config.y_label,
                zaxis_title="Z",
            )
        )

        self._apply_layout()
        return self.fig

    def create_gauge_chart(
        self,
        value: float,
        min_value: float = 0,
        max_value: float = 100,
        target: Optional[float] = None,
        color_ranges: Optional[List[Tuple[float, float, str]]] = None,
    ) -> go.Figure:
        """
        Criar gráfico de gauge/medidor.

        Args:
            value: Valor atual
            min_value: Valor mínimo
            max_value: Valor máximo
            target: Valor alvo
            color_ranges: Lista de (min, max, cor) para zonas coloridas

        Returns:
            Figura do Plotly
        """
        steps = []
        if color_ranges:
            for min_val, max_val, color in color_ranges:
                steps.append({"range": [min_val, max_val], "color": color})
        else:
            steps = [{"range": [min_value, max_value], "color": "lightgray"}]

        self.fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=value,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": self.config.title},
                delta={"reference": target} if target else None,
                gauge={
                    "axis": {"range": [min_value, max_value]},
                    "bar": {"color": "darkblue"},
                    "steps": steps,
                    "threshold": (
                        {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": target,
                        }
                        if target
                        else None
                    ),
                },
            )
        )

        self._apply_layout()
        return self.fig

    def create_multi_axis_chart(
        self, primary_series: List[SeriesData], secondary_series: List[SeriesData]
    ) -> go.Figure:
        """
        Criar gráfico com múltiplos eixos Y.

        Args:
            primary_series: Séries para eixo Y primário
            secondary_series: Séries para eixo Y secundário

        Returns:
            Figura do Plotly
        """
        self.fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Adicionar séries primárias
        for series in primary_series:
            self.fig.add_trace(
                go.Scatter(
                    x=series.x,
                    y=series.y,
                    name=series.name,
                    line=dict(color=series.color, width=series.line_width),
                ),
                secondary_y=False,
            )

        # Adicionar séries secundárias
        for series in secondary_series:
            self.fig.add_trace(
                go.Scatter(
                    x=series.x,
                    y=series.y,
                    name=series.name,
                    line=dict(color=series.color, width=series.line_width),
                ),
                secondary_y=True,
            )

        # Configurar títulos dos eixos
        self.fig.update_xaxes(title_text=self.config.x_label)
        self.fig.update_yaxes(title_text="Primário", secondary_y=False)
        self.fig.update_yaxes(title_text="Secundário", secondary_y=True)

        self._apply_layout()
        return self.fig

    def add_annotations(self, annotations: List[Dict[str, Any]]) -> None:
        """
        Adicionar anotações ao gráfico.

        Args:
            annotations: Lista de anotações com configurações
        """
        if self.fig:
            for annotation in annotations:
                self.fig.add_annotation(**annotation)

    def add_shapes(self, shapes: List[Dict[str, Any]]) -> None:
        """
        Adicionar formas ao gráfico.

        Args:
            shapes: Lista de formas com configurações
        """
        if self.fig:
            for shape in shapes:
                self.fig.add_shape(**shape)

    def _apply_layout(self) -> None:
        """Aplicar layout padronizado ao gráfico."""
        if not self.fig:
            return

        self.fig.update_layout(
            title=dict(
                text=self.config.title,
                x=0.5,
                xanchor="center",
                font=dict(size=16, family="Arial, sans-serif"),
            ),
            xaxis_title=self.config.x_label,
            yaxis_title=self.config.y_label,
            height=self.config.height,
            width=self.config.width,
            template=self.config.theme,
            showlegend=self.config.show_legend,
            hovermode="x unified",
            margin=dict(l=60, r=60, t=60, b=60),
        )

        # Configurar grid
        if self.config.show_grid:
            self.fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
            self.fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
        else:
            self.fig.update_xaxes(showgrid=False)
            self.fig.update_yaxes(showgrid=False)

    def render(
        self,
        key: Optional[str] = None,
        use_container_width: bool = True,
        config: Optional[Dict] = None,
    ) -> None:
        """
        Renderizar gráfico no Streamlit.

        Args:
            key: Chave única para o componente
            use_container_width: Se deve usar largura do container
            config: Configurações do plotly
        """
        if not self.fig:
            st.error("Nenhum gráfico foi criado. Use um dos métodos create_* primeiro.")
            return

        plot_config = config or {
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
        }

        st.plotly_chart(
            self.fig,
            use_container_width=use_container_width,
            key=key,
            config=plot_config,
        )

    def export_html(self, filename: str) -> None:
        """
        Exportar gráfico como HTML.

        Args:
            filename: Nome do arquivo
        """
        if self.fig:
            self.fig.write_html(filename)


# Funções utilitárias para tipos comuns de gráficos FuelTech
def create_rpm_vs_time_chart(
    time_data: List[float], rpm_data: List[int], title: str = "RPM vs Tempo"
) -> ChartBuilder:
    """Criar gráfico padrão RPM vs Tempo."""
    config = ChartConfig(title=title, x_label="Tempo (s)", y_label="RPM", height=300)

    builder = ChartBuilder(config)
    series = [SeriesData(x=time_data, y=rpm_data, name="RPM", color="#1f77b4")]

    builder.create_line_chart(series)
    return builder


def create_lambda_chart(
    time_data: List[float], lambda_data: List[float], target_lambda: float = 0.85
) -> ChartBuilder:
    """Criar gráfico de Lambda com linha de target."""
    config = ChartConfig(
        title="Lambda Sensor", x_label="Tempo (s)", y_label="Lambda (λ)", height=300
    )

    builder = ChartBuilder(config)
    series = [SeriesData(x=time_data, y=lambda_data, name="Lambda", color="#ff7f0e")]

    builder.create_line_chart(series)

    # Adicionar linha de target
    builder.add_shapes(
        [
            {
                "type": "line",
                "x0": min(time_data),
                "x1": max(time_data),
                "y0": target_lambda,
                "y1": target_lambda,
                "line": dict(color="red", dash="dash", width=2),
            }
        ]
    )

    return builder


def create_map_vs_rpm_chart(rpm_data: List[int], map_data: List[float]) -> ChartBuilder:
    """Criar gráfico MAP vs RPM (scatter)."""
    config = ChartConfig(title="MAP vs RPM", x_label="RPM", y_label="MAP (bar)", height=400)

    builder = ChartBuilder(config)
    series = [SeriesData(x=rpm_data, y=map_data, name="MAP", color="#2ca02c")]

    builder.create_scatter_chart(series, trendline=True)
    return builder


if __name__ == "__main__":
    # Exemplo de uso
    import numpy as np

    # Dados de exemplo
    time_data = list(range(100))
    rpm_data = [3000 + 1000 * np.sin(i * 0.1) for i in range(100)]

    # Criar gráfico
    chart = create_rpm_vs_time_chart(time_data, rpm_data)
    chart.render()
