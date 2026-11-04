"""Escritura atómica de `data/outputs/` (falla segura)."""

import os
import shutil
import tempfile
from pathlib import Path


def write_outputs(files: dict[str, bytes], output_dir: Path) -> list[Path]:
    """Escribe `files` en un directorio temporal y lo mueve a `output_dir` solo si todo salió bien.

    Si algo falla, `output_dir` queda como estaba. Reemplaza la carpeta completa, así que no
    quedan archivos de corridas anteriores.
    """
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(dir=output_dir.parent, prefix=".outputs-"))
    backup = staging.with_name(staging.name + "-old")
    try:
        for name, content in sorted(files.items()):
            (staging / name).write_bytes(content)
        if output_dir.exists():
            os.replace(output_dir, backup)
        try:
            os.replace(staging, output_dir)
        except OSError:
            if backup.exists():
                os.replace(backup, output_dir)
            raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)
    return [output_dir / name for name in sorted(files)]
