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


_GB_HEADER = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-GB">\n'
)
NBSP = chars.NO_BREAK_SPACE
EN = chars.EN_DASH


def _gb_dashes(body: str) -> str:
    source = _GB_HEADER + body + "\n</html>"
    return typogrify_bytes(source.encode("utf-8"), normalize_dashes=True).decode()


def test_parenthetical_dash_binds_across_inline_boundary_in_tail() -> None:
    # Dash in the tail of <em>: its preceding word is in the previous inline node.
    out = _gb_dashes("<body><p><em>this is it</em> – business as usual</p></body>")
    assert f"</em>{NBSP}{EN} business as usual" in out


def test_parenthetical_dash_binds_across_inline_boundary_before_element() -> None:
    # Dash before <em>: its following word is in the next inline node.
    out = _gb_dashes("<body><p>this is it – <em>business as usual</em></p></body>")
    assert f"this is it{NBSP}{EN} <em>" in out


def test_block_start_dash_is_left_alone() -> None:
    # A dash at the very start of a block (dialogue/list) has no preceding word.
    out = _gb_dashes("<body><p>– Yes, indeed.</p></body>")
    assert "<p>– Yes" in out  # unchanged, no nbsp inserted
    assert NBSP not in out


def _default(body: str) -> str:
    source = _GB_HEADER + body + "\n</html>"
    return typogrify_bytes(source.encode("utf-8")).decode()  # no --normalize-dashes


def test_interrupted_dialogue_dash_before_closing_inline_element() -> None:
    # A trailing "--" right before </em></p>: closed em dash (CMOS/NHR/Duden),
    # regardless of --normalize-dashes (always on) and of en-GB's own spaced en
    # dash convention for ordinary parenthetical dashes.
    out = _default("<body><p><em>what if --</em></p></body>")
    assert f"what if{chars.WORD_JOINER}{EM}</em>" in out
    out = _default("<body><p><em>what if -- </em></p></body>")
    assert f"what if{chars.WORD_JOINER}{EM}</em>" in out


def test_interrupted_dialogue_dash_is_not_confused_by_a_following_element() -> None:
    # A dash before <em> with more sentence content inside it is mid-sentence, not
    # the end of the paragraph — left as the ordinary "--" conversion produced it.
    out = _default("<body><p>this is it -- <em>business as usual</em></p></body>")
    assert chars.WORD_JOINER not in out
    assert f"this is it {EN} <em>" in out


WJ = chars.WORD_JOINER
PS = chars.PUNCTUATION_SPACE


def test_ellipsis_spacing_opt_in_and_inline_boundary() -> None:
    source = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n'
        "<body><p>well<em>now</em>... <em>then</em>...</p></body>\n</html>"
    )
    out = typogrify_bytes(source.encode("utf-8"), ellipsis_spacing=True).decode()
    # The ellipsis in the tail of <em>now</em> binds across the boundary, and the
    # trailing ellipsis at paragraph end gets the before-sandwich but no after-space.
    assert f"</em>{WJ}{PS}{WJ}{ELL} <em>then</em>{WJ}{PS}{WJ}{ELL}" in out


def test_ellipsis_spacing_off_by_default() -> None:
    source = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n'
        "<body><p>Wait... what</p></body>\n</html>"
    )
    out = typogrify_bytes(source.encode("utf-8")).decode()
    assert f"Wait{ELL} what" in out  # collapsed only, no spacing
    assert WJ not in out


_EN_US_HEADER = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<html xmlns="http://www.w3.org/1999/xhtml"'
    ' xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en-US">\n'
)


def _en_us(body: str) -> str:
    source = _EN_US_HEADER + body + "\n</html>"
    return typogrify_bytes(source.encode("utf-8")).decode()


def test_abbreviation_binds_across_inline_boundary() -> None:
    # A personal-title abbreviation wrapped in <abbr> (Standard Ebooks
    # epub:type="z3998:name-title" convention): its target name is a sibling
    # text node, not inside the <abbr> itself.
    out = _en_us(
        '<body><p>He called on <abbr epub:type="z3998:name-title">Mr.</abbr>'
        " Adequate yesterday.</p></body>"
    )
    assert f'<abbr epub:type="z3998:name-title">Mr.</abbr>{NBSP}Adequate' in out


