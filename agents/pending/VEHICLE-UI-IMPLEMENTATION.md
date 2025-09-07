# VEHICLE-UI-IMPLEMENTATION

## Objetivo
Criar interface completa de cadastro e gerenciamento de veículos seguindo padrões profissionais, com foco em usabilidade e experiência do usuário.

## Padrões de Desenvolvimento
Este agente segue os padrões definidos em:
- /srv/projects/shared/docs/agents/development/A04-STREAMLIT-PROFESSIONAL.md

### Princípios Fundamentais:
1. **ZERO emojis** - Usar apenas Material Design Icons
2. **Interface profissional** - Sem decorações infantis  
3. **CSS adaptativo** - Funciona em tema claro e escuro
4. **Português brasileiro** - Todos os textos traduzidos
5. **Ícones consistentes** - Material Icons em todos os componentes

## Estrutura da Interface

### 1. Criar src/ui/pages/vehicles.py

```python
"""
Página de cadastro e gerenciamento de veículos.
Interface completa para CRUD de veículos com design profissional.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime

from src.data.database import (
    create_vehicle, get_vehicle_by_id, get_all_vehicles,
    update_vehicle, delete_vehicle, search_vehicles,
    get_vehicle_statistics
)
from src.data.vehicle_validators import validate_vehicle_data, normalize_plate
from src.ui.styles.professional import apply_professional_styles

def show_vehicles_page():
    """Página principal de gerenciamento de veículos."""
    
    # Aplicar estilos profissionais
    apply_professional_styles()
    
    # Header principal
    st.markdown('''
        <div class="main-header">
            <span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">
                directions_car
            </span>
            Gerenciamento de Veículos
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('''
        <div class="sub-header">
            Configure e gerencie os veículos para análise de telemetria
        </div>
    ''', unsafe_allow_html=True)
    
    # Abas principais
    tab_list, tab_new, tab_edit = st.tabs([
        "📋 Lista de Veículos", 
        "➕ Cadastrar Novo", 
        "✏️ Editar Veículo"
    ])
    
    with tab_list:
        show_vehicle_list()
    
    with tab_new:
        show_vehicle_form()
    
    with tab_edit:
        show_vehicle_editor()

def show_vehicle_list():
    """Lista todos os veículos cadastrados com funcionalidades de busca e filtro."""
    
    st.markdown('''
        <div class="section-header">
            <span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">
                list
            </span>
            Veículos Cadastrados
        </div>
    ''', unsafe_allow_html=True)
    
    # Controles de filtro
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input(
            "Buscar veículo",
            placeholder="Digite nome, marca ou modelo...",
            help="Busca em nome, marca, modelo e apelido"
        )
    
    with col2:
        show_inactive = st.checkbox("Mostrar inativos", value=False)
    
    with col3:
        if st.button("🔄 Atualizar Lista"):
            st.rerun()
    
    # Buscar veículos
    if search_term:
        vehicles = search_vehicles(search_term, active_only=not show_inactive)
    else:
        vehicles = get_all_vehicles(active_only=not show_inactive)
    
    if not vehicles:
        st.info("Nenhum veículo encontrado. Cadastre o primeiro veículo na aba 'Cadastrar Novo'.")
        return
    
    # Exibir veículos em cards
    for i, vehicle in enumerate(vehicles):
        with st.container():
            render_vehicle_card(vehicle)
            
            if i < len(vehicles) - 1:
                st.divider()

def render_vehicle_card(vehicle):
    """Renderiza card individual do veículo."""
    
    # Status badge
    status_color = "#4CAF50" if vehicle.is_active else "#757575"
    status_text = "Ativo" if vehicle.is_active else "Inativo"
    
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        st.markdown(f'''
            <div class="vehicle-card">
                <div class="vehicle-header">
                    <span class="material-icons" style="margin-right: 0.5rem;">directions_car</span>
                    <strong>{vehicle.display_name}</strong>
                    <span class="status-badge" style="background-color: {status_color};">{status_text}</span>
                </div>
                <div class="vehicle-details">
                    <span class="detail-item">
                        <span class="material-icons" style="font-size: 16px;">business</span>
                        {vehicle.brand or 'N/A'} {vehicle.model or ''}
                    </span>
                    <span class="detail-item">
                        <span class="material-icons" style="font-size: 16px;">speed</span>
                        {vehicle.technical_summary}
                    </span>
                </div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        # Estatísticas rápidas
        stats = get_vehicle_statistics(vehicle.id)
        if stats:
            st.metric("Sessões", stats.get("session_count", 0))
            st.metric("Registros", f"{stats.get('core_data_count', 0):,}")
    
    with col3:
        # Botões de ação
        if st.button(f"👁️ Ver", key=f"view_{vehicle.id}"):
            show_vehicle_details(vehicle.id)
        
        if st.button(f"✏️ Editar", key=f"edit_{vehicle.id}"):
            st.session_state.edit_vehicle_id = vehicle.id
            st.rerun()
        
        if st.button(f"🗑️ Excluir", key=f"delete_{vehicle.id}"):
            if st.session_state.get(f"confirm_delete_{vehicle.id}"):
                delete_vehicle(vehicle.id, soft_delete=True)
                st.success(f"Veículo {vehicle.name} foi desativado")
                st.rerun()
            else:
                st.session_state[f"confirm_delete_{vehicle.id}"] = True
                st.warning("Clique novamente para confirmar exclusão")

def show_vehicle_form(edit_mode: bool = False, vehicle_data: Optional[dict] = None):
    """Formulário de cadastro/edição de veículo."""
    
    form_title = "Editar Veículo" if edit_mode else "Cadastrar Novo Veículo"
    
    st.markdown(f'''
        <div class="section-header">
            <span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">
                {"edit" if edit_mode else "add"}
            </span>
            {form_title}
        </div>
    ''', unsafe_allow_html=True)
    
    with st.form("vehicle_form", clear_on_submit=not edit_mode):
        # Seção 1: Identificação
        st.markdown('''
            <div class="form-section-header">
                <span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">
                    info
                </span>
                Identificação Básica
            </div>
        ''', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Nome/Modelo *",
                value=vehicle_data.get("name", "") if vehicle_data else "",
                placeholder="Ex: Civic Si 2020",
                help="Nome principal do veículo"
            )
            
            nickname = st.text_input(
                "Apelido",
                value=vehicle_data.get("nickname", "") if vehicle_data else "",
                placeholder="Ex: Carro da Pista",
                help="Nome popular ou apelido"
            )
            
            plate = st.text_input(
                "Placa",
                value=vehicle_data.get("plate", "") if vehicle_data else "",
                placeholder="ABC-1234",
                help="Placa do veículo (opcional)"
            )
        
        with col2:
            brand = st.selectbox(
                "Marca",
                options=["", "Honda", "Toyota", "Volkswagen", "Ford", "Chevrolet", 
                        "Nissan", "Hyundai", "BMW", "Mercedes-Benz", "Audi", "Outro"],
                index=0,
                help="Marca do veículo"
            )
            
            model = st.text_input(
                "Modelo Específico",
                value=vehicle_data.get("model", "") if vehicle_data else "",
                placeholder="Ex: Civic Si 2.0 VTEC Turbo",
                help="Modelo detalhado"
            )
            
            year = st.number_input(
                "Ano",
                min_value=1980,
                max_value=2030,
                value=vehicle_data.get("year", 2020) if vehicle_data else 2020,
                help="Ano de fabricação"
            )
        
        st.divider()
        
        # Seção 2: Motor
        st.markdown('''
            <div class="form-section-header">
                <span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">
                    precision_manufacturing
                </span>
                Especificações do Motor
            </div>
        ''', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            engine_displacement = st.number_input(
                "Cilindrada (L)",
                min_value=0.5,
                max_value=15.0,
                step=0.1,
                value=vehicle_data.get("engine_displacement", 2.0) if vehicle_data else 2.0,
                help="Cilindrada do motor em litros"
            )
            
            engine_cylinders = st.number_input(
                "Número de Cilindros",
                min_value=1,
                max_value=16,
                value=vehicle_data.get("engine_cylinders", 4) if vehicle_data else 4,
                help="Quantidade de cilindros"
            )
            
            engine_configuration = st.selectbox(
                "Configuração do Motor",
                options=["", "I3", "I4", "I5", "I6", "V6", "V8", "V10", "V12", "H4", "W12"],
                help="Disposição dos cilindros"
            )
        
        with col2:
            engine_aspiration = st.selectbox(
                "Sistema de Aspiração",
                options=["", "Naturally Aspirated", "Turbocharged", "Supercharged", 
                        "Twin-Turbo", "Twin-Scroll Turbo"],
                help="Tipo de aspiração do motor"
            )
            
            fuel_type = st.selectbox(
                "Tipo de Combustível",
                options=["", "Gasoline", "Ethanol", "Flex", "Diesel", "CNG", "Electric", "Hybrid"],
                help="Combustível principal"
            )
            
            octane_rating = st.number_input(
                "Octanagem",
                min_value=80,
                max_value=120,
                value=vehicle_data.get("octane_rating", 91) if vehicle_data else 91,
                help="Octanagem do combustível utilizado"
            )
        
        st.divider()
        
        # Seção 3: Performance e Características
        st.markdown('''
            <div class="form-section-header">
                <span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">
                    speed
                </span>
                Performance e Características
            </div>
        ''', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            estimated_power = st.number_input(
                "Potência Estimada (HP)",
                min_value=0,
                max_value=2000,
                value=vehicle_data.get("estimated_power", 200) if vehicle_data else 200,
                help="Potência estimada em cavalos"
            )
            
            estimated_torque = st.number_input(
                "Torque Estimado (Nm)",
                min_value=0,
                max_value=3000,
                value=vehicle_data.get("estimated_torque", 300) if vehicle_data else 300,
                help="Torque estimado em Newton-metros"
            )
            
            max_rpm = st.number_input(
                "RPM Máximo",
                min_value=1000,
                max_value=12000,
                value=vehicle_data.get("max_rpm", 7000) if vehicle_data else 7000,
                help="Rotação máxima do motor"
            )
        
        with col2:
            curb_weight = st.number_input(
                "Peso (kg)",
                min_value=500,
                max_value=5000,
                value=vehicle_data.get("curb_weight", 1400) if vehicle_data else 1400,
                help="Peso em ordem de marcha"
            )
            
            drivetrain = st.selectbox(
                "Tração",
                options=["", "FWD", "RWD", "AWD", "4WD"],
                help="Sistema de tração"
            )
            
            transmission_type = st.selectbox(
                "Transmissão",
                options=["", "Manual", "Automatic", "CVT", "Semi-Automatic", "Dual-Clutch"],
                help="Tipo de transmissão"
            )
        
        st.divider()
        
        # Seção 4: Observações
        st.markdown('''
            <div class="form-section-header">
                <span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">
                    notes
                </span>
                Observações Adicionais
            </div>
        ''', unsafe_allow_html=True)
        
        notes = st.text_area(
            "Notas e Observações",
            value=vehicle_data.get("notes", "") if vehicle_data else "",
            placeholder="Modificações, características especiais, histórico...",
            help="Informações adicionais sobre o veículo",
            height=100
        )
        
        # Botões de ação
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit_button = st.form_submit_button(
                "💾 Salvar Veículo" if not edit_mode else "✅ Atualizar Veículo",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            if st.form_submit_button(
                "🔄 Limpar Formulário",
                use_container_width=True
            ):
                st.rerun()
        
        # Processar submissão
        if submit_button:
            process_vehicle_form(
                {
                    "name": name,
                    "nickname": nickname,
                    "plate": normalize_plate(plate),
                    "brand": brand,
                    "model": model,
                    "year": year,
                    "engine_displacement": engine_displacement,
                    "engine_cylinders": engine_cylinders,
                    "engine_configuration": engine_configuration,
                    "engine_aspiration": engine_aspiration,
                    "fuel_type": fuel_type,
                    "octane_rating": octane_rating,
                    "estimated_power": estimated_power,
                    "estimated_torque": estimated_torque,
                    "max_rpm": max_rpm,
                    "curb_weight": curb_weight,
                    "drivetrain": drivetrain,
                    "transmission_type": transmission_type,
                    "notes": notes
                },
                edit_mode,
                vehicle_data.get("id") if vehicle_data else None
            )

def process_vehicle_form(form_data: dict, edit_mode: bool = False, vehicle_id: Optional[str] = None):
    """Processa submissão do formulário de veículo."""
    
    # Validar dados
    errors = validate_vehicle_data(form_data)
    
    if errors:
        st.error("Erro de validação nos seguintes campos:")
        for field, field_errors in errors.items():
            for error in field_errors:
                st.error(f"• {error}")
        return
    
    try:
        if edit_mode and vehicle_id:
            # Atualizar veículo existente
            success = update_vehicle(vehicle_id, form_data)
            if success:
                st.success(f"Veículo '{form_data['name']}' atualizado com sucesso!")
                st.balloons()
            else:
                st.error("Erro ao atualizar veículo. Tente novamente.")
        else:
            # Criar novo veículo
            new_vehicle_id = create_vehicle(form_data)
            if new_vehicle_id:
                st.success(f"Veículo '{form_data['name']}' cadastrado com sucesso!")
                st.balloons()
                
                # Mostrar ID para referência
                st.info(f"ID do veículo: `{new_vehicle_id}`")
            else:
                st.error("Erro ao cadastrar veículo. Tente novamente.")
                
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")

def show_vehicle_editor():
    """Interface para edição de veículo existente."""
    
    if "edit_vehicle_id" not in st.session_state:
        st.info("Selecione um veículo na lista para editar.")
        return
    
    vehicle_id = st.session_state.edit_vehicle_id
    vehicle = get_vehicle_by_id(vehicle_id)
    
    if not vehicle:
        st.error("Veículo não encontrado.")
        if st.button("🔙 Voltar à Lista"):
            del st.session_state.edit_vehicle_id
            st.rerun()
        return
    
    # Converter vehicle para dict
    vehicle_data = {
        "id": vehicle.id,
        "name": vehicle.name,
        "nickname": vehicle.nickname,
        "plate": vehicle.plate,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "year": vehicle.year,
        "engine_displacement": vehicle.engine_displacement,
        "engine_cylinders": vehicle.engine_cylinders,
        "engine_configuration": vehicle.engine_configuration,
        "engine_aspiration": vehicle.engine_aspiration,
        "fuel_type": vehicle.fuel_type,
        "octane_rating": vehicle.octane_rating,
        "estimated_power": vehicle.estimated_power,
        "estimated_torque": vehicle.estimated_torque,
        "max_rpm": vehicle.max_rpm,
        "curb_weight": vehicle.curb_weight,
        "drivetrain": vehicle.drivetrain,
        "transmission_type": vehicle.transmission_type,
        "notes": vehicle.notes
    }
    
    # Botão para voltar
    if st.button("🔙 Voltar à Lista", key="back_to_list"):
        del st.session_state.edit_vehicle_id
        st.rerun()
    
    # Mostrar formulário em modo de edição
    show_vehicle_form(edit_mode=True, vehicle_data=vehicle_data)

def show_vehicle_details(vehicle_id: str):
    """Mostra detalhes completos do veículo em modal."""
    
    vehicle = get_vehicle_by_id(vehicle_id)
    if not vehicle:
        st.error("Veículo não encontrado.")
        return
    
    # Modal usando expander
    with st.expander(f"📋 Detalhes - {vehicle.display_name}", expanded=True):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Identificação:**")
            st.write(f"• Nome: {vehicle.name}")
            st.write(f"• Apelido: {vehicle.nickname or 'N/A'}")
            st.write(f"• Marca: {vehicle.brand or 'N/A'}")
            st.write(f"• Modelo: {vehicle.model or 'N/A'}")
            st.write(f"• Ano: {vehicle.year or 'N/A'}")
            st.write(f"• Placa: {vehicle.plate or 'N/A'}")
            
            st.markdown("**Motor:**")
            st.write(f"• Cilindrada: {vehicle.engine_displacement}L")
            st.write(f"• Cilindros: {vehicle.engine_cylinders}")
            st.write(f"• Configuração: {vehicle.engine_configuration or 'N/A'}")
            st.write(f"• Aspiração: {vehicle.engine_aspiration or 'N/A'}")
        
        with col2:
            st.markdown("**Performance:**")
            st.write(f"• Potência: {vehicle.estimated_power} HP")
            st.write(f"• Torque: {vehicle.estimated_torque} Nm")
            st.write(f"• RPM Máximo: {vehicle.max_rpm}")
            st.write(f"• Peso: {vehicle.curb_weight} kg")
            
            st.markdown("**Sistema:**")
            st.write(f"• Combustível: {vehicle.fuel_type or 'N/A'}")
            st.write(f"• Octanagem: {vehicle.octane_rating}")
            st.write(f"• Tração: {vehicle.drivetrain or 'N/A'}")
            st.write(f"• Transmissão: {vehicle.transmission_type or 'N/A'}")
        
        if vehicle.notes:
            st.markdown("**Observações:**")
            st.write(vehicle.notes)
        
        # Estatísticas
        stats = get_vehicle_statistics(vehicle_id)
        if stats:
            st.markdown("**Estatísticas de Uso:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Sessões", stats.get("session_count", 0))
            with col2:
                st.metric("Registros", f"{stats.get('core_data_count', 0):,}")
            with col3:
                if stats.get("last_session_date"):
                    st.metric("Último Uso", stats["last_session_date"].strftime("%d/%m/%Y"))

# Componente reutilizável para seleção de veículo
def vehicle_selector(key: str = "vehicle_selector") -> Optional[str]:
    """
    Componente de seleção de veículo ativo.
    
    Args:
        key: Chave única para o componente
    
    Returns:
        ID do veículo selecionado ou None
    """
    vehicles = get_all_vehicles(active_only=True)
    
    if not vehicles:
        st.warning("⚠️ Nenhum veículo cadastrado. Cadastre um veículo primeiro.")
        if st.button("➕ Cadastrar Veículo", key=f"{key}_create"):
            st.switch_page("vehicles")
        return None
    
    vehicle_options = {v.id: v.display_name for v in vehicles}
    
    selected_id = st.selectbox(
        "🚗 Veículo Ativo",
        options=list(vehicle_options.keys()),
        format_func=lambda x: vehicle_options[x],
        key=key,
        help="Selecione o veículo para análise dos dados"
    )
    
    return selected_id

# CSS específico para página de veículos
def inject_vehicle_styles():
    """Injeta estilos CSS específicos para a página de veículos."""
    
    st.markdown('''
        <style>
        .vehicle-card {
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: var(--background-color);
            margin-bottom: 1rem;
        }
        
        .vehicle-header {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .vehicle-header strong {
            flex-grow: 1;
            font-size: 1.2rem;
        }
        
        .status-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            color: white;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .vehicle-details {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-top: 0.5rem;
        }
        
        .detail-item {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            font-size: 0.9rem;
            color: var(--text-color-secondary);
        }
        
        .form-section-header {
            display: flex;
            align-items: center;
            font-size: 1.1rem;
            font-weight: bold;
            margin: 1.5rem 0 1rem 0;
            color: var(--primary-color);
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 0.5rem;
        }
        </style>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    inject_vehicle_styles()
    show_vehicles_page()
```

