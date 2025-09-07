"""
Inicializa o banco de dados fueltech_data.db com todas as tabelas necessárias
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
    db_path = project_root / "data" / "fueltech_data.db"
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Criar todas as tabelas
    print("Criando tabelas do banco de dados fueltech_data.db...")
    Base.metadata.create_all(engine)
    print("Tabelas criadas com sucesso!")
    
    # Verificar tabelas criadas
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nTabelas criadas: {', '.join(tables)}")
    
    # Verificar colunas da tabela vehicles
    if 'vehicles' in tables:
        columns = inspector.get_columns('vehicles')
        print("\nColunas da tabela vehicles:")
        bank_columns = [col['name'] for col in columns if 'bank' in col['name'].lower()]
        if bank_columns:
            print(f"  Colunas de bancada encontradas: {', '.join(bank_columns)}")
        else:
            print("  AVISO: Nenhuma coluna de bancada encontrada!")

if __name__ == "__main__":
    init_database()