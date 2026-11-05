"""Publicación de la serie mensual: supresión R13 del valor (D4, D6; ADR 0040)."""

from collections import defaultdict
from collections.abc import Callable, Hashable

from veeduria.publish.models import MonthlySeries, MonthlySeriesRow
from veeduria.publish.suppression import SUPPRESSION_THRESHOLD


def _sort_key(row: MonthlySeriesRow) -> tuple[str, str, str]:
    return (row.period, row.procurement_method or "", row.contract_type or "")


def _suppress(row: MonthlySeriesRow) -> MonthlySeriesRow:
    # R13: conserva el conteo y `value_sample_size`, y oculta el valor.
    return row.model_copy(update={"value": None, "is_suppressed": True})


def _types_of_a_method(row: MonthlySeriesRow) -> Hashable | None:
    # Los tipos de una modalidad y mes suman el valor de esa modalidad.
    if row.procurement_method is None or row.contract_type is None:
        return None
    return ("types", row.period, row.procurement_method)


def _methods_of_a_type(row: MonthlySeriesRow) -> Hashable | None:
    # Las modalidades de un tipo y mes suman el valor de ese tipo.
    if row.procurement_method is None or row.contract_type is None:
        return None
    return ("methods", row.period, row.contract_type)


def _methods_of_a_month(row: MonthlySeriesRow) -> Hashable | None:
    # Las modalidades de un mes suman el valor del mes.
    if row.procurement_method is None or row.contract_type is not None:
        return None
    return ("month-methods", row.period)


def _types_of_a_month(row: MonthlySeriesRow) -> Hashable | None:
    # Los tipos de un mes suman el valor del mes.
    if row.procurement_method is not None or row.contract_type is None:
        return None
    return ("month-types", row.period)


def _months_of_a_year(row: MonthlySeriesRow) -> Hashable:
    # Los meses de un año suman la cifra anual, que I1 ya publica para la contratación directa.
    return ("months", row.period[:4], row.procurement_method, row.contract_type)


BREAKDOWNS: tuple[Callable[[MonthlySeriesRow], Hashable | None], ...] = (
    _types_of_a_method,
    _methods_of_a_type,
    _methods_of_a_month,
    _types_of_a_month,
    _months_of_a_year,
)


def suppress_series_values(rows: list[MonthlySeriesRow]) -> list[MonthlySeriesRow]:
    """Aplica R13 al valor y devuelve las filas ordenadas. El conteo nunca se suprime.

    Primaria: el valor respaldado por entre 1 y 4 contratos con valor se suprime. Con cero
    contratos con valor el valor es cero y no hay nada que despejar. Complementaria (D6): si un
    desglose queda con un solo valor suprimido, se suprime también el publicado de menor
    `value_sample_size` que tenga contratos. Se repite hasta que ningún desglose cambie.
    """
    result = sorted(
        (
            _suppress(row) if 0 < row.value_sample_size < SUPPRESSION_THRESHOLD else row
            for row in rows
        ),
        key=_sort_key,
    )
    changed = True
    while changed:
        changed = False
        for breakdown in BREAKDOWNS:
            groups: dict[Hashable, list[int]] = defaultdict(list)
            for index, row in enumerate(result):
                key = breakdown(row)
                if key is not None:
                    groups[key].append(index)
            for indexes in groups.values():
                if sum(result[i].is_suppressed for i in indexes) != 1:
                    continue
                candidates = [
                    i
                    for i in indexes
                    if not result[i].is_suppressed and result[i].value_sample_size
                ]
                if not candidates:
                    continue
                # El orden de `result` desempata por mes, modalidad y tipo.
                smallest = min(candidates, key=lambda i: (result[i].value_sample_size, i))
                result[smallest] = _suppress(result[smallest])
                changed = True
    return result


def publish_monthly_series(rows: list[MonthlySeriesRow]) -> MonthlySeries:
    """R13: el tablero nunca recibe un valor mensual pequeño sin suprimir."""
    return MonthlySeries(rows=suppress_series_values(rows))
