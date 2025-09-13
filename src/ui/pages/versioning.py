"""
Versioning System - Interface de Versionamento de Mapas FuelTech

Este módulo fornece interface completa para gerenciamento de versões,
comparação visual A/B, diff entre versões e funcionalidade de rollback.

Features:
- Histórico visual de snapshots
- Comparação lado a lado A/B
- Diff colorido entre versões
- Interface de rollback
- Timeline de mudanças
- Gerenciamento de storage

CRITICAL: Segue PYTHON-CODE-STANDARDS.md:
- ZERO emojis na interface (apenas Material Icons)
- CSS adaptativo (suporte light/dark)
- Type hints 100% de cobertura
- Performance < 1s para operações
- Interface profissional padronizada

Author: IMPLEMENT-VERSIONING-SYSTEM Agent
Created: 2025-01-04
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Imports para snapshot system
try:
    # Importação relativa (quando chamado como módulo)
    from ...data.database import get_database
    from ...maps.snapshots import MapSnapshots, SnapshotMetadata
    from ...utils.logging_config import get_logger
except ImportError:
    # Fallback para importação absoluta (quando executado via st.navigation)
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.data.database import get_database
    from src.maps.snapshots import MapSnapshots, SnapshotMetadata
    from src.utils.logging_config import get_logger

logger = get_logger("versioning_page")

# CSS Profissional para Versioning
VERSIONING_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">
<style>
    .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        vertical-align: middle;
        margin-right: 8px;
    }
    
    /* Versioning Professional Styling */
    .versioning-container {
        background: var(--background-color);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
        margin-bottom: 1rem;
    }
    
    .snapshot-card {
        background: var(--secondary-background-color);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border-left: 4px solid var(--primary-color);
        transition: all 0.3s ease;
    }
    
    .snapshot-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    
    .snapshot-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .snapshot-meta {
        display: flex;
        gap: 1rem;
        font-size: 0.85rem;
        color: var(--text-color-secondary);
    }
    
    .version-badge {
        background: var(--primary-color);
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .diff-positive {
        background: rgba(76, 175, 80, 0.1);
        color: #4CAF50;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .diff-negative {
        background: rgba(244, 67, 54, 0.1);
        color: #f44336;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .diff-neutral {
        background: rgba(158, 158, 158, 0.1);
        color: #9E9E9E;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .timeline-item {
        position: relative;
        padding-left: 2rem;
        padding-bottom: 1.5rem;
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        left: 0.5rem;
        top: 0.5rem;
        width: 0.75rem;
        height: 0.75rem;
        background: var(--primary-color);
        border-radius: 50%;
        border: 3px solid var(--background-color);
    }
    
    .timeline-line {
        position: absolute;
        left: 0.875rem;
        top: 1.25rem;
        bottom: 0;
        width: 2px;
        background: var(--border-color);
    }
    
    .comparison-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .comparison-panel {
        background: var(--secondary-background-color);
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid var(--border-color);
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .stat-card {
        background: var(--secondary-background-color);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid var(--border-color);
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 600;
        color: var(--primary-color);
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: var(--text-color-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .action-button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .action-button:hover {
        background: var(--primary-color-dark);
        transform: translateY(-1px);
    }
    
    .danger-button {
        background: #f44336;
    }
    
    .danger-button:hover {
        background: #d32f2f;
    }
    
    .success-button {
        background: #4CAF50;
    }
    
    .success-button:hover {
        background: #388E3C;
    }
</style>
"""


