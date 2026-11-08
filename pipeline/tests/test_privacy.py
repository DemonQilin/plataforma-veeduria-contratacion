"""Pruebas de privacidad (regla no negociable 1, ADR 0007).

Se escriben antes que la extracción. La función de supresión de celdas pequeñas (R13)
se prueba en `test_suppression.py`; aquí vive la guarda sobre lo que se publica en
`data/outputs/`.
"""

import csv
import json
import subprocess
from pathlib import Path

import pytest

from tests.paths import REPO_ROOT
from veeduria.extract.sources import Query, load_queries
from veeduria.publish.models import Indicators
from veeduria.publish.suppression import SUPPRESSION_THRESHOLD

SNAPSHOT_DIR = REPO_ROOT / "data" / "snapshot"
OUTPUTS_DIR = REPO_ROOT / "data" / "outputs"
QUERIES = load_queries()
EXCLUDED = {column for query in QUERIES for column in query.excluded}


SNAPSHOT_EXTRA_FILES = {"manifest.json", ".gitkeep"}
SUPPLIER_COLUMNS = {"documento_proveedor"}
NIT_FILTER = "tipodocproveedor = 'NIT'"
# Una persona natural también puede tener NIT; las personas jurídicas empiezan por 8 o 9
# (R14, ADR 0017) y tienen 9 dígitos, o 10 con el dígito de verificación (ADR 0026).
PREFIX_FILTER = "(documento_proveedor LIKE '8%' OR documento_proveedor LIKE '9%')"
LENGTH_FILTER = "length(documento_proveedor) >= 9 AND length(documento_proveedor) <= 10"
LEGAL_ENTITY_PREFIXES = ("8", "9")
LEGAL_ENTITY_LENGTHS = (9, 10)


def _header(path: Path) -> list[str]:
    # `utf-8-sig` descarta el BOM, que de otro modo cambiaría el nombre de la primera columna.
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle), [])


def _json_keys(node: object) -> set[str]:
    if isinstance(node, dict):
        return set(node) | {key for value in node.values() for key in _json_keys(value)}
    if isinstance(node, list):
        return {key for value in node for key in _json_keys(value)}
    return set()


def _files(directory: Path) -> list[Path]:
    return [path for path in sorted(directory.rglob("*")) if path.is_file()]


def snapshot_violations(directory: Path, queries: tuple[Query, ...]) -> list[str]:
    """Archivos de la copia que no están declarados o traen columnas fuera de la lista blanca."""
    by_id = {query.id: query for query in queries}
    violations = []
    for path in _files(directory):
        relative = path.relative_to(directory)
        if relative.as_posix() in SNAPSHOT_EXTRA_FILES:
            continue
        if len(relative.parts) > 1 or path.suffix != ".csv" or path.stem not in by_id:
            violations.append(f"{relative}: archivo no declarado en sources.toml")
            continue
        outside = set(_header(path)) - set(by_id[path.stem].allowed)
        if outside:
            violations.append(f"{relative}: columnas fuera de la lista blanca {sorted(outside)}")
    return violations


def excluded_column_violations(directory: Path, excluded: set[str]) -> list[str]:
    """Columnas o llaves excluidas en CSV y JSON, sin distinguir mayúsculas ni nivel."""
    forbidden = {column.casefold() for column in excluded}
    violations = []
    for path in _files(directory):
        if path.suffix == ".csv":
            found = {column.casefold() for column in _header(path)} & forbidden
        elif path.suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            found = {key.casefold() for key in _json_keys(payload)} & forbidden
        else:
            continue
        if found:
            violations.append(f"{path.relative_to(directory)}: columnas excluidas {sorted(found)}")
    return violations


def supplier_query_violations(queries: tuple[Query, ...]) -> list[str]:
    """Consultas que piden datos del proveedor sin NIT de 9 o 10 dígitos que empiezan por 8 o 9."""
    return [
        f"{query.id}: pide datos del proveedor sin el filtro {required}"
        for query in queries
        if SUPPLIER_COLUMNS & set(query.allowed)
        for required in (NIT_FILTER, PREFIX_FILTER, LENGTH_FILTER)
        if required not in query.where
    ]