def test_initials_bind_across_inline_boundary() -> None:
    # A wrapped middle initial (epub:type="z3998:given-name"): both the
    # internal initials spacing and the binding to the following surname must
    # cross the markup boundary.
    out = _en_us(
        "<body><p>William "
        '<abbr epub:type="z3998:given-name">H.</abbr> Taft was our'
        " twenty-seventh president.</p></body>"
    )
    # A single initial is still excluded (indistinguishable from a list/outline
    # marker, per §2.3) -- even at a markup boundary.
    assert '<abbr epub:type="z3998:given-name">H.</abbr> Taft' in out
    assert NBSP not in out


def test_two_initials_bind_across_inline_boundary() -> None:
    out = _en_us(
        "<body><p>Author "
        '<abbr epub:type="z3998:given-name">V. S.</abbr> Naipaul wrote it.</p></body>'
    )
    assert f'<abbr epub:type="z3998:given-name">V.{NBSP}S.</abbr>{NBSP}Naipaul' in out


def test_abbreviation_at_block_end_does_not_leak_into_next_block() -> None:
    # An abbreviation with nothing to bind to, and no following run at all in
    # its own block, must not carry a stale pending-bind flag into the next
    # paragraph's leading space.
    out = _en_us(
        "<body>"
        '<p>He called on <abbr epub:type="z3998:name-title">Mr.</abbr></p>'
        "<p> Adequate was not available.</p>"
        "</body>"
    )
    assert NBSP not in out


def test_abbreviation_with_no_markup_gap_is_unaffected() -> None:
    # No space at all between the closing tag and the following word: nothing
    # to convert, and no crash.
    out = _en_us(
        '<body><p>He called on <abbr epub:type="z3998:name-title">Mr.</abbr>'
        "Adequate, no space at all.</p></body>"
    )
    assert NBSP not in out
    assert "</abbr>Adequate" in out


def test_cross_boundary_binding_is_idempotent() -> None:
    source = _EN_US_HEADER + (
        '<body><p>He called on <abbr epub:type="z3998:name-title">Mr.</abbr>'
        " Adequate.</p></body>\n</html>"
    )
    once = typogrify_bytes(source.encode("utf-8"), publication_lang="en-US")
    twice = typogrify_bytes(once, publication_lang="en-US")
    assert once == twice


def test_abbreviation_binds_forward_to_word_in_a_following_element() -> None:
    # The reverse shape: the abbreviation is plain text, and its target word is
    # what's wrapped (`Mr. <em>Adequate</em>`) -- the space to convert is
    # already in the abbreviation's own run (trailing, nothing after it there),
    # so no cross-run flag is even needed for this direction.
    out = _en_us("<body><p>He called on Mr. <em>Adequate</em>.</p></body>")
    assert f"on Mr.{NBSP}<em>Adequate</em>" in out


def test_abbreviation_and_word_both_wrapped_in_separate_elements() -> None:
    # Both the abbreviation and its target word are wrapped, with the
    # separating space its own bare tail run between the two closing/opening
    # tags -- that gap run has no word of its own to look ahead to either.
    out = _en_us("<body><p><strong>Mr.</strong> <em>Adequate</em> said hello.</p></body>")
    assert f"<strong>Mr.</strong>{NBSP}<em>Adequate</em>" in out


def test_abbreviation_and_word_wrapped_with_no_separating_text_node() -> None:
    # No tail text node at all between the two elements (adjacent markup, no
    # space in the source): nothing to convert, no crash.
    out = _en_us("<body><p><strong>Mr.</strong><em>Adequate</em> said hello.</p></body>")
    assert NBSP not in out
    assert "<strong>Mr.</strong><em>Adequate</em>" in out


def test_reverse_and_both_wrapped_binding_is_idempotent() -> None:
    for body in (
        "<body><p>He called on Mr. <em>Adequate</em>.</p></body>",
        "<body><p><strong>Mr.</strong> <em>Adequate</em> said hello.</p></body>",
    ):
        source = (_EN_US_HEADER + body + "\n</html>").encode("utf-8")
        once = typogrify_bytes(source, publication_lang="en-US")
        twice = typogrify_bytes(once, publication_lang="en-US")
        assert once == twice
