"""Calidad de datos publicada: conciliación SECOP–MEData por mes (R15; ADR 0031, ADR 0038)."""

import duckdb

from veeduria.link.reconciliation import RECONCILIATION_THRESHOLD
from veeduria.publish.models import Quality, Reconciliation, ReconciliationMonth

QUERY = """
SELECT
    strftime(month, '%Y-%m'),
    secop_count,
    medata_count,
    shared_count,
    union_count,
    shared_share::DOUBLE,
    secop_coverage::DOUBLE,
    medata_coverage::DOUBLE,
    below_threshold
FROM reconciliation
ORDER BY month
"""


def build_quality(connection: duckdb.DuckDBPyConnection) -> Quality:
    """Lee la tabla `reconciliation` que deja `build()`; no recalcula nada."""
    months = [
        ReconciliationMonth(
            period=period,
            secop_count=secop_count,
            medata_count=medata_count,
            shared_count=shared_count,
            union_count=union_count,
            shared_share=shared_share,
            secop_coverage=secop_coverage,
            medata_coverage=medata_coverage,
            below_threshold=below_threshold,
        )
        for (
            period,
            secop_count,
            medata_count,
            shared_count,
            union_count,
            shared_share,
            secop_coverage,
            medata_coverage,
            below_threshold,
        ) in connection.execute(QUERY).fetchall()
    ]
    return Quality(
        reconciliation=Reconciliation(threshold=float(RECONCILIATION_THRESHOLD), months=months)
    )
