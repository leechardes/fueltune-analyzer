# FUEL-MAPS-BANKS-IMPLEMENTATION

## Objetivo
Implementar sistema completo de configuração e gerenciamento de bancadas A/B de injeção, incluindo interface de configuração, cálculos de vazão, duplicação de mapas e sincronização entre bancadas.

## Contexto
Você é um especialista em sistemas de injeção eletrônica automotiva com foco na configuração de bancadas múltiplas. Deve implementar todas as funcionalidades necessárias para suportar configurações desde motores simples (apenas bancada A) até sistemas complexos com bancadas A e B independentes.

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
- **Modelos implementados**: src/data/fuel_maps_models.py (do agente anterior)
- **Documentação**: docs/FUEL-MAPS-SPECIFICATION.md
- **Diretório base**: /home/lee/projects/fueltune-streamlit/

## Tarefas

### 1. Criar Componente de Configuração de Bancadas

#### 1.1 Arquivo: src/components/bank_configurator.py
```python
"""
Componente para configuração de bancadas de injeção A/B.
Permite configurar modo de injeção, saídas, vazão e dead time.
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple
import json

from ..data.models import Vehicle, get_database
from ..utils.calculations import calculate_total_flow, validate_injector_flow

class BankConfigurator:
    """Configurador de bancadas de injeção."""
    
    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.db = get_database()
    
    def render_bank_config(self) -> None:
        """Renderiza interface completa de configuração de bancadas."""
        
        st.markdown(
            '<div class="main-header">'
            '<span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">settings</span>'
            'Configuração de Bancadas de Injeção'
            '</div>',
            unsafe_allow_html=True
        )
        
        # Carregar dados do veículo
        vehicle = self._load_vehicle_data()
        if not vehicle:
            st.error("Veículo não encontrado")
            return
        
        # Layout em duas colunas
        col1, col2 = st.columns(2)
        
        # Configuração Bancada A
        with col1:
            self._render_bank_a_config(vehicle)
        
        # Configuração Bancada B
        with col2:
            self._render_bank_b_config(vehicle)
        
        # Resumo e validações
        st.markdown("---")
        self._render_configuration_summary(vehicle)
        
        # Botões de ação
        self._render_action_buttons(vehicle)
    
    def _render_bank_a_config(self, vehicle: Vehicle) -> None:
        """Renderiza configuração da Bancada A."""
        
        st.markdown(
            '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">electrical_services</span>Bancada A (Principal)</h3>',
            unsafe_allow_html=True
        )
        
        # Bancada A sempre ativa
        st.info("Bancada A é sempre ativa (principal)")
        
        # Modo de injeção
        bank_a_mode = st.selectbox(
            "Modo de Injeção A",
            options=["multiponto", "semissequencial", "sequencial"],
            index=self._get_mode_index(vehicle.bank_a_mode or "semissequencial"),
            key="bank_a_mode",
            help="Multiponto: todos simultaneamente | Semissequencial: pares | Sequencial: individual"
        )
        
        # Saídas disponíveis
        available_outputs = list(range(1, 9))  # Saídas 1 a 8
        bank_a_outputs = st.multiselect(
            "Saídas Utilizadas A",
            options=available_outputs,
            default=self._parse_outputs(vehicle.bank_a_outputs) or [1, 2, 3, 4],
            key="bank_a_outputs",
            help="Selecione as saídas conectadas aos bicos da Bancada A"
        )
        
        # Configuração dos bicos
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            bank_a_flow = st.number_input(
                "Vazão por Bico A (lb/h)",
                min_value=10.0,
                max_value=2000.0,
                value=float(vehicle.bank_a_injector_flow or 80.0),
                step=5.0,
                key="bank_a_flow",
                help="Vazão individual de cada bico injetor"
            )
        
        with col_a2:
            bank_a_count = st.number_input(
                "Quantidade de Bicos A",
                min_value=1,
                max_value=8,
                value=int(vehicle.bank_a_injector_count or len(bank_a_outputs or [4])),
                key="bank_a_count",
                help="Número total de bicos na Bancada A"
            )
        
        # Vazão total calculada
        total_flow_a = calculate_total_flow(bank_a_flow, bank_a_count)
        st.metric(
            "Vazão Total Bancada A",
            f"{total_flow_a:.1f} lb/h",
            help="Vazão total da bancada (vazão por bico × quantidade)"
        )
        
        # Dead time
        bank_a_dead_time = st.number_input(
            "Dead Time Bancada A (ms)",
            min_value=0.0,
            max_value=10.0,
            value=float(vehicle.bank_a_dead_time or 1.0),
            step=0.1,
            key="bank_a_dead_time",
            help="Compensação de tempo de resposta dos injetores"
        )
        
        # Salvar configurações da Bancada A
        if st.button(":material/save: Salvar Bancada A", key="save_bank_a"):
            self._save_bank_a_config(
                vehicle, bank_a_mode, bank_a_outputs, 
                bank_a_flow, bank_a_count, bank_a_dead_time
            )
    
    def _render_bank_b_config(self, vehicle: Vehicle) -> None:
        """Renderiza configuração da Bancada B."""
        
        st.markdown(
            '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">power</span>Bancada B (Auxiliar)</h3>',
            unsafe_allow_html=True
        )
        
        # Habilitar/Desabilitar Bancada B
        bank_b_enabled = st.checkbox(
            "Habilitar Bancada B",
            value=vehicle.bank_b_enabled or False,
            key="bank_b_enabled",
            help="Ativar bancada auxiliar para sistemas avançados"
        )
        
        if not bank_b_enabled:
            st.info("Bancada B desabilitada. Marque acima para configurar.")
            return
        
        # Configurações da Bancada B (similares à A)
        bank_b_mode = st.selectbox(
            "Modo de Injeção B",
            options=["multiponto", "semissequencial", "sequencial"],
            index=self._get_mode_index(vehicle.bank_b_mode or "semissequencial"),
            key="bank_b_mode"
        )
        
        # Saídas disponíveis (excluindo as já usadas pela Bancada A)
        bank_a_outputs = self._parse_outputs(vehicle.bank_a_outputs) or []
        available_for_b = [x for x in range(1, 9) if x not in bank_a_outputs]
        
        bank_b_outputs = st.multiselect(
            "Saídas Utilizadas B",
            options=available_for_b,
            default=self._parse_outputs(vehicle.bank_b_outputs) or [],
            key="bank_b_outputs",
            help="Saídas restantes não utilizadas pela Bancada A"
        )
        
        # Configuração dos bicos B
        col_b1, col_b2 = st.columns(2)
        
        with col_b1:
            bank_b_flow = st.number_input(
                "Vazão por Bico B (lb/h)",
                min_value=10.0,
                max_value=2000.0,
                value=float(vehicle.bank_b_injector_flow or 80.0),
                step=5.0,
                key="bank_b_flow"
            )
        
        with col_b2:
            bank_b_count = st.number_input(
                "Quantidade de Bicos B",
                min_value=1,
                max_value=8,
                value=int(vehicle.bank_b_injector_count or len(bank_b_outputs or [2])),
                key="bank_b_count"
            )
        
        # Vazão total B
        total_flow_b = calculate_total_flow(bank_b_flow, bank_b_count)
        st.metric(
            "Vazão Total Bancada B",
            f"{total_flow_b:.1f} lb/h"
        )
        
        # Dead time B
        bank_b_dead_time = st.number_input(
            "Dead Time Bancada B (ms)",
            min_value=0.0,
            max_value=10.0,
            value=float(vehicle.bank_b_dead_time or 1.0),
            step=0.1,
            key="bank_b_dead_time"
        )
        
        # Salvar Bancada B
        if st.button(":material/save: Salvar Bancada B", key="save_bank_b"):
            self._save_bank_b_config(
                vehicle, bank_b_enabled, bank_b_mode, bank_b_outputs,
                bank_b_flow, bank_b_count, bank_b_dead_time
            )
    
    def _render_configuration_summary(self, vehicle: Vehicle) -> None:
        """Renderiza resumo da configuração atual."""
        
        st.markdown(
            '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">analytics</span>Resumo da Configuração</h3>',
            unsafe_allow_html=True
        )
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Saídas Bancada A",
                len(self._parse_outputs(vehicle.bank_a_outputs) or [])
            )
        
        with col2:
            st.metric(
                "Saídas Bancada B",
                len(self._parse_outputs(vehicle.bank_b_outputs) or []) if vehicle.bank_b_enabled else 0
            )
        
        with col3:
            total_a = calculate_total_flow(
                vehicle.bank_a_injector_flow or 0,
                vehicle.bank_a_injector_count or 0
            )
            total_b = calculate_total_flow(
                vehicle.bank_b_injector_flow or 0,
                vehicle.bank_b_injector_count or 0
            ) if vehicle.bank_b_enabled else 0
            
            st.metric(
                "Vazão Total Sistema",
                f"{total_a + total_b:.1f} lb/h"
            )
        
        with col4:
            # Verificar conflitos de saídas
            conflicts = self._check_output_conflicts(vehicle)
            st.metric(
                "Conflitos",
                len(conflicts),
                delta="OK" if len(conflicts) == 0 else "ERRO"
            )
        
        # Exibir conflitos se houver
        if conflicts:
            st.error(f"Conflitos detectados nas saídas: {', '.join(map(str, conflicts))}")
    
    def _render_action_buttons(self, vehicle: Vehicle) -> None:
        """Renderiza botões de ação."""
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(":material/content_copy: Duplicar Mapas", key="duplicate_maps"):
                self._duplicate_maps_for_banks(vehicle)
        
        with col2:
            if st.button(":material/sync: Sincronizar A→B", key="sync_a_to_b"):
                self._sync_bank_a_to_b(vehicle)
        
        with col3:
            if st.button(":material/refresh: Recalcular Vazões", key="recalculate"):
                self._recalculate_flows(vehicle)
        
        with col4:
            if st.button(":material/settings_backup_restore: Restaurar Padrão", key="restore_default"):
                self._restore_default_config(vehicle)
    
    # Métodos auxiliares
    def _load_vehicle_data(self) -> Optional[Vehicle]:
        """Carrega dados do veículo."""
        db = self.db.get_session()
        try:
            return db.query(Vehicle).filter(Vehicle.id == self.vehicle_id).first()
        finally:
            db.close()
    
    def _get_mode_index(self, mode: str) -> int:
        """Retorna índice do modo na lista."""
        modes = ["multiponto", "semissequencial", "sequencial"]
        try:
            return modes.index(mode)
        except ValueError:
            return 1  # Padrão: semissequencial
    
    def _parse_outputs(self, outputs_json: str) -> List[int]:
        """Parseia JSON de saídas."""
        if not outputs_json:
            return []
        try:
            return json.loads(outputs_json) if isinstance(outputs_json, str) else outputs_json
        except:
            return []
    
    def _check_output_conflicts(self, vehicle: Vehicle) -> List[int]:
        """Verifica conflitos entre saídas das bancadas."""
        outputs_a = set(self._parse_outputs(vehicle.bank_a_outputs) or [])
        outputs_b = set(self._parse_outputs(vehicle.bank_b_outputs) or [])
        
        if not vehicle.bank_b_enabled:
            return []
        
        return list(outputs_a.intersection(outputs_b))
    
    def _save_bank_a_config(self, vehicle: Vehicle, mode: str, outputs: List[int], 
                           flow: float, count: int, dead_time: float) -> None:
        """Salva configuração da Bancada A."""
        db = self.db.get_session()
        try:
            vehicle.bank_a_mode = mode
            vehicle.bank_a_outputs = json.dumps(outputs)
            vehicle.bank_a_injector_flow = flow
            vehicle.bank_a_injector_count = count
            vehicle.bank_a_total_flow = calculate_total_flow(flow, count)
            vehicle.bank_a_dead_time = dead_time
            
            db.commit()
            st.success("Configuração da Bancada A salva com sucesso!")
            
        except Exception as e:
            db.rollback()
            st.error(f"Erro ao salvar Bancada A: {str(e)}")
        finally:
            db.close()
    
    def _save_bank_b_config(self, vehicle: Vehicle, enabled: bool, mode: str, 
                           outputs: List[int], flow: float, count: int, dead_time: float) -> None:
        """Salva configuração da Bancada B."""
        db = self.db.get_session()
        try:
            vehicle.bank_b_enabled = enabled
            vehicle.bank_b_mode = mode
            vehicle.bank_b_outputs = json.dumps(outputs)
            vehicle.bank_b_injector_flow = flow
            vehicle.bank_b_injector_count = count
            vehicle.bank_b_total_flow = calculate_total_flow(flow, count)
            vehicle.bank_b_dead_time = dead_time
            
            db.commit()
            st.success("Configuração da Bancada B salva com sucesso!")
            
        except Exception as e:
            db.rollback()
            st.error(f"Erro ao salvar Bancada B: {str(e)}")
        finally:
            db.close()
```

