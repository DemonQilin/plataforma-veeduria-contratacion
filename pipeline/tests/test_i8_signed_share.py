"""I8 · Comparación de lo planeado con lo firmado (R7, R17; docs/indicadores.md §3)."""

from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from veeduria.indicators.i8_signed_share import build_signed_share
from veeduria.pipeline import build

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"


def _connection(rows: list[tuple]) -> duckdb.DuckDBPyConnection:
    """`linked_contracts` mínima con las columnas que lee la comparación de I8."""
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE linked_contracts (signed_date TIMESTAMP, direct_award BOOLEAN,"
        " initial_value DECIMAL(18, 2), is_value_eligible BOOLEAN)"
    )
    for row in rows:
        connection.execute("INSERT INTO linked_contracts VALUES (?, ?, ?, ?)", row)
    return connection


def _row(signed, *, direct=True, value=100, eligible=True):
    return (signed, direct, None if value is None else Decimal(value), eligible)


def _cells(rows):
    return {(c.period, c.variant, c.measure): c for c in build_signed_share(_connection(rows))}


def test_i8_signed_january_and_february_june_shares() -> None:
    cells = _cells(
        [
            _row("2022-01-15 00:00:00"),
            _row("2022-03-10 00:00:00"),
            _row("2022-06-30 12:00:00"),
            _row("2022-12-31 23:00:00"),
        ]
    )
    january = cells[("2022", "signed_january", "count")]
    february_june = cells[("2022", "signed_february_june", "count")]
    assert (january.numerator, january.denominator) == (1, 4)
    assert (february_june.numerator, february_june.denominator) == (2, 4)
    assert january.ratio == pytest.approx(0.25)
    assert february_june.ratio == pytest.approx(0.5)


def test_i8_signed_only_direct_awards_count() -> None:
    cells = _cells([_row("2022-01-15 00:00:00"), _row("2022-01-16 00:00:00", direct=False)])
    assert cells[("2022", "signed_january", "count")].denominator == 1


def test_i8_signed_value_excludes_public_credit_and_null_values() -> None:
    cells = _cells(
        [
            _row("2022-01-15 00:00:00", value=300),
            _row("2022-04-15 00:00:00", value=100),
            _row("2022-04-16 00:00:00", value=900, eligible=False),
            _row("2022-04-17 00:00:00", value=None),
        ]
    )
    count = cells[("2022", "signed_february_june", "count")]
    value = cells[("2022", "signed_february_june", "value")]
    assert (count.numerator, count.denominator) == (3, 4)
    assert (value.numerator, value.denominator, value.sample_size) == (100, 400, 2)
    assert value.ratio == pytest.approx(0.25)


def test_i8_signed_only_comparison_years() -> None:
    cells = _cells(
        [
            _row("2021-01-15 00:00:00"),
            _row("2023-01-15 00:00:00"),
            _row("2024-01-15 00:00:00"),
        ]
    )
    assert {period for period, _, _ in cells} == {"2023"}


def test_i8_signed_year_without_direct_awards_emits_no_cell() -> None:
    assert _cells([_row("2022-01-15 00:00:00", direct=False)]) == {}


@pytest.fixture(scope="module")
def real_linked() -> duckdb.DuckDBPyConnection:
    if not (SNAPSHOT_DIR / "secop_contracts.csv").exists():
        pytest.skip("No hay copia de datos.")
    return build(SNAPSHOT_DIR)


def test_golden_i8_signed_2022_january_count(real_linked) -> None:
    cells = {(c.period, c.variant, c.measure): c for c in build_signed_share(real_linked)}
    january = cells[("2022", "signed_january", "count")]
    # Enero de 2022: 723 contratos directos en SECOP II (docs/bitacora.md).
    assert january.numerator == 723
