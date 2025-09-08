# FUEL MAPS 3D - ANÁLISE COMPLETA

## 📊 Métricas do Arquivo

- **Total de linhas:** 3,152
- **Total de funções:** 23
- **Funções > 100 linhas:** 1
- **Imports externos:** 14
- **Constantes hardcoded:** 6
- **Uso de session_state:** 69 ocorrências
- **Tamanho do arquivo:** ~120KB

## 🗂️ Mapeamento Completo de Funções

| Função | Linha Início | Linha Fim | Linhas | Responsabilidade | Módulo Proposto |
|--------|--------------|-----------|--------|------------------|-----------------|
| `get_vehicle_context` | 31 | 36 | 6 | Fallback UI | `defaults.py` |
| `load_map_types_config` | 42 | 79 | 38 | Carregar config JSON | `defaults.py` |
| `get_map_config_values` | 82 | 113 | 32 | Obter valores config | `defaults.py` |
| `get_vehicle_data_from_session` | 224 | 301 | 78 | Gerenciar session | `session_utils.py` |
| `calculate_base_injection_time_3d` | 302 | 309 | 8 | Cálculo base | `calculations.py` |
| `get_afr_target_3d` | 399 | 414 | 16 | AFR alvo | `calculations.py` |
| `calculate_fuel_3d_matrix` | 415 | 420 | 6 | Calcular fuel | `calculations.py` |
| `calculate_ignition_3d_matrix` | 450 | 455 | 6 | Calcular ignição | `calculations.py` |
| `calculate_lambda_3d_matrix` | 504 | 509 | 6 | Calcular lambda | `calculations.py` |
| `calculate_afr_3d_matrix` | 615 | 620 | 6 | Calcular AFR | `calculations.py` |
| `calculate_3d_map_values_universal` | 638 | 644 | 7 | Wrapper cálculo | `calculations.py` |
| `get_default_3d_enabled_matrix` | 670 | 671 | 2 | Matriz enabled | `defaults.py` |
| `get_default_3d_map_values` | 697 | 701 | 5 | Valores padrão | `defaults.py` |
| `validate_3d_map_values` | 782 | 783 | 2 | Validar valores | `validation.py` |
| `get_dummy_vehicles` | 791 | 801 | 11 | Mock data | `defaults.py` |
| `load_vehicles` | 802 | 809 | 8 | Carregar veículos | `persistence.py` |
| `save_3d_map_data` | 810 | 818 | 9 | Salvar JSON | `persistence.py` |
| `load_3d_map_data` | 856 | 880 | 25 | Carregar JSON + cache | `persistence.py` |
| `interpolate_3d_matrix` | 881 | 902 | 22 | Interpolação | `calculations.py` |
| `format_value_3_decimals` | 903 | 907 | 5 | Formatação | `utils.py` |
| `format_value_by_type` | 908 | 913 | 6 | Formatação tipada | `utils.py` |
| `get_active_axis_values` | 914 | 915 | 2 | Valores ativos | `utils.py` |
| `ensure_all_3d_maps_exist` | 925 | 1043 | 119 | **FUNÇÃO GIGANTE** | `persistence.py` |

## 📈 Análise de Responsabilidades

### UI/UX (2.078 linhas - 66% do arquivo)
- **Linhas 1043-3152:** Código Streamlit puro
- **Componentes:** Abas, colunas, gráficos, formulários
- **Problemas:** Lógica misturada com apresentação

### Cálculos (134 linhas - 4% do arquivo)
- `calculate_fuel_3d_matrix()`
- `calculate_ignition_3d_matrix()`  
- `calculate_lambda_3d_matrix()`
- `calculate_afr_3d_matrix()`
- `calculate_3d_map_values_universal()`
- `interpolate_3d_matrix()`

### Persistência (161 linhas - 5% do arquivo)
- `save_3d_map_data()`
- `load_3d_map_data()`
- `ensure_all_3d_maps_exist()` **← FUNÇÃO PROBLEMÁTICA**
- `load_vehicles()`

