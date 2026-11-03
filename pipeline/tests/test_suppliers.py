"""Normalización de los proveedores de SECOP II (R14)."""

import csv
from pathlib import Path

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.normalize.suppliers import normalize_suppliers, strip_check_digit

HEADER = ["id_contrato", "documento_proveedor", "proveedor_adjudicado"]
SNAPSHOT_SUPPLIERS = REPO_ROOT / "data" / "snapshot" / "secop_contracts_suppliers.csv"


def _row(**overrides: str) -> list[str]:
    values = {
        "id_contrato": "CO1.PCCNTR.1",
        "documento_proveedor": "890900081",
        "proveedor_adjudicado": "AUTOLARTE S.A",
    }
    values.update(overrides)
    return [values[column] for column in HEADER]


def _normalize(tmp_path: Path, rows: list[list[str]]) -> duckdb.DuckDBPyConnection:
    path = tmp_path / "secop_contracts_suppliers.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)
    connection = duckdb.connect()
    normalize_suppliers(connection, path)
    return connection


def test_r14_check_digit_is_removed_when_it_matches() -> None:
    # 8909000818: el 8 final es el dígito de verificación de 890900081 según la DIAN.
    assert strip_check_digit("8909000818") == "890900081"


def test_r14_ten_digits_with_a_wrong_check_digit_are_kept() -> None:
    assert strip_check_digit("8909000811") == "8909000811"


def test_r14_nine_digits_are_unchanged() -> None:
    assert strip_check_digit("890900081") == "890900081"


def test_r14_same_supplier_with_and_without_check_digit_gets_one_id(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_contrato="A", documento_proveedor="890900081"),
            _row(id_contrato="B", documento_proveedor="8909000818"),
        ],
    )
    assert connection.execute(
        "SELECT contract_id, supplier_id FROM suppliers ORDER BY contract_id"
    ).fetchall() == [("A", "890900081"), ("B", "890900081")]


def test_r14_name_is_the_most_frequent_trimmed_one(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_contrato="A", proveedor_adjudicado="ESU"),
            _row(id_contrato="B", proveedor_adjudicado="  EMPRESA PARA LA SEGURIDAD - ESU "),
            _row(id_contrato="C", proveedor_adjudicado="EMPRESA PARA LA SEGURIDAD - ESU"),
        ],
    )
    assert connection.execute("SELECT DISTINCT supplier_name FROM suppliers").fetchall() == [
        ("EMPRESA PARA LA SEGURIDAD - ESU",)
    ]


def test_r14_name_tie_goes_to_the_first_in_alphabetical_order(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_contrato="A", proveedor_adjudicado="GOLD SYS LTDA"),
            _row(id_contrato="B", proveedor_adjudicado="GOLD SYS"),
        ],
    )
    assert connection.execute("SELECT DISTINCT supplier_name FROM suppliers").fetchall() == [
        ("GOLD SYS",)
    ]


def test_r14_empty_name_is_null_and_never_wins_over_a_name(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_contrato="A", documento_proveedor="900111222", proveedor_adjudicado=""),
            _row(id_contrato="B", documento_proveedor="900111222", proveedor_adjudicado=""),
            _row(id_contrato="C", documento_proveedor="900111222", proveedor_adjudicado="EMPRESA"),
            _row(id_contrato="D", documento_proveedor="900333444", proveedor_adjudicado=""),
        ],
    )
    assert connection.execute(
        "SELECT contract_id, supplier_name FROM suppliers ORDER BY contract_id"
    ).fetchall() == [("A", "EMPRESA"), ("B", "EMPRESA"), ("C", "EMPRESA"), ("D", None)]


def test_identical_rows_are_not_deduplicated_here(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(), _row()])
    assert connection.execute("SELECT count(*) FROM suppliers").fetchone() == (2,)


def test_output_columns(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(id_contrato="CO1.PCCNTR.7")])
    result = connection.execute("SELECT * FROM suppliers")
    assert [description[0] for description in result.description] == [
        "contract_id",
        "supplier_id",
        "supplier_name",
    ]
    assert connection.execute("SELECT contract_id FROM suppliers").fetchall() == [("CO1.PCCNTR.7",)]


@pytest.fixture(scope="module")
def real_suppliers() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    normalize_suppliers(connection, SNAPSHOT_SUPPLIERS)
    return connection


def test_golden_suppliers_one_row_per_contract_and_one_name_per_id(
    real_suppliers: duckdb.DuckDBPyConnection,
) -> None:
    # 4.459 filas de 4.459 contratos; 975 documentos distintos se vuelven 972 NIT: 23 pierden el
    # dígito de verificación (3 se fusionan con su versión de 9 dígitos) y uno queda con 10.
    assert real_suppliers.execute(
        "SELECT count(*), count(DISTINCT contract_id), count(DISTINCT supplier_id),"
        " count(*) FILTER (WHERE length(supplier_id) = 10),"
        " count(*) FILTER (WHERE supplier_name IS NULL) FROM suppliers"
    ).fetchone() == (4459, 4459, 972, 1, 0)
    assert real_suppliers.execute(
        "SELECT count(*) FROM (SELECT supplier_id FROM suppliers GROUP BY 1"
        " HAVING count(DISTINCT supplier_name) > 1)"
    ).fetchone() == (0,)
