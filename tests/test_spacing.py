"""Word-joiner and whitespace-cleanup rules (TypographyConversions.md §1.6-1.7)."""

from __future__ import annotations

import pytest

from epub_typogrify.chars import EM_DASH, NO_BREAK_SPACE, THREE_EM_DASH, WORD_JOINER
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState
from epub_typogrify.rules.spacing import collapse_whitespace, word_joiner_before_em_dash


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (f"word{EM_DASH}next", f"word{WORD_JOINER}{EM_DASH}next"),
        (f"word{WORD_JOINER}{EM_DASH}next", f"word{WORD_JOINER}{EM_DASH}next"),  # idempotent
        (f"a{THREE_EM_DASH}b", f"a{WORD_JOINER}{THREE_EM_DASH}b"),
        (f" {EM_DASH}next", f" {EM_DASH}next"),  # preceded by space -> no joiner
    ],
)
def test_word_joiner(en: LocaleProfile, text: str, expected: str) -> None:
    assert word_joiner_before_em_dash(text, en, ContextState()) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a  b", "a b"),
        ("a   b", "a b"),
        (f"a{NO_BREAK_SPACE}{NO_BREAK_SPACE}b", f"a{NO_BREAK_SPACE}b"),
        ("a b", "a b"),
    ],
)
def test_collapse_whitespace(en: LocaleProfile, text: str, expected: str) -> None:
    assert collapse_whitespace(text, en, ContextState()) == expected
