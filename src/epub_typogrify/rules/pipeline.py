"""The ordered transformation pipeline (TechnicalDesign.md §6c).

A :class:`Pipeline` applies its rules in sequence, threading a single
:class:`ContextState`. :func:`build_pipeline` assembles the Phase 1 rules in the
canonical order; Phase 2 inserts non-breaking spacing and the locale code hooks,
and the cleanup stage stays last.
"""

from __future__ import annotations

from dataclasses import dataclass

from epub_typogrify.locales.hooks import hooks_for
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState, Rule
from epub_typogrify.rules.dashes import dash_rule, normalize_parenthetical_dashes
from epub_typogrify.rules.ellipsis import ellipsis_rule
from epub_typogrify.rules.fractions import fractions_rule
from epub_typogrify.rules.punctuation import punctuation_placement_rule
from epub_typogrify.rules.quotes import normalize_quotes_rule, smart_quotes_rule
from epub_typogrify.rules.spacing import (
    collapse_whitespace,
    nonbreaking_abbreviations,
    nonbreaking_units,
    word_joiner_before_em_dash,
)

__all__ = ["ContextState", "Pipeline", "build_pipeline", "pre_normalise_rule"]


def pre_normalise_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Stage 1: normalise Project-Gutenberg-style backtick quoting to straight quotes."""
    return text.replace("``", '"').replace("`", "'")


@dataclass(frozen=True)
class Pipeline:
    """An ordered, reusable sequence of rules bound to a locale profile."""

    rules: tuple[Rule, ...]
    profile: LocaleProfile

    def run(self, text: str, ctx: ContextState | None = None) -> str:
        if ctx is None:
            ctx = ContextState()
        for rule in self.rules:
            text = rule(text, self.profile, ctx)
        if text:
            # Leave the running state pointing at the final emitted character so a
            # following run (Phase 3) resolves its opening quotes correctly.
            ctx.prev_char = text[-1]
        return text


def build_pipeline(
    profile: LocaleProfile,
    *,
    quotes: bool = True,
    normalize_dashes: bool = False,
    normalize_quotes: bool = False,
) -> Pipeline:
    """Assemble the pipeline for *profile* in canonical order (TechnicalDesign §6c).

    ``normalize_dashes`` (opt-in) rewrites existing parenthetical em/en dashes to
    the locale convention (§2.2). ``normalize_quotes`` (opt-in) reflows quotation
    marks — straight or curly — to the locale's nesting convention (§2.7).
    """
    rules: list[Rule] = [pre_normalise_rule]
    if quotes:
        rules.append(normalize_quotes_rule if normalize_quotes else smart_quotes_rule)
    rules.append(dash_rule)
    if normalize_dashes:
        rules.append(normalize_parenthetical_dashes)
    rules.append(ellipsis_rule)
    if profile.fractions_enabled:
        rules.append(fractions_rule)
    # Stage 6: non-breaking spacing.
    rules.append(nonbreaking_abbreviations)
    rules.append(nonbreaking_units)
    rules.append(word_joiner_before_em_dash)
    rules.append(punctuation_placement_rule)
    # Stage 7: locale code hooks (general-to-specific for the resolved tag).
    rules.extend(hooks_for(profile.tag))
    # Stage 8: cleanup.
    rules.append(collapse_whitespace)
    return Pipeline(tuple(rules), profile)
