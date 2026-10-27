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
`--theme/--type/--depth`; the tool renders it and checks the PDF. Anything a guide
needs belongs in `build.py` or `picker/base.css`, and anything a content author needs
to know belongs in `CONTENT-FORMAT.md`. Do not reintroduce per-guide generator
scripts: if a block is rendered differently for one guide, that is a missing option
in `build.py`.

`picker/` stays the source of truth for appearance — `base.css` for the stylesheet,
`theme.py` for the theme assets, `presets/` for the eight palettes.
