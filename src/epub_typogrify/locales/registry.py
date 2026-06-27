"""``LocaleRegistry`` — resolve a BCP-47 tag to a :class:`LocaleProfile`.

Two distinct mechanisms (see ``doc/TechnicalDesign.md`` §6a):

* **Resolution** maps a *requested* tag to the most specific *registered*
  profile by walking the subtag chain (``fr-CA`` -> ``fr``). If nothing in that
  chain is registered, resolution returns ``None`` and the caller leaves the
  text unchanged — the tool never invents rules for an unsupported language.
* **Inheritance** composes a registered profile over its ``inherits`` parent up
  to the shared ``default`` base. ``default`` is an inheritance base only; it is
  never itself a resolution target.
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from epub_typogrify.locales.profile import LocaleProfile, profile_from_dict

DEFAULT_TAG = "default"


def _norm(tag: str) -> str:
    return tag.strip().lower()


def _subtag_chain(tag: str) -> list[str]:
    """``"fr-CA"`` -> ``["fr-ca", "fr"]`` (most specific first)."""
    parts = _norm(tag).split("-")
    return ["-".join(parts[:i]) for i in range(len(parts), 0, -1)]


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = dict(base)
    for key, value in override.items():
        existing = result.get(key)
        if isinstance(value, Mapping) and isinstance(existing, Mapping):
            result[key] = _deep_merge(existing, value)
        else:
            result[key] = value
    return result


class LocaleRegistry:
    """Holds raw per-tag profile data and resolves/inherits on demand."""

    def __init__(self, raw_profiles: Mapping[str, Mapping[str, Any]]) -> None:
        self._raw: dict[str, dict[str, Any]] = {
            _norm(tag): dict(data) for tag, data in raw_profiles.items()
        }
        self._cache: dict[str, LocaleProfile | None] = {}

    @classmethod
    def from_directory(cls, directory: Path | str) -> LocaleRegistry:
        """Load every ``<tag>.toml`` in *directory* (file stem is the tag)."""
        raw: dict[str, dict[str, Any]] = {}
        for path in sorted(Path(directory).glob("*.toml")):
            with path.open("rb") as handle:
                raw[path.stem] = tomllib.load(handle)
        return cls(raw)

    @classmethod
    def default(cls) -> LocaleRegistry:
        """Load the locale profiles shipped in :mod:`epub_typogrify.locales.data`."""
        return cls.from_directory(Path(__file__).parent / "data")

    def _merged(self, tag: str) -> dict[str, Any] | None:
        """Return the inheritance-merged data for *tag*, or ``None`` if unregistered."""
        key = _norm(tag)
        data = self._raw.get(key)
        if data is None:
            return None
        own = {k: v for k, v in data.items() if k != "inherits"}
        parent = data.get("inherits")
        if parent:
            base = self._merged(str(parent)) or {}
            return _deep_merge(base, own)
        return own

    def resolve(self, tag: str | None) -> LocaleProfile | None:
        """Resolve *tag* to a profile, or ``None`` if the language is unsupported."""
        if not tag:
            return None
        key = _norm(tag)
        if key in self._cache:
            return self._cache[key]

        profile: LocaleProfile | None = None
        for candidate in _subtag_chain(tag):
            if candidate == DEFAULT_TAG:
                continue  # default is an inheritance base, never a resolution target
            if candidate in self._raw:
                profile = profile_from_dict(candidate, self._merged(candidate) or {})
                break

        self._cache[key] = profile
        return profile
