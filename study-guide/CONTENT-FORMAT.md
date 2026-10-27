# Content format

One YAML (or JSON) file is the whole input to `build.py`. It carries the content
and, optionally, the choices; everything else — theme assets, block rendering,
maths, contents page, PDF, delivery checks — the tool owns.

```bash
python build.py guide.yaml --theme cobalt --type qna --depth quick
python build.py guide.yaml                 # theme/type/depth read from the file
python build.py --example guide.yaml     # write a working sample to edit
```

Flags win over the file; the file wins over the defaults (`dark`, `default`, `full`). Output is `<content-stem>.pdf` next to the content file unless `-o`
is given.

## Top level

```yaml
meta:
  title: Operating Systems          # required in practice; the cover prints it
  subtitle: Everything from the twelve lectures.
  tag: CS 301 · Revision            # the small line above the title
  terminal:                         # the cover's terminal block; omit for none
    - cmd: python build.py guide.yaml --theme cobalt
      note: rebuilds this file
  contents_title: Contents          # optional, defaults to "Contents"
  contents_blurb: ...               # optional line under the contents heading

theme: cobalt                       # dark graphite cobalt obsidian paper sepia ice mono
type: qna                           # default | qna | code
depth: quick                        # full | quick

closing: Built from the lecture slides.   # optional closing line

sections:
  - tag: SCHEDULING
    title: CPU Scheduling
    blurb: The policies and the trade they make.
    items:
      - pts: [...]
```

Each section is one unit: an italic tag, an `h1`, a one-line blurb, then items.
The unit's top hairline is the only horizontal rule that opens a block.

## Items

Every item is a single-key mapping. A bare string is shorthand for `p:`.

| Key | Shape | Renders as |
|---|---|---|
| `p` | `"text"` | a paragraph |
| `h2` | `"Title"` | a ruled subheading |
| `h3` | `"Title"` | a plain subheading |
| `pts` | `["pointer", ...]` | hanging-indent pointer list (quick theory) |
| `math` | `{tex: "...", num: 1}` or `"..."` | centred display equation, inline SVG |
| `algo` | `{pin, title, steps: [...], cx}` | numbered algorithm card |
| `code` | `{file: a.c, lang: c, cx: "..."}` or `{text: "..."}` | code card |
| `work` | `{title, steps: [...]}` | open worked-example block |
| `fig` | `{file: img.png, caption: "..."}` | figure with a caption |
| `table` | `{head: [...], rows: [[...]], caption}` | hairline table |
| `note` | `{title, text}` | amber callout |
| `tip` | `{title, text}` | green callout |
| `qa` | see below | one numbered question item |
| `fn` | see below | one function, explained (code guide) |

`h2`, `h3` take a plain string. `text` in `note`/`tip` and every string inside
`pts`/`work` accepts the inline forms below.

### `qa`

```yaml
- qa:
    num: 4                 # optional - the tool numbers items in document order
    star: true             # optional - revision-priority star
    q:                     # one or more equivalent wordings
      - Why does round robin keep the queue fair?
      - Explain how round robin guarantees every process a turn.
    a: >
      Every ready process is served in **FIFO order** with a bounded
      **time quantum**, so the longest wait is the number of ready
      processes times the quantum.
    kw: [FIFO order, time quantum]   # bolded in the answer; ** ** also works
```

`q` may be a bare string when there is one wording. `kw` wraps the first
occurrence of each term in the answer; a term not found is reported.

**Code-lab item.** Give `file` (or `code.text`) instead of `a`; optional `out`
prints an "Expected output" card under the program, and `lang` sets the tag.

```yaml
- qa:
    q: Write a program that forks and prints from both processes.
    file: fork_demo.c
    lang: c
```

**Algorithm item.** Give `algo` instead of `a`; the card becomes the answer.

```yaml
- qa:
    q: State the steps fork() takes inside the kernel.
    algo:
      pin: Fork
      title: Creating a process
      steps:
        - Call fork(); the kernel copies the address space.
        - Check the return value.
      cx: O(1) system call
```

