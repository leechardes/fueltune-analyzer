# FUEL-MAPS-MODEL-IMPLEMENTATION

## Objetivo
Implementar estrutura completa de banco de dados para sistema de mapas de injeção com suporte a diferentes tamanhos de slots (8, 9, 16, 20, 32) e bancadas A/B, seguindo rigorosamente a especificação FUEL-MAPS-SPECIFICATION.md.

## Contexto
Você é um especialista em modelagem de dados automotivos com foco em sistemas de injeção eletrônica. Deve implementar todos os modelos de dados necessários para suportar o sistema completo de mapas de injeção compatível com FTManager.

## Padrões de Desenvolvimento
Este agente segue os padrões definidos em:
- /srv/projects/shared/docs/agents/development/A04-STREAMLIT-PROFESSIONAL.md

### Princípios Fundamentais:
1. **ZERO emojis** - Usar apenas Material Design Icons
2. **Interface profissional** - Sem decorações infantis  
3. **CSS adaptativo** - Funciona em tema claro e escuro
4. **Português brasileiro** - Todos os textos traduzidos
5. **Ícones consistentes** - Material Icons em todos os componentes
6. **Varredura PROFUNDA** - Não deixar NENHUM emoji escapar
7. **NUNCA usar !important no CSS** - Para permitir adaptação de temas

## Entrada Esperada
- **Diretório**: /home/lee/projects/fueltune-streamlit/
- **Documentação**: docs/FUEL-MAPS-SPECIFICATION.md
- **Modelo existente**: src/data/models.py
- **Migrations**: migrations/ (Alembic)

## Tarefas

### 1. Análise da Estrutura Existente
- Examinar src/data/models.py atual
- Identificar estrutura de Vehicle existente
- Verificar sistema de migrations Alembic
- Documentar campos que precisam ser adicionados

### 2. Atualizar Modelo Vehicle
Adicionar campos para configuração das bancadas A/B conforme especificação:

```python
# Bancada A
bank_a_enabled = Column(Boolean, default=True, comment="Bancada A habilitada")
bank_a_mode = Column(String(20), default='semissequential', comment="Modo: multiponto, semissequencial, sequencial")
bank_a_outputs = Column(JSON, comment="Lista de saídas: [1, 2, 3, 4] etc")
bank_a_injector_flow = Column(Float, comment="Vazão por bico em lb/h")
bank_a_injector_count = Column(Integer, comment="Quantidade de bicos")
bank_a_total_flow = Column(Float, comment="Vazão total calculada")
bank_a_dead_time = Column(Float, comment="Dead time dos injetores em ms")

# Bancada B
bank_b_enabled = Column(Boolean, default=False, comment="Bancada B habilitada")
bank_b_mode = Column(String(20), default='semissequential', comment="Modo: multiponto, semissequencial, sequencial")
bank_b_outputs = Column(JSON, comment="Lista de saídas: [1, 2, 3, 4] etc")
bank_b_injector_flow = Column(Float, comment="Vazão por bico em lb/h")
bank_b_injector_count = Column(Integer, comment="Quantidade de bicos")
bank_b_total_flow = Column(Float, comment="Vazão total calculada")
bank_b_dead_time = Column(Float, comment="Dead time dos injetores em ms")

# Limites operacionais
max_map_pressure = Column(Float, default=5.0, comment="Pressão MAP máxima em bar")
min_map_pressure = Column(Float, default=-1.0, comment="Pressão MAP mínima em bar")
```

### 3. Criar Modelos de Mapas Principais

