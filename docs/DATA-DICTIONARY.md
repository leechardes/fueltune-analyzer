# 📊 Dicionário de Dados - FuelTune Analyzer

## ⚠️ IMPORTANTE: Versão Real vs Documentada
- **Campos Reais Descobertos:** 64 campos (arquivo real do FuelTech)
- **Campos Documentados:** 37 campos (especificação original)
- **Diferença:** O sistema exporta 27 campos adicionais não documentados originalmente

## Visão Geral

Este documento consolida o dicionário de dados completo do FuelTune Analyzer, combinando:
1. A especificação teórica original (37 campos)
2. Os campos reais descobertos em logs do FuelTech (64 campos)

---

## PARTE 1: CAMPOS REAIS DO SISTEMA (64 campos)
- **Total de Campos:** 64
- **Total de Linhas:** 751
- **Delimitador:** Vírgula (,)
- **Encoding:** UTF-8

### Lista Completa dos 64 Campos

| # | Campo Original | Campo Normalizado | Tipo | Descrição |
|---|----------------|-------------------|------|-----------|
| 1 | TIME | time | float | Tempo em segundos |
| 2 | RPM | rpm | int | Rotação do motor |
| 3 | TPS | tps | float | Throttle Position Sensor (%) |
| 4 | Posição_do_acelerador | throttle_position | float | Posição física do acelerador |
| 5 | Ponto_de_ignição | ignition_timing | float | Avanço de ignição em graus |
| 6 | MAP | map | float | Manifold Absolute Pressure (bar) |
| 7 | Alvo_do_malha_fechada | closed_loop_target | float | Lambda target |
| 8 | Sonda_Malha_Fechada | closed_loop_o2 | float | O2 sensor malha fechada |
| 9 | Correção_do_malha_fechada | closed_loop_correction | float | Correção % malha fechada |
| 10 | Sonda_Geral | o2_general | float | Sonda lambda geral |
| 11 | 2-step | two_step | str | Status 2-step (ON/OFF) |
| 12 | Conteúdo_de_Etanol | ethanol_content | int | Percentual de etanol |
| 13 | Largada_validada | launch_validated | str | Status largada (ON/OFF) |
| 14 | Temperatura_do_combustível | fuel_temp | float | Temperatura combustível (°C) |
| 15 | Marcha | gear | int | Marcha engrenada |
| 16 | Vazão_da_bancada_A | flow_bank_a | float | Vazão bancada A (cc/min) |
| 17 | Ângulo_da_Fase_de_Injeção | injection_phase_angle | float | Ângulo fase injeção |
| 18 | Abertura_bicos_A | injector_duty_a | float | Duty cycle injetores A (%) |
| 19 | Tempo_de_Injeção_Banco_A | injection_time_a | float | Tempo injeção banco A (ms) |
| 20 | Temp._do_motor | engine_temp | float | Temperatura motor (°C) |
| 21 | Temp._do_Ar | air_temp | float | Temperatura ar admissão (°C) |
| 22 | Pressão_de_Óleo | oil_pressure | float | Pressão óleo (bar) |
| 23 | Pressão_de_Combustível | fuel_pressure | float | Pressão combustível (bar) |
| 24 | Tensão_da_Bateria | battery_voltage | float | Tensão bateria (V) |
| 25 | Dwell_de_ignição | ignition_dwell | float | Dwell ignição (ms) |
| 26 | Eletroventilador_1_-_Enriquecimento | fan1_enrichment | float | Enriquecimento ventoinha 1 |
| 27 | Nível_de_combustível | fuel_level | float | Nível combustível (%) |
| 28 | Sinal_de_sincronia_do_motor | engine_sync | str | Sinal sincronismo (ON/OFF) |
| 29 | Corte_na_desaceleração_(cutoff) | decel_cutoff | str | Cutoff desaceleração (ON/OFF) |
| 30 | Partida_do_motor | engine_cranking | str | Motor em partida (ON/OFF) |
| 31 | Lenta | idle | str | Motor em lenta (ON/OFF) |
| 32 | Primeiro_pulso_de_partida | first_pulse_cranking | str | Primeiro pulso partida (ON/OFF) |
| 33 | Injeção_rápida_e_de_decaimento | accel_decel_injection | str | AE/DE ativo (ON/OFF) |
| 34 | **Consumo_total** | total_consumption | float | Consumo total (L) |
| 35 | **Consumo_medio** | average_consumption | float | Consumo médio (km/L) |
| 36 | **Consumo_instantâneo** | instant_consumption | float | Consumo instantâneo (L/h) |
| 37 | **Potência_estimada** | estimated_power | int | Potência estimada (HP) |
| 38 | **Torque_estimado** | estimated_torque | int | Torque estimado (Nm) |
| 39 | **Distância_total** | total_distance | float | Distância total (km) |
| 40 | **Autonomia** | range | float | Autonomia (km) |
| 41 | Ajuste_ativo | active_adjustment | int | Ajuste ativo (%) |
| 42 | Eletroventilador_1 | fan1 | str | Ventoinha 1 (ON/OFF) |
| 43 | Eletroventilador_2 | fan2 | str | Ventoinha 2 (ON/OFF) |
| 44 | Bomba_Combustível | fuel_pump | str | Bomba combustível (ON/OFF) |
| 45 | **Velocidade_de_tração** | traction_speed | float | Velocidade tração (km/h) |
| 46 | **Velocidade_em_aceleração** | acceleration_speed | float | Velocidade aceleração (km/h) |
| 47 | **Controle_de_tração_-_Slip** | traction_control_slip | float | Slip controle tração (%) |
| 48 | **Controle_de_tração_-_Slip_rate** | traction_control_slip_rate | int | Taxa slip (%) |
| 49 | Delta_TPS | delta_tps | float | Variação TPS (%/s) |
| 50 | **Força_G_aceleração** | g_force_accel | float | Força G longitudinal |
| 51 | **Força_G_lateral** | g_force_lateral | float | Força G lateral |
| 52 | **Inclinação_frontal** | pitch_angle | float | Ângulo pitch (graus) |
| 53 | **Taxa_de_inclinação_frontal** | pitch_rate | float | Taxa pitch (graus/s) |
| 54 | **Direção_(Heading)** | heading | float | Direção (graus) |
| 55 | **Inclinação_lateral** | roll_angle | float | Ângulo roll (graus) |
| 56 | **Distancia_em_aceleração** | acceleration_distance | float | Distância em aceleração (m) |
| 57 | **Taxa_de_inclinação_lateral** | roll_rate | float | Taxa roll (graus/s) |
| 58 | **Força_G_aceleração_(Raw)** | g_force_accel_raw | float | Força G bruta longitudinal |
| 59 | **Força_G_lateral_(Raw)** | g_force_lateral_raw | float | Força G bruta lateral |
| 60 | Injeção_rápida | accel_enrichment | str | Enriquecimento aceleração (ON/OFF) |
| 61 | Injeção_de_decaimento | decel_enrichment | str | Enriquecimento desaceleração (ON/OFF) |
| 62 | Cutoff_de_injeção | injection_cutoff | str | Corte injeção (ON/OFF) |
| 63 | Injeção_pós_partida | after_start_injection | str | Injeção pós-partida (ON/OFF) |
| 64 | Botão_de_partida_-_Alternar | start_button_toggle | str | Botão partida (ON/OFF) |

