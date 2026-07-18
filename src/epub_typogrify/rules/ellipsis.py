"""Ellipsis rules (TypographyConversions.md §1.1, §2.5).

:func:`ellipsis_rule` collapses ``...`` and spaced ``. . .`` to a single ellipsis
glyph, and a trailing sentence-ending ``....`` (three ellipsis dots plus the
sentence's own full stop) to the glyph followed by a literal ``.`` (runs of five
or more dots are left alone). :func:`ellipsis_spacing_rule` (opt-in) applies the
Standard Ebooks spacing convention around the glyph.
"""

from __future__ import annotations

import regex as re

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

# Three dots, optionally separated by horizontal whitespace — including the
# non-breaking/narrow/punctuation/hair spaces a word processor or an earlier
# conversion pass may have already inserted between them, not just a plain
# space/tab — and not part of a longer run of dots. ``(?<!\.)``/``(?!\.)`` keep
# us from biting into four-or-more dots.
_DOT_SPACE = (
    " \t"
    + chars.NO_BREAK_SPACE
    + chars.NARROW_NO_BREAK_SPACE
    + chars.PUNCTUATION_SPACE
    + chars.HAIR_SPACE
)
_THREE_DOTS = r"\.[" + _DOT_SPACE + r"]*\.[" + _DOT_SPACE + r"]*\."
_SPACED_DOTS = re.compile(r"(?<!\.)" + _THREE_DOTS + r"(?!\.)")

# Three (optionally spaced) ellipsis dots immediately followed by one more
# literal, unspaced period: the common convention for a sentence that trails
# off into an ellipsis at its very end ("He said he would go....") — the
# fourth dot is the sentence's own full stop, not part of the ellipsis, so it
# collapses to the glyph plus a literal "." rather than being swallowed.
# ``(?<!\.)``/``(?!\.)`` still exclude runs of five or more dots. Applied
# before ``_SPACED_DOTS`` so the trailing period is consumed as part of this
# match, not left as a lone fourth dot for the plain 3-dot pattern to reject.
_THREE_DOTS_PLUS_PERIOD = re.compile(r"(?<!\.)" + _THREE_DOTS + r"\.(?!\.)")


def ellipsis_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    if not profile.ellipsis.collapse_spaced_dots:
        return text
    text = _THREE_DOTS_PLUS_PERIOD.sub(profile.ellipsis.char + ".", text)
    result: str = _SPACED_DOTS.sub(profile.ellipsis.char, text)
    return result


# --- Standard Ebooks ellipsis spacing (SEMOS §8.7.6) --------------------------

# Spacing characters normalised around an ellipsis (so the rule is idempotent).
_SP = (
    " \t"
    + chars.NO_BREAK_SPACE
    + chars.NARROW_NO_BREAK_SPACE
    + chars.PUNCTUATION_SPACE
    + chars.HAIR_SPACE
    + chars.WORD_JOINER
)
_ELLIPSIS_SPACING = re.compile("([" + _SP + "]*)" + chars.ELLIPSIS + "([" + _SP + "]*)")

# Before-spacing: word joiner + punctuation space + word joiner, so the ellipsis keeps a
# subtle non-breaking gap from the preceding word and never wraps to a new line.
_BEFORE = chars.WORD_JOINER + chars.PUNCTUATION_SPACE + chars.WORD_JOINER

# Same sandwich for the gap before following punctuation (e.g. the "." completing
# "old....") — a bare PUNCTUATION_SPACE is line-break class BA (breakable after),
# *not* non-breaking on its own; only the flanking WORD_JOINERs (class WJ, which
# forbids a break on either side of it) make the gap non-breaking, same as _BEFORE.
_AFTER_PUNCT = chars.WORD_JOINER + chars.PUNCTUATION_SPACE + chars.WORD_JOINER

# After an opening quote the ellipsis hugs it (no space before).
_OPEN_QUOTES = frozenset(
    {chars.LEFT_DOUBLE_QUOTE, chars.LEFT_SINGLE_QUOTE, chars.LEFT_GUILLEMET, '"'}
)
# Before a closing quote the ellipsis hugs it (no space after).
_CLOSE_QUOTES = frozenset(
    {chars.RIGHT_DOUBLE_QUOTE, chars.RIGHT_SINGLE_QUOTE, chars.RIGHT_GUILLEMET, '"'}
)
# Other directly-following punctuation takes a punctuation space.
_FOLLOWING_PUNCT = frozenset(".,;:!?")


def ellipsis_spacing_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Apply the modified Standard Ebooks spacing convention around ellipses (opt-in).

    * **Before** (SEMOS §8.7.6.3): word joiner + punctuation space + word joiner, except
      when the ellipsis begins a block (no preceding word, incl. across an inline
      boundary via ``ctx.run_prev_char``) or directly follows an opening quote.
    * **After** (§8.7.6.4): a regular (breakable) space before a following word.
    * **Before following punctuation** (§8.7.6.5): a non-breaking punctuation space
      (word joiner + punctuation space + word joiner, the same sandwich as "Before"),
      except before a quotation mark, which hugs the ellipsis with no space.
    """

    def replace(match: re.Match[str]) -> str:
        start, end = match.start(), match.end()
        if start > 0:
            before_char = text[start - 1]
        else:
            before_char = ctx.run_prev_char or ""
        after_char = text[end] if end < len(text) else ""
        trailing_ws = bool(match.group(2))

        if before_char == "" or before_char in _OPEN_QUOTES:
            prefix = ""
        else:
            prefix = _BEFORE

        if after_char in _CLOSE_QUOTES:
            suffix = ""
        elif after_char in _FOLLOWING_PUNCT:
            suffix = _AFTER_PUNCT
        elif after_char != "":
            suffix = " "
        else:  # run end: a regular space only if content followed (trailing space)
            suffix = " " if trailing_ws else ""

        return prefix + chars.ELLIPSIS + suffix

    result: str = _ELLIPSIS_SPACING.sub(replace, text)
    return result