#### 3.1 Tabela Principal de Mapas
```python
class FuelMap(Base):
    __tablename__ = 'fuel_maps'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=False)
    map_type = Column(String(50), nullable=False)  # 'main_fuel_2d_map', 'main_fuel_3d', etc
    bank_id = Column(String(1), nullable=True)     # 'A', 'B' ou NULL para mapas compartilhados
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Dimensões e estrutura
    dimensions = Column(Integer, nullable=False)     # 1 para 2D, 2 para 3D
    x_axis_type = Column(String(50), nullable=False) # 'RPM', 'MAP', 'TEMP', 'TPS', 'VOLTAGE', 'TIME'
    y_axis_type = Column(String(50), nullable=True)  # NULL para 2D, preenchido para 3D
    data_unit = Column(String(20), nullable=False)   # 'ms', '%', 'degrees', 'lambda'
    
    # Slots e configuração
    x_slots_total = Column(Integer, default=32, comment="Total de slots no eixo X")
    x_slots_active = Column(Integer, default=0, comment="Slots ativos no eixo X")
    y_slots_total = Column(Integer, default=32, comment="Total de slots no eixo Y")
    y_slots_active = Column(Integer, default=0, comment="Slots ativos no eixo Y")
    
    # Versionamento
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    modified_by = Column(String(100), comment="Usuário que fez a modificação")
    
    # Relacionamentos
    vehicle = relationship("Vehicle", back_populates="fuel_maps")
    axis_data = relationship("MapAxisData", back_populates="fuel_map", cascade="all, delete-orphan")
    map_2d_data = relationship("MapData2D", back_populates="fuel_map", cascade="all, delete-orphan")
    map_3d_data = relationship("MapData3D", back_populates="fuel_map", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("vehicle_id", "map_type", "bank_id", name="uix_vehicle_map_bank"),
        CheckConstraint("dimensions IN (1, 2)", name="chk_dimensions"),
        CheckConstraint("x_slots_active <= x_slots_total", name="chk_x_slots"),
        CheckConstraint("y_slots_active <= y_slots_total", name="chk_y_slots"),
        Index("idx_vehicle_map_type", "vehicle_id", "map_type"),
        Index("idx_map_active", "is_active"),
    )
```

#### 3.2 Tabela de Dados dos Eixos (Genérica)
```python
class MapAxisData(Base):
    __tablename__ = 'map_axis_data'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id = Column(String(36), ForeignKey("fuel_maps.id"), nullable=False)
    axis_type = Column(String(10), nullable=False)  # 'X' ou 'Y'
    data_type = Column(String(50), nullable=False)  # 'RPM', 'MAP', 'TEMP', etc
    
    # 32 slots para todos os eixos (máximo possível)
    slot_0 = Column(Float)
    slot_1 = Column(Float)
    # ... continuar até slot_31
    slot_31 = Column(Float)
    
    active_slots = Column(Integer, default=0, comment="Número de slots ativos")
    
    # Relacionamentos
    fuel_map = relationship("FuelMap", back_populates="axis_data")
    
    # Índices
    __table_args__ = (
        Index("idx_map_axis", "map_id", "axis_type"),
    )
```

#### 3.3 Tabela de Dados 2D
```python
class MapData2D(Base):
    __tablename__ = 'map_data_2d'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id = Column(String(36), ForeignKey("fuel_maps.id"), nullable=False)
    
    # 32 valores possíveis (correspondem aos slots do eixo X)
    value_0 = Column(Float)
    value_1 = Column(Float)
    # ... continuar até value_31
    value_31 = Column(Float)
    
    # Relacionamentos
    fuel_map = relationship("FuelMap", back_populates="map_2d_data")
    
    # Índices
    __table_args__ = (
        Index("idx_map_2d", "map_id"),
    )
```

#### 3.4 Tabela de Dados 3D
```python
class MapData3D(Base):
    __tablename__ = 'map_data_3d'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id = Column(String(36), ForeignKey("fuel_maps.id"), nullable=False)
    
    # Matriz 32x32 = 1024 células (máximo possível)
    # Nomeação: value_X_Y onde X é linha (eixo X) e Y é coluna (eixo Y)
    value_0_0 = Column(Float)
    value_0_1 = Column(Float)
    # ... continuar até value_31_31 (total de 1024 campos)
    value_31_31 = Column(Float)
    
    # Relacionamentos
    fuel_map = relationship("FuelMap", back_populates="map_3d_data")
    
    # Índices
    __table_args__ = (
        Index("idx_map_3d", "map_id"),
    )
```

### 4. Criar Tabelas Especializadas por Tipo de Eixo

#### 4.1 Eixo RPM (32 slots)
```python
class MapAxisRPM(Base):
    __tablename__ = 'map_axis_rpm'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id = Column(String(36), ForeignKey("fuel_maps.id"), nullable=False)
    
    # 32 slots para RPM
    slot_0 = Column(Integer)  # RPM como Integer
    # ... até slot_31
    slot_31 = Column(Integer)
    
    active_slots = Column(Integer, default=24, comment="24 slots ativos por padrão")
    min_rpm = Column(Integer, default=400, comment="RPM mínimo")
    max_rpm = Column(Integer, default=8000, comment="RPM máximo")
```

