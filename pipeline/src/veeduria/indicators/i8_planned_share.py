"""I8 · Serie de planeación de la contratación directa (R17)."""

from pathlib import Path

import duckdb

from veeduria.indicators.i2_pre_restriction_share import RATIO_DIGITS
from veeduria.publish.models import IndicatorCell

SQL_PATH = Path(__file__).with_name("i8_planned_share.sql")


def build_planned_share(connection: duckdb.DuckDBPyConnection) -> list[IndicatorCell]:
    """Celdas de I8 del Distrito por año, variante y medida, sobre `procurement_plan`.

    El denominador son las líneas directas del año con mes estimado de inicio; el numerador, las
    que empiezan en enero (`planned_january`) o de febrero a junio (`planned_february_june`). La
    medida por valor suma el valor estimado de las líneas que lo tienen; el plan no distingue el
    crédito público, así que R7 no se puede aplicar. Un año sin denominador no publica celda.
    """
    rows = connection.execute(SQL_PATH.read_text(encoding="utf-8")).fetchall()
    cells: list[IndicatorCell] = []
    for year, variant, count_num, count_den, value_num, value_den, value_sample in rows:
        measures = (
            ("count", count_num, count_den, count_den),
            ("value", value_num, value_den, value_sample),
        )
        for measure, numerator, denominator, sample_size in measures:
            if not denominator:
                continue
            cells.append(
                IndicatorCell(
                    indicator="I8",
                    variant=variant,
                    measure=measure,
                    level="district",
                    department=None,
                    period=str(year),
                    sample_size=sample_size,
                    numerator=float(numerator),
                    denominator=float(denominator),
                    ratio=round(float(numerator) / float(denominator), RATIO_DIGITS),
                    is_suppressed=False,
                )
            )
    return cells
