---
name: "study-guide"
description: "Build textbook, walkthrough, or QA PDF study guides at full or quick depth in one of eight preset themes from any subject's source material — slides, textbook chapters, lab manuals, notes."
---

# Study Guide

Turn source material — slide decks, lab manuals, textbook chapters, past papers, messy notes — into a print-ready PDF study guide in the selected preset theme. Choose the requested guide type: textbook, walkthrough, or QA — at the requested depth, full or quick. Use one accent colour, hairline structure, and verified spacing.

The output is a **standalone reference**: it never cites where the material came from.

---

## Step 0 — Ask before building

Do not start with a layout guess and a 40-page render. Ask **as plain sentences in the
conversation**, not as a question card:

- How much of the source should it cover - everything, the core topics, or an explicit list?
- Which guide type: textbook, walkthrough, or QA?
- Full depth or quick? **Quick** covers exactly the same material but states it as
  pointers, keywords and code snippets instead of explained prose. Default to full.
- Only for QA: how many question wordings should each item carry? **Recommend three** -
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

**1. Textbook** — information, formulae and diagrams only. Organise definitions,
concept explanations, conditions, units, formulae and reference tables by topic.
Include all in-scope source diagram screenshots. Do not add worked sums, solved
examples, question-and-answer banks or implementation code to this type.

**2. Walkthrough** — worked sums, equations, derivatives and derivations. For each
problem, show the given information, what must be found, the relevant formula or
method, substitutions, each meaningful algebra/calculus step, and the final result
with units or conditions where appropriate. Explain why the method or step applies;
do not jump from the problem to the answer. In **quick** mode the same chain is
written one line per step and the method is named rather than explained.
Respect calculator use for arithmetic.
Keep source notation and include the relevant source diagram screenshots. Restrict
theory to what is needed to understand and solve the requested problems.

**3. QA** — an exam question bank. Each numbered item contains **two or more ways of
asking the same question**, followed by **one shared model answer**. The default and
recommended count is **three**; ask in Step 0 and use whatever the user asks for.
The wordings must test the same knowledge, have equivalent scope and depth,
and be fully answered by that one answer. They are not different questions,
subparts, or separately answered prompts. Keep meaningful wording variation.

Use this vertical layout for every QA item:

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

**QA for a code lab.** When the source is a lab manual of programs rather than an
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
requirement applies to QA too.

The algorithm, code and complexity conventions later in this skill apply only to
blocks appropriate to the chosen type and requested scope. They do not require
adding code, algorithms, or complexity to a textbook, mathematical walkthrough,
or theory QA guide.

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
- A walkthrough states the method instead of arguing for it.

Quick does not smuggle in content the type forbids: a quick textbook still has no
worked examples and no code. Depth subtracts; it never adds.

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

Write `{"version": 1, "basedOn": "<chosen-preset>"}` to `design.json` in the build
directory. Run `python picker/theme.py <build-dir> --preset <chosen-preset>`.
The explicit preset is authoritative: legacy `picker/design.json` and arbitrary
per-guide overrides must not replace its palette, layout, fonts or texture.
Stop the gallery process after selection or when the task ends.
`picker/design.schema.json` remains the underlying renderer config contract.

### Several guides in one request

**Always use subagents when more than one study guide is to be made.** Count output
guides, not source files: several files combined into one guide do not require a
split, but two separate PDFs do, including two requested theme variants.

1. Identify each requested guide and its scope; use an explicit user split directly.
   Resolve depth once per guide too — the same batch can mix full and quick guides.
2. Resolve the theme once in chat for the batch, unless different themes were requested.
3. Bake shared assets once per selected preset with the command above. Depth changes
   no asset: both depths link the same `theme.css`.
4. Delegate each guide to a subagent, assigning exclusive ownership of its build
   directory and output PDF, and state that guide's depth in the brief. Tell workers
   they share the workspace, must preserve others' edits, and must use this skill,
   the selected preset and the already-baked stylesheet, fonts and grain. They must
   include source diagram screenshots. Workers must not launch the gallery or ask for
   another theme choice.

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

## Step 2 — Draft the content map

