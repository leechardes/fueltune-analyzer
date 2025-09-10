"""
Inicializa o banco de dados com todas as tabelas necessárias
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import create_engine
from src.data.models import Base, Vehicle, DataSession, FuelTechCoreData, FuelTechExtendedData, DataQualityCheck

def init_database():
    """Inicializa o banco de dados com todas as tabelas."""
    db_path = project_root / "data" / "fueltune.db"
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Criar todas as tabelas
    print("Criando tabelas do banco de dados...")
    Base.metadata.create_all(engine)
    print("Tabelas criadas com sucesso!")
    
    # Verificar tabelas criadas
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nTabelas criadas: {', '.join(tables)}")
    
    # Verificar colunas da tabela vehicles
    columns = inspector.get_columns('vehicles')
    print("\nColunas da tabela vehicles:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")

if __name__ == "__main__":
    init_database()