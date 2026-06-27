"""Spacing rules.

Phase 1: word joiner before em dashes (§1.6) and whitespace cleanup (§1.7).
Phase 2: non-breaking spaces that keep paired tokens together (§2.3) —
abbreviations bound to the following word, and units bound to a preceding number.
French high-punctuation spacing (§2.4) lives in the French code hook.
"""

from __future__ import annotations

import functools

import regex as re

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

_DASHES = chars.EM_DASH + chars.TWO_EM_DASH + chars.THREE_EM_DASH
# An em/two-em/three-em dash directly preceded by a non-space, non-joiner,
# non-dash character: insert a word joiner so the line cannot break before it.
_BEFORE_DASH = re.compile(r"(?<![\s" + chars.WORD_JOINER + _DASHES + r"])([" + _DASHES + r"])")

_MULTI_SPACE = re.compile(r" {2,}")
_MULTI_NBSP = re.compile(chars.NO_BREAK_SPACE + r"{2,}")


def word_joiner_before_em_dash(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    result: str = _BEFORE_DASH.sub(lambda m: chars.WORD_JOINER + m.group(1), text)
    return result


def collapse_whitespace(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_NBSP.sub(chars.NO_BREAK_SPACE, text)
    return text


@functools.cache
def _abbreviation_pattern(abbreviations: tuple[str, ...]) -> re.Pattern[str]:
    # Longest first so e.g. "Mrs." wins over "Mr."; bind the abbreviation to the
    # following word via a non-breaking space.
    alternatives = "|".join(re.escape(a) for a in sorted(abbreviations, key=len, reverse=True))
    return re.compile(r"(?<!\w)(" + alternatives + r") +(?=\w)")


@functools.cache
def _units_pattern(units: tuple[str, ...]) -> re.Pattern[str]:
    alternatives = "|".join(re.escape(u) for u in sorted(units, key=len, reverse=True))
    return re.compile(r"(\d) +(" + alternatives + r")(?!\w)")


def nonbreaking_abbreviations(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Bind an abbreviation (``Mr.``, ``No.``, …) to the following word (§2.3)."""
    abbreviations = profile.abbreviations.nonbreaking
    if not abbreviations:
        return text
    nbsp = profile.spaces.nbsp
    pattern = _abbreviation_pattern(abbreviations)
    result: str = pattern.sub(lambda m: m.group(1) + nbsp, text)
    return result


def nonbreaking_units(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Bind a unit (``km``, ``%``, ``°C``, …) to a preceding number (§2.3)."""
    units = profile.keep_together.units
    if not units:
        return text
    nbsp = profile.spaces.nbsp
    pattern = _units_pattern(units)
    result: str = pattern.sub(lambda m: m.group(1) + nbsp + m.group(2), text)
    return result
