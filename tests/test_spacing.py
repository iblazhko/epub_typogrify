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
        (f"{EM_DASH}next", f"{EM_DASH}next"),  # block start, no ctx: no preceding word
    ],
)
def test_word_joiner(en: LocaleProfile, text: str, expected: str) -> None:
    assert word_joiner_before_em_dash(text, en, ContextState()) == expected


def test_word_joiner_block_start_dialogue_dash(en: LocaleProfile) -> None:
    # A dash opening its block (a Russian block-start dialogue dash is the
    # common case) has nothing before it on the line -- no word joiner to add.
    text = f"{EM_DASH}Реплика"
    assert word_joiner_before_em_dash(text, en, ContextState()) == text


def test_word_joiner_across_markup_boundary(en: LocaleProfile) -> None:
    # A dash at the *start* of this run whose previous run ends in a real word
    # (an inline-markup boundary, not a block start) still gets the joiner --
    # ctx.run_prev_char carries that word across.
    ctx = ContextState(run_prev_char="d")
    assert word_joiner_before_em_dash(f"{EM_DASH}next", en, ctx) == f"{WORD_JOINER}{EM_DASH}next"


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
