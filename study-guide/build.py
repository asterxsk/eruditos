"""build.py - one command from a content file to a print-ready study-guide PDF.

The agent writes one YAML (or JSON) content file. This tool owns everything
else: the theme assets, every block renderer, the maths, the contents page, the
PDF, and the delivery checks. There is no per-guide Python to write.

    python build.py guide.yaml --theme paper --mode quick

Content file shape: see CONTENT-FORMAT.md next to this file, or run
`python build.py --example` to print a working sample.
"""

from __future__ import annotations

import argparse
import html
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
PICKER = HERE / "picker"
sys.path.insert(0, str(PICKER))

import theme as themes  # noqa: E402  (needs PICKER on sys.path)

THEMES = ("paper", "paperx", "obsidian")
MODES = ("full", "quick")
BLOCKS = {"h2", "h3", "p", "pts", "math", "fig", "table", "note", "tip",
          "theory", "algo", "work", "code"}

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

    def __init__(self, colour: str, display_size: float = 11.0):
        self.colour = colour
        self.display_size = display_size
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
                    f"${tex}$", str(tmp), prop=FontProperties(size=self.display_size if display else 10.2),
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


# Emphasis needs non-space on both sides of its markers. Without that, a C
# signature like `struct task *pick_next(struct rq *q)` parses as an emphasis
# span from the first `*` to the second, and `int **p` parses as a bold
# keyword. Code listings bypass this prose parser.
INLINE = re.compile(
    r"(`[^`]+`|\*\*(?!\s)[^*\n]+?(?<!\s)\*\*|\$[^$]+\$|\*(?!\s)[^*\n]+?(?<!\s)\*)"
)

# Spelling variants a content author may reasonably write. One table, used by
# both the type checker and the renderer, so the two can never disagree about
# what a block is called.
KIND_ALIASES = {
    "para": "p",
    "point": "pts",
    "points": "pts",
    "algorithms": "algo",
    "figures": "fig",
}


def normalise_kind(kind: str) -> str:
    return KIND_ALIASES.get(kind, kind)


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


def code_card(item: dict, base: Path, math: Math, label: str | None = None,
              limit: int = MAX_CODE_LINE) -> str:
    name = label or item.get("title") or (Path(item["file"]).name if item.get("file") else None) or item.get("lang") or "listing"
    lang = item.get("lang") or ""
    body = code_body(item, base)
    lines = body.splitlines() or [""]
    longest = max((len(line) for line in lines), default=0)
    if longest > limit:
        raise SystemExit(
            f"{name}: longest line is {longest} characters, limit is {limit}. "
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






def algo_card(item: dict, math: Math) -> str:
    pin = item.get("pin") or ""
    title = item.get("title") or ""
    steps = item.get("steps") or []
    if isinstance(steps, str):
        steps = steps.splitlines()
    prose = item.get("format") == "prose"
    if prose:
        body = '<ol class="algorithm-steps">' + "".join(
            f'<li>{inline(s, math)}</li>' for s in steps
        ) + '</ol>'
    else:
        body = "".join(f'<span class="step">{inline(s, math)}</span>' for s in steps)
    head = (f'<span class="pill">{html.escape(pin)}</span>{html.escape(title)}'
            if title else f'<span class="pill">{html.escape(pin)}</span>')
    cx = item.get("cx")
    cx_html = f'\n<div class="cx">{inline(cx, math)}</div>' if cx else ""
    head_html = f'<div class="card-h">{head}</div>' if pin or title else ""
    card_class = "card prose" if prose else "card"
    return (f'<div class="{card_class}">\n{head_html}\n'
            f'<div class="card-b">{body}</div>{cx_html}\n</div>')


# --------------------------------------------------------------------------- #
# function explanations (the code guide)
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# blocks
# --------------------------------------------------------------------------- #
def figure_name(path: Path) -> str:
    digest = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:16]
    return digest + path.suffix.lower()


def copy_figure(source: Path, dest: Path) -> None:
    if not source.is_file():
        raise SystemExit(f"figure not found: {source}")
    if source.suffix.lower() == ".svg":
        try:
            root = ET.parse(source).getroot()
        except ET.ParseError as exc:
            raise SystemExit(f"invalid SVG {source}: {exc}") from exc
        if root.tag.rsplit("}", 1)[-1] != "svg":
            raise SystemExit(f"not an SVG document: {source}")
        for node in root.iter():
            if node.tag.rsplit("}", 1)[-1] in ("script", "foreignObject"):
                raise SystemExit(f"SVG must be static (no scripts or HTML): {source}")
            for key, value in node.attrib.items():
                if key.rsplit("}", 1)[-1] == "href" and not value.startswith(("#", "data:")):
                    raise SystemExit(f"SVG must embed its resources: {source} references {value!r}")
    dest.mkdir(exist_ok=True)
    shutil.copyfile(source, dest / figure_name(source))


