"""
Script para adicionar veículos de teste ao banco de dados
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.models import Vehicle

def add_test_vehicles():
    """Adiciona veículos de teste ao banco de dados."""
    db_path = project_root / "data" / "fueltech_data.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verificar se já existem veículos
        existing = session.query(Vehicle).count()
        if existing > 0:
            print(f"Já existem {existing} veículos no banco. Pulando adição.")
            return
        
        # Veículo 1: Golf GTI
        golf = Vehicle(
            name="VW Golf GTI MK7",
            nickname="Golf",
            plate="ABC-1234",
            year=2018,
            brand="Volkswagen",
            model="Golf GTI",
            engine_displacement=2.0,
            engine_cylinders=4,
            engine_configuration="I4",
            engine_aspiration="Turbo",
            injector_type="Bosch",
            injector_count=4,
            injector_flow_rate=550,
            fuel_rail_pressure=3.5,
            turbo_brand="IHI",
            turbo_model="IS20",
            max_boost_pressure=1.5,
            wastegate_type="Eletrônica",
            transmission_type="DSG",
            gear_count=6,
            final_drive_ratio=3.23,
            curb_weight=1365,
            drivetrain="FWD",
            tire_size="225/40R18",
            fuel_type="Gasolina",
            octane_rating=98,
            fuel_system="Direct Injection",
            estimated_power=230,
            estimated_torque=350,
            max_rpm=6500,
            bank_a_enabled=True,
            bank_a_mode="sequential",
            bank_a_outputs=["1", "2", "3", "4"],
            bank_a_injector_flow=550,
            bank_a_injector_count=4,
            bank_a_total_flow=2200,
            bank_a_dead_time=1.0,
            max_map_pressure=250.0,
            min_map_pressure=0.0,
            notes="Golf GTI Stage 1"
        )
        
        # Veículo 2: Civic Si
        civic = Vehicle(
            name="Honda Civic Si",
            nickname="Civic",
            plate="XYZ-5678",
            year=2020,
            brand="Honda",
            model="Civic Si",
            engine_displacement=1.5,
            engine_cylinders=4,
            engine_configuration="I4",
            engine_aspiration="Turbo",
            injector_type="Denso",
            injector_count=4,
            injector_flow_rate=450,
            fuel_rail_pressure=3.0,
            turbo_brand="Honeywell",
            turbo_model="MGT14",
            max_boost_pressure=1.3,
            wastegate_type="Pneumática",
            transmission_type="Manual",
            gear_count=6,
            final_drive_ratio=4.35,
            curb_weight=1362,
            drivetrain="FWD",
            tire_size="235/40R18",
            fuel_type="Gasolina",
            octane_rating=95,
            fuel_system="Direct Injection",
            estimated_power=205,
            estimated_torque=260,
            max_rpm=6500,
            bank_a_enabled=True,
            bank_a_mode="sequential",
            bank_a_outputs=["1", "2", "3", "4"],
            bank_a_injector_flow=450,
            bank_a_injector_count=4,
            bank_a_total_flow=1800,
            bank_a_dead_time=0.9,
            max_map_pressure=230.0,
            min_map_pressure=0.0,
            notes="Civic Si com intake e downpipe"
        )
        
        # Veículo 3: WRX STI
        wrx = Vehicle(
            name="Subaru WRX STI",
            nickname="STI",
            plate="RST-9012",
            year=2019,
            brand="Subaru",
            model="WRX STI",
            engine_displacement=2.5,
            engine_cylinders=4,
            engine_configuration="H4",
            engine_aspiration="Turbo",
            injector_type="Injector Dynamics",
            injector_count=4,
            injector_flow_rate=1050,
            fuel_rail_pressure=3.5,
            turbo_brand="IHI",
            turbo_model="VF48",
            max_boost_pressure=1.8,
            wastegate_type="Eletrônica",
            transmission_type="Manual",
            gear_count=6,
            final_drive_ratio=4.44,
            curb_weight=1568,
            drivetrain="AWD",
            tire_size="245/40R18",
            fuel_type="E85",
            octane_rating=105,
            fuel_system="Port Injection",
            estimated_power=350,
            estimated_torque=450,
            max_rpm=7000,
            bank_a_enabled=True,
            bank_a_mode="sequential",
            bank_a_outputs=["1", "3"],
            bank_a_injector_flow=1050,
            bank_a_injector_count=2,
            bank_a_total_flow=2100,
            bank_a_dead_time=1.2,
            bank_b_enabled=True,
            bank_b_mode="sequential",
            bank_b_outputs=["2", "4"],
            bank_b_injector_flow=1050,
            bank_b_injector_count=2,
            bank_b_total_flow=2100,
            bank_b_dead_time=1.2,
            max_map_pressure=300.0,
            min_map_pressure=0.0,
            notes="STI com turbo upgrade e flex fuel"
        )
        
        # Adicionar veículos ao banco
        session.add(golf)
        session.add(civic)
        session.add(wrx)
        session.commit()
        
        print("3 veículos de teste adicionados com sucesso!")
        
        # Listar veículos adicionados
        vehicles = session.query(Vehicle).all()
        print("\nVeículos no banco:")
        for v in vehicles:
            print(f"  - {v.name} ({v.nickname}) - {v.year} - {v.estimated_power}hp")
            if v.bank_a_enabled:
                print(f"    Bancada A: {v.bank_a_injector_count} bicos de {v.bank_a_injector_flow}cc")
            if v.bank_b_enabled:
                print(f"    Bancada B: {v.bank_b_injector_count} bicos de {v.bank_b_injector_flow}cc")
            
    except Exception as e:
        print(f"Erro ao adicionar veículos: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    add_test_vehicles()