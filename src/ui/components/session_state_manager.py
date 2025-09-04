"""
Advanced Session State Manager para FuelTune Analyzer.

Gerenciador centralizado de estado da sessão Streamlit com:
- Persistência de dados entre páginas
- Cache inteligente de dados
- Sincronização de estado
- Histórico de navegação
- Configurações do usuário

Author: A03-UI-STREAMLIT Agent
Created: 2025-01-02
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar

import streamlit as st

from ...utils.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class UserPreferences:
    """Preferências do usuário."""

    theme: str = "light"
    default_chart_height: int = 400
    auto_refresh_interval: int = 30
    decimal_places: int = 2
    preferred_units: Dict[str, str] = field(
        default_factory=lambda: {
            "temperature": "celsius",
            "pressure": "bar",
            "flow": "lh",
            "speed": "kmh",
        }
    )
    show_advanced_features: bool = False
    cache_ttl: int = 300

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        """Criar a partir de dicionário."""
        return cls(**data)


@dataclass
class NavigationState:
    """Estado de navegação."""

    current_page: str = "dashboard"
    previous_page: Optional[str] = None
    page_history: List[str] = field(default_factory=list)
    last_navigation: datetime = field(default_factory=datetime.now)

    def navigate_to(self, page: str) -> None:
        """Navegar para uma página."""
        if self.current_page != page:
            self.previous_page = self.current_page
            self.page_history.append(self.current_page)

            # Manter apenas últimas 10 páginas no histórico
            if len(self.page_history) > 10:
                self.page_history = self.page_history[-10:]

            self.current_page = page
            self.last_navigation = datetime.now()


@dataclass
class SessionData:
    """Dados da sessão selecionada."""

    session_id: Optional[str] = None
    session_name: Optional[str] = None
    format_version: Optional[str] = None
    total_records: int = 0
    quality_score: Optional[float] = None
    last_loaded: Optional[datetime] = None
    data_cache: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Verificar se a sessão é válida."""
        return self.session_id is not None

    def is_cache_valid(self, key: str, ttl: int = 300) -> bool:
        """Verificar se o cache é válido."""
        if key not in self.data_cache:
            return False

        cache_time = self.data_cache[key].get("timestamp")
        if not cache_time:
            return False

        return (datetime.now() - cache_time).total_seconds() < ttl

    def set_cache(self, key: str, data: Any) -> None:
        """Definir dados no cache."""
        self.data_cache[key] = {"data": data, "timestamp": datetime.now()}

    def get_cache(self, key: str) -> Any:
        """Obter dados do cache."""
        if key in self.data_cache:
            return self.data_cache[key].get("data")
        return None


@dataclass
class FilterState:
    """Estado dos filtros aplicados."""

    time_range: Optional[tuple] = None
    rpm_range: Optional[tuple] = None
    throttle_range: Optional[tuple] = None
    map_range: Optional[tuple] = None
    selected_gears: Optional[List[int]] = None
    show_two_step_only: bool = False
    show_launch_only: bool = False
    custom_filters: Dict[str, Any] = field(default_factory=dict)

    def reset(self) -> None:
        """Resetar todos os filtros."""
        self.time_range = None
        self.rpm_range = None
        self.throttle_range = None
        self.map_range = None
        self.selected_gears = None
        self.show_two_step_only = False
        self.show_launch_only = False
        self.custom_filters.clear()

    def has_active_filters(self) -> bool:
        """Verificar se há filtros ativos."""
        return any(
            [
                self.time_range,
                self.rpm_range,
                self.throttle_range,
                self.map_range,
                self.selected_gears,
                self.show_two_step_only,
                self.show_launch_only,
                self.custom_filters,
            ]
        )


@dataclass
class AppState:
    """Estado completo da aplicação."""

    user_preferences: UserPreferences = field(default_factory=UserPreferences)
    navigation: NavigationState = field(default_factory=NavigationState)
    session_data: SessionData = field(default_factory=SessionData)
    filter_state: FilterState = field(default_factory=FilterState)
    ui_state: Dict[str, Any] = field(default_factory=dict)
    debug_mode: bool = False
    last_updated: datetime = field(default_factory=datetime.now)

    def update_timestamp(self) -> None:
        """Atualizar timestamp da última modificação."""
        self.last_updated = datetime.now()