def render_block(item, math: Math, base: Path, paperx: bool = False) -> tuple[str, str]:
    """Return (block_name, html) for one content item."""
    if isinstance(item, str):
        return "p", f"<p>{inline(item, math)}</p>"
    if not isinstance(item, dict) or len(item) != 1:
        raise SystemExit(f"content item must be a single-key mapping, got: {item!r}")
    kind, val = next(iter(item.items()))
    kind = normalise_kind(kind)

    if kind == "theory":
        if not isinstance(val, dict):
            raise SystemExit("theory needs a mapping with paragraphs and/or points")
        parts = []
        for field in ("paragraphs", "points"):
            values = val.get(field) or []
            if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                raise SystemExit(f"theory.{field} must be a list of strings")
            if field == "paragraphs":
                parts += [f'<p>{inline(v, math)}</p>' for v in values]
            elif values:
                parts.append('<ul>' + ''.join(f'<li>{inline(v, math)}</li>' for v in values) + '</ul>')
        return kind, '<div class="theory">' + ''.join(parts) + '</div>'

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
        title = val.get("title") or ""
        steps = val.get("steps") or []
        rows = []
        for step in steps:
            if isinstance(step, dict):
                cls = f"cont {step['c']}" if step.get("c") else "cont"
                rows.append(f'<span class="{html.escape(cls)}">{inline(step.get("t", ""), math)}</span>')
            else:
                rows.append(f'<span class="cont">{inline(step, math)}</span>')
        title_html = f'<div class="work-h">{html.escape(str(title))}</div>' if title else ""
        return kind, (f'<div class="work">{title_html}'
                      f'<div class="work-b">{"".join(rows)}</div></div>')
    if kind in ("note", "tip"):
        title = val.get("title") or ""
        text = val.get("text") or val.get("html") or ""
        generic = str(title).strip().casefold() in ("", "note", "tip", "remember", "remember / exam tip")
        title_html = "" if generic else f'<div class="nt">{html.escape(str(title))}</div>'
        return kind, (f'<div class="{kind}">{title_html}'
                      f'<p>{inline(text, math)}</p></div>')
    if kind == "fig":
        src = val.get("file") or val.get("path")
        if not src:
            raise SystemExit("fig block needs 'file'")
        caption = val.get("caption") or ""
        cap = f'<div class="figcap">{inline(caption, math)}</div>' if caption else ""
        figure_styles = []
        if "width" in val:
            width = str(val["width"])
            match = re.fullmatch(r"(\d+(?:\.\d+)?)(%|mm)", width)
            if not match or float(match[1]) <= 0 or (match[2] == "%" and float(match[1]) > 100):
                raise SystemExit("fig.width must be a positive percentage up to 100% or millimetres, e.g. '90%' or '150mm'")
            figure_styles.append(f"width:{width}")
        if "max_height" in val:
            max_height = str(val["max_height"])
            match = re.fullmatch(r"(\d+(?:\.\d+)?)mm", max_height)
            if not match or not 0 < float(match[1]) <= 230:
                raise SystemExit("fig.max_height must be a positive millimetre length up to 230mm")
            figure_styles.append(f"max-height:{max_height}")
        style = f' style="{";".join(figure_styles)}"' if figure_styles else ""
        alt = str(val.get("alt") or caption)
        target = figure_name(base / src)
        return kind, (f'<div class="fig"><img src="figs/{target}"{style} '
                      f'alt="{html.escape(alt)}">{cap}</div>')
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
    raise SystemExit(f"unknown block type {kind!r}. Blocks: h2 h3 p pts math algo code work "
                     "fig table note tip theory")




# --------------------------------------------------------------------------- #
# document
# --------------------------------------------------------------------------- #


def contents_html(sections: list[dict], meta: dict, math: Math) -> str:
    rows = []
    for i, sec in enumerate(sections, 1):
        num = html.escape(str(sec.get("num") or f"{i:02d}"))
        title = inline(sec.get("title") or "", math)
        rows.append(f'<div class="contents-item chapter"><a class="toc" href="#u{num}">'
                    f'<span class="t">{title}</span></a></div>')
        topic = 0
        for item in sec.get("items") or []:
            if isinstance(item, dict) and len(item) == 1 and "h2" in item:
                topic += 1
                rows.append(f'<div class="contents-item topic"><a class="toc" href="#u{num}-t{topic}">'
                            f'<span class="n">{i}.{topic}</span>'
                            f'<span class="t">{inline(item["h2"], math)}</span></a></div>')
    return '<section class="contents"><h1>Contents</h1>' + ''.join(rows) + '</section>'


