"""Escritor de la copia en `data/snapshot/` (ADR 0006).

Un CSV por consulta, UTF-8 sin BOM y finales de línea LF, con valores crudos. Se escribe
en un archivo temporal de la misma carpeta y se mueve al final: si algo falla, la copia
anterior queda intacta y no quedan restos.
"""

import csv
import hashlib
import os
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from veeduria.extract.sources import Query

FILE_MODE = 0o644


@dataclass(frozen=True)
class SnapshotResult:
    path: Path
    row_count: int
    sha256: str


def write_snapshot(
    query: Query,
    header: Sequence[str],
    rows: Iterable[Sequence[str]],
    directory: Path,
) -> SnapshotResult:
    outside = sorted(set(header) - set(query.allowed))
    if outside:
        # Segunda red de la lista blanca (ADR 0007): nada fuera de `allowed` llega al disco.
        raise ValueError(f"{query.id}: columnas fuera de la lista blanca {outside}.")

    directory.mkdir(parents=True, exist_ok=True)
    final = directory / f"{query.id}.csv"
    descriptor, temp_name = tempfile.mkstemp(dir=directory, prefix=f".{query.id}.", suffix=".tmp")
    temp = Path(temp_name)
    try:
        row_count = 0
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(header)
            for row in rows:
                if len(row) != len(header):
                    raise ValueError(
                        f"{query.id}: la línea {row_count + 2} tiene {len(row)} columnas "
                        f"y se esperaban {len(header)}."
                    )
                writer.writerow(row)
                row_count += 1
        sha256 = hashlib.sha256(temp.read_bytes()).hexdigest()
        temp.chmod(FILE_MODE)
        os.replace(temp, final)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    return SnapshotResult(path=final, row_count=row_count, sha256=sha256)