## 🆕 CAMPOS NOVOS DESCOBERTOS (27 campos adicionais)

Os seguintes campos **NÃO** estavam na documentação original:

### 📊 Campos de Consumo e Eficiência
- Consumo_total, Consumo_medio, Consumo_instantâneo
- Potência_estimada, Torque_estimado
- Distância_total, Autonomia

### 🏎️ Campos de Performance e Dinâmica
- Velocidade_de_tração, Velocidade_em_aceleração
- Controle_de_tração_-_Slip, Controle_de_tração_-_Slip_rate
- Força_G_aceleração, Força_G_lateral
- Força_G_aceleração_(Raw), Força_G_lateral_(Raw)

### 📐 Campos de Telemetria Avançada
- Inclinação_frontal, Taxa_de_inclinação_frontal
- Inclinação_lateral, Taxa_de_inclinação_lateral
- Direção_(Heading)
- Distancia_em_aceleração

### 🔧 Campos de Controle Refinado
- Alvo_do_malha_fechada, Sonda_Malha_Fechada, Correção_do_malha_fechada
- Conteúdo_de_Etanol, Temperatura_do_combustível
- Eletroventilador_1_-_Enriquecimento, Nível_de_combustível

## 📈 ANÁLISE ESTATÍSTICA DA AMOSTRA