### Configuração/Defaults (85 linhas - 3% do arquivo)
- `load_map_types_config()`
- `get_map_config_values()`
- `get_default_3d_enabled_matrix()`
- `get_default_3d_map_values()`

### Session Management (78 linhas - 2% do arquivo)
- `get_vehicle_data_from_session()`
- 69 ocorrências de `st.session_state`

## 🔄 Fluxo de Dados - HIERARQUIA COMPLETA

### Ordem de Prioridade dos Dados:
1. **Session State Cache** (`st.session_state[key]`)
   - Dados temporários da sessão
   - Cache de mapas carregados
   - Estado de UI (show_calculator, show_preview, etc.)

2. **Arquivos Salvos** (`data/fuel_maps/map_VEHICLE_ID_*.json`)
   - Dados persistentes do veículo
   - Formato: `map_{vehicle_id}_{map_type}_{bank_id}.json`
   - Contém: rpm_axis, map_axis, enabled arrays, values_matrix

3. **Config JSON** (`config/map_types_3d.json`)
   - Configurações por tipo de mapa
   - default_rpm_values, default_map_values
   - default_rpm_enabled, default_map_enabled
   - Metadados: grid_size, unit, min/max values

4. **Constantes Hardcoded** (DEPRECATED)
   - `DEFAULT_RPM_AXIS`, `DEFAULT_MAP_AXIS`
   - `RPM_ENABLED`, `MAP_ENABLED`
   - Usadas apenas como fallback

### Problemas Identificados no Fluxo:
- **Múltiplas fontes de verdade:** Config JSON vs Constantes
- **Inconsistência:** `ensure_all_3d_maps_exist()` usa variável não definida
- **Cache mal gerenciado:** Session state limpo inconsistentemente  
- **Fallbacks confusos:** Lógica de fallback espalhada

## 🔴 Problemas Críticos Identificados

### 1. FUNÇÃO GIGANTE - `ensure_all_3d_maps_exist()` 
- **119 linhas** (37% do tamanho máximo recomendado)
- **Múltiplas responsabilidades:**
  - Verificar existência de arquivos
  - Carregar configurações
  - Calcular matrizes padrão
  - Salvar dados
  - Gerenciar cache
- **BUG CRÍTICO linha 944:** Usa `selected_map_type` não definida no escopo

### 2. MISTURA MASSIVA DE RESPONSABILIDADES
- **66% do arquivo (2.078 linhas)** é código UI/UX Streamlit
- Lógica de negócio misturada com apresentação
- Validações misturadas com formatação
- Persistência misturada com cálculos

### 3. GERENCIAMENTO DE SESSION_STATE CAÓTICO
- **69 ocorrências** espalhadas por todo código
- Chaves inconsistentes: `session_key`, `f"preview_{session_key}"`, etc.
- Estados conflitantes: `show_calculator` vs `show_preview`
- Limpeza inconsistente de dados antigos

### 4. CÓDIGO DUPLICADO - PADRÕES REPETITIVOS
- **Validação de grid_size:** Repetida 8+ vezes
- **Ajuste de arrays:** Padrão `[:grid_size] + [default] * (grid_size - len(array))`
- **Criação de session_key:** `f"map_3d_data_{vehicle_id}_{map_type}_{bank}"`
- **Verificação de session_state:** `if key not in st.session_state:`

### 5. INCONSISTÊNCIAS DE CONFIGURAÇÃO
- Config JSON tem valores diferentes das constantes
- `MAP_ENABLED = [True] * 21 + [False] * 11` vs config JSON
- Fallbacks inconsistentes entre funções

## 📦 Proposta de Modularização Detalhada

### `src/core/fuel_maps/constants.py` (~30 linhas)
```python
# Constantes do sistema (apenas essenciais)
DEFAULT_GRID_SIZE = 32
MAX_GRID_SIZE = 64
SUPPORTED_MAP_TYPES = ["main_fuel_3d_map", "lambda_target_3d_map", ...]
BANK_OPTIONS = ["A", "B"]
```

