# RELATÓRIO DE ANÁLISE DE CÁLCULOS - FUELTUNE ANALYZER

## Resumo Executivo

### Totais Identificados
- **Tipos de Mapas:** 9 tipos encontrados
- **Mapas 2D:** 6 tipos (main_fuel, tps_correction, temp_correction, air_temp_correction, voltage_correction, rpm_compensation)
- **Mapas 3D:** 4 tipos (main_fuel, lambda_target, ignition_timing, ve_table)
- **Estratégias:** 3 estratégias principais (conservative, balanced, aggressive)
- **Funções Principais:** 15+ funções de cálculo identificadas

### Status da Implementação
- **✅ Implementado:** Estrutura básica 3D com 4 tipos de mapas
- **⚠️ Parcial:** Mapas 2D com função universal incompleta
- **❌ Faltante:** Funções específicas 2D (TPS, temp, voltage, etc.)

---

## Catálogo de Cálculos

### MAPAS 2D

#### 1. main_fuel_2d_map - Mapa Principal de Combustível 2D
**Localização:** `fuel_maps_2d.py.backup`
**Função:** `calculate_map_values_universal() -> calculate_map_values()`

**Parâmetros de Entrada:**
- `map_values`: Lista de valores MAP (-1.0 a 2.0 bar)
- `vehicle_data`: Dados do veículo
- `strategy`: Estratégia de tuning
- `safety_factor`: Fator de segurança

**Estratégias Disponíveis:**
- **Conservative:** Fator base 0.85, AFR rica (11.0-13.5)
- **Balanced:** Fator base 1.0, AFR padrão (12.0-14.2)  
- **Aggressive:** Fator base 1.15, AFR pobre (12.5-14.7)

**Fórmula de Cálculo:**
```python
# Cálculo base por MAP
if abs(map_value) < 10:  # Valor em bar
    map_bar_relative = map_value
else:
    map_bar_relative = map_value / 100  # Converter kPa para bar

map_kpa = (map_bar_relative + 1.013) * 100  # Pressão absoluta
afr_target = get_afr_target(map_kpa, strategy)

# Tempo de injeção base
base_time = calculate_base_injection_time(
    map_kpa, rpm, displacement, cylinders, 
    injector_flow, afr_target, boost_pressure
)

# Aplicar correções
final_value = base_time * engine_factor * fuel_factor * turbo_factor * safety_factor
```

**Particularidades:**
- Suporte para turbo (valores MAP positivos)
- Correção por tipo de combustível (Gasolina/Etanol/Flex)
- Limites: 0.0 - 50.0 ms

#### 2. tps_correction_2d - Correção por TPS
**Localização:** `fuel_maps_2d.py.backup`
**Função:** `calculate_tps_correction()`

**Parâmetros de Entrada:**
- `tps_values`: Lista de valores TPS (0-100%)
- `strategy`: Estratégia de correção

**Estratégias Disponíveis:**
```python
strategy_factors = {
    "conservative": {"economy": -2.0, "neutral": 0.0, "power": 8.0, "wot": 12.0},
    "balanced": {"economy": -5.0, "neutral": 0.0, "power": 10.0, "wot": 15.0},
    "aggressive": {"economy": -8.0, "neutral": 0.0, "power": 15.0, "wot": 20.0},
}
```

**Fórmula de Cálculo:**
```python
if tps <= 20:  # Zona de economia
    correction = factors["economy"] * (tps / 20.0)
elif tps <= 70:  # Zona neutra
    transition = (tps - 20) / 50.0
    correction = factors["economy"] * (1 - transition)
elif tps < 100:  # Zona de potência
    transition = (tps - 70) / 30.0
    correction = factors["power"] * transition
else:  # WOT (100%)
    correction = factors["wot"]
```

**Particularidades:**
- 4 zonas de operação bem definidas
- Transições suaves entre zonas
- Limites: -50.0 a +50.0%

#### 3. temp_correction_2d - Correção por Temperatura
**Localização:** `fuel_maps_2d.py.backup`
**Função:** `calculate_temp_correction()`

**Parâmetros de Entrada:**
- `temp_values`: Lista de temperaturas (-10 a 140°C)
- `cooling_type`: Tipo de refrigeração ("water"/"air")
- `climate`: Tipo de clima ("cold"/"temperate"/"hot")

