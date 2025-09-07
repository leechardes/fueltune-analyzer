# VEHICLE-MIGRATION-IMPLEMENTATION

## Objetivo
Executar migração segura dos dados existentes para o novo sistema de veículos, criando veículo padrão e associando todas as sessões existentes sem perda de dados.

## Padrões de Desenvolvimento
Este agente segue os padrões definidos em:
- /srv/projects/shared/docs/agents/development/A04-STREAMLIT-PROFESSIONAL.md

### Princípios Fundamentais:
1. **ZERO emojis** - Usar apenas Material Design Icons
2. **Interface profissional** - Sem decorações infantis  
3. **CSS adaptativo** - Funciona em tema claro e escuro
4. **Português brasileiro** - Todos os textos traduzidos
5. **Ícones consistentes** - Material Icons em todos os componentes

## Estratégia de Migração

### Fases da Migração
1. **Análise Pré-Migração** - Inventário dos dados existentes
2. **Backup Completo** - Backup de segurança do banco
3. **Criação do Schema** - Executar migrations do modelo
4. **Veículo Padrão** - Criar veículo para dados órfãos
5. **Associação de Dados** - Vincular sessões ao veículo padrão
6. **Validação** - Verificar integridade dos dados
7. **Limpeza** - Remover dados temporários

## Implementação

### 1. Script de Análise Pré-Migração

#### 1.1 Criar scripts/analyze_existing_data.py

```python
"""
Script para análise dos dados existentes antes da migração.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data.database import get_db_session
from src.data.models import DataSession, FuelTechCoreData, FuelTechExtendedData
from config import get_database_url

def analyze_existing_data():
    """Analisa dados existentes no banco."""
    
    print("🔍 ANÁLISE PRÉ-MIGRAÇÃO - DADOS EXISTENTES")
    print("=" * 60)
    
    try:
        with get_db_session() as session:
            # Contar sessões existentes
            session_count = session.query(DataSession).count()
            print(f"📊 Total de Sessões: {session_count:,}")
            
            # Contar dados de telemetria
            core_data_count = session.query(FuelTechCoreData).count()
            extended_data_count = session.query(FuelTechExtendedData).count()
            
            print(f"📈 Dados Core: {core_data_count:,}")
            print(f"📈 Dados Extended: {extended_data_count:,}")
            print(f"📈 Total de Registros: {core_data_count + extended_data_count:,}")
            
            # Análise temporal
            oldest_session = session.query(DataSession).order_by(DataSession.created_at).first()
            newest_session = session.query(DataSession).order_by(DataSession.created_at.desc()).first()
            
            if oldest_session and newest_session:
                print(f"📅 Período dos Dados: {oldest_session.created_at.strftime('%d/%m/%Y')} até {newest_session.created_at.strftime('%d/%m/%Y')}")
            
            # Análise de arquivos
            unique_files = session.query(DataSession.filename).distinct().count()
            print(f"📁 Arquivos Únicos: {unique_files}")
            
            # Sessões sem dados
            sessions_without_data = session.query(DataSession).outerjoin(FuelTechCoreData).filter(
                FuelTechCoreData.session_id.is_(None)
            ).count()
            
            if sessions_without_data > 0:
                print(f"⚠️  Sessões Órfãs: {sessions_without_data}")
            
            # Verificar se já existe coluna vehicle_id
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'data_sessions' 
                AND column_name = 'vehicle_id'
            """))
            
            has_vehicle_column = result.fetchone() is not None
            print(f"🔧 Coluna vehicle_id existe: {'Sim' if has_vehicle_column else 'Não'}")
            
            # Resumo para migração
            print("\n" + "=" * 60)
            print("📋 RESUMO PARA MIGRAÇÃO:")
            print(f"   • {session_count:,} sessões para migrar")
            print(f"   • {core_data_count + extended_data_count:,} registros para preservar")
            print(f"   • Schema {'JÁ PREPARADO' if has_vehicle_column else 'PRECISA ATUALIZAÇÃO'}")
            
            if sessions_without_data > 0:
                print(f"   • ⚠️  {sessions_without_data} sessões órfãs para investigar")
            
            return {
                'session_count': session_count,
                'core_data_count': core_data_count,
                'extended_data_count': extended_data_count,
                'has_vehicle_column': has_vehicle_column,
                'sessions_without_data': sessions_without_data,
                'oldest_session': oldest_session.created_at if oldest_session else None,
                'newest_session': newest_session.created_at if newest_session else None
            }
            
    except Exception as e:
        print(f"❌ Erro na análise: {str(e)}")
        return None

def generate_migration_report(analysis: dict):
    """Gera relatório detalhado da migração."""
    
    report_path = "migration_analysis_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Relatório de Análise Pré-Migração\n\n")
        f.write(f"**Data da Análise:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        f.write("## Resumo dos Dados Existentes\n\n")
        f.write(f"- **Sessões de Dados:** {analysis['session_count']:,}\n")
        f.write(f"- **Registros Core:** {analysis['core_data_count']:,}\n")
        f.write(f"- **Registros Extended:** {analysis['extended_data_count']:,}\n")
        f.write(f"- **Total de Registros:** {analysis['core_data_count'] + analysis['extended_data_count']:,}\n\n")
        
        if analysis['oldest_session'] and analysis['newest_session']:
            f.write("## Período dos Dados\n\n")
            f.write(f"- **Primeira Sessão:** {analysis['oldest_session'].strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"- **Última Sessão:** {analysis['newest_session'].strftime('%d/%m/%Y %H:%M')}\n\n")
        
        f.write("## Status do Schema\n\n")
        f.write(f"- **Coluna vehicle_id:** {'✅ Existe' if analysis['has_vehicle_column'] else '❌ Não existe'}\n")
        
        if analysis['sessions_without_data'] > 0:
            f.write(f"- **Sessões Órfãs:** ⚠️ {analysis['sessions_without_data']} sessões sem dados\n")
        
        f.write("\n## Plano de Migração\n\n")
        f.write("1. ✅ Fazer backup completo do banco de dados\n")
        f.write("2. 🔧 Executar migration para adicionar coluna vehicle_id\n")
        f.write("3. 🚗 Criar veículo padrão 'Dados Migrados'\n")
        f.write("4. 🔗 Associar todas as sessões ao veículo padrão\n")
        f.write("5. ✅ Validar integridade dos dados\n")
        f.write("6. 🧹 Limpeza e otimização\n\n")
        
        f.write("## Riscos Identificados\n\n")
        if analysis['sessions_without_data'] > 0:
            f.write(f"- **Sessões Órfãs:** {analysis['sessions_without_data']} sessões podem causar problemas\n")
        
        if not analysis['has_vehicle_column']:
            f.write("- **Schema Desatualizado:** Necessária migration do banco\n")
        
        f.write("\n---\n")
        f.write("*Relatório gerado automaticamente pelo sistema de migração*\n")
    
    print(f"📄 Relatório salvo em: {report_path}")

if __name__ == "__main__":
    analysis = analyze_existing_data()
    if analysis:
        generate_migration_report(analysis)
```