#### 4.2 Eixo MAP (32 slots)
```python
class MapAxisMAP(Base):
    __tablename__ = 'map_axis_map'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id = Column(String(36), ForeignKey("fuel_maps.id"), nullable=False)
    
    # 32 slots para MAP
    slot_0 = Column(Float)  # Pressão em bar
    # ... até slot_31
    slot_31 = Column(Float)
    
    active_slots = Column(Integer, default=21, comment="21 slots ativos por padrão")
    min_pressure = Column(Float, default=-1.0, comment="Pressão mínima em bar")
    max_pressure = Column(Float, default=2.0, comment="Pressão máxima em bar")
```

#### 4.3 Eixo Temperatura (16 slots)
```python
class MapAxisTemperature(Base):
    __tablename__ = 'map_axis_temperature'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id = Column(String(36), ForeignKey("fuel_maps.id"), nullable=False)
    
    # 16 slots para temperatura
    slot_0 = Column(Float)  # Temperatura em °C
    # ... até slot_15
    slot_15 = Column(Float)
    
    active_slots = Column(Integer, default=14, comment="14 slots ativos por padrão")
    min_temperature = Column(Float, default=-10, comment="Temperatura mínima em °C")
    max_temperature = Column(Float, default=180, comment="Temperatura máxima em °C")
```

#### 4.4 Eixo TPS (20 slots)
```python
class MapAxisTPS(Base):
    __tablename__ = 'map_axis_tps'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id = Column(String(36), ForeignKey("fuel_maps.id"), nullable=False)
    
    # 20 slots para TPS
    slot_0 = Column(Float)  # TPS em %
    # ... até slot_19
    slot_19 = Column(Float)
    
    active_slots = Column(Integer, default=11, comment="11 slots ativos por padrão")
    min_tps = Column(Float, default=0.0, comment="TPS mínimo em %")
    max_tps = Column(Float, default=100.0, comment="TPS máximo em %")
```

#### 4.5 Eixo Tensão Bateria (9 slots)
```python
class MapAxisVoltage(Base):
    __tablename__ = 'map_axis_voltage'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id = Column(String(36), ForeignKey("fuel_maps.id"), nullable=False)
    
    # 9 slots para tensão
    slot_0 = Column(Float)  # Tensão em V
    # ... até slot_8
    slot_8 = Column(Float)
    
    active_slots = Column(Integer, default=9, comment="9 slots ativos por padrão")
    min_voltage = Column(Float, default=8.0, comment="Tensão mínima em V")
    max_voltage = Column(Float, default=16.0, comment="Tensão máxima em V")
```

#### 4.6 Eixo Partida (8 slots)
```python
class MapAxisStartup(Base):
    __tablename__ = 'map_axis_startup'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id = Column(String(36), ForeignKey("fuel_maps.id"), nullable=False)
    
    # 8 slots para partida
    slot_0 = Column(Float)  # Temperatura em °C
    # ... até slot_7
    slot_7 = Column(Float)
    
    active_slots = Column(Integer, default=8, comment="8 slots ativos por padrão")
    min_temperature = Column(Float, default=-10, comment="Temperatura mínima em °C")
    max_temperature = Column(Float, default=110, comment="Temperatura máxima em °C")
```

### 5. Criar Mapas com Dados Padrão

#### 5.1 Função para Criar Mapa Principal 2D MAP
```python
def create_main_fuel_2d_map(vehicle_id: str, bank_id: str = 'A') -> FuelMap:
    """
    Cria mapa principal de injeção 2D (MAP) com dados padrão da especificação.
    """
    # Dados padrão do eixo MAP (21 pontos ativos)
    map_values = [-1.00, -0.90, -0.80, -0.70, -0.60, -0.50, -0.40, -0.30, 
                  -0.20, -0.10, 0.00, 0.20, 0.40, 0.60, 0.80, 1.00, 
                  1.20, 1.40, 1.60, 1.80, 2.00]
    
    # Valores de injeção correspondentes (ms)
    injection_values = [5.550, 5.550, 5.550, 5.550, 5.550, 5.913, 6.277, 6.640,
                       7.004, 7.367, 7.731, 8.458, 9.185, 9.912, 10.638, 11.365,
                       12.092, 12.819, 13.546, 14.273, 15.000]
    
    return fuel_map
```

