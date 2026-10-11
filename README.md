# Eruditos

**A skills library for AI coding agents — interactive tutoring and print-ready study guides.**

[![Skills: 2](https://img.shields.io/badge/skills-2-FF8A5C)](#whats-inside)

Built on the [skills](https://skills.sh) CLI from [vercel-labs/skills](https://github.com/vercel-labs/skills).

```bash
npx skills add asterxsk/eruditos --skill study-guide --skill professor -g -y
```

That installs both skills to your user directory. Add `--agent claude-code codex ...` to target specific agents, or drop `-g` to install into the current project.

One at a time:

```bash
npx skills add asterxsk/eruditos --skill study-guide -g -y
npx skills add asterxsk/eruditos --skill professor  -g -y
```

Restart your agent afterwards so it picks up the new skills.

---

## What's inside

Two skills that share the same subject: turning source material into durable learning.

| Skill | Role |
|---|---|
| **study-guide** | Turns slide decks, textbook chapters, lab manuals, and past papers into a print-ready PDF — textbook, worked walkthrough, or exam-style Q&A. Renders in one of eight preset themes, with a bundled theme picker. |
| **professor** | Teaches interactively in chat, drilling the hardest questions from the learner's own material, and keeps a persistent Markdown progress tracker across compaction and new sessions. |

They complement each other. `study-guide` produces a document to revise from; `professor` runs the revision — asking the questions, not just listing them.

### study-guide

A standalone reference builder. It harvests the source material (`.pptx`, `.docx`, `.pdf`, images, pasted text), drafts a content map, generates the design assets, pre-renders every equation to SVG, and renders the PDF with WeasyPrint. Three guide types:

- **Textbook** — definitions, formulae, and diagrams, organised by topic.
- **Walkthrough** — worked sums and derivations, every step explained.
- **QA** — an exam question bank: three equivalent wordings per numbered item, one shared model answer.

Diagrams from the source are captured as screenshots and kept legible; no author names, course codes, or source citations reach the finished guide.

### professor

A tutoring loop, not a study guide generator. It reads the course folder and an existing `learning-progress.md` tracker before resuming, records the exact scope and watched exclusions, then asks a configurable number of the hardest questions per topic — recommending 2–5. Progress is written back to the tracker so a new chat or a context compaction does not lose where the lesson stopped. Exposure is never treated as mastery.

## Manual install

A skill is just a folder with a `SKILL.md`. Clone and copy the ones you want:

```bash
git clone --depth 1 https://github.com/asterxsk/eruditos
cp -r eruditos/study-guide ~/.claude/skills/study-guide
cp -r eruditos/professor   ~/.claude/skills/professor
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
```

## License

Not yet specified.
