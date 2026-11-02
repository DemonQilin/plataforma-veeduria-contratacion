"""Normalización de los procesos de contratación de SECOP II (R1, R6)."""

from pathlib import Path

import duckdb

from veeduria.normalize.catalogs import classify_contract_type, classify_procurement_method

SQL_PATH = Path(__file__).with_name("r06_procurement_processes.sql")
ENTITY_NAME = "DISTRITO ESPECIAL DE CIENCIA TECNOLOGIA E INNOVACION DE MEDELLIN"


def normalize_procurement_processes(
    connection: duckdb.DuckDBPyConnection, snapshot_path: Path
) -> None:
    """Crea la tabla `procurement_processes` desde la copia, una fila por fila de la copia.

    Los catálogos se aplican en Python sobre las combinaciones distintas de textos crudos y
    llegan a DuckDB como parámetros de lista. No consolida: eso es R5 (tarea 7).
    """
    combos = connection.execute(
        "SELECT DISTINCT coalesce(modalidad_de_contratacion, ''), coalesce(tipo_de_contrato, '')"
        " FROM read_csv($snapshot_path, all_varchar = true, header = true) ORDER BY ALL",
        {"snapshot_path": str(snapshot_path)},
    ).fetchall()
    methods = [classify_procurement_method(method) for method, _ in combos]
    connection.execute(
        SQL_PATH.read_text(encoding="utf-8"),
        {
            "snapshot_path": str(snapshot_path),
            "entity_name": ENTITY_NAME,
            "method_texts": [combo[0] for combo in combos],
            "type_texts": [combo[1] for combo in combos],
            "method_codes": [method.code for method in methods],
            "direct_awards": [method.direct_award for method in methods],
            "competitives": [method.competitive for method in methods],
            "contract_types": [classify_contract_type(combo[1]).code for combo in combos],
        },
    )
