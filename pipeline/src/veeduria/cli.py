"""CLI del pipeline: `veeduria run --from-snapshot | --refresh` y `veeduria export-schema`."""

from pathlib import Path
from typing import Annotated

import typer

from veeduria.publish.models import export_schemas

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Veeduría de contratación.")

DEFAULT_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "data" / "schema"


@app.callback()
def main() -> None:
    """Veeduría de contratación de la Alcaldía de Medellín."""


@app.command()
def run(
    from_snapshot: Annotated[
        bool, typer.Option("--from-snapshot", help="Usa la copia de data/snapshot/, sin red.")
    ] = False,
    refresh: Annotated[
        bool, typer.Option("--refresh", help="Actualiza la copia desde las fuentes.")
    ] = False,
) -> None:
    """Ejecuta el pipeline."""
    if from_snapshot == refresh:
        raise typer.BadParameter("indica exactamente una opción: --from-snapshot o --refresh")
    typer.echo("Las etapas del pipeline todavía no están implementadas.", err=True)
    raise typer.Exit(1)


@app.command("export-schema")
def export_schema(
    output_dir: Annotated[
        Path, typer.Option("--output-dir", help="Carpeta de destino de los JSON Schema.")
    ] = DEFAULT_SCHEMA_DIR,
) -> None:
    """Exporta el contrato (JSON Schema) a data/schema/."""
    for path in export_schemas(output_dir):
        typer.echo(f"Escrito {path.name}")