### 2. Criar Componentes Auxiliares

#### 2.1 Criar src/ui/components/vehicle_selector.py

```python
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
        
        with st.expander("ℹ️ Informações do Veículo", expanded=False):
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
```

#### 2.2 Criar src/ui/styles/vehicle_styles.py

```python
"""
Estilos CSS específicos para componentes de veículos.
"""

def get_vehicle_styles():
    """Retorna CSS para componentes de veículos."""
    
    return '''
    <style>
    /* Cards de Veículos */
    .vehicle-card {
        background: var(--secondary-background-color);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .vehicle-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .vehicle-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .vehicle-title {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-color);
    }
    
    .vehicle-status {
        padding: 0.25rem 0.75rem;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .vehicle-status.active {
        background-color: #E8F5E8;
        color: #2E7D32;
        border: 1px solid #4CAF50;
    }
    
    .vehicle-status.inactive {
        background-color: #F5F5F5;
        color: #757575;
        border: 1px solid #BDBDBD;
    }
    
    /* Detalhes do Veículo */
    .vehicle-details {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .vehicle-detail-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem;
        background: var(--background-color);
        border-radius: 6px;
        font-size: 0.9rem;
    }
    
    .vehicle-detail-item .material-icons {
        font-size: 18px;
        color: var(--primary-color);
    }
    
    /* Formulário de Veículo */
    .vehicle-form-section {
        background: var(--secondary-background-color);
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-left: 4px solid var(--primary-color);
    }
    
    .vehicle-form-section-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: var(--primary-color);
    }
    
    /* Seletor de Veículo */
    .vehicle-selector-container {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        color: white;
    }
    
    .vehicle-selector-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    /* Estatísticas do Veículo */
    .vehicle-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .vehicle-stat-card {
        background: var(--background-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    
    .vehicle-stat-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: var(--primary-color);
        margin-bottom: 0.25rem;
    }
    
    .vehicle-stat-label {
        font-size: 0.8rem;
        color: var(--text-color-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Botões de Ação */
    .vehicle-actions {
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-color);
    }
    
    .vehicle-action-btn {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.5rem 1rem;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        background: var(--background-color);
        color: var(--text-color);
        text-decoration: none;
        font-size: 0.85rem;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .vehicle-action-btn:hover {
        background: var(--primary-color);
        color: white;
        border-color: var(--primary-color);
    }
    
    .vehicle-action-btn.danger:hover {
        background: #F44336;
        border-color: #F44336;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .vehicle-card {
            padding: 1rem;
        }
        
        .vehicle-details {
            grid-template-columns: 1fr;
        }
        
        .vehicle-stats {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .vehicle-actions {
            flex-direction: column;
        }
        
        .vehicle-action-btn {
            justify-content: center;
        }
    }
    
    /* Tema Escuro */
    @media (prefers-color-scheme: dark) {
        .vehicle-status.active {
            background-color: #1B5E20;
            color: #A5D6A7;
        }
        
        .vehicle-detail-item {
            background: var(--secondary-background-color);
        }
    }
    </style>
    '''
```

