"""End-to-end document processing (TechnicalDesign.md §4-§6)."""

from __future__ import annotations

from epub_typogrify import chars
from epub_typogrify.processor import typogrify_bytes
from epub_typogrify.source.xhtml import XhtmlDocument

LDQ = chars.LEFT_DOUBLE_QUOTE
RDQ = chars.RIGHT_DOUBLE_QUOTE
RSQ = chars.RIGHT_SINGLE_QUOTE
EM = chars.EM_DASH
ELL = chars.ELLIPSIS
HALF = chars.ONE_HALF
NN = chars.NARROW_NO_BREAK_SPACE
LG = chars.LEFT_GUILLEMET
RG = chars.RIGHT_GUILLEMET

_HEADER = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    "<!DOCTYPE html>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n'
)


def _canon(text: str) -> bytes:
    return XhtmlDocument.from_bytes(text.encode("utf-8")).to_bytes()


def test_golden_multilingual_document() -> None:
    source = _HEADER + (
        "<head><title>Title...</title></head>\n"
        "<body>\n"
        '<p>He said "hello" -- it\'s 1/2 done...</p>\n'
        '<p xml:lang="fr">Il dit : « Bonjour »</p>\n'
        "<p>the <em>cat</em>'s tail</p>\n"
        '<pre>leave "this" -- alone...</pre>\n'
        '<p class="notypo">keep "verbatim"...</p>\n'
        "</body>\n</html>"
    )
    expected = _HEADER + (
        f"<head><title>Title{ELL}</title></head>\n"
        "<body>\n"
        f"<p>He said {LDQ}hello{RDQ} {EM} it{RSQ}s {HALF} done{ELL}</p>\n"
        f'<p xml:lang="fr">Il dit{NN}: {LG}{NN}Bonjour{NN}{RG}</p>\n'
        f"<p>the <em>cat</em>{RSQ}s tail</p>\n"
        '<pre>leave "this" -- alone...</pre>\n'
        '<p class="notypo">keep "verbatim"...</p>\n'
        "</body>\n</html>"
    )
    assert typogrify_bytes(source.encode("utf-8")) == _canon(expected)


def test_markup_invariance_when_nothing_to_convert() -> None:
    source = _HEADER + "<body><p>Plain text, nothing here.</p></body>\n</html>"
    data = source.encode("utf-8")
    assert typogrify_bytes(data) == _canon(source)  # byte-for-byte


def test_protected_subtrees_are_untouched() -> None:
    source = _HEADER + (
        '<body><p>code: <code>a--b...</code> and <kbd>"x"</kbd> done...</p></body>\n</html>'
    )
    out = typogrify_bytes(source.encode("utf-8")).decode()
    assert "<code>a--b...</code>" in out  # inline protected element unchanged
    assert '<kbd>"x"</kbd>' in out
    assert f"done{ELL}" in out  # surrounding text still converted


def test_unresolved_language_is_left_unchanged() -> None:
    # No xml:lang anywhere and no default -> nothing converts.
    source = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>He said "hi"...</p></body></html>'
    )
    data = source.encode("utf-8")
    assert typogrify_bytes(data) == _canon(source)
    # With an explicit default, it converts.
    assert LDQ.encode("utf-8") in typogrify_bytes(data, default_lang="en")


def test_unsupported_language_is_left_unchanged() -> None:
    source = _HEADER.replace('xml:lang="en"', 'xml:lang="sw"') + (
        '<body><p>He said "hi"...</p></body>\n</html>'
    )
    data = source.encode("utf-8")
    assert typogrify_bytes(data) == _canon(source)


def test_publication_language_fallback() -> None:
    # No document/inline lang; the publication default drives conversion.
    source = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>done...</p></body></html>'
    )
    out = typogrify_bytes(source.encode("utf-8"), publication_lang="en").decode()
    assert f"done{ELL}" in out