def non_nit_supplier_violations(directory: Path) -> list[str]:
    """Filas de proveedores cuyo contrato no es de una persona jurídica (por número de fila)."""
    contracts_path = directory / "secop_contracts.csv"
    suppliers_path = directory / "secop_contracts_suppliers.csv"
    if not (contracts_path.exists() and suppliers_path.exists()):
        return []
    with contracts_path.open(encoding="utf-8-sig", newline="") as handle:
        document_type = {
            row["id_contrato"]: row["tipodocproveedor"] for row in csv.DictReader(handle)
        }
    violations = []
    with suppliers_path.open(encoding="utf-8-sig", newline="") as handle:
        for line, row in enumerate(csv.DictReader(handle), start=2):
            if document_type.get(row["id_contrato"]) != "NIT":
                violations.append(
                    f"{suppliers_path.name} fila {line}: el contrato no es de proveedor NIT"
                )
            elif not row["documento_proveedor"].startswith(LEGAL_ENTITY_PREFIXES):
                violations.append(
                    f"{suppliers_path.name} fila {line}: el documento no empieza por 8 ni 9"
                )
            elif len(row["documento_proveedor"]) not in LEGAL_ENTITY_LENGTHS:
                violations.append(
                    f"{suppliers_path.name} fila {line}: el documento no tiene 9 ni 10 dígitos"
                )
    return violations


def test_sources_are_declared() -> None:
    assert {query.id for query in QUERIES} >= {
        "secop_contracts",
        "secop_contracts_suppliers",
        "secop_procurement_processes",
        "secop_additions",
        "medata_contract_execution",
        "medata_procurement_plan",
    }


@pytest.mark.parametrize("query", QUERIES, ids=lambda query: query.id)
def test_allowed_and_excluded_do_not_overlap(query: Query) -> None:
    assert query.allowed, f"{query.id}: la lista permitida está vacía"
    assert not set(query.allowed) & set(query.excluded)


def test_no_query_allows_a_column_excluded_by_another() -> None:
    allowed = {column for query in QUERIES for column in query.allowed}
    assert not allowed & EXCLUDED


def test_socrata_queries_never_select_everything() -> None:
    for query in QUERIES:
        assert "*" not in query.allowed


def _write_csv(path: Path, header: list[str], rows: tuple[list[str], ...] = ()) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


# --- Copia: solo columnas de la lista blanca y solo archivos declarados -------------------


def test_snapshot_columns_are_whitelisted() -> None:
    assert snapshot_violations(SNAPSHOT_DIR, QUERIES) == []


def test_snapshot_rejects_column_outside_allowed(tmp_path: Path) -> None:
    _write_csv(tmp_path / "secop_additions.csv", ["id_contrato", "descripcion"])
    violations = snapshot_violations(tmp_path, QUERIES)
    assert len(violations) == 1
    assert "descripcion" in violations[0]


def test_snapshot_rejects_csv_without_query(tmp_path: Path) -> None:
    _write_csv(tmp_path / "unknown_source.csv", ["id_contrato"])
    assert len(snapshot_violations(tmp_path, QUERIES)) == 1


def test_snapshot_rejects_nested_csv(tmp_path: Path) -> None:
    _write_csv(tmp_path / "extra" / "secop_additions.csv", ["id_contrato"])
    assert len(snapshot_violations(tmp_path, QUERIES)) == 1


