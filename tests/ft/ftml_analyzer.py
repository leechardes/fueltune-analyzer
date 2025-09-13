#!/usr/bin/env python3
"""
FTML File Analyzer and Converter
Analisa arquivos .ftml da FuelTech e tenta converter para CSV
"""

import argparse
import csv
import json
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional


class FTMLAnalyzer:
    """Analisador de arquivos FTML da FuelTech"""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data = None
        self.header_info = {}
        self.records = []

    def read_file(self) -> bytes:
        """Lê o arquivo FTML em modo binário"""
        with open(self.filepath, "rb") as f:
            self.data = f.read()
        return self.data

    def analyze_structure(self) -> Dict[str, Any]:
        """Analisa a estrutura do arquivo"""
        if not self.data:
            self.read_file()

        analysis = {
            "file_size": len(self.data),
            "file_name": self.filepath.name,
            "first_bytes": self.data[:20].hex(),
            "last_bytes": self.data[-20:].hex(),
            "printable_strings": self._extract_strings(),
            "possible_floats": self._find_float_patterns(),
            "possible_integers": self._find_int_patterns(),
        }

        return analysis

    def _extract_strings(self, min_length: int = 4) -> List[str]:
        """Extrai strings legíveis do arquivo"""
        strings = []
        current_string = []

        for byte in self.data:
            if 32 <= byte <= 126:  # Caracteres ASCII imprimíveis
                current_string.append(chr(byte))
            else:
                if len(current_string) >= min_length:
                    strings.append("".join(current_string))
                current_string = []

        if len(current_string) >= min_length:
            strings.append("".join(current_string))

        return strings[:100]  # Limita a 100 strings

    def _find_float_patterns(self) -> List[float]:
        """Tenta encontrar padrões de float no arquivo"""
        floats = []

        # Tenta interpretar bytes como floats (32 bits)
        for i in range(0, len(self.data) - 4, 4):
            try:
                # Little-endian float
                value = struct.unpack("<f", self.data[i : i + 4])[0]
                if -10000 < value < 10000 and value != 0:  # Valores razoáveis
                    floats.append(round(value, 3))
            except:
                pass

        return floats[:50]  # Limita a 50 valores

    def _find_int_patterns(self) -> List[int]:
        """Tenta encontrar padrões de inteiros no arquivo"""
        integers = []

        # Tenta interpretar bytes como inteiros (16 bits)
        for i in range(0, len(self.data) - 2, 2):
            try:
                # Little-endian int16
                value = struct.unpack("<H", self.data[i : i + 2])[0]
                if 0 < value < 20000:  # Valores típicos de RPM, MAP, etc
                    integers.append(value)
            except:
                pass

        return integers[:50]  # Limita a 50 valores

    def try_decode_as_records(self, record_size: int = 64) -> List[Dict]:
        """Tenta decodificar o arquivo como registros de tamanho fixo"""
        records = []

        for i in range(0, len(self.data) - record_size, record_size):
            record_data = self.data[i : i + record_size]

            # Tenta interpretar cada registro
            try:
                record = {
                    "index": i // record_size,
                    "hex": record_data[:16].hex(),
                    "possible_rpm": struct.unpack("<H", record_data[0:2])[0],
                    "possible_map": struct.unpack("<H", record_data[2:4])[0],
                    "possible_tps": record_data[4],
                    "possible_lambda": struct.unpack("<f", record_data[8:12])[0],
                }

                # Filtra valores razoáveis
                if 0 < record["possible_rpm"] < 10000:
                    records.append(record)

            except:
                pass

        return records[:100]  # Limita a 100 registros

    def export_to_csv(self, output_path: Optional[str] = None) -> str:
        """Exporta dados analisados para CSV"""
        if not output_path:
            output_path = self.filepath.with_suffix(".csv")

        records = self.try_decode_as_records()

        if records:
            with open(output_path, "w", newline="") as csvfile:
                fieldnames = records[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for record in records:
                    writer.writerow(record)

            return str(output_path)
        else:
            return "Não foi possível extrair registros válidos"

    def save_analysis(self, output_path: Optional[str] = None) -> str:
        """Salva análise completa em JSON"""
        if not output_path:
            output_path = self.filepath.with_suffix(".analysis.json")

        analysis = self.analyze_structure()

        with open(output_path, "w") as f:
            json.dump(analysis, f, indent=2, default=str)

        return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="Analisa e converte arquivos FTML")
    parser.add_argument("input_file", help="Arquivo FTML de entrada")
    parser.add_argument("--csv", action="store_true", help="Exporta para CSV")
    parser.add_argument("--analyze", action="store_true", help="Salva análise em JSON")
    parser.add_argument("--output", help="Arquivo de saída (opcional)")

    args = parser.parse_args()

    analyzer = FTMLAnalyzer(args.input_file)

    print(f"Analisando: {args.input_file}")
    print("-" * 50)

    # Análise básica
    analysis = analyzer.analyze_structure()
    print(f"Tamanho do arquivo: {analysis['file_size']} bytes")
    print(f"Primeiros bytes: {analysis['first_bytes']}")
    print(f"Strings encontradas: {len(analysis['printable_strings'])}")

    if analysis["printable_strings"]:
        print("\nPrimeiras 10 strings:")
        for s in analysis["printable_strings"][:10]:
            print(f"  - {s}")

    # Exportações
    if args.csv:
        csv_path = analyzer.export_to_csv(args.output)
        print(f"\nCSV salvo em: {csv_path}")

    if args.analyze:
        json_path = analyzer.save_analysis(args.output)
        print(f"Análise salva em: {json_path}")

    # Tenta decodificar registros
    records = analyzer.try_decode_as_records()
    if records:
        print(f"\nPossíveis registros encontrados: {len(records)}")
        print("\nPrimeiros 3 registros:")
        for r in records[:3]:
            print(f"  Index {r['index']}: RPM={r['possible_rpm']}, MAP={r['possible_map']}")


if __name__ == "__main__":
    # Se executado sem argumentos, analisa todos os .ftml no diretório
    import sys

    if len(sys.argv) == 1:
        print("Uso: python ftml_analyzer.py <arquivo.ftml> [--csv] [--analyze]")
        print("\nArquivos FTML encontrados no diretório:")

        for ftml_file in Path(".").glob("*.ftml"):
            print(f"  - {ftml_file}")

        print("\nAnalisando todos os arquivos...")
        for ftml_file in Path(".").glob("*.ftml"):
            print(f"\n{'='*60}")
            analyzer = FTMLAnalyzer(ftml_file)
            analysis = analyzer.analyze_structure()

            print(f"Arquivo: {ftml_file}")
            print(f"Tamanho: {analysis['file_size']} bytes")
            print(f"Strings: {len(analysis['printable_strings'])}")

            # Salva análise
            json_path = analyzer.save_analysis()
            csv_path = analyzer.export_to_csv()

            print(f"Análise: {json_path}")
            print(f"CSV: {csv_path}")
    else:
        main()
