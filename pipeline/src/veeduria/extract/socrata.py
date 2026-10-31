"""Cliente de Socrata para datos.gov.co (ADR 0009).

Pide siempre el endpoint CSV, con `$select` explícito, filtro en `$where`, orden estable
y paginación completa. Al terminar compara las filas recibidas con un `count(*)` de la
misma consulta. Los errores citan columnas y números de línea, nunca el contenido de una
fila, porque puede traer datos personales (regla no negociable 1).
"""

import csv
import io
import os
from collections.abc import Sequence
from dataclasses import dataclass

import httpx
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)
from tenacity.wait import wait_base

from veeduria.extract.sources import Query

DEFAULT_PAGE_SIZE = 1000
DEFAULT_MAX_ATTEMPTS = 5
REQUEST_TIMEOUT_SECONDS = 60.0
TOKEN_ENV_VAR = "SOCRATA_APP_TOKEN"


class SocrataError(Exception):
    """La extracción no puede garantizar una copia completa y correcta."""


@dataclass(frozen=True)
class Extraction:
    header: tuple[str, ...]
    rows: list[list[str]]
    total: int


def app_token_from_env() -> str | None:
    """El token es opcional: sin él, las peticiones comparten el cupo por IP."""
    return os.environ.get(TOKEN_ENV_VAR, "").strip() or None


def make_client(token: str | None, transport: httpx.BaseTransport | None = None) -> httpx.Client:
    headers = {"X-App-Token": token} if token else {}
    return httpx.Client(
        headers=headers,
        timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS),
        transport=transport,
    )


def _is_retryable(error: BaseException) -> bool:
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        return status == 429 or status >= 500
    return isinstance(error, httpx.TransportError)


def _get(
    client: httpx.Client,
    url: str,
    params: dict[str, str],
    wait: wait_base,
    max_attempts: int,
) -> list[list[str]]:
    retrying = Retrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait,
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )
    try:
        for attempt in retrying:
            with attempt:
                response = client.get(url, params=params)
                response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise SocrataError(f"La API respondió HTTP {error.response.status_code}.") from None
    except httpx.TransportError as error:
        raise SocrataError(f"Falla de conexión con la API: {type(error).__name__}.") from None
    return list(csv.reader(io.StringIO(response.text, newline="")))


def _check_header(query: Query, header: Sequence[str]) -> tuple[str, ...]:
    if tuple(header) != query.allowed:
        unexpected = sorted(set(header) - set(query.allowed))
        missing = sorted(set(query.allowed) - set(header))
        raise SocrataError(
            f"{query.id}: el encabezado no coincide con la lista blanca "
            f"(columnas inesperadas: {unexpected}; faltantes: {missing})."
        )
    return tuple(header)


def _count(client: httpx.Client, query: Query, wait: wait_base, max_attempts: int) -> int:
    params = {"$select": "count(*) AS total", "$where": query.where}
    table = _get(client, query.url, params, wait, max_attempts)
    try:
        return int(table[1][0])
    except (IndexError, ValueError):
        raise SocrataError(f"{query.id}: respuesta inesperada al contar las filas.") from None


def fetch_query(
    client: httpx.Client,
    query: Query,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    wait: wait_base | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> Extraction:
    """Descarga todas las filas de la consulta o falla sin devolver una copia parcial."""
    if not query.where.strip():
        # Sin `where` se descargaría el conjunto nacional con todas sus filas.
        raise SocrataError(f"{query.id}: la consulta no tiene where; no se descarga el conjunto.")
    wait = wait or wait_exponential(multiplier=1, min=1, max=30)

    select = ",".join(query.allowed)
    header: tuple[str, ...] = ()
    rows: list[list[str]] = []
    offset = 0
    while True:
        params = {
            "$select": select,
            "$where": query.where,
            "$order": query.order_by,
            "$limit": str(page_size),
            "$offset": str(offset),
        }
        table = _get(client, query.url, params, wait, max_attempts)
        if not table:
            raise SocrataError(f"{query.id}: la API devolvió una respuesta vacía.")
        header = _check_header(query, table[0])
        page = table[1:]
        for index, row in enumerate(page):
            if len(row) != len(header):
                # Línea del archivo final: el encabezado es la 1.
                raise SocrataError(
                    f"{query.id}: la línea {offset + index + 2} tiene {len(row)} columnas "
                    f"y se esperaban {len(header)}."
                )
        rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size

    total = _count(client, query, wait, max_attempts)
    if len(rows) != total:
        raise SocrataError(f"{query.id}: se recibieron {len(rows)} filas y count(*) da {total}.")
    if not rows:
        raise SocrataError(f"{query.id}: la consulta devolvió 0 filas.")
    return Extraction(header=header, rows=rows, total=total)
