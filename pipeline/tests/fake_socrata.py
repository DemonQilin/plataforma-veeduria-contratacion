"""API de Socrata simulada para las pruebas: pagina y cuenta como el servicio real."""

import csv
import io
import re
from collections.abc import Callable, Sequence

import httpx

IN_CLAUSE = re.compile(r"^(\w+) in\((.*)\)$")
QUOTED_VALUE = re.compile(r"'((?:[^']|'')*)'")


def select_rows(
    header: Sequence[str], rows: Sequence[Sequence[str]], where: str
) -> list[Sequence[str]]:
    """Aplica `columna in('a','b')`; cualquier otro `where` deja todas las filas."""
    match = IN_CLAUSE.match(where)
    if not match:
        return list(rows)
    wanted = {value.replace("''", "'") for value in QUOTED_VALUE.findall(match.group(2))}
    index = header.index(match.group(1))
    return [row for row in rows if row[index] in wanted]


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
        selected = select_rows(header, rows, params.get("$where", ""))
        if "count(*)" in params["$select"]:
            total = len(selected) if reported_total is None else reported_total
            return httpx.Response(200, text=csv_text(["total"], [[str(total)]]))
        offset = int(params["$offset"])
        limit = int(params["$limit"])
        return httpx.Response(200, text=csv_text(header, selected[offset : offset + limit]))

    return handler