One section per subject area. Each section is a short tag, a title, a one-line blurb, then items:

```python
{"num": "01", "tag": "ARRAYS", "title": "Array Operations",
 "blurb": "One line saying what this section covers and who needs it.",
 "items": [
   {"t": "algo", "pin": "Traversal", "title": "TRAVERSING AN ARRAY", "steps": [...], "cx": "O(n) time · O(1) extra space"},
   {"t": "code", "file": "array_operations.c", "title": "array_operations.c", "cx": "O(n) overall"},
   {"t": "work", "title": "Worked example", "steps": [...]},
   {"t": "math", "tex": r"T(n) = \sum_{i=1}^{n} c_i", "num": 1},
   {"t": "table", "head": [...], "rows": [[...]], "caption": "..."},
   {"t": "note", "title": "Common mistake", "html": "<p>...</p>"},
   {"t": "pts", "items": ["Linear search — scans every element, O(n)", "Binary search — needs sorted input, O(log n)"]},
   {"t": "qa", "num": 1, "questions": ["First wording", "Second wording", "Third wording"], "answer": "One model answer", "keywords": ["marking term"], "exam_likely": False},
 ]}
```

Block types: `h2`, `h3`, `p`, `pts`, `math`, `algo`, `code`, `work`, `fig`, `table`, `note`, `tip`, `qa`.

`pts` is the quick-mode pointer list — `{"t": "pts", "items": ["Keyword — the phrase or value that defines it", "..."]}`. One pointer per line, each opening with the term being pointed at, then the thing worth remembering. It renders as a hanging-indent list with a short accent dash, so a scan down the page hits every term. Use it for quick theory; keep prose `p` for the connective sentence that introduces a list and for anything that genuinely needs a sentence. Short symbols still go in `$…$`, so `$O(n \log n)$` renders as maths and not as typewriter text.

Only choose block types allowed by the requested guide type. For a QA guide, use
one `qa` item per shared answer, not three independent items. `num` is the item
number; `questions` holds the equivalent wordings — **three unless the user asked
for another count in Step 0** — and every one of them must be answerable by the one
`answer`. For a code lab, `questions` holds a single task sentence and can be
emitted without the `Q.` prefix; the answer is the code and output cards. `keywords`
identifies the terms to highlight; `exam_likely` controls the star. Store supporting
likelihood evidence internally, not as extra Q lines or source citations in the
finished guide.


`math` is a display equation — its own block, rendered to SVG in Step 5, centred with space above and below, `num` optional for a right-aligned `(1)` when the prose cites it later. It is never inlined into a paragraph.

**Write the prose like a person, not a brochure.** Concrete numbers, specific values from the source, an actual opinion about which approach to use. Cut every sentence that could be deleted with no loss — significance inflation ("plays a crucial role"), negative parallelism ("not just X, but Y") and trailing `, highlighting…` clauses are the fastest way to make a study guide read as filler. In quick mode this applies to the pointers too: a pointer is a fact, not a mini-essay, and "important because…" is the first thing to cut.

---

## Step 3 — Generate the design assets

**Do not hand-roll the stylesheet or the grain.** `picker/theme.py` resolves the design
config and writes everything the page needs into the build directory in one call:

```bash
python picker/theme.py <build-dir> --preset <chosen-preset>
```

Pass `--preset <chosen-preset>` as shown in Step 0. The CLI reads the selected
bundled preset directly and writes:

| Output | What it is |
|---|---|
| `theme.css` | `picker/base.css` — the whole static stylesheet — with this design's `:root` tokens and `@page` rule generated ahead of it. The page links this one file. |
| `fonts/*.woff2` | the bundled faces the config's roles reference, copied in so the `@font-face` URLs resolve. **Without this the guide silently falls back to Georgia and Segoe UI** — the page still renders, so the failure is invisible unless you read the embedded font names back out of the PDF. |
| `grain.png` | the uniform 220px tile (no patch, or `texture: none`). |
| `grain-patch.png` | the page-sized raster, with the density patch baked into the pixels. |

