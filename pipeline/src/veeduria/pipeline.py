"""Orquestación de las etapas sobre la copia versionada (`run --from-snapshot`)."""

from pathlib import Path

import duckdb

from veeduria.consolidate.canonical_contracts import consolidate_contracts
from veeduria.consolidate.canonical_processes import consolidate_processes
from veeduria.link.linked_contracts import link_contracts
from veeduria.link.medata_contracts import collapse_medata_contracts
from veeduria.link.reconciliation import reconcile_sources
from veeduria.normalize.additions import normalize_additions
from veeduria.normalize.contract_execution import normalize_contract_execution
from veeduria.normalize.contracts import normalize_contracts
from veeduria.normalize.procurement_plan import normalize_procurement_plan
from veeduria.normalize.procurement_processes import normalize_procurement_processes
from veeduria.normalize.suppliers import normalize_suppliers


def build(snapshot_dir: Path) -> duckdb.DuckDBPyConnection:
    """Corre normalización, consolidación, cruce y conciliación en memoria.

    Solo lee `snapshot_dir`: no usa la red ni escribe nada. Si falta un CSV, DuckDB falla con
    `duckdb.IOException`, que la CLI traduce a un mensaje.
    """
    connection = duckdb.connect()
    normalize_contracts(connection, snapshot_dir / "secop_contracts.csv")
    normalize_suppliers(connection, snapshot_dir / "secop_contracts_suppliers.csv")
    normalize_procurement_processes(connection, snapshot_dir / "secop_procurement_processes.csv")
    normalize_additions(connection, snapshot_dir / "secop_additions.csv")
    normalize_procurement_plan(connection, snapshot_dir / "medata_procurement_plan.csv")
    normalize_contract_execution(connection, snapshot_dir / "medata_contract_execution.csv")
    consolidate_contracts(connection)
    consolidate_processes(connection)
    collapse_medata_contracts(connection)
    link_contracts(connection)
    reconcile_sources(connection)
    return connection
