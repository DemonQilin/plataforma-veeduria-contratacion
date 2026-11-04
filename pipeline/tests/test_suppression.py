"""R13 (supresión de celdas pequeñas), D4 (umbral de 5) y D6 (supresión complementaria)."""

from veeduria.publish.models import IndicatorCell
from veeduria.publish.suppression import SUPPRESSION_THRESHOLD, suppress_small_cells


def cell(
    sample_size: int,
    *,
    department: str | None = None,
    period: str = "2022",
    indicator: str = "I2",
) -> IndicatorCell:
    numerator = sample_size / 2
    return IndicatorCell(
        indicator=indicator,
        variant=None,
        measure="count",
        level="department" if department else "district",
        department=department,
        period=period,
        sample_size=sample_size,
        numerator=numerator,
        denominator=float(sample_size),
        ratio=0.5 if sample_size else 0.0,
        is_suppressed=False,
    )


def suppressed_keys(cells: list[IndicatorCell]) -> set[tuple[str | None, str]]:
    return {(c.department, c.period) for c in cells if c.is_suppressed}


def test_d4_threshold_is_five() -> None:
    assert SUPPRESSION_THRESHOLD == 5


def test_r13_department_cell_below_threshold_is_suppressed_and_keeps_sample_size() -> None:
    result = suppress_small_cells([cell(4, department="A"), cell(5, department="B")])

    small = next(c for c in result if c.department == "A")
    assert small.is_suppressed is True
    assert small.sample_size == 4
    assert (small.numerator, small.denominator, small.ratio) == (None, None, None)


def test_r13_cell_at_threshold_is_published() -> None:
    result = suppress_small_cells([cell(5, department="B")])

    assert result[0].is_suppressed is False
    assert result[0].numerator == 2.5


def test_r13_annual_district_cell_is_never_suppressed() -> None:
    result = suppress_small_cells([cell(3)])

    assert result[0].is_suppressed is False


def test_r13_monthly_district_cell_below_threshold_is_suppressed() -> None:
    result = suppress_small_cells([cell(3, period="2022-01"), cell(3, period="2022-02")])

    assert suppressed_keys(result) == {(None, "2022-01"), (None, "2022-02")}


def test_d6_lone_suppressed_cell_takes_the_next_smallest_with_it() -> None:
    cells = [cell(3, department="A"), cell(9, department="B"), cell(20, department="C")]

    result = suppress_small_cells(cells)

    assert suppressed_keys(result) == {("A", "2022"), ("B", "2022")}


def test_d6_two_suppressed_cells_need_no_complement() -> None:
    cells = [cell(3, department="A"), cell(4, department="B"), cell(9, department="C")]

    result = suppress_small_cells(cells)

    assert suppressed_keys(result) == {("A", "2022"), ("B", "2022")}


def test_d6_ties_break_by_department_name() -> None:
    cells = [cell(3, department="A"), cell(9, department="C"), cell(9, department="B")]

    result = suppress_small_cells(cells)

    assert suppressed_keys(result) == {("A", "2022"), ("B", "2022")}


def test_d6_breakdowns_are_separate_per_indicator_and_period() -> None:
    cells = [
        cell(3, department="A"),
        cell(9, department="B"),
        cell(9, department="A", indicator="I8"),
        cell(9, department="B", indicator="I8"),
        cell(9, department="A", period="2023"),
        cell(9, department="B", period="2023"),
    ]

    result = suppress_small_cells(cells)

    assert sum(c.is_suppressed for c in result) == 2
    assert all(c.indicator == "I2" and c.period == "2022" for c in result if c.is_suppressed)


def test_d6_complement_cascades_across_department_and_month_breakdowns() -> None:
    # Solo A en enero es pequeña. Su complemento por secretarías es B en enero, que queda
    # sola entre los meses de B y arrastra a B en febrero; A en enero arrastra a A en febrero.
    cells = [
        cell(3, department="A", period="2022-01"),
        cell(50, department="A", period="2022-02"),
        cell(6, department="B", period="2022-01"),
        cell(40, department="B", period="2022-02"),
        cell(50, department="C", period="2022-01"),
        cell(50, department="C", period="2022-02"),
    ]

    result = suppress_small_cells(cells)

    assert suppressed_keys(result) == {
        ("A", "2022-01"),
        ("A", "2022-02"),
        ("B", "2022-01"),
        ("B", "2022-02"),
    }
    # Febrero tenía dos suprimidas (A y B), así que C queda publicada.
    assert all(not c.is_suppressed for c in result if c.department == "C")


def test_r13_output_is_deterministic_and_sorted() -> None:
    cells = [cell(20, department="C"), cell(3, department="A"), cell(9, department="B"), cell(7)]

    forward = suppress_small_cells(cells)
    backward = suppress_small_cells(list(reversed(cells)))

    assert forward == backward
    assert [c.department for c in forward] == [None, "A", "B", "C"]


def test_d6_breakdowns_are_separate_per_variant_and_measure() -> None:
    base = [cell(3, department="A"), cell(9, department="B"), cell(20, department="C")]
    by_value = [c.model_copy(update={"measure": "value"}) for c in base]
    by_variant = [c.model_copy(update={"variant": "non_competitive"}) for c in base]

    result = suppress_small_cells(base + by_value + by_variant)

    for variant, measure in ((None, "count"), (None, "value"), ("non_competitive", "count")):
        group = [c for c in result if c.variant == variant and c.measure == measure]
        assert suppressed_keys(group) == {("A", "2022"), ("B", "2022")}
