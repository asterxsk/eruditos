---
name: "study-guide"
description: "Build default, Q&A, or code-explanation PDF study guides at full or quick depth in one of eight preset themes from any subject's source material — slides, textbook chapters, lab manuals, codebases, notes. One YAML content file in, one PDF out."
---

# Study Guide

Turn source material — slide decks, lab manuals, textbook chapters, past papers, messy notes, source code — into a print-ready PDF study guide in the selected preset theme. Choose the requested guide type — **default**, **Q&A**, or **code** — at the requested depth, full or quick. Use one accent colour, hairline structure, and verified spacing.

The output is a **standalone reference**: it never cites where the material came from.

**Your input is one YAML content file plus three choices** — theme, guide type, depth.
`build.py` turns that into the PDF in about two seconds: theme assets, block
rendering, maths, contents page, render and delivery checks. Do not write Python per
guide; the tool already exists. Its schema is `CONTENT-FORMAT.md` and a working
sample is `python build.py --example guide.yaml`.

---

## Step 0 — Ask before building

Do not start with a layout guess and a 40-page render. Ask **as plain sentences in the
conversation**, not as a question card:

- How much of the source should it cover - everything, the core topics, or an explicit list?
- Which guide type: default (information and worked examples), Q&A (an exam
  question bank), or code (a codebase explained function by function)?
- Full depth or quick? **Quick** covers exactly the same material but states it as
  pointers, keywords and code snippets instead of explained prose. Default to full.
- Only for Q&A: how many question wordings should each item carry? **Recommend three** -
  it is enough to show the question can be asked several ways without padding the
  guide out. Take any number the user gives.
- Only when implementation code is requested: keep the source's code language, or rewrite it into one language?
- Dark pages (screen), light pages with dark code cards (prints cheap), or both files?

Only skip a question the request already pins down; state the default you took and move on.

### Guide types

Guide type controls the content; theme controls its appearance; depth controls how
much that content is explained. Apply the chosen type and depth before drafting. If
the user already specifies either, do not ask again. If they request separate guides
of different types, the existing mandatory subagent rule applies.

**1. Default** — the general guide: information, formulae, diagrams and worked
examples. Organise definitions, concept explanations, conditions, units, formulae,
reference tables and solved problems by topic. Explanations may include code and
algorithms when the source does. This is the type to pick when the request does not
name one.

**2. Q&A** — an exam question bank. Each numbered item contains **two or more ways of
asking the same question**, followed by **one shared model answer**. The default and
recommended count is **three**; ask in Step 0 and use whatever the user asks for.
The wordings must test the same knowledge, have equivalent scope and depth,
and be fully answered by that one answer. They are not different questions,
subparts, or separately answered prompts. Keep meaningful wording variation.

Use this vertical layout for every Q&A item:

```text
1 [star only if exam-likely]

Q. First wording of the question.

Q. Second wording of the same question.

Q. Third wording of the same question.

Ans. One model answer covering all the wordings.
```

`1` is the **question number**, incremented once per item, not a heading or a count
of question variants. Keep each Q line separate, followed by the single Ans
block. Write the answer in proper English: complete, grammatically correct sentences,
with the expected technical terminology. Use coherent paragraphs or numbered steps
when appropriate to the answer. Highlight the marking keywords with bold accent
text (`<strong class="keyword">`), not the whole answer. In **quick** mode the answer
is a keyword chain plus a short pointer list, covering every mark the full answer
would earn. Match the user's marks and
exam format; do not assume a mark allocation that was not supplied.

**Q&A for a code lab.** When the source is a lab manual of programs rather than an
exam paper, the question is a one-line statement of the task and the answer is the
program plus its console output — not a prose answer. Keep the number, the single
question sentence, then the code card and the output card beneath it. Do not print
`Q.` or `Ans.` labels, and do not restate the question inside the code card. One
task is one page item; do not split a task across two numbered items.

Place **★** beside the item number for questions judged likely in the exam. Base
stars on supplied past-paper recurrence, stated exam priorities or emphasis in the
source, and keep that evidence in the internal coverage record. If likelihood is
inferred without past-paper evidence, label the star legend as an **estimated
revision priority**, not a confirmed prediction. Do not star everything by default.
Include source diagram screenshots needed by the question or answer; the diagram
requirement applies here too.

**3. Code** — a codebase explained. One `fn` item per function: its name, its
signature, what it does in one or two sentences, every parameter with its type and
meaning, what it returns, and the traps worth knowing. Then the body listing, then
the complexity line. Organise by module or file, in source order, so the guide reads
like the program.

