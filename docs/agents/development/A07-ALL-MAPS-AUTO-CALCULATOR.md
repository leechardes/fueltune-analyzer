# A07 - ALL MAPS AUTO CALCULATOR

## 📋 Objetivo
Expandir o calculador automático de mapas 2D para suportar todos os tipos de mapas (não apenas o principal), implementando cálculos específicos baseados na unidade de medida e tipo de correção/compensação.

## 🎯 Tarefas

### 1. Análise e Preparação
- [x] Analisar todos os tipos de mapas em map_types_2d.json
- [x] Identificar unidades de medida (ms vs %)
- [x] Mapear comportamentos específicos de cada tipo
- [ ] Verificar padrões em STREAMLIT-DEVELOPMENT-STANDARDS.md

### 2. Implementar Cálculos Específicos

#### 2.1 Correção por TPS (%)
- [ ] Implementar `calculate_tps_correction()`:
  ```python
  def calculate_tps_correction(tps_values: List[float], strategy: str) -> List[float]:
      # 0-20%: economia (-5% a 0%)
      # 20-70%: neutro (0%)
      # 70-100%: potência (0% a +15%)
      # WOT: máximo (+15% a +20%)
  ```

#### 2.2 Correção por Temperatura Motor (%)
- [ ] Implementar `calculate_temp_correction()`:
  ```python
  def calculate_temp_correction(temp_values: List[float], 
                               engine_displacement: float) -> List[float]:
      # < 40°C: enriquecimento (+30% a +10%)
      # 80-90°C: sem correção (0%)
      # > 100°C: resfriamento (+5% a +10%)
  ```

#### 2.3 Correção por Temperatura Ar (%)
- [ ] Implementar `calculate_air_temp_correction()`:
  ```python
  def calculate_air_temp_correction(air_temp_values: List[float]) -> List[float]:
      # Baseado na densidade do ar (lei dos gases)
      # < 20°C: redução (-5% a 0%)
      # 20-30°C: sem correção (0%)
      # > 40°C: enriquecimento (0% a +15%)
  ```

#### 2.4 Correção por Voltagem (ms)
- [ ] Implementar `calculate_voltage_correction()`:
  ```python
  def calculate_voltage_correction(voltage_values: List[float], 
                                  injector_type: str) -> List[float]:
      # Dead time dos bicos
      # < 12V: +2ms a +5ms
      # 13-14V: 0.8-1.2ms
      # > 14V: -0.5ms a 0ms
  ```

#### 2.5 Compensação por RPM (%)
- [ ] Implementar `calculate_rpm_compensation()`:
  ```python
  def calculate_rpm_compensation(rpm_values: List[float], 
                                has_turbo: bool,
                                redline: int) -> List[float]:
      # < 2000: estabilidade (0% a +5%)
      # 2000-4500: sem correção (0%)
      # > 4500: enriquecimento (0% a +20%)
      # Limitador: máximo (+15% a +25%)
  ```

### 3. Refatorar Interface do Calculador
- [ ] Detectar tipo de mapa selecionado
- [ ] Mostrar controles específicos para cada tipo:
  - TPS: Estratégia de aceleração
  - Temperatura: Tipo de refrigeração
  - Voltagem: Tipo de bico (alta/baixa impedância)
  - RPM: Redline e tipo de motor
- [ ] Adaptar preview para unidade correta (% ou ms)

### 4. Implementar Função Mestre
- [ ] Criar `calculate_map_values_universal()`:
  ```python
  def calculate_map_values_universal(
      map_type: str,
      axis_values: List[float],
      vehicle_data: Dict[str, Any],
      strategy: str = 'balanced'
  ) -> List[float]:
      """Calcula valores para qualquer tipo de mapa."""
      
      map_info = MAP_TYPES_2D.get(map_type)
      unit = map_info.get('unit', '%')
      axis_type = map_info.get('axis_type')
      
      if map_type == "main_fuel_2d_map":
          return calculate_main_fuel_map(...)
      elif map_type == "tps_correction_2d":
          return calculate_tps_correction(...)
      elif map_type == "temp_correction_2d":
          return calculate_temp_correction(...)
      # ... etc
  ```