### 2. Criar Utilitários de Cálculo

#### 2.1 Arquivo: src/utils/bank_calculations.py
```python
"""
Utilitários para cálculos relacionados a bancadas de injeção.
"""

from typing import Dict, List, Tuple
import math

def calculate_total_flow(flow_per_injector: float, injector_count: int) -> float:
    """
    Calcula vazão total da bancada.
    
    Args:
        flow_per_injector: Vazão por bico em lb/h
        injector_count: Quantidade de bicos
    
    Returns:
        Vazão total em lb/h
    """
    return flow_per_injector * injector_count

def calculate_duty_cycle(injection_time_ms: float, rpm: int, cylinders: int) -> float:
    """
    Calcula duty cycle dos injetores.
    
    Args:
        injection_time_ms: Tempo de injeção em ms
        rpm: RPM do motor
        cylinders: Número de cilindros
    
    Returns:
        Duty cycle em % (0-100)
    """
    if rpm <= 0:
        return 0.0
    
    # Tempo disponível por ciclo (4 tempos = 2 voltas)
    cycle_time_ms = (60.0 / rpm) * 1000.0 / 2.0
    
    # Para motores multiponto, divide por número de cilindros
    available_time_ms = cycle_time_ms / cylinders
    
    duty_cycle = (injection_time_ms / available_time_ms) * 100.0
    
    return min(duty_cycle, 100.0)

def validate_injector_flow(flow_lb_h: float, max_duty: float = 85.0) -> Tuple[bool, str]:
    """
    Valida se a vazão do injetor é adequada.
    
    Args:
        flow_lb_h: Vazão em lb/h
        max_duty: Duty cycle máximo recomendado
    
    Returns:
        Tuple com (válido, mensagem)
    """
    if flow_lb_h < 10:
        return False, "Vazão muito baixa (< 10 lb/h)"
    
    if flow_lb_h > 2000:
        return False, "Vazão muito alta (> 2000 lb/h)"
    
    return True, "Vazão adequada"

def calculate_fuel_pressure_compensation(base_pressure: float, actual_pressure: float) -> float:
    """
    Calcula fator de compensação por pressão de combustível.
    
    Args:
        base_pressure: Pressão base de calibração (bar)
        actual_pressure: Pressão atual do sistema (bar)
    
    Returns:
        Fator de compensação (multiplicador)
    """
    if base_pressure <= 0 or actual_pressure <= 0:
        return 1.0
    
    # A vazão varia com a raiz quadrada da pressão
    return math.sqrt(actual_pressure / base_pressure)

def estimate_power_per_bank(total_flow_lb_h: float, bsfc: float = 0.5) -> float:
    """
    Estima potência suportada por bancada.
    
    Args:
        total_flow_lb_h: Vazão total da bancada em lb/h
        bsfc: Consumo específico (lb/hp/h) - padrão 0.5
    
    Returns:
        Potência estimada em HP
    """
    return total_flow_lb_h / bsfc

def check_bank_balance(bank_a_flow: float, bank_b_flow: float, tolerance: float = 0.1) -> Tuple[bool, str]:
    """
    Verifica balanceamento entre bancadas.
    
    Args:
        bank_a_flow: Vazão bancada A
        bank_b_flow: Vazão bancada B
        tolerance: Tolerância aceita (0.1 = 10%)
    
    Returns:
        Tuple com (balanceado, mensagem)
    """
    if bank_b_flow == 0:
        return True, "Apenas uma bancada ativa"
    
    difference = abs(bank_a_flow - bank_b_flow) / max(bank_a_flow, bank_b_flow)
    
    if difference <= tolerance:
        return True, "Bancadas balanceadas"
    else:
        return False, f"Desbalanceamento de {difference*100:.1f}%"

def recommend_injector_size(target_power_hp: float, cylinders: int, 
                          max_duty: float = 85.0, bsfc: float = 0.5) -> Dict:
    """
    Recomenda tamanho de injetor para potência alvo.
    
    Args:
        target_power_hp: Potência desejada
        cylinders: Número de cilindros
        max_duty: Duty cycle máximo
        bsfc: Consumo específico
    
    Returns:
        Dict com recomendações
    """
    # Fluxo necessário total
    total_flow_needed = target_power_hp * bsfc
    
    # Ajustar para duty cycle máximo
    total_flow_adjusted = total_flow_needed / (max_duty / 100.0)
    
    # Fluxo por injetor
    flow_per_injector = total_flow_adjusted / cylinders
    
    # Tamanhos comerciais comuns
    common_sizes = [19, 24, 30, 36, 42, 47, 55, 60, 72, 80, 96, 110, 120, 160, 200, 250, 300, 440, 550, 650, 750, 850, 1000, 1200, 1600, 2000]
    
    # Encontrar tamanho mais próximo (maior que necessário)
    recommended_size = min([size for size in common_sizes if size >= flow_per_injector], default=common_sizes[-1])
    
    return {
        "target_power": target_power_hp,
        "total_flow_needed": total_flow_needed,
        "total_flow_adjusted": total_flow_adjusted,
        "flow_per_injector_needed": flow_per_injector,
        "recommended_size": recommended_size,
        "actual_total_flow": recommended_size * cylinders,
        "safety_margin": ((recommended_size * cylinders * (max_duty / 100.0)) / total_flow_needed - 1) * 100
    }
```

