"""
Session Selector Component para FuelTune Analyzer.

Componente para seleção e gerenciamento de sessões de dados.
Integra com o DatabaseManager para carregar sessões disponíveis.

Author: A03-UI-STREAMLIT Agent
Created: 2025-01-02
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
import streamlit as st

try:
    from ...data.database import get_database
except ImportError:
    from src.data.database import get_database
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SessionInfo:
    """Informações de uma sessão de dados."""

    id: str
    name: str
    filename: str
    format_version: str
    total_records: int
    duration_seconds: Optional[float]
    quality_score: Optional[float]
    created_at: datetime
    import_status: str
    file_size_mb: Optional[float]


class SessionSelector:
    """
    Componente para seleção de sessões de dados.

    Características:
    - Lista sessões disponíveis
    - Filtros por data, qualidade, status
    - Preview das sessões
    - Caching inteligente
    - Callback de seleção
    """

    def __init__(
        self,
        key_prefix: str = "session_selector",
        cache_ttl: int = 300,
        show_preview: bool = True,
        show_filters: bool = True,
    ):
        """
        Inicializar seletor de sessão.

        Args:
            key_prefix: Prefixo para chaves do Streamlit
            cache_ttl: TTL do cache em segundos
            show_preview: Se deve mostrar preview da sessão
            show_filters: Se deve mostrar filtros
        """
        self.key_prefix = key_prefix
        self.cache_ttl = cache_ttl
        self.show_preview = show_preview
        self.show_filters = show_filters
        self.db_manager = get_database()

    @st.cache_data(ttl=300)
    def _load_sessions(_self) -> List[SessionInfo]:
        """Carregar sessões do banco de dados (com cache)."""
        try:
            _self.db_manager.initialize_database()
            sessions_data = _self.db_manager.get_sessions()

            sessions = []
            for session_data in sessions_data:
                sessions.append(
                    SessionInfo(
                        id=session_data["id"],
                        name=session_data["name"],
                        filename=session_data["filename"],
                        format_version=session_data["format"],
                        total_records=session_data["records"],
                        duration_seconds=session_data["duration"],
                        quality_score=session_data["quality_score"],
                        created_at=session_data["created_at"],
                        import_status=session_data["status"],
                        file_size_mb=session_data.get("file_size_mb"),
                    )
                )

            return sessions
        except Exception as e:
            logger.error(f"Erro ao carregar sessões: {str(e)}")
            st.error(f"Erro ao carregar sessões: {str(e)}")
            return []

    def render_selector(
        self,
        selected_session_id: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
    ) -> Optional[SessionInfo]:
        """
        Renderizar seletor de sessões.

        Args:
            selected_session_id: ID da sessão selecionada
            on_change: Callback quando seleção muda

        Returns:
            Informações da sessão selecionada
        """
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2; font-size: 1.5rem;">folder</i>
            <h3 style="margin: 0; color: #1976D2;">Selecionar Sessão de Dados</h3>
        </div>
        """, unsafe_allow_html=True)

        # Carregar sessões
        sessions = self._load_sessions()

        if not sessions:
            st.warning("Nenhuma sessão encontrada. Importe dados primeiro.")
            return None

        # Aplicar filtros se habilitados
        filtered_sessions = self._apply_filters(sessions) if self.show_filters else sessions

        if not filtered_sessions:
            st.warning("Nenhuma sessão encontrada com os filtros aplicados.")
            return None

        # Criar opções para selectbox
        session_options = {}
        for session in filtered_sessions:
            display_name = self._format_session_display_name(session)
            session_options[display_name] = session

        # Encontrar índice da sessão selecionada
        selected_index = 0
        if selected_session_id:
            for i, session in enumerate(filtered_sessions):
                if session.id == selected_session_id:
                    selected_index = i
                    break

        # Renderizar selectbox
        selected_display_name = st.selectbox(
            "Escolha uma sessão:",
            options=list(session_options.keys()),
            index=selected_index,
            key=f"{self.key_prefix}_selectbox",
            help="Selecione a sessão de dados para análise",
        )

        selected_session = session_options[selected_display_name]

        # Callback de mudança
        if (
            on_change
            and st.session_state.get(f"{self.key_prefix}_last_selected") != selected_session.id
        ):
            st.session_state[f"{self.key_prefix}_last_selected"] = selected_session.id
            on_change(selected_session.id)

        # Preview da sessão se habilitado
        if self.show_preview:
            self._render_session_preview(selected_session)

        return selected_session

    def render_multi_selector(self, max_selections: int = 5) -> List[SessionInfo]:
        """
        Renderizar seletor múltiplo de sessões.

        Args:
            max_selections: Número máximo de seleções

        Returns:
            Lista de sessões selecionadas
        """
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2; font-size: 1.5rem;">checklist</i>
            <h3 style="margin: 0; color: #1976D2;">Selecionar Múltiplas Sessões</h3>
        </div>
        """, unsafe_allow_html=True)

        sessions = self._load_sessions()

        if not sessions:
            st.warning("Nenhuma sessão encontrada.")
            return []

        # Aplicar filtros
        filtered_sessions = self._apply_filters(sessions) if self.show_filters else sessions

        # Criar dataframe para exibição
        df = self._create_sessions_dataframe(filtered_sessions)

        # Seletor de sessões
        selected_rows = st.dataframe(
            df,
            width='stretch',
            key=f"{self.key_prefix}_multi",
            on_select="rerun",
            selection_mode="multi-row",
            hide_index=True,
        )

        # Limitar seleções
        if len(selected_rows.selection.rows) > max_selections:
            st.warning(f"Máximo de {max_selections} sessões permitidas.")
            return []

        # Retornar sessões selecionadas
        selected_sessions = []
        for idx in selected_rows.selection.rows:
            if idx < len(filtered_sessions):
                selected_sessions.append(filtered_sessions[idx])

        return selected_sessions

    def _apply_filters(self, sessions: List[SessionInfo]) -> List[SessionInfo]:
        """Aplicar filtros às sessões."""
        with st.expander("Filtros", expanded=False):
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <i class="material-icons" style="color: #1976D2;">filter_alt</i>
                <strong style="color: #212529;">Opções de Filtro</strong>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)

            with col1:
                # Filtro por data
                date_filter = st.selectbox(
                    "Período:",
                    ["Todos", "Última semana", "Último mês", "Últimos 3 meses"],
                    key=f"{self.key_prefix}_date_filter",
                )

            with col2:
                # Filtro por qualidade
                quality_filter = st.selectbox(
                    "Qualidade mínima:",
                    ["Qualquer", "50%", "70%", "80%", "90%"],
                    key=f"{self.key_prefix}_quality_filter",
                )

            with col3:
                # Filtro por status
                status_filter = st.selectbox(
                    "Status:",
                    ["Todos", "completed", "processing", "failed"],
                    key=f"{self.key_prefix}_status_filter",
                )

        # Aplicar filtros
        filtered = sessions

        # Filtro de data
        if date_filter != "Todos":
            now = datetime.now()
            if date_filter == "Última semana":
                cutoff = now - timedelta(weeks=1)
            elif date_filter == "Último mês":
                cutoff = now - timedelta(days=30)
            elif date_filter == "Últimos 3 meses":
                cutoff = now - timedelta(days=90)
            else:
                cutoff = datetime.min

            filtered = [s for s in filtered if s.created_at >= cutoff]

        # Filtro de qualidade
        if quality_filter != "Qualquer":
            min_quality = float(quality_filter.rstrip("%"))
            filtered = [
                s
                for s in filtered
                if s.quality_score is not None and s.quality_score >= min_quality
            ]

        # Filtro de status
        if status_filter != "Todos":
            filtered = [s for s in filtered if s.import_status == status_filter]

        return filtered

    def _format_session_display_name(self, session: SessionInfo) -> str:
        """Formatar nome de exibição da sessão."""
        date_str = session.created_at.strftime("%d/%m/%Y %H:%M")
        records_str = f"{session.total_records:,}" if session.total_records else "0"

        quality_icon = "check_circle" if session.quality_score and session.quality_score >= 80 else "warning"
        quality_color = "#4CAF50" if session.quality_score and session.quality_score >= 80 else "#FF9800"
        status_icon = "check_circle" if session.import_status == "completed" else "schedule"
        status_color = "#4CAF50" if session.import_status == "completed" else "#FF9800"

        return f"{quality_icon}{status_icon} {session.name} | {date_str} | {records_str} pts"

    def _render_session_preview(self, session: SessionInfo) -> None:
        """Renderizar preview da sessão."""
        with st.expander("Detalhes da Sessão", expanded=True):
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <i class="material-icons" style="color: #1976D2;">info</i>
                <strong style="color: #212529;">Detalhes da Sessão</strong>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Pontos de Dados", f"{session.total_records:,}")
                st.metric("Versão", session.format_version)

            with col2:
                duration_str = (
                    f"{session.duration_seconds:.1f}s" if session.duration_seconds else "N/A"
                )
                st.metric("Duração", duration_str)

                quality_str = f"{session.quality_score:.1f}%" if session.quality_score else "N/A"
                st.metric("Qualidade", quality_str)

            with col3:
                st.metric("Status", session.import_status.title())

                size_str = f"{session.file_size_mb:.1f} MB" if session.file_size_mb else "N/A"
                st.metric("Tamanho", size_str)

            # Informações adicionais
            st.markdown("**Arquivo:** " + session.filename)
            st.markdown("**Criado em:** " + session.created_at.strftime("%d/%m/%Y às %H:%M:%S"))

    def _create_sessions_dataframe(self, sessions: List[SessionInfo]) -> pd.DataFrame:
        """Criar DataFrame das sessões para exibição."""
        data = []
        for session in sessions:
            data.append(
                {
                    "Nome": session.name,
                    "Arquivo": session.filename,
                    "Data": session.created_at.strftime("%d/%m/%Y"),
                    "Pontos": f"{session.total_records:,}",
                    "Duração": (
                        f"{session.duration_seconds:.1f}s" if session.duration_seconds else "N/A"
                    ),
                    "Qualidade": (
                        f"{session.quality_score:.1f}%" if session.quality_score else "N/A"
                    ),
                    "Status": session.import_status.title(),
                    "Formato": session.format_version,
                }
            )

        return pd.DataFrame(data)

    def render_session_comparison(self, session1: SessionInfo, session2: SessionInfo) -> None:
        """
        Renderizar comparação entre duas sessões.

        Args:
            session1: Primeira sessão
            session2: Segunda sessão
        """
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2; font-size: 1.5rem;">compare</i>
            <h3 style="margin: 0; color: #1976D2;">Comparação de Sessões</h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <i class="material-icons" style="color: #1976D2;">folder</i>
                <strong style="color: #1976D2; font-size: 1.25rem;">{session1.name}</strong>
            </div>
            """)
            self._render_session_preview(session1)

        with col2:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <i class="material-icons" style="color: #1976D2;">folder</i>
                <strong style="color: #1976D2; font-size: 1.25rem;">{session2.name}</strong>
            </div>
            """)
            self._render_session_preview(session2)

        # Métricas de comparação
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2;">analytics</i>
            <h4 style="margin: 0; color: #1976D2;">Análise Comparativa</h4>
        </div>
        """, unsafe_allow_html=True)

        comp_col1, comp_col2, comp_col3 = st.columns(3)

        with comp_col1:
            points_diff = session2.total_records - session1.total_records
            st.metric("Diferença de Pontos", f"{points_diff:+,}", delta=points_diff)

        with comp_col2:
            if session1.duration_seconds and session2.duration_seconds:
                duration_diff = session2.duration_seconds - session1.duration_seconds
                st.metric(
                    "Diferença de Duração",
                    f"{duration_diff:+.1f}s",
                    delta=duration_diff,
                )
            else:
                st.metric("Diferença de Duração", "N/A")

        with comp_col3:
            if session1.quality_score and session2.quality_score:
                quality_diff = session2.quality_score - session1.quality_score
                st.metric(
                    "Diferença de Qualidade",
                    f"{quality_diff:+.1f}%",
                    delta=quality_diff,
                )
            else:
                st.metric("Diferença de Qualidade", "N/A")

    def clear_cache(self) -> None:
        """Limpar cache de sessões."""
        if hasattr(st, "cache_data"):
            st.cache_data.clear()