### 5. Integração com Dados do Veículo
- [ ] Adicionar campos necessários ao veículo:
  - `injector_impedance`: "high" ou "low"
  - `cooling_type`: "air" ou "water"
  - `redline_rpm`: limite de rotação
  - `idle_rpm`: rotação de marcha lenta
- [ ] Usar dados reais do veículo nos cálculos
- [ ] Aplicar fatores de correção baseados no motor

### 6. Validações e Limites
- [ ] Respeitar min_value e max_value de cada mapa
- [ ] Aplicar suavização entre pontos
- [ ] Validar coerência dos valores calculados
- [ ] Mostrar avisos para valores extremos

### 7. Interface Aprimorada
- [ ] Adicionar explicação do que cada mapa faz
- [ ] Mostrar impacto visual das correções
- [ ] Permitir ajuste fino após cálculo
- [ ] Opção de resetar para valores padrão

## 🔧 Comandos
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Testar aplicação
make run

# Verificar alterações
git status
git diff src/ui/pages/fuel_maps_2d.py
```

## 📝 Exemplo de Interface por Tipo

### Para Correção TPS:
```
Estratégia de Aceleração:
○ Econômica (menos resposta)
● Balanceada (padrão)
○ Esportiva (mais resposta)

Sensibilidade: [====|====] 50%
```

### Para Correção Temperatura:
```
Tipo de Motor:
● Refrigerado a água
○ Refrigerado a ar

Clima predominante:
○ Frio ● Temperado ○ Quente
```

### Para Correção Voltagem:
```
Tipo de Bico:
● Alta impedância (12-16Ω)
○ Baixa impedância (2-3Ω)

Voltagem do alternador: [14.2] V
```

## ✅ Checklist de Validação
- [ ] Interface 100% em português
- [ ] Sem emojis no código (apenas interface)
- [ ] Padrão STREAMLIT-DEVELOPMENT-STANDARDS aplicado
- [ ] Cálculos específicos para cada tipo de mapa
- [ ] Unidades corretas (% ou ms)
- [ ] Integração com dados do veículo
- [ ] Preview antes de aplicar
- [ ] Validações de segurança
- [ ] Documentação inline clara

## 📊 Resultado Esperado
Sistema que permite ao usuário:
1. Calcular automaticamente QUALQUER tipo de mapa 2D
2. Ver cálculos específicos para cada correção/compensação
3. Entender o impacto de cada ajuste
4. Ter valores iniciais tecnicamente corretos
5. Personalizar baseado no uso do veículo

## 🚀 Benefícios
- **Completude**: Todos os mapas podem ser calculados
- **Precisão**: Cálculos baseados em física e engenharia
- **Educacional**: Usuário aprende função de cada mapa
- **Personalização**: Ajustes para cada tipo de uso
- **Segurança**: Valores sempre dentro de limites seguros

## 📚 Referências Técnicas

### Fórmulas de Correção

#### Densidade do Ar (para correção por temperatura):
```python
# Densidade relativa = P / (R * T)
# Onde P = pressão, R = constante dos gases, T = temperatura absoluta
density_ratio = (273.15 + 20) / (273.15 + air_temp)
correction = (density_ratio - 1.0) * 100  # Em percentual
```

#### Dead Time dos Bicos (correção voltagem):
```python
# Fórmula típica para bicos de alta impedância
dead_time_ms = 1.0 + (14.0 - voltage) * 0.15
```

#### Compensação RPM (perdas de enchimento):
```python
# VE cai em alta rotação
ve_loss = max(0, (rpm - 5000) / 1000 * 0.05)  # 5% perda por 1000rpm
compensation = ve_loss * 100  # Em percentual
```

---
**Agente**: A07-ALL-MAPS-AUTO-CALCULATOR
**Versão**: 1.0
**Data**: Janeiro 2025
**Dependências**: 
- STREAMLIT-DEVELOPMENT-STANDARDS.md
- A06-FUEL-MAP-AUTO-CALCULATOR.md (base)