"""
Página de configuração de bancadas de injeção.
Padrão A04-STREAMLIT-PROFESSIONAL: Zero emojis, apenas componentes nativos.
"""

import streamlit as st
from typing import Optional, Dict, List
from src.data.vehicle_database import (
    get_all_vehicles,
    get_vehicle_by_id,
    update_vehicle
)

# Título principal - SEM HTML, SEM EMOJIS
st.title("Configuração de Bancadas de Injeção")
st.caption("Configure as bancadas A e B do sistema de injeção")

# Seleção de veículo
vehicles = get_all_vehicles(active_only=True)

if not vehicles:
    st.error("Nenhum veículo cadastrado. Cadastre um veículo primeiro.")
    st.stop()

# Criar opções de veículo
vehicle_options = {v["id"]: f"{v['name']} ({v.get('nickname', 'Sem apelido')})" for v in vehicles}

selected_vehicle_id = st.selectbox(
    "Selecione o Veículo",
    options=list(vehicle_options.keys()),
    format_func=lambda x: vehicle_options[x],
    help="Escolha o veículo para configurar as bancadas"
)

if selected_vehicle_id:
    vehicle = get_vehicle_by_id(selected_vehicle_id)
    
    # Informações do veículo
    with st.expander("Informações do Veículo", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Marca/Modelo", f"{vehicle.get('brand', '')} {vehicle.get('model', '')}")
            st.metric("Ano", vehicle.get("year", "N/A"))
        
        with col2:
            st.metric("Motor", f"{vehicle.get('engine_displacement', 0)}L {vehicle.get('engine_configuration', '')}")
            st.metric("Cilindros", vehicle.get("engine_cylinders", 0))
        
        with col3:
            st.metric("Aspiração", vehicle.get("engine_aspiration", "N/A"))
            st.metric("Potência", f"{vehicle.get('estimated_power', 0)} hp")
        
        with col4:
            st.metric("Combustível", vehicle.get("fuel_type", "N/A"))
            st.metric("Sistema", vehicle.get("fuel_system", "N/A"))
    
    # Tabs de configuração
    tab1, tab2, tab3 = st.tabs([
        "Bancada A",
        "Bancada B", 
        "Sincronização"
    ])
    
    with tab1:
        st.header("Configuração da Bancada A")
        
        with st.form("bank_a_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                bank_a_enabled = st.checkbox(
                    "Habilitar Bancada A",
                    value=vehicle.get("bank_a_enabled", False),
                    help="Ativa a bancada A de injeção"
                )
                
                if bank_a_enabled:
                    mode_options = ["sequential", "semi-sequential", "batch"]
                    current_mode = vehicle.get("bank_a_mode", "sequential")
                    # Garantir que o modo atual está na lista
                    try:
                        mode_index = mode_options.index(current_mode) if current_mode in mode_options else 0
                    except:
                        mode_index = 0
                    
                    bank_a_mode = st.selectbox(
                        "Modo de Operação",
                        mode_options,
                        index=mode_index
                    )
                    
                    # Garantir valor padrão para quantidade de bicos
                    a_count = vehicle.get("bank_a_injector_count")
                    if a_count is None:
                        a_count = 4
                    bank_a_injector_count = st.number_input(
                        "Quantidade de Bicos",
                        min_value=1,
                        max_value=16,
                        value=int(a_count)
                    )
            
            with col2:
                if bank_a_enabled:
                    # Garantir valor padrão para vazão
                    a_flow = vehicle.get("bank_a_injector_flow")
                    if a_flow is None:
                        a_flow = 80
                    bank_a_injector_flow = st.number_input(
                        "Vazão dos Bicos (lbs/h)",
                        min_value=0,
                        max_value=300,
                        value=int(a_flow),
                        step=5
                    )
                    
                    # Garantir valor padrão para dead time
                    a_dead = vehicle.get("bank_a_dead_time")
                    if a_dead is None:
                        a_dead = 1.0
                    bank_a_dead_time = st.number_input(
                        "Dead Time (ms)",
                        min_value=0.0,
                        max_value=10.0,
                        value=float(a_dead),
                        step=0.1,
                        format="%.1f"
                    )
                    
                    # Cálculo da vazão total
                    total_flow_a = bank_a_injector_flow * bank_a_injector_count
                    st.metric("Vazão Total", f"{total_flow_a} lbs/h")
            
            if not bank_a_enabled:
                # Valores padrão quando desabilitado
                bank_a_mode = None
                bank_a_injector_count = 0
                bank_a_injector_flow = 0
                bank_a_dead_time = 0
                total_flow_a = 0
            
            # Botão de salvar
            submitted_a = st.form_submit_button("Salvar Configuração Bancada A", type="primary", use_container_width=True)
            
            if submitted_a:
                update_data = {}
                if bank_a_enabled:
                    update_data.update({
                        "bank_a_enabled": True,
                        "bank_a_mode": bank_a_mode,
                        "bank_a_injector_count": bank_a_injector_count,
                        "bank_a_injector_flow": bank_a_injector_flow,
                        "bank_a_dead_time": bank_a_dead_time,
                        "bank_a_total_flow": total_flow_a
                    })
                else:
                    update_data.update({
                        "bank_a_enabled": False,
                        "bank_a_mode": None,
                        "bank_a_injector_count": 0,
                        "bank_a_injector_flow": 0,
                        "bank_a_dead_time": 0,
                        "bank_a_total_flow": 0
                    })
                
                if update_vehicle(selected_vehicle_id, update_data):
                    st.success("Configuração da Bancada A salva com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao salvar configuração")
    
    with tab2:
        st.header("Configuração da Bancada B")
        
        with st.form("bank_b_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                bank_b_enabled = st.checkbox(
                    "Habilitar Bancada B",
                    value=vehicle.get("bank_b_enabled", False),
                    help="Ativa a bancada B de injeção (secundária)"
                )
                
                if bank_b_enabled:
                    mode_options = ["sequential", "semi-sequential", "batch"]
                    current_mode = vehicle.get("bank_b_mode", "sequential")
                    # Garantir que o modo atual está na lista
                    try:
                        mode_index = mode_options.index(current_mode) if current_mode in mode_options else 0
                    except:
                        mode_index = 0
                    
                    bank_b_mode = st.selectbox(
                        "Modo de Operação",
                        mode_options,
                        index=mode_index
                    )
                    
                    # Garantir valor padrão para quantidade de bicos
                    b_count = vehicle.get("bank_b_injector_count")
                    if b_count is None:
                        b_count = 4
                    bank_b_injector_count = st.number_input(
                        "Quantidade de Bicos",
                        min_value=1,
                        max_value=16,
                        value=int(b_count)
                    )
            
            with col2:
                if bank_b_enabled:
                    # Garantir valor padrão para vazão
                    b_flow = vehicle.get("bank_b_injector_flow")
                    if b_flow is None:
                        b_flow = 80
                    bank_b_injector_flow = st.number_input(
                        "Vazão dos Bicos (lbs/h)",
                        min_value=0,
                        max_value=300,
                        value=int(b_flow),
                        step=5
                    )
                    
                    # Garantir valor padrão para dead time
                    b_dead = vehicle.get("bank_b_dead_time")
                    if b_dead is None:
                        b_dead = 1.0
                    bank_b_dead_time = st.number_input(
                        "Dead Time (ms)",
                        min_value=0.0,
                        max_value=10.0,
                        value=float(b_dead),
                        step=0.1,
                        format="%.1f"
                    )
                    
                    # Cálculo da vazão total
                    total_flow_b = bank_b_injector_flow * bank_b_injector_count
                    st.metric("Vazão Total", f"{total_flow_b} lbs/h")
            
            if not bank_b_enabled:
                # Valores padrão quando desabilitado
                bank_b_mode = None
                bank_b_injector_count = 0
                bank_b_injector_flow = 0
                bank_b_dead_time = 0
                total_flow_b = 0
            
            # Botão de salvar
            submitted_b = st.form_submit_button("Salvar Configuração Bancada B", type="primary", use_container_width=True)
            
            if submitted_b:
                update_data = {}
                if bank_b_enabled:
                    update_data.update({
                        "bank_b_enabled": True,
                        "bank_b_mode": bank_b_mode,
                        "bank_b_injector_count": bank_b_injector_count,
                        "bank_b_injector_flow": bank_b_injector_flow,
                        "bank_b_dead_time": bank_b_dead_time,
                        "bank_b_total_flow": total_flow_b
                    })
                else:
                    update_data.update({
                        "bank_b_enabled": False,
                        "bank_b_mode": None,
                        "bank_b_injector_count": 0,
                        "bank_b_injector_flow": 0,
                        "bank_b_dead_time": 0,
                        "bank_b_total_flow": 0
                    })
                
                if update_vehicle(selected_vehicle_id, update_data):
                    st.success("Configuração da Bancada B salva com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao salvar configuração")
    
    with tab3:
        st.header("Sincronização de Bancadas")
        
        # Mostrar status atual
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Status Bancada A")
            if vehicle.get("bank_a_enabled"):
                st.success("Ativa")
                st.write(f"**Modo:** {vehicle.get('bank_a_mode', 'N/A')}")
                st.write(f"**Bicos:** {vehicle.get('bank_a_injector_count', 0)}")
                st.write(f"**Vazão Total:** {vehicle.get('bank_a_total_flow', 0)} lbs/h")
            else:
                st.info("Desativada")
        
        with col2:
            st.subheader("Status Bancada B")
            if vehicle.get("bank_b_enabled"):
                st.success("Ativa")
                st.write(f"**Modo:** {vehicle.get('bank_b_mode', 'N/A')}")
                st.write(f"**Bicos:** {vehicle.get('bank_b_injector_count', 0)}")
                st.write(f"**Vazão Total:** {vehicle.get('bank_b_total_flow', 0)} lbs/h")
            else:
                st.info("Desativada")
        
        # Opções de sincronização
        st.divider()
        st.subheader("Configuração de Sincronização")
        
        if vehicle.get("bank_a_enabled") and vehicle.get("bank_b_enabled"):
            sync_mode = st.radio(
                "Modo de Sincronização",
                ["Independente", "Simultâneo", "Alternado", "Progressivo"],
                help="Define como as bancadas trabalham em conjunto"
            )
            
            if sync_mode == "Progressivo":
                transition_rpm = st.slider(
                    "RPM de Transição",
                    min_value=1000,
                    max_value=10000,
                    value=4000,
                    step=100,
                    help="RPM onde a bancada B começa a atuar"
                )
                
                transition_load = st.slider(
                    "Carga de Transição (%)",
                    min_value=0,
                    max_value=100,
                    value=70,
                    help="Percentual de carga onde a bancada B entra"
                )
            
            # Balanceamento
            st.divider()
            st.subheader("Balanceamento de Vazão")
            
            total_flow = (vehicle.get("bank_a_total_flow") or 0) + (vehicle.get("bank_b_total_flow") or 0)
            
            if total_flow > 0:
                bank_a_percent = ((vehicle.get("bank_a_total_flow") or 0) / total_flow) * 100
                bank_b_percent = ((vehicle.get("bank_b_total_flow") or 0) / total_flow) * 100
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Bancada A", f"{bank_a_percent:.1f}%")
                with col2:
                    st.metric("Bancada B", f"{bank_b_percent:.1f}%")
                with col3:
                    st.metric("Vazão Total", f"{total_flow} lbs/h")
                
                # Gráfico de barras simples
                import pandas as pd
                df = pd.DataFrame({
                    "Bancada": ["A", "B"],
                    "Vazão (lbs/h)": [
                        vehicle.get("bank_a_total_flow") or 0,
                        vehicle.get("bank_b_total_flow") or 0
                    ]
                })
                st.bar_chart(df.set_index("Bancada"))
        else:
            st.info("Ative ambas as bancadas para configurar sincronização")