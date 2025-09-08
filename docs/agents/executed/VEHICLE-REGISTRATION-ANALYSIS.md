# VEHICLE-REGISTRATION-ANALYSIS

## Objetivo
Análise completa para implementação de um sistema de cadastro de veículos no FuelTune, permitindo que todos os registros de telemetria sejam vinculados a veículos específicos com suas características detalhadas.

## Padrões de Desenvolvimento
Este agente segue os padrões definidos em:
- /srv/projects/shared/docs/agents/development/A04-STREAMLIT-PROFESSIONAL.md

### Princípios Fundamentais:
1. **ZERO emojis** - Usar apenas Material Design Icons
2. **Interface profissional** - Sem decorações infantis
3. **CSS adaptativo** - Funciona em tema claro e escuro
4. **Português brasileiro** - Todos os textos traduzidos
5. **Ícones consistentes** - Material Icons em todos os componentes

## Análise do Sistema Atual

### Estado Atual do Banco de Dados
Com base na análise de `/home/lee/projects/fueltune-streamlit/src/data/models.py`:

**Estrutura Existente:**
- `DataSession`: Agrupa sessões de logging com metadados do arquivo
- `FuelTechCoreData`: 37 campos básicos de telemetria do motor
- `FuelTechExtendedData`: 27 campos adicionais para formato v2.0 (64 campos)
- `DataQualityCheck`: Validações e métricas de qualidade

**Problema Identificado:**
- Não há vinculação dos dados a veículos específicos
- Dados de telemetria são anônimos
- Impossível comparar performance entre diferentes veículos
- Contexto do veículo perdido na análise

### Estado Atual das Interfaces
Páginas existentes em `/home/lee/projects/fueltune-streamlit/src/ui/pages/`:
- `dashboard.py` - Painel principal com métricas
- `upload.py` - Upload de arquivos CSV
- `analysis.py` - Análise de dados
- `performance.py` - Métricas de performance  
- `consumption.py` - Análise de consumo
- `imu.py` - Dados de aceleração/IMU
- `reports.py` - Relatórios
- `versioning.py` - Controle de versão

**Necessidades Identificadas:**
- Nova página de cadastro de veículos
- Seletor de veículo ativo em todas as páginas
- Migração de dados existentes

## Proposta de Solução

### 1. Modelo de Dados

#### Tabela Vehicle (Nova)
```python
class Vehicle(Base):
    """
    Tabela de veículos cadastrados.
    Armazena todas as informações técnicas do veículo.
    """
    __tablename__ = "vehicles"
    
    # Identificação
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)  # Nome/Modelo
    nickname = Column(String(100))  # Apelido/nome popular
    plate = Column(String(20))  # Placa (opcional)
    year = Column(Integer)  # Ano de fabricação
    brand = Column(String(100))  # Marca
    model = Column(String(100))  # Modelo específico
    
    # Motor
    engine_displacement = Column(Float)  # Cilindrada (L)
    engine_cylinders = Column(Integer)  # Número de cilindros
    engine_configuration = Column(String(50))  # V6, I4, V8, etc.
    engine_aspiration = Column(String(50))  # Naturally Aspirated, Turbo, Supercharged
    
    # Sistema de Injeção
    injector_type = Column(String(100))  # Tipo de bico injetor
    injector_count = Column(Integer)  # Quantidade de bicos
    injector_flow_rate = Column(Float)  # Vazão (cc/min)
    fuel_rail_pressure = Column(Float)  # Pressão do rail (bar)
    
    # Turbocompressor
    turbo_brand = Column(String(100))  # Marca do turbo
    turbo_model = Column(String(100))  # Modelo do turbo
    max_boost_pressure = Column(Float)  # Pressão máxima (bar)
    wastegate_type = Column(String(50))  # Internal/External
    
    # Transmissão
    transmission_type = Column(String(50))  # Manual/Automatic/CVT
    gear_count = Column(Integer)  # Número de marchas
    final_drive_ratio = Column(Float)  # Relação final
    
    # Características Físicas
    curb_weight = Column(Float)  # Peso em ordem de marcha (kg)
    power_weight_ratio = Column(Float)  # Relação peso/potência
    drivetrain = Column(String(50))  # FWD, RWD, AWD
    tire_size = Column(String(50))  # Medida dos pneus
    
    # Combustível
    fuel_type = Column(String(50))  # Gasoline, Ethanol, Flex, Diesel
    octane_rating = Column(Integer)  # Octanagem
    fuel_system = Column(String(100))  # Port Injection, Direct, Dual
    
    # Performance (estimado/oficial)
    estimated_power = Column(Float)  # Potência estimada (HP)
    estimated_torque = Column(Float)  # Torque estimado (Nm)
    max_rpm = Column(Integer)  # RPM máximo
    
    # Metadados
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)  # Veículo ativo
    notes = Column(Text)  # Observações adicionais
    
    # Relationships
    sessions = relationship("DataSession", back_populates="vehicle")
    
    # Constraints
    __table_args__ = (
        Index("idx_vehicle_name", "name"),
        Index("idx_vehicle_active", "is_active"),
        Index("idx_vehicle_created", "created_at"),
    )
```

