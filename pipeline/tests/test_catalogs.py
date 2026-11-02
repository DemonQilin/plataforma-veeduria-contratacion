"""Catálogos de modalidad, tipo de contrato y tipo de proveedor (R6, D1, D2)."""

import csv
from collections import Counter
from pathlib import Path

import ftfy
import pytest

from tests.paths import REPO_ROOT
from veeduria.normalize.catalogs import (
    CatalogError,
    catalog_key,
    classify_contract_type,
    classify_procurement_method,
    classify_supplier_type,
    is_interadministrative,
    load_contract_types,
    load_procurement_methods,
    load_supplier_types,
)

SNAPSHOT = REPO_ROOT / "data" / "snapshot"

# (texto crudo, código esperado, directa, competitiva)
KNOWN = [
    ("Contratación directa", "direct_award", True, False),
    ("Contratación Directa (con ofertas)", "direct_award", True, False),
    ("contratacion directa", "direct_award", True, False),
    ("Contratación régimen especial", "special_regime", False, False),
    ("Contratación régimen especial (con ofertas)", "special_regime", False, False),
    ("r egimen especial", "special_regime", False, False),
    ("Licitación pública", "public_tender", False, True),
    ("Licitación pública Obra Publica", "public_tender", False, True),
    ("Selección abreviada subasta inversa", "abbreviated_selection", False, True),
    ("Selección Abreviada de Menor Cuantía", "abbreviated_selection", False, True),
    (
        "Seleccion Abreviada Menor Cuantia Sin Manifestacion Interes",
        "abbreviated_selection",
        False,
        True,
    ),
    ("Concurso de méritos abierto", "merit_based_selection", False, True),
    ("concurso de m eritos", "merit_based_selection", False, True),
    ("Mínima cuantía", "minimum_amount", False, True),
    ("mnima cuanta", "minimum_amount", False, True),
]


@pytest.mark.parametrize(("raw", "code", "direct", "competitive"), KNOWN)
def test_known_text_falls_in_its_category(raw, code, direct, competitive):
    method = classify_procurement_method(raw)
    assert (method.code, method.direct_award, method.competitive) == (code, direct, competitive)


@pytest.mark.parametrize("raw", ["Subasta de prueba", "", "   ", None])
def test_unknown_or_empty_falls_in_other(raw):
    method = classify_procurement_method(raw)
    assert (method.code, method.direct_award, method.competitive) == ("other", False, False)


def test_direct_with_offers_counts_as_direct_but_special_regime_does_not():
    """D1 y D2."""
    assert classify_procurement_method("Contratación Directa (con ofertas)").direct_award
    assert not classify_procurement_method("Contratación régimen especial").direct_award


def test_catalog_key_ignores_case_accents_and_inner_spaces():
    assert catalog_key("  Concurso de M éritos ") == catalog_key("concurso de meritos")


def test_duplicate_raw_key_across_methods_fails_to_load(tmp_path: Path):
    catalog = tmp_path / "methods.toml"
    catalog.write_text(
        '[[method]]\ncode = "a"\nlabel = "A"\ndirect_award = true\ncompetitive = false\n'
        'raw = ["Igual"]\n'
        '[[method]]\ncode = "b"\nlabel = "B"\ndirect_award = false\ncompetitive = true\n'
        'raw = ["igual"]\n'
        '[[method]]\ncode = "other"\nlabel = "Otra"\ndirect_award = false\ncompetitive = false\n'
        "raw = []\n",
        encoding="utf-8",
    )
    with pytest.raises(CatalogError, match="igual"):
        load_procurement_methods(catalog)


def _raw_values(source: str, column: str) -> Counter[str]:
    with (SNAPSHOT / f"{source}.csv").open(newline="", encoding="utf-8") as handle:
        return Counter(ftfy.fix_encoding(row[column]) for row in csv.DictReader(handle))


@pytest.mark.parametrize(
    ("source", "column", "expected_unknown"),
    [
        ("secop_contracts", "modalidad_de_contratacion", set()),
        (
            "secop_procurement_processes",
            "modalidad_de_contratacion",
            {"Solicitud de información a los Proveedores", "Subasta de prueba"},
        ),
        ("medata_contract_execution", "modalidad", set()),
        ("medata_procurement_plan", "modalidad_seleccion", set()),
    ],
)
def test_snapshot_values_are_all_recognized(source, column, expected_unknown):
    unknown = {
        value
        for value in _raw_values(source, column)
        if classify_procurement_method(value).code == "other"
    }
    assert unknown == expected_unknown


# (tipo crudo, justificación, código esperado)
CONTRACT_TYPES = [
    ("Prestación de servicios", "Servicios profesionales y apoyo a la gestión", "service_contract"),
    ("prestacion de servicios", None, "service_contract"),
    ("Obra", None, "works"),
    (
        "Suministros",
        "Suministro de bienes y servicios de características técnicas uniformes",
        "supply_and_purchase",
    ),
    ("Compraventa", None, "supply_and_purchase"),
    ("Operaciones de Crédito Público", "Operaciones de Crédito Público", "public_credit"),
    ("Arrendamiento de inmuebles", None, "other"),
    ("Interventoría", None, "other"),
    ("Decreto 092 de 2017", "Decreto 092 de 2017", "other"),
    ("Otro", "Regla aplicable", "other"),
    ("No Especificado", None, "other"),
    ("", None, "other"),
    (None, None, "other"),
]


