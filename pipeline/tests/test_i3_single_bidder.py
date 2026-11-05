"""I3 · Oferente único y la exclusión de R9 (R5, R8, R9, R13; ADR 0043)."""

from datetime import date, datetime
from pathlib import Path
from typing import Any

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.consolidate.single_bidder_processes import select_single_bidder_processes
from veeduria.indicators.i3_single_bidder import build_single_bidder
from veeduria.pipeline import build
from veeduria.publish.indicators import publish_indicators

SNAPSHOT = REPO_ROOT / "data" / "snapshot"
SUPPLIES = "SUMINISTROS Y SERVICIOS"
SECURITY = "Secretaría de Seguridad y Convivencia"


def _process(number: int, **overrides: Any) -> tuple[Any, ...]:
    values: dict[str, Any] = {
        "procurement_process": f"CO1.BDOS.{number}",
        "competitive": True,
        "awarded": True,
        "published_date": datetime(2023, 3, 1),
        "unique_suppliers": 2,
        "department": SUPPLIES,
    }
    values.update(overrides)
    return (
        values["procurement_process"],
        values["competitive"],
        values["awarded"],
        values["published_date"],
        values["unique_suppliers"],
        values["department"],
    )


def _connection(processes: list[tuple[Any, ...]]) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE canonical_processes (procurement_process VARCHAR, competitive BOOLEAN,"
        " awarded BOOLEAN, published_date TIMESTAMP, unique_suppliers INTEGER, department VARCHAR)"
    )
    connection.executemany("INSERT INTO canonical_processes VALUES (?, ?, ?, ?, ?, ?)", processes)
    connection.execute("CREATE TABLE canonical_contracts (signed_date TIMESTAMP)")
    connection.execute("INSERT INTO canonical_contracts VALUES (TIMESTAMP '2026-10-30')")
    select_single_bidder_processes(connection)
    return connection


def _cells(connection: duckdb.DuckDBPyConnection) -> dict[tuple[str, str | None, str], tuple]:
    return {
        (cell.level, cell.department, cell.period): (
            cell.numerator,
            cell.denominator,
            cell.sample_size,
        )
        for cell in build_single_bidder(connection)
    }


def test_r09_only_competitive_awarded_processes_in_the_period_are_valid() -> None:
    connection = _connection(
        [
            _process(1),
            _process(2, competitive=False),
            _process(3, awarded=False),
            _process(4, awarded=None),
            _process(5, published_date=datetime(2021, 12, 31)),
            _process(6, published_date=datetime(2026, 10, 31)),
            _process(7, published_date=datetime(2026, 10, 30, 15)),
        ]
    )
    rows = connection.execute(
        "SELECT procurement_process FROM single_bidder_processes ORDER BY 1"
    ).fetchall()
    assert rows == [("CO1.BDOS.1",), ("CO1.BDOS.7",)]


def test_r09_zero_or_missing_bidders_are_excluded_and_reported() -> None:
    connection = _connection(
        [_process(1), _process(2, unique_suppliers=0), _process(3, unique_suppliers=None)]
    )
    excluded = connection.execute(
        "SELECT procurement_process FROM single_bidder_processes WHERE is_excluded ORDER BY 1"
    ).fetchall()
    assert excluded == [("CO1.BDOS.2",), ("CO1.BDOS.3",)]
    issues = connection.execute(
        "SELECT rule, record_key FROM quality_issues WHERE rule = 'R9' ORDER BY 2"
    ).fetchall()
    assert issues == [("R9", "CO1.BDOS.2"), ("R9", "CO1.BDOS.3")]


def test_r09_selecting_twice_does_not_duplicate_quality_issues() -> None:
    connection = _connection([_process(1, unique_suppliers=0)])
    select_single_bidder_processes(connection)
    (count,) = connection.execute("SELECT count(*) FROM quality_issues").fetchone() or (0,)
    assert count == 1


