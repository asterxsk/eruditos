---
name: assign-to-ai
description: Take a written assignment (lab manual, question sheet, worksheet) and complete it end to end — write the code, run it in the app the user names, screenshot the result, crop the screenshot to just the output, and paste each answer into their Word document under "Code:" and "Output:" headings with dark syntax-highlighted code. Use when someone asks to answer or fill in an assignment, lab manual, or question paper in Word.
argument-hint: "[assignment.docx]"
---

# assign-to-ai

Complete a written assignment inside the user's own Word document. For each
question: write the code, run it in the app they chose, screenshot the run, crop
to the output only, and paste code + screenshot into the document under `Code:`
and `Output:`.

You are a guest in a document someone else wrote. Read it before you touch it,
insert rather than rewrite, and back it up first.

## 1 · Ask the questions

Ask all of these in one plain message. Do not use question cards — the user
answers in prose. If an answer is a clear default from the document itself,
proceed on it and say so.

1. **Which app, and which language?** VS Code in C, Code::Blocks in C,
   RStudio in R, Matplotlib in a Python script, a Jupyter notebook — whatever
   they actually use. This decides how you run the code and what the screenshot
   will look like.
2. **Which Word document, and which questions in it?** The path, and the
   questions to answer (all of them, or a subset).
3. **Screenshot scope.** Confirm you are capturing the whole app window and
   cropping down to the terminal/output pane only.
4. **Anything else** — output style, specific inputs, the student's roll number
   if it needs to appear.

## 2 · Tell them to close Word

Word holds a lock and the edits will not land. Say plainly:

> Close `<file>.docx` in Word before I start — I cannot write to it while it is open.

Then wait for confirmation. If you save anyway, you may silently overwrite their
unsaved work, so never skip this.

## 3 · Read the document

Read the document first — this is why the skill exists. Use the WordCraft MCP if
it is available (`open_document`, `get_text`, `inspect_document`), otherwise
extract the text directly:

```bash
python -I -c "
import docx
for i, p in enumerate(docx.Document('ASSIGNMENT.docx').paragraphs):
    if p.text.strip(): print(i, repr(p.text[:100]))"
```

Note the exact paragraphs you will insert after, and the page furniture (a header
table, section headings, a faculty-evaluation table at the end). Copy the
document's own conventions: `O(n²)` with a real superscript beats `O(n^2)` if
that is what the tables already use.

Keep a pristine copy before any edit:

```bash
cp assignment.docx /tmp/assignment_backup.docx
```

## 4 · Write the code

One file per question, in the language they chose. Match the level of the
course: beginner code, short names, no comments, no cleverness. Compile and run
it before it goes anywhere near the document — the screenshot must show a real
run, and a wrong answer in a lab manual is worse than a slow one.

Put the project in its own working directory.

## 5 · Run it in their app and screenshot

The whole point is that the screenshot proves the code ran in the app they
actually use. Set up that app so a single action runs the file.

**VS Code.** Attach the folder, open the file, and add a build task to
`.vscode/tasks.json`:

```json
{ "version": "2.0.0", "tasks": [{
    "label": "run", "type": "shell",
    "command": "gcc ${fileBasenameNoExtension}.c -o ${fileBasenameNoExtension}.exe && .\\${fileBasenameNoExtension}.exe < in.txt",
    "options": { "shell": { "executable": "cmd.exe", "args": ["/d", "/c"] } },
    "problemMatcher": [],
    "presentation": { "reveal": "always", "panel": "new", "clear": true, "focus": true },
    "group": { "kind": "build", "isDefault": true } }] }
```

`Ctrl+Shift+B` then runs it with no terminal typing at all. Put the inputs in
`in.txt` and change the file per question.

**Screenshot without stealing focus.** Run `scripts/capture_app.py`. It
maximises the window, activates it, verifies `GetForegroundWindow` matches
before sending anything, and aborts with `FOCUSFAIL` rather than leak keystrokes
into an unrelated app — which is what happens when `SetForegroundWindow`
silently fails.

