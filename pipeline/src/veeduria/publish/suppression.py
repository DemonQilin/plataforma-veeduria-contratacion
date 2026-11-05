"""Supresión de celdas pequeñas (R13), con umbral D4 y supresión complementaria D6."""

from collections import defaultdict
from collections.abc import Callable, Hashable

from veeduria.publish.models import IndicatorCell

# D4: un indicador desagregado calculado sobre menos de 5 contratos no se publica.
SUPPRESSION_THRESHOLD = 5


def _is_monthly(cell: IndicatorCell) -> bool:
    return len(cell.period) == len("AAAA-MM")


def _is_disaggregated(cell: IndicatorCell) -> bool:
    # R13: desagregado es por secretaría o por mes. La cifra anual del Distrito siempre se publica.
    return cell.level == "department" or _is_monthly(cell)


def _sort_key(cell: IndicatorCell) -> tuple:
    return (
        cell.indicator,
        cell.variant is not None,
        cell.variant or "",
        cell.measure,
        cell.level != "district",
        cell.department or "",
        cell.period,
    )


def _by_department(cell: IndicatorCell) -> Hashable | None:
    # Las secretarías de un mismo indicador, variante, medida y periodo suman al Distrito.
    if cell.level != "department":
        return None
    return ("department", cell.indicator, cell.variant, cell.measure, cell.period)


def _by_month(cell: IndicatorCell) -> Hashable | None:
    # Los meses de un mismo año, en el mismo nivel y secretaría, suman a la cifra anual.
    if not _is_monthly(cell):
        return None
    return (
        "month",
        cell.indicator,
        cell.variant,
        cell.measure,
        cell.level,
        cell.department,
        cell.period[:4],
    )


BREAKDOWNS: tuple[Callable[[IndicatorCell], Hashable | None], ...] = (_by_department, _by_month)


# Variantes cuyo denominador casi coincide con el numerador de otra celda (indicador, variante,
# medida): si esa celda se oculta, la variante también, o se despejaría por la variante (ADR 0044).
DEPENDENT_VARIANTS: dict[tuple[str, str | None, str], tuple[str, str | None, str]] = {
    ("I5", "near_addition_cap", "count"): ("I5", None, "count"),
}


def _suppress_dependents(result: list[IndicatorCell]) -> bool:
    hidden = {
        (cell.indicator, cell.variant, cell.measure, cell.level, cell.department, cell.period)
        for cell in result
        if cell.is_suppressed
    }
    changed = False
    for index, cell in enumerate(result):
        source = DEPENDENT_VARIANTS.get((cell.indicator, cell.variant, cell.measure))
        if source is None or cell.is_suppressed:
            continue
        if (*source, cell.level, cell.department, cell.period) in hidden:
            result[index] = _suppress(cell)
            changed = True
    return changed


def _suppress(cell: IndicatorCell) -> IndicatorCell:
    # R13: conserva `sample_size` y oculta las cifras que permitirían despejar la celda.
    return cell.model_copy(
        update={"numerator": None, "denominator": None, "ratio": None, "is_suppressed": True}
    )


def suppress_small_cells(cells: list[IndicatorCell]) -> list[IndicatorCell]:
    """Aplica R13 y devuelve las celdas ordenadas.

    Primaria: una celda desagregada con `sample_size` < `SUPPRESSION_THRESHOLD` se suprime.
    Complementaria (D6): si un desglose queda con una sola celda suprimida, se suprime
    también la publicada de menor `sample_size`, para que no se despeje restando del total.
    Se repite hasta que ningún desglose cambie, porque una celda puede estar en dos desgloses.
    """
    result = sorted(
        (
            _suppress(cell)
            if _is_disaggregated(cell) and cell.sample_size < SUPPRESSION_THRESHOLD
            else cell
            for cell in cells
        ),
        key=_sort_key,
    )
    changed = True
    while changed:
        changed = False
        for breakdown in BREAKDOWNS:
            groups: dict[Hashable, list[int]] = defaultdict(list)
            for index, cell in enumerate(result):
                key = breakdown(cell)
                if key is not None:
                    groups[key].append(index)
            for indexes in groups.values():
                if sum(result[i].is_suppressed for i in indexes) != 1:
                    continue
                candidates = [i for i in indexes if not result[i].is_suppressed]
                if not candidates:
                    continue
                # El orden de `result` desempata por secretaría y periodo.
                smallest = min(candidates, key=lambda i: (result[i].sample_size, i))
                result[smallest] = _suppress(result[smallest])
                changed = True
        if _suppress_dependents(result):
            changed = True
    return result
