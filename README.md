# EPUB Typogrify

`epub_typogrify` is a tool for applying typographic conversions to EPUB3 content in order to improve text readability.

## High-Level Design

EPUB is a distribution and interchange format for digital publications and documents. This format allows for a multi-language content:
- EPUB project metadata can specify overall language of the publication
- Individual content file can specify file-specific language
- Individual parts of a file can specify their own language, e.g. a title in English and a subtitle in French, or a quote in Latin inside an English text

`epub_typogrify` operates on EPUB content files, applying typographic conversions to improve readability. Typographic conversions are applied to content nodes of EPUB XHTML leaving the rest of the file, in particular the XHTML markup, untouched.

Typographic conversions are language-specific and applied according to the effective language of the current block of the content file.

See [`doc/TechnicalDesign.md`](doc/TechnicalDesign.md) for the architecture and
[`doc/ImplementationPlan.md`](doc/ImplementationPlan.md) for the build plan.

## Typographic Rules

The catalogue of conversions — language-agnostic and language-specific — is in
[`doc/TypographyConversions.md`](doc/TypographyConversions.md).

## Usage

Point the tool at an unpacked EPUB project directory, or at individual XHTML
files. Edits are written in place (rely on version control for review/rollback).

```sh
# Process a project: the OPF supplies the publication language and content set.
epub_typogrify path/to/book/

# Preview without writing, with per-file reporting.
epub_typogrify --dry-run -v path/to/book/

# Loose files are processed standalone; give a language for undeclared text.
epub_typogrify --default-lang en chapter.xhtml
```

Text whose language cannot be resolved — and that has no `--default-lang` — is
left unchanged, as is anything in `pre`/`code`/MathML/`translate="no"` and in
`titlepage`/`imprint`/`copyright-page`/`colophon` sections.

## Development

Dependencies are managed with [`uv`](https://docs.astral.sh/uv/); the project
virtualenv and the locked dependency set are provisioned for you.

```sh
uv sync                 # create .venv and install runtime + dev deps from uv.lock
uv run pytest           # run the tests
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy src         # type-check
```

Continuous integration (GitHub Actions) runs the lint, format-check, type-check,
and test steps across supported Python versions on every push and pull request.

> Status: **Phase 4** (OPF discovery + CLI) is in place — the tool runs
> end-to-end. Point `epub_typogrify` at an unpacked EPUB project directory (its
> OPF supplies the publication language and content set) or at loose `.xhtml`
> files; edits are written in place, with `--dry-run` to preview. Phase 5
> (hardening, packaging) remains. See
> [`doc/ImplementationPlan.md`](doc/ImplementationPlan.md) for the roadmap.

## References

1. EPUB3 Specification: [https://www.w3.org/publishing/epub3/](https://www.w3.org/publishing/epub3/)
2. Standard Ebooks: [https://standardebooks.org/](https://standardebooks.org/)
3. [`se typogrify`](https://github.com/standardebooks/tools/blob/master/se/commands/typogrify.py) - reference implementation that inspired this project; `se typogrify` targets American English only.
