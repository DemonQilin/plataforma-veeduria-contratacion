"""CLI del pipeline: `veeduria run --from-snapshot | --refresh` y `veeduria export-schema`."""

from pathlib import Path
from typing import Annotated

import typer

from veeduria.extract.http import Extraction, ExtractionError
from veeduria.extract.medata import fetch_sql_query
from veeduria.extract.medata_csv import fetch_csv_query
from veeduria.extract.snapshot import read_column, write_snapshot
from veeduria.extract.socrata import (
    app_token_from_env,
    fetch_query,
    fetch_query_by_ids,
    make_client,
)
from veeduria.extract.sources import Query, load_queries
from veeduria.publish.models import export_schemas

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Veeduría de contratación.")

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DEFAULT_SCHEMA_DIR = DATA_DIR / "schema"
DEFAULT_SNAPSHOT_DIR = DATA_DIR / "snapshot"
DEFAULT_RAW_DIR = DATA_DIR / "raw"


def _batch_ids(query: Query, snapshot_dir: Path) -> list[str]:
    """Identificadores de la copia de origen; sin ella no hay qué consultar."""
    try:
        return read_column(snapshot_dir / f"{query.batch_source}.csv", query.batch_column)
    except (FileNotFoundError, ValueError):
        raise ExtractionError(
            f"{query.id} necesita la copia de {query.batch_source}. "
            f"Extráela primero: veeduria extract {query.batch_source}."
        ) from None


def _download(query: Query, snapshot_dir: Path, raw_dir: Path) -> Extraction:
    if query.kind == "medata_csv":
        # Sin token de datos.gov.co, y el archivo completo queda en data/raw/ (fuera de git).
        with make_client(None) as client:
            return fetch_csv_query(client, query, raw_dir)
    if query.kind == "medata_sql":
        # El token de datos.gov.co no debe viajar a otro dominio.
        with make_client(None) as client:
            return fetch_sql_query(client, query)
    ids = _batch_ids(query, snapshot_dir) if query.batch_source else None
    with make_client(app_token_from_env()) as client:
        if ids is None:
            return fetch_query(client, query)
        return fetch_query_by_ids(client, query, ids)


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
    raw_dir: Annotated[
        Path,
        typer.Option("--raw-dir", help="Carpeta del archivo completo de MEData (fuera de git)."),
    ] = DEFAULT_RAW_DIR,
) -> None:
    """Descarga una consulta de SECOP II o de MEData a data/snapshot/."""
    queries = {query.id: query for query in load_queries()}
    if query_id not in queries:
        typer.echo(f"Consulta desconocida: {query_id}. Disponibles: {sorted(queries)}.", err=True)
        raise typer.Exit(2)
    query = queries[query_id]
    try:
        extraction = _download(query, snapshot_dir, raw_dir)
        result = write_snapshot(query, extraction.header, extraction.rows, snapshot_dir)
    except ExtractionError as error:
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