### 2. Relacionamentos

#### Modificação da Tabela DataSession
```python
# Adicionar à classe DataSession existente:
vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=True)  # Nullable para migração
vehicle = relationship("Vehicle", back_populates="sessions")
```

#### Relacionamento 1:N
- 1 Vehicle pode ter N DataSessions
- 1 DataSession pertence a 1 Vehicle (após migração)
- Permite histórico completo por veículo
- Comparações entre diferentes veículos

### 3. Interface de Cadastro

#### Página: `vehicles.py`
```python
# Nova página: /src/ui/pages/vehicles.py

def show_vehicle_registration():
    """Interface principal de cadastro de veículos."""
    
    st.markdown('<div class="main-header"><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">directions_car</span>Cadastro de Veículos</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["Lista de Veículos", "Cadastrar Novo", "Editar Veículo"])
    
    with tabs[0]:
        show_vehicle_list()
    
    with tabs[1]:
        show_vehicle_form()
    
    with tabs[2]:
        show_vehicle_editor()

def show_vehicle_form():
    """Formulário de cadastro de novo veículo."""
    
    with st.form("vehicle_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>info</span>Identificação", unsafe_allow_html=True)
            name = st.text_input("Nome/Modelo", placeholder="Ex: Civic Si")
            nickname = st.text_input("Apelido", placeholder="Ex: Carro da pista")
            plate = st.text_input("Placa", placeholder="Ex: ABC-1234")
            year = st.number_input("Ano", min_value=1980, max_value=2030, value=2020)
            brand = st.selectbox("Marca", ["Honda", "Toyota", "Volkswagen", "Ford", "Chevrolet", "Outro"])
            model = st.text_input("Modelo Específico", placeholder="Ex: Civic Si 2.0 VTEC")
        
        with col2:
            st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>engineering</span>Motor", unsafe_allow_html=True)
            engine_displacement = st.number_input("Cilindrada (L)", min_value=0.5, max_value=10.0, step=0.1, value=2.0)
            engine_cylinders = st.number_input("Cilindros", min_value=2, max_value=16, value=4)
            engine_configuration = st.selectbox("Configuração", ["I4", "V6", "V8", "H4", "V10", "V12", "I3", "I5"])
            engine_aspiration = st.selectbox("Aspiração", ["Naturally Aspirated", "Turbocharged", "Supercharged", "Twin-Turbo"])
        
        # Mais seções: Injeção, Turbo, Transmissão, etc.
        
        submitted = st.form_submit_button(":material/save: Salvar Veículo")
        
        if submitted:
            save_vehicle(vehicle_data)
```

#### Componente: Seletor de Veículo
```python
# Componente reutilizável para seleção de veículo ativo
def vehicle_selector():
    """Seletor de veículo ativo para usar em todas as páginas."""
    
    vehicles = get_active_vehicles()
    
    if not vehicles:
        st.warning("Nenhum veículo cadastrado. Cadastre um veículo primeiro.")
        if st.button(":material/add: Cadastrar Veículo"):
            st.switch_page("vehicles")
        return None
    
    vehicle_options = [f"{v.name} ({v.year})" for v in vehicles]
    
    selected_index = st.selectbox(
        "Veículo Ativo",
        range(len(vehicles)),
        format_func=lambda i: vehicle_options[i],
        key="active_vehicle"
    )
    
    return vehicles[selected_index] if selected_index is not None else None
```

### 4. Integração com Sistema Existente

#### Modificações Necessárias por Página:

**dashboard.py:**
- Adicionar seletor de veículo no topo
- Filtrar métricas pelo veículo selecionado
- Adicionar card com informações do veículo ativo

**upload.py:**
- Solicitar seleção de veículo antes do upload
- Vincular automaticamente sessão ao veículo
- Validar se veículo existe antes de processar

**analysis.py:**
- Filtro por veículo nas análises
- Comparação entre veículos
- Contexto do veículo nas análises

**performance.py:**
- Usar dados do veículo para cálculos mais precisos
- Peso real para cálculos de potência/peso
- RPM máximo do veículo para validações

#### Função de Contexto Global:
```python
# src/data/context.py
class VehicleContext:
    """Contexto global do veículo ativo na aplicação."""
    
    def __init__(self):
        if "active_vehicle_id" not in st.session_state:
            st.session_state.active_vehicle_id = None
    
    @property
    def active_vehicle_id(self):
        return st.session_state.active_vehicle_id
    
    @active_vehicle_id.setter
    def active_vehicle_id(self, value):
        st.session_state.active_vehicle_id = value
    
    def get_active_vehicle(self):
        if not self.active_vehicle_id:
            return None
        return get_vehicle_by_id(self.active_vehicle_id)
```

### 5. Migração de Dados

