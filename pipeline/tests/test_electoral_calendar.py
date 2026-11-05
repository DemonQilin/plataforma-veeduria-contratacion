"""Calendario electoral (R10) y ventanas de comparación (R11, R12) de I2."""

from datetime import date

import pytest

from veeduria.indicators.electoral_calendar import (
    comparison_windows,
    load_electoral_calendar,
)
from veeduria.normalize.catalogs import CatalogError

CUTOFF = date(2026, 10, 30)


def _write(tmp_path, body: str):
    path = tmp_path / "electoral_calendar.toml"
    path.write_text(body, encoding="utf-8")
    return path


def _restriction(
    cycle="presidential_2022",
    scope="direct_award",
    start="2022-01-29",
    end="2022-06-19",
    sources='["Ley 996 de 2005"]',
):
    return (
        f'[[restriction]]\ncycle = "{cycle}"\nscope = "{scope}"\n'
        f"start = {start}\nend = {end}\nsources = {sources}\n"
    )


def _windows(cutoff: date = CUTOFF):
    return {w.year: w for w in comparison_windows(load_electoral_calendar(), cutoff)}


def test_r10_calendar_dates_match_fuentes() -> None:
    calendar = {r.cycle: r for r in load_electoral_calendar()}
    assert (calendar["presidential_2022"].start, calendar["presidential_2022"].end) == (
        date(2022, 1, 29),
        date(2022, 6, 19),
    )
    assert (calendar["presidential_2026"].start, calendar["presidential_2026"].end) == (
        date(2026, 1, 31),
        date(2026, 6, 21),
    )
    assert (calendar["congress_2026"].start, calendar["congress_2026"].end) == (
        date(2025, 11, 8),
        date(2026, 3, 8),
    )
    assert calendar["presidential_2022"].scope == "direct_award"
    assert calendar["congress_2026"].scope == "interadministrative"


def test_r10_every_restriction_cites_a_source() -> None:
    assert all(r.sources for r in load_electoral_calendar())


@pytest.mark.parametrize(
    "body",
    [
        _restriction(sources="[]"),
        _restriction(start="2022-06-19", end="2022-01-29"),
        _restriction(scope="other"),
        _restriction() + _restriction(),
    ],
    ids=["without_source", "start_after_end", "unknown_scope", "duplicated_cycle"],
)
def test_r10_malformed_calendar_is_rejected(tmp_path, body: str) -> None:
    with pytest.raises(CatalogError):
        load_electoral_calendar(_write(tmp_path, body))


def test_i2_r11_window_2022_ends_jan_28() -> None:
    window = _windows()[2022]
    assert (window.role, window.window_start, window.window_end) == (
        "treatment",
        date(2022, 1, 1),
        date(2022, 1, 28),
    )


def test_i2_r11_window_2026_ends_jan_30() -> None:
    window = _windows()[2026]
    assert (window.role, window.window_start, window.window_end) == (
        "treatment",
        date(2026, 1, 1),
        date(2026, 1, 30),
    )


def test_i2_r11_control_years_2023_to_2025_end_jan_29() -> None:
    windows = _windows()
    assert sorted(windows) == [2022, 2023, 2024, 2025, 2026]
    for year in (2023, 2024, 2025):
        assert windows[year].role == "control"
        assert windows[year].window_start == date(year, 1, 1)
        assert windows[year].window_end == date(year, 1, 29)


def test_i2_r11_restriction_end_of_presidential_years() -> None:
    windows = _windows()
    assert windows[2022].restriction_end == date(2022, 6, 19)
    assert windows[2026].restriction_end == date(2026, 6, 21)
    assert all(windows[year].restriction_end is None for year in (2023, 2024, 2025))


def test_i2_r11_interadministrative_restriction_does_not_create_a_window() -> None:
    # La restricción del Congreso de 2026 no cubre la contratación directa.
    assert len(comparison_windows(load_electoral_calendar(), CUTOFF)) == 5


def test_r12_denominator_ends_at_cutoff_day_every_year() -> None:
    windows = _windows()
    for year, window in windows.items():
        assert window.denominator_end == date(year, 10, 30)


def test_r12_leap_day_cutoff_falls_back_to_feb_28() -> None:
    windows = _windows(date(2028, 2, 29))
    assert windows[2023].denominator_end == date(2023, 2, 28)
    assert windows[2026].denominator_end == date(2026, 2, 28)


def test_r11_years_after_the_cutoff_are_excluded() -> None:
    assert sorted(_windows(date(2025, 10, 30))) == [2022, 2023, 2024, 2025]