### 3. Sistema de Duplicação de Mapas

#### 3.1 Arquivo: src/services/map_duplication.py
```python
"""
Serviço para duplicação e sincronização de mapas entre bancadas.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..data.fuel_maps_models import FuelMap, MapData2D, MapData3D
from ..data.models import Vehicle, get_database

class MapDuplicationService:
    """Serviço para gerenciar duplicação de mapas entre bancadas."""
    
    def __init__(self):
        self.db = get_database()
    
    def duplicate_maps_for_banks(self, vehicle_id: str) -> bool:
        """
        Cria mapas separados para bancadas A e B quando necessário.
        
        Args:
            vehicle_id: ID do veículo
        
        Returns:
            True se duplicação foi bem sucedida
        """
        db_session = self.db.get_session()
        try:
            vehicle = db_session.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
            if not vehicle:
                return False
            
            # Mapas que devem ser duplicados para A e B
            maps_to_duplicate = [
                'main_fuel_2d_map',     # Mapa principal MAP
                'main_fuel_3d',         # Mapa principal 3D
                'battery_voltage_compensation'  # Compensação tensão
            ]
            
            for map_type in maps_to_duplicate:
                self._duplicate_single_map(db_session, vehicle_id, map_type)
            
            db_session.commit()
            return True
            
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()
    
    def _duplicate_single_map(self, db_session: Session, vehicle_id: str, map_type: str) -> None:
        """Duplica um mapa específico para bancadas A e B."""
        
        # Buscar mapa original (sem bank_id ou com bank_id = A)
        original_map = db_session.query(FuelMap).filter(
            FuelMap.vehicle_id == vehicle_id,
            FuelMap.map_type == map_type
        ).filter(
            (FuelMap.bank_id == None) | (FuelMap.bank_id == 'A')
        ).first()
        
        if not original_map:
            # Criar mapa padrão se não existir
            original_map = self._create_default_map(db_session, vehicle_id, map_type, 'A')
        
        # Atualizar mapa original para bancada A
        original_map.bank_id = 'A'
        
        # Verificar se já existe mapa para bancada B
        existing_b = db_session.query(FuelMap).filter(
            FuelMap.vehicle_id == vehicle_id,
            FuelMap.map_type == map_type,
            FuelMap.bank_id == 'B'
        ).first()
        
        if not existing_b:
            # Criar cópia para bancada B
            map_b = FuelMap(
                vehicle_id=vehicle_id,
                map_type=map_type,
                bank_id='B',
                name=original_map.name.replace('A', 'B'),
                description=f"{original_map.description} - Bancada B",
                dimensions=original_map.dimensions,
                x_axis_type=original_map.x_axis_type,
                y_axis_type=original_map.y_axis_type,
                data_unit=original_map.data_unit,
                x_slots_total=original_map.x_slots_total,
                x_slots_active=original_map.x_slots_active,
                y_slots_total=original_map.y_slots_total,
                y_slots_active=original_map.y_slots_active
            )
            
            db_session.add(map_b)
            db_session.flush()  # Para obter o ID
            
            # Copiar dados do mapa
            self._copy_map_data(db_session, original_map.id, map_b.id)
    
    def _copy_map_data(self, db_session: Session, source_map_id: str, target_map_id: str) -> None:
        """Copia dados entre mapas."""
        
        # Copiar dados 2D se existirem
        source_2d = db_session.query(MapData2D).filter(MapData2D.map_id == source_map_id).first()
        if source_2d:
            target_2d = MapData2D(map_id=target_map_id)
            
            # Copiar todos os valores
            for i in range(32):
                value = getattr(source_2d, f'value_{i}', None)
                setattr(target_2d, f'value_{i}', value)
            
            db_session.add(target_2d)
        
        # Copiar dados 3D se existirem
        source_3d = db_session.query(MapData3D).filter(MapData3D.map_id == source_map_id).first()
        if source_3d:
            target_3d = MapData3D(map_id=target_map_id)
            
            # Copiar todos os valores da matriz
            for x in range(32):
                for y in range(32):
                    value = getattr(source_3d, f'value_{x}_{y}', None)
                    setattr(target_3d, f'value_{x}_{y}', value)
            
            db_session.add(target_3d)
    
    def sync_bank_a_to_b(self, vehicle_id: str, map_type: str) -> bool:
        """
        Sincroniza dados da bancada A para B.
        
        Args:
            vehicle_id: ID do veículo
            map_type: Tipo do mapa a sincronizar
        
        Returns:
            True se sincronização foi bem sucedida
        """
        db_session = self.db.get_session()
        try:
            # Buscar mapas A e B
            map_a = db_session.query(FuelMap).filter(
                FuelMap.vehicle_id == vehicle_id,
                FuelMap.map_type == map_type,
                FuelMap.bank_id == 'A'
            ).first()
            
            map_b = db_session.query(FuelMap).filter(
                FuelMap.vehicle_id == vehicle_id,
                FuelMap.map_type == map_type,
                FuelMap.bank_id == 'B'
            ).first()
            
            if not map_a or not map_b:
                return False
            
            # Sincronizar configurações do mapa
            map_b.x_slots_active = map_a.x_slots_active
            map_b.y_slots_active = map_a.y_slots_active
            
            # Copiar dados
            self._copy_map_data(db_session, map_a.id, map_b.id)
            
            db_session.commit()
            return True
            
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()
    
    def get_bank_maps(self, vehicle_id: str, bank_id: str) -> List[FuelMap]:
        """
        Retorna todos os mapas de uma bancada específica.
        
        Args:
            vehicle_id: ID do veículo
            bank_id: 'A' ou 'B'
        
        Returns:
            Lista de mapas da bancada
        """
        db_session = self.db.get_session()
        try:
            return db_session.query(FuelMap).filter(
                FuelMap.vehicle_id == vehicle_id,
                FuelMap.bank_id == bank_id,
                FuelMap.is_active == True
            ).all()
        finally:
            db_session.close()
```