### 3. Integração com Menu Principal

#### 3.1 Adicionar ao app.py

```python
# Adicionar na seção de páginas do app.py:

# Importar a página de veículos
from src.ui.pages.vehicles import show_vehicles_page

# Adicionar no menu de navegação:
if page == "🚗 Veículos":
    show_vehicles_page()
```

### 4. Testes da Interface

#### 4.1 Criar tests/test_vehicle_ui.py

```python
"""
Testes para a interface de veículos.
"""

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock

from src.ui.pages.vehicles import (
    show_vehicles_page,
    show_vehicle_form,
    process_vehicle_form,
    vehicle_selector
)

@patch('src.ui.pages.vehicles.get_all_vehicles')
def test_vehicle_selector_empty(mock_get_vehicles):
    """Testa seletor quando não há veículos."""
    mock_get_vehicles.return_value = []
    
    result = vehicle_selector()
    assert result is None

@patch('src.ui.pages.vehicles.get_all_vehicles')
def test_vehicle_selector_with_vehicles(mock_get_vehicles):
    """Testa seletor com veículos disponíveis."""
    mock_vehicle = MagicMock()
    mock_vehicle.id = "test-id"
    mock_vehicle.display_name = "Test Vehicle"
    
    mock_get_vehicles.return_value = [mock_vehicle]
    
    with patch('streamlit.selectbox', return_value="test-id"):
        result = vehicle_selector()
        assert result == "test-id"

@patch('src.ui.pages.vehicles.validate_vehicle_data')
@patch('src.ui.pages.vehicles.create_vehicle')
def test_process_vehicle_form_success(mock_create, mock_validate):
    """Testa processamento bem-sucedido do formulário."""
    mock_validate.return_value = {}  # Sem erros
    mock_create.return_value = "new-vehicle-id"
    
    form_data = {
        "name": "Test Vehicle",
        "brand": "Honda",
        "year": 2020
    }
    
    with patch('streamlit.success') as mock_success:
        process_vehicle_form(form_data, edit_mode=False)
        mock_create.assert_called_once_with(form_data)
        mock_success.assert_called_once()

@patch('src.ui.pages.vehicles.validate_vehicle_data')
def test_process_vehicle_form_validation_errors(mock_validate):
    """Testa processamento com erros de validação."""
    mock_validate.return_value = {
        "name": ["Nome é obrigatório"]
    }
    
    form_data = {"name": ""}
    
    with patch('streamlit.error') as mock_error:
        process_vehicle_form(form_data, edit_mode=False)
        mock_error.assert_called()
```

