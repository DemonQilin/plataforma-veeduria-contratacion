"""Publicación de indicadores con la supresión R13 cableada (D4, D6, R16)."""

from veeduria.publish.indicators import publish_indicators
from veeduria.publish.models import IndicatorCell


def _department_cell(department: str, sample_size: int) -> IndicatorCell:
    return IndicatorCell(
        indicator="I2",
        variant=None,
        measure="count",
        level="department",
        department=department,
        period="2025",
        sample_size=sample_size,
        numerator=float(sample_size),
        denominator=float(sample_size),
        ratio=1.0,
        is_suppressed=False,
    )


def test_r13_publish_indicators_suppresses_small_department_cells() -> None:
    published = publish_indicators([_department_cell("Hacienda", 3), _department_cell("Salud", 40)])

    small = next(cell for cell in published.cells if cell.department == "Hacienda")
    assert small.is_suppressed
    assert small.sample_size == 3
    assert (small.numerator, small.denominator, small.ratio) == (None, None, None)


def test_publish_indicators_without_cells_is_empty() -> None:
    assert publish_indicators([]).cells == []
