"""Comando `veeduria extract`: extrae una consulta a data/snapshot/."""

import httpx
import pytest
from typer.testing import CliRunner

from tests.fake_socrata import fake_socrata
from veeduria.cli import app
from veeduria.extract.socrata import make_client
from veeduria.extract.sources import load_queries

runner = CliRunner()


@pytest.fixture
def contracts_header() -> tuple[str, ...]:
    return next(q for q in load_queries() if q.id == "secop_contracts").allowed


def test_extract_unknown_query_exits_with_2(tmp_path) -> None:
    result = runner.invoke(app, ["extract", "no_existe", "--snapshot-dir", str(tmp_path)])
    assert result.exit_code == 2
    assert "no_existe" in result.output
    assert list(tmp_path.iterdir()) == []


def test_extract_query_not_implemented_yet_exits_with_2(tmp_path) -> None:
    result = runner.invoke(app, ["extract", "secop_additions", "--snapshot-dir", str(tmp_path)])
    assert result.exit_code == 2
    assert list(tmp_path.iterdir()) == []


def test_extract_secop_contracts_writes_the_snapshot(
    tmp_path, monkeypatch: pytest.MonkeyPatch, contracts_header
) -> None:
    rows = [[f"C{n}"] + ["x"] * (len(contracts_header) - 1) for n in range(3)]
    transport = httpx.MockTransport(fake_socrata(contracts_header, rows))
    monkeypatch.setattr(
        "veeduria.cli.make_client", lambda token: make_client(token, transport=transport)
    )

    result = runner.invoke(app, ["extract", "secop_contracts", "--snapshot-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "3 filas" in result.output
    written = (tmp_path / "secop_contracts.csv").read_text(encoding="utf-8").splitlines()
    assert written[0] == ",".join(contracts_header)
    assert len(written) == 4


def test_extract_failure_exits_with_1_and_writes_nothing(
    tmp_path, monkeypatch: pytest.MonkeyPatch, contracts_header
) -> None:
    rows = [["C1"] + ["x"] * (len(contracts_header) - 1)]
    transport = httpx.MockTransport(fake_socrata(contracts_header, rows, reported_total=99))
    monkeypatch.setattr(
        "veeduria.cli.make_client", lambda token: make_client(token, transport=transport)
    )

    result = runner.invoke(app, ["extract", "secop_contracts", "--snapshot-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert list(tmp_path.iterdir()) == []