## Checklist de Implementação

### Interface Principal
- [ ] Página vehicles.py criada com design profissional
- [ ] Tabs organizadas (Lista, Cadastrar, Editar)
- [ ] Material Design Icons implementados
- [ ] Zero emojis na interface
- [ ] CSS adaptativo para temas claro/escuro

### Funcionalidades CRUD
- [ ] Formulário de cadastro completo com validações
- [ ] Lista de veículos com filtros e busca
- [ ] Edição de veículos existentes
- [ ] Soft delete com confirmação
- [ ] Visualização detalhada em modals

### Componentes Reutilizáveis
- [ ] Vehicle selector para uso global
- [ ] Componentes de cards de veículo
- [ ] Estilos CSS organizados
- [ ] Contexto global de veículo ativo

### Validações e UX
- [ ] Validação de campos obrigatórios
- [ ] Normalização de dados (placas, etc.)
- [ ] Mensagens de erro/sucesso claras
- [ ] Feedback visual adequado
- [ ] Responsividade mobile

### Integração
- [ ] Menu principal atualizado
- [ ] Rotas configuradas
- [ ] Dependências importadas
- [ ] Testes básicos implementados

## Próximos Passos

1. **Integrar com VEHICLE-MODEL-IMPLEMENTATION** - Usar as funções CRUD criadas
2. **Testar interface completa** - Validar todos os fluxos de uso
3. **Otimizar performance** - Cache de listas e validações
4. **Implementar VEHICLE-INTEGRATION-IMPLEMENTATION** - Adicionar seletor nas outras páginas

---

**Prioridade:** Alta  
**Complexidade:** Média-Alta  
**Tempo Estimado:** 2-3 dias  
**Dependências:** VEHICLE-MODEL-IMPLEMENTATION  
**Bloqueia:** VEHICLE-INTEGRATION-IMPLEMENTATION