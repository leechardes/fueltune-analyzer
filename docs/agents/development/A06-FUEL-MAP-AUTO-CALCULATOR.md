# A06 - FUEL MAP AUTO CALCULATOR

## 📋 Objetivo
Implementar um calculador automático de valores para mapas de combustível 2D, usando informações do veículo (motor, bicos, potência) para gerar valores iniciais aproximados que sirvam como ponto de partida para ajuste fino.

## 🎯 Tarefas

### 1. Análise e Preparação
- [ ] Ler arquivo fuel_maps_2d.py atual
- [ ] Identificar estrutura de dados dos mapas 2D
- [ ] Verificar integração com dados do veículo
- [ ] Confirmar padrões em STREAMLIT-DEVELOPMENT-STANDARDS.md

### 2. Criar Funções de Cálculo
- [ ] Implementar `calculate_base_injection_time()`:
  - Entrada: MAP, cilindrada, cilindros, vazão_bico, AFR_alvo
  - Saída: Tempo de injeção em ms
- [ ] Implementar `calculate_ve_from_map()`:
  - Calcular eficiência volumétrica baseada em MAP
- [ ] Implementar `get_afr_target()`:
  - Retornar AFR alvo baseado em MAP e estratégia
- [ ] Implementar `apply_boost_correction()`:
  - Aplicar correção para pressão de turbo
- [ ] Implementar `apply_fuel_correction()`:
  - Ajustar para tipo de combustível

### 3. Estratégias de Cálculo
- [ ] Definir três estratégias:
  - **Conservadora**: AFR mais rico, margens maiores
  - **Balanceada**: Valores típicos de fábrica
  - **Agressiva**: AFR mais pobre, eficiência máxima
- [ ] Criar presets de AFR para cada estratégia:
  ```python
  STRATEGY_PRESETS = {
      'conservative': {
          'idle': 13.5,
          'cruise': 14.0,
          'wot': 11.5
      },
      'balanced': {
          'idle': 14.2,
          'cruise': 14.7,
          'wot': 12.5
      },
      'aggressive': {
          'idle': 14.7,
          'cruise': 15.5,
          'wot': 13.0
      }
  }
  ```

### 4. Interface do Calculador
- [ ] Adicionar botão "Calcular Valores Automáticos" na página fuel_maps_2d
- [ ] Criar modal/dialog com opções:
  - Seleção de estratégia (dropdown)
  - AFR alvo para diferentes faixas (editável)
  - Checkbox para considerar boost
  - Fator de segurança (0.8 - 1.2)
- [ ] Implementar preview dos valores antes de aplicar
- [ ] Botão "Aplicar Cálculo" para preencher tabela
- [ ] Manter opção de edição manual após cálculo

### 5. Fórmulas de Cálculo

#### Tempo Base de Injeção
```python
def calculate_base_injection_time(map_kpa, engine_displacement, cylinders, injector_flow_lbs_hr, afr_target):
    # Converter MAP para eficiência volumétrica (VE)
    ve = map_kpa / 100.0  # Simplificado, pode ser refinado
    
    # Volume de ar por ciclo (L)
    air_per_cycle = (engine_displacement * ve) / (cylinders * 2)
    
    # Densidade do ar (g/L) - aproximado ao nível do mar
    air_density = 1.2  
    
    # Massa de ar por ciclo (g)
    air_mass = air_per_cycle * air_density
    
    # Massa de combustível necessária (g)
    fuel_mass = air_mass / afr_target
    
    # Converter vazão do bico de lbs/hr para g/ms
    # 1 lb = 453.592g, 1 hr = 3600000 ms
    injector_flow_g_ms = (injector_flow_lbs_hr * 453.592) / 3600000
    
    # Tempo de injeção (ms)
    injection_time = fuel_mass / injector_flow_g_ms
    
    return injection_time
```

