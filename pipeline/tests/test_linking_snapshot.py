"""Cruce sobre la copia versionada (R7, R8, D3): cifras conocidas y determinismo."""

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.consolidate.canonical_contracts import consolidate_contracts
from veeduria.consolidate.canonical_processes import consolidate_processes
from veeduria.link.linked_contracts import link_contracts
from veeduria.link.medata_contracts import collapse_medata_contracts
from veeduria.normalize.catalogs import classify_department
from veeduria.normalize.contract_execution import normalize_contract_execution
from veeduria.normalize.contracts import normalize_contracts
from veeduria.normalize.procurement_processes import normalize_procurement_processes

SNAPSHOT = REPO_ROOT / "data" / "snapshot"


def _run() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    normalize_contracts(connection, SNAPSHOT / "secop_contracts.csv")
    normalize_procurement_processes(connection, SNAPSHOT / "secop_procurement_processes.csv")
    normalize_contract_execution(connection, SNAPSHOT / "medata_contract_execution.csv")
    consolidate_contracts(connection)
    consolidate_processes(connection)
    collapse_medata_contracts(connection)
    link_contracts(connection)
    return connection


@pytest.fixture(scope="module")
def linked() -> duckdb.DuckDBPyConnection:
    return _run()


def test_link_snapshot_keeps_one_row_per_canonical_contract(
    linked: duckdb.DuckDBPyConnection,
) -> None:
    assert linked.execute(
        "SELECT count(*), count(DISTINCT contract_reference) FROM linked_contracts"
    ).fetchone() == (7428, 7428)


def test_r08_snapshot_assigns_2633_from_medata_4776_from_secop_and_19_unassigned(
    linked: duckdb.DuckDBPyConnection,
) -> None:
    assert linked.execute(
        "SELECT department_source, count(*) FROM linked_contracts GROUP BY 1 ORDER BY 1"
    ).fetchall() == [("medata", 2633), ("secop", 4776), ("unassigned", 19)]


def test_r08_snapshot_has_a_single_unmapped_text_and_it_belongs_to_no_contract(
    linked: duckdb.DuckDBPyConnection,
) -> None:
    assert linked.execute(
        "SELECT record_key FROM quality_issues"
        " WHERE rule = 'R8' AND detail = 'reason=unmapped_department_text'"
    ).fetchall() == [("SUMINISTRO DE VESTIDO Y CALZADO DE LABOR",)]


def test_d03_snapshot_matches_2633_contracts_with_medata(
    linked: duckdb.DuckDBPyConnection,
) -> None:
    assert linked.execute(
        "SELECT count(*) FILTER (WHERE in_medata) FROM linked_contracts"
    ).fetchone() == (2633,)


def test_adr0046_snapshot_links_the_contract_whose_secop_reference_ends_in_nbsp(
    linked: duckdb.DuckDBPyConnection,
) -> None:
    assert linked.execute(
        "SELECT in_medata, length(contract_reference) FROM linked_contracts"
        " WHERE contract_reference = '4600098086'"
    ).fetchall() == [(True, 10)]


def test_r07_snapshot_has_11_public_credit_contracts_outside_the_value_indicators(
    linked: duckdb.DuckDBPyConnection,
) -> None:
    assert linked.execute(
        "SELECT count(*) FILTER (WHERE NOT is_value_eligible) FROM linked_contracts"
    ).fetchone() == (11,)


def test_determinism_two_runs_produce_identical_tables(
    linked: duckdb.DuckDBPyConnection,
) -> None:
    second = _run()
    for query in (
        "SELECT * FROM medata_contracts",
        "SELECT * FROM linked_contracts",
        "SELECT * FROM quality_issues ORDER BY rule, record_key",
    ):
        assert linked.execute(query).fetchall() == second.execute(query).fetchall()


def test_r08_snapshot_both_sources_agree_on_the_department_of_every_shared_contract(
    linked: duckdb.DuckDBPyConnection,
) -> None:
    """Evidencia del catálogo (ADR 0030): los 2.629 contratos presentes en ambas fuentes."""
    pairs = linked.execute(
        "SELECT m.department, p.department, count(*)"
        " FROM canonical_contracts AS k"
        " JOIN canonical_processes AS p USING (procurement_process)"
        " JOIN medata_contracts AS m USING (contract_reference)"
        " GROUP BY ALL"
    ).fetchall()
    codes = [
        (classify_department(medata), classify_department(secop), count)
        for medata, secop, count in pairs
    ]
    assert sum(count for _, _, count in codes) == 2629
    assert [(left, right) for left, right, _ in codes if left != right] == []
