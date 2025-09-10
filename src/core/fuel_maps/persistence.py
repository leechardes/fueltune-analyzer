"""
Gerenciamento de persistência para mapas de combustível 3D.
Salva/carrega dados de mapas em arquivos JSON.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# from .models import Map3DData, MapConfig, VehicleData  # Removido imports não utilizados
from .defaults import ConfigManager

logger = logging.getLogger(__name__)

class PersistenceManager:
    """Gerenciador de persistência de mapas 3D."""
    
    def __init__(self, data_dir: str = "data/fuel_maps"):
        self.data_dir = Path(data_dir)
        self.config_manager = ConfigManager()
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Garante que o diretório de dados existe."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_filename(self, vehicle_id: str, map_type: str, bank_id: str) -> Path:
        """Gera nome do arquivo baseado nos parâmetros."""
        return self.data_dir / f"map_{vehicle_id}_{map_type}_{bank_id}.json"
    
    def save_3d_map_data(
        self,
        vehicle_id: str,
        map_type: str,
        bank_id: str,
        rpm_axis: List[float],
        map_axis: List[float],
        rpm_enabled: List[bool],
        map_enabled: List[bool],
        values_matrix: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Salva dados do mapa 3D em arquivo JSON persistente."""
        try:
            filename = self._get_filename(vehicle_id, map_type, bank_id)
            # Garantir tipo numpy para serialização consistente
            if not isinstance(values_matrix, np.ndarray):
                values_matrix = np.array(values_matrix)
            
            # Dados a salvar
            data = {
                "vehicle_id": vehicle_id,
                "map_type": map_type,
                "bank_id": bank_id,
                "rpm_axis": rpm_axis,
                "map_axis": map_axis,
                "rpm_enabled": rpm_enabled,
                "map_enabled": map_enabled,
                "values_matrix": values_matrix.tolist(),
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "metadata": metadata or {}
            }

            # Salvar no arquivo
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Mapa 3D salvo: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar mapa 3D: {e}")
            return False

    def load_3d_map_data(self, vehicle_id: str, map_type: str, bank_id: str) -> Optional[Dict]:
        """Carrega dados do mapa 3D de arquivo JSON persistente."""
        try:
            filename = self._get_filename(vehicle_id, map_type, bank_id)
            
            if filename.exists():
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                logger.debug(f"Mapa 3D carregado: {filename}")
                return data
            
            logger.debug(f"Arquivo não encontrado: {filename}")
            return None
        except Exception as e:
            logger.error(f"Erro ao carregar mapa 3D: {e}")
            return None

    def regenerate_ve_3d_map(self, vehicle_id: str, bank_id: str = "shared") -> bool:
        """Recria os valores do mapa VE 3D com base nos eixos salvos (como no mapa.html).

        Carrega o arquivo existente de `ve_3d_map`, lê `rpm_axis` e `map_axis`,
        calcula a matriz usando generate_ve_3d_matrix e salva de volta.
        """
        try:
            map_type = "ve_3d_map"
            current = self.load_3d_map_data(vehicle_id, map_type, bank_id)
            if not current:
                logger.error("VE 3D não encontrado para regenerar")
                return False
            rpm_axis = current.get("rpm_axis") or []
            map_axis = current.get("map_axis") or []
            from .calculations import generate_ve_3d_matrix
            values_matrix = generate_ve_3d_matrix(rpm_axis, map_axis)
            return self.save_3d_map_data(
                vehicle_id=vehicle_id,
                map_type=map_type,
                bank_id=bank_id,
                rpm_axis=rpm_axis,
                map_axis=map_axis,
                rpm_enabled=current.get("rpm_enabled") or [True] * len(rpm_axis),
                map_enabled=current.get("map_enabled") or [True] * len(map_axis),
                values_matrix=values_matrix,
                metadata={"created_from": "generated_function"}
            )
        except Exception as e:
            logger.error(f"Erro ao regenerar VE 3D: {e}")
            return False

    def regenerate_ve_table_3d_map(self, vehicle_id: str, bank_id: str = "shared") -> bool:
        """Recria os valores da Tabela de VE 3D (em %) com base nos eixos salvos."""
        try:
            map_type = "ve_table_3d_map"
            current = self.load_3d_map_data(vehicle_id, map_type, bank_id)
            if not current:
                logger.error("VE Table 3D não encontrado para regenerar")
                return False
            rpm_axis = current.get("rpm_axis") or []
            map_axis = current.get("map_axis") or []
            from .calculations import generate_ve_3d_matrix
            values_matrix = generate_ve_3d_matrix(rpm_axis, map_axis) * 100.0
            return self.save_3d_map_data(
                vehicle_id=vehicle_id,
                map_type=map_type,
                bank_id=bank_id,
                rpm_axis=rpm_axis,
                map_axis=map_axis,
                rpm_enabled=current.get("rpm_enabled") or [True] * len(rpm_axis),
                map_enabled=current.get("map_enabled") or [True] * len(map_axis),
                values_matrix=values_matrix,
                metadata={"created_from": "generated_function"}
            )
        except Exception as e:
            logger.error(f"Erro ao regenerar VE Table 3D: {e}")
            return False

    def create_default_map(
        self,
        vehicle_id: str,
        map_type: str,
        bank_id: str,
        vehicle_data: Dict[str, Any],
        grid_size: int = 32
    ) -> bool:
        """Cria um mapa 3D padrão para o veículo e tipo especificados."""
        try:
            config = self.config_manager.get_map_config(map_type)
            if not config:
                logger.error(f"Configuração não encontrada para tipo de mapa: {map_type}")
                return False

            # Obter configurações padrão - CORRIGIDO: usar map_type ao invés de selected_map_type
            rpm_axis = self.config_manager.get_map_config_values(
                map_type, "default_rpm_values", grid_size
            ) or [1000.0 + i * 300 for i in range(grid_size)]
            
            map_axis = self.config_manager.get_map_config_values(
                map_type, "default_map_values", grid_size
            ) or [20.0 + i * 5 for i in range(grid_size)]

            # Ajustar tamanhos se necessário
            rpm_axis = self._adjust_axis_size(rpm_axis, grid_size)
            map_axis = self._adjust_axis_size(map_axis, grid_size)

            # Obter configurações enable/disable inteligentes
            rpm_enabled, map_enabled = self.config_manager.get_default_3d_enabled_matrix(
                map_type, vehicle_data
            )

            # Ajustar tamanhos das matrizes enabled
            rpm_enabled = self._adjust_enabled_size(rpm_enabled, grid_size)
            map_enabled = self._adjust_enabled_size(map_enabled, grid_size)

            # Gerar valores padrão da matriz
            if map_type == "ve_3d_map":
                # Popular VE 3D como no mapa.html (curvas base e ganho), respeitando eixos escolhidos
                from .calculations import generate_ve_3d_matrix  # import local para evitar ciclos
                values_matrix = generate_ve_3d_matrix(
                    rpm_axis, [float(x) for x in map_axis]
                )
            elif map_type == "ve_table_3d_map":
                from .calculations import generate_ve_3d_matrix
                values_matrix = generate_ve_3d_matrix(rpm_axis, [float(x) for x in map_axis]) * 100.0
            else:
                values_matrix = self.config_manager.get_default_3d_map_values(
                    map_type, grid_size, rpm_enabled, map_enabled
                )

            # Salvar o mapa padrão
            return self.save_3d_map_data(
                vehicle_id=vehicle_id,
                map_type=map_type,
                bank_id=bank_id,
                rpm_axis=rpm_axis,
                map_axis=map_axis,
                rpm_enabled=rpm_enabled,
                map_enabled=map_enabled,
                values_matrix=values_matrix,
                metadata={
                    "created_from": "default"
                }
            )

        except Exception as e:
            logger.error(f"Erro ao criar mapa padrão: {e}")
            return False

    def _adjust_axis_size(self, axis: List[float], target_size: int) -> List[float]:
        """Ajusta tamanho do eixo para o tamanho desejado."""
        if len(axis) == target_size:
            return axis
        elif len(axis) > target_size:
            return axis[:target_size]
        else:
            # Preencher com valores interpolados
            if axis:
                last_value = axis[-1]
                step = (axis[-1] - axis[0]) / (len(axis) - 1) if len(axis) > 1 else 1.0
                extension = [last_value + step * (i + 1) for i in range(target_size - len(axis))]
                return axis + extension
            return [0.0] * target_size

    def _adjust_enabled_size(self, enabled: List[bool], target_size: int) -> List[bool]:
        """Ajusta tamanho da lista enabled para o tamanho desejado."""
        if len(enabled) == target_size:
            return enabled
        elif len(enabled) > target_size:
            return enabled[:target_size]
        else:
            return enabled + [False] * (target_size - len(enabled))

    def ensure_all_3d_maps_exist(self, vehicle_id: str, vehicle_data: Dict[str, Any]) -> bool:
        """Garante que todos os mapas 3D necessários existam para um veículo."""
        try:
            config = self.config_manager.get_config()
            maps_created = 0

            for map_type, map_config in config.items():
                # Determinar quais bancos criar baseado no tipo de mapa
                banks = ["A", "B"] if map_type == "main_fuel_3d_map" else ["shared"]
                
                for bank in banks:
                    filename = self._get_filename(vehicle_id, map_type, bank)
                    
                    if not filename.exists():
                        logger.info(f"Criando mapa padrão: {map_type} bank {bank} para veículo {vehicle_id}")
                        
                        if self.create_default_map(
                            vehicle_id=vehicle_id,
                            map_type=map_type,
                            bank_id=bank,
                            vehicle_data=vehicle_data,
                            grid_size=map_config.get("grid_size", 32)
                        ):
                            maps_created += 1
                        else:
                            logger.error(f"Falha ao criar mapa {map_type} bank {bank}")

            if maps_created > 0:
                logger.info(f"Criados {maps_created} mapas padrão para veículo {vehicle_id}")
            
            return True

        except Exception as e:
            logger.error(f"Erro ao garantir existência de mapas: {e}")
            return False

    def load_vehicles(self) -> List[Dict[str, Any]]:
        """Carrega lista de veículos disponíveis com fallback."""
        try:
            # Tentar importar função do database
            from src.data.vehicle_database import get_all_vehicles
            return get_all_vehicles()
        except ImportError:
            logger.warning("Database de veículos não disponível, usando dados dummy")
            return self.config_manager.get_dummy_vehicles()

    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados de um veículo específico por ID."""
        try:
            from src.data.vehicle_database import get_vehicle_by_id
            return get_vehicle_by_id(vehicle_id)
        except ImportError:
            # Fallback para dados dummy
            vehicles = self.config_manager.get_dummy_vehicles()
            for vehicle in vehicles:
                if vehicle["id"] == vehicle_id:
                    return vehicle
            return None

    def backup_map(self, vehicle_id: str, map_type: str, bank_id: str) -> bool:
        """Cria backup de um mapa específico."""
        try:
            original_file = self._get_filename(vehicle_id, map_type, bank_id)
            if not original_file.exists():
                return False
                
            backup_dir = self.data_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"map_{vehicle_id}_{map_type}_{bank_id}_backup_{timestamp}.json"
            
            # Copiar arquivo
            with open(original_file, "r", encoding="utf-8") as src:
                data = json.load(src)
            
            with open(backup_file, "w", encoding="utf-8") as dst:
                json.dump(data, dst, indent=2, ensure_ascii=False)
            
            logger.info(f"Backup criado: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            return False

    def list_map_files(self, vehicle_id: Optional[str] = None) -> List[Path]:
        """Lista arquivos de mapas disponíveis."""
        pattern = f"map_{vehicle_id}_*.json" if vehicle_id else "map_*.json"
        return list(self.data_dir.glob(pattern))

    def delete_map(self, vehicle_id: str, map_type: str, bank_id: str, create_backup: bool = True) -> bool:
        """Remove um mapa específico (opcionalmente criando backup antes)."""
        try:
            if create_backup:
                self.backup_map(vehicle_id, map_type, bank_id)
            
            filename = self._get_filename(vehicle_id, map_type, bank_id)
            if filename.exists():
                filename.unlink()
                logger.info(f"Mapa removido: {filename}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao remover mapa: {e}")
            return False

    def save_2d_map_data(
        self,
        vehicle_id: str,
        map_type: str,
        bank_id: str,
        axis_values: List[float],
        values: List[float],
        enabled: List[bool],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Salva dados do mapa 2D em arquivo JSON persistente."""
        try:
            filename = self._get_filename(vehicle_id, map_type, bank_id)
            
            # Dados a salvar para mapa 2D
            data = {
                "vehicle_id": vehicle_id,
                "map_type": map_type,
                "bank_id": bank_id,
                "dimension": "2D",
                "axis_values": axis_values,
                "values": values,
                "enabled": enabled,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "metadata": metadata or {}
            }

            # Salvar no arquivo
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Mapa 2D salvo: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar mapa 2D: {e}")
            return False

    def load_2d_map_data(self, vehicle_id: str, map_type: str, bank_id: str) -> Optional[Dict]:
        """Carrega dados do mapa 2D de arquivo JSON persistente."""
        try:
            filename = self._get_filename(vehicle_id, map_type, bank_id)
            
            if filename.exists():
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Verificar se é um mapa 2D
                if data.get("dimension") == "2D":
                    logger.debug(f"Mapa 2D carregado: {filename}")
                    return data
                else:
                    logger.warning(f"Arquivo não é um mapa 2D: {filename}")
                    return None
            
            logger.debug(f"Arquivo 2D não encontrado: {filename}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao carregar mapa 2D: {e}")
            return None

    def create_default_2d_map(
        self,
        vehicle_id: str,
        map_type: str,
        bank_id: str,
        vehicle_data: Dict[str, Any],
        map_config: Dict[str, Any]
    ) -> bool:
        """Cria um mapa 2D padrão para o veículo e tipo especificados."""
        try:
            positions = map_config.get("positions", 32)
            
            # Obter valores padrão do eixo
            axis_values = map_config.get("default_axis_values", list(range(positions)))
            enabled = map_config.get("default_enabled", [True] * positions)
            
            # Ajustar tamanhos
            axis_values = self._adjust_2d_axis_size(axis_values, positions)
            enabled = self._adjust_enabled_size(enabled, positions)
            
            # Valores padrão baseados no tipo de mapa
            if "fuel" in map_type:
                default_value = 2.0  # ms
            elif "correction" in map_type or "compensation" in map_type:
                default_value = 0.0  # % correction
            elif "voltage" in map_type:
                default_value = 0.0  # ms correction
            else:
                default_value = 1.0
            
            values = [default_value] * positions
            
            # Salvar o mapa padrão
            return self.save_2d_map_data(
                vehicle_id=vehicle_id,
                map_type=map_type,
                bank_id=bank_id,
                axis_values=axis_values,
                values=values,
                enabled=enabled,
                metadata={
                    "created_from": "default_2d"
                }
            )

        except Exception as e:
            logger.error(f"Erro ao criar mapa 2D padrão: {e}")
            return False

    def _adjust_2d_axis_size(self, axis: List[float], target_size: int) -> List[float]:
        """Ajusta tamanho do eixo 2D para o tamanho desejado."""
        if len(axis) == target_size:
            return axis
        elif len(axis) > target_size:
            return axis[:target_size]
        else:
            # Preencher com valores crescentes
            if axis:
                last_value = axis[-1]
                if len(axis) > 1:
                    step = (axis[-1] - axis[0]) / (len(axis) - 1)
                else:
                    step = 1.0 if last_value >= 0 else -1.0
                extension = [last_value + step * (i + 1) for i in range(target_size - len(axis))]
                return axis + extension
            return [float(i) for i in range(target_size)]

    def ensure_all_maps_exist(self, vehicle_id: str, vehicle_data: Dict[str, Any]) -> bool:
        """Garante que todos os mapas (2D e 3D) necessários existam para um veículo."""
        try:
            config = self.config_manager.get_all_maps()
            maps_created = 0

            for map_type, map_config in config.items():
                dimension = map_config.get("dimension", "3D")
                
                # Determinar quais bancos criar baseado no tipo de mapa
                banks = ["A", "B"] if self.config_manager.has_bank_selection(map_type) else ["shared"]
                
                for bank in banks:
                    filename = self._get_filename(vehicle_id, map_type, bank)
                    
                    if not filename.exists():
                        logger.info(f"Criando mapa {dimension} padrão: {map_type} bank {bank} para veículo {vehicle_id}")
                        
                        success = False
                        if dimension == "3D":
                            success = self.create_default_map(
                                vehicle_id=vehicle_id,
                                map_type=map_type,
                                bank_id=bank,
                                vehicle_data=vehicle_data,
                                grid_size=map_config.get("grid_size", 32)
                            )
                        else:  # 2D
                            success = self.create_default_2d_map(
                                vehicle_id=vehicle_id,
                                map_type=map_type,
                                bank_id=bank,
                                vehicle_data=vehicle_data,
                                map_config=map_config
                            )
                        
                        if success:
                            maps_created += 1
                        else:
                            logger.error(f"Falha ao criar mapa {dimension} {map_type} bank {bank}")

            if maps_created > 0:
                logger.info(f"Criados {maps_created} mapas padrão para veículo {vehicle_id}")
            
            return True

        except Exception as e:
            logger.error(f"Erro ao garantir existência de mapas: {e}")
            return False

    def load_map_data(self, vehicle_id: str, map_type: str, bank_id: str) -> Optional[Dict]:
        """Carrega dados de mapa (detecta automaticamente se é 2D ou 3D)."""
        # Primeiro tenta carregar como qualquer tipo
        filename = self._get_filename(vehicle_id, map_type, bank_id)
        
        if not filename.exists():
            return None
        
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            dimension = data.get("dimension", "3D")  # Default 3D para compatibilidade
            logger.debug(f"Mapa {dimension} carregado: {filename}")
            return data
            
        except Exception as e:
            logger.error(f"Erro ao carregar mapa: {e}")
            return None

