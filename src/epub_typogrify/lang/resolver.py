"""Resolve the effective language of a DOM node (TechnicalDesign.md §5).

Walk up from a node to the first ancestor that declares ``xml:lang`` or ``lang``;
falling back to the publication default (the OPF ``dc:language``, supplied by the
caller in Phase 4) and then ``--default-lang``. Returns ``None`` when nothing in
that chain declares a language, in which case the caller leaves the text
unchanged.
"""

from __future__ import annotations

from lxml import etree

_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class LanguageResolver:
    """Nearest-ancestor language resolution with publication/default fallback."""

    def __init__(
        self,
        *,
        publication_lang: str | None = None,
        default_lang: str | None = None,
    ) -> None:
        self._publication = _clean(publication_lang)
        self._default = _clean(default_lang)

    def effective_lang(self, elem: etree._Element) -> str | None:
        node: etree._Element | None = elem
        while node is not None:
            if isinstance(node.tag, str):  # skip comments / PIs
                lang = _clean(node.get(_XML_LANG) or node.get("lang"))
                if lang is not None:
                    return lang
            node = node.getparent()
        return self._publication or self._default
