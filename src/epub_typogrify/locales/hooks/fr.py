"""French code hook: narrow no-break space around high punctuation and guillemets
(TypographyConversions.md §2.4).

Existing spacing before ``; : ! ?`` and inside ``« »`` is normalised to a single
narrow no-break space, driven by the ``spaces`` profile flags.
"""

from __future__ import annotations

import regex as re

from epub_typogrify import chars
from epub_typogrify.locales.hooks import locale_hook
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

# Any run of space / no-break / narrow-no-break (so the rule is idempotent).
_SPACE = "[ " + chars.NO_BREAK_SPACE + chars.NARROW_NO_BREAK_SPACE + "]+"
_HIGH_PUNCT = re.compile(_SPACE + r"([;:!?])")
_AFTER_GUILLEMET = re.compile(chars.LEFT_GUILLEMET + _SPACE)
_BEFORE_GUILLEMET = re.compile(_SPACE + chars.RIGHT_GUILLEMET)


@locale_hook("fr")
def french_spacing(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    spaces = profile.spaces
    narrow = spaces.narrow_nbsp
    if spaces.before_high_punctuation:
        text = _HIGH_PUNCT.sub(lambda m: narrow + m.group(1), text)
    if spaces.guillemet_inner:
        text = _AFTER_GUILLEMET.sub(chars.LEFT_GUILLEMET + narrow, text)
        text = _BEFORE_GUILLEMET.sub(narrow + chars.RIGHT_GUILLEMET, text)
    return text
