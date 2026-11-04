"""Indicadores I1 a I8."""

import duckdb

from veeduria.publish.models import IndicatorCell


def build_indicators(connection: duckdb.DuckDBPyConnection) -> list[IndicatorCell]:
    """Celdas de indicador (R16) calculadas sobre las tablas del pipeline.

    Aún no hay indicadores implementados: I2 e I8 se agregan aquí y `run` ya los publica con la
    supresión R13 aplicada.
    """
    return []