`fn` is the type's unit of content, and it is not optional — a code guide with no
`fn` items is a listing dump and the tool warns about it. Cover every function in
scope, including the small ones; a guide that skips the helpers is the one that
leaves a gap on the exam. Algorithms the source states as numbered steps belong in
`algo`, and a file whose functions are all one-liners can be a single `code` item
with a short paragraph each.

The code itself still has to compile and run. Explanations are what this type adds,
never a substitute for a working listing.

The algorithm, code and complexity conventions later in this skill apply only to
blocks appropriate to the chosen type and requested scope. They do not require
adding code, algorithms, or complexity to a default guide or a theory Q&A guide.

### Depth: full or quick

Depth controls how much the guide **explains**. It never changes the guide type,
the theme, or what is covered. Full is the default; if the user does not say, take
full and state it.

Quick covers **exactly the same source material, to the same accuracy**. It just
drops the explanation and assumes the reader knows what to do with a pointer.
Write it the way the reader's own notes would look the night before an exam.

| | Full | Quick |
|---|---|---|
| Theory | definitions in prose, one idea per paragraph | pointers and keywords — the term, then the phrase, value or formula that defines it |
| Walkthrough | every meaningful step, with why the method applies | given → formula → substitution → result, one line naming the method |
| QA answer | full model answer in prose | keyword chain plus a short pointer list; every mark still covered |
| Code | complete program, compiled and run | the snippet that answers the question; a complete program still compiles and runs |
| Function | signature, description, parameters, returns, body, notes | signature, one-line description, parameters, returns — no body, no notes |
| Diagrams | screenshot, cropped and captioned | same — a diagram is source content, not explanation |

**What does not relax in quick mode:**

- Coverage and correctness. Nothing in scope is dropped, and nothing becomes
  approximate because it is terse. A pointer that is off by one term is still wrong.
- Source algorithms, reproduced verbatim as numbered cards. They are already terse;
  there is nothing to compress.
- Complexity lines on every algorithm and code card — a complexity is a pointer.
- Diagram screenshots, captions and legibility.
- Every label, accent, hairline, spacing and verification rule in this skill.

**What does relax:**

- Narration. No section commentary, no "common mistake" essay, no rationale for a
  method beyond one line. A section blurb stays one line.
- `note` / `tip` become a single pointer sentence, and only when they carry a real
  warning or a trap that costs marks. Do not convert prose into bullets just to
  fill them.
- A worked example states the method instead of arguing for it.

Quick does not smuggle in content the type forbids: a quick Q&A guide still has no
code listings. Depth subtracts; it never adds.

Quick is **shorter, not sparser** — the same rules fill a page to about 72%. Pointer
lists and code snippets flow and split freely, so there is no reason for a quick
guide to trail half-empty pages; if it does, the sections are too short, and the
pointer list should carry the whole topic rather than one line per section.

Emit pointers as `pts` items so they render as a hanging-indent list with a short
accent dash, not as prose paragraphs. Keywords inside a pointer or a QA answer go in
`strong.keyword`, exactly as in full depth — bold the marking term, never the whole
line.

### Choose one of eight preset themes in chat

Use exactly these bundled presets: **dark, graphite, cobalt, obsidian, paper, sepia,
ice, mono**. Dark, graphite and obsidian have dark pages; cobalt, paper, sepia,
ice and mono have light pages with dark code cards.

The web page is a **read-only theme gallery**, solely to show what the eight themes
look like. It is not a guide preview, editor, or selection form. Run
`python picker/server.py` as a hidden background process and share its printed
localhost URL when the user needs to compare themes. The user tells the agent the
preset name or number **in chat**. Never wait for a browser click, a saved config,
or server exit. Do not build or publish a web preview of the study guide.

If the request already names a preset, use it immediately without launching the
gallery or asking again. Otherwise show the gallery and ask which preset they want
in chat; wait for their answer before styling or rendering. Source harvesting may
continue while they choose. If the gallery is unavailable, list the same eight
names in chat and ask there; do not silently choose a saved design or default.

Pass the chosen preset as `--theme <preset>` and it is authoritative: `build.py`
reads the bundled preset directly, so a legacy `picker/design.json` or any per-guide
override cannot replace its palette, layout, fonts or texture.
Stop the gallery process after selection or when the task ends.
`picker/design.schema.json` remains the underlying renderer config contract.

### Several guides in one request

