"""I8 · Lo firmado frente a lo planeado en 2022–2023 (R7, R17)."""

from pathlib import Path

import duckdb

from veeduria.indicators.i2_pre_restriction_share import RATIO_DIGITS
from veeduria.publish.models import IndicatorCell

SQL_PATH = Path(__file__).with_name("i8_signed_share.sql")

# Años con datos de plan y de ejecución a la vez (el plan se detuvo en septiembre de 2023).
COMPARISON_YEARS = (2022, 2023)


def build_signed_share(
    connection: duckdb.DuckDBPyConnection, years: tuple[int, ...] = COMPARISON_YEARS
) -> list[IndicatorCell]:
    """Celdas de I8 con la proporción firmada en enero y de febrero a junio, por año.

    Replica la definición de `build_planned_share` sobre `linked_contracts`: el denominador son
    los contratos directos firmados en el año calendario; el numerador, los de enero
    (`signed_january`) o de febrero a junio (`signed_february_june`). El valor es el inicial y
    excluye el crédito público (R7). Como el plan no tiene llave por contrato, la comparación es
    solo agregada (R17). Un año sin denominador no publica celda.
    """
    rows = connection.execute(SQL_PATH.read_text(encoding="utf-8"), {"years": list(years)})
    cells: list[IndicatorCell] = []
    for year, variant, count_num, count_den, value_num, value_den, value_sample in rows.fetchall():
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
