"""Normalización del Plan Anual de Adquisiciones (R6, R17, I8)."""

import csv
from pathlib import Path

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.normalize.procurement_plan import normalize_procurement_plan

HEADER = [
    "ano",
    "fecha_estimada_inicio",
    "modalidad_seleccion",
    "valor_total_estimado",
    "unidad_de_contratacion",
    "codigos_unspsc",
]
SNAPSHOT_PLAN = REPO_ROOT / "data" / "snapshot" / "medata_procurement_plan.csv"


def _normalize(tmp_path: Path, rows: list[list[str]]) -> duckdb.DuckDBPyConnection:
    path = tmp_path / "medata_procurement_plan.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)
    connection = duckdb.connect()
    normalize_procurement_plan(connection, path)
    return connection


def _row(
    month: str = "Enero",
    method: str = "Contratacion Directa",
    value: str = "1000",
    year: str = "2022.0",
) -> list[str]:
    return [year, month, method, value, "Secretaria Falsa", "80101500"]


def test_r06_method_variants_share_one_category(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [_row(method="Contratacion Directa"), _row(method="contratacion directa")],
    )
    rows = connection.execute(
        "SELECT DISTINCT procurement_method, direct_award, competitive FROM procurement_plan"
    ).fetchall()
    assert rows == [("direct_award", True, False)]


def test_r06_unknown_and_empty_method_fall_into_other(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(method="Modalidad Inventada"), _row(method="")])
    rows = connection.execute(
        "SELECT DISTINCT procurement_method, direct_award, competitive FROM procurement_plan"
    ).fetchall()
    assert rows == [("other", False, False)]


def test_r06_competitive_method_is_not_direct(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(method="mnima cuanta")])
    assert connection.execute(
        "SELECT procurement_method, direct_award, competitive FROM procurement_plan"
    ).fetchall() == [("minimum_amount", False, True)]


def test_r17_year_and_month_become_numbers(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [_row(month="Enero", year="2014.0"), _row(month="septiembre", year="2023.0")],
    )
    rows = connection.execute(
        "SELECT year, estimated_start_month FROM procurement_plan ORDER BY year"
    ).fetchall()
    assert rows == [(2014, 1), (2023, 9)]


def test_r17_unknown_month_is_null(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(month="Trimestre 1")])
    assert connection.execute("SELECT estimated_start_month FROM procurement_plan").fetchall() == [
        (None,)
    ]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1000", 1000),
        ("0", 0),
        ("1,10E+11", 110_000_000_000),
        ("1,14054E+12", 1_140_540_000_000),
        ("1,2611", None),
        ("", None),
    ],
)
def test_r17_estimated_value(tmp_path: Path, raw: str, expected: int | None) -> None:
    connection = _normalize(tmp_path, [_row(value=raw)])
    assert connection.execute("SELECT estimated_value FROM procurement_plan").fetchall() == [
        (expected,)
    ]


def test_r17_identical_lines_are_kept(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(), _row()])
    assert connection.execute("SELECT count(*) FROM procurement_plan").fetchone() == (2,)


def test_r17_output_columns(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row()])
    columns = [
        description[0]
        for description in connection.execute("SELECT * FROM procurement_plan").description
    ]
    assert columns == [
        "year",
        "estimated_start_month",
        "procurement_method",
        "direct_award",
        "competitive",
        "estimated_value",
        "department",
        "unspsc_codes",
    ]


def test_normalization_does_not_change_the_source_text(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row()])
    assert connection.execute(
        "SELECT department, unspsc_codes FROM procurement_plan"
    ).fetchall() == [("Secretaria Falsa", "80101500")]


@pytest.fixture(scope="module")
def real_plan() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    normalize_procurement_plan(connection, SNAPSHOT_PLAN)
    return connection


def test_golden_every_line_is_classified(real_plan: duckdb.DuckDBPyConnection) -> None:
    assert real_plan.execute(
        "SELECT count(*), count(*) FILTER (WHERE procurement_method = 'other'),"
        " count(*) FILTER (WHERE estimated_start_month IS NULL),"
        " count(*) FILTER (WHERE estimated_value IS NULL) FROM procurement_plan"
    ).fetchone() == (18764, 0, 0, 2)


def test_golden_direct_awards_planned_for_january_2022(
    real_plan: duckdb.DuckDBPyConnection,
) -> None:
    assert real_plan.execute(
        "SELECT count(*) FROM procurement_plan"
        " WHERE year = 2022 AND estimated_start_month = 1 AND direct_award"
    ).fetchone() == (726,)


def test_i8_share_of_direct_awards_planned_for_january_and_february_to_june(
    real_plan: duckdb.DuckDBPyConnection,
) -> None:
    rows = real_plan.execute(
        """
        SELECT year,
               round(100.0 * count(*) FILTER (WHERE estimated_start_month = 1) / count(*)),
               round(100.0 * count(*) FILTER (WHERE estimated_start_month BETWEEN 2 AND 6)
                     / count(*))
        FROM procurement_plan
        WHERE direct_award AND year IN (2014, 2018, 2022)
        GROUP BY year ORDER BY year
        """
    ).fetchall()
    assert rows == [(2014, 46, 15), (2018, 57, 16), (2022, 52, 8)]
