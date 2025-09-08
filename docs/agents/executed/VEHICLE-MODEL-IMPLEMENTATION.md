# VEHICLE-MODEL-IMPLEMENTATION

## Objetivo
Implementar o modelo de dados Vehicle e estabelecer relacionamentos com o sistema existente, incluindo criação de migrations e métodos CRUD.

## Padrões de Desenvolvimento
Este agente segue os padrões definidos em:
- /srv/projects/shared/docs/agents/development/A04-STREAMLIT-PROFESSIONAL.md

### Princípios Fundamentais:
1. **ZERO emojis** - Usar apenas Material Design Icons
2. **Interface profissional** - Sem decorações infantis  
3. **CSS adaptativo** - Funciona em tema claro e escuro
4. **Português brasileiro** - Todos os textos traduzidos
5. **Ícones consistentes** - Material Icons em todos os componentes

## Tarefas de Implementação

### 1. Modificar src/data/models.py

#### 1.1 Adicionar Imports Necessários
```python
# Adicionar no topo do arquivo, após imports existentes:
import uuid
from sqlalchemy import Text, Index
```

#### 1.2 Criar Classe Vehicle
Adicionar no final do arquivo models.py, antes das configurações de relacionamento:

```python
class Vehicle(Base):
    """
    Modelo de dados para veículos cadastrados.
    Armazena todas as informações técnicas do veículo para contextualização
    dos dados de telemetria.
    """
    __tablename__ = "vehicles"
    
    # Identificação Principal
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, comment="Nome/modelo do veículo")
    nickname = Column(String(100), comment="Apelido ou nome popular")
    plate = Column(String(20), comment="Placa do veículo")
    year = Column(Integer, comment="Ano de fabricação")
    brand = Column(String(100), comment="Marca do veículo")
    model = Column(String(100), comment="Modelo específico")
    
    # Especificações do Motor
    engine_displacement = Column(Float, comment="Cilindrada em litros")
    engine_cylinders = Column(Integer, comment="Número de cilindros")
    engine_configuration = Column(String(50), comment="Configuração: V6, I4, V8, etc")
    engine_aspiration = Column(String(50), comment="Naturally Aspirated, Turbo, Supercharged")
    
    # Sistema de Injeção
    injector_type = Column(String(100), comment="Tipo de bico injetor")
    injector_count = Column(Integer, comment="Quantidade de bicos")
    injector_flow_rate = Column(Float, comment="Vazão em cc/min")
    fuel_rail_pressure = Column(Float, comment="Pressão do rail em bar")
    
    # Turbocompressor
    turbo_brand = Column(String(100), comment="Marca do turbocompressor")
    turbo_model = Column(String(100), comment="Modelo do turbocompressor")
    max_boost_pressure = Column(Float, comment="Pressão máxima em bar")
    wastegate_type = Column(String(50), comment="Internal/External wastegate")
    
    # Transmissão
    transmission_type = Column(String(50), comment="Manual/Automatic/CVT")
    gear_count = Column(Integer, comment="Número de marchas")
    final_drive_ratio = Column(Float, comment="Relação final da transmissão")
    
    # Características Físicas
    curb_weight = Column(Float, comment="Peso em ordem de marcha (kg)")
    power_weight_ratio = Column(Float, comment="Relação peso/potência")
    drivetrain = Column(String(50), comment="FWD, RWD, AWD")
    tire_size = Column(String(50), comment="Medida dos pneus")
    
    # Sistema de Combustível
    fuel_type = Column(String(50), comment="Gasoline, Ethanol, Flex, Diesel")
    octane_rating = Column(Integer, comment="Octanagem do combustível")
    fuel_system = Column(String(100), comment="Port Injection, Direct, Dual")
    
    # Performance Estimada
    estimated_power = Column(Float, comment="Potência estimada em HP")
    estimated_torque = Column(Float, comment="Torque estimado em Nm")
    max_rpm = Column(Integer, comment="RPM máximo do motor")
    
    # Metadados de Sistema
    created_at = Column(DateTime, default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Última atualização")
    is_active = Column(Boolean, default=True, comment="Veículo está ativo")
    notes = Column(Text, comment="Observações adicionais")
    
    # Relacionamentos
    sessions = relationship("DataSession", back_populates="vehicle", cascade="all, delete-orphan")
    
    # Índices para Performance
    __table_args__ = (
        Index("idx_vehicle_name", "name"),
        Index("idx_vehicle_brand_model", "brand", "model"),
        Index("idx_vehicle_active", "is_active"),
        Index("idx_vehicle_created", "created_at"),
        Index("idx_vehicle_year", "year"),
    )
    
    def __repr__(self):
        return f"<Vehicle(id={self.id}, name='{self.name}', year={self.year})>"
    
    @property
    def display_name(self):
        """Nome formatado para exibição."""
        if self.nickname:
            return f"{self.name} ({self.nickname})"
        return f"{self.name} ({self.year})" if self.year else self.name
    
    @property
    def technical_summary(self):
        """Resumo técnico do veículo."""
        parts = []
        if self.engine_displacement:
            parts.append(f"{self.engine_displacement}L")
        if self.engine_configuration:
            parts.append(self.engine_configuration)
        if self.engine_aspiration and self.engine_aspiration != "Naturally Aspirated":
            parts.append(self.engine_aspiration)
        return " ".join(parts) if parts else "Não especificado"
```

