"""Source-project access for the authoring stage (no EPUB ZIP handling).

``SourceProject`` (locate/parse the OPF, enumerate spine content files, apply the
skip-list) and ``XhtmlDocument`` (markup-preserving parse/serialize). Built in
Phases 3-4 (see ``doc/ImplementationPlan.md``).
"""

from __future__ import annotations
