"""Smart-quote and apostrophe engine (TypographyConversions.md §2.1, §2.7).

Two modes share one scan, which classifies each mark as opening / closing /
apostrophe and tracks nesting depth on ``ctx.quote_stack`` (so a quotation can
span inline markup):

* **Default (character-based).** A straight ``"`` becomes the locale's ``double``
  pair, a straight ``'`` its ``single`` pair (or apostrophe). Existing curly
  quotes are left untouched. This preserves the author's double/single choice.
* **Normalisation (opt-in, ``--normalize-quotes``).** Both straight *and* curly
  quotes are read and re-emitted by **nesting depth** — the outermost level uses
  the locale's ``primary`` pair, the next its ``secondary``, alternating — so a
  document quoted in one convention is reflowed to its locale's convention.

Apostrophes are distinguished from single quotes heuristically (contractions,
possessives, year/decade elisions like ``'92``, and leading elisions like
``'tis``). A residual ambiguity remains for a possessive ``’`` inside a
single-quoted span (``‘the dogs’ bone’``); that is left best-effort.
"""

from __future__ import annotations

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile, QuotePair, Quotes
from epub_typogrify.rules.context import ContextState

_LEFT_DOUBLE = chars.LEFT_DOUBLE_QUOTE
_RIGHT_DOUBLE = chars.RIGHT_DOUBLE_QUOTE
_LEFT_SINGLE = chars.LEFT_SINGLE_QUOTE
_RIGHT_SINGLE = chars.RIGHT_SINGLE_QUOTE

# Characters after which a straight/curly quote is treated as *opening*.
_OPENERS = {
    "(",
    "[",
    "{",
    _LEFT_SINGLE,
    _LEFT_DOUBLE,
    chars.LEFT_GUILLEMET,
    chars.EM_DASH,
    chars.EN_DASH,
}

# Leading elisions the apostrophe heuristic would otherwise read as an opening
# single quote (``'tis`` etc.). Resolved to an apostrophe before glyph selection.
_ELISIONS = (
    "twould",
    "twas",
    "twere",
    "twill",
    "tis",
    "cause",
    "round",
    "bout",
    "neath",
    "gainst",
    "em",
    "n",
)


def _is_opening(prev: str | None) -> bool:
    if prev is None or prev.isspace():
        return True
    return prev in _OPENERS


def _is_elision(text: str, start: int) -> bool:
    rest = text[start:]
    lowered = rest.lower()
    for word in _ELISIONS:
        end = len(word)
        if lowered.startswith(word) and (len(rest) == end or not rest[end].isalnum()):
            return True
    return False


def _classify_single(prev: str | None, nxt: str | None, stack: list[str]) -> str:
    """Return ``"apostrophe"``, ``"open"`` or ``"close"`` for a ``'`` / ``’``."""
    prev_alnum = prev is not None and prev.isalnum()
    next_alnum = nxt is not None and nxt.isalnum()
    single_open = bool(stack) and stack[-1] == "'"

    if prev_alnum and next_alnum:
        return "apostrophe"  # medial: don't, o'clock, it's
    if not prev_alnum and nxt is not None and nxt.isdigit():
        return "apostrophe"  # year/decade elision: '92, '90s
    if single_open and not next_alnum:
        # A single quote is open and this is not a medial apostrophe — close it.
        # (This also covers a close after sentence punctuation, e.g. `not.'`.)
        return "close"
    if prev_alnum and not next_alnum:
        return "apostrophe"  # possessive with nothing open: dogs'
    if not prev_alnum and nxt is not None and nxt.isalpha():
        return "open"
    return "apostrophe"


def _classify(
    text: str, i: int, prev: str | None, stack: list[str], normalize: bool
) -> tuple[str | None, str]:
    """Return ``(role, kind)`` for the mark at *i*.

    ``role`` is ``"open"``/``"close"``/``"apostrophe"`` or ``None`` (passthrough);
    ``kind`` is ``'"'`` (double family) or ``"'"`` (single family).
    """
    char = text[i]
    nxt = text[i + 1] if i + 1 < len(text) else None

    if char == '"':
        return ("open" if _is_opening(prev) else "close"), '"'
    if char == "'":
        role = _classify_single(prev, nxt, stack)
        if role == "open" and _is_elision(text, i + 1):
            return "apostrophe", "'"
        return role, "'"
    if normalize:
        if char == _LEFT_DOUBLE:
            return "open", '"'
        if char == _RIGHT_DOUBLE:
            return "close", '"'
        if char == _LEFT_SINGLE:
            return ("apostrophe" if _is_elision(text, i + 1) else "open"), "'"
        if char == _RIGHT_SINGLE:
            role = _classify_single(prev, nxt, stack)
            return ("apostrophe" if role == "open" else role), "'"
    return None, "'"


def _pair(quotes: Quotes, kind: str, depth: int, normalize: bool) -> QuotePair:
    if normalize:
        return quotes.primary if depth % 2 == 0 else quotes.secondary
    return quotes.double if kind == '"' else quotes.single


def _convert(text: str, profile: LocaleProfile, ctx: ContextState, *, normalize: bool) -> str:
    quotes = profile.quotes
    out: list[str] = []
    prev = ctx.prev_char
    stack = ctx.quote_stack

    for i in range(len(text)):
        char = text[i]
        role, kind = _classify(text, i, prev, stack, normalize)
        if role is None:
            out.append(char)
            prev = char
            continue
        if role == "apostrophe":
            glyph = quotes.apostrophe
        elif role == "open":
            glyph = _pair(quotes, kind, len(stack), normalize).open
            stack.append(kind)
        else:  # close
            if stack and stack[-1] == kind:
                stack.pop()
            glyph = _pair(quotes, kind, len(stack), normalize).close
        out.append(glyph)
        prev = glyph

    ctx.prev_char = prev
    return "".join(out)


def smart_quotes_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Character-based smart quotes (default): straight ``"``/``'`` only."""
    return _convert(text, profile, ctx, normalize=False)


def normalize_quotes_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Reflow straight *and* curly quotes to the locale's nesting convention."""
    return _convert(text, profile, ctx, normalize=True)
