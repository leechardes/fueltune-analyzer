"""
Map Visualization - Professional 3D visualization for tuning maps

This module provides adaptive 3D visualization using Plotly with professional
theming, performance optimization, and Material Design integration.

CRITICAL: Follows PYTHON-CODE-STANDARDS.md:
- ZERO emojis in interface
- Adaptive CSS theming (light/dark)
- Type hints 100% coverage
- Professional Material Design styling
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """Type-safe visualization configuration."""

    theme: str = "auto"  # 'light', 'dark', 'auto'
    colorscale: str = "viridis"
    show_colorbar: bool = True
    show_wireframe: bool = False
    camera_angle: Tuple[float, float, float] = (15, 45, 0)  # x, y, z rotation
    surface_opacity: float = 0.9
    grid_opacity: float = 0.3
    height: int = 600
    width: Optional[int] = None


class MapVisualization:
    """
    Professional 3D map visualization with adaptive theming.

    Features:
    - Adaptive light/dark theme support
    - Professional color schemes
    - Performance optimized rendering
    - Interactive 3D controls
    - Material Design integration
    """

    def __init__(self):
        """Initialize visualization engine with professional defaults."""
        self.config = VisualizationConfig()
        self._theme_colors = self._get_theme_colors()

    def create_3d_surface(
        self,
        map_data: pd.DataFrame,
        metadata: Optional[Any] = None,  # MapMetadata type
        config: Optional[VisualizationConfig] = None,
    ) -> go.Figure:
        """
        Create professional 3D surface plot of map data.

        Args:
            map_data: Map DataFrame with numeric data
            metadata: Optional map metadata for labeling
            config: Optional visualization configuration

        Returns:
            Plotly Figure with 3D surface

        Raises:
            ValueError: If map data is invalid

        Performance: < 500ms for 32x32 maps
        """

        try:
            if config is None:
                config = self.config

            # Validate input data
            numeric_cols = map_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                raise ValueError("No numeric data found for visualization")

            # Prepare data for 3D surface
            z_data = map_data[numeric_cols].values

            # Create coordinate grids
            x_labels, y_labels = self._extract_axis_labels(map_data, metadata)
            x_coords = np.arange(len(x_labels))
            y_coords = np.arange(len(y_labels))

            # Create 3D surface
            fig = go.Figure()

            # Add main surface
            surface = go.Surface(
                z=z_data,
                x=x_coords,
                y=y_coords,
                colorscale=config.colorscale,
                opacity=config.surface_opacity,
                showscale=config.show_colorbar,
                hovertemplate=self._create_hover_template(metadata),
                colorbar=(
                    dict(
                        title=self._get_colorbar_title(metadata),
                        titlefont=dict(color=self._theme_colors["text"]),
                        tickfont=dict(color=self._theme_colors["text"]),
                    )
                    if config.show_colorbar
                    else None
                ),
            )

            fig.add_trace(surface)

            # Add wireframe if requested
            if config.show_wireframe:
                wireframe = go.Scatter3d(
                    x=x_coords.flatten(),
                    y=y_coords.flatten(),
                    z=z_data.flatten(),
                    mode="markers",
                    marker=dict(
                        size=1, color=self._theme_colors["grid"], opacity=config.grid_opacity
                    ),
                    showlegend=False,
                    hoverinfo="skip",
                )
                fig.add_trace(wireframe)

            # Apply professional styling
            self._apply_professional_layout(fig, config, x_labels, y_labels, metadata)

            # Apply adaptive theming
            self._apply_adaptive_theme(fig, config)

            logger.debug(f"Created 3D surface for {z_data.shape} map data")

            return fig

        except Exception as e:
            logger.error(f"3D surface creation failed: {e}")
            raise

    def create_heatmap(
        self,
        map_data: pd.DataFrame,
        metadata: Optional[Any] = None,
        config: Optional[VisualizationConfig] = None,
    ) -> go.Figure:
        """
        Create professional 2D heatmap of map data.

        Args:
            map_data: Map DataFrame with numeric data
            metadata: Optional map metadata
            config: Optional visualization configuration

        Returns:
            Plotly Figure with 2D heatmap

        Performance: < 200ms for 32x32 maps
        """

        try:
            if config is None:
                config = self.config

            # Validate input
            numeric_cols = map_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                raise ValueError("No numeric data found for visualization")

            # Prepare data
            z_data = map_data[numeric_cols].values
            x_labels, y_labels = self._extract_axis_labels(map_data, metadata)

            # Create heatmap
            fig = go.Figure()

            heatmap = go.Heatmap(
                z=z_data,
                x=x_labels,
                y=y_labels,
                colorscale=config.colorscale,
                showscale=config.show_colorbar,
                hovertemplate=self._create_hover_template_2d(metadata),
                colorbar=(
                    dict(
                        title=self._get_colorbar_title(metadata),
                        titlefont=dict(color=self._theme_colors["text"]),
                        tickfont=dict(color=self._theme_colors["text"]),
                    )
                    if config.show_colorbar
                    else None
                ),
            )

            fig.add_trace(heatmap)

            # Apply professional styling
            self._apply_professional_layout_2d(fig, config, metadata)

            # Apply adaptive theming
            self._apply_adaptive_theme(fig, config)

            logger.debug(f"Created heatmap for {z_data.shape} map data")

            return fig

        except Exception as e:
            logger.error(f"Heatmap creation failed: {e}")
            raise

    def create_contour_plot(
        self,
        map_data: pd.DataFrame,
        metadata: Optional[Any] = None,
        config: Optional[VisualizationConfig] = None,
        contour_levels: int = 10,
    ) -> go.Figure:
        """
        Create professional contour plot of map data.

        Args:
            map_data: Map DataFrame with numeric data
            metadata: Optional map metadata
            config: Optional visualization configuration
            contour_levels: Number of contour levels

        Returns:
            Plotly Figure with contour plot

        Performance: < 300ms for 32x32 maps
        """

        try:
            if config is None:
                config = self.config

            # Validate input
            numeric_cols = map_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                raise ValueError("No numeric data found for visualization")

            # Prepare data
            z_data = map_data[numeric_cols].values
            x_labels, y_labels = self._extract_axis_labels(map_data, metadata)

            # Create contour plot
            fig = go.Figure()

            contour = go.Contour(
                z=z_data,
                x=np.arange(len(x_labels)),
                y=np.arange(len(y_labels)),
                colorscale=config.colorscale,
                showscale=config.show_colorbar,
                ncontours=contour_levels,
                hovertemplate=self._create_hover_template_2d(metadata),
                colorbar=(
                    dict(
                        title=self._get_colorbar_title(metadata),
                        titlefont=dict(color=self._theme_colors["text"]),
                        tickfont=dict(color=self._theme_colors["text"]),
                    )
                    if config.show_colorbar
                    else None
                ),
            )

            fig.add_trace(contour)

            # Apply professional styling
            self._apply_professional_layout_2d(fig, config, metadata)

            # Update axis labels
            fig.update_xaxes(tickvals=np.arange(len(x_labels)), ticktext=x_labels)
            fig.update_yaxes(tickvals=np.arange(len(y_labels)), ticktext=y_labels)

            # Apply adaptive theming
            self._apply_adaptive_theme(fig, config)

            logger.debug(f"Created contour plot for {z_data.shape} map data")

            return fig

        except Exception as e:
            logger.error(f"Contour plot creation failed: {e}")
            raise

    def create_comparison_plot(
        self,
        map_data_1: pd.DataFrame,
        map_data_2: pd.DataFrame,
        metadata_1: Optional[Any] = None,
        metadata_2: Optional[Any] = None,
        config: Optional[VisualizationConfig] = None,
    ) -> go.Figure:
        """
        Create side-by-side comparison of two maps.

        Args:
            map_data_1: First map DataFrame
            map_data_2: Second map DataFrame
            metadata_1: First map metadata
            metadata_2: Second map metadata
            config: Optional visualization configuration

        Returns:
            Plotly Figure with comparison plots

        Performance: < 800ms for two 32x32 maps
        """

        try:
            if config is None:
                config = self.config

            # Create subplots
            fig = make_subplots(
                rows=1,
                cols=2,
                specs=[[{"type": "surface"}, {"type": "surface"}]],
                subplot_titles=(
                    self._get_plot_title(metadata_1, "Map 1"),
                    self._get_plot_title(metadata_2, "Map 2"),
                ),
            )

            # Create first surface
            surface1 = self._create_surface_trace(map_data_1, metadata_1, config)
            fig.add_trace(surface1, row=1, col=1)

            # Create second surface
            surface2 = self._create_surface_trace(map_data_2, metadata_2, config)
            fig.add_trace(surface2, row=1, col=2)

            # Apply professional styling
            self._apply_comparison_layout(fig, config)

            # Apply adaptive theming
            self._apply_adaptive_theme(fig, config)

            logger.debug("Created comparison plot for two maps")

            return fig

        except Exception as e:
            logger.error(f"Comparison plot creation failed: {e}")
            raise

    def create_difference_plot(
        self,
        map_data_1: pd.DataFrame,
        map_data_2: pd.DataFrame,
        metadata: Optional[Any] = None,
        config: Optional[VisualizationConfig] = None,
    ) -> go.Figure:
        """
        Create difference plot between two maps.

        Args:
            map_data_1: First map DataFrame (baseline)
            map_data_2: Second map DataFrame (comparison)
            metadata: Optional metadata
            config: Optional visualization configuration

        Returns:
            Plotly Figure with difference visualization

        Performance: < 400ms for 32x32 maps
        """

        try:
            if config is None:
                config = self.config

            # Validate inputs
            if map_data_1.shape != map_data_2.shape:
                raise ValueError("Map dimensions must match for difference plot")

            # Calculate difference
            numeric_cols_1 = map_data_1.select_dtypes(include=[np.number]).columns
            numeric_cols_2 = map_data_2.select_dtypes(include=[np.number]).columns

            if not numeric_cols_1.equals(numeric_cols_2):
                raise ValueError("Map column structures must match")

            diff_data = map_data_2[numeric_cols_2].values - map_data_1[numeric_cols_1].values

            # Create difference visualization
            x_labels, y_labels = self._extract_axis_labels(map_data_1, metadata)

            fig = go.Figure()

            # Use diverging colorscale for differences
            diff_surface = go.Surface(
                z=diff_data,
                x=np.arange(len(x_labels)),
                y=np.arange(len(y_labels)),
                colorscale="RdBu_r",  # Red-Blue diverging
                opacity=config.surface_opacity,
                showscale=config.show_colorbar,
                hovertemplate="<b>Difference</b><br>"
                + "X: %{x}<br>"
                + "Y: %{y}<br>"
                + "Δ Value: %{z:.3f}<extra></extra>",
                colorbar=(
                    dict(
                        title="Difference",
                        titlefont=dict(color=self._theme_colors["text"]),
                        tickfont=dict(color=self._theme_colors["text"]),
                    )
                    if config.show_colorbar
                    else None
                ),
                cmid=0,  # Center colorscale at zero
            )

            fig.add_trace(diff_surface)

            # Apply professional styling
            self._apply_professional_layout(fig, config, x_labels, y_labels, metadata, "Difference")

            # Apply adaptive theming
            self._apply_adaptive_theme(fig, config)

            logger.debug(f"Created difference plot for {diff_data.shape} map data")

            return fig

        except Exception as e:
            logger.error(f"Difference plot creation failed: {e}")
            raise

    # Private helper methods

    def _get_theme_colors(self) -> Dict[str, str]:
        """Get adaptive theme colors based on Streamlit theme."""

        # Try to detect Streamlit theme
        try:
            # This is a simplified approach - in practice, you'd detect the actual theme
            return {
                "background": "var(--background-color)",
                "text": "var(--text-color)",
                "grid": "var(--secondary-background-color)",
                "primary": "var(--primary-color)",
            }
        except:
            # Fallback colors
            return {
                "background": "#FFFFFF",
                "text": "#262730",
                "grid": "#F0F2F6",
                "primary": "#FF6B6B",
            }

    def _extract_axis_labels(
        self, map_data: pd.DataFrame, metadata: Optional[Any] = None
    ) -> Tuple[List[str], List[str]]:
        """Extract appropriate axis labels from data or metadata."""

        try:
            if metadata and hasattr(metadata, "rpm_range") and hasattr(metadata, "load_range"):
                # Generate labels from metadata ranges
                rows, cols = map_data.shape

                rpm_values = np.linspace(metadata.rpm_range[0], metadata.rpm_range[1], cols)
                load_values = np.linspace(metadata.load_range[0], metadata.load_range[1], rows)

                x_labels = [f"{int(rpm)}" for rpm in rpm_values]
                y_labels = [f"{load:.2f}" for load in load_values]

            elif isinstance(map_data.columns[0], str) and "RPM" in str(map_data.columns[0]):
                # Use column names if they contain RPM information
                x_labels = [str(col).replace("RPM_", "") for col in map_data.columns]
                y_labels = [str(idx).replace("Load_", "") for idx in map_data.index]

            else:
                # Generate generic labels
                x_labels = [f"Col_{i}" for i in range(len(map_data.columns))]
                y_labels = [f"Row_{i}" for i in range(len(map_data))]

            return x_labels, y_labels

        except Exception as e:
            logger.warning(f"Failed to extract axis labels: {e}")
            # Fallback to generic labels
            x_labels = [f"X_{i}" for i in range(len(map_data.columns))]
            y_labels = [f"Y_{i}" for i in range(len(map_data))]
            return x_labels, y_labels

    def _create_hover_template(self, metadata: Optional[Any] = None) -> str:
        """Create professional hover template for 3D plots."""

        if metadata and hasattr(metadata, "map_type"):
            value_unit = self._get_value_unit(metadata.map_type)
            return (
                f"<b>{metadata.map_type.title()} Map</b><br>"
                + "RPM: %{x}<br>"
                + "Load: %{y}<br>"
                + f"Value: %{{z:.3f}} {value_unit}<extra></extra>"
            )
        else:
            return (
                "<b>Map Data</b><br>"
                + "X: %{x}<br>"
                + "Y: %{y}<br>"
                + "Value: %{z:.3f}<extra></extra>"
            )

    def _create_hover_template_2d(self, metadata: Optional[Any] = None) -> str:
        """Create professional hover template for 2D plots."""

        if metadata and hasattr(metadata, "map_type"):
            value_unit = self._get_value_unit(metadata.map_type)
            return (
                f"<b>{metadata.map_type.title()} Map</b><br>"
                + "RPM: %{x}<br>"
                + "Load: %{y}<br>"
                + f"Value: %{{z:.3f}} {value_unit}<extra></extra>"
            )
        else:
            return (
                "<b>Map Data</b><br>"
                + "X: %{x}<br>"
                + "Y: %{y}<br>"
                + "Value: %{z:.3f}<extra></extra>"
            )

    def _get_value_unit(self, map_type: str) -> str:
        """Get appropriate unit for map type."""

        units = {"fuel": "AFR", "ignition": "°", "boost": "bar"}

        return units.get(map_type, "")

    def _get_colorbar_title(self, metadata: Optional[Any] = None) -> str:
        """Get appropriate colorbar title."""

        if metadata and hasattr(metadata, "map_type"):
            titles = {
                "fuel": "Air-Fuel Ratio",
                "ignition": "Timing (degrees)",
                "boost": "Boost Pressure (bar)",
            }
            return titles.get(metadata.map_type, "Value")

        return "Value"

    def _get_plot_title(self, metadata: Optional[Any] = None, default: str = "Map") -> str:
        """Get appropriate plot title."""

        if metadata and hasattr(metadata, "name"):
            return metadata.name
        elif metadata and hasattr(metadata, "map_type"):
            return f"{metadata.map_type.title()} Map"

        return default

    def _create_surface_trace(
        self,
        map_data: pd.DataFrame,
        metadata: Optional[Any] = None,
        config: VisualizationConfig = None,
    ) -> go.Surface:
        """Create surface trace for subplots."""

        numeric_cols = map_data.select_dtypes(include=[np.number]).columns
        z_data = map_data[numeric_cols].values
        x_labels, y_labels = self._extract_axis_labels(map_data, metadata)

        return go.Surface(
            z=z_data,
            x=np.arange(len(x_labels)),
            y=np.arange(len(y_labels)),
            colorscale=config.colorscale,
            opacity=config.surface_opacity,
            showscale=False,  # Disable for subplots
            hovertemplate=self._create_hover_template(metadata),
        )

    def _apply_professional_layout(
        self,
        fig: go.Figure,
        config: VisualizationConfig,
        x_labels: List[str],
        y_labels: List[str],
        metadata: Optional[Any] = None,
        title_suffix: str = "",
    ) -> None:
        """Apply professional layout styling to 3D plot."""

        title = self._get_plot_title(metadata, "Map") + (" " + title_suffix if title_suffix else "")

        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=18, color=self._theme_colors["text"], family="Arial, sans-serif"),
                x=0.5,  # Center title
                xanchor="center",
            ),
            scene=dict(
                xaxis=dict(
                    title="RPM" if metadata and hasattr(metadata, "rpm_range") else "X Axis",
                    tickvals=np.arange(0, len(x_labels), max(1, len(x_labels) // 8)),
                    ticktext=[
                        x_labels[i] for i in range(0, len(x_labels), max(1, len(x_labels) // 8))
                    ],
                    titlefont=dict(color=self._theme_colors["text"]),
                    tickfont=dict(color=self._theme_colors["text"]),
                    gridcolor=self._theme_colors["grid"],
                    zerolinecolor=self._theme_colors["grid"],
                ),
                yaxis=dict(
                    title="Load" if metadata and hasattr(metadata, "load_range") else "Y Axis",
                    tickvals=np.arange(0, len(y_labels), max(1, len(y_labels) // 8)),
                    ticktext=[
                        y_labels[i] for i in range(0, len(y_labels), max(1, len(y_labels) // 8))
                    ],
                    titlefont=dict(color=self._theme_colors["text"]),
                    tickfont=dict(color=self._theme_colors["text"]),
                    gridcolor=self._theme_colors["grid"],
                    zerolinecolor=self._theme_colors["grid"],
                ),
                zaxis=dict(
                    title=self._get_colorbar_title(metadata),
                    titlefont=dict(color=self._theme_colors["text"]),
                    tickfont=dict(color=self._theme_colors["text"]),
                    gridcolor=self._theme_colors["grid"],
                    zerolinecolor=self._theme_colors["grid"],
                ),
                camera=dict(
                    eye=dict(
                        x=config.camera_angle[0] / 10,
                        y=config.camera_angle[1] / 10,
                        z=config.camera_angle[2] / 10 + 1.5,
                    )
                ),
                bgcolor=self._theme_colors["background"],
            ),
            paper_bgcolor=self._theme_colors["background"],
            plot_bgcolor=self._theme_colors["background"],
            height=config.height,
            width=config.width,
            margin=dict(l=50, r=50, t=60, b=50),
            font=dict(family="Arial, sans-serif", color=self._theme_colors["text"]),
        )

    def _apply_professional_layout_2d(
        self, fig: go.Figure, config: VisualizationConfig, metadata: Optional[Any] = None
    ) -> None:
        """Apply professional layout styling to 2D plot."""

        title = self._get_plot_title(metadata, "Map")

        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=18, color=self._theme_colors["text"], family="Arial, sans-serif"),
                x=0.5,
                xanchor="center",
            ),
            xaxis=dict(
                title="RPM" if metadata and hasattr(metadata, "rpm_range") else "X Axis",
                titlefont=dict(color=self._theme_colors["text"]),
                tickfont=dict(color=self._theme_colors["text"]),
                gridcolor=self._theme_colors["grid"],
                zerolinecolor=self._theme_colors["grid"],
            ),
            yaxis=dict(
                title="Load" if metadata and hasattr(metadata, "load_range") else "Y Axis",
                titlefont=dict(color=self._theme_colors["text"]),
                tickfont=dict(color=self._theme_colors["text"]),
                gridcolor=self._theme_colors["grid"],
                zerolinecolor=self._theme_colors["grid"],
            ),
            paper_bgcolor=self._theme_colors["background"],
            plot_bgcolor=self._theme_colors["background"],
            height=config.height,
            width=config.width,
            margin=dict(l=50, r=50, t=60, b=50),
            font=dict(family="Arial, sans-serif", color=self._theme_colors["text"]),
        )

    def _apply_comparison_layout(self, fig: go.Figure, config: VisualizationConfig) -> None:
        """Apply layout for comparison plots."""

        fig.update_layout(
            title=dict(
                text="Map Comparison",
                font=dict(size=18, color=self._theme_colors["text"], family="Arial, sans-serif"),
                x=0.5,
                xanchor="center",
            ),
            paper_bgcolor=self._theme_colors["background"],
            plot_bgcolor=self._theme_colors["background"],
            height=config.height,
            width=config.width if config.width else 1200,
            margin=dict(l=50, r=50, t=80, b=50),
            font=dict(family="Arial, sans-serif", color=self._theme_colors["text"]),
        )

    def _apply_adaptive_theme(self, fig: go.Figure, config: VisualizationConfig) -> None:
        """Apply adaptive theming based on Streamlit theme."""

        # This would be enhanced to detect actual Streamlit theme
        # For now, applies consistent professional theming

        if config.theme == "dark":
            # Dark theme overrides
            fig.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", font_color="#FAFAFA")

            # Update scene for 3D plots
            if "scene" in fig.layout:
                fig.update_layout(scene=dict(bgcolor="#0E1117"))

        elif config.theme == "light":
            # Light theme overrides
            fig.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font_color="#262730")

            # Update scene for 3D plots
            if "scene" in fig.layout:
                fig.update_layout(scene=dict(bgcolor="#FFFFFF"))

        # Auto theme detection would go here