### Dados Gerais
- **Período de tempo:** 0.020s a ~30s (estimado)
- **Taxa de amostragem:** ~25 Hz (0.040s entre amostras)
- **RPM Range:** 992-1002 (marcha lenta)
- **MAP Range:** -0.70 a -0.68 bar (vácuo)

### Valores Típicos Encontrados
```
TIME: 0.020 - 30.000 (segundos)
RPM: 992 - 1002 (lenta)
TPS: 0.0 (fechado)
MAP: -0.70 bar (vácuo)
Sonda_Geral: 0.865 - 0.887 (lambda)
Temp_motor: 86.6°C
Temp_ar: 55.4°C
Tensão_bateria: 14.11V
```

## 🔄 IMPACTO NA ARQUITETURA

### Mudanças Necessárias

1. **Modelo de Dados Expandido**
   - 64 campos em vez de 37
   - Novos tipos de análise possíveis
   - Telemetria IMU completa

2. **Análises Adicionais Possíveis**
   - Análise de consumo e eficiência
   - Análise dinâmica do veículo (G-forces)
   - Controle de tração detalhado
   - Análise de inclinação (pitch/roll)

3. **Visualizações Extras**
   - Gráficos de força G
   - Mapas de consumo
   - Análise de potência/torque
   - Telemetria de movimento

## 📝 RECOMENDAÇÕES

1. **Atualizar todos os agentes** para suportar 64 campos
2. **Criar módulos especializados** para:
   - Análise de consumo
   - Telemetria IMU
   - Controle de tração
3. **Expandir validações** para novos campos
4. **Adicionar dashboards** específicos para novos dados

---

**Versão:** 2.0  
**Data:** 2025-01-02  
**Status:** ✅ VALIDADO COM DADOS REAIS
---

## PARTE 2: ESPECIFICAÇÃO COMPLETA ORIGINAL (37 campos documentados)


- **Core Engine Parameters**: RPM, timing, pressure, temperature
- **Fuel System Data**: Injection timing, flow rates, pressures  
- **Control Systems**: Launch control, gear detection, various flags
- **Sensor Data**: Lambda, temperatures, pressures, voltages
- **Advanced Parameters**: Dwell time, sync signals, injection modes

## Complete Field Specification

### 1. Core Engine Parameters

#### TIME
- **CSV Field**: `TIME`
- **Database Field**: `timestamp`
- **Data Type**: `float`
- **Unit**: `seconds`
- **Range**: `0.000 - 999999.999`
- **Precision**: `3 decimal places`
- **Required**: `True`
- **Description**: Timestamp in seconds since start of logging session
- **Validation**: Must be positive, monotonically increasing
- **Category**: `system`
- **Chartable**: `True`

#### RPM
- **CSV Field**: `RPM`
- **Database Field**: `rpm`
- **Data Type**: `integer`
- **Unit**: `rpm`
- **Range**: `0 - 20000`
- **Precision**: `0 decimal places`
- **Required**: `True`
- **Description**: Engine revolutions per minute
- **Validation**: Must be between 0 and 20000
- **Category**: `engine`
- **Chartable**: `True`

#### Posição do Acelerador (Throttle Position)
- **CSV Field**: `Posição_do_acelerador`
- **Database Field**: `throttle_position`
- **Data Type**: `float`
- **Unit**: `%`
- **Range**: `0.0 - 100.0`
- **Precision**: `1 decimal place`
- **Required**: `False`
- **Description**: Throttle position percentage (0% = closed, 100% = wide open)
- **Validation**: Must be between 0 and 100
- **Category**: `control`
- **Chartable**: `True`

#### Ponto de Ignição (Ignition Timing)
- **CSV Field**: `Ponto_de_ignição`
- **Database Field**: `ignition_timing`
- **Data Type**: `float`
- **Unit**: `°BTDC`
- **Range**: `-30.0 - 50.0`
- **Precision**: `1 decimal place`
- **Required**: `False`
- **Description**: Ignition timing in degrees before top dead center
- **Validation**: Must be between -30 and 50 degrees
- **Category**: `ignition`
- **Chartable**: `True`

