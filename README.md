# EPUB Typogrify

`epub_typogrify` is a tool for applying typographic conversions to EPUB3 content.

## High-Level Design

EPUB is a distribution and interchange format for digital publications and documents. This format allows for a multi-language content:
- Overall language is specified in the EPUB project metadata
- Individual language is specified in the EPUB content file metadata
- Individual parts of a file may have different languages, e.g. a title in English and a subtitle in French, or a quote in Latin inside an English text

`epub_typogrify` operates on EPUB content files, applying typographic conversions to improve readability. Typographic conversions are applied to content nodes of EPUB XHTML leaving the rest of the file, in particular the XHTML markup, untouched.

Typographic conversions are language-specific and applied according to the language of the current block of content.

See [`doc/TechnicalDesign.md`](doc/TechnicalDesign.md) for the architecture and
[`doc/ImplementationPlan.md`](doc/ImplementationPlan.md) for the build plan.

## Typographic Rules

The catalogue of conversions — language-agnostic and language-specific — is in
[`doc/TypographyConversions.md`](doc/TypographyConversions.md).

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

> Status: **Phase 2** (locale profiles + code hooks; en, en-GB, fr, de, la) is in
> place. See [`doc/ImplementationPlan.md`](doc/ImplementationPlan.md) for the roadmap.

## References

1. EPUB3 Specification: [https://www.w3.org/publishing/epub3/](https://www.w3.org/publishing/epub3/)
2. Standard Ebooks: [https://standardebooks.org/](https://standardebooks.org/)
3. [`se typogrify`](https://github.com/standardebooks/tools/blob/master/se/commands/typogrify.py) (American English only)
