"""Cliente de Socrata (ADR 0009): paginación, verificación de conteo y reintentos."""

import httpx
import pytest
from tenacity import wait_none

from tests.fake_socrata import csv_text, fake_socrata
from veeduria.extract.socrata import (
    SocrataError,
    app_token_from_env,
    fetch_query,
    fetch_query_by_ids,
    make_client,
)
from veeduria.extract.sources import Query

HEADER = ("id_contrato", "valor")
ROWS = [[f"C{n}", str(n * 10)] for n in range(1, 6)]


def make_query(**overrides: object) -> Query:
    values: dict[str, object] = {
        "id": "secop_contracts",
        "dataset": "dataset",
        "kind": "socrata",
        "url": "https://example.test/resource/dataset.csv",
        "where": "nombre_entidad = 'ENTIDAD X' AND fecha_de_firma >= '2022-01-01T00:00:00'",
        "order_by": "id_contrato",
        "allowed": HEADER,
        "excluded": ("nombre_supervisor",),
    }
    values.update(overrides)
    return Query(**values)  # type: ignore[arg-type]


def client_for(handler) -> httpx.Client:
    return make_client(None, transport=httpx.MockTransport(handler))


def fetch(handler, query: Query | None = None, **kwargs):
    return fetch_query(client_for(handler), query or make_query(), wait=wait_none(), **kwargs)


# --- Parámetros de la consulta (R1, ADR 0009) ---------------------------------------------


def test_request_uses_explicit_select_where_order_and_limit() -> None:
    log: list[httpx.Request] = []
    fetch(fake_socrata(HEADER, ROWS, log=log), page_size=10)

    page = next(r for r in log if "count(*)" not in r.url.params["$select"])
    params = page.url.params
    assert params["$select"] == "id_contrato,valor"
    assert "*" not in params["$select"]
    assert params["$where"] == make_query().where
    assert params["$order"] == "id_contrato"
    assert params["$limit"] == "10"
    assert params["$offset"] == "0"
    assert page.url.path == "/resource/dataset.csv"


def test_count_query_uses_the_same_where() -> None:
    log: list[httpx.Request] = []
    fetch(fake_socrata(HEADER, ROWS, log=log))

    count = next(r for r in log if "count(*)" in r.url.params["$select"])
    assert count.url.params["$where"] == make_query().where


# --- Paginación completa -------------------------------------------------------------------


def test_paginates_until_a_short_page() -> None:
    extraction = fetch(fake_socrata(HEADER, ROWS), page_size=2)
    assert extraction.rows == ROWS
    assert extraction.header == HEADER


def test_paginates_when_total_is_an_exact_multiple_of_the_page_size() -> None:
    extraction = fetch(fake_socrata(HEADER, ROWS[:4]), page_size=2)
    assert extraction.rows == ROWS[:4]


def test_offsets_advance_by_page_size() -> None:
    log: list[httpx.Request] = []
    fetch(fake_socrata(HEADER, ROWS, log=log), page_size=2)
    offsets = [r.url.params["$offset"] for r in log if "count(*)" not in r.url.params["$select"]]
    assert offsets == ["0", "2", "4"]


# --- Verificación y fallas seguras ---------------------------------------------------------


def test_count_mismatch_fails() -> None:
    with pytest.raises(SocrataError, match="5.*9"):
        fetch(fake_socrata(HEADER, ROWS, reported_total=9))


def test_unexpected_header_fails_without_repeating_values() -> None:
    handler = fake_socrata(("id_contrato", "nombre_supervisor"), [["C1", "PERSONA REAL"]])
    with pytest.raises(SocrataError) as error:
        fetch(handler)
    assert "nombre_supervisor" in str(error.value)
    assert "PERSONA REAL" not in str(error.value)


def test_malformed_row_cites_the_line_number_but_not_its_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "count(*)" in request.url.params["$select"]:
            return httpx.Response(200, text=csv_text(["total"], [["2"]]))
        body = csv_text(HEADER, [["C1", "10"]]) + '"C2","20","DATO PERSONAL"\n'
        return httpx.Response(200, text=body)

    with pytest.raises(SocrataError) as error:
        fetch(handler)
    assert "3" in str(error.value)
    assert "DATO PERSONAL" not in str(error.value)


