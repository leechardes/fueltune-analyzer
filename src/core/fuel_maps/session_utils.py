"""
Utilitários para gerenciar session_state do Streamlit.
Centraliza acesso e manipulação dos dados de sessão.
"""

import logging
from typing import Any, Dict, Optional

try:
    import streamlit as st
except ImportError:
    # Mock do Streamlit para testes sem interface
    class MockStreamlit:
        class session_state:
            _data = {}

            def get(self, key, default=None):
                return self._data.get(key, default)

            def __setitem__(self, key, value):
                self._data[key] = value

            def __getitem__(self, key):
                return self._data[key]

            def __contains__(self, key):
                return key in self._data

            def keys(self):
                return self._data.keys()

    st = MockStreamlit()

logger = logging.getLogger(__name__)


class SessionManager:
    """Gerenciador de session_state para mapas 3D."""

    # Chaves padrão do session_state
    VEHICLE_ID_KEY = "selected_vehicle_id"
    MAP_DATA_PREFIX = "saved_3d_map"
    CACHE_PREFIX = "cache_3d_map"

    @staticmethod
    def get_vehicle_data_from_session() -> Dict[str, Any]:
        """Obtém dados do veículo do session_state."""
        try:
            from src.data.vehicle_database import get_vehicle_by_id

            # Tentar obter o veículo selecionado
            selected_vehicle_id = st.session_state.get(SessionManager.VEHICLE_ID_KEY)

            if selected_vehicle_id:
                vehicle = get_vehicle_by_id(selected_vehicle_id)
                if vehicle:
                    return SessionManager._process_vehicle_data(vehicle)

        except ImportError:
            logger.warning("Database de veículos não disponível")
        except Exception as e:
            logger.error(f"Erro ao obter dados do veículo: {e}")

        # Retornar valores padrão
        return SessionManager._get_default_vehicle_data()

    @staticmethod
    def _process_vehicle_data(vehicle: Dict[str, Any]) -> Dict[str, Any]:
        """Processa dados do veículo do banco para formato padronizado."""
        # Calcular vazão total dos bicos em lbs/h
        total_flow_a = vehicle.get("bank_a_total_flow", 0) if vehicle.get("bank_a_enabled") else 0
        total_flow_b = vehicle.get("bank_b_total_flow", 0) if vehicle.get("bank_b_enabled") else 0
        total_flow_lbs = total_flow_a + total_flow_b

        # Converter vazão de lbs/h para cc/min (1 lb/h ≈ 10.5 cc/min)
        injector_flow_cc = total_flow_lbs * 10.5 if total_flow_lbs > 0 else 550

        # Verificar se é turbo
        aspiration = vehicle.get("engine_aspiration", "").lower()
        is_turbo = any(term in aspiration for term in ["turbo", "super"])

        # Usar boost_pressure (pressão máxima) para o calculador
        boost_value = 0.0
        if is_turbo:
            boost_value = vehicle.get("boost_pressure") or vehicle.get("max_boost_pressure") or 1.0
            if boost_value is None:
                boost_value = 1.0

        return {
            "displacement": vehicle.get("engine_displacement", 2.0),
            "cylinders": vehicle.get("engine_cylinders", 4),
            "injector_flow_cc": injector_flow_cc,
            "injector_flow_lbs": total_flow_lbs,
            "fuel_type": vehicle.get("fuel_type", "Gasolina"),
            "turbo": is_turbo,
            "boost_pressure": boost_value,
            "bsfc_factor": vehicle.get("bsfc_factor", 0.50),
            "injector_impedance": vehicle.get("injector_impedance", "high"),
            "cooling_type": vehicle.get("cooling_type", "water"),
            "redline_rpm": vehicle.get("redline_rpm", 7000),
            "idle_rpm": vehicle.get("idle_rpm", 800),
            "climate": vehicle.get("climate", "temperate"),
            "vehicle_id": vehicle.get("id", "unknown"),
            "vehicle_name": vehicle.get("name", "Veículo"),
        }

    @staticmethod
    def _get_default_vehicle_data() -> Dict[str, Any]:
        """Retorna dados padrão do veículo."""
        return {
            "displacement": 2.0,
            "cylinders": 4,
            "injector_flow_cc": 550,
            "injector_flow_lbs": 52,
            "fuel_type": "Gasolina",
            "turbo": False,
            "boost_pressure": 0.0,
            "bsfc_factor": 0.50,
            "injector_impedance": "high",
            "cooling_type": "water",
            "redline_rpm": 7000,
            "idle_rpm": 800,
            "climate": "temperate",
            "vehicle_id": "default",
            "vehicle_name": "Veículo Padrão",
        }

    @staticmethod
    def get_selected_vehicle_id() -> Optional[str]:
        """Obtém ID do veículo selecionado."""
        return st.session_state.get(SessionManager.VEHICLE_ID_KEY)

    @staticmethod
    def set_selected_vehicle_id(vehicle_id: str):
        """Define ID do veículo selecionado."""
        st.session_state[SessionManager.VEHICLE_ID_KEY] = vehicle_id

    @staticmethod
    def get_map_cache_key(vehicle_id: str, map_type: str, bank_id: str) -> str:
        """Gera chave de cache para um mapa específico."""
        return f"{SessionManager.MAP_DATA_PREFIX}_{vehicle_id}_{map_type}_{bank_id}"

    @staticmethod
    def cache_map_data(vehicle_id: str, map_type: str, bank_id: str, data: Dict[str, Any]):
        """Armazena dados do mapa no cache da sessão."""
        key = SessionManager.get_map_cache_key(vehicle_id, map_type, bank_id)
        st.session_state[key] = data
        logger.debug(f"Dados em cache: {key}")

    @staticmethod
    def get_cached_map_data(
        vehicle_id: str, map_type: str, bank_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtém dados do mapa do cache da sessão."""
        key = SessionManager.get_map_cache_key(vehicle_id, map_type, bank_id)
        return st.session_state.get(key)

    @staticmethod
    def clear_map_cache(vehicle_id: Optional[str] = None):
        """Limpa cache de mapas (todos ou de um veículo específico)."""
        keys_to_remove = []

        for key in st.session_state.keys():
            if key.startswith(SessionManager.MAP_DATA_PREFIX):
                if vehicle_id is None or f"_{vehicle_id}_" in key:
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            del st.session_state[key]

        logger.info(f"Cache limpo: {len(keys_to_remove)} itens removidos")

    @staticmethod
    def get_session_info() -> Dict[str, Any]:
        """Obtém informações sobre o estado atual da sessão."""
        info = {
            "vehicle_id": SessionManager.get_selected_vehicle_id(),
            "cached_maps": 0,
            "session_keys": len(st.session_state.keys()),
            "memory_usage": "N/A",  # Placeholder para futura implementação
        }

        # Contar mapas em cache
        for key in st.session_state.keys():
            if key.startswith(SessionManager.MAP_DATA_PREFIX):
                info["cached_maps"] += 1

        return info

    @staticmethod
    def cleanup_old_cache(max_age_minutes: int = 60):
        """Remove cache antigo baseado em timestamp."""
        # Esta função pode ser implementada para limpar cache baseado em timestamp
        # Por enquanto, implementação básica
        current_vehicle = SessionManager.get_selected_vehicle_id()

        # Limpar cache de outros veículos se houver um selecionado
        if current_vehicle:
            keys_to_remove = []
            for key in st.session_state.keys():
                if (
                    key.startswith(SessionManager.MAP_DATA_PREFIX)
                    and f"_{current_vehicle}_" not in key
                ):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del st.session_state[key]

            if keys_to_remove:
                logger.info(
                    f"Cache limpo: {len(keys_to_remove)} mapas de outros veículos removidos"
                )

    @staticmethod
    def initialize_session_defaults():
        """Inicializa valores padrão na sessão se não existirem."""
        defaults = {
            "fuel_3d_strategy": "balanced",
            "fuel_3d_safety_factor": 1.0,
            "fuel_3d_interpolation_method": "linear",
            "fuel_3d_grid_size": 32,
            "fuel_3d_show_advanced": False,
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def reset_session():
        """Reseta completamente a sessão (usar com cuidado)."""
        keys_to_remove = list(st.session_state.keys())
        for key in keys_to_remove:
            del st.session_state[key]

        # Reinicializar defaults
        SessionManager.initialize_session_defaults()
        logger.warning("Sessão resetada completamente")

    @staticmethod
    def get_ui_state(component: str) -> Dict[str, Any]:
        """Obtém estado específico da UI de um componente."""
        key = f"ui_state_{component}"
        return st.session_state.get(key, {})

    @staticmethod
    def set_ui_state(component: str, state: Dict[str, Any]):
        """Define estado específico da UI de um componente."""
        key = f"ui_state_{component}"
        st.session_state[key] = state

    @staticmethod
    def update_ui_state(component: str, updates: Dict[str, Any]):
        """Atualiza estado específico da UI de um componente."""
        current_state = SessionManager.get_ui_state(component)
        current_state.update(updates)
        SessionManager.set_ui_state(component, current_state)


# Instância global do gerenciador de sessão
session_manager = SessionManager()


# Funções de conveniência para manter compatibilidade
def get_vehicle_data_from_session() -> Dict[str, Any]:
    """Compatibilidade: obtém dados do veículo da sessão."""
    return SessionManager.get_vehicle_data_from_session()


def get_selected_vehicle_id() -> Optional[str]:
    """Compatibilidade: obtém ID do veículo selecionado."""
    return SessionManager.get_selected_vehicle_id()


def cache_map_data(vehicle_id: str, map_type: str, bank_id: str, data: Dict[str, Any]):
    """Compatibilidade: armazena dados no cache."""
    return SessionManager.cache_map_data(vehicle_id, map_type, bank_id, data)


def get_cached_map_data(vehicle_id: str, map_type: str, bank_id: str) -> Optional[Dict[str, Any]]:
    """Compatibilidade: obtém dados do cache."""
    return SessionManager.get_cached_map_data(vehicle_id, map_type, bank_id)
