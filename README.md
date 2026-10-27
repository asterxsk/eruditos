# Eruditos

**A skills library for AI coding agents — interactive tutoring, print-ready study guides, and finished assignments.**

[![Skills: 3](https://img.shields.io/badge/skills-3-FF8A5C)](#whats-inside)

Built on the [skills](https://skills.sh) CLI from [vercel-labs/skills](https://github.com/vercel-labs/skills).

```bash
npx skills add asterxsk/eruditos --skill study-guide --skill professor --skill assign-to-ai -g -y
```

That installs all three skills to your user directory. Add `--agent claude-code codex ...` to target specific agents, or drop `-g` to install into the current project.

One at a time:

```bash
npx skills add asterxsk/eruditos --skill study-guide   -g -y
npx skills add asterxsk/eruditos --skill professor     -g -y
npx skills add asterxsk/eruditos --skill assign-to-ai  -g -y
```

Restart your agent afterwards so it picks up the new skills.

---

## What's inside

Two skills that share the same subject: turning source material into durable learning.

| Skill | Role |
|---|---|
| **study-guide** | Turns slide decks, textbook chapters, lab manuals, and past papers into a print-ready PDF — textbook, worked walkthrough, or exam-style Q&A. Renders in one of eight preset themes, with a bundled theme picker. |
| **professor** | Teaches interactively in chat, drilling the hardest questions from the learner's own material, and keeps a persistent Markdown progress tracker across compaction and new sessions. |
| **assign-to-ai** | Completes a written assignment in the learner's own Word document: writes the code, runs it in the app they name, screenshots the run, crops to the output, and pastes each answer in under `Code:` and `Output:` headings. |

They complement each other. `study-guide` produces a document to revise from; `professor` runs the revision — asking the questions, not just listing them. `assign-to-ai` is the odd one out: it does the work rather than teaching it, so reach for the other two when the goal is understanding rather than a submitted file.

### study-guide

A standalone reference builder. It harvests the source material (`.pptx`, `.docx`, `.pdf`, images, pasted text), drafts a content map, generates the design assets, pre-renders every equation to SVG, and renders the PDF with WeasyPrint. Three guide types:

- **Textbook** — definitions, formulae, and diagrams, organised by topic.
- **Walkthrough** — worked sums and derivations, every step explained.
- **QA** — an exam question bank: three equivalent wordings per numbered item, one shared model answer.

Each type comes at **full** or **quick** depth. Quick covers exactly the same material with the same accuracy, but states it as pointers, keywords and code snippets rather than explained prose — for a revision sheet rather than a walkthrough.

Diagrams from the source are captured as screenshots and kept legible; no author names, course codes, or source citations reach the finished guide.

### professor

A tutoring loop, not a study guide generator. It reads the course folder and an existing `learning-progress.md` tracker before resuming, records the exact scope and watched exclusions, then asks a configurable number of the hardest questions per topic — recommending 2–5. Progress is written back to the tracker so a new chat or a context compaction does not lose where the lesson stopped. Exposure is never treated as mastery.

### assign-to-ai

Takes a lab manual, question sheet, or worksheet and fills it in. It asks four things up front — which app and language (VS Code in C, RStudio in R, a Matplotlib script, anything), which document and which questions, whether the screenshot should be cropped to the output pane, and anything else specific — then asks the learner to **close the file in Word** before it writes, because an open document is locked and edits will not land.

From there it reads the document, writes one beginner-level source file per question, and runs each one in the app the learner named. Screenshots are taken through `capture_app.py`, which verifies the target window actually holds focus before sending a single keystroke and aborts with `FOCUSFAIL` otherwise — blind `SendKeys` lands in whatever window is focused, which is how you end up typing into your own terminal. Each screenshot is then cropped down to the output text alone: no tab bar, no editor, no status bar.

`docx_code_inserter.py` pastes the result into the document. Every block is inserted *after* a paragraph the learner wrote — nothing existing is rewritten — and the document is backed up first. Code renders on a dark `#181818` background in Courier New with syntax highlighting (C, Python, R, or plain); body text stays Times New Roman 12.

It finishes by asking whether the result meets the learner's standard, then deletes the working files: screenshots, crops, binaries, `in.txt`, and backups. Source files and the document stay.

Requires `python-docx` and `Pillow`. The screenshot step is Windows-only; elsewhere the skill falls back to the platform's own capture tool, keeping the same focus check.

## Manual install

A skill is just a folder with a `SKILL.md`. Clone and copy the ones you want:

```bash
git clone --depth 1 https://github.com/asterxsk/eruditos
cp -r eruditos/study-guide  ~/.claude/skills/study-guide
cp -r eruditos/professor    ~/.claude/skills/professor
cp -r eruditos/assign-to-ai ~/.claude/skills/assign-to-ai
```

## Repository layout

```text
study-guide/
├── SKILL.md            the skill instructions
├── AGENTS.md           notes for agents working on the skill
├── docs/
├── picker/             theme picker: base.css, theme.py, presets, index.html
└── ...
professor/
├── SKILL.md
├── agents/
└── assets/             learning-progress template
assign-to-ai/
├── SKILL.md            the skill instructions
└── scripts/
    ├── docx_code_inserter.py   Code:/Output: blocks + syntax highlighting
    ├── capture_app.py          run in the named app, screenshot it
    └── cleanup.py              dry-run cleanup of working files
```

## License

Not yet specified.
