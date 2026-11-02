"""Normalización de Procesos de Contratación de SECOP II (R1, R6)."""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.normalize.procurement_processes import normalize_procurement_processes

ENTITY = "DISTRITO ESPECIAL DE CIENCIA TECNOLOGIA E INNOVACION DE MEDELLIN"
HEADER = [
    "id_del_portafolio",
    "id_del_proceso",
    "nit_entidad",
    "entidad",
    "modalidad_de_contratacion",
    "tipo_de_contrato",
    "fecha_de_publicacion_del",
    "fecha_de_recepcion_de",
    "precio_base",
    "valor_total_adjudicacion",
    "respuestas_al_procedimiento",
    "proveedores_unicos_con",
    "adjudicado",
    "nombre_de_la_unidad_de",
]
SNAPSHOT_PROCESSES = REPO_ROOT / "data" / "snapshot" / "secop_procurement_processes.csv"


def _row(**overrides: str) -> list[str]:
    values = {
        "id_del_portafolio": "CO1.BDOS.1",
        "id_del_proceso": "CO1.REQ.1",
        "nit_entidad": "890905211",
        "entidad": ENTITY,
        "modalidad_de_contratacion": "Licitación pública",
        "tipo_de_contrato": "Obra",
        "fecha_de_publicacion_del": "2022-03-01T00:00:00.000",
        "fecha_de_recepcion_de": "2022-03-15T00:00:00.000",
        "precio_base": "1000",
        "valor_total_adjudicacion": "900",
        "respuestas_al_procedimiento": "3",
        "proveedores_unicos_con": "2",
        "adjudicado": "Si",
        "nombre_de_la_unidad_de": "SECRETARÍA DE INFRAESTRUCTURA FÍSICA",
    }
    values.update(overrides)
    return [values[column] for column in HEADER]


def _normalize(tmp_path: Path, rows: list[list[str]]) -> duckdb.DuckDBPyConnection:
    path = tmp_path / "secop_procurement_processes.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)
    connection = duckdb.connect()
    normalize_procurement_processes(connection, path)
    return connection


def test_r01_other_entities_are_left_out(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_del_proceso="A"),
            _row(id_del_proceso="B", entidad="CONCEJO DE MEDELLIN"),
            _row(id_del_proceso="C", entidad=ENTITY.lower()),
        ],
    )
    assert connection.execute("SELECT process_id FROM procurement_processes").fetchall() == [("A",)]


def test_r06_method_variants_and_flags(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(
                id_del_proceso="A", modalidad_de_contratacion="Contratación Directa (con ofertas)"
            ),
            _row(id_del_proceso="B", modalidad_de_contratacion="Mínima cuantía"),
            _row(
                id_del_proceso="C",
                modalidad_de_contratacion="Solicitud de información a los Proveedores",
            ),
            _row(id_del_proceso="D", modalidad_de_contratacion="Subasta de prueba"),
            _row(id_del_proceso="E", modalidad_de_contratacion="Modalidad Inventada"),
        ],
    )
    assert connection.execute(
        "SELECT process_id, procurement_method, direct_award, competitive"
        " FROM procurement_processes ORDER BY process_id"
    ).fetchall() == [
        ("A", "direct_award", True, False),
        ("B", "minimum_amount", False, True),
        ("C", "other", False, False),
        ("D", "other", False, False),
        ("E", "other", False, False),
    ]


def test_r06_contract_type(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_del_proceso="A", tipo_de_contrato="Obra"),
            _row(id_del_proceso="B", tipo_de_contrato="Prestación de servicios"),
            _row(id_del_proceso="C", tipo_de_contrato="Operaciones de Crédito Público"),
            _row(id_del_proceso="D", tipo_de_contrato="No Especificado"),
            _row(id_del_proceso="E", tipo_de_contrato="Algo nuevo"),
        ],
    )
    assert connection.execute(
        "SELECT process_id, contract_type FROM procurement_processes ORDER BY process_id"
    ).fetchall() == [
        ("A", "works"),
        ("B", "service_contract"),
        ("C", "public_credit"),
        ("D", "other"),
        ("E", "other"),
    ]


