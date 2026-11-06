"""I5 · Adiciones desde MEData y la variante cerca del tope (R7, R8, R13; ADR 0044)."""

from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.indicators.i5_additions import build_additions
from veeduria.pipeline import build
from veeduria.publish.indicators import publish_indicators

SNAPSHOT = REPO_ROOT / "data" / "snapshot"


def _contract(number: int, **overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "contract_reference": f"CO1.PCCNTR.{number}",
        "signed_date": datetime(2022, 3, 1),
        "department": "supplies_and_services",
        "in_medata": True,
        "is_value_eligible": True,
        "initial_value": 100.0,
        "total_addition_value": 0.0,
    }
    values.update(overrides)
    return values


def _connection(contracts: list[dict[str, Any]]) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE linked_contracts (contract_reference VARCHAR, signed_date TIMESTAMP,"
        " department VARCHAR, in_medata BOOLEAN, is_value_eligible BOOLEAN)"
    )
    connection.execute(
        "CREATE TABLE medata_contracts (contract_reference VARCHAR, signed_date TIMESTAMP,"
        " initial_value DECIMAL(18, 2), total_addition_value DECIMAL(18, 2))"
    )
    for contract in contracts:
        connection.execute(
            "INSERT INTO linked_contracts VALUES (?, ?, ?, ?, ?)",
            [
                contract["contract_reference"],
                contract["signed_date"],
                contract["department"],
                contract["in_medata"],
                contract["is_value_eligible"],
            ],
        )
        if contract["in_medata"]:
            connection.execute(
                "INSERT INTO medata_contracts VALUES (?, ?, ?, ?)",
                [
                    contract["contract_reference"],
                    contract.get("medata_signed_date", contract["signed_date"]),
                    contract["initial_value"],
                    contract["total_addition_value"],
                ],
            )
    return connection


def _cells(
    connection: duckdb.DuckDBPyConnection,
) -> dict[tuple[str, str | None, str, str | None, str], tuple]:
    return {
        (cell.level, cell.department, cell.period, cell.variant, cell.measure): (
            cell.numerator,
            cell.denominator,
            cell.sample_size,
        )
        for cell in build_additions(connection)
    }


def test_i5_count_is_contracts_with_an_addition_over_contracts_in_medata() -> None:
    connection = _connection(
        [
            _contract(1, total_addition_value=10.0),
            _contract(2),
            _contract(3),
            _contract(4, in_medata=False),
        ]
    )
    assert _cells(connection)[("district", None, "2022", None, "count")] == (1.0, 3.0, 3)


def test_i5_contracts_without_a_reported_addition_amount_are_left_out() -> None:
    connection = _connection([_contract(1, total_addition_value=10.0), _contract(2)])
    connection.execute(
        "UPDATE medata_contracts SET total_addition_value = NULL"
        " WHERE contract_reference = 'CO1.PCCNTR.2'"
    )
    assert _cells(connection)[("district", None, "2022", None, "count")] == (1.0, 1.0, 1)


def test_i5_value_is_added_value_over_medata_initial_value_without_public_credit() -> None:
    connection = _connection(
        [
            _contract(1, initial_value=100.0, total_addition_value=30.0),
            _contract(2, initial_value=300.0),
            _contract(3, initial_value=1000.0, total_addition_value=500.0, is_value_eligible=False),
        ]
    )
    cells = _cells(connection)
    # R7: el crédito público cuenta en el conteo y no en el valor.
    assert cells[("district", None, "2022", None, "count")] == (2.0, 3.0, 3)
    assert cells[("district", None, "2022", None, "value")] == (30.0, 400.0, 2)


def test_i5_near_cap_counts_contracts_at_or_above_45_percent_of_the_initial_value() -> None:
    connection = _connection(
        [
            _contract(1, total_addition_value=45.0),
            _contract(2, total_addition_value=50.0),
            _contract(3, total_addition_value=44.0),
            _contract(4),
        ]
    )
    cells = _cells(connection)
    # El denominador son los contratos con adición; los que no tienen no entran.
    assert cells[("district", None, "2022", "near_addition_cap", "count")] == (2.0, 3.0, 3)
    assert ("district", None, "2022", "near_addition_cap", "value") not in cells


def test_i5_departments_use_r8_and_add_up_to_the_district() -> None:
    connection = _connection(
        [
            _contract(1, total_addition_value=10.0),
            _contract(2, department="security"),
            _contract(3, department="unassigned"),
        ]
    )
    cells = _cells(connection)
    departments = {
        key[1]: value
        for key, value in cells.items()
        if key[0] == "department" and key[3] is None and key[4] == "count"
    }
    assert departments == {
        "supplies_and_services": (1.0, 1.0, 1),
        "security": (0.0, 1.0, 1),
        "unassigned": (0.0, 1.0, 1),
    }
    assert cells[("district", None, "2022", None, "count")] == (1.0, 3.0, 3)


