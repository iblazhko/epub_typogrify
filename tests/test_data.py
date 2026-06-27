"""The shipped locale profiles load and carry the expected conventions (§2)."""

from __future__ import annotations

from epub_typogrify import chars
from epub_typogrify.locales.registry import LocaleRegistry


def test_shipped_locales_resolve(registry: LocaleRegistry) -> None:
    for tag in ["en", "en-GB", "fr", "de", "la"]:
        assert registry.resolve(tag) is not None, tag
    assert registry.resolve("sw") is None  # unsupported
    assert registry.resolve("default") is None  # base, not a target


def test_en_profile(registry: LocaleRegistry) -> None:
    en = registry.resolve("en")
    assert en is not None
    assert en.quotes.double.open == chars.LEFT_DOUBLE_QUOTE
    assert en.quotes.punctuation == "typesetters"
    assert en.dashes.double_hyphen == chars.EM_DASH
    assert "Mr." in en.abbreviations.nonbreaking
    assert "%" in en.keep_together.units


def test_en_gb_profile(registry: LocaleRegistry) -> None:
    gb = registry.resolve("en-GB")
    assert gb is not None
    # Same quote marks as en; the differences are elsewhere.
    assert gb.quotes.double.open == chars.LEFT_DOUBLE_QUOTE
    assert gb.quotes.punctuation == "logical"
    assert gb.dashes.double_hyphen == chars.EN_DASH
    assert "Mr" in gb.abbreviations.nonbreaking
    assert gb.abbreviations.full_stop_after_contractions is False
    assert "km" in gb.keep_together.units  # inherited from en


def test_fr_profile(registry: LocaleRegistry) -> None:
    fr = registry.resolve("fr")
    assert fr is not None
    assert fr.quotes.double.open == chars.LEFT_GUILLEMET
    assert fr.quotes.double.close == chars.RIGHT_GUILLEMET
    assert fr.spaces.before_high_punctuation is True
    assert fr.spaces.guillemet_inner is True


def test_de_profile(registry: LocaleRegistry) -> None:
    de = registry.resolve("de")
    assert de is not None
    assert de.quotes.double.open == chars.LEFT_LOW_DOUBLE_QUOTE
    assert de.quotes.double.close == chars.LEFT_DOUBLE_QUOTE
    assert de.dashes.double_hyphen == chars.EN_DASH


def test_la_inherits_default(registry: LocaleRegistry) -> None:
    la = registry.resolve("la")
    assert la is not None
    assert la.quotes.double.open == chars.LEFT_DOUBLE_QUOTE
