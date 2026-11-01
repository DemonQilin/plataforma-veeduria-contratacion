"""Parser y descarga de MEData · Ejecución contractual (ADR 0010).

El fixture son líneas reales recortadas del archivo, con nombres, documentos y texto libre
reemplazados por valores ficticios. Conserva el formato original: cada línea envuelta en
comillas, dos capas de escape y filas cortadas a mitad de campo.
"""

import os
import re
import stat
from pathlib import Path

import httpx
import pytest
from tenacity import wait_none
from typer.testing import CliRunner

from veeduria.cli import app
from veeduria.extract.medata import MedataError
from veeduria.extract.medata_csv import fetch_csv_query, parse_execution_csv
from veeduria.extract.socrata import make_client
from veeduria.extract.sources import Query, load_queries

FIXTURE = Path(__file__).parent / "fixtures" / "medata_execution_sample.csv"
QUERY_ID = "medata_contract_execution"
runner = CliRunner()


def execution_query() -> Query:
    return next(q for q in load_queries() if q.id == QUERY_ID)


def sample_text() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def parse(text: str | None = None):
    return parse_execution_csv(sample_text() if text is None else text, execution_query())


def as_dicts(extraction) -> list[dict[str, str]]:
    return [dict(zip(extraction.header, row, strict=True)) for row in extraction.rows]


# --- Estructura del archivo (ADR 0010) ----------------------------------------------------


def test_header_is_the_whitelist_and_every_row_has_one_value_per_column() -> None:
    extraction = parse()

    assert extraction.header == execution_query().allowed
    assert len(extraction.rows) == 14
    assert extraction.total == 14
    assert all(len(row) == len(extraction.header) for row in extraction.rows)


def test_full_rows_keep_commas_inside_quoted_values_and_stay_aligned() -> None:
    rows = [r for r in as_dicts(parse()) if r["truncated"] == "false"]

    assert len(rows) == 10
    for row in rows:
        assert re.fullmatch(r"\d{1,3}(\.\d{3})*,\d+", row["valor_inicial_contrato"])
        assert re.fullmatch(r"\d{1,3}(\.\d{3})*,\d+", row["valor_fin_contrato"])
        assert re.fullmatch(r"\d+", row["duracion_en_dias"])
        assert re.fullmatch(r"20\d\d\.0", row["ano"])
        assert re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", row["fecha_contrato"])


def test_row_with_quotes_backslash_and_comma_in_free_text_does_not_shift_columns() -> None:
    row = as_dicts(parse())[2]

    assert row["contrato"] == "460090003"
    assert re.fullmatch(r"20\d\d\.0", row["ano"])
    assert re.fullmatch(r"\d{1,3}(\.\d{3})*,\d+", row["valor_fin_contrato"])


def test_truncated_rows_are_marked_and_keep_only_the_leading_columns() -> None:
    truncated = [r for r in as_dicts(parse()) if r["truncated"] == "true"]

    assert len(truncated) == 4
    for row in truncated:
        assert row["contrato"] and row["fecha_contrato"] and row["modalidad"]
        assert row["nombre_secretaria"]
        for lost in ("valor_inicial_contrato", "valor_fin_contrato", "estado", "ano"):
            assert row[lost] == ""


def test_text_is_kept_as_in_the_source_without_repairing_the_encoding() -> None:
    modalities = {r["modalidad"] for r in as_dicts(parse())}

    assert any("Ã" in value for value in modalities)


def test_crlf_and_lf_line_endings_give_the_same_rows() -> None:
    assert parse(sample_text().replace("\n", "\r\n")).rows == parse().rows


# --- Privacidad (regla 1) -----------------------------------------------------------------


def test_personal_and_free_text_values_never_reach_the_rows() -> None:
    text = sample_text()
    assert "CONTRATISTA FICTICIO" in text and "SUPERVISOR FICTICIO" in text

    extraction = parse(text)

    flat = "\n".join(cell for row in extraction.rows for cell in row)
    for personal in ("CONTRATISTA FICTICIO", "SUPERVISOR FICTICIO", "1000000", "2000000"):
        assert personal not in flat
    for excluded in execution_query().excluded:
        assert excluded not in extraction.header


# --- Errores sin contenido ----------------------------------------------------------------


def test_unexpected_column_count_stops_with_the_line_number_and_no_content() -> None:
    lines = sample_text().split("\n")
    lines[2] = '"SECRETO,2,3"""'

    with pytest.raises(MedataError) as error:
        parse("\n".join(lines))

    assert "línea 3" in str(error.value)
    assert "SECRETO" not in str(error.value)


def test_line_without_the_outer_quotes_stops_with_the_line_number_and_no_content() -> None:
    lines = sample_text().split("\n")
    lines[4] = "SECRETO sin comillas"

    with pytest.raises(MedataError) as error:
        parse("\n".join(lines))

    assert "línea 5" in str(error.value)
    assert "SECRETO" not in str(error.value)


def test_header_without_an_allowed_column_stops_naming_the_column() -> None:
    lines = sample_text().split("\n")
    lines[0] = lines[0].replace("nombre_secretaria", "otra_columna")

    with pytest.raises(MedataError, match="nombre_secretaria"):
        parse("\n".join(lines))


