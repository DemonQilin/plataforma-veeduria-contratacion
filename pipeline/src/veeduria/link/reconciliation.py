"""Conciliación mensual de contratos entre SECOP II y MEData (R15; ADR 0031)."""

from decimal import Decimal
from pathlib import Path

import duckdb

SQL_PATH = Path(__file__).with_name("r15_reconciliation.sql")

# R15: un mes con menos de este porcentaje de contratos en ambas fuentes se advierte.
RECONCILIATION_THRESHOLD = Decimal("0.80")


def reconcile_sources(connection: duckdb.DuckDBPyConnection) -> None:
    """Crea `reconciliation` con una fila por mes del periodo cubierto por MEData.

    Cuenta los contratos de cada fuente y los presentes en ambas, y marca los meses cuya
    proporción de contratos compartidos sobre la unión queda bajo `RECONCILIATION_THRESHOLD`.
    """
    connection.execute(
        SQL_PATH.read_text(encoding="utf-8"), {"threshold": RECONCILIATION_THRESHOLD}
    )
