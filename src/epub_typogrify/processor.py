"""End-to-end document processing: parse → walk → serialise.

Ties together :class:`~epub_typogrify.source.xhtml.XhtmlDocument`,
:class:`~epub_typogrify.lang.resolver.LanguageResolver` and
:class:`~epub_typogrify.lang.walker.TextWalker`. The Phase 4 CLI builds on this.
"""

from __future__ import annotations

from epub_typogrify.lang.resolver import LanguageResolver
from epub_typogrify.lang.walker import TextWalker
from epub_typogrify.locales.registry import LocaleRegistry
from epub_typogrify.source.xhtml import XhtmlDocument


def typogrify_document(
    document: XhtmlDocument,
    registry: LocaleRegistry,
    *,
    publication_lang: str | None = None,
    default_lang: str | None = None,
    normalize_dashes: bool = False,
    normalize_quotes: bool = False,
) -> None:
    """Apply typographic conversions to *document* in place."""
    resolver = LanguageResolver(publication_lang=publication_lang, default_lang=default_lang)
    TextWalker(
        registry,
        resolver,
        normalize_dashes=normalize_dashes,
        normalize_quotes=normalize_quotes,
    ).process(document.root)


def typogrify_bytes(
    data: bytes,
    registry: LocaleRegistry | None = None,
    *,
    publication_lang: str | None = None,
    default_lang: str | None = None,
    normalize_dashes: bool = False,
    normalize_quotes: bool = False,
) -> bytes:
    """Convert the text content of an XHTML document given as bytes."""
    document = XhtmlDocument.from_bytes(data)
    typogrify_document(
        document,
        registry or LocaleRegistry.default(),
        publication_lang=publication_lang,
        default_lang=default_lang,
        normalize_dashes=normalize_dashes,
        normalize_quotes=normalize_quotes,
    )
    return document.to_bytes()
