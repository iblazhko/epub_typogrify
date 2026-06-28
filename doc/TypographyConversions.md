# Typographic Conversions

This catalogue lists the conversions `epub_typogrify` performs. Each conversion
is either **language-agnostic** (same everywhere) or **language-specific**
(governed by the `LocaleProfile`, see [TechnicalDesign.md](./TechnicalDesign.md)
§6). Inputs are the *raw* author forms; every rule is idempotent — already-
converted characters are left untouched.

Every rule cites a **source** by short key (e.g. `[SEMOS §8]`); the keys are
defined in [§4 References](#4-references). Code points are named per the
Unicode Standard `[U]`.

Notation for invisible characters used below:

| Name | Code point | Shown as |
|---|---|---|
| No-break space | U+00A0 | `␣ₙ` |
| Narrow no-break space | U+202F | `␣ₜ` |
| Punctuation space | U+2008 | `␣ₚ` |
| Hair space | U+200A | `␣ₕ` |
| Word joiner | U+2060 | `⁤` |

---

## 1. Language-agnostic conversions

These apply to text in any language (subject to the protected-element rules).

### 1.1 Ellipsis
| Input | Output | Source |
|---|---|---|
| `...` | `…` (U+2026) | `[U]`, `[SEMOS §8]` |
| `. . .` (spaced) | `…` | `[SEMOS §8]` |

### 1.2 Em/En dash from hyphens
| Input | Output | Notes | Source |
|---|---|---|---|
| `--` | en/em dash | exact target is **locale-specific** (§2.2) | `[CMOS ch.6]`, `[NHR ch.4]` |
| `---` | `—` (em, U+2014) | | `[CMOS ch.6]`, `[U]` |
| `———` | `⸻` (three-em, U+2E3B) | author/translator name omitted, repeated | `[CMOS ch.6]`, `[SEMOS §8]` |
| `——` | `⸺` (two-em, U+2E3A) | missing/elided word | `[CMOS ch.6]`, `[SEMOS §8]` |

### 1.3 Minus sign
| Input | Output | Source |
|---|---|---|
| `-5` (numeric context) | `−5` (U+2212 true minus) | `[U]`, `[SEMOS §8]` |

### 1.4 Numeric & roman ranges
| Input | Output | Source |
|---|---|---|
| `1914-1918` | `1914–1918` (en dash, U+2013) | `[CMOS ch.6]`, `[NHR ch.4]` |
| `pp. 10-20` | `pp. 10–20` | `[CMOS ch.6]` |
| roman `IV-VI` | `IV–VI` | `[CMOS ch.6]` |

### 1.5 Fractions (where enabled)
| Input | Output | Source |
|---|---|---|
| `1/2 1/4 3/4` | `½ ¼ ¾` | `[U]` (Number Forms), `[SEMOS §8]` |
| `3/8`, … | `⅜`, … | `[U]`, `[SEMOS §8]` |

### 1.6 Word joiner before em dash
Prevents a line break immediately before an em dash: `word—` → `word⁤—`.
Source: `[SEMOS §8]` (em dashes are preceded by a word joiner, U+2060).

### 1.7 Cleanup
- Collapse doubled spaces / doubled nbsp. Source: `[CMOS ch.2]` (single space
  between sentences), `[SEMOS §8]`.
- Strip word joiners and nbsp from attribute values and OPF metadata
  (they are reading-flow aids, not data). Source: `[SEMOS §8]`.

---

## 2. Language-specific conversions

Driven by each locale's `LocaleProfile`. Representative locales below; the engine
is generic, so other languages are added as data.

### 2.1 Quotation marks & apostrophe

The mapping is **character-based**: a straight `"` becomes the locale's *double*
pair, a straight `'` its *single* pair (or the apostrophe). Opening vs. closing
is decided from context, carried across inline markup by the `ContextState`. The
tool does **not** reflow an author's double/single choice into a different
nesting convention.

| Locale | `"` → (double) | `'` → (single) | Apostrophe | Source |
|---|---|---|---|---|
| `en` (US) | `“ … ”` | `‘ … ’` | `’` | `[CMOS ch.6, ch.13]` |
| `en-GB` | `“ … ”` | `‘ … ’` | `’` | `[NHR ch.9]` |
| `fr` | `« … »` | `“ … ”` | `’` | `[IN]` |
| `de` | `„ … “` | `‚ … ‘` | `’` | `[DUDEN]` |
| `la` | inherit surrounding / `“ … ”` | — | — | — (follows host locale) |

> `en` and `en-GB` use the **same** Unicode quote marks; the British convention
> of single quotes as the *outer* mark is realised by the author using `'` for
> outer quotations, which the engine renders faithfully. Code points per `[U]`
> (General Punctuation). British/American differences that the tool *does* apply
> are punctuation placement, abbreviations, and the dash — see §2.7.

### 2.2 `--` target (dialogue/parenthetical dash)

| Locale | `--` becomes | Convention | Source |
|---|---|---|---|
| `en` (US) | `—` (em), closed | `cat—black as night—ran` | `[CMOS ch.6]` |
| `en-GB` | `–` (en), spaced | `cat – black as night – ran` | `[NHR ch.4]` |
| `de` | `–` (en) | Halbgeviertstrich, spaced | `[DUDEN]` |
| `fr` | `—` (em) | dialogue dash + space | `[IN]` |

The table above describes what the author shorthand `--`/`---` becomes. An
**existing** em/en dash is left as the author wrote it by default.

**Opt-in: normalise existing parenthetical dashes** (`--normalize-dashes`). When
enabled, an already-typed parenthetical em/en dash is rewritten to the locale's
convention — glyph from `double_hyphen`, spacing from `parenthetical_spacing`:

| Locale | Input | Output |
|---|---|---|
| `en-GB` | `cat—black`, `cat — black`, `cat–black` | `cat␣ₙ–␣black` (spaced en) |
| `en` (US) | `cat – black` | `cat—black` (closed em) |

This rewrites authorial choices, so it is off by default. The spaced form uses a
non-breaking space before the dash so it cannot begin a line. A dash is bound to
its preceding word whenever it has one — **including a trailing dash at the end
of a paragraph** (interrupted speech), which keeps the non-breaking space but no
following space: `we gotta␣ₙ–`. Left untouched: numeric ranges (`1914–1918`),
the two-/three-em ligatures, dash *runs*, and a dash with **no preceding word**
(a block-start dialogue/list dash, e.g. `– Yes`).

The normalisation works **across inline-markup boundaries**: a dash adjacent to
an element (its word in a neighbouring node) is still bound, e.g. both
`<em>this is it</em> – business` and `this is it – <em>business</em>` become
`…it␣ₙ– business…`, and `we <em>gotta</em> –` becomes `we gotta␣ₙ–`.

### 2.3 Non-breaking spaces (keep-together)

Inserted so paired tokens never split across a line:

| Locale | Pattern → result | Source |
|---|---|---|
| `en` (US) | `Mr. Smith` → `Mr.␣ₙSmith`; `No. 5` → `No.␣ₙ5`; `St. James` → `St.␣ₙJames` | `[CMOS ch.6, ch.10]`, `[SEMOS §8]` |
| `en-GB` | `Mr Smith` → `Mr␣ₙSmith`; `No. 5` → `No.␣ₙ5`; `St James` → `St␣ₙJames` | `[NHR ch.10]` |
| `fr` | `M. Dupont` → `M.␣ₙDupont`; `p. 12` → `p.␣ₙ12` | `[IN]` |
| all | `100 km` → `100␣ₙkm`; `20 °C` → `20␣ₙ°C`; `5 %` → `5␣ₙ%` (configurable units) | `[U]` (SI/general), `[IN]` |

Abbreviation lists are **per locale** (`Mr./Mrs./Dr.` for American English,
the stop-less `Mr/Mrs/Dr` for British English — see §2.7 — `M./Mme/Mlle` for
French, etc.).

### 2.4 Narrow no-break space before high punctuation (French)

French inserts a narrow no-break space inside guillemets and before
`; : ! ?`:

| Input | Output | Source |
|---|---|---|
| `« Bonjour »` | `«␣ₜBonjour␣ₜ»` | `[IN]` |
| `Vraiment ?` | `Vraiment␣ₜ?` | `[IN]` |
| `Oui : voilà` | `Oui␣ₜ: voilà` | `[IN]` |

(Per `[IN]`, the colon takes a full non-breaking space and the high punctuation
`; ! ?` a narrow one; the engine applies the locale-configured widths.)

### 2.5 Ellipsis spacing (Standard Ebooks house style)

**Opt-in** (`--ellipsis-spacing`), spacing is
applied around the ellipsis glyph `…` . Notation: `⁤` = word
joiner (U+2060), `␣ₚ` = punctuation space (U+2008).

| Position | Rule | Example |
|---|---|---|
| Before | word joiner + punctuation space + word joiner | `word⁤␣ₚ⁤…` |
| Before — exceptions | none at a block start, or directly after an opening quote | `“…` (tight) |
| After a word | regular space | `…␣word` |
| After — before punctuation | punctuation space | `…␣ₚ!` |
| After — before a closing quote | nothing (tight) | `…”` |

The before-sandwich keeps the ellipsis a subtle, **non-breaking** punctuation space from
the preceding word (the word joiners stop it wrapping to a new line). The "block
start" and "opening quote" exceptions are resolved across inline-markup
boundaries (via the cross-node preceding character), so an ellipsis at the start
of a `<em>` tail is still bound to the word before it. Off by default; the rule
implements the **English** convention and is independent of locale.

### 2.6 Locale code-hook conversions

Irregularities handled in code rather than data (TechnicalDesign §6b):

- **English** — contractions `’tis`, `’twas`, `’twere`; `M'…` → `Mc…`;
  `i. e.` → `i.e.`, `e. g.` → `e.g.`; `A. D.` → `AD`.
  Source: `[CMOS ch.7, ch.10]`, `[SEMOS §8]`.
- **French** — narrow no-break space around high punctuation and guillemets
  (§2.4). Source: `[IN]`.
- **Greek** *(deferred)* — diacritic normalisation, mixed Latin/Greek glyph
  correction. Source: `[U]` (Greek block, normalization), `[SEMOS §8]`.

Two conventions that the catalogue once listed as hooks are in fact handled
elsewhere:

- **Punctuation placement** (US typesetters' vs. British logical, §2.7) is a
  **profile-driven core rule**, not a per-locale hook: it keys off the
  `punctuation` setting, so it applies to any locale that declares it.
- **German `„…“` / `‚…‘` nesting** is **data-driven**: the character-based quote
  engine produces it from the author's `"`/`'` and the `de` profile's marks, so
  no hook is needed. Only a `»…«` variant selector would require one (deferred).

### 2.7 British vs. American English

The two English locales share most rules but differ on three conventions the
tool applies. `en` (bare tag) is treated as American English; `en-GB` is a small
delta over it. US conventions follow `[CMOS]`; British conventions follow `[NHR]`.

| Convention | `en` (American) | `en-GB` (British) | Source |
|---|---|---|---|
| Punctuation vs. closing quote | typesetters' — always inside | logical — inside only if part of the quote | `[CMOS ch.6]` / `[NHR ch.9]` |
| Parenthetical dash (§2.2) | em, closed: `cat—black—ran` | en, spaced: `cat – black – ran` | `[CMOS ch.6]` / `[NHR ch.4]` |
| Title abbreviations (§2.3) | `Mr.` `Mrs.` `Dr.` `St.` | `Mr` `Mrs` `Dr` `St` (no stop) | `[CMOS ch.10]` / `[NHR ch.10]` |

> **Quote marks: by default *not* a difference the tool applies.** Both locales
> map `"` → `“ ”` and `'` → `‘ ’` (§2.1). British single-as-outer is, by default,
> the author's choice of straight mark, rendered faithfully.

**Opt-in: normalise quote nesting** (`--normalize-quotes`). When enabled, the
engine reads quotation marks — **straight or curly, in any combination** — and
re-emits them by **nesting depth**: the outermost level uses the locale's
*primary* mark (`quotes.outer`), the next its *secondary*, alternating. So a
document quoted in one convention is reflowed to its locale's:

| Locale (`outer`) | Input | Output |
|---|---|---|
| `en` (double) | `'systems', he said, "with us"` | `“systems,” he said, ‘with us’` |
| `en-GB` (single) | `"systems," he said, 'with us'` | `‘systems,’ he said, “with us”` |

Off by default — it rewrites authorial choices. Apostrophes, contractions,
possessives, and elisions (`don't`, `dogs'`, `'92`, `'tis`) are preserved.
Residual ambiguity: a possessive `’` inside a single-quoted span
(`‘the dogs’ bone’`) may be read as the close — best-effort, and pre-existing.

**Punctuation placement** — the position of a trailing period/comma relative to
the closing quote differs by locale: `[CMOS ch.6]` typesetters' style puts it
*inside*, `[NHR ch.9]` logical style *outside*:

| Input | `en` (inside) | `en-GB` (outside) |
|---|---|---|
| `"cat".` | `“cat.”` | `‘cat’.` |
| `'go',` | `‘go,’` | `“go”,` (nested) |

This has two layers:

1. **Default (always on, mild).** A trailing period/comma is moved *inside* a
   closing **double** quote for `typesetters` locales (`“cat”.` → `“cat.”`).
   Restricted to double quotes, since a regex cannot tell a closing single quote
   from an apostrophe; `logical` locales are left as authored.
2. **Opt-in (`--normalize-quote-punctuation`).** The relocation is done inside
   the quote engine — which *does* know a `’` is a close, not an apostrophe — so
   it applies to **single and double** closing quotes. `typesetters` (American)
   pulls a trailing period/comma inside. `logical` (British) pushes a trailing
   **comma** outside but **keeps sentence-terminal punctuation (`.` `!` `?`)
   inside**, because British style retains it inside when the quotation is, or
   ends with, a complete sentence — the common dialogue case:

   > `‘Not today’, Skinner said. ‘Not like the other day … around.’`

   The comma after the fragment *Not today* moves outside; the period that ends
   the complete-sentence quotation stays inside. A trailing ellipsis (a run of
   dots) is never split. Combine with `--normalize-quotes` to conform a document
   to full locale house style.

   **Limitation.** Distinguishing a complete-sentence quotation from an embedded
   fragment (where logical style *would* move a terminal period outside, e.g.
   `he called it ‘a disgrace’.`) is not reliably decidable, so terminal
   punctuation is left where the author placed it rather than risk the more
   jarring error of ejecting a sentence's full stop. Only the unambiguous comma
   is relocated.

**Abbreviation full stops** — British style drops the stop after a contraction
that ends in the word's final letter (`Mr`, `Mrs`, `Dr`, `St`) but keeps it
after a true truncation (`vol.`, `p.`, `No.`). Source: `[NHR ch.10]` vs.
`[CMOS ch.10]`.

| Input | `en` output | `en-GB` output |
|---|---|---|
| `Mr. Smith` | `Mr.␣ₙSmith` | `Mr␣ₙSmith` |
| `vol. II` | `vol.␣ₙII` | `vol.␣ₙII` |

---

## 3. What is **not** converted

- Content inside `pre`, `code`, `kbd`, `samp`, `var`, `tt`, `script`, `style`,
  MathML, SVG text.
- Elements marked `translate="no"` / `class="notypo"`.
- Skipped sections: `titlepage`, `imprint`, `copyright-page`, `colophon`.
- Text whose language cannot be resolved — no inline/document/OPF language and
  no `--default-lang` — is left exactly as authored (no rules are applied).
- Text whose resolved language has **no rule set** in the project is likewise
  left unchanged (the tool never substitutes another locale's rules).
- All XHTML markup, attributes (except `alt`/`title` where a rule targets them),
  entities, and non-text resources.

---

## 4. References

Citation keys used throughout this document. Section/rule numbers refer to the
cited edition; where an online edition exists, the link points to it.

- **`[U]`** — *The Unicode Standard*, code charts: General Punctuation
  (U+2000–U+206F), Supplemental Punctuation (U+2E00–U+2E7F), and Number Forms
  (U+2150–U+218F). <https://www.unicode.org/charts/>
- **`[CMOS]`** — *The Chicago Manual of Style*, 17th ed. (American English).
  Ch. 6 (Punctuation: dashes, quotation marks), Ch. 10 (Abbreviations), Ch. 13
  (Quotations and Dialogue). <https://www.chicagomanualofstyle.org/>
- **`[NHR]`** — *New Hart's Rules: The Oxford Style Guide*, 2nd ed. (British
  English). Ch. 4 (Punctuation), Ch. 9 (Quotations), Ch. 10 (Abbreviations).
  Oxford University Press.
- **`[IN]`** — *Lexique des règles typographiques en usage à l'Imprimerie
  nationale* (French). See also *Espace fine insécable* —
  <https://fr.wikipedia.org/wiki/Espace_fine_ins%C3%A9cable>
- **`[DUDEN]`** — *Duden — Die deutsche Rechtschreibung* (German quotation
  marks `„ “` and `‚ ‘`). <https://www.duden.de/>
- **`[SEMOS]`** — *The Standard Ebooks Manual of Style*, §8 Typography (the
  house style this tool's English/agnostic rules most closely follow).
  <https://standardebooks.org/manual/latest/8-typography>
