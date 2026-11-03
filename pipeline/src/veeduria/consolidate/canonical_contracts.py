"""Consolidación de los contratos de SECOP II en un contrato por referencia (R3, R4, D3)."""

from pathlib import Path

import duckdb

from veeduria.consolidate.quality import ensure_quality_issues

CONTRACT_SQL_PATH = Path(__file__).with_name("r03_canonical_contract.sql")
CONFLICTS_SQL_PATH = Path(__file__).with_name("r03_conflicting_processes.sql")
UNSIGNED_SQL_PATH = Path(__file__).with_name("r04_unsigned_contracts.sql")


def consolidate_contracts(connection: duckdb.DuckDBPyConnection) -> None:
    """Crea `canonical_contracts` desde `contracts` y anota los hallazgos en `quality_issues`.

    R4 excluye los contratos sin fecha de firma. R3 elige la primera versión firmada para los
    atributos del contrato y la más reciente para el valor final y el estado. El valor final de
    MEData (D3) se aplica al cruzar, en la tarea 8.
    """
    ensure_quality_issues(connection, ("R3", "R4"))
    connection.execute(CONTRACT_SQL_PATH.read_text(encoding="utf-8"))
    connection.execute(CONFLICTS_SQL_PATH.read_text(encoding="utf-8"))
    connection.execute(UNSIGNED_SQL_PATH.read_text(encoding="utf-8"))