#### MAP (Manifold Absolute Pressure)
- **CSV Field**: `MAP`
- **Database Field**: `map_pressure`
- **Data Type**: `float`
- **Unit**: `bar`
- **Range**: `-1.0 - 5.0`
- **Precision**: `2 decimal places`
- **Required**: `False`
- **Description**: Manifold absolute pressure in bar
- **Validation**: Must be between -1 and 5 bar
- **Category**: `sensor`
- **Chartable**: `True`

### 2. Fuel System Data

#### Sonda Geral (Lambda Sensor)
- **CSV Field**: `Sonda_Geral`
- **Database Field**: `lambda_sensor`
- **Data Type**: `float`
- **Unit**: `λ`
- **Range**: `0.5 - 2.0`
- **Precision**: `3 decimal places`
- **Required**: `False`
- **Description**: Lambda sensor reading (air-fuel ratio measurement)
- **Validation**: Must be between 0.5 and 2.0
- **Category**: `sensor`
- **Chartable**: `True`

#### Vazão da Bancada A (Fuel Flow Bank A)
- **CSV Field**: `Vazão_da_bancada_A`
- **Database Field**: `fuel_flow_bank_a`
- **Data Type**: `float`
- **Unit**: `L/h`
- **Range**: `0.0 - 1000.0`
- **Precision**: `2 decimal places`
- **Required**: `False`
- **Description**: Fuel flow rate for bank A injectors in liters per hour
- **Validation**: Must be non-negative
- **Category**: `fuel`
- **Chartable**: `True`

#### Fluxo Total de Combustível (Total Fuel Flow)
- **CSV Field**: `Fluxo_total_de_combustível`
- **Database Field**: `total_fuel_flow`
- **Data Type**: `float`
- **Unit**: `L/h`
- **Range**: `0.0 - 2000.0`
- **Precision**: `2 decimal places`
- **Required**: `False`
- **Description**: Total fuel flow rate for all injectors
- **Validation**: Must be non-negative
- **Category**: `fuel`
- **Chartable**: `True`

#### Ângulo da Fase de Injeção (Injection Angle)
- **CSV Field**: `Ângulo_da_Fase_de_Injeção`
- **Database Field**: `injection_angle`
- **Data Type**: `float`
- **Unit**: `°`
- **Range**: `-180.0 - 180.0`
- **Precision**: `1 decimal place`
- **Required**: `False`
- **Description**: Injection timing angle in degrees
- **Validation**: Must be between -180 and 180 degrees
- **Category**: `fuel`
- **Chartable**: `True`

#### Abertura Bicos A (Injector Opening Bank A)
- **CSV Field**: `Abertura_bicos_A`
- **Database Field**: `injector_opening_a`
- **Data Type**: `float`
- **Unit**: `%`
- **Range**: `0.0 - 100.0`
- **Precision**: `2 decimal places`
- **Required**: `False`
- **Description**: Injector opening percentage for bank A
- **Validation**: Must be between 0 and 100 percent
- **Category**: `fuel`
- **Chartable**: `True`

#### Tempo de Injeção Banco A (Injection Time Bank A)
- **CSV Field**: `Tempo_de_Injeção_Banco_A`
- **Database Field**: `injection_time_bank_a`
- **Data Type**: `float`
- **Unit**: `ms`
- **Range**: `0.0 - 50.0`
- **Precision**: `2 decimal places`
- **Required**: `False`
- **Description**: Injection pulse width for bank A injectors in milliseconds
- **Validation**: Must be between 0 and 50 milliseconds
- **Category**: `fuel`
- **Chartable**: `True`

### 3. Temperature & Pressure Sensors

#### Temp. do Motor (Engine Temperature)
- **CSV Field**: `Temp._do_motor`
- **Database Field**: `engine_temp`
- **Data Type**: `float`
- **Unit**: `°C`
- **Range**: `-40.0 - 200.0`
- **Precision**: `1 decimal place`
- **Required**: `False`
- **Description**: Engine coolant temperature in Celsius
- **Validation**: Must be between -40 and 200 °C
- **Category**: `sensor`
- **Chartable**: `True`