#### 5.2 Função para Criar Mapa Principal 3D
```python
def create_main_fuel_3d_map(vehicle_id: str, bank_id: str = 'A') -> FuelMap:
    """
    Cria mapa principal de injeção 3D (MAP x RPM) com dados padrão da especificação.
    21x24 células ativas em matriz 32x32.
    """
    # Implementar criação do mapa 3D com valores padrão
    pass
```

### 6. Sistema de Templates

#### 6.1 Classe para Templates de Mapas
```python
class MapTemplate(Base):
    __tablename__ = 'map_templates'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment="Nome do template")
    description = Column(Text, comment="Descrição do template")
    
    # Características do motor
    engine_type = Column(String(50), comment="Aspirado, Turbo, Supercharged")
    fuel_type = Column(String(50), comment="Gasolina, Etanol, Flex")
    displacement_min = Column(Float, comment="Cilindrada mínima em L")
    displacement_max = Column(Float, comment="Cilindrada máxima em L")
    
    # Configuração padrão
    default_bank_config = Column(JSON, comment="Configuração padrão das bancadas")
    default_maps = Column(JSON, comment="Lista de mapas incluídos no template")
    
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
```

### 7. Sistema de Versionamento

#### 7.1 Tabela de Histórico de Mapas
```python
class FuelMapHistory(Base):
    __tablename__ = 'fuel_map_history'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    map_id = Column(String(36), ForeignKey("fuel_maps.id"), nullable=False)
    version = Column(Integer, nullable=False)
    
    # Snapshot dos dados
    axis_data_snapshot = Column(JSON, comment="Snapshot dos dados dos eixos")
    map_data_snapshot = Column(JSON, comment="Snapshot dos dados do mapa")
    
    # Metadados da versão
    change_description = Column(Text, comment="Descrição das alterações")
    changed_by = Column(String(100), comment="Usuário que fez a alteração")
    change_timestamp = Column(DateTime, default=func.now())
    
    # Relacionamentos
    fuel_map = relationship("FuelMap")
    
    __table_args__ = (
        Index("idx_map_version", "map_id", "version"),
    )
```

### 8. Migrations Alembic

#### 8.1 Criar Migration para Bancadas
```python
# Migration: add_fuel_injection_banks.py
"""Add fuel injection banks configuration to Vehicle model

Revision ID: fuel_banks_001
Revises: previous_revision
Create Date: 2025-01-07

"""

def upgrade():
    # Adicionar campos de bancadas ao modelo Vehicle
    op.add_column('vehicles', sa.Column('bank_a_enabled', sa.Boolean(), default=True))
    op.add_column('vehicles', sa.Column('bank_a_mode', sa.String(20), default='semissequential'))
    # ... adicionar todos os campos necessários
    pass

def downgrade():
    # Remover campos adicionados
    pass
```

#### 8.2 Criar Migration para Tabelas de Mapas
```python
# Migration: create_fuel_maps_tables.py
"""Create fuel maps tables and relationships

Revision ID: fuel_maps_001
Revises: fuel_banks_001
Create Date: 2025-01-07

"""

def upgrade():
    # Criar todas as tabelas de mapas
    op.create_table('fuel_maps', ...)
    op.create_table('map_axis_data', ...)
    op.create_table('map_data_2d', ...)
    op.create_table('map_data_3d', ...)
    # ... criar todas as tabelas especializadas
    pass

def downgrade():
    # Remover tabelas criadas
    pass
```

### 9. Validações e Constraints

#### 9.1 Validações de Dados
```python
class MapDataValidator:
    """Validador para dados de mapas de injeção."""
    
    @staticmethod
    def validate_rpm_range(rpm_value: int) -> bool:
        """Valida se RPM está na faixa válida."""
        return 0 <= rpm_value <= 15000
    
    @staticmethod
    def validate_map_pressure(pressure: float) -> bool:
        """Valida se pressão MAP está na faixa válida."""
        return -1.0 <= pressure <= 5.0
    
    @staticmethod
    def validate_injection_time(time_ms: float) -> bool:
        """Valida se tempo de injeção está na faixa válida."""
        return 0.0 <= time_ms <= 100.0
    
    @staticmethod
    def validate_temperature(temp_c: float) -> bool:
        """Valida se temperatura está na faixa válida."""
        return -40.0 <= temp_c <= 200.0
    
    @staticmethod
    def validate_lambda(lambda_value: float) -> bool:
        """Valida se valor lambda está na faixa válida."""
        return 0.6 <= lambda_value <= 1.5
```

