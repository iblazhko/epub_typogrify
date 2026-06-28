"""Ellipsis rules (TypographyConversions.md §1.1, §2.5).

:func:`ellipsis_rule` collapses ``...`` and spaced ``. . .`` to a single ellipsis
glyph (runs of four or more dots are left alone). :func:`ellipsis_spacing_rule`
(opt-in) applies the Standard Ebooks spacing convention around the glyph.
"""

from __future__ import annotations

import regex as re

from epub_typogrify import chars
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
    * **After** (§8.7.6.4): a regular space before a following word.
    * **Before following punctuation** (§8.7.6.5): a punctuation space, except before a
      quotation mark, which hugs the ellipsis with no space.
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
            suffix = chars.PUNCTUATION_SPACE
        elif after_char != "":
            suffix = " "
        else:  # run end: a regular space only if content followed (trailing space)
            suffix = " " if trailing_ws else ""

        return prefix + chars.ELLIPSIS + suffix

    result: str = _ELLIPSIS_SPACING.sub(replace, text)
    return result
