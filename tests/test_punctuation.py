"""Punctuation placement relative to closing quotes (§2.7)."""

from __future__ import annotations

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState
from epub_typogrify.rules.punctuation import punctuation_placement_rule

RDQ = chars.RIGHT_DOUBLE_QUOTE


def test_typesetters_moves_punctuation_inside(en: LocaleProfile) -> None:
    assert punctuation_placement_rule(f"cat{RDQ}.", en, ContextState()) == f"cat.{RDQ}"
    assert punctuation_placement_rule(f"go{RDQ},", en, ContextState()) == f"go,{RDQ}"
    # idempotent
    assert punctuation_placement_rule(f"cat.{RDQ}", en, ContextState()) == f"cat.{RDQ}"


def test_logical_leaves_punctuation_outside(en_gb: LocaleProfile) -> None:
    assert punctuation_placement_rule(f"cat{RDQ}.", en_gb, ContextState()) == f"cat{RDQ}."
    assert punctuation_placement_rule(f"go{RDQ},", en_gb, ContextState()) == f"go{RDQ},"


def test_stacked_closing_quotes_are_idempotent(en: LocaleProfile) -> None:
    # Punctuation moves before the whole run of closing quotes, so a second pass
    # is a no-op (regression for a Hypothesis-found case).
    once = punctuation_placement_rule(f"x{RDQ}{RDQ}.", en, ContextState())
    assert once == f"x.{RDQ}{RDQ}"
    assert punctuation_placement_rule(once, en, ContextState()) == once