**Always use subagents when more than one study guide is to be made.** Count output
guides, not source files: several files combined into one guide do not require a
split, but two separate PDFs do, including two requested theme variants.

1. Identify each requested guide and its scope; use an explicit user split directly.
   Resolve depth once per guide too — the same batch can mix full and quick guides.
2. Resolve the theme once in chat for the batch, unless different themes were requested.
   Nothing needs baking ahead of time now: each `build.py` run writes its own assets.
3. Delegate each guide to a subagent, giving it its own content file and output PDF
   path, and stating that guide's theme, type and depth in the brief. Tell workers
   they share the workspace and must not overwrite another guide's content file or
   PDF. Workers must not launch the gallery or ask for another theme choice.

Run workers in waves within the environment's available concurrency slots. Retry a
failed guide once, then report any remaining failure. Review every child's coverage,
diagram inclusion and rendered PDF QA before delivering the batch. If subagent tools
are unavailable, report the limitation and ask how to proceed; do not silently build
multiple guides serially yourself.

---

## Step 1 — Harvest the source

Sources arrive as `.docx`, `.pptx`, `.ppt`, `.pdf`, images or pasted text.

```bash
python -c "import docx, pptx; print('ok')"   # python-docx + python-pptx; install if absent
```

Legacy `.ppt` must be converted first — `soffice --headless --convert-to pptx --outdir /tmp/conv *.ppt`, then read normally. `.pptx` files never convert reliably the other way.

Walk **every** element, not just paragraphs. Tables and slide text boxes carry most of the content in lab manuals:

```python
def docx_text(p):
    d = Document(p); out = []
    for para in d.paragraphs:
        if para.text.strip(): out.append(para.text.strip())
    for tb in d.tables:
        for row in tb.rows:
            cells = [c.text.strip().replace("\n", " | ") for c in row.cells]
            if "".join(cells).strip(): out.append("TABLE: " + " || ".join(cells))
    return "\n".join(out)

def pptx_text(p):
    pr = Presentation(p); out = []
    for i, s in enumerate(pr.slides, 1):
        out.append(f"=== SLIDE {i} ===")
        for sh in s.shapes:
            if sh.has_text_frame and sh.text_frame.text.strip():
                out.append(sh.text_frame.text.strip())
            if sh.has_table:
                for row in sh.table.rows:
                    out.append("TBL: " + " || ".join(c.text.strip() for c in row.cells))
    return "\n".join(out)
```

### Diagram screenshots are mandatory

**Always include source diagram screenshots: they carry marks.** Inspect every
in-scope source page or slide visually, including image-only material. Render the
source pages/slides or extract their embedded images, then crop each diagram with
all labels, axes, arrows, legends and annotations intact. Include source graphs,
curves, flowcharts, trees, circuits and other examinable figures beside their topic.
Keep their original colours and readable background, even on a dark theme.

Record a coverage inventory mapping source page/slide and diagram to its image file
and final guide section. Check that every in-scope diagram appears and its smallest
labels remain readable in the rendered PDF. Never omit a diagram because text
extraction missed it, because it is inconvenient to crop, or to save pages. If no
in-scope diagrams exist, record that fact; do not invent one. If an image cannot be
recovered, report the missing figure rather than claiming coverage is complete.

Read the dumps before writing anything. The algorithms usually exist **verbatim** in the source and must be reproduced in their own voice, not paraphrased — a student reproducing them under exam pressure needs the words their marker expects.

---

## Step 2 — Write the content file

**One YAML file. Do not write Python.** The build is a tool now:

```bash
python build.py guide.yaml --theme <preset> --type <default|qna|code> --depth <full|quick>
```

It owns the theme assets, every block renderer, the maths, the contents page, the
PDF and the delivery checks. A guide takes seconds, not a scripting session. The
full schema is in `CONTENT-FORMAT.md` beside it; `python build.py --example guide.yaml` writes
a working file to edit.

Content goes in one section per subject area — a short tag, a title, a one-line
blurb, then items:

```yaml
sections:
  - tag: ARRAYS
    title: Array Operations
    blurb: Traversal, insertion and deletion on a fixed-size array.
    items:
      - pts:
          - "**Traversal** — visit every element once, O(n)"
      - algo:
          pin: Traversal
          title: TRAVERSING AN ARRAY
          steps: ["[INITIALIZE] SET I = lower_bound", "..."]
          cx: O(n) time · O(1) extra space
      - code: {file: array_operations.c, lang: c, cx: O(n) overall}
      - work: {title: Worked example, steps: ["..."]}
      - math: {tex: "T(n) = \sum_{i=1}^{n} c_i", num: 1}
      - table: {head: [Quantity, Value], rows: [[Time, "O(n)"]], caption: "..."}
      - note: {title: Common mistake, text: "..."}
      - qa:
          num: 1
          q: [First wording, Second wording, Third wording]
          a: One model answer.
          kw: [marking term]
```