def test_zero_rows_fails() -> None:
    with pytest.raises(SocrataError, match="0 filas"):
        fetch(fake_socrata(HEADER, []))


def test_empty_where_is_refused_before_any_request() -> None:
    log: list[httpx.Request] = []
    with pytest.raises(SocrataError, match="where"):
        fetch(fake_socrata(HEADER, ROWS, log=log), make_query(where=""))
    assert log == []


# --- Reintentos (ADR 0009) -----------------------------------------------------------------


def flaky(status: int, failures: int, calls: list[int]):
    good = fake_socrata(HEADER, ROWS)

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) <= failures:
            return httpx.Response(status)
        return good(request)

    return handler


@pytest.mark.parametrize("status", [429, 500, 503, 504])
def test_retries_on_transient_status(status: int) -> None:
    calls: list[int] = []
    extraction = fetch(flaky(status, 2, calls))
    assert extraction.rows == ROWS
    assert len(calls) > 2


def test_retries_on_connection_failure() -> None:
    good = fake_socrata(HEADER, ROWS)
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) == 1:
            raise httpx.ConnectError("sin conexión")
        return good(request)

    assert fetch(handler).rows == ROWS


def test_does_not_retry_client_errors() -> None:
    calls: list[int] = []
    with pytest.raises(SocrataError, match="400"):
        fetch(flaky(400, 99, calls))
    assert len(calls) == 1


def test_gives_up_after_the_attempt_limit() -> None:
    calls: list[int] = []
    with pytest.raises(SocrataError, match="503"):
        fetch(flaky(503, 99, calls), max_attempts=3)
    assert len(calls) == 3


# --- Consulta por lotes de identificadores (Adiciones, ADR 0009) ------------------------------

ADD_HEADER = ("id_contrato", "tipo", "fecharegistro")


def make_addition_query(**overrides: object) -> Query:
    values: dict[str, object] = {
        "id": "secop_additions",
        "where": "",
        "order_by": ":id",
        "allowed": ADD_HEADER,
        "excluded": ("descripcion",),
        "batch_source": "secop_contracts",
        "batch_column": "id_contrato",
    }
    values.update(overrides)
    return make_query(**values)


def addition_rows(ids: list[str]) -> list[list[str]]:
    return [[contract_id, "Adicion en el valor", "2022-01-12T15:08:16.288"] for contract_id in ids]


def fetch_ids(handler, ids: list[str], query: Query | None = None, **kwargs):
    return fetch_query_by_ids(
        client_for(handler), query or make_addition_query(), ids, wait=wait_none(), **kwargs
    )


def page_requests(log: list[httpx.Request]) -> list[httpx.Request]:
    return [r for r in log if "count(*)" not in r.url.params["$select"]]


def listed_ids(request: httpx.Request) -> list[str]:
    return request.url.params["$where"].removeprefix("id_contrato in(").removesuffix(")").split(",")


def test_ids_are_split_into_batches_of_200() -> None:
    ids = [f"CO1.PCCNTR.{n:04d}" for n in range(450)]
    log: list[httpx.Request] = []
    extraction = fetch_ids(fake_socrata(ADD_HEADER, addition_rows(ids), log=log), ids)

    assert [len(listed_ids(r)) for r in page_requests(log)] == [200, 200, 50]
    assert len(extraction.rows) == 450


def test_ids_are_deduplicated_and_sorted_before_batching() -> None:
    log: list[httpx.Request] = []
    ids = ["C3", "C1", "C2", "C1"]
    fetch_ids(fake_socrata(ADD_HEADER, addition_rows(["C1"]), log=log), ids)

    assert listed_ids(page_requests(log)[0]) == ["'C1'", "'C2'", "'C3'"]


