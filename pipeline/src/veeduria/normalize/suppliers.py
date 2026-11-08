"""Normalización de los proveedores de SECOP II (R14)."""

from pathlib import Path

import duckdb

SQL_PATH = Path(__file__).with_name("r14_suppliers.sql")

# Pesos de la DIAN para el dígito de verificación, de derecha a izquierda.
_DIAN_WEIGHTS = (3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71)
_NIT_LENGTH = 9


def _check_digit(nit: str) -> int:
    remainder = sum(int(digit) * _DIAN_WEIGHTS[i] for i, digit in enumerate(reversed(nit))) % 11
    return remainder if remainder < 2 else 11 - remainder


def strip_check_digit(document: str) -> str:
    """Quita el dígito de verificación de un NIT de 10 dígitos si coincide con el calculado.

    Un documento de otra longitud, o de 10 dígitos con un dígito que no coincide, queda tal cual
    (ADR 0027).
    """
    nit = document[:_NIT_LENGTH]
    if (
        len(document) == _NIT_LENGTH + 1
        and document.isdigit()
        and int(document[-1]) == _check_digit(nit)
    ):
        return nit
    return document


def normalize_suppliers(connection: duckdb.DuckDBPyConnection, snapshot_path: Path) -> None:
    """Crea la tabla `suppliers` desde la copia, una fila por fila de la copia.

    `supplier_id` es el NIT sin dígito de verificación, para que el NIT con y sin ese dígito
    cuente como un solo proveedor (ADR 0027). El nombre del proveedor no está en la copia
    (ADR 0049). No consolida ni deduplica.
    """
    documents = [
        document
        for (document,) in connection.execute(
            "SELECT DISTINCT coalesce(documento_proveedor, '')"
            " FROM read_csv($snapshot_path, all_varchar = true, header = true) ORDER BY ALL",
            {"snapshot_path": str(snapshot_path)},
        ).fetchall()
    ]
    connection.execute(
        SQL_PATH.read_text(encoding="utf-8"),
        {
            "snapshot_path": str(snapshot_path),
            "documents": documents,
            "document_ids": [strip_check_digit(document) for document in documents],
        },
    )
