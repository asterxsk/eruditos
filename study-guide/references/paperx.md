# PaperX

Read when the selected theme is `paperx`. Its appearance is independent of
`mode: full|quick`: full gives concise textbook-style topic answers; quick selects
the crux for revision and may omit minor topics. Keep the selection honest.
Follow the shared startup flow: collect missing theme/mode choices with the
harness's built-in question tool before requesting source. Recommend Full for a
proper, in-depth guide; reserve Quick for skimming and last-minute revision. Use
source already supplied instead of asking the user to provide it again.

## Composition

Like every theme, PaperX opens with **contents, then topics**. It has no cover,
terminal card, preliminary guide, paper pattern, checklist, exam-answer frame,
question/answer labels or likely stars. Do not print readiness claims or
instructions on how to write answers. Keep internal coverage evidence outside
the PDF. Topic titles and genuine content-specific note titles remain useful.

Use white pages, compact serif explanatory text, bold sans-serif headings,
light washes and stronger **2pt left vertical rules** matching the reference.
Colour groups convey structure: blue theory, green diagrams, orange equations,
purple tables and pale-yellow clarifications. **Do not print generic semantic
labels** such as THEORY, GRAPH / DIAGRAM or EQUATIONS above each group. No grain
is required. Paper and Obsidian keep their own typography and appearance.

Let the content determine the composition. Keep headings with their first
content, allow long explanations to flow, and keep equations and figure labels
readable. Do not force each topic onto a page or fabricate blocks to complete a
template. Contents and final pages can naturally be sparse; do not copy accidental
empty areas from the reference.

## Authored figures

Inspect source pages visually, including image-only material, before redrawing.
Inventory all examinable labels, axes, arrows, values, units, annotations and
relationships. Prefer self-contained SVG for graphs, flowcharts, trees, circuits
and organisation charts. Agents can write SVG directly or use plotting/layout
code. Supply explicit dimensions and viewBox, readable labels and clear strokes;
avoid scripts, remote assets and browser-runtime dependencies.

### Match the source geometry and technical detail

A redraw must remain recognisable as the source diagram. Preserve its shapes,
orientation, relative placement and grouping: circular states remain circular,
ellipses remain ellipses, 3D blocks retain their perspective faces, and ALU,
decoder, gate, transistor and register symbols retain their distinctive forms.
Do not flatten 3D diagrams or replace circuits with generic rectangular blocks.
Typography and print colours may be cleaned up without changing this geometry.

Keep every meaningful port, connection, arrow direction, branch, feedback path
and junction. Distinguish connected junctions from crossing wires using dots or
wire jumps. Separate signal groups, such as address, data and control buses,
must not appear shorted together. Add complexity when needed to preserve the
source's structure rather than simplifying away instructional detail.

For timing diagrams, preserve the source's waveform shapes, signal rows,
polarity, clock/cycle boundaries, transition ordering, valid-address/data
windows, acknowledgments and wait states. Show multi-bit validity envelopes
as in the source rather than replacing them with plain boxes or generic lines.
Check that sampling and transfer events agree with the waveforms.

Inspect every source diagram at readable resolution and compare every completed
SVG with it, including diagrams that initially look simple. Record the source
location and shape/connection checks in the coverage record. Render through the
final PDF's SVG engine, then inspect the smallest labels and wire endpoints at
their actual PDF size; a successful XML parse is not visual verification.
Split combined figures into separate source diagrams or panels when needed for
legibility, preserving each panel's geometry. Use `fig.max_height` when the
default height cap would shrink detailed labels excessively.

If a source is technically wrong, make the smallest necessary correction,
preserve the rest of its geometry and record the correction internally. An
additional explanatory figure without a source diagram may use an appropriate
new layout, but identify it as explanatory rather than a source redraw. Calling
a redraw "schematic" does not excuse missing source shapes or connections.

Reference assets with `fig.file`; use the shared `table`, `math` and prose blocks
for semantic content. Do not exchange arbitrary chapter HTML or create a separate
PDF generator per guide. Extend reusable renderer support when necessary.

Additional explanatory figures can clarify source-backed concepts. Label schematic
or illustrative plots where appropriate, and never fabricate empirical data. A
photo or other intrinsically visual evidence may retain its source image if a
redraw would change its meaning; record the exception internally. Report a figure
that cannot be reconstructed faithfully rather than dropping it silently.

Keep a source-to-asset-to-section mapping. Check redraws against their source or
mathematical model and inspect the smallest labels in the final PDF. This redraw
policy applies to PaperX; Paper and Obsidian retain source diagram screenshots.

## Chapter workers

Use subagents for a multi-chapter PaperX guide even when the result is one PDF.
The main agent first inventories the source, defines the full scope or quick
selection, chapter boundaries, terminology, figure conventions, theme and mode.

Assign one substantial chapter or two short related chapters per worker. Give
each worker exclusive ownership of chapter YAML, assets and internal coverage
record. Tell workers they share the workspace and must not overwrite others'
files or edit shared renderer, styles, metadata or contents. They return content,
figures, unresolved questions and relevant numerical/code validation results;
they do not style independent final PDFs.

Work in waves within available slots without nested guide/chapter fan-out. A
single chapter needs no artificial splitting. If delegation is unavailable,
disclose that and agree on a serial fallback rather than claiming workers ran.

The main agent verifies accuracy and selection/coverage, reconciles overlaps and
cross-references, then assembles chapter files in manifest order with `assemble.py`.
Build the canonical YAML with `build.py` so contents, numbering and pagination
are global. Do not concatenate chapter PDFs. Inspect the final document for
contents destinations, readable figures, split tables, orphaned headings, gaps
and overflow. See [CONTENT-FORMAT.md](../CONTENT-FORMAT.md) for the schema.
