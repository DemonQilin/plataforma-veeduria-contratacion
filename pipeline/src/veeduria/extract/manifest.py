"""Manifiesto de la copia: `data/snapshot/manifest.json` (ADR 0006).

Registra por fuente el conjunto, la consulta exacta, las filas, el SHA-256 del CSV, la fecha de
extracción y la fecha de corte. Nunca guarda el token de datos.gov.co.
"""

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from veeduria.extract.http import Extraction
from veeduria.extract.sources import Query

MANIFEST_NAME = "manifest.json"
FILE_MODE = 0o644
# La fecha de corte global es la de los contratos (R12).
CUTOFF_SOURCE = "secop_contracts"

_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
# MEData escribe día/mes/año; «24/06/2022» confirma que el día va primero.
_DAY_FIRST_DATE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def to_iso_date(value: str) -> str | None:
    """Lleva una fecha de la copia a AAAA-MM-DD; `None` si no tiene un formato conocido."""
    day_first = _DAY_FIRST_DATE.fullmatch(value)
    if day_first:
        day, month, year = day_first.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    if _ISO_DATE.match(value):
        return value[:10]
    return None


def cutoff_date(query: Query, extraction: Extraction) -> str | None:
    """Fecha más reciente de la columna de corte de la consulta, o `None` si no tiene."""
    if not query.cutoff_column:
        return None
    index = extraction.header.index(query.cutoff_column)
    dates = (to_iso_date(row[index]) for row in extraction.rows)
    return max((date for date in dates if date), default=None)


def source_entry(
    query: Query,
    *,
    row_count: int,
    sha256: str,
    source_sha256: str,
    extracted_at: datetime,
    cutoff: str | None,
) -> dict[str, Any]:
    description: dict[str, Any] = {
        "select": list(query.allowed),
        "where": query.where,
        "order_by": query.order_by,
    }
    for name in ("batch_source", "batch_column", "distribution"):
        if getattr(query, name):
            description[name] = getattr(query, name)
    entry: dict[str, Any] = {
        "dataset": query.dataset,
        "url": query.url,
        "kind": query.kind,
        "query": description,
        "row_count": row_count,
        "sha256": sha256,
        "extracted_at": extracted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cutoff_date": cutoff,
    }
    if source_sha256:
        # MEData: huella del archivo descargado, para detectar si la fuente cambió.
        entry["source_sha256"] = source_sha256
    return entry


def read_manifest(directory: Path) -> dict[str, Any]:
    path = directory / MANIFEST_NAME
    if not path.exists():
        return {"cutoff_date": None, "sources": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(directory: Path, sources: dict[str, dict[str, Any]]) -> None:
    """Escribe el manifiesto de forma atómica, con llaves ordenadas y finales de línea LF."""
    contracts = sources.get(CUTOFF_SOURCE, {})
    manifest = {"cutoff_date": contracts.get("cutoff_date"), "sources": sources}
    text = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    directory.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(dir=directory, prefix=".manifest.", suffix=".tmp")
    temp = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        temp.chmod(FILE_MODE)
        os.replace(temp, directory / MANIFEST_NAME)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