@pytest.mark.parametrize(("raw", "justification", "code"), CONTRACT_TYPES)
def test_r06_contract_type_falls_in_its_category(raw, justification, code):
    assert classify_contract_type(raw, justification).code == code


@pytest.mark.parametrize("raw_type", ["Otro", "Suministros", "Obra", None])
@pytest.mark.parametrize(
    "justification",
    [
        "Contratos o convenios Interadministrativos (con valor)",
        "Contratos o convenios Interadministrativos (valor cero)",
        "contratos o convenios interadministrativos (con valor)",
    ],
)
def test_r06_interadministrative_justification_wins_over_contract_type(raw_type, justification):
    assert classify_contract_type(raw_type, justification).code == "interadministrative"


@pytest.mark.parametrize(
    "causal",
    [
        "Contrato Interadmin",
        "Adic. Contr. Interad",
        "Cto Interadm Segurid",
        "Convenio Interadmin",
        "Ad. Cto InterSegurid",
    ],
)
def test_r06_medata_interadministrative_causal_is_recognized(causal):
    assert is_interadministrative(causal)


@pytest.mark.parametrize(
    "causal",
    ["Serv Prof y Apyo PN", "Ley 489 Artículo  95", "Conv. Coop. Internal", "", None],
)
def test_r06_other_causal_is_not_interadministrative(causal):
    assert not is_interadministrative(causal)


def test_r06_medata_causal_is_compared_after_repairing_the_encoding():
    assert is_interadministrative(ftfy.fix_encoding("Contrato Interadmin"))
    assert not is_interadministrative(ftfy.fix_encoding("Ley 489 ArtÃ\xadculo  95"))


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        ("NIT", "legal_entity"),
        ("nit", "legal_entity"),
        ("Cédula de Ciudadanía", "natural_person"),
        ("Cédula de Extranjería", "natural_person"),
        ("Pasaporte", "natural_person"),
        ("Permiso de protección temporal", "natural_person"),
        ("No Definido", "undefined"),
        ("Otro", "undefined"),
        ("Tarjeta nueva", "undefined"),
        ("", "undefined"),
        (None, "undefined"),
    ],
)
def test_r06_supplier_type_falls_in_its_category(raw, code):
    assert classify_supplier_type(raw).code == code


def _write_contract_types(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_duplicate_contract_type_text_fails_to_load(tmp_path: Path):
    catalog = _write_contract_types(
        tmp_path / "types.toml",
        "interadministrative_justifications = []\n"
        '[[type]]\ncode = "a"\nlabel = "A"\nraw = ["Igual"]\n'
        '[[type]]\ncode = "b"\nlabel = "B"\nraw = ["igual"]\n'
        '[[type]]\ncode = "other"\nlabel = "Otro"\nraw = []\n',
    )
    with pytest.raises(CatalogError, match="igual"):
        load_contract_types(catalog)


def test_contract_types_without_other_fail_to_load(tmp_path: Path):
    catalog = _write_contract_types(
        tmp_path / "types.toml",
        'interadministrative_justifications = []\n[[type]]\ncode = "a"\nlabel = "A"\nraw = []\n',
    )
    with pytest.raises(CatalogError, match="other"):
        load_contract_types(catalog)


def test_supplier_types_without_undefined_fail_to_load(tmp_path: Path):
    catalog = _write_contract_types(
        tmp_path / "suppliers.toml", '[[type]]\ncode = "legal_entity"\nlabel = "J"\nraw = ["NIT"]\n'
    )
    with pytest.raises(CatalogError, match="undefined"):
        load_supplier_types(catalog)


def _justification_flags() -> Counter[tuple[str, str]]:
    with (SNAPSHOT / "secop_contracts.csv").open(newline="", encoding="utf-8") as handle:
        return Counter(
            (row["tipo_de_contrato"], row["justificacion_modalidad_de"])
            for row in csv.DictReader(handle)
        )


def test_r06_snapshot_has_1446_interadministrative_contracts_in_secop():
    total = sum(
        count
        for (raw_type, justification), count in _justification_flags().items()
        if classify_contract_type(raw_type, justification).code == "interadministrative"
    )
    assert total == 1446


@pytest.mark.parametrize(
    ("source", "expected_unknown"),
    [
        ("secop_contracts", set()),
        ("secop_procurement_processes", {"No", "No Especificado"}),
    ],
)
def test_r06_snapshot_contract_types_are_all_recognized(source, expected_unknown):
    known = load_contract_types().by_key
    unknown = {
        value
        for value in _raw_values(source, "tipo_de_contrato")
        if value and catalog_key(value) not in known
    }
    assert unknown == expected_unknown


def test_r06_snapshot_supplier_types_are_all_recognized():
    unknown = {
        value
        for value in _raw_values("secop_contracts", "tipodocproveedor")
        if catalog_key(value) not in load_supplier_types().by_key
    }
    assert unknown == set()
