"""End-to-end pipeline behaviour and ordering."""

from __future__ import annotations

from epub_typogrify.locales.profile import LocaleProfile
from epub_typogrify.chars import ELLIPSIS, EM_DASH, EN_DASH, WORD_JOINER
from epub_typogrify.chars import LEFT_DOUBLE_QUOTE as LDQ
from epub_typogrify.chars import ONE_HALF as HALF
from epub_typogrify.chars import RIGHT_DOUBLE_QUOTE as RDQ
from epub_typogrify.chars import RIGHT_SINGLE_QUOTE as RSQ
from epub_typogrify.rules.pipeline import build_pipeline


def test_combined_conversions(en: LocaleProfile) -> None:
    text = '"Wait... it\'s 1/2 done--really" 1914-1918'
    expected = (
        f"{LDQ}Wait{ELLIPSIS} it{RSQ}s {HALF} "
        f"done{WORD_JOINER}{EM_DASH}really{RDQ} 1914{EN_DASH}1918"
    )
    assert build_pipeline(en).run(text) == expected


def test_quotes_can_be_disabled(en: LocaleProfile) -> None:
    out = build_pipeline(en, quotes=False).run('say "hi"')
    assert '"' in out  # straight quotes left untouched
    assert LDQ not in out


def test_fresh_state_per_run_by_default(en: LocaleProfile) -> None:
    pipeline = build_pipeline(en)
    assert pipeline.run('"a"') == pipeline.run('"a"')
