"""Interrupted-dialogue dash: always on (where the locale has the convention at
all), independent of ``--normalize-dashes`` (TypographyConversions.md §2.2).

Per ``[CMOS ch.6]``/``[NHR ch.4]``/``[DUDEN]`` this dash is always closed — no
space either side — regardless of the locale's ordinary parenthetical-dash
spacing; English always uses the em dash here, even for ``en-GB`` (whose
ordinary parenthetical dash is a spaced en dash). French marks an interruption
with an ellipsis rather than a dash ``[IN]``, so the rule is out of scope there.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from epub_typogrify import chars
from epub_typogrify.locales.registry import LocaleRegistry
from epub_typogrify.rules.pipeline import build_pipeline

_REG = LocaleRegistry.default()
_GB = _REG.resolve("en-GB")
_EN = _REG.resolve("en")
_DE = _REG.resolve("de")
_FR = _REG.resolve("fr")
assert _GB is not None and _EN is not None and _DE is not None and _FR is not None

EM = chars.EM_DASH
EN = chars.EN_DASH
WJ = chars.WORD_JOINER


def _gb(text: str) -> str:
    return build_pipeline(_GB).run(text)


def _us(text: str) -> str:
    return build_pipeline(_EN).run(text)


def _de(text: str) -> str:
    return build_pipeline(_DE).run(text)


def _fr(text: str) -> str:
    return build_pipeline(_FR).run(text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("what if --", f"what if{WJ}{EM}"),  # nothing follows
        ("what if -- ", f"what if{WJ}{EM}"),  # trailing space stripped
        ("what if --'", f"what if{WJ}{EM}’"),  # tight against trailing punctuation
        ("what if -- '", f"what if{WJ}{EM}’"),  # spacing before punctuation dropped
    ],
)
def test_en_gb_uses_closed_em_dash_not_its_own_spaced_convention(
    text: str, expected: str
) -> None:
    # en-GB's ordinary parenthetical dash is a spaced en dash, but interrupted
    # dialogue is a distinct, universal convention: closed em dash regardless.
    assert _gb(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("what if --", f"what if{WJ}{EM}"),
        ("what if -- ", f"what if{WJ}{EM}"),
        ("what if --'", f"what if{WJ}{EM}’"),
        ("what if -- '", f"what if{WJ}{EM}’"),
    ],
)
def test_en_us_closed_em_dash(text: str, expected: str) -> None:
    assert _us(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("was ich -- ", f"was ich{WJ}{EN}"),
        ("was ich --'", f"was ich{WJ}{EN}’"),
    ],
)
def test_german_uses_its_own_glyph_but_closes_it(text: str, expected: str) -> None:
    # Duden: same Gedankenstrich glyph (en dash) as the ordinary dash, but always
    # closed for an interruption — unlike English, no glyph switch.
    assert _de(text) == expected


def test_french_is_out_of_scope() -> None:
    # French marks interruption with an ellipsis, not a dash: the rule does not
    # apply, and "--" is left exactly as the (locale-agnostic) dash_rule and
    # existing pipeline already handle it, spacing included.
    assert _fr("qu'est-ce que -- ") == f"qu’est-ce que {EM} "
    assert WJ not in _fr("qu'est-ce que -- ")


def test_block_start_dash_is_left_alone() -> None:
    # No preceding word: a dialogue/list dash opening a block, not ending one.
    assert _gb("-- Yes, indeed.") == f"{EN} Yes, indeed."


def test_mid_sentence_double_hyphen_is_unaffected() -> None:
    # More word content follows: not a trailing/interrupted dash, so this is
    # just the ordinary (agnostic) "--" conversion, spacing untouched.
    assert _gb("what if -- we tried") == f"what if {EN} we tried"
    assert _us("done--really well") == f"done{WJ}{EM}really well"


def test_numeric_range_is_unaffected() -> None:
    assert _gb("1914--1918") == f"1914{EN}1918"


@settings(max_examples=300)
@given(st.text(alphabet=st.sampled_from(list("ab 12-'" + EM + EN + WJ)), max_size=40))
def test_default_pipeline_is_idempotent(text: str) -> None:
    for profile in (_GB, _EN, _DE):
        pipeline = build_pipeline(profile)
        once = pipeline.run(text)
        assert pipeline.run(once) == once
