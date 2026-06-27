"""Parse and serialise an XHTML content document with markup fidelity.

We only ever mutate the ``.text``/``.tail`` payloads of text nodes (the walker's
job); the document structure, attributes, namespaces, comments, DOCTYPE and the
original XML declaration are preserved. The XML declaration is captured verbatim
from the source and re-emitted unchanged, so a file that declares no convertible
text round-trips byte-for-byte.
"""

from __future__ import annotations

import re
from pathlib import Path

from lxml import etree

XHTML_NS = "http://www.w3.org/1999/xhtml"

# Leading ``<?xml ... ?>`` plus any trailing horizontal space and one newline.
_DECLARATION = re.compile(rb"^\s*(<\?xml[^>]*\?>)([ \t]*\r?\n?)")


class XhtmlDocument:
    """An XHTML document as a mutable lxml tree, with fidelity-preserving I/O."""

    def __init__(self, tree: etree._ElementTree, declaration: bytes, separator: bytes) -> None:
        self._tree = tree
        self._declaration = declaration
        self._separator = separator

    @classmethod
    def from_bytes(cls, data: bytes) -> XhtmlDocument:
        parser = etree.XMLParser(resolve_entities=False, strip_cdata=False)
        root = etree.fromstring(data, parser)
        match = _DECLARATION.match(data)
        declaration = match.group(1) if match else b""
        separator = match.group(2) if match else b""
        return cls(root.getroottree(), declaration, separator)

    @classmethod
    def from_path(cls, path: Path | str) -> XhtmlDocument:
        return cls.from_bytes(Path(path).read_bytes())

    @property
    def root(self) -> etree._Element:
        return self._tree.getroot()

    def to_bytes(self) -> bytes:
        doctype = self._tree.docinfo.doctype or None
        body = etree.tostring(self._tree, xml_declaration=False, encoding="utf-8", doctype=doctype)
        if self._declaration:
            return self._declaration + self._separator + body
        return body

    def write(self, path: Path | str) -> None:
        Path(path).write_bytes(self.to_bytes())
