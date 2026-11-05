"""Serie mensual de contratos y valor por modalidad y tipo (R7, R12, D3; ADR 0040)."""

from datetime import date
from pathlib import Path

import duckdb

from veeduria.publish.models import MonthlySeriesRow

SQL_PATH = Path(__file__).with_name("monthly_series.sql")


def build_monthly_series(
    connection: duckdb.DuckDBPyConnection, cutoff_date: date
) -> list[MonthlySeriesRow]:
    """Filas del Distrito por mes, modalidad y tipo, sobre `linked_contracts`, sin suprimir.

    Una modalidad o un tipo vacíos son el total de esa dimensión. El conteo incluye todos los
    contratos firmados del mes; el valor suma el valor inicial (D3) de los que cuentan en los
    indicadores de valor, sin el crédito público (R7). La serie va del primer mes con firma al
    mes de la fecha de corte (R12) y publica los meses vacíos como cero. La supresión R13 del
    valor la aplica `publish_monthly_series`.
    """
    rows = connection.execute(
        SQL_PATH.read_text(encoding="utf-8"), {"cutoff_date": cutoff_date}
    ).fetchall()
    return [
        MonthlySeriesRow(
            period=period,
            procurement_method=method,
            contract_type=contract_type,
            contract_count=contract_count,
            value_sample_size=value_sample_size,
            value=value,
            is_suppressed=False,
        )
        for period, method, contract_type, contract_count, value_sample_size, value in rows
    ]
