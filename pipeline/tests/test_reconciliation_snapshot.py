"""Conciliación SECOP–MEData sobre la copia versionada (R15): cifras conocidas y determinismo."""

import duckdb
import pytest

from tests.test_linking_snapshot import _run
from veeduria.link.reconciliation import reconcile_sources


@pytest.fixture(scope="module")
def reconciled() -> duckdb.DuckDBPyConnection:
    connection = _run()
    reconcile_sources(connection)
    return connection


def test_r15_snapshot_covers_the_18_months_of_medata(
    reconciled: duckdb.DuckDBPyConnection,
) -> None:
    assert reconciled.execute(
        "SELECT count(*), min(month)::VARCHAR, max(month)::VARCHAR FROM reconciliation"
    ).fetchone() == (18, "2022-01-01", "2023-06-01")


def test_r15_snapshot_january_2022_matches_the_first_validation(
    reconciled: duckdb.DuckDBPyConnection,
) -> None:
    assert reconciled.execute(
        "SELECT secop_count, medata_count, shared_count, union_count FROM reconciliation"
        " WHERE month = DATE '2022-01-01'"
    ).fetchone() == (726, 725, 661, 790)


def test_r15_snapshot_flags_6_of_18_months_below_80_percent(
    reconciled: duckdb.DuckDBPyConnection,
) -> None:
    assert reconciled.execute(
        "SELECT list(month::VARCHAR ORDER BY month) FROM reconciliation WHERE below_threshold"
    ).fetchone() == (
        [
            "2022-03-01",
            "2022-04-01",
            "2022-05-01",
            "2022-06-01",
            "2022-07-01",
            "2022-12-01",
        ],
    )


def test_r15_snapshot_leaves_4_shared_contracts_signed_in_july_2023_outside_the_period(
    reconciled: duckdb.DuckDBPyConnection,
) -> None:
    """MEData las fecha en junio de 2023 y SECOP II en julio, fuera de los 18 meses."""
    assert reconciled.execute("SELECT sum(shared_count) FROM reconciliation").fetchone() == (2628,)


def test_r15_snapshot_is_deterministic(reconciled: duckdb.DuckDBPyConnection) -> None:
    second = _run()
    reconcile_sources(second)
    query = "SELECT * FROM reconciliation ORDER BY month"
    assert reconciled.execute(query).fetchall() == second.execute(query).fetchall()