**The patch is a density boost, not a mask.** Grain is uniform everywhere and simply
thicker inside a radius around the patch point, fading to the uniform field at the edge.
It **must be baked into the raster** — WeasyPrint silently ignores `mask-image`, so a
CSS mask over a uniform tile renders as a hard-edged disc, not a falloff. Measured boost
for a strength of 2.0 is about 2.7x; the page-sized raster generates in under a second.

**Read `picker/base.css` before writing any HTML.** It already defines every container
the block renderers emit — `.unit-head`, `.card`/`.card-h`/`.card-b`, `.code`/`.code-h`,
`.work`/`.work-h`/`.work-b`, `.note`/`.tip`, `.eq`, `table.data`, `.qa`,
`.contents-item`, `.cx` — and every break rule. **Do not restate any of it in the page.**
The class names are the contract between the renderer and the stylesheet.

WeasyPrint constraints `base.css` already respects, measured on this machine
(see `.scratch/picker/research/weasyprint-css-support.md`): no `color-mix()`, no
`mask-image`, no `filter`, no `backdrop-filter`; no comma inside a `var()` fallback (it
is silently truncated at the first comma). `calc()` and `var()` both work, including in
`@page`. Stay inside that subset if you add CSS.

Only if you are working without `theme.py` at all, build the uniform tile by hand:

```python
from PIL import Image
import random
random.seed(7)
S = 220
img = Image.new("RGBA", (S, S)); px = img.load()
for y in range(S):
    for x in range(S):
        a = max(0, min(26, int(random.gauss(11, 6))))
        px[x, y] = (255, 255, 255, a)
        a = max(0, min(22, int(random.gauss(9, 5))))
        px[x, y] = (0, 0, 0, a)
img.save("grain.png")
```

Roughly 4% alpha, mixed light and dark. Heavier reads as compression artefacts; lighter disappears.

---

## Step 4 — Build the HTML

One Python module per section (`c1.py`, `c2.py`, …) plus a `gen.py` that owns the block renderers and assembly. The page's only stylesheet is the `theme.css` Step 3 generated:

```html
<link rel="stylesheet" href="theme.css">
```

Do not inline a `<style>` block and do not re-declare any rule `base.css` already holds; `gen.py` emits HTML and nothing else.

Syntax-highlight code with Pygments (`CppLexer` handles C, C++ and Java acceptably; `HtmlFormatter(nowrap=True)` then map the classes in CSS). **Pygments is not installed on this machine** - either `pip install pygments`, or emit the token spans by hand; do not assume the import succeeds.

Code lives in real files on disk and is read at render time, so a typo in a program is visible and fixable in one place.

**Where the renderers must change to match this skill.** The block renderers live in `gen.py`; the per-section `c1.py` modules only pass item dicts.

- `gen.py` gains a `math` renderer (display block, `class="eq"`, inline SVG from Step 5, optional `num` → `<span class="eqn">(1)</span>`) and an inline-math pass that rewrites `$…$` in `p`/`pts`/`note`/`qa` prose to a small `<span class="imath">` SVG.
- `gen.py` must **never uppercase label text**. Emit `Worked example`, `Watch the phase wrap`, `Quantity` — sentence case, acronyms intact. All label styling is one block in `base.css` (`.unit-tag, .nt, .work-h, thead th, .figcap, .cap, a.toc .d`), serif italic via `--font-label`.
- `gen.py`'s `work`, `note`, `tip` renderers must **stop emitting the card wrapper**. Drop `.card`/`.card-h`/`.card-b` from those three; emit `.work-h` (label) + `.work-b` (steps) with `.work` as the open left-rule container, and `.nt` + body with `.note`/`.tip` as the open container. If they still wrap in `.card`, you get the old bordered box and the new CSS will look half-applied.
- Keep `algo` → `.card`/`.card-h`/`.card-b` and `code` → `.code`/`.code-h` exactly as they are. Those are the two surviving cards.
- `fig` renderer: `.fig` container with an `<img>` of the source diagram screenshot
  and a `.figcap` caption. Keep the image and caption together across page breaks.
  Include every diagram relevant to the requested scope; do not replace source
  screenshots with redraws. A supplementary SVG explanation may accompany the image.
