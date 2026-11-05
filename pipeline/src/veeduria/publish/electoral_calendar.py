"""Calendario electoral publicado: restricciones y ventanas de I2 (R10, R11, R12; ADR 0041)."""

from datetime import date
from typing import Literal

from veeduria.indicators.electoral_calendar import ComparisonWindow, Restriction
from veeduria.publish.models import ComparisonYear, ElectoralCalendar, ElectoralRestriction


def _status(restriction: Restriction, cutoff_date: date) -> Literal["ended", "ongoing", "upcoming"]:
    # R12: el estado sale de la fecha de corte, nunca del reloj. Los extremos son inclusivos: el día
    # de la elección sigue restringido.
    if restriction.end < cutoff_date:
        return "ended"
    if restriction.start > cutoff_date:
        return "upcoming"
    return "ongoing"


def publish_electoral_calendar(
    calendar: tuple[Restriction, ...], windows: list[ComparisonWindow], cutoff_date: date
) -> ElectoralCalendar:
    """Son fechas públicas con su fuente, no cifras de contratos: R13 no aplica (ADR 0041)."""
    return ElectoralCalendar(
        restrictions=[
            ElectoralRestriction(
                cycle=item.cycle,
                scope=item.scope,  # el cargador ya validó el alcance
                start=item.start,
                end=item.end,
                status=_status(item, cutoff_date),
                sources=list(item.sources),
            )
            for item in sorted(calendar, key=lambda item: (item.start, item.cycle))
        ],
        comparison_windows=[
            ComparisonYear(
                year=item.year,
                role=item.role,
                window_start=item.window_start,
                window_end=item.window_end,
                denominator_end=item.denominator_end,
                reference_restriction_end=item.reference_restriction_end,
            )
            for item in sorted(windows, key=lambda item: item.year)
        ],
    )
