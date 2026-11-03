"""Cruce de los contratos con su proceso y con MEData (R7, R8, D3; ADR 0030)."""

from pathlib import Path

import duckdb

from veeduria.consolidate.quality import ensure_quality_issues
from veeduria.normalize.catalogs import UNASSIGNED_CODE, classify_department

LINK_SQL_PATH = Path(__file__).with_name("r08_linked_contracts.sql")
QUALITY_SQL_PATH = Path(__file__).with_name("r08_quality.sql")


def link_contracts(connection: duckdb.DuckDBPyConnection) -> None:
    """Crea `linked_contracts` desde `canonical_contracts`, `canonical_processes` y MEData.

    Conserva una fila por contrato aunque no tenga proceso ni aparezca en MEData. La secretaría
    sigue R8, el valor final sigue D3 y `is_value_eligible` deja lista la exclusión de R7. Anota
    en `quality_issues` los textos de secretaría sin mapear y los contratos sin secretaría.
    """
    ensure_quality_issues(connection, ("R8",))
    texts = [
        text
        for (text,) in connection.execute(
            "SELECT department FROM medata_contracts WHERE department IS NOT NULL"
            " UNION SELECT department FROM canonical_processes WHERE department IS NOT NULL"
            " ORDER BY 1"
        ).fetchall()
    ]
    entries = [classify_department(text) for text in texts]
    connection.execute(
        LINK_SQL_PATH.read_text(encoding="utf-8"),
        {
            "department_texts": texts,
            "department_codes": [entry.code if entry else None for entry in entries],
            "unassigned_code": UNASSIGNED_CODE,
        },
    )
    connection.execute(
        QUALITY_SQL_PATH.read_text(encoding="utf-8"),
        {"unmapped_texts": [text for text, entry in zip(texts, entries, strict=True) if not entry]},
    )
