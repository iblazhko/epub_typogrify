"""Opt-in quote-nesting normalisation (TypographyConversions.md §2.7)."""

from __future__ import annotations

import pytest

from epub_typogrify import chars
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.locales.registry import LocaleRegistry
from epub_typogrify.rules.pipeline import build_pipeline

_REG = LocaleRegistry.default()
_EN = _REG.resolve("en")
_GB = _REG.resolve("en-GB")
assert _EN is not None and _GB is not None

LDQ = chars.LEFT_DOUBLE_QUOTE
RDQ = chars.RIGHT_DOUBLE_QUOTE
LSQ = chars.LEFT_SINGLE_QUOTE
RSQ = chars.RIGHT_SINGLE_QUOTE


def _gb(text: str) -> str:
    return build_pipeline(_GB, normalize_quotes=True).run(text)


def _en(text: str) -> str:
    return build_pipeline(_EN, normalize_quotes=True).run(text)


_US_STRAIGHT = '"Economic systems," said White, "are, as Doe said, \'with us or not.\'"'
_US_CURLY = (
    f"{LDQ}Economic systems,{RDQ} said White, {LDQ}are, as Doe said, {LSQ}with us or not.{RSQ}{RDQ}"
)
_GB_EXPECTED = (
    f"{LSQ}Economic systems,{RSQ} said White, {LSQ}are, as Doe said, {LDQ}with us or not.{RDQ}{RSQ}"
)


def test_en_gb_reflows_to_single_outer_from_straight() -> None:
    assert _gb(_US_STRAIGHT) == _GB_EXPECTED


def test_en_gb_reflows_to_single_outer_from_curly() -> None:
    # Any combination of straight and curly is accepted.
    assert _gb(_US_CURLY) == _GB_EXPECTED


def test_en_reflows_british_source_to_double_outer() -> None:
    british = "'Economic systems', said White, 'are, as Doe said, \"with us or not\"'."
    expected = (
        f"{LDQ}Economic systems,{RDQ} said White, "
        f"{LDQ}are, as Doe said, {LSQ}with us or not{RSQ}.{RDQ}"
    )
    assert _en(british) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("don't", f"don{RSQ}t"),
        ("dogs'", f"dogs{RSQ}"),
        ("o'clock", f"o{RSQ}clock"),
        ("'92", f"{RSQ}92"),
        ("it's here", f"it{RSQ}s here"),
        ("'tis the season", f"{RSQ}tis the season"),
    ],
)
def test_apostrophes_and_elisions_preserved(text: str, expected: str) -> None:
    assert _en(text) == expected


def test_standalone_single_quote_becomes_outer_mark() -> None:
    # A top-level single-quoted span normalises to the locale's outer mark.
    assert _en("a 'word' here") == f"a {LDQ}word{RDQ} here"  # en outer = double
    assert _gb('a "word" here') == f"a {LSQ}word{RSQ} here"  # en-GB outer = single


def test_already_correct_curly_is_unchanged() -> None:
    text = f"{LDQ}He said {LSQ}hi{RSQ} then left{RDQ}"
    assert _en(text) == text


def test_flag_off_is_character_based() -> None:
    # Default: `"` -> double, `'` -> single, regardless of locale.
    assert build_pipeline(_GB).run('say "hi"') == f"say {LDQ}hi{RDQ}"


# Idempotency over realistic (balanced) quotations — both straight and curly. The
# default-mode property test (test_idempotency.py) stresses the char-based engine;
# normalisation is only guaranteed idempotent for well-formed nesting.
_CORPUS = [
    "",
    "Plain text, no quotes at all.",
    _US_STRAIGHT,
    _US_CURLY,
    "'Economic systems', said White, 'are, as Doe said, \"with us or not\"'.",
    "He said \"it's a 'nested' quote\" loudly.",
    f"She said {LDQ}it{RSQ}s a {LSQ}nested{RSQ} quote{RDQ} loudly.",
    "don't, dogs', o'clock, '92, and 'tis the season",
    f"{LDQ}already curly American{RDQ}",
    f"{LSQ}already curly British{RSQ}",
]


@pytest.mark.parametrize("profile", [_EN, _GB], ids=["en", "en-gb"])
@pytest.mark.parametrize("text", _CORPUS)
def test_normalize_quotes_idempotent(profile: LocaleProfile, text: str) -> None:
    pipeline = build_pipeline(profile, normalize_quotes=True)
    once = pipeline.run(text)
    assert pipeline.run(once) == once
