#!/usr/bin/env python3
"""
Remove campos de dados do veículo dos arquivos de mapas (2D/3D) em data/fuel_maps/.

Execução:
  python scripts/cleanup_maps_metadata.py
"""
from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    maps_dir = root / "data" / "fuel_maps"
    if not maps_dir.exists():
        print("Diretório data/fuel_maps não encontrado; nada a limpar.")
        return

    changed = 0
    for p in maps_dir.glob("map_*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue

        meta = data.get("metadata")
        if isinstance(meta, dict) and "vehicle_data" in meta:
            meta.pop("vehicle_data", None)
            data["metadata"] = meta
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            changed += 1

    print(f"Arquivos atualizados: {changed}")


if __name__ == "__main__":
    main()

