"""Dash and hyphen rules (TypographyConversions.md §1.2-1.4, §2.2).

Order matters and is handled within :func:`dash_rule`:

1. ``---`` -> em (or the locale's ``triple_hyphen``), then ``--`` -> the locale's
   ``double_hyphen`` (em for en, en for en-GB);
2. runs of literal em-dash characters collapse to the two-/three-em ligatures;
3. number and roman-numeral ranges take an en dash;
4. a leading hyphen before digits becomes a true minus sign.
"""

from __future__ import annotations

import regex as re

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

# Hyphen runs (guarded so e.g. four hyphens are left untouched).
_TRIPLE_HYPHEN = re.compile(r"(?<!-)---(?!-)")
_DOUBLE_HYPHEN = re.compile(r"(?<!-)--(?!-)")

# Literal em-dash character runs -> ligatures (three before two).
_THREE_EM = re.compile(chars.EM_DASH + r"{3}")
_TWO_EM = re.compile(chars.EM_DASH + r"{2}")

# Ranges and minus.
_NUMERIC_RANGE = re.compile(r"(?<=\d)-(?=\d)")
_ROMAN_RANGE = re.compile(r"(?<![A-Za-z])([IVXLCDM]+)-([IVXLCDM]+)(?![A-Za-z])")
_MINUS = re.compile(r"(?<!\w)-(?=\d)")


