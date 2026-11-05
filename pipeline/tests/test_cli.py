import json

import duckdb
from typer.testing import CliRunner

from tests.paths import REPO_ROOT
from veeduria.cli import app
from veeduria.publish.models import Indicators, Metadata

runner = CliRunner()
SNAPSHOT = REPO_ROOT / "data" / "snapshot"


def test_run_requires_a_mode() -> None:
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 2
    assert "--from-snapshot" in result.output
    assert "--refresh" in result.output


def test_run_rejects_both_modes() -> None:
    result = runner.invoke(app, ["run", "--from-snapshot", "--refresh"])
    assert result.exit_code == 2


def test_r12_run_from_snapshot_writes_metadata_with_the_latest_signed_date(tmp_path) -> None:
    result = runner.invoke(app, ["run", "--from-snapshot", "--output-dir", str(tmp_path / "out")])
    assert result.exit_code == 0, result.output
    metadata = json.loads((tmp_path / "out" / "metadata.json").read_text(encoding="utf-8"))
    Metadata.model_validate(metadata)
    latest = (
        duckdb.connect()
        .execute(
            "SELECT max(CAST(fecha_de_firma AS TIMESTAMP))::DATE::VARCHAR"
            f" FROM read_csv('{SNAPSHOT / 'secop_contracts.csv'}', all_varchar = true)"
        )
        .fetchone()
    )
    assert metadata["cutoff_date"] == latest[0]
    assert [source["name"] for source in metadata["sources"]] == sorted(
        source["name"] for source in metadata["sources"]
    )
    assert {source["license"] for source in metadata["sources"]} == {"CC BY-SA 4.0", "CC BY 4.0"}


def test_r13_run_from_snapshot_writes_indicators_that_match_the_contract(tmp_path) -> None:
    result = runner.invoke(app, ["run", "--from-snapshot", "--output-dir", str(tmp_path / "out")])
    assert result.exit_code == 0, result.output
    payload = json.loads((tmp_path / "out" / "indicators.json").read_text(encoding="utf-8"))
    Indicators.model_validate(payload)
    assert {cell["indicator"] for cell in payload["cells"]} == {"I1", "I2", "I3", "I8"}


def test_run_from_snapshot_is_deterministic(tmp_path) -> None:
    for name in ("first", "second"):
        result = runner.invoke(
            app, ["run", "--from-snapshot", "--output-dir", str(tmp_path / name)]
        )
        assert result.exit_code == 0, result.output
    for name in (
        "electoral_calendar.json",
        "metadata.json",
        "indicators.json",
        "monthly_series.json",
        "quality.json",
    ):
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()


def test_run_from_snapshot_failure_leaves_outputs_untouched(tmp_path) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    (output_dir / "metadata.json").write_text("previous", encoding="utf-8")
    (output_dir / "indicators.json").write_text("previous", encoding="utf-8")
    (output_dir / "quality.json").write_text("previous", encoding="utf-8")
    (output_dir / "monthly_series.json").write_text("previous", encoding="utf-8")
    (output_dir / "electoral_calendar.json").write_text("previous", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "run",
            "--from-snapshot",
            "--snapshot-dir",
            str(tmp_path / "missing"),
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 1
    assert "copia" in result.output
    assert (output_dir / "metadata.json").read_text(encoding="utf-8") == "previous"
    assert (output_dir / "indicators.json").read_text(encoding="utf-8") == "previous"
    assert (output_dir / "quality.json").read_text(encoding="utf-8") == "previous"
    assert (output_dir / "monthly_series.json").read_text(encoding="utf-8") == "previous"
    assert (output_dir / "electoral_calendar.json").read_text(encoding="utf-8") == "previous"
    assert [path.name for path in tmp_path.iterdir()] == ["out"]


def test_export_schema_is_idempotent(tmp_path) -> None:
    first = runner.invoke(app, ["export-schema", "--output-dir", str(tmp_path)])
    assert first.exit_code == 0
    written = (tmp_path / "metadata.json").read_bytes()

    second = runner.invoke(app, ["export-schema", "--output-dir", str(tmp_path)])
    assert second.exit_code == 0
    assert (tmp_path / "metadata.json").read_bytes() == written

    schema = json.loads(written)
    assert schema["title"] == "Metadata"
    assert "cutoff_date" in schema["properties"]


def test_export_schema_removes_schemas_without_a_model(tmp_path) -> None:
    stale = tmp_path / "removed_model.json"
    stale.write_text("{}", encoding="utf-8")

    result = runner.invoke(app, ["export-schema", "--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert not stale.exists()
    assert (tmp_path / "metadata.json").exists()
