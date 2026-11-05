"""I3 · Oferente único (R5, R8, R9; ADR 0043)."""

from pathlib import Path

import duckdb

from veeduria.indicators.i2_pre_restriction_share import RATIO_DIGITS
from veeduria.publish.models import IndicatorCell

SQL_PATH = Path(__file__).with_name("i3_single_bidder.sql")


def build_single_bidder(connection: duckdb.DuckDBPyConnection) -> list[IndicatorCell]:
    """Celdas de I3 del Distrito y de cada secretaría, por año de publicación del proceso.

    El denominador son los procesos competitivos adjudicados que R9 deja válidos; el numerador,
    los que tuvieron un solo oferente. Solo se mide por número de procesos. Cada secretaría de R8,
    incluida «sin asignar», tiene su celda, así que suman al Distrito. El año de la fecha de corte
    queda parcial. La supresión R13 la aplica `publish_indicators`.
    """
    rows = connection.execute(SQL_PATH.read_text(encoding="utf-8")).fetchall()
    return [
        IndicatorCell(
            indicator="I3",
            variant=None,
            measure="count",
            level=level,
            department=department,
            period=str(year),
            sample_size=denominator,
            numerator=float(numerator),
            denominator=float(denominator),
            ratio=round(float(numerator) / float(denominator), RATIO_DIGITS),
            is_suppressed=False,
        )
        for year, level, department, numerator, denominator in rows
    ]
