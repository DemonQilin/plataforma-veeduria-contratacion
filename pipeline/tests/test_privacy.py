"""Pruebas de privacidad (regla no negociable 1, ADR 0007).

Se escriben antes que la extracción. La supresión de celdas pequeñas (R13) se prueba
en `publish/`, cuando existan las salidas.
"""

import csv
import subprocess

import pytest

from tests.paths import REPO_ROOT
from veeduria.extract.sources import Query, load_queries

SNAPSHOT_DIR = REPO_ROOT / "data" / "snapshot"
OUTPUTS_DIR = REPO_ROOT / "data" / "outputs"
QUERIES = load_queries()
EXCLUDED = {column for query in QUERIES for column in query.excluded}


def _header(path) -> set[str]:
    with path.open(encoding="utf-8", newline="") as handle:
        return set(next(csv.reader(handle), []))


def test_sources_are_declared() -> None:
    assert {query.id for query in QUERIES} >= {
        "secop_contracts",
        "secop_contracts_suppliers",
        "secop_procurement_processes",
        "secop_additions",
        "medata_contract_execution",
        "medata_procurement_plan",
    }


@pytest.mark.parametrize("query", QUERIES, ids=lambda query: query.id)
def test_allowed_and_excluded_do_not_overlap(query: Query) -> None:
    assert query.allowed, f"{query.id}: la lista permitida está vacía"
    assert not set(query.allowed) & set(query.excluded)


def test_no_query_allows_a_column_excluded_by_another() -> None:
    allowed = {column for query in QUERIES for column in query.allowed}
    assert not allowed & EXCLUDED


def test_socrata_queries_never_select_everything() -> None:
    for query in QUERIES:
        assert "*" not in query.allowed


def test_snapshot_columns_are_whitelisted() -> None:
    by_id = {query.id: query for query in QUERIES}
    for path in sorted(SNAPSHOT_DIR.glob("*.csv")):
        assert path.stem in by_id, f"{path.name} no corresponde a ninguna consulta"
        assert _header(path) <= set(by_id[path.stem].allowed), path.name


def test_excluded_columns_never_reach_snapshot_or_outputs() -> None:
    for directory in (SNAPSHOT_DIR, OUTPUTS_DIR):
        for path in sorted(directory.glob("*.csv")):
            assert not _header(path) & EXCLUDED, path.name
        for path in sorted(directory.glob("*.json")):
            assert not any(column in path.read_text(encoding="utf-8") for column in EXCLUDED), (
                path.name
            )


def test_raw_data_is_ignored_by_git() -> None:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "data/raw/anything.csv"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0
