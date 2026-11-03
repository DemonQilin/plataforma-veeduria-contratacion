"""Consolidación de los procesos de SECOP II en un proceso por portafolio (R5)."""

from pathlib import Path

import duckdb

SQL_PATH = Path(__file__).with_name("r05_canonical_process.sql")


def consolidate_processes(connection: duckdb.DuckDBPyConnection) -> None:
    """Crea `canonical_processes` desde `procurement_processes`, una fila por portafolio.

    El número de oferentes es el máximo entre las filas (R5) y el proceso cuenta como adjudicado
    si alguna fila lo está (ADR 0029). R9 decide después qué procesos entran a cada indicador.
    """
    connection.execute(SQL_PATH.read_text(encoding="utf-8"))