### 4. Interface de Seleção de Bancada

#### 4.1 Arquivo: src/components/bank_selector.py
```python
"""
Componente para seleção de bancada ativa na interface.
"""

import streamlit as st
from typing import Optional

class BankSelector:
    """Seletor de bancada para interface de mapas."""
    
    @staticmethod
    def render_bank_selector(vehicle_has_bank_b: bool, key_prefix: str = "") -> str:
        """
        Renderiza seletor de bancada.
        
        Args:
            vehicle_has_bank_b: Se veículo tem bancada B habilitada
            key_prefix: Prefixo para keys únicos
        
        Returns:
            Bancada selecionada ('A' ou 'B')
        """
        if not vehicle_has_bank_b:
            st.info("Veículo configurado apenas com Bancada A")
            return 'A'
        
        st.markdown(
            '<h4><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">electrical_services</span>Selecionar Bancada</h4>',
            unsafe_allow_html=True
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            bank_a_selected = st.button(
                ":material/electrical_services: Bancada A (Principal)",
                key=f"{key_prefix}_bank_a",
                use_container_width=True,
                type="primary" if st.session_state.get(f"{key_prefix}_selected_bank", 'A') == 'A' else "secondary"
            )
        
        with col2:
            bank_b_selected = st.button(
                ":material/power: Bancada B (Auxiliar)",
                key=f"{key_prefix}_bank_b",
                use_container_width=True,
                type="primary" if st.session_state.get(f"{key_prefix}_selected_bank", 'A') == 'B' else "secondary"
            )
        
        # Atualizar seleção
        if bank_a_selected:
            st.session_state[f"{key_prefix}_selected_bank"] = 'A'
        elif bank_b_selected:
            st.session_state[f"{key_prefix}_selected_bank"] = 'B'
        
        return st.session_state.get(f"{key_prefix}_selected_bank", 'A')
    
    @staticmethod
    def get_selected_bank(key_prefix: str = "") -> str:
        """Retorna bancada selecionada no session state."""
        return st.session_state.get(f"{key_prefix}_selected_bank", 'A')
    
    @staticmethod
    def set_selected_bank(bank_id: str, key_prefix: str = "") -> None:
        """Define bancada selecionada no session state."""
        st.session_state[f"{key_prefix}_selected_bank"] = bank_id
```

