"""I4 · Concentración de proveedores, solo agregada (R7, R8, R13, R14; ADR 0045)."""

from decimal import Decimal

import duckdb
import pytest

from tests.paths import REPO_ROOT
from veeduria.indicators.i2_pre_restriction_share import RATIO_DIGITS
from veeduria.indicators.i4_supplier_concentration import (
    TOP_SUPPLIERS,
    build_supplier_concentration,
)
from veeduria.pipeline import build
from veeduria.publish.indicators import publish_indicators

SNAPSHOT = REPO_ROOT / "data" / "snapshot"
TREASURY = "treasury"
HEALTH = "health"


class _Fixture:
    """`linked_contracts`, `contracts` y `suppliers` mínimas con las columnas que lee I4."""

    def __init__(self) -> None:
        self.connection = duckdb.connect()
        self.connection.execute(
            "CREATE TABLE linked_contracts (contract_reference VARCHAR, contract_id VARCHAR,"
            " signed_date TIMESTAMP, initial_value DECIMAL(18, 2), is_value_eligible BOOLEAN,"
            " department VARCHAR)"
        )
        self.connection.execute(
            "CREATE TABLE contracts (contract_id VARCHAR, contract_reference VARCHAR)"
        )
        self.connection.execute("CREATE TABLE suppliers (contract_id VARCHAR, supplier_id VARCHAR)")
        self.count = 0

    def add(
        self,
        supplier: str | None,
        *,
        value: int | None = 100,
        department: str = TREASURY,
        signed: str = "2022-03-10 00:00:00",
        eligible: bool = True,
    ) -> str:
        """Agrega un contrato canónico con su proveedor (o sin fila de proveedor si es `None`)."""
        self.count += 1
        reference = f"REF-{self.count}"
        contract_id = f"CO1.{self.count}"
        amount = None if value is None else Decimal(value)
        self.connection.execute(
            "INSERT INTO linked_contracts VALUES (?, ?, ?, ?, ?, ?)",
            (reference, contract_id, signed, amount, eligible, department),
        )
        self.connection.execute("INSERT INTO contracts VALUES (?, ?)", (contract_id, reference))
        if supplier is not None:
            self.connection.execute("INSERT INTO suppliers VALUES (?, ?)", (contract_id, supplier))
        return reference

    def add_version(self, reference: str, supplier: str) -> None:
        """Una versión no canónica del contrato, con otro proveedor."""
        self.count += 1
        contract_id = f"CO1.{self.count}"
        self.connection.execute("INSERT INTO contracts VALUES (?, ?)", (contract_id, reference))
        self.connection.execute("INSERT INTO suppliers VALUES (?, ?)", (contract_id, supplier))

    def cells(self):
        return {
            (c.period, c.level, c.department): c
            for c in build_supplier_concentration(self.connection)
        }


def _many_suppliers(fixture: _Fixture, count: int, **kwargs) -> None:
    for number in range(count):
        fixture.add(f"90000000{number}", **kwargs)


def test_i4_top_five_value_over_total_value() -> None:
    fixture = _Fixture()
    for supplier, value in zip("ABCDEFG", (700, 600, 500, 400, 300, 200, 100), strict=True):
        fixture.add(supplier, value=value)
    cell = fixture.cells()[("2022", "district", None)]
    assert (cell.numerator, cell.denominator) == (2500, 2800)
    assert cell.ratio == pytest.approx(2500 / 2800, abs=1e-4)
    assert (cell.indicator, cell.measure, cell.variant) == ("I4", "value", None)
    assert cell.is_suppressed is False


def test_i4_sums_the_value_of_a_supplier_across_contracts() -> None:
    fixture = _Fixture()
    for _ in range(3):
        fixture.add("A", value=100)
    for supplier in "BCDEFG":
        fixture.add(supplier, value=100)
    cell = fixture.cells()[("2022", "district", None)]
    # A suma 300, y cuatro de los otros seis completan el top 5.
    assert (cell.numerator, cell.denominator, cell.sample_size) == (700, 900, 9)


def test_i4_ties_for_the_fifth_place_do_not_change_the_figure() -> None:
    fixture = _Fixture()
    for supplier, value in zip("ABCDEFG", (500, 400, 300, 200, 100, 100, 100), strict=True):
        fixture.add(supplier, value=value)
    cell = fixture.cells()[("2022", "district", None)]
    assert cell.numerator == 1500


def test_i4_r7_public_credit_and_contracts_without_value_are_left_out() -> None:
    fixture = _Fixture()
    _many_suppliers(fixture, 7)
    fixture.add("CREDIT", value=1_000_000, eligible=False)
    fixture.add("NOVALUE", value=None)
    cell = fixture.cells()[("2022", "district", None)]
    assert (cell.numerator, cell.denominator, cell.sample_size) == (500, 700, 7)


def test_i4_r14_contracts_without_a_supplier_row_are_left_out() -> None:
    fixture = _Fixture()
    _many_suppliers(fixture, 7)
    fixture.add(None, value=5000)
    cell = fixture.cells()[("2022", "district", None)]
    assert (cell.denominator, cell.sample_size) == (700, 7)