Block keys: `p`, `h2`, `h3`, `pts`, `math`, `algo`, `code`, `work`, `fig`, `table`,
`note`, `tip`, `qa`, `fn`. Prose strings accept `**keyword**`, `` `code` ``, `*emphasis*`
and `$inline math$`.

Only choose blocks the guide type allows — the tool rejects the rest before
rendering, so a mistake costs a second, not a render:

| Type | Blocks allowed |
|---|---|
| `default` | `p pts h2 h3 math fig table note tip algo work code fn` |
| `qna` | `p pts h2 h3 math fig table note tip qa` |
| `code` | `p pts h2 h3 math fig table note tip algo code fn` |

The older names still parse — `textbook` and `walkthrough` both resolve to
`default`, `qa` to `qna` — so an existing content file keeps building.

`pts` is the quick-mode pointer list: one pointer per line, each opening with the
term being pointed at. It renders as a hanging-indent list with a short accent dash,
so a scan down the page hits every term. Use it for quick theory; keep prose `p` for
the connective sentence that introduces a list. Short symbols still go in `$…$`.

For a QA guide, use one `qa` item per shared answer, not three items. `q` holds the
equivalent wordings — **three unless the user asked for another count in Step 0** —
and every one must be answerable by the one `a`. For a code lab, `q` is a single task
sentence and the answer is `file` (plus optional `out`); for an algorithm answer,
give `algo` instead of `a`. `kw` highlights the marking terms. `star: true` marks a
likely question. Store likelihood evidence internally, never as citations in the
guide.

`num` is optional — the tool numbers items in document order across sections, which
is the right default. Supply it only to force a number.

`math` is a display equation rendered to SVG and centred, `num` optional for a
right-aligned `(1)`. It is never inlined into a paragraph; inline `$…$` is for a
short symbol.

**Write the prose like a person, not a brochure.** Concrete numbers, specific values from the source, an actual opinion about which approach to use. Cut every sentence that could be deleted with no loss — significance inflation ("plays a crucial role"), negative parallelism ("not just X, but Y") and trailing `, highlighting…` clauses are the fastest way to make a study guide read as filler. In quick mode this applies to the pointers too: a pointer is a fact, not a mini-essay, and "important because…" is the first thing to cut.

---

## Step 3 — Build and verify

The one command does both. Assets, maths, render and checks:

```bash
python build.py guide.yaml --theme cobalt --type qa --depth quick
```

Every build runs the delivery checks unless `--no-check`:

- **Sparse pages** — anything under 72% full except the cover, contents and last
  page. One gap is structural: a code card cannot split, so a listing pushed to the
  next page leaves its own page short. That is reported, not failed.
- **Margin seams** — a step between the margin and the content box, which is exactly
  what the `@page` background bug looks like. Verified against a deliberately broken
  stylesheet, so a pass means something.
- **Leaks** — escaped entities, `None`, `Traceback`, raw LaTeX, and unrendered `$…$`.
- **Fonts** — warns if no bundled face reached page 1.

Read the output. Fix the content file and run it again; never hand-edit the built
`doc.html` or `theme.css`.

### When the tool is not the right tool

`build.py` covers whole guides. Reach for the lower-level pieces only when changing
how the skill itself looks or behaves, not when making a guide:

- `picker/theme.py` — the theme assets on their own.
- `picker/base.css` — the stylesheet. This is where the design lives.
- `picker/server.py` — the read-only theme gallery offered in Step 0.

The WeasyPrint constraints `base.css` respects, and the reasons for them, stay in
force for anyone editing it: no `color-mix()`, no `mask-image`, no `filter`, no
comma inside a `var()` fallback, and the `@page` background shim described below.

## Visual design system

### Palette

The palette is **per design**, not fixed — `theme.py` emits it as `:root` tokens and
`base.css` consumes every one with a dark fallback. The dark preset's values, and the
role each token plays:

