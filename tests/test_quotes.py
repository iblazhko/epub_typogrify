"""Smart-quote and apostrophe engine (TypographyConversions.md §2.1, §2.7)."""

from __future__ import annotations

import pytest

from epub_typogrify.chars import LEFT_DOUBLE_QUOTE as LDQ
from epub_typogrify.chars import LEFT_SINGLE_QUOTE as LSQ
from epub_typogrify.chars import RIGHT_DOUBLE_QUOTE as RDQ
from epub_typogrify.chars import RIGHT_SINGLE_QUOTE as RSQ
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState
from epub_typogrify.rules.quotes import smart_quotes_rule


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('"quote"', f"{LDQ}quote{RDQ}"),
        ("'quote'", f"{LSQ}quote{RSQ}"),
        ("don't", f"don{RSQ}t"),
        ("o'clock", f"o{RSQ}clock"),
        ("dogs'", f"dogs{RSQ}"),  # possessive apostrophe, not a closing quote
        ("'92", f"{RSQ}92"),  # year elision
        ("it's a 'test'", f"it{RSQ}s a {LSQ}test{RSQ}"),
        ("\"He said 'hi' then left\"", f"{LDQ}He said {LSQ}hi{RSQ} then left{RDQ}"),
    ],
)
def test_quotes_en(en: LocaleProfile, text: str, expected: str) -> None:
    assert smart_quotes_rule(text, en, ContextState()) == expected


def test_quote_mapping_is_character_based(en: LocaleProfile, en_gb: LocaleProfile) -> None:
    # `"` -> double pair, `'` -> single pair, regardless of nesting. en and en-GB
    # share the same marks, so the quote output is identical (their differences
    # are punctuation placement, abbreviations, and the dash — not quote glyphs).
    text = "\"He said 'hi' then left\""
    expected = f"{LDQ}He said {LSQ}hi{RSQ} then left{RDQ}"
    assert smart_quotes_rule(text, en, ContextState()) == expected
    assert smart_quotes_rule(text, en_gb, ContextState()) == expected


def test_quote_state_threads_across_runs(en: LocaleProfile) -> None:
    """A quotation opened in one run is closed correctly in the next."""
    ctx = ContextState()
    first = smart_quotes_rule('"open here ', en, ctx)
    second = smart_quotes_rule('and close"', en, ctx)
    assert first == f"{LDQ}open here "
    assert second == f"and close{RDQ}"
