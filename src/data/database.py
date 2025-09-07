"""
Database interface and management for FuelTech data.

Provides high-level database operations, data import/export,
and session management for SQLite backend.

Author: A02-DATA-PANDAS Agent
Created: 2025-01-02
"""

import hashlib
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from sqlalchemy import or_
from sqlalchemy.sql import func

from ..utils.logging_config import get_logger
from .csv_parser import CSVParser
from .models import DatabaseManager as BaseDBManager
from .models import DataQualityCheck, DataSession, FuelTechCoreData, FuelTechExtendedData, Vehicle
from .normalizer import normalize_fueltech_data
from .quality import assess_fueltech_data_quality
from .validators import validate_fueltech_data

logger = get_logger(__name__)


class DatabaseError(Exception):
    """Exception raised during database operations."""


class DataImportError(Exception):
    """Exception raised during data import."""


class FuelTechDatabase:
    """
    High-level database interface for FuelTech data management.

    Features:
    - Session management
    - Data import with validation
    - Query interface
    - Export capabilities
    - Data quality tracking
    """

    def __init__(self, db_path: str = "data/fueltech_data.db", create_tables: bool = True):
        """
        Initialize FuelTech database.

        Args:
            db_path: Path to SQLite database file
            create_tables: Whether to create tables if they don't exist
        """
        self.db_path = Path(db_path)
        self.database_url = f"sqlite:///{self.db_path.absolute()}"

        # Initialize base database manager
        self.db_manager = BaseDBManager(self.database_url)

        if create_tables:
            self.initialize_database()

    def initialize_database(self) -> None:
        """Initialize database and create all tables."""
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Initialize database
            self.db_manager.init_database()

            logger.info(f"Database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise DatabaseError(f"Failed to initialize database: {str(e)}")

    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.db_manager.get_session()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()

    def calculate_file_hash(self, file_path: Union[str, Path]) -> str:
        """Calculate SHA-256 hash of file for deduplication."""
        file_path = Path(file_path)

        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    def import_csv_file(
        self,
        file_path: Union[str, Path],
        session_name: Optional[str] = None,
        force_reimport: bool = False,
        validate_data: bool = True,
        normalize_data: bool = True,
        assess_quality: bool = True,
    ) -> Dict[str, Any]:
        """
        Import CSV file into database with full processing pipeline.

        Args:
            file_path: Path to CSV file
            session_name: Custom session name (default: filename)
            force_reimport: Force reimport even if file already exists
            validate_data: Validate data before import
            normalize_data: Normalize data during import
            assess_quality: Assess data quality during import

        Returns:
            Dictionary with import results and statistics
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise DataImportError(f"File not found: {file_path}")

        # Calculate file hash for deduplication
        file_hash = self.calculate_file_hash(file_path)

        # Check if file already imported
        existing_session = self.db_manager.get_session_by_hash(file_hash)
        if existing_session:
            if not force_reimport:
                logger.info(f"File already imported as session {existing_session.id}")
                return {
                    "status": "skipped",
                    "reason": "file_already_imported",
                    "session_id": existing_session.id,
                    "session_name": existing_session.session_name,
                }
            else:
                # Delete existing session and reimport
                logger.info(f"Force reimport: Deleting existing session {existing_session.id}")
                deleted = self.delete_session(existing_session.id, confirm=True)
                if deleted:
                    logger.info("Existing session deleted, proceeding with reimport")
                else:
                    raise DataImportError("Failed to delete existing session for force reimport")

        logger.info(f"Starting import of {file_path.name}")

        import_results = {
            "status": "processing",
            "file_path": str(file_path),
            "file_hash": file_hash,
            "import_timestamp": datetime.now(),
            "steps_completed": [],
            "errors": [],
            "warnings": [],
        }

        try:
            # Step 1: Parse CSV
            logger.info("Step 1: Parsing CSV file")
            parser = CSVParser()
            df = parser.parse_csv(file_path, validate_types=True, chunk_processing=False)
            file_info = parser.get_file_info(file_path)

            import_results["steps_completed"].append("csv_parsing")
            import_results["format_version"] = parser.detected_version
            import_results["field_count"] = len(df.columns)
            import_results["total_records"] = len(df)

            # Step 2: Data validation
            validation_results = None
            if validate_data:
                logger.info("Step 2: Validating data")
                validation_results = validate_fueltech_data(df, parser.detected_version)
                import_results["steps_completed"].append("data_validation")
                import_results["validation_results"] = validation_results

                if not validation_results["is_valid"]:
                    import_results["warnings"].append(
                        f"Validation issues found: {len(validation_results['errors'])} errors"
                    )

            # Step 3: Data normalization
            normalization_stats = None
            if normalize_data:
                logger.info("Step 3: Normalizing data")
                df, normalization_stats = normalize_fueltech_data(
                    df, outlier_method="clip", missing_method="interpolate"
                )
                import_results["steps_completed"].append("data_normalization")
                import_results["normalization_stats"] = normalization_stats

            # Step 4: Quality assessment
            quality_results = None
            if assess_quality:
                logger.info("Step 4: Assessing data quality")
                quality_results = assess_fueltech_data_quality(df)
                import_results["steps_completed"].append("quality_assessment")
                import_results["quality_results"] = quality_results

            # Step 5: Create database session record
            logger.info("Step 5: Creating session record")
            session_name = session_name or file_path.stem

            # Calculate session statistics
            duration = df["time"].max() - df["time"].min() if "time" in df.columns else None
            sample_rate = 1 / df["time"].diff().median() if "time" in df.columns else None

            session_record = self.db_manager.create_session_record(
                session_name=session_name,
                filename=file_path.name,
                file_hash=file_hash,
                format_version=parser.detected_version,
                field_count=len(df.columns),
                total_records=len(df),
                duration_seconds=duration,
                sample_rate_hz=sample_rate,
                file_size_mb=file_info.get("file_size_mb"),
                original_encoding=parser.encoding,
                quality_score=(quality_results.get("overall_score") if quality_results else None),
                validation_status=(
                    "valid" if validation_results and validation_results["is_valid"] else "invalid"
                ),
                import_status="processing",
                metadata_json={
                    "import_config": {
                        "validate_data": validate_data,
                        "normalize_data": normalize_data,
                        "assess_quality": assess_quality,
                    },
                    "file_info": file_info,
                    "processing_timestamp": datetime.now().isoformat(),
                },
            )

            import_results["session_id"] = session_record.id
            import_results["session_name"] = session_record.session_name
            import_results["steps_completed"].append("session_creation")

            # Step 6: Insert data records
            logger.info("Step 6: Inserting data records")
            self._insert_data_records(df, session_record.id, parser.detected_version)
            import_results["steps_completed"].append("data_insertion")

            # Step 7: Insert quality check results
            if quality_results:
                logger.info("Step 7: Inserting quality check results")
                self._insert_quality_results(quality_results, session_record.id)
                import_results["steps_completed"].append("quality_results_insertion")

            # Step 8: Update session status
            with self.get_session() as db:
                db.query(DataSession).filter(DataSession.id == session_record.id).update(
                    {"import_status": "completed"}
                )
                db.commit()

            import_results["status"] = "completed"
            import_results["steps_completed"].append("status_update")

            logger.info(f"Import completed successfully for session {session_record.id}")

        except Exception as e:
            import_results["status"] = "failed"
            
            # Handle specific constraint errors
            error_msg = str(e)
            if "CHECK constraint failed: chk_g_accel_range" in error_msg:
                user_friendly_msg = (
                    "Erro: Valores de g_force_accel fora do range permitido (-7.0 a 7.0). "
                    "Verifique se os dados estão corretos ou se o arquivo foi modificado."
                )
                import_results["errors"].append(user_friendly_msg)
                import_results["error_type"] = "constraint_g_accel_range"
            elif "CHECK constraint failed: chk_g_lateral_range" in error_msg:
                user_friendly_msg = (
                    "Erro: Valores de g_force_lateral fora do range permitido (-7.0 a 7.0). "
                    "Verifique se os dados estão corretos ou se o arquivo foi modificado."
                )
                import_results["errors"].append(user_friendly_msg)
                import_results["error_type"] = "constraint_g_lateral_range"
            elif "CHECK constraint failed" in error_msg:
                import_results["errors"].append(f"Erro de validação de dados: {error_msg}")
                import_results["error_type"] = "constraint_violation"
            else:
                import_results["errors"].append(error_msg)
                import_results["error_type"] = "general_error"
            
            logger.error(f"Import failed: {error_msg}")

            # Update session status if record was created
            if "session_id" in import_results:
                try:
                    with self.get_session() as db:
                        db.query(DataSession).filter(
                            DataSession.id == import_results["session_id"]
                        ).update({"import_status": "failed"})
                        db.commit()
                except Exception:
                    pass  # Don't fail again if status update fails

            raise DataImportError(f"Import failed: {import_results['errors'][0]}")

        return import_results

    def _insert_data_records(self, df: pd.DataFrame, session_id: str, version: str) -> None:
        """Insert data records into appropriate tables."""
        # Prepare core data (always present)
        core_fields = [
            "time",
            "rpm",
            "tps",
            "throttle_position",
            "ignition_timing",
            "map",
            "closed_loop_target",
            "closed_loop_o2",
            "closed_loop_correction",
            "o2_general",
            "two_step",
            "ethanol_content",
            "launch_validated",
            "fuel_temp",
            "gear",
            "flow_bank_a",
            "injection_phase_angle",
            "injector_duty_a",
            "injection_time_a",
            "engine_temp",
            "air_temp",
            "oil_pressure",
            "fuel_pressure",
            "battery_voltage",
            "ignition_dwell",
            "fan1_enrichment",
            "fuel_level",
            "engine_sync",
            "decel_cutoff",
            "engine_cranking",
            "idle",
            "first_pulse_cranking",
            "accel_decel_injection",
            "active_adjustment",
            "fan1",
            "fan2",
            "fuel_pump",
        ]

        # Filter to existing columns
        available_core_fields = [f for f in core_fields if f in df.columns]
        core_data = df[available_core_fields].to_dict("records")

        # Insert core data
        self.db_manager.bulk_insert_core_data(session_id, core_data)

        # Insert extended data if version 2.0
        if version == "v2.0":
            extended_fields = [
                "time",
                "total_consumption",
                "average_consumption",
                "instant_consumption",
                "estimated_power",
                "estimated_torque",
                "total_distance",
                "range",
                "traction_speed",
                "acceleration_speed",
                "traction_control_slip",
                "traction_control_slip_rate",
                "delta_tps",
                "g_force_accel",
                "g_force_lateral",
                "pitch_angle",
                "pitch_rate",
                "roll_angle",
                "roll_rate",
                "heading",
                "acceleration_distance",
                "g_force_accel_raw",
                "g_force_lateral_raw",
                "accel_enrichment",
                "decel_enrichment",
                "injection_cutoff",
                "after_start_injection",
                "start_button_toggle",
            ]

            available_extended_fields = [f for f in extended_fields if f in df.columns]
            if available_extended_fields:
                extended_data = df[available_extended_fields].to_dict("records")
                self.db_manager.bulk_insert_extended_data(session_id, extended_data)

    def _insert_quality_results(self, quality_results: Dict[str, Any], session_id: str) -> None:
        """Insert quality assessment results."""
        with self.get_session() as db:
            for result in quality_results["detailed_results"]:
                quality_check = DataQualityCheck(
                    session_id=session_id,
                    check_type=result["check_name"],
                    status=result["status"],
                    severity=result["severity"],
                    message=result["message"],
                    error_percentage=result["error_percentage"],
                    details_json=result["details"],
                )
                db.add(quality_check)

            db.commit()

    def get_sessions(self) -> List[Dict[str, Any]]:
        """Get all data sessions with summary information."""
        return self.db_manager.get_sessions_summary()

    def get_session_data(
        self,
        session_id: str,
        include_extended: bool = True,
        time_range: Optional[Tuple[float, float]] = None,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Get data for a specific session.

        Args:
            session_id: Session ID
            include_extended: Include extended data fields
            time_range: Optional time range (start, end)
            columns: Specific columns to retrieve

        Returns:
            DataFrame with session data
        """
        with self.get_session() as db:
            # Build query for core data
            query = db.query(FuelTechCoreData).filter(FuelTechCoreData.session_id == session_id)

            if time_range:
                query = query.filter(
                    FuelTechCoreData.time >= time_range[0],
                    FuelTechCoreData.time <= time_range[1],
                )

            # Convert to DataFrame
            core_data = pd.read_sql(query.statement, db.bind)

            if include_extended:
                # Get extended data
                ext_query = db.query(FuelTechExtendedData).filter(
                    FuelTechExtendedData.session_id == session_id
                )

                if time_range:
                    ext_query = ext_query.filter(
                        FuelTechExtendedData.time >= time_range[0],
                        FuelTechExtendedData.time <= time_range[1],
                    )

                extended_data = pd.read_sql(ext_query.statement, db.bind)

                if not extended_data.empty:
                    # Merge on time
                    merged_data = pd.merge(
                        core_data,
                        extended_data,
                        on="time",
                        how="left",
                        suffixes=("", "_ext"),
                    )
                    core_data = merged_data

            # Filter columns if specified
            if columns:
                available_columns = [col for col in columns if col in core_data.columns]
                core_data = core_data[available_columns]

            return core_data

    def get_session_quality(self, session_id: str) -> Dict[str, Any]:
        """Get quality assessment results for a session."""
        with self.get_session() as db:
            quality_checks = (
                db.query(DataQualityCheck).filter(DataQualityCheck.session_id == session_id).all()
            )

            if not quality_checks:
                return {"message": "No quality assessment available"}

            results = {"session_id": session_id, "checks": []}

            for check in quality_checks:
                results["checks"].append(
                    {
                        "check_type": check.check_type,
                        "status": check.status,
                        "severity": check.severity,
                        "message": check.message,
                        "error_percentage": check.error_percentage,
                        "details": check.details_json,
                        "timestamp": check.check_timestamp,
                    }
                )

            return results

    def export_session_data(
        self,
        session_id: str,
        output_path: Union[str, Path],
        format: str = "csv",
        include_extended: bool = True,
    ) -> None:
        """
        Export session data to file.

        Args:
            session_id: Session ID to export
            output_path: Output file path
            format: Export format ('csv', 'parquet', 'json')
            include_extended: Include extended data fields
        """
        data = self.get_session_data(session_id, include_extended=include_extended)
        output_path = Path(output_path)

        if format.lower() == "csv":
            data.to_csv(output_path, index=False)
        elif format.lower() == "parquet":
            data.to_parquet(output_path, index=False)
        elif format.lower() == "json":
            data.to_json(output_path, orient="records", indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Exported session {session_id} to {output_path}")

    def delete_session(self, session_id: str, confirm: bool = False) -> bool:
        """
        Delete a session and all its data.

        Args:
            session_id: Session ID to delete
            confirm: Confirmation flag (safety measure)

        Returns:
            True if deleted, False if not found or not confirmed
        """
        if not confirm:
            logger.warning("Delete operation requires confirmation")
            return False

        with self.get_session() as db:
            session_record = db.query(DataSession).filter(DataSession.id == session_id).first()

            if not session_record:
                logger.warning(f"Session {session_id} not found")
                return False

            # Delete will cascade to related data
            db.delete(session_record)
            db.commit()

            logger.info(f"Deleted session {session_id}")
            return True

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics and information."""
        with self.get_session() as db:
            stats = {}

            # Session statistics
            total_sessions = db.query(DataSession).count()
            completed_sessions = (
                db.query(DataSession).filter(DataSession.import_status == "completed").count()
            )

            stats["sessions"] = {
                "total": total_sessions,
                "completed": completed_sessions,
                "failed": total_sessions - completed_sessions,
            }

            # Data statistics
            total_core_records = db.query(FuelTechCoreData).count()
            total_extended_records = db.query(FuelTechExtendedData).count()

            stats["records"] = {
                "core_data": total_core_records,
                "extended_data": total_extended_records,
                "total": total_core_records + total_extended_records,
            }

            # Quality statistics
            total_quality_checks = db.query(DataQualityCheck).count()
            passed_checks = (
                db.query(DataQualityCheck).filter(DataQualityCheck.status == "passed").count()
            )

            stats["quality"] = {
                "total_checks": total_quality_checks,
                "passed_checks": passed_checks,
                "pass_rate": (
                    (passed_checks / total_quality_checks * 100) if total_quality_checks > 0 else 0
                ),
            }

            # File statistics
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            stats["database"] = {
                "file_path": str(self.db_path),
                "size_mb": db_size / (1024 * 1024),
                "created": (
                    datetime.fromtimestamp(self.db_path.stat().st_ctime)
                    if self.db_path.exists()
                    else None
                ),
            }

            return stats


# Global database instance
_db_instance = None


def get_database(db_path: str = "data/fueltech_data.db") -> FuelTechDatabase:
    """Get the global database instance."""
    global _db_instance

    if _db_instance is None or str(_db_instance.db_path) != db_path:
        _db_instance = FuelTechDatabase(db_path)

    return _db_instance


# ========================================
# CRUD Operations para Vehicle
# ========================================

def get_db_session():
    """Helper para obter sessão do banco de dados usando a instância global."""
    return get_database().get_session()

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


if __name__ == "__main__":
    # Example usage
    import sys

    # Initialize database
    db = FuelTechDatabase("example_fueltech.db")

    print("Database initialized successfully")
    print(f"Database path: {db.db_path}")

    # Show stats
    stats = db.get_database_stats()
    print(f"Database stats: {stats}")

    # Example import (if CSV file provided)
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        print(f"Importing {csv_file}...")

        try:
            results = db.import_csv_file(csv_file)
            print(f"Import results: {results}")
        except Exception as e:
            print(f"Import failed: {e}")

    # Show sessions
    sessions = db.get_sessions()
    print(f"Sessions in database: {len(sessions)}")
    for session in sessions[:5]:  # Show first 5
        print(f"  - {session['name']} ({session['records']} records)")
