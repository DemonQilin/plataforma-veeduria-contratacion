"""Textos que los catálogos no reconocen (R6, R8; ADR 0042)."""

from pathlib import Path

import duckdb

from veeduria.normalize.catalogs import is_recognized
from veeduria.normalize.unrecognized_values import record_unrecognized_values

FILES = {
    "secop_contracts": ("modalidad_de_contratacion", "tipo_de_contrato", "tipodocproveedor"),
    "secop_procurement_processes": (
        "modalidad_de_contratacion",
        "tipo_de_contrato",
        "nombre_de_la_unidad_de",
    ),
    "secop_additions": ("tipo",),
    "medata_procurement_plan": ("modalidad_seleccion",),
    "medata_contract_execution": ("modalidad", "nombre_secretaria"),
}


def write_snapshot(directory: Path, rows: dict[str, list[tuple[str, ...]]]) -> None:
    for name, columns in FILES.items():
        lines = [",".join(columns)]
        lines += [",".join(f'"{value}"' for value in row) for row in rows.get(name, [])]
        (directory / f"{name}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def found(tmp_path: Path, rows: dict[str, list[tuple[str, ...]]]) -> list[tuple[str, ...]]:
    write_snapshot(tmp_path, rows)
    connection = duckdb.connect()
    record_unrecognized_values(connection, tmp_path)
    return connection.execute(
        "SELECT catalog, source, raw_text, row_count FROM unrecognized_values ORDER BY ALL"
    ).fetchall()


def test_r06_a_text_listed_under_other_is_not_reported(tmp_path: Path) -> None:
    rows = {"secop_contracts": [("Contratación directa", "Otro", "NIT")]}
    assert is_recognized("contract_type", "Otro")
    assert found(tmp_path, rows) == []


def test_r06_a_new_text_is_reported_with_its_row_count(tmp_path: Path) -> None:
    rows = {
        "secop_procurement_processes": [
            ("Subasta de prueba", "Prestación de servicios", ""),
            ("Subasta de prueba", "Prestación de servicios", ""),
            ("Contratación directa", "Prestación de servicios", ""),
        ]
    }
    assert found(tmp_path, rows) == [
        ("procurement_method", "secop_procurement_processes", "Subasta de prueba", 2)
    ]


def test_r06_the_same_text_in_two_sources_is_reported_per_source(tmp_path: Path) -> None:
    rows = {
        "secop_contracts": [("Modalidad nueva", "Otro", "NIT")],
        "medata_procurement_plan": [("Modalidad nueva",)],
    }
    assert [(catalog, source) for catalog, source, _, _ in found(tmp_path, rows)] == [
        ("procurement_method", "medata_procurement_plan"),
        ("procurement_method", "secop_contracts"),
    ]


def test_r06_empty_texts_are_not_values_to_review(tmp_path: Path) -> None:
    rows = {"secop_additions": [("",)], "medata_contract_execution": [("", "")]}
    assert found(tmp_path, rows) == []


def test_r08_an_unknown_department_text_is_reported(tmp_path: Path) -> None:
    rows = {"secop_procurement_processes": [("Contratación directa", "Otro", "Unidad inventada")]}
    assert found(tmp_path, rows) == [
        ("department", "secop_procurement_processes", "Unidad inventada", 1)
    ]


def test_r06_medata_texts_are_compared_after_repairing_the_encoding(tmp_path: Path) -> None:
    # «Contratación directa» mal codificada en origen se repara antes de compararse (ADR 0010).
    broken = "Contratación directa".encode().decode("latin-1")
    rows = {"medata_contract_execution": [(broken, "")]}
    assert found(tmp_path, rows) == []
