"""Locate and read an unpacked EPUB project (TechnicalDesign.md §2).

``SourceProject`` finds the OPF package document, reads the publication default
language (``dc:language``) and the ordered set of XHTML content documents from
the spine (plus the navigation document). No ZIP handling: this operates on the
unpacked source tree at the authoring stage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from epub_typogrify.source.xhtml import XHTML_NS, XhtmlDocument

_OPF_NS = "http://www.idpf.org/2007/opf"
_DC_NS = "http://purl.org/dc/elements/1.1/"
_CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
_EPUB_TYPE = "{http://www.idpf.org/2007/ops}type"
_XHTML_MEDIA_TYPE = "application/xhtml+xml"

# Sections whose typography is usually deliberate (mirrors `se`'s ignore list).
IGNORED_EPUB_TYPES = frozenset({"titlepage", "imprint", "copyright-page", "colophon"})


@dataclass(frozen=True)
class SourceProject:
    """An unpacked EPUB project's OPF, language, and content documents."""

    opf_path: Path
    publication_language: str | None
    content_documents: tuple[Path, ...]
    nav_document: Path | None

    @classmethod
    def from_directory(cls, directory: Path | str) -> SourceProject:
        directory = Path(directory)
        opf_path = _locate_opf(directory)
        if opf_path is None:
            raise FileNotFoundError(f"no OPF package document found under {directory}")
        return cls._from_opf(opf_path)

    @classmethod
    def _from_opf(cls, opf_path: Path) -> SourceProject:
        root = etree.parse(str(opf_path)).getroot()
        opf_dir = opf_path.parent

        language = None
        lang_el = root.find(f".//{{{_DC_NS}}}language")
        if lang_el is not None and lang_el.text and lang_el.text.strip():
            language = lang_el.text.strip()

        manifest: dict[str, tuple[str, str | None, str]] = {}
        for item in root.iterfind(f".//{{{_OPF_NS}}}manifest/{{{_OPF_NS}}}item"):
            item_id = item.get("id")
            href = item.get("href")
            if item_id and href:
                manifest[item_id] = (href, item.get("media-type"), item.get("properties") or "")

        content: list[Path] = []
        seen: set[Path] = set()
        for itemref in root.iterfind(f".//{{{_OPF_NS}}}spine/{{{_OPF_NS}}}itemref"):
            entry = manifest.get(itemref.get("idref", ""))
            if entry and entry[1] == _XHTML_MEDIA_TYPE:
                path = (opf_dir / entry[0]).resolve()
                if path not in seen:
                    seen.add(path)
                    content.append(path)

        nav_document: Path | None = None
        for href, media_type, properties in manifest.values():
            if "nav" in properties.split() and media_type == _XHTML_MEDIA_TYPE:
                nav_document = (opf_dir / href).resolve()
                if nav_document not in seen:
                    content.append(nav_document)
                break

        return cls(opf_path.resolve(), language, tuple(content), nav_document)

    @staticmethod
    def find_enclosing_opf(file_path: Path | str) -> Path | None:
        """Return the OPF of an EPUB project that *file_path* sits inside, if any.

        Walks up the ancestors; at each level only an OPF *at that level* (a
        direct ``*.opf`` or one named by ``META-INF/container.xml``) counts, so an
        unrelated OPF in a sibling subtree is never mistaken for an enclosing one.
        """
        for parent in Path(file_path).resolve().parents:
            opf = _locate_opf(parent, descend=False)
            if opf is not None:
                return opf
        return None


def _locate_opf(directory: Path, *, descend: bool = True) -> Path | None:
    container = directory / "META-INF" / "container.xml"
    if container.is_file():
        rootfile = etree.parse(str(container)).find(f".//{{{_CONTAINER_NS}}}rootfile")
        if rootfile is not None and rootfile.get("full-path"):
            candidate = (directory / rootfile.get("full-path")).resolve()
            if candidate.is_file():
                return candidate
    opfs = sorted(directory.glob("*.opf"))
    if not opfs and descend:
        opfs = sorted(directory.glob("*/*.opf"))
    return opfs[0].resolve() if opfs else None


def is_ignored_document(
    document: XhtmlDocument, ignored_types: frozenset[str] = IGNORED_EPUB_TYPES
) -> bool:
    """True if the document's body (or a top-level section) has an ignored
    ``epub:type`` (titlepage, imprint, copyright-page, colophon)."""
    body = document.root.find(f".//{{{XHTML_NS}}}body")
    if body is None:
        return False
    types: set[str] = set((body.get(_EPUB_TYPE) or "").split())
    for child in body:
        if isinstance(child.tag, str):
            types.update((child.get(_EPUB_TYPE) or "").split())
    return bool(types & ignored_types)
