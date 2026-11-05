"""Textos crudos que los catálogos no reconocen, para el reporte de calidad (R6, R8; ADR 0042).

Un texto es no reconocido cuando su clave de comparación no está en el catálogo. No sirve contar
el código `other`: los catálogos listan a propósito textos conocidos bajo «Otro».
"""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import duckdb
from ftfy import fix_encoding

from veeduria.normalize.catalogs import CatalogName, is_recognized


@dataclass(frozen=True)
class _Check:
    catalog: CatalogName
    source: str
    column: str
    repair_encoding: bool = False


# Los mismos pares (archivo de la copia, columna) que clasifican los módulos de `normalize/`.
# MEData · Ejecución se compara después de reparar la codificación (ADR 0010).
CHECKS = (
    _Check("procurement_method", "secop_contracts", "modalidad_de_contratacion"),
    _Check("contract_type", "secop_contracts", "tipo_de_contrato"),
    _Check("supplier_type", "secop_contracts", "tipodocproveedor"),
    _Check("procurement_method", "secop_procurement_processes", "modalidad_de_contratacion"),
    _Check("contract_type", "secop_procurement_processes", "tipo_de_contrato"),
    _Check("department", "secop_procurement_processes", "nombre_de_la_unidad_de"),
    _Check("addition_type", "secop_additions", "tipo"),
    _Check("procurement_method", "medata_procurement_plan", "modalidad_seleccion"),
    _Check("procurement_method", "medata_contract_execution", "modalidad", True),
    _Check("department", "medata_contract_execution", "nombre_secretaria", True),
)


def record_unrecognized_values(connection: duckdb.DuckDBPyConnection, snapshot_dir: Path) -> None:
    """Crea `unrecognized_values`: una fila por catálogo, fuente y texto, con sus filas de la copia.

    Los textos vacíos no cuentan: no son un valor que el catálogo deba conocer.
    """
    found: list[tuple[str, str, str, int]] = []
    for check in CHECKS:
        counts: Counter[str] = Counter()
        rows = connection.execute(
            f"SELECT coalesce({check.column}, ''), count(*)"
            " FROM read_csv($path, all_varchar = true, header = true) GROUP BY 1",
            {"path": str(snapshot_dir / f"{check.source}.csv")},
        ).fetchall()
        for text, count in rows:
            counts[fix_encoding(text) if check.repair_encoding else text] += count
        found.extend(
            (check.catalog, check.source, text, count)
            for text, count in counts.items()
            if text.strip() and not is_recognized(check.catalog, text)
        )
    found.sort()
    connection.execute(
        "CREATE OR REPLACE TABLE unrecognized_values AS"
        " SELECT unnest($catalogs::VARCHAR[]) AS catalog, unnest($sources::VARCHAR[]) AS source,"
        " unnest($texts::VARCHAR[]) AS raw_text, unnest($counts::BIGINT[]) AS row_count",
        {
            "catalogs": [row[0] for row in found],
            "sources": [row[1] for row in found],
            "texts": [row[2] for row in found],
            "counts": [row[3] for row in found],
        },
    )
