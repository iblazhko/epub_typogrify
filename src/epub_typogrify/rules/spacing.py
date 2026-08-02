"""Spacing rules.

Phase 1: word joiner before em dashes (§1.6) and whitespace cleanup (§1.7).
Phase 2: non-breaking spaces that keep paired tokens together (§2.3) —
abbreviations bound to the following word, units bound to a preceding number,
and a person's initials bound to each other and to the surname that follows.
The abbreviation/initials binding also works across an inline-markup boundary
(e.g. an abbreviation wrapped in ``<abbr>``, its target word a sibling text
node) via `ContextState.pending_bind_forward` and `bind_forward_leading_space`.
French high-punctuation spacing (§2.4) lives in the French code hook.
"""

from __future__ import annotations

import functools

import regex as re

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.rules.context import ContextState

_DASHES = chars.EM_DASH + chars.TWO_EM_DASH + chars.THREE_EM_DASH
# An em/two-em/three-em dash directly preceded by a non-space, non-joiner,
# non-dash character: insert a word joiner so the line cannot break before it.
_BEFORE_DASH = re.compile(r"(?<![\s" + chars.WORD_JOINER + _DASHES + r"])([" + _DASHES + r"])")

_MULTI_SPACE = re.compile(r" {2,}")
_MULTI_NBSP = re.compile(chars.NO_BREAK_SPACE + r"{2,}")