**Estratégias por Refrigeração:**
```python
cooling_factors = {
    "water": {"cold_max": 25.0, "hot_max": 8.0},
    "air": {"cold_max": 30.0, "hot_max": 12.0},
}
climate_factors = {"cold": 0.8, "temperate": 1.0, "hot": 1.3}
```

**Fórmula de Cálculo:**
```python
if temp < 40:  # Motor frio
    correction = cool_factor["cold_max"] * ((40 - temp) / 50) * climate_factor
elif temp <= 90:  # Temperatura ideal
    correction = 0.0  # Sem correção
else:  # Motor quente
    correction = cool_factor["hot_max"] * ((temp - 90) / 50) * climate_factor
```

#### 4. air_temp_correction_2d - Correção por Temperatura do Ar
**Localização:** `fuel_maps_2d.py.backup`
**Função:** `calculate_air_temp_correction()`

**Fórmula de Cálculo:**
```python
# Baseado na lei dos gases ideais
ref_temp = 25.0  # Temperatura de referência
temp_absolute = air_temp + 273.15
ref_temp_absolute = ref_temp + 273.15
density_ratio = ref_temp_absolute / temp_absolute

# Correção percentual
correction = (1.0 - density_ratio) * 100
# Limitar a ±15%
correction = max(-15.0, min(15.0, correction))
```

#### 5. voltage_correction_2d - Correção por Voltagem
**Localização:** `fuel_maps_2d.py.backup`
**Função:** `calculate_voltage_correction()`

**Parâmetros:**
```python
dead_time_base = {
    "high": 1.0,  # Bicos alta impedância (12-16Ω)
    "low": 0.6,   # Bicos baixa impedância (2-3Ω)
}
```

**Fórmula de Cálculo:**
```python
base_voltage = 13.5
voltage_ratio = base_voltage / voltage

# Dead time corrigido
dead_time_correction = base_dead_time * (voltage_ratio - 1.0)
# Limitar correção
dead_time_correction = max(-2.0, min(3.0, dead_time_correction))
```

#### 6. rpm_compensation_2d - Compensação por RPM
**Localização:** `fuel_maps_2d.py.backup`
**Função:** `calculate_rpm_compensation()`

**Fórmula de Cálculo:**
```python
start_correction_rpm = 2400
peak_rpm = 4200 if not has_turbo else 4500

if rpm < idle_rpm:
    correction = 0.0
elif rpm < start_correction_rpm:
    correction = 0.0  # Sem correção até 2400 RPM
elif rpm <= peak_rpm:
    # Crescimento linear até o pico
    progress = (rpm - start_correction_rpm) / (peak_rpm - start_correction_rpm)
    max_correction = 18.0 if has_turbo else 15.0
    correction = max_correction * progress
else:
    # Decrescimento após o pico
    decay_factor = (redline - rpm) / (redline - peak_rpm)
    max_correction = 18.0 if has_turbo else 15.0
    correction = max_correction * max(0, decay_factor)
```

### MAPAS 3D

#### 1. main_fuel_3d_map - Mapa Principal de Combustível 3D
**Localização:** `fuel_maps_3d.py.backup` + `calculations.py`
**Função:** `calculate_fuel_3d_matrix()`

**Parâmetros de Entrada:**
- `rpm_axis`: Array de RPM (400-12000)
- `map_axis`: Array de MAP (-1.0 a 4.2 bar)
- `vehicle_data`: Dados completos do veículo
- `strategy`: Estratégia AFR
- `safety_factor`: Fator de segurança

**Estratégias AFR 3D:**
```python
STRATEGY_PRESETS = {
    "conservative": {
        "idle": 13.5, "cruise": 14.0, "load": 12.5, 
        "wot": 11.5, "boost": 11.0, "safety_factor": 1.1
    },
    "balanced": {
        "idle": 14.2, "cruise": 14.7, "load": 13.2, 
        "wot": 12.5, "boost": 12.0, "safety_factor": 1.0
    },
    "aggressive": {
        "idle": 14.7, "cruise": 15.5, "load": 13.8, 
        "wot": 13.0, "boost": 12.5, "safety_factor": 0.9
    }
}
```

