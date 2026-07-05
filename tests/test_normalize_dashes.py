"""Opt-in normalisation of parenthetical dashes (TypographyConversions.md §2.2)."""

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
assert _GB is not None and _EN is not None

EM = chars.EM_DASH
EN = chars.EN_DASH
NBSP = chars.NO_BREAK_SPACE
WJ = chars.WORD_JOINER


def _gb(text: str) -> str:
    return build_pipeline(_GB, normalize_dashes=True).run(text)


def _us(text: str) -> str:
    return build_pipeline(_EN, normalize_dashes=True).run(text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (f"cat{EM}black", f"cat{NBSP}{EN} black"),  # em, closed -> spaced en
        (f"cat {EM} black", f"cat{NBSP}{EN} black"),  # em, spaced -> spaced en
        (f"cat{EN}black", f"cat{NBSP}{EN} black"),  # en, closed -> spaced en
        (f"a{EM}b{EM}c", f"a{NBSP}{EN} b{NBSP}{EN} c"),  # multiple
    ],
)
def test_en_gb_spaced_en_dash(text: str, expected: str) -> None:
    assert _gb(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (f"cat {EM} black", f"cat{WJ}{EM}black"),  # em, spaced -> closed em (+ word joiner)
        (f"cat {EN} black", f"cat{WJ}{EM}black"),  # en -> closed em
    ],
)
def test_en_us_closed_em_dash(text: str, expected: str) -> None:
    assert _us(text) == expected


def test_ranges_and_dialogue_dashes_are_left_alone() -> None:
    assert _gb("1914-1918") == f"1914{EN}1918"  # hyphen range -> en (normal rule)
    assert _gb(f"1914{EM}1918") == f"1914{WJ}{EM}1918"  # em between digits: not parenthetical
    assert _gb(f"{EM}go on") == f"{WJ}{EM}go on"  # leading dash (dialogue/list): no preceding word


def test_trailing_interrupted_dash_is_bound() -> None:
    # A trailing dash (interrupted speech) is a distinct, universal convention
    # (CMOS/NHR/Duden) — always the closed em dash, regardless of the locale's
    # ordinary (here, spaced en dash) parenthetical style — so the always-on
    # interrupted-dialogue rule supersedes --normalize-dashes's own rewrite here.
    assert _gb(f"we gotta{EM}") == f"we gotta{WJ}{EM}"
    assert _gb("we gotta --") == f"we gotta{WJ}{EM}"
    assert _gb(f"we gotta {EN}") == f"we gotta{WJ}{EM}"


def test_ligatures_are_left_alone() -> None:
    # The ligature itself is preserved (the pipeline's word joiner precedes it).
    assert _gb(f"a{chars.TWO_EM_DASH}b") == f"a{WJ}{chars.TWO_EM_DASH}b"
    assert _gb(f"a{chars.THREE_EM_DASH}b") == f"a{WJ}{chars.THREE_EM_DASH}b"


def test_flag_off_does_not_normalize() -> None:
    # Default pipeline keeps the author's em dash (only adds the word joiner).
    assert build_pipeline(_GB).run(f"cat{EM}black") == f"cat{WJ}{EM}black"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("big question - whether", f"big question{NBSP}{EN} whether"),
        ("a - b - c", f"a{NBSP}{EN} b{NBSP}{EN} c"),
        ("question -  whether", f"question{NBSP}{EN} whether"),  # extra space collapsed too
    ],
)
def test_en_gb_spaced_ascii_hyphen(text: str, expected: str) -> None:
    assert _gb(text) == expected


def test_en_us_closed_ascii_hyphen() -> None:
    assert _us("big question - whether") == f"big question{WJ}{EM}whether"


def test_ascii_hyphen_left_alone_when_not_a_clean_parenthetical() -> None:
    assert _gb("well-known author") == "well-known author"  # hyphenated compound
    assert _gb("well -known") == "well -known"  # space on one side only
    assert _gb("well- known") == "well- known"  # space on one side only
    assert _gb("1914 - 1918") == "1914 - 1918"  # numeric range, left alone
    assert _gb("we gotta -") == "we gotta -"  # no trailing space: not recognised


def test_flag_off_does_not_normalize_ascii_hyphen() -> None:
    assert build_pipeline(_GB).run("big question - whether") == "big question - whether"


@settings(max_examples=300)
@given(st.text(alphabet=st.sampled_from(list("ab 12-" + EM + EN + NBSP + WJ)), max_size=40))
def test_normalize_is_idempotent(text: str) -> None:
    for profile in (_GB, _EN):
        pipeline = build_pipeline(profile, normalize_dashes=True)
        once = pipeline.run(text)
        assert pipeline.run(once) == once
