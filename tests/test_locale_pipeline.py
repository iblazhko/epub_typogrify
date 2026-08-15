"""End-to-end pipeline behaviour per locale, using the shipped profiles (§2)."""

from __future__ import annotations

from epub_typogrify import chars
from epub_typogrify.locales.registry import LocaleRegistry
from epub_typogrify.rules.pipeline import build_pipeline

LDQ = chars.LEFT_DOUBLE_QUOTE
RDQ = chars.RIGHT_DOUBLE_QUOTE
EM = chars.EM_DASH
EN = chars.EN_DASH
WJ = chars.WORD_JOINER
NBSP = chars.NO_BREAK_SPACE
NN = chars.NARROW_NO_BREAK_SPACE
LG = chars.LEFT_GUILLEMET
RG = chars.RIGHT_GUILLEMET


def _run(registry: LocaleRegistry, tag: str, text: str) -> str:
    profile = registry.resolve(tag)
    assert profile is not None
    return build_pipeline(profile).run(text)


def test_en_typesetters_and_nbsp(registry: LocaleRegistry) -> None:
    assert _run(registry, "en", 'Mr. Smith said "cat".') == f"Mr.{NBSP}Smith said {LDQ}cat.{RDQ}"
    # The em dash is preceded by a word joiner (§1.6).
    assert _run(registry, "en", "a--b") == f"a{WJ}{EM}b"
    assert _run(registry, "en", "100 km") == f"100{NBSP}km"


def test_en_gb_logical_and_nbsp(registry: LocaleRegistry) -> None:
    assert _run(registry, "en-GB", 'Mr Smith said "cat".') == f"Mr{NBSP}Smith said {LDQ}cat{RDQ}."
    assert _run(registry, "en-GB", "a--b") == f"a{EN}b"


def test_en_elision_via_hook(registry: LocaleRegistry) -> None:
    # The opening single quote the engine would produce for 'tis is fixed by the hook.
    assert _run(registry, "en", "'tis so") == f"{chars.APOSTROPHE}tis so"


def test_fr_guillemets_and_high_punctuation(registry: LocaleRegistry) -> None:
    assert _run(registry, "fr", "« Bonjour »") == f"{LG}{NN}Bonjour{NN}{RG}"
    assert _run(registry, "fr", "Vraiment ?") == f"Vraiment{NN}?"
    # A straight double quote maps to guillemets in French.
    assert _run(registry, "fr", '"Oui"') == f"{LG}Oui{RG}"


def test_de_nesting_from_character_based_engine(registry: LocaleRegistry) -> None:
    assert _run(registry, "de", '"Hallo"') == f"{chars.LEFT_LOW_DOUBLE_QUOTE}Hallo{LDQ}"
    assert _run(registry, "de", "1--2") == f"1{EN}2"


def test_ru_guillemets_and_nesting(registry: LocaleRegistry) -> None:
    # A straight double quote maps to guillemets; a straight single quote to the
    # nested лапки pair (same glyphs German uses as its primary).
    assert _run(registry, "ru", '"Привет"') == f"{LG}Привет{RG}"
    assert _run(registry, "ru", "'Привет'") == f"{chars.LEFT_LOW_DOUBLE_QUOTE}Привет{LDQ}"


def test_ru_normalize_dashes_is_spaced_em(registry: LocaleRegistry) -> None:
    # `--` on its own is plain em dash (plus the agnostic word-joiner, §1.6), no
    # extra spacing added.
    assert _run(registry, "ru", "кот--чёрный") == f"кот{WJ}{EM}чёрный"
    # The opt-in rewrite of an *existing* parenthetical dash uses Russian's
    # spaced convention: nbsp before the dash, a breakable space after.
    profile = registry.resolve("ru")
    assert profile is not None
    normalized = build_pipeline(profile, normalize_dashes=True).run(f"кот{EM}чёрный")
    assert normalized == f"кот{NBSP}{EM} чёрный"


def test_ru_interrupted_dialogue_dash(registry: LocaleRegistry) -> None:
    # A run defaults to block-final (ContextState.run_is_block_final=True), so a
    # trailing em dash with a preceding word is bound as interrupted speech.
    assert _run(registry, "ru", "что если—") == f"что если{WJ}{EM}"


def test_ru_compound_abbreviation_hook(registry: LocaleRegistry) -> None:
    assert _run(registry, "ru", "и т. д.") == f"и{NBSP}т.{NBSP}д."
