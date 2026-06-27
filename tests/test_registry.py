"""``LocaleRegistry`` resolution, inheritance, and the unsupported-language path."""

from __future__ import annotations

from pathlib import Path

from epub_typogrify import chars
from epub_typogrify.locales.registry import LocaleRegistry

EM = chars.EM_DASH
EN = chars.EN_DASH
LSQ = chars.LEFT_SINGLE_QUOTE
LDQ = chars.LEFT_DOUBLE_QUOTE

RAW = {
    "default": {
        "quotes": {
            "double": {"open": LDQ, "close": chars.RIGHT_DOUBLE_QUOTE},
            "single": {"open": LSQ, "close": chars.RIGHT_SINGLE_QUOTE},
        }
    },
    "en": {"inherits": "default", "dashes": {"double_hyphen": EM}},
    "en-gb": {
        "inherits": "en",
        "quotes": {"punctuation": "logical"},
        "dashes": {"double_hyphen": EN},
    },
    "fr": {"inherits": "default", "quotes": {"double": {"open": "«", "close": "»"}}},
}


def test_resolves_registered_tag() -> None:
    reg = LocaleRegistry(RAW)
    profile = reg.resolve("en")
    assert profile is not None
    assert profile.dashes.double_hyphen == EM


def test_inheritance_overlay() -> None:
    reg = LocaleRegistry(RAW)
    gb = reg.resolve("en-GB")
    assert gb is not None
    assert gb.quotes.punctuation == "logical"  # overridden in en-gb
    assert gb.quotes.double.open == LDQ  # inherited from default
    assert gb.dashes.double_hyphen == EN  # overridden in en-gb
    assert gb.dashes.numeric_range == chars.EN_DASH  # default, inherited


def test_subtag_fallback() -> None:
    reg = LocaleRegistry(RAW)
    # Region without its own profile falls back to the base language.
    assert reg.resolve("en-US") is reg.resolve("en-US")  # cached
    en_us = reg.resolve("en-US")
    assert en_us is not None
    assert en_us.dashes.double_hyphen == EM
    fr_ca = reg.resolve("fr-CA")
    assert fr_ca is not None
    assert fr_ca.quotes.double.open == "«"


def test_unsupported_language_returns_none() -> None:
    reg = LocaleRegistry(RAW)
    assert reg.resolve("sw") is None
    assert reg.resolve("zh-Hant") is None


def test_default_is_not_a_resolution_target() -> None:
    reg = LocaleRegistry(RAW)
    assert reg.resolve("default") is None


def test_empty_and_none_tags() -> None:
    reg = LocaleRegistry(RAW)
    assert reg.resolve(None) is None
    assert reg.resolve("") is None


def test_from_directory(tmp_path: Path) -> None:
    (tmp_path / "default.toml").write_text(
        '[quotes.double]\nopen = "\\u201c"\nclose = "\\u201d"\n', encoding="utf-8"
    )
    (tmp_path / "en.toml").write_text(
        'inherits = "default"\n[dashes]\ndouble_hyphen = "\\u2014"\n', encoding="utf-8"
    )
    reg = LocaleRegistry.from_directory(tmp_path)
    en = reg.resolve("en")
    assert en is not None
    assert en.dashes.double_hyphen == EM
    assert reg.resolve("default") is None
