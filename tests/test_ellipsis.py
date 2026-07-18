"""Ellipsis rule (TypographyConversions.md §1.1)."""

from __future__ import annotations

import pytest

from epub_typogrify.chars import (
    ELLIPSIS,
    HAIR_SPACE,
    NARROW_NO_BREAK_SPACE,
    NO_BREAK_SPACE,
    PUNCTUATION_SPACE,
)
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState
from epub_typogrify.rules.ellipsis import ellipsis_rule


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("...", ELLIPSIS),
        ("Wait... what", f"Wait{ELLIPSIS} what"),
        (". . .", ELLIPSIS),
        (".  .  .", ELLIPSIS),
        (ELLIPSIS, ELLIPSIS),  # already converted -> unchanged
        ("....", f"{ELLIPSIS}."),  # 3 ellipsis dots + sentence's own full stop
        ("It looks so old....", f"It looks so old{ELLIPSIS}."),
        (".....", "....."),  # five dots left alone (not the 3-dots-plus-period case)
        ("......", "......"),  # six dots (and beyond) left alone
        ("a.b.c", "a.b.c"),  # dots not forming an ellipsis
        (f".{NO_BREAK_SPACE}.{NO_BREAK_SPACE}.", ELLIPSIS),  # NBSP-spaced dots
        (f".{NARROW_NO_BREAK_SPACE}.{NARROW_NO_BREAK_SPACE}.", ELLIPSIS),
        (f".{PUNCTUATION_SPACE}.{PUNCTUATION_SPACE}.", ELLIPSIS),
        (f".{HAIR_SPACE}.{HAIR_SPACE}.", ELLIPSIS),
        (f". {NO_BREAK_SPACE}. .", ELLIPSIS),  # mixed space kinds between dots
        (f".{NO_BREAK_SPACE}.{NO_BREAK_SPACE}..", f"{ELLIPSIS}."),  # spaced dots + period
    ],
)
def test_ellipsis(en: LocaleProfile, text: str, expected: str) -> None:
    assert ellipsis_rule(text, en, ContextState()) == expected
