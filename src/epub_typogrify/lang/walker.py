"""Walk a DOM, converting text-node payloads per their effective language.

Traversal is in document order. Protected subtrees (``pre``, ``code``, MathML,
SVG, ``class="notypo"``, ``translate="no"``, comments) are skipped entirely.
A :class:`~epub_typogrify.rules.context.ContextState` is threaded through the
inline text of a block so context-sensitive rules (quotes) work across inline
markup; it is reset at each block boundary. Each text run is converted with the
pipeline for its own language, so a foreign quotation inside a paragraph is
typeset with the foreign rules.
"""

from __future__ import annotations

from lxml import etree

from epub_typogrify.lang.resolver import LanguageResolver
from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.locales.registry import LocaleRegistry
from epub_typogrify.rules.context import ContextState
from epub_typogrify.rules.pipeline import Pipeline, build_pipeline

_XHTML_NS = "http://www.w3.org/1999/xhtml"
_MATHML_NS = "http://www.w3.org/1998/Math/MathML"
_SVG_NS = "http://www.w3.org/2000/svg"

PROTECTED_TAGS = frozenset({"pre", "code", "kbd", "samp", "var", "tt", "script", "style"})
BLOCK_TAGS = frozenset(
    {
        "p",
        "div",
        "blockquote",
        "section",
        "article",
        "aside",
        "header",
        "footer",
        "nav",
        "figure",
        "figcaption",
        "main",
        "hgroup",
        "address",
        "details",
        "summary",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "dl",
        "dt",
        "dd",
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "td",
        "th",
        "caption",
        "title",
        "body",
    }
)


class TextWalker:
    """Apply per-language pipelines to the text nodes of an XHTML tree."""

    def __init__(
        self,
        registry: LocaleRegistry,
        resolver: LanguageResolver,
        *,
        protected_tags: frozenset[str] = PROTECTED_TAGS,
        block_tags: frozenset[str] = BLOCK_TAGS,
        normalize_dashes: bool = False,
        normalize_quotes: bool = False,
    ) -> None:
        self._registry = registry
        self._resolver = resolver
        self._protected = protected_tags
        self._block = block_tags
        self._normalize_dashes = normalize_dashes
        self._normalize_quotes = normalize_quotes
        self._pipelines: dict[str, Pipeline] = {}

    def process(self, root: etree._Element) -> None:
        """Convert the text content of *root* in place."""
        if not self._is_protected(root):
            self._walk(root, ContextState())

    def _walk(self, elem: etree._Element, ctx: ContextState) -> None:
        # Precondition: *elem* is not protected.
        if elem.text:
            elem.text = self._convert(elem.text, elem, ctx)
        for child in elem:
            if self._is_protected(child):
                pass  # skip the child's text and its whole subtree
            elif self._is_block(child):
                self._walk(child, ContextState())  # fresh state per block
            else:
                self._walk(child, ctx)  # inline: thread the state
            if child.tail:
                # The tail belongs to *elem* (it follows the child within elem).
                child.tail = self._convert(child.tail, elem, ctx)

    def _convert(self, text: str, owner: etree._Element, ctx: ContextState) -> str:
        profile = self._registry.resolve(self._resolver.effective_lang(owner))
        if profile is None:
            # No rules for this language: leave the text untouched, but keep the
            # running state's preceding character current for following nodes.
            if text:
                ctx.prev_char = text[-1]
            return text
        return self._pipeline_for(profile).run(text, ctx)

    def _pipeline_for(self, profile: LocaleProfile) -> Pipeline:
        pipeline = self._pipelines.get(profile.tag)
        if pipeline is None:
            pipeline = build_pipeline(
                profile,
                normalize_dashes=self._normalize_dashes,
                normalize_quotes=self._normalize_quotes,
            )
            self._pipelines[profile.tag] = pipeline
        return pipeline

    def _is_protected(self, elem: etree._Element) -> bool:
        tag = elem.tag
        if not isinstance(tag, str):
            return True  # comment, PI, or entity reference
        qname = etree.QName(elem)
        if qname.namespace in (_MATHML_NS, _SVG_NS):
            return True
        if qname.localname in self._protected:
            return True
        if "notypo" in (elem.get("class") or "").split():
            return True
        return elem.get("translate") == "no"

    def _is_block(self, elem: etree._Element) -> bool:
        if not isinstance(elem.tag, str):
            return False
        qname = etree.QName(elem)
        if qname.namespace not in (None, _XHTML_NS):
            return False
        return qname.localname in self._block
