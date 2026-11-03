"""Colapso de MEData · Ejecución a un registro por contrato (R8, D3; ADR 0030)."""

from pathlib import Path

import duckdb

SQL_PATH = Path(__file__).with_name("r08_medata_contracts.sql")


def collapse_medata_contracts(connection: duckdb.DuckDBPyConnection) -> None:
    """Crea `medata_contracts` desde `contract_execution`, una fila por referencia.

    La secretaría y los valores no cambian entre las líneas de un contrato. Un contrato cuyas
    líneas están todas truncadas conserva la secretaría y queda sin valores (`truncated`).
    """
    connection.execute(SQL_PATH.read_text(encoding="utf-8"))