- QA guide renderer: emit `.qa` with one `.qa-num` line containing the item number
  and optional `.qa-star`, then one `.q` paragraph per wording (default three,
  prefixed `Q.` unless the guide is a code lab), then one `.a` block prefixed
  `Ans.` Escape content before inserting safe keyword
  markup; highlight only the intended words using `strong.keyword`. Do not repeat
  the number on each Q line, use three columns, or provide several answers. Emit
  no rule between items — `.qa` is deliberately borderless so the unit head is the
  only divider. Keep a short item together; for an answer longer than a page, use
  `.qa-long` so it can flow, keeping the number and the prompts with the start of
  the answer.
- `table` renderer: drop any border/box wrapper; `table.data` is already open.
- `pts` renderer (quick mode): a `<ul class="pts">` of `<li>` pointers. No bullets in
  CSS — `base.css` draws the short accent dash as a `::before` and sets a hanging
  indent, so a wrapped pointer aligns under its own text. Keep one pointer per `<li>`
  and do not nest lists; a sub-point belongs in the pointer's own line after a
  semicolon, or the structure is wrong for the material.
- Unit and section chrome: each unit opens with `.unit` + `.unit-head`, whose `.unit-tag`
  is the small italic serif tag above the `h1`. `.unitbreak` forces a new page before a
  unit — use it only when the user asked for one guide page per topic, never by default.

---

## Step 5 — Pre-render the math to SVG

WeasyPrint cannot do MathML and cannot run MathJax at render time. So every equation is **pre-rendered to SVG at build time** and embedded in the HTML. Vector, not a rasterised screenshot — a 300 dpi PNG of a fraction still looks soft next to the text.

Two ways to produce that SVG. Take the first one that works and move on.

**A. MathJax → SVG via node (preferred — full LaTeX, Computer Modern).**

`node --version` (v26 fine), `npm install mathjax-full` in the build dir. Then a converter that reads a jobs file and writes one SVG per equation:

```javascript
// tex2svg.js — run: node tex2svg.js jobs.json '#c8cfd8'
const {mathjax} = require('mathjax-full/js/mathjax.js');
const {TeX} = require('mathjax-full/js/input/tex.js');
const {SVG} = require('mathjax-full/js/output/svg.js');
const {liteAdaptor} = require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('mathjax-full/js/handlers/html.js');
const {AllPackages} = require('mathjax-full/js/input/tex/AllPackages.js');
const fs = require('fs');
const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const tex = new TeX({packages: AllPackages});
const svg = new SVG({fontCache: 'local'});        // 'local' = glyph outlines in <defs>, no external font
const doc = mathjax.document('', {InputJax: tex, OutputJax: svg});
const COLOR = process.argv[3] || '#c8cfd8';
for (const j of JSON.parse(fs.readFileSync(process.argv[2], 'utf8'))) {
  const node = doc.convert(j.tex, {display: j.display !== false, em: 16, ex: 8, containerWidth: 80 * 16});
  let out = adaptor.outerHTML(adaptor.childNodes(node)[0]);
  out = out.replace(/currentColor/g, COLOR);      // see the gotcha below — <img> SVG cannot inherit colour
  fs.writeFileSync(j.out, out);
  console.log(j.out, out.length);
}
```

Run node **hidden/headless** — no foreground interactive process, no visible terminal. It is a batch build step, not something the user watches.

**B. matplotlib mathtext (fallback — pure Python, no node, no LaTeX install).**

```python
import matplotlib; matplotlib.use("Agg")
from matplotlib import mathtext
import re
def mtex(tex, out, color="#c8cfd8"):
    mathtext.math_to_image(tex, out, format="svg", dpi=200, color=color)
    s = open(out, encoding="utf-8").read()
    s = re.sub(r'<g id="patch_1">.*?</g>\s*', "", s, flags=re.S)   # opaque white page patch
    s = s.replace("fill: #ffffff", "fill: none")
    open(out, "w", encoding="utf-8").write(s)
```

