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

| Locale | Primary | Secondary (nested) | Apostrophe | Source |
|---|---|---|---|---|
| `en` (US) | `“ … ”` | `‘ … ’` | `’` | `[CMOS ch.6, ch.13]` |
| `en-GB` | `‘ … ’` | `“ … ”` | `’` | `[NHR ch.9]` |
| `fr` | `« … »` | `“ … ”` | `’` | `[IN]` |
| `de` | `„ … “` | `‚ … ‘` | `’` | `[DUDEN]` |
| `la` | inherit surrounding / `“ … ”` | — | — | — (follows host locale) |

Straight `"`/`'` are converted to the locale's marks using context (opening vs
closing) carried across inline markup by the `ContextState`. Mark code points
per `[U]` (General Punctuation).

### 2.2 `--` target (dialogue/parenthetical dash)

| Locale | `--` becomes | Convention | Source |
|---|---|---|---|
| `en` (US) | `—` (em), closed | `cat—black as night—ran` | `[CMOS ch.6]` |
| `en-GB` | `–` (en), spaced | `cat – black as night – ran` | `[NHR ch.4]` |
| `de` | `–` (en) | Halbgeviertstrich, spaced | `[DUDEN]` |
| `fr` | `—` (em) | dialogue dash + space | `[IN]` |

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

### 2.5 Hair space around ellipsis / closing quote (English, SE house style)
| Input | Output | Source |
|---|---|---|
| `…"` | `…␣ₕ”` | `[SEMOS §8]` |
| `well …` before tag | spacing normalised to hair space | `[SEMOS §8]` |

### 2.6 Locale code-hook conversions

Irregularities handled in code rather than data (TechnicalDesign §6b):

- **English** — contractions `’tis`, `’twas`, `’twere`; `M'…` → `Mc…`;
  `i. e.` → `i.e.`, `e. g.` → `e.g.`; `A. D.` → `AD`.
  Source: `[CMOS ch.7, ch.10]`, `[SEMOS §8]`.
- **British English (`en-GB`)** — logical punctuation placement (see §2.7);
  applied only to unambiguous patterns. Source: `[NHR ch.9]`.
- **German** — `„…“` / `‚…‘` nesting; optional `»…«` guillemet variant.
  Source: `[DUDEN]`.
- **Greek** — diacritic normalisation, mixed Latin/Greek glyph correction.
  Source: `[U]` (Greek block, normalization), `[SEMOS §8]`.

### 2.7 British vs. American English

The two English locales share most rules but differ on four conventions. `en`
(bare tag) is treated as American English; `en-GB` is a small delta over it.
US conventions follow `[CMOS]`; British conventions follow `[NHR]`.

| Convention | `en` (American) | `en-GB` (British) | Source |
|---|---|---|---|
| Outer / inner quotes | `“double”` then `‘single’` | `‘single’` then `“double”` | `[CMOS ch.6]` / `[NHR ch.9]` |
| Punctuation vs. closing quote | typesetters' — always inside | logical — inside only if part of the quote | `[CMOS ch.6]` / `[NHR ch.9]` |
| Parenthetical dash (§2.2) | em, closed: `cat—black—ran` | en, spaced: `cat – black – ran` | `[CMOS ch.6]` / `[NHR ch.4]` |
| Title abbreviations (§2.3) | `Mr.` `Mrs.` `Dr.` `St.` | `Mr` `Mrs` `Dr` `St` (no stop) | `[CMOS ch.10]` / `[NHR ch.10]` |

**Quotes** — straight quotes resolve to opposite primary/secondary marks
(`[CMOS ch.6]` / `[NHR ch.9]`):

| Input (US vs GB) | `en` output | `en-GB` output |
|---|---|---|
| `"He said 'hi' then left"` | `“He said ‘hi’ then left”` | `‘He said “hi” then left’` |

**Punctuation placement** — only the closing punctuation differs
(`[CMOS ch.6]` typesetters' style / `[NHR ch.9]` logical style):

| Input | `en` output | `en-GB` output |
|---|---|---|
| `the word "cat".` | `the word “cat.”` | `the word ‘cat’.` |
| `she said "go",` | `she said “go,”` | `she said ‘go’,` |

The `en-GB` relocation is a code hook (§2.6) and is applied **only** when it is
unambiguous that the punctuation is not part of the quoted material; otherwise
the text is left as authored.

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