class VersioningPage:
    """Interface completa para versionamento de mapas."""

    def __init__(self):
        """Inicializar sistema de versionamento."""
        self.snapshots = MapSnapshots()
        self.db = get_database()

        # Initialize session state
        self._initialize_session_state()

        logger.info("Versioning system initialized")

    def _initialize_session_state(self) -> None:
        """Inicializar estado da sessão."""
        if "selected_snapshot_a" not in st.session_state:
            st.session_state.selected_snapshot_a = None

        if "selected_snapshot_b" not in st.session_state:
            st.session_state.selected_snapshot_b = None

        if "comparison_data" not in st.session_state:
            st.session_state.comparison_data = None

    def render(self) -> None:
        """Renderizar interface principal de versionamento."""

        # Load professional CSS
        st.markdown(VERSIONING_CSS, unsafe_allow_html=True)

        # Page header
        st.markdown(
            """
        <div style="display: flex; align-items: center; margin-bottom: 2rem;">
            <span class="material-symbols-outlined" style="font-size: 2rem; color: var(--primary-color);">history</span>
            <div>
                <h1 style="margin: 0; color: var(--text-color);">Sistema de Versionamento</h1>
                <p style="margin: 0; color: var(--text-color-secondary);">
                    Gerenciamento, comparação e rollback de versões de mapas
                </p>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                ":material/history: Histórico",
                ":material/compare: Comparação A/B",
                ":material/analytics: Timeline",
                ":material/settings: Gerenciar Storage",
            ]
        )

        with tab1:
            self._render_snapshot_history()

        with tab2:
            self._render_ab_comparison()

        with tab3:
            self._render_timeline()

        with tab4:
            self._render_storage_management()

    def _render_snapshot_history(self) -> None:
        """Renderizar histórico de snapshots."""

        st.markdown("### Histórico de Snapshots")

        # Filters
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            map_name_filter = st.selectbox(
                "Filtrar por mapa:",
                options=["Todos"] + self._get_available_maps(),
                key="map_filter",
            )

        with col2:
            map_type_filter = st.selectbox(
                "Tipo de mapa:", options=["Todos", "fuel", "ignition", "boost"], key="type_filter"
            )

        with col3:
            limit = st.number_input(
                "Limite:", min_value=10, max_value=100, value=25, key="history_limit"
            )

        # Get filtered snapshots
        try:
            snapshots = self._get_filtered_snapshots(map_name_filter, map_type_filter, limit)

            if not snapshots:
                st.info(
                    "Nenhum snapshot encontrado. "
                    "Snapshots são criados automaticamente quando mapas são salvos."
                )
                return

            # Render snapshots
            for snapshot in snapshots:
                self._render_snapshot_card(snapshot)

        except Exception as e:
            logger.error(f"Error loading snapshot history: {e}")
            st.error("Erro ao carregar histórico de snapshots.")

    def _render_snapshot_card(self, snapshot: SnapshotMetadata) -> None:
        """Renderizar card individual de snapshot."""

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(
                f"""
            <div class="snapshot-card">
                <div class="snapshot-header">
                    <div>
                        <strong>{snapshot.map_name}</strong>
                        <span class="version-badge">v{snapshot.version}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-color-secondary);">
                        {snapshot.created_at.strftime('%d/%m/%Y %H:%M')}
                    </div>
                </div>
                <div class="snapshot-meta">
                    <span>
                        <span class="material-symbols-outlined" style="font-size: 1rem;">map</span>
                        {snapshot.map_type.title()}
                    </span>
                    <span>
                        <span class="material-symbols-outlined" style="font-size: 1rem;">person</span>
                        {snapshot.created_by}
                    </span>
                    <span>
                        <span class="material-symbols-outlined" style="font-size: 1rem;">storage</span>
                        {self._format_file_size(snapshot.file_size)}
                    </span>
                </div>
                {f'<div style="margin-top: 0.5rem; font-style: italic;">{snapshot.description}</div>' if snapshot.description else ''}
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            if st.button(
                "Visualizar",
                key=f"view_{snapshot.snapshot_id}",
                type="secondary",
                use_container_width=True,
            ):
                self._view_snapshot(snapshot)

        with col3:
            if st.button(
                "Rollback",
                key=f"rollback_{snapshot.snapshot_id}",
                type="primary",
                use_container_width=True,
            ):
                self._confirm_rollback(snapshot)

    def _render_ab_comparison(self) -> None:
        """Renderizar interface de comparação A/B."""

        st.markdown("### Comparação A/B de Snapshots")

        # Get available snapshots
        snapshots = self._get_filtered_snapshots(None, None, 50)

        if len(snapshots) < 2:
            st.warning("Pelo menos 2 snapshots são necessários para comparação.")
            return

        # Snapshot selectors
        col1, col2 = st.columns(2)

        snapshot_options = [
            f"{s.map_name} v{s.version} ({s.created_at.strftime('%d/%m %H:%M')})" for s in snapshots
        ]

        with col1:
            st.markdown("#### Snapshot A (Base)")
            selected_a_idx = st.selectbox(
                "Selecionar snapshot A:",
                range(len(snapshots)),
                format_func=lambda x: snapshot_options[x],
                key="snapshot_a_select",
            )
            st.session_state.selected_snapshot_a = snapshots[selected_a_idx]

        with col2:
            st.markdown("#### Snapshot B (Comparação)")
            selected_b_idx = st.selectbox(
                "Selecionar snapshot B:",
                range(len(snapshots)),
                format_func=lambda x: snapshot_options[x],
                key="snapshot_b_select",
                index=min(1, len(snapshots) - 1),
            )
            st.session_state.selected_snapshot_b = snapshots[selected_b_idx]

        # Compare button
        if st.button(
            "Comparar Snapshots", type="primary", use_container_width=True, key="compare_btn"
        ):
            self._perform_comparison()

        # Show comparison results
        if st.session_state.comparison_data:
            self._render_comparison_results()

    def _perform_comparison(self) -> None:
        """Executar comparação entre snapshots selecionados."""

        snapshot_a = st.session_state.selected_snapshot_a
        snapshot_b = st.session_state.selected_snapshot_b

        try:
            with st.spinner("Comparando snapshots..."):
                diff = self.snapshots.compare_snapshots(
                    snapshot_a.snapshot_id, snapshot_b.snapshot_id
                )

                # Load actual data
                map_data_a, _ = self.snapshots.load_snapshot(snapshot_a.snapshot_id)
                map_data_b, _ = self.snapshots.load_snapshot(snapshot_b.snapshot_id)

                st.session_state.comparison_data = {
                    "diff": diff,
                    "snapshot_a": snapshot_a,
                    "snapshot_b": snapshot_b,
                    "map_data_a": map_data_a,
                    "map_data_b": map_data_b,
                }

            st.success("Comparação concluída!")

        except Exception as e:
            logger.error(f"Error comparing snapshots: {e}")
            st.error(f"Erro na comparação: {str(e)}")

    def _render_comparison_results(self) -> None:
        """Renderizar resultados da comparação."""

        data = st.session_state.comparison_data
        diff = data["diff"]

        # Statistics
        st.markdown("### Estatísticas da Comparação")

        stats_html = f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Células Alteradas</div>
                <div class="stat-value">{diff.cells_changed}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">% Alterado</div>
                <div class="stat-value">{diff.change_summary['percent_changed']:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Mudança Média</div>
                <div class="stat-value {'diff-positive' if diff.mean_change > 0 else 'diff-negative'}">{diff.mean_change:+.3f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Máx. Mudança</div>
                <div class="stat-value {'diff-positive' if diff.max_change > 0 else 'diff-negative'}">{diff.max_change:+.3f}</div>
            </div>
        </div>
        """
        st.markdown(stats_html, unsafe_allow_html=True)

        # Visual comparison
        st.markdown("### Comparação Visual")

        tab1, tab2, tab3 = st.tabs(["Lado a Lado", "Mapa de Diferenças", "Gráfico de Mudanças"])

        with tab1:
            self._render_side_by_side(data)

        with tab2:
            self._render_diff_heatmap(data)

        with tab3:
            self._render_change_chart(data)

    def _render_side_by_side(self, data: Dict[str, Any]) -> None:
        """Renderizar comparação lado a lado."""

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"#### {data['snapshot_a'].map_name} v{data['snapshot_a'].version}")
            st.dataframe(data["map_data_a"], use_container_width=True, height=400)

        with col2:
            st.markdown(f"#### {data['snapshot_b'].map_name} v{data['snapshot_b'].version}")
            st.dataframe(data["map_data_b"], use_container_width=True, height=400)

    def _render_diff_heatmap(self, data: Dict[str, Any]) -> None:
        """Renderizar mapa de calor das diferenças."""

        map_a = data["map_data_a"]
        map_b = data["map_data_b"]

        # Calculate difference
        numeric_cols = map_a.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # Use first numeric column for diff
            col = numeric_cols[0]
            diff_matrix = map_b[col].values.reshape(-1, 1) - map_a[col].values.reshape(-1, 1)

            # Create heatmap
            fig = px.imshow(
                diff_matrix.T,
                color_continuous_scale="RdBu_r",
                title=f"Mapa de Diferenças - {col}",
                labels={"color": "Diferença"},
            )

            fig.update_layout(height=500, showlegend=True, font=dict(size=12))

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhuma coluna numérica encontrada para visualização.")

    def _render_change_chart(self, data: Dict[str, Any]) -> None:
        """Renderizar gráfico de distribuição de mudanças."""

        map_a = data["map_data_a"]
        map_b = data["map_data_b"]

        numeric_cols = map_a.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) > 0:
            col = numeric_cols[0]
            diff_values = map_b[col].values - map_a[col].values
            diff_values = diff_values[np.abs(diff_values) > 1e-6]  # Remove near-zero changes

            if len(diff_values) > 0:
                # Create histogram
                fig = px.histogram(
                    x=diff_values,
                    nbins=30,
                    title="Distribuição de Mudanças",
                    labels={"x": "Mudança de Valor", "y": "Frequência"},
                )

                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhuma mudança significativa detectada.")
        else:
            st.warning("Nenhuma coluna numérica encontrada para análise.")

    def _render_timeline(self) -> None:
        """Renderizar timeline visual de mudanças."""

        st.markdown("### Timeline de Mudanças")

        # Get snapshots for timeline
        snapshots = self._get_filtered_snapshots(None, None, 50)

        if not snapshots:
            st.info("Nenhum snapshot disponível para timeline.")
            return

        # Group by map
        maps_data = {}
        for snapshot in snapshots:
            key = f"{snapshot.map_name}_{snapshot.map_type}"
            if key not in maps_data:
                maps_data[key] = []
            maps_data[key].append(snapshot)

        # Render timeline for each map
        for map_key, map_snapshots in maps_data.items():
            map_name, map_type = map_key.split("_", 1)

            st.markdown(f"#### {map_name} ({map_type.title()})")

            # Sort by creation date
            map_snapshots.sort(key=lambda x: x.created_at, reverse=True)

            timeline_html = '<div style="position: relative;">'

            for i, snapshot in enumerate(map_snapshots):
                is_last = i == len(map_snapshots) - 1

                timeline_html += f"""
                <div class="timeline-item">
                    {'' if is_last else '<div class="timeline-line"></div>'}
                    <div>
                        <strong>v{snapshot.version}</strong>
                        <span style="margin-left: 1rem; color: var(--text-color-secondary); font-size: 0.9rem;">
                            {snapshot.created_at.strftime('%d/%m/%Y %H:%M')}
                        </span>
                        <span style="margin-left: 1rem; color: var(--primary-color); font-size: 0.85rem;">
                            {snapshot.created_by}
                        </span>
                    </div>
                    {f'<div style="margin-top: 0.25rem; font-size: 0.9rem; color: var(--text-color-secondary);">{snapshot.description}</div>' if snapshot.description else ''}
                </div>
                """

            timeline_html += "</div>"
            st.markdown(timeline_html, unsafe_allow_html=True)
            st.markdown("---")

    def _render_storage_management(self) -> None:
        """Renderizar interface de gerenciamento de storage."""

        st.markdown("### Gerenciamento de Storage")

        try:
            # Get storage statistics
            stats = self.snapshots.get_storage_stats()

            # Display statistics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total de Snapshots", stats["total_snapshots"])

            with col2:
                st.metric(
                    "Tamanho Comprimido", self._format_file_size(stats["total_compressed_size"])
                )

            with col3:
                st.metric("Arquivo DB", self._format_file_size(stats["database_file_size"]))

            with col4:
                st.metric("Tamanho Médio", self._format_file_size(stats["average_snapshot_size"]))

            # Snapshots by type
            if stats["snapshots_by_type"]:
                st.markdown("#### Snapshots por Tipo")

                type_df = pd.DataFrame(
                    list(stats["snapshots_by_type"].items()), columns=["Tipo", "Quantidade"]
                )

                fig = px.pie(
                    type_df,
                    values="Quantidade",
                    names="Tipo",
                    title="Distribuição por Tipo de Mapa",
                )
                st.plotly_chart(fig, use_container_width=True)

            # Recent activity
            if stats["recent_activity"]:
                st.markdown("#### Atividade Recente (30 dias)")

                activity_df = pd.DataFrame(
                    list(stats["recent_activity"].items()), columns=["Data", "Snapshots"]
                )
                activity_df["Data"] = pd.to_datetime(activity_df["Data"])

                fig = px.line(
                    activity_df, x="Data", y="Snapshots", title="Snapshots Criados por Dia"
                )
                st.plotly_chart(fig, use_container_width=True)

            # Cleanup options
            st.markdown("#### Limpeza de Storage")

            col1, col2 = st.columns(2)

            with col1:
                keep_count = st.number_input(
                    "Manter quantos snapshots por mapa:", min_value=1, max_value=50, value=10
                )

            with col2:
                if st.button(
                    "Limpar Snapshots Antigos", type="secondary", use_container_width=True
                ):
                    self._cleanup_old_snapshots(keep_count)

        except Exception as e:
            logger.error(f"Error loading storage stats: {e}")
            st.error("Erro ao carregar estatísticas de storage.")

    def _get_available_maps(self) -> List[str]:
        """Obter lista de mapas disponíveis."""
        try:
            snapshots = self.snapshots.get_snapshot_history(limit=1000)
            return sorted(list(set(s.map_name for s in snapshots)))
        except Exception as e:
            logger.error(f"Error getting available maps: {e}")
            return []

    def _get_filtered_snapshots(
        self, map_name_filter: Optional[str], map_type_filter: Optional[str], limit: int
    ) -> List[SnapshotMetadata]:
        """Obter snapshots filtrados."""
        try:
            map_name = None if map_name_filter == "Todos" else map_name_filter
            map_type = None if map_type_filter == "Todos" else map_type_filter

            return self.snapshots.get_snapshot_history(
                map_name=map_name, map_type=map_type, limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting filtered snapshots: {e}")
            return []

    def _format_file_size(self, size_bytes: int) -> str:
        """Formatar tamanho de arquivo em formato legível."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _view_snapshot(self, snapshot: SnapshotMetadata) -> None:
        """Visualizar snapshot específico."""
        try:
            map_data, metadata = self.snapshots.load_snapshot(snapshot.snapshot_id)

            st.success(f"Snapshot {snapshot.snapshot_id} carregado com sucesso!")

            # Show metadata
            with st.expander("Metadados", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Nome:** {snapshot.map_name}")
                    st.write(f"**Tipo:** {snapshot.map_type}")
                    st.write(f"**Versão:** {snapshot.version}")
                with col2:
                    st.write(f"**Criado em:** {snapshot.created_at}")
                    st.write(f"**Por:** {snapshot.created_by}")
                    st.write(f"**Tamanho:** {self._format_file_size(snapshot.file_size)}")

            # Show data
            st.dataframe(map_data, use_container_width=True)

        except Exception as e:
            logger.error(f"Error viewing snapshot: {e}")
            st.error(f"Erro ao visualizar snapshot: {str(e)}")

    def _confirm_rollback(self, snapshot: SnapshotMetadata) -> None:
        """Confirmar e executar rollback."""

        # Show confirmation dialog
        with st.form(f"rollback_form_{snapshot.snapshot_id}"):
            st.warning(
                f"Confirmar rollback para snapshot **{snapshot.map_name} v{snapshot.version}**?"
            )
            st.write("Esta ação irá restaurar o mapa para esta versão.")

            col1, col2 = st.columns(2)

            with col1:
                if st.form_submit_button(
                    "Confirmar Rollback", type="primary", use_container_width=True
                ):
                    self._execute_rollback(snapshot)

            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.info("Rollback cancelado.")

    def _execute_rollback(self, snapshot: SnapshotMetadata) -> None:
        """Executar rollback para snapshot."""
        try:
            with st.spinner("Executando rollback..."):
                map_data, metadata = self.snapshots.rollback_to_snapshot(snapshot.snapshot_id)

            st.success(f"Rollback para v{snapshot.version} executado com sucesso!")

            # Show restored data preview
            with st.expander("Preview dos Dados Restaurados", expanded=True):
                st.dataframe(map_data.head(), use_container_width=True)

        except Exception as e:
            logger.error(f"Error executing rollback: {e}")
            st.error(f"Erro no rollback: {str(e)}")

    def _cleanup_old_snapshots(self, keep_count: int) -> None:
        """Limpar snapshots antigos."""
        try:
            with st.spinner("Limpando snapshots antigos..."):
                deleted_count = self.snapshots.cleanup_old_snapshots(keep_count=keep_count)

            st.success(f"{deleted_count} snapshots antigos foram removidos.")
            st.rerun()

        except Exception as e:
            logger.error(f"Error cleaning up snapshots: {e}")
            st.error(f"Erro na limpeza: {str(e)}")


def main():
    """Função principal da página de versionamento."""

    # Configure page
    st.set_page_config(
        page_title="Versionamento - FuelTune", page_icon=":material/history:", layout="wide"
    )

    try:
        # Initialize and render versioning page
        versioning_page = VersioningPage()
        versioning_page.render()

    except Exception as e:
        logger.error(f"Error in versioning page: {e}")
        st.error("Erro ao carregar página de versionamento.")
        st.exception(e)


if __name__ == "__main__":
    main()