def test_i5_has_one_cell_set_per_signed_year() -> None:
    connection = _connection(
        [
            _contract(1, signed_date=datetime(2022, 1, 5)),
            _contract(2, signed_date=datetime(2023, 6, 30), total_addition_value=5.0),
            _contract(3, signed_date=None),
        ]
    )
    periods = {cell.period for cell in build_additions(connection)}
    assert periods == {"2022", "2023"}
    assert all(
        cell.indicator == "I5" and not cell.is_suppressed for cell in build_additions(connection)
    )


def test_i5_ratio_is_rounded_and_reconstructible() -> None:
    connection = _connection([_contract(1, total_addition_value=10.0), _contract(2), _contract(3)])
    (cell,) = [
        c
        for c in build_additions(connection)
        if c.level == "district" and c.measure == "count" and c.variant is None
    ]
    assert (cell.numerator, cell.denominator, cell.ratio) == (1.0, 3.0, 0.333333)


def test_r13_i5_small_department_cells_are_suppressed_and_district_is_published() -> None:
    connection = _connection(
        [_contract(n, total_addition_value=10.0 if n % 2 else 0.0) for n in range(1, 10)]
        + [_contract(20, department="security", total_addition_value=10.0)]
    )
    cells = {
        (cell.level, cell.department): cell
        for cell in publish_indicators(build_additions(connection)).cells
        if cell.measure == "count" and cell.variant is None
    }
    assert not cells[("district", None)].is_suppressed
    assert cells[("department", "security")].is_suppressed
    # D6: con una sola secretaría suprimida, la complementaria oculta también la mayor.
    assert cells[("department", "supplies_and_services")].is_suppressed


def test_i5_period_follows_the_medata_signed_date() -> None:
    connection = _connection(
        [
            # SECOP II lo fecha en 2023, pero MEData lo firma en 2022: cuenta en 2022.
            _contract(
                1,
                signed_date=datetime(2023, 1, 25),
                medata_signed_date=datetime(2022, 12, 30),
                total_addition_value=10.0,
            ),
            # SECOP II lo fecha el 4 de julio de 2023, fuera de la cobertura de MEData.
            _contract(
                2,
                signed_date=datetime(2023, 7, 4),
                medata_signed_date=datetime(2023, 6, 30),
            ),
        ]
    )
    cells = _cells(connection)
    assert cells[("district", None, "2022", None, "count")] == (1.0, 1.0, 1)
    assert cells[("district", None, "2023", None, "count")] == (0.0, 1.0, 1)
    assert {key[2] for key in cells} == {"2022", "2023"}


def test_r13_i5_near_cap_cell_is_suppressed_when_its_count_cell_is() -> None:
    # El denominador de la variante es el numerador del conteo: si el conteo está oculto, la
    # variante también, o se despejaría restando.
    connection = _connection(
        [_contract(n, total_addition_value=50.0 if n <= 5 else 0.0) for n in range(1, 7)]
        + [_contract(20, department="security")]
    )
    cells = {
        (cell.department, cell.variant, cell.measure): cell
        for cell in publish_indicators(build_additions(connection)).cells
        if cell.level == "department"
    }
    # D6: «security» tiene un solo contrato; se suprime y arrastra a la otra secretaría.
    assert cells[("supplies_and_services", None, "count")].is_suppressed
    assert cells[("supplies_and_services", "near_addition_cap", "count")].is_suppressed


@pytest.fixture(scope="module")
def real() -> duckdb.DuckDBPyConnection:
    return build(Path(SNAPSHOT))


def test_i5_golden_district_by_year(real: duckdb.DuckDBPyConnection) -> None:
    cells = _cells(real)
    expected = {
        # ADR 0047: los 200 cruces por «NNNNNNNNNN de AAAA» suman 108 contratos en 2022 y 85 en
        # 2023; las cifras se verificaron aparte contra los CSV de la copia.
        ("2022", None, "count"): (387.0, 1632.0, 1632),
        ("2023", None, "count"): (69.0, 1165.0, 1165),
        ("2022", None, "value"): (130639475795.0, 1838029562783.0, 1632),
        ("2023", None, "value"): (32444774397.0, 1607084459701.0, 1163),
        ("2022", "near_addition_cap", "count"): (164.0, 387.0, 387),
        ("2023", "near_addition_cap", "count"): (25.0, 69.0, 69),
    }
    assert {
        (period, variant, measure): cells[("district", None, period, variant, measure)]
        for period, variant, measure in expected
    } == expected
    # MEData cubre contratos firmados hasta el 30 de junio de 2023.
    assert {cell.period for cell in build_additions(real)} == {"2022", "2023"}


def test_i5_golden_departments_add_up_to_the_district(real: duckdb.DuckDBPyConnection) -> None:
    totals: dict[tuple[str, str | None, str], list[float]] = {}
    district: dict[tuple[str, str | None, str], list[float]] = {}
    for cell in build_additions(real):
        key = (cell.period, cell.variant, cell.measure)
        target = district if cell.level == "district" else totals
        figures = target.setdefault(key, [0.0, 0.0, 0.0])
        figures[0] += cell.numerator or 0.0
        figures[1] += cell.denominator or 0.0
        figures[2] += cell.sample_size
    assert totals == district
    assert {key[2] for key in district} == {"count", "value"}