# Função utilitária para uso rápido
@st.cache_data(ttl=300)
def get_available_sessions() -> List[Dict[str, Any]]:
    """
    Obter lista de sessões disponíveis (função utilitária).

    Returns:
        Lista de dicionários com informações das sessões
    """
    try:
        db_manager = get_database()
        db_manager.initialize_database()
        return db_manager.get_sessions()
    except Exception as e:
        logger.error(f"Erro ao obter sessões: {str(e)}")
        return []


def render_quick_session_selector(key: str = "quick_session") -> Optional[str]:
    """
    Renderizar seletor rápido de sessão (função utilitária).

    Args:
        key: Chave única para o componente

    Returns:
        ID da sessão selecionada ou None
    """
    sessions = get_available_sessions()

    if not sessions:
        st.warning("Nenhuma sessão encontrada.")
        return None

    # Criar opções simples
    options = {}
    for session in sessions:
        display_name = f"{session['name']} ({session['records']:,} pts)"
        options[display_name] = session["id"]

    selected_display = st.selectbox("Sessão:", options=list(options.keys()), key=key)

    return options[selected_display]


if __name__ == "__main__":
    # Exemplo de uso
    selector = SessionSelector(show_preview=True, show_filters=True)

    selected = selector.render_selector()
    if selected:
        st.write(f"Sessão selecionada: {selected.name}")
        st.json(
            {
                "id": selected.id,
                "records": selected.total_records,
                "quality": selected.quality_score,
            }
        )
