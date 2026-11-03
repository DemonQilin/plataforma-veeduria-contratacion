"""Normalización de las adiciones de SECOP II (R6)."""

import csv
from datetime import datetime
from pathlib import Path

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.normalize.additions import normalize_additions

HEADER = ["id_contrato", "tipo", "fecharegistro"]
SNAPSHOT_ADDITIONS = REPO_ROOT / "data" / "snapshot" / "secop_additions.csv"


def _row(**overrides: str) -> list[str]:
    values = {
        "id_contrato": "CO1.PCCNTR.1",
        "tipo": "Adicion en el valor",
        "fecharegistro": "2022-03-01T10:30:00.123",
    }
    values.update(overrides)
    return [values[column] for column in HEADER]


def _normalize(tmp_path: Path, rows: list[list[str]]) -> duckdb.DuckDBPyConnection:
    path = tmp_path / "secop_additions.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)
    connection = duckdb.connect()
    normalize_additions(connection, path)
    return connection


def test_r06_addition_type_variants_and_flag(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_contrato="A", tipo="Adicion en el valor"),
            _row(id_contrato="B", tipo="  ADICIÓN EN EL VALOR "),
            _row(id_contrato="C", tipo="Modificacion General"),
            _row(id_contrato="D", tipo="Conclusion"),
            _row(id_contrato="E", tipo="Reactivación"),
            _row(id_contrato="F", tipo="Reactivacion"),
            _row(id_contrato="G", tipo="Suspensión"),
            _row(id_contrato="H", tipo="Cesion"),
            _row(id_contrato="I", tipo="No definido"),
        ],
    )
    assert connection.execute(
        "SELECT contract_id, addition_type, is_value_addition FROM additions ORDER BY contract_id"
    ).fetchall() == [
        ("A", "value_addition", True),
        ("B", "value_addition", True),
        ("C", "general_modification", False),
        ("D", "closure", False),
        ("E", "reactivation", False),
        ("F", "reactivation", False),
        ("G", "suspension", False),
        ("H", "assignment", False),
        ("I", "undefined", False),
    ]


def test_r06_unknown_or_empty_type_is_other_and_not_a_value_addition(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [_row(id_contrato="A", tipo="Prórroga"), _row(id_contrato="B", tipo="")],
    )
    assert connection.execute(
        "SELECT contract_id, addition_type, is_value_addition FROM additions ORDER BY contract_id"
    ).fetchall() == [("A", "other", False), ("B", "other", False)]


def test_registered_date_keeps_time_and_nulls(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_contrato="A"),
            _row(id_contrato="B", fecharegistro=""),
            _row(id_contrato="C", fecharegistro="no es una fecha"),
        ],
    )
    assert connection.execute(
        "SELECT contract_id, registered_date FROM additions ORDER BY contract_id"
    ).fetchall() == [("A", datetime(2022, 3, 1, 10, 30, 0, 123000)), ("B", None), ("C", None)]


def test_identical_rows_are_not_deduplicated_here(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(), _row()])
    assert connection.execute("SELECT count(*) FROM additions").fetchone() == (2,)


def test_output_columns_and_source_text(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(id_contrato="CO1.PCCNTR.7")])
    result = connection.execute("SELECT * FROM additions")
    assert [description[0] for description in result.description] == [
        "contract_id",
        "addition_type",
        "is_value_addition",
        "registered_date",
    ]
    assert connection.execute("SELECT contract_id FROM additions").fetchall() == [("CO1.PCCNTR.7",)]


@pytest.fixture(scope="module")
def real_additions() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    normalize_additions(connection, SNAPSHOT_ADDITIONS)
    return connection


def test_golden_every_addition_is_classified(real_additions: duckdb.DuckDBPyConnection) -> None:
    # I5: solo «Adicion en el valor» cuenta como adición en el valor (642 filas); la conciliación
    # con MEData (R15) lo confirma o lo corrige (docs/bitacora.md).
    assert real_additions.execute(
        "SELECT count(*), count(DISTINCT contract_id),"
        " count(*) FILTER (WHERE is_value_addition),"
        " count(*) FILTER (WHERE addition_type = 'other'),"
        " count(*) FILTER (WHERE registered_date IS NULL) FROM additions"
    ).fetchone() == (15884, 5990, 642, 0, 0)
