"""
Utilitários para trabalhar com mapas de injeção.
Funções para criação, validação e manipulação de mapas padrão.

Padrão: A04-STREAMLIT-PROFESSIONAL (ZERO emojis, Material Icons)
"""

import uuid
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from ..data.fuel_maps_models import (
    FuelMap, MapAxisData, MapData2D, MapData3D, 
    create_default_main_fuel_2d_map, create_default_rpm_compensation_map,
    create_default_temp_compensation_map, MapDataValidator
)
from ..data.models import get_database
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class FuelMapManager:
    """Gerenciador para operações com mapas de injeção."""
    
    def __init__(self):
        self.db = get_database()
        self.validator = MapDataValidator()
    
    def create_default_maps_for_vehicle(self, vehicle_id: str, bank_enabled_b: bool = False) -> Dict[str, Any]:
        """
        Cria conjunto completo de mapas padrão para um veículo.
        
        Args:
            vehicle_id: ID do veículo
            bank_enabled_b: Se bancada B está habilitada
            
        Returns:
            Resultado da criação com contadores de sucesso/erro
        """
        
        logger.info(f"Criando mapas padrão para veículo {vehicle_id}")
        
        results = {
            "success": 0,
            "errors": 0,
            "created_maps": [],
            "error_details": []
        }
        
        # Lista de mapas padrão a criar
        default_maps_config = [
            # Mapas principais (bancadas A/B)
            {
                "template": create_default_main_fuel_2d_map,
                "banks": ["A", "B"] if bank_enabled_b else ["A"],
                "shared": False
            },
            # Mapas de compensação (compartilhados)
            {
                "template": create_default_rpm_compensation_map,
                "banks": [None],
                "shared": True
            },
            {
                "template": create_default_temp_compensation_map,
                "banks": [None],
                "shared": True
            },
            # Mapas adicionais
            {
                "template": self._create_tps_compensation_map,
                "banks": [None],
                "shared": True
            },
            {
                "template": self._create_voltage_compensation_map,
                "banks": ["A", "B"] if bank_enabled_b else ["A"],
                "shared": False
            },
            {
                "template": self._create_cranking_pulse_map,
                "banks": [None],
                "shared": True
            },
        ]
        
        db_session = self.db.get_session()
        
        try:
            for map_config in default_maps_config:
                for bank_id in map_config["banks"]:
                    try:
                        # Gerar dados do template
                        map_template_data = map_config["template"](vehicle_id, bank_id)
                        
                        # Criar mapa no banco
                        map_id = self._create_map_from_template(
                            db_session, vehicle_id, map_template_data
                        )
                        
                        results["created_maps"].append({
                            "map_id": map_id,
                            "map_type": map_template_data["map_data"]["map_type"],
                            "bank_id": bank_id,
                            "name": map_template_data["map_data"]["name"]
                        })
                        results["success"] += 1
                        
                    except Exception as e:
                        error_msg = f"Erro criando mapa {map_config['template'].__name__} bancada {bank_id}: {str(e)}"
                        logger.error(error_msg)
                        results["error_details"].append(error_msg)
                        results["errors"] += 1
            
            db_session.commit()
            logger.info(f"Mapas criados com sucesso: {results['success']}, Erros: {results['errors']}")
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Erro geral na criação de mapas: {str(e)}")
            results["error_details"].append(f"Erro geral: {str(e)}")
            
        finally:
            db_session.close()
        
        return results
    
    def _create_map_from_template(self, db_session, vehicle_id: str, template_data: Dict) -> str:
        """
        Cria um mapa no banco a partir de dados de template.
        
        Args:
            db_session: Sessão do banco de dados
            vehicle_id: ID do veículo
            template_data: Dados do template
            
        Returns:
            ID do mapa criado
        """
        
        map_info = template_data["map_data"]
        
        # Criar registro do mapa
        fuel_map = FuelMap(
            vehicle_id=vehicle_id,
            map_type=map_info["map_type"],
            bank_id=map_info.get("bank_id"),
            name=map_info["name"],
            description=map_info.get("description", ""),
            dimensions=map_info["dimensions"],
            x_axis_type=map_info["x_axis_type"],
            y_axis_type=map_info.get("y_axis_type"),
            data_unit=map_info["data_unit"],
            x_slots_active=map_info.get("x_slots_active", 0),
            y_slots_active=map_info.get("y_slots_active", 0)
        )
        
        db_session.add(fuel_map)
        db_session.flush()  # Para obter o ID
        
        # Criar dados dos eixos
        if "axis_data" in template_data:
            for axis_type, axis_info in template_data["axis_data"].items():
                axis_data = MapAxisData(
                    map_id=fuel_map.id,
                    axis_type=axis_type,
                    data_type=axis_info["data_type"],
                    active_slots=axis_info["active_slots"]
                )
                
                # Definir valores dos slots
                for i, value in enumerate(axis_info["values"]):
                    if i < 32:  # Máximo 32 slots
                        setattr(axis_data, f'slot_{i}', value)
                
                db_session.add(axis_data)
        
        # Criar dados dos valores
        if fuel_map.dimensions == 1:  # 2D
            values_2d = MapData2D(map_id=fuel_map.id)
            
            if "values_data" in template_data:
                for i, value in enumerate(template_data["values_data"]):
                    if i < 32:
                        setattr(values_2d, f'value_{i}', value)
            
            db_session.add(values_2d)
            
        elif fuel_map.dimensions == 2:  # 3D
            values_3d = MapData3D(map_id=fuel_map.id)
            
            if "values_data" in template_data:
                # template_data["values_data"] deve ser uma matriz
                matrix = template_data["values_data"]
                for x in range(min(len(matrix), 32)):
                    for y in range(min(len(matrix[x]), 32)):
                        if hasattr(values_3d, f'value_{x}_{y}'):
                            setattr(values_3d, f'value_{x}_{y}', matrix[x][y])
            
            db_session.add(values_3d)
        
        return fuel_map.id
    
    def _create_tps_compensation_map(self, vehicle_id: str, bank_id: str = None) -> Dict[str, Any]:
        """Cria dados padrão para mapa de compensação por TPS."""
        
        # TPS values (11 pontos ativos de 20 slots)
        tps_values = [0.00, 10.00, 20.00, 30.00, 40.00, 50.00, 
                      60.00, 70.00, 80.00, 90.00, 100.00]
        
        # Valores de compensação (empobrecimento em carga baixa)
        compensation_values = [-5.0, -4.4, -3.8, -3.1, -2.5, -1.9, 
                              -1.3, -0.6, 0.0, 0.0, 0.0]
        
        return {
            "map_data": {
                "map_type": "tps_compensation",
                "bank_id": bank_id,
                "name": "Compensação por TPS",
                "description": "Compensação de combustível baseada na posição do acelerador",
                "dimensions": 1,
                "x_axis_type": "TPS",
                "data_unit": "%",
                "x_slots_active": 11,
            },
            "axis_data": {
                "X": {
                    "data_type": "TPS",
                    "active_slots": 11,
                    "values": tps_values
                }
            },
            "values_data": compensation_values
        }
    
    def _create_voltage_compensation_map(self, vehicle_id: str, bank_id: str = 'A') -> Dict[str, Any]:
        """Cria dados padrão para mapa de compensação por tensão de bateria."""
        
        # Tensão values (9 pontos ativos)
        voltage_values = [8.00, 9.00, 10.00, 11.00, 12.00, 13.00, 14.00, 15.00, 16.00]
        
        # Valores de compensação em ms (tempo adicional)
        compensation_values = [0.600, 0.500, 0.400, 0.300, 0.180, 0.050, -0.060, -0.150, -0.220]
        
        return {
            "map_data": {
                "map_type": "battery_voltage_compensation",
                "bank_id": bank_id,
                "name": f"Compensação por Tensão - Bancada {bank_id}",
                "description": "Compensação de tempo de injeção baseada na tensão da bateria",
                "dimensions": 1,
                "x_axis_type": "VOLTAGE",
                "data_unit": "ms",
                "x_slots_active": 9,
            },
            "axis_data": {
                "X": {
                    "data_type": "VOLTAGE",
                    "active_slots": 9,
                    "values": voltage_values
                }
            },
            "values_data": compensation_values
        }
    
    def _create_cranking_pulse_map(self, vehicle_id: str, bank_id: str = None) -> Dict[str, Any]:
        """Cria dados padrão para mapa de pulso de partida."""
        
        # Temperatura values (8 pontos ativos)
        temp_values = [-10, 0, 10, 20, 40, 60, 80, 100]
        
        # Valores de tempo de injeção para partida
        injection_values = [24.00, 24.00, 21.00, 18.00, 15.00, 9.00, 6.00, 6.00]
        
        return {
            "map_data": {
                "map_type": "cranking_pulse",
                "bank_id": bank_id,
                "name": "Pulso de Partida",
                "description": "Tempo de injeção durante a partida do motor",
                "dimensions": 1,
                "x_axis_type": "TEMP",
                "data_unit": "ms",
                "x_slots_active": 8,
            },
            "axis_data": {
                "X": {
                    "data_type": "TEMP",
                    "active_slots": 8,
                    "values": temp_values
                }
            },
            "values_data": injection_values
        }
    
    def duplicate_map_for_bank(self, source_map_id: str, target_bank_id: str) -> Optional[str]:
        """
        Duplica um mapa para outra bancada.
        
        Args:
            source_map_id: ID do mapa origem
            target_bank_id: Bancada de destino ('A' ou 'B')
            
        Returns:
            ID do novo mapa ou None se erro
        """
        
        db_session = self.db.get_session()
        
        try:
            # Carregar mapa origem
            source_map = db_session.query(FuelMap).filter(FuelMap.id == source_map_id).first()
            if not source_map:
                return None
            
            # Criar novo mapa
            new_map = FuelMap(
                vehicle_id=source_map.vehicle_id,
                map_type=source_map.map_type,
                bank_id=target_bank_id,
                name=source_map.name.replace(source_map.bank_id or 'A', target_bank_id),
                description=f"{source_map.description} - Bancada {target_bank_id}",
                dimensions=source_map.dimensions,
                x_axis_type=source_map.x_axis_type,
                y_axis_type=source_map.y_axis_type,
                data_unit=source_map.data_unit,
                x_slots_active=source_map.x_slots_active,
                y_slots_active=source_map.y_slots_active,
                x_slots_total=source_map.x_slots_total,
                y_slots_total=source_map.y_slots_total
            )
            
            db_session.add(new_map)
            db_session.flush()
            
            # Copiar dados dos eixos
            source_axes = db_session.query(MapAxisData).filter(MapAxisData.map_id == source_map_id).all()
            for source_axis in source_axes:
                new_axis = MapAxisData(
                    map_id=new_map.id,
                    axis_type=source_axis.axis_type,
                    data_type=source_axis.data_type,
                    active_slots=source_axis.active_slots,
                    min_value=source_axis.min_value,
                    max_value=source_axis.max_value
                )
                
                # Copiar valores dos slots
                for i in range(32):
                    value = getattr(source_axis, f'slot_{i}', None)
                    setattr(new_axis, f'slot_{i}', value)
                
                db_session.add(new_axis)
            
            # Copiar dados dos valores
            if source_map.dimensions == 1:  # 2D
                source_data = db_session.query(MapData2D).filter(MapData2D.map_id == source_map_id).first()
                if source_data:
                    new_data = MapData2D(map_id=new_map.id)
                    
                    for i in range(32):
                        value = getattr(source_data, f'value_{i}', None)
                        setattr(new_data, f'value_{i}', value)
                    
                    db_session.add(new_data)
            
            elif source_map.dimensions == 2:  # 3D
                source_data = db_session.query(MapData3D).filter(MapData3D.map_id == source_map_id).first()
                if source_data:
                    new_data = MapData3D(map_id=new_map.id)
                    
                    for x in range(32):
                        for y in range(32):
                            attr_name = f'value_{x}_{y}'
                            if hasattr(source_data, attr_name):
                                value = getattr(source_data, attr_name, None)
                                setattr(new_data, attr_name, value)
                    
                    db_session.add(new_data)
            
            db_session.commit()
            logger.info(f"Mapa duplicado com sucesso: {source_map_id} -> {new_map.id}")
            return new_map.id
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Erro ao duplicar mapa: {str(e)}")
            return None
            
        finally:
            db_session.close()
    
    def get_maps_summary_for_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        """
        Retorna resumo dos mapas de um veículo.
        
        Args:
            vehicle_id: ID do veículo
            
        Returns:
            Resumo com estatísticas dos mapas
        """
        
        db_session = self.db.get_session()
        
        try:
            maps = db_session.query(FuelMap).filter(
                FuelMap.vehicle_id == vehicle_id,
                FuelMap.is_active == True
            ).all()
            
            summary = {
                "total_maps": len(maps),
                "maps_by_type": {},
                "maps_by_bank": {"A": 0, "B": 0, "Shared": 0},
                "maps_2d": 0,
                "maps_3d": 0,
                "latest_modification": None
            }
            
            for map_obj in maps:
                # Contar por tipo
                map_type = map_obj.map_type
                if map_type not in summary["maps_by_type"]:
                    summary["maps_by_type"][map_type] = 0
                summary["maps_by_type"][map_type] += 1
                
                # Contar por bancada
                if map_obj.bank_id == 'A':
                    summary["maps_by_bank"]["A"] += 1
                elif map_obj.bank_id == 'B':
                    summary["maps_by_bank"]["B"] += 1
                else:
                    summary["maps_by_bank"]["Shared"] += 1
                
                # Contar por dimensão
                if map_obj.dimensions == 1:
                    summary["maps_2d"] += 1
                else:
                    summary["maps_3d"] += 1
                
                # Última modificação
                if not summary["latest_modification"] or map_obj.modified_at > summary["latest_modification"]:
                    summary["latest_modification"] = map_obj.modified_at
            
            return summary
            
        finally:
            db_session.close()
    
    def validate_map_data(self, map_id: str) -> List[Dict[str, str]]:
        """
        Valida dados de um mapa.
        
        Args:
            map_id: ID do mapa a validar
            
        Returns:
            Lista de validações com status e mensagens
        """
        
        validations = []
        db_session = self.db.get_session()
        
        try:
            fuel_map = db_session.query(FuelMap).filter(FuelMap.id == map_id).first()
            if not fuel_map:
                return [{"status": "ERROR", "message": "Mapa não encontrado"}]
            
            # Validar configuração básica
            if fuel_map.x_slots_active <= 0:
                validations.append({"status": "ERROR", "message": "Nenhum slot ativo no eixo X"})
            else:
                validations.append({"status": "OK", "message": f"Eixo X: {fuel_map.x_slots_active} slots ativos"})
            
            if fuel_map.dimensions == 2 and fuel_map.y_slots_active <= 0:
                validations.append({"status": "ERROR", "message": "Mapa 3D sem slots ativos no eixo Y"})
            elif fuel_map.dimensions == 2:
                validations.append({"status": "OK", "message": f"Eixo Y: {fuel_map.y_slots_active} slots ativos"})
            
            # Validar dados dos eixos
            axis_data = db_session.query(MapAxisData).filter(MapAxisData.map_id == map_id).all()
            
            for axis in axis_data:
                axis_values = [getattr(axis, f'slot_{i}', None) for i in range(axis.active_slots)]
                valid_values = [v for v in axis_values if v is not None]
                
                if len(valid_values) < 2:
                    validations.append({
                        "status": "ERROR", 
                        "message": f"Eixo {axis.axis_type}: menos de 2 valores válidos"
                    })
                else:
                    # Verificar ordem crescente
                    is_ordered = all(valid_values[i] <= valid_values[i+1] for i in range(len(valid_values)-1))
                    if is_ordered:
                        validations.append({
                            "status": "OK",
                            "message": f"Eixo {axis.axis_type}: valores em ordem correta"
                        })
                    else:
                        validations.append({
                            "status": "WARNING",
                            "message": f"Eixo {axis.axis_type}: valores fora de ordem"
                        })
            
            # Validar dados dos valores
            if fuel_map.dimensions == 1:
                data_2d = db_session.query(MapData2D).filter(MapData2D.map_id == map_id).first()
                if data_2d:
                    valid_count = sum(1 for i in range(fuel_map.x_slots_active) 
                                    if getattr(data_2d, f'value_{i}', None) is not None)
                    
                    if valid_count >= fuel_map.x_slots_active * 0.8:  # 80% dos valores
                        validations.append({"status": "OK", "message": f"Dados 2D: {valid_count} valores válidos"})
                    else:
                        validations.append({"status": "WARNING", "message": f"Dados 2D: apenas {valid_count} valores válidos"})
            
            return validations
            
        except Exception as e:
            return [{"status": "ERROR", "message": f"Erro na validação: {str(e)}"}]
            
        finally:
            db_session.close()


# Função global para facilitar uso
def create_default_vehicle_maps(vehicle_id: str, bank_b_enabled: bool = False) -> Dict[str, Any]:
    """
    Função conveniente para criar mapas padrão para um veículo.
    
    Args:
        vehicle_id: ID do veículo
        bank_b_enabled: Se bancada B está habilitada
        
    Returns:
        Resultado da criação
    """
    manager = FuelMapManager()
    return manager.create_default_maps_for_vehicle(vehicle_id, bank_b_enabled)