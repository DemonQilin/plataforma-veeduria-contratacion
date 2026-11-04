"""Modelos del contrato con el tablero (ADR 0004).

Son la única fuente de verdad: de aquí salen `data/schema/*.json` y
`web/src/types/contract.ts`.
"""

import json
from datetime import date
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class IndicatorCell(BaseModel):
    """Un indicador en un nivel y un periodo, con su trazabilidad (R16).

    Una celda suprimida (R13) publica su `sample_size` y oculta numerador, denominador y razón.
    """

    model_config = ConfigDict(extra="forbid")

    indicator: Literal["I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8"]
    variant: str | None
    measure: Literal["count", "value"]
    level: Literal["district", "department"]
    department: str | None
    period: str = Field(pattern=r"^\d{4}(-\d{2})?$")
    sample_size: int = Field(ge=0)
    numerator: float | None
    denominator: float | None
    ratio: float | None
    is_suppressed: bool

    @model_validator(mode="after")
    def check_coherence(self) -> Self:
        # R13: una celda suprimida no puede llevar ninguna cifra que permita despejarla.
        figures = (self.numerator, self.denominator, self.ratio)
        if self.is_suppressed and any(figure is not None for figure in figures):
            raise ValueError("Una celda suprimida no publica numerador, denominador ni razón.")
        # R16: una celda publicada trae las tres cifras para poder reconstruirla.
        if not self.is_suppressed and any(figure is None for figure in figures):
            raise ValueError("Una celda publicada trae numerador, denominador y razón.")
        if (self.level == "department") != (self.department is not None):
            raise ValueError("La secretaría va si y solo si el nivel es `department`.")
        return self


class Indicators(BaseModel):
    """Una fila por indicador, nivel y periodo (docs/reglas.md, sección 7)."""

    model_config = ConfigDict(extra="forbid")

    cells: list[IndicatorCell]


CONTRACT_MODELS: dict[str, type[BaseModel]] = {
    "indicators": Indicators,
    "metadata": Metadata,
}


def export_schemas(output_dir: Path) -> list[Path]:
    """Escribe un JSON Schema por modelo, con llaves ordenadas y finales de línea LF.

    Borra los esquemas que ya no tienen modelo, para que el contrato no conserve restos.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("*.json"):
        if stale.stem not in CONTRACT_MODELS:
            stale.unlink()
    written: list[Path] = []
    for name, model in sorted(CONTRACT_MODELS.items()):
        schema = json.dumps(model.model_json_schema(), indent=2, sort_keys=True, ensure_ascii=False)
        path = output_dir / f"{name}.json"
        path.write_bytes((schema + "\n").encode("utf-8"))
        written.append(path)
    return written
