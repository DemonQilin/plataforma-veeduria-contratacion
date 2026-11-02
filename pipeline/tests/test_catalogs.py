"""Catálogo de modalidades (R6, D1, D2): cada texto crudo cae en su categoría."""

import csv
from collections import Counter
from pathlib import Path

import ftfy
import pytest

from tests.paths import REPO_ROOT
from veeduria.normalize.catalogs import (
    CatalogError,
    classify_procurement_method,
    load_procurement_methods,
    method_key,
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


def test_method_key_ignores_case_accents_and_inner_spaces():
    assert method_key("  Concurso de M éritos ") == method_key("concurso de meritos")


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
