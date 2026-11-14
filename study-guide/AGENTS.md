# Working in this repo

This repo holds the `study-guide` agent skill.

## Agent skills

### Issue tracker

Issues live as local markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root, when they exist.

### Skills

Wayfinder maps live at `.scratch/<effort>/map.md` with child tickets in
`.scratch/<effort>/issues/NN-<slug>.md`. That convention is defined in
`docs/agents/issue-tracker.md` under "Wayfinding operations".

## The build tool

`build.py` is the product, not a helper. A guide is a YAML content file plus
`--theme/--mode`; the tool renders it and checks the PDF. Theme is Paper, PaperX
or Obsidian. Mode is full (concise textbook-style topic answers) or quick (a
selective revision crux). No guide types or separate depth setting remain. Anything
a guide needs belongs in `build.py` or `picker/base.css`, and anything a content author needs
to know belongs in `CONTENT-FORMAT.md`. Do not reintroduce per-guide generator
scripts: if a block is rendered differently for one guide, that is a missing option
in `build.py`.

`picker/` stays the source of truth for appearance — `base.css` for the stylesheet,
`theme.py` for the theme assets, `presets/` for exactly Paper, PaperX and Obsidian.
All themes start with contents, followed directly by topics. No covers,
preliminary guides, question-bank labels, exam frames or boilerplate instructions.
PaperX is a distinct academic layout with thicker 2pt left vertical rules and
semantic colours, without generic printed block labels, and supports authored
SVG figures. Keep its overrides scoped so Paper and Obsidian retain their appearance
apart from the shared contents-first composition.

`assemble.py` combines ordered worker chapter YAML files into the one canonical
input consumed by `build.py`. Chapter workers own their content/assets/coverage;
the main agent owns shared layout and final compilation. Figure-generation code
is allowed for PaperX, but per-guide PDF generator scripts remain prohibited.