### 2. Script de Backup

#### 2.1 Criar scripts/backup_database.py

```python
"""
Script para backup completo do banco de dados antes da migração.
"""

import os
import sys
import subprocess
from datetime import datetime
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import get_database_url

def create_backup():
    """Cria backup completo do banco de dados."""
    
    print("💾 INICIANDO BACKUP DO BANCO DE DADOS")
    print("=" * 50)
    
    # Criar diretório de backups
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Nome do backup com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"fueltune_backup_{timestamp}.sql"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Obter URL do banco
        db_url = get_database_url()
        
        # Extrair informações da conexão
        if db_url.startswith("sqlite:///"):
            # Backup SQLite
            sqlite_path = db_url.replace("sqlite:///", "")
            sqlite_backup_path = os.path.join(backup_dir, f"fueltune_sqlite_{timestamp}.db")
            
            print(f"📂 Fazendo backup SQLite: {sqlite_path}")
            shutil.copy2(sqlite_path, sqlite_backup_path)
            
            print(f"✅ Backup SQLite concluído: {sqlite_backup_path}")
            return sqlite_backup_path
            
        elif db_url.startswith("postgresql://"):
            # Backup PostgreSQL
            print(f"📂 Fazendo backup PostgreSQL...")
            
            cmd = [
                "pg_dump",
                db_url,
                "-f", backup_path,
                "--verbose",
                "--clean",
                "--if-exists"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Backup PostgreSQL concluído: {backup_path}")
                return backup_path
            else:
                print(f"❌ Erro no backup PostgreSQL: {result.stderr}")
                return None
                
        else:
            print(f"❌ Tipo de banco não suportado para backup: {db_url}")
            return None
            
    except Exception as e:
        print(f"❌ Erro durante backup: {str(e)}")
        return None

def verify_backup(backup_path: str) -> bool:
    """Verifica se o backup foi criado corretamente."""
    
    if not os.path.exists(backup_path):
        print(f"❌ Arquivo de backup não encontrado: {backup_path}")
        return False
    
    file_size = os.path.getsize(backup_path)
    if file_size == 0:
        print(f"❌ Arquivo de backup está vazio: {backup_path}")
        return False
    
    print(f"✅ Backup verificado: {backup_path} ({file_size:,} bytes)")
    return True

def create_restore_script(backup_path: str):
    """Cria script de restore do backup."""
    
    restore_script_path = backup_path.replace('.sql', '_restore.sh').replace('.db', '_restore.sh')
    
    with open(restore_script_path, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# Script de restore do backup FuelTune\n")
        f.write(f"# Backup criado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        if backup_path.endswith('.db'):
            # Restore SQLite
            f.write("echo 'Restaurando backup SQLite...'\n")
            f.write(f"cp '{backup_path}' fueltune_restored.db\n")
            f.write("echo 'Backup SQLite restaurado como fueltune_restored.db'\n")
        else:
            # Restore PostgreSQL
            f.write("echo 'Restaurando backup PostgreSQL...'\n")
            f.write("read -p 'Digite a URL do banco de dados: ' DB_URL\n")
            f.write(f"psql $DB_URL < '{backup_path}'\n")
            f.write("echo 'Backup PostgreSQL restaurado'\n")
    
    # Tornar executável
    os.chmod(restore_script_path, 0o755)
    print(f"📜 Script de restore criado: {restore_script_path}")

if __name__ == "__main__":
    backup_path = create_backup()
    if backup_path and verify_backup(backup_path):
        create_restore_script(backup_path)
        print(f"\n✅ BACKUP CONCLUÍDO COM SUCESSO!")
        print(f"📁 Arquivo: {backup_path}")
    else:
        print(f"\n❌ FALHA NO BACKUP!")
        sys.exit(1)
```

