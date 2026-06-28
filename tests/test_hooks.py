"""Locale code hooks (TypographyConversions.md §2.4, §2.6)."""

from __future__ import annotations

import pytest

from epub_typogrify import chars
from epub_typogrify.locales.hooks import hooks_for
from epub_typogrify.locales.hooks.en import english_contractions, english_latinisms
from epub_typogrify.locales.hooks.fr import french_spacing
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.locales.registry import LocaleRegistry
from epub_typogrify.rules.context import ContextState

LSQ = chars.LEFT_SINGLE_QUOTE
RSQ = chars.RIGHT_SINGLE_QUOTE
NN = chars.NARROW_NO_BREAK_SPACE


def test_english_hooks_apply_to_en_and_en_gb() -> None:
    en_hooks = hooks_for("en")
    assert en_hooks  # registered
    # en-GB has no hooks of its own, so it inherits exactly the en hooks.
    assert hooks_for("en-GB") == en_hooks
    # French is separate.
    assert hooks_for("fr") != en_hooks


def test_english_contractions(en: LocaleProfile) -> None:
    # Leading elisions (’tis etc.) are handled by the quote engine now; the hook
    # only fixes the Scottish/Irish M' prefix.
    assert english_contractions(f"M{RSQ}Donald", en, ContextState()) == "McDonald"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("i. e. this", "i.e. this"),
        ("e. g. that", "e.g. that"),
        ("in A. D. 1066", "in AD 1066"),
        ("by B. C. times", "by BC times"),
    ],
)
def test_english_latinisms(en: LocaleProfile, text: str, expected: str) -> None:
    assert english_latinisms(text, en, ContextState()) == expected


def test_french_spacing(registry: LocaleRegistry) -> None:
    fr = registry.resolve("fr")
    assert fr is not None
    assert french_spacing("Vraiment ?", fr, ContextState()) == f"Vraiment{NN}?"
    assert french_spacing("Oui : non", fr, ContextState()) == f"Oui{NN}: non"
    guillemets = f"{chars.LEFT_GUILLEMET} Bonjour {chars.RIGHT_GUILLEMET}"
    expected = f"{chars.LEFT_GUILLEMET}{NN}Bonjour{NN}{chars.RIGHT_GUILLEMET}"
    assert french_spacing(guillemets, fr, ContextState()) == expected
    # idempotent
    assert french_spacing(expected, fr, ContextState()) == expected
