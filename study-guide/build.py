"""build.py - one command from a content file to a print-ready study-guide PDF.

The agent writes one YAML (or JSON) content file. This tool owns everything
else: the theme assets, every block renderer, the maths, the contents page, the
PDF, and the delivery checks. There is no per-guide Python to write.

    python build.py guide.yaml --theme cobalt --type qa --depth quick

Content file shape: see CONTENT-FORMAT.md next to this file, or run
`python build.py --example` to print a working sample.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PICKER = HERE / "picker"
sys.path.insert(0, str(PICKER))

import theme as themes  # noqa: E402  (needs PICKER on sys.path)

THEMES = ("dark", "graphite", "cobalt", "obsidian", "paper", "sepia", "ice", "mono")
TYPES = ("textbook", "walkthrough", "qa")
DEPTHS = ("full", "quick")

# Blocks each guide type is allowed to carry. A textbook is information only;
# a walkthrough is solved problems; a QA guide is questions with answers.
ALLOWED = {
    "textbook": {"h2", "h3", "p", "pts", "math", "fig", "table", "note", "tip", "algo"},
    "walkthrough": {"h2", "h3", "p", "pts", "math", "fig", "table", "note", "tip",
                    "algo", "work", "code"},
    "qa": {"h2", "h3", "p", "pts", "math", "fig", "table", "note", "tip", "qa"},
}
# Blocks whose absence means the guide is not really that type.
EXPECTED = {"qa": "qa", "walkthrough": "work"}

MAX_CODE_LINE = 105       # 7.5pt DejaVu Mono in 180mm of text column
QUICK_PARA_LIMIT = 420    # a quick-mode paragraph longer than this is prose


# --------------------------------------------------------------------------- #
# content loading
# --------------------------------------------------------------------------- #
def load_content(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:  # pragma: no cover
            raise SystemExit("PyYAML is required for .yaml content: pip install pyyaml")
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            hint = ""
            if "unknown escape character" in str(exc):
                hint = ("\nTeX inside a double-quoted YAML string eats the backslash. "
                        "Use single quotes for any string containing LaTeX:\n"
                        "    - math: {tex: 'h \\leq \\log_2(n+1)', num: 2}")
            raise SystemExit(f"{path.name}: YAML did not parse{exc}{hint}")
    else:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path.name}: JSON did not parse\n{exc}")
    if not isinstance(data, dict) or "sections" not in data:
        raise SystemExit(f"{path.name}: expected a mapping with a 'sections' list")
    return data


def setting(content: dict, cli_value, key: str, default=None):
    """CLI wins, then the content file, then the default."""
    if cli_value not in (None, ""):
        return cli_value
    return content.get(key, default)


# --------------------------------------------------------------------------- #
# inline markup
# --------------------------------------------------------------------------- #
class Math:
    """Collects display and inline TeX and renders it to SVG in one batch."""

    def __init__(self, colour: str):
        self.colour = colour
        self.jobs: list[tuple[str, bool]] = []     # (tex, display)
        self.cache: dict[tuple[str, bool], str] = {}

    def placeholder(self, tex: str, display: bool) -> str:
        tex = tex.strip()
        if not tex:
            return ""
        key = (tex, display)
        if key not in self.cache:
            self.jobs.append(key)
            self.cache[key] = f"\x00MATH{len(self.cache)}\x00"
        return self.cache[key]

    def resolve(self, document: str, work: Path) -> str:
        if not self.cache:
            return document
        svgs = self._render(work)
        for (tex, display), token in self.cache.items():
            svg = svgs.get((tex, display))
            if svg is None:
                continue
            if display:
                markup = svg
            else:
                # Inline: drop the pt width/height so the CSS em size applies;
                # the viewBox keeps the aspect ratio. The wrapper span is what
                # sizes and baselines it - an unclassified <svg> inside a
                # paragraph takes the full text width and scales to the line.
                markup = re.sub(
                    r'(<svg[^>]*?)\s+width="[\d.]+pt"\s+height="[\d.]+pt"', r"\1", svg, count=1
                )
                markup = f'<span class="imath">{markup}</span>'
            document = document.replace(token, markup)
        return document

    def _render(self, work: Path) -> dict[tuple[str, bool], str]:
        jobs = list(self.cache)
        if _have_mathjax():
            try:
                return self._mathjax(jobs, work)
            except Exception as exc:  # noqa: BLE001 - fall back, don't die
                print(f"  mathjax failed ({exc}); falling back to matplotlib", file=sys.stderr)
        return self._matplotlib(jobs)

    def _mathjax(self, jobs, work: Path) -> dict:
        script = work / "_tex2svg.js"
        script.write_text(MATHJAX_JS, encoding="utf-8")
        payload = [
            {"tex": tex, "display": display, "out": f"eq{i}.svg"}
            for i, (tex, display) in enumerate(jobs)
        ]
        (work / "_jobs.json").write_text(json.dumps(payload), encoding="utf-8")
        env = {"NODE_PATH": str(_mathjax_root())}
        proc = subprocess.run(
            ["node", str(script), str(work / "_jobs.json"), self.colour],
            cwd=str(work), capture_output=True, text=True, env={**__import__('os').environ, **env},
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip()[:300] or "node exited nonzero")
        out = {}
        for i, key in enumerate(jobs):
            path = work / f"eq{i}.svg"
            if not path.exists() or path.stat().st_size < 200:
                raise RuntimeError(f"empty SVG for {key[0][:40]}")
            out[key] = path.read_text(encoding="utf-8")
        return out

    def _matplotlib(self, jobs) -> dict:
        import matplotlib
        matplotlib.use("Agg")
        matplotlib.rcParams["mathtext.fontset"] = "stix"
        matplotlib.rcParams["svg.fonttype"] = "path"
        from matplotlib import mathtext
        from matplotlib.font_manager import FontProperties

        out, failed = {}, []
        for tex, display in jobs:
            tmp = Path(tempfile.mkdtemp()) / "eq.svg"
            try:
                mathtext.math_to_image(
                    f"${tex}$", str(tmp), prop=FontProperties(size=11.0 if display else 10.2),
                    format="svg", dpi=300, color=self.colour,
                )
            except ValueError:
                failed.append(tex)
                continue
            s = tmp.read_text(encoding="utf-8")
            s = re.sub(r'<g id="patch_1">.*?</g>\s*', "", s, flags=re.S)
            s = s.replace("fill: #ffffff", "fill: none")
            out[(tex, display)] = s[s.index("<svg"):]
            shutil.rmtree(tmp.parent, ignore_errors=True)
        if failed:
            print("  these equations did not parse (mathtext is not LaTeX - "
                  "use \\leq not \\le, and avoid \\left/\\right):", file=sys.stderr)
            for tex in failed:
                print(f"    {tex}", file=sys.stderr)
            raise SystemExit(2)
        return out


_MATHJAX_ROOT_CACHE: list[Path | None] = []


def _mathjax_root() -> Path | None:
    if _MATHJAX_ROOT_CACHE:
        return _MATHJAX_ROOT_CACHE[0]
    candidates = [PICKER / "node_modules", HERE / "node_modules", Path.cwd() / "node_modules"]
    found = None
    for base in candidates:
        if (base / "mathjax-full").exists():
            found = base
            break
    if found is None:                      # try the global root once
        try:
            proc = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, timeout=20)
            root = Path(proc.stdout.strip())
            if (root / "mathjax-full").exists():
                found = root
        except Exception:  # noqa: BLE001
            found = None
    _MATHJAX_ROOT_CACHE.append(found)
    return found


def _have_mathjax() -> bool:
    return _mathjax_root() is not None


MATHJAX_JS = r"""
// tex2svg.js - batch LaTeX -> self-contained SVG. Run from the build directory.
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
const svg = new SVG({fontCache: 'local'});
const doc = mathjax.document('', {InputJax: tex, OutputJax: svg});
const COLOR = process.argv[3] || '#c8cfd8';
for (const j of JSON.parse(fs.readFileSync(process.argv[2], 'utf8'))) {
  const node = doc.convert(j.tex, {display: j.display !== false, em: 16, ex: 8, containerWidth: 80 * 16});
  let out = adaptor.outerHTML(adaptor.childNodes(node)[0]);
  out = out.replace(/currentColor/g, COLOR);
  fs.writeFileSync(j.out, out);
}
"""


INLINE = re.compile(r"(`[^`]+`|\*\*.+?\*\*|\$[^$]+\$|\*[^*\n]+\*)")


def inline(text: str, math: Math) -> str:
    """Escape, then apply the four inline forms the content file may use."""
    text = str(text)
    out, pos = [], 0
    for m in INLINE.finditer(text):
        out.append(html.escape(text[pos:m.start()], quote=False))
        tok = m.group(0)
        if tok[0] == "`":
            out.append(f"<code>{html.escape(tok[1:-1])}</code>")
        elif tok.startswith("**"):
            out.append(f'<strong class="keyword">{html.escape(tok[2:-2])}</strong>')
        elif tok[0] == "$":
            out.append(math.placeholder(tok[1:-1], display=False))
        else:
            out.append(f"<em>{html.escape(tok[1:-1])}</em>")
        pos = m.end()
    out.append(html.escape(text[pos:], quote=False))
    return "".join(out)


def keywordise(text: str, keywords) -> str:
    """Wrap the first occurrence of each marking keyword in ** ** for the parser."""
    if not keywords:
        return text
    if isinstance(keywords, str):
        keywords = [keywords]
    for kw in keywords:
        if not kw:
            continue
        if f"**{kw}**" in text:
            continue
        pattern = re.compile(rf"(?<![\w*]){re.escape(str(kw))}(?![\w*])")
        text, n = pattern.subn(f"**{kw}**", text, count=1)
        if n == 0:
            print(f"  keyword not found in answer: {kw!r}", file=sys.stderr)
    return text


# --------------------------------------------------------------------------- #
# code highlighting
# --------------------------------------------------------------------------- #
def highlight_code(text: str, lang: str | None, filename: str | None) -> str:
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import TextLexer, get_lexer_by_name, get_lexer_for_filename
        from pygments.util import ClassNotFound
    except ImportError:
        return html.escape(text, quote=False)
    lexer = None
    if lang:
        try:
            lexer = get_lexer_by_name(lang)
        except ClassNotFound:
            lexer = None
    if lexer is None and filename:
        try:
            lexer = get_lexer_for_filename(filename)
        except ClassNotFound:
            lexer = None
    return highlight(text, lexer or TextLexer(), HtmlFormatter(nowrap=True))


def code_body(item: dict, base: Path) -> str:
    if item.get("text"):
        return str(item["text"]).rstrip("\n")
    name = item.get("file") or item.get("path")
    if not name:
        raise SystemExit("code block needs 'text' or 'file'")
    path = Path(name)
    if not path.is_absolute():
        path = base / name
    if not path.exists():
        alt = base / "code" / name
        if alt.exists():
            path = alt
        else:
            raise SystemExit(f"code file not found: {name} (looked in {base} and {base / 'code'})")
    return path.read_text(encoding="utf-8").rstrip("\n")


def code_card(item: dict, base: Path, math: Math, label: str | None = None) -> str:
    name = label or item.get("file") or item.get("title") or item.get("lang") or "listing"
    lang = item.get("lang") or ""
    body = code_body(item, base)
    lines = body.splitlines() or [""]
    longest = max((len(line) for line in lines), default=0)
    if longest > MAX_CODE_LINE:
        raise SystemExit(
            f"{name}: longest line is {longest} characters, limit is {MAX_CODE_LINE}. "
            "Wrap it by hand before it reaches the PDF."
        )
    shown = highlight_code(body, item.get("lang"), item.get("file"))
    shown = shown.rstrip("\n")
    cx = item.get("cx")
    cx_html = f'\n<div class="cx">{inline(cx, math)}</div>' if cx else ""
    lang_tag = f'<span class="lang">{html.escape(lang)}</span>' if lang else ""
    return (
        f'<div class="code">\n'
        f'<div class="code-h"><span class="dots"><i></i><i></i><i></i></span>'
        f'<span class="name">{html.escape(name)}</span>{lang_tag}</div>\n'
        f'<pre>{shown}</pre>{cx_html}\n</div>'
    )


# --------------------------------------------------------------------------- #
# algorithms
# --------------------------------------------------------------------------- #
STEP_REF = re.compile(r"[Ss]teps? \d+(?:\s+(?:and|to)\s+\d+)*")
STEP_LEAD = re.compile(r"^\s*Step\s+\d+\s*[:.)-]\s*", re.I)


def bump_refs(text: str, offset: int) -> str:
    def rep(m):
        return re.sub(r"\d+", lambda d: str(int(d.group(0)) + offset), m.group(0))
    return STEP_REF.sub(rep, text)


def algo_steps(steps) -> list[str]:
    """Strip any source numbering, add the Start/Stop bookends, bump references."""
    if isinstance(steps, str):
        steps = [s for s in steps.splitlines() if s.strip()]
    steps = [STEP_LEAD.sub("", str(s)).strip() for s in steps if str(s).strip()]
    if not steps:
        return []
    # A pure code listing is not an algorithm: no bookends, no renumbering.
    if any(any(ch in s for ch in "{};") for s in steps):
        return steps
    bookended = (steps[0].lower().startswith("start")
                 and steps[-1].lower().startswith("stop"))
    if bookended:
        body = steps[1:-1]
        return ["Step 1: Start"] + [f"Step {i}: {s}" for i, s in enumerate(body, 2)] + \
               [f"Step {len(body) + 2}: Stop"]
    body = [bump_refs(s, 1) for s in steps]
    return (["Step 1: Start"]
            + [f"Step {i}: {s}" for i, s in enumerate(body, 2)]
            + [f"Step {len(body) + 2}: Stop"])


def algo_card(item: dict, math: Math) -> str:
    pin = item.get("pin") or "Algorithm"
    title = item.get("title") or ""
    steps = algo_steps(item.get("steps") or [])
    body = "".join(f'<span class="step">{inline(s, math)}</span>' for s in steps)
    head = (f'<span class="pill">{html.escape(pin)}</span>{html.escape(title)}'
            if title else f'<span class="pill">{html.escape(pin)}</span>')
    cx = item.get("cx")
    cx_html = f'\n<div class="cx">{inline(cx, math)}</div>' if cx else ""
    return (f'<div class="card">\n<div class="card-h">{head}</div>\n'
            f'<div class="card-b">{body}</div>{cx_html}\n</div>')


# --------------------------------------------------------------------------- #
# blocks
# --------------------------------------------------------------------------- #
def render_block(item, math: Math, base: Path) -> tuple[str, str]:
    """Return (block_name, html) for one content item."""
    if isinstance(item, str):
        return "p", f"<p>{inline(item, math)}</p>"
    if not isinstance(item, dict) or len(item) != 1:
        raise SystemExit(f"content item must be a single-key mapping, got: {item!r}")
    kind, val = next(iter(item.items()))
    kind = {"para": "p", "point": "pts", "points": "pts", "algo": "algo"}.get(kind, kind)

    if kind == "p":
        return kind, f"<p>{inline(val, math)}</p>"
    if kind == "h2":
        return kind, f'<h2 class="sec">{inline(val, math)}</h2>'
    if kind == "h3":
        return kind, f'<h3 class="sub">{inline(val, math)}</h3>'
    if kind == "pts":
        items = val if isinstance(val, list) else [val]
        body = "".join(f"<li>{inline(str(x), math)}</li>" for x in items)
        return kind, f'<ul class="pts">{body}</ul>'
    if kind == "math":
        if isinstance(val, dict):
            tex, num = val.get("tex", ""), val.get("num")
        else:
            tex, num = str(val), None
        num_html = f'<span class="eqn">({num})</span>' if num else ""
        return kind, f'<div class="eq">{math.placeholder(tex, display=True)}{num_html}</div>'
    if kind == "algo":
        return kind, algo_card(val, math)
    if kind == "code":
        return kind, code_card(val, base, math)
    if kind == "work":
        title = val.get("title") or "Worked example"
        steps = val.get("steps") or []
        rows = []
        for step in steps:
            if isinstance(step, dict):
                cls = f"cont {step['c']}" if step.get("c") else "cont"
                rows.append(f'<span class="{html.escape(cls)}">{inline(step.get("t", ""), math)}</span>')
            else:
                rows.append(f'<span class="cont">{inline(step, math)}</span>')
        return kind, (f'<div class="work"><div class="work-h">{html.escape(str(title))}</div>'
                      f'<div class="work-b">{"".join(rows)}</div></div>')
    if kind in ("note", "tip"):
        title = val.get("title") or ("Note" if kind == "note" else "Tip")
        text = val.get("text") or val.get("html") or ""
        return kind, (f'<div class="{kind}"><div class="nt">{html.escape(str(title))}</div>'
                      f'<p>{inline(text, math)}</p></div>')
    if kind == "fig":
        src = val.get("file") or val.get("path")
        if not src:
            raise SystemExit("fig block needs 'file'")
        caption = val.get("caption") or ""
        cap = f'<div class="figcap">{inline(caption, math)}</div>' if caption else ""
        return kind, (f'<div class="fig"><img src="figs/{html.escape(Path(src).name)}" '
                      f'alt="{html.escape(caption[:120])}">{cap}</div>')
    if kind == "table":
        head = val.get("head") or []
        rows = val.get("rows") or []
        thead = ""
        if head:
            thead = "<thead><tr>" + "".join(f"<th>{inline(c, math)}</th>" for c in head) + "</tr></thead>"
        body = "".join(
            "<tr>" + "".join(f"<td>{inline(c, math)}</td>" for c in row) + "</tr>" for row in rows
        )
        cap = val.get("caption")
        cap_html = f'<div class="cap">{inline(cap, math)}</div>' if cap else ""
        return kind, f'<table class="data">{thead}<tbody>{body}</tbody></table>{cap_html}'
    if kind == "qa":
        return kind, qa_block(val, math, base)
    raise SystemExit(f"unknown block type {kind!r}. Blocks: h2 h3 p pts math algo code work "
                     "fig table note tip qa")


def qa_block(val: dict, math: Math, base: Path) -> str:
    num = val.get("num", "")
    star = ' <span class="qa-star">★</span>' if val.get("star") else ""
    algo = val.get("algo")
    lab = bool(val.get("file") or val.get("code") or val.get("out"))

    if algo:
        # An algorithm answer: the task sentence, then the numbered card.
        qs = val.get("q") or val.get("questions") or [""]
        q = qs[0] if isinstance(qs, list) else qs
        return (f'<div class="qa qa-long">\n<div class="qa-num">{num}{star}</div>\n'
                f'<p class="q">{inline(q, math)}</p>\n'
                f'<div class="a">{algo_card(algo, math)}</div>\n</div>')

    if lab:
        # A code-lab item: one task sentence, then the program and its output.
        qs = val.get("q") or val.get("questions") or [""]
        q = qs[0] if isinstance(qs, list) else qs
        code = dict(val.get("code") or {})
        if not code:
            code = {"file": val.get("file"), "lang": val.get("lang"), "cx": val.get("cx")}
        inner = code_card(code, base, math)
        if val.get("out"):
            out_card = (f'<div class="code"><div class="code-h"><span class="dots"><i></i>'
                        f'<i></i><i></i></span><span class="name">Expected output</span>'
                        f'<span class="lang">console</span></div>'
                        f'<pre>{html.escape(str(val["out"]).rstrip())}</pre></div>')
            inner += "\n" + out_card
        return (f'<div class="qa qa-long">\n<div class="qa-num">{num}{star}</div>\n'
                f'<p class="q">{inline(q, math)}</p>\n<div class="a">{inner}</div>\n</div>')

    qs = val.get("q") or val.get("questions") or []
    if isinstance(qs, str):
        qs = [qs]
    asked = "".join(f'<p class="q">Q. {inline(q, math)}</p>\n' for q in qs)
    answer = keywordise(str(val.get("a") or val.get("answer") or ""), val.get("kw") or val.get("keywords"))
    long_cls = " qa-long" if len(answer) > 1100 else ""
    return (f'<div class="qa{long_cls}">\n<div class="qa-num">{num}{star}</div>\n{asked}'
            f'<div class="a">Ans. {inline(answer, math)}</div>\n</div>')


# --------------------------------------------------------------------------- #
# document
# --------------------------------------------------------------------------- #
def cover_html(meta: dict, math: Math) -> str:
    tag = meta.get("tag") or ""
    subtitle = meta.get("subtitle") or ""
    lines = meta.get("terminal") or []
    term = ""
    if lines:
        rows = []
        for line in lines:
            if isinstance(line, dict):
                cmd = html.escape(str(line.get("cmd", "")))
                note = line.get("note")
                tail = f' <span class="dim"># {html.escape(str(note))}</span>' if note else ""
                rows.append(f'<span class="ln cmd">{cmd}{tail}</span>')
            else:
                rows.append(f'<span class="ln">{html.escape(str(line))}</span>')
        term = f'<div class="term">{"".join(rows)}</div>'
    tag_html = f'<span class="cover-tag">{html.escape(str(tag))}</span>' if tag else ""
    sub_html = f'<div class="cover-sub">{inline(subtitle, math)}</div>' if subtitle else ""
    return (f'<section class="cover">\n{tag_html}'
            f'<h1 class="cover-title">{html.escape(str(meta.get("title", "Study guide")))}</h1>'
            f'{sub_html}{term}\n</section>')


def contents_html(sections: list[dict], meta: dict, math: Math) -> str:
    rows = []
    for i, sec in enumerate(sections, 1):
        num = str(sec.get("num") or f"{i:02d}")
        tag = sec.get("tag") or ""
        title = sec.get("title") or ""
        blurb = sec.get("blurb") or ""
        label = f"{tag} · {title}" if tag and title else (title or tag)
        rows.append(
            f'<div class="contents-item"><a class="toc" href="#u{num}">'
            f'<span class="n">{html.escape(num)}</span>'
            f'<span class="t">{inline(label, math)}</span>'
            f'<span class="d">{inline(blurb, math)}</span></a></div>'
        )
    heading = html.escape(str(meta.get("contents_title") or "Contents"))
    return ('<section class="contents">\n<div class="unit-head">'
            '<span class="unit-tag">Index</span>'
            f'<h1>{heading}</h1>'
            f'<p class="blurb">{inline(meta.get("contents_blurb", ""), math)}</p>'
            f'</div>\n{"".join(rows)}\n</section>')


def unit_html(sec: dict, i: int, math: Math, base: Path) -> str:
    num = str(sec.get("num") or f"{i:02d}")
    tag = sec.get("tag") or ""
    title = sec.get("title") or ""
    blurb = sec.get("blurb") or ""
    parts = []
    for item in sec.get("items") or []:
        parts.append(render_block(item, math, base)[1])
    blurb_html = f'<p class="blurb">{inline(blurb, math)}</p>' if blurb else ""
    tag_html = f'<span class="unit-tag">{html.escape(str(tag))}</span>' if tag else ""
    return (f'<section class="unit" id="u{html.escape(num)}">\n<div class="unit-head">'
            f'{tag_html}<h1>{html.escape(str(title))}</h1>{blurb_html}</div>\n'
            f'{"".join(parts)}\n</section>')


def number_items(sections: list[dict]) -> None:
    """Give every qa item a number, continuing across sections.

    Omitting `num` is the common case when the agent writes the content: the
    guide numbers items itself, once each, in document order.
    """
    n = 1
    for sec in sections:
        for item in sec.get("items") or []:
            if not (isinstance(item, dict) and len(item) == 1 and "qa" in item):
                continue
            qa = item["qa"]
            if not isinstance(qa, dict):
                continue
            if qa.get("num") in (None, ""):
                qa["num"] = n
                n += 1
            else:
                try:
                    n = int(re.sub(r"\D", "", str(qa["num"]))) + 1
                except ValueError:
                    n += 1


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a print-ready study-guide PDF from one content file.")
    parser.add_argument("content", type=Path, nargs="?",
                        help="content file (.yaml, .yml or .json)")
    parser.add_argument("--theme", choices=THEMES, help="preset theme")
    parser.add_argument("--type", dest="guide_type", choices=TYPES, help="textbook | walkthrough | qa")
    parser.add_argument("--depth", choices=DEPTHS, help="full | quick")
    parser.add_argument("-o", "--out", type=Path, help="output PDF (default: <content>.pdf)")
    parser.add_argument("--work", type=Path, help="build directory (default: <out>.build)")
    parser.add_argument("--keep", action="store_true", help="keep the build directory")
    parser.add_argument("--html", action="store_true", help="write doc.html and keep the build dir")
    parser.add_argument("--no-check", action="store_true",
                        help="skip the delivery checks (they run by default)")
    parser.add_argument("--lax", action="store_true", help="downgrade type-rule violations to warnings")
    parser.add_argument("--example", action="store_true", help="print a sample content file and exit")
    args = parser.parse_args(argv)

    if args.example:
        print(EXAMPLE)
        return 0
    if not args.content:
        parser.error("a content file is required (or use --example)")

    content_path = args.content.resolve()
    if not content_path.exists():
        raise SystemExit(f"no such content file: {content_path}")
    base = content_path.parent
    content = load_content(content_path)
    meta = content.get("meta") or {}

    theme_name = setting(content, args.theme, "theme", "dark")
    guide_type = setting(content, args.guide_type, "type", "textbook")
    depth = setting(content, args.depth, "depth", "full")
    for name, value, allowed in (("theme", theme_name, THEMES), ("type", guide_type, TYPES),
                                 ("depth", depth, DEPTHS)):
        if value not in allowed:
            raise SystemExit(f"{name} {value!r} is not one of {', '.join(allowed)}")

    sections = content["sections"]
    if not isinstance(sections, list):
        raise SystemExit("'sections' must be a list")

    # ---- rule checks before any rendering happens -------------------------
    allowed = ALLOWED[guide_type]
    problems, warnings = [], []
    counts: dict[str, int] = {}
    starred = qa_total = 0
    for si, sec in enumerate(sections, 1):
        for ii, item in enumerate(sec.get("items") or [], 1):
            if isinstance(item, str):
                kind = "p"
            elif isinstance(item, dict) and len(item) == 1:
                kind = next(iter(item))
            else:
                problems.append(f"section {si}: malformed item {item!r}")
                continue
            counts[kind] = counts.get(kind, 0) + 1
            if kind not in allowed:
                problems.append(
                    f"section {si} ({sec.get('title', '?')}): a '{kind}' block is not allowed in a "
                    f"{guide_type} guide. Allowed: {', '.join(sorted(allowed))}")
            if depth == "quick" and kind == "p":
                text = item.get("p") if isinstance(item, dict) else item
                if len(str(text)) > QUICK_PARA_LIMIT:
                    warnings.append(
                        f"section {si}: a paragraph is over {QUICK_PARA_LIMIT} characters in "
                        "quick mode - quick states pointers, not prose")
            if kind == "qa" and isinstance(item["qa"], dict):
                qa = item["qa"]
                wordings = qa.get("q") or qa.get("questions") or []
                if isinstance(wordings, str):
                    wordings = [wordings]
                # A code-lab or algorithm item is one task sentence by design.
                if not (qa.get("file") or qa.get("code") or qa.get("out") or qa.get("algo")):
                    if len(wordings) < 2:
                        warnings.append(
                            f"section {si}, item {ii}: {len(wordings)} wording(s) - a QA "
                            "item carries two or more ways of asking the same question")
                    if qa.get("star"):
                        starred += 1
                    qa_total += 1
    if qa_total and starred > max(2, qa_total // 3):
        warnings.append(
            f"{starred} of {qa_total} QA items are starred - a star means exam-likely, "
            "so starring most items says nothing")
    expected = EXPECTED.get(guide_type)
    if expected and not counts.get(expected):
        warnings.append(f"a {guide_type} guide with no '{expected}' blocks - is the type right?")
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if problems and not args.lax:
        raise SystemExit("content does not match the guide type; fix it or pass --lax")

    # ---- assets ------------------------------------------------------------
    out_pdf = (args.out or content_path.with_suffix(".pdf")).resolve()
    work = (args.work or out_pdf.with_suffix(".build")).resolve()
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    cfg = json.loads((PICKER / "presets" / f"{theme_name}.json").read_text(encoding="utf-8"))
    themes.build(cfg, work)
    mode = "light" if "light" in (cfg.get("themes") or []) and "dark" not in (cfg.get("themes") or []) else "dark"
    text_colour = cfg[mode]["text"]
    math = Math(text_colour)

    # figures are copied in so the build dir is self-contained and base_url works
    figs = work / "figs"
    for sec in sections:
        for item in sec.get("items") or []:
            if isinstance(item, dict) and "fig" in item:
                src = item["fig"].get("file") or item["fig"].get("path")
                if src:
                    figs.mkdir(exist_ok=True)
                    shutil.copyfile(base / src, figs / Path(src).name)

    body = [cover_html(meta, math), contents_html(sections, meta, math)]
    number_items(sections)
    body += [unit_html(sec, i, math, base) for i, sec in enumerate(sections, 1)]
    if content.get("closing"):
        body.append(f'<div class="end"><p>{inline(content["closing"], math)}</p></div>')

    document = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f'<title>{html.escape(str(meta.get("title", "Study guide")))}</title>\n'
        '<link rel="stylesheet" href="theme.css">\n</head>\n<body>\n'
        + "\n".join(body) + "\n</body>\n</html>\n"
    )
    document = math.resolve(document, work)
    (work / "doc.html").write_text(document, encoding="utf-8")

    from weasyprint import HTML
    HTML(str(work / "doc.html"), base_url=str(work) + "/").write_pdf(str(out_pdf))

    pages = _page_count(out_pdf)
    items = sum(len(sec.get("items") or []) for sec in sections)
    print(f"{out_pdf.name}: {pages} pages · {len(sections)} sections · {items} items · "
          f"{theme_name} · {guide_type} · {depth}")

    if not args.no_check:
        if not run_checks(out_pdf):
            print("checks reported problems above - the PDF was still written", file=sys.stderr)
    if not (args.keep or args.html):
        shutil.rmtree(work, ignore_errors=True)
    return 0


def _page_count(pdf: Path) -> int:
    try:
        import pymupdf
        return pymupdf.open(str(pdf)).page_count
    except Exception:  # noqa: BLE001
        return 0


# --------------------------------------------------------------------------- #
# delivery checks
# --------------------------------------------------------------------------- #
def run_checks(pdf: Path) -> bool:
    """Fill ratio, plus both background seams, measured on rasters of the PDF.

    The seam reference is the page's *modal* colour, not a column at the centre:
    on a page with a dark code card the centre column is code, and a reference
    taken there reports every margin as broken. Grain averages to the page tone,
    so the modal colour is the page background whatever sits on top of it.
    """
    try:
        import pymupdf
        from PIL import Image
    except ImportError:
        print("  checks need pymupdf and Pillow", file=sys.stderr)
        return False
    from collections import Counter

    pages = pymupdf.open(str(pdf))
    if not pages.page_count:
        print("  the PDF has no pages", file=sys.stderr)
        return False
    tmp = Path(tempfile.mkdtemp())
    dpi = 40
    for i, page in enumerate(pages, 1):
        page.get_pixmap(dpi=dpi).save(str(tmp / f"p-{i:02d}.png"))

    ok = True
    files = sorted(tmp.glob("p-*.png"))
    first = Image.open(files[0]).convert("L")
    width, height = first.size
    top = int(19 / 25.4 * dpi)
    bottom = height - int(22 / 25.4 * dpi)
    band = int(15 / 25.4 * dpi)             # the side margin

    sparse = []
    for f in files:
        n = int(f.stem.split("-")[1])
        img = Image.open(f).convert("RGB")
        px = img.load()
        # Per row, the page tone is read from the left margin at that exact
        # height and content is anything far from it. A single page-wide
        # reference cannot work: the background is a gradient, and a big card
        # can own the page's modal colour. This also works on light and dark
        # pages alike, where a fixed brightness cut only ever saw dark ones.
        last = top
        for y in range(top, bottom):
            band_px = [px[x, y] for x in range(2, max(3, band - 3), 2)]
            tone = tuple(sum(p[i] for p in band_px) // len(band_px) for i in range(3))
            for x in range(band, width - band, 3):
                if max(abs(c - t) for c, t in zip(px[x, y], tone)) > 14:
                    last = y
                    break
        frac = (last - top) / (bottom - top)
        # One gap is structural, not a fault: a code card cannot split, so a
        # listing pushed to the next page leaves its own page short. Report it,
        # do not fail the build over it.
        if frac < 0.72 and n not in (1, 2, len(files)):
            sparse.append((n, round(frac, 2)))
    if sparse:
        print(f"  warning: sparse pages (< 72% full): {sparse}", file=sys.stderr)

    for f in files:
        n = int(f.stem.split("-")[1])
        img = Image.open(f).convert("RGB")
        w, h = img.size
        px = img.load()

        def mode(x0, x1, y0, y1):
            counts = Counter()
            for y in range(y0, y1, 2):
                for x in range(x0, x1, 2):
                    r, g, b = px[x, y]
                    counts[(r // 3, g // 3, b // 3)] += 1
            (qr, qg, qb), _ = counts.most_common(1)[0]
            return (qr * 3 + 1, qg * 3 + 1, qb * 3 + 1)

        # The bug this catches is a *step* at the content-box boundary: the
        # margin keeps the flat background-color while the content box gets the
        # gradient and grain, so a hard band appears at x = 15mm or y = 19mm.
        # So compare just outside the boundary with just inside it, in rows or
        # columns that hold no content. Comparing two margins with each other
        # fails instead: the gradient is tilted, so left and right genuinely
        # differ by a few levels. And comparing a page-wide reference fails
        # because a big card can own the page's modal colour.
        inner = max(2, band - 3)

        def strip(x0, x1, y0, y1):
            vals = [px[x, y] for y in range(y0, y1, 2) for x in range(x0, x1, 2)]
            if not vals:
                return None
            return tuple(sum(v[i] for v in vals) // len(vals) for i in range(3))

        # content-free bands: the top margin, and the bottom margin left of
        # the page number
        top_rows = (4, max(5, top - 8))
        bottom_rows = (bottom + 8, h - 4)
        left_cols = (4, max(5, band - 8))
        right_cols = (w - band + 8, w - 4)

        checks = []
        for rows, where in ((top_rows, "top"), (bottom_rows, "bottom")):
            outside = strip(0, band - 2, *rows)
            inside = strip(band + 2, band + 12, *rows)
            if outside and inside:
                checks.append((f"{where} seam", outside, inside))
        for cols, where in ((left_cols, "left"), (right_cols, "right")):
            outside = strip(*cols, 0, top - 6)
            inside = strip(*cols, top + 4, top + 16)
            if outside and inside:
                checks.append((f"{where} seam", outside, inside))
        for label, outside, inside in checks:
            if max(abs(outside[i] - inside[i]) for i in range(3)) > 6:
                ok = False
                print(f"  page {n}: {label} steps from {outside} in the margin to "
                      f"{inside} inside the content box - the @page background is not "
                      "reaching the sheet edge", file=sys.stderr)
        _ = inner

    shutil.rmtree(tmp, ignore_errors=True)

    # ---- text leaks -------------------------------------------------------
    leaked = []
    for page in pages:
        text = page.get_text()
        for needle in ("&amp;", "&lt;", "&gt;", "None", "Traceback", "\x00"):
            if needle in text:
                leaked.append((page.number + 1, needle))
        for m in re.finditer(r"\\(frac|sum|begin|alpha|beta|gamma|log|varepsilon)", text):
            leaked.append((page.number + 1, m.group(0)))
        # Raw inline TeX that never reached the SVG pass. A lone `$` is not a
        # leak - the cover's terminal block prints a shell prompt - so this
        # only fires on a matched pair with TeX inside it.
        for m in re.finditer(r"\$([^$\n]{1,80})\$", text):
            if re.search(r"[\\^_{}]", m.group(1)):
                leaked.append((page.number + 1, m.group(0)[:30]))
    if leaked:
        ok = False
        print(f"  leaked markup or raw LaTeX: {sorted(set(leaked))[:8]}", file=sys.stderr)

    # ---- fonts actually embedded ------------------------------------------
    try:
        names = {f[3].split("+")[-1] for f in pages[0].get_fonts()}
        if not any("Guide" in n or "Poppins" in n or "DejaVu" in n for n in names):
            print(f"  warning: no bundled font in page 1 ({sorted(names)}) - "
                  "the theme's fonts may have fallen back", file=sys.stderr)
    except Exception:  # noqa: BLE001
        pass

    if ok:
        print("  checks passed")
    return ok


EXAMPLE = r"""# One YAML file is the whole input. Everything else is the tool's job.
#   python build.py guide.yaml --theme cobalt --type qa --depth quick
#
# meta, theme, type and depth can live here or arrive as CLI flags.


