"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from epub_typogrify.locales.profile import LocaleProfile
from tests.profiles import EN, EN_GB


@pytest.fixture
def en() -> LocaleProfile:
    return EN


@pytest.fixture
def en_gb() -> LocaleProfile:
    return EN_GB