### 5. Página de Configuração de Bancadas

#### 5.1 Arquivo: src/ui/pages/bank_configuration.py
```python
"""
Página dedicada à configuração de bancadas de injeção.
"""

import streamlit as st
from typing import Optional

from ...components.bank_configurator import BankConfigurator
from ...data.models import Vehicle, get_database
from ...services.map_duplication import MapDuplicationService

def render_bank_configuration_page():
    """Renderiza página completa de configuração de bancadas."""
    
    st.markdown(
        '<div class="main-header">'
        '<span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">settings</span>'
        'Configuração de Bancadas de Injeção'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Seleção de veículo
    vehicle_id = _render_vehicle_selector()
    if not vehicle_id:
        st.warning("Selecione um veículo para configurar as bancadas")
        return
    
    # Tabs de configuração
    tab1, tab2, tab3, tab4 = st.tabs([
        "Configuração Básica",
        "Mapas por Bancada", 
        "Sincronização",
        "Diagnósticos"
    ])
    
    with tab1:
        _render_basic_configuration_tab(vehicle_id)
    
    with tab2:
        _render_maps_per_bank_tab(vehicle_id)
    
    with tab3:
        _render_synchronization_tab(vehicle_id)
    
    with tab4:
        _render_diagnostics_tab(vehicle_id)

def _render_vehicle_selector() -> Optional[str]:
    """Renderiza seletor de veículo."""
    db = get_database()
    db_session = db.get_session()
    
    try:
        vehicles = db_session.query(Vehicle).filter(Vehicle.is_active == True).all()
        
        if not vehicles:
            st.error("Nenhum veículo ativo encontrado")
            return None
        
        vehicle_options = {
            f"{v.display_name} - {v.technical_summary}": v.id 
            for v in vehicles
        }
        
        selected_display = st.selectbox(
            "Selecionar Veículo",
            options=list(vehicle_options.keys()),
            key="bank_config_vehicle_selector"
        )
        
        return vehicle_options.get(selected_display)
        
    finally:
        db_session.close()

def _render_basic_configuration_tab(vehicle_id: str):
    """Tab de configuração básica das bancadas."""
    configurator = BankConfigurator(vehicle_id)
    configurator.render_bank_config()

def _render_maps_per_bank_tab(vehicle_id: str):
    """Tab mostrando mapas por bancada."""
    st.markdown(
        '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">map</span>Mapas por Bancada</h3>',
        unsafe_allow_html=True
    )
    
    duplication_service = MapDuplicationService()
    
    # Botão para criar mapas duplicados
    if st.button(":material/content_copy: Criar Mapas Duplicados"):
        try:
            success = duplication_service.duplicate_maps_for_banks(vehicle_id)
            if success:
                st.success("Mapas duplicados criados com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao criar mapas duplicados")
        except Exception as e:
            st.error(f"Erro: {str(e)}")
    
    # Exibir mapas existentes
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Bancada A")
        maps_a = duplication_service.get_bank_maps(vehicle_id, 'A')
        for map_obj in maps_a:
            st.info(f"{map_obj.name} - {map_obj.map_type}")
    
    with col2:
        st.markdown("#### Bancada B")
        maps_b = duplication_service.get_bank_maps(vehicle_id, 'B')
        for map_obj in maps_b:
            st.info(f"{map_obj.name} - {map_obj.map_type}")

def _render_synchronization_tab(vehicle_id: str):
    """Tab de sincronização entre bancadas."""
    st.markdown(
        '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">sync</span>Sincronização de Mapas</h3>',
        unsafe_allow_html=True
    )
    
    duplication_service = MapDuplicationService()
    
    # Mapas disponíveis para sincronização
    sync_options = [
        "main_fuel_2d_map",
        "main_fuel_3d", 
        "battery_voltage_compensation"
    ]
    
    selected_map = st.selectbox(
        "Mapa para Sincronizar",
        options=sync_options,
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(":material/east: Sincronizar A → B"):
            try:
                success = duplication_service.sync_bank_a_to_b(vehicle_id, selected_map)
                if success:
                    st.success(f"Mapa {selected_map} sincronizado A → B")
                else:
                    st.error("Erro na sincronização")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    with col2:
        if st.button(":material/west: Sincronizar B → A"):
            st.warning("Funcionalidade em desenvolvimento")

def _render_diagnostics_tab(vehicle_id: str):
    """Tab de diagnósticos das bancadas."""
    st.markdown(
        '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">health_and_safety</span>Diagnósticos</h3>',
        unsafe_allow_html=True
    )
    
    # Carregar dados do veículo
    db = get_database()
    db_session = db.get_session()
    
    try:
        vehicle = db_session.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            st.error("Veículo não encontrado")
            return
        
        # Diagnósticos automáticos
        diagnostics = _run_bank_diagnostics(vehicle)
        
        for diagnostic in diagnostics:
            if diagnostic["status"] == "OK":
                st.success(f"✓ {diagnostic['test']}: {diagnostic['message']}")
            elif diagnostic["status"] == "WARNING":
                st.warning(f"⚠ {diagnostic['test']}: {diagnostic['message']}")
            else:
                st.error(f"✗ {diagnostic['test']}: {diagnostic['message']}")
                
    finally:
        db_session.close()

def _run_bank_diagnostics(vehicle: Vehicle) -> List[Dict]:
    """Executa diagnósticos das bancadas."""
    from ...utils.bank_calculations import check_bank_balance, validate_injector_flow
    import json
    
    diagnostics = []
    
    # Verificar configuração básica
    if not vehicle.bank_a_enabled:
        diagnostics.append({
            "test": "Bancada A",
            "status": "ERROR", 
            "message": "Bancada A deve estar sempre habilitada"
        })
    else:
        diagnostics.append({
            "test": "Bancada A",
            "status": "OK",
            "message": "Bancada A configurada corretamente"
        })
    
    # Verificar conflitos de saídas
    outputs_a = json.loads(vehicle.bank_a_outputs or "[]")
    outputs_b = json.loads(vehicle.bank_b_outputs or "[]") if vehicle.bank_b_enabled else []
    
    conflicts = set(outputs_a).intersection(set(outputs_b))
    if conflicts:
        diagnostics.append({
            "test": "Conflito de Saídas",
            "status": "ERROR",
            "message": f"Saídas em conflito: {list(conflicts)}"
        })
    else:
        diagnostics.append({
            "test": "Conflito de Saídas",
            "status": "OK", 
            "message": "Sem conflitos detectados"
        })
    
    # Verificar balanceamento
    if vehicle.bank_b_enabled:
        flow_a = vehicle.bank_a_total_flow or 0
        flow_b = vehicle.bank_b_total_flow or 0
        
        balanced, message = check_bank_balance(flow_a, flow_b)
        diagnostics.append({
            "test": "Balanceamento",
            "status": "OK" if balanced else "WARNING",
            "message": message
        })
    
    # Verificar vazões
    flow_a_valid, msg_a = validate_injector_flow(vehicle.bank_a_injector_flow or 0)
    diagnostics.append({
        "test": "Vazão Bancada A",
        "status": "OK" if flow_a_valid else "WARNING",
        "message": msg_a
    })
    
    if vehicle.bank_b_enabled:
        flow_b_valid, msg_b = validate_injector_flow(vehicle.bank_b_injector_flow or 0)
        diagnostics.append({
            "test": "Vazão Bancada B", 
            "status": "OK" if flow_b_valid else "WARNING",
            "message": msg_b
        })
    
    return diagnostics

# Registrar página no sistema de navegação
if __name__ == "__main__":
    render_bank_configuration_page()
```