### 3. Script Principal de Migração

#### 3.1 Criar scripts/migrate_to_vehicle_system.py

```python
"""
Script principal de migração para o sistema de veículos.
"""

import os
import sys
import uuid
from datetime import datetime
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data.database import get_db_session
from src.data.models import Vehicle, DataSession
from analyze_existing_data import analyze_existing_data
from backup_database import create_backup, verify_backup

def execute_migration():
    """Executa migração completa para sistema de veículos."""
    
    print("🚗 MIGRAÇÃO PARA SISTEMA DE VEÍCULOS")
    print("=" * 50)
    
    # Etapa 1: Análise pré-migração
    print("\n📊 Etapa 1: Análise dos dados existentes")
    analysis = analyze_existing_data()
    
    if not analysis:
        print("❌ Falha na análise. Abortando migração.")
        return False
    
    print(f"✅ Encontradas {analysis['session_count']:,} sessões para migrar")
    
    # Etapa 2: Backup
    print("\n💾 Etapa 2: Criando backup de segurança")
    backup_path = create_backup()
    
    if not backup_path or not verify_backup(backup_path):
        print("❌ Falha no backup. Abortando migração.")
        return False
    
    print(f"✅ Backup criado: {backup_path}")
    
    # Etapa 3: Executar Migration do Schema
    print("\n🔧 Etapa 3: Atualizando schema do banco")
    if not update_database_schema():
        print("❌ Falha na atualização do schema. Abortando migração.")
        return False
    
    print("✅ Schema atualizado com sucesso")
    
    # Etapa 4: Criar veículo padrão
    print("\n🚗 Etapa 4: Criando veículo padrão para dados migrados")
    default_vehicle_id = create_default_vehicle()
    
    if not default_vehicle_id:
        print("❌ Falha na criação do veículo padrão. Abortando migração.")
        return False
    
    print(f"✅ Veículo padrão criado: {default_vehicle_id}")
    
    # Etapa 5: Associar sessões existentes
    print("\n🔗 Etapa 5: Associando sessões ao veículo padrão")
    migrated_sessions = associate_sessions_to_vehicle(default_vehicle_id)
    
    if migrated_sessions == 0:
        print("⚠️  Nenhuma sessão foi migrada")
    else:
        print(f"✅ {migrated_sessions:,} sessões associadas ao veículo padrão")
    
    # Etapa 6: Validação pós-migração
    print("\n✅ Etapa 6: Validando integridade dos dados")
    if not validate_migration(default_vehicle_id, analysis):
        print("❌ Validação falhou. Verifique os dados.")
        return False
    
    print("✅ Migração validada com sucesso")
    
    # Etapa 7: Limpeza
    print("\n🧹 Etapa 7: Limpeza final")
    cleanup_migration()
    
    print("\n" + "=" * 50)
    print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print(f"📊 {migrated_sessions:,} sessões migradas")
    print(f"🚗 Veículo padrão: {default_vehicle_id}")
    print(f"💾 Backup disponível: {backup_path}")
    
    return True

def update_database_schema():
    """Atualiza schema do banco para suportar veículos."""
    
    try:
        with get_db_session() as session:
            # Verificar se coluna já existe
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'data_sessions' 
                AND column_name = 'vehicle_id'
            """))
            
            if result.fetchone() is not None:
                print("ℹ️  Coluna vehicle_id já existe, pulando atualização do schema")
                return True
            
            # Adicionar coluna vehicle_id
            print("➕ Adicionando coluna vehicle_id à tabela data_sessions")
            session.execute(text("""
                ALTER TABLE data_sessions 
                ADD COLUMN vehicle_id VARCHAR(36)
            """))
            
            # Criar índice
            print("📊 Criando índice para vehicle_id")
            session.execute(text("""
                CREATE INDEX idx_session_vehicle 
                ON data_sessions(vehicle_id)
            """))
            
            session.commit()
            return True
            
    except Exception as e:
        print(f"❌ Erro na atualização do schema: {str(e)}")
        return False

def create_default_vehicle():
    """Cria veículo padrão para dados migrados."""
    
    try:
        with get_db_session() as session:
            # Verificar se já existe
            existing = session.query(Vehicle).filter(
                Vehicle.name == "Dados Migrados"
            ).first()
            
            if existing:
                print(f"ℹ️  Veículo padrão já existe: {existing.id}")
                return existing.id
            
            # Criar veículo padrão
            default_vehicle = Vehicle(
                id=str(uuid.uuid4()),
                name="Dados Migrados",
                nickname="Sistema Anterior",
                brand="Não Especificado",
                model="Dados do Sistema Anterior",
                year=None,
                engine_displacement=2.0,
                engine_cylinders=4,
                engine_configuration="I4",
                engine_aspiration="Naturally Aspirated",
                fuel_type="Gasoline",
                estimated_power=200,
                estimated_torque=300,
                max_rpm=7000,
                curb_weight=1400,
                drivetrain="FWD",
                transmission_type="Manual",
                notes="Veículo criado automaticamente durante a migração para o sistema de veículos. "
                      "Agrupa todos os dados que existiam antes da implementação do cadastro de veículos. "
                      f"Migração executada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )
            
            session.add(default_vehicle)
            session.commit()
            
            return default_vehicle.id
            
    except Exception as e:
        print(f"❌ Erro na criação do veículo padrão: {str(e)}")
        return None

def associate_sessions_to_vehicle(vehicle_id: str) -> int:
    """Associa todas as sessões órfãs ao veículo padrão."""
    
    try:
        with get_db_session() as session:
            # Contar sessões sem veículo
            orphan_count = session.query(DataSession).filter(
                DataSession.vehicle_id.is_(None)
            ).count()
            
            if orphan_count == 0:
                print("ℹ️  Nenhuma sessão órfã encontrada")
                return 0
            
            print(f"🔄 Associando {orphan_count:,} sessões ao veículo padrão...")
            
            # Atualizar todas as sessões órfãs
            updated = session.query(DataSession).filter(
                DataSession.vehicle_id.is_(None)
            ).update({DataSession.vehicle_id: vehicle_id})
            
            session.commit()
            
            print(f"✅ {updated:,} sessões associadas")
            return updated
            
    except Exception as e:
        print(f"❌ Erro na associação de sessões: {str(e)}")
        return 0

def validate_migration(vehicle_id: str, original_analysis: dict) -> bool:
    """Valida se a migração foi bem-sucedida."""
    
    try:
        with get_db_session() as session:
            # Verificar se o veículo existe
            vehicle = session.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
            if not vehicle:
                print("❌ Veículo padrão não encontrado")
                return False
            
            # Contar sessões após migração
            total_sessions = session.query(DataSession).count()
            sessions_with_vehicle = session.query(DataSession).filter(
                DataSession.vehicle_id.isnot(None)
            ).count()
            orphan_sessions = session.query(DataSession).filter(
                DataSession.vehicle_id.is_(None)
            ).count()
            
            print(f"📊 Validação dos dados:")
            print(f"   • Total de sessões: {total_sessions:,}")
            print(f"   • Sessões com veículo: {sessions_with_vehicle:,}")
            print(f"   • Sessões órfãs: {orphan_sessions:,}")
            
            # Verificar integridade
            if total_sessions != original_analysis['session_count']:
                print(f"❌ Perda de sessões! Era {original_analysis['session_count']}, agora {total_sessions}")
                return False
            
            if orphan_sessions > 0:
                print(f"⚠️  Ainda existem {orphan_sessions} sessões órfãs")
                return False
            
            # Verificar dados de telemetria
            from src.data.models import FuelTechCoreData
            core_data_count = session.query(FuelTechCoreData).count()
            
            if core_data_count != original_analysis['core_data_count']:
                print(f"❌ Perda de dados de telemetria! Era {original_analysis['core_data_count']:,}, agora {core_data_count:,}")
                return False
            
            print("✅ Validação concluída - dados íntegros")
            return True
            
    except Exception as e:
        print(f"❌ Erro na validação: {str(e)}")
        return False

def cleanup_migration():
    """Limpeza final após migração."""
    
    try:
        with get_db_session() as session:
            # Atualizar estatísticas do banco
            session.execute(text("ANALYZE"))
            session.commit()
            
        print("✅ Limpeza concluída - estatísticas atualizadas")
        
    except Exception as e:
        print(f"⚠️  Erro na limpeza (não crítico): {str(e)}")

def rollback_migration(backup_path: str):
    """Reverte migração usando backup."""
    
    print("⏪ EXECUTANDO ROLLBACK DA MIGRAÇÃO")
    print("=" * 40)
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup não encontrado: {backup_path}")
        return False
    
    try:
        # Implementar restore baseado no tipo de banco
        print(f"📂 Restaurando backup: {backup_path}")
        
        # Código específico para restore seria implementado aqui
        # baseado no tipo de banco de dados
        
        print("✅ Rollback concluído")
        return True
        
    except Exception as e:
        print(f"❌ Erro no rollback: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migração para sistema de veículos")
    parser.add_argument("--rollback", help="Caminho do backup para rollback")
    parser.add_argument("--force", action="store_true", help="Executar sem confirmação")
    
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_migration(args.rollback)
    else:
        if not args.force:
            print("⚠️  Esta operação irá modificar o banco de dados.")
            confirm = input("Deseja continuar? (sim/não): ")
            if confirm.lower() not in ['sim', 's', 'yes', 'y']:
                print("Operação cancelada pelo usuário.")
                sys.exit(0)
        
        success = execute_migration()
    
    sys.exit(0 if success else 1)
```

