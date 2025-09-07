"""
Utilitários para contexto de veículo.
Funções auxiliares para usar o contexto do veículo em todas as páginas.
"""

import streamlit as st
from typing import Optional, Dict, Any
from src.data.database import get_vehicle_by_id, get_vehicle_statistics
from src.ui.components.vehicle_selector import get_vehicle_context

def get_current_vehicle():
    """
    Obtém o veículo atualmente selecionado no contexto global.
    
    Returns:
        Vehicle object ou None se nenhum veículo estiver selecionado
    """
    vehicle_id = get_vehicle_context()
    if vehicle_id:
        return get_vehicle_by_id(vehicle_id)
    return None

def get_current_vehicle_id() -> Optional[str]:
    """
    Obtém o ID do veículo atualmente selecionado.
    
    Returns:
        ID do veículo ou None
    """
    return get_vehicle_context()

def show_vehicle_context_warning():
    """
    Mostra aviso quando nenhum veículo está selecionado.
    """
    st.warning("""
    **Nenhum veículo selecionado**
    
    Para uma análise mais precisa, selecione um veículo na barra lateral.
    Os dados serão contextualizados com as especificações técnicas do veículo.
    """)

def show_vehicle_context_info(vehicle=None):
    """
    Mostra informações do veículo ativo na página.
    
    Args:
        vehicle: Objeto Vehicle (opcional, será obtido automaticamente se não fornecido)
    """
    if vehicle is None:
        vehicle = get_current_vehicle()
    
    if vehicle:
        st.info(f"""
        **Contexto Ativo:** {vehicle.display_name}  
        **Motor:** {vehicle.technical_summary}  
        **Especificações:** {vehicle.estimated_power}HP, {vehicle.curb_weight}kg
        """)

def get_vehicle_context_metrics() -> Dict[str, Any]:
    """
    Obtém métricas do veículo ativo para exibição em páginas.
    
    Returns:
        Dicionário com métricas do veículo ou vazio se nenhum veículo ativo
    """
    vehicle_id = get_vehicle_context()
    if not vehicle_id:
        return {}
    
    vehicle = get_vehicle_by_id(vehicle_id)
    stats = get_vehicle_statistics(vehicle_id)
    
    if not vehicle:
        return {}
    
    return {
        "vehicle": vehicle,
        "stats": stats,
        "display_name": vehicle.display_name,
        "technical_summary": vehicle.technical_summary,
        "power_weight_ratio": vehicle.estimated_power / vehicle.curb_weight if vehicle.estimated_power and vehicle.curb_weight else None,
        "session_count": stats.get("session_count", 0),
        "data_count": stats.get("core_data_count", 0)
    }

def filter_sessions_by_vehicle(sessions: list) -> list:
    """
    Filtra sessões pelo veículo ativo.
    
    Args:
        sessions: Lista de sessões
    
    Returns:
        Lista de sessões filtradas pelo veículo ativo
    """
    vehicle_id = get_vehicle_context()
    if not vehicle_id:
        return sessions
    
    return [s for s in sessions if s.get("vehicle_id") == vehicle_id]

def add_vehicle_context_to_session_data(session_data: dict) -> dict:
    """
    Adiciona contexto do veículo aos dados da sessão.
    
    Args:
        session_data: Dados da sessão
    
    Returns:
        Dados da sessão com vehicle_id adicionado
    """
    vehicle_id = get_vehicle_context()
    if vehicle_id:
        session_data["vehicle_id"] = vehicle_id
    
    return session_data