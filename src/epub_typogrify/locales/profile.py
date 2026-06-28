"""``LocaleProfile`` — the declarative, per-locale rule data.

A profile is a frozen dataclass tree built from a (possibly merged) mapping, so
it can come either from a TOML file (via :mod:`epub_typogrify.locales.registry`)
or be constructed directly in tests. Phase 1 covers the fields the agnostic
rules and the quote engine need; later phases extend it (spacing, abbreviations,
keep-together) without disturbing what is here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from epub_typogrify import chars


@dataclass(frozen=True)
class QuotePair:
    """An opening/closing pair of quotation marks."""

    open: str
    close: str


@dataclass(frozen=True)
class Quotes:
    """Quotation-mark conventions for a locale.

    By default the quote engine is character-based: a straight ``"`` becomes the
    ``double`` pair, a straight ``'`` the ``single`` pair (or ``apostrophe``),
    preserving the author's double/single distinction.

    ``outer`` (``"double"`` or ``"single"``) names which pair is the *top level*
    quotation; it is only consumed by the opt-in nesting normalisation, where
    ``primary``/``secondary`` are assigned by nesting depth. ``punctuation`` is
    ``"typesetters"`` (commas/periods inside the closing quote, US style) or
    ``"logical"`` (British style).
    """

    double: QuotePair
    single: QuotePair
    apostrophe: str = chars.APOSTROPHE
    punctuation: str = "typesetters"
    outer: str = "double"

    @property
    def primary(self) -> QuotePair:
        """The top-level (outermost) pair, per ``outer``."""
        return self.double if self.outer == "double" else self.single

    @property
    def secondary(self) -> QuotePair:
        """The nested pair (the other of ``double``/``single``)."""
        return self.single if self.outer == "double" else self.double


@dataclass(frozen=True)
class Dashes:
    """Dash conventions. ``double_hyphen``/``triple_hyphen`` are what ``--``/``---``
    become; ``numeric_range`` is the range dash; ``parenthetical_spacing`` is
    ``"closed"`` or ``"spaced"`` (consumed by Phase 2 spacing)."""

    double_hyphen: str = chars.EM_DASH
    triple_hyphen: str = chars.EM_DASH
    numeric_range: str = chars.EN_DASH
    parenthetical_spacing: str = "closed"


@dataclass(frozen=True)
class EllipsisStyle:
    """Ellipsis glyph and whether spaced dots (``. . .``) are collapsed."""

    char: str = chars.ELLIPSIS
    collapse_spaced_dots: bool = True


@dataclass(frozen=True)
class Spaces:
    """Which non-breaking space a locale uses, and French high-punctuation spacing.

    ``before_high_punctuation``/``guillemet_inner`` drive the French narrow-space
    hook (§2.4); they are off by default.
    """

    nbsp: str = chars.NO_BREAK_SPACE
    narrow_nbsp: str = chars.NARROW_NO_BREAK_SPACE
    before_high_punctuation: bool = False
    guillemet_inner: bool = False


@dataclass(frozen=True)
class Abbreviations:
    """Abbreviations that take a non-breaking space before the following token
    (§2.3), and whether a full stop follows a contraction (US) or not (British)."""

    nonbreaking: tuple[str, ...] = ()
    full_stop_after_contractions: bool = True


@dataclass(frozen=True)
class KeepTogether:
    """Units that bind to a preceding number with a non-breaking space (§2.3)."""

    units: tuple[str, ...] = ()


@dataclass(frozen=True)
class LocaleProfile:
    """The complete set of data-driven conventions for one locale."""

    tag: str
    quotes: Quotes
    dashes: Dashes = field(default_factory=Dashes)
    ellipsis: EllipsisStyle = field(default_factory=EllipsisStyle)
    spaces: Spaces = field(default_factory=Spaces)
    abbreviations: Abbreviations = field(default_factory=Abbreviations)
    keep_together: KeepTogether = field(default_factory=KeepTogether)
    fractions_enabled: bool = True


_DEFAULT_DOUBLE = QuotePair(chars.LEFT_DOUBLE_QUOTE, chars.RIGHT_DOUBLE_QUOTE)
_DEFAULT_SINGLE = QuotePair(chars.LEFT_SINGLE_QUOTE, chars.RIGHT_SINGLE_QUOTE)


def _quotes_from_dict(data: Mapping[str, Any]) -> Quotes:
    double = data.get("double")
    single = data.get("single")
    return Quotes(
        double=QuotePair(**double) if double else _DEFAULT_DOUBLE,
        single=QuotePair(**single) if single else _DEFAULT_SINGLE,
        apostrophe=data.get("apostrophe", chars.APOSTROPHE),
        punctuation=data.get("punctuation", "typesetters"),
        outer=data.get("outer", "double"),
    )


def _dashes_from_dict(data: Mapping[str, Any]) -> Dashes:
    return Dashes(
        double_hyphen=data.get("double_hyphen", chars.EM_DASH),
        triple_hyphen=data.get("triple_hyphen", chars.EM_DASH),
        numeric_range=data.get("numeric_range", chars.EN_DASH),
        parenthetical_spacing=data.get("parenthetical_spacing", "closed"),
    )


def _ellipsis_from_dict(data: Mapping[str, Any]) -> EllipsisStyle:
    return EllipsisStyle(
        char=data.get("char", chars.ELLIPSIS),
        collapse_spaced_dots=data.get("collapse_spaced_dots", True),
    )


def _spaces_from_dict(data: Mapping[str, Any]) -> Spaces:
    return Spaces(
        nbsp=data.get("nbsp", chars.NO_BREAK_SPACE),
        narrow_nbsp=data.get("narrow_nbsp", chars.NARROW_NO_BREAK_SPACE),
        before_high_punctuation=bool(data.get("before_high_punctuation", False)),
        guillemet_inner=bool(data.get("guillemet_inner", False)),
    )


def _abbreviations_from_dict(data: Mapping[str, Any]) -> Abbreviations:
    return Abbreviations(
        nonbreaking=tuple(data.get("nonbreaking", ())),
        full_stop_after_contractions=bool(data.get("full_stop_after_contractions", True)),
    )


def _keep_together_from_dict(data: Mapping[str, Any]) -> KeepTogether:
    return KeepTogether(units=tuple(data.get("units", ())))


def profile_from_dict(tag: str, data: Mapping[str, Any]) -> LocaleProfile:
    """Build a :class:`LocaleProfile` from a (merged) mapping, applying defaults
    for any absent section or field."""
    fractions = data.get("fractions", {})
    fractions_enabled = (
        bool(fractions.get("enabled", True)) if isinstance(fractions, Mapping) else True
    )
    return LocaleProfile(
        tag=tag,
        quotes=_quotes_from_dict(data.get("quotes", {})),
        dashes=_dashes_from_dict(data.get("dashes", {})),
        ellipsis=_ellipsis_from_dict(data.get("ellipsis", {})),
        spaces=_spaces_from_dict(data.get("spaces", {})),
        abbreviations=_abbreviations_from_dict(data.get("abbreviations", {})),
        keep_together=_keep_together_from_dict(data.get("keep_together", {})),
        fractions_enabled=fractions_enabled,
    )
