# Content format

One YAML or JSON file is the input to `build.py`. Theme controls appearance; mode
controls what the agent writes. Every theme opens with contents, followed by topics.

```bash
python build.py --example guide.yaml
python build.py guide.yaml --theme paperx --mode full
```

CLI settings override the file. Renderer fallbacks are `theme: paper` and
`mode: full`; these are not permission to skip the skill's opening questions.
Collect missing theme/mode choices with the harness's built-in question tool,
recommend Full for an in-depth guide, then use the supplied source or request it
if absent. Quick is for skimming and last-minute revision.
The themes are `paper`, `paperx`, `obsidian`, and `pdfcn`; the only modes are `full`,
`quick`. Output is `<content-stem>.pdf` unless `-o` supplies a path.

Full contains concise textbook-style topic answers covering the requested
essentials. Quick is a deliberately selective crux for revision, not the same
coverage compressed. Selection is an authoring decision; the renderer does not
decide which source topics are important or make completeness claims.

## A practical guide file

```yaml
meta:
  title: Demand and Supply
theme: paperx
mode: full
sections:
  - title: Demand
    items:
      - h2: Movement along versus shift of demand
      - theory:
          paragraphs:
            - "A change in the commodity's **own price** moves quantity demanded along the same demand curve, with other determinants held constant."
          points:
            - "A fall in price produces an extension; a rise produces a contraction."
            - "A change in another determinant shifts the entire curve."
      - table:
          head: [Change, Cause, Result]
          rows:
            - [Quantity demanded, Own price, Movement along the same curve]
            - [Demand, Another determinant, Shift of the curve]
      - note:
          title: Holding other factors constant
          text: "The movement comparison assumes income, tastes and related prices are unchanged."
```

`sections` is an ordered list of topic groups; each has a `title` and `items`.
Use `h2` and `h3` for content-specific headings within a group. Contents navigation
and page numbers are global. `meta.title` identifies the document; it does not
create a cover. Do not encode preliminary guides or checklists as extra sections.

## Content primitives

Each item is a single-key mapping; a bare string is shorthand for `p:`. The same
primitives are available in both modes and all themes.

| Key | Shape | Purpose |
|---|---|---|
| `p` | `"text"` | explanatory paragraph |
| `pts` | `["point", ...]` | concise pointers |
| `h2` | `"Topic title"` | topic heading |
| `h3` | `"Subtopic title"` | subordinate heading |
| `theory` | `{paragraphs: [...], points: [...]}` | related prose/points without a generic printed label |
| `math` | `{tex: '...', num: 1}` or `'...'` | display equation rendered as SVG |
| `fig` | `{file: img.svg, caption: "...", alt: "...", width: "100%"}` | SVG or raster figure |
| `table` | `{head: [...], rows: [[...]], caption: "..."}` | comparison or reference table |
| `note` | `{title: "Specific concept", text: "..."}` | content-specific caution or clarification |
| `tip` | `{title: "Specific concept", text: "..."}` | content-specific useful observation |
| `work` | `{title: "...", steps: [...]}` | worked example or derivation |
| `code` | `{file: a.c, lang: c}` or `{text: "...", lang: c}` | source listing or concise snippet |
| `algo` | `{title: "...", steps: [...]}` | meaningful ordered algorithm steps |

`theory.paragraphs` and `theory.points` are lists of strings, not nested blocks;
omit either when unused. Quick may use these or `pts` to carry selected key points.
Do not automatically add paragraphs, function listings or complexity fields to
fill a template. For `note`, `tip` and `work`, use a genuine content-specific title
when useful. Generic semantic headings are not printed in PaperX.

For `pdfcn`, use `h3` for a specific explanation or a worked example's setup,
`p` for short paragraphs, and `work` for the calculation itself. Existing
SVG and raster figures keep their artwork and can use the usual sizing fields.
The preset uses locally installed SF Pro Display or bundled Guide Sans. Set
`SF_PRO_DISPLAY_DIR` to the directory containing the local SF Pro Display OTF
files if the PDF builder needs an explicit path.

### Tables across pages

Use one `table` block per logical table, with one `head` and all its `rows`.
The renderer paginates long tables and repeats the header only on continuation
pages. Keep distinct tables in separate blocks even if their column labels match.

### Inline markup and equations

Prose strings, table cells and captions accept:

| Syntax | Result |
|---|---|
| `**term**` | meaningful emphasis |
| `` `code` `` | inline code |
| `*emphasis*` | italic |
| `$O(n \log n)$` | inline mathematics rendered as SVG |

