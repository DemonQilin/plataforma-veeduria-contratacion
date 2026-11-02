"""`veeduria run --refresh`: copia todo o nada, Plan Anual congelado y manifiesto (ADR 0006)."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from veeduria.cli import app
from veeduria.extract.http import Extraction, ExtractionError
from veeduria.extract.manifest import read_manifest
from veeduria.extract.refresh import refresh_snapshot
from veeduria.extract.snapshot import read_column
from veeduria.extract.sources import Query, load_queries

runner = CliRunner()
QUERIES = load_queries()
NOW = datetime(2026, 11, 2, 9, 30, tzinfo=UTC)
PLAN = "medata_procurement_plan"

DATE_VALUES = {
    "secop_contracts": "2026-10-30T22:26:24.549",
    "secop_procurement_processes": "2026-10-29T00:00:00.000",
    "secop_additions": "2026-10-28T10:00:00.000",
    "medata_contract_execution": "9/12/2022",
}


class FakeSources:
    """Descargas simuladas: registra qué se pidió y qué identificadores vio Adiciones."""

    def __init__(self, contract_id: str = "C-NEW", fail_on: str = "") -> None:
        self.contract_id = contract_id
        self.fail_on = fail_on
        self.requested: list[str] = []
        self.additions_saw: list[str] = []
        self.source_sha = {"medata_contract_execution": "e" * 64}

    def __call__(self, query: Query, staging: Path) -> Extraction:
        self.requested.append(query.id)
        if query.id == self.fail_on:
            raise ExtractionError("falla simulada")
        if query.batch_source:
            self.additions_saw = read_column(staging / f"{query.batch_source}.csv", "id_contrato")
        row = ["x"] * len(query.allowed)
        if "id_contrato" in query.allowed:
            row[query.allowed.index("id_contrato")] = self.contract_id
        if query.id in DATE_VALUES:
            column = query.cutoff_column
            row[query.allowed.index(column)] = DATE_VALUES[query.id]
        return Extraction(
            header=query.allowed,
            rows=[row],
            total=1,
            source_sha256=self.source_sha.get(query.id, ""),
        )


def seed(directory: Path, queries: tuple[Query, ...] = QUERIES) -> None:
    """Una copia anterior con contratos viejos y todas las fuentes en el manifiesto."""
    first = FakeSources(contract_id="C-OLD")
    raw = directory.parent / "seed-raw"
    refresh_snapshot(queries, directory, raw, first, now=NOW)


def snapshot_bytes(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(directory.iterdir())}


def test_refresh_writes_every_csv_and_the_manifest(tmp_path) -> None:
    snapshot, raw = tmp_path / "snapshot", tmp_path / "raw"

    report = refresh_snapshot(QUERIES, snapshot, raw, FakeSources(), now=NOW)

    assert sorted(path.stem for path in snapshot.glob("*.csv")) == sorted(q.id for q in QUERIES)
    manifest = read_manifest(snapshot)
    assert sorted(manifest["sources"]) == sorted(q.id for q in QUERIES)
    assert manifest["cutoff_date"] == "2026-10-30"
    assert manifest["sources"]["secop_contracts"]["row_count"] == 1
    assert manifest["sources"]["medata_contract_execution"]["cutoff_date"] == "2022-12-09"
    assert manifest["sources"]["medata_contract_execution"]["source_sha256"] == "e" * 64
    assert manifest["sources"]["secop_contracts_suppliers"]["cutoff_date"] is None
    assert [item[0] for item in report.refreshed] == [q.id for q in QUERIES]
    assert report.skipped == []


def test_refresh_leaves_no_staging_folder(tmp_path) -> None:
    refresh_snapshot(QUERIES, tmp_path / "snapshot", tmp_path / "raw", FakeSources(), now=NOW)
    assert list((tmp_path / "raw").iterdir()) == []


def test_refresh_batches_additions_with_the_fresh_contract_ids(tmp_path) -> None:
    snapshot = tmp_path / "snapshot"
    seed(snapshot)
    fake = FakeSources(contract_id="C-NEW")

    refresh_snapshot(QUERIES, snapshot, tmp_path / "raw", fake, force_frozen=True, now=NOW)

    assert fake.additions_saw == ["C-NEW"]


def test_failed_refresh_keeps_the_previous_copy_and_manifest(tmp_path) -> None:
    snapshot = tmp_path / "snapshot"
    seed(snapshot)
    before = snapshot_bytes(snapshot)

    fake = FakeSources(contract_id="C-NEW", fail_on="medata_contract_execution")
    with pytest.raises(ExtractionError):
        refresh_snapshot(QUERIES, snapshot, tmp_path / "raw", fake, force_frozen=True, now=NOW)

    assert snapshot_bytes(snapshot) == before
    assert list((tmp_path / "raw").iterdir()) == []


def test_refresh_skips_the_frozen_procurement_plan_and_keeps_its_entry(tmp_path) -> None:
    snapshot = tmp_path / "snapshot"
    seed(snapshot)
    old_entry = read_manifest(snapshot)["sources"][PLAN]
    old_csv = (snapshot / f"{PLAN}.csv").read_bytes()
    fake = FakeSources(contract_id="C-NEW")

    report = refresh_snapshot(QUERIES, snapshot, tmp_path / "raw", fake, now=NOW)

    assert PLAN not in fake.requested
    assert report.skipped == [PLAN]
    assert read_manifest(snapshot)["sources"][PLAN] == old_entry
    assert (snapshot / f"{PLAN}.csv").read_bytes() == old_csv


def test_refresh_requests_the_frozen_plan_when_forced_or_when_it_has_no_entry(tmp_path) -> None:
    snapshot = tmp_path / "snapshot"
    seed(snapshot)
    forced = FakeSources()
    refresh_snapshot(QUERIES, snapshot, tmp_path / "raw", forced, force_frozen=True, now=NOW)
    assert PLAN in forced.requested

    fresh = FakeSources()
    refresh_snapshot(QUERIES, tmp_path / "other", tmp_path / "raw", fresh, now=NOW)
    assert PLAN in fresh.requested


def test_refresh_warns_when_the_medata_source_changes(tmp_path) -> None:
    snapshot = tmp_path / "snapshot"
    seed(snapshot)
    fake = FakeSources()
    fake.source_sha = {"medata_contract_execution": "f" * 64}

    report = refresh_snapshot(QUERIES, snapshot, tmp_path / "raw", fake, now=NOW)

    assert len(report.warnings) == 1
    assert "medata_contract_execution" in report.warnings[0]
    unchanged = refresh_snapshot(QUERIES, snapshot, tmp_path / "raw", fake, now=NOW)
    assert unchanged.warnings == []


def patch_download(monkeypatch: pytest.MonkeyPatch, fake: FakeSources) -> None:
    monkeypatch.setattr("veeduria.cli._download", lambda query, snap, raw: fake(query, snap))


def test_run_refresh_updates_the_copy_through_the_cli(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_download(monkeypatch, FakeSources())
    snapshot = tmp_path / "snapshot"

    result = runner.invoke(
        app,
        ["run", "--refresh", "--snapshot-dir", str(snapshot), "--raw-dir", str(tmp_path / "raw")],
    )

    assert result.exit_code == 0, result.output
    assert "secop_contracts: 1 filas" in result.output
    assert json.loads((snapshot / "manifest.json").read_text())["cutoff_date"] == "2026-10-30"


def test_run_refresh_failure_exits_with_1_and_keeps_the_copy(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    snapshot = tmp_path / "snapshot"
    seed(snapshot)
    before = snapshot_bytes(snapshot)
    patch_download(monkeypatch, FakeSources(fail_on="secop_additions"))

    result = runner.invoke(
        app,
        [
            "run",
            "--refresh",
            "--force-procurement-plan",
            "--snapshot-dir",
            str(snapshot),
            "--raw-dir",
            str(tmp_path / "raw"),
        ],
    )

    assert result.exit_code == 1
    assert "la copia no se modificó" in result.output
    assert snapshot_bytes(snapshot) == before


def test_force_procurement_plan_requires_refresh() -> None:
    result = runner.invoke(app, ["run", "--from-snapshot", "--force-procurement-plan"])
    assert result.exit_code == 2
    assert "--refresh" in result.output
