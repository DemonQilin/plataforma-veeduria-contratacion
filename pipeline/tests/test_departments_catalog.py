"""Catálogo de secretarías (R8): un código por secretaría para los dos vocabularios."""

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.normalize.catalogs import (
    CatalogError,
    classify_department,
    load_departments,
)
from veeduria.normalize.contract_execution import normalize_contract_execution
from veeduria.normalize.procurement_processes import normalize_procurement_processes

SNAPSHOT = REPO_ROOT / "data" / "snapshot"

# (texto de MEData, texto de SECOP II, código común)
SAME_DEPARTMENT = [
    ("Suministros y Serv", "SECRETARÍA SUMINISTROS Y SERVICIOS", "supplies_and_services"),
    ("Suministros y Serv", "SUMINISTROS Y SERVICIOS", "supplies_and_services"),
    ("Educación", "Secretaria Educación", "education"),
    ("Hacienda", "Secretaría de Hacienda", "treasury"),
    ("Medio Ambiente", "MEDIO AMBIENTE", "environment"),
    ("DAGRED", "DAGRD", "disaster_management"),
    ("Gcia Centro", "Gerencia del Centro", "downtown_management"),
    ("Alcaldía", "Secretaria Privada", "private_office"),
    ("Seguridad", "Secretaría de Seguridad y Convivencia", "security"),
]


@pytest.mark.parametrize(("medata", "secop", "code"), SAME_DEPARTMENT)
def test_r08_both_vocabularies_map_to_one_code(medata: str, secop: str, code: str) -> None:
    left, right = classify_department(medata), classify_department(secop)
    assert left is not None
    assert right is not None
    assert (left.code, right.code) == (code, code)


def test_r08_comparison_ignores_case_accents_and_spaces() -> None:
    entry = classify_department("  secretaria   EDUCACION ")
    assert entry is not None
    assert entry.code == "education"


@pytest.mark.parametrize("raw", [None, "", "   ", "Texto que no es una secretaría"])
def test_r08_unknown_or_empty_text_is_unmapped(raw: str | None) -> None:
    assert classify_department(raw) is None


def test_r08_repeated_raw_text_is_rejected(tmp_path) -> None:
    path = tmp_path / "departments.toml"
    path.write_text(
        '[[type]]\ncode = "a"\nlabel = "A"\nraw = ["Salud"]\n'
        '[[type]]\ncode = "b"\nlabel = "B"\nraw = ["SALUD"]\n'
        '[[type]]\ncode = "unassigned"\nlabel = "Sin asignar"\nraw = []\n',
        encoding="utf-8",
    )
    with pytest.raises(CatalogError):
        load_departments(path)


def test_r08_catalog_without_unassigned_is_rejected(tmp_path) -> None:
    path = tmp_path / "departments.toml"
    path.write_text('[[type]]\ncode = "a"\nlabel = "A"\nraw = ["Salud"]\n', encoding="utf-8")
    with pytest.raises(CatalogError):
        load_departments(path)


def test_r08_snapshot_maps_every_department_text_except_one_process_row() -> None:
    connection = duckdb.connect()
    normalize_contract_execution(connection, SNAPSHOT / "medata_contract_execution.csv")
    normalize_procurement_processes(connection, SNAPSHOT / "secop_procurement_processes.csv")
    texts = connection.execute(
        "SELECT department FROM contract_execution WHERE department IS NOT NULL"
        " UNION SELECT department FROM procurement_processes WHERE department IS NOT NULL"
    ).fetchall()
    unmapped = sorted(text for (text,) in texts if classify_department(text) is None)
    assert unmapped == ["SUMINISTRO DE VESTIDO Y CALZADO DE LABOR"]
