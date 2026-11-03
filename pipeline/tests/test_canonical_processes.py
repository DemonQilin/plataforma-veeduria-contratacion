"""Consolidación de procesos de SECOP II (R5)."""

from datetime import datetime
from decimal import Decimal
from typing import Any

import duckdb

from veeduria.consolidate.canonical_processes import consolidate_processes

COLUMNS = [
    ("procurement_process", "VARCHAR"),
    ("process_id", "VARCHAR"),
    ("procurement_method", "VARCHAR"),
    ("direct_award", "BOOLEAN"),
    ("competitive", "BOOLEAN"),
    ("contract_type", "VARCHAR"),
    ("published_date", "TIMESTAMP"),
    ("response_deadline", "TIMESTAMP"),
    ("base_price", "DECIMAL(18, 2)"),
    ("awarded_value", "DECIMAL(18, 2)"),
    ("response_count", "INTEGER"),
    ("unique_suppliers", "INTEGER"),
    ("awarded", "BOOLEAN"),
    ("department", "VARCHAR"),
]


def _row(**overrides: Any) -> list[Any]:
    values: dict[str, Any] = {
        "procurement_process": "CO1.BDOS.1",
        "process_id": "CO1.REQ.1",
        "procurement_method": "public_tender",
        "direct_award": False,
        "competitive": True,
        "contract_type": "works",
        "published_date": datetime(2022, 3, 1),
        "response_deadline": datetime(2022, 3, 15),
        "base_price": Decimal("1000.00"),
        "awarded_value": Decimal("900.00"),
        "response_count": 3,
        "unique_suppliers": 2,
        "awarded": True,
        "department": "SECRETARÍA DE INFRAESTRUCTURA FÍSICA",
    }
    values.update(overrides)
    return [values[name] for name, _ in COLUMNS]


def _consolidate(rows: list[list[Any]]) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    definition = ", ".join(f"{name} {kind}" for name, kind in COLUMNS)
    connection.execute(f"CREATE TABLE procurement_processes ({definition})")
    placeholders = ", ".join("?" for _ in COLUMNS)
    connection.executemany(f"INSERT INTO procurement_processes VALUES ({placeholders})", rows)
    consolidate_processes(connection)
    return connection


def test_r05_rows_of_one_portfolio_collapse_to_one_process() -> None:
    connection = _consolidate(
        [_row(process_id="A"), _row(process_id="A"), _row(procurement_process="CO1.BDOS.2")]
    )
    assert connection.execute(
        "SELECT procurement_process, row_count FROM canonical_processes"
    ).fetchall() == [("CO1.BDOS.1", 2), ("CO1.BDOS.2", 1)]


def test_r05_bidder_counts_are_the_maximum_across_rows() -> None:
    connection = _consolidate(
        [
            _row(response_count=1, unique_suppliers=1),
            _row(response_count=5, unique_suppliers=0),
            _row(response_count=None, unique_suppliers=None),
        ]
    )
    assert connection.execute(
        "SELECT response_count, unique_suppliers FROM canonical_processes"
    ).fetchall() == [(5, 1)]


def test_r05_awarded_if_any_row_is_awarded() -> None:
    mixed = _consolidate([_row(awarded=False), _row(awarded=True), _row(awarded=None)])
    assert mixed.execute("SELECT awarded FROM canonical_processes").fetchall() == [(True,)]


def test_r05_not_awarded_when_no_row_is_awarded() -> None:
    connection = _consolidate([_row(awarded=False), _row(awarded=None)])
    assert connection.execute("SELECT awarded FROM canonical_processes").fetchall() == [(False,)]


def test_r05_unknown_awarded_stays_unknown() -> None:
    connection = _consolidate([_row(awarded=None), _row(awarded=None)])
    assert connection.execute("SELECT awarded FROM canonical_processes").fetchall() == [(None,)]


def test_r05_descriptive_fields_come_from_the_first_published_row() -> None:
    connection = _consolidate(
        [
            _row(process_id="B", published_date=datetime(2022, 5, 1), department="OTRA SECRETARÍA"),
            _row(
                process_id="A",
                published_date=datetime(2022, 3, 1),
                department="SECRETARÍA DE INFRAESTRUCTURA FÍSICA",
            ),
        ]
    )
    assert connection.execute(
        "SELECT process_id, published_date, department FROM canonical_processes"
    ).fetchall() == [("A", datetime(2022, 3, 1), "SECRETARÍA DE INFRAESTRUCTURA FÍSICA")]


def test_r05_values_are_the_maximum_and_repeated_rows_are_not_summed() -> None:
    connection = _consolidate(
        [
            _row(base_price=Decimal("1000.00"), awarded_value=Decimal("900.00")),
            _row(base_price=Decimal("1000.00"), awarded_value=Decimal("900.00")),
            _row(base_price=Decimal("400.00"), awarded_value=None),
        ]
    )
    assert connection.execute(
        "SELECT base_price, awarded_value FROM canonical_processes"
    ).fetchall() == [(Decimal("1000.00"), Decimal("900.00"))]


def test_r05_rows_without_portfolio_are_left_out() -> None:
    connection = _consolidate([_row(procurement_process=None), _row()])
    assert connection.execute("SELECT procurement_process FROM canonical_processes").fetchall() == [
        ("CO1.BDOS.1",)
    ]


def test_output_columns_and_order() -> None:
    connection = _consolidate([_row(procurement_process="B"), _row(procurement_process="A")])
    result = connection.execute("SELECT * FROM canonical_processes")
    assert [column[0] for column in result.description] == [
        "procurement_process",
        "process_id",
        "procurement_method",
        "direct_award",
        "competitive",
        "contract_type",
        "published_date",
        "response_deadline",
        "base_price",
        "awarded_value",
        "response_count",
        "unique_suppliers",
        "awarded",
        "department",
        "row_count",
    ]
    assert [row[0] for row in result.fetchall()] == ["A", "B"]
