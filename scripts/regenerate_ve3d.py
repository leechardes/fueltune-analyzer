#!/usr/bin/env python3
import sys
from src.core.fuel_maps.persistence import persistence_manager

def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/regenerate_ve3d.py <vehicle_id> [bank_id]")
        sys.exit(1)
    vehicle_id = sys.argv[1]
    bank_id = sys.argv[2] if len(sys.argv) > 2 else "shared"
    ok = persistence_manager.regenerate_ve_3d_map(vehicle_id, bank_id)
    print("OK" if ok else "FALHA")

if __name__ == "__main__":
    main()