**Fórmula de Cálculo:**
```python
def calculate_base_injection_time_3d():
    # Converter MAP para pressão absoluta
    map_bar = map_kpa / 100.0
    
    # Pressão de combustível com correção boost
    fuel_pressure_actual = fuel_pressure_base + boost_pressure
    flow_correction = (fuel_pressure_actual / fuel_pressure_base) ** 0.5
    effective_flow = injector_flow_cc_min * flow_correction
    
    # Densidade do ar
    air_density_correction = map_bar / 1.013
    
    # Volume de ar por ciclo
    volume_per_cycle = (displacement / cylinders) * (rpm / 60 / 2)
    air_mass_per_cycle = volume_per_cycle * air_density_correction
    
    # Massa de combustível necessária
    fuel_mass_needed = air_mass_per_cycle / afr_target
    
    # Tempo de injeção
    injection_time = fuel_volume_ml / effective_flow * 60 * 1000
    
    return max(0.5, min(50.0, injection_time))
```

#### 2. lambda_target_3d_map - Mapa de Lambda Alvo 3D
**Localização:** `fuel_maps_3d.py.backup` + `calculations.py`
**Função:** `calculate_lambda_3d_matrix()`

**Fórmula de Cálculo:**
```python
def calculate_lambda_3d_matrix():
    for i, map_value in enumerate(map_axis):
        map_kpa = (map_value + 1.013) * 100 if map_value < 0 else (map_value + 1.013) * 100
        
        for j, rpm in enumerate(rpm_axis):
            afr_target = get_afr_target_3d(map_kpa, strategy)
            # Lambda = AFR / AFR_stoich (14.7 para gasolina)
            lambda_value = afr_target / 14.7
            matrix[i, j] = max(0.7, min(1.3, lambda_value))
```

#### 3. ignition_timing_3d_map - Mapa de Ignição 3D
**Localização:** `fuel_maps_3d.py.backup` + `calculations.py`
**Função:** `calculate_ignition_3d_matrix()`

**Estratégias de Avanço:**
```python
base_advance = {
    "conservative": {"idle": 10, "cruise": 25, "load": 20, "wot": 15, "boost": 10},
    "balanced": {"idle": 12, "cruise": 30, "load": 25, "wot": 20, "boost": 15},
    "aggressive": {"idle": 15, "cruise": 35, "load": 30, "wot": 25, "boost": 20},
}
```

**Fórmula de Cálculo:**
```python
def calculate_ignition_3d_matrix():
    # Avanço base por RPM
    base_advance = 15.0 + (rpm - 1000) / 1000 * 5.0
    
    # Correção por carga (MAP)
    if map_kpa < 50:  # Vácuo - mais avanço
        load_correction = 5.0
    elif map_kpa < 90:  # Carga parcial
        load_correction = 2.0
    elif map_kpa < 100:  # WOT atmosférico
        load_correction = 0.0
    else:  # Boost - menos avanço
        boost_level = (map_kpa - 100) / 100
        load_correction = -3.0 * boost_level
    
    # Correção por octanagem
    octane_correction = (octane_rating - 91) * 0.5
    
    total_advance = base_advance + load_correction + octane_correction
    return max(-10.0, min(45.0, total_advance))
```

#### 4. ve_table_3d_map - Tabela de Eficiência Volumétrica 3D
**Localização:** `map_types.json` (configuração apenas)
**Status:** Não implementado nos backups

**Configuração:**
- **Unidade:** % (0.0 - 150.0)
- **Grid:** 16x16
- **Eixos:** RPM x MAP

---

## Matriz de Estratégias

| Tipo de Mapa | Conservative | Balanced | Aggressive |
|---------------|-------------|----------|------------|
| **main_fuel_2d_map** | Fator: 0.85<br>AFR rica | Fator: 1.0<br>AFR padrão | Fator: 1.15<br>AFR pobre |
| **tps_correction_2d** | Eco: -2%, Power: +8% | Eco: -5%, Power: +10% | Eco: -8%, Power: +15% |
| **main_fuel_3d_map** | Safety: 1.1<br>Boost AFR: 11.0 | Safety: 1.0<br>Boost AFR: 12.0 | Safety: 0.9<br>Boost AFR: 12.5 |
| **lambda_target_3d** | Lambda rica | Lambda estequiométrica | Lambda pobre |
| **ignition_3d_map** | Avanço conservador | Avanço padrão | Avanço agressivo |

