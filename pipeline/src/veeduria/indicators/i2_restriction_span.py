"""I2 · Factor de confusión 3: contratos de enero que terminan después de la restricción (R11)."""

from pathlib import Path

import duckdb

from veeduria.indicators.electoral_calendar import ComparisonWindow
from veeduria.publish.models import IndicatorCell

SQL_PATH = Path(__file__).with_name("i2_restriction_span.sql")
RATIO_DIGITS = 6
VARIANT = "spans_restriction"


def build_restriction_span(
    connection: duckdb.DuckDBPyConnection, windows: list[ComparisonWindow]
) -> list[IndicatorCell]:
    """Celdas del Distrito por año, sobre `linked_contracts`, solo por número de contratos.

    El denominador son los contratos directos firmados en la ventana de enero (R11) con fecha de
    fin; el numerador, los que terminan después del `reference_restriction_end` de la ventana,
    con el plazo pactado: la fecha de fin sin los días adicionados (ADR 0035). Un año sin
    denominador no publica celda.
    """
    rows = connection.execute(
        SQL_PATH.read_text(encoding="utf-8"),
        {
            "years": [window.year for window in windows],
            "window_ends": [window.window_end for window in windows],
            "reference_ends": [window.reference_restriction_end for window in windows],
        },
    ).fetchall()
    return [
        IndicatorCell(
            indicator="I2",
            variant=VARIANT,
            measure="count",
            level="district",
            department=None,
            period=str(year),
            sample_size=denominator,
            numerator=float(numerator),
            denominator=float(denominator),
            ratio=round(numerator / denominator, RATIO_DIGITS),
            is_suppressed=False,
        )
        for year, numerator, denominator in rows
        if denominator
    ]
