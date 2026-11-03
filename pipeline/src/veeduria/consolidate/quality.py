"""Tabla compartida de hallazgos de calidad que llenan las reglas de consolidación."""

import duckdb


def ensure_quality_issues(connection: duckdb.DuckDBPyConnection, rules: tuple[str, ...]) -> None:
    """Crea `quality_issues` si no existe y borra las filas de `rules` para repetir la regla."""
    connection.execute(
        "CREATE TABLE IF NOT EXISTS quality_issues"
        " (rule VARCHAR, record_key VARCHAR, detail VARCHAR)"
    )
    connection.execute(
        "DELETE FROM quality_issues WHERE rule = ANY($rules)", {"rules": list(rules)}
    )
