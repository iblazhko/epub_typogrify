"""Ellipsis rule (TypographyConversions.md §1.1).

``...`` and spaced ``. . .`` collapse to a single ellipsis glyph. Runs of four or
more dots are left alone (four-dot handling is out of Phase 1 scope).
"""

from __future__ import annotations

import regex as re

from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

# Three dots, optionally separated by horizontal whitespace, not part of a longer
# run of dots. ``(?<!\.)``/``(?!\.)`` keep us from biting into four-or-more dots.
_SPACED_DOTS = re.compile(r"(?<!\.)\.[ \t]*\.[ \t]*\.(?!\.)")


def ellipsis_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    if not profile.ellipsis.collapse_spaced_dots:
        return text
    result: str = _SPACED_DOTS.sub(profile.ellipsis.char, text)
    return result
