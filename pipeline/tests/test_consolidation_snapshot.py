"""Consolidación sobre la copia versionada (R3, R4, R5): cifras conocidas y determinismo."""

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.consolidate.canonical_contracts import consolidate_contracts
from veeduria.consolidate.canonical_processes import consolidate_processes
from veeduria.normalize.contracts import normalize_contracts
from veeduria.normalize.procurement_processes import normalize_procurement_processes

SNAPSHOT = REPO_ROOT / "data" / "snapshot"


def _run() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    normalize_contracts(connection, SNAPSHOT / "secop_contracts.csv")
    normalize_procurement_processes(connection, SNAPSHOT / "secop_procurement_processes.csv")
    consolidate_contracts(connection)
    consolidate_processes(connection)
    return connection


@pytest.fixture(scope="module")
def consolidated() -> duckdb.DuckDBPyConnection:
    return _run()


def test_r03_snapshot_has_one_contract_per_reference(
    consolidated: duckdb.DuckDBPyConnection,
) -> None:
    assert consolidated.execute(
        "SELECT count(*), count(DISTINCT contract_reference) FROM canonical_contracts"
    ).fetchone() == (7428, 7428)


def test_r03_snapshot_reports_six_references_with_different_processes(
    consolidated: duckdb.DuckDBPyConnection,
) -> None:
    assert consolidated.execute(
        "SELECT count(*) FROM quality_issues WHERE rule = 'R3'"
    ).fetchone() == (6,)


def test_r04_snapshot_has_no_unsigned_contracts(consolidated: duckdb.DuckDBPyConnection) -> None:
    assert consolidated.execute(
        "SELECT count(*) FROM quality_issues WHERE rule = 'R4'"
    ).fetchone() == (0,)


def test_r05_snapshot_has_one_process_per_portfolio(
    consolidated: duckdb.DuckDBPyConnection,
) -> None:
    assert consolidated.execute(
        "SELECT count(*), count(DISTINCT procurement_process) FROM canonical_processes"
    ).fetchone() == (17260, 17260)


def test_determinism_two_runs_produce_identical_tables(
    consolidated: duckdb.DuckDBPyConnection,
) -> None:
    second = _run()
    for query in (
        "SELECT * FROM canonical_contracts",
        "SELECT * FROM canonical_processes",
        "SELECT * FROM quality_issues ORDER BY rule, record_key",
    ):
        assert consolidated.execute(query).fetchall() == second.execute(query).fetchall()
