"""Calendario electoral (R10) y ventanas de comparación de I2 (R11, R12)."""

import tomllib
from dataclasses import dataclass
from datetime import date, timedelta
from functools import cache
from pathlib import Path
from typing import Literal

from veeduria.normalize.catalogs import REFERENCE_DIR, CatalogError

ELECTORAL_CALENDAR_PATH = REFERENCE_DIR / "electoral_calendar.toml"
DIRECT_AWARD_SCOPE = "direct_award"
SCOPES = frozenset({DIRECT_AWARD_SCOPE, "interadministrative"})
_COMMON_YEAR = 2001  # año no bisiesto para calcular puntos medios por día y mes


@dataclass(frozen=True)
class Restriction:
    """Una restricción de la Ley de Garantías, con la fuente de sus fechas (R10)."""

    cycle: str
    scope: str
    start: date
    end: date
    sources: tuple[str, ...]


@dataclass(frozen=True)
class ComparisonWindow:
    """Ventana de comparación de I2 para un año (R11).

    `restriction_end` es el fin de la restricción presidencial y solo existe en los años de
    tratamiento; los años de control no tienen restricción.

    `reference_restriction_end` es el fin de restricción contra el que se compara la terminación de
    los contratos (ADR 0035): el real en los años de tratamiento y, en los de control, el punto
    medio de los fines de restricción presidencial, para que los dos grupos sean comparables.
    """

    year: int
    role: Literal["treatment", "control"]
    window_start: date
    window_end: date
    denominator_end: date
    restriction_end: date | None
    reference_restriction_end: date


@cache
def load_electoral_calendar(path: Path = ELECTORAL_CALENDAR_PATH) -> tuple[Restriction, ...]:
    """Lee y valida el calendario; lo mal formado lanza `CatalogError`."""
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    restrictions: list[Restriction] = []
    cycles: set[str] = set()
    for entry in data.get("restriction", []):
        restriction = Restriction(
            cycle=entry["cycle"],
            scope=entry["scope"],
            start=entry["start"],
            end=entry["end"],
            sources=tuple(entry.get("sources", [])),
        )
        if restriction.cycle in cycles:
            raise CatalogError(f"El ciclo «{restriction.cycle}» está repetido en el calendario.")
        cycles.add(restriction.cycle)
        if restriction.scope not in SCOPES:
            raise CatalogError(f"El alcance «{restriction.scope}» no existe ({restriction.cycle}).")
        if restriction.start >= restriction.end:
            raise CatalogError(f"El inicio no es anterior al fin ({restriction.cycle}).")
        if not restriction.sources:
            raise CatalogError(f"La restricción «{restriction.cycle}» no cita su fuente (R10).")
        restrictions.append(restriction)
    return tuple(sorted(restrictions, key=lambda restriction: restriction.start))


def comparison_windows(
    calendar: tuple[Restriction, ...], cutoff_date: date
) -> list[ComparisonWindow]:
    """Ventanas de I2 por año hasta la fecha de corte, ordenadas por año (R11, R12).

    - Tratamiento: cada año con restricción de contratación directa; la ventana va del 1 de enero
      al día anterior al inicio de la restricción.
    - Control: los años intermedios sin restricción, con la ventana a mitad de camino entre las de
      tratamiento, para comparar periodos de igual duración.
    - Denominador: del 1 de enero al día y mes de la fecha de corte en todos los años (tramo común).
    - Fin de restricción de referencia: el real en tratamiento; en control, el punto medio de los
      fines de restricción presidencial (20 de junio con el calendario actual, ADR 0035).
    """
    direct = [r for r in calendar if r.scope == DIRECT_AWARD_SCOPE]
    if not direct:
        return []
    treatment = {r.start.year: r for r in direct}
    offsets = [(r.start - timedelta(days=1) - date(r.start.year, 1, 1)).days for r in direct]
    if sum(offsets) % len(offsets):
        raise CatalogError("Las ventanas de tratamiento no tienen un punto medio de día entero.")
    control_offset = sum(offsets) // len(offsets)
    # Los días se cuentan desde el 1 de enero de un año no bisiesto, para que el día y mes del
    # punto medio sea el mismo en todos los años de control.
    end_offsets = [
        (date(_COMMON_YEAR, r.end.month, r.end.day) - date(_COMMON_YEAR, 1, 1)).days for r in direct
    ]
    if sum(end_offsets) % len(end_offsets):
        raise CatalogError("Los fines de restricción no tienen un punto medio de día entero.")
    reference_day = date(_COMMON_YEAR, 1, 1) + timedelta(days=sum(end_offsets) // len(end_offsets))

    windows: list[ComparisonWindow] = []
    for year in range(min(treatment), min(max(treatment), cutoff_date.year) + 1):
        restriction = treatment.get(year)
        if restriction:
            role = "treatment"
            window_end = restriction.start - timedelta(days=1)
        else:
            role = "control"
            window_end = date(year, 1, 1) + timedelta(days=control_offset)
        windows.append(
            ComparisonWindow(
                year=year,
                role=role,
                window_start=date(year, 1, 1),
                window_end=window_end,
                denominator_end=_same_day(year, cutoff_date),
                restriction_end=restriction.end if restriction else None,
                reference_restriction_end=(
                    restriction.end
                    if restriction
                    else date(year, reference_day.month, reference_day.day)
                ),
            )
        )
    return windows


def _same_day(year: int, cutoff_date: date) -> date:
    try:
        return date(year, cutoff_date.month, cutoff_date.day)
    except ValueError:  # 29 de febrero en un año no bisiesto
        return date(year, cutoff_date.month, cutoff_date.day - 1)
