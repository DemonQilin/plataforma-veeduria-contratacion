"""Consolidación de contratos de SECOP II (R3, R4, D3 parte SECOP)."""

from datetime import datetime
from decimal import Decimal
from typing import Any

import duckdb

from veeduria.consolidate.canonical_contracts import consolidate_contracts

COLUMNS = [
    ("contract_id", "VARCHAR"),
    ("contract_reference", "VARCHAR"),
    ("procurement_process", "VARCHAR"),
    ("procurement_method", "VARCHAR"),
    ("direct_award", "BOOLEAN"),
    ("competitive", "BOOLEAN"),
    ("method_justification", "VARCHAR"),
    ("contract_type", "VARCHAR"),
    ("supplier_type", "VARCHAR"),
    ("signed_date", "TIMESTAMP"),
    ("start_date", "TIMESTAMP"),
    ("end_date", "TIMESTAMP"),
    ("contract_value", "DECIMAL(18, 2)"),
    ("added_days", "INTEGER"),
    ("contract_status", "VARCHAR"),
    ("main_category_code", "VARCHAR"),
    ("process_url", "VARCHAR"),
]


def _row(**overrides: Any) -> list[Any]:
    values: dict[str, Any] = {
        "contract_id": "CO1.PCCNTR.1",
        "contract_reference": "4600000001",
        "procurement_process": "CO1.BDOS.1",
        "procurement_method": "direct_award",
        "direct_award": True,
        "competitive": False,
        "method_justification": "Servicios profesionales",
        "contract_type": "service_contract",
        "supplier_type": "natural_person",
        "signed_date": datetime(2022, 3, 1, 8, 0),
        "start_date": datetime(2022, 3, 2),
        "end_date": datetime(2022, 12, 31),
        "contract_value": Decimal("1000.00"),
        "added_days": 0,
        "contract_status": "Modificado",
        "main_category_code": "V1.80111600",
        "process_url": "https://example.test/1",
    }
    values.update(overrides)
    return [values[name] for name, _ in COLUMNS]


def _consolidate(rows: list[list[Any]]) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    definition = ", ".join(f"{name} {kind}" for name, kind in COLUMNS)
    connection.execute(f"CREATE TABLE contracts ({definition})")
    placeholders = ", ".join("?" for _ in COLUMNS)
    connection.executemany(f"INSERT INTO contracts VALUES ({placeholders})", rows)
    consolidate_contracts(connection)
    return connection


def test_r03_versions_collapse_to_one_contract() -> None:
    connection = _consolidate(
        [
            _row(
                contract_id="A",
                signed_date=datetime(2022, 3, 1, 8, 0),
                contract_value=Decimal("1000.00"),
                end_date=datetime(2022, 12, 31),
                added_days=0,
                contract_status="Firmado",
            ),
            _row(
                contract_id="B",
                signed_date=datetime(2022, 6, 1, 9, 0),
                contract_value=Decimal("1500.00"),
                end_date=datetime(2023, 3, 31),
                added_days=90,
                contract_status="Modificado",
            ),
        ]
    )
    assert connection.execute(
        "SELECT contract_id, signed_date, initial_value, final_value, end_date,"
        " added_days, contract_status, version_count FROM canonical_contracts"
    ).fetchall() == [
        (
            "A",
            datetime(2022, 3, 1, 8, 0),
            Decimal("1000.00"),
            Decimal("1500.00"),
            datetime(2023, 3, 31),
            90,
            "Modificado",
            2,
        )
    ]


def test_r03_input_order_does_not_matter() -> None:
    later = _row(contract_id="B", signed_date=datetime(2022, 6, 1), contract_value=Decimal("2.00"))
    earlier = _row(
        contract_id="A", signed_date=datetime(2022, 3, 1), contract_value=Decimal("1.00")
    )
    query = "SELECT contract_id, initial_value, final_value FROM canonical_contracts"
    assert _consolidate([later, earlier]).execute(query).fetchall() == [
        ("A", Decimal("1.00"), Decimal("2.00"))
    ]