def unit_html(sec: dict, i: int, math: Math, base: Path, paperx: bool = False) -> str:
    num = html.escape(str(sec.get("num") or f"{i:02d}"))
    title = html.escape(str(sec.get("title") or ""))
    parts = []
    topic = 0
    for item in sec.get("items") or []:
        kind, rendered = render_block(item, math, base, paperx)
        if kind == "h2":
            topic += 1
            rendered = (f'<h2 class="sec" id="u{num}-t{topic}">'
                        f'<span class="topic-num">{i}.{topic}</span> {inline(item["h2"], math)}</h2>')
        elif paperx and kind in {"theory", "p", "pts", "fig", "math", "table", "note", "tip"}:
            rendered = f'<div class="px-block px-{kind}">{rendered}</div>'
        parts.append(rendered)
    return (f'<section class="unit" id="u{num}"><div class="unit-head">'
            f'<h1>{title}</h1></div>' + ''.join(parts) + '</section>')




# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a print-ready study-guide PDF from one content file.")
    parser.add_argument("content", type=Path, nargs="?",
                        help="content file (.yaml, .yml or .json)")
    parser.add_argument("--theme", choices=THEMES, help="preset theme")
    parser.add_argument("--mode", choices=MODES,
                        help="full: concise study guide; quick: selective revision essentials")
    parser.add_argument("-o", "--out", type=Path, help="output PDF (default: <content>.pdf)")
    parser.add_argument("--work", type=Path, help="build directory (default: <out>.build)")
    parser.add_argument("--keep", action="store_true", help="keep the build directory")
    parser.add_argument("--html", action="store_true", help="write doc.html and keep the build dir")
    parser.add_argument("--no-check", action="store_true",
                        help="skip the delivery checks (they run by default)")
    parser.add_argument("--example", nargs="?", const="-", metavar="PATH",
                        help="write a sample content file to PATH (or stdout) and exit")
    args = parser.parse_args(argv)

    if args.example:
        if args.example == "-":
            # stdout is cp1252 on a redirected Windows shell, which mangles the
            # middle dots and dashes in the sample; write UTF-8 bytes instead.
            sys.stdout.buffer.write(EXAMPLE.encode("utf-8"))
            sys.stdout.buffer.flush()
        else:
            Path(args.example).write_text(EXAMPLE, encoding="utf-8")
            print(f"wrote {args.example}")
        return 0
    if not args.content:
        parser.error("a content file is required (or use --example)")

    content_path = args.content.resolve()
    if not content_path.exists():
        raise SystemExit(f"no such content file: {content_path}")
    base = content_path.parent
    content = load_content(content_path)
    meta = content.get("meta") or {}

    if "type" in content or "depth" in content:
        raise SystemExit("Guide types and depth were removed. Delete type/depth and use mode: full or mode: quick.")

    theme_name = setting(content, args.theme, "theme", "paper")
    guide_mode = str(setting(content, args.mode, "mode", "full")).lower()
    for name, value, allowed in (("theme", theme_name, THEMES), ("mode", guide_mode, MODES)):
        if value not in allowed:
            raise SystemExit(f"{name} {value!r} is not one of {', '.join(allowed)}")

    sections = content["sections"]
    if not isinstance(sections, list):
        raise SystemExit("'sections' must be a list")
    section_ids = set()
    for index, section in enumerate(sections, 1):
        if not isinstance(section, dict):
            raise SystemExit(f"section {index} must be a mapping")
        section_id = str(section.get("num") or f"{index:02d}")
        if section_id in section_ids:
            raise SystemExit(f"duplicate section number {section_id!r}; omit num for global numbering")
        section_ids.add(section_id)

    # Validate content primitives; both modes support source-appropriate code and figures.
    for si, sec in enumerate(sections, 1):
        items = sec.get("items") or []
        if not isinstance(items, list):
            raise SystemExit(f"section {si}: items must be a list")
        for item in items:
            if isinstance(item, str):
                kind, val = "p", item
            elif isinstance(item, dict) and len(item) == 1:
                raw_kind, val = next(iter(item.items()))
                kind = normalise_kind(raw_kind)
            else:
                raise SystemExit(f"section {si}: each item must be a string or single-key mapping")
            if kind not in BLOCKS:
                raise SystemExit(f"section {si}: unsupported block {kind!r}; use topic prose, points, code, formulas or figures")
            if guide_mode == "quick" and kind in ("p", "theory"):
                paragraphs = val.get("paragraphs", []) if kind == "theory" and isinstance(val, dict) else [val]
                if any(len(str(paragraph)) > QUICK_PARA_LIMIT for paragraph in paragraphs):
                    print(f"warning: section {si}: quick mode should contain selective revision cues, not long prose", file=sys.stderr)

    # ---- assets ------------------------------------------------------------
    out_pdf = (args.out or content_path.with_suffix(".pdf")).resolve()
    work = (args.work or out_pdf.with_suffix(".build")).resolve()
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    cfg = json.loads((PICKER / "presets" / f"{theme_name}.json").read_text(encoding="utf-8"))
    themes.build(cfg, work)
    appearance = "light" if "light" in (cfg.get("themes") or []) and "dark" not in (cfg.get("themes") or []) else "dark"
    text_colour = cfg[appearance]["text"]
    math = Math(text_colour, display_size=14.0 if theme_name == "paperx" else 11.0)

    # figures are copied in so the build dir is self-contained and base_url works
    figs = work / "figs"
    for sec in sections:
        for item in sec.get("items") or []:
            if not (isinstance(item, dict) and len(item) == 1):
                continue
            raw_kind, val = next(iter(item.items()))
            if normalise_kind(raw_kind) != "fig" or not isinstance(val, dict):
                continue
            src = val.get("file") or val.get("path")
            if src:
                figs.mkdir(exist_ok=True)
                copy_figure(base / src, figs)

    paperx = theme_name == "paperx"
    body = [contents_html(sections, meta, math)]
    body += [unit_html(sec, i, math, base, paperx) for i, sec in enumerate(sections, 1)]

    document = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f'<title>{html.escape(str(meta.get("title", "Study guide")))}</title>\n'
        f'<link rel="stylesheet" href="theme.css">\n</head>\n<body data-theme="{theme_name}">\n'
        + "\n".join(body) + "\n</body>\n</html>\n"
    )
    document = math.resolve(document, work)
    (work / "doc.html").write_text(document, encoding="utf-8")

    from weasyprint import HTML
    rendered = HTML(str(work / "doc.html"), base_url=str(work) + "/").render()
    rendered.write_pdf(str(out_pdf))

    pages = _page_count(out_pdf)
    items = sum(len(sec.get("items") or []) for sec in sections)
    print(f"{out_pdf.name}: {pages} pages · {len(sections)} sections · {items} items · "
          f"{theme_name} · {guide_mode}")

    checks_ok = True
    if not args.no_check:
        first_unit = "u" + str(sections[0].get("num") or "01") if sections else None
        front_pages = next((i for i, page in enumerate(rendered.pages)
                            if first_unit in page.anchors), 1)
        checks_ok = run_checks(out_pdf, geometry=themes.page_geometry(cfg), front_pages=front_pages)
        if not checks_ok:
            print("checks reported problems above - the PDF was still written", file=sys.stderr)
    if not (args.keep or args.html):
        shutil.rmtree(work, ignore_errors=True)
    return 0 if checks_ok else 1


