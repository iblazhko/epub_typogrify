"""Typographic transformation rules and the pipeline that composes them.

Pure ``str``-level logic (no DOM, no IO): the ``Rule``/``Pipeline`` abstraction,
``ContextState``, the language-agnostic rules, and the locale-parametrised quote
engine. Built in Phase 1 (see ``doc/ImplementationPlan.md``).
"""

from __future__ import annotations
