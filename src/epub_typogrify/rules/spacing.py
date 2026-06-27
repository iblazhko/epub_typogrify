"""Spacing rules — Phase 1 (language-agnostic) portion.

Covers the word joiner before em dashes (§1.6) and whitespace cleanup (§1.7).
Locale-specific non-breaking spacing (abbreviations, French high punctuation) is
added to this module in Phase 2.
"""

from __future__ import annotations

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
