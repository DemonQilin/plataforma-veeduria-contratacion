"""Calidad de datos publicada: conciliación SECOP–MEData por mes (R15; ADR 0038)."""

import json
from typing import Any

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from tests.paths import REPO_ROOT
from veeduria.cli import app
from veeduria.publish.models import CONTRACT_MODELS, Quality, QualityShare, ReconciliationMonth

runner = CliRunner()
# ADR 0047: junio y julio de 2022 dejaron de estar por debajo del 80 % al cruzar «de AAAA».
BELOW_THRESHOLD = [
    "2022-03",
    "2022-04",
    "2022-05",
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


def test_r15_quality_flags_the_4_months_below_80_percent(quality: Quality) -> None:
    flagged = [item.period for item in quality.reconciliation.months if item.below_threshold]
    assert flagged == BELOW_THRESHOLD


def test_r15_quality_january_2022_counts_the_contracts_linked_by_adr_0047(
    quality: Quality,
) -> None:
    """ADR 0031 daba 661 de 790 (83,67 %); el cruce por «de AAAA» deja 722 de 729."""
    january = quality.reconciliation.months[0]
    assert (
        january.secop_count,
        january.medata_count,
        january.shared_count,
        january.union_count,
    ) == (726, 725, 722, 729)
    assert january.shared_share == 0.9904


def test_r15_quality_march_2022_is_the_lowest_month(quality: Quality) -> None:
    march = next(item for item in quality.reconciliation.months if item.period == "2022-03")
    assert (march.shared_count, march.union_count, march.shared_share) == (10, 15, 0.6667)


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


def test_r08_quality_reports_the_unassigned_share_of_the_district(quality: Quality) -> None:
    district = quality.unassigned_share.district
    assert (district.count, district.total, district.share) == (19, 7420, 0.0026)


def test_r08_quality_unassigned_years_add_up_to_the_district(quality: Quality) -> None:
    years = quality.unassigned_share.years
    district = quality.unassigned_share.district
    assert [year.period for year in years] == ["2022", "2023", "2024", "2025", "2026"]
    assert sum(year.unassigned.count for year in years) == district.count
    assert sum(year.unassigned.total for year in years) == district.total


def test_adr_0010_quality_reports_the_truncated_medata_rows(quality: Quality) -> None:
    rows, contracts = quality.truncated_rows.rows, quality.truncated_rows.contracts
    assert (rows.count, rows.total, rows.share) == (2072, 25783, 0.0804)
    assert (contracts.count, contracts.total) == (54, 2939)


def test_r04_quality_reports_the_unsigned_records_excluded(quality: Quality) -> None:
    # La copia no trae registros sin firma: el reporte existe y dice cero sobre el total.
    unsigned = quality.unsigned_records
    assert (unsigned.count, unsigned.total, unsigned.share) == (0, 7468, 0.0)


def test_r09_quality_reports_the_processes_with_zero_bidders_excluded(quality: Quality) -> None:
    excluded = quality.single_bidder_exclusions
    assert (excluded.count, excluded.total, excluded.share) == (21, 894, 0.0235)


def test_r06_quality_reports_the_texts_the_catalogs_do_not_know(quality: Quality) -> None:
    reported = {
        (value.catalog, value.raw_text): value.row_count for value in quality.unrecognized_values
    }
    assert reported[("procurement_method", "Subasta de prueba")] == 343
    assert reported[("contract_type", "No")] == 492
    assert reported[("contract_type", "No Especificado")] == 638
    assert reported[("department", "SUMINISTRO DE VESTIDO Y CALZADO DE LABOR")] == 1
    assert sum(1 for catalog, _ in reported if catalog == "procurement_method") == 2


def test_adr_0042_quality_json_publishes_no_contract_reference() -> None:
    published = (REPO_ROOT / "data" / "outputs" / "quality.json").read_text(encoding="utf-8")
    assert "contract_reference" not in published
    assert "referencia_del_contrato" not in published


def test_adr_0042_share_accepts_a_coherent_count() -> None:
    assert QualityShare.model_validate({"count": 1, "total": 4, "share": 0.25}).count == 1


def test_adr_0042_share_rejects_a_count_above_the_total() -> None:
    with pytest.raises(ValidationError, match="conteo"):
        QualityShare.model_validate({"count": 5, "total": 4, "share": 1.25})


def test_adr_0042_share_is_missing_if_and_only_if_the_total_is_zero() -> None:
    assert QualityShare.model_validate({"count": 0, "total": 0, "share": None}).share is None
    with pytest.raises(ValidationError, match="proporción"):
        QualityShare.model_validate({"count": 0, "total": 0, "share": 0.0})
