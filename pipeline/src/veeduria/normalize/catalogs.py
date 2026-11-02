"""Catálogos de `reference/` aplicados a los textos crudos (R6).

Un valor no reconocido no rompe el pipeline: cae en `other` (`undefined` en proveedores) y queda
para el reporte de calidad.
"""

import tomllib
import unicodedata
from dataclasses import dataclass
from functools import cache
from pathlib import Path

REFERENCE_DIR = Path(__file__).resolve().parents[3] / "reference"
PROCUREMENT_METHODS_PATH = REFERENCE_DIR / "procurement_methods.toml"
CONTRACT_TYPES_PATH = REFERENCE_DIR / "contract_types.toml"
SUPPLIER_TYPES_PATH = REFERENCE_DIR / "supplier_types.toml"
OTHER_CODE = "other"
UNDEFINED_CODE = "undefined"
INTERADMINISTRATIVE_CODE = "interadministrative"


class CatalogError(Exception):
    """El catálogo de `reference/` está mal formado."""


@dataclass(frozen=True)
class ProcurementMethod:
    code: str
    label: str
    direct_award: bool
    competitive: bool


@dataclass(frozen=True)
class CatalogEntry:
    code: str
    label: str


@dataclass(frozen=True)
class EntryCatalog:
    by_key: dict[str, CatalogEntry]
    default: CatalogEntry
    by_code: dict[str, CatalogEntry]
    interadministrative_keys: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ProcurementMethodCatalog:
    by_key: dict[str, ProcurementMethod]
    other: ProcurementMethod


def catalog_key(text: str) -> str:
    """Clave de comparación: sin mayúsculas, tildes ni espacios."""
    decomposed = unicodedata.normalize("NFKD", text)
    letters = (char for char in decomposed if not unicodedata.combining(char))
    return "".join("".join(letters).casefold().split())


def load_procurement_methods(path: Path = PROCUREMENT_METHODS_PATH) -> ProcurementMethodCatalog:
    with path.open("rb") as handle:
        entries = tomllib.load(handle).get("method", [])
    by_key: dict[str, ProcurementMethod] = {}
    other: ProcurementMethod | None = None
    for entry in entries:
        method = ProcurementMethod(
            code=entry["code"],
            label=entry["label"],
            direct_award=entry["direct_award"],
            competitive=entry["competitive"],
        )
        if method.code == OTHER_CODE:
            other = method
        for raw in entry["raw"]:
            key = catalog_key(raw)
            if key in by_key:
                raise CatalogError(f"El texto «{raw}» ({key}) está repetido en el catálogo.")
            by_key[key] = method
    if other is None:
        raise CatalogError(f"El catálogo no define la modalidad «{OTHER_CODE}».")
    return ProcurementMethodCatalog(by_key=by_key, other=other)


def _load_entries(path: Path, default_code: str) -> EntryCatalog:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    by_key: dict[str, CatalogEntry] = {}
    by_code: dict[str, CatalogEntry] = {}
    default: CatalogEntry | None = None
    for entry in data.get("type", []):
        item = CatalogEntry(code=entry["code"], label=entry["label"])
        by_code[item.code] = item
        if item.code == default_code:
            default = item
        for raw in entry["raw"]:
            key = catalog_key(raw)
            if key in by_key:
                raise CatalogError(f"El texto «{raw}» ({key}) está repetido en el catálogo.")
            by_key[key] = item
    if default is None:
        raise CatalogError(f"El catálogo no define el tipo «{default_code}».")
    justifications = frozenset(
        catalog_key(text) for text in data.get("interadministrative_justifications", [])
    )
    return EntryCatalog(
        by_key=by_key,
        default=default,
        by_code=by_code,
        interadministrative_keys=justifications,
    )


def load_contract_types(path: Path = CONTRACT_TYPES_PATH) -> EntryCatalog:
    catalog = _load_entries(path, OTHER_CODE)
    if catalog.interadministrative_keys and INTERADMINISTRATIVE_CODE not in catalog.by_code:
        raise CatalogError(f"El catálogo no define el tipo «{INTERADMINISTRATIVE_CODE}».")
    return catalog


def load_supplier_types(path: Path = SUPPLIER_TYPES_PATH) -> EntryCatalog:
    return _load_entries(path, UNDEFINED_CODE)


@cache
def _default_catalog() -> ProcurementMethodCatalog:
    return load_procurement_methods()


def classify_procurement_method(
    raw: str | None, catalog: ProcurementMethodCatalog | None = None
) -> ProcurementMethod:
    """Traduce un texto crudo (ya con la codificación reparada) a su modalidad."""
    catalog = catalog or _default_catalog()
    return catalog.by_key.get(catalog_key(raw or ""), catalog.other)


@cache
def _default_contract_types() -> EntryCatalog:
    return load_contract_types()


@cache
def _default_supplier_types() -> EntryCatalog:
    return load_supplier_types()


def is_interadministrative(
    method_justification: str | None, catalog: EntryCatalog | None = None
) -> bool:
    """¿La justificación (SECOP II) o la causal (MEData, ya reparada) es interadministrativa?"""
    catalog = catalog or _default_contract_types()
    return catalog_key(method_justification or "") in catalog.interadministrative_keys


def classify_contract_type(
    raw_type: str | None,
    method_justification: str | None = None,
    catalog: EntryCatalog | None = None,
) -> CatalogEntry:
    """La justificación interadministrativa gana sobre el tipo crudo (ADR 0022)."""
    catalog = catalog or _default_contract_types()
    if is_interadministrative(method_justification, catalog):
        return catalog.by_code[INTERADMINISTRATIVE_CODE]
    return catalog.by_key.get(catalog_key(raw_type or ""), catalog.default)


def classify_supplier_type(raw: str | None, catalog: EntryCatalog | None = None) -> CatalogEntry:
    catalog = catalog or _default_supplier_types()
    return catalog.by_key.get(catalog_key(raw or ""), catalog.default)
