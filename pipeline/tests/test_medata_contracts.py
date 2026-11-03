"""Colapso de MEData · Ejecución a un registro por contrato (R8, D3; ADR 0030)."""

from datetime import date

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.link.medata_contracts import collapse_medata_contracts
from veeduria.normalize.contract_execution import normalize_contract_execution

SNAPSHOT = REPO_ROOT / "data" / "snapshot"


def _connection(rows: str) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE contract_execution (contract_reference VARCHAR, signed_date DATE,"
        " department VARCHAR, initial_value DECIMAL(18, 2), total_addition_value DECIMAL(18, 2),"
        " final_value DECIMAL(18, 2), duration_days INTEGER, contract_status VARCHAR,"
        " truncated BOOLEAN)"
    )
    connection.execute(f"INSERT INTO contract_execution VALUES {rows}")
    return connection


def test_d03_many_lines_collapse_to_one_contract_with_the_complete_values() -> None:
    connection = _connection(
        "('4600-1', DATE '2022-01-10', 'Salud', 100, 20, 120, 30, 'Terminado', FALSE),"
        "('4600-1', DATE '2022-01-10', 'Salud', 100, 20, 120, 30, 'Terminado', FALSE)"
    )
    collapse_medata_contracts(connection)
    assert connection.execute(
        "SELECT contract_reference, signed_date, department, initial_value,"
        " total_addition_value, final_value, duration_days, contract_status, row_count, truncated"
        " FROM medata_contracts"
    ).fetchall() == [
        ("4600-1", date(2022, 1, 10), "Salud", 100, 20, 120, 30, "Terminado", 2, False)
    ]


def test_d03_truncated_lines_do_not_erase_the_values_of_complete_lines() -> None:
    connection = _connection(
        "('4600-1', DATE '2022-01-10', 'Salud', NULL, NULL, NULL, NULL, NULL, TRUE),"
        "('4600-1', DATE '2022-01-10', 'Salud', 100, 20, 120, 30, 'Terminado', FALSE)"
    )
    collapse_medata_contracts(connection)
    assert connection.execute(
        "SELECT final_value, truncated, row_count FROM medata_contracts"
    ).fetchone() == (120, False, 2)


def test_d03_contract_with_only_truncated_lines_keeps_department_and_has_no_values() -> None:
    connection = _connection(
        "('4600-2', DATE '2022-02-01', 'Educación', NULL, NULL, NULL, NULL, NULL, TRUE),"
        "('4600-2', DATE '2022-02-01', 'Educación', NULL, NULL, NULL, NULL, NULL, TRUE)"
    )
    collapse_medata_contracts(connection)
    assert connection.execute(
        "SELECT department, final_value, truncated FROM medata_contracts"
    ).fetchone() == ("Educación", None, True)


def test_d03_running_twice_is_idempotent() -> None:
    connection = _connection(
        "('4600-1', DATE '2022-01-10', 'Salud', 100, 0, 100, 30, 'Terminado', FALSE)"
    )
    collapse_medata_contracts(connection)
    collapse_medata_contracts(connection)
    assert connection.execute("SELECT count(*) FROM medata_contracts").fetchone() == (1,)


@pytest.fixture(scope="module")
def snapshot_connection() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    normalize_contract_execution(connection, SNAPSHOT / "medata_contract_execution.csv")
    collapse_medata_contracts(connection)
    return connection


def test_d03_snapshot_has_one_row_per_contract(
    snapshot_connection: duckdb.DuckDBPyConnection,
) -> None:
    assert snapshot_connection.execute(
        "SELECT count(*), count(DISTINCT contract_reference), sum(row_count) FROM medata_contracts"
    ).fetchone() == (2939, 2939, 25783)


def test_d03_snapshot_has_54_contracts_without_values_because_all_lines_are_truncated(
    snapshot_connection: duckdb.DuckDBPyConnection,
) -> None:
    assert snapshot_connection.execute(
        "SELECT count(*) FILTER (WHERE truncated), count(*) FILTER (WHERE final_value IS NULL)"
        " FROM medata_contracts"
    ).fetchone() == (54, 54)
