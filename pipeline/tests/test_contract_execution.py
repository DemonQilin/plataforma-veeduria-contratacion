"""Normalización de MEData · Ejecución contractual (R2, R6; ADR 0010)."""

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb

from tests.paths import REPO_ROOT
from veeduria.normalize.contract_execution import normalize_contract_execution

HEADER = [
    "contrato",
    "fecha_contrato",
    "modalidad",
    "causal",
    "nombre_secretaria",
    "nombre_programa",
    "valor_inicial_contrato",
    "valor_total_adic_contrato",
    "valor_fin_contrato",
    "duracion_en_dias",
    "estado",
    "ano",
    "truncated",
]
SNAPSHOT_EXECUTION = REPO_ROOT / "data" / "snapshot" / "medata_contract_execution.csv"


def _normalize(tmp_path: Path, rows: list[list[str]]) -> duckdb.DuckDBPyConnection:
    path = tmp_path / "medata_contract_execution.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)
    connection = duckdb.connect()
    normalize_contract_execution(connection, path)
    return connection


def _row(
    reference: str = "4600000001",
    signed: str = "4/01/2022",
    method: str = "Contratación Directa",
    justification: str = "NoPluralidadOferente",
    department: str = "Secretaría Falsa",
    program: str = "Programa Falso",
    initial: str = "54.600.000,00",
    additions: str = "1.000,50",
    final: str = "54.601.000,50",
    days: str = "120",
    status: str = "En Ejecución",
    year: str = "2022.0",
    truncated: str = "false",
) -> list[str]:
    return [
        reference,
        signed,
        method,
        justification,
        department,
        program,
        initial,
        additions,
        final,
        days,
        status,
        year,
        truncated,
    ]


def test_r03_reference_drops_surrounding_spaces_and_nbsp(tmp_path: Path) -> None:
    """ADR 0046: la llave de cruce con SECOP II no lleva espacios en los extremos."""
    connection = _normalize(
        tmp_path,
        [_row(reference="4600000001 "), _row(reference=" 4600000002 ")],
    )
    assert connection.execute(
        "SELECT contract_reference FROM contract_execution ORDER BY contract_reference"
    ).fetchall() == [("4600000001",), ("4600000002",)]


def test_adr0010_mojibake_is_repaired_before_the_catalog(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(
                method="ContrataciÃ³n Directa",
                department="SecretarÃ\xada Falsa",
                status="En EjecuciÃ³n",
            )
        ],
    )
    assert connection.execute(
        "SELECT procurement_method, direct_award, competitive, department, contract_status"
        " FROM contract_execution"
    ).fetchall() == [("direct_award", True, False, "Secretaría Falsa", "En Ejecución")]


def test_adr0010_correct_text_and_typographic_quotes_stay_unchanged(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path, [_row(program="Programa “Falso” de Educación", department="Secretaría Falsa")]
    )
    assert connection.execute("SELECT program, department FROM contract_execution").fetchall() == [
        ("Programa “Falso” de Educación", "Secretaría Falsa")
    ]


def test_r06_unknown_method_falls_into_other(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(method="Modalidad Inventada"), _row(method="")])
    assert connection.execute(
        "SELECT DISTINCT procurement_method, direct_award, competitive FROM contract_execution"
    ).fetchall() == [("other", False, False)]


def test_values_dates_and_year_become_typed_columns(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row()])
    assert connection.execute(
        "SELECT contract_reference, signed_date, initial_value, total_addition_value,"
        " final_value, duration_days, year, truncated, method_justification, program"
        " FROM contract_execution"
    ).fetchall() == [
        (
            "4600000001",
            date(2022, 1, 4),
            Decimal("54600000.00"),
            Decimal("1000.50"),
            Decimal("54601000.50"),
            120,
            2022,
            False,
            "NoPluralidadOferente",
            "Programa Falso",
        )
    ]


def test_r02_rows_before_2022_leave_and_unreadable_dates_stay(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(reference="1", signed="31/12/2021"),
            _row(reference="2", signed="1/01/2022"),
            _row(reference="3", signed=""),
            _row(reference="4", signed="no-es-fecha"),
        ],
    )
    assert connection.execute(
        "SELECT contract_reference FROM contract_execution ORDER BY 1"
    ).fetchall() == [("2",), ("3",), ("4",)]


def test_adr0010_truncated_rows_stay_with_null_values(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(
                initial="",
                additions="",
                final="",
                days="",
                status="",
                year="",
                truncated="true",
            )
        ],
    )
    assert connection.execute(
        "SELECT truncated, procurement_method, department, signed_date, initial_value,"
        " total_addition_value, final_value, duration_days, contract_status, year"
        " FROM contract_execution"
    ).fetchall() == [
        (
            True,
            "direct_award",
            "Secretaría Falsa",
            date(2022, 1, 4),
            None,
            None,
            None,
            None,
            None,
            None,
        )
    ]


def test_each_snapshot_line_is_one_row(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(), _row(), _row(reference="4600000002")])
    assert connection.execute("SELECT count(*) FROM contract_execution").fetchone() == (3,)


def test_real_snapshot_counts_and_clean_text() -> None:
    connection = duckdb.connect()
    normalize_contract_execution(connection, SNAPSHOT_EXECUTION)
    assert connection.execute(
        "SELECT count(*), count(DISTINCT contract_reference), count(*) FILTER (WHERE truncated)"
        " FROM contract_execution"
    ).fetchone() == (25783, 2939, 2072)
    assert connection.execute(
        "SELECT count(*) FROM contract_execution WHERE department LIKE '%Ã%'"
        " OR contract_status LIKE '%Ã%' OR program LIKE '%Ã%' OR method_justification LIKE '%Ã%'"
    ).fetchone() == (0,)
    assert connection.execute(
        "SELECT count(*) FROM contract_execution WHERE procurement_method = 'other'"
    ).fetchone() == (0,)