`import matplotlib` first; if missing, `pip install matplotlib`. Handles a good subset — fractions, `\sum`/`\int` with limits, Greek, `\log`, matrices via `\begin{matrix}`. **It is not LaTeX**: `\le` and `\left[\begin{matrix}…\right]` both parse-error (`\leq` works, `\left`/`\right` do not). If an equation fails to parse, that is your signal to fix the MathJax path rather than rewrite the maths.

`latex2mathml` is a dead end here — it emits MathML, and WeasyPrint does not render MathML. Only use it if you first prove WeasyPrint lays it out; it will not.

Verification that the mechanism actually ran, not silently produced blank files:

```bash
ls -l eq*.svg                              # a real equation is 3–7 KB; a blank one is a few hundred bytes
grep -o '<path' eq_sum.svg | wc -l         # must be > 0 (use -o | wc -l: the SVG is one line, so -c always says 1)
grep -o 'href="[^#][^"]*"' eq*.svg         # must be empty — no external font or image references
```

Then embed. Inline SVG inherits the page colour; `<img src="eqN.svg">` does not, so the converter bakes the hex fill in (see the gotcha). Prefer inline for display equations — one fewer file per page — and `<img>` only when the same equation repeats.

### Display vs inline

- **Display** (`{"t": "math", "tex": …}`) gets its own centred block: `margin: 7mm 0`, `page-break-inside: avoid`, an optional right-aligned number. Fractions, summations, matrices, derivations — anything a marker would write on its own line.
- **Inline** (`$…$` in prose) is for a short symbol only: `$O(n \log n)$`, `$x^2$`, `$n$`. Render it the same way to a small SVG and set it on the text baseline with `vertical-align`.

If it is a real equation, a derivation step, or looks wrong squeezed into a sentence — it goes in a display block. Inline math that breaks the line height is the tell that it should have been display.

### The math gotchas

- **`<img>`-embedded SVG cannot inherit `currentColor`.** MathJax emits `fill="currentColor"`; inline, that picks up the body colour and works, but the moment the same file is referenced as `<img src>`, there is no inheritance context and it resolves to black — invisible on a dark page. Bake the hex in at build time (`out.replace(/currentColor/g, "#c8cfd8")`). This is the one that wastes an afternoon.
- **`base_url` again.** Any `<img src="eqN.svg">` by relative path needs `base_url` on the `HTML(...)` call, same class of bug as the grain PNG — it renders nothing, silently.
- **Self-contained SVGs only.** Convert fonts to outlines (`fontCache: 'local'` for MathJax, `svg.fonttype = "path"` for matplotlib) and keep no external `href`. An SVG that reaches for a font the render host does not have falls back to the body font and the maths loses its shape.
- **matplotlib writes an opaque white background.** Strip `<g id="patch_1">` or every equation carries a white box onto the dark page.
- **Duplicate `<defs>` ids across inlined equations.** Two SVGs inlined on the same page can define the same glyph id; WeasyPrint resolves them consistently and it renders fine in practice, but if a glyph ever comes out wrong, that is the cause — the fix is to uniquify the ids per equation, or reference repeated equations as `<img src>` instead of inlining them twice.

---

## Step 6 — Render

```python
from weasyprint import HTML
HTML("doc.html", base_url="/tmp/build/").write_pdf("doc.pdf")
```

`base_url` is required — the grain PNG is referenced relatively and silently vanishes without it.

If WeasyPrint is missing: `pip install weasyprint --break-system-packages`. Note that **WeasyPrint 70.0 ignores `background-origin` and `background-clip` on `@page` silently** - the page background is anchored at the content box and no warning is emitted. See the gotcha below for the working fix; it is not `background-origin`. Chromium/Playwright also work if present - swap the render call and keep the CSS as-is.

---

## Step 7 — Verify spacing before delivering

Two mechanical checks catch everything. Run both; do not eyeball it.

**Rasterise with PyMuPDF, not poppler.** `pdftoppm`/`pdftocairo` are absent on this
machine, but PyMuPDF is installed and rasterises directly:

