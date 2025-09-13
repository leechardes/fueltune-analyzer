"""
Página de configuração de bancadas de injeção.
Padrão A04-STREAMLIT-PROFESSIONAL: Zero emojis, apenas componentes nativos.
"""

import streamlit as st

from src.data.vehicle_database import get_vehicle_by_id, update_vehicle


# Funções de cálculo de potência
def get_default_bsfc(fuel_type: str) -> float:
    """Retorna valor padrão de BSFC baseado no tipo de combustível."""
    bsfc_defaults = {
        "Gasoline": 0.50,
        "Gasolina": 0.50,
        "Ethanol": 0.60,
        "Etanol": 0.60,
        "Methanol": 0.65,
        "Metanol": 0.65,
        "Flex": 0.55,
        "E85": 0.55,
        "CNG": 0.45,
        "GNV": 0.45,
    }
    return bsfc_defaults.get(fuel_type, 0.50)


def calculate_turbo_hp(base_hp: float, boost_pressure: float) -> float:
    """Calcula potência com turbo baseada na pressão de boost."""
    if boost_pressure <= 0:
        return base_hp
    # Fórmula correta: base_hp × (1 + boost_pressure)
    # 1 bar de boost = dobra a pressão atmosférica = dobra a potência
    # Pressão absoluta = 1 bar (atmosférica) + boost_pressure
    # Multiplicador = pressão_absoluta / pressão_atmosférica = (1 + boost) / 1
    return base_hp * (1 + boost_pressure)


def calculate_max_supported_hp(total_flow_lbs_h: float, bsfc: float) -> float:
    """Calcula potência máxima suportada pelos injetores."""
    if bsfc <= 0 or total_flow_lbs_h <= 0:
        return 0
    # Fórmula: total_flow ÷ bsfc
    return total_flow_lbs_h / bsfc


def calculate_hp_margin(supported_hp: float, required_hp: float) -> tuple[float, float]:
    """Calcula margem de potência absoluta e percentual."""
    if required_hp <= 0:
        return supported_hp, 100.0

    margin_absolute = supported_hp - required_hp
    margin_percent = (margin_absolute / required_hp) * 100
    return margin_absolute, margin_percent


def get_margin_color(margin_percent: float) -> str:
    """Retorna cor do indicador baseado na margem percentual."""
    if margin_percent >= 20:
        return "normal"  # Verde
    elif margin_percent >= 10:
        return "off"  # Amarelo
    else:
        return "inverse"  # Vermelho


# Título principal - SEM HTML, SEM EMOJIS
st.title("Configuração de Bancadas de Injeção")
st.caption("Configure as bancadas A e B do sistema de injeção")

# Obter veículo selecionado do session_state (vem do sidebar)
if "selected_vehicle_id" not in st.session_state:
    st.error("Nenhum veículo selecionado. Por favor, selecione um veículo no menu lateral.")
    st.stop()

selected_vehicle_id = st.session_state.selected_vehicle_id

