"""The ordered transformation pipeline (TechnicalDesign.md §6c).

A :class:`Pipeline` applies its rules in sequence, threading a single
:class:`ContextState`. :func:`build_pipeline` assembles the Phase 1 rules in the
canonical order; Phase 2 inserts non-breaking spacing and the locale code hooks,
and the cleanup stage stays last.
"""

from __future__ import annotations

from dataclasses import dataclass

from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState, Rule
from epub_typogrify.rules.dashes import dash_rule
from epub_typogrify.rules.ellipsis import ellipsis_rule
from epub_typogrify.rules.fractions import fractions_rule
from epub_typogrify.rules.quotes import smart_quotes_rule
from epub_typogrify.rules.spacing import collapse_whitespace, word_joiner_before_em_dash

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


def build_pipeline(profile: LocaleProfile, *, quotes: bool = True) -> Pipeline:
    """Assemble the Phase 1 pipeline for *profile* in canonical order."""
    rules: list[Rule] = [pre_normalise_rule]
    if quotes:
        rules.append(smart_quotes_rule)
    rules.append(dash_rule)
    rules.append(ellipsis_rule)
    if profile.fractions_enabled:
        rules.append(fractions_rule)
    rules.append(word_joiner_before_em_dash)
    rules.append(collapse_whitespace)
    return Pipeline(tuple(rules), profile)
