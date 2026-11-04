"""Publicación de indicadores: aplica la supresión R13 antes de escribir (D4, D6)."""

from veeduria.publish.models import IndicatorCell, Indicators
from veeduria.publish.suppression import suppress_small_cells


def publish_indicators(cells: list[IndicatorCell]) -> Indicators:
    """R13: el tablero nunca recibe una celda desagregada pequeña sin suprimir."""
    return Indicators(cells=suppress_small_cells(cells))
