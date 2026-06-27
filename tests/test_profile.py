"""``LocaleProfile`` construction and defaults."""

from __future__ import annotations

from epub_typogrify import chars
from epub_typogrify.locales.profile import profile_from_dict


def test_defaults_when_empty() -> None:
    profile = profile_from_dict("xx", {})
    assert profile.tag == "xx"
    assert profile.quotes.double.open == chars.LEFT_DOUBLE_QUOTE
    assert profile.quotes.single.open == chars.LEFT_SINGLE_QUOTE
    assert profile.quotes.apostrophe == chars.APOSTROPHE
    assert profile.dashes.double_hyphen == chars.EM_DASH
    assert profile.dashes.numeric_range == chars.EN_DASH
    assert profile.ellipsis.char == chars.ELLIPSIS
    assert profile.fractions_enabled is True


def test_partial_overrides() -> None:
    data = {
        "quotes": {"double": {"open": chars.LEFT_GUILLEMET, "close": chars.RIGHT_GUILLEMET}},
        "dashes": {"double_hyphen": chars.EN_DASH},
        "fractions": {"enabled": False},
    }
    profile = profile_from_dict("fr", data)
    assert profile.quotes.double.open == chars.LEFT_GUILLEMET
    # Untouched sections still get their defaults.
    assert profile.quotes.single.open == chars.LEFT_SINGLE_QUOTE
    assert profile.dashes.double_hyphen == chars.EN_DASH
    assert profile.dashes.triple_hyphen == chars.EM_DASH
    assert profile.fractions_enabled is False
