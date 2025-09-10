"""
Página de cadastro e gerenciamento de veículos.
Interface completa para CRUD de veículos com design profissional.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime

from src.data.vehicle_database import (
    create_vehicle, get_vehicle_by_id, get_all_vehicles,
    update_vehicle, delete_vehicle, search_vehicles,
    get_vehicle_statistics
)
from src.data.vehicle_validators import validate_vehicle_data, normalize_plate

# Header principal
st.title("Gerenciamento de Veículos")
st.caption("Configure e gerencie os veículos para análise de telemetria")

# Abas principais
tab_list, tab_new, tab_edit = st.tabs([
    "Lista de Veículos", 
    "Cadastrar Novo", 
    "Editar Veículo"
])

with tab_list:
    st.header("Veículos Cadastrados")
    
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
        if st.button("Atualizar Lista", use_container_width=True):
            st.rerun()
    
    # Buscar veículos
    if search_term:
        vehicles = search_vehicles(search_term, active_only=not show_inactive)
    else:
        vehicles = get_all_vehicles(active_only=not show_inactive)
    
    if not vehicles:
        st.info("Nenhum veículo encontrado. Cadastre o primeiro veículo na aba 'Cadastrar Novo'.")
    else:
        # Exibir veículos em containers
        for vehicle in vehicles:
            with st.container():
                # Usar expander para cada veículo
                status_icon = "✓" if vehicle.get("is_active", True) else "✗"
                with st.expander(f"{status_icon} **{vehicle['name']}** ({vehicle.get('nickname', 'Sem apelido')})"):
                    # Informações do veículo em colunas
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Ano", vehicle.get("year", "N/A"))
                        st.metric("Marca", vehicle.get("brand", "N/A"))
                        st.metric("Modelo", vehicle.get("model", "N/A"))
                    
                    with col2:
                        st.metric("Motor", f"{vehicle.get('engine_displacement', 0)}L")
                        hp = float(vehicle.get('estimated_power', 0) or 0)
                        cv = hp * 1.01387
                        st.metric("Potência", f"{cv:.0f} CV")
                        st.metric("Torque", f"{vehicle.get('estimated_torque', 0)} Nm")
                    
                    with col3:
                        st.metric("Combustível", vehicle.get("fuel_type", "N/A"))
                        st.metric("Aspiração", vehicle.get("engine_aspiration", "N/A"))
                        st.metric("Transmissão", vehicle.get("transmission_type", "N/A"))
                    
                    # Botões de ação
                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("Ver Detalhes", key=f"view_{vehicle['id']}", use_container_width=True):
                            st.session_state.selected_vehicle_id = vehicle['id']
                            st.session_state.show_vehicle_details = True
                    
                    with col2:
                        if st.button("Editar", key=f"edit_{vehicle['id']}", use_container_width=True):
                            st.session_state.editing_vehicle_id = vehicle['id']
                            st.session_state.active_tab = 2
                    
                    with col3:
                        if st.button("Excluir", key=f"delete_{vehicle['id']}", type="secondary", use_container_width=True):
                            if st.session_state.get(f"confirm_delete_{vehicle['id']}"):
                                delete_vehicle(vehicle['id'])
                                st.success(f"Veículo {vehicle['name']} excluído com sucesso!")
                                st.rerun()
                            else:
                                st.session_state[f"confirm_delete_{vehicle['id']}"] = True
                                st.warning("Clique novamente para confirmar a exclusão.")

with tab_new:
    st.header("Cadastrar Novo Veículo")
    
    with st.form("new_vehicle_form"):
        # Informações básicas
        st.subheader("Informações Básicas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Nome do Veículo *", placeholder="Ex: Golf GTI MK7")
            nickname = st.text_input("Apelido", placeholder="Ex: Golfinho")
        
        with col2:
            brand = st.text_input("Marca *", placeholder="Ex: Volkswagen")
            model = st.text_input("Modelo *", placeholder="Ex: Golf GTI")
        
        with col3:
            year = st.number_input("Ano", min_value=1900, max_value=2030, value=2020)
            plate = st.text_input("Placa", placeholder="Ex: ABC-1234")
        
        # Informações do motor
        st.subheader("Motor e Performance")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            engine_displacement = st.number_input("Cilindrada (L)", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
            engine_cylinders = st.number_input("Cilindros", min_value=1, max_value=16, value=4)
        
        with col2:
            engine_configuration = st.selectbox("Configuração", ["I4", "I6", "V6", "V8", "V10", "V12", "H4", "H6"])
            engine_aspiration = st.selectbox("Aspiração", ["Aspirado", "Turbo", "Supercharger", "Turbo + Supercharger"])
        
        with col3:
            estimated_power = st.number_input("Potência (CV)", min_value=0, max_value=2600, value=200)
            estimated_torque = st.number_input("Torque (Nm)", min_value=0, max_value=2000, value=300)
        
        with col4:
            max_rpm = st.number_input("RPM Máximo", min_value=1000, max_value=20000, value=7000, step=100)
            fuel_type = st.selectbox("Combustível", ["Gasolina", "Etanol", "Flex", "Diesel", "GNV", "E85"])
        
        # Injeção
        st.subheader("Sistema de Injeção")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            injector_type = st.text_input("Tipo de Bico", placeholder="Ex: Bosch 550cc")
            injector_count = st.number_input("Quantidade de Bicos", min_value=1, max_value=16, value=4)
        
        with col2:
            injector_flow_rate = st.number_input("Vazão (lbs/h)", min_value=0, max_value=300, value=80)
            fuel_rail_pressure = st.number_input("Pressão da Linha (bar)", min_value=0.0, max_value=10.0, value=3.5, step=0.1)
        
        with col3:
            fuel_system = st.selectbox("Sistema", ["Port Injection", "Direct Injection", "Dual Injection"])
            octane_rating = st.number_input("Octanagem", min_value=87, max_value=110, value=95)
        
        # Turbo (se aplicável)
        if engine_aspiration in ["Turbo", "Turbo + Supercharger"]:
            st.subheader("Turbo/Supercharger")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                turbo_brand = st.text_input("Marca do Turbo", placeholder="Ex: Garrett")
                turbo_model = st.text_input("Modelo do Turbo", placeholder="Ex: GTX2867R")
            
            with col2:
                max_boost_pressure = st.number_input("Pressão Máxima (bar)", min_value=0.0, max_value=5.0, value=1.5, step=0.1)
                wastegate_type = st.selectbox("Tipo de Wastegate", ["Interna", "Externa", "Eletrônica"])
            
            with col3:
                st.empty()  # Espaço vazio para alinhamento
        else:
            turbo_brand = None
            turbo_model = None
            max_boost_pressure = None
            wastegate_type = None
        
        # Transmissão e drivetrain
        st.subheader("Transmissão e Tração")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            transmission_type = st.selectbox("Transmissão", ["Manual", "Automática", "DSG/DCT", "CVT"])
            gear_count = st.number_input("Marchas", min_value=3, max_value=10, value=6)
        
        with col2:
            drivetrain = st.selectbox("Tração", ["FWD", "RWD", "AWD", "4WD"])
            final_drive_ratio = st.number_input("Relação Final", min_value=2.0, max_value=6.0, value=3.5, step=0.01)
        
        with col3:
            curb_weight = st.number_input("Peso (kg)", min_value=500, max_value=5000, value=1500)
            tire_size = st.text_input("Pneus", placeholder="Ex: 225/40R18")
        
        # Configuração de Bancadas
        st.subheader("Configuração de Bancadas de Injeção")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Bancada A**")
            bank_a_enabled = st.checkbox("Habilitar Bancada A", value=True)
            if bank_a_enabled:
                bank_a_mode = st.selectbox("Modo Bancada A", ["sequential", "semi-sequential", "batch"], key="bank_a_mode")
                bank_a_injector_count = st.number_input("Qtd Bicos A", min_value=1, max_value=8, value=4, key="bank_a_count")
                bank_a_injector_flow = st.number_input("Vazão Bicos A (lbs/h)", min_value=0, max_value=300, value=80, key="bank_a_flow")
                bank_a_dead_time = st.number_input("Dead Time A (ms)", min_value=0.0, max_value=10.0, value=1.0, step=0.1, key="bank_a_dt")
            else:
                bank_a_mode = None
                bank_a_injector_count = 0
                bank_a_injector_flow = 0
                bank_a_dead_time = 0
        
        with col2:
            st.markdown("**Bancada B**")
            bank_b_enabled = st.checkbox("Habilitar Bancada B", value=False)
            if bank_b_enabled:
                bank_b_mode = st.selectbox("Modo Bancada B", ["sequential", "semi-sequential", "batch"], key="bank_b_mode")
                bank_b_injector_count = st.number_input("Qtd Bicos B", min_value=1, max_value=8, value=4, key="bank_b_count")
                bank_b_injector_flow = st.number_input("Vazão Bicos B (lbs/h)", min_value=0, max_value=300, value=80, key="bank_b_flow")
                bank_b_dead_time = st.number_input("Dead Time B (ms)", min_value=0.0, max_value=10.0, value=1.0, step=0.1, key="bank_b_dt")
            else:
                bank_b_mode = None
                bank_b_injector_count = 0
                bank_b_injector_flow = 0
                bank_b_dead_time = 0
        
        # Limites de MAP
        st.subheader("Limites de Pressão MAP")
        col1, col2 = st.columns(2)
        
        with col1:
            min_map_pressure = st.number_input("Pressão MAP Mínima (kPa)", min_value=0.0, max_value=300.0, value=0.0, step=1.0)
        
        with col2:
            max_map_pressure = st.number_input("Pressão MAP Máxima (kPa)", min_value=0.0, max_value=500.0, value=250.0, step=1.0)
        
        # Notas adicionais
        notes = st.text_area("Observações", placeholder="Modificações, histórico, etc...")
        
        # Botão de envio
        submitted = st.form_submit_button("Cadastrar Veículo", type="primary", use_container_width=True)
        
        if submitted:
            # Validar dados
            vehicle_data = {
                "name": name,
                "nickname": nickname,
                "brand": brand,
                "model": model,
                "year": year,
                "plate": normalize_plate(plate) if plate else None,
                "engine_displacement": engine_displacement,
                "engine_cylinders": engine_cylinders,
                "engine_configuration": engine_configuration,
                "engine_aspiration": engine_aspiration,
                "injector_type": injector_type,
                "injector_count": injector_count,
                "injector_flow_rate": injector_flow_rate,
                "fuel_rail_pressure": fuel_rail_pressure,
                "fuel_system": fuel_system,
                "octane_rating": octane_rating,
                "estimated_power": estimated_power,
                "estimated_torque": estimated_torque,
                "max_rpm": max_rpm,
                "fuel_type": fuel_type,
                "transmission_type": transmission_type,
                "gear_count": gear_count,
                "drivetrain": drivetrain,
                "final_drive_ratio": final_drive_ratio,
                "curb_weight": curb_weight,
                "tire_size": tire_size,
                "notes": notes,
                # Bancada A
                "bank_a_enabled": bank_a_enabled,
                "bank_a_mode": bank_a_mode,
                "bank_a_injector_count": bank_a_injector_count,
                "bank_a_injector_flow": bank_a_injector_flow,
                "bank_a_total_flow": bank_a_injector_flow * bank_a_injector_count if bank_a_enabled else 0,
                "bank_a_dead_time": bank_a_dead_time,
                # Bancada B
                "bank_b_enabled": bank_b_enabled,
                "bank_b_mode": bank_b_mode,
                "bank_b_injector_count": bank_b_injector_count,
                "bank_b_injector_flow": bank_b_injector_flow,
                "bank_b_total_flow": bank_b_injector_flow * bank_b_injector_count if bank_b_enabled else 0,
                "bank_b_dead_time": bank_b_dead_time,
                # MAP
                "min_map_pressure": min_map_pressure,
                "max_map_pressure": max_map_pressure
            }
            
            # Adicionar dados do turbo se aplicável
            if engine_aspiration in ["Turbo", "Turbo + Supercharger"]:
                vehicle_data.update({
                    "turbo_brand": turbo_brand,
                    "turbo_model": turbo_model,
                    "max_boost_pressure": max_boost_pressure,
                    "wastegate_type": wastegate_type
                })
            
            # Validar e criar
            validation_result = validate_vehicle_data(vehicle_data)
            if validation_result["is_valid"]:
                try:
                    vehicle_id = create_vehicle(vehicle_data)
                    st.success(f"Veículo {name} cadastrado com sucesso!")
                    st.balloons()
                    # Limpar formulário
                    for key in st.session_state.keys():
                        if key.startswith("bank_"):
                            del st.session_state[key]
                except Exception as e:
                    st.error(f"Erro ao cadastrar veículo: {str(e)}")
            else:
                for error in validation_result["errors"]:
                    st.error(error)
                for warning in validation_result.get("warnings", []):
                    st.warning(warning)

with tab_edit:
    st.header("Editar Veículo")
    
    # Seletor de veículo
    vehicles = get_all_vehicles()
    
    if not vehicles:
        st.info("Nenhum veículo cadastrado para editar.")
    else:
        vehicle_options = {v["id"]: f"{v['name']} ({v.get('nickname', 'N/A')})" for v in vehicles}
        
        selected_id = st.selectbox(
            "Selecione o veículo para editar",
            options=list(vehicle_options.keys()),
            format_func=lambda x: vehicle_options[x],
            key="edit_vehicle_selector"
        )
        
        if selected_id:
            vehicle = get_vehicle_by_id(selected_id)
            
            if vehicle:
                with st.form("edit_vehicle_form"):
                    # Formulário similar ao de cadastro mas com valores preenchidos
                    st.subheader("Informações Básicas")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        name = st.text_input("Nome do Veículo *", value=vehicle.get("name", ""))
                        nickname = st.text_input("Apelido", value=vehicle.get("nickname", ""))
                    
                    with col2:
                        brand = st.text_input("Marca *", value=vehicle.get("brand", ""))
                        model = st.text_input("Modelo *", value=vehicle.get("model", ""))
                    
                    with col3:
                        year = st.number_input("Ano", min_value=1900, max_value=2030, value=vehicle.get("year", 2020))
                        plate = st.text_input("Placa", value=vehicle.get("plate", ""))
                    
                    # Status
                    is_active = st.checkbox("Veículo Ativo", value=vehicle.get("is_active", True))
                    
                    submitted = st.form_submit_button("Salvar Alterações", type="primary", use_container_width=True)
                    
                    if submitted:
                        updated_data = {
                            "name": name,
                            "nickname": nickname,
                            "brand": brand,
                            "model": model,
                            "year": year,
                            "plate": normalize_plate(plate) if plate else None,
                            "is_active": is_active
                        }
                        
                        if update_vehicle(selected_id, updated_data):
                            st.success("Veículo atualizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar veículo")
