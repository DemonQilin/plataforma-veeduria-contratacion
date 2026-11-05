"""Procesos válidos para el indicador de oferente único (R9; ADR 0043)."""

from pathlib import Path

import duckdb

from veeduria.consolidate.quality import ensure_quality_issues
from veeduria.normalize.catalogs import UNASSIGNED_CODE, classify_department

SQL_PATH = Path(__file__).with_name("r09_single_bidder_processes.sql")


def select_single_bidder_processes(connection: duckdb.DuckDBPyConnection) -> None:
    """Crea `single_bidder_processes` desde `canonical_processes` y reporta las exclusiones.

    Entran los procesos competitivos y adjudicados publicados entre el inicio del periodo (R2) y
    la fecha de corte (R12). Los que reportan cero oferentes quedan marcados `is_excluded` y se
    anotan en `quality_issues` con la regla R9, identificados por el portafolio. La secretaría es
    la unidad del proceso traducida con el catálogo de R8 y, si no se reconoce, `unassigned`.
    """
    texts = [
        text
        for (text,) in connection.execute(
            "SELECT DISTINCT department FROM canonical_processes"
            " WHERE department IS NOT NULL ORDER BY department"
        ).fetchall()
    ]
    entries = [classify_department(text) for text in texts]
    pairs = [(text, entry.code) for text, entry in zip(texts, entries, strict=True) if entry]
    connection.execute(
        SQL_PATH.read_text(encoding="utf-8"),
        {
            "department_texts": [text for text, _ in pairs],
            "department_codes": [code for _, code in pairs],
            "unassigned": UNASSIGNED_CODE,
        },
    )
    ensure_quality_issues(connection, ("R9",))
    connection.execute(
        "INSERT INTO quality_issues"
        " SELECT 'R9', procurement_process, 'Proceso adjudicado sin oferentes'"
        " FROM single_bidder_processes WHERE is_excluded ORDER BY procurement_process"
    )