def test_batch_request_keeps_select_order_and_limit() -> None:
    log: list[httpx.Request] = []
    fetch_ids(fake_socrata(ADD_HEADER, addition_rows(["C1"]), log=log), ["C1"])

    params = page_requests(log)[0].url.params
    assert params["$select"] == "id_contrato,tipo,fecharegistro"
    assert params["$order"] == ":id"
    assert params["$limit"] == "1000"


def test_count_uses_the_where_of_its_own_batch() -> None:
    log: list[httpx.Request] = []
    fetch_ids(
        fake_socrata(ADD_HEADER, addition_rows(["C1", "C2", "C3"]), log=log),
        ["C1", "C2", "C3"],
        batch_size=2,
    )

    wheres = [r.url.params["$where"] for r in log]
    assert wheres == [wheres[0], wheres[0], wheres[2], wheres[2]]
    assert wheres[0] != wheres[2]


def test_a_batch_without_additions_is_valid() -> None:
    handler = fake_socrata(ADD_HEADER, addition_rows(["C3", "C4"]))
    extraction = fetch_ids(handler, ["C1", "C2", "C3", "C4"], batch_size=2)

    assert extraction.rows == addition_rows(["C3", "C4"])
    assert extraction.total == 2


def test_no_additions_in_any_batch_fails() -> None:
    with pytest.raises(SocrataError, match="0 filas"):
        fetch_ids(fake_socrata(ADD_HEADER, []), ["C1", "C2"])


def test_empty_id_list_is_refused_before_any_request() -> None:
    log: list[httpx.Request] = []
    with pytest.raises(SocrataError, match="identificadores"):
        fetch_ids(fake_socrata(ADD_HEADER, addition_rows(["C1"]), log=log), [])
    assert log == []


def test_batch_count_mismatch_fails() -> None:
    handler = fake_socrata(ADD_HEADER, addition_rows(["C1", "C2"]), reported_total=9)
    with pytest.raises(SocrataError, match="2.*9"):
        fetch_ids(handler, ["C1", "C2"])


def test_single_quotes_in_ids_are_escaped() -> None:
    log: list[httpx.Request] = []
    fetch_ids(fake_socrata(ADD_HEADER, addition_rows(["A'B"]), log=log), ["A'B"])

    assert "'A''B'" in page_requests(log)[0].url.params["$where"]


def test_pagination_works_inside_a_batch() -> None:
    ids = ["C1", "C2", "C3", "C4", "C5"]
    extraction = fetch_ids(fake_socrata(ADD_HEADER, addition_rows(ids)), ids, page_size=2)

    assert extraction.rows == addition_rows(ids)


def test_query_without_batch_column_is_refused() -> None:
    with pytest.raises(SocrataError, match="batch_column"):
        fetch_ids(fake_socrata(ADD_HEADER, []), ["C1"], make_addition_query(batch_column=""))


def test_unexpected_header_in_a_batch_fails() -> None:
    handler = fake_socrata(("id_contrato", "descripcion", "fecharegistro"), [["C1", "x", "y"]])
    with pytest.raises(SocrataError, match="descripcion"):
        fetch_ids(handler, ["C1"])


# --- Token de aplicación (opcional) ----------------------------------------------------------


def test_app_token_header_is_sent_when_present() -> None:
    seen: list[httpx.Request] = []
    client = make_client(
        "secreto", transport=httpx.MockTransport(fake_socrata(HEADER, ROWS, log=seen))
    )
    fetch_query(client, make_query(), wait=wait_none())
    assert {r.headers["X-App-Token"] for r in seen} == {"secreto"}


def test_no_token_header_when_absent() -> None:
    seen: list[httpx.Request] = []
    fetch(fake_socrata(HEADER, ROWS, log=seen))
    assert all("X-App-Token" not in r.headers for r in seen)


def test_app_token_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOCRATA_APP_TOKEN", "  abc  ")
    assert app_token_from_env() == "abc"
    monkeypatch.setenv("SOCRATA_APP_TOKEN", "")
    assert app_token_from_env() is None
    monkeypatch.delenv("SOCRATA_APP_TOKEN")
    assert app_token_from_env() is None
