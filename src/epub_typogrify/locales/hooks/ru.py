"""Russian code hooks (TypographyConversions.md §2.x).

Two irregularities a plain word list can't express:

* Fixed lowercase compound abbreviations (``т. д.``, ``н. э.``, …) — the generic
  initials-binding pattern (``rules/spacing.py``) only matches *capitalised*
  ``\\p{Lu}.`` groups, so these lowercase idioms need their own regex to bind
  their *internal* spacing, distinct from ``abbreviations.nonbreaking`` (which
  only binds a single token to the word *after* it).
* An opt-in short-word (single-letter preposition/conjunction) binding, gated by
  ``profile.spaces.nbsp_after_short_words`` — off unless a project turns it on.
"""

from __future__ import annotations

import regex as re

from epub_typogrify.locales.hooks import locale_hook
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

# Fixed lowercase compound abbreviations: an optional leading "и" (as in
# "и т. д."), then "т." plus one particle letter, or the era marker "н. э."
# (optionally preceded by "до"). Case-insensitive so a sentence-initial "Т. д."
# still binds. Matched as a single alternation so overlapping candidates (e.g.
# "т. е." inside "и т. д.") don't fight each other.
_COMPOUND = re.compile(
    r"\b(и\s+)?(т\.)\s+([дпекн]\.)"  # и т. д. / т. п. / т. е. / т. к. / т. н.
    r"|\b(до\s+)?(н\.)\s+(э\.)",  # н. э. / до н. э.
    re.IGNORECASE,
)


@locale_hook("ru")
def russian_compound_abbreviations(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    nbsp = profile.spaces.nbsp

    def replace(m: re.Match[str]) -> str:
        groups = [g for g in m.groups() if g is not None]
        return nbsp.join(g.rstrip() for g in groups)

    return _COMPOUND.sub(replace, text)


# Common single-letter and short prepositions/conjunctions/particles [MC][KOV].
_SHORT_WORDS = (
    "а",
    "б",
    "в",
    "и",
    "к",
    "о",
    "с",
    "у",
    "я",
    "во",
    "из",
    "ко",
    "на",
    "не",
    "ни",
    "но",
    "об",
    "от",
    "по",
    "со",
    "то",
    "уж",
)
_SHORT_WORD_PATTERN = re.compile(
    r"(?<!\w)(" + "|".join(sorted(_SHORT_WORDS, key=len, reverse=True)) + r") +(?=\w)",
    re.IGNORECASE,
)


@locale_hook("ru")
def russian_short_word_nbsp(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    if not profile.spaces.nbsp_after_short_words:
        return text
    nbsp = profile.spaces.nbsp
    return _SHORT_WORD_PATTERN.sub(lambda m: m.group(1) + nbsp, text)
