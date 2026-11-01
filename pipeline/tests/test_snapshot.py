"""Escritor de la copia (ADR 0006): CSV UTF-8 sin BOM, finales LF y escritura atómica."""

import hashlib
from collections.abc import Iterator
from pathlib import Path

import pytest

from veeduria.extract.snapshot import read_column, write_snapshot
from veeduria.extract.sources import Query

HEADER = ("id_contrato", "valor")


def make_query() -> Query:
    return Query(
        id="secop_contracts",
        dataset="dataset",
        kind="socrata",
        url="https://example.test/resource/dataset.csv",
        where="entidad = 'X'",
        order_by="id_contrato",
        allowed=HEADER,
        excluded=("nombre_supervisor",),
    )


def test_writes_utf8_without_bom_and_with_lf(tmp_path: Path) -> None:
    result = write_snapshot(make_query(), HEADER, [["C1", "Ñandú"], ["C2", "20"]], tmp_path)

    data = result.path.read_bytes()
    assert result.path == tmp_path / "secop_contracts.csv"
    assert not data.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in data
    assert data.decode("utf-8") == "id_contrato,valor\nC1,Ñandú\nC2,20\n"


def test_reports_row_count_and_sha256_of_the_file(tmp_path: Path) -> None:
    result = write_snapshot(make_query(), HEADER, [["C1", "10"], ["C2", "20"]], tmp_path)
    assert result.row_count == 2
    assert result.sha256 == hashlib.sha256(result.path.read_bytes()).hexdigest()


def test_preserves_commas_and_quotes(tmp_path: Path) -> None:
    result = write_snapshot(make_query(), HEADER, [["C1", 'a,"b"']], tmp_path)
    assert result.path.read_text(encoding="utf-8") == 'id_contrato,valor\nC1,"a,""b"""\n'


def test_creates_the_directory(tmp_path: Path) -> None:
    result = write_snapshot(make_query(), HEADER, [["C1", "10"]], tmp_path / "nueva" / "copia")
    assert result.path.exists()


def test_writes_rows_in_a_deterministic_order(tmp_path: Path) -> None:
    result = write_snapshot(make_query(), HEADER, [["C3", "1"], ["C1", "9"], ["C2", "5"]], tmp_path)
    assert result.path.read_text(encoding="utf-8") == "id_contrato,valor\nC1,9\nC2,5\nC3,1\n"


def test_same_rows_in_any_arrival_order_give_the_same_sha256(tmp_path: Path) -> None:
    rows = [["C1", "10"], ["C2", "20"], ["C2", "20"], ["C3", "30"]]
    first = write_snapshot(make_query(), HEADER, rows, tmp_path / "a")
    second = write_snapshot(make_query(), HEADER, list(reversed(rows)), tmp_path / "b")
    assert first.sha256 == second.sha256
    assert first.row_count == second.row_count == 4


def test_duplicate_rows_are_kept(tmp_path: Path) -> None:
    # La copia guarda valores crudos: los duplicados se consolidan después (R5).
    result = write_snapshot(make_query(), HEADER, [["C1", "10"], ["C1", "10"]], tmp_path)
    assert result.row_count == 2


def test_rejects_columns_outside_the_whitelist(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="nombre_supervisor"):
        write_snapshot(
            make_query(), ("id_contrato", "nombre_supervisor"), [["C1", "PERSONA"]], tmp_path
        )
    assert list(tmp_path.iterdir()) == []


def test_rejects_rows_with_the_wrong_width(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="línea 3"):
        write_snapshot(make_query(), HEADER, [["C1", "10"], ["C2"]], tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_failure_while_replacing_keeps_the_previous_copy_and_leaves_no_leftovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_snapshot(make_query(), HEADER, [["C1", "10"]], tmp_path)
    before = (tmp_path / "secop_contracts.csv").read_bytes()

    def failing_replace(source: object, destination: object) -> None:
        raise OSError("falla al mover el archivo")

    monkeypatch.setattr("veeduria.extract.snapshot.os.replace", failing_replace)

    with pytest.raises(OSError):
        write_snapshot(make_query(), HEADER, [["C9", "90"]], tmp_path)

    assert (tmp_path / "secop_contracts.csv").read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["secop_contracts.csv"]


def test_failure_keeps_the_previous_copy_and_leaves_no_leftovers(tmp_path: Path) -> None:
    write_snapshot(make_query(), HEADER, [["C1", "10"]], tmp_path)
    before = (tmp_path / "secop_contracts.csv").read_bytes()

    def exploding() -> Iterator[list[str]]:
        yield ["C9", "90"]
        raise RuntimeError("falla a la mitad")

    with pytest.raises(RuntimeError):
        write_snapshot(make_query(), HEADER, exploding(), tmp_path)

    assert (tmp_path / "secop_contracts.csv").read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["secop_contracts.csv"]


# --- Lectura de una columna de la copia (identificadores para Adiciones) ----------------------


def test_read_column_returns_that_column_in_file_order(tmp_path: Path) -> None:
    path = tmp_path / "secop_contracts.csv"
    path.write_text("valor,id_contrato\n10,C1\n20,C2\n", encoding="utf-8")
    assert read_column(path, "id_contrato") == ["C1", "C2"]


def test_read_column_rejects_a_missing_column(tmp_path: Path) -> None:
    path = tmp_path / "secop_contracts.csv"
    path.write_text("valor\n10\n", encoding="utf-8")
    with pytest.raises(ValueError, match="id_contrato"):
        read_column(path, "id_contrato")


def test_read_column_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_column(tmp_path / "no_existe.csv", "id_contrato")
