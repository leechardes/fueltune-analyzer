"""
Script simplificado de migração para o sistema de veículos.
"""

import os
import sys
import shutil
from datetime import datetime

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.database import get_database, create_vehicle, get_all_vehicles
from src.data.models import DataSession

def create_backup():
    """Cria backup do banco SQLite."""
    print("💾 Criando backup do banco de dados...")
    
    db_path = "data/fueltech_data.db"
    if not os.path.exists(db_path):
        print("⚠️ Banco de dados não encontrado, criando novo...")
        return True
    
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"fueltune_backup_{timestamp}.db")
    
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup criado: {backup_path}")
    return backup_path

def analyze_existing_data():
    """Analisa dados existentes."""
    print("🔍 Analisando dados existentes...")
    
    try:
        db = get_database()
        
        with db.get_session() as session:
            # Contar sessões
            session_count = session.query(DataSession).count()
            
            # Contar sessões sem veículo
            orphan_count = session.query(DataSession).filter(
                DataSession.vehicle_id.is_(None)
            ).count()
            
            print(f"📊 Total de Sessões: {session_count}")
            print(f"📊 Sessões Órfãs: {orphan_count}")
            
            return {
                'session_count': session_count,
                'orphan_count': orphan_count
            }
            
    except Exception as e:
        print(f"❌ Erro na análise: {str(e)}")
        return None

def create_default_vehicle():
    """Cria veículo padrão para migração."""
    print("🚗 Criando veículo padrão...")
    
    try:
        # Verificar se já existe
        vehicles = get_all_vehicles()
        for vehicle in vehicles:
            if vehicle.name == "Dados Migrados":
                print(f"ℹ️ Veículo padrão já existe: {vehicle.id}")
                return vehicle.id
        
        # Criar veículo padrão
        vehicle_data = {
            "name": "Dados Migrados",
            "nickname": "Sistema Anterior",
            "brand": "Não Especificado",
            "model": "Dados do Sistema Anterior",
            "engine_displacement": 2.0,
            "engine_cylinders": 4,
            "engine_configuration": "I4",
            "engine_aspiration": "Naturally Aspirated",
            "fuel_type": "Gasoline",
            "estimated_power": 200,
            "estimated_torque": 300,
            "max_rpm": 7000,
            "curb_weight": 1400,
            "drivetrain": "FWD",
            "transmission_type": "Manual",
            "notes": f"Veículo criado automaticamente durante a migração para o sistema de veículos. "
                    f"Agrupa todos os dados que existiam antes da implementação do cadastro de veículos. "
                    f"Migração executada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}."
        }
        
        vehicle_id = create_vehicle(vehicle_data)
        print(f"✅ Veículo padrão criado: {vehicle_id}")
        return vehicle_id
        
    except Exception as e:
        print(f"❌ Erro na criação do veículo padrão: {str(e)}")
        return None

def associate_orphan_sessions(vehicle_id):
    """Associa sessões órfãs ao veículo padrão."""
    print("🔗 Associando sessões órfãs ao veículo padrão...")
    
    try:
        db = get_database()
        
        with db.get_session() as session:
            # Contar sessões órfãs
            orphan_count = session.query(DataSession).filter(
                DataSession.vehicle_id.is_(None)
            ).count()
            
            if orphan_count == 0:
                print("ℹ️ Nenhuma sessão órfã encontrada")
                return 0
            
            # Atualizar sessões órfãs
            updated = session.query(DataSession).filter(
                DataSession.vehicle_id.is_(None)
            ).update({DataSession.vehicle_id: vehicle_id})
            
            session.commit()
            
            print(f"✅ {updated} sessões associadas ao veículo padrão")
            return updated
            
    except Exception as e:
        print(f"❌ Erro na associação: {str(e)}")
        return 0

def validate_migration():
    """Valida o resultado da migração."""
    print("✅ Validando migração...")
    
    try:
        db = get_database()
        
        with db.get_session() as session:
            total_sessions = session.query(DataSession).count()
            sessions_with_vehicle = session.query(DataSession).filter(
                DataSession.vehicle_id.isnot(None)
            ).count()
            orphan_sessions = session.query(DataSession).filter(
                DataSession.vehicle_id.is_(None)
            ).count()
            
            vehicle_count = len(get_all_vehicles())
            
            print(f"📊 Total de sessões: {total_sessions}")
            print(f"📊 Sessões com veículo: {sessions_with_vehicle}")
            print(f"📊 Sessões órfãs: {orphan_sessions}")
            print(f"📊 Veículos cadastrados: {vehicle_count}")
            
            # Verificar se migração foi bem-sucedida
            if orphan_sessions == 0 and vehicle_count > 0:
                print("✅ Migração validada com sucesso!")
                return True
            else:
                print("❌ Migração falhou na validação")
                return False
                
    except Exception as e:
        print(f"❌ Erro na validação: {str(e)}")
        return False

def execute_migration():
    """Executa migração completa."""
    print("🚗 INICIANDO MIGRAÇÃO PARA SISTEMA DE VEÍCULOS")
    print("=" * 50)
    
    # Etapa 1: Backup
    backup_path = create_backup()
    if not backup_path:
        print("❌ Falha no backup. Abortando.")
        return False
    
    # Etapa 2: Análise
    analysis = analyze_existing_data()
    if not analysis:
        print("❌ Falha na análise. Abortando.")
        return False
    
    if analysis['orphan_count'] == 0:
        print("ℹ️ Todas as sessões já têm veículos associados.")
        print("✅ Sistema já migrado!")
        return True
    
    # Etapa 3: Criar veículo padrão
    vehicle_id = create_default_vehicle()
    if not vehicle_id:
        print("❌ Falha na criação do veículo. Abortando.")
        return False
    
    # Etapa 4: Associar sessões
    migrated_count = associate_orphan_sessions(vehicle_id)
    
    # Etapa 5: Validar
    if validate_migration():
        print("\n" + "=" * 50)
        print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"📊 {migrated_count} sessões migradas")
        print(f"🚗 Veículo padrão: {vehicle_id}")
        print(f"💾 Backup: {backup_path}")
        return True
    else:
        print("❌ Migração falhou!")
        return False

if __name__ == "__main__":
    success = execute_migration()
    sys.exit(0 if success else 1)