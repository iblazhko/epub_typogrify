"""Vulgar-fraction rule (TypographyConversions.md §1.5)."""

from __future__ import annotations

import dataclasses

import pytest

from epub_typogrify.chars import ONE_HALF, THREE_EIGHTHS, THREE_QUARTERS
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState
from epub_typogrify.rules.fractions import fractions_rule


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1/2", ONE_HALF),
        ("3/4", THREE_QUARTERS),
        ("3/8", THREE_EIGHTHS),
        ("a 1/2 cup", f"a {ONE_HALF} cup"),
        ("11/2", "11/2"),  # digit before -> untouched
        ("1/24", "1/24"),  # digit after -> untouched
        ("1/2/2020", "1/2/2020"),  # date -> untouched
    ],
)
def test_fractions(en: LocaleProfile, text: str, expected: str) -> None:
    assert fractions_rule(text, en, ContextState()) == expected


def test_fractions_can_be_disabled(en: LocaleProfile) -> None:
    disabled = dataclasses.replace(en, fractions_enabled=False)
    assert fractions_rule("1/2", disabled, ContextState()) == "1/2"
