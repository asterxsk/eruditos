---
name: "study-guide"
description: "Build PDF study guides from slides, textbook chapters, lab manuals, code, and notes in Paper, PaperX, or Obsidian. Full gives concise textbook-style topic answers; quick selects the crux for revision. PaperX supports redrawn figures and chapter subagents."
---

# Study Guide

Turn the learner's material into a standalone PDF reference. Choose **theme** and
**mode** independently. Every theme opens with a contents table, followed directly
by topics. The shared renderer owns layout, mathematics, numbering and PDF checks;
the agent writes content and figure assets.

## Start with the harness's question tool

Before drafting or rendering, collect the user's theme and mode through the
harness's built-in question/input tool. Inspect the tools actually available
and permitted in the current mode; do not guess a tool name or change modes.
Ask both missing choices together in one batch when supported. If the tool only
supports one question at a time, ask them consecutively before requesting source.
Reuse choices explicitly supplied in the request or earlier in the conversation;
do not ask the user to answer them again.

- **Theme:** Paper (`paper`), PaperX (`paperx`), or Obsidian (`obsidian`). Paper is
  light with dark code cards; Obsidian is dark; PaperX is a compact white academic
  layout with serif body text, sans-serif headings and stronger coloured left rules.
- **Mode:** offer **Full (Recommended)** (`full`) and **Quick** (`quick`). Explain
  the choice in the question: Full is recommended for a proper, in-depth study
  guide with clear topic explanations and the important exam material. Quick is
  only for skimming, rapid recap and last-minute revision: selected key points,
  formulas and cues, with less explanation and potentially less coverage.
  Theme does not change mode. Recommend Full, but wait for the user's choice
  rather than silently selecting it.

Include any genuinely necessary, independent scope clarification in this opening
batch if it is already apparent from the request. Do not add board, question-bank,
code-guide, marks-format or other removed settings. If a setting is unanswered,
keep it pending; an asynchronous tool acknowledgement, preselected option or
timeout is not an answer. If no built-in question tool is available and permitted,
ask the same concise questions in chat and explain that limitation once.

After the settings are answered, use the source already supplied in the
conversation (attachments, pasted material, paths or links). Do not ask for it
again. If no source was supplied, ask the user to attach, paste or identify the
material, then wait for it before harvesting or drafting. Request attachments in
ordinary chat when the harness's input tool accepts text only; do not pretend it
can receive file uploads. Ask a later source-dependent clarification only when
inspection reveals an ambiguity that materially blocks the guide.

The read-only gallery at `picker/server.py` can show the three theme samples when
the learner needs to compare them. Run it as a hidden process if used, take the
choice through the harness's built-in question tool when available, and stop the
process when done. The gallery is optional and does not replace the opening questions.
A theme named in the request needs no gallery or repeat selection. If the gallery
cannot be shown, list the same three names; do not silently choose a saved design.

### Full

Recommended for a proper, in-depth guide rather than last-minute skimming.
Write concise, textbook-style answers organised by topic. Cover the examinable
essentials in the requested scope: the definition, important principles,
conditions, formulas and units, plus the steps or examples needed to understand
and apply them. Keep the terminology and distinctions a learner needs to answer
accurately. Use connected explanation where it helps, without exhaustive textbook
detail, repeated definitions or filler.

Code, algorithms, equations, diagrams and worked examples belong naturally where
the source contains them or the concept needs them. There is no separate code
guide, question-bank mode, forced function inventory or mandatory complexity line.

### Quick

Use for skimming, rapid recap and last-minute revision, not as a replacement for
the explanations in Full.
Select the **crux for skim and revision**: high-priority key points, formulas,
contrasts, memory cues and concise snippets. Quick is deliberately selective; it
may omit minor topics and detail. It is not a promise to preserve the full guide's
coverage in compressed wording. Choose priorities from the learner's goals and
the source's emphasis, and keep an honest internal record of included/omitted
topics. Do not invent exam probabilities or describe a selective guide as complete.

The learner can later request full explanations of weak topics only. Do not expand
every quick pointer into a full answer unless asked. Selected facts, formulas,
figures and code remain technically accurate even when the scope is selective.

## Harvest and organise

Read every relevant source element, including tables, slide text boxes, formulas
and image-only pages. Inspect examinable figures visually; text extraction alone
does not establish coverage. Preserve source order and meaning where they matter,
especially algorithm steps, code behaviour and definitions.

Keep an internal inventory mapping topics and figures to source locations and
output sections. In full mode, use it to check the requested coverage. In quick
mode, record the intentional selection. The PDF itself is source-neutral: no
author/student details, course codes, copied experiment identifiers or source
citations unless the learner explicitly asks for them. Its own chapter and topic
numbers are navigation and are allowed.

All themes begin with **contents, then topics**. Do not add a cover, terminal card,
preliminary guide, paper pattern, checklist, board-selection prompt, exam-answer
frame, question/answer label, likely-question star, or printed instructions on
how to write an answer. Do not print generic readiness claims. Genuine content
headings and concise, content-specific notes are useful; boilerplate is not.

