# A03 - FUEL MAPS 3D IMPLEMENT REFACTOR

## 📋 Objetivo
Implementar a refatoração completa do fuel_maps_3d.py baseado na análise do A02, separando em módulos organizados e corrigindo todos os problemas identificados.

## 🎯 Missão
Transformar um arquivo caótico de 3,152 linhas em uma arquitetura modular, testável e maintível, resolvendo os problemas de dados defaults e bugs identificados.

## 📦 Estrutura a Criar

```
src/
├── core/
│   └── fuel_maps/
│       ├── __init__.py
│       ├── models.py        # Classes e tipos (87 linhas)
│       ├── defaults.py      # Configurações e defaults (198 linhas)
│       ├── calculations.py  # Lógica de cálculo (474 linhas)
│       ├── persistence.py   # Save/Load (287 linhas)
│       ├── validation.py    # Validações (95 linhas)
│       └── ui_components.py # Componentes reutilizáveis (156 linhas)
└── ui/
    └── pages/
        └── fuel_maps_3d.py # APENAS UI principal (~400 linhas)
```

## 🔧 Ordem de Implementação

### FASE 1: Criar Estrutura Base
1. Criar diretório `src/core/fuel_maps/`
2. Criar `__init__.py` com exports
3. Criar arquivos vazios dos módulos

### FASE 2: Models e Types
```python
# models.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

@dataclass
class MapConfig:
    name: str
    grid_size: int
    x_axis_type: str
    y_axis_type: str
    unit: str
    min_value: float
    max_value: float
    description: str
    default_rpm_values: List[float]
    default_rpm_enabled: List[bool]
    default_map_values: List[float]
    default_map_enabled: List[bool]

@dataclass
class Map3DData:
    vehicle_id: str
    map_type: str
    bank: str
    rpm_axis: List[float]
    map_axis: List[float]
    rpm_enabled: List[bool]
    map_enabled: List[bool]
    values_matrix: np.ndarray
    timestamp: str
    version: str = "1.0"
```

### FASE 3: Defaults Module
```python
# defaults.py
"""Gerenciamento de configurações e valores padrão."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from .models import MapConfig

class ConfigManager:
    """Gerencia configurações centralizadas."""
    
    def __init__(self, config_path: str = "config/map_types_3d.json"):
        self.config_path = Path(config_path)
        self._config_cache = None
        
    def load_config(self) -> Dict[str, MapConfig]:
        """Carrega configuração uma única vez."""
        if self._config_cache is None:
            self._config_cache = self._load_from_file()
        return self._config_cache
    
    def get_map_config(self, map_type: str) -> Optional[MapConfig]:
        """Obtém configuração específica do mapa."""
        configs = self.load_config()
        return configs.get(map_type)
    
    def get_default_values(self, map_type: str, key: str, grid_size: int):
        """Obtém valores padrão do JSON, não de constantes."""
        # SEMPRE do JSON, nunca hardcoded
        pass
```

### FASE 4: Calculations Module
Mover todas as funções de cálculo:
- `calculate_fuel_3d_matrix()`
- `calculate_lambda_3d_matrix()` 
- `calculate_ignition_3d_matrix()`
- `calculate_afr_3d_matrix()`
- `calculate_3d_map_values_universal()`
- Funções auxiliares de cálculo

### FASE 5: Persistence Module
```python
# persistence.py
"""Gerenciamento de persistência de dados."""

from pathlib import Path
import json
from typing import Optional
from .models import Map3DData

class PersistenceManager:
    """Gerencia save/load de mapas."""
    
    def __init__(self, data_dir: str = "data/fuel_maps"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def save_map(self, data: Map3DData) -> bool:
        """Salva mapa com validação."""
        pass
    
    def load_map(self, vehicle_id: str, map_type: str, bank: str) -> Optional[Map3DData]:
        """Carrega mapa se existir."""
        pass
    
    def ensure_defaults_exist(self, vehicle_id: str) -> None:
        """Garante que mapas padrão existam."""
        pass
```

