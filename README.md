# EPUB Typogrify

`epub_typogrify` is a tool for applying typographic conversions to EPUB3 content in order to improve text readability.

## High-Level Design

EPUB is a distribution and interchange format for digital publications and documents. This format allows for a multi-language content:
- EPUB project metadata can specify overall language of the publication
- Individual content file can specify file-specific language
- Individual parts of a file can specify their own language, e.g. a title in English and a subtitle in French, or a quote in Latin inside an English text

`epub_typogrify` operates on EPUB content files, applying typographic conversions to improve readability. Typographic conversions are applied to content nodes of EPUB XHTML leaving the rest of the file, in particular the XHTML markup, untouched.

Typographic conversions are language-specific and applied according to the effective language of the current block of the content file.

See [`doc/TechnicalDesign.md`](doc/TechnicalDesign.md) for the architecture.

## Typographic Rules

The catalogue of conversions — language-agnostic and language-specific — is in
[`doc/TypographyConversions.md`](doc/TypographyConversions.md).

## Usage

```
epub_typogrify [OPTIONS] <source-dir | file.xhtml ...>
```

`epub_typogrify` operates at the authoring stage, on the **unpacked** EPUB source
files (it does not read or write a `.epub` ZIP). Edits are written **in place**,
so run it from a clean version-control state and review the diff.

### Targets

- **A project directory** — the tool finds the OPF package document (via
  `META-INF/container.xml`, or an `*.opf` glob), reads the publication language
  from `dc:language`, and processes the XHTML documents listed in the spine
  (plus the navigation document).
- **Individual `.xhtml` files** — processed standalone. The OPF is *not*
  consulted even if one exists nearby; a warning is emitted if the file appears
  to belong to a project, suggesting you point at the project directory or pass
  `--default-lang`.

### Options

| Option | Description |
|---|---|
| `-l`, `--default-lang TAG` | Fallback language (BCP-47, e.g. `en`, `en-GB`, `fr`) for text that declares none. If omitted, text with no resolvable language is left unchanged — no default is assumed. |
| `--normalize-dashes` | Also rewrite existing parenthetical em/en dashes to the locale convention (e.g. closed em dashes for `en`, spaced en dashes for `en-GB`). Off by default — it rewrites authorial dash choices, so it is opt-in. |
| `--normalize-quotes` | Also reflow quotation marks (straight *or* curly, in any combination) to the locale's nesting convention — double-outer for `en`, single-outer for `en-GB`. Off by default (same opt-in rationale). |
| `--dry-run` | Report what would change; write nothing. |
| `-v`, `--verbose` | Per-file reporting (`conv` changed, `skip` ignored section, `--` unchanged). |
| `-h`, `--help` | Show help and exit. |

### How the language of each text run is chosen

Conversions are language-specific and selected **per content node**. The language
of a run of text is resolved as: nearest ancestor `xml:lang`/`lang` → the
document's `<html lang>` → the publication `dc:language` (project runs only) →
`--default-lang`. If none of these apply, the run is left unchanged. Supported
languages are `en` (American), `en-GB` (British), `fr`, `de`, and `la`; text in
any other language is left untouched.

### What is left untouched

- All XHTML markup, attributes, entities, and non-text resources — only text
  content is transformed.
- Content inside `pre`, `code`, `kbd`, `samp`, `var`, `tt`, `script`, `style`,
  MathML, SVG, and any element marked `translate="no"` or `class="notypo"`.
- Sections whose typography is usually deliberate: `titlepage`, `imprint`,
  `copyright-page`, `colophon`.

### Examples

```sh
# Process a project in place (publication language comes from the OPF).
epub_typogrify path/to/book/

# Preview the changes without writing them, with per-file reporting.
epub_typogrify --dry-run -v path/to/book/

# Process loose files, supplying a language for otherwise-undeclared text.
epub_typogrify --default-lang en src/chapter-1.xhtml src/chapter-2.xhtml

# Also normalise existing em dashes to the locale convention (e.g. a British
# book that uses closed em dashes -> spaced en dashes).
epub_typogrify --normalize-dashes path/to/book/
```

The full catalogue of conversions is in
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

## References

1. EPUB3 Specification: [https://www.w3.org/publishing/epub3/](https://www.w3.org/publishing/epub3/)
2. Standard Ebooks: [https://standardebooks.org/](https://standardebooks.org/)
3. [`se typogrify`](https://github.com/standardebooks/tools/blob/master/se/commands/typogrify.py) - reference implementation that inspired this project; `se typogrify` targets American English only.
