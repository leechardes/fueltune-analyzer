"""
Script para completar a tabela map_data_3d com todas as 1024 colunas.
Este script deve ser executado após a migration fuel_maps_001.

Cria as colunas value_X_Y para X=0-31 e Y=0-31 (exceto as já criadas na migration).
"""

from sqlalchemy import create_engine, text

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


def complete_3d_table(database_url: str = "sqlite:///data/fueltech_data.db"):
    """
    Completa a tabela map_data_3d com todas as colunas necessárias.

    Args:
        database_url: URL de conexão com o banco de dados
    """

    logger.info("Iniciando criação das colunas 3D restantes...")

    engine = create_engine(database_url)

    # Colunas já criadas na migration (primeira linha apenas)
    existing_columns = {
        "value_0_0",
        "value_0_1",
        "value_0_2",
        "value_0_3",
        "value_0_4",
        "value_0_5",
    }

    # Lista de todas as colunas necessárias
    all_columns = []
    for x in range(32):
        for y in range(32):
            column_name = f"value_{x}_{y}"
            all_columns.append(column_name)

    # Filtrar colunas que precisam ser criadas
    columns_to_create = [col for col in all_columns if col not in existing_columns]

    logger.info(f"Criando {len(columns_to_create)} colunas restantes...")

    with engine.connect() as connection:
        for column_name in columns_to_create:
            x, y = column_name.replace("value_", "").split("_")
            f"Célula [{x},{y}]"

            try:
                # Criar a coluna
                alter_statement = text(f"ALTER TABLE map_data_3d ADD COLUMN {column_name} FLOAT")
                connection.execute(alter_statement)

                if int(x) % 5 == 0 and int(y) == 0:  # Log a cada 5 linhas
                    logger.info(f"Criadas colunas para linha {x}")

            except Exception as e:
                logger.error(f"Erro ao criar coluna {column_name}: {str(e)}")
                continue

        # Commit das alterações
        connection.commit()

    logger.info("Criação das colunas 3D concluída com sucesso!")


def verify_3d_table_structure(database_url: str = "sqlite:///data/fueltech_data.db"):
    """
    Verifica se a tabela 3D foi criada corretamente.

    Args:
        database_url: URL de conexão com o banco de dados

    Returns:
        Tuple com (total_colunas, colunas_faltando)
    """

    engine = create_engine(database_url)

    with engine.connect() as connection:
        # Obter informações das colunas
        result = connection.execute(text("PRAGMA table_info(map_data_3d)"))
        columns = [row[1] for row in result]  # row[1] é o nome da coluna

        # Filtrar apenas colunas value_X_Y
        value_columns = [col for col in columns if col.startswith("value_")]

        # Verificar quais colunas esperadas estão faltando
        expected_columns = {f"value_{x}_{y}" for x in range(32) for y in range(32)}
        missing_columns = expected_columns - set(value_columns)

        logger.info(f"Tabela map_data_3d possui {len(value_columns)} colunas de dados")

        if missing_columns:
            logger.warning(
                f"{len(missing_columns)} colunas faltando: {list(missing_columns)[:10]}..."
            )
        else:
            logger.info("Tabela 3D está completa!")

        return len(value_columns), missing_columns


def create_sample_3d_data():
    """
    Cria dados de exemplo para testar a tabela 3D.
    Baseado nos valores padrão da especificação.
    """

    # MAP values (21 pontos ativos)
    map_values = [
        -1.00,
        -0.90,
        -0.80,
        -0.70,
        -0.60,
        -0.50,
        -0.40,
        -0.30,
        -0.20,
        -0.10,
        0.00,
        0.20,
        0.40,
        0.60,
        0.80,
        1.00,
        1.20,
        1.40,
        1.60,
        1.80,
        2.00,
    ]

    # RPM values (24 pontos ativos)
    rpm_values = [
        400,
        600,
        800,
        1000,
        1200,
        1400,
        1600,
        1800,
        2000,
        2200,
        2400,
        2600,
        2800,
        3000,
        3500,
        4000,
        4500,
        5000,
        5500,
        6000,
        6500,
        7000,
        7500,
        8000,
    ]

    # Criar matriz de dados baseada na especificação
    matrix_data = {}

    for x, map_pressure in enumerate(map_values):
        if x >= 21:  # Apenas 21 pontos ativos em MAP
            break

        for y, rpm in enumerate(rpm_values):
            if y >= 24:  # Apenas 24 pontos ativos em RPM
                break

            # Cálculo baseado nos valores da especificação
            # Fórmula simplificada que gera valores entre ~5.5ms e ~16.7ms
            base_value = 5.550

            # Fator baseado na pressão MAP (mais pressão = mais combustível)
            map_factor = (map_pressure + 1.0) / 3.0  # Normalizado 0-1

            # Fator baseado no RPM (mais RPM = mais combustível até certo ponto)
            rpm_factor = min(rpm / 4000.0, 1.5)  # Cap em 1.5 para RPMs altos

            # Cálculo final
            injection_time = (
                base_value + (base_value * map_factor * 1.2) + (base_value * rpm_factor * 0.3)
            )

            # Garantir faixa entre 5.5 e 16.7ms
            injection_time = max(5.550, min(16.690, injection_time))

            matrix_data[f"value_{x}_{y}"] = round(injection_time, 3)

    return matrix_data


if __name__ == "__main__":
    # Executar completação da tabela
    complete_3d_table()

    # Verificar estrutura
    total_cols, missing = verify_3d_table_structure()

    if not missing:
        print(f"✓ Tabela 3D criada com sucesso! {total_cols} colunas de dados.")

        # Criar dados de exemplo
        sample_data = create_sample_3d_data()
        print(f"✓ Dados de exemplo gerados: {len(sample_data)} células com valores.")

    else:
        print(f"✗ Tabela 3D incompleta. {len(missing)} colunas faltando.")
