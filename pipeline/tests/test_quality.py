"""Calidad de datos publicada: conciliación SECOP–MEData por mes (R15; ADR 0038)."""

import json
from typing import Any

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from tests.paths import REPO_ROOT
from veeduria.cli import app
from veeduria.publish.models import CONTRACT_MODELS, Quality, ReconciliationMonth

runner = CliRunner()
BELOW_THRESHOLD = [
    "2022-03",
    "2022-04",
    "2022-05",
    "2022-06",
    "2022-07",
    "2022-12",
]


def month(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "period": "2022-01",
        "secop_count": 726,
        "medata_count": 725,
        "shared_count": 661,
        "union_count": 790,
        "shared_share": 0.8367,
        "secop_coverage": 0.9105,
        "medata_coverage": 0.9117,
        "below_threshold": False,
    }
    row.update(overrides)
    return row


@pytest.fixture(scope="module")
def quality(tmp_path_factory: pytest.TempPathFactory) -> Quality:
    output_dir = tmp_path_factory.mktemp("quality") / "out"
    result = runner.invoke(app, ["run", "--from-snapshot", "--output-dir", str(output_dir)])
    assert result.exit_code == 0, result.output
    payload = json.loads((output_dir / "quality.json").read_text(encoding="utf-8"))
    return Quality.model_validate(payload)


def test_r15_quality_is_part_of_the_contract() -> None:
    assert CONTRACT_MODELS["quality"] is Quality


def test_r15_quality_publishes_the_18_months_and_the_threshold(quality: Quality) -> None:
    months = quality.reconciliation.months
    assert quality.reconciliation.threshold == 0.8
    assert (len(months), months[0].period, months[-1].period) == (18, "2022-01", "2023-06")
    assert [item.period for item in months] == sorted(item.period for item in months)


def test_r15_quality_flags_the_6_months_below_80_percent(quality: Quality) -> None:
    flagged = [item.period for item in quality.reconciliation.months if item.below_threshold]
    assert flagged == BELOW_THRESHOLD


def test_r15_quality_january_2022_keeps_the_counts_of_adr_0031(quality: Quality) -> None:
    january = quality.reconciliation.months[0]
    assert (
        january.secop_count,
        january.medata_count,
        january.shared_count,
        january.union_count,
    ) == (726, 725, 661, 790)
    assert january.shared_share == 0.8367


def test_r15_quality_march_2022_is_the_lowest_month(quality: Quality) -> None:
    march = next(item for item in quality.reconciliation.months if item.period == "2022-03")
    assert (march.shared_count, march.union_count, march.shared_share) == (5, 20, 0.25)


def test_adr_0038_no_month_has_fewer_than_5_contracts(quality: Quality) -> None:
    """ADR 0038 publica los conteos sin supresión. Si esto falla, hay que revisar esa decisión."""
    smallest = min(
        min(item.secop_count, item.medata_count, item.shared_count)
        for item in quality.reconciliation.months
    )
    assert smallest >= 5


def test_r15_month_accepts_a_coherent_row() -> None:
    assert ReconciliationMonth.model_validate(month()).union_count == 790


def test_r15_month_rejects_an_incoherent_union() -> None:
    with pytest.raises(ValidationError, match="unión"):
        ReconciliationMonth.model_validate(month(union_count=800))


def test_r15_month_rejects_a_period_that_is_not_a_month() -> None:
    with pytest.raises(ValidationError):
        ReconciliationMonth.model_validate(month(period="2022"))


def test_r15_month_without_contracts_has_no_share() -> None:
    empty = month(
        secop_count=0,
        medata_count=0,
        shared_count=0,
        union_count=0,
        shared_share=None,
        secop_coverage=None,
        medata_coverage=None,
    )
    assert ReconciliationMonth.model_validate(empty).shared_share is None
    with pytest.raises(ValidationError, match="razón"):
        ReconciliationMonth.model_validate({**empty, "shared_share": 0.5})


def test_r15_quality_json_in_outputs_matches_a_fresh_run(quality: Quality) -> None:
    published = (REPO_ROOT / "data" / "outputs" / "quality.json").read_text(encoding="utf-8")
    assert Quality.model_validate(json.loads(published)) == quality