def test_i3_counts_single_bidder_over_valid_processes_and_leaves_out_excluded() -> None:
    connection = _connection(
        [
            _process(1, unique_suppliers=1),
            _process(2, unique_suppliers=1),
            _process(3, unique_suppliers=2),
            _process(4, unique_suppliers=5),
            _process(5, unique_suppliers=0),
        ]
    )
    assert _cells(connection)[("district", None, "2023")] == (2.0, 4.0, 4)


def test_i3_departments_use_the_catalog_and_add_up_to_the_district() -> None:
    connection = _connection(
        [
            _process(1, unique_suppliers=1),
            _process(2, department=SECURITY, unique_suppliers=1),
            _process(3, department="UNIDAD QUE NO ESTA EN EL CATALOGO"),
            _process(4, department=None),
        ]
    )
    cells = _cells(connection)
    departments = {key[1]: value for key, value in cells.items() if key[0] == "department"}
    assert departments == {
        "supplies_and_services": (1.0, 1.0, 1),
        "security": (1.0, 1.0, 1),
        "unassigned": (0.0, 2.0, 2),
    }
    assert cells[("district", None, "2023")] == (2.0, 4.0, 4)


def test_i3_has_one_count_cell_per_year_with_the_partial_cutoff_year() -> None:
    connection = _connection(
        [
            _process(1, published_date=datetime(2022, 1, 5)),
            _process(2, published_date=datetime(2026, 2, 1)),
        ]
    )
    cells = build_single_bidder(connection)
    assert {(cell.level, cell.period, cell.measure, cell.variant) for cell in cells} == {
        ("district", "2022", "count", None),
        ("district", "2026", "count", None),
        ("department", "2022", "count", None),
        ("department", "2026", "count", None),
    }
    assert all(cell.indicator == "I3" and not cell.is_suppressed for cell in cells)


def test_i3_ratio_is_rounded_and_reconstructible() -> None:
    connection = _connection([_process(1, unique_suppliers=1), *map(_process, (2, 3))])
    (cell,) = [c for c in build_single_bidder(connection) if c.level == "district"]
    assert (cell.numerator, cell.denominator, cell.ratio) == (1.0, 3.0, 0.333333)


def test_r13_i3_small_department_cells_are_suppressed_and_district_is_published() -> None:
    connection = _connection(
        [_process(n, unique_suppliers=1 if n % 2 else 2) for n in range(1, 10)]
        + [_process(20, department=SECURITY, unique_suppliers=1)]
    )
    cells = {
        (cell.level, cell.department): cell
        for cell in publish_indicators(build_single_bidder(connection)).cells
    }
    assert not cells[("district", None)].is_suppressed
    assert cells[("department", "security")].is_suppressed
    # D6: con una sola secretaría suprimida, la complementaria oculta también la mayor.
    assert cells[("department", "supplies_and_services")].is_suppressed


@pytest.fixture(scope="module")
def real() -> duckdb.DuckDBPyConnection:
    return build(Path(SNAPSHOT))


def test_i3_golden_district_by_year(real: duckdb.DuckDBPyConnection) -> None:
    cells = _cells(real)
    expected = {
        "2022": (44.0, 198.0),
        "2023": (49.0, 164.0),
        "2024": (31.0, 194.0),
        "2025": (25.0, 173.0),
        "2026": (21.0, 144.0),
    }
    assert {year: cells[("district", None, year)][:2] for year in expected} == expected


def test_r09_golden_excluded_processes(real: duckdb.DuckDBPyConnection) -> None:
    excluded, total = real.execute(
        "SELECT count(*) FILTER (WHERE is_excluded), count(*) FROM single_bidder_processes"
    ).fetchone() or (0, 0)
    assert (excluded, total) == (21, 894)
    issues = real.execute("SELECT count(*) FROM quality_issues WHERE rule = 'R9'").fetchall()
    assert issues == [(21,)]


def test_i3_cutoff_year_is_the_snapshot_cutoff(real: duckdb.DuckDBPyConnection) -> None:
    cutoff = real.execute("SELECT max(signed_date)::DATE FROM canonical_contracts").fetchall()
    assert cutoff == [(date(2026, 10, 30),)]
