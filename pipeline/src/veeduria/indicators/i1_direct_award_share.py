"""I1 · Proporción de contratación directa (R6, R7, R8, D1, D2)."""

from pathlib import Path

import duckdb

from veeduria.indicators.i2_pre_restriction_share import RATIO_DIGITS
from veeduria.publish.models import IndicatorCell

SQL_PATH = Path(__file__).with_name("i1_direct_award_share.sql")


def build_direct_award_share(connection: duckdb.DuckDBPyConnection) -> list[IndicatorCell]:
    """Celdas de I1 del Distrito y de cada secretaría, por año, variante y medida.

    El denominador son todos los contratos firmados en el año; el numerador, los de contratación
    directa (variante `None`, D1) o los de contratación directa más régimen especial
    (`non_competitive`, D2). La medida por valor suma el valor inicial (D3) y excluye el crédito
    público y los contratos sin valor (R7). Cada secretaría de R8, incluida «sin asignar», tiene
    su celda, así que suman al Distrito. Se publica cada año de la copia; el de la fecha de corte
    queda parcial (ADR 0039). Una medida sin denominador no publica celda. La supresión R13 la
    aplica `publish_indicators`.
    """
    rows = connection.execute(SQL_PATH.read_text(encoding="utf-8")).fetchall()
    cells: list[IndicatorCell] = []
    for (
        year,
        level,
        department,
        variant,
        count_num,
        count_den,
        value_num,
        value_den,
        value_sample,
    ) in rows:
        measures = (
            ("count", count_num, count_den, count_den),
            ("value", value_num, value_den, value_sample),
        )
        for measure, numerator, denominator, sample_size in measures:
            if not denominator:
                continue
            cells.append(
                IndicatorCell(
                    indicator="I1",
                    variant=variant,
                    measure=measure,
                    level=level,
                    department=department,
                    period=str(year),
                    sample_size=sample_size,
                    numerator=float(numerator),
                    denominator=float(denominator),
                    ratio=round(float(numerator) / float(denominator), RATIO_DIGITS),
                    is_suppressed=False,
                )
            )
    return cells
