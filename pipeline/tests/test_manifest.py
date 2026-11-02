"""Manifiesto de la copia: fecha de corte por fuente y coherencia con los CSV (ADR 0006, R12)."""

import hashlib
import json
from datetime import UTC, datetime

import pytest

from tests.paths import REPO_ROOT
from veeduria.extract.http import Extraction
from veeduria.extract.manifest import (
    cutoff_date,
    read_manifest,
    source_entry,
    to_iso_date,
    write_manifest,
)
from veeduria.extract.sources import load_queries

SNAPSHOT_DIR = REPO_ROOT / "data" / "snapshot"
QUERIES = {query.id: query for query in load_queries()}
NOW = datetime(2026, 11, 2, 9, 30, tzinfo=UTC)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-10-30T22:26:24.549", "2026-10-30"),
        ("2022-01-06", "2022-01-06"),
        ("9/12/2022", "2022-12-09"),
        ("24/06/2022", "2022-06-24"),
        ("", None),
        ("Abril", None),
    ],
)
def test_manifest_dates_are_normalized_to_iso(raw: str, expected: str | None) -> None:
    assert to_iso_date(raw) == expected


def _extraction(query_id: str, column: str, values: list[str]) -> Extraction:
    query = QUERIES[query_id]
    index = query.allowed.index(column)
    rows = []
    for value in values:
        row = ["x"] * len(query.allowed)
        row[index] = value
        rows.append(row)
    return Extraction(header=query.allowed, rows=rows, total=len(rows))


def test_r12_cutoff_is_the_latest_signed_date() -> None:
    extraction = _extraction(
        "secop_contracts",
        "fecha_de_firma",
        ["2022-01-06T14:47:15.257", "2026-10-30T22:26:24.549", "2024-05-01T00:00:00.000"],
    )
    assert cutoff_date(QUERIES["secop_contracts"], extraction) == "2026-10-30"


def test_cutoff_of_medata_compares_dates_not_text() -> None:
    # Como texto, «9/12/2022» ordena después de «10/11/2022»; como fecha es anterior.
    extraction = _extraction(
        "medata_contract_execution", "fecha_contrato", ["9/12/2022", "10/11/2022", "1/09/2022"]
    )
    assert cutoff_date(QUERIES["medata_contract_execution"], extraction) == "2022-12-09"


def test_cutoff_ignores_empty_dates_and_sources_without_a_date_column() -> None:
    blank = _extraction("secop_procurement_processes", "fecha_de_publicacion_del", ["", ""])
    assert cutoff_date(QUERIES["secop_procurement_processes"], blank) is None
    suppliers = _extraction("secop_contracts_suppliers", "id_contrato", ["C1"])
    assert cutoff_date(QUERIES["secop_contracts_suppliers"], suppliers) is None


def test_source_entry_records_the_query_and_never_a_token() -> None:
    entry = source_entry(
        QUERIES["secop_additions"],
        row_count=3,
        sha256="a" * 64,
        source_sha256="",
        extracted_at=NOW,
        cutoff="2026-10-30",
    )
    assert entry["dataset"] == "cb9c-h8sn"
    assert entry["row_count"] == 3
    assert entry["extracted_at"] == "2026-11-02T09:30:00Z"
    assert entry["query"]["select"] == ["id_contrato", "tipo", "fecharegistro"]
    assert entry["query"]["batch_source"] == "secop_contracts"
    assert "source_sha256" not in entry
    assert "token" not in json.dumps(entry).lower()


def test_manifest_is_deterministic_and_takes_the_global_cutoff_from_contracts(tmp_path) -> None:
    contracts = source_entry(
        QUERIES["secop_contracts"],
        row_count=1,
        sha256="b" * 64,
        source_sha256="",
        extracted_at=NOW,
        cutoff="2026-10-30",
    )
    write_manifest(tmp_path, {"secop_contracts": contracts})
    first = (tmp_path / "manifest.json").read_bytes()
    write_manifest(tmp_path, {"secop_contracts": contracts})

    assert (tmp_path / "manifest.json").read_bytes() == first
    assert first.endswith(b"\n") and b"\r" not in first
    manifest = read_manifest(tmp_path)
    assert manifest["cutoff_date"] == "2026-10-30"
    assert list(manifest["sources"]) == ["secop_contracts"]


def test_read_manifest_without_a_file_has_no_sources(tmp_path) -> None:
    assert read_manifest(tmp_path)["sources"] == {}


def test_committed_manifest_matches_the_committed_csvs() -> None:
    path = SNAPSHOT_DIR / "manifest.json"
    if not path.exists():
        pytest.skip("Todavía no hay manifiesto.")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert sorted(manifest["sources"]) == sorted(QUERIES)
    for query_id, entry in manifest["sources"].items():
        data = (SNAPSHOT_DIR / f"{query_id}.csv").read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], query_id
        assert data.count(b"\n") - 1 >= entry["row_count"], query_id