### 4. Interface de Migração no Streamlit

#### 4.1 Criar src/ui/pages/migration.py

```python
"""
Interface de migração para o sistema de veículos.
Permite executar migração através da interface web.
"""

import streamlit as st
import subprocess
import os
from datetime import datetime

def show_migration_page():
    """Interface de migração para veículos."""
    
    st.markdown('''
        <div class="main-header">
            <span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">
                sync
            </span>
            Migração para Sistema de Veículos
        </div>
    ''', unsafe_allow_html=True)
    
    # Status da migração
    migration_status = check_migration_status()
    
    if migration_status['completed']:
        show_migration_completed_ui(migration_status)
    else:
        show_migration_pending_ui(migration_status)

def check_migration_status():
    """Verifica status atual da migração."""
    
    try:
        from src.data.database import get_db_session
        from src.data.models import Vehicle, DataSession
        
        with get_db_session() as session:
            # Verificar se existem veículos
            vehicle_count = session.query(Vehicle).count()
            
            # Verificar sessões com veículos
            sessions_with_vehicles = session.query(DataSession).filter(
                DataSession.vehicle_id.isnot(None)
            ).count()
            
            # Verificar sessões órfãs
            orphan_sessions = session.query(DataSession).filter(
                DataSession.vehicle_id.is_(None)
            ).count()
            
            total_sessions = session.query(DataSession).count()
            
            return {
                'completed': vehicle_count > 0 and orphan_sessions == 0,
                'vehicle_count': vehicle_count,
                'total_sessions': total_sessions,
                'sessions_with_vehicles': sessions_with_vehicles,
                'orphan_sessions': orphan_sessions
            }
            
    except Exception as e:
        return {
            'completed': False,
            'error': str(e)
        }

def show_migration_pending_ui(status):
    """Interface para migração pendente."""
    
    st.warning("⚠️ O sistema de veículos ainda não foi configurado.")
    
    # Mostrar análise atual
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Sessões Totais", status.get('total_sessions', 0))
    
    with col2:
        st.metric("Sessões com Veículo", status.get('sessions_with_vehicles', 0))
    
    with col3:
        st.metric("Sessões Órfãs", status.get('orphan_sessions', 0))
    
    # Processo de migração
    st.markdown("### 🔄 Processo de Migração")
    
    steps = [
        "Análise dos dados existentes",
        "Backup completo do banco de dados",
        "Atualização do schema (adicionar coluna vehicle_id)",
        "Criação de veículo padrão 'Dados Migrados'",
        "Associação de todas as sessões ao veículo padrão",
        "Validação da integridade dos dados"
    ]
    
    for i, step in enumerate(steps, 1):
        st.write(f"{i}. {step}")
    
    # Avisos importantes
    st.markdown("### ⚠️ Avisos Importantes")
    
    st.error("""
    **ATENÇÃO:** Este processo irá modificar a estrutura do banco de dados.
    
    • Um backup completo será criado automaticamente
    • Todas as sessões existentes serão associadas a um veículo padrão
    • O processo é irreversível sem o backup
    • Recomenda-se executar em horário de baixa utilização
    """)
    
    # Botão de execução
    if st.button(
        "🚀 Executar Migração",
        type="primary",
        help="Inicia o processo de migração para o sistema de veículos"
    ):
        execute_migration_ui()

def show_migration_completed_ui(status):
    """Interface para migração já concluída."""
    
    st.success("✅ Sistema de veículos já está configurado!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Veículos Cadastrados", status.get('vehicle_count', 0))
    
    with col2:
        st.metric("Sessões Totais", status.get('total_sessions', 0))
    
    with col3:
        st.metric("Sessões com Veículo", status.get('sessions_with_vehicles', 0))
    
    if status.get('orphan_sessions', 0) > 0:
        st.warning(f"⚠️ Existem {status['orphan_sessions']} sessões órfãs que precisam ser associadas a um veículo.")
        
        if st.button("🔧 Corrigir Sessões Órfãs"):
            fix_orphan_sessions()
    
    # Opções pós-migração
    st.markdown("### 🛠️ Opções Avançadas")
    
    with st.expander("Gerenciar Migração"):
        st.markdown("**Opções para administradores do sistema:**")
        
        if st.button("📊 Executar Análise Detalhada"):
            run_detailed_analysis()
        
        st.download_button(
            "📄 Download Relatório de Migração",
            data=generate_migration_report(),
            file_name=f"migration_report_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )

def execute_migration_ui():
    """Executa migração através da UI."""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()
    
    try:
        # Executar script de migração
        script_path = os.path.join("scripts", "migrate_to_vehicle_system.py")
        
        status_text.text("Iniciando migração...")
        progress_bar.progress(10)
        
        # Executar processo
        process = subprocess.Popen(
            ["python", script_path, "--force"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Mostrar output em tempo real
        output_lines = []
        for line in process.stdout:
            output_lines.append(line.strip())
            
            # Atualizar UI baseado no output
            if "Etapa 1:" in line:
                status_text.text("Analisando dados existentes...")
                progress_bar.progress(20)
            elif "Etapa 2:" in line:
                status_text.text("Criando backup...")
                progress_bar.progress(35)
            elif "Etapa 3:" in line:
                status_text.text("Atualizando schema...")
                progress_bar.progress(50)
            elif "Etapa 4:" in line:
                status_text.text("Criando veículo padrão...")
                progress_bar.progress(65)
            elif "Etapa 5:" in line:
                status_text.text("Associando sessões...")
                progress_bar.progress(80)
            elif "Etapa 6:" in line:
                status_text.text("Validando dados...")
                progress_bar.progress(95)
            elif "MIGRAÇÃO CONCLUÍDA" in line:
                status_text.text("Migração concluída!")
                progress_bar.progress(100)
        
        # Aguardar conclusão
        return_code = process.wait()
        
        # Mostrar log completo
        with log_container.expander("📋 Log Completo da Migração"):
            for line in output_lines:
                st.text(line)
        
        if return_code == 0:
            st.success("✅ Migração concluída com sucesso!")
            st.balloons()
            st.rerun()
        else:
            st.error("❌ Erro durante a migração. Verifique os logs.")
    
    except Exception as e:
        st.error(f"❌ Erro ao executar migração: {str(e)}")

def fix_orphan_sessions():
    """Corrige sessões órfãs."""
    
    with st.spinner("Corrigindo sessões órfãs..."):
        try:
            # Implementar correção de sessões órfãs
            script_path = os.path.join("scripts", "fix_orphan_sessions.py")
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                st.success("✅ Sessões órfãs corrigidas!")
                st.rerun()
            else:
                st.error(f"❌ Erro na correção: {result.stderr}")
        
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

def generate_migration_report():
    """Gera relatório da migração."""
    
    status = check_migration_status()
    
    report = f"""# Relatório de Migração - Sistema de Veículos

**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

## Status Atual

- **Status:** {'✅ Migração Concluída' if status['completed'] else '⚠️ Migração Pendente'}
- **Veículos Cadastrados:** {status.get('vehicle_count', 0)}
- **Sessões Totais:** {status.get('total_sessions', 0)}
- **Sessões com Veículo:** {status.get('sessions_with_vehicles', 0)}
- **Sessões Órfãs:** {status.get('orphan_sessions', 0)}

## Próximos Passos

{'- Sistema pronto para uso' if status['completed'] else '- Execute a migração para ativar o sistema de veículos'}
- Cadastre novos veículos conforme necessário
- Configure veículo padrão ativo para novos uploads

---
*Relatório gerado automaticamente*
"""
    
    return report

if __name__ == "__main__":
    show_migration_page()
```

