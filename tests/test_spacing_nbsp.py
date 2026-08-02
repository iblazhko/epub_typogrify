"""Non-breaking keep-together spacing (TypographyConversions.md §2.3)."""

from __future__ import annotations

import pytest

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile, profile_from_dict
from epub_typogrify.rules.context import ContextState
from epub_typogrify.rules.spacing import (
    bind_forward_leading_space,
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


# --- Cross-markup-boundary binding (§2.3): an abbreviation or a run of
# initials with no following word *in its own run* (e.g. the text of an
# `<abbr>Mr.</abbr>` element) sets `ctx.pending_bind_forward`; the next run's
# leading space is turned into a non-breaking space by
# `bind_forward_leading_space`. See test_processor.py for the DOM-level
# (TextWalker) end-to-end version of these scenarios.


def test_abbreviation_with_nothing_to_bind_to_sets_pending_flag() -> None:
    ctx = ContextState()
    nonbreaking_abbreviations("Mr.", PROFILE, ctx)
    assert ctx.pending_bind_forward is True


def test_abbreviation_bound_within_its_own_run_does_not_set_pending_flag() -> None:
    ctx = ContextState()
    nonbreaking_abbreviations("Mr. Smith", PROFILE, ctx)
    assert ctx.pending_bind_forward is False


def test_ordinary_text_does_not_set_pending_flag() -> None:
    ctx = ContextState()
    nonbreaking_abbreviations("nothing to see here", PROFILE, ctx)
    assert ctx.pending_bind_forward is False


def test_initials_with_nothing_to_bind_to_sets_pending_flag_and_binds_internally() -> None:
    ctx = ContextState()
    result = nonbreaking_initials("V. S.", PROFILE, ctx)
    assert result == f"V.{NBSP}S."  # bound to each other even without the surname
    assert ctx.pending_bind_forward is True


def test_single_trailing_initial_does_not_set_pending_flag() -> None:
    # Same policy as the intra-run case: one initial alone is indistinguishable
    # from a list/outline marker, even at a markup boundary.
    ctx = ContextState()
    result = nonbreaking_initials("H.", PROFILE, ctx)
    assert result == "H."
    assert ctx.pending_bind_forward is False


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (" Adequate", f"{NBSP}Adequate"),
        (" word", f"{NBSP}word"),
        ("  Adequate", f"{NBSP}Adequate"),  # multiple leading spaces collapse too
        ("Adequate", "Adequate"),  # no leading space: nothing to convert
        ("", ""),
        (", said Mr. Smith", ", said Mr. Smith"),  # doesn't start with a space+word
    ],
)
def test_bind_forward_leading_space_when_pending(text: str, expected: str) -> None:
    ctx = ContextState()
    ctx.pending_bind_forward = True
    assert bind_forward_leading_space(text, PROFILE, ctx) == expected
    assert ctx.pending_bind_forward is False  # one-shot: cleared once a real word is seen


def test_bind_forward_leading_space_is_noop_when_not_pending() -> None:
    ctx = ContextState()
    assert bind_forward_leading_space(" Adequate", PROFILE, ctx) == " Adequate"
    assert ctx.pending_bind_forward is False


def test_bind_forward_leading_space_only_consumes_once() -> None:
    ctx = ContextState()
    ctx.pending_bind_forward = True
    assert bind_forward_leading_space(" Adequate", PROFILE, ctx) == f"{NBSP}Adequate"
    # A second run, even one that would otherwise match, is untouched: the flag
    # was for exactly one run.
    assert bind_forward_leading_space(" Smith", PROFILE, ctx) == " Smith"


def test_bind_forward_stays_armed_through_a_pure_whitespace_run() -> None:
    # The gap in `<strong>Mr.</strong> <em>Adequate</em>`: the tail between the
    # two inline elements is nothing but the separating space -- no word for
    # its own run to look ahead to. It becomes a lone nbsp, and the flag stays
    # armed for the run after it (the <em>'s own text), which is where the
    # word actually is.
    ctx = ContextState()
    ctx.pending_bind_forward = True
    assert bind_forward_leading_space(" ", PROFILE, ctx) == NBSP
    assert ctx.pending_bind_forward is True  # still armed
    assert bind_forward_leading_space("Adequate", PROFILE, ctx) == "Adequate"
    assert ctx.pending_bind_forward is False  # consumed now


def test_bind_forward_stays_armed_through_multiple_whitespace_runs() -> None:
    ctx = ContextState()
    ctx.pending_bind_forward = True
    assert bind_forward_leading_space(" ", PROFILE, ctx) == NBSP
    assert bind_forward_leading_space(" ", PROFILE, ctx) == NBSP
    assert ctx.pending_bind_forward is True
    assert bind_forward_leading_space(" Adequate", PROFILE, ctx) == f"{NBSP}Adequate"
    assert ctx.pending_bind_forward is False