#### 1.3 Modificar Classe DataSession
Adicionar na classe DataSession existente:

```python
# Adicionar na classe DataSession após os campos existentes:
vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=True, comment="ID do veículo vinculado")

# Modificar o relacionamento existente ou adicionar:
vehicle = relationship("Vehicle", back_populates="sessions")
```

### 2. Criar Migration com Alembic

#### 2.1 Gerar Migration Automática
```bash
# Executar no diretório raiz do projeto:
alembic revision --autogenerate -m "add_vehicle_model_and_relationships"
```

#### 2.2 Verificar e Ajustar Migration
Editar o arquivo de migration gerado para garantir:
- Ordem correta de criação de tabelas
- Foreign keys adequadas
- Índices necessários
- Comentários nas colunas

### 3. Atualizar src/data/database.py

#### 3.1 Adicionar Funções CRUD para Vehicle

Adicionar as seguintes funções ao final do arquivo database.py:

```python
# ========================================
# CRUD Operations para Vehicle
# ========================================

def create_vehicle(vehicle_data: dict) -> str:
    """
    Cria um novo veículo no banco de dados.
    
    Args:
        vehicle_data: Dicionário com dados do veículo
    
    Returns:
        str: ID do veículo criado
    
    Raises:
        ValueError: Se dados obrigatórios estão ausentes
        Exception: Para outros erros de banco
    """
    if not vehicle_data.get("name"):
        raise ValueError("Nome do veículo é obrigatório")
    
    try:
        with get_db_session() as session:
            vehicle = Vehicle(**vehicle_data)
            session.add(vehicle)
            session.commit()
            
            logger.info(f"Veículo criado: {vehicle.id} - {vehicle.name}")
            return vehicle.id
            
    except Exception as e:
        logger.error(f"Erro ao criar veículo: {str(e)}")
        raise

def get_vehicle_by_id(vehicle_id: str) -> Optional[Vehicle]:
    """
    Busca veículo por ID.
    
    Args:
        vehicle_id: ID do veículo
    
    Returns:
        Vehicle ou None se não encontrado
    """
    try:
        with get_db_session() as session:
            return session.query(Vehicle).filter(
                Vehicle.id == vehicle_id
            ).first()
            
    except Exception as e:
        logger.error(f"Erro ao buscar veículo {vehicle_id}: {str(e)}")
        return None

def get_all_vehicles(active_only: bool = True) -> List[Vehicle]:
    """
    Lista todos os veículos.
    
    Args:
        active_only: Se True, retorna apenas veículos ativos
    
    Returns:
        List[Vehicle]: Lista de veículos
    """
    try:
        with get_db_session() as session:
            query = session.query(Vehicle)
            
            if active_only:
                query = query.filter(Vehicle.is_active == True)
            
            return query.order_by(Vehicle.name).all()
            
    except Exception as e:
        logger.error(f"Erro ao listar veículos: {str(e)}")
        return []

def update_vehicle(vehicle_id: str, update_data: dict) -> bool:
    """
    Atualiza dados do veículo.
    
    Args:
        vehicle_id: ID do veículo
        update_data: Dados para atualizar
    
    Returns:
        bool: True se atualizado com sucesso
    """
    try:
        with get_db_session() as session:
            vehicle = session.query(Vehicle).filter(
                Vehicle.id == vehicle_id
            ).first()
            
            if not vehicle:
                logger.warning(f"Veículo não encontrado: {vehicle_id}")
                return False
            
            # Atualizar campos fornecidos
            for field, value in update_data.items():
                if hasattr(vehicle, field):
                    setattr(vehicle, field, value)
            
            # Atualizar timestamp
            vehicle.updated_at = func.now()
            
            session.commit()
            logger.info(f"Veículo atualizado: {vehicle_id}")
            return True
            
    except Exception as e:
        logger.error(f"Erro ao atualizar veículo {vehicle_id}: {str(e)}")
        return False

def delete_vehicle(vehicle_id: str, soft_delete: bool = True) -> bool:
    """
    Remove veículo (soft delete por padrão).
    
    Args:
        vehicle_id: ID do veículo
        soft_delete: Se True, apenas marca como inativo
    
    Returns:
        bool: True se removido com sucesso
    """
    try:
        with get_db_session() as session:
            vehicle = session.query(Vehicle).filter(
                Vehicle.id == vehicle_id
            ).first()
            
            if not vehicle:
                logger.warning(f"Veículo não encontrado: {vehicle_id}")
                return False
            
            # Verificar se há sessões vinculadas
            session_count = session.query(DataSession).filter(
                DataSession.vehicle_id == vehicle_id
            ).count()
            
            if session_count > 0 and not soft_delete:
                raise ValueError(
                    f"Não é possível excluir veículo com {session_count} sessões vinculadas. "
                    "Use soft delete ou migre as sessões primeiro."
                )
            
            if soft_delete:
                vehicle.is_active = False
                vehicle.updated_at = func.now()
                logger.info(f"Veículo desativado: {vehicle_id}")
            else:
                session.delete(vehicle)
                logger.info(f"Veículo removido: {vehicle_id}")
            
            session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Erro ao remover veículo {vehicle_id}: {str(e)}")
        return False

def search_vehicles(search_term: str, active_only: bool = True) -> List[Vehicle]:
    """
    Busca veículos por termo.
    
    Args:
        search_term: Termo para buscar (nome, marca, modelo)
        active_only: Se True, busca apenas veículos ativos
    
    Returns:
        List[Vehicle]: Lista de veículos encontrados
    """
    try:
        with get_db_session() as session:
            query = session.query(Vehicle)
            
            if active_only:
                query = query.filter(Vehicle.is_active == True)
            
            # Buscar em múltiplos campos
            search_filter = or_(
                Vehicle.name.ilike(f"%{search_term}%"),
                Vehicle.brand.ilike(f"%{search_term}%"),
                Vehicle.model.ilike(f"%{search_term}%"),
                Vehicle.nickname.ilike(f"%{search_term}%")
            )
            
            return query.filter(search_filter).order_by(Vehicle.name).all()
            
    except Exception as e:
        logger.error(f"Erro ao buscar veículos com termo '{search_term}': {str(e)}")
        return []

def get_vehicle_statistics(vehicle_id: str) -> dict:
    """
    Obtém estatísticas do veículo (sessões, dados, etc.).
    
    Args:
        vehicle_id: ID do veículo
    
    Returns:
        dict: Estatísticas do veículo
    """
    try:
        with get_db_session() as session:
            vehicle = session.query(Vehicle).filter(
                Vehicle.id == vehicle_id
            ).first()
            
            if not vehicle:
                return {}
            
            # Contar sessões
            session_count = session.query(DataSession).filter(
                DataSession.vehicle_id == vehicle_id
            ).count()
            
            # Data da primeira e última sessão
            first_session = session.query(DataSession).filter(
                DataSession.vehicle_id == vehicle_id
            ).order_by(DataSession.created_at).first()
            
            last_session = session.query(DataSession).filter(
                DataSession.vehicle_id == vehicle_id
            ).order_by(DataSession.created_at.desc()).first()
            
            # Contar registros de dados
            core_data_count = session.query(FuelTechCoreData).join(DataSession).filter(
                DataSession.vehicle_id == vehicle_id
            ).count()
            
            return {
                "vehicle_id": vehicle_id,
                "vehicle_name": vehicle.display_name,
                "session_count": session_count,
                "core_data_count": core_data_count,
                "first_session_date": first_session.created_at if first_session else None,
                "last_session_date": last_session.created_at if last_session else None,
                "created_at": vehicle.created_at,
                "updated_at": vehicle.updated_at
            }
            
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do veículo {vehicle_id}: {str(e)}")
        return {}
```

