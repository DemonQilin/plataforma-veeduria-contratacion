"""I1 · Proporción de contratación directa (R6, R7, R8, D1, D2; docs/indicadores.md §1)."""

from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from veeduria.indicators.i1_direct_award_share import build_direct_award_share
from veeduria.pipeline import build

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"


def _connection(rows: list[tuple]) -> duckdb.DuckDBPyConnection:
    """`linked_contracts` mínima con las columnas que lee I1."""
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE linked_contracts (signed_date TIMESTAMP, direct_award BOOLEAN,"
        " procurement_method VARCHAR, initial_value DECIMAL(18, 2), is_value_eligible BOOLEAN,"
        " department VARCHAR)"
    )
    for row in rows:
        connection.execute("INSERT INTO linked_contracts VALUES (?, ?, ?, ?, ?, ?)", row)
    return connection


def _row(
    signed="2022-03-10 00:00:00",
    *,
    method="direct_award",
    value=100,
    eligible=True,
    department="treasury",
):
    direct = method == "direct_award"
    return (signed, direct, method, None if value is None else Decimal(value), eligible, department)


def _cells(rows):
    return {
        (c.period, c.variant, c.measure, c.level, c.department): c
        for c in build_direct_award_share(_connection(rows))
    }


def test_i1_direct_award_share_by_count() -> None:
    cells = _cells([_row(), _row(), _row(method="public_tender"), _row(method="minimum_amount")])
    cell = cells[("2022", None, "count", "district", None)]
    assert (cell.numerator, cell.denominator, cell.sample_size) == (2, 4, 4)
    assert cell.ratio == pytest.approx(0.5)
    assert cell.indicator == "I1"
    assert cell.is_suppressed is False


def test_i1_d2_main_variant_leaves_special_regime_out_of_the_numerator() -> None:
    cells = _cells([_row(), _row(method="special_regime"), _row(method="public_tender")])
    main = cells[("2022", None, "count", "district", None)]
    assert (main.numerator, main.denominator) == (1, 3)


def test_i1_d2_non_competitive_adds_special_regime() -> None:
    cells = _cells([_row(), _row(method="special_regime"), _row(method="public_tender")])
    cell = cells[("2022", "non_competitive", "count", "district", None)]
    assert (cell.numerator, cell.denominator) == (2, 3)


def test_i1_r7_value_excludes_public_credit_and_null_values() -> None:
    cells = _cells(
        [
            _row(value=300),
            _row(method="public_tender", value=100),
            _row(value=900, eligible=False),
            _row(value=None),
        ]
    )
    count = cells[("2022", None, "count", "district", None)]
    value = cells[("2022", None, "value", "district", None)]
    assert (count.numerator, count.denominator) == (3, 4)
    assert (value.numerator, value.denominator, value.sample_size) == (300, 400, 2)
    assert value.ratio == pytest.approx(0.75)


def test_i1_r8_department_cells_include_unassigned_and_add_up_to_district() -> None:
    rows = [
        _row(department="treasury"),
        _row(department="treasury", method="public_tender"),
        _row(department="health"),
        _row(department="unassigned"),
        _row(department="unassigned", method="public_tender"),
    ]
    cells = _cells(rows)
    assert {key[4] for key in cells if key[3] == "department"} == {
        "treasury",
        "health",
        "unassigned",
    }
    district = cells[("2022", None, "count", "district", None)]
    departments = [c for key, c in cells.items() if key[1:4] == (None, "count", "department")]
    assert sum(c.numerator for c in departments) == district.numerator
    assert sum(c.denominator for c in departments) == district.denominator
    unassigned = cells[("2022", None, "count", "department", "unassigned")]
    assert (unassigned.numerator, unassigned.denominator) == (1, 2)


def test_i1_department_without_contracts_in_a_year_emits_no_cell() -> None:
    cells = _cells([_row(department="treasury"), _row("2023-02-01 00:00:00", department="health")])
    assert ("2022", None, "count", "department", "health") not in cells
    assert ("2023", None, "count", "department", "treasury") not in cells


def test_i1_publishes_every_year_present_including_the_partial_cutoff_year() -> None:
    cells = _cells(
        [_row("2022-03-10 00:00:00"), _row("2025-12-31 00:00:00"), _row("2026-10-30 00:00:00")]
    )
    periods = {key[0] for key in cells}
    assert periods == {"2022", "2025", "2026"}


def test_i1_value_cell_is_omitted_when_no_contract_has_value() -> None:
    cells = _cells([_row(value=None), _row(value=900, eligible=False)])
    assert ("2022", None, "value", "district", None) not in cells
    assert ("2022", None, "count", "district", None) in cells


@pytest.fixture(scope="module")
def real_linked() -> duckdb.DuckDBPyConnection:
    if not (SNAPSHOT_DIR / "secop_contracts.csv").exists():
        pytest.skip("No hay copia de datos.")
    return build(SNAPSHOT_DIR)


def test_golden_i1_2022_district_counts(real_linked) -> None:
    cells = {
        (c.period, c.variant, c.measure, c.level, c.department): c
        for c in build_direct_award_share(real_linked)
    }
    direct = cells[("2022", None, "count", "district", None)]
    non_competitive = cells[("2022", "non_competitive", "count", "district", None)]
    # 2022: 1.716 contratos, 1.387 directos (coincide con el denominador de I8) y 76 de
    # régimen especial (docs/bitacora.md).
    assert (direct.numerator, direct.denominator) == (1387, 1716)
    assert (non_competitive.numerator, non_competitive.denominator) == (1463, 1716)


def test_golden_i1_district_value_by_year(real_linked) -> None:
    """Valor inicial sin crédito público (R7, D3), verificado aparte contra los CSV (C4)."""
    cells = {
        (c.period, c.variant, c.measure, c.level, c.department): c
        for c in build_direct_award_share(real_linked)
    }
    expected = {
        ("2022", None): (1916233975757.0, 2791146036155.44, 1714),
        ("2023", None): (1866565769282.0, 3760558108849.0, 1666),
        ("2024", None): (2501013379477.41, 3684382611042.83, 1285),
        ("2025", None): (5077549775211.0, 6595801305008.82, 1446),
        ("2026", None): (1916087544312.0, 2886199314029.01, 1306),
        ("2022", "non_competitive"): (2010614108055.0, 2791146036155.44, 1714),
        ("2023", "non_competitive"): (3310482034405.0, 3760558108849.0, 1666),
        ("2024", "non_competitive"): (2867068127851.41, 3684382611042.83, 1285),
        ("2025", "non_competitive"): (5457159517105.0, 6595801305008.82, 1446),
        ("2026", "non_competitive"): (1958365438458.0, 2886199314029.01, 1306),
    }
    observed = {
        (period, variant): (
            cells[(period, variant, "value", "district", None)].numerator,
            cells[(period, variant, "value", "district", None)].denominator,
            cells[(period, variant, "value", "district", None)].sample_size,
        )
        for period, variant in expected
    }
    assert observed == expected
