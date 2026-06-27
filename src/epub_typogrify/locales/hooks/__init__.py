"""Per-locale code hooks — irregularities that profile data cannot express.

A hook is an ordinary :data:`~epub_typogrify.rules.context.Rule` registered for a
BCP-47 tag with :func:`locale_hook`. :func:`hooks_for` returns the hooks that
apply to a tag, walking the subtag chain from general to specific so that, e.g.,
``en-GB`` also runs the ``en`` hooks (then any of its own).
"""

from __future__ import annotations

from collections.abc import Callable

from epub_typogrify.rules.context import Rule

_HOOKS: dict[str, list[Rule]] = {}


def locale_hook(tag: str) -> Callable[[Rule], Rule]:
    """Register a rule as a code hook for *tag* (preserving registration order)."""

    def decorator(func: Rule) -> Rule:
        _HOOKS.setdefault(tag.strip().lower(), []).append(func)
        return func

    return decorator


def _subtag_chain(tag: str) -> list[str]:
    """``"fr-CA"`` -> ``["fr", "fr-ca"]`` (general first)."""
    parts = tag.strip().lower().split("-")
    return ["-".join(parts[: i + 1]) for i in range(len(parts))]


def hooks_for(tag: str) -> list[Rule]:
    """All hooks applying to *tag*, general-to-specific."""
    result: list[Rule] = []
    for candidate in _subtag_chain(tag):
        result.extend(_HOOKS.get(candidate, []))
    return result


# Import hook modules for their registration side effects (after the registry and
# decorator are defined, so the modules can import them).
from epub_typogrify.locales.hooks import en as _en  # noqa: E402,F401
from epub_typogrify.locales.hooks import fr as _fr  # noqa: E402,F401