class SessionStateManager:
    """
    Gerenciador avançado de estado da sessão.

    Características:
    - Estado centralizado e tipado
    - Persistência automática
    - Sincronização entre páginas
    - Cache inteligente
    - Histórico de navegação
    """

    def __init__(self):
        self._state_key = "fueltune_app_state"
        self._init_state()

    def _init_state(self) -> None:
        """Inicializar estado se não existir."""
        if self._state_key not in st.session_state:
            st.session_state[self._state_key] = AppState()
            logger.info("Estado da aplicação inicializado")

    @property
    def state(self) -> AppState:
        """Obter estado atual."""
        return st.session_state[self._state_key]

    def get_user_preferences(self) -> UserPreferences:
        """Obter preferências do usuário."""
        return self.state.user_preferences

    def update_user_preferences(self, **kwargs) -> None:
        """Atualizar preferências do usuário."""
        prefs = self.state.user_preferences
        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        self.state.update_timestamp()
        logger.info(f"Preferências atualizadas: {kwargs}")

    def get_navigation_state(self) -> NavigationState:
        """Obter estado de navegação."""
        return self.state.navigation

    def navigate_to(self, page: str) -> None:
        """Navegar para uma página."""
        self.state.navigation.navigate_to(page)
        self.state.update_timestamp()
        logger.info(f"Navegação: {page}")

    def get_current_page(self) -> str:
        """Obter página atual."""
        return self.state.navigation.current_page

    def get_previous_page(self) -> Optional[str]:
        """Obter página anterior."""
        return self.state.navigation.previous_page

    def get_page_history(self) -> List[str]:
        """Obter histórico de páginas."""
        return self.state.navigation.page_history.copy()

    def get_session_data(self) -> SessionData:
        """Obter dados da sessão."""
        return self.state.session_data

    def set_selected_session(
        self,
        session_id: str,
        session_name: str,
        format_version: str = "v1.0",
        total_records: int = 0,
        quality_score: Optional[float] = None,
    ) -> None:
        """Definir sessão selecionada."""
        session_data = self.state.session_data

        # Se mudou a sessão, limpar cache
        if session_data.session_id != session_id:
            session_data.data_cache.clear()

        session_data.session_id = session_id
        session_data.session_name = session_name
        session_data.format_version = format_version
        session_data.total_records = total_records
        session_data.quality_score = quality_score
        session_data.last_loaded = datetime.now()

        self.state.update_timestamp()
        logger.info(f"Sessão selecionada: {session_name} ({session_id})")

    def get_selected_session_id(self) -> Optional[str]:
        """Obter ID da sessão selecionada."""
        return self.state.session_data.session_id

    def cache_data(self, key: str, data: Any, page_specific: bool = False) -> None:
        """Cachear dados."""
        cache_key = f"{self.get_current_page()}_{key}" if page_specific else key
        self.state.session_data.set_cache(cache_key, data)
        logger.debug(f"Dados cacheados: {cache_key}")

    def get_cached_data(self, key: str, page_specific: bool = False, ttl: int = 300) -> Any:
        """Obter dados do cache."""
        cache_key = f"{self.get_current_page()}_{key}" if page_specific else key

        if self.state.session_data.is_cache_valid(cache_key, ttl):
            return self.state.session_data.get_cache(cache_key)

        return None

    def clear_cache(self, pattern: Optional[str] = None) -> None:
        """Limpar cache."""
        cache = self.state.session_data.data_cache

        if pattern is None:
            cache.clear()
            logger.info("Cache completo limpo")
        else:
            keys_to_remove = [k for k in cache.keys() if pattern in k]
            for key in keys_to_remove:
                del cache[key]
            logger.info(f"Cache limpo com padrão: {pattern}")

    def get_filter_state(self) -> FilterState:
        """Obter estado dos filtros."""
        return self.state.filter_state

    def update_filters(self, **kwargs) -> None:
        """Atualizar filtros."""
        filters = self.state.filter_state
        for key, value in kwargs.items():
            if hasattr(filters, key):
                setattr(filters, key, value)
        self.state.update_timestamp()
        logger.debug(f"Filtros atualizados: {kwargs}")

    def reset_filters(self) -> None:
        """Resetar todos os filtros."""
        self.state.filter_state.reset()
        self.state.update_timestamp()
        logger.info("Filtros resetados")

    def set_ui_state(self, key: str, value: Any) -> None:
        """Definir estado da UI."""
        self.state.ui_state[key] = value
        self.state.update_timestamp()

    def get_ui_state(self, key: str, default: Any = None) -> Any:
        """Obter estado da UI."""
        return self.state.ui_state.get(key, default)

    def set_debug_mode(self, enabled: bool) -> None:
        """Definir modo debug."""
        self.state.debug_mode = enabled
        self.state.update_timestamp()
        logger.info(f"Modo debug: {enabled}")

    def is_debug_mode(self) -> bool:
        """Verificar se está em modo debug."""
        return self.state.debug_mode

    def get_state_summary(self) -> Dict[str, Any]:
        """Obter resumo do estado."""
        return {
            "current_page": self.get_current_page(),
            "selected_session": self.state.session_data.session_name,
            "session_records": self.state.session_data.total_records,
            "cache_entries": len(self.state.session_data.data_cache),
            "active_filters": self.state.filter_state.has_active_filters(),
            "last_updated": self.state.last_updated,
            "debug_mode": self.state.debug_mode,
        }

    def export_state(self) -> Dict[str, Any]:
        """Exportar estado para persistência."""
        # Não incluir cache nem dados sensíveis
        export_data = {
            "user_preferences": self.state.user_preferences.to_dict(),
            "current_page": self.state.navigation.current_page,
            "session_id": self.state.session_data.session_id,
            "session_name": self.state.session_data.session_name,
            "debug_mode": self.state.debug_mode,
        }
        return export_data

    def import_state(self, data: Dict[str, Any]) -> None:
        """Importar estado de persistência."""
        try:
            if "user_preferences" in data:
                self.state.user_preferences = UserPreferences.from_dict(data["user_preferences"])

            if "current_page" in data:
                self.state.navigation.current_page = data["current_page"]

            if "session_id" in data and "session_name" in data:
                self.state.session_data.session_id = data["session_id"]
                self.state.session_data.session_name = data["session_name"]

            if "debug_mode" in data:
                self.state.debug_mode = data["debug_mode"]

            self.state.update_timestamp()
            logger.info("Estado importado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao importar estado: {str(e)}")

    def create_callback(self, callback: Callable[[Any], None]) -> Callable:
        """Criar callback com atualização automática do estado."""

        def wrapper(*args, **kwargs):
            result = callback(*args, **kwargs)
            self.state.update_timestamp()
            return result

        return wrapper

    def with_state_sync(self, func: Callable[[], T]) -> T:
        """Executar função com sincronização de estado."""
        try:
            result = func()
            self.state.update_timestamp()
            return result
        except Exception as e:
            logger.error(f"Erro na execução com sync de estado: {str(e)}")
            raise

    def render_debug_panel(self) -> None:
        """Renderizar painel de debug do estado."""
        if not self.is_debug_mode():
            return

        with st.sidebar.expander("Debug - Estado da App", expanded=False):
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <i class="material-icons" style="color: #1976D2;">build</i>
                <strong style="color: #212529;">Debug - Estado da App</strong>
            </div>
            """, unsafe_allow_html=True)
            st.json(self.get_state_summary())

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Limpar Cache", key="debug_clear_cache"):
                    self.clear_cache()
                    st.success("Cache limpo!")

            with col2:
                if st.button("Reset Filtros", key="debug_reset_filters"):
                    self.reset_filters()
                    st.success("Filtros resetados!")

            # Export/Import estado
            st.markdown("**Export/Import:**")

            export_data = self.export_state()
            st.download_button(
                "Export Estado",
                data=json.dumps(export_data, indent=2, default=str),
                file_name="fueltune_state.json",
                mime="application/json",
            )


# Instância global do gerenciador
_state_manager: Optional[SessionStateManager] = None


def get_state_manager() -> SessionStateManager:
    """Obter instância global do gerenciador de estado."""
    global _state_manager
    if _state_manager is None:
        _state_manager = SessionStateManager()
    return _state_manager


# Funções de conveniência para uso direto
def get_selected_session_id() -> Optional[str]:
    """Obter ID da sessão selecionada."""
    return get_state_manager().get_selected_session_id()


def set_selected_session(session_id: str, session_name: str, **kwargs) -> None:
    """Definir sessão selecionada."""
    get_state_manager().set_selected_session(session_id, session_name, **kwargs)


def cache_data(key: str, data: Any, page_specific: bool = False) -> None:
    """Cachear dados."""
    get_state_manager().cache_data(key, data, page_specific)


def get_cached_data(key: str, page_specific: bool = False, ttl: int = 300) -> Any:
    """Obter dados do cache."""
    return get_state_manager().get_cached_data(key, page_specific, ttl)


def navigate_to(page: str) -> None:
    """Navegar para uma página."""
    get_state_manager().navigate_to(page)


def get_user_preferences() -> UserPreferences:
    """Obter preferências do usuário."""
    return get_state_manager().get_user_preferences()


def update_user_preferences(**kwargs) -> None:
    """Atualizar preferências do usuário."""
    get_state_manager().update_user_preferences(**kwargs)


def get_filter_state() -> FilterState:
    """Obter estado dos filtros."""
    return get_state_manager().get_filter_state()


def update_filters(**kwargs) -> None:
    """Atualizar filtros."""
    get_state_manager().update_filters(**kwargs)


def render_debug_panel() -> None:
    """Renderizar painel de debug."""
    get_state_manager().render_debug_panel()


if __name__ == "__main__":
    # Teste do gerenciador de estado
    manager = get_state_manager()

    print("Estado inicial:")
    print(manager.get_state_summary())

    # Simular uso
    manager.set_selected_session("test-123", "Sessão Teste")
    manager.navigate_to("analysis")
    manager.update_filters(rpm_range=(1000, 5000))

    print("\nEstado após modificações:")
    print(manager.get_state_summary())