if selected_vehicle_id:
    vehicle = get_vehicle_by_id(selected_vehicle_id)

    # Informações do veículo com análise de potência - EDITÁVEL
    with st.expander("Informações do Veículo", expanded=True):
        # Formulário para editar dados do veículo
        with st.form("vehicle_info_form"):
            st.subheader("Dados do Motor")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                brand = st.text_input("Marca", value=vehicle.get("brand", ""), key="brand_input")
                model = st.text_input("Modelo", value=vehicle.get("model", ""), key="model_input")
                year = st.number_input(
                    "Ano",
                    min_value=1900,
                    max_value=2030,
                    value=int(vehicle.get("year", 2020)),
                    key="year_input",
                )

            with col2:
                engine_displacement = st.number_input(
                    "Cilindrada (L)",
                    min_value=0.1,
                    max_value=10.0,
                    value=float(vehicle.get("engine_displacement", 2.0)),
                    step=0.1,
                    format="%.1f",
                    key="displacement_input",
                )
                engine_configuration = st.text_input(
                    "Configuração",
                    value=vehicle.get("engine_configuration", ""),
                    help="Ex: V8, I4, I6, V6",
                    key="config_input",
                )
                engine_cylinders = st.number_input(
                    "Cilindros",
                    min_value=1,
                    max_value=16,
                    value=int(vehicle.get("engine_cylinders", 4)),
                    key="cylinders_input",
                )

            with col3:
                aspiration_options = ["Aspirado", "Turbo", "Supercharger", "Twin Turbo"]
                current_aspiration = vehicle.get("engine_aspiration", "Aspirado")
                if current_aspiration not in aspiration_options:
                    aspiration_options.append(current_aspiration)

                engine_aspiration = st.selectbox(
                    "Aspiração",
                    options=aspiration_options,
                    index=(
                        aspiration_options.index(current_aspiration)
                        if current_aspiration in aspiration_options
                        else 0
                    ),
                    key="aspiration_input",
                )

                estimated_power = st.number_input(
                    "Potência Base (CV)",
                    min_value=0,
                    max_value=2000,
                    value=int(vehicle.get("estimated_power", 250)),
                    step=5,
                    help="Potência em modo aspirado ou base",
                    key="power_input",
                )

                system_options = [
                    "Injeção Eletrônica",
                    "Carburador",
                    "Injeção Direta",
                    "Port Injection",
                ]
                current_system = vehicle.get("fuel_system", "Injeção Eletrônica")
                if current_system not in system_options:
                    system_options.append(current_system)

                fuel_system = st.selectbox(
                    "Sistema",
                    options=system_options,
                    index=(
                        system_options.index(current_system)
                        if current_system in system_options
                        else 0
                    ),
                    key="system_input",
                )

            with col4:
                fuel_options = [
                    "Gasolina",
                    "Etanol",
                    "Flex",
                    "Metanol",
                    "GNV",
                    "E85",
                    "Diesel",
                    "Nitrometano",
                ]
                current_fuel_raw = str(vehicle.get("fuel_type", "Gasolina"))
                cf = current_fuel_raw.lower()
                # Normalizar exibição em pt-BR (não mostrar "Ethanol")
                if "ethanol" in cf or "etanol" in cf:
                    current_fuel = "Etanol"
                elif "gasoline" in cf or "gasolina" in cf or "gas" == cf:
                    current_fuel = "Gasolina"
                elif "e85" in cf:
                    current_fuel = "E85"
                elif "gnv" in cf or "cng" in cf:
                    current_fuel = "GNV"
                elif "methanol" in cf or "metanol" in cf:
                    current_fuel = "Metanol"
                elif "nitromethane" in cf or "nitrometano" in cf or "nitro" in cf:
                    current_fuel = "Nitrometano"
                elif "diesel" in cf:
                    current_fuel = "Diesel"
                elif "flex" in cf:
                    current_fuel = "Flex"
                else:
                    current_fuel = current_fuel_raw
                    if current_fuel not in fuel_options:
                        fuel_options.append(current_fuel)

                fuel_type = st.selectbox(
                    "Combustível",
                    options=fuel_options,
                    index=fuel_options.index(current_fuel) if current_fuel in fuel_options else 0,
                    key="fuel_input",
                )

                # Taxa de compressão
                compression_options = ["Baixa compressão", "Média compressão", "Alta compressão"]
                current_compression = vehicle.get("compression_ratio", "Baixa compressão")
                # Garantir que o valor está na lista
                if current_compression not in compression_options:
                    # Se for um valor como "10.5:1", tentar mapear
                    if current_compression and ":" in str(current_compression):
                        current_compression = (
                            "Média compressão"  # Valor padrão para valores numéricos
                        )
                    else:
                        current_compression = "Baixa compressão"

                compression_ratio = st.radio(
                    "Taxa de Compressão",
                    options=compression_options,
                    index=compression_options.index(current_compression),
                    key="compression_input",
                    horizontal=True,
                )

                # Comando de válvulas
                camshaft_options = ["Baixa graduação", "Alta graduação"]
                current_camshaft = vehicle.get("camshaft_profile", "Baixa graduação")
                # Garantir que o valor está na lista
                if current_camshaft not in camshaft_options:
                    # Se for um valor diferente como "Original", mapear para baixa graduação
                    current_camshaft = "Baixa graduação"

                camshaft_profile = st.radio(
                    "Comando de Válvulas",
                    options=camshaft_options,
                    index=camshaft_options.index(current_camshaft),
                    key="camshaft_input",
                    horizontal=True,
                )

            # Botão para salvar informações do veículo
            submitted_vehicle = st.form_submit_button(
                "Salvar Informações do Veículo", type="primary", use_container_width=True
            )

            if submitted_vehicle:
                # Persistir combustível em formato canônico ('Ethanol' para 'Etanol', etc.)
                if fuel_type == "Etanol":
                    fuel_type_save = "Ethanol"
                elif fuel_type == "Gasolina":
                    fuel_type_save = "Gasoline"
                elif fuel_type == "GNV":
                    fuel_type_save = "CNG"
                else:
                    fuel_type_save = fuel_type

                vehicle_update = {
                    "brand": brand,
                    "model": model,
                    "year": year,
                    "engine_displacement": engine_displacement,
                    "engine_configuration": engine_configuration,
                    "engine_cylinders": engine_cylinders,
                    "engine_aspiration": engine_aspiration,
                    "estimated_power": estimated_power,
                    "fuel_type": fuel_type_save,
                    "fuel_system": fuel_system,
                    "compression_ratio": compression_ratio,
                    "camshaft_profile": camshaft_profile,
                }

                if update_vehicle(selected_vehicle_id, vehicle_update):
                    st.success("Informações do veículo atualizadas com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao atualizar informações do veículo")

        st.divider()

        # Seção 2: Sistema de Injeção e Análise de Potência
        st.subheader("Sistema de Injeção e Análise de Potência")

        # Campos editáveis em um formulário
        with st.form("power_analysis_form"):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Configurações de Análise**")

                # BSFC editável - usando fuel_type do formulário ou do banco
                fuel_type_current = vehicle.get("fuel_type", "Gasolina")
                default_bsfc = get_default_bsfc(fuel_type_current)
                current_bsfc = vehicle.get("bsfc_factor", default_bsfc)

                bsfc_factor = st.number_input(
                    "BSFC Factor",
                    min_value=0.30,
                    max_value=0.80,
                    value=float(current_bsfc),
                    step=0.01,
                    format="%.2f",
                    help=f"Fator BSFC para {fuel_type_current}. Padrão: {default_bsfc:.2f}",
                )

                # Pressão boost editável apenas para turbo/super
                aspiration = vehicle.get("engine_aspiration", "")
                is_forced_induction = any(term in aspiration.lower() for term in ["turbo", "super"])

                if is_forced_induction:
                    current_boost = (
                        vehicle.get("boost_pressure") or vehicle.get("max_boost_pressure") or 1.0
                    )
                    # Garantir que current_boost não seja None
                    if current_boost is None:
                        current_boost = 1.0
                    boost_pressure = st.number_input(
                        "Pressão Máxima (bar)",
                        min_value=0.1,
                        max_value=5.0,
                        value=float(current_boost),
                        step=0.1,
                        format="%.1f",
                        help="Pressão máxima de boost para cálculo de potência máxima",
                    )

                    # Pressão padrão/normal de uso
                    current_standard_boost = vehicle.get(
                        "standard_boost_pressure", boost_pressure * 0.7
                    )
                    # Garantir que current_standard_boost não seja None
                    if current_standard_boost is None:
                        current_standard_boost = boost_pressure * 0.7
                    # Garantir que a pressão padrão não exceda a pressão máxima atual
                    if current_standard_boost > boost_pressure:
                        current_standard_boost = boost_pressure * 0.7

                    standard_boost_pressure = st.number_input(
                        "Pressão Padrão (bar)",
                        min_value=0.1,
                        max_value=float(
                            boost_pressure
                        ),  # Usar boost_pressure em vez de current_boost
                        value=float(current_standard_boost),
                        step=0.1,
                        format="%.1f",
                        help="Pressão típica de uso diário/normal",
                    )
                else:
                    boost_pressure = 0.0
                    standard_boost_pressure = 0.0
                    st.info("Motor aspirado - sem pressão de boost")

                # Informativo sobre BSFC
                st.divider()
                st.caption("**Sobre BSFC (Brake Specific Fuel Consumption):**")
                st.caption(
                    """
                O BSFC indica quantas libras de combustível são necessárias para produzir 1 HP por hora.
                Valores típicos:
                • Gasolina: 0.45-0.50
                • Etanol: 0.55-0.65
                • Metanol: 0.60-0.70
                • GNV: 0.40-0.45
                
                Quanto menor o valor, mais eficiente é o combustível.
                """
                )

            with col2:
                st.write("**Vazão e Potência**")

                # Calcular vazões totais atuais
                total_flow_a = (
                    vehicle.get("bank_a_total_flow", 0) if vehicle.get("bank_a_enabled") else 0
                )
                total_flow_b = (
                    vehicle.get("bank_b_total_flow", 0) if vehicle.get("bank_b_enabled") else 0
                )
                total_flow = total_flow_a + total_flow_b

                st.metric("Vazão Total", f"{total_flow:.0f} lbs/h")

                # Cálculos de potência
                base_hp = vehicle.get("estimated_power", 250)
                max_supported_hp = calculate_max_supported_hp(total_flow, bsfc_factor)

                # Primeira linha: Potências do motor
                st.divider()
                power_cols = st.columns(3)

                with power_cols[0]:
                    st.metric("Potência Aspirada", f"{(base_hp*1.01387):.0f} CV")

                if is_forced_induction and boost_pressure > 0:
                    # Calcular potências
                    standard_hp = calculate_turbo_hp(base_hp, standard_boost_pressure)
                    turbo_hp = calculate_turbo_hp(base_hp, boost_pressure)

                    with power_cols[1]:
                        st.metric(
                            "Potência Padrão",
                            f"{(standard_hp*1.01387):.0f} CV",
                            delta=f"+{((standard_hp - base_hp)*1.01387):.0f}",
                            help=f"Com {standard_boost_pressure:.1f} bar",
                        )

                    with power_cols[2]:
                        st.metric(
                            "Potência Máxima",
                            f"{(turbo_hp*1.01387):.0f} CV",
                            delta=f"+{((turbo_hp - base_hp)*1.01387):.0f}",
                            help=f"Com {boost_pressure:.1f} bar",
                        )

                    required_hp = turbo_hp
                else:
                    # Para aspirados, apenas mostrar na primeira coluna
                    with power_cols[1]:
                        st.empty()
                    with power_cols[2]:
                        st.empty()
                    required_hp = base_hp

                # Segunda linha: Análise de capacidade
                st.divider()
                if total_flow > 0:
                    margin_abs, margin_percent = calculate_hp_margin(max_supported_hp, required_hp)
                    margin_color = get_margin_color(margin_percent)
                    margin_status = (
                        "Seguro"
                        if margin_percent >= 20
                        else "Adequado" if margin_percent >= 10 else "Limite"
                    )

                    capacity_cols = st.columns(3)

                    with capacity_cols[0]:
                        st.metric(
                            "Máximo Suportado",
                            f"{(max_supported_hp*1.01387):.0f} CV",
                            help="Baseado na vazão total dos bicos",
                        )

                    with capacity_cols[1]:
                        st.metric(
                            "Margem",
                            f"{(margin_abs*1.01387):.0f} CV",
                            help=f"Diferença para potência máxima",
                        )

                    with capacity_cols[2]:
                        st.metric(
                            "Margem %",
                            f"{margin_percent:.1f}%",
                            delta=margin_status,
                            delta_color=margin_color,
                            help="Verde > 20% | Amarelo 10-20% | Vermelho < 10%",
                        )
                else:
                    st.info("Configure as bancadas para ver análise")

            # Botão para salvar configurações
            submitted_power = st.form_submit_button(
                "Salvar Configurações de Análise", type="secondary"
            )

            if submitted_power:
                update_data = {"bsfc_factor": bsfc_factor}

                if is_forced_induction:
                    update_data["boost_pressure"] = boost_pressure
                    update_data["standard_boost_pressure"] = standard_boost_pressure

                # Salvar cálculos atuais
                turbo_hp_value = (
                    turbo_hp
                    if (is_forced_induction and boost_pressure > 0 and "turbo_hp" in locals())
                    else base_hp
                )
                standard_hp_value = (
                    standard_hp
                    if (
                        is_forced_induction
                        and standard_boost_pressure > 0
                        and "standard_hp" in locals()
                    )
                    else base_hp
                )
                margin_abs_value = (
                    margin_abs if (total_flow > 0 and "margin_abs" in locals()) else 0
                )
                margin_percent_value = (
                    margin_percent if (total_flow > 0 and "margin_percent" in locals()) else 0
                )

                update_data.update(
                    {
                        "max_supported_hp": max_supported_hp,
                        "required_hp_na": base_hp,
                        "required_hp_boost": turbo_hp_value,
                        "required_hp_standard": standard_hp_value,
                        "hp_margin": margin_abs_value,
                        "hp_margin_percent": margin_percent_value,
                    }
                )

                if update_vehicle(selected_vehicle_id, update_data):
                    st.success("Configurações de análise salvas com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao salvar configurações")

    # Tabs de configuração
    tab1, tab2, tab3 = st.tabs(["Bancada A", "Bancada B", "Sincronização"])

    with tab1:
        st.header("Configuração da Bancada A")

        with st.form("bank_a_form"):
            col1, col2 = st.columns(2)

            with col1:
                bank_a_enabled = st.checkbox(
                    "Habilitar Bancada A",
                    value=vehicle.get("bank_a_enabled", False),
                    help="Ativa a bancada A de injeção",
                )

                if bank_a_enabled:
                    mode_options = ["sequential", "semi-sequential", "batch"]
                    current_mode = vehicle.get("bank_a_mode", "sequential")
                    # Garantir que o modo atual está na lista
                    try:
                        mode_index = (
                            mode_options.index(current_mode) if current_mode in mode_options else 0
                        )
                    except:
                        mode_index = 0

                    bank_a_mode = st.selectbox("Modo de Operação", mode_options, index=mode_index)

                    # Garantir valor padrão para quantidade de bicos
                    a_count = vehicle.get("bank_a_injector_count")
                    if a_count is None:
                        a_count = 4
                    bank_a_injector_count = st.number_input(
                        "Quantidade de Bicos", min_value=1, max_value=16, value=int(a_count)
                    )

            with col2:
                if bank_a_enabled:
                    # Garantir valor padrão para vazão
                    a_flow = vehicle.get("bank_a_injector_flow")
                    if a_flow is None:
                        a_flow = 80
                    # Garantir que o valor não exceda o máximo permitido
                    a_flow_value = min(int(a_flow), 500)  # Aumentando o máximo para 500
                    bank_a_injector_flow = st.number_input(
                        "Vazão dos Bicos (lb/h)",
                        min_value=0,
                        max_value=500,  # Aumentado de 300 para 500
                        value=a_flow_value,
                        step=5,
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
                        format="%.1f",
                    )

                    # Cálculo da vazão total
                    total_flow_a = bank_a_injector_flow * bank_a_injector_count
                    st.metric("Vazão Total", f"{total_flow_a} lb/h")

            if not bank_a_enabled:
                # Valores padrão quando desabilitado
                bank_a_mode = None
                bank_a_injector_count = 0
                bank_a_injector_flow = 0
                bank_a_dead_time = 0
                total_flow_a = 0

            # Botão de salvar
            submitted_a = st.form_submit_button(
                "Salvar Configuração Bancada A", type="primary", use_container_width=True
            )

            if submitted_a:
                update_data = {}
                if bank_a_enabled:
                    update_data.update(
                        {
                            "bank_a_enabled": True,
                            "bank_a_mode": bank_a_mode,
                            "bank_a_injector_count": bank_a_injector_count,
                            "bank_a_injector_flow": bank_a_injector_flow,
                            "bank_a_dead_time": bank_a_dead_time,
                            "bank_a_total_flow": total_flow_a,
                        }
                    )
                else:
                    update_data.update(
                        {
                            "bank_a_enabled": False,
                            "bank_a_mode": None,
                            "bank_a_injector_count": 0,
                            "bank_a_injector_flow": 0,
                            "bank_a_dead_time": 0,
                            "bank_a_total_flow": 0,
                        }
                    )

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
                    help="Ativa a bancada B de injeção (secundária)",
                )

                if bank_b_enabled:
                    mode_options = ["sequential", "semi-sequential", "batch"]
                    current_mode = vehicle.get("bank_b_mode", "sequential")
                    # Garantir que o modo atual está na lista
                    try:
                        mode_index = (
                            mode_options.index(current_mode) if current_mode in mode_options else 0
                        )
                    except:
                        mode_index = 0

                    bank_b_mode = st.selectbox("Modo de Operação", mode_options, index=mode_index)

                    # Garantir valor padrão para quantidade de bicos
                    b_count = vehicle.get("bank_b_injector_count")
                    if b_count is None:
                        b_count = 4
                    bank_b_injector_count = st.number_input(
                        "Quantidade de Bicos", min_value=1, max_value=16, value=int(b_count)
                    )

                    # Pressão inicial da bancada B
                    initial_pressure_value = vehicle.get("bank_b_initial_pressure", 0.0)
                    if initial_pressure_value is None:
                        initial_pressure_value = 0.0
                    bank_b_initial_pressure = st.number_input(
                        "Pressão Inicial Bancada B",
                        min_value=0.0,
                        max_value=10.0,
                        value=float(initial_pressure_value),
                        step=0.1,
                        format="%.1f",
                        help="Pressão inicial para ativação da bancada B em bar",
                    )

            with col2:
                if bank_b_enabled:
                    # Garantir valor padrão para vazão
                    b_flow = vehicle.get("bank_b_injector_flow")
                    if b_flow is None:
                        b_flow = 80
                    # Garantir que o valor não exceda o máximo permitido
                    b_flow_value = min(int(b_flow), 500)  # Aumentando o máximo para 500
                    bank_b_injector_flow = st.number_input(
                        "Vazão dos Bicos (lb/h)",
                        min_value=0,
                        max_value=500,  # Aumentado de 300 para 500
                        value=b_flow_value,
                        step=5,
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
                        format="%.1f",
                    )

                    # Cálculo da vazão total
                    total_flow_b = bank_b_injector_flow * bank_b_injector_count
                    st.metric("Vazão Total", f"{total_flow_b} lb/h")

            if not bank_b_enabled:
                # Valores padrão quando desabilitado
                bank_b_mode = None
                bank_b_injector_count = 0
                bank_b_injector_flow = 0
                bank_b_dead_time = 0
                bank_b_initial_pressure = 0.0
                total_flow_b = 0

            # Botão de salvar
            submitted_b = st.form_submit_button(
                "Salvar Configuração Bancada B", type="primary", use_container_width=True
            )

            if submitted_b:
                update_data = {}
                if bank_b_enabled:
                    update_data.update(
                        {
                            "bank_b_enabled": True,
                            "bank_b_mode": bank_b_mode,
                            "bank_b_injector_count": bank_b_injector_count,
                            "bank_b_injector_flow": bank_b_injector_flow,
                            "bank_b_dead_time": bank_b_dead_time,
                            "bank_b_initial_pressure": bank_b_initial_pressure,
                            "bank_b_total_flow": total_flow_b,
                        }
                    )
                else:
                    update_data.update(
                        {
                            "bank_b_enabled": False,
                            "bank_b_mode": None,
                            "bank_b_injector_count": 0,
                            "bank_b_injector_flow": 0,
                            "bank_b_dead_time": 0,
                            "bank_b_initial_pressure": 0.0,
                            "bank_b_total_flow": 0,
                        }
                    )

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
                help="Define como as bancadas trabalham em conjunto",
            )

            if sync_mode == "Progressivo":
                transition_rpm = st.slider(
                    "RPM de Transição",
                    min_value=1000,
                    max_value=10000,
                    value=4000,
                    step=100,
                    help="RPM onde a bancada B começa a atuar",
                )

                transition_load = st.slider(
                    "Carga de Transição (%)",
                    min_value=0,
                    max_value=100,
                    value=70,
                    help="Percentual de carga onde a bancada B entra",
                )

            # Balanceamento
            st.divider()
            st.subheader("Balanceamento de Vazão")

            total_flow = (vehicle.get("bank_a_total_flow") or 0) + (
                vehicle.get("bank_b_total_flow") or 0
            )

            if total_flow > 0:
                bank_a_percent = ((vehicle.get("bank_a_total_flow") or 0) / total_flow) * 100
                bank_b_percent = ((vehicle.get("bank_b_total_flow") or 0) / total_flow) * 100

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Bancada A", f"{bank_a_percent:.1f}%")
                with col2:
                    st.metric("Bancada B", f"{bank_b_percent:.1f}%")

                # Gráfico de barras simples
                import pandas as pd

                df = pd.DataFrame(
                    {
                        "Bancada": ["A", "B"],
                        "Vazão (lbs/h)": [
                            vehicle.get("bank_a_total_flow") or 0,
                            vehicle.get("bank_b_total_flow") or 0,
                        ],
                    }
                )
                st.bar_chart(df.set_index("Bancada"))
        else:
            st.info("Ative ambas as bancadas para configurar sincronização")
