"""Opt-in Standard Ebooks ellipsis spacing (TypographyConversions.md §2.5)."""

from __future__ import annotations

import pytest

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.locales.registry import LocaleRegistry
from epub_typogrify.rules.context import ContextState
from epub_typogrify.rules.ellipsis import ellipsis_spacing_rule
from epub_typogrify.rules.pipeline import build_pipeline

_EN = LocaleRegistry.default().resolve("en")
assert _EN is not None

ELL = chars.ELLIPSIS
WJ = chars.WORD_JOINER
PS = chars.PUNCTUATION_SPACE
LDQ = chars.LEFT_DOUBLE_QUOTE
RDQ = chars.RIGHT_DOUBLE_QUOTE
BEFORE = WJ + PS + WJ  # the before-ellipsis sandwich
AFTER_PUNCT = BEFORE  # the identical sandwich, before following punctuation


def _rule(text: str, *, run_prev_char: str | None = None) -> str:
    ctx = ContextState(run_prev_char=run_prev_char)
    return ellipsis_spacing_rule(text, _EN, ctx)


@pytest.mark.parametrize(
    "text, expected",
    [
        # Before a closing quote: tight (no space).
        (f"done{ELL}{RDQ}", f"done{BEFORE}{ELL}{RDQ}"),
        # After an opening quote: tight before, normal after.
        (f"{LDQ}{ELL}and then", f"{LDQ}{ELL} and then"),
        # Before following punctuation: the same non-breaking sandwich as "before".
        (f"done{ELL}!", f"done{BEFORE}{ELL}{AFTER_PUNCT}!"),
        (f"done{ELL}.", f"done{BEFORE}{ELL}{AFTER_PUNCT}."),
    ],
)
def test_spacing(text: str, expected: str) -> None:
    assert _rule(text) == expected


def test_paragraph_start_has_no_before_spacing() -> None:
    # No preceding word (block start) -> no sandwich before.
    assert _rule(f"{ELL}and so") == f"{ELL} and so"


def test_before_spacing_crosses_inline_boundary() -> None:
    # The ellipsis starts the run but a word precedes it in the previous node.
    assert _rule(f"{ELL} more", run_prev_char="d") == f"{BEFORE}{ELL} more"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "no ellipsis here",
        f"word{ELL}",
        f"{LDQ}{ELL}quoted{ELL}{RDQ}",
        f"a{ELL}b{ELL}c",
        f"hungry {ELL} !",
        f"done{ELL}!",
        f"It looks so old{ELL}.",
    ],
)
def test_idempotent(text: str) -> None:
    once = _rule(text)
    assert _rule(once) == once


def test_pipeline_integration_opt_in() -> None:
    # End-to-end through the pipeline: collapse then SE spacing.
    out = build_pipeline(_EN, ellipsis_spacing=True).run("Wait... what")
    assert out == f"Wait{BEFORE}{ELL} what"
    # Off by default: only the glyph collapse, no spacing.
    assert build_pipeline(_EN).run("Wait... what") == f"Wait{ELL} what"


def test_pipeline_integration_sentence_ending_ellipsis() -> None:
    # "...." (3 ellipsis dots + the sentence's own full stop): the collapse
    # rule leaves a literal "." after the glyph, and this rule then spaces it
    # like any other ellipsis-before-punctuation case -- a *non-breaking*
    # punctuation-space sandwich, same as "before", not a bare breakable space.
    out = build_pipeline(_EN, ellipsis_spacing=True).run("It looks so old....")
    assert out == f"It looks so old{BEFORE}{ELL}{AFTER_PUNCT}."


def test_does_not_run_for_disabled_profile_flag() -> None:
    # The rule itself is unconditional; gating is done by the pipeline flag.
    plain: LocaleProfile = _EN
    assert build_pipeline(plain).run(f"x{ELL}y") == f"x{ELL}y"  # no spacing added
