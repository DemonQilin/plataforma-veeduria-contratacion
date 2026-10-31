"""API de Socrata simulada para las pruebas: pagina y cuenta como el servicio real."""

import csv
import io
from collections.abc import Callable, Sequence

import httpx


def csv_text(header: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def fake_socrata(
    header: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    reported_total: int | None = None,
    log: list[httpx.Request] | None = None,
) -> Callable[[httpx.Request], httpx.Response]:
    """Responde `count(*)` y páginas con `$limit` y `$offset`, igual que Socrata."""

    def handler(request: httpx.Request) -> httpx.Response:
        if log is not None:
            log.append(request)
        params = request.url.params
        if "count(*)" in params["$select"]:
            total = len(rows) if reported_total is None else reported_total
            return httpx.Response(200, text=csv_text(["total"], [[str(total)]]))
        offset = int(params["$offset"])
        limit = int(params["$limit"])
        return httpx.Response(200, text=csv_text(header, rows[offset : offset + limit]))

    return handler
