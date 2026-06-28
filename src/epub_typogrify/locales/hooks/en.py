"""English code hooks (TypographyConversions.md §2.6).

Applies to ``en`` and, via subtag inheritance, to ``en-GB`` and other regions.
"""

from __future__ import annotations

import regex as re

from epub_typogrify import chars
from epub_typogrify.locales.hooks import locale_hook
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

# Note: leading elisions (``'tis`` etc.) are classified as apostrophes by the quote
# engine itself (rules/quotes.py), so they no longer need a hook here.
_MAC = re.compile(r"\bM" + chars.APOSTROPHE + r"([A-Z])")

_IE = re.compile(r"\bi\.\s+e\.")
_EG = re.compile(r"\be\.\s+g\.")
_AD = re.compile(r"\bA\.\s*D\.(?=\s|$)")
_BC = re.compile(r"\bB\.\s*C\.(?=\s|$)")


@locale_hook("en")
def english_contractions(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    return _MAC.sub(lambda m: "Mc" + m.group(1), text)


@locale_hook("en")
def english_latinisms(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    text = _IE.sub("i.e.", text)
    text = _EG.sub("e.g.", text)
    text = _AD.sub("AD", text)
    text = _BC.sub("BC", text)
    return text
