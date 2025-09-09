# A11 - IMPLEMENT 2D CALCULATIONS

## 📋 Objetivo
Migrar todas as funções de cálculo 2D dos arquivos de backup para a estrutura modular atual, padronizando a nomenclatura para usar "Compensação" em vez de "Correção", seguindo o padrão FuelTech.

## 🎯 Escopo da Implementação

### Funções a Migrar do Backup
Baseado na análise do agente A10, precisamos migrar 5 funções específicas de `fuel_maps_2d.py.backup`:

1. **calculate_tps_compensation()** - Compensação por TPS
2. **calculate_temp_compensation()** - Compensação por temperatura do motor  
3. **calculate_air_temp_compensation()** - Compensação por temperatura do ar
4. **calculate_voltage_compensation()** - Compensação por voltagem (dead time)
5. **calculate_rpm_compensation()** - Compensação por RPM

### Nomenclatura Padronizada
**IMPORTANTE**: Usar "Compensação" em vez de "Correção" em todos os lugares:
- Nomes de funções
- Comentários
- Strings de interface
- Tipos de mapas no JSON

## 📁 Estrutura de Arquivos

### Arquivo Principal a Modificar
`/Users/leechardes/Projetos/fueltune/fueltune-analyzer/src/core/fuel_maps/calculations.py`

### Arquivos de Configuração a Atualizar
`/Users/leechardes/Projetos/fueltune/fueltune-analyzer/config/map_types.json`
- Renomear "correction" para "compensation" em todos os tipos 2D

### Arquivo de Referência
`/Users/leechardes/Projetos/fueltune/fueltune-analyzer/src/ui/pages/fuel_maps_2d.py.backup`

## 🔧 Implementação Detalhada

### 1. Atualizar map_types.json
Renomear os tipos de mapas 2D:
```json
{
  "tps_compensation_2d": {  // Era tps_correction_2d
    "name": "Compensação por TPS",
    "unit": "%",
    ...
  },
  "temp_compensation_2d": {  // Era temp_correction_2d
    "name": "Compensação por Temperatura",
    "unit": "%",
    ...
  },
  "air_temp_compensation_2d": {  // Era air_temp_correction_2d
    "name": "Compensação por Temp. Ar",
    "unit": "%",
    ...
  },
  "voltage_compensation_2d": {  // Era voltage_correction_2d
    "name": "Compensação por Voltagem",
    "unit": "ms",
    ...
  }
}
```

### 2. Estrutura das Funções em calculations.py

#### A. Compensação por TPS
```python
def calculate_tps_compensation(
    tps_values: List[float],
    strategy: str = "balanced",
    safety_factor: float = 1.0
) -> List[float]:
    """
    Calcula compensação baseada na posição do acelerador (TPS).
    
    Args:
        tps_values: Lista de valores TPS (0-100%)
        strategy: Estratégia de compensação
        safety_factor: Fator de segurança adicional
        
    Returns:
        Lista de valores de compensação em %
    """
    # Implementação conforme backup
```

#### B. Compensação por Temperatura do Motor
```python
def calculate_temp_compensation(
    temp_values: List[float],
    cooling_type: str = "water",
    climate: str = "temperate",
    strategy: str = "balanced"
) -> List[float]:
    """
    Calcula compensação baseada na temperatura do motor.
    
    Args:
        temp_values: Lista de temperaturas (-10 a 140°C)
        cooling_type: Tipo de refrigeração ("water"/"air")
        climate: Tipo de clima ("cold"/"temperate"/"hot")
        strategy: Estratégia de compensação
        
    Returns:
        Lista de valores de compensação em %
    """
    # Implementação conforme backup
```

#### C. Compensação por Temperatura do Ar
```python
def calculate_air_temp_compensation(
    air_temp_values: List[float],
    altitude: float = 0.0,
    humidity: float = 50.0
) -> List[float]:
    """
    Calcula compensação baseada na temperatura do ar de admissão.
    Usa lei dos gases ideais para correção de densidade.
    
    Args:
        air_temp_values: Lista de temperaturas do ar (-20 a 60°C)
        altitude: Altitude em metros (opcional)
        humidity: Umidade relativa % (opcional)
        
    Returns:
        Lista de valores de compensação em %
    """
    # Implementação conforme backup
```

#### D. Compensação por Voltagem (Dead Time)
```python
def calculate_voltage_compensation(
    voltage_values: List[float],
    injector_impedance: str = "high",
    injector_flow: float = 440.0
) -> List[float]:
    """
    Calcula compensação de dead time dos injetores por voltagem.
    
    Args:
        voltage_values: Lista de voltagens (8.0 a 16.0V)
        injector_impedance: Impedância dos bicos ("high"/"low")
        injector_flow: Vazão dos bicos em cc/min
        
    Returns:
        Lista de valores de compensação em ms
    """
    # Implementação conforme backup
```

#### E. Compensação por RPM
```python
def calculate_rpm_compensation(
    rpm_values: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced"
) -> List[float]:
    """
    Calcula compensação baseada no RPM do motor.
    
    Args:
        rpm_values: Lista de valores de RPM (400-12000)
        vehicle_data: Dados do veículo (idle_rpm, redline, has_turbo)
        strategy: Estratégia de compensação
        
    Returns:
        Lista de valores de compensação em %
    """
    # Implementação conforme backup
```

