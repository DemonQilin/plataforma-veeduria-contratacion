"""Cliente de la API SQL de MEData (ADR 0018): paginación, conteo y reintentos."""

import httpx
import pytest
from tenacity import wait_none

from tests.fake_medata import fake_medata
from veeduria.extract.http import ExtractionError
from veeduria.extract.medata import MedataError, fetch_sql_query
from veeduria.extract.socrata import SocrataError, make_client
from veeduria.extract.sources import Query

HEADER = ("ano", "modalidad_seleccion")
ROWS = [[f"202{n}.0", f"Modalidad {n}"] for n in range(5)]
DISTRIBUTION = "f338ad23-c393-51bc-8455-b0405e7d8655"


def make_query(**overrides: object) -> Query:
    values: dict[str, object] = {
        "id": "medata_procurement_plan",
        "dataset": "1-028-11-000089",
        "kind": "medata_sql",
        "url": "https://example.test/api/1/datastore/sql/",
        "where": "",
        "order_by": "record_number",
        "allowed": HEADER,
        "excluded": ("descripcion",),
        "distribution": DISTRIBUTION,
    }
    values.update(overrides)
    return Query(**values)  # type: ignore[arg-type]


def client_for(handler) -> httpx.Client:
    return make_client(None, transport=httpx.MockTransport(handler))


def fetch(handler, query: Query | None = None, **kwargs):
    return fetch_sql_query(client_for(handler), query or make_query(), wait=wait_none(), **kwargs)


def sql_requests(log: list[httpx.Request]) -> list[str]:
    return [r.url.params["query"] for r in log if "COUNT(*)" not in r.url.params["query"]]


# --- Consulta (R17, ADR 0018) -------------------------------------------------------------


def test_request_selects_only_allowed_columns_ordered_by_record_number() -> None:
    log: list[httpx.Request] = []
    fetch(fake_medata(HEADER, ROWS, log=log), page_size=10)

    assert sql_requests(log) == [
        f"[SELECT ano,modalidad_seleccion FROM {DISTRIBUTION}]"
        "[ORDER BY record_number ASC][LIMIT 10 OFFSET 0];"
    ]
    assert all("*" not in r.url.params["query"].replace("COUNT(*)", "") for r in log)
    assert log[0].url.path == "/api/1/datastore/sql/"


def test_pages_until_a_short_page_and_returns_every_row() -> None:
    log: list[httpx.Request] = []
    extraction = fetch(fake_medata(HEADER, ROWS, log=log), page_size=2)

    assert extraction.header == HEADER
    assert extraction.rows == ROWS
    assert extraction.total == 5
    assert [q.split("OFFSET ")[1] for q in sql_requests(log)] == ["0];", "2];", "4];"]


def test_a_full_last_page_asks_for_one_more_empty_page() -> None:
    log: list[httpx.Request] = []
    extraction = fetch(fake_medata(HEADER, ROWS[:4], log=log), page_size=2)

    assert len(extraction.rows) == 4
    assert len(sql_requests(log)) == 3


def test_null_values_become_empty_strings() -> None:
    rows = [["2022.0", None], ["2023.0", "Contratacion Directa"]]
    extraction = fetch(fake_medata(HEADER, rows))

    assert extraction.rows == [["2022.0", ""], ["2023.0", "Contratacion Directa"]]


# --- Verificación (ADR 0018) --------------------------------------------------------------


def test_count_mismatch_fails() -> None:
    with pytest.raises(MedataError, match="count"):
        fetch(fake_medata(HEADER, ROWS, reported_total=99))


def test_zero_rows_fails() -> None:
    with pytest.raises(MedataError, match="0 filas"):
        fetch(fake_medata(HEADER, []))


def test_query_without_distribution_fails_before_any_request() -> None:
    log: list[httpx.Request] = []
    with pytest.raises(MedataError, match="distribution"):
        fetch(fake_medata(HEADER, ROWS, log=log), make_query(distribution=""))
    assert log == []


def test_a_column_outside_the_allowlist_fails_without_leaking_the_value() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "COUNT(*)" in request.url.params["query"]:
            return httpx.Response(200, json=[{"expression": "1"}])
        return httpx.Response(200, json=[{"ano": "2022.0", "contratista": "NOMBRE SECRETO"}])

    with pytest.raises(MedataError) as error:
        fetch(handler)
    assert "contratista" in str(error.value)
    assert "NOMBRE SECRETO" not in str(error.value)


def test_a_row_missing_a_column_fails_with_its_line_number() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "COUNT(*)" in request.url.params["query"]:
            return httpx.Response(200, json=[{"expression": "2"}])
        return httpx.Response(
            200, json=[{"ano": "2022.0", "modalidad_seleccion": "x"}, {"ano": "2023.0"}]
        )

    with pytest.raises(MedataError, match="línea 3"):
        fetch(handler)


def test_a_response_that_is_not_a_list_of_rows_fails() -> None:
    handler = lambda request: httpx.Response(200, json={"message": "otra cosa"})  # noqa: E731
    with pytest.raises(MedataError, match="inesperada"):
        fetch(handler)


# --- Reintentos y tiempo límite (ADR 0018) ------------------------------------------------


def flaky(inner, failures: int, status: int = 504):
    state = {"left": failures}

    def handler(request: httpx.Request) -> httpx.Response:
        if state["left"] > 0:
            state["left"] -= 1
            return httpx.Response(status, text="Gateway Time-out")
        return inner(request)

    return handler


def test_a_504_followed_by_success_is_retried() -> None:
    extraction = fetch(flaky(fake_medata(HEADER, ROWS), failures=2))
    assert extraction.rows == ROWS


def test_a_persistent_504_fails_after_the_attempt_limit() -> None:
    log: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        log.append(request)
        return httpx.Response(504, text="Gateway Time-out")

    with pytest.raises(MedataError, match="504"):
        fetch(handler, max_attempts=3)
    assert len(log) == 3


def test_a_400_is_not_retried() -> None:
    log: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        log.append(request)
        return httpx.Response(400, json={"message": "Column not found.", "status": 400})

    with pytest.raises(MedataError, match="400"):
        fetch(handler)
    assert len(log) == 1


def test_the_time_limit_stops_the_retries() -> None:
    log: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        log.append(request)
        return httpx.Response(504, text="Gateway Time-out")

    with pytest.raises(MedataError):
        fetch(handler, max_attempts=50, max_seconds=0)
    assert len(log) == 1


def test_connection_failures_are_reported_without_details() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    with pytest.raises(MedataError, match="ConnectError"):
        fetch(handler, max_attempts=2)


# --- Compatibilidad entre errores de extracción -------------------------------------------


def test_both_extraction_errors_share_a_base_class() -> None:
    assert issubclass(MedataError, ExtractionError)
    assert issubclass(SocrataError, ExtractionError)