Use a `math` block for display equations. Single-quote TeX in YAML so backslashes
are preserved rather than interpreted as YAML escape sequences:

```yaml
- math:
    tex: 'E_s = \frac{\Delta Q_s}{\Delta P}\frac{P}{Q_s}'
```

### Code and algorithms

Code appears when the source contains it or the concept needs it. The same block
can carry a complete program in full mode or a concise, accurate snippet in quick
mode; mode does not automatically strip code. `file` resolves from the content
file's directory, with its `code/` directory as a fallback. Missing files are errors.

```yaml
- code:
    text: |
      total = sum(values)
      mean = total / len(values)
    lang: python
- algo:
    title: Binary search
    steps:
      - Compare the target with the middle value of the sorted interval.
      - If equal, return its position.
      - Otherwise continue in the half that can contain the target.
      - If the interval becomes empty, report that the target is absent.
```

For numbered natural-language procedures in the body typeface, set `algo.format: prose`.
Omit this option to retain the existing compact algorithm card typography.

Keep code behaviour and algorithm order faithful to the source. Do not insert
automatic Start/Stop bookends, force a function inventory, or require complexity
lines on every listing. Include a complexity fact in topic prose when it helps.
Validate runnable examples in the available runtime and report verification limits.

### Figures

```yaml
- fig:
    file: assets/demand.svg
    caption: Movement along a demand curve versus a shift of the curve.
    alt: Two price–quantity panels contrasting own-price movement with a change in demand.
    width: 100%
```

`file` resolves from the content file's directory. The renderer copies assets with
collision-safe names, so different chapters can use different images with the
same basename. `alt` defaults to the caption. `width` is a percentage or millimetre
length such as `100%`, `75%`, or `140mm`. PaperX defaults to `100%`; Paper and
Obsidian retain natural sizing constrained to the text column when width is
omitted. Size figures for legibility, not just to fit them onto a page.

For a detailed portrait diagram, `fig.max_height: 180mm` overrides the default
94mm height cap without changing its aspect ratio. Use a positive millimetre
length up to 230mm; leave room for the caption. Split combined diagrams into
separate figures when that makes their source labels easier to read.

Paper and Obsidian keep in-scope source diagram screenshots and their original
backgrounds/colours. PaperX redraws instructional figures, preferably as static,
self-contained SVG with explicit dimensions and viewBox. Preserve source labels,
values, axes, units, shapes, relative layout and connections. Follow the source
geometry and timing-waveform verification rules in [references/paperx.md](references/paperx.md).
Figure-generation code is allowed; custom
per-guide PDF renderers and arbitrary chapter HTML are not the content interface.
Do not rely on remote assets or browser JavaScript. Label schematic figures where
appropriate and never invent empirical data. A photo or other intrinsically
visual evidence can keep its source image when redrawing would change its meaning;
record that exception internally.

## Chapter assembly

For multi-chapter PaperX, chapter workers write separate files with `sections: [...]`.
Their figure/code paths are relative to their own chapter file. The main agent
defines global settings and order in a manifest:

```yaml
# manifest.yaml
meta:
  title: Economics and Management
theme: paperx
mode: quick
chapters:
  - chapters/economics/chapter.yaml
  - chapters/management/chapter.yaml
```

```bash
python assemble.py manifest.yaml -o guide.yaml
python build.py guide.yaml --theme paperx --mode quick
```

Chapter paths resolve from the manifest. The assembler preserves their order and
writes one canonical YAML file with absolute figure/code references. Keep assets
available until rendering; assembled YAML is not an asset archive. The main agent
reviews chapter content and selection/coverage before assembly, then checks the
global contents, numbering, pagination and figures in the final PDF. Workers do
not produce final PDFs or contents tables.

## Migration

Old top-level `type` and `depth` settings and their `--type`/`--depth` flags are
rejected. Choose `mode: full` or `mode: quick` and rewrite content accordingly.
There are no hidden guide-type aliases. Removed `qa`, `qna`, `question`, `answer`,
`fn`, `function`, `explain`, and `exam` blocks must become topic prose, pointers,
figures, tables or code where needed. Do not preserve question/answer labels,
likely stars, exam frames or boilerplate instructions in replacement text.

## Verification

Build diagnostics check sparse pages, margin seams, leaked markup and bundled
fonts. Review warnings rather than bypassing them. Visually inspect the rendered
PDF for correct contents destinations, readable formulas/figures, missing assets,
clipped tables or code, orphaned headings and avoidable empty areas. Contents and
the final page can naturally be short. Neither mode nor a successful render
establishes source accuracy or coverage; those remain authoring checks.
