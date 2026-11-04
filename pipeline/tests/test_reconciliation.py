"""Conciliación SECOP–MEData por mes (R15; ADR 0031)."""

from decimal import Decimal

import duckdb

from veeduria.link.reconciliation import reconcile_sources


def _connection(contracts: str, medata: str) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE canonical_contracts (contract_reference VARCHAR, signed_date TIMESTAMP)"
    )
    connection.execute(
        "CREATE TABLE medata_contracts (contract_reference VARCHAR, signed_date DATE)"
    )
    connection.execute(f"INSERT INTO canonical_contracts VALUES {contracts}")
    connection.execute(f"INSERT INTO medata_contracts VALUES {medata}")
    return connection


def _rows(connection: duckdb.DuckDBPyConnection) -> list[tuple]:
    return connection.execute(
        "SELECT month::VARCHAR, secop_count, medata_count, shared_count, union_count,"
        " shared_share, secop_coverage, medata_coverage, below_threshold"
        " FROM reconciliation ORDER BY month"
    ).fetchall()


def test_r15_counts_each_source_and_the_shared_contracts_per_month() -> None:
    connection = _connection(
        contracts="('A', '2022-01-10'), ('B', '2022-01-20'), ('C', '2022-01-25')",
        medata="('A', '2022-01-12'), ('D', '2022-01-30')",
    )
    reconcile_sources(connection)
    assert _rows(connection) == [
        (
            "2022-01-01",
            3,
            2,
            1,
            4,
            Decimal("0.2500"),
            Decimal("0.3333"),
            Decimal("0.5000"),
            True,
        )
    ]


def test_r15_a_shared_contract_counts_in_the_month_of_its_secop_signing_date() -> None:
    connection = _connection(
        contracts="('A', '2022-01-31'), ('B', '2022-02-03')",
        medata="('E', '2022-01-05'), ('A', '2022-02-02'), ('B', '2022-02-03'), ('C', '2022-02-04')",
    )
    reconcile_sources(connection)
    assert [(r[0], r[3], r[4]) for r in _rows(connection)] == [
        ("2022-01-01", 1, 2),
        ("2022-02-01", 1, 2),
    ]


def test_r15_a_month_at_or_above_the_threshold_is_not_flagged() -> None:
    connection = _connection(
        contracts="('A', '2022-03-01'), ('B', '2022-03-02'), ('C', '2022-03-03'), "
        "('D', '2022-03-04'), ('E', '2022-03-05')",
        medata="('A', '2022-03-01'), ('B', '2022-03-02'), ('C', '2022-03-03'), ('D', '2022-03-04')",
    )
    reconcile_sources(connection)
    (row,) = _rows(connection)
    assert (row[3], row[4], row[5], row[8]) == (4, 5, Decimal("0.8000"), False)


def test_r15_only_covers_the_months_where_medata_has_contracts() -> None:
    connection = _connection(
        contracts="('A', '2021-12-15'), ('B', '2022-01-10'), ('C', '2022-03-10'), "
        "('D', '2023-08-10')",
        medata="('B', '2022-01-10'), ('C', '2022-03-10')",
    )
    reconcile_sources(connection)
    assert [r[0] for r in _rows(connection)] == ["2022-01-01", "2022-02-01", "2022-03-01"]


def test_r15_a_month_without_contracts_in_the_period_has_zero_counts_and_no_share() -> None:
    connection = _connection(
        contracts="('B', '2022-01-10'), ('C', '2022-03-10')",
        medata="('B', '2022-01-10'), ('C', '2022-03-10')",
    )
    reconcile_sources(connection)
    assert _rows(connection)[1] == (
        "2022-02-01",
        0,
        0,
        0,
        0,
        None,
        None,
        None,
        False,
    )


def test_r15_is_deterministic() -> None:
    args = {
        "contracts": "('A', '2022-01-10'), ('B', '2022-02-20')",
        "medata": "('A', '2022-01-12'), ('C', '2022-02-25')",
    }
    first, second = _connection(**args), _connection(**args)
    reconcile_sources(first)
    reconcile_sources(second)
    assert _rows(first) == _rows(second)
