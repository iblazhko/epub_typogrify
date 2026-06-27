"""Punctuation placement relative to closing quotes (TypographyConversions.md §2.7).

Driven by ``profile.quotes.punctuation``:

* ``"typesetters"`` (American) — a trailing period or comma is moved *inside* the
  closing double quote: ``cat”.`` → ``cat.”``.
* ``"logical"`` (British) — left as authored.

Only the unambiguous ``” .`` / ``” ,`` pattern around a closing *double* quote is
touched; the closing single quote is left alone because it cannot be told apart
from an apostrophe with certainty.
"""

from __future__ import annotations

import regex as re

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

# Move the whole run of trailing punctuation before the run of closing quotes,
# but only when no punctuation already precedes them (so we never create a fresh
# ``.”.``). Moving punctuation can make two quotes adjacent and expose a further
# match, so we iterate to a fixed point — punctuation only ever moves leftward,
# so this terminates — and the result is therefore itself idempotent.
_CLOSING_THEN_PUNCT = re.compile(r"(?<![.,])(" + chars.RIGHT_DOUBLE_QUOTE + r"+)([.,]+)")


def punctuation_placement_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    if profile.quotes.punctuation != "typesetters":
        return text
    while True:
        moved: str = _CLOSING_THEN_PUNCT.sub(lambda m: m.group(2) + m.group(1), text)
        if moved == text:
            return text
        text = moved