def dash_rule(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    dashes = profile.dashes
    text = _TRIPLE_HYPHEN.sub(dashes.triple_hyphen, text)
    text = _DOUBLE_HYPHEN.sub(dashes.double_hyphen, text)
    text = _THREE_EM.sub(chars.THREE_EM_DASH, text)
    text = _TWO_EM.sub(chars.TWO_EM_DASH, text)
    text = _NUMERIC_RANGE.sub(dashes.numeric_range, text)
    text = _ROMAN_RANGE.sub(lambda m: m.group(1) + dashes.numeric_range + m.group(2), text)
    text = _MINUS.sub(chars.MINUS_SIGN, text)
    return text


# A single em/en dash with any surrounding spacing — and an absorbed word joiner,
# which a later stage may have inserted before an em dash on a previous run (so it
# is not left orphaned, and the rule stays idempotent) — or a lone ASCII hyphen
# with the same affix spacing on both sides, the shorthand some authors use for a
# parenthetical dash in place of "--"/an em dash. Requiring the affix (not just
# any character) keeps a hyphenated compound (``well-known``) untouched, and the
# ``(?<!-)``/``(?!-)`` guards keep a longer hyphen run from matching. Consuming
# the affix as part of the match (rather than a zero-width lookaround) matters for
# idempotency: it stops an alternative from starting mid-match on affix an earlier
# pass already inserted — and both arms must consume the *same* affix set (word
# joiner included), or one pass strands a word joiner next to the rewritten dash
# for a second pass to swallow and discard: same text, a different number of
# passes to reach the fixed point.
_AFFIX = " " + chars.NO_BREAK_SPACE + chars.NARROW_NO_BREAK_SPACE + chars.WORD_JOINER
_PARENTHETICAL_DASH = re.compile(
    "[" + _AFFIX + "]*([" + chars.EM_DASH + chars.EN_DASH + "])[" + _AFFIX + "]*"
    "|[" + _AFFIX + r"]+(?<!-)-(?!-)[" + _AFFIX + "]+"
)
_TRANSPARENT = frozenset(_AFFIX)
# Dash-like characters a neighbour check must not treat as ordinary content: the
# two single dashes this rule rewrites, plus the two-/three-em ligatures it
# leaves alone — the ligature is never affix, so a neighbouring word joiner
# resolves *past* it to whatever word joiner previously protected it against,
# which must still be recognised as "a dash sits here", not a letter.
_DASHES = frozenset(chars.EM_DASH + chars.EN_DASH + chars.TWO_EM_DASH + chars.THREE_EM_DASH)


def _neighbour(text: str, index: int, step: int) -> str:
    while 0 <= index < len(text) and text[index] in _TRANSPARENT:
        index += step
    return text[index] if 0 <= index < len(text) else ""


def normalize_parenthetical_dashes(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Normalise an existing parenthetical em/en dash to the locale convention
    (opt-in, TypographyConversions.md §2.2): glyph from ``dashes.double_hyphen``
    and spacing from ``dashes.parenthetical_spacing`` — closed (``cat—black``) for
    American English, spaced (``cat – black``) for British English.

    Works across inline-markup boundaries: a dash at the *start* of a run takes its
    preceding neighbour from ``ctx.run_prev_char`` (the word in the previous inline
    node), and a dash with trailing whitespace at the *end* of a run is treated as
    having following content in the next node. So
    ``<em>this is it</em> – business`` and ``this is it – <em>business</em>`` both
    bind the dash to the preceding word.

    A dash is bound to its preceding word whenever it has one — including a
    trailing dash at the end of a paragraph (interrupted speech), which keeps the
    non-breaking space but no following space (``gotta␣ₙ–``). Left untouched:
    numeric ranges (digits on both sides), the two-/three-em ligatures, a dash with
    *no* preceding word (a block-start dialogue/list dash), and a dash whose
    neighbour is itself a dash (a dash *run*).

    Also recognises a lone ASCII hyphen flanked by whitespace (``big question -
    whether``) — a common substitute for ``--``/an em dash — and folds it into the
    same treatment. A hyphenated compound (``well-known``) is unaffected, since
    that has no whitespace on either side.
    """
    glyph = profile.dashes.double_hyphen
    spaced = profile.dashes.parenthetical_spacing == "spaced"

    def replace(match: re.Match[str]) -> str:
        whole: str = match.group(0)
        # Preceding neighbour: local, or — at the run start — the last char of the
        # previous run (the word in a preceding inline node). A previous run ending
        # in whitespace, or a block start (None), counts as no preceding word.
        if match.start() > 0:
            before = _neighbour(text, match.start() - 1, -1)
        else:
            prev = ctx.run_prev_char
            before = prev if prev and not prev.isspace() else ""
        # Following neighbour: local, or — when the run ends right after the dash's
        # trailing space — assume content follows in the next inline node.
        after = _neighbour(text, match.end(), 1)
        if after == "" and whole[-1] in _TRANSPARENT and whole[-1] != chars.WORD_JOINER:
            after = " "  # trailing space before a markup boundary

        if before in _DASHES or after in _DASHES:
            return whole  # part of a dash run, not a clean parenthetical
        if before.isdigit() and after.isdigit():
            return whole  # numeric range
        if before == "":
            return whole  # no preceding word: block-start dialogue/list dash

        if spaced:
            # Bind to the preceding word; keep a following space only when content
            # follows (a trailing/interrupted dash ends the line at the dash).
            return chars.NO_BREAK_SPACE + glyph + (" " if after else "")
        return glyph

    result: str = _PARENTHETICAL_DASH.sub(replace, text)
    return result


# --- Interrupted dialogue: a dash that ends a run of speech -------------------

# Trailing punctuation after the dash (a closing quote ending the dialogue, most
# commonly) — anything that isn't a word character, whitespace, a dash (single or
# the two-/three-em ligatures — a ligature right after our dash is a dash run,
# not punctuation to touch), or the word joiner (an invisible formatting
# character, already claimed by the gap above as ordinary affix).
_TRAILING_PUNCT = (
    r"[^\w\s"
    + chars.EM_DASH
    + chars.EN_DASH
    + chars.TWO_EM_DASH
    + chars.THREE_EM_DASH
    + chars.WORD_JOINER
    + r"]*"
)
_TRAILING_DIALOGUE_DASH = re.compile(
    "[" + _AFFIX + "]*([" + chars.EM_DASH + chars.EN_DASH + "])"
    "[" + _AFFIX + "]*(" + _TRAILING_PUNCT + ")$"
)


def bind_interrupted_dialogue_dash(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Bind a dash ending a run of dialogue (interrupted speech) to its preceding
    word — always on, independent of ``--normalize-dashes`` (TypographyConversions.md
    §2.2): a dash at the very end of a run — a paragraph, or an inline element with
    nothing left in it — is unambiguously the interrupted-speech marker, not a
    stylistic dash choice under review. A no-op where the locale has no such
    convention (``profile.dashes.interrupted_dialogue`` is ``None`` — French marks
    this with an ellipsis instead, so the rule is absent from its pipeline).

    Per ``[CMOS ch.6]``/``[NHR ch.4]``/``[DUDEN]``, this dash is always **closed**
    — no space before the preceding word (protected from wrapping by a word
    joiner instead), none after, whether the run ends right there or a closing
    quote follows — regardless of the locale's ordinary ``parenthetical_spacing``
    (British prose is spaced for an aside but still closes up an interruption).
    The glyph is ``dashes.interrupted_dialogue``, which need not match
    ``double_hyphen``: English always uses the em dash here even where its
    general parenthetical dash is an en dash (``en-GB``).

    Only a dash that is the *last* thing in its **block** counts
    (``ctx.run_is_block_final``, set by the ``TextWalker`` — a run ending merely
    because an inline element follows, e.g. ``it – <em>business</em>``, is not
    this) — optionally followed by trailing punctuation but no further word
    content — and only when it has a preceding word; a dash with none (a
    block-start dialogue/list dash, e.g. ``– Yes``) is left alone, as is a dash
    that is itself part of a dash run.
    """
    glyph = profile.dashes.interrupted_dialogue
    if glyph is None:
        return text

    def replace(match: re.Match[str]) -> str:
        if not ctx.run_is_block_final:
            return match.group(0)  # more content follows later in the block
        if match.start() > 0:
            before = text[match.start() - 1]
        else:
            before = ctx.run_prev_char or ""
        if not before or before in _DASHES:
            return match.group(0)  # block-start dash, or part of a dash run

        punct = match.group(2)
        return chars.WORD_JOINER + glyph + punct

    result: str = _TRAILING_DIALOGUE_DASH.sub(replace, text)
    return result
