"""End-to-end CLI behaviour (§8)."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from epub_typogrify import chars
from epub_typogrify.cli import main
from tests.epubs import make_project


def _chapter(root: Path) -> Path:
    return root / "OEBPS" / "chapter.xhtml"


def test_processes_project_in_place(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    result = CliRunner().invoke(main, ["-v", str(project)])
    assert result.exit_code == 0, result.output
    text = _chapter(project).read_text(encoding="utf-8")
    assert "“hi”" in text  # converted (publication language from the OPF)
    assert "done…" in text
    # The titlepage was skipped, the chapter converted.
    assert "skip" in result.output
    assert "changed 1 of 2 file(s); 1 skipped" in result.output
    # Skipped titlepage is untouched on disk.
    assert '"X"' in (project / "OEBPS" / "titlepage.xhtml").read_text(encoding="utf-8")


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    before = _chapter(project).read_bytes()
    result = CliRunner().invoke(main, ["--dry-run", str(project)])
    assert result.exit_code == 0, result.output
    assert "would change 1 of 2 file(s); 1 skipped" in result.output
    assert _chapter(project).read_bytes() == before  # untouched


def test_idempotent_second_run(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    CliRunner().invoke(main, [str(project)])
    result = CliRunner().invoke(main, [str(project)])
    assert "changed 0 of 2 file(s); 1 skipped" in result.output


def test_loose_file_warns_and_converts(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    chapter = _chapter(project)
    result = CliRunner().invoke(main, ["--default-lang", "en", str(chapter)])
    assert result.exit_code == 0, result.output
    assert "appears to belong to the EPUB project" in result.output
    assert "“hi”" in chapter.read_text(encoding="utf-8")


def test_loose_file_unresolved_is_unchanged(tmp_path: Path) -> None:
    lone = tmp_path / "lone.xhtml"
    lone.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>He said "hi"...</p></body></html>',
        encoding="utf-8",
    )
    before = lone.read_bytes()
    result = CliRunner().invoke(main, [str(lone)])
    assert result.exit_code == 0, result.output
    assert lone.read_bytes() == before  # no language, no default -> unchanged
    assert "changed 0 of 1 file(s)" in result.output


def test_missing_target_errors() -> None:
    result = CliRunner().invoke(main, ["does-not-exist.xhtml"])
    assert result.exit_code != 0


def test_normalize_dashes_flag(tmp_path: Path) -> None:
    em = chars.EM_DASH
    en = chars.EN_DASH
    nbsp = chars.NO_BREAK_SPACE
    file = tmp_path / "gb.xhtml"
    file.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-GB">'
        f"<body><p>the cat{em}black{em}ran</p></body></html>",
        encoding="utf-8",
    )
    # Without the flag the em dashes are kept (no en dash appears).
    CliRunner().invoke(main, [str(file)])
    assert en not in file.read_text(encoding="utf-8")
    # With the flag they become spaced en dashes (nbsp before, regular space after).
    result = CliRunner().invoke(main, ["--normalize-dashes", str(file)])
    assert result.exit_code == 0, result.output
    assert f"cat{nbsp}{en} black{nbsp}{en} ran" in file.read_text(encoding="utf-8")


def test_normalize_quotes_flag(tmp_path: Path) -> None:
    ldq = chars.LEFT_DOUBLE_QUOTE
    lsq = chars.LEFT_SINGLE_QUOTE
    rsq = chars.RIGHT_SINGLE_QUOTE
    file = tmp_path / "gb.xhtml"
    file.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-GB">'
        '<body><p>He said "stop" at once.</p></body></html>',
        encoding="utf-8",
    )
    # Default: double-outer (character-based).
    CliRunner().invoke(main, [str(file)])
    assert ldq in file.read_text(encoding="utf-8")
    # With the flag: reflowed to British single-outer nesting.
    file.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-GB">'
        '<body><p>He said "stop" at once.</p></body></html>',
        encoding="utf-8",
    )
    result = CliRunner().invoke(main, ["--normalize-quotes", str(file)])
    assert result.exit_code == 0, result.output
    text = file.read_text(encoding="utf-8")
    assert f"{lsq}stop{rsq}" in text
    assert ldq not in text
