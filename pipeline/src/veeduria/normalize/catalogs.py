"""Catálogos de `reference/` aplicados a los textos crudos (R6).

Un valor no reconocido no rompe el pipeline: cae en `other` y queda para el reporte de calidad.
"""

import tomllib
import unicodedata
from dataclasses import dataclass
from functools import cache
from pathlib import Path

REFERENCE_DIR = Path(__file__).resolve().parents[3] / "reference"
PROCUREMENT_METHODS_PATH = REFERENCE_DIR / "procurement_methods.toml"
OTHER_CODE = "other"


class CatalogError(Exception):
    """El catálogo de `reference/` está mal formado."""


@dataclass(frozen=True)
class ProcurementMethod:
    code: str
    label: str
    direct_award: bool
    competitive: bool


@dataclass(frozen=True)
class ProcurementMethodCatalog:
    by_key: dict[str, ProcurementMethod]
    other: ProcurementMethod


def method_key(text: str) -> str:
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
            key = method_key(raw)
            if key in by_key:
                raise CatalogError(f"El texto «{raw}» ({key}) está repetido en el catálogo.")
            by_key[key] = method
    if other is None:
        raise CatalogError(f"El catálogo no define la modalidad «{OTHER_CODE}».")
    return ProcurementMethodCatalog(by_key=by_key, other=other)


@cache
def _default_catalog() -> ProcurementMethodCatalog:
    return load_procurement_methods()


def classify_procurement_method(
    raw: str | None, catalog: ProcurementMethodCatalog | None = None
) -> ProcurementMethod:
    """Traduce un texto crudo (ya con la codificación reparada) a su modalidad."""
    catalog = catalog or _default_catalog()
    return catalog.by_key.get(method_key(raw or ""), catalog.other)
