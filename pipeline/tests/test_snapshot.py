"""Escritor de la copia (ADR 0006): CSV UTF-8 sin BOM, finales LF y escritura atómica."""

import hashlib
from collections.abc import Iterator
from pathlib import Path

import pytest

from veeduria.extract.snapshot import write_snapshot
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
