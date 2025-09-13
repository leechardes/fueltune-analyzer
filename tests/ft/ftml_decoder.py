#!/usr/bin/env python3
"""
FTML Advanced Decoder
Decodificador avançado para arquivos FTML com múltiplas estratégias
"""

import json
import struct
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd


class FTMLDecoder:
    """Decodificador avançado de arquivos FTML"""

    # Possíveis campos e seus tipos/tamanhos
    FIELD_DEFINITIONS = {
        "rpm": ("H", 2),  # uint16
        "map": ("H", 2),  # uint16
        "tps": ("B", 1),  # uint8
        "lambda": ("f", 4),  # float
        "egt": ("H", 2),  # uint16
        "oil_pressure": ("H", 2),  # uint16
        "oil_temp": ("h", 2),  # int16
        "water_temp": ("h", 2),  # int16
        "battery": ("H", 2),  # uint16 (x100 para volts)
        "injection_time": ("H", 2),  # uint16
        "ignition": ("h", 2),  # int16
        "speed": ("H", 2),  # uint16
    }

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data = None
        self.decoded_data = []

    def load_file(self):
        """Carrega o arquivo FTML"""
        with open(self.filepath, "rb") as f:
            self.data = f.read()
        print(f"Arquivo carregado: {len(self.data)} bytes")

    def find_patterns(self) -> Dict[str, Any]:
        """Busca padrões no arquivo para identificar estrutura"""
        patterns = {
            "repeating_sequences": [],
            "possible_header_size": None,
            "possible_record_size": None,
            "data_start_offset": None,
        }

        # Busca sequências repetidas
        for size in [32, 64, 128, 256]:
            if self._check_repeating_pattern(size):
                patterns["repeating_sequences"].append(size)

        # Tenta identificar cabeçalho
        header_end = self._find_header_end()
        if header_end:
            patterns["possible_header_size"] = header_end
            patterns["data_start_offset"] = header_end

        return patterns

    def _check_repeating_pattern(self, size: int) -> bool:
        """Verifica se há padrão repetido de determinado tamanho"""
        if len(self.data) < size * 10:
            return False

        # Pega amostras
        samples = []
        for i in range(0, min(size * 10, len(self.data)), size):
            samples.append(self.data[i : i + 4])  # Primeiros 4 bytes de cada bloco

        # Verifica se há padrão
        unique_samples = len(set(samples))
        return unique_samples < len(samples) * 0.8  # 80% de repetição

    def _find_header_end(self) -> Optional[int]:
        """Tenta encontrar onde termina o cabeçalho"""
        # Procura por sequência de zeros ou padrão de mudança
        zero_count = 0
        for i in range(min(4096, len(self.data))):
            if self.data[i] == 0:
                zero_count += 1
                if zero_count > 16:  # 16 zeros consecutivos
                    return i - 16
            else:
                zero_count = 0

        # Procura por mudança de padrão
        for i in range(256, min(4096, len(self.data)), 16):
            chunk1 = self.data[i - 16 : i]
            chunk2 = self.data[i : i + 16]

            # Se entropia muda significativamente
            if self._calculate_entropy(chunk1) > 0.8 and self._calculate_entropy(chunk2) < 0.5:
                return i

        return None

    def _calculate_entropy(self, data: bytes) -> float:
        """Calcula entropia de Shannon dos dados"""
        if not data:
            return 0

        freq = {}
        for byte in data:
            freq[byte] = freq.get(byte, 0) + 1

        entropy = 0
        for count in freq.values():
            p = count / len(data)
            if p > 0:
                entropy -= p * np.log2(p)

        return entropy / 8  # Normaliza para 0-1

    def decode_strategy_1(self) -> pd.DataFrame:
        """Estratégia 1: Assume registros de 64 bytes com campos conhecidos"""
        records = []
        record_size = 64

        for i in range(0, len(self.data) - record_size, record_size):
            record_data = self.data[i : i + record_size]

            try:
                record = {
                    "timestamp": i,
                    "rpm": struct.unpack("<H", record_data[0:2])[0],
                    "map": struct.unpack("<H", record_data[2:4])[0],
                    "tps": record_data[4] * 100 / 255,  # Converte para %
                    "lambda": struct.unpack("<f", record_data[8:12])[0],
                    "water_temp": struct.unpack("<h", record_data[12:14])[0],
                    "oil_temp": struct.unpack("<h", record_data[14:16])[0],
                    "battery": struct.unpack("<H", record_data[16:18])[0] / 100,
                    "injection_time": struct.unpack("<H", record_data[20:22])[0] / 1000,
                    "ignition": struct.unpack("<h", record_data[24:26])[0] / 10,
                }

                # Valida valores
                if 0 <= record["rpm"] <= 20000 and 0 <= record["map"] <= 5000:
                    records.append(record)

            except:
                continue

        return pd.DataFrame(records)

    def decode_strategy_2(self) -> pd.DataFrame:
        """Estratégia 2: Busca por marcadores e decodifica dinamicamente"""
        records = []

        # Procura por padrões de RPM (valores típicos: 800-8000)
        for i in range(0, len(self.data) - 32):
            try:
                possible_rpm = struct.unpack("<H", self.data[i : i + 2])[0]

                if 800 <= possible_rpm <= 8000:
                    # Tenta decodificar registro a partir daqui
                    record = self._decode_record_at_position(i)
                    if record:
                        records.append(record)
                        i += 32  # Pula para próximo possível registro

            except:
                continue

        return pd.DataFrame(records)

    def _decode_record_at_position(self, pos: int) -> Optional[Dict]:
        """Tenta decodificar um registro em determinada posição"""
        if pos + 32 > len(self.data):
            return None

        try:
            record = {
                "position": pos,
                "rpm": struct.unpack("<H", self.data[pos : pos + 2])[0],
                "value_1": struct.unpack("<H", self.data[pos + 2 : pos + 4])[0],
                "value_2": self.data[pos + 4],
                "value_3": self.data[pos + 5],
                "float_1": struct.unpack("<f", self.data[pos + 8 : pos + 12])[0],
                "int_1": struct.unpack("<h", self.data[pos + 12 : pos + 14])[0],
                "int_2": struct.unpack("<h", self.data[pos + 14 : pos + 16])[0],
            }

            # Validação básica
            if 0 <= record["rpm"] <= 20000 and -1000 < record["float_1"] < 1000:
                return record

        except:
            pass

        return None

    def decode_strategy_3(self) -> pd.DataFrame:
        """Estratégia 3: Decodifica como stream contínuo de valores"""
        values = []

        # Decodifica como sequência de uint16
        for i in range(0, len(self.data) - 2, 2):
            try:
                value = struct.unpack("<H", self.data[i : i + 2])[0]
                values.append(value)
            except:
                values.append(0)

        # Reorganiza em colunas (assume 10 campos por registro)
        num_fields = 10
        records = []

        for i in range(0, len(values) - num_fields, num_fields):
            record = {f"field_{j}": values[i + j] for j in range(num_fields)}
            record["index"] = i // num_fields
            records.append(record)

        return pd.DataFrame(records)

    def auto_decode(self) -> pd.DataFrame:
        """Tenta todas as estratégias e retorna a melhor"""
        if not self.data:
            self.load_file()

        print("Tentando estratégia 1...")
        df1 = self.decode_strategy_1()

        print("Tentando estratégia 2...")
        df2 = self.decode_strategy_2()

        print("Tentando estratégia 3...")
        df3 = self.decode_strategy_3()

        # Escolhe a estratégia com mais registros válidos
        results = [
            (df1, "Estratégia 1: Registros fixos de 64 bytes"),
            (df2, "Estratégia 2: Busca por marcadores"),
            (df3, "Estratégia 3: Stream contínuo"),
        ]

        best_df = max(results, key=lambda x: len(x[0]) if not x[0].empty else 0)

        print(f"\nMelhor resultado: {best_df[1]} com {len(best_df[0])} registros")

        return best_df[0]

    def save_csv(self, df: pd.DataFrame, output_path: Optional[str] = None):
        """Salva DataFrame como CSV"""
        if output_path is None:
            output_path = self.filepath.with_suffix(".decoded.csv")

        df.to_csv(output_path, index=False)
        print(f"CSV salvo em: {output_path}")

        # Salva também estatísticas
        stats_path = Path(output_path).with_suffix(".stats.json")
        stats = {
            "num_records": len(df),
            "columns": list(df.columns),
            "file_size": len(self.data),
            "source_file": str(self.filepath),
        }

        if not df.empty:
            stats["summary"] = df.describe().to_dict()

        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2, default=str)

        print(f"Estatísticas salvas em: {stats_path}")


def main():
    import sys

    if len(sys.argv) < 2:
        print("Analisando todos os arquivos FTML no diretório...")

        for ftml_file in Path(".").glob("*.ftml"):
            print(f"\n{'='*60}")
            print(f"Processando: {ftml_file}")

            decoder = FTMLDecoder(ftml_file)
            decoder.load_file()

            # Busca padrões
            patterns = decoder.find_patterns()
            print(f"Padrões encontrados: {patterns}")

            # Decodifica
            df = decoder.auto_decode()

            if not df.empty:
                decoder.save_csv(df)
                print(f"Primeiras linhas do resultado:")
                print(df.head())
            else:
                print("Não foi possível decodificar o arquivo")

    else:
        filepath = sys.argv[1]
        decoder = FTMLDecoder(filepath)
        decoder.load_file()

        df = decoder.auto_decode()

        if not df.empty:
            decoder.save_csv(df)
            print(f"\nPrimeiras 10 linhas:")
            print(df.head(10))

            print(f"\nEstatísticas:")
            print(df.describe())
        else:
            print("Não foi possível decodificar o arquivo")


if __name__ == "__main__":
    main()
