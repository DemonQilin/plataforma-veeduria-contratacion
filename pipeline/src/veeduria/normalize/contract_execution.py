"""Normalización de MEData · Ejecución contractual (R2, R6; ADR 0010)."""

from pathlib import Path

import duckdb
from ftfy import fix_encoding

from veeduria.normalize.catalogs import classify_procurement_method

SQL_PATH = Path(__file__).with_name("r02_contract_execution.sql")
TEXT_COLUMNS = ("modalidad", "causal", "nombre_secretaria", "nombre_programa", "estado")


def normalize_contract_execution(
    connection: duckdb.DuckDBPyConnection, snapshot_path: Path
) -> None:
    """Crea la tabla `contract_execution`: una fila por línea de la copia (ADR 0010).

    La codificación se repara en Python sobre los textos distintos, solo con
    `ftfy.fix_encoding`, y la modalidad se clasifica sobre el texto ya reparado. Los
    resultados llegan a DuckDB como parámetros, para que el SQL no dependa de funciones
    definidas desde Python.
    """
    union = " UNION ".join(
        f"SELECT coalesce({column}, '') AS text"
        f" FROM read_csv($snapshot_path, all_varchar = true, header = true)"
        for column in TEXT_COLUMNS
    )
    raw_texts = [
        text
        for (text,) in connection.execute(
            f"SELECT text FROM ({union}) ORDER BY text", {"snapshot_path": str(snapshot_path)}
        ).fetchall()
    ]
    fixed_texts = [fix_encoding(text) for text in raw_texts]
    methods = [classify_procurement_method(text) for text in fixed_texts]
    connection.execute(
        SQL_PATH.read_text(encoding="utf-8"),
        {
            "snapshot_path": str(snapshot_path),
            "raw_texts": raw_texts,
            "fixed_texts": fixed_texts,
            "codes": [method.code for method in methods],
            "direct_awards": [method.direct_award for method in methods],
            "competitives": [method.competitive for method in methods],
        },
    )