def _page_count(pdf: Path) -> int:
    try:
        import pymupdf
        return pymupdf.open(str(pdf)).page_count
    except Exception:  # noqa: BLE001
        return 0


# --------------------------------------------------------------------------- #
# delivery checks
# --------------------------------------------------------------------------- #
def run_checks(pdf: Path, geometry: dict | None = None, front_pages: int = 1) -> bool:
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
    geometry = geometry or themes.PAGE
    top = int(geometry["top"] / 25.4 * dpi)
    bottom = height - int(geometry["bottom"] / 25.4 * dpi)
    band = int(geometry["left"] / 25.4 * dpi)

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
        if frac < 0.72 and n > front_pages and n != len(files):
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
        # Stay immediately below the content box: PaperX has a running title
        # farther down in the left footer, which is ink rather than a seam.
        bottom_rows = (bottom + 2, min(bottom + 6, h - 4))
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
        # leak; this only fires on a matched pair with TeX inside it.
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


EXAMPLE = r"""# Author the content for the chosen mode before rendering.
#   python build.py guide.yaml --theme paperx --mode full
meta:
  title: Core Concepts
theme: paperx
mode: full
sections:
  - title: Demand
    items:
      - h2: Quantity demanded and demand
      - p: >
          **Quantity demanded** is the amount bought at a given price.
          A change in own price causes movement along the same demand curve.
          A change in another determinant, such as income, shifts the curve.
      - pts:
          - A price fall causes an extension along the curve.
          - An increase in demand shifts the curve to the right.
  - title: Code and Algorithms
    items:
      - h2: Squaring a number
      - p: Multiply the input by itself. The function returns the result.
      - code:
          title: square.c
          lang: c
          text: |
            int square(int n) {
                return n * n;
            }
"""

if __name__ == "__main__":
    sys.exit(main())
