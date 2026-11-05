"""I2 · Factor de confusión 3: contratos de enero que terminan después de la restricción
(R11; docs/indicadores.md §3)."""

from datetime import date
from pathlib import Path

import duckdb
import pytest

from veeduria.indicators.electoral_calendar import (
    ComparisonWindow,
    comparison_windows,
    load_electoral_calendar,
)
from veeduria.indicators.i2_restriction_span import build_restriction_span
from veeduria.pipeline import build

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"

WINDOW_2022 = ComparisonWindow(
    year=2022,
    role="treatment",
    window_start=date(2022, 1, 1),
    window_end=date(2022, 1, 28),
    denominator_end=date(2022, 10, 30),
    restriction_end=date(2022, 6, 19),
    reference_restriction_end=date(2022, 6, 19),
)
WINDOW_2024 = ComparisonWindow(
    year=2024,
    role="control",
    window_start=date(2024, 1, 1),
    window_end=date(2024, 1, 29),
    denominator_end=date(2024, 10, 30),
    restriction_end=None,
    reference_restriction_end=date(2024, 6, 20),
)


def _connection(rows: list[tuple]) -> duckdb.DuckDBPyConnection:
    """`linked_contracts` mínima con las columnas que lee esta señal."""
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE linked_contracts (contract_reference VARCHAR, signed_date TIMESTAMP,"
        " direct_award BOOLEAN, end_date TIMESTAMP, added_days INTEGER)"
    )
    for row in rows:
        connection.execute("INSERT INTO linked_contracts VALUES (?, ?, ?, ?, ?)", row)
    return connection


def _row(reference, signed, end, *, direct=True, added=0):
    return (reference, signed, direct, end, added)


def _cell(rows, window=WINDOW_2022):
    cells = build_restriction_span(_connection(rows), [window])
    assert len(cells) <= 1
    return cells[0] if cells else None


def test_i2_end_on_the_reference_day_does_not_span() -> None:
    cell = _cell(
        [
            _row("a", "2022-01-10", "2022-06-19 00:00:00"),
            _row("b", "2022-01-11", "2022-06-20 00:00:00"),
        ]
    )
    assert (cell.numerator, cell.denominator) == (1, 2)


def test_i2_added_days_are_subtracted_from_the_end() -> None:
    cell = _cell(
        [
            _row("a", "2022-01-10", "2022-06-30", added=30),
            _row("b", "2022-01-11", "2022-06-30", added=0),
        ]
    )
    assert (cell.numerator, cell.denominator) == (1, 2)


def test_i2_null_added_days_count_as_zero() -> None:
    cell = _cell([_row("a", "2022-01-10", "2022-06-30", added=None)])
    assert (cell.numerator, cell.denominator) == (1, 1)


def test_i2_window_end_is_inclusive_and_later_contracts_are_out() -> None:
    cell = _cell(
        [
            _row("a", "2022-01-28 23:00:00", "2022-12-01"),
            _row("b", "2022-01-29 00:00:00", "2022-12-01"),
        ]
    )
    assert (cell.numerator, cell.denominator) == (1, 1)


def test_i2_only_direct_awards_count() -> None:
    cell = _cell(
        [
            _row("a", "2022-01-10", "2022-12-01"),
            _row("b", "2022-01-11", "2022-12-01", direct=False),
        ]
    )
    assert (cell.numerator, cell.denominator) == (1, 1)


def test_i2_contracts_without_end_date_are_left_out() -> None:
    cell = _cell(
        [
            _row("a", "2022-01-10", "2022-12-01"),
            _row("b", "2022-01-11", None),
        ]
    )
    assert (cell.numerator, cell.denominator) == (1, 1)


def test_i2_control_year_uses_june_20() -> None:
    cell = _cell(
        [
            _row("a", "2024-01-10", "2024-06-20"),
            _row("b", "2024-01-11", "2024-06-21"),
        ],
        WINDOW_2024,
    )
    assert (cell.numerator, cell.denominator) == (1, 2)


def test_i2_cell_is_a_district_yearly_count_with_its_variant() -> None:
    cell = _cell([_row("a", "2022-01-10", "2022-12-01")])
    assert (cell.indicator, cell.variant, cell.measure, cell.level) == (
        "I2",
        "spans_restriction",
        "count",
        "district",
    )
    assert (cell.department, cell.period, cell.sample_size) == (None, "2022", 1)
    assert cell.ratio == pytest.approx(1.0)
    assert cell.is_suppressed is False


def test_i2_year_without_eligible_contracts_emits_no_cell() -> None:
    assert _cell([_row("a", "2022-01-10", None)]) is None


@pytest.fixture(scope="module")
def real_linked() -> duckdb.DuckDBPyConnection:
    return build(SNAPSHOT_DIR)


def test_golden_i2_restriction_span_2022(real_linked) -> None:
    windows = comparison_windows(load_electoral_calendar(), date(2026, 10, 30))
    cells = build_restriction_span(real_linked, windows)
    cell = next(c for c in cells if c.period == "2022")
    assert (cell.numerator, cell.denominator) == (720, 723)