### 10. Funções Utilitárias

#### 10.1 Interpolação Linear
```python
def linear_interpolation(x_values: List[float], y_values: List[float], target_x: float) -> float:
    """
    Realiza interpolação linear entre pontos conhecidos.
    
    Regras da especificação:
    - Entre pontos existentes: Interpolação linear
    - Antes do primeiro ponto: Repete primeiro valor
    - Após o último ponto: Repete último valor
    """
    if not x_values or not y_values or len(x_values) != len(y_values):
        raise ValueError("Listas de valores inválidas")
    
    # Antes do primeiro ponto
    if target_x <= x_values[0]:
        return y_values[0]
    
    # Após o último ponto
    if target_x >= x_values[-1]:
        return y_values[-1]
    
    # Encontrar pontos para interpolação
    for i in range(len(x_values) - 1):
        if x_values[i] <= target_x <= x_values[i + 1]:
            # Interpolação linear
            x1, x2 = x_values[i], x_values[i + 1]
            y1, y2 = y_values[i], y_values[i + 1]
            
            factor = (target_x - x1) / (x2 - x1)
            return y1 + factor * (y2 - y1)
    
    raise ValueError("Erro na interpolação")
```

#### 10.2 Conversão 2D para 3D
```python
def convert_2d_to_3d(map_2d_data: dict, rpm_2d_data: dict) -> dict:
    """
    Converte mapas 2D (MAP e RPM) em mapa 3D (MAP x RPM).
    
    Para cada célula (map[i], rpm[j]):
        valor_3d[i][j] = valor_2d_map[i] * fator_rpm[j]
    """
    # Implementar conversão conforme especificação
    pass
```

## Saída Esperada

### 1. Arquivo Principal: src/data/fuel_maps_models.py
- Todos os modelos de dados implementados
- Relacionamentos corretos entre tabelas
- Validações e constraints apropriados
- Funções utilitárias de interpolação

### 2. Migrations Alembic
- Migration para adicionar campos de bancadas ao Vehicle
- Migration para criar tabelas de mapas
- Scripts de rollback funcionais

### 3. Dados Padrão
- Templates de mapas por tipo de motor
- Valores padrão da especificação implementados
- Sistema de criação automática de mapas

### 4. Validações
- Classe MapDataValidator completa
- Constraints de banco implementados
- Verificações de integridade

### 5. Documentação
- Comentários detalhados nos modelos
- Exemplos de uso das funções
- Guia de configuração de bancadas

## Validações Finais

### Checklist A04-STREAMLIT-PROFESSIONAL:
- [ ] ZERO emojis em todo o código
- [ ] Comentários em português brasileiro
- [ ] Nomes de variáveis descritivos
- [ ] Código limpo e profissional
- [ ] Documentação clara

### Checklist Técnico:
- [ ] Todos os tipos de mapas da especificação implementados
- [ ] Suporte completo a bancadas A/B
- [ ] Slots variáveis (8, 9, 16, 20, 32) funcionais
- [ ] Sistema de interpolação implementado
- [ ] Versionamento de mapas funcional
- [ ] Migrations Alembic criadas
- [ ] Validações de dados implementadas
- [ ] Relacionamentos corretos entre tabelas

## Observações Importantes

1. **Compatibilidade FTManager**: Estrutura deve ser idêntica ao formato .ftm
2. **Slots Fixos**: Cada eixo tem quantidade fixa de slots disponíveis
3. **Interpolação**: Implementar regras exatas da especificação
4. **Bancadas A/B**: Mapas duplicados onde necessário
5. **Performance**: Índices apropriados para consultas rápidas
6. **Integridade**: Constraints para evitar dados inválidos

Este agente deve ser executado ANTES dos outros agentes de implementação, pois fornece a base de dados necessária para todo o sistema.