```python
import pymupdf   # the fitz module is deprecated; import pymupdf
doc = pymupdf.open("doc.pdf")
for i, page in enumerate(doc, 1):
    page.get_pixmap(dpi=40).save(f"px/p-{i:02d}.png")
```

**A. Fill ratio — finds near-empty pages.**

```python
from PIL import Image
import glob, os
files = sorted(glob.glob("px/p-*.png"))          # rasterise first - see below; pdftoppm is absent
im0 = Image.open(files[0]); W, H = im0.size
top = int(19 / 25.4 * 40); bot = H - int(22 / 25.4 * 40)   # match the @page margins
for f in files:
    n = int(os.path.basename(f).split("-")[1].split(".")[0])
    px = Image.open(f).convert("L").load()
    last = top
    for y in range(top, bot):
        for x in range(0, W, 3):
            if px[x, y] > 95: last = y; break
    frac = (last - top) / (bot - top)
    if frac < 0.72: print("sparse page", n, round(frac, 2))
```

Deliberate exceptions are the cover, the contents page and a closing page. Anything else under 72% is a bug — almost always a card that could not split, or a forced section break. One gap is unavoidable: `.code` sets `overflow: hidden`, so a card cannot break across pages, and the last item before a new unit can leave a quarter page empty rather than splitting its listing. That is the preferred failure — splitting a code card mid-listing reads worse than the gap.

**B. Top-edge seam — finds the flat band.**

```python
im = Image.open("page.png").convert("RGB"); W, H = im.size
for y in (3, 20, 45, 59, 61, 75, 400):
    row = [im.getpixel((x, y)) for x in range(8, W - 8, 9)]
    print(y, tuple(sum(c[i] for c in row) // len(row) for i in range(3)))
```

The averages must drift smoothly. A jump right at the top margin means the page gradient is not covering the margins — see the gotcha below.

**C. Side edges — finds the left/right band.**

Check B averages *across* each row, so it cannot see a vertical band: the bad strip is
part of the average it is already taking. Scan the other axis, comparing each column
against the middle of the page. Sample a block, not a single pixel — grain is noise.

```python
im = Image.open("page.png").convert("RGB"); W, H = im.size
mid = W // 2
def col(x, y0, y1):                       # block average down one column
    c = [im.getpixel((x, y)) for y in range(y0, y1, 4)]
    return tuple(sum(p[i] for p in c) // len(c) for i in range(3))
ref = col(mid, H//3, 2*H//3)
for x in (1, 4, 8, 12, W-12, W-8, W-4, W-2):
    v = col(x, H//3, 2*H//3)
    print(x, v, "DIFFERS" if max(abs(v[i]-ref[i]) for i in range(3)) > 3 else "")
```

Every column must match the middle. A column at the sheet edge that is visibly darker
than the middle is the content-box anchor bug: the background is not reaching the
margin. It is invisible in the gradient alone (which is near-flat across a page and
hides it) and shows up only in the **grain**, so run this on a build with the texture on.


---

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

The light presets (`paper`, `sepia`) invert the same roles and give the code card a
*dark* fill — the code card is the one container that grounds against the page tone.

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
- **15mm sides** gives about 180mm of text width. At 7.5pt DejaVu Sans Mono a character is ~1.59mm, so plan for **≤ 105 characters per code line** — measure the source files (`awk '{print length}' f | sort -rn | head -1`) and wrap anything longer by hand before it ever reaches the PDF.

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

Verify with check B **and** check C below — a row-average scan is blind to a side band,
because it averages *across* the very strip that is wrong.

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

Two things to get right:

- **Keep the source's wording and numbering.** Do not rewrite `[INITIALIZE]` into plain English — reproduce it.
- **When Start is prepended, shift every internal reference with it.** `Repeat Steps 3 and 4` becomes `Repeat Steps 4 and 5`; `Go to step 6` becomes `Go to step 7`; `[End of step 2 loop]` becomes `[End of step 3 loop]`. Miss this and the algorithm cites steps that no longer exist.

A reference bumper that handles all the shapes:

