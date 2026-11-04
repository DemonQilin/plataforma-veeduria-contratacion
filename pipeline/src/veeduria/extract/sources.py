"""Lectura de `sources.toml`: lista blanca de columnas y consultas (ADR 0007)."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SOURCES_PATH = Path(__file__).resolve().parents[3] / "sources.toml"


@dataclass(frozen=True)
class Query:
    id: str
    dataset: str
    kind: str
    url: str
    where: str
    order_by: str
    allowed: tuple[str, ...]
    excluded: tuple[str, ...]
    # Consultas sin campo de entidad (Adiciones): los identificadores salen de la copia
    # de otra consulta, en la columna indicada, y se piden por lotes.
    batch_source: str = ""
    batch_column: str = ""
    # API SQL de MEData: identificador de la distribución CSV que se consulta. La ficha
    # del conjunto da 504 con frecuencia, así que no se averigua en cada ejecución.
    distribution: str = ""
    # Fuente que ya no se actualiza: `--refresh` no la vuelve a pedir salvo que se fuerce.
    frozen: bool = False
    # Columna con la que se calcula la fecha de corte de la fuente en el manifiesto.
    cutoff_column: str = ""


def load_queries(path: Path = DEFAULT_SOURCES_PATH) -> tuple[Query, ...]:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return tuple(
        Query(
            id=item["id"],
            dataset=item["dataset"],
            kind=item["kind"],
            url=item["url"],
            where=item["where"],
            order_by=item["order_by"],
            allowed=tuple(item["allowed"]),
            excluded=tuple(item["excluded"]),
            batch_source=item.get("batch_source", ""),
            batch_column=item.get("batch_column", ""),
            distribution=item.get("distribution", ""),
            frozen=item.get("frozen", False),
            cutoff_column=item.get("cutoff_column", ""),
        )
        for item in raw["queries"]
    )


@dataclass(frozen=True)
class Dataset:
    """Fuente citada en el tablero: enlace y licencia (R16)."""

    id: str
    name: str
    url: str
    license: str


def load_datasets(path: Path = DEFAULT_SOURCES_PATH) -> tuple[Dataset, ...]:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return tuple(
        Dataset(id=item["id"], name=item["name"], url=item["url"], license=item["license"])
        for item in raw["datasets"]
    )
