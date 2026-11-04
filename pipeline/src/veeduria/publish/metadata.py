"""Metadatos del contrato: fecha de corte (R12), fuentes y versión de las reglas (R16)."""

import json
from datetime import date

import duckdb
from pydantic import BaseModel

from veeduria.extract.sources import load_datasets
from veeduria.publish.models import Metadata, Source

# Sube cuando cambia una regla R1–R17 y, con ella, alguna cifra publicada.
RULES_VERSION = "1"


def build_metadata(connection: duckdb.DuckDBPyConnection) -> Metadata:
    """R12: la fecha de corte es la firma más reciente de la copia, nunca el reloj."""
    row = connection.execute("SELECT max(signed_date)::DATE FROM canonical_contracts").fetchone()
    cutoff = row[0] if row else None
    if not isinstance(cutoff, date):
        raise ValueError("La copia no tiene contratos con fecha de firma.")
    sources = sorted(load_datasets(), key=lambda dataset: dataset.name)
    return Metadata(
        cutoff_date=cutoff,
        sources=[Source(name=item.name, url=item.url, license=item.license) for item in sources],
        rules_version=RULES_VERSION,
    )


def serialize(model: BaseModel) -> bytes:
    """JSON con llaves ordenadas, sangría fija y final de línea LF."""
    text = json.dumps(model.model_dump(mode="json"), indent=2, sort_keys=True, ensure_ascii=False)
    return (text + "\n").encode("utf-8")
