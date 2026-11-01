"""Descarga y parser de MEData · Ejecución contractual (ADR 0010).

El portal solo entrega el CSV completo, con nombres y cédulas de contratistas y supervisores.
El archivo se guarda tal cual en `data/raw/` (fuera de git) y el parser conserva únicamente las
columnas de la lista blanca antes de que algo llegue a `data/snapshot/`.

Formato observado (1 nov 2026): cada línea va envuelta en comillas y termina en tres comillas
seguidas, con dos capas de escape. La exterior escribe dos barras por cada barra y una barra
con dos comillas por cada comilla, y deja una barra suelta donde abre un campo entrecomillado.
La interior es un CSV normal. Las filas completas tienen tantas columnas como el encabezado;
las cortadas en origen traen 21 o 28 y se rellenan con vacíos. Los errores citan el número de
línea, nunca su contenido.
"""

import csv
import os
import re
import tempfile
from pathlib import Path

import httpx
from tenacity import wait_exponential
from tenacity.wait import wait_base

from veeduria.extract.http import Extraction, make_retrying
from veeduria.extract.medata import DEFAULT_MAX_ATTEMPTS, DEFAULT_MAX_SECONDS, MedataError
from veeduria.extract.sources import Query

TRUNCATED = "truncated"
TRUNCATED_WIDTHS = (21, 28)

_OUTER_ESCAPE = re.compile(r'\\\\|\\""|(?<=,)\\(?=[^\\"])')


def _unescape(match: re.Match[str]) -> str:
    return "\\" if match.group() == "\\\\" else '"'


def _split_line(line: str) -> list[str] | None:
    """Campos de una línea de datos, o `None` si no tiene la envoltura esperada."""
    if len(line) < 4 or not (line.startswith('"') and line.endswith('"""')):
        return None
    body = _OUTER_ESCAPE.sub(_unescape, line[1:-3])
    try:
        return next(csv.reader([body], strict=False))
    except csv.Error:
        return None


def parse_execution_csv(text: str, query: Query) -> Extraction:
    """Proyecta el CSV a la lista blanca; falla ante cualquier fila que no pueda interpretar."""
    lines = [line.removesuffix("\r") for line in text.split("\n")]
    header_line = lines[0] if lines else ""
    if not (len(header_line) >= 2 and header_line.startswith('"') and header_line.endswith('"')):
        raise MedataError(f"{query.id}: la línea 1 no tiene el formato de encabezado esperado.")
    header = next(csv.reader([header_line[1:-1]]))
    position = {name: index for index, name in enumerate(header)}
    missing = [c for c in query.allowed if c != TRUNCATED and c not in position]
    if missing:
        raise MedataError(f"{query.id}: el encabezado no trae las columnas {missing}.")

    width = len(header)
    rows: list[list[str]] = []
    for number, line in enumerate(lines[1:], start=2):
        if not line:
            continue
        fields = _split_line(line)
        if fields is None:
            raise MedataError(f"{query.id}: la línea {number} no tiene el formato esperado.")
        if len(fields) != width and len(fields) not in TRUNCATED_WIDTHS:
            raise MedataError(
                f"{query.id}: la línea {number} tiene {len(fields)} columnas y se esperaban "
                f"{width}, {' o '.join(map(str, TRUNCATED_WIDTHS))} si viene cortada."
            )
        is_truncated = len(fields) < width
        values = fields + [""] * (width - len(fields))
        rows.append(
            [
                ("true" if is_truncated else "false")
                if column == TRUNCATED
                else values[position[column]]
                for column in query.allowed
            ]
        )

    if not rows:
        raise MedataError(f"{query.id}: el archivo trae 0 filas.")
    return Extraction(header=query.allowed, rows=rows, total=len(rows))


def _download(
    client: httpx.Client,
    query: Query,
    destination: Path,
    wait: wait_base,
    max_attempts: int,
    max_seconds: float,
) -> None:
    try:
        for attempt in make_retrying(wait, max_attempts, max_seconds):
            with attempt:
                with client.stream("GET", query.url) as response:
                    response.raise_for_status()
                    with destination.open("wb") as handle:
                        for chunk in response.iter_bytes():
                            handle.write(chunk)
    except httpx.HTTPStatusError as error:
        raise MedataError(
            f"{query.id}: el portal respondió HTTP {error.response.status_code}."
        ) from None
    except httpx.TransportError as error:
        raise MedataError(
            f"{query.id}: falla de conexión con el portal: {type(error).__name__}."
        ) from None


def fetch_csv_query(
    client: httpx.Client,
    query: Query,
    raw_dir: Path,
    *,
    wait: wait_base | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    max_seconds: float = DEFAULT_MAX_SECONDS,
) -> Extraction:
    """Descarga el CSV a `raw_dir` y lo parsea.

    El archivo anterior solo se reemplaza si la descarga y el parseo salieron bien.
    """
    wait = wait or wait_exponential(multiplier=1, min=1, max=30)
    raw_dir.mkdir(parents=True, exist_ok=True)
    final = raw_dir / f"{query.id}.csv"
    descriptor, temp_name = tempfile.mkstemp(dir=raw_dir, prefix=f".{query.id}.", suffix=".tmp")
    os.close(descriptor)
    temp = Path(temp_name)  # mkstemp lo crea con modo 0600: tiene datos personales
    try:
        _download(client, query, temp, wait, max_attempts, max_seconds)
        try:
            text = temp.read_bytes().decode("utf-8-sig")
        except UnicodeDecodeError:
            raise MedataError(f"{query.id}: el archivo no está en UTF-8.") from None
        extraction = parse_execution_csv(text, query)
        os.replace(temp, final)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    return extraction