```css
--base:        #090a0c;   /* page background, flat beneath the gradient */
--grad-from/via/to        /* the gradient stops; derived layers for mesh/vignette */
--strong:      #f2f5f9;   /* headings and emphasis */
--text:        #c8cfd8;   /* body */
--dim:         #8f98a6;   /* captions, table headers */
--faint:       #5d6672;   /* footnotes, page numbers — must clear 4.5:1 on the base */
--rule / --rule-strong    /* hairlines; card borders and header rules */
--wash:                   /* table-header and card-header wash */
--accent:      #79c0ff;   /* ONE accent. the only saturated colour */
--accent-soft:            /* the accent at ~32%, for the algo card's left edge */
--dim-soft:               /* the worked-example left rule */
--warn / --ok: #e0a856 / #78be96;   /* callout labels only, never general text */
--block-fill:             /* algorithm and callout card fills */
--code-fill/text/keyword/comment/selection
```

The light presets (`cobalt`, `paper`, `sepia`, `ice`, `mono`) invert the same roles
and give the code card a *dark* fill — the code card is the one container that grounds
against the page tone.

### The rules that make it look designed rather than templated

Each of these was learned by shipping the wrong version first.

**Before any of these: labels are serif italic, sentence case, untracked.** Never `text-transform: uppercase`, never `letter-spacing`, never the mono face — on the unit tag, the callout head, the worked-example head, the table header, the figure caption, the contents sub-tag or the footer. `WORKED EXAMPLE` in tracked mono is the strongest generated-document tell there is, and it destroys acronyms (`HRTF` becomes `Hrtf`). Casing lives in the generator's source string, so `Worked example` and `HRTFs after 3D Tune-In` come out correctly. They share one rule block in `base.css`, driven by `--font-label`; do not restyle one label without the others.