```bash
python -I scripts/capture_app.py --list                  # find the window
python -I scripts/capture_app.py --src task1_sort.c --out shot1.png
```

On a non-Windows machine, or an app this cannot drive, use whatever the platform
gives you (`screencapture -l` on macOS, `gnome-screenshot` on Linux) — but keep
the focus check. Never blind-type into a window you have not confirmed.

Re-shoot per question, with the right file open and the right inputs in `in.txt`,
so each screenshot matches its own answer.

## 6 · Crop to the output only

The image in the document should contain the output text and nothing else — no
tab bar, no editor, no sidebar, no status bar, no taskbar.

Locate the text band with the probe:

```bash
python -I scripts/docx_code_inserter.py --probe shot1.png --band 470 570
```

That prints an ink count per row and the columns that contain ink, which gives
you the crop box. Then eyeball it — crop, read the PNG back, and confirm the
first character is not clipped and no editor chrome survived. Iterate the box
until it is clean; this is the step people skip and regret.

## 7 · Insert into the document

Build a spec and let `scripts/docx_code_inserter.py` do the insertion. It
inserts *after* an anchor paragraph, never rewrites, and backs the document up
first.

```json
{
  "doc": "assignment.docx",
  "lang": "c",
  "image_width_in": 5.6,
  "blocks": [
    { "after": "State the time and space complexity of the algorithm.",
      "code": "task1_insertion_sort.c",
      "image": "shot1.png",
      "crop": [300, 505, 1015, 543] }
  ]
}
```

```bash
python -I scripts/docx_code_inserter.py --spec spec.json
```

Each block produces, after the anchor:

| | |
|---|---|
| *(blank)* | |
| **Code:** | bold, Times New Roman 12 |
| *(blank)* | |
| code | dark `#181818` background, Courier New 10, one paragraph per line, syntax coloured |
| *(blank)* | |
| **Output:** | bold, Times New Roman 12 |
| screenshot | cropped to the output only |

`lang` selects the keyword set (`c`, `python`, `r`, `plain`). All non-code text is
Times New Roman 12; only the `Code:` and `Output:` headings are bold.

Verify by rendering the pages — `render_page` in WordCraft, or convert to images
and look. Confirm every question has its code, its screenshot, and nothing
overlapping or clipped. If the anchor lookup fails the script prints the
document's short paragraphs so you can pick the right one.

## 8 · Hand it over and check

Tell them the file is ready and that a backup is alongside it. Ask directly
whether the result meets their standard — and expect the answer to be a change.
Re-running from the backup plus the spec is cheap; re-doing it by hand is not.

```bash
cp /tmp/assignment_backup.docx assignment.docx && python -I scripts/docx_code_inserter.py --spec spec.json
```

## 9 · Clean up

Keep the source files and the document; delete everything else.

```bash
python -I scripts/cleanup.py          # dry run, prints what would go
python -I scripts/cleanup.py --yes
```

It keeps `.c`/`.py`/`.R`/`.ipynb`/`.md` and the `.docx`, drops screenshots and
crops, binaries, `in.txt`, backups and editor scratch, and flags anything it
cannot classify instead of guessing. Never delete without showing the list first,
and never delete outside the assignment's working directory.

## Rules that keep this safe

- **Back up before writing.** Every path into the document starts from a copy.
- **Insert, never rewrite.** Anchor-based insertion after a paragraph the user
  wrote; nothing existing is touched.
- **Verify focus before sending keys.** A `FOCUSFAIL` abort is a success, not a
  failure. Typing into the wrong window is how you end up editing your own
  terminal.
- **Screenshot a real run.** Compile and execute first — never fabricate output.
- **Crop, then look at the crop.** Read the PNG back before it goes in.
- **Confirm before deleting.** Dry run, show the list, then `--yes`.