```python
def bump_refs(txt, off):
    def rep(m):
        return re.sub(r"\d+", lambda d: str(int(d.group(0)) + off), m.group(0))
    return re.sub(r"[Ss]teps? \d+(?:\s+(?:and|to)\s+\d+)*", rep, txt)
```

Shift by a uniform offset rather than renumbering sequentially — sequential renumbering silently breaks references to steps that were never numbered in the source.

**Do not** bookend a pure code listing (a function body with braces or semicolons). Detect them and leave them alone:

```python
if any(("{" in l or "}" in l or ";" in l) for l in lines): skip_bookends()
```

Strip HTML entities before that test — `&lt;` contains a semicolon and will wrongly flag every algorithm that uses a `<`.

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
the single source of truth for every component the renderers emit. Read it before
writing HTML, and treat its class names as the contract between `gen.py` and the page.

`theme.py` (Step 3) concatenates it into the guide's `theme.css` **ahead of** the
generated `:root` tokens and `@page` rule, so the built page links exactly one file.
Edit `base.css` to change how the guide looks; never edit a built `theme.css` by hand,
since the next `theme.py` run overwrites it.

The one thing that is *not* in `base.css` is `@page`, because it is per-design: the
background colour, the gradient and the grain layer are all resolved from the config
and written by `theme.py`. The `@page` background gotcha (above) applies to it.

---

## Checklist before delivering

- [ ] Selected depth respected: quick covers every in-scope topic and loses no marks-bearing fact, but carries pointers/snippets instead of explained prose; full is unchanged
- [ ] Selected guide type respected: textbook has only information/formulae/diagrams; walkthrough has explained solution steps; QA has the number of equivalent wordings the user chose (default three) and one shared answer per numbered item
- [ ] Dividers checked: the unit head's rule is the only horizontal rule opening a block; no hairline sits between consecutive Q&A items
- [ ] QA answers are in proper English, marking keywords highlighted, marks respected, and likely-question stars have an accurate legend and internal evidence
- [ ] Every in-scope source diagram is included as a screenshot, with all labels readable and coverage inventory checked
- [ ] Theme chosen in chat from the eight presets; no guide web preview or browser save gate
- [ ] Subagents used whenever more than one guide was requested; every child PDF reviewed
- [ ] Every program compiles and ran with sample input
- [ ] Every algorithm starts `Step 1: Start` and ends `Step N: Stop`, references shifted to match
- [ ] Every algorithm card and code card has a complexity line
- [ ] No source citations, no experiment or chapter numbers, no descriptive paragraphs above code
- [ ] No author name, roll number or course code anywhere
- [ ] Fill-ratio check run — only cover, contents and closing page under 72%
- [ ] Edge checks run — **both** axes: row averages drift smoothly across the top margin (B) **and** every column matches the page centre (C). The gradient is near-flat across a page, so a missing side band shows only in the grain
- [ ] Every display equation rendered to SVG — no blank `eq*.svg`, every file thousands of bytes with `<path>` in it
- [ ] `pdftotext` grepped for leaked markup (`&amp;`, `&lt;`, `None`, `Traceback`) **and for leaked LaTeX**: `grep -nE '\\\\(frac|sum|begin|alpha|beta|gamma|log|varepsilon)|[^0-9]\$'` must be empty, so no raw `$…$` or backslash command reached the page
- [ ] Fonts actually embedded — read the names back out of the PDF (`pymupdf` `get_fonts()`); the bundled families assigned to the selected preset must appear, not unintended fallback fonts
- [ ] One accent colour, hairline structure, grain visible but not obvious
- [ ] Cards are the exception — more than two or three real cards on a page means boxes have crept back in where an open block belonged
- [ ] No label is uppercase or tracked — `grep -nE 'text-transform:\s*uppercase' theme.css` and `grep -nE 'letter-spacing:\s*[0-9.]*[1-9]' theme.css` both empty, and `grep -nE '>[A-Z][A-Z /&·-]{3,}<' ` over the built HTML finds no shouted label. Every label reads `Worked example`, not `WORKED EXAMPLE`, and acronyms survived (`HRTF`, `ITD`, `FFT`, `8D` — not `Hrtf`)
- [ ] Descriptive filename for the PDF itself
