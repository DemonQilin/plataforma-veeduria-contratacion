"""Piezas comunes de los clientes de extracción: errores, resultado y criterio de reintento."""

from dataclasses import dataclass

import httpx


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