meta:
  title: Operating Systems
  subtitle: Everything from the twelve lectures, in the order it is examined.
  tag: CS 301 · Revision
  terminal:
    - cmd: python build.py guide.yaml --theme cobalt
      note: rebuilds this file
    - cmd: python build.py guide.yaml --depth full
      note: the long version

theme: cobalt
type: qa
depth: quick

sections:
  - tag: SCHEDULING
    title: CPU Scheduling
    blurb: The policies and the trade they make.
    items:
      - pts:
          - "**FCFS** — run to completion, convoy effect on long jobs"
          - "**Round robin** — time slice q, ready queue FIFO, O(1) dispatch"
          - "**Priority** — starvation is real; fix with ageing"
      - math:
          tex: W = \frac{1}{n} \sum_{i=1}^{n} w_i
          num: 1
      - qa:
          num: 1
          star: true
          q:
            - Why does round robin keep the ready queue fair?
            - Explain how round robin guarantees every process a turn.
            - What property of round robin prevents starvation?
          a: >
            Every ready process is served in **FIFO order** with a bounded
            **time quantum**, so the longest wait is the number of ready
            processes times the quantum.
          kw: [FIFO order, time quantum, starvation]

  - tag: SYSCALLS
    title: System Calls
    blurb: The boundary between user code and the kernel.
    items:
      - qa:
          num: 2
          q: Write a program that forks and prints from both processes.
          file: fork_demo.c
          lang: c
      - qa:
          num: 3
          q: State the steps fork() takes inside the kernel.
          algo:
            pin: Fork
            title: Creating a process
            steps:
              - Call fork(); the kernel copies the address space.
              - Check the return value, 0 in the child, child PID in the parent.
            cx: O(1) system call · O(n) copy on write
"""

if __name__ == "__main__":
    sys.exit(main())