---

## Dependências

### Parâmetros do Veículo Obrigatórios
```python
vehicle_data = {
    "displacement": 2000,        # Cilindrada em cc
    "cylinders": 4,              # Número de cilindros
    "injector_flow": 440,        # Vazão bicos em cc/min
    "fuel_type": "Gasolina",     # Tipo de combustível
}
```

### Parâmetros Opcionais
```python
optional_params = {
    "turbo": False,              # Tem turbo
    "boost_pressure": 0,         # Pressão de boost
    "redline_rpm": 7000,         # RPM máximo
    "idle_rpm": 800,             # RPM marcha lenta
    "cooling_type": "water",     # Tipo arrefecimento
    "injector_impedance": "high", # Impedância bicos
    "octane_rating": 91,         # Octanagem combustível
}
```

### Funções Auxiliares Identificadas

#### Interpolação e Suavização
```python
# Implementadas em calculations.py
def interpolate_3d_matrix(matrix, method="linear") -> np.ndarray
def apply_safety_corrections(matrix, map_type, safety_factor) -> np.ndarray

# Faltantes (identificadas nos backups)
def smooth_values()
def apply_gaussian_filter()
```

#### Conversões
```python
# Implementadas
def lambda_to_afr(lambda_val) -> float:
    return lambda_val * 14.7

# Faltantes  
def ms_to_duty_cycle()
def afr_to_lambda()
```

#### Validação
```python
# Faltantes (referenciadas nos backups)
def validate_range()
def check_monotonic()
```

---

## Recomendações de Implementação

### Ordem Sugerida
1. **ALTA PRIORIDADE:** Migrar funções 2D específicas do backup
   - `calculate_tps_correction()`
   - `calculate_temp_correction()`
   - `calculate_air_temp_correction()`
   - `calculate_voltage_correction()`
   - `calculate_rpm_compensation()`

2. **MÉDIA PRIORIDADE:** Implementar função universal 2D completa
   - Integrar todas as funções específicas
   - Adicionar validações
   - Implementar limites de segurança

3. **BAIXA PRIORIDADE:** Melhorar funções 3D existentes
   - Adicionar interpolação avançada
   - Implementar suavização
   - Adicionar ve_table_3d_map

### Pontos de Atenção

#### Estrutura de Dados
- **CRÍTICO:** Orientação de matrizes 3D inconsistente
  ```python
  # backup: matrix[map_index, rpm_index] 
  # atual: matrix[rpm_index, map_index]
  ```

#### Conversões de Unidades
- MAP: Verificar se valores são relativos ou absolutos
- Pressão: bar vs kPa vs psi
- Vazão: cc/min vs lbs/h

#### Validações Necessárias
```python
def validate_calculations():
    # Validar ranges por tipo de mapa
    # Verificar monotonia onde necessário
    # Aplicar limites de segurança
    # Validar dados do veículo
```

### Estrutura Recomendada
```python
# src/core/fuel_maps/calculations/
├── __init__.py
├── universal.py          # Função universal (2D e 3D)
├── maps_2d.py           # Todas as funções 2D específicas
├── maps_3d.py           # Todas as funções 3D específicas  
├── strategies.py        # Definições de estratégias
├── validators.py        # Funções de validação
└── converters.py        # Conversões de unidades
```

---

## Conclusões

### O que está Funcionando
- ✅ Estrutura básica 3D implementada
- ✅ Função universal 3D funcional
- ✅ 4 tipos de mapas 3D implementados
- ✅ Sistema de estratégias definido

### O que Precisa ser Migrado
- ❌ 5 funções específicas de mapas 2D
- ❌ Função universal 2D completa
- ❌ Validações e conversões auxiliares
- ❌ Interpolação e suavização avançadas

### Estimativa de Trabalho
- **Migração 2D:** 2-3 dias (alta complexidade)
- **Testes e validação:** 1-2 dias
- **Documentação:** 1 dia
- **Total:** 4-6 dias

---

**Versão:** 1.0  
**Data:** Janeiro 2025  
**Status:** Análise Completa  
**Próximo passo:** Migração das funções 2D