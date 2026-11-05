"""Calidad de datos publicada: conciliación R15 y reportes de R4, R6 y R8 (ADR 0038, ADR 0042)."""

import duckdb

from veeduria.link.reconciliation import RECONCILIATION_THRESHOLD
from veeduria.normalize.catalogs import UNASSIGNED_CODE
from veeduria.publish.models import (
    Quality,
    QualityShare,
    Reconciliation,
    ReconciliationMonth,
    TruncatedRows,
    UnassignedShare,
    UnassignedYear,
    UnrecognizedValue,
)

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
UNASSIGNED_YEARS_QUERY = """
SELECT
    year(signed_date)::VARCHAR,
    count(*) FILTER (WHERE department_source = $unassigned),
    count(*)
FROM linked_contracts
GROUP BY 1
ORDER BY 1
"""
UNRECOGNIZED_QUERY = """
SELECT catalog, source, raw_text, row_count
FROM unrecognized_values
ORDER BY catalog, source, raw_text
"""
SHARE_DIGITS = 4


def _share(count: int, total: int) -> QualityShare:
    ratio = round(count / total, SHARE_DIGITS) if total else None
    return QualityShare(count=count, total=total, share=ratio)


def _count_where(
    connection: duckdb.DuckDBPyConnection,
    table: str,
    condition: str,
    parameters: dict[str, str] | None = None,
) -> QualityShare:
    """Cuántas filas de `table` cumplen `condition`; tabla y condición son constantes del módulo."""
    count, total = connection.execute(
        f"SELECT count(*) FILTER (WHERE {condition}), count(*) FROM {table}", parameters
    ).fetchone() or (0, 0)
    return _share(count, total)


def build_quality(connection: duckdb.DuckDBPyConnection) -> Quality:
    """Lee las tablas que deja `build()`; no recalcula ninguna regla."""
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
    unassigned_years = [
        UnassignedYear(period=period, unassigned=_share(count, total))
        for period, count, total in connection.execute(
            UNASSIGNED_YEARS_QUERY, {"unassigned": UNASSIGNED_CODE}
        ).fetchall()
        if period is not None
    ]
    (unsigned,) = connection.execute(
        "SELECT count(*) FROM quality_issues WHERE rule = 'R4'"
    ).fetchone() or (0,)
    (records,) = connection.execute("SELECT count(*) FROM contracts").fetchone() or (0,)
    return Quality(
        reconciliation=Reconciliation(threshold=float(RECONCILIATION_THRESHOLD), months=months),
        unassigned_share=UnassignedShare(
            district=_count_where(
                connection,
                "linked_contracts",
                "department_source = $unassigned",
                {"unassigned": UNASSIGNED_CODE},
            ),
            years=unassigned_years,
        ),
        truncated_rows=TruncatedRows(
            rows=_count_where(connection, "contract_execution", "truncated"),
            contracts=_count_where(connection, "medata_contracts", "truncated"),
        ),
        unsigned_records=_share(unsigned, records),
        unrecognized_values=[
            UnrecognizedValue(catalog=catalog, source=source, raw_text=raw_text, row_count=count)
            for catalog, source, raw_text, count in connection.execute(
                UNRECOGNIZED_QUERY
            ).fetchall()
        ],
    )