## Saída Esperada

### 1. Componente BankConfigurator
- Interface completa de configuração das bancadas A/B
- Validações em tempo real
- Cálculos automáticos de vazão total
- Detecção de conflitos de saídas

### 2. Utilitários de Cálculo
- Funções para cálculo de vazão total
- Duty cycle dos injetores
- Recomendações de tamanho de injetor
- Verificação de balanceamento

### 3. Sistema de Duplicação
- Criação automática de mapas para ambas bancadas
- Sincronização A → B
- Gerenciamento de dados duplicados

### 4. Interface Integrada
- Página dedicada à configuração
- Tabs organizadas por funcionalidade
- Diagnósticos automáticos
- Seleção de bancada ativa

### 5. Validações
- Verificação de conflitos
- Balanceamento entre bancadas
- Limites de vazão e duty cycle

## Validações Finais

### Checklist A04-STREAMLIT-PROFESSIONAL:
- [ ] ZERO emojis em toda interface
- [ ] Material Icons em TODOS os headers
- [ ] Material Icons em TODOS os botões
- [ ] Interface 100% em português
- [ ] CSS adaptativo sem !important
- [ ] Sem decorações infantis

### Checklist Funcional:
- [ ] Configuração completa de bancadas A/B
- [ ] Cálculos de vazão automáticos
- [ ] Duplicação de mapas funcionando
- [ ] Sincronização entre bancadas
- [ ] Validações e diagnósticos
- [ ] Interface integrada ao sistema

Este agente implementa o sistema completo de configuração e gerenciamento de bancadas A/B, preparando a base para o agente de interface de mapas.