#### Temp. do Ar (Air Temperature)
- **CSV Field**: `Temp._do_Ar`
- **Database Field**: `air_temp`
- **Data Type**: `float`
- **Unit**: `°C`
- **Range**: `-40.0 - 100.0`
- **Precision**: `1 decimal place`
- **Required**: `False`
- **Description**: Intake air temperature in Celsius
- **Validation**: Must be between -40 and 100 °C
- **Category**: `sensor`
- **Chartable**: `True`

#### Pressão de Óleo (Oil Pressure)
- **CSV Field**: `Pressão_de_Óleo`
- **Database Field**: `oil_pressure`
- **Data Type**: `float`
- **Unit**: `bar`
- **Range**: `0.0 - 10.0`
- **Precision**: `2 decimal places`
- **Required**: `False`
- **Description**: Engine oil pressure in bar
- **Validation**: Must be between 0 and 10 bar
- **Category**: `sensor`
- **Chartable**: `True`

#### Pressão de Combustível (Fuel Pressure)
- **CSV Field**: `Pressão_de_Combustível`
- **Database Field**: `fuel_pressure`
- **Data Type**: `float`
- **Unit**: `bar`
- **Range**: `0.0 - 10.0`
- **Precision**: `2 decimal places`
- **Required**: `False`
- **Description**: Fuel rail pressure in bar
- **Validation**: Must be between 0 and 10 bar
- **Category**: `sensor`
- **Chartable**: `True`

#### Pressão Diferencial de Combustível (Fuel Differential Pressure)
- **CSV Field**: `Pressão_diferencial_de_combustível`
- **Database Field**: `fuel_diff_pressure`
- **Data Type**: `float`
- **Unit**: `bar`
- **Range**: `-2.0 - 5.0`
- **Precision**: `2 decimal places`
- **Required**: `False`
- **Description**: Differential fuel pressure (fuel pressure - manifold pressure)
- **Validation**: Must be between -2 and 5 bar
- **Category**: `sensor`
- **Chartable**: `True`

### 4. Electrical System

#### Tensão da Bateria (Battery Voltage)
- **CSV Field**: `Tensão_da_Bateria`
- **Database Field**: `battery_voltage`
- **Data Type**: `float`
- **Unit**: `V`
- **Range**: `8.0 - 18.0`
- **Precision**: `2 decimal places`
- **Required**: `False`
- **Description**: Battery voltage in volts
- **Validation**: Must be between 8 and 18 volts
- **Category**: `system`
- **Chartable**: `True`

#### Dwell de Ignição (Ignition Dwell)
- **CSV Field**: `Dwell_de_ignição`
- **Database Field**: `ignition_dwell`
- **Data Type**: `float`
- **Unit**: `ms`
- **Range**: `0.0 - 20.0`
- **Precision**: `2 decimal places`
- **Required**: `False`
- **Description**: Ignition coil dwell time in milliseconds
- **Validation**: Must be between 0 and 20 milliseconds
- **Category**: `ignition`
- **Chartable**: `True`

### 5. Control System Flags

#### 2-Step (Launch Control)
- **CSV Field**: `2-step`
- **Database Field**: `two_step`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Two-step launch control system active status
- **Validation**: Must be boolean value
- **Category**: `control`
- **Chartable**: `False`

#### Largada Validada (Launch Validated)
- **CSV Field**: `Largada_validada`
- **Database Field**: `launch_validated`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Launch control validation status
- **Validation**: Must be boolean value
- **Category**: `control`
- **Chartable**: `False`

#### Marcha (Gear)
- **CSV Field**: `Marcha`
- **Database Field**: `gear`
- **Data Type**: `integer`
- **Unit**: `-`
- **Range**: `0 - 8`
- **Precision**: `0 decimal places`
- **Required**: `False`
- **Description**: Current gear selection (0=neutral, 1-8=gears)
- **Validation**: Must be between 0 and 8
- **Category**: `control`
- **Chartable**: `True`

### 6. System Status Signals

#### Sinal de Sincronia do Motor (Engine Sync Signal)
- **CSV Field**: `Sinal_de_sincronia_do_motor`
- **Database Field**: `sync_signal`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Engine synchronization signal status
- **Validation**: Must be boolean value
- **Category**: `system`
- **Chartable**: `False`

