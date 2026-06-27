"""Language resolution and text-node traversal.

``LanguageResolver`` (nearest-ancestor language -> document -> OPF -> default, or
none) and ``TextWalker`` (block-wise traversal that skips protected subtrees and
threads ``ContextState`` across inline markup).
"""

from __future__ import annotations