def test_snapshot_rejects_files_that_are_not_csv(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("cualquier cosa", encoding="utf-8")
    assert len(snapshot_violations(tmp_path, QUERIES)) == 1


def test_snapshot_accepts_declared_csv_manifest_and_gitkeep(tmp_path: Path) -> None:
    _write_csv(tmp_path / "secop_additions.csv", ["id_contrato", "tipo", "fecharegistro"])
    (tmp_path / "manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".gitkeep").write_text("", encoding="utf-8")
    assert snapshot_violations(tmp_path, QUERIES) == []


def test_snapshot_accepts_truncated_marker_in_medata_execution(tmp_path: Path) -> None:
    # El parser marca las filas truncadas con una columna derivada, sin datos personales.
    _write_csv(tmp_path / "medata_contract_execution.csv", ["contrato", "ano", "truncated"])
    assert snapshot_violations(tmp_path, QUERIES) == []


# --- Columnas excluidas: ni en la copia ni en las salidas ---------------------------------


def test_excluded_columns_never_reach_snapshot_or_outputs() -> None:
    for directory in (SNAPSHOT_DIR, OUTPUTS_DIR):
        assert excluded_column_violations(directory, EXCLUDED) == [], directory.name


@pytest.mark.parametrize(
    "content",
    [
        "contratista,otro\n",
        "﻿contratista,otro\n",
        "CC_NIT,otro\n",
    ],
    ids=["plain", "with-bom", "uppercase"],
)
def test_excluded_csv_column_is_detected_even_nested(tmp_path: Path, content: str) -> None:
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "table.csv").write_text(content, encoding="utf-8")
    assert len(excluded_column_violations(tmp_path, EXCLUDED)) == 1


def test_excluded_json_key_is_detected_when_nested(tmp_path: Path) -> None:
    payload = {"rows": [{"detail": {"contratista": "valor"}}]}
    (tmp_path / "summary.json").write_text(json.dumps(payload), encoding="utf-8")
    assert len(excluded_column_violations(tmp_path, EXCLUDED)) == 1


def test_excluded_name_inside_json_text_is_not_a_violation(tmp_path: Path) -> None:
    payload = {"note": "el contratista firmó y la descripcion está en otro documento"}
    (tmp_path / "summary.json").write_text(json.dumps(payload), encoding="utf-8")
    assert excluded_column_violations(tmp_path, EXCLUDED) == []


# --- Proveedores (R14): documento solo de personas jurídicas, nunca el nombre -------------------


def _supplier_query(where: str) -> Query:
    return Query(
        id="suppliers",
        dataset="dataset",
        kind="socrata",
        url="https://example.test/resource/dataset.csv",
        where=where,
        order_by="id_contrato",
        allowed=("id_contrato", "documento_proveedor"),
        excluded=(),
    )


def test_supplier_columns_require_nit_filter() -> None:
    assert supplier_query_violations((_supplier_query("entidad = 'X'"),)) != []


def test_supplier_columns_with_nit_filter_but_no_prefix_filter_are_rejected() -> None:
    where = f"entidad = 'X' AND tipodocproveedor = 'NIT' AND {LENGTH_FILTER}"
    violations = supplier_query_violations((_supplier_query(where),))
    assert len(violations) == 1
    assert "LIKE" in violations[0]


def test_supplier_columns_with_nit_and_prefix_but_no_length_filter_are_rejected() -> None:
    where = f"entidad = 'X' AND tipodocproveedor = 'NIT' AND {PREFIX_FILTER}"
    violations = supplier_query_violations((_supplier_query(where),))
    assert len(violations) == 1
    assert "length" in violations[0]


def test_supplier_columns_with_nit_prefix_and_length_filters_are_accepted() -> None:
    where = f"entidad = 'X' AND tipodocproveedor = 'NIT' AND {PREFIX_FILTER} AND {LENGTH_FILTER}"
    assert supplier_query_violations((_supplier_query(where),)) == []


def test_r14_supplier_name_is_excluded_and_never_allowed() -> None:
    # Los organizadores pidieron no mostrar nombres de personas naturales ni jurídicas (ADR 0049).
    assert "proveedor_adjudicado" in EXCLUDED
    assert all("proveedor_adjudicado" not in query.allowed for query in QUERIES)


def test_declared_supplier_queries_filter_by_nit() -> None:
    assert supplier_query_violations(QUERIES) == []


def test_snapshot_supplier_rows_must_belong_to_nit_contracts(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "secop_contracts.csv",
        ["id_contrato", "tipodocproveedor"],
        (["C1", "NIT"], ["C2", "Cédula de Ciudadanía"]),
    )
    _write_csv(
        tmp_path / "secop_contracts_suppliers.csv",
        ["id_contrato", "documento_proveedor"],
        (["C1", "900111222"], ["C2", "7654321"]),
    )
    violations = non_nit_supplier_violations(tmp_path)
    assert len(violations) == 1
    assert "fila 3" in violations[0]
    # El mensaje nunca repite el contenido de la fila.
    assert "7654321" not in violations[0]


def test_snapshot_supplier_rows_with_a_non_legal_entity_prefix_are_rejected(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "secop_contracts.csv",
        ["id_contrato", "tipodocproveedor"],
        (["C1", "NIT"], ["C2", "NIT"]),
    )
    _write_csv(
        tmp_path / "secop_contracts_suppliers.csv",
        ["id_contrato", "documento_proveedor"],
        (["C1", "900111222"], ["C2", "7654321"]),
    )
    violations = non_nit_supplier_violations(tmp_path)
    assert len(violations) == 1
    assert "fila 3" in violations[0]
    # El mensaje nunca repite el contenido de la fila.
    assert "7654321" not in violations[0]


@pytest.mark.parametrize("document", ["80123456", "9001112", "90011122233"])
def test_snapshot_supplier_rows_with_a_non_legal_entity_length_are_rejected(
    tmp_path: Path, document: str
) -> None:
    _write_csv(
        tmp_path / "secop_contracts.csv",
        ["id_contrato", "tipodocproveedor"],
        (["C1", "NIT"], ["C2", "NIT"]),
    )
    _write_csv(
        tmp_path / "secop_contracts_suppliers.csv",
        ["id_contrato", "documento_proveedor"],
        (["C1", "900111222"], ["C2", document]),
    )
    violations = non_nit_supplier_violations(tmp_path)
    assert len(violations) == 1
    assert "fila 3" in violations[0]
    assert document not in violations[0]


def test_snapshot_supplier_rows_with_nine_or_ten_digits_are_accepted(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "secop_contracts.csv",
        ["id_contrato", "tipodocproveedor"],
        (["C1", "NIT"], ["C2", "NIT"]),
    )
    _write_csv(
        tmp_path / "secop_contracts_suppliers.csv",
        ["id_contrato", "documento_proveedor"],
        (["C1", "900111222"], ["C2", "8909000811"]),
    )
    assert non_nit_supplier_violations(tmp_path) == []


def test_snapshot_supplier_rows_without_contract_are_rejected(tmp_path: Path) -> None:
    _write_csv(tmp_path / "secop_contracts.csv", ["id_contrato", "tipodocproveedor"])
    _write_csv(
        tmp_path / "secop_contracts_suppliers.csv",
        ["id_contrato", "documento_proveedor"],
        (["C9", "900111222"],),
    )
    assert len(non_nit_supplier_violations(tmp_path)) == 1


def test_snapshot_supplier_rows_of_nit_contracts_are_accepted(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "secop_contracts.csv", ["id_contrato", "tipodocproveedor"], (["C1", "NIT"],)
    )
    _write_csv(
        tmp_path / "secop_contracts_suppliers.csv",
        ["id_contrato", "documento_proveedor"],
        (["C1", "900111222"],),
    )
    assert non_nit_supplier_violations(tmp_path) == []


def test_real_snapshot_suppliers_belong_to_nit_contracts() -> None:
    assert non_nit_supplier_violations(SNAPSHOT_DIR) == []


def test_raw_data_is_ignored_by_git() -> None:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "data/raw/anything.csv"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


# --- Celdas pequeñas (R13, D4): ninguna celda desagregada con n < 5 sale sin suprimir ------------


def small_cell_violations(directory: Path) -> list[str]:
    """Celdas desagregadas con `sample_size` < umbral que se publicaron sin suprimir.

    Desagregada es por secretaría o por mes; la cifra anual del Distrito siempre se publica.
    El predicado no reutiliza `suppression.py`, para que la guarda no herede sus errores.
    """
    violations = []
    for path in _files(directory):
        if path.suffix != ".json":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not (isinstance(payload, dict) and "cells" in payload):
            continue
        for position, cell in enumerate(Indicators.model_validate(payload).cells):
            disaggregated = cell.level == "department" or len(cell.period) == len("AAAA-MM")
            if (
                disaggregated
                and cell.sample_size < SUPPRESSION_THRESHOLD
                and not cell.is_suppressed
            ):
                violations.append(
                    f"{path.relative_to(directory)} celda {position}: {cell.indicator} "
                    f"{cell.level} {cell.period} con n < {SUPPRESSION_THRESHOLD} sin suprimir"
                )
    return violations


def _cell(
    *, level: str = "department", period: str = "2025", sample_size: int, suppressed: bool = False
) -> dict:
    figures = None if suppressed else 1.0
    return {
        "indicator": "I2",
        "variant": None,
        "measure": "count",
        "level": level,
        "department": "Secretaría de Prueba" if level == "department" else None,
        "period": period,
        "sample_size": sample_size,
        "numerator": figures,
        "denominator": figures,
        "ratio": figures,
        "is_suppressed": suppressed,
    }


def _write_cells(directory: Path, *cells: dict, name: str = "indicators.json") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps({"cells": list(cells)}), encoding="utf-8")


