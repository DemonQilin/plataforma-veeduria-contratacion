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


class ReconciliationMonth(BaseModel):
    """Un mes de la conciliación SECOP–MEData (R15; ADR 0031).

    Publica los conteos junto a las razones: con pocos contratos, uno de diferencia mueve mucho
    el porcentaje y el tablero debe mostrar la base (ADR 0038).
    """

    model_config = ConfigDict(extra="forbid")

    # El título distinto evita que el generador de tipos cree dos alias `Period`.
    period: str = Field(pattern=r"^\d{4}-\d{2}$", title="ReconciliationPeriod")
    secop_count: int = Field(ge=0)
    medata_count: int = Field(ge=0)
    shared_count: int = Field(ge=0)
    union_count: int = Field(ge=0)
    shared_share: float | None
    secop_coverage: float | None
    medata_coverage: float | None
    below_threshold: bool

    @model_validator(mode="after")
    def check_coherence(self) -> Self:
        if self.union_count != self.secop_count + self.medata_count - self.shared_count:
            raise ValueError("La unión es SECOP II más MEData menos los contratos en ambas.")
        if (self.shared_share is None) != (self.union_count == 0):
            raise ValueError("La razón de un mes falta si y solo si el mes no tiene contratos.")
        return self


class Reconciliation(BaseModel):
    """Conciliación mensual y el umbral con el que se advierte (R15)."""

    model_config = ConfigDict(extra="forbid")

    threshold: float
    months: list[ReconciliationMonth]


class QualityShare(BaseModel):
    """Cuántos de un total cumplen una condición de calidad, con su proporción (ADR 0042)."""

    model_config = ConfigDict(extra="forbid")

    count: int = Field(ge=0)
    total: int = Field(ge=0)
    share: float | None

    @model_validator(mode="after")
    def check_coherence(self) -> Self:
        if self.count > self.total:
            raise ValueError("El conteo no puede superar al total.")
        if (self.share is None) != (self.total == 0):
            raise ValueError("La proporción falta si y solo si el total es cero.")
        return self


class UnassignedYear(BaseModel):
    """Contratos sin secretaría de un año de firma (R8)."""

    model_config = ConfigDict(extra="forbid")

    # El título distinto evita que el generador de tipos cree dos alias `Period`.
    period: str = Field(pattern=r"^\d{4}$", title="UnassignedPeriod")
    unassigned: QualityShare


class UnassignedShare(BaseModel):
    """Contratos «Sin asignar» en el Distrito y por año de firma (R8; ADR 0042)."""

    model_config = ConfigDict(extra="forbid")

    district: QualityShare
    years: list[UnassignedYear]


class TruncatedRows(BaseModel):
    """Filas de MEData cortadas en origen, que no traen valores (ADR 0010, ADR 0028, ADR 0042).

    `rows` son las líneas de MEData · Ejecución; `contracts`, los contratos cuyas líneas vienen
    todas cortadas.
    """

    model_config = ConfigDict(extra="forbid")

    rows: QualityShare
    contracts: QualityShare


class UnrecognizedValue(BaseModel):
    """Un texto que un catálogo no reconoce, con las filas de la copia que lo traen (R6)."""

    model_config = ConfigDict(extra="forbid")

    catalog: Literal[
        "procurement_method", "contract_type", "supplier_type", "addition_type", "department"
    ]
    # El título distinto evita chocar con la interfaz `Source` de los metadatos.
    source: str = Field(title="UnrecognizedSource")
    raw_text: str
    row_count: int = Field(ge=1)


class Quality(BaseModel):
    """Calidad de datos que el tablero advierte (docs/reglas.md, sección 7)."""

    model_config = ConfigDict(extra="forbid")

    reconciliation: Reconciliation
    unassigned_share: UnassignedShare
    truncated_rows: TruncatedRows
    unsigned_records: QualityShare
    unrecognized_values: list[UnrecognizedValue]


ProcurementMethod = Literal[
    "direct_award",
    "special_regime",
    "public_tender",
    "abbreviated_selection",
    "merit_based_selection",
    "minimum_amount",
    "other",
]
ContractType = Literal[
    "service_contract",
    "interadministrative",
    "works",
    "supply_and_purchase",
    "public_credit",
    "other",
]


class MonthlySeriesRow(BaseModel):
    """Contratos y valor de un mes, por modalidad y tipo (docs/reglas.md, sección 7; ADR 0040).

    Una modalidad o un tipo vacíos son el total de esa dimensión. El conteo siempre se publica
    (es la `n` de R13); el valor se suprime si lo respaldan menos de 5 contratos con valor.
    """

    model_config = ConfigDict(extra="forbid")

    # El título distinto evita que el generador de tipos cree dos alias `Period`.
    period: str = Field(pattern=r"^\d{4}-\d{2}$", title="SeriesPeriod")
    procurement_method: ProcurementMethod | None
    contract_type: ContractType | None
    contract_count: int = Field(ge=0)
    value_sample_size: int = Field(ge=0)
    value: float | None
    is_suppressed: bool = Field(title="SeriesIsSuppressed")

    @model_validator(mode="after")
    def check_coherence(self) -> Self:
        # R13: una celda suprimida no publica el valor; una publicada lo trae (R16).
        if self.is_suppressed != (self.value is None):
            raise ValueError("El valor falta si y solo si la celda está suprimida.")
        # R7: solo cuentan en el valor los contratos con valor, que son parte de los del mes.
        if self.value_sample_size > self.contract_count:
            raise ValueError("Los contratos con valor no pueden superar a los del mes.")
        return self


class MonthlySeries(BaseModel):
    """Una fila por mes, modalidad y tipo del Distrito (docs/reglas.md, sección 7)."""

    model_config = ConfigDict(extra="forbid")

    rows: list[MonthlySeriesRow]


class ElectoralRestriction(BaseModel):
    """Un periodo de la Ley de Garantías con su fuente (R10).

    `status` es relativo a la fecha de corte (R12): `ended` si ya terminó, `upcoming` si aún no
    empieza y `ongoing` en cualquier otro caso. Los extremos son inclusivos.
    """

    model_config = ConfigDict(extra="forbid")

    cycle: str
    scope: Literal["direct_award", "interadministrative"]
    start: date
    end: date
    status: Literal["ended", "ongoing", "upcoming"]
    sources: list[str] = Field(min_length=1, title="RestrictionSources")


class ComparisonYear(BaseModel):
    """La ventana de comparación de I2 de un año (R11, R12)."""

    model_config = ConfigDict(extra="forbid")

    year: int
    role: Literal["treatment", "control"]
    window_start: date
    window_end: date
    denominator_end: date
    reference_restriction_end: date


class ElectoralCalendar(BaseModel):
    """Restricciones por inicio y ventanas de I2 por año (docs/reglas.md, sección 7)."""

    model_config = ConfigDict(extra="forbid")

    restrictions: list[ElectoralRestriction]
    comparison_windows: list[ComparisonYear]


CONTRACT_MODELS: dict[str, type[BaseModel]] = {
    "electoral_calendar": ElectoralCalendar,
    "indicators": Indicators,
    "metadata": Metadata,
    "monthly_series": MonthlySeries,
    "quality": Quality,
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
