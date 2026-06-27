"""SourceProject OPF discovery, parsing, and skip detection (§2)."""

from __future__ import annotations

from pathlib import Path

from epub_typogrify.source.project import SourceProject, is_ignored_document
from epub_typogrify.source.xhtml import XhtmlDocument
from tests.epubs import make_project


def test_from_directory_reads_language_and_spine(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    parsed = SourceProject.from_directory(project)
    assert parsed.publication_language == "en"
    names = [p.name for p in parsed.content_documents]
    assert names == ["titlepage.xhtml", "chapter.xhtml", "nav.xhtml"]  # spine order + nav
    assert parsed.nav_document is not None
    assert parsed.nav_document.name == "nav.xhtml"
    assert parsed.opf_path.name == "content.opf"


def test_locates_opf_by_glob_without_container(tmp_path: Path) -> None:
    (tmp_path / "book.opf").write_text(
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="u">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:language>fr</dc:language>'
        '<dc:identifier id="u">x</dc:identifier></metadata>'
        "<manifest/><spine/></package>",
        encoding="utf-8",
    )
    parsed = SourceProject.from_directory(tmp_path)
    assert parsed.publication_language == "fr"


def test_is_ignored_document(tmp_path: Path) -> None:
    make_project(tmp_path)
    titlepage = XhtmlDocument.from_path(tmp_path / "OEBPS" / "titlepage.xhtml")
    chapter = XhtmlDocument.from_path(tmp_path / "OEBPS" / "chapter.xhtml")
    assert is_ignored_document(titlepage) is True
    assert is_ignored_document(chapter) is False


def test_find_enclosing_opf(tmp_path: Path) -> None:
    make_project(tmp_path)
    inside = tmp_path / "OEBPS" / "chapter.xhtml"
    found = SourceProject.find_enclosing_opf(inside)
    assert found is not None
    assert found.name == "content.opf"


def test_find_enclosing_opf_returns_none_when_standalone(tmp_path: Path) -> None:
    lone = tmp_path / "lone.xhtml"
    lone.write_text("<html/>", encoding="utf-8")
    assert SourceProject.find_enclosing_opf(lone) is None
