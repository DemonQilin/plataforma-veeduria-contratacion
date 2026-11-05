"""I2 · Concentración pre-restricción de la contratación directa (R7, R11, R12)."""

from pathlib import Path

import duckdb

from veeduria.indicators.electoral_calendar import ComparisonWindow
from veeduria.publish.models import IndicatorCell

SQL_PATH = Path(__file__).with_name("i2_pre_restriction_share.sql")
RATIO_DIGITS = 6


def build_pre_restriction_share(
    connection: duckdb.DuckDBPyConnection, windows: list[ComparisonWindow]
) -> list[IndicatorCell]:
    """Celdas de I2 del Distrito por año, variante y medida, sobre `linked_contracts`.

    El numerador son los contratos directos firmados hasta el fin de la ventana (R11) y el
    denominador, los firmados hasta el día y mes de la fecha de corte (R12). La medida por valor
    suma el valor inicial (D3) y excluye el crédito público (R7). Una medida sin denominador no
    publica celda. Las variantes son el total (`None`), `service_contract`,
    `non_service_contract` y `excluding_interadministrative`, que quita los contratos
    interadministrativos del numerador y del denominador (ADR 0036).
    """
    rows = connection.execute(
        SQL_PATH.read_text(encoding="utf-8"),
        {
            "years": [window.year for window in windows],
            "window_ends": [window.window_end for window in windows],
            "denominator_ends": [window.denominator_end for window in windows],
        },
    ).fetchall()
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
                    indicator="I2",
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
