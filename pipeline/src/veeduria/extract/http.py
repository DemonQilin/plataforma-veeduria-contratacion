"""Piezas comunes de los clientes de extracción: errores, resultado y criterio de reintento."""

from dataclasses import dataclass

import httpx
from tenacity import Retrying, retry_if_exception, stop_after_attempt, stop_after_delay
from tenacity.wait import wait_base


class ExtractionError(Exception):
    """La extracción no puede garantizar una copia completa y correcta."""


@dataclass(frozen=True)
class Extraction:
    header: tuple[str, ...]
    rows: list[list[str]]
    total: int


def is_retryable(error: BaseException) -> bool:
    """Reintenta límites de uso, errores del servidor y fallas de conexión; nada más."""
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        return status == 429 or status >= 500
    return isinstance(error, httpx.TransportError)


def make_retrying(wait: wait_base, max_attempts: int, max_seconds: float) -> Retrying:
    """Reintentos con límite de intentos y de tiempo total; relanza el último error."""
    return Retrying(
        stop=stop_after_attempt(max_attempts) | stop_after_delay(max_seconds),
        wait=wait,
        retry=retry_if_exception(is_retryable),
        reraise=True,
    )
