"""API SQL de MEData simulada para las pruebas: pagina y cuenta como el portal real."""

import re
from collections.abc import Callable, Sequence

import httpx

COUNT_QUERY = re.compile(r"^\[SELECT COUNT\(\*\) FROM ([\w-]+)\];$")
PAGE_QUERY = re.compile(
    r"^\[SELECT ([\w,]+) FROM ([\w-]+)\]\[ORDER BY ([\w,]+) ASC\]"
    r"\[LIMIT (\d+) OFFSET (\d+)\];$"
)


def fake_medata(
    header: Sequence[str],
    rows: Sequence[Sequence[str | None]],
    *,
    reported_total: int | None = None,
    log: list[httpx.Request] | None = None,
) -> Callable[[httpx.Request], httpx.Response]:
    """Responde `COUNT(*)` y páginas con `LIMIT` y `OFFSET`, en JSON como el portal."""

    def handler(request: httpx.Request) -> httpx.Response:
        if log is not None:
            log.append(request)
        query = request.url.params["query"]
        if COUNT_QUERY.match(query):
            total = len(rows) if reported_total is None else reported_total
            return httpx.Response(200, json=[{"expression": str(total)}])
        match = PAGE_QUERY.match(query)
        if not match:
            return httpx.Response(400, json={"message": "Syntax error.", "status": 400})
        columns = match.group(1).split(",")
        limit, offset = int(match.group(4)), int(match.group(5))
        page = rows[offset : offset + limit]
        indexes = [header.index(column) for column in columns]
        body = [{c: r[i] for c, i in zip(columns, indexes, strict=True)} for r in page]
        return httpx.Response(200, json=body)

    return handler