### 4. Validações e Constraints

#### 4.1 Adicionar Validações de Dados
Criar arquivo `src/data/vehicle_validators.py`:

```python
"""
Validadores específicos para dados de veículos.
"""
from typing import Dict, List, Optional
import re

def validate_vehicle_data(data: dict) -> Dict[str, List[str]]:
    """
    Valida dados de veículo antes da inserção/atualização.
    
    Args:
        data: Dicionário com dados do veículo
    
    Returns:
        Dict com campo -> lista de erros
    """
    errors = {}
    
    # Nome é obrigatório
    if not data.get("name") or not data["name"].strip():
        errors["name"] = ["Nome do veículo é obrigatório"]
    elif len(data["name"].strip()) < 2:
        errors["name"] = ["Nome deve ter pelo menos 2 caracteres"]
    
    # Validar ano
    if data.get("year"):
        year = data["year"]
        if not isinstance(year, int) or year < 1980 or year > 2030:
            errors["year"] = ["Ano deve estar entre 1980 e 2030"]
    
    # Validar placa (formato brasileiro)
    if data.get("plate"):
        plate = data["plate"].upper().replace("-", "").replace(" ", "")
        if not re.match(r'^[A-Z]{3}\d{4}$|^[A-Z]{3}\d[A-Z]\d{2}$', plate):
            errors["plate"] = ["Formato de placa inválido (use ABC1234 ou ABC1D23)"]
    
    # Validar cilindrada
    if data.get("engine_displacement"):
        disp = data["engine_displacement"]
        if not isinstance(disp, (int, float)) or disp <= 0 or disp > 15:
            errors["engine_displacement"] = ["Cilindrada deve estar entre 0.1 e 15.0 litros"]
    
    # Validar número de cilindros
    if data.get("engine_cylinders"):
        cyl = data["engine_cylinders"]
        if not isinstance(cyl, int) or cyl < 1 or cyl > 16:
            errors["engine_cylinders"] = ["Número de cilindros deve estar entre 1 e 16"]
    
    # Validar peso
    if data.get("curb_weight"):
        weight = data["curb_weight"]
        if not isinstance(weight, (int, float)) or weight <= 0 or weight > 5000:
            errors["curb_weight"] = ["Peso deve estar entre 1 e 5000 kg"]
    
    # Validar potência estimada
    if data.get("estimated_power"):
        power = data["estimated_power"]
        if not isinstance(power, (int, float)) or power <= 0 or power > 2000:
            errors["estimated_power"] = ["Potência deve estar entre 1 e 2000 HP"]
    
    return errors

def validate_plate_format(plate: str) -> bool:
    """Valida formato de placa brasileira."""
    if not plate:
        return True  # Placa é opcional
    
    plate_clean = plate.upper().replace("-", "").replace(" ", "")
    return bool(re.match(r'^[A-Z]{3}\d{4}$|^[A-Z]{3}\d[A-Z]\d{2}$', plate_clean))

def normalize_plate(plate: str) -> str:
    """Normaliza formato da placa."""
    if not plate:
        return ""
    
    plate_clean = plate.upper().replace("-", "").replace(" ", "")
    if len(plate_clean) == 7:
        # Formato ABC1234 -> ABC-1234
        return f"{plate_clean[:3]}-{plate_clean[3:]}"
    elif len(plate_clean) == 7 and re.match(r'^[A-Z]{3}\d[A-Z]\d{2}$', plate_clean):
        # Formato ABC1D23 -> ABC1D23 (Mercosul)
        return plate_clean
    
    return plate
```

