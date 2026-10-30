import json

from typer.testing import CliRunner

from veeduria.cli import app

runner = CliRunner()


def test_run_requires_a_mode() -> None:
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 2
    assert "--from-snapshot" in result.output
    assert "--refresh" in result.output


def test_run_rejects_both_modes() -> None:
    result = runner.invoke(app, ["run", "--from-snapshot", "--refresh"])
    assert result.exit_code == 2


def test_run_from_snapshot_is_not_implemented_yet() -> None:
    result = runner.invoke(app, ["run", "--from-snapshot"])
    assert result.exit_code == 1
    assert "etapas" in result.output


def test_run_refresh_is_not_implemented_yet() -> None:
    result = runner.invoke(app, ["run", "--refresh"])
    assert result.exit_code == 1


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
