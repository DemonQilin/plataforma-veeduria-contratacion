"""Modelos del contrato con el tablero (ADR 0004).

Son la única fuente de verdad: de aquí salen `data/schema/*.json` y
`web/src/types/contract.ts`.
"""

import json
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    url: str
    license: str


class Metadata(BaseModel):
    """Fecha de corte, fuentes con enlace y licencia, y versión de las reglas."""

    model_config = ConfigDict(extra="forbid")

    cutoff_date: date
    sources: list[Source]
    rules_version: str


CONTRACT_MODELS: dict[str, type[BaseModel]] = {
    "metadata": Metadata,
}


def export_schemas(output_dir: Path) -> list[Path]:
    """Escribe un JSON Schema por modelo, con llaves ordenadas y finales de línea LF."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, model in sorted(CONTRACT_MODELS.items()):
        schema = json.dumps(model.model_json_schema(), indent=2, sort_keys=True, ensure_ascii=False)
        path = output_dir / f"{name}.json"
        path.write_bytes((schema + "\n").encode("utf-8"))
        written.append(path)
    return written
