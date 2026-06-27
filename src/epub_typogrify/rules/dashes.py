"""Dash and hyphen rules (TypographyConversions.md §1.2-1.4, §2.2).

Order matters and is handled within :func:`dash_rule`:

1. ``---`` -> em (or the locale's ``triple_hyphen``), then ``--`` -> the locale's
   ``double_hyphen`` (em for en, en for en-GB);
2. runs of literal em-dash characters collapse to the two-/three-em ligatures;
3. number and roman-numeral ranges take an en dash;
4. a leading hyphen before digits becomes a true minus sign.
"""

from __future__ import annotations

import regex as re

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

# Hyphen runs (guarded so e.g. four hyphens are left untouched).
_TRIPLE_HYPHEN = re.compile(r"(?<!-)---(?!-)")
_DOUBLE_HYPHEN = re.compile(r"(?<!-)--(?!-)")

# Literal em-dash character runs -> ligatures (three before two).
_THREE_EM = re.compile(chars.EM_DASH + r"{3}")
_TWO_EM = re.compile(chars.EM_DASH + r"{2}")

# Ranges and minus.
_NUMERIC_RANGE = re.compile(r"(?<=\d)-(?=\d)")
_ROMAN_RANGE = re.compile(r"(?<![A-Za-z])([IVXLCDM]+)-([IVXLCDM]+)(?![A-Za-z])")
_MINUS = re.compile(r"(?<!\w)-(?=\d)")


def dash_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    dashes = profile.dashes
    text = _TRIPLE_HYPHEN.sub(dashes.triple_hyphen, text)
    text = _DOUBLE_HYPHEN.sub(dashes.double_hyphen, text)
    text = _THREE_EM.sub(chars.THREE_EM_DASH, text)
    text = _TWO_EM.sub(chars.TWO_EM_DASH, text)
    text = _NUMERIC_RANGE.sub(dashes.numeric_range, text)
    text = _ROMAN_RANGE.sub(lambda m: m.group(1) + dashes.numeric_range + m.group(2), text)
    text = _MINUS.sub(chars.MINUS_SIGN, text)
    return text
