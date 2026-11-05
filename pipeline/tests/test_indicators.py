"""Conexión de I2 e I8 en `build_indicators` (R13, R16; docs/indicadores.md §3)."""

from datetime import date
from pathlib import Path

import duckdb
import pytest

from veeduria.indicators import build_indicators
from veeduria.pipeline import build
from veeduria.publish.indicators import publish_indicators
from veeduria.publish.metadata import build_metadata

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"


@pytest.fixture(scope="module")
def real_connection() -> duckdb.DuckDBPyConnection:
    return build(SNAPSHOT_DIR)


@pytest.fixture(scope="module")
def cells(real_connection):
    cutoff = build_metadata(real_connection).cutoff_date
    return build_indicators(real_connection, cutoff)


def _find(cells, indicator, variant, measure, period):
    return next(
        c
        for c in cells
        if (c.indicator, c.variant, c.measure, c.period) == (indicator, variant, measure, period)
    )


def test_i2_golden_total_2022_by_count(cells) -> None:
    cell = _find(cells, "I2", None, "count", "2022")
    assert (cell.numerator, cell.denominator) == (723, 1240)


def test_i2_golden_excluding_interadministrative_2022_by_count(cells) -> None:
    cell = _find(cells, "I2", "excluding_interadministrative", "count", "2022")
    assert (cell.numerator, cell.denominator) == (723, 1031)


def test_i2_golden_spans_restriction_2022(cells) -> None:
    cell = _find(cells, "I2", "spans_restriction", "count", "2022")
    assert (cell.numerator, cell.denominator) == (720, 723)


def test_i8_golden_planned_january_2022(cells) -> None:
    cell = _find(cells, "I8", "planned_january", "count", "2022")
    assert (cell.numerator, cell.denominator) == (726, 1383)


def test_i8_golden_signed_january_2022(cells) -> None:
    cell = _find(cells, "I8", "signed_january", "count", "2022")
    assert (cell.numerator, cell.denominator) == (723, 1387)


def test_r16_every_cell_has_a_unique_key(cells) -> None:
    keys = [(c.indicator, c.variant, c.measure, c.level, c.department, c.period) for c in cells]
    assert len(keys) == len(set(keys))


def test_i1_golden_2022_by_count(cells) -> None:
    cell = next(
        c
        for c in cells
        if (c.indicator, c.variant, c.measure, c.level, c.period)
        == ("I1", None, "count", "district", "2022")
    )
    assert (cell.numerator, cell.denominator) == (1387, 1716)


def test_r13_published_cells_are_yearly_and_never_leak_small_figures(cells) -> None:
    published = publish_indicators(cells).cells
    assert len(published) == len(cells)
    assert all(len(c.period) == len("AAAA") for c in published)
    # La cifra anual del Distrito siempre se publica.
    assert {c.is_suppressed for c in published if c.level == "district"} == {False}
    for cell in published:
        if cell.is_suppressed:
            assert (cell.numerator, cell.denominator, cell.ratio) == (None, None, None)
        elif cell.level == "department":
            assert cell.sample_size >= 5


def test_build_indicators_covers_i1_i2_and_i8(cells) -> None:
    assert {c.indicator for c in cells} == {"I1", "I2", "I3", "I8"}


def test_build_indicators_uses_the_given_cutoff_date(real_connection) -> None:
    # R12: sin ventanas más allá del corte, el último año de I2 es el del corte.
    cells = build_indicators(real_connection, date(2024, 10, 30))
    i2_periods = {c.period for c in cells if c.indicator == "I2" and c.variant is None}
    assert max(i2_periods) == "2024"
