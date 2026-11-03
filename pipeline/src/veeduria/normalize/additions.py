"""Normalización de las adiciones de SECOP II (R6)."""

from pathlib import Path

import duckdb

from veeduria.normalize.catalogs import VALUE_ADDITION_CODE, classify_addition_type

SQL_PATH = Path(__file__).with_name("r06_additions.sql")


def normalize_additions(connection: duckdb.DuckDBPyConnection, snapshot_path: Path) -> None:
    """Crea la tabla `additions` desde la copia, una fila por fila de la copia.

    Adiciones no trae la entidad: R1 queda garantizada porque la extracción pide solo los
    `id_contrato` de Contratos (ADR 0025). No consolida ni deduplica.
    """
    texts = [
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT coalesce(tipo, '')"
            " FROM read_csv($snapshot_path, all_varchar = true, header = true) ORDER BY ALL",
            {"snapshot_path": str(snapshot_path)},
        ).fetchall()
    ]
    codes = [classify_addition_type(text).code for text in texts]
    connection.execute(
        SQL_PATH.read_text(encoding="utf-8"),
        {
            "snapshot_path": str(snapshot_path),
            "type_texts": texts,
            "addition_types": codes,
            "value_flags": [code == VALUE_ADDITION_CODE for code in codes],
        },
    )
