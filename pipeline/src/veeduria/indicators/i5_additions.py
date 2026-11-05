"""I5 · Adiciones de los contratos de MEData (R7, R8; ADR 0044)."""

from pathlib import Path

import duckdb

from veeduria.indicators.i2_pre_restriction_share import RATIO_DIGITS
from veeduria.publish.models import IndicatorCell

SQL_PATH = Path(__file__).with_name("i5_additions.sql")


def build_additions(connection: duckdb.DuckDBPyConnection) -> list[IndicatorCell]:
    """Celdas de I5 del Distrito y de cada secretaría, por año de firma, solo con MEData.

    Contratos con adición ÷ contratos de MEData con monto de adiciones informado; valor
    adicionado ÷ valor inicial de MEData, sin crédito público (R7); y la variante
    `near_addition_cap`: contratos cuya adición llega al 45 % del valor inicial ÷ contratos con
    adición, sin calificarlos. SECOP II no sirve para esto: su `valor_del_contrato` ya incluye las
    adiciones y su tipo «Adicion en el valor» las subcuenta (ADR 0044). MEData cubre contratos
    firmados del 4 de enero de 2022 al 30 de junio de 2023. Cada secretaría de R8, incluida
    «sin asignar», tiene su celda, así que suman al Distrito. Una medida sin denominador no
    publica celda. La supresión R13 la aplica `publish_indicators`.
    """
    rows = connection.execute(SQL_PATH.read_text(encoding="utf-8")).fetchall()
    cells: list[IndicatorCell] = []
    for (
        year,
        level,
        department,
        count_num,
        count_den,
        value_num,
        value_den,
        value_sample,
        cap_num,
        cap_den,
    ) in rows:
        measures = (
            (None, "count", count_num, count_den, count_den),
            (None, "value", value_num, value_den, value_sample),
            ("near_addition_cap", "count", cap_num, cap_den, cap_den),
        )
        for variant, measure, numerator, denominator, sample_size in measures:
            if not denominator:
                continue
            cells.append(
                IndicatorCell(
                    indicator="I5",
                    variant=variant,
                    measure=measure,
                    level=level,
                    department=department,
                    period=str(year),
                    sample_size=sample_size,
                    numerator=float(numerator),
                    denominator=float(denominator),
                    ratio=round(float(numerator) / float(denominator), RATIO_DIGITS),
                    is_suppressed=False,
                )
            )
    return cells
