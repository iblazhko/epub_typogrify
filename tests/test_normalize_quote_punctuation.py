"""Opt-in quote-adjacent punctuation relocation (TypographyConversions.md §2.7)."""

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


def _run(profile: LocaleProfile, text: str, *, quotes: bool = False) -> str:
    return build_pipeline(profile, normalize_quotes=quotes, normalize_quote_punctuation=True).run(
        text
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('He said "stop".', f"He said {LDQ}stop.{RDQ}"),  # double: pull inside
        ("He said 'stop'.", f"He said {LSQ}stop.{RSQ}"),  # single: pull inside
        ("a 'b', then", f"a {LSQ}b,{RSQ} then"),  # comma pulled in
    ],
)
def test_en_typesetters_pulls_inside(text: str, expected: str) -> None:
    assert _run(_EN, text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # A trailing comma is the matrix sentence's — pushed outside.
        ("a 'b,' then", f"a {LSQ}b{RSQ}, then"),
        ("'Not today,' he said", f"{LSQ}Not today{RSQ}, he said"),
        # A complete-sentence terminator stays inside.
        ("'A whole sentence.'", f"{LSQ}A whole sentence.{RSQ}"),
        ("'Stop!' he yelled", f"{LSQ}Stop!{RSQ} he yelled"),
        ("'Who?' she asked", f"{LSQ}Who?{RSQ} she asked"),
        # A period already outside (fragment) is left outside.
        (f"a 'fragment{RSQ}.", f"a {LSQ}fragment{RSQ}."),
    ],
)
def test_en_gb_logical_relocation(text: str, expected: str) -> None:
    # en-GB needs --normalize-quotes too (single-outer). Commas move outside;
    # sentence-terminal punctuation stays inside a complete-sentence quote.
    assert _run(_GB, text, quotes=True) == expected


def test_complete_sentence_keeps_terminal_punctuation_inside() -> None:
    # Regression for the British complete-sentence rule: the comma after the
    # fragment goes outside, but the terminal period of the complete-sentence
    # quotation stays inside.
    american = (
        '"Not today," Skinner said. '
        '"Not like the other day, watching you chase those turds around."'
    )
    expected = (
        f"{LSQ}Not today{RSQ}, Skinner said. "
        f"{LSQ}Not like the other day, watching you chase those turds around.{RSQ}"
    )
    assert _run(_GB, american, quotes=True) == expected


def test_full_british_house_style() -> None:
    american = '"Economic systems," said White, "as Doe said, \'with us or not.\'"'
    # The outer quotation is a complete sentence, so its terminal period stays
    # inside; only the fragment comma after "systems" moves outside.
    expected = (
        f"{LSQ}Economic systems{RSQ}, said White, {LSQ}as Doe said, {LDQ}with us or not.{RDQ}{RSQ}"
    )
    assert _run(_GB, american, quotes=True) == expected


def test_ellipsis_is_not_relocated() -> None:
    # A trailing ellipsis (run of dots) must stay where it is, not be split.
    assert _run(_GB, '"wait..."', quotes=True) == f"{LSQ}wait{chars.ELLIPSIS}{RSQ}"
    assert _run(_EN, '"wait..."') == f"{LDQ}wait{chars.ELLIPSIS}{RDQ}"


def test_apostrophes_unaffected() -> None:
    assert _run(_EN, "don't stop.") == f"don{RSQ}t stop."
    assert _run(_EN, "the dogs' bone.") == f"the dogs{RSQ} bone."


def test_default_pipeline_unchanged() -> None:
    # Without the flag, the standalone rule applies (typesetters, double only);
    # single quotes are not relocated.
    assert build_pipeline(_EN).run('He said "stop".') == f"He said {LDQ}stop.{RDQ}"
    assert build_pipeline(_EN).run("He said 'stop'.") == f"He said {LSQ}stop{RSQ}."


_CORPUS = [
    "",
    "Nothing to do here.",
    "He said \"it's a 'nested' quote\".",
    "'systems', said White, 'with us or not.'",
    f"{LDQ}curly American,{RDQ} and {LSQ}single{RSQ}.",
    "don't, dogs', o'clock.",
]


@pytest.mark.parametrize("profile", [_EN, _GB], ids=["en", "en-gb"])
@pytest.mark.parametrize("text", _CORPUS)
def test_relocation_idempotent(profile: LocaleProfile, text: str) -> None:
    pipeline = build_pipeline(profile, normalize_quotes=True, normalize_quote_punctuation=True)
    once = pipeline.run(text)
    assert pipeline.run(once) == once
