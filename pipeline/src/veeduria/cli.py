"""CLI del pipeline: `veeduria run --from-snapshot | --refresh` y `veeduria export-schema`."""

from pathlib import Path
from typing import Annotated

import duckdb
import typer

from veeduria.extract.http import Extraction, ExtractionError
from veeduria.extract.medata import fetch_sql_query
from veeduria.extract.medata_csv import fetch_csv_query
from veeduria.extract.refresh import refresh_snapshot
from veeduria.extract.snapshot import read_column, write_snapshot
from veeduria.extract.socrata import (
    app_token_from_env,
    fetch_query,
    fetch_query_by_ids,
    make_client,
)
from veeduria.extract.sources import Query, load_queries
from veeduria.indicators import build_indicators
from veeduria.indicators.electoral_calendar import comparison_windows, load_electoral_calendar
from veeduria.indicators.monthly_series import build_monthly_series
from veeduria.normalize.catalogs import CatalogError
from veeduria.pipeline import build
from veeduria.publish.electoral_calendar import publish_electoral_calendar
from veeduria.publish.indicators import publish_indicators
from veeduria.publish.metadata import build_metadata, serialize
from veeduria.publish.models import export_schemas
from veeduria.publish.outputs import write_outputs
from veeduria.publish.quality import build_quality
from veeduria.publish.series import publish_monthly_series

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Veeduría de contratación.")

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DEFAULT_SCHEMA_DIR = DATA_DIR / "schema"
DEFAULT_SNAPSHOT_DIR = DATA_DIR / "snapshot"
DEFAULT_RAW_DIR = DATA_DIR / "raw"
DEFAULT_OUTPUT_DIR = DATA_DIR / "outputs"


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
    force_procurement_plan: Annotated[
        bool,
        typer.Option(
            "--force-procurement-plan",
            help="Con --refresh, vuelve a pedir el Plan Anual, que ya no se actualiza.",
        ),
    ] = False,
    snapshot_dir: Annotated[
        Path, typer.Option("--snapshot-dir", help="Carpeta de la copia de datos.")
    ] = DEFAULT_SNAPSHOT_DIR,
    raw_dir: Annotated[
        Path,
        typer.Option("--raw-dir", help="Carpeta de trabajo de las descargas (fuera de git)."),
    ] = DEFAULT_RAW_DIR,
    output_dir: Annotated[
        Path, typer.Option("--output-dir", help="Carpeta de las salidas del tablero.")
    ] = DEFAULT_OUTPUT_DIR,
) -> None:
    """Ejecuta el pipeline."""
    if from_snapshot == refresh:
        # Sin el recuadro de Rich de BadParameter: el mensaje sale igual con o sin color.
        typer.echo("Indica exactamente una opción: --from-snapshot o --refresh.", err=True)
        raise typer.Exit(2)
    if force_procurement_plan and not refresh:
        typer.echo("--force-procurement-plan solo se usa junto con --refresh.", err=True)
        raise typer.Exit(2)
    if refresh:
        _refresh(snapshot_dir, raw_dir, force_procurement_plan)
    if from_snapshot:
        _publish(snapshot_dir, output_dir)


def _publish(snapshot_dir: Path, output_dir: Path) -> None:
    """Corre las etapas desde la copia y publica; ante un fallo no toca `output_dir`."""
    try:
        connection = build(snapshot_dir)
        metadata = build_metadata(connection)
        indicators = publish_indicators(build_indicators(connection, metadata.cutoff_date))
        monthly_series = publish_monthly_series(
            build_monthly_series(connection, metadata.cutoff_date)
        )
        quality = build_quality(connection)
        calendar = load_electoral_calendar()
        electoral_calendar = publish_electoral_calendar(
            calendar, comparison_windows(calendar, metadata.cutoff_date), metadata.cutoff_date
        )
    except (duckdb.IOException, CatalogError, ValueError) as error:
        # El mensaje de DuckDB puede citar rutas, nunca filas; no se imprime tal cual.
        typer.echo(
            f"No se pudo leer la copia de {snapshot_dir}: {type(error).__name__}. "
            "Las salidas no se modificaron.",
            err=True,
        )
        raise typer.Exit(1) from None
    files = {
        "electoral_calendar.json": serialize(electoral_calendar),
        "indicators.json": serialize(indicators),
        "metadata.json": serialize(metadata),
        "monthly_series.json": serialize(monthly_series),
        "quality.json": serialize(quality),
    }
    for path in write_outputs(files, output_dir):
        typer.echo(f"Escrito {path}")


def _refresh(snapshot_dir: Path, raw_dir: Path, force_procurement_plan: bool) -> None:
    try:
        report = refresh_snapshot(
            load_queries(),
            snapshot_dir,
            raw_dir,
            lambda query, staging: _download(query, staging, raw_dir),
            force_frozen=force_procurement_plan,
        )
    except ExtractionError as error:
        typer.echo(f"Extracción fallida, la copia no se modificó: {error}", err=True)
        raise typer.Exit(1) from None
    for query_id, row_count, sha256 in report.refreshed:
        typer.echo(f"{query_id}: {row_count} filas, SHA-256 {sha256}")
    for query_id in report.skipped:
        typer.echo(
            f"{query_id}: sin cambios, la fuente ya no se actualiza (--force-procurement-plan)."
        )
    for warning in report.warnings:
        typer.echo(f"Aviso · {warning}", err=True)
    typer.echo(f"Copia actualizada: {snapshot_dir / 'manifest.json'}")


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