# Instância global do gerenciador de persistência
persistence_manager = PersistenceManager()

# Funções de conveniência para manter compatibilidade
def save_3d_map_data(*args, **kwargs) -> bool:
    """Compatibilidade: salva dados do mapa 3D."""
    return persistence_manager.save_3d_map_data(*args, **kwargs)

def load_3d_map_data(*args, **kwargs) -> Optional[Dict]:
    """Compatibilidade: carrega dados do mapa 3D."""
    return persistence_manager.load_3d_map_data(*args, **kwargs)

def ensure_all_3d_maps_exist(*args, **kwargs) -> bool:
    """Compatibilidade: garante existência de todos os mapas."""
    return persistence_manager.ensure_all_3d_maps_exist(*args, **kwargs)

def load_vehicles() -> List[Dict[str, Any]]:
    """Compatibilidade: carrega lista de veículos."""
    return persistence_manager.load_vehicles()

# Funções de compatibilidade para mapas 2D
def save_2d_map_data(*args, **kwargs) -> bool:
    """Compatibilidade: salva dados do mapa 2D."""
    return persistence_manager.save_2d_map_data(*args, **kwargs)

def load_2d_map_data(*args, **kwargs) -> Optional[Dict]:
    """Compatibilidade: carrega dados do mapa 2D."""
    return persistence_manager.load_2d_map_data(*args, **kwargs)

def create_default_2d_map(*args, **kwargs) -> bool:
    """Compatibilidade: cria mapa 2D padrão."""
    return persistence_manager.create_default_2d_map(*args, **kwargs)

def ensure_all_maps_exist(*args, **kwargs) -> bool:
    """Compatibilidade: garante existência de todos os mapas (2D e 3D)."""
    return persistence_manager.ensure_all_maps_exist(*args, **kwargs)

def load_map_data(*args, **kwargs) -> Optional[Dict]:
    """Compatibilidade: carrega dados de mapa (auto-detecta dimensão)."""
    return persistence_manager.load_map_data(*args, **kwargs)