#### Corte na Desaceleração (Deceleration Cutoff)
- **CSV Field**: `Corte_na_desaceleração_(cutoff)`
- **Database Field**: `decel_cutoff`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Deceleration fuel cutoff active status
- **Validation**: Must be boolean value
- **Category**: `control`
- **Chartable**: `False`

#### Partida do Motor (Engine Start)
- **CSV Field**: `Partida_do_motor`
- **Database Field**: `engine_start`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Engine start sequence active status
- **Validation**: Must be boolean value
- **Category**: `control`
- **Chartable**: `False`

#### Lenta (Idle)
- **CSV Field**: `Lenta`
- **Database Field**: `idle`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Idle speed control active status
- **Validation**: Must be boolean value
- **Category**: `control`
- **Chartable**: `False`

### 7. Advanced Injection Control

#### Primeiro Pulso de Partida (First Start Pulse)
- **CSV Field**: `Primeiro_pulso_de_partida`
- **Database Field**: `first_start_pulse`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: First injection pulse during engine start
- **Validation**: Must be boolean value
- **Category**: `fuel`
- **Chartable**: `False`

#### Injeção Rápida e de Decaimento (Fast and Decay Injection)
- **CSV Field**: `Injeção_rápida_e_de_decaimento`
- **Database Field**: `fast_decay_injection`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Fast injection with decay mode active
- **Validation**: Must be boolean value
- **Category**: `fuel`
- **Chartable**: `False`

#### Ajuste Ativo (Active Adjustment)
- **CSV Field**: `Ajuste_ativo`
- **Database Field**: `active_adjustment`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Active tune adjustment mode enabled
- **Validation**: Must be boolean value
- **Category**: `control`
- **Chartable**: `False`

#### Eletroventilador 2 (Cooling Fan 2)
- **CSV Field**: `Eletroventilador_2`
- **Database Field**: `cooling_fan_2`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Secondary cooling fan status
- **Validation**: Must be boolean value
- **Category**: `system`
- **Chartable**: `False`

#### Bomba Combustível (Fuel Pump)
- **CSV Field**: `Bomba_Combustível`
- **Database Field**: `fuel_pump`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Fuel pump operation status
- **Validation**: Must be boolean value
- **Category**: `fuel`
- **Chartable**: `False`

### 8. Additional Control Parameters

#### Delta TPS
- **CSV Field**: `Delta_TPS`
- **Database Field**: `delta_tps`
- **Data Type**: `float`
- **Unit**: `%/s`
- **Range**: `-100.0 - 100.0`
- **Precision**: `2 decimal places`
- **Required**: `False`
- **Description**: Rate of change of throttle position (delta TPS)
- **Validation**: Must be between -100 and 100 %/s
- **Category**: `control`
- **Chartable**: `True`

#### 2-Step - Botão (Two-Step Button)
- **CSV Field**: `2-step_-_Botão`
- **Database Field**: `two_step_button`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Two-step button input status
- **Validation**: Must be boolean value
- **Category**: `control`
- **Chartable**: `False`

#### Injeção Rápida (Fast Injection)
- **CSV Field**: `Injeção_rápida`
- **Database Field**: `fast_injection`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Fast injection mode active
- **Validation**: Must be boolean value
- **Category**: `fuel`
- **Chartable**: `False`

#### Injeção de Decaimento (Decay Injection)
- **CSV Field**: `Injeção_de_decaimento`
- **Database Field**: `decay_injection`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Decay injection mode active
- **Validation**: Must be boolean value
- **Category**: `fuel`
- **Chartable**: `False`

#### Cutoff de Injeção (Injection Cutoff)
- **CSV Field**: `Cutoff_de_injeção`
- **Database Field**: `injection_cutoff`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Fuel injection cutoff active
- **Validation**: Must be boolean value
- **Category**: `fuel`
- **Chartable**: `False`

#### Injeção Pós-Partida (Post-Start Injection)
- **CSV Field**: `Injeção_pós_partida`
- **Database Field**: `post_start_injection`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Post-start enrichment injection active
- **Validation**: Must be boolean value
- **Category**: `fuel`
- **Chartable**: `False`