def test_i4_a_contract_counts_once_even_if_another_version_names_a_different_supplier() -> None:
    fixture = _Fixture()
    _many_suppliers(fixture, 6)
    reference = fixture.add("CANONICAL", value=100)
    fixture.add_version(reference, "AAA-OTHER")
    cell = fixture.cells()[("2022", "district", None)]
    assert (cell.denominator, cell.sample_size) == (700, 7)


def test_i4_links_the_supplier_of_a_non_canonical_version_by_reference() -> None:
    fixture = _Fixture()
    _many_suppliers(fixture, 6)
    reference = fixture.add(None, value=100)
    fixture.add_version(reference, "FROM-OLD-VERSION")
    cell = fixture.cells()[("2022", "district", None)]
    assert (cell.denominator, cell.sample_size) == (700, 7)


def test_i4_r8_departments_add_up_to_the_district() -> None:
    fixture = _Fixture()
    _many_suppliers(fixture, 6, department=TREASURY)
    _many_suppliers(fixture, 6, department=HEALTH)
    cells = fixture.cells()
    district = cells[("2022", "district", None)]
    parts = [cells[("2022", "department", d)] for d in (TREASURY, HEALTH)]
    assert district.denominator == sum(part.denominator for part in parts) == 1200
    assert district.sample_size == sum(part.sample_size for part in parts)


def test_i4_each_year_has_its_own_cell() -> None:
    fixture = _Fixture()
    _many_suppliers(fixture, 6, signed="2022-03-10 00:00:00")
    _many_suppliers(fixture, 6, signed="2023-03-10 00:00:00")
    assert {(period, level) for period, level, _ in fixture.cells()} >= {
        ("2022", "district"),
        ("2023", "district"),
    }


def test_i4_department_with_five_suppliers_or_fewer_is_published_suppressed() -> None:
    fixture = _Fixture()
    _many_suppliers(fixture, TOP_SUPPLIERS, department=HEALTH)
    # Cinco contratos pasan R13, pero el top 5 sería 100 % por construcción.
    cell = fixture.cells()[("2022", "department", HEALTH)]
    assert cell.is_suppressed is True
    assert cell.sample_size == TOP_SUPPLIERS
    assert (cell.numerator, cell.denominator, cell.ratio) == (None, None, None)


def test_i4_department_with_six_suppliers_is_published() -> None:
    fixture = _Fixture()
    _many_suppliers(fixture, TOP_SUPPLIERS + 1, department=HEALTH)
    assert fixture.cells()[("2022", "department", HEALTH)].is_suppressed is False


def test_i4_district_is_never_suppressed_even_with_few_suppliers() -> None:
    fixture = _Fixture()
    fixture.add("A")
    cell = publish_indicators(build_supplier_concentration(fixture.connection)).cells[0]
    assert (cell.level, cell.is_suppressed) == ("district", False)
    assert cell.ratio == 1.0


def test_i4_r13_small_department_cells_are_suppressed_without_figures() -> None:
    fixture = _Fixture()
    _many_suppliers(fixture, 7, department=TREASURY)
    _many_suppliers(fixture, 3, department=HEALTH)
    cells = {
        (c.level, c.department): c
        for c in publish_indicators(build_supplier_concentration(fixture.connection)).cells
    }
    small = cells[("department", HEALTH)]
    assert small.is_suppressed is True
    assert (small.sample_size, small.numerator, small.ratio) == (3, None, None)


def test_i4_d6_a_single_hidden_department_also_hides_the_next_smallest() -> None:
    fixture = _Fixture()
    _many_suppliers(fixture, 8, department=TREASURY)
    _many_suppliers(fixture, 6, department=HEALTH)
    _many_suppliers(fixture, 3, department="culture")
    cells = {
        c.department: c
        for c in publish_indicators(build_supplier_concentration(fixture.connection)).cells
        if c.level == "department"
    }
    # La secretaría pequeña (R13) queda sola; D6 oculta la siguiente menor, y el Distrito sigue.
    assert cells["culture"].is_suppressed and cells[HEALTH].is_suppressed
    assert not cells[TREASURY].is_suppressed


def test_i4_cells_carry_no_supplier_identity() -> None:
    fixture = _Fixture()
    _many_suppliers(fixture, 7)
    dumped = " ".join(c.model_dump_json() for c in build_supplier_concentration(fixture.connection))
    assert "90000000" not in dumped


def test_i4_ratio_is_rounded_and_reconstructible() -> None:
    fixture = _Fixture()
    for supplier, value in zip("ABCDEFG", (3, 3, 3, 3, 3, 2, 1), strict=True):
        fixture.add(supplier, value=value)
    cell = fixture.cells()[("2022", "district", None)]
    assert cell.ratio == round(cell.numerator / cell.denominator, RATIO_DIGITS)


@pytest.fixture(scope="module")
def snapshot_connection() -> duckdb.DuckDBPyConnection:
    return build(SNAPSHOT)


def test_golden_i4_district_2022(snapshot_connection: duckdb.DuckDBPyConnection) -> None:
    cells = {
        (c.period, c.level, c.department): c
        for c in build_supplier_concentration(snapshot_connection)
    }
    cell = cells[("2022", "district", None)]
    assert (cell.numerator, cell.denominator, cell.sample_size) == (
        1_109_311_641_923,
        2_571_277_284_234,
        914,
    )
    assert cell.ratio == pytest.approx(0.4314, abs=1e-4)
