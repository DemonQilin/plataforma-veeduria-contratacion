"""Normalización de Contratos de SECOP II (R1, R2, R6)."""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.normalize.contracts import normalize_contracts

ENTITY = "DISTRITO ESPECIAL DE CIENCIA TECNOLOGIA E INNOVACION DE MEDELLIN"
HEADER = [
    "id_contrato",
    "referencia_del_contrato",
    "proceso_de_compra",
    "nombre_entidad",
    "modalidad_de_contratacion",
    "justificacion_modalidad_de",
    "tipo_de_contrato",
    "fecha_de_firma",
    "fecha_de_inicio_del_contrato",
    "fecha_de_fin_del_contrato",
    "valor_del_contrato",
    "dias_adicionados",
    "estado_contrato",
    "tipodocproveedor",
    "codigo_de_categoria_principal",
    "urlproceso",
]
SNAPSHOT_CONTRACTS = REPO_ROOT / "data" / "snapshot" / "secop_contracts.csv"


def _row(**overrides: str) -> list[str]:
    values = {
        "id_contrato": "CO1.PCCNTR.1",
        "referencia_del_contrato": "0001",
        "proceso_de_compra": "CO1.BDOS.1",
        "nombre_entidad": ENTITY,
        "modalidad_de_contratacion": "Contratación directa",
        "justificacion_modalidad_de": "Servicios profesionales y apoyo a la gestión",
        "tipo_de_contrato": "Prestación de servicios",
        "fecha_de_firma": "2022-01-06T14:47:15.257",
        "fecha_de_inicio_del_contrato": "2022-01-10T00:00:00.000",
        "fecha_de_fin_del_contrato": "2022-12-31T23:59:00.000",
        "valor_del_contrato": "1000",
        "dias_adicionados": "0",
        "estado_contrato": "Cerrado",
        "tipodocproveedor": "NIT",
        "codigo_de_categoria_principal": "UNSPECIFIED",
        "urlproceso": "https://example.test/proceso",
    }
    values.update(overrides)
    return [values[column] for column in HEADER]


def _normalize(tmp_path: Path, rows: list[list[str]]) -> duckdb.DuckDBPyConnection:
    path = tmp_path / "secop_contracts.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)
    connection = duckdb.connect()
    normalize_contracts(connection, path)
    return connection


def test_r01_other_entities_are_left_out(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_contrato="A"),
            _row(id_contrato="B", nombre_entidad="CONCEJO DE MEDELLIN"),
            _row(id_contrato="C", nombre_entidad=ENTITY.lower()),
        ],
    )
    assert connection.execute("SELECT contract_id FROM contracts").fetchall() == [("A",)]


def test_r02_signed_before_2022_is_left_out(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_contrato="old", fecha_de_firma="2021-12-31T23:59:59.000"),
            _row(id_contrato="first", fecha_de_firma="2022-01-01T00:00:00.000"),
        ],
    )
    assert connection.execute("SELECT contract_id FROM contracts").fetchall() == [("first",)]


def test_r03_reference_drops_surrounding_spaces_and_nbsp(tmp_path: Path) -> None:
    """ADR 0046: la llave de cruce con MEData no lleva espacios en los extremos."""
    connection = _normalize(
        tmp_path,
        [
            _row(id_contrato="A", referencia_del_contrato="4600000001 "),
            _row(id_contrato="B", referencia_del_contrato=" 4600000002 "),
            _row(id_contrato="C", referencia_del_contrato="4600000003 de 2022"),
        ],
    )
    assert connection.execute(
        "SELECT contract_reference FROM contracts ORDER BY contract_id"
    ).fetchall() == [("4600000001",), ("4600000002",), ("4600000003 de 2022",)]


def test_r02_unsigned_contract_is_kept_for_r04(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(fecha_de_firma="")])
    assert connection.execute("SELECT signed_date FROM contracts").fetchall() == [(None,)]


