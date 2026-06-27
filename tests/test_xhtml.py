"""XhtmlDocument parse/serialise fidelity (TechnicalDesign.md §4)."""

from __future__ import annotations

from pathlib import Path

from epub_typogrify.source.xhtml import XhtmlDocument

_DOC = (
    b'<?xml version="1.0" encoding="utf-8"?>\n'
    b"<!DOCTYPE html>\n"
    b'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"'
    b' xml:lang="en">\n'
    b'<head><title>A &amp; B</title><meta charset="utf-8"/></head>\n'
    b'<body epub:type="bodymatter"><p>Plain &lt;text&gt;</p><!-- note --></body>\n'
    b"</html>"
)


def _canon(data: bytes) -> bytes:
    return XhtmlDocument.from_bytes(data).to_bytes()


def test_round_trip_is_stable() -> None:
    once = _canon(_DOC)
    assert _canon(once) == once


def test_canonical_doc_round_trips_byte_for_byte() -> None:
    # The fixture is already written in the serializer's canonical form.
    assert _canon(_DOC) == _DOC


def test_preserves_declaration_doctype_and_namespaces() -> None:
    out = _canon(_DOC)
    assert out.startswith(b'<?xml version="1.0" encoding="utf-8"?>\n')
    assert b"<!DOCTYPE html>" in out
    assert b'xmlns:epub="http://www.idpf.org/2007/ops"' in out
    assert b"<!-- note -->" in out
    assert b"&amp;" in out  # reserved characters stay escaped


def test_document_without_declaration() -> None:
    data = b'<html xmlns="http://www.w3.org/1999/xhtml"><body><p>Hi</p></body></html>'
    out = XhtmlDocument.from_bytes(data).to_bytes()
    assert not out.startswith(b"<?xml")
    assert b"<p>Hi</p>" in out


def test_from_path_and_write(tmp_path: Path) -> None:
    source = tmp_path / "in.xhtml"
    source.write_bytes(_DOC)
    document = XhtmlDocument.from_path(source)
    target = tmp_path / "out.xhtml"
    document.write(target)
    assert target.read_bytes() == _canon(_DOC)
