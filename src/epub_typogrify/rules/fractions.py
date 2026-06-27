"""Common vulgar-fraction rule (TypographyConversions.md §1.5).

A fixed set of ``n/m`` forms map to their Unicode vulgar-fraction glyphs, guarded
so digits or slashes on either side (``11/2``, ``1/24``, dates ``1/2/2020``) are
left alone. Gated on ``profile.fractions_enabled``.
"""

from __future__ import annotations

import regex as re

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

_FRACTIONS: dict[str, str] = {
    "1/2": chars.ONE_HALF,
    "1/3": chars.ONE_THIRD,
    "2/3": chars.TWO_THIRDS,
    "1/4": chars.ONE_QUARTER,
    "3/4": chars.THREE_QUARTERS,
    "1/5": chars.ONE_FIFTH,
    "2/5": chars.TWO_FIFTHS,
    "3/5": chars.THREE_FIFTHS,
    "4/5": chars.FOUR_FIFTHS,
    "1/6": chars.ONE_SIXTH,
    "5/6": chars.FIVE_SIXTHS,
    "1/7": chars.ONE_SEVENTH,
    "1/8": chars.ONE_EIGHTH,
    "3/8": chars.THREE_EIGHTHS,
    "5/8": chars.FIVE_EIGHTHS,
    "7/8": chars.SEVEN_EIGHTHS,
    "1/9": chars.ONE_NINTH,
    "1/10": chars.ONE_TENTH,
}

# Longest keys first so e.g. "1/10" wins over "1/1".
_KEYS = sorted(_FRACTIONS, key=len, reverse=True)
_PATTERN = re.compile(r"(?<![\d/])(" + "|".join(re.escape(k) for k in _KEYS) + r")(?![\d/])")


def fractions_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    if not profile.fractions_enabled:
        return text
    result: str = _PATTERN.sub(lambda m: _FRACTIONS[m.group(1)], text)
    return result