def test_types_keep_time_decimals_and_nulls(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(
                valor_del_contrato="558039804.44",
                dias_adicionados="15",
                fecha_de_inicio_del_contrato="",
            )
        ],
    )
    assert connection.execute(
        "SELECT signed_date, start_date, end_date, contract_value, added_days FROM contracts"
    ).fetchall() == [
        (
            datetime(2022, 1, 6, 14, 47, 15, 257000),
            None,
            datetime(2022, 12, 31, 23, 59),
            Decimal("558039804.44"),
            15,
        )
    ]


def test_r06_method_variants_and_flags(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_contrato="A", modalidad_de_contratacion="Contratación Directa (con ofertas)"),
            _row(id_contrato="B", modalidad_de_contratacion="Mínima cuantía"),
            _row(id_contrato="C", modalidad_de_contratacion="Modalidad Inventada"),
        ],
    )
    assert connection.execute(
        "SELECT contract_id, procurement_method, direct_award, competitive"
        " FROM contracts ORDER BY contract_id"
    ).fetchall() == [
        ("A", "direct_award", True, False),
        ("B", "minimum_amount", False, True),
        ("C", "other", False, False),
    ]


def test_r06_interadministrative_justification_wins_over_raw_type(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(
                id_contrato="A",
                tipo_de_contrato="Otro",
                justificacion_modalidad_de="Contratos o convenios Interadministrativos (con valor)",
            ),
            _row(id_contrato="B", tipo_de_contrato="Obra"),
            _row(id_contrato="C", tipo_de_contrato="Algo nuevo"),
        ],
    )
    assert connection.execute(
        "SELECT contract_id, contract_type FROM contracts ORDER BY contract_id"
    ).fetchall() == [("A", "interadministrative"), ("B", "works"), ("C", "other")]


def test_r06_supplier_type(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_contrato="A", tipodocproveedor="NIT"),
            _row(id_contrato="B", tipodocproveedor="Cédula de Ciudadanía"),
            _row(id_contrato="C", tipodocproveedor="No Definido"),
            _row(id_contrato="D", tipodocproveedor=""),
        ],
    )
    assert connection.execute(
        "SELECT contract_id, supplier_type FROM contracts ORDER BY contract_id"
    ).fetchall() == [
        ("A", "legal_entity"),
        ("B", "natural_person"),
        ("C", "undefined"),
        ("D", "undefined"),
    ]


def test_identical_rows_are_not_deduplicated_here(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(id_contrato="A"), _row(id_contrato="B")])
    assert connection.execute("SELECT count(*) FROM contracts").fetchone() == (2,)


def test_output_columns_and_source_text(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row()])
    result = connection.execute("SELECT * FROM contracts")
    assert [description[0] for description in result.description] == [
        "contract_id",
        "contract_reference",
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
        "contract_value",
        "added_days",
        "contract_status",
        "main_category_code",
        "process_url",
    ]
    assert connection.execute(
        "SELECT contract_reference, procurement_process, contract_status FROM contracts"
    ).fetchall() == [("0001", "CO1.BDOS.1", "Cerrado")]


@pytest.fixture(scope="module")
def real_contracts() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    normalize_contracts(connection, SNAPSHOT_CONTRACTS)
    return connection


def test_golden_every_contract_is_classified(real_contracts: duckdb.DuckDBPyConnection) -> None:
    assert real_contracts.execute(
        "SELECT count(*), count(*) FILTER (WHERE procurement_method = 'other'),"
        " count(*) FILTER (WHERE contract_type = 'interadministrative'),"
        " count(*) FILTER (WHERE supplier_type = 'legal_entity'),"
        " count(*) FILTER (WHERE supplier_type = 'natural_person'),"
        " count(*) FILTER (WHERE supplier_type = 'undefined'),"
        " count(*) FILTER (WHERE signed_date IS NULL) FROM contracts"
    ).fetchone() == (7468, 0, 1446, 4508, 2875, 85, 0)


def test_golden_direct_awards_signed_in_january_2022(
    real_contracts: duckdb.DuckDBPyConnection,
) -> None:
    assert real_contracts.execute(
        "SELECT count(DISTINCT contract_reference) FROM contracts"
        " WHERE direct_award AND signed_date >= '2022-01-01' AND signed_date < '2022-02-01'"
    ).fetchone() == (723,)
