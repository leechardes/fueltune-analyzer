"""
Migration script to add bank columns to vehicles table
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import config

def migrate():
    """Add bank columns to vehicles table."""
    # Use the database in data directory
    db_path = project_root / "data" / "fueltune.db"
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(vehicles)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # List of new columns to add
        new_columns = [
            ("bank_a_enabled", "BOOLEAN DEFAULT 0"),
            ("bank_a_mode", "VARCHAR(20)"),
            ("bank_a_outputs", "VARCHAR(50)"),
            ("bank_a_injector_flow", "FLOAT"),
            ("bank_a_injector_count", "INTEGER"),
            ("bank_a_total_flow", "FLOAT"),
            ("bank_a_dead_time", "FLOAT"),
            ("bank_b_enabled", "BOOLEAN DEFAULT 0"),
            ("bank_b_mode", "VARCHAR(20)"),
            ("bank_b_outputs", "VARCHAR(50)"),
            ("bank_b_injector_flow", "FLOAT"),
            ("bank_b_injector_count", "INTEGER"),
            ("bank_b_total_flow", "FLOAT"),
            ("bank_b_dead_time", "FLOAT"),
            ("max_map_pressure", "FLOAT DEFAULT 250.0"),
            ("min_map_pressure", "FLOAT DEFAULT 0.0")
        ]
        
        # Add columns that don't exist
        for col_name, col_type in new_columns:
            if col_name not in columns:
                print(f"Adding column: {col_name}")
                cursor.execute(f"ALTER TABLE vehicles ADD COLUMN {col_name} {col_type}")
        
        conn.commit()
        print("Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()