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

Optionally (opt-in, ``--normalize-quote-punctuation``) the engine also relocates
quote-adjacent punctuation across the closing mark per ``quotes.punctuation``:
``typesetters`` (American) pulls a trailing period/comma *inside*; ``logical``
(British) pushes a trailing **comma** *outside* but leaves sentence-terminal
``.``/``!``/``?`` in place (it stays inside a complete-sentence quotation). Done
here — not as a regex — because only the engine knows a given ``’`` is a closing
quote rather than an apostrophe.
"""

from __future__ import annotations

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile, QuotePair, Quotes
from epub_typogrify.rules.context import ContextState, Rule

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


# `typesetters` (American) places both periods and commas inside the quote.
_PULL_INSIDE = frozenset(".,")


def _pop_inner_punct(out: list[str]) -> str:
    """Pop a trailing **comma** from emitted content for the ``logical`` push-outside
    direction.

    Sentence-terminal punctuation (``.``/``!``/``?``) is deliberately *not* moved:
    British logical style keeps it **inside** when the quotation is, or ends with, a
    complete sentence (the common dialogue case — ``‘…around.’``), and only outside
    for an embedded fragment (``‘a disgrace’.``). Reliably telling those apart is an
    NLP-grade problem, so we move only the comma (which is the matrix sentence's, not
    the quote's) and leave terminal punctuation where the author placed it.
    """
    if out and out[-1] == "," and (len(out) < 2 or out[-2] not in _PULL_INSIDE):
        return out.pop()
    return ""


def _following_punct(text: str, j: int, out: list[str]) -> str:
    """A single ``.``/``,`` at ``text[j]`` to pull inside (``typesetters``), unless
    it is part of a run or punctuation already sits just inside the quote."""
    if (
        j < len(text)
        and text[j] in _PULL_INSIDE
        and (j + 1 >= len(text) or text[j + 1] not in _PULL_INSIDE)
    ):
        if out and out[-1] in _PULL_INSIDE:
            return ""  # already punctuation inside — don't duplicate
        return text[j]
    return ""


def _convert(
    text: str,
    profile: LocaleProfile,
    ctx: ContextState,
    *,
    normalize: bool,
    relocate: bool,
) -> str:
    quotes = profile.quotes
    direction = quotes.punctuation if relocate else None  # "typesetters" | "logical" | None
    out: list[str] = []
    prev = ctx.prev_char
    stack = ctx.quote_stack
    n = len(text)
    i = 0

    while i < n:
        char = text[i]
        role, kind = _classify(text, i, prev, stack, normalize)
        if role is None:
            out.append(char)
            prev = char
            i += 1
            continue
        if role == "apostrophe":
            out.append(quotes.apostrophe)
            prev = quotes.apostrophe
            i += 1
            continue
        if role == "open":
            glyph = _pair(quotes, kind, len(stack), normalize).open
            stack.append(kind)
            out.append(glyph)
            prev = glyph
            i += 1
            continue

        # close
        if stack and stack[-1] == kind:
            stack.pop()
        glyph = _pair(quotes, kind, len(stack), normalize).close
        if direction == "logical":
            moved = _pop_inner_punct(out)
            out.append(glyph)
            if moved:
                out.append(moved)
            prev = moved or glyph
            i += 1
            continue
        if direction == "typesetters":
            punct = _following_punct(text, i + 1, out)
            if punct:
                out.append(punct)
                out.append(glyph)
                prev = glyph
                i += 1 + len(punct)
                continue
        out.append(glyph)
        prev = glyph
        i += 1

    ctx.prev_char = prev
    return "".join(out)


def make_quote_rule(*, normalize: bool, relocate: bool) -> Rule:
    """Build the quote rule with the given modes (used by the pipeline)."""

    def rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
        return _convert(text, profile, ctx, normalize=normalize, relocate=relocate)

    return rule


# Convenience rules for the default modes (used directly in tests).
def smart_quotes_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Character-based smart quotes (default): straight ``"``/``'`` only."""
    return _convert(text, profile, ctx, normalize=False, relocate=False)


def normalize_quotes_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Reflow straight *and* curly quotes to the locale's nesting convention."""
    return _convert(text, profile, ctx, normalize=True, relocate=False)
