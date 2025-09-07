"""
Componente reutilizável de seleção de veículo.
Para uso em todas as páginas do sistema.
"""

import streamlit as st
from typing import Optional
from src.data.database import get_all_vehicles

def render_vehicle_selector(
    label: str = "Veículo Ativo",
    key: str = "global_vehicle_selector",
    help_text: str = "Selecione o veículo para filtrar os dados",
    show_create_button: bool = True
) -> Optional[str]:
    """
    Renderiza seletor de veículo ativo.
    
    Args:
        label: Rótulo do seletor
        key: Chave única do componente
        help_text: Texto de ajuda
        show_create_button: Se deve mostrar botão de criar veículo
    
    Returns:
        ID do veículo selecionado ou None
    """
    
    vehicles = get_all_vehicles(active_only=True)
    
    if not vehicles:
        st.warning("Nenhum veículo cadastrado no sistema.")
        
        if show_create_button:
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Cadastrar Veículo", type="primary", key=f"{key}_create"):
                    st.switch_page("pages/vehicles")
        
        return None
    
    # Preparar opções
    vehicle_options = {}
    for vehicle in vehicles:
        display_name = vehicle.display_name
        # Adicionar informação técnica se disponível
        if vehicle.technical_summary and vehicle.technical_summary != "Não especificado":
            display_name += f" - {vehicle.technical_summary}"
        vehicle_options[vehicle.id] = display_name
    
    # Seletor principal
    selected_id = st.selectbox(
        label,
        options=list(vehicle_options.keys()),
        format_func=lambda x: vehicle_options[x],
        key=key,
        help=help_text
    )
    
    # Informações do veículo selecionado
    if selected_id:
        selected_vehicle = next(v for v in vehicles if v.id == selected_id)
        
        with st.expander("Informações do Veículo", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Nome:** {selected_vehicle.name}")
                st.write(f"**Marca:** {selected_vehicle.brand or 'N/A'}")
                st.write(f"**Ano:** {selected_vehicle.year or 'N/A'}")
                st.write(f"**Motor:** {selected_vehicle.technical_summary}")
            
            with col2:
                if selected_vehicle.estimated_power:
                    st.write(f"**Potência:** {selected_vehicle.estimated_power} HP")
                if selected_vehicle.curb_weight:
                    st.write(f"**Peso:** {selected_vehicle.curb_weight} kg")
                if selected_vehicle.fuel_type:
                    st.write(f"**Combustível:** {selected_vehicle.fuel_type}")
    
    return selected_id

def get_vehicle_context():
    """
    Obtém o contexto do veículo ativo da sessão.
    
    Returns:
        ID do veículo ativo ou None
    """
    return st.session_state.get("selected_vehicle_id")

def set_vehicle_context(vehicle_id: Optional[str]):
    """
    Define o veículo ativo no contexto da sessão.
    
    Args:
        vehicle_id: ID do veículo ou None
    """
    st.session_state.selected_vehicle_id = vehicle_id