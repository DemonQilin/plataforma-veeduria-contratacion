"""I4 · Concentración de proveedores, solo agregada (R7, R8, R13, R14; ADR 0045)."""

from pathlib import Path

import duckdb

from veeduria.indicators.i2_pre_restriction_share import RATIO_DIGITS
from veeduria.publish.models import IndicatorCell

SQL_PATH = Path(__file__).with_name("i4_supplier_concentration.sql")
# Cuántos proveedores forman el numerador; con esos o menos en una secretaría la razón es 100 %.
TOP_SUPPLIERS = 5


def build_supplier_concentration(connection: duckdb.DuckDBPyConnection) -> list[IndicatorCell]:
    """Celdas de I4 del Distrito y de cada secretaría, por año de firma, solo por valor.

    Valor inicial (D3) de los 5 proveedores con más valor ÷ valor total a personas jurídicas
    (R14), sin crédito público ni contratos sin valor (R7). No publica ningún proveedor: sin
    respuesta de los organizadores, I4 es solo agregado (ADR 0045). Cada secretaría de R8,
    incluida «sin asignar», tiene su celda, así que suman al Distrito. Una secretaría con
    `TOP_SUPPLIERS` proveedores o menos se publica suprimida, porque su razón sería 100 % por
    construcción. La supresión R13 y D6 la aplica `publish_indicators`.
    """
    rows = connection.execute(
        SQL_PATH.read_text(encoding="utf-8"), {"top_suppliers": TOP_SUPPLIERS}
    )
    cells: list[IndicatorCell] = []
    for (
        year,
        level,
        department,
        top_value,
        total_value,
        sample_size,
        supplier_count,
    ) in rows.fetchall():
        if not total_value:
            continue
        if level == "department" and supplier_count <= TOP_SUPPLIERS:
            cells.append(
                IndicatorCell(
                    indicator="I4",
                    variant=None,
                    measure="value",
                    level=level,
                    department=department,
                    period=str(year),
                    sample_size=int(sample_size),
                    numerator=None,
                    denominator=None,
                    ratio=None,
                    is_suppressed=True,
                )
            )
            continue
        cells.append(
            IndicatorCell(
                indicator="I4",
                variant=None,
                measure="value",
                level=level,
                department=department,
                period=str(year),
                sample_size=int(sample_size),
                numerator=float(top_value),
                denominator=float(total_value),
                ratio=round(float(top_value) / float(total_value), RATIO_DIGITS),
                is_suppressed=False,
            )
        )
    return cells