def word_joiner_before_em_dash(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    result: str = _BEFORE_DASH.sub(lambda m: chars.WORD_JOINER + m.group(1), text)
    return result


def collapse_whitespace(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_NBSP.sub(chars.NO_BREAK_SPACE, text)
    return text


@functools.cache
def _abbreviation_pattern(abbreviations: tuple[str, ...]) -> re.Pattern[str]:
    # Longest first so e.g. "Mrs." wins over "Mr."; bind the abbreviation to the
    # following word via a non-breaking space.
    alternatives = "|".join(re.escape(a) for a in sorted(abbreviations, key=len, reverse=True))
    return re.compile(r"(?<!\w)(" + alternatives + r") +(?=\w)")


@functools.cache
def _abbreviation_end_pattern(abbreviations: tuple[str, ...]) -> re.Pattern[str]:
    # Same alternatives as `_abbreviation_pattern`, anchored at the end of the
    # string with no following word required in *this* string -- used to detect
    # a run that ends in an abbreviation with nothing left to bind to locally
    # (e.g. the text of an `<abbr>Mr.</abbr>` element), so the following run can
    # pick up the binding (see `bind_forward_leading_space`).
    alternatives = "|".join(re.escape(a) for a in sorted(abbreviations, key=len, reverse=True))
    return re.compile(r"(?<!\w)(?:" + alternatives + r")$")


@functools.cache
def _abbreviation_trailing_space_pattern(abbreviations: tuple[str, ...]) -> re.Pattern[str]:
    # Same alternatives, but for an abbreviation followed by trailing space(s)
    # and nothing else in *this* string -- e.g. a run ending "...on Mr. " right
    # before an inline element holding the target word
    # (`Mr. <em>Adequate</em>`). The mirror image of `_abbreviation_end_pattern`
    # (no trailing space) -- here the space to convert is already in this run,
    # so no `ctx.pending_bind_forward` signalling is needed; it binds directly.
    alternatives = "|".join(re.escape(a) for a in sorted(abbreviations, key=len, reverse=True))
    return re.compile(r"(?<!\w)(" + alternatives + r") +$")


@functools.cache
def _units_pattern(units: tuple[str, ...]) -> re.Pattern[str]:
    alternatives = "|".join(re.escape(u) for u in sorted(units, key=len, reverse=True))
    return re.compile(r"(\d) +(" + alternatives + r")(?!\w)")


def nonbreaking_abbreviations(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Bind an abbreviation (``Mr.``, ``No.``, …) to the following word (§2.3).

    Also works **across an inline-markup boundary**, in both directions:

    - The abbreviation's own run has no following word (e.g. the text of an
      ``<abbr epub:type="z3998:name-title">Mr.</abbr>`` element, whose target
      name is a *later* sibling node): sets ``ctx.pending_bind_forward``,
      consumed by ``bind_forward_leading_space`` at the start of the next run.
    - The abbreviation's own run trails off with nothing but whitespace after
      it (e.g. ``Mr. <em>Adequate</em>`` -- the target name is inside a
      *following* inline element, not a plain sibling text node): bound
      directly here, since the space to convert is already in this run.
    """
    abbreviations = profile.abbreviations.nonbreaking
    if not abbreviations:
        return text
    nbsp = profile.spaces.nbsp
    pattern = _abbreviation_pattern(abbreviations)
    result: str = pattern.sub(lambda m: m.group(1) + nbsp, text)
    result = _abbreviation_trailing_space_pattern(abbreviations).sub(
        lambda m: m.group(1) + nbsp, result
    )
    ctx.pending_bind_forward = bool(_abbreviation_end_pattern(abbreviations).search(result))
    return result


_LEADING_SPACE_BEFORE_WORD = re.compile(r"^ +(?=\w)")
_ALL_SPACES = re.compile(r"^ +$")


def bind_forward_leading_space(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Consume ``ctx.pending_bind_forward`` (§2.3): if the previous run ended in
    an abbreviation or a run of initials with nothing left in that run to bind
    to, and this run opens with one or more ordinary spaces before a word, turn
    that leading whitespace into a single non-breaking space so the two stay
    together across the markup boundary that split them (e.g.
    ``<abbr>Mr.</abbr> Adequate``).

    A run that is *itself* nothing but the separating space between two inline
    elements (e.g. the gap in ``<strong>Mr.</strong> <em>Adequate</em>`` --
    neither sibling node holds a word for that gap's own text to look ahead
    to) is bound too: it becomes a lone non-breaking space, and the flag stays
    armed for the run after *that*, which is where the actual word is.

    One-shot per word-bearing run: the flag is cleared once this run contains
    anything other than pure whitespace, whether or not the leading-space
    conversion ends up applying to it -- it is only ever valid for the run(s)
    immediately following the one that set it, up to and including the first
    one that isn't pure whitespace.
    """
    if not ctx.pending_bind_forward:
        return text
    nbsp = profile.spaces.nbsp
    if _ALL_SPACES.fullmatch(text):
        return nbsp  # still no word in sight; stay armed for the next run
    ctx.pending_bind_forward = False
    result: str = _LEADING_SPACE_BEFORE_WORD.sub(nbsp, text, count=1)
    return result


def nonbreaking_units(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Bind a unit (``km``, ``%``, ``°C``, …) to a preceding number (§2.3)."""
    units = profile.keep_together.units
    if not units:
        return text
    nbsp = profile.spaces.nbsp
    pattern = _units_pattern(units)
    result: str = pattern.sub(lambda m: m.group(1) + nbsp + m.group(2), text)
    return result


# Two or more "capital letter + full stop" groups (optionally spaced, as some
# house styles set ``J. M.`` rather than ``J.M.``), immediately followed by a
# capitalised word — a person's initials followed by their surname. A single
# ``[A-Z].`` is deliberately excluded: on its own it is indistinguishable from
# a list/outline marker ("A. The first point…"), which must not be bound to
# the sentence that follows it.
_INITIALS = re.compile(r"\b(?:\p{Lu}\. ?){2,}(?=\p{Lu})")

# Same shape as `_INITIALS`, anchored at the end of the string instead of
# requiring a following capitalised word in *this* string -- a run of initials
# whose surname is a sibling node (e.g. `<abbr>V. S.</abbr> Naipaul`) has no
# lookahead target to match against here. Still requires 2+ groups, same as
# `_INITIALS` and for the same reason (a single trailing initial is still
# indistinguishable from a list/outline marker, even at a markup boundary).
_INITIALS_END = re.compile(r"\b(?:\p{Lu}\. ?){2,}$")


def nonbreaking_initials(text: str, profile: LocaleProfile, ctx: ContextState) -> str:
    """Bind a run of initials to each other and to the following surname (§2.3),
    e.g. ``J.M. Coetzee`` -> ``J.M.<nbsp>Coetzee``, ``V. S. Naipaul`` ->
    ``V.<nbsp>S.<nbsp>Naipaul``. Locale-independent: unlike
    `nonbreaking_abbreviations`, this is a closed-class *pattern* (any capital
    letter), not a per-locale word list.

    Also works **across an inline-markup boundary**: a run of initials at the
    very end of this run, with its surname a sibling node (e.g. the text of an
    ``<abbr epub:type="z3998:given-name">V. S.</abbr>`` element), is bound
    internally here (``V. S.`` -> ``V.<nbsp>S.``, same as the intra-run case)
    and sets ``ctx.pending_bind_forward`` so ``bind_forward_leading_space``
    binds it to the surname when it appears in the next run.
    """
    nbsp = profile.spaces.nbsp
    result: str = _INITIALS.sub(lambda m: m.group().replace(" ", nbsp), text)
    end_match = _INITIALS_END.search(result)
    if end_match:
        matched = end_match.group()
        bound = matched.replace(" ", nbsp)
        if bound != matched:
            result = result[: end_match.start()] + bound
        ctx.pending_bind_forward = True
    return result
