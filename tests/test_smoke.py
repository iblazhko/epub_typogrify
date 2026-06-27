"""Phase 0 smoke tests: the package imports and exposes its scaffolding."""

from __future__ import annotations

import epub_typogrify


def test_package_exposes_version() -> None:
    assert isinstance(epub_typogrify.__version__, str)
    assert epub_typogrify.__version__


def test_cli_entry_point_is_callable() -> None:
    from epub_typogrify.cli import main

    assert callable(main)
