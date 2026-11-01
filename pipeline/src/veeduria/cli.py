"""CLI del pipeline: `veeduria run --from-snapshot | --refresh` y `veeduria export-schema`."""

from pathlib import Path
from typing import Annotated

import typer

from veeduria.extract.snapshot import write_snapshot
from veeduria.extract.socrata import SocrataError, app_token_from_env, fetch_query, make_client
from veeduria.extract.sources import load_queries
from veeduria.publish.models import export_schemas

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Veeduría de contratación.")

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DEFAULT_SCHEMA_DIR = DATA_DIR / "schema"
DEFAULT_SNAPSHOT_DIR = DATA_DIR / "snapshot"

# Consultas de Socrata que `extract` ya sabe descargar. Las demás llegan en sus tareas.
EXTRACTABLE_QUERIES = (
    "secop_contracts",
    "secop_contracts_suppliers",
    "secop_procurement_processes",
)


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
        # Sin el recuadro de Rich de BadParameter: el mensaje sale igual con o sin color.
        typer.echo("Indica exactamente una opción: --from-snapshot o --refresh.", err=True)
        raise typer.Exit(2)
    typer.echo("Las etapas del pipeline todavía no están implementadas.", err=True)
    raise typer.Exit(1)


@app.command()
def extract(
    query_id: Annotated[str, typer.Argument(help="Identificador de la consulta en sources.toml.")],
    snapshot_dir: Annotated[
        Path, typer.Option("--snapshot-dir", help="Carpeta de destino de la copia.")
    ] = DEFAULT_SNAPSHOT_DIR,
) -> None:
    """Descarga una consulta de SECOP II a data/snapshot/."""
    queries = {query.id: query for query in load_queries()}
    if query_id not in queries:
        typer.echo(f"Consulta desconocida: {query_id}. Disponibles: {sorted(queries)}.", err=True)
        raise typer.Exit(2)
    if query_id not in EXTRACTABLE_QUERIES:
        typer.echo(
            f"La consulta {query_id} todavía no está implementada. "
            f"Disponibles: {list(EXTRACTABLE_QUERIES)}.",
            err=True,
        )
        raise typer.Exit(2)
    try:
        with make_client(app_token_from_env()) as client:
            extraction = fetch_query(client, queries[query_id])
        result = write_snapshot(queries[query_id], extraction.header, extraction.rows, snapshot_dir)
    except SocrataError as error:
        typer.echo(f"Extracción fallida, la copia no se modificó: {error}", err=True)
        raise typer.Exit(1) from None
    typer.echo(f"{query_id}: {result.row_count} filas, SHA-256 {result.sha256}")


@app.command("export-schema")
def export_schema(
    output_dir: Annotated[
        Path, typer.Option("--output-dir", help="Carpeta de destino de los JSON Schema.")
    ] = DEFAULT_SCHEMA_DIR,
) -> None:
    """Exporta el contrato (JSON Schema) a data/schema/."""
    for path in export_schemas(output_dir):
        typer.echo(f"Escrito {path.name}")
