"""Named Unicode constants shared across the package.

Single source of truth for the literal characters the typographic rules emit, so
no module instantiates ``chr(0x...)`` in place. Characters are defined via
``chr(0x...)`` here (and only here) to keep the source pure ASCII; the comment on
each line names the glyph.
"""

from __future__ import annotations

# --- Punctuation and dashes ---
ELLIPSIS = chr(0x2026)  # …  HORIZONTAL ELLIPSIS
EM_DASH = chr(0x2014)  # —  EM DASH
EN_DASH = chr(0x2013)  # –  EN DASH
TWO_EM_DASH = chr(0x2E3A)  # TWO-EM DASH
THREE_EM_DASH = chr(0x2E3B)  # THREE-EM DASH
MINUS_SIGN = chr(0x2212)  # MINUS SIGN

# --- Spaces and joiners (invisible) ---
WORD_JOINER = chr(0x2060)  # WORD JOINER
NO_BREAK_SPACE = chr(0x00A0)  # NO-BREAK SPACE
NARROW_NO_BREAK_SPACE = chr(0x202F)  # NARROW NO-BREAK SPACE
PUNCTUATION_SPACE = chr(0x2008)  # PUNCTUATION SPACE
HAIR_SPACE = chr(0x200A)  # HAIR SPACE

# --- Quotation marks ---
LEFT_DOUBLE_QUOTE = chr(0x201C)  # “
RIGHT_DOUBLE_QUOTE = chr(0x201D)  # ”
LEFT_SINGLE_QUOTE = chr(0x2018)  # ‘
RIGHT_SINGLE_QUOTE = chr(0x2019)  # ’  (also the apostrophe)
APOSTROPHE = RIGHT_SINGLE_QUOTE  # ’  (semantic alias)
LEFT_GUILLEMET = chr(0x00AB)  # «
RIGHT_GUILLEMET = chr(0x00BB)  # »
# German low/high quotation marks (closing marks reuse the left-pointing glyphs).
LEFT_LOW_DOUBLE_QUOTE = chr(0x201E)  # „
LEFT_LOW_SINGLE_QUOTE = chr(0x201A)  # ‚

# --- Vulgar fractions ---
ONE_HALF = chr(0x00BD)  # ½
ONE_THIRD = chr(0x2153)  # ⅓
TWO_THIRDS = chr(0x2154)  # ⅔
ONE_QUARTER = chr(0x00BC)  # ¼
THREE_QUARTERS = chr(0x00BE)  # ¾
ONE_FIFTH = chr(0x2155)  # ⅕
TWO_FIFTHS = chr(0x2156)  # ⅖
THREE_FIFTHS = chr(0x2157)  # ⅗
FOUR_FIFTHS = chr(0x2158)  # ⅘
ONE_SIXTH = chr(0x2159)  # ⅙
FIVE_SIXTHS = chr(0x215A)  # ⅚
ONE_SEVENTH = chr(0x2150)  # ⅐
ONE_EIGHTH = chr(0x215B)  # ⅛
THREE_EIGHTHS = chr(0x215C)  # ⅜
FIVE_EIGHTHS = chr(0x215D)  # ⅝
SEVEN_EIGHTHS = chr(0x215E)  # ⅞
ONE_NINTH = chr(0x2151)  # ⅑
ONE_TENTH = chr(0x2152)  # ⅒