#### Botão de Partida - Alternar (Start Button Toggle)
- **CSV Field**: `Botão_de_partida_-_Alternar`
- **Database Field**: `start_button_toggle`
- **Data Type**: `boolean`
- **Unit**: `-`
- **Range**: `True/False`
- **Precision**: `-`
- **Required**: `False`
- **Description**: Start button toggle input status
- **Validation**: Must be boolean value
- **Category**: `control`
- **Chartable**: `False`

## Field Mapping Configuration

### CSV to Database Field Mapping
```python
FIELD_MAPPING = {
    'TIME': 'timestamp',
    'RPM': 'rpm',
    'Posição_do_acelerador': 'throttle_position',
    'Ponto_de_ignição': 'ignition_timing',
    'MAP': 'map_pressure',
    'Sonda_Geral': 'lambda_sensor',
    '2-step': 'two_step',
    'Largada_validada': 'launch_validated',
    'Marcha': 'gear',
    'Vazão_da_bancada_A': 'fuel_flow_bank_a',
    'Fluxo_total_de_combustível': 'total_fuel_flow',
    'Ângulo_da_Fase_de_Injeção': 'injection_angle',
    'Abertura_bicos_A': 'injector_opening_a',
    'Tempo_de_Injeção_Banco_A': 'injection_time_bank_a',
    'Temp._do_motor': 'engine_temp',
    'Temp._do_Ar': 'air_temp',
    'Pressão_de_Óleo': 'oil_pressure',
    'Pressão_de_Combustível': 'fuel_pressure',
    'Pressão_diferencial_de_combustível': 'fuel_diff_pressure',
    'Tensão_da_Bateria': 'battery_voltage',
    'Dwell_de_ignição': 'ignition_dwell',
    'Sinal_de_sincronia_do_motor': 'sync_signal',
    'Corte_na_desaceleração_(cutoff)': 'decel_cutoff',
    'Partida_do_motor': 'engine_start',
    'Lenta': 'idle',
    'Primeiro_pulso_de_partida': 'first_start_pulse',
    'Injeção_rápida_e_de_decaimento': 'fast_decay_injection',
    'Ajuste_ativo': 'active_adjustment',
    'Eletroventilador_2': 'cooling_fan_2',
    'Bomba_Combustível': 'fuel_pump',
    'Delta_TPS': 'delta_tps',
    '2-step_-_Botão': 'two_step_button',
    'Injeção_rápida': 'fast_injection',
    'Injeção_de_decaimento': 'decay_injection',
    'Cutoff_de_injeção': 'injection_cutoff',
    'Injeção_pós_partida': 'post_start_injection',
    'Botão_de_partida_-_Alternar': 'start_button_toggle'
}
```

### Data Type Mapping
```python
DATA_TYPE_MAPPING = {
    'timestamp': float,
    'rpm': int,
    'throttle_position': float,
    'ignition_timing': float,
    'map_pressure': float,
    'lambda_sensor': float,
    'two_step': bool,
    'launch_validated': bool,
    'gear': int,
    'fuel_flow_bank_a': float,
    'total_fuel_flow': float,
    'injection_angle': float,
    'injector_opening_a': float,
    'injection_time_bank_a': float,
    'engine_temp': float,
    'air_temp': float,
    'oil_pressure': float,
    'fuel_pressure': float,
    'fuel_diff_pressure': float,
    'battery_voltage': float,
    'ignition_dwell': float,
    'sync_signal': bool,
    'decel_cutoff': bool,
    'engine_start': bool,
    'idle': bool,
    'first_start_pulse': bool,
    'fast_decay_injection': bool,
    'active_adjustment': bool,
    'cooling_fan_2': bool,
    'fuel_pump': bool,
    'delta_tps': float,
    'two_step_button': bool,
    'fast_injection': bool,
    'decay_injection': bool,
    'injection_cutoff': bool,
    'post_start_injection': bool,
    'start_button_toggle': bool
}
```