### `code`

`file` is resolved against the content file's directory, then `<dir>/code/`.
A file not found is an error, not a silent skip. `text` inlines the listing.

```yaml
- code:
    file: array_operations.c
    lang: c
    cx: Time complexity · O(n) scan · O(1) extra space
```

### `algo`

Steps get `Step 1: Start` / `Step N: Stop` bookends and are renumbered
automatically, with `Step 3` references inside the text bumped to match. A
listing that contains braces or semicolons is treated as code, not an algorithm,
and is left alone.

```yaml
- algo:
    pin: Traversal
    title: TRAVERSING AN ARRAY
    steps:
      - "[INITIALIZE] SET I = lower_bound"
      - Repeat Steps 1 and 2 until I = upper_bound.
    cx: O(n) time · O(1) extra space
```

## Inline markup

Available in every prose string, plus `table` cells and captions:

| Syntax | Result |
|---|---|
| `**term**` | bold accent keyword |
| `` `code` `` | monospace |
| `*emphasis*` | italic |
| `$O(n \log n)$` | inline maths, rendered to SVG |

Display maths goes in a `math` item, not inline.

## Guide types and what they allow

The tool rejects a block the chosen type does not carry, before rendering:

| Type | Sections may contain |
|---|---|
| `default` | `p pts h2 h3 math fig table note tip algo work code fn` |
| `qna` | `p pts h2 h3 math fig table note tip qa` |
| `code` | `p pts h2 h3 math fig table note tip algo code fn` |

`textbook` and `walkthrough` are accepted as aliases for `default`, and `qa` for
`qna`, so older content files keep building.

Pass `--lax` to downgrade those to warnings. Depth is not enforced the same
way — a long paragraph in quick mode is reported, not rejected.

### `fn` — the code guide's unit

```yaml
- fn:
    name: sort_ints
    sig: "void sort_ints(int *a, size_t n)"
    does: >
      Sorts n integers in place, ascending, using an iterative merge sort so the
      stack depth stays constant.
    args:
      - {name: a, type: "int *", desc: The array to sort, holding at least `n` elements.}
      - {name: n, type: size_t, desc: Element count; 0 and 1 return immediately.}
    returns: Nothing. The array is sorted in place.
    notes:
      - Stable, so equal keys keep their original order.
    cx: "Time complexity · O(n log n) all cases · O(n) extra space"
    code:
      text: |
        void sort_ints(int *a, size_t n) { ... }
      lang: c
```

`name` and `does` are the two that matter everywhere; `sig`, `args`, `returns`,
`notes`, `cx` and `code` fill in around them. An argument can be a bare string
when it needs no type column.

In **quick** mode `fn` keeps the signature, the description, the parameters and the
return value, and drops the body listing and the notes — the interface without the
implementation. In **full** mode the body is expected: the tool warns about a
function with no listing.

`code.text`, `code.file` and `code.lang` work exactly as they do for a top-level
`code` item. A nested listing's line limit is 95 characters rather than 105, because
the fn indent narrows the card.

Put the complexity line at the `fn` level, not inside `code` — a `cx` under `code` is
dropped, since the function's own line is the one that matters. `file` is resolved against the content file's directory, then
`<dir>/code/`.

## What the tool checks

Runs on every build unless `--no-check`:

- **Sparse pages** — under 72% full, excluding cover, contents and last page.
- **Margin seams** — a step between the margin and the content box, which is
  what the `@page` background bug looks like. Verified to catch a deliberately
  broken stylesheet.
- **Leaked markup** — escaped HTML entities, `None`, `Traceback`, raw LaTeX
  commands, and unrendered `$…$` with TeX inside.
- **Fonts** — warns if no bundled face reached page 1.

## Figures

`fig.file` is copied into the build directory and referenced by name, so the
path in the content file only has to resolve from the content file's directory.
Screenshots keep their own background and colour — do not recolour a diagram to
match a dark theme.