def test_r13_published_outputs_have_no_small_unsuppressed_cells() -> None:
    assert small_cell_violations(OUTPUTS_DIR) == []


def test_r13_unsuppressed_department_cell_below_threshold_is_detected(tmp_path: Path) -> None:
    _write_cells(tmp_path, _cell(sample_size=3))
    violations = small_cell_violations(tmp_path)
    assert len(violations) == 1
    assert "celda 0" in violations[0]


def test_r13_unsuppressed_monthly_district_cell_below_threshold_is_detected(
    tmp_path: Path,
) -> None:
    _write_cells(tmp_path, _cell(level="district", period="2025-03", sample_size=3))
    assert len(small_cell_violations(tmp_path)) == 1


def test_r13_annual_district_cell_below_threshold_is_not_a_violation(tmp_path: Path) -> None:
    _write_cells(tmp_path, _cell(level="district", sample_size=3))
    assert small_cell_violations(tmp_path) == []


def test_r13_suppressed_and_threshold_cells_are_not_violations(tmp_path: Path) -> None:
    _write_cells(
        tmp_path,
        _cell(sample_size=3, suppressed=True),
        _cell(sample_size=SUPPRESSION_THRESHOLD),
    )
    assert small_cell_violations(tmp_path) == []


def test_r13_nested_outputs_are_checked_too(tmp_path: Path) -> None:
    _write_cells(tmp_path / "a" / "b", _cell(sample_size=3), name="by_department.json")
    assert len(small_cell_violations(tmp_path)) == 1