### Validation Rules
```python
VALIDATION_RULES = {
    'rpm': {'min': 0, 'max': 20000},
    'throttle_position': {'min': 0.0, 'max': 100.0},
    'ignition_timing': {'min': -30.0, 'max': 50.0},
    'map_pressure': {'min': -1.0, 'max': 5.0},
    'lambda_sensor': {'min': 0.5, 'max': 2.0},
    'gear': {'min': 0, 'max': 8},
    'fuel_flow_bank_a': {'min': 0.0, 'max': 1000.0},
    'total_fuel_flow': {'min': 0.0, 'max': 2000.0},
    'injection_angle': {'min': -180.0, 'max': 180.0},
    'injector_opening_a': {'min': 0.0, 'max': 100.0},
    'injection_time_bank_a': {'min': 0.0, 'max': 50.0},
    'engine_temp': {'min': -40.0, 'max': 200.0},
    'air_temp': {'min': -40.0, 'max': 100.0},
    'oil_pressure': {'min': 0.0, 'max': 10.0},
    'fuel_pressure': {'min': 0.0, 'max': 10.0},
    'fuel_diff_pressure': {'min': -2.0, 'max': 5.0},
    'battery_voltage': {'min': 8.0, 'max': 18.0},
    'ignition_dwell': {'min': 0.0, 'max': 20.0},
    'delta_tps': {'min': -100.0, 'max': 100.0}
}
```

## Usage in Python Implementation

### Pydantic Models
```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class LogEntryModel(BaseModel):
    """Pydantic model for log entry validation"""
    
    timestamp: float = Field(..., ge=0.0, description="Timestamp in seconds")
    rpm: int = Field(..., ge=0, le=20000, description="Engine RPM")
    throttle_position: Optional[float] = Field(None, ge=0.0, le=100.0)
    ignition_timing: Optional[float] = Field(None, ge=-30.0, le=50.0)
    map_pressure: Optional[float] = Field(None, ge=-1.0, le=5.0)
    lambda_sensor: Optional[float] = Field(None, ge=0.5, le=2.0)
    
    # Boolean fields
    two_step: Optional[bool] = None
    launch_validated: Optional[bool] = None
    sync_signal: Optional[bool] = None
    # ... additional boolean fields
    
    # Additional numeric fields
    gear: Optional[int] = Field(None, ge=0, le=8)
    fuel_flow_bank_a: Optional[float] = Field(None, ge=0.0)
    # ... additional fields
    
    class Config:
        validate_assignment = True
        extra = "forbid"
```

### Database Schema (SQLAlchemy)
```python
from sqlalchemy import Column, Integer, Float, Boolean, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class LogEntry(Base):
    """SQLAlchemy model for log entries"""
    
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    
    # Core fields
    timestamp = Column(Float, nullable=False, index=True)
    rpm = Column(Integer, nullable=False, index=True)
    throttle_position = Column(Float, nullable=True)
    ignition_timing = Column(Float, nullable=True)
    map_pressure = Column(Float, nullable=True, index=True)
    lambda_sensor = Column(Float, nullable=True)
    
    # Boolean control flags
    two_step = Column(Boolean, nullable=True)
    launch_validated = Column(Boolean, nullable=True)
    sync_signal = Column(Boolean, nullable=True)
    # ... additional boolean fields
    
    # Additional numeric fields  
    gear = Column(Integer, nullable=True)
    fuel_flow_bank_a = Column(Float, nullable=True)
    total_fuel_flow = Column(Float, nullable=True)
    # ... additional fields
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Data Quality Considerations

### Missing Data Handling
- **Timestamp and RPM**: Required fields, reject records if missing
- **Optional Fields**: Store as NULL/None, handle gracefully in analysis
- **Boolean Fields**: Default to False if missing, with explicit validation

### Outlier Detection
- **Statistical Bounds**: Flag values outside 3 standard deviations
- **Physical Limits**: Enforce realistic physical constraints
- **Temporal Consistency**: Check for impossible rate changes

### Data Cleaning Pipeline
1. **Format Validation**: Check data types and formats
2. **Range Validation**: Apply min/max constraints
3. **Consistency Checks**: Validate relationships between fields
4. **Duplicate Detection**: Identify and handle duplicate timestamps
5. **Gap Analysis**: Identify and flag data gaps or jumps

---

*This data dictionary serves as the authoritative reference for all FuelTech data processing in the FuelTune Analyzer application. All CSV import, database operations, and analysis functions must conform to these field specifications.*