"""Calendario electoral publicado: restricciones y ventanas de I2 (R10, R11, R12; ADR 0041)."""

import json
from datetime import date, timedelta

import pytest
from typer.testing import CliRunner

from tests.paths import REPO_ROOT
from veeduria.cli import app
from veeduria.indicators.electoral_calendar import comparison_windows, load_electoral_calendar
from veeduria.publish.electoral_calendar import publish_electoral_calendar
from veeduria.publish.models import CONTRACT_MODELS, ElectoralCalendar

runner = CliRunner()
CUTOFF = date(2026, 10, 30)


def _publish(cutoff: date = CUTOFF) -> ElectoralCalendar:
    calendar = load_electoral_calendar()
    return publish_electoral_calendar(calendar, comparison_windows(calendar, cutoff), cutoff)


def _status(cycle: str, cutoff: date) -> str:
    return {item.cycle: item.status for item in _publish(cutoff).restrictions}[cycle]


def test_r10_electoral_calendar_is_part_of_the_contract() -> None:
    assert CONTRACT_MODELS["electoral_calendar"] is ElectoralCalendar


def test_r10_publishes_every_restriction_by_start_with_its_sources() -> None:
    restrictions = _publish().restrictions
    assert [item.cycle for item in restrictions] == [
        "presidential_2022",
        "local_2023",
        "congress_2026",
        "presidential_2026",
        "local_2027",
    ]
    assert [item.start for item in restrictions] == sorted(item.start for item in restrictions)
    assert all(item.sources for item in restrictions)
    local_2027 = restrictions[-1]
    assert (local_2027.scope, local_2027.start, local_2027.end) == (
        "interadministrative",
        date(2027, 6, 30),
        date(2027, 10, 31),
    )


def test_r12_status_is_relative_to_the_cutoff_date() -> None:
    assert {item.cycle: item.status for item in _publish().restrictions} == {
        "presidential_2022": "ended",
        "local_2023": "ended",
        "congress_2026": "ended",
        "presidential_2026": "ended",
        "local_2027": "upcoming",
    }


@pytest.mark.parametrize(
    ("offset_days", "expected"),
    [(-1, "upcoming"), (0, "ongoing"), (1, "ongoing")],
    ids=["day_before_start", "start_day", "day_after_start"],
)
def test_r12_status_around_the_start(offset_days: int, expected: str) -> None:
    assert _status("local_2027", date(2027, 6, 30) + timedelta(days=offset_days)) == expected


@pytest.mark.parametrize(
    ("offset_days", "expected"),
    [(-1, "ongoing"), (0, "ongoing"), (1, "ended")],
    ids=["day_before_end", "end_day", "day_after_end"],
)
def test_r12_status_around_the_end_includes_the_election_day(
    offset_days: int, expected: str
) -> None:
    assert _status("local_2027", date(2027, 10, 31) + timedelta(days=offset_days)) == expected


def test_r11_windows_label_treatment_and_control_years() -> None:
    windows = _publish().comparison_windows
    assert [(item.year, item.role) for item in windows] == [
        (2022, "treatment"),
        (2023, "control"),
        (2024, "control"),
        (2025, "control"),
        (2026, "treatment"),
    ]
    by_year = {item.year: item for item in windows}
    assert by_year[2022].window_end == date(2022, 1, 28)
    assert by_year[2026].window_end == date(2026, 1, 30)
    assert all(item.denominator_end == date(item.year, 10, 30) for item in windows)


def test_r11_adding_the_2027_restriction_does_not_add_a_comparison_window() -> None:
    assert [item.year for item in _publish().comparison_windows] == [2022, 2023, 2024, 2025, 2026]


def test_r10_electoral_calendar_json_in_outputs_matches_a_fresh_run(tmp_path) -> None:
    result = runner.invoke(app, ["run", "--from-snapshot", "--output-dir", str(tmp_path / "out")])
    assert result.exit_code == 0, result.output
    fresh = (tmp_path / "out" / "electoral_calendar.json").read_bytes()
    published = (REPO_ROOT / "data" / "outputs" / "electoral_calendar.json").read_bytes()
    assert published == fresh
    assert ElectoralCalendar.model_validate(json.loads(published)) == _publish()