def test_file_without_rows_stops() -> None:
    header_only = sample_text().split("\n")[0] + "\n"

    with pytest.raises(MedataError, match="0 filas"):
        parse(header_only)


# --- Descarga a data/raw/ -----------------------------------------------------------------


def serve(content: bytes, statuses: list[int] | None = None):
    pending = list(statuses or [])
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        status = pending.pop(0) if pending else 200
        if status != 200:
            return httpx.Response(status)
        return httpx.Response(200, content=content)

    return handler, seen


def download(handler, raw_dir: Path, **kwargs):
    client = make_client(None, transport=httpx.MockTransport(handler))
    return fetch_csv_query(client, execution_query(), raw_dir, wait=wait_none(), **kwargs)


def test_download_saves_the_raw_file_privately_and_parses_it(tmp_path: Path) -> None:
    content = FIXTURE.read_bytes()
    handler, seen = serve(content)

    extraction = download(handler, tmp_path)

    raw = tmp_path / f"{QUERY_ID}.csv"
    assert raw.read_bytes() == content
    assert stat.S_IMODE(os.stat(raw).st_mode) == 0o600
    assert len(extraction.rows) == 14
    assert str(seen[0].url) == execution_query().url
    assert [p.name for p in tmp_path.iterdir()] == [raw.name]


def test_download_retries_server_errors(tmp_path: Path) -> None:
    handler, seen = serve(FIXTURE.read_bytes(), statuses=[504, 504])

    extraction = download(handler, tmp_path)

    assert len(seen) == 3
    assert len(extraction.rows) == 14


def test_failed_download_leaves_no_partial_file_and_keeps_the_previous_one(
    tmp_path: Path,
) -> None:
    previous = tmp_path / f"{QUERY_ID}.csv"
    previous.write_bytes(b"copia anterior")
    handler, _ = serve(b"", statuses=[504, 504, 504])

    with pytest.raises(MedataError, match="HTTP 504"):
        download(handler, tmp_path, max_attempts=3)

    assert previous.read_bytes() == b"copia anterior"
    assert [p.name for p in tmp_path.iterdir()] == [previous.name]


def test_invalid_file_does_not_replace_the_previous_raw_file(tmp_path: Path) -> None:
    previous = tmp_path / f"{QUERY_ID}.csv"
    previous.write_bytes(b"copia anterior")
    handler, _ = serve(b'"SECRETO,2,3"""\n')

    with pytest.raises(MedataError) as error:
        download(handler, tmp_path)

    assert "SECRETO" not in str(error.value)
    assert previous.read_bytes() == b"copia anterior"
    assert [p.name for p in tmp_path.iterdir()] == [previous.name]


def test_file_that_is_not_utf8_stops_without_content(tmp_path: Path) -> None:
    handler, _ = serve(b'"contrato,\xff\xfe"""\n')

    with pytest.raises(MedataError, match="UTF-8"):
        download(handler, tmp_path)

    assert list(tmp_path.iterdir()) == []


# --- Comando `veeduria extract` -----------------------------------------------------------


def invoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, handler, tokens=None):
    transport = httpx.MockTransport(handler)

    def client_factory(token):
        if tokens is not None:
            tokens.append(token)
        return make_client(token, transport=transport)

    monkeypatch.setattr("veeduria.cli.make_client", client_factory)
    return runner.invoke(
        app,
        [
            "extract",
            QUERY_ID,
            "--snapshot-dir",
            str(tmp_path / "snapshot"),
            "--raw-dir",
            str(tmp_path / "raw"),
        ],
    )


def test_extract_writes_the_snapshot_without_personal_columns_or_the_socrata_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    handler, _ = serve(FIXTURE.read_bytes())
    tokens: list[str | None] = []
    monkeypatch.setenv("SOCRATA_APP_TOKEN", "token-de-datos-gov-co")

    result = invoke(tmp_path, monkeypatch, handler, tokens)

    assert result.exit_code == 0, result.output
    assert "14 filas" in result.output
    assert tokens == [None]
    snapshot = (tmp_path / "snapshot" / f"{QUERY_ID}.csv").read_text(encoding="utf-8")
    assert snapshot.splitlines()[0] == ",".join(execution_query().allowed)
    assert "FICTICIO" not in snapshot
    assert (tmp_path / "raw" / f"{QUERY_ID}.csv").exists()


def test_extract_failure_exits_with_1_and_writes_no_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    handler, _ = serve(b"", statuses=[404])

    result = invoke(tmp_path, monkeypatch, handler)

    assert result.exit_code == 1
    assert "la copia no se modificó" in result.output
    assert not (tmp_path / "snapshot").exists()


# --- Archivo completo (usa la red) --------------------------------------------------------


@pytest.mark.network
def test_full_file_has_the_documented_row_counts(tmp_path: Path) -> None:
    query = execution_query()
    with make_client(None) as client:
        extraction = fetch_csv_query(client, query, tmp_path)

    rows = as_dicts(extraction)
    assert len(rows) == 25783
    assert sum(r["truncated"] == "true" for r in rows) == 2072
    assert len({r["contrato"] for r in rows}) == 2939