0. **Dividers belong to units, not items.** One `1px` rule opens each unit (`.unit-head`'s top border) and nothing else on the page has one. A hairline under every Q&A row turns a 70-item guide into 70 stripes and reads as a form. If a reviewer asks why two items blur together, add vertical space (about 5mm between items), not a rule. The same applies to the `table.data` body and the code cards: no extra frames.
1. **Cards are the exception.** The default container is no container: an italic serif label, a left hairline rule and space. A bordered box is a machine-like unit you are fencing off — real code, a numbered algorithm — not the wrapper for every item on the page. If a page carries more than two or three real cards, it has too many. A pile of bordered boxes is the fastest way to make the guide look templated; open blocks separated by rules read as a designed document. When in doubt, drop the fill and the border, keep the label and the space.
2. **One accent hue, used sparingly.** Two or more saturated hues spread across section headers, table headers and blocks reads as a template. The accent belongs on: the card label, the complexity line, the contents page numbers, the algorithm card's left edge at 55% opacity.
3. **Structure comes from hairlines, not fills.** Rules, indentation and whitespace do the work. Filled colour blocks and boxes around every item make a document look like a slide deck.
4. **The page background is one flat colour.** The `@page` gradient is a light wash at best: keep any delta between its lightest and darkest stop within about 8 RGB values, and prefer `base` for all three stops when a reviewer says the pages look different from each other. A gradient tall enough to be seen turns every screenful into a different sheet of paper and makes facing pages mismatched — the one thing print readers notice first. Texture (grain) carries the paper feel instead; the gradient never does.
5. **No CSS text effects.** `background-clip: text` renders as a solid gradient bar behind the glyphs in PDF. If a heading needs weight, use a bigger font weight.
6. **Small radii.** `4px` on the two surviving cards; no radius anywhere else — labels are type, not chips. Large radii plus gradients is the templated look.
7. **Dark code cards sit on dark pages.** Give them a slightly *different* dark (`#0a0d12`) and the muted syntax palette below; do not lift them with light backgrounds.

### Two real cards, everything else opens

| Container | What it is | Chrome |
|---|---|---|
| **Code card** (`.code`) | a file listing. The fake window chrome is meaningful here — it says "this is a program". | kept: window dots + filename bar, `#0a0d12` body, `1px` border |
| **Algorithm card** (`.card`) | a numbered step procedure. Fenced off because it is machine-like and self-contained. | kept: italic accent label + title header, mono body, `2px` accent left edge |
| Worked example (`.work`) | a hand-worked derivation | **open** — `2px` dim left rule, label, indented mono steps |
| Note / tip (`.note` / `.tip`) | a called-out warning or hint | **open** — left rule in amber/green, italic serif label, no fill, no border |
| Definition / prose (`p`) | narration and definitions | **open** — no chrome at all, just spacing |
| Pointer list (`ul.pts`) | quick-mode theory pointers | **open** — hanging indent + accent hairline marker, no bullets |
| Q&A (`.qa`) | question + answer | **open** — no rule at all; space only |
| Table (`.data`) | tabular data | **open** — hairlines only; the header wash stays, the box does not |

The open variants all share one shape: a **left hairline rule or margin indent**, an **italic serif label in sentence case**, and **space**. No fill, no border, no radius — that is what stops the page reading as a grid of boxes.

### Typography

| Role | Family | Size / weight |
|---|---|---|
| Headings, block titles | Poppins | 600, −0.7px tracking on the cover only |
| Body | Guide Sans | 10.2pt / 1.55 line-height |
| Code, algorithms, table figures | DejaVu Sans Mono | 7.5pt code, 8.1pt algorithms |
| Every label (unit tag, callout head, worked-example head, table header, caption, footer) | Guide Serif italic | 9.6pt, sentence case, no tracking |
| Maths | Computer Modern look (MathJax default), STIX/DejaVu Serif fallback | sized to body; never the mono font |

Install once if missing: `fonts-poppins`, `fonts-lato` (Debian ships both as `fonts-google-fonts` / `fonts-lato`); otherwise fall back to any humanist sans plus DejaVu Sans Mono, which is present everywhere and is the most legible monospace at 7.5pt.

Table headers are **serif italic at 9.6pt in sentence case** on a 3.5% wash. No tracking, no capitals. `WORKED EXAMPLE` becomes `Worked example`; acronyms stay as written (`HRTF`, `ITD`, `FFT`), because casing now lives in the source text rather than in `text-transform`.

**Maths rule.** Equations are set in a serif math font — MathJax's default Computer Modern, or STIX/DejaVu Serif as the fallback — at body size. Never in the mono font used for algorithms and code: mono numerals and operators read as a terminal, not as mathematics. Colour is the body text colour (`#c8cfd8`); the equation number is in the faint tone (`#5d6672`).

### Components

| Component | Recipe |
|---|---|
| Section header | 23pt title, small italic serif tag above, one-line dim blurb, `1px` rule above the whole block |
| Algorithm card | header bar = italic accent label + title, body = mono 8.1pt, `pre-wrap`, `2px` accent left edge |
| Code card | fake window chrome (three 1.9mm dots at 16% white) + filename, `#0a0d12` body, muted syntax |
| Worked example | `2px` dim left rule, italic serif label, indented mono steps, amber/green/red spans for highlight/result/error |
| Callout (`note` / `tip`) | `2px` amber or green left rule, italic serif label, body indented — no fill, no border |
| Display equation (`.eq`) | centred SVG, `margin: 7mm 0`, optional `(N)` floated right in mono faint, `page-break-inside: avoid` |
| Complexity line | mono 7.4pt in the accent, `1px` hairline above, at the bottom of the algo/code card |
| Q&A | no card — 4mm padding, question in Poppins 9.6pt light, answer dim; no rule between items, only the unit's opening rule separates subjects |
| Pointer list (`ul.pts`) | open, no bullets: hanging indent 5mm, a 2.6mm accent hairline as the marker, 2.2mm between pointers, keywords in bold accent |
| Contents | rows separated by hairlines, number in dim mono, page number floated right in the accent, sub-tag in italic serif |
| Cover | no rule, 46mm top space, italic tag, 34pt title at −0.7px, 11pt dim subtitle, and a dark terminal card of `$ command  # note` lines |
| Figure | centred `<img>` at up to 100% width and 94mm tall, italic serif caption under it, kept with the image across pages |
| Inline maths | `span.imath` wrapping the SVG at 1.15em so it sits on the baseline at body size, in a card as well as a paragraph |

---

## Spacing and layout

### Page geometry

```css
@page {
  size: A4;
  margin: 19mm 15mm 22mm 15mm;   /* top right bottom left */
}
```

- **19mm top / 22mm bottom** keeps content clear of both the sheet edge and the footer. Footers need `padding-bottom: 5mm` so the page number does not crowd the trim.
- Footers: page number on the right in mono, and nothing else unless asked.
- **15mm sides** gives about 180mm of text width. At 7.5pt DejaVu Sans Mono a character is ~1.59mm, so plan for **≤ 105 characters per code line**. `build.py` enforces this: a code block with a longer line is an error naming the file and the length, so wrap it by hand before it reaches the PDF.

### The `@page` background gotcha

This is the single most likely thing to go wrong, and it has two halves that must be
fixed together.

A `background-image` on `@page` is anchored at the **content box**, not the page box, so
the margins render in the flat `background-color` and a hard band appears at the sheet
edges. **`background-origin` and `background-clip` do not fix this** — WeasyPrint 70.0
ignores both silently (no warning), verified by pixel sampling: the boundary sits at
`stop + margin` for every margin. The working shim is a negative `background-position`.

The second half: the shim only lines up if the `@page` declares the margins it is
compensating for. An `@page` with a background but **no `margin`** gets WeasyPrint's own
default (measured at ~19.8 mm here), the shift falls short by the difference, and a strip
along the edge is left with no grain. Emit `size` and `margin` in the same rule as the
background, and derive the shift from those same numbers.

`theme.py` does this from one `PAGE` constant (`picker/theme.py`), which is the single
source of truth for the geometry — read it for the emitted shape. The invariants:

- **Every layer is sized to the whole sheet** in absolute units (`210mm 297mm`), never
  `cover`, which would scale the gradient to the text column.
- **`background-position` shifts out by the margins**: `-15mm -19mm` for the default
  geometry. Negative values are honoured; `origin`/`clip` are not.
- **One entry per layer**, lists kept aligned. With a density patch, swap the first layer
  for `grain-patch.png` sized to the sheet; otherwise it is the `220px 220px` tile with
  `repeat`.

`build.py` verifies this on every build: it compares a strip just outside each margin
with a strip just inside the content box, in rows and columns that hold no content, and
fails on a step between them. A page-wide reference cannot be used — the background is
a gradient, so it genuinely differs top from bottom, and a large card can own the page's
modal colour.

### Break control — the difference between flowing and gappy

Forcing `page-break-before: always` on every section is what produces a trail of half-empty pages, one per section. Let content flow and separate sections with space instead:

```css
.unit        { margin-top: 15mm; }                 /* sections flow */
.unit-head   { border-top: 1px solid rgba(255,255,255,0.09);
               padding-top: 9mm; page-break-inside: avoid; page-break-after: avoid; }
.contents    { page-break-before: always;          /* contents gets its own page */
               page-break-after: always; }          /* ...and stops before the first unit */
```

`.contents` needs **both** breaks. With only the trailing one the cover and the contents
share page 1 and the last rows spill onto a near-empty page of their own. This is the one
place a forced break is right; everywhere else, space separates sections.

Then keep only what genuinely must stay whole:

```css
.qa, .contents-item              { page-break-inside: avoid; }  /* never split a question from its answer */
.card-b .step, .work-b span.cont { page-break-inside: avoid; }  /* never split a line */
.eq                              { page-break-inside: avoid; }  /* never split an equation across a page */
table.data tr                    { page-break-inside: avoid; }
.code-h, .card-h, .work-h,
h2.sec, h3.sub                   { page-break-after: avoid; }    /* never orphan a header */
p, li                            { orphans: 2; widows: 2; }
```

**Do not** put `page-break-inside: avoid` on the big content cards themselves. A card that cannot split gets pushed to the next page whole and leaves a gap behind it — that is exactly how a page ends up holding a single four-line code snippet. (Open blocks do not have this problem: they split anywhere, which is one more reason to prefer them.)

### Vertical rhythm

| Gap | Value |
|---|---|
| Between blocks / cards | 4.4–4.6mm |
| Card padding | 3.6–4.6mm |
| Open-block padding (`.work`, `.note`, `.tip`) | 0 0 0 5mm — left rule only, no box |
| Before an `h2` | 9mm, plus a `1px` rule under it |
| Before an `h3` | 6mm |
| Above and below a display equation | 7mm |
| Inside a card, above the complexity line | 3.4mm |
| Before a section | 15mm |

Spacious but not wasteful: every element gets its own space, and no page carries less than about 72% of its height in content.

---

## Content conventions

### Algorithms

Bookend every step-by-step algorithm:

```
Step 1: Start
Step 2: [INITIALIZE] SET I = lower_bound
…
Step N: Stop
```

**`build.py` does the numbering.** Put the source steps in the `algo` block exactly
as they appear — no `Step 1: Start` line — and the tool adds the bookends, numbers
the steps and shifts every internal reference by the same offset. It leaves a
listing alone when it sees braces or semicolons, so a function body is never
bookended.

What you still get right in the content:

- **Keep the source's wording.** Do not rewrite `[INITIALIZE]` into plain English —
  reproduce it. The tool never paraphrases.
- **Keep the source's step order.** The tool shifts references by a uniform offset;
  it cannot recover an order you changed.

### Code

- Real, compiling code. Write the files, **compile and run them** with sample input before they go in the document. A study guide with a syntax error is worse than no study guide.
- No comments. Short names. Declarations at the top. A `while (1)` + `switch` menu for anything with a set of operations. Match the house style of the student's own submitted work.
- Descriptive filenames in the card header (`array_operations.c`, `linked_list.c`), never source-derived ones (`expt3_…`, `ch4_…`).
- No description paragraph above the code. Filename and code.
- In **quick** mode, emit the snippet that carries the answer rather than a whole
  program — but it still has to be real code lifted from something that compiles
  and runs, not hand-written pseudo-code. If the requested task is "write a program",
  quick mode still writes the program; quick trims explanation, never completeness
  where completeness is what is being marked.

### Complexity

Every algorithm card and every code card carries one line at the bottom, in the accent:

```
Time complexity · O(n) worst case · Ω(1) best case · O(1) extra space
Time complexity · Factorial O(n) · Fibonacci O(2ⁿ) · GCD O(log n)
```

Write all three bounds when they differ; the best/average/worst distinction is what gets marked.

### Source neutrality

The guide never mentions where content came from. Strip, in this order:

- Section tags (`EXPERIMENT 1 · ARRAYS` → `ARRAYS`)
- Cross-references (`Unit 7` → `the linked-list section`)
- Algorithm numbers sold as chapter numbers (`Algorithm 1.3` → the descriptive pin)
- Captions like "from the slide deck", "from the workbook"
- Titles like `expt5_expr.c (reference)`
- Any author name, roll number or course code on the cover or closing page

The cover carries a title, a one-line subtitle, and a terminal-style block. Nothing else.

---

## Reference CSS

The stylesheet is **not** reproduced here — it ships in the skill as `picker/base.css`,
the single source of truth for every component `build.py` renders. Read it before
changing how a guide looks; its class names are the contract between the renderer and
the page.

`theme.py` concatenates it into the guide's `theme.css` **ahead of** the generated
`:root` tokens and `@page` rule, so the built page links exactly one file.
Edit `base.css` to change how the guide looks; never edit a built `theme.css` by hand,
since the next `theme.py` run overwrites it.

The one thing that is *not* in `base.css` is `@page`, because it is per-design: the
background colour, the gradient and the grain layer are all resolved from the config
and written by `theme.py`. The `@page` background gotcha (above) applies to it.

---

## Checklist before delivering

- [ ] Selected depth respected: quick covers every in-scope topic and loses no marks-bearing fact, but carries pointers/snippets instead of explained prose; full is unchanged
- [ ] Selected guide type respected: default carries information and explained worked examples; Q&A has the number of equivalent wordings the user chose (default three) and one shared answer per numbered item; code explains every in-scope function with its parameters and return value
- [ ] Dividers checked: the unit head's rule is the only horizontal rule opening a block; no hairline sits between consecutive Q&A items
- [ ] QA answers are in proper English, marking keywords highlighted, marks respected, and likely-question stars have an accurate legend and internal evidence
- [ ] Every in-scope source diagram is included as a screenshot, with all labels readable and coverage inventory checked
- [ ] Theme chosen in chat from the eight presets; no guide web preview or browser save gate
- [ ] Subagents used whenever more than one guide was requested; every child PDF reviewed
- [ ] Every program compiles and ran with sample input
- [ ] Every algorithm starts `Step 1: Start` and ends `Step N: Stop`, references shifted to match
- [ ] Every algorithm card and code card has a complexity line
- [ ] No source citations, no experiment or chapter numbers, no descriptive paragraphs above code
- [ ] `python build.py` ran clean: no sparse-page warning, no margin seam, no leak, no font fallback — the tool checks all four on every build
- [ ] No author name, roll number or course code anywhere
- [ ] One accent colour, hairline structure, grain visible but not obvious
- [ ] Cards are the exception — more than two or three real cards on a page means boxes have crept back in where an open block belonged
- [ ] No label is uppercase or tracked — `grep -nE 'text-transform:\s*uppercase' theme.css` and `grep -nE 'letter-spacing:\s*[0-9.]*[1-9]' theme.css` both empty, and `grep -nE '>[A-Z][A-Z /&·-]{3,}<' ` over the built HTML finds no shouted label. Every label reads `Worked example`, not `WORKED EXAMPLE`, and acronyms survived (`HRTF`, `ITD`, `FFT`, `8D` — not `Hrtf`)
- [ ] Descriptive filename for the PDF itself
