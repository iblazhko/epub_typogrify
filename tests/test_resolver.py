"""LanguageResolver nearest-ancestor resolution and fallback (§5)."""

from __future__ import annotations

from lxml import etree

from epub_typogrify.lang.resolver import LanguageResolver

_TREE = etree.fromstring(
    b'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">'
    b"<body>"
    b'<p id="p1">english</p>'
    b'<p id="p2" xml:lang="fr"><span id="s1">french</span>'
    b'<span id="s2" lang="la">latin</span></p>'
    b"</body></html>"
)


def _by_id(tag: str) -> etree._Element:
    found = _TREE.find(f'.//*[@id="{tag}"]')
    assert found is not None
    return found


def test_inherits_from_document() -> None:
    assert LanguageResolver().effective_lang(_by_id("p1")) == "en"


def test_nearest_ancestor_wins() -> None:
    resolver = LanguageResolver()
    assert resolver.effective_lang(_by_id("s1")) == "fr"  # from p2
    assert resolver.effective_lang(_by_id("s2")) == "la"  # own lang attr


def test_publication_then_default_fallback() -> None:
    plain = etree.fromstring(
        b'<html xmlns="http://www.w3.org/1999/xhtml"><body><p id="x">t</p></body></html>'
    )
    node = plain.find('.//*[@id="x"]')
    assert LanguageResolver().effective_lang(node) is None
    assert LanguageResolver(publication_lang="de").effective_lang(node) == "de"
    assert LanguageResolver(default_lang="en").effective_lang(node) == "en"
    # publication wins over default
    assert LanguageResolver(publication_lang="de", default_lang="en").effective_lang(node) == "de"