### 5. Testes do Modelo

#### 5.1 Criar Arquivo de Testes
Criar `tests/test_vehicle_model.py`:

```python
"""
Testes para o modelo Vehicle e operações CRUD.
"""
import pytest
from src.data.models import Vehicle
from src.data.database import (
    create_vehicle, get_vehicle_by_id, get_all_vehicles,
    update_vehicle, delete_vehicle, search_vehicles
)

def test_create_vehicle():
    """Testa criação de veículo."""
    vehicle_data = {
        "name": "Civic Si",
        "brand": "Honda",
        "year": 2020,
        "engine_displacement": 2.0,
        "engine_cylinders": 4
    }
    
    vehicle_id = create_vehicle(vehicle_data)
    assert vehicle_id is not None
    
    # Verificar se foi criado
    vehicle = get_vehicle_by_id(vehicle_id)
    assert vehicle is not None
    assert vehicle.name == "Civic Si"
    assert vehicle.brand == "Honda"

def test_vehicle_display_name():
    """Testa propriedade display_name."""
    vehicle_data = {
        "name": "Civic Si",
        "nickname": "Carro da Pista",
        "year": 2020
    }
    
    vehicle_id = create_vehicle(vehicle_data)
    vehicle = get_vehicle_by_id(vehicle_id)
    
    assert vehicle.display_name == "Civic Si (Carro da Pista)"
```

