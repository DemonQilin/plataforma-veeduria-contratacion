"""Serie mensual (R7, R12, R13, D3, D4, D6; docs/reglas.md §7 y ADR 0040)."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from veeduria.indicators.i1_direct_award_share import build_direct_award_share
from veeduria.indicators.monthly_series import build_monthly_series
from veeduria.pipeline import build
from veeduria.publish.models import MonthlySeries, MonthlySeriesRow
from veeduria.publish.series import publish_monthly_series
from veeduria.publish.suppression import SUPPRESSION_THRESHOLD

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"
CUTOFF = date(2022, 3, 31)


def _connection(rows: list[tuple]) -> duckdb.DuckDBPyConnection:
    """`linked_contracts` mínima con las columnas que lee la serie."""
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE linked_contracts (signed_date TIMESTAMP, procurement_method VARCHAR,"
        " contract_type VARCHAR, initial_value DECIMAL(18, 2), is_value_eligible BOOLEAN)"
    )
    for row in rows:
        connection.execute("INSERT INTO linked_contracts VALUES (?, ?, ?, ?, ?)", row)
    return connection


def _row(
    signed="2022-01-10 00:00:00",
    *,
    method="direct_award",
    kind="service_contract",
    value=100,
    eligible=True,
):
    return (signed, method, kind, None if value is None else Decimal(value), eligible)


def _rows(contracts, cutoff=CUTOFF):
    return build_monthly_series(_connection(contracts), cutoff)


def _by_key(rows):
    return {(r.period, r.procurement_method, r.contract_type): r for r in rows}


def _series_row(
    period="2022-01",
    method=None,
    kind=None,
    *,
    count=10,
    sample=10,
    value=1000.0,
    suppressed=False,
):
    return MonthlySeriesRow(
        period=period,
        procurement_method=method,
        contract_type=kind,
        contract_count=count,
        value_sample_size=sample,
        value=None if suppressed else value,
        is_suppressed=suppressed,
    )


def test_series_counts_and_value_by_month_method_and_type() -> None:
    rows = _by_key(
        _rows([_row(value=100), _row(value=50), _row(method="public_tender", kind="works")])
    )
    leaf = rows[("2022-01", "direct_award", "service_contract")]
    assert (leaf.contract_count, leaf.value_sample_size, leaf.value) == (2, 2, 150.0)
    other = rows[("2022-01", "public_tender", "works")]
    assert (other.contract_count, other.value) == (1, 100.0)


def test_series_margins_add_up() -> None:
    rows = _by_key(
        _rows(
            [
                _row(),
                _row(kind="works"),
                _row(method="public_tender", kind="works"),
                _row(method="public_tender", kind="works", value=40),
            ]
        )
    )
    total = rows[("2022-01", None, None)]
    assert (total.contract_count, total.value) == (4, 340.0)
    by_method = rows[("2022-01", "direct_award", None)]
    assert (by_method.contract_count, by_method.value) == (2, 200.0)
    by_type = rows[("2022-01", None, "works")]
    assert (by_type.contract_count, by_type.value) == (3, 240.0)


def test_r7_series_value_excludes_public_credit_and_null_values() -> None:
    rows = _by_key(_rows([_row(value=300), _row(value=900, eligible=False), _row(value=None)]))
    total = rows[("2022-01", None, None)]
    assert total.contract_count == 3
    assert (total.value_sample_size, total.value) == (1, 300.0)


def test_r12_series_runs_from_first_signed_month_to_cutoff_month_with_explicit_zeros() -> None:
    rows = _rows([_row("2022-01-10 00:00:00")], cutoff=date(2022, 3, 15))
    total = [r for r in rows if r.procurement_method is None and r.contract_type is None]
    assert [r.period for r in total] == ["2022-01", "2022-02", "2022-03"]
    assert [r.contract_count for r in total] == [1, 0, 0]
    assert total[1].value == 0.0


def test_r12_series_ignores_contracts_signed_after_the_cutoff() -> None:
    rows = _rows([_row("2022-01-10 00:00:00"), _row("2022-04-02 00:00:00")], cutoff=CUTOFF)
    assert "2022-04" not in {r.period for r in rows}


def test_r2_series_ignores_contracts_without_signed_date() -> None:
    rows = _rows([_row(None), _row()])
    assert _by_key(rows)[("2022-01", None, None)].contract_count == 1


def test_r13_series_count_is_published_and_value_suppressed_below_five() -> None:
    contracts = [_row() for _ in range(3)] + [_row(kind="works") for _ in range(6)]
    published = _by_key(publish_monthly_series(_rows(contracts)).rows)
    small = published[("2022-01", "direct_award", "service_contract")]
    assert small.contract_count == 3
    assert small.is_suppressed is True
    assert small.value is None
    assert small.value_sample_size == 3


def test_r13_series_value_of_five_contracts_is_published() -> None:
    published = _by_key(publish_monthly_series(_rows([_row() for _ in range(5)])).rows)
    cell = published[("2022-01", "direct_award", "service_contract")]
    assert (cell.is_suppressed, cell.value) == (False, 500.0)


def test_r13_series_month_without_contracts_is_published_as_zero() -> None:
    rows = publish_monthly_series(_rows([_row() for _ in range(5)], cutoff=date(2022, 2, 28))).rows
    february = _by_key(rows)[("2022-02", None, None)]
    assert (february.contract_count, february.value, february.is_suppressed) == (0, 0.0, False)


def test_r13_series_value_sample_below_five_is_suppressed_even_with_many_contracts() -> None:
    contracts = [_row() for _ in range(2)] + [_row(value=None) for _ in range(8)]
    published = _by_key(publish_monthly_series(_rows(contracts)).rows)
    total = published[("2022-01", None, None)]
    assert (total.contract_count, total.value_sample_size) == (10, 2)
    assert total.is_suppressed is True


def test_d6_series_single_suppressed_type_hides_the_smallest_other_type() -> None:
    rows = publish_monthly_series(
        [
            _series_row(method="direct_award", kind=None, count=20, sample=20),
            _series_row(method="direct_award", kind="service_contract", count=3, sample=3),
            _series_row(method="direct_award", kind="works", count=7, sample=7),
            _series_row(method="direct_award", kind="other", count=10, sample=10),
        ]
    ).rows
    hidden = {r.contract_type for r in rows if r.is_suppressed}
    assert hidden == {"service_contract", "works"}


def test_d6_series_single_suppressed_method_hides_the_smallest_other_method() -> None:
    rows = publish_monthly_series(
        [
            _series_row(count=20, sample=20),
            _series_row(method="direct_award", count=3, sample=3),
            _series_row(method="public_tender", count=8, sample=8),
            _series_row(method="special_regime", count=9, sample=9),
        ]
    ).rows
    hidden = {r.procurement_method for r in rows if r.is_suppressed}
    assert hidden == {"direct_award", "public_tender"}


def test_d6_series_single_suppressed_month_hides_the_smallest_other_month() -> None:
    rows = publish_monthly_series(
        [
            _series_row("2022-01", count=3, sample=3),
            _series_row("2022-02", count=9, sample=9),
            _series_row("2022-03", count=12, sample=12),
            _series_row("2023-01", count=3, sample=3),
        ]
    ).rows
    hidden = {r.period for r in rows if r.is_suppressed}
    # 2022 queda con un mes suprimido, así que se oculta también el menor de los demás; 2023 no
    # tiene otro mes que ocultar.
    assert hidden == {"2022-01", "2022-02", "2023-01"}


def test_d6_series_complementary_never_hides_a_zero_value_cell() -> None:
    rows = publish_monthly_series(
        [
            _series_row(method="direct_award", kind=None, count=3, sample=3),
            _series_row(method="direct_award", kind="service_contract", count=3, sample=3),
            _series_row(method="direct_award", kind="works", count=0, sample=0, value=0.0),
        ]
    ).rows
    zero = next(r for r in rows if r.contract_type == "works")
    assert zero.is_suppressed is False


def test_series_row_rejects_value_with_suppression() -> None:
    with pytest.raises(ValueError):
        MonthlySeriesRow(
            period="2022-01",
            procurement_method=None,
            contract_type=None,
            contract_count=3,
            value_sample_size=3,
            value=10.0,
            is_suppressed=True,
        )


def test_series_row_rejects_more_valued_contracts_than_contracts() -> None:
    with pytest.raises(ValueError):
        _series_row(count=2, sample=3)


def test_series_rows_are_sorted_by_period_then_method_then_type() -> None:
    rows = publish_monthly_series(
        _rows([_row("2022-02-01 00:00:00"), _row("2022-01-05 00:00:00", method="public_tender")])
    ).rows
    keys = [(r.period, r.procurement_method or "", r.contract_type or "") for r in rows]
    assert keys == sorted(keys)


@pytest.fixture(scope="module")
def real_linked() -> duckdb.DuckDBPyConnection:
    if not (SNAPSHOT_DIR / "secop_contracts.csv").exists():
        pytest.skip("No hay copia de datos.")
    return build(SNAPSHOT_DIR)


def test_r13_published_series_never_shows_a_value_backed_by_one_to_four_contracts() -> None:
    path = SNAPSHOT_DIR.parent / "outputs" / "monthly_series.json"
    if not path.exists():
        pytest.skip("No hay salida publicada.")
    series = MonthlySeries.model_validate(json.loads(path.read_text(encoding="utf-8")))
    assert series.rows
    for row in series.rows:
        if row.value is not None:
            assert not 0 < row.value_sample_size < SUPPRESSION_THRESHOLD


def test_golden_series_direct_award_matches_i1_numerators_by_year(real_linked) -> None:
    cutoff = real_linked.execute(
        "SELECT max(signed_date)::DATE FROM canonical_contracts"
    ).fetchone()[0]
    series = [
        r
        for r in build_monthly_series(real_linked, cutoff)
        if r.procurement_method == "direct_award" and r.contract_type is None
    ]
    i1 = {
        (c.period, c.measure): c
        for c in build_direct_award_share(real_linked)
        if c.level == "district" and c.variant is None
    }
    for year in sorted({r.period[:4] for r in series}):
        months = [r for r in series if r.period.startswith(year)]
        count = i1[(year, "count")]
        value = i1.get((year, "value"))
        assert sum(r.contract_count for r in months) == count.numerator
        if value is not None:
            assert sum(r.value for r in months) == pytest.approx(value.numerator)
