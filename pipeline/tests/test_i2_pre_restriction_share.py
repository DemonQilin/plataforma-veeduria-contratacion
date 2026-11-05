"""I2 · Concentración pre-restricción (R7, R11, R12; docs/indicadores.md §3)."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from veeduria.indicators.electoral_calendar import (
    ComparisonWindow,
    comparison_windows,
    load_electoral_calendar,
)
from veeduria.indicators.i2_pre_restriction_share import build_pre_restriction_share
from veeduria.pipeline import build
from veeduria.publish.indicators import publish_indicators

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"

WINDOW_2022 = ComparisonWindow(
    year=2022,
    role="treatment",
    window_start=date(2022, 1, 1),
    window_end=date(2022, 1, 28),
    denominator_end=date(2022, 10, 30),
    restriction_end=date(2022, 6, 19),
)


def _connection(rows: list[tuple]) -> duckdb.DuckDBPyConnection:
    """`linked_contracts` mínima con las columnas que lee I2."""
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE linked_contracts (contract_reference VARCHAR, signed_date TIMESTAMP,"
        " direct_award BOOLEAN, contract_type VARCHAR, initial_value DECIMAL(18, 2),"
        " final_value DECIMAL(18, 2), is_value_eligible BOOLEAN)"
    )
    for row in rows:
        connection.execute("INSERT INTO linked_contracts VALUES (?, ?, ?, ?, ?, ?, ?)", row)
    return connection


def _row(reference, signed, *, direct=True, kind="service_contract", initial=100, final=None):
    eligible = kind != "public_credit"
    return (
        reference,
        signed,
        direct,
        kind,
        Decimal(initial),
        Decimal(final if final is not None else initial),
        eligible,
    )


def _cells(rows, windows=(WINDOW_2022,)):
    cells = build_pre_restriction_share(_connection(rows), list(windows))
    return {(c.variant, c.measure): c for c in cells}


def test_i2_r11_window_end_is_inclusive() -> None:
    cells = _cells(
        [
            _row("a", "2022-01-28 23:00:00"),
            _row("b", "2022-01-29 00:00:00"),
            _row("c", "2022-03-01 00:00:00"),
        ]
    )
    cell = cells[(None, "count")]
    assert (cell.numerator, cell.denominator) == (1, 3)
    assert cell.ratio == pytest.approx(1 / 3, abs=1e-6)


def test_i2_r12_denominator_stops_at_cutoff_day() -> None:
    cells = _cells([_row("a", "2022-01-10"), _row("b", "2022-10-30"), _row("c", "2022-10-31")])
    assert cells[(None, "count")].denominator == 2


def test_i2_only_direct_awards_count() -> None:
    cells = _cells([_row("a", "2022-01-10"), _row("b", "2022-01-11", direct=False)])
    assert (cells[(None, "count")].numerator, cells[(None, "count")].denominator) == (1, 1)


def test_i2_r7_public_credit_counts_in_count_not_in_value() -> None:
    cells = _cells(
        [
            _row("a", "2022-01-10", initial=100),
            _row("b", "2022-01-11", kind="public_credit", initial=900),
        ]
    )
    assert cells[(None, "count")].denominator == 2
    value = cells[(None, "value")]
    assert (value.numerator, value.denominator, value.sample_size) == (100, 100, 1)


def test_i2_value_uses_initial_value() -> None:
    cells = _cells([_row("a", "2022-01-10", initial=100, final=500)])
    assert cells[(None, "value")].numerator == 100


def test_i2_variants_split_service_contracts_and_the_rest() -> None:
    cells = _cells(
        [
            _row("a", "2022-01-10", kind="service_contract"),
            _row("b", "2022-03-10", kind="service_contract"),
            _row("c", "2022-01-12", kind="works"),
            _row("d", "2022-04-12", kind="supply_and_purchase"),
            _row("e", "2022-05-12", kind="other"),
        ]
    )
    assert (
        cells[("service_contract", "count")].numerator,
        cells[("service_contract", "count")].denominator,
    ) == (1, 2)
    assert (
        cells[("non_service_contract", "count")].numerator,
        cells[("non_service_contract", "count")].denominator,
    ) == (1, 3)
    assert (cells[(None, "count")].numerator, cells[(None, "count")].denominator) == (2, 5)
    assert cells[("non_service_contract", "count")].sample_size == 3


def test_i2_cells_are_district_yearly_and_sorted() -> None:
    window_2023 = ComparisonWindow(
        year=2023,
        role="control",
        window_start=date(2023, 1, 1),
        window_end=date(2023, 1, 29),
        denominator_end=date(2023, 10, 30),
        restriction_end=None,
    )
    cells = build_pre_restriction_share(
        _connection([_row("a", "2023-01-05"), _row("b", "2022-01-05")]),
        [WINDOW_2022, window_2023],
    )
    assert {(c.indicator, c.level, c.department) for c in cells} == {("I2", "district", None)}
    assert [c.period for c in cells] == sorted(c.period for c in cells)
    assert {c.period for c in cells} == {"2022", "2023"}
    assert publish_indicators(cells).cells == cells or all(
        not c.is_suppressed for c in publish_indicators(cells).cells
    )


def test_i2_year_without_direct_awards_emits_no_cell() -> None:
    assert (
        build_pre_restriction_share(
            _connection([_row("a", "2022-01-10", direct=False)]), [WINDOW_2022]
        )
        == []
    )


@pytest.fixture(scope="module")
def real_linked() -> duckdb.DuckDBPyConnection:
    return build(SNAPSHOT_DIR)


def test_golden_i2_linked_contracts_january_2022_has_723_direct_awards(real_linked) -> None:
    assert real_linked.execute(
        "SELECT count(*) FROM linked_contracts WHERE direct_award"
        " AND signed_date >= '2022-01-01' AND signed_date < '2022-02-01'"
    ).fetchone() == (723,)


def test_golden_i2_2022_total_by_count(real_linked) -> None:
    cutoff = date(2026, 10, 30)
    cells = build_pre_restriction_share(
        real_linked, comparison_windows(load_electoral_calendar(), cutoff)
    )
    cell = next(c for c in cells if (c.period, c.variant, c.measure) == ("2022", None, "count"))
    assert (cell.numerator, cell.denominator) == (723, 1240)


def test_golden_i2_every_window_year_has_a_published_total(real_linked) -> None:
    cutoff = date(2026, 10, 30)
    windows = comparison_windows(load_electoral_calendar(), cutoff)
    cells = build_pre_restriction_share(real_linked, windows)
    totals = {c.period for c in cells if c.variant is None and c.measure == "count"}
    assert totals == {"2022", "2023", "2024", "2025", "2026"}
