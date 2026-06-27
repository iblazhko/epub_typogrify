"""Dash and hyphen rules (TypographyConversions.md §1.2-1.4, §2.2)."""

from __future__ import annotations

import pytest

from epub_typogrify.chars import (
    EM_DASH,
    EN_DASH,
    MINUS_SIGN,
    THREE_EM_DASH,
    TWO_EM_DASH,
)
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState
from epub_typogrify.rules.dashes import dash_rule


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a---b", f"a{EM_DASH}b"),  # triple hyphen -> em
        (EM_DASH * 3, THREE_EM_DASH),  # three em dashes -> three-em ligature
        (EM_DASH * 2, TWO_EM_DASH),  # two em dashes -> two-em ligature
        ("1914-1918", f"1914{EN_DASH}1918"),  # numeric range
        ("pp. 10-20", f"pp. 10{EN_DASH}20"),
        ("IV-VI", f"IV{EN_DASH}VI"),  # roman range
        ("X-ray", "X-ray"),  # not a roman range
        ("a-b", "a-b"),  # plain hyphenated word untouched
        ("it was -5 degrees", f"it was {MINUS_SIGN}5 degrees"),  # minus
        ("(-5)", f"({MINUS_SIGN}5)"),
        ("x-5", "x-5"),  # hyphen after a letter is neither range nor minus
    ],
)
def test_dashes_agnostic(en: LocaleProfile, text: str, expected: str) -> None:
    assert dash_rule(text, en, ContextState()) == expected


def test_double_hyphen_is_locale_specific(en: LocaleProfile, en_gb: LocaleProfile) -> None:
    assert dash_rule("yes--no", en, ContextState()) == f"yes{EM_DASH}no"
    assert dash_rule("yes--no", en_gb, ContextState()) == f"yes{EN_DASH}no"
