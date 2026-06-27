"""Build a minimal unpacked EPUB project tree for tests."""

from __future__ import annotations

from pathlib import Path

_CONTAINER = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" \
media-type="application/oebps-package+xml"/></rootfiles>
</container>"""

_OPF = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="uid">x</dc:identifier><dc:title>X</dc:title><dc:language>en</dc:language>
</metadata>
<manifest>
<item id="title" href="titlepage.xhtml" media-type="application/xhtml+xml"/>
<item id="ch1" href="chapter.xhtml" media-type="application/xhtml+xml"/>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
</manifest>
<spine><itemref idref="title"/><itemref idref="ch1"/></spine>
</package>"""

# No xml:lang: relies on the OPF dc:language (publication tier).
_CHAPTER = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body><p>He said "hi" -- done...</p></body></html>"""

_TITLEPAGE = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\
<body epub:type="titlepage"><p>Title "X"...</p></body></html>"""

_NAV = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body><nav>Plain nav</nav></body></html>"""


def make_project(root: Path) -> Path:
    """Create the EPUB source tree under *root* and return it."""
    (root / "META-INF").mkdir(parents=True, exist_ok=True)
    (root / "OEBPS").mkdir(parents=True, exist_ok=True)
    (root / "META-INF" / "container.xml").write_text(_CONTAINER, encoding="utf-8")
    (root / "OEBPS" / "content.opf").write_text(_OPF, encoding="utf-8")
    (root / "OEBPS" / "chapter.xhtml").write_text(_CHAPTER, encoding="utf-8")
    (root / "OEBPS" / "titlepage.xhtml").write_text(_TITLEPAGE, encoding="utf-8")
    (root / "OEBPS" / "nav.xhtml").write_text(_NAV, encoding="utf-8")
    return root