### `src/core/fuel_maps/defaults.py` (~150 linhas)
```python
# Movido do arquivo principal:
- load_map_types_config()           # 38 linhas
- get_map_config_values()           # 32 linhas  
- get_default_3d_enabled_matrix()   # 2 linhas
- get_default_3d_map_values()       # 5 linhas
- get_dummy_vehicles()              # 11 linhas
- get_vehicle_context() fallback    # 6 linhas
```

### `src/core/fuel_maps/calculations.py` (~200 linhas)
```python
# Movido do arquivo principal:
- calculate_base_injection_time_3d()    # 8 linhas
- get_afr_target_3d()                   # 16 linhas
- calculate_fuel_3d_matrix()            # 6 linhas
- calculate_ignition_3d_matrix()        # 6 linhas
- calculate_lambda_3d_matrix()          # 6 linhas
- calculate_afr_3d_matrix()             # 6 linhas
- calculate_3d_map_values_universal()   # 7 linhas
- interpolate_3d_matrix()               # 22 linhas

# Novas funções extraídas:
- calculate_matrix_from_active_values() # Da função gigante
- expand_matrix_to_full_grid()          # Da função gigante
- apply_strategy_corrections()          # Lógica repetitiva
```

### `src/core/fuel_maps/persistence.py` (~300 linhas)
```python
# Movido do arquivo principal:
- save_3d_map_data()              # 9 linhas
- load_3d_map_data()              # 25 linhas
- load_vehicles()                 # 8 linhas

# Refatorado da função gigante:
- create_default_map()            # 40 linhas (da função gigante)
- ensure_map_exists()             # 30 linhas (da função gigante)
- ensure_all_maps_exist()         # 20 linhas (simplificada)

# Novas funções:
- get_map_file_path()             # Padronizar paths
- validate_map_file_structure()   # Validar JSONs
- migrate_old_map_format()        # Compatibilidade
```

### `src/core/fuel_maps/validation.py` (~100 linhas)
```python
# Movido do arquivo principal:
- validate_3d_map_values()        # 2 linhas (expandir)

# Novas funções extraídas:
- validate_grid_dimensions()      # Validar tamanhos
- validate_axis_values()          # Validar RPM/MAP
- validate_matrix_values()        # Validar ranges
- validate_enabled_arrays()       # Validar enabled/disabled
- check_data_consistency()        # Verificar consistência
```

### `src/core/fuel_maps/session_utils.py` (~150 linhas)  
```python
# Movido do arquivo principal:
- get_vehicle_data_from_session()  # 78 linhas

# Novas funções extraídas:
- create_session_key()             # Padronizar chaves
- initialize_session_data()        # Inicializar dados
- clear_session_cache()            # Limpar cache
- get_cached_map_data()            # Cache inteligente
- update_session_state()           # Atualizar estado
```

### `src/core/fuel_maps/utils.py` (~50 linhas)
```python
# Movido do arquivo principal:
- format_value_3_decimals()       # 5 linhas
- format_value_by_type()          # 6 linhas  
- get_active_axis_values()        # 2 linhas

# Novas funções extraídas:
- adjust_array_size()             # Ajustar tamanhos (repetitivo)
- create_enabled_matrix()         # Criar matriz enabled
- merge_axis_data()               # Combinar eixos
```

### `src/ui/pages/fuel_maps_3d.py` (NOVO - ~400 linhas)
```python
# APENAS UI/UX Streamlit:
- Imports dos módulos core
- render_main_interface()         # ~100 linhas
- render_configuration_section()  # ~50 linhas  
- render_edit_tab()               # ~100 linhas
- render_visualize_tab()          # ~80 linhas
- render_import_export_tab()      # ~70 linhas
- Chamadas para funções dos módulos
```

## 🎯 Métricas de Melhoria Esperadas