## Checklist de Validação

### Modelo de Dados
- [ ] Classe Vehicle criada com todos os campos especificados
- [ ] Relacionamento com DataSession estabelecido
- [ ] Índices de performance criados
- [ ] Comentários adicionados às colunas
- [ ] Propriedades display_name e technical_summary implementadas

### Migrations
- [ ] Migration gerada automaticamente
- [ ] Foreign key constraints verificadas
- [ ] Índices incluídos na migration
- [ ] Migration testada em ambiente de desenvolvimento

### Operações CRUD
- [ ] create_vehicle implementada com validações
- [ ] get_vehicle_by_id funcional
- [ ] get_all_vehicles com filtro de ativos
- [ ] update_vehicle com timestamp automático
- [ ] delete_vehicle com soft delete
- [ ] search_vehicles em múltiplos campos
- [ ] get_vehicle_statistics para métricas

### Validações
- [ ] Validadores de dados implementados
- [ ] Validação de placa brasileira
- [ ] Normalização de dados
- [ ] Tratamento de erros adequado

### Testes
- [ ] Testes básicos de CRUD criados
- [ ] Testes de validação implementados
- [ ] Testes de relacionamentos verificados
- [ ] Coverage de testes > 80%

## Riscos e Mitigações

### Riscos Técnicos:
1. **Conflitos de Schema**: Migration pode falhar se houver dados inconsistentes
2. **Performance**: Novos índices podem impactar queries existentes
3. **Relacionamentos**: Foreign keys podem causar problemas de integridade

### Mitigações:
1. **Backup completo** antes de executar migrations
2. **Testes extensivos** em ambiente de desenvolvimento
3. **Rollback plan** preparado para reversão
4. **Monitoring** de performance pós-implementação

## Próximos Passos

Após conclusão deste agente:
1. Executar migration em ambiente de desenvolvimento
2. Validar modelo com dados de teste
3. Proceder com VEHICLE-MIGRATION-IMPLEMENTATION
4. Integrar com VEHICLE-UI-IMPLEMENTATION

---

**Prioridade:** Alta  
**Complexidade:** Média  
**Tempo Estimado:** 1-2 dias  
**Dependências:** Nenhuma  
**Bloqueia:** Todos os outros agentes de veículos