### FASE 6: Validation Module
```python
# validation.py
"""Validações de dados de mapas."""

import numpy as np
from typing import Tuple, List
from .models import Map3DData, MapConfig

class MapValidator:
    """Valida dados de mapas 3D."""
    
    @staticmethod
    def validate_matrix(matrix: np.ndarray, config: MapConfig) -> Tuple[bool, str]:
        """Valida valores da matriz."""
        pass
    
    @staticmethod
    def validate_axes(rpm_axis: List[float], map_axis: List[float]) -> Tuple[bool, str]:
        """Valida eixos."""
        pass
```

### FASE 7: UI Components
```python
# ui_components.py
"""Componentes UI reutilizáveis."""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any

def render_3d_surface_plot(data: Dict[str, Any]) -> None:
    """Renderiza gráfico 3D surface."""
    pass

def render_matrix_editor(data: Dict[str, Any]) -> pd.DataFrame:
    """Renderiza editor de matriz."""
    pass

def render_axis_config(axis_type: str, values: List[float]) -> List[float]:
    """Renderiza configurador de eixo."""
    pass
```

### FASE 8: Refatorar UI Principal
```python
# fuel_maps_3d.py (NOVO - ~400 linhas)
"""Interface principal de mapas 3D - APENAS UI."""

import streamlit as st
from src.core.fuel_maps import (
    ConfigManager,
    PersistenceManager,
    MapValidator,
    Calculator,
    render_3d_surface_plot,
    render_matrix_editor
)

# Configuração da página
st.title("Mapas de Injeção 3D")

# Instanciar managers
config_manager = ConfigManager()
persistence_manager = PersistenceManager()
validator = MapValidator()
calculator = Calculator()

# UI simples e limpa
def main():
    # Seleção de mapa
    map_type = st.selectbox("Tipo de Mapa", options=config_manager.get_map_types())
    
    # Carregar dados (lógica no manager)
    data = persistence_manager.load_or_create_default(vehicle_id, map_type)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Editor", "Visualização 3D", "Configurações"])
    
    with tab1:
        # Editor de matriz
        edited_data = render_matrix_editor(data)
        
        if st.button("Salvar"):
            if validator.validate(edited_data):
                persistence_manager.save(edited_data)
    
    with tab2:
        # Visualização 3D
        render_3d_surface_plot(data)
    
    with tab3:
        # Configurações
        render_axis_config(data)
```

## 🔴 Bugs a Corrigir Durante Refatoração

1. **Linha 944**: Variável `selected_map_type` não definida
2. **Hierarquia de dados**: Estabelecer ordem clara de prioridade
3. **Session state**: Centralizar gerenciamento
4. **Grid size**: Usar sempre do config, não hardcoded

## ✅ Checklist de Validação

### Por Módulo:
- [ ] Módulo criado e importável
- [ ] Funções movidas e testadas
- [ ] Sem dependências circulares
- [ ] Documentação básica
- [ ] Tipos bem definidos

### Geral:
- [ ] Arquivo principal < 500 linhas
- [ ] Todos os cálculos em calculations.py
- [ ] Toda persistência em persistence.py
- [ ] Configurações centralizadas
- [ ] Session state gerenciado
- [ ] Bugs corrigidos
- [ ] Funcionalidades preservadas

## 🎯 Resultado Esperado

1. **Código organizado**: Cada módulo com responsabilidade única
2. **Bugs resolvidos**: Especialmente o problema dos defaults
3. **Manutenível**: Fácil de entender e modificar
4. **Testável**: Lógica separada da UI
5. **Performance**: Sem recarregamentos desnecessários

## ⚠️ Cuidados na Implementação

1. **Testar cada fase**: Não quebrar funcionalidades
2. **Backup primeiro**: Copiar arquivo original
3. **Incremental**: Uma função por vez
4. **Validar imports**: Evitar dependências circulares
5. **Session state**: Migrar com cuidado

## 🚀 Comando de Execução

```bash
# Este agente VAI modificar código
# Fazer backup primeiro!

1. Criar estrutura de diretórios
2. Criar módulos base
3. Mover funções por categoria
4. Refatorar UI principal
5. Testar tudo
6. Documentar mudanças
```

---

**Versão:** 1.0
**Data:** Janeiro 2025
**Status:** Pronto para execução
**Tipo:** Implementação
**Risco:** Alto - Fazer backup antes!