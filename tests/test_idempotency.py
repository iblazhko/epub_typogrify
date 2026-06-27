"""Idempotency: applying the pipeline twice equals applying it once."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from epub_typogrify.chars import ELLIPSIS, EM_DASH, NO_BREAK_SPACE
from epub_typogrify.rules.pipeline import build_pipeline
from tests.profiles import EN, EN_GB

_CORPUS = [
    "",
    "Plain text with nothing to convert.",
    '"Wait... it\'s 1/2 done--really" 1914-1918',
    "He said 'go'--then left...",
    "Ranges 1-2, 10-20 and IV-VI; minus -5.",
    "dogs' bones and o'clock and '92",
    f"already {ELLIPSIS} converted {EM_DASH} text",
    "----",  # four hyphens, left alone
    ". . . .",  # four spaced dots
]


@pytest.mark.parametrize("profile", [EN, EN_GB], ids=["en", "en-gb"])
@pytest.mark.parametrize("text", _CORPUS)
def test_corpus_idempotent(profile, text: str) -> None:
    pipeline = build_pipeline(profile)
    once = pipeline.run(text)
    assert pipeline.run(once) == once


_ALPHABET = list("ab .,;:-'\"/0129()" + EM_DASH + ELLIPSIS + NO_BREAK_SPACE + "`")


@given(st.text(alphabet=st.sampled_from(_ALPHABET), max_size=48))
def test_pipeline_idempotent_property(text: str) -> None:
    pipeline = build_pipeline(EN)
    once = pipeline.run(text)
    assert pipeline.run(once) == once
