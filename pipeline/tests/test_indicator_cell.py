"""R13 (supresión de celdas pequeñas) y R16 (trazabilidad): forma de la celda de indicador."""

import json
from typing import Any

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from veeduria.cli import app
from veeduria.publish.models import CONTRACT_MODELS, IndicatorCell, Indicators

runner = CliRunner()


def published(**overrides: Any) -> dict[str, Any]:
    cell: dict[str, Any] = {
        "indicator": "I1",
        "variant": None,
        "measure": "count",
        "level": "district",
        "department": None,
        "period": "2022",
        "sample_size": 120,
        "numerator": 90.0,
        "denominator": 120.0,
        "ratio": 0.75,
        "is_suppressed": False,
    }
    cell.update(overrides)
    return cell


def suppressed(**overrides: Any) -> dict[str, Any]:
    cell = published(
        level="department",
        department="Secretaría de Salud",
        sample_size=3,
        numerator=None,
        denominator=None,
        ratio=None,
        is_suppressed=True,
    )
    cell.update(overrides)
    return cell


def test_r16_published_cell_carries_numerator_denominator_and_ratio() -> None:
    cell = IndicatorCell(**published())

    assert (cell.numerator, cell.denominator, cell.ratio) == (90.0, 120.0, 0.75)
    assert cell.sample_size == 120
    assert cell.is_suppressed is False


def test_r13_suppressed_cell_keeps_its_sample_size() -> None:
    cell = IndicatorCell(**suppressed())

    assert cell.sample_size == 3
    assert cell.is_suppressed is True


@pytest.mark.parametrize("field", ["numerator", "denominator", "ratio"])
def test_r13_suppressed_cell_rejects_a_figure(field: str) -> None:
    with pytest.raises(ValidationError):
        IndicatorCell(**suppressed(**{field: 1.0}))


@pytest.mark.parametrize("field", ["numerator", "denominator", "ratio"])
def test_r16_published_cell_requires_each_figure(field: str) -> None:
    with pytest.raises(ValidationError):
        IndicatorCell(**published(**{field: None}))


def test_department_level_requires_a_department() -> None:
    with pytest.raises(ValidationError):
        IndicatorCell(**published(level="department", department=None))


def test_district_level_rejects_a_department() -> None:
    with pytest.raises(ValidationError):
        IndicatorCell(**published(level="district", department="Secretaría de Salud"))


@pytest.mark.parametrize("period", ["2022", "2022-01"])
def test_period_accepts_year_or_month(period: str) -> None:
    assert IndicatorCell(**published(period=period)).period == period


@pytest.mark.parametrize("period", ["22", "2022-1", "2022-01-05", "enero 2022", ""])
def test_period_rejects_other_shapes(period: str) -> None:
    with pytest.raises(ValidationError):
        IndicatorCell(**published(period=period))


def test_sample_size_cannot_be_negative() -> None:
    with pytest.raises(ValidationError):
        IndicatorCell(**published(sample_size=-1))


def test_cell_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        IndicatorCell(**published(supplier_name="no debe existir"))


def test_indicators_is_a_registered_contract_model() -> None:
    assert CONTRACT_MODELS["indicators"] is Indicators
    assert Indicators(cells=[IndicatorCell(**published())]).cells[0].indicator == "I1"


def test_indicators_schema_is_exported(tmp_path) -> None:
    result = runner.invoke(app, ["export-schema", "--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    schema = json.loads((tmp_path / "indicators.json").read_bytes())
    assert schema["title"] == "Indicators"
    assert (tmp_path / "metadata.json").exists()
