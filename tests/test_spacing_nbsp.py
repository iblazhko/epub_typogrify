"""Non-breaking keep-together spacing (TypographyConversions.md §2.3)."""

from __future__ import annotations

import pytest

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile, profile_from_dict
from epub_typogrify.rules.context import ContextState
from epub_typogrify.rules.spacing import (
    nonbreaking_abbreviations,
    nonbreaking_initials,
    nonbreaking_units,
)

NBSP = chars.NO_BREAK_SPACE

PROFILE = profile_from_dict(
    "en",
    {
        "abbreviations": {"nonbreaking": ["Mr.", "Mrs.", "No.", "St."]},
        "keep_together": {"units": ["km", "m", "%", "°C"]},
    },
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Mr. Smith", f"Mr.{NBSP}Smith"),
        ("No. 5", f"No.{NBSP}5"),
        ("St. James", f"St.{NBSP}James"),
        ("Mr.  Smith", f"Mr.{NBSP}Smith"),  # collapses multiple spaces
        ("Mr. Smith and Mrs. Jones", f"Mr.{NBSP}Smith and Mrs.{NBSP}Jones"),
        (f"Mr.{NBSP}Smith", f"Mr.{NBSP}Smith"),  # idempotent
        ("Mr.", "Mr."),  # nothing to bind to
        ("Smithr. x", "Smithr. x"),  # not a standalone abbreviation
    ],
)
def test_abbreviations(text: str, expected: str) -> None:
    assert nonbreaking_abbreviations(text, PROFILE, ContextState()) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("100 km", f"100{NBSP}km"),
        ("5 %", f"5{NBSP}%"),
        ("20 °C", f"20{NBSP}°C"),
        (f"100{NBSP}km", f"100{NBSP}km"),  # idempotent
        ("100 metres", "100 metres"),  # `m` must not match inside a word
    ],
)
def test_units(text: str, expected: str) -> None:
    assert nonbreaking_units(text, PROFILE, ContextState()) == expected


def test_no_abbreviations_is_noop(en: LocaleProfile) -> None:
    # The minimal test profile has no abbreviation/unit lists.
    assert nonbreaking_abbreviations("Mr. Smith", en, ContextState()) == "Mr. Smith"
    assert nonbreaking_units("100 km", en, ContextState()) == "100 km"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("J.M. Coetzee", f"J.M.{NBSP}Coetzee"),
        ("V.S. Naipaul", f"V.S.{NBSP}Naipaul"),
        (
            "J.M. Coetzee, Milan Kundera, and V.S. Naipaul",
            f"J.M.{NBSP}Coetzee, Milan Kundera, and V.S.{NBSP}Naipaul",
        ),
        ("V. S. Naipaul", f"V.{NBSP}S.{NBSP}Naipaul"),  # spaced initials
        (f"J.M.{NBSP}Coetzee", f"J.M.{NBSP}Coetzee"),  # idempotent
        ("T.S. Eliot", f"T.S.{NBSP}Eliot"),
        ("A. The first point.", "A. The first point."),  # single initial: list marker, not bound
        ("J.M.", "J.M."),  # nothing to bind to
        ("j.m. coetzee", "j.m. coetzee"),  # lower case: not initials
    ],
)
def test_initials(text: str, expected: str) -> None:
    assert nonbreaking_initials(text, PROFILE, ContextState()) == expected


def test_initials_is_locale_independent(en: LocaleProfile) -> None:
    # Unlike nonbreaking_abbreviations/nonbreaking_units, this rule needs no
    # profile-configured word list -- it applies from the bare minimal profile.
    assert nonbreaking_initials("J.M. Coetzee", en, ContextState()) == f"J.M.{NBSP}Coetzee"