def test_types_keep_time_decimals_and_nulls(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(
                id_del_proceso="A",
                precio_base="558039804.44",
                valor_total_adjudicacion="0",
                fecha_de_recepcion_de="",
            ),
            _row(id_del_proceso="B", fecha_de_publicacion_del="", precio_base="no es un número"),
        ],
    )
    assert connection.execute(
        "SELECT process_id, published_date, response_deadline, base_price, awarded_value,"
        " response_count, unique_suppliers FROM procurement_processes ORDER BY process_id"
    ).fetchall() == [
        ("A", datetime(2022, 3, 1), None, Decimal("558039804.44"), Decimal("0.00"), 3, 2),
        ("B", None, datetime(2022, 3, 15), None, Decimal("900.00"), 3, 2),
    ]


def test_awarded_becomes_boolean(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_del_proceso="A", adjudicado="Si"),
            _row(id_del_proceso="B", adjudicado="No"),
            _row(id_del_proceso="C", adjudicado=""),
            _row(id_del_proceso="D", adjudicado="Quizá"),
        ],
    )
    assert connection.execute(
        "SELECT process_id, awarded FROM procurement_processes ORDER BY process_id"
    ).fetchall() == [("A", True), ("B", False), ("C", None), ("D", None)]


def test_no_date_filter_and_zero_values_are_kept(tmp_path: Path) -> None:
    connection = _normalize(
        tmp_path,
        [
            _row(id_del_proceso="old", fecha_de_publicacion_del="2017-05-02T00:00:00.000"),
            _row(
                id_del_proceso="zero",
                precio_base="0",
                respuestas_al_procedimiento="0",
                proveedores_unicos_con="0",
            ),
        ],
    )
    assert connection.execute(
        "SELECT process_id, base_price, response_count, unique_suppliers"
        " FROM procurement_processes ORDER BY process_id"
    ).fetchall() == [
        ("old", Decimal("1000.00"), 3, 2),
        ("zero", Decimal("0.00"), 0, 0),
    ]


def test_identical_rows_are_not_deduplicated_here(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row(), _row()])
    assert connection.execute("SELECT count(*) FROM procurement_processes").fetchone() == (2,)


def test_output_columns_and_source_text(tmp_path: Path) -> None:
    connection = _normalize(tmp_path, [_row()])
    result = connection.execute("SELECT * FROM procurement_processes")
    assert [description[0] for description in result.description] == [
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
    ]
    assert connection.execute(
        "SELECT procurement_process, process_id, department FROM procurement_processes"
    ).fetchall() == [("CO1.BDOS.1", "CO1.REQ.1", "SECRETARÍA DE INFRAESTRUCTURA FÍSICA")]


@pytest.fixture(scope="module")
def real_processes() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    normalize_procurement_processes(connection, SNAPSHOT_PROCESSES)
    return connection


def test_golden_every_process_is_classified(real_processes: duckdb.DuckDBPyConnection) -> None:
    # R6: las 1.129 filas en «Otra» son «Solicitud de información a los Proveedores» (786) y
    # «Subasta de prueba» (343); ninguna está adjudicada (docs/reglas.md).
    assert real_processes.execute(
        "SELECT count(*), count(DISTINCT procurement_process),"
        " count(*) FILTER (WHERE procurement_method = 'other'),"
        " count(*) FILTER (WHERE procurement_method = 'other' AND awarded),"
        " count(*) FILTER (WHERE direct_award),"
        " count(*) FILTER (WHERE awarded),"
        " count(*) FILTER (WHERE awarded IS NULL),"
        " count(*) FILTER (WHERE published_date IS NULL) FROM procurement_processes"
    ).fetchone() == (23450, 17260, 1129, 0, 15509, 7305, 0, 633)
