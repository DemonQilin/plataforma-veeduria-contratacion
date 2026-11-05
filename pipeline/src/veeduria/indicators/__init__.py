"""Indicadores I1 a I8."""

from datetime import date

import duckdb

from veeduria.indicators.electoral_calendar import comparison_windows, load_electoral_calendar
from veeduria.indicators.i1_direct_award_share import build_direct_award_share
from veeduria.indicators.i2_pre_restriction_share import build_pre_restriction_share
from veeduria.indicators.i2_restriction_span import build_restriction_span
from veeduria.indicators.i3_single_bidder import build_single_bidder
from veeduria.indicators.i4_supplier_concentration import build_supplier_concentration
from veeduria.indicators.i5_additions import build_additions
from veeduria.indicators.i8_planned_share import build_planned_share
from veeduria.indicators.i8_signed_share import build_signed_share
from veeduria.publish.models import IndicatorCell


def build_indicators(
    connection: duckdb.DuckDBPyConnection, cutoff_date: date
) -> list[IndicatorCell]:
    """Celdas de indicador (R16) calculadas sobre las tablas del pipeline.

    Por ahora I1 (contratación directa por año y secretaría), I2 (concentración
    pre-restricción y duración de los contratos de enero), I3 (oferente único por año y
    secretaría), I4 (concentración agregada de proveedores), I5 (adiciones de MEData por año y
    secretaría) e I8 (planeado y firmado). Las
    ventanas de I2 salen del calendario electoral hasta la fecha de corte (R12).
    `publish_indicators` aplica la supresión R13 y ordena las celdas.
    """
    windows = comparison_windows(load_electoral_calendar(), cutoff_date)
    return [
        *build_direct_award_share(connection),
        *build_single_bidder(connection),
        *build_supplier_concentration(connection),
        *build_additions(connection),
        *build_pre_restriction_share(connection, windows),
        *build_restriction_span(connection, windows),
        *build_planned_share(connection),
        *build_signed_share(connection),
    ]
