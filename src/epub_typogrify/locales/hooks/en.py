"""English code hooks (TypographyConversions.md §2.6).

Applies to ``en`` and, via subtag inheritance, to ``en-GB`` and other regions.
"""

from __future__ import annotations

import regex as re

from epub_typogrify import chars
from epub_typogrify.locales.hooks import locale_hook
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

# Leading-apostrophe elisions the quote engine renders as an opening single quote;
# restore the apostrophe (e.g. ‘tis -> ’tis). This is the case the engine
# deliberately leaves for a hook (it cannot tell an elision from an opening quote).
_ELISIONS = ("tis", "twas", "twere", "twould", "twill", "em", "cause", "round", "bout", "n")
_ELISION = re.compile(
    chars.LEFT_SINGLE_QUOTE + r"(" + "|".join(_ELISIONS) + r")\b", flags=re.IGNORECASE
)
_MAC = re.compile(r"\bM" + chars.APOSTROPHE + r"([A-Z])")

_IE = re.compile(r"\bi\.\s+e\.")
_EG = re.compile(r"\be\.\s+g\.")
_AD = re.compile(r"\bA\.\s*D\.(?=\s|$)")
_BC = re.compile(r"\bB\.\s*C\.(?=\s|$)")


@locale_hook("en")
def english_contractions(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    text = _ELISION.sub(lambda m: chars.APOSTROPHE + m.group(1), text)
    text = _MAC.sub(lambda m: "Mc" + m.group(1), text)
    return text


@locale_hook("en")
def english_latinisms(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    text = _IE.sub("i.e.", text)
    text = _EG.sub("e.g.", text)
    text = _AD.sub("AD", text)
    text = _BC.sub("BC", text)
    return text