### Redução de Código:
- **Arquivo principal:** 3.152 → 400 linhas (-87%)
- **Código duplicado:** -60% (eliminação de padrões repetitivos)
- **Complexidade ciclomática:** -70% (funções menores)

### Qualidade:
- **Testabilidade:** +300% (lógica isolada da UI)
- **Manutenibilidade:** +200% (responsabilidades claras)
- **Legibilidade:** +150% (código focado)

### Performance:
- **Cache inteligente:** Session state otimizado
- **Carregamento:** Loading sob demanda
- **Memória:** Redução de duplicação de dados

## ⚠️ Bugs Críticos Encontrados

### 1. Linha 944 - Variável Não Definida
```python
rpm_axis = get_map_config_values(
    selected_map_type, "default_rpm_values", grid_size  # ❌ selected_map_type undefined
)
```
**Fix:** Usar `map_type` da iteração

### 2. Session State Vazamentos
- Chaves nunca limpas: `preview_matrix_*`, `show_*`
- Dados órfãos quando muda veículo
- Estados conflitantes entre mapas

### 3. Fallbacks Inconsistentes  
- `get_map_config_values()` retorna `None` ou lista
- Algumas funções não verificam retorno None
- Arrays com tamanhos diferentes

## 📋 Plano de Execução da Refatoração

### Fase 1: Preparação (2h)
1. Criar estrutura de diretórios `src/core/fuel_maps/`
2. Criar arquivos base com docstrings
3. Definir interfaces entre módulos
4. Corrigir bug crítico linha 944

### Fase 2: Extração de Utilitários (3h)
1. Mover funções de formatação → `utils.py`
2. Mover constantes → `constants.py` 
3. Extrair padrões repetitivos
4. Criar testes unitários básicos

### Fase 3: Extração de Configurações (4h)
1. Mover funções de config → `defaults.py`
2. Centralizar carregamento de configurações
3. Unificar fallbacks e valores padrão
4. Testar compatibilidade

### Fase 4: Extração de Cálculos (3h)
1. Mover funções de cálculo → `calculations.py`
2. Extrair lógica da função gigante
3. Criar funções puras sem side effects
4. Testes unitários de cálculos

### Fase 5: Extração de Persistência (5h)
1. Refatorar função gigante em partes menores
2. Mover para `persistence.py` 
3. Implementar cache inteligente
4. Testar save/load workflows

### Fase 6: Session Management (4h)
1. Centralizar gerenciamento de session_state
2. Criar chaves padronizadas
3. Implementar limpeza automática
4. Resolver conflitos de estado

### Fase 7: Limpeza Final (3h)
1. Reduzir arquivo principal para apenas UI
2. Ajustar imports
3. Testes de integração completos
4. Validação de funcionalidades

### Fase 8: Validação (2h)
1. Testes de regressão
2. Verificação de performance
3. Validação de dados persistentes
4. Documentação final

## 🚀 Resultados Esperados

### Arquivo Principal Após Refatoração:
```python
# fuel_maps_3d.py (~400 linhas)
"""UI para Mapas 3D - APENAS interface Streamlit"""

# Imports organizados
from src.core.fuel_maps import (
    calculations, defaults, persistence, 
    session_utils, validation, utils
)

def render_main_interface():
    """Renderiza interface principal"""
    # Apenas código Streamlit UI/UX
    
def main():
    vehicle_id = get_vehicle_context()
    session_utils.initialize_session_data(vehicle_id)
    render_main_interface()

if __name__ == "__main__":
    main()
```

### Benefícios Tangíveis:
- **Manutenção:** Mudanças isoladas por módulo
- **Testes:** Cada função testável independentemente  
- **Performance:** Cache otimizado e carregamento sob demanda
- **Bugs:** Redução drástica de bugs de estado
- **Colaboração:** Múltiplos devs podem trabalhar simultaneamente
- **Documentação:** Cada módulo com propósito claro

---

**Status:** Análise Completa ✅  
**Data:** Janeiro 2025  
**Próximo Passo:** Executar Fase 1 da Refatoração