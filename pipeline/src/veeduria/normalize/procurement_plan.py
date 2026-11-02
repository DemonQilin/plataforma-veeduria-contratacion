"""Normalización del Plan Anual de Adquisiciones de MEData (R6, R17)."""

from pathlib import Path

import duckdb

from veeduria.normalize.catalogs import classify_procurement_method

SQL_PATH = Path(__file__).with_name("r06_procurement_plan.sql")


def normalize_procurement_plan(connection: duckdb.DuckDBPyConnection, snapshot_path: Path) -> None:
    """Crea la tabla `procurement_plan` desde la copia, sin quitar ninguna línea.

    El catálogo se aplica en Python sobre los textos distintos y llega a DuckDB como
    parámetros, para que el SQL no dependa de funciones definidas desde Python.
    """
    raw_texts = [
        text
        for (text,) in connection.execute(
            "SELECT DISTINCT coalesce(modalidad_seleccion, '') AS text"
            " FROM read_csv($snapshot_path, all_varchar = true, header = true) ORDER BY text",
            {"snapshot_path": str(snapshot_path)},
        ).fetchall()
    ]
    methods = [classify_procurement_method(text) for text in raw_texts]
    connection.execute(
        SQL_PATH.read_text(encoding="utf-8"),
        {
            "snapshot_path": str(snapshot_path),
            "raw_texts": raw_texts,
            "codes": [method.code for method in methods],
            "direct_awards": [method.direct_award for method in methods],
            "competitives": [method.competitive for method in methods],
        },
    )
