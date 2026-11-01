"""Cliente de la API SQL de MEData (ADR 0018).

Pide solo las columnas de la lista blanca, ordena por `record_number` y pagina hasta una
página corta. Al terminar compara las filas recibidas con un `COUNT(*)`. El portal da 504
de forma intermitente: cada petición se reintenta con espera exponencial, con un límite de
intentos y de tiempo. Los errores citan columnas y números de línea, nunca valores.
"""

import httpx
from tenacity import wait_exponential
from tenacity.wait import wait_base

from veeduria.extract.http import Extraction, ExtractionError, make_retrying
from veeduria.extract.sources import Query

DEFAULT_PAGE_SIZE = 1000
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_MAX_SECONDS = 300.0


class MedataError(ExtractionError):
    """La extracción de MEData no puede garantizar una copia completa y correcta."""


def _get_json(
    client: httpx.Client,
    query: Query,
    sql: str,
    wait: wait_base,
    max_attempts: int,
    max_seconds: float,
) -> object:
    try:
        for attempt in make_retrying(wait, max_attempts, max_seconds):
            with attempt:
                response = client.get(query.url, params={"query": sql})
                response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise MedataError(
            f"{query.id}: la API respondió HTTP {error.response.status_code}."
        ) from None
    except httpx.TransportError as error:
        raise MedataError(
            f"{query.id}: falla de conexión con la API: {type(error).__name__}."
        ) from None
    try:
        return response.json()
    except ValueError:
        raise MedataError(f"{query.id}: respuesta inesperada, no es JSON.") from None


def _count(
    client: httpx.Client, query: Query, wait: wait_base, max_attempts: int, max_seconds: float
) -> int:
    sql = f"[SELECT COUNT(*) FROM {query.distribution}];"
    body = _get_json(client, query, sql, wait, max_attempts, max_seconds)
    try:
        return int(body[0]["expression"])  # type: ignore[index]
    except (IndexError, KeyError, TypeError, ValueError):
        raise MedataError(f"{query.id}: respuesta inesperada al contar las filas.") from None


def _check_row(query: Query, row: object, line: int) -> list[str]:
    if not isinstance(row, dict):
        raise MedataError(f"{query.id}: respuesta inesperada en la línea {line}.")
    unexpected = sorted(set(row) - set(query.allowed))
    missing = sorted(set(query.allowed) - set(row))
    if unexpected or missing:
        raise MedataError(
            f"{query.id}: la línea {line} no coincide con la lista blanca "
            f"(columnas inesperadas: {unexpected}; faltantes: {missing})."
        )
    return ["" if row[column] is None else str(row[column]) for column in query.allowed]


def fetch_sql_query(
    client: httpx.Client,
    query: Query,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    wait: wait_base | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    max_seconds: float = DEFAULT_MAX_SECONDS,
) -> Extraction:
    """Descarga todas las filas de la distribución o falla sin devolver una copia parcial."""
    if not query.distribution:
        raise MedataError(f"{query.id}: la consulta no declara distribution en sources.toml.")
    wait = wait or wait_exponential(multiplier=1, min=1, max=30)

    select = ",".join(query.allowed)
    rows: list[list[str]] = []
    offset = 0
    while True:
        sql = (
            f"[SELECT {select} FROM {query.distribution}]"
            f"[ORDER BY {query.order_by} ASC][LIMIT {page_size} OFFSET {offset}];"
        )
        body = _get_json(client, query, sql, wait, max_attempts, max_seconds)
        if not isinstance(body, list):
            raise MedataError(f"{query.id}: respuesta inesperada, no es una lista de filas.")
        # Línea del archivo final: el encabezado es la 1.
        rows.extend(_check_row(query, row, offset + index + 2) for index, row in enumerate(body))
        if len(body) < page_size:
            break
        offset += page_size

    total = _count(client, query, wait, max_attempts, max_seconds)
    if len(rows) != total:
        raise MedataError(f"{query.id}: se recibieron {len(rows)} filas y count(*) da {total}.")
    if not rows:
        raise MedataError(f"{query.id}: la consulta devolvió 0 filas.")
    return Extraction(header=query.allowed, rows=rows, total=total)