def test_r03_full_timestamp_breaks_same_day_tie() -> None:
    connection = _consolidate(
        [
            _row(contract_id="A", signed_date=datetime(2022, 3, 1, 15, 0)),
            _row(contract_id="B", signed_date=datetime(2022, 3, 1, 8, 0)),
        ]
    )
    assert connection.execute("SELECT contract_id FROM canonical_contracts").fetchall() == [("B",)]


def test_r03_identical_timestamps_break_by_contract_id() -> None:
    connection = _consolidate(
        [
            _row(contract_id="B", contract_value=Decimal("2.00")),
            _row(contract_id="A", contract_value=Decimal("1.00")),
        ]
    )
    assert connection.execute(
        "SELECT contract_id, initial_value, final_value FROM canonical_contracts"
    ).fetchall() == [("A", Decimal("1.00"), Decimal("2.00"))]


def test_r03_first_signed_process_wins_and_conflict_is_reported() -> None:
    connection = _consolidate(
        [
            _row(contract_id="A", procurement_process="P1", signed_date=datetime(2022, 3, 1)),
            _row(contract_id="B", procurement_process="P2", signed_date=datetime(2022, 6, 1)),
        ]
    )
    assert connection.execute("SELECT procurement_process FROM canonical_contracts").fetchall() == [
        ("P1",)
    ]
    assert connection.execute("SELECT rule, record_key, detail FROM quality_issues").fetchall() == [
        ("R3", "4600000001", "kept=P1; discarded=P2")
    ]


def test_r03_same_process_is_not_a_conflict() -> None:
    connection = _consolidate(
        [
            _row(contract_id="A", signed_date=datetime(2022, 3, 1)),
            _row(contract_id="B", signed_date=datetime(2022, 6, 1)),
        ]
    )
    assert connection.execute("SELECT count(*) FROM quality_issues").fetchone() == (0,)


def test_r04_unsigned_rows_are_excluded_and_reported() -> None:
    connection = _consolidate(
        [
            _row(contract_id="A", contract_reference="R1"),
            _row(contract_id="B", contract_reference="R2", signed_date=None),
            _row(contract_id="C", contract_reference="R1", signed_date=None),
        ]
    )
    assert connection.execute(
        "SELECT contract_reference, version_count FROM canonical_contracts"
    ).fetchall() == [("R1", 1)]
    assert connection.execute(
        "SELECT rule, record_key FROM quality_issues ORDER BY record_key"
    ).fetchall() == [("R4", "B"), ("R4", "C")]


def test_r03_consolidating_twice_does_not_duplicate_quality_issues() -> None:
    connection = _consolidate(
        [
            _row(contract_id="A", procurement_process="P1", signed_date=datetime(2022, 3, 1)),
            _row(contract_id="B", procurement_process="P2", signed_date=datetime(2022, 6, 1)),
            _row(contract_id="C", contract_reference="R2", signed_date=None),
        ]
    )
    consolidate_contracts(connection)
    assert connection.execute("SELECT count(*) FROM quality_issues").fetchone() == (2,)


def test_output_columns_and_order() -> None:
    connection = _consolidate([_row(contract_reference="B"), _row(contract_reference="A")])
    result = connection.execute("SELECT * FROM canonical_contracts")
    assert [column[0] for column in result.description] == [
        "contract_reference",
        "contract_id",
        "procurement_process",
        "procurement_method",
        "direct_award",
        "competitive",
        "method_justification",
        "contract_type",
        "supplier_type",
        "signed_date",
        "start_date",
        "end_date",
        "initial_value",
        "final_value",
        "added_days",
        "contract_status",
        "main_category_code",
        "process_url",
        "version_count",
    ]
    assert [row[0] for row in result.fetchall()] == ["A", "B"]
