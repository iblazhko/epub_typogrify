"""Locale profiles (declarative data) and per-locale code hooks, plus the registry.

``LocaleProfile`` loading/inheritance, the ``LocaleRegistry`` (tag -> profile, or
none for unsupported languages), the ``data/`` TOML profiles, and the ``hooks/``
code overrides. Built in Phase 2 (see ``doc/ImplementationPlan.md``).
"""

from __future__ import annotations
