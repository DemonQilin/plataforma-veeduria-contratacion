"""I8 · Serie de planeación (R17; docs/indicadores.md §3)."""

from pathlib import Path

import duckdb
import pytest

from veeduria.indicators.i8_planned_share import build_planned_share
from veeduria.pipeline import build
from veeduria.publish.indicators import publish_indicators

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"


def _connection(rows: list[tuple]) -> duckdb.DuckDBPyConnection:
    """`procurement_plan` mínima con las columnas que lee I8."""
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE procurement_plan (year INTEGER, estimated_start_month INTEGER,"
        " direct_award BOOLEAN, estimated_value BIGINT)"
    )
    for row in rows:
        connection.execute("INSERT INTO procurement_plan VALUES (?, ?, ?, ?)", row)
    return connection


def _line(year, month, *, direct=True, value=100):
    return (year, month, direct, value)


def _cells(rows):
    return {(c.period, c.variant, c.measure): c for c in build_planned_share(_connection(rows))}


def test_i8_january_and_february_june_shares() -> None:
    cells = _cells([_line(2022, 1), _line(2022, 3), _line(2022, 6), _line(2022, 7)])
    january = cells[("2022", "planned_january", "count")]
    february_june = cells[("2022", "planned_february_june", "count")]
    assert (january.numerator, january.denominator) == (1, 4)
    assert (february_june.numerator, february_june.denominator) == (2, 4)
    assert january.ratio == pytest.approx(0.25)
    assert february_june.ratio == pytest.approx(0.5)


def test_i8_only_direct_awards_count() -> None:
    cells = _cells([_line(2022, 1), _line(2022, 1, direct=False)])
    assert cells[("2022", "planned_january", "count")].denominator == 1


def test_i8_value_skips_lines_without_value() -> None:
    cells = _cells(
        [_line(2022, 1, value=300), _line(2022, 4, value=100), _line(2022, 4, value=None)]
    )
    count = cells[("2022", "planned_february_june", "count")]
    value = cells[("2022", "planned_february_june", "value")]
    assert (count.numerator, count.denominator) == (2, 3)
    assert (value.numerator, value.denominator, value.sample_size) == (100, 400, 2)
    assert value.ratio == pytest.approx(0.25)


def test_i8_cells_are_district_yearly_and_sorted() -> None:
    cells = build_planned_share(_connection([_line(2023, 1), _line(2022, 2)]))
    assert {(c.indicator, c.level, c.department) for c in cells} == {("I8", "district", None)}
    assert [c.period for c in cells] == sorted(c.period for c in cells)
    assert {c.period for c in cells} == {"2022", "2023"}


def test_i8_year_without_direct_awards_emits_no_cell() -> None:
    assert build_planned_share(_connection([_line(2022, 1, direct=False)])) == []


@pytest.fixture(scope="module")
def real_plan() -> duckdb.DuckDBPyConnection:
    return build(SNAPSHOT_DIR)


def test_golden_i8_2022_planned_shares_by_count(real_plan) -> None:
    cells = {(c.period, c.variant, c.measure): c for c in build_planned_share(real_plan)}
    january = cells[("2022", "planned_january", "count")]
    february_june = cells[("2022", "planned_february_june", "count")]
    assert (january.numerator, january.denominator) == (726, 1383)
    assert (february_june.numerator, february_june.denominator) == (115, 1383)


def test_golden_i8_covers_2014_to_2023_and_is_never_suppressed(real_plan) -> None:
    cells = build_planned_share(real_plan)
    assert {c.period for c in cells} == {str(year) for year in range(2014, 2024)}
    published = publish_indicators(cells).cells
    assert len(published) == len(cells)
    assert not any(cell.is_suppressed for cell in published)