#### Estratégia de Migração:
```python
# scripts/migrate_existing_data.py

def create_default_vehicle():
    """Cria veículo padrão para dados existentes."""
    
    default_vehicle = Vehicle(
        name="Veículo Não Identificado",
        nickname="Dados Migrados",
        engine_displacement=2.0,  # Valores padrão
        engine_cylinders=4,
        engine_configuration="I4",
        engine_aspiration="Naturally Aspirated",
        fuel_type="Gasoline",
        notes="Dados migrados automaticamente do sistema anterior"
    )
    
    db.add(default_vehicle)
    db.commit()
    return default_vehicle

def migrate_existing_sessions():
    """Migra sessões existentes para o veículo padrão."""
    
    default_vehicle = create_default_vehicle()
    
    # Atualizar todas as sessões sem veículo
    db.query(DataSession).filter(
        DataSession.vehicle_id.is_(None)
    ).update({
        DataSession.vehicle_id: default_vehicle.id
    })
    
    db.commit()
    logger.info(f"Migrados dados para veículo padrão: {default_vehicle.id}")
```

#### Queries SQL de Migração:
```sql
-- 1. Adicionar coluna vehicle_id à tabela data_sessions
ALTER TABLE data_sessions ADD COLUMN vehicle_id VARCHAR(36);

-- 2. Criar índice na nova coluna
CREATE INDEX idx_session_vehicle ON data_sessions(vehicle_id);

-- 3. Criar foreign key constraint (após migração dos dados)
-- ALTER TABLE data_sessions ADD CONSTRAINT fk_session_vehicle 
-- FOREIGN KEY (vehicle_id) REFERENCES vehicles(id);
```

## Plano de Implementação

### Fase 1: Estrutura Base (1-2 dias)
1. **Criar modelo Vehicle** - Adicionar nova tabela ao models.py
2. **Modificar DataSession** - Adicionar relationship com Vehicle
3. **Criar migrações** - Scripts SQL e Python para migração
4. **Testar modelo** - Validar relacionamentos e constraints

### Fase 2: Interface de Cadastro (2-3 dias)  
1. **Criar vehicles.py** - Página principal de cadastro
2. **Formulário completo** - Todos os campos organizados em seções
3. **Validações** - Regras de negócio e validação de dados
4. **CRUD completo** - Criar, listar, editar, excluir veículos

### Fase 3: Integração (2-3 dias)
1. **Seletor de veículo** - Componente reutilizável
2. **Modificar páginas existentes** - Adicionar contexto de veículo
3. **Filtros por veículo** - Implementar em todas as análises
4. **Contexto global** - Sistema de veículo ativo

### Fase 4: Migração e Testes (1-2 dias)
1. **Executar migração** - Dados existentes para veículo padrão
2. **Testes extensivos** - Validar todas as funcionalidades
3. **Documentação** - Guia do usuário para cadastro
4. **Validação final** - Performance e usabilidade

### Fase 5: Features Avançadas (2-3 dias)
1. **Comparação entre veículos** - Análises comparativas
2. **Templates de veículo** - Modelos pré-cadastrados
3. **Importação/Exportação** - Backup de configurações
4. **Relatórios por veículo** - Análises específicas

## Riscos e Considerações

### Riscos Técnicos:
1. **Migração de dados** - Possível perda de referências
2. **Performance** - Queries mais complexas com joins
3. **Compatibilidade** - Impacto em código existente
4. **Validação** - Dados inconsistentes em veículos

### Mitigações:
1. **Backup completo** antes de qualquer migração
2. **Testes em ambiente de desenvolvimento** primeiro
3. **Migração gradual** com rollback disponível
4. **Monitoramento** de performance pós-migração

### Considerações de UX:
1. **Seleção obrigatória** - Forçar escolha de veículo pode frustrar
2. **Complexidade** - Muitos campos podem intimidar usuários
3. **Defaults inteligentes** - Valores padrão baseados em dados existentes
4. **Wizard de configuração** - Guiar usuário no primeiro cadastro

## Próximos Passos

### Agentes a Criar Após Aprovação:
1. **VEHICLE-MODEL-IMPLEMENTATION.md** - Implementar modelo de dados
2. **VEHICLE-INTERFACE-DESIGN.md** - Criar interfaces de cadastro  
3. **VEHICLE-INTEGRATION.md** - Integrar com páginas existentes
4. **VEHICLE-MIGRATION.md** - Executar migração de dados
5. **VEHICLE-TESTING.md** - Testes e validação completa

### Validação Necessária:
1. **Aprovação da estrutura** - Validar campos propostos
2. **Review da UX** - Fluxo de trabalho do usuário
3. **Teste de migração** - Simular em dados de desenvolvimento
4. **Capacitação** - Treinar usuário no novo sistema

### Métricas de Sucesso:
- [ ] 100% dos dados migrados sem perda
- [ ] Tempo de cadastro < 5 minutos por veículo
- [ ] Performance das queries mantida < 2s
- [ ] Zero erros de validação pós-migração
- [ ] Satisfação do usuário > 8/10

---

**Data de Criação:** 2025-01-06  
**Autor:** VEHICLE-REGISTRATION-ANALYSIS Agent  
**Status:** Aguardando Aprovação  
**Complexidade:** Alta  
**Tempo Estimado:** 8-12 dias