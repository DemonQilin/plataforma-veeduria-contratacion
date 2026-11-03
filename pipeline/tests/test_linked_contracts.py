"""Cruce de contratos con procesos y MEData (R7, R8, D3; ADR 0030)."""

import duckdb
import pytest

from veeduria.link.linked_contracts import link_contracts


def _connection(
    contracts: str = "", processes: str = "", medata: str = ""
) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE canonical_contracts (contract_reference VARCHAR,"
        " procurement_process VARCHAR, contract_type VARCHAR, final_value DECIMAL(18, 2))"
    )
    connection.execute(
        "CREATE TABLE canonical_processes (procurement_process VARCHAR, department VARCHAR,"
        " response_count INTEGER, unique_suppliers INTEGER, awarded BOOLEAN,"
        " base_price DECIMAL(18, 2), awarded_value DECIMAL(18, 2), published_date TIMESTAMP,"
        " response_deadline TIMESTAMP)"
    )
    connection.execute(
        "CREATE TABLE medata_contracts (contract_reference VARCHAR, department VARCHAR,"
        " total_addition_value DECIMAL(18, 2), final_value DECIMAL(18, 2))"
    )
    for table, rows in (
        ("canonical_contracts", contracts),
        ("canonical_processes", processes),
        ("medata_contracts", medata),
    ):
        if rows:
            connection.execute(f"INSERT INTO {table} VALUES {rows}")
    return connection


def _department(connection: duckdb.DuckDBPyConnection, reference: str) -> tuple[str, str]:
    row = connection.execute(
        "SELECT department, department_source FROM linked_contracts WHERE contract_reference = ?",
        [reference],
    ).fetchone()
    assert row is not None
    return row


def test_r08_medata_department_wins_over_the_secop_unit() -> None:
    connection = _connection(
        contracts="('C1', 'P1', 'service_contract', 100)",
        processes="('P1', 'Secretaria Educación', 3, 2, TRUE, 90, 80, NULL, NULL)",
        medata="('C1', 'Salud', 0, 100)",
    )
    link_contracts(connection)
    assert _department(connection, "C1") == ("health", "medata")


def test_r08_secop_unit_is_used_when_the_contract_is_not_in_medata() -> None:
    connection = _connection(
        contracts="('C1', 'P1', 'service_contract', 100)",
        processes="('P1', 'Secretaria Educación', 3, 2, TRUE, 90, 80, NULL, NULL)",
    )
    link_contracts(connection)
    assert _department(connection, "C1") == ("education", "secop")


def test_r08_unmapped_medata_text_falls_back_to_the_secop_unit() -> None:
    connection = _connection(
        contracts="('C1', 'P1', 'service_contract', 100)",
        processes="('P1', 'Secretaria Educación', 3, 2, TRUE, 90, 80, NULL, NULL)",
        medata="('C1', 'Texto desconocido', 0, 100)",
    )
    link_contracts(connection)
    assert _department(connection, "C1") == ("education", "secop")


def test_r08_contract_without_any_department_is_unassigned() -> None:
    connection = _connection(contracts="('C1', NULL, 'service_contract', 100)")
    link_contracts(connection)
    assert _department(connection, "C1") == ("unassigned", "unassigned")


def test_r08_reports_unassigned_contracts_and_unmapped_texts() -> None:
    connection = _connection(
        contracts="('C1', NULL, 'service_contract', 100), ('C2', 'P2', 'service_contract', 5)",
        processes="('P2', 'Texto desconocido', NULL, NULL, NULL, NULL, NULL, NULL, NULL)",
    )
    link_contracts(connection)
    assert connection.execute(
        "SELECT rule, record_key, detail FROM quality_issues ORDER BY detail, record_key"
    ).fetchall() == [
        ("R8", "C1", "reason=no_department"),
        ("R8", "C2", "reason=no_department"),
        ("R8", "Texto desconocido", "reason=unmapped_department_text"),
    ]


def test_d03_medata_final_value_replaces_the_secop_value() -> None:
    connection = _connection(
        contracts="('C1', NULL, 'service_contract', 100)",
        medata="('C1', 'Salud', 30, 130)",
    )
    link_contracts(connection)
    assert connection.execute(
        "SELECT final_value, total_addition_value, in_medata FROM linked_contracts"
    ).fetchone() == (130, 30, True)


def test_d03_secop_final_value_stays_without_medata_or_with_truncated_medata() -> None:
    connection = _connection(
        contracts="('C1', NULL, 'service_contract', 100), ('C2', NULL, 'service_contract', 50)",
        medata="('C2', 'Salud', NULL, NULL)",
    )
    link_contracts(connection)
    assert connection.execute(
        "SELECT contract_reference, final_value, total_addition_value, in_medata"
        " FROM linked_contracts ORDER BY contract_reference"
    ).fetchall() == [("C1", 100, None, False), ("C2", 50, None, True)]


def test_r07_public_credit_stays_in_the_table_but_is_not_value_eligible() -> None:
    connection = _connection(
        contracts="('C1', NULL, 'public_credit', 500), ('C2', NULL, 'works', 5)",
    )
    link_contracts(connection)
    assert connection.execute(
        "SELECT contract_reference, is_value_eligible FROM linked_contracts"
        " ORDER BY contract_reference"
    ).fetchall() == [("C1", False), ("C2", True)]


def test_link_keeps_one_row_per_contract_even_if_the_process_is_missing() -> None:
    connection = _connection(
        contracts="('C1', 'P-missing', 'works', 5)",
        processes="('P1', 'Salud', 1, 1, TRUE, 1, 1, NULL, NULL)",
    )
    link_contracts(connection)
    assert connection.execute(
        "SELECT count(*), count(response_count) FROM linked_contracts"
    ).fetchone() == (1, 0)


def test_link_running_twice_does_not_duplicate_the_quality_issues() -> None:
    connection = _connection(contracts="('C1', NULL, 'works', 5)")
    link_contracts(connection)
    link_contracts(connection)
    assert connection.execute("SELECT count(*) FROM quality_issues").fetchone() == (1,)


@pytest.mark.parametrize("column", ["department", "department_source", "is_value_eligible"])
def test_link_adds_the_derived_columns(column: str) -> None:
    connection = _connection(contracts="('C1', NULL, 'works', 5)")
    link_contracts(connection)
    names = {row[0] for row in connection.execute("DESCRIBE linked_contracts").fetchall()}
    assert column in names
