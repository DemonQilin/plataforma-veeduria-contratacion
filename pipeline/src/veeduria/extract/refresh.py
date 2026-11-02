"""`veeduria run --refresh`: actualiza toda la copia o no toca nada (ADR 0006).

Cada consulta se extrae a una carpeta temporal dentro de `data/raw/` (fuera de git). Adiciones
lee los `id_contrato` de esa carpeta, no de la copia anterior. Solo si todas terminan bien se
mueven los CSV a `data/snapshot/` y, al final, se escribe el manifiesto.
"""

import os
import shutil
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from veeduria.extract.http import Extraction
from veeduria.extract.manifest import cutoff_date, read_manifest, source_entry, write_manifest
from veeduria.extract.snapshot import write_snapshot
from veeduria.extract.sources import Query

Download = Callable[[Query, Path], Extraction]


@dataclass
class RefreshReport:
    refreshed: list[tuple[str, int, str]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _fingerprint(entry: dict) -> str:
    return entry.get("source_sha256") or entry["sha256"]


def refresh_snapshot(
    queries: Sequence[Query],
    snapshot_dir: Path,
    raw_dir: Path,
    download: Download,
    *,
    force_frozen: bool = False,
    now: datetime | None = None,
) -> RefreshReport:
    """Extrae todas las consultas; si una falla, la copia y el manifiesto quedan intactos.

    Las consultas `frozen` (el Plan Anual, que ya no se actualiza) solo se vuelven a pedir si
    se fuerza o si todavía no tienen entrada en el manifiesto.
    """
    extracted_at = (now or datetime.now(UTC)).replace(microsecond=0)
    previous = read_manifest(snapshot_dir)["sources"]
    report = RefreshReport()
    entries: dict[str, dict] = {}
    staged: list[Path] = []

    raw_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(dir=raw_dir, prefix=".refresh-"))
    try:
        for query in queries:
            old = previous.get(query.id)
            kept = query.frozen and not force_frozen and old is not None
            if kept and (snapshot_dir / f"{query.id}.csv").exists():
                entries[query.id] = old
                report.skipped.append(query.id)
                continue

            extraction = download(query, staging)
            result = write_snapshot(query, extraction.header, extraction.rows, staging)
            entry = source_entry(
                query,
                row_count=result.row_count,
                sha256=result.sha256,
                source_sha256=extraction.source_sha256,
                extracted_at=extracted_at,
                cutoff=cutoff_date(query, extraction),
            )
            if query.kind.startswith("medata") and old and _fingerprint(old) != _fingerprint(entry):
                report.warnings.append(
                    f"{query.id}: la fuente cambió desde la última extracción "
                    f"({_fingerprint(old)[:8]}… → {_fingerprint(entry)[:8]}…)."
                )
            entries[query.id] = entry
            staged.append(result.path)
            report.refreshed.append((query.id, result.row_count, result.sha256))

        snapshot_dir.mkdir(parents=True, exist_ok=True)
        for path in staged:
            os.replace(path, snapshot_dir / path.name)
        write_manifest(snapshot_dir, entries)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return report
