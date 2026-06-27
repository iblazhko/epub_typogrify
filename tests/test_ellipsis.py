"""Ellipsis rule (TypographyConversions.md §1.1)."""

from __future__ import annotations

import pytest

from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.chars import ELLIPSIS
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
        ("....", "...."),  # four dots left alone
        ("a.b.c", "a.b.c"),  # dots not forming an ellipsis
    ],
)
def test_ellipsis(en: LocaleProfile, text: str, expected: str) -> None:
    assert ellipsis_rule(text, en, ContextState()) == expected
