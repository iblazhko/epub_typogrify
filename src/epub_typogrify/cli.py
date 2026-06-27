"""Command-line entry point for ``epub_typogrify`` (TechnicalDesign.md §8).

Targets are a source directory (its OPF drives language and the content set) or
loose ``.xhtml`` files (processed standalone). Files are edited in place;
``--dry-run`` reports without writing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import click

from epub_typogrify.locales.registry import LocaleRegistry
from epub_typogrify.processor import typogrify_document
from epub_typogrify.source.project import SourceProject, is_ignored_document
from epub_typogrify.source.xhtml import XhtmlDocument


@dataclass
class _Stats:
    processed: int = 0
    changed: int = 0
    skipped: int = 0


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "targets",
    nargs=-1,
    required=True,
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "-l",
    "--default-lang",
    "default_lang",
    metavar="TAG",
    default=None,
    help="Fallback language for text that declares none. If omitted, text with no "
    "resolvable language is left unchanged.",
)
@click.option("--dry-run", is_flag=True, help="Report changes; write nothing.")
@click.option("-v", "--verbose", is_flag=True, help="Per-file reporting.")
def main(targets: tuple[Path, ...], default_lang: str | None, dry_run: bool, verbose: bool) -> None:
    """Apply language-aware typographic conversions to EPUB source files."""
    registry = LocaleRegistry.default()
    stats = _Stats()
    for target in targets:
        if target.is_dir():
            _process_directory(target, registry, default_lang, dry_run, verbose, stats)
        else:
            _process_loose_file(target, registry, default_lang, dry_run, verbose, stats)
    _report_summary(stats, dry_run)


def _process_directory(
    directory: Path,
    registry: LocaleRegistry,
    default_lang: str | None,
    dry_run: bool,
    verbose: bool,
    stats: _Stats,
) -> None:
    try:
        project = SourceProject.from_directory(directory)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    if verbose:
        language = project.publication_language or "undeclared"
        click.echo(f"{directory} (publication language: {language})")
    for doc_path in project.content_documents:
        data = doc_path.read_bytes()
        document = XhtmlDocument.from_bytes(data)
        label = _relative(doc_path, directory)
        if is_ignored_document(document):
            stats.skipped += 1
            _verbose_line(verbose, "skip", label)
            continue
        typogrify_document(
            document,
            registry,
            publication_lang=project.publication_language,
            default_lang=default_lang,
        )
        _finish(document, doc_path, data, label, dry_run, verbose, stats)


def _process_loose_file(
    path: Path,
    registry: LocaleRegistry,
    default_lang: str | None,
    dry_run: bool,
    verbose: bool,
    stats: _Stats,
) -> None:
    enclosing = SourceProject.find_enclosing_opf(path)
    if enclosing is not None:
        click.echo(
            f"warning: {path} appears to belong to the EPUB project at {enclosing}; "
            "its dc:language is not used. Pass the project directory or --default-lang.",
            err=True,
        )
    data = path.read_bytes()
    document = XhtmlDocument.from_bytes(data)
    typogrify_document(document, registry, publication_lang=None, default_lang=default_lang)
    _finish(document, path, data, path, dry_run, verbose, stats)


def _finish(
    document: XhtmlDocument,
    path: Path,
    original: bytes,
    label: Path | str,
    dry_run: bool,
    verbose: bool,
    stats: _Stats,
) -> None:
    output = document.to_bytes()
    stats.processed += 1
    if output != original:
        stats.changed += 1
        if not dry_run:
            path.write_bytes(output)
        _verbose_line(verbose, "conv", label)
    else:
        _verbose_line(verbose, "--", label)


def _relative(path: Path, base: Path) -> Path | str:
    try:
        return path.relative_to(base.resolve())
    except ValueError:
        return path


def _verbose_line(verbose: bool, marker: str, label: Path | str) -> None:
    if verbose:
        click.echo(f"  {marker:<4} {label}")


def _report_summary(stats: _Stats, dry_run: bool) -> None:
    verb = "would change" if dry_run else "changed"
    parts = [f"{verb} {stats.changed} of {stats.processed} file(s)"]
    if stats.skipped:
        parts.append(f"{stats.skipped} skipped")
    click.echo("; ".join(parts))