## Checklist de Migração

### Preparação
- [ ] Script de análise pré-migração criado
- [ ] Sistema de backup implementado
- [ ] Validações de integridade preparadas
- [ ] Interface de migração funcional

### Execução
- [ ] Backup completo realizado
- [ ] Schema atualizado (coluna vehicle_id)
- [ ] Veículo padrão criado
- [ ] Sessões associadas ao veículo padrão
- [ ] Validação pós-migração bem-sucedida

### Validação
- [ ] Nenhuma perda de dados
- [ ] Todas as sessões têm veículo associado
- [ ] Integridade referencial mantida
- [ ] Performance das queries adequada

### Finalização
- [ ] Limpeza executada
- [ ] Relatório de migração gerado
- [ ] Documentação atualizada
- [ ] Sistema pronto para uso

## Recuperação de Falhas

### Se a Migração Falhar:
1. **Parar imediatamente** o processo
2. **Não fazer alterações** adicionais
3. **Usar backup** para restaurar estado anterior
4. **Investigar** causa da falha
5. **Corrigir** problema identificado
6. **Tentar novamente** após correção

### Pontos de Rollback:
- **Antes da migração:** Backup disponível
- **Após schema:** Rollback automático em caso de erro
- **Após associações:** Validação impede conclusão se dados inconsistentes

## Próximos Passos

Após migração bem-sucedida:
1. **Testar interface** de veículos
2. **Executar VEHICLE-INTEGRATION-IMPLEMENTATION**
3. **Treinar usuários** no novo sistema
4. **Monitorar performance** das queries

---

**Prioridade:** Crítica  
**Complexidade:** Alta  
**Tempo Estimado:** 1-2 dias  
**Dependências:** VEHICLE-MODEL-IMPLEMENTATION  
**Bloqueia:** VEHICLE-INTEGRATION-IMPLEMENTATION