"""Profiles used across the rule tests.

Constructed directly (not loaded from TOML) so the rule tests don't depend on the
Phase 2 locale data. The values mirror ``doc/TechnicalDesign.md`` §6a.
"""

from __future__ import annotations

from epub_typogrify import chars
from epub_typogrify.locales.profile import Dashes, LocaleProfile, QuotePair, Quotes

# Quote glyphs are shared between en and en-GB (same Unicode marks); the British
# differences are punctuation placement, abbreviations, and the dash.
_DOUBLE = QuotePair(chars.LEFT_DOUBLE_QUOTE, chars.RIGHT_DOUBLE_QUOTE)
_SINGLE = QuotePair(chars.LEFT_SINGLE_QUOTE, chars.RIGHT_SINGLE_QUOTE)

EN = LocaleProfile(
    tag="en",
    quotes=Quotes(double=_DOUBLE, single=_SINGLE, punctuation="typesetters"),
    dashes=Dashes(double_hyphen=chars.EM_DASH),  # `--` -> em
)

EN_GB = LocaleProfile(
    tag="en-GB",
    quotes=Quotes(double=_DOUBLE, single=_SINGLE, punctuation="logical"),
    dashes=Dashes(double_hyphen=chars.EN_DASH),  # `--` -> en
)
