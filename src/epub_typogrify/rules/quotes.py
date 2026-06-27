"""Smart-quote and apostrophe engine (TypographyConversions.md §2.1).

Character-based, like smartypants / ``se``: a straight ``"`` becomes the locale's
``double`` curly pair and a straight ``'`` its ``single`` pair (or apostrophe).
Opening vs closing is decided from the preceding character; ``ctx.quote_stack``
records open quotes so a quotation can span inline markup and so a ``'`` after a
word can be told apart from a possessive apostrophe.

Apostrophes are distinguished from single quotes heuristically. Regular cases
(contractions, possessives, year elisions like ``'92``) are handled here;
genuinely ambiguous leading elisions (``'tis``) are left for the locale code
hooks in Phase 2, as planned.
"""

from __future__ import annotations

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

# Characters after which a straight quote is treated as *opening*.
_OPENERS = {
    "(",
    "[",
    "{",
    chars.LEFT_SINGLE_QUOTE,
    chars.LEFT_DOUBLE_QUOTE,
    chars.LEFT_GUILLEMET,
    chars.EM_DASH,
    chars.EN_DASH,
}


def _is_opening(prev: str | None) -> bool:
    if prev is None or prev.isspace():
        return True
    return prev in _OPENERS


def _classify_single(prev: str | None, nxt: str | None, stack: list[str]) -> str:
    """Return ``"apostrophe"``, ``"open"`` or ``"close"`` for a straight ``'``."""
    prev_alnum = prev is not None and prev.isalnum()
    next_alnum = nxt is not None and nxt.isalnum()

    if prev_alnum and next_alnum:
        return "apostrophe"  # medial: don't, o'clock
    if not prev_alnum and nxt is not None and nxt.isdigit():
        return "apostrophe"  # year/decade elision: '92, '90s
    if prev_alnum and not next_alnum:
        # closing single quote if one is open here, otherwise a possessive
        if stack and stack[-1] == "'":
            return "close"
        return "apostrophe"
    if not prev_alnum and nxt is not None and nxt.isalpha():
        return "open"
    return "apostrophe"


def smart_quotes_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    quotes = profile.quotes
    out: list[str] = []
    prev = ctx.prev_char
    stack = ctx.quote_stack
    length = len(text)

    for i, char in enumerate(text):
        nxt = text[i + 1] if i + 1 < length else None

        if char == '"':
            if _is_opening(prev):
                glyph = quotes.double.open
                stack.append('"')
            else:
                if stack and stack[-1] == '"':
                    stack.pop()
                glyph = quotes.double.close
        elif char == "'":
            kind = _classify_single(prev, nxt, stack)
            if kind == "apostrophe":
                glyph = quotes.apostrophe
            elif kind == "open":
                glyph = quotes.single.open
                stack.append("'")
            else:  # close
                if stack and stack[-1] == "'":
                    stack.pop()
                glyph = quotes.single.close
        else:
            out.append(char)
            prev = char
            continue

        out.append(glyph)
        prev = glyph

    ctx.prev_char = prev
    return "".join(out)