### Figure policy

**Paper and Obsidian:** include source screenshots for in-scope diagrams, cropped
with all labels, axes, arrows, annotations and legends intact. Preserve their
original colours and readable backgrounds, including on dark pages.

**PaperX:** read [references/paperx.md](references/paperx.md) before drafting.
Redraw instructional figures, preferably as self-contained SVG. Inspect their
sources first and preserve all examinable values, labels, units and relationships.
Keep the source diagram's shapes and relative layout: circles stay circles,
3D blocks stay 3D, and circuit symbols and timing waveforms retain their form.
Retain the detail needed for accurate connections and sequencing; do not replace
a source diagram with a simpler generic schematic. Verify every SVG against its
source at readable size, then inspect its labels and connections in the final PDF.
Additional explanatory figures may clarify source-backed concepts; label schematic
or illustrative plots where appropriate and never fabricate empirical data.
Intrinsically visual evidence, such as a photo, can keep its source image if a
redraw would change its meaning; record that exception internally.

For either policy, check the smallest labels in the final PDF. Report missing or
unrecoverable figures rather than claiming coverage. Figure-generation code is
allowed; per-guide PDF generator scripts are not. Use the shared `fig`, `table`,
`math` and other semantic blocks instead of exchanging arbitrary chapter HTML.

## Delegate chapter work

Use subagents for multiple requested guides, and for a multi-chapter PaperX guide
even when the output is one PDF. A single chapter does not need artificial splits.

1. The main agent inventories the source and defines scope or quick selection,
   chapter boundaries, terminology, figure conventions, theme and mode.
2. Assign one substantial chapter or two short related chapters per worker. Give
   each worker exclusive ownership of its chapter YAML, assets and coverage record.
   Tell workers they share the workspace and must not overwrite other chapters or
   edit global renderer/styles. Workers return content, figures, unresolved issues
   and relevant numerical/code validation; they do not make final contents or PDFs.
3. Run workers in waves within available slots. Avoid nested guide/chapter fan-out.
   The main agent checks accuracy, selection/coverage and figure fidelity, resolves
   overlaps and cross-references, then compiles one canonical YAML file per guide.
4. Render and inspect the complete PDF, so contents, pagination and numbering are
   global. Do not concatenate independently styled chapter PDFs.

If delegation is unavailable, disclose the limitation and agree on a serial
fallback; never claim subagents ran when they did not.

## Write, assemble and build

The schema and practical examples are in [CONTENT-FORMAT.md](CONTENT-FORMAT.md).
Use only the content primitives the renderer supports: `p`, `pts`, `h2`, `h3`,
`theory`, `math`, `fig`, `table`, `note`, `tip`, `work`, `code`, and `algo`.
They are building blocks, not separate guide modes.

```bash
python build.py --example guide.yaml
python build.py guide.yaml --theme paperx --mode full
```

For chapter workers, put the chapter paths in a manifest and assemble first:

```bash
python assemble.py manifest.yaml -o guide.yaml
python build.py guide.yaml --theme paperx --mode quick
```

Write prose that carries a definition, condition, distinction or explanation;
remove sentences that add no information. Use `pts` for short pointers and
`theory` for related paragraphs/points. Display equations belong in `math`;
short inline mathematics can use `$…$`. Highlight meaningful terms with `**…**`.

Use real code when source code or the concept needs it. Check syntax and run
examples when an appropriate runtime exists; report any unverified code. Do not
turn a topic into an automatic function-by-function inventory. State complexity
only where useful. Preserve an algorithm's meaningful steps and order without
adding artificial Start/Stop bookends.

`mode: full|quick` is the only content-mode setting. Old `type`/`depth` keys and
`--type`/`--depth` flags are rejected rather than silently mapped. Migrate by
choosing `mode`, drafting topic content for that mode, and replacing removed
question-bank/function/exam blocks with the supported primitives.

## Verify and deliver

Read build diagnostics, fix the content or shared renderer, and rebuild. Do not
hand-edit generated HTML/CSS. Retain delivery checks and visually inspect rendered
pages, including chapter transitions, equations, tables, code and figures.

- Contents links and printed page numbers reach the right topics; contents is the
  first material in all three themes.
- Full covers the requested essentials concisely; quick states an honest selection
  and carries no false completeness or exam-likelihood claims.
- Figures follow the selected theme's policy, preserve their technical meaning,
  and have readable labels. No clipping, overflow, raw markup or missing assets.
- Topic headings stay with their content; long blocks flow without large avoidable
  gaps. Naturally short contents and final pages are acceptable.
- Paper/Obsidian retain their style. PaperX retains its academic palette and thicker
  2pt left rules without generic semantic labels printed above each block.
- No obsolete guide-type, question-bank, exam-frame or preliminary-page machinery
  appears in the PDF. Genuine content-specific note titles remain allowed.

Deliver the PDF with a descriptive filename. State material verification limits
truthfully and keep the coverage/selection record available for follow-up topics.
