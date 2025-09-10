"""
Recria a tabela vehicles com as novas colunas de bancada
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import create_engine, text
from src.data.models import Base, Vehicle

def recreate_vehicles_table():
    """Recria a tabela vehicles com todas as colunas."""
    db_path = project_root / "data" / "fueltech_data.db"
    engine = create_engine(f"sqlite:///{db_path}")
    
    try:
        # Deletar tabela existente
        with engine.begin() as conn:
            print("Removendo tabela vehicles existente...")
            conn.execute(text("DROP TABLE IF EXISTS vehicles"))
            print("Tabela removida.")
        
        # Recriar tabela com novas colunas
        print("Criando nova tabela vehicles com colunas de bancada...")
        Vehicle.__table__.create(engine, checkfirst=True)
        print("Tabela criada com sucesso!")
        
        # Verificar colunas criadas
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = inspector.get_columns('vehicles')
        
        print("\nColunas da tabela vehicles:")
        for col in columns:
            if 'bank' in col['name'].lower() or 'map' in col['name'].lower():
                print(f"  ✓ {col['name']}: {col['type']}")
        
        # Contar colunas de bancada
        bank_columns = [col['name'] for col in columns if 'bank' in col['name'].lower()]
        print(f"\nTotal de colunas de bancada: {len(bank_columns)}")
        
    except Exception as e:
        print(f"Erro ao recriar tabela: {e}")
        raise

if __name__ == "__main__":
    recreate_vehicles_table()