# `epub_typogrify` — Technical Design

## 1. Overview

`epub_typogrify` applies typographic conversions to the textual content of EPUB3 publications:
replacing `...` (3 dots) with `…` (ellipsis), `--` with `–`/`—` (en-/em-dash), straight quotes
with the correct curly quotes, inserting non-breaking spaces where words must stay together, and so on.

`epub_typogrify` is similar to [`se typogrify`](https://github.com/standardebooks/tools/blob/master/se/commands/typogrify.py), but there are some essential differences:

- `se typogrify` assumes American English throughout, `epub_typogrify` is language-aware
- `se typogrify` operates on serialized HTML strings representing the whole file, `epub_typogrify` operates on XHTML DOM, allowing for node-specific language detection
  - `epub_typogrify` selects conversion rules per content node, based on the language that applies to that node. E.g. a French quotation embedded in an English chapter will be typeset with French rules; the surrounding English text will use English rules.

### Goals

- Transform only **text content**; never alter XHTML markup, attributes (except
  where a rule explicitly targets `alt`/`title`), or non-text resources.
- Resolve the **effective language** of every run of text from the EPUB/XHTML
  language model and apply the matching rule set.
- Be **idempotent**: running the tool twice produces the same result as running
  it once.
- Be **extensible**: adding a language should usually mean adding a data file,
  not changing the engine.

### Non-goals

- **EPUB packing/unpacking.** Like `se typogrify`, the tool operates at the
  **authoring stage**, on the *unpacked EPUB project source files* on disk. It
  never reads or writes a `.epub` ZIP container; producing the distributable
  EPUB is a separate build step.
- EPUB2 support (we target EPUB3; EPUB2 may work but is untested).
- Hyphenation / soft-hyphen insertion.
- Spell/grammar correction, content rewriting, or markup normalization.

## 2. Input Model: EPUB Source Files

The tool is pointed at an **unpacked EPUB project directory** (or at individual
XHTML files). It works directly on the source files, in place — the same context
as `se typogrify`, which is run against a checked-out book repository, not a
built `.epub`.

1. **Discover the package (OPF).** Within the project directory, locate the OPF
   package document (via `META-INF/container.xml` when present, or by globbing
   for `*.opf`). The OPF gives:
   - `dc:language` (one or more) — the **publication default language**.
   - the **manifest** + **spine** — the set of XHTML content documents to process.
   When the tool is invoked on **loose `.xhtml` files**, the OPF is *not*
   consulted even if one exists nearby: each file is treated as standalone, the
   publication default falls back to `--default-lang` (and, if that too is
   absent, remains undefined), and a warning is emitted if the file appears to
   belong to an EPUB project — see §5.
2. **Select content documents.** Process spine XHTML items (plus, optionally,
   the navigation document). Certain semantic sections are **skipped**
   (`titlepage`, `imprint`, `copyright-page`, `colophon`) because their
   typography is usually deliberate — mirroring `se`'s ignore list.
3. **Process each XHTML document** (§4–§6).
4. **Write each document back to its file**, in place (the authoring workflow
   relies on version control for review/rollback). `--dry-run` reports changes
   without writing.

## 3. Architecture

```plaintext
   ┌──────────────────────────────────────────────────────────────────────┐
   │ SourceProject  —  find OPF, read spine, enumerate XHTML files        │
   └──────────────────────────────────┬───────────────────────────────────┘
                                      │  per content document
                                      ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │ XhtmlDocument  —  parse → DOM, serialize back                        │
   └──────────────────────────────────┬───────────────────────────────────┘
                                      │  DOM
                                      ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │ TextWalker                                                           │
   │   • in-order traversal of text nodes within each block element       │
   │   • skips protected elements (code, pre, script, MathML, …)          │
   │   • LanguageResolver: nearest xml:lang / lang ancestor → tag         │
   │   • emits (text-run, language, context-state) to the pipeline        │
   └──────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │ LocaleRegistry:  BCP-47 tag → LocaleProfile (+ fallback)             │
   │                                                                      │
   │ Pipeline = generic rules parametrised by LocaleProfile (DATA)        │
   │            + locale-specific code hooks (CODE)                       │
   └──────────────────────────────────┬───────────────────────────────────┘
                                      │  transformed text written back into the text nodes
                                      ▼
   modified DOM ──► serialize ──► overwrite source .xhtml file
```

### Key components

| Component | Responsibility |
|---|---|
| `SourceProject` | Locate the OPF in a source tree, parse it, enumerate spine/content XHTML files on disk. No ZIP handling. |
| `XhtmlDocument` | Parse XHTML to a DOM that **preserves** structure; serialize back without reflowing markup. |
| `LanguageResolver` | Given a node, return the effective BCP-47 language (nearest `xml:lang`/`lang` ancestor → OPF `dc:language` → `--default-lang`), or **none** if nothing in that chain declares one. |
| `TextWalker` | Traverse processable text nodes block-by-block, skipping protected subtrees, carrying cross-node context. |
| `LocaleRegistry` | Map a resolved BCP-47 tag to the most specific **registered** `LocaleProfile` (`fr-CA → fr`); returns **none** when no profile is registered for the language. The shared `default` layer is an inheritance base, not a resolution target. |
| `Pipeline` / `Rule` | Ordered, idempotent transformation stages built from profile data + code hooks. |
| `cli` | Argument parsing, orchestration, reporting. |

## 4. Why DOM, not regex-over-serialized-HTML

`se typogrify` runs regexes against the **serialized HTML string**. This is
simple but couples rules to markup (patterns must dodge tags and attributes) and
makes per-node language switching impractical.

We operate on the **DOM** instead:

- **Markup is never at risk** — we only ever replace the `.text`/`.tail` string
  payload of text nodes. Tags, attributes, and entities are untouched.
- **Language is a property of the tree**, so the nearest-ancestor lookup is
  natural and exact.
- **Protected subtrees** (code, math, etc.) are excluded by not descending into
  them.

The one cost is **context that spans inline markup** — e.g. choosing a closing
quote in `…the <em>cat</em>'s…`, where the apostrophe sits in a different text
node than its opening quote. The `TextWalker` handles this by walking the text
nodes of a block **in document order** and threading a small `ContextState`
(preceding character, open-quote stack) from one node to the next, so
context-sensitive rules see a continuous stream even across element boundaries.

### Protected elements (never transformed)

`pre`, `code`, `kbd`, `samp`, `var`, `tt`, `script`, `style`, MathML
(`math` and descendants), SVG text, and any element carrying an opt-out marker
(`class="notypo"` / `translate="no"`).

## 5. Language Resolution & Segmentation

The XHTML/EPUB language model is hierarchical (README §High-Level Design):

1. Publication default — OPF `dc:language`.
2. Document default — `<html xml:lang>` / `lang`.
3. Inline override — any element's `xml:lang`/`lang` (e.g. a `<span xml:lang="la">`).

`LanguageResolver.effective_lang(node)` walks **up** from a text node to the
first ancestor that declares a language, falling back through document → OPF →
`--default-lang`. The result is a normalised BCP-47 tag, or **none** when the
chain is exhausted: no inline override, no document default, no OPF
`dc:language`, and no `--default-lang` given.

**The publication tier exists only when invoked on a project.** When the target
is a *directory*, the OPF is discovered (§2) and its `dc:language` fills the
publication tier. When the target is an **individual `.xhtml` file**, that file
is treated as **standalone**: the OPF is *not* consulted, so the publication
tier is empty and resolution relies solely on the document/inline languages and
`--default-lang`. This keeps single-file runs predictable and self-contained,
rather than implicitly depending on a file's location on disk. If the tool
detects that a loose file nonetheless sits inside an EPUB project (an enclosing
`container.xml` / `*.opf` is found by walking up), it emits a **warning** noting
that the project's `dc:language` is not being applied and suggesting the user
point at the project directory or pass `--default-lang`.

`TextWalker` therefore yields a stream of **(text-run, lang)** pairs where the
language can change mid-paragraph. The pipeline used for each run is selected
per run, so mixed-language blocks are handled correctly.

**Unresolved language ⇒ no change.** When `effective_lang` returns none, there
is no basis for choosing a rule set, so the text run is **left exactly as
authored** — no pipeline is applied. Applying some arbitrary locale (e.g.
defaulting to English) could silently corrupt correctly-typeset text in an
undeclared language, so the safe behaviour is to do nothing. To opt every such
run into a concrete locale, pass `--default-lang`.

The same hands-off behaviour applies one step later: even when a language *is*
resolved, if the project ships **no rule set** for it, that block is likewise
left unchanged (see §6a).

## 6. Rule Model (Hybrid: data + code)

A locale's behaviour is the sum of two parts.

### 6a. `LocaleProfile` — declarative data

One file per locale (`locales/<tag>.toml`). Profiles **inherit** along the
chain (`fr-CA` overlays `fr` overlays the shared `default` base), so regional
variants state only their differences. `default` is the common base every
profile builds on — it is **not** a locale that text can resolve to. Schema
(illustrative):

```toml
# locales/fr.toml
inherits = "default"

[quotes]
primary   = { open = "«", close = "»" }   # guillemets
secondary = { open = "“", close = "”" }
apostrophe = "’"

[quotes.spacing]
# French inserts a space inside guillemets
inner = " "          # NARROW NO-BREAK SPACE

[dashes]
# what `--` and `---` become, and how ranges are rendered
double_hyphen = "—"       # em dash (range dash differs per locale)
triple_hyphen = "—"
numeric_range = "–"       # en dash, e.g. 1914–1918
dialogue      = "em"      # French dialogue uses em dash + space

[ellipsis]
char = "…"
collapse_spaced_dots = true

[spaces]
# narrow no-break space before high punctuation ; : ! ? and inside « »
before_high_punctuation = " "
nbsp_after_abbreviations = true

[abbreviations]                       # take a (narrow) nbsp before the following token
nonbreaking = ["M.", "Mme", "Mlle", "Dr", "No", "p.", "vol."]

[keep_together]                       # arbitrary "stays on one line" patterns
patterns = [
  { match = '\b(\d+)\s+(°C|°F|%|km|kg|m|cm)\b', join = " " },
]
```

```toml
# locales/en.toml  —  American English (the default for a bare `en` tag)
inherits = "default"

[quotes]
primary   = { open = "“", close = "”" }   # double quotes outermost
secondary = { open = "‘", close = "’" }   # single quotes when nested
apostrophe = "’"
punctuation = "typesetters"               # commas/periods go INSIDE the quotes

[dashes]
double_hyphen = "—"       # `--` → em dash (US parenthetical convention)
triple_hyphen = "—"
numeric_range = "–"       # en dash, e.g. 1914–1918
parenthetical_spacing = "closed"   # the cat—black as night—ran  (no spaces)

[abbreviations]
# American style keeps the full stop on every abbreviation
full_stop_after_contractions = true
nonbreaking = ["Mr.", "Mrs.", "Ms.", "Dr.", "St.", "No.", "vol.", "p."]
```

```toml
# locales/en-GB.toml  —  British English, stated as a DELTA over en.toml.
# Only the conventions that differ from American English appear here; everything
# else (ellipsis, fractions, ranges, …) is inherited unchanged.
inherits = "en"

[quotes]
primary   = { open = "‘", close = "’" }   # single quotes outermost
secondary = { open = "“", close = "”" }   # double quotes when nested
punctuation = "logical"                   # punctuation INSIDE only if part of the quote

[dashes]
double_hyphen = "–"            # `--` → en dash (British parenthetical convention)
parenthetical_spacing = "spaced"   # the cat – black as night – ran

[abbreviations]
# British style drops the full stop after contractions that end in the word's
# last letter (Mr, Mrs, Dr, St) but keeps it after true truncations (vol., p.)
full_stop_after_contractions = false
nonbreaking = ["Mr", "Mrs", "Ms", "Dr", "St", "No.", "vol.", "p."]
```

#### British vs. American English at a glance

| Convention | `en` (American) | `en-GB` (British) |
|---|---|---|
| Outer / inner quotes | `“double”` then `‘single’` | `‘single’` then `“double”` |
| Comma/period vs. closing quote | inside: `“cat,”` | logical: `‘cat’,` (unless part of quote) |
| Parenthetical dash | em, closed: `cat—black—ran` | en, spaced: `cat – black – ran` |
| Title abbreviations | `Mr.` `Mrs.` `Dr.` `St.` | `Mr` `Mrs` `Dr` `St` (no stop) |
| Keep-together nbsp | `Mr.␣ₙSmith` | `Mr␣ₙSmith` |

The **generic engine** turns a profile into a set of parametrised rules
(smart quotes, dashes, ellipsis, ranges, abbreviation nbsp, keep-together,
spacing). Adding a *regular* language is just a new TOML file — and a regional
variant such as `en-GB`, as shown, is usually just the handful of deltas above.

**Resolved-but-unsupported language ⇒ no change.** The registry resolves a tag
to the most specific *registered* profile (`fr-CA → fr`). If the language has
no registered profile at all — text resolves to a tag for which the project
ships no rules — the block is **left unchanged**, exactly as for an unresolved
language (§5). The tool never falls back to applying `default` (or any other
locale's) rules to a language it does not actually support; doing so could
mis-typeset correct text. Supporting that language means adding its profile
(§12).

### 6b. Code hooks — for what data cannot express

Some languages have irregularities a table cannot capture cleanly. Each locale
may register an ordered list of Python callables `(text, profile, ctx) -> text`:

- **French** — narrow no-break space before `;:!?»` and after `«` (partly data,
  but the spacing/exception logic is cleaner in code).
- **German** — low/high quote nesting `„…“ ‚…‘`; `»…«` variant selection.
- **Greek** — diacritic normalisation, mixed Latin/Greek glyph correction
  (as in `se`).
- **English** — historical contraction handling (`’tis`, `’twas`, `M'… → Mc…`),
  fractions, `i.e./e.g.` spacing.
- **British English (`en-GB`)** — the `punctuation = "logical"` setting is a
  hook, not a pure substitution: deciding whether a trailing comma/period
  belongs *inside* a quotation (and so stays) or *outside* (and so moves past
  the closing quote) needs the quote context from `ContextState`. Because the
  general case is ambiguous, the hook only relocates punctuation in
  unambiguous patterns and otherwise leaves the text untouched.

Hooks are discovered through a registry (`@locale_hook("fr")`), keeping the core
engine language-agnostic.

### 6c. Pipeline order

Order matters; the pipeline runs per text-run as:

1. **Pre-normalisation** — Gutenberg backtick→apostrophe, optional whitespace collapse.
2. **Smart quotes & apostrophes** — context-aware, using profile quote chars + the cross-node `ContextState`.
3. **Dashes & hyphens** — `--`/`---`, numeric & roman ranges, true minus `−`.
4. **Ellipsis** — spaced dots → `…`, spacing around it.
5. **Fractions** (where enabled) — `1/2 → ½`, etc.
6. **Non-breaking spacing** — abbreviations, units/numbers, around dashes, word joiners before em dash.
7. **Locale code hooks** — §6b.
8. **Cleanup** — collapse doubled spaces, strip joiners/nbsp from attributes & metadata.

## 7. Idempotency & Safety

- Every rule is written to be **idempotent**: it matches the *raw* form
  (`...`, `--`, `"`) and treats already-converted characters (`…`, `—`, `“`) as
  inert. Running twice is a no-op on the second pass.
- **Markup invariant**: the serializer guarantees that, with no rule matches,
  the file is left byte-identical to its input (verified in tests). Because edits
  are in place, this keeps version-control diffs limited to genuine conversions.
- **Protected subtrees** and **skipped sections** are never entered.
- `--dry-run` reports the diffs without writing; `--verbose` lists per-file,
  per-language change counts.

## 8. CLI

Mirrors `se typogrify`'s ergonomics: a target is a source directory or one or
more `.xhtml` files, and edits are written in place.

```
epub_typogrify [OPTIONS] <source-dir | file.xhtml ...>

  -l, --default-lang TAG   Fallback language for text that declares none.
                           If omitted, text with no resolvable language is
                           left unchanged (no default is assumed).
      --dry-run            Report changes; write nothing.
  -v, --verbose            Per-file / per-language reporting.
```

When given a directory, the tool finds the OPF to resolve the publication
default language and the set of content documents; when given loose `.xhtml`
files it processes them standalone — the OPF is not consulted (a warning is
emitted if the file appears to belong to a project), and `--default-lang` is
the only publication-level fallback. There is deliberately **no built-in
default language** — without a declared language and without `--default-lang`,
the affected text is left untouched (see §5).

## 9. Project Layout

```
src/epub_typogrify/
  __init__.py
  cli.py                 # argument parsing, orchestration, reporting
  source/
    project.py           # locate/parse OPF, enumerate content files on disk
    xhtml.py             # parse / serialize, DOM helpers
  lang/
    resolver.py          # nearest-ancestor BCP-47 resolution
    walker.py            # block-wise text-node traversal + ContextState
  rules/
    pipeline.py          # ordered Rule pipeline
    quotes.py            # context-aware smart quotes/apostrophes
    dashes.py            # hyphens, en/em, ranges, minus
    ellipsis.py
    spacing.py           # nbsp / narrow nbsp / word joiner
    fractions.py
  locales/
    registry.py          # tag → profile, fallback chain, hook registry
    profile.py           # LocaleProfile dataclass + TOML loader
    data/
      default.toml
      en.toml  en-GB.toml
      fr.toml
      de.toml
      la.toml
    hooks/
      en.py  fr.py  de.py  el.py
doc/
  TechnicalDesign.md          (this file)
  TypographyConversions.md    (rule catalogue)
tests/
  unit/  ...               # per-rule, table-driven, multi-locale
  fixtures/                # sample source trees + loose .xhtml, golden outputs
```

The design favours **composition over inheritance** (a pipeline of small,
pure transformation functions; profiles compose via overlay; hooks compose via
registry) and **functional style** (rules are `str -> str` with explicit
context), per project conventions.

## 10. Dependencies

- `lxml` — robust XHTML/XML parsing & serialization with namespace and
  `.text`/`.tail` fidelity.
- `regex` — Unicode property classes (`\p{Letter}`, `\p{Lu}`) that the stdlib
  `re` lacks, as used heavily in the `se` rules.
- `tomli`/`tomllib` — locale profile loading.
- `click` (or stdlib `argparse`) — CLI.

We deliberately **do not** depend on `smartypants` (English-centric); the
quote engine is locale-parametrised and lives in `rules/quotes.py`. `pyphen`
becomes a dependency only if/when hyphenation (§13) is added.

## 11. Testing Strategy

- **Table-driven unit tests** per rule × per locale: `(input, lang) → expected`.
- **Idempotency property test**: `f(f(x)) == f(x)` over the corpus.
- **Markup-invariance test**: documents with no convertible text round-trip
  byte-for-byte.
- **Language-switching fixtures**: paragraphs mixing en/fr/la to verify the
  resolver + per-run pipeline selection.
- **Golden-file end-to-end**: fixture source trees / `.xhtml` files in →
  expected `.xhtml` out (diffed in place).

## 12. Extending to a New Language

1. Add `locales/data/<tag>.toml` declaring quotes, dashes, spacing,
   abbreviations, keep-together patterns (inherit from `default` or a base tag).
2. If the language has irregularities, add `locales/hooks/<tag>.py` and register
   callables with `@locale_hook("<tag>")`.
3. Add table-driven tests.

No engine changes for the common case.

## 13. Open Questions / Future Work

- **Quote-direction ambiguity**: leading apostrophes (`’tis`, `’90s`) need
  per-language heuristics; handled in code hooks initially.
- **CSS-driven language**? Languages set via stylesheets/`:lang()` rather than
  attributes are out of scope — we trust the XHTML/EPUB language attributes.
- **Performance**: large projects — process documents independently; parallelise
  per-file if needed (each file is self-contained once its language context is
  resolved).