#### Correção para Turbo
```python
def apply_boost_correction(base_time, map_kpa, boost_pressure_bar):
    if map_kpa <= 100:  # Sem boost
        return base_time
    
    # Fator de correção baseado na pressão de boost
    boost_factor = 1 + (boost_pressure_bar * (map_kpa - 100) / 100)
    return base_time * boost_factor
```

### 6. Integração com Dados do Veículo
- [ ] Buscar do session_state:
  - Cilindrada do motor
  - Número de cilindros
  - Vazão total dos bicos
  - Tipo de combustível
  - Pressão de boost (se turbo)
  - BSFC factor
- [ ] Validar se todos os dados necessários estão disponíveis
- [ ] Mostrar aviso se dados estiverem incompletos

### 7. Aplicação dos Valores
- [ ] Calcular valores para cada posição ativa do mapa
- [ ] Respeitar pontos desabilitados (manter vazios)
- [ ] Aplicar suavização entre pontos adjacentes
- [ ] Permitir undo/reset para valores originais
- [ ] Salvar histórico de cálculos

### 8. Validações e Limites
- [ ] Verificar limites do mapa (min_value, max_value)
- [ ] Alertar se valores calculados excedem capacidade dos bicos
- [ ] Validar duty cycle máximo (geralmente 85%)
- [ ] Mostrar margem de segurança para cada ponto

## 🔧 Comandos
```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Testar aplicação
make run

# Verificar alterações
git status
git diff src/ui/pages/fuel_maps_2d.py
```

## 📝 Exemplo de Interface

```
┌──────────────────────────────────────────────┐
│     🔧 Calcular Valores Automáticos          │
├──────────────────────────────────────────────┤
│                                              │
│ Estratégia: [Balanceada         ▼]          │
│                                              │
│ AFR Alvo:                                    │
│   Idle (20-40 kPa):    [14.2]              │
│   Cruzeiro (40-70):    [14.7]              │
│   Carga Alta (70-100): [13.0]              │
│   Boost (>100):        [12.0]              │
│                                              │
│ ☑ Considerar Boost                          │
│ ☑ Aplicar BSFC Factor                       │
│                                              │
│ Fator de Segurança: [1.0] (0.8-1.2)        │
│                                              │
│ ╔════════════════════════════════╗          │
│ ║  Preview de Valores (ms)       ║          │
│ ║  20 kPa: 2.3                   ║          │
│ ║  40 kPa: 4.1                   ║          │
│ ║  60 kPa: 6.2                   ║          │
│ ║  80 kPa: 8.5                   ║          │
│ ║  100 kPa: 10.2                 ║          │
│ ╚════════════════════════════════╝          │
│                                              │
│ [Cancelar]        [Aplicar Cálculo]         │
└──────────────────────────────────────────────┘
```

## ✅ Checklist de Validação
- [ ] Interface 100% em português
- [ ] Sem emojis no código (apenas interface)
- [ ] Padrão STREAMLIT-DEVELOPMENT-STANDARDS aplicado
- [ ] Cálculos matematicamente corretos
- [ ] Validações de segurança implementadas
- [ ] Preview antes de aplicar
- [ ] Possibilidade de ajuste manual após cálculo
- [ ] Integração com dados do veículo
- [ ] Mensagens de erro/sucesso claras

## 📊 Resultado Esperado
Sistema que permite ao usuário:
1. Gerar rapidamente um mapa base funcional
2. Escolher entre diferentes estratégias de tune
3. Visualizar preview antes de aplicar
4. Manter controle total com edição manual
5. Ter um ponto de partida seguro e calculado

## 🚀 Benefícios
- **Economia de tempo**: Não precisa preencher célula por célula
- **Segurança**: Valores calculados respeitam limites físicos
- **Educacional**: Usuário aprende relações entre parâmetros
- **Flexibilidade**: Três estratégias + ajuste manual
- **Confiabilidade**: Baseado em dados reais do veículo

---
**Agente**: A06-FUEL-MAP-AUTO-CALCULATOR
**Versão**: 1.0
**Data**: Janeiro 2025