### 3. Função Universal 2D Atualizada
```python
def calculate_map_values_universal(
    map_type: str,
    axis_values: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced",
    safety_factor: float = 1.0,
    **kwargs
) -> List[float]:
    """
    Função universal para cálculo de valores de mapas 2D.
    
    Args:
        map_type: Tipo do mapa (ex: "tps_compensation_2d")
        axis_values: Valores do eixo
        vehicle_data: Dados do veículo
        strategy: Estratégia de cálculo
        safety_factor: Fator de segurança
        **kwargs: Parâmetros adicionais específicos
        
    Returns:
        Lista de valores calculados
    """
    
    # Mapeamento de funções específicas
    calculation_functions = {
        "main_fuel_2d_map": calculate_main_fuel_2d,
        "tps_compensation_2d": calculate_tps_compensation,
        "temp_compensation_2d": calculate_temp_compensation,
        "air_temp_compensation_2d": calculate_air_temp_compensation,
        "voltage_compensation_2d": calculate_voltage_compensation,
        "rpm_compensation_2d": calculate_rpm_compensation,
    }
    
    if map_type not in calculation_functions:
        logger.warning(f"Tipo de mapa 2D não suportado: {map_type}")
        return axis_values  # Retorna valores sem modificação
    
    # Chamar função específica
    calc_func = calculation_functions[map_type]
    
    # Preparar argumentos baseado no tipo
    if map_type == "tps_compensation_2d":
        return calc_func(axis_values, strategy, safety_factor)
    elif map_type == "temp_compensation_2d":
        cooling_type = vehicle_data.get("cooling_type", "water")
        climate = kwargs.get("climate", "temperate")
        return calc_func(axis_values, cooling_type, climate, strategy)
    elif map_type == "air_temp_compensation_2d":
        altitude = kwargs.get("altitude", 0.0)
        humidity = kwargs.get("humidity", 50.0)
        return calc_func(axis_values, altitude, humidity)
    elif map_type == "voltage_compensation_2d":
        injector_impedance = vehicle_data.get("injector_impedance", "high")
        injector_flow = vehicle_data.get("injector_flow", 440.0)
        return calc_func(axis_values, injector_impedance, injector_flow)
    elif map_type == "rpm_compensation_2d":
        return calc_func(axis_values, vehicle_data, strategy)
    else:
        return calc_func(axis_values, vehicle_data, strategy, safety_factor)
```

### 4. Estratégias de Compensação
```python
# Adicionar ao início de calculations.py
COMPENSATION_STRATEGIES = {
    "tps": {
        "conservative": {"economy": -2.0, "neutral": 0.0, "power": 8.0, "wot": 12.0},
        "balanced": {"economy": -5.0, "neutral": 0.0, "power": 10.0, "wot": 15.0},
        "aggressive": {"economy": -8.0, "neutral": 0.0, "power": 15.0, "wot": 20.0},
    },
    "temp": {
        "water": {"cold_max": 25.0, "hot_max": 8.0},
        "air": {"cold_max": 30.0, "hot_max": 12.0},
    },
    "rpm": {
        "conservative": {"max_compensation": 12.0, "start_rpm": 2600},
        "balanced": {"max_compensation": 15.0, "start_rpm": 2400},
        "aggressive": {"max_compensation": 18.0, "start_rpm": 2200},
    }
}
```

## ✅ Checklist de Validação

- [ ] Todas as 5 funções de compensação 2D migradas
- [ ] Nomenclatura "Compensação" aplicada consistentemente
- [ ] map_types.json atualizado com novos nomes
- [ ] Função universal 2D funcionando com todos os tipos
- [ ] Estratégias de compensação implementadas
- [ ] Limites de segurança aplicados em todas as funções
- [ ] Testes unitários para cada função (se aplicável)
- [ ] Interface UI exibindo corretamente os novos nomes

## 🧪 Testes a Realizar

### Teste 1: Compensação por TPS
```python
# Valores de teste
tps_test = [0, 10, 20, 50, 70, 90, 100]
result = calculate_tps_compensation(tps_test, "balanced")
# Verificar transições suaves entre zonas
```

### Teste 2: Compensação por Temperatura
```python
# Teste motor frio/quente
temp_test = [-10, 0, 20, 40, 90, 110, 140]
result = calculate_temp_compensation(temp_test, "water", "temperate")
# Verificar compensação maior em extremos
```

### Teste 3: Função Universal
```python
# Testar todos os tipos
for map_type in ["tps_compensation_2d", "temp_compensation_2d", ...]:
    result = calculate_map_values_universal(
        map_type, test_values, vehicle_data
    )
    assert len(result) == len(test_values)
```

## 🚀 Como Executar

1. **Fazer backup do arquivo atual**
   ```bash
   cp src/core/fuel_maps/calculations.py src/core/fuel_maps/calculations.py.backup
   ```

2. **Atualizar map_types.json**
   - Renomear todos os "correction" para "compensation"
   - Atualizar nomes em português

3. **Implementar funções em calculations.py**
   - Copiar código do backup
   - Adaptar nomenclatura
   - Adicionar docstrings

4. **Testar no servidor em execução**
   - O servidor está rodando com hot-reload
   - Testar cada tipo de mapa 2D
   - Verificar cálculos na aba Ferramentas

5. **Validar interface**
   - Verificar se novos nomes aparecem corretamente
   - Testar aplicação de cálculos
   - Confirmar salvamento de dados

## 🎯 Resultado Esperado

- Sistema completo de compensações 2D funcionando
- Nomenclatura padronizada conforme FuelTech
- Todos os cálculos do backup restaurados
- Interface unificada funcionando para 2D e 3D
- Estratégias aplicadas corretamente

## ⚠️ Pontos de Atenção

1. **Não modificar** funções 3D existentes
2. **Manter compatibilidade** com dados salvos anteriormente
3. **Preservar ranges** de valores conforme configuração JSON
4. **Aplicar limites** de segurança em todos os cálculos
5. **Usar logger** para debug de problemas

---

**Versão:** 1.0
**Data:** Janeiro 2025
**Status:** Pronto para execução
**Tipo:** Implementação de Funcionalidades
**Prioridade:** Alta