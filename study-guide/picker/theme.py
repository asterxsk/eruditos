"""Generate the shared theme.css and the grain raster from a resolved design config.

Consumed by both the picker's browser preview and the WeasyPrint PDF build.

WeasyPrint 70.0 constraints enforced here (see .scratch/picker/research/weasyprint-css-support.md):
  - no comma inside a var() fallback (truncated silently)
  - the @page background is baked literally; origin/clip are ignored, so the
    content-box anchor is corrected with background-position
  - no color-mix(); mixes are computed here and emitted as hex
  - no mask-image; the grain density patch is baked into the raster
  - multi-layer @page background stays on the print path only
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required: pip install pillow") from exc

HERE = Path(__file__).resolve().parent
PRESETS = HERE / "presets"
FONTS = HERE / "fonts"
BASE_CSS = HERE / "base.css"

# ---- bundled font manifest: role-appropriate weights, per the vendored files ----
BUNDLED = {
    "Poppins": {"files": {600: "Poppins-600.woff2", 500: "Poppins-500.woff2"},
                "stack": '"Poppins", "Segoe UI", sans-serif'},
    "Guide Sans": {"files": {400: "Lato-400.woff2", 300: "Lato-300.woff2", 700: "Lato-700.woff2"},
                   "stack": '"Guide Sans", Georgia, serif'},
    "DejaVu Sans Mono": {"files": {400: "DejaVuSansMono-400.woff2", 700: "DejaVuSansMono-700.woff2"},
                         "stack": '"DejaVu Sans Mono", "Cascadia Mono", Consolas, monospace'},
    # Labels are set in serif italic, never in tracked mono capitals.
    "Guide Serif": {"files": {400: "GuideSerif-400.woff2"},
                    "stack": '"Guide Serif", Georgia, "Times New Roman", serif'},
}

# Label faces carry an italic cut; the manifest above only names roman files, so
# the italic is emitted separately rather than pretending weight 400 has both.
LABEL_ITALIC = "GuideSerif-400i.woff2"

LAYOUTS = {
    # scale multiplies the base type ramp and the vertical rhythm together
    "comfortable": {"scale": 1.08, "rhythm": 1.30},
    "normal":      {"scale": 1.00, "rhythm": 1.15},
    "compact":     {"scale": 0.92, "rhythm": 1.02},
}

# Page geometry. This is the single source of truth: the numbers are emitted into
# the @page rule AND used to compute the background-position shim, so the two can
# never disagree. WeasyPrint anchors an @page background image at the CONTENT box
# and ignores background-origin/background-clip (silently â€” see
# .scratch/picker/research/weasyprint-css-support.md 3.3). Left to itself the
# background spans only the text column and the margins fall back to the flat
# background-color. Every layer is therefore sized to the whole sheet and shifted
# back out by the margins via a negative background-position.
#
# The margins MUST be declared in the same @page rule. Without them WeasyPrint
# applies its own default (measured at ~19.8mm), the shift is short by the
# difference, and a strip along the left edge gets no grain at all.
PAGE = {"w": 210.0, "h": 297.0, "top": 19.0, "right": 15.0, "bottom": 22.0, "left": 15.0}


# --------------------------------------------------------------------------- #
# config resolution
# --------------------------------------------------------------------------- #
def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def resolve_config(per_guide: dict | None = None, repo_default: dict | None = None) -> dict:
    """library preset <- repo default <- per-guide config."""
    chosen = None
    name = None
    for layer in (per_guide, repo_default):
        if layer and layer.get("basedOn"):
            name = layer["basedOn"]
            break
    name = name or "dark"
    preset_file = PRESETS / f"{name}.json"
    if preset_file.exists():
        chosen = json.loads(preset_file.read_text(encoding="utf-8"))
    else:
        chosen = json.loads((PRESETS / "dark.json").read_text(encoding="utf-8"))
    if repo_default:
        chosen = _deep_merge(chosen, {k: v for k, v in repo_default.items() if k != "basedOn"})
    if per_guide:
        chosen = _deep_merge(chosen, {k: v for k, v in per_guide.items() if k != "basedOn"})
    return chosen


def _light_preset(name: str) -> dict:
    f = PRESETS / f"{name}.json"
    cfg = json.loads(f.read_text(encoding="utf-8"))
    return cfg["light"]


# --------------------------------------------------------------------------- #
# colour helpers (no color-mix in the output)
# --------------------------------------------------------------------------- #
def _parse_colour(c: str):
    c = c.strip()
    if c.startswith("#"):
        h = c[1:]
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        if len(h) == 8:
            h = h[:6]
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), 1.0
    if c.startswith("rgb"):
        inner = c[c.index("(") + 1:c.index(")")].replace("/", ",")
        parts = [p.strip() for p in inner.split(",")]
        rgb = tuple(int(round(float(p))) for p in parts[:3])
        a = float(parts[3]) if len(parts) > 3 else 1.0
        return rgb, a
    if c == "transparent":
        return (0, 0, 0), 0.0
    return (0, 0, 0), 1.0


def mix(a: str, b: str, t: float) -> str:
    """Precomputed replacement for CSS color-mix(in srgb, a (1-t), b t)."""
    (ar, ag, ab), aa = _parse_colour(a)
    (br, bg, bb), ba = _parse_colour(b)
    r = round(ar * (1 - t) + br * t)
    g = round(ag * (1 - t) + bg * t)
    bl = round(ab * (1 - t) + bb * t)
    al = aa * (1 - t) + ba * t
    if al >= 0.999:
        return f"#{r:02x}{g:02x}{bl:02x}"
    return f"rgba({r},{g},{bl},{al:.3f})"


# --------------------------------------------------------------------------- #
# grain raster: uniform field + baked density patch
# --------------------------------------------------------------------------- #
def make_grain(cfg: dict, out_path: Path, size: int = 220, seed: int = 7) -> None:
    """Write the grain tile.

    The tile is the uniform field. WeasyPrint cannot mask, so when the config
    names a density patch the patch is modelled by emitting a *second* image
    (see make_grain_patch) rather than by masking this one.
    """
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            a = max(0, min(26, int(rng.gauss(11, 6))))
            px[x, y] = (255, 255, 255, a)
            a = max(0, min(22, int(rng.gauss(9, 5))))
            px[x, y] = (0, 0, 0, a)
    img.save(out_path)


def make_grain_patch(cfg: dict, out_path: Path, w: int = 1240, h: int = 1754, seed: int = 11) -> None:
    """A page-sized grain layer with the density patch painted in.

    Grain is uniform everywhere; inside the patch radius the speckle count rises
    with `strength`, fading to the uniform field at the edge. This is the raster
    that replaces the CSS mask WeasyPrint cannot do, and it is what both the
    preview and the PDF show when a patch is set. A4 at ~150 dpi.
    """
    patch = (cfg.get("gradient") or {}).get("patch")
    if not patch:
        return
    rng = random.Random(seed)

    # uniform field: one 220px tile, pasted across the page (fast)
    tile = Image.new("RGBA", (220, 220))
    tpx = tile.load()
    for y in range(220):
        for x in range(220):
            tpx[x, y] = (255, 255, 255, max(0, min(26, int(rng.gauss(11, 6)))))
    img = Image.new("RGBA", (w, h))
    for ty in range(0, h, 220):
        for tx in range(0, w, 220):
            img.paste(tile, (tx, ty))   # no mask: copy the tile's RGBA directly
    px = img.load()

    # boost inside the patch, weighted by a smooth falloff
    cx, cy = patch["x"] * w, patch["y"] * h
    R = max(1.0, patch["radius"] * min(w, h))
    S = float(patch["strength"])
    count = int(w * h * 0.02 * max(0.0, S))
    for _ in range(count):
        ang = rng.uniform(0, 2 * math.pi)
        rad = R * math.sqrt(rng.random())
        x = int(cx + rad * math.cos(ang))
        y = int(cy + rad * math.sin(ang))
        if 0 <= x < w and 0 <= y < h:
            fall = 1.0 - rad / R
            a = max(0, min(240, int(rng.gauss(150, 45) * fall + rng.gauss(20, 8))))
            px[x, y] = (255, 255, 255, a)
    img.save(out_path)


# --------------------------------------------------------------------------- #
# CSS emission
# --------------------------------------------------------------------------- #
def _font_faces(cfg: dict) -> str:
    """@font-face for each role's family. A local family falls back to a bundled url."""
    lines = []
    for role in ("heading", "body", "code", "label"):
        spec = (cfg.get("fonts") or {}).get(role)
        if not spec:
            continue
        fam = spec["family"]
        if spec.get("source") == "local":
            stack = f'"{fam}", "Segoe UI", sans-serif'
            lines.append(f"/* {role}: local family {fam!r} - falls back to bundled if absent */")
            continue
        manifest = BUNDLED.get(fam)
        if not manifest:
            continue
        for weight, filename in sorted(manifest["files"].items()):
            lines.append(
                "@font-face {"
                f' font-family: "{fam}";'
                f' src: url("fonts/{filename}") format("woff2");'
                f" font-weight: {weight}; font-style: normal; font-display: swap; }}"
            )
    # the label role always ships an italic: kickers, tags and captions are set in it
    label_fam = (((cfg.get("fonts") or {}).get("label") or {}).get("family")
                 or "Guide Serif")
    if label_fam in BUNDLED and (FONTS / LABEL_ITALIC).exists():
        lines.append(
            "@font-face {"
            f' font-family: "{label_fam}";'
            f' src: url("fonts/{LABEL_ITALIC}") format("woff2");'
            f" font-weight: 400; font-style: italic; font-display: swap; }}"
        )
    return "\n".join(lines)


def _role_stack(cfg: dict, role: str) -> str:
    spec = (cfg.get("fonts") or {}).get(role) or {}
    fam = spec.get("family", "Guide Serif" if role == "label" else "Guide Sans")
    if spec.get("source") == "local":
        return f'"{fam}", "Segoe UI", sans-serif'
    default = "Guide Serif" if role == "label" else "Guide Sans"
    return BUNDLED.get(fam, BUNDLED[default])["stack"]


def _tokens(theme: dict) -> str:
    """The :root custom-property block. No commas inside var() fallbacks anywhere.

    base.css falls back to the dark palette on every token, so a missing key
    degrades gracefully rather than emitting an empty declaration.
    """
    t = theme
    code = t.get("code", {})
    g = t.get("gradient", {})
    accent = t["accent"]
    pairs = [
        ("--base", t["base"]),
        ("--grad-from", g.get("from", t["base"])),
        ("--grad-via", g.get("via", t["base"])),
        ("--grad-to", g.get("to", t["base"])),
        ("--grad-angle", f'{g.get("angle", 178)}deg'),
        ("--strong", t["strong"]),
        ("--text", t["text"]),
        ("--dim", t["dim"]),
        ("--faint", t["faint"]),
        ("--rule", t["rule"]),
        ("--rule-strong", t.get("ruleStrong", "rgba(255,255,255,0.11)")),
        ("--wash", t.get("wash", "rgba(255,255,255,0.035)")),
        ("--accent", accent),
        ("--accent-soft", t.get("accentSoft", _alpha(accent, 0.32))),
        ("--dim-soft", t.get("dimSoft", "rgba(150,160,175,0.40)")),
        ("--warn", t.get("warn", "#e0a856")),
        ("--warn-line", t.get("warnLine", "rgba(224,168,86,0.60)")),
        ("--ok", t.get("ok", "#78be96")),
        ("--ok-line", t.get("okLine", "rgba(120,190,150,0.60)")),
        ("--bad", t.get("bad", "#e08585")),
        ("--block-fill", t["blockFill"]),
        ("--code-fill", code.get("fill", "#0c0e12")),
        ("--code-text", code.get("text", "#cfd6de")),
        ("--code-keyword", code.get("keyword", accent)),
        ("--code-comment", code.get("comment", t["faint"])),
        ("--code-sel", code.get("selection", _alpha(accent, 0.22))),
    ]
    return ":root {\n" + "\n".join(f"  {k}: {v};" for k, v in pairs) + "\n}"


def _alpha(colour: str, a: float) -> str:
    """An rgba() of `colour` at alpha `a`, derived from whatever form it is in."""
    (r, g, b), _ = _parse_colour(colour)
    return f"rgba({r},{g},{b},{a})"


def _gradient_layers(t: dict) -> str:
    """The shape as literal CSS layers. No var() composition (invalid in WeasyPrint).

    A preset whose three stops are the same colour emits no layer at all: a
    full-page gradient is only invisible when it is flat, and any visible one
    makes each page look like a different sheet.
    """
    g = t.get("gradient", {})
    frm, via, to = g.get("from", t["base"]), g.get("via", t["base"]), g.get("to", t["base"])
    if frm.lower() == via.lower() == to.lower():
        return ""
    ang = g.get("angle", 178)
    return (f'linear-gradient({ang}deg, {frm} 0%, {via} 45%, {to} 100%)')


def emit_css(cfg: dict, theme_name: str, base_css: str | None = None) -> str:
    """The generated theme.css: static base + generated tokens + baked @page."""
    theme = cfg.get(theme_name) or cfg.get("dark") or {}
    if theme_name == "light" and isinstance(cfg.get("light"), dict) and "preset" in cfg["light"]:
        theme = _light_preset(cfg["light"]["preset"])
    layout = LAYOUTS.get(cfg.get("layout", "normal"), LAYOUTS["normal"])
    root = _tokens(theme)
    grad = _gradient_layers(theme)
    gtop = cfg.get("gradient") or {}
    patch = gtop.get("patch") or {}
    texture = gtop.get("texture", "none")
    use_patch = texture != "none" and float(patch.get("strength", 0) or 0) > 0
    # Sized to the whole sheet and shifted back out by the margins â€” see PAGE.
    # The `size`/`margin` declarations are not decoration: they are what the
    # shift compensates for, and omitting them resets WeasyPrint's own default
    # margins, which measured ~19.8mm and left an ungrain'd strip on the left.
    sheet = f'{PAGE["w"]:g}mm {PAGE["h"]:g}mm'
    if texture == "none":
        layers, sizes, repeats = [], [], []
    elif use_patch:
        layers, sizes, repeats = ['url("grain-patch.png")'], [sheet], ["no-repeat"]
    else:
        layers, sizes, repeats = ['url("grain.png")'], ["220px 220px"], ["repeat"]
    if grad:                      # a flat preset deliberately emits no gradient layer
        layers.append(grad)
        sizes.append(sheet)
        repeats.append("no-repeat")
    if layers:                    # an empty list would emit `background-size: ;`
        bg_line = f'  background-image: {", ".join(layers)};\n'
        bg_geom = (
            f'  background-size: {", ".join(sizes)};\n'
            f'  background-repeat: {", ".join(repeats)};\n'
            f'  background-position: {-PAGE["left"]:g}mm {-PAGE["top"]:g}mm;\n'
        )
    else:
        bg_line = bg_geom = ""
    page_bg = (
        f'  size: A4;\n'
        f'  margin: {PAGE["top"]:g}mm {PAGE["right"]:g}mm '
        f'{PAGE["bottom"]:g}mm {PAGE["left"]:g}mm;\n'
        f'  background-color: {theme["base"]};\n'
        + bg_line + bg_geom
    )
    faces = _font_faces(cfg)
    heading = _role_stack(cfg, "heading")
    body = _role_stack(cfg, "body")
    code = _role_stack(cfg, "code")
    label = _role_stack(cfg, "label")
    ramp = (
        f"  --type-scale: {layout['scale']};\n"
        f"  --rhythm: {layout['rhythm']};\n"
        f"  --font-heading: {heading};\n"
        f"  --font-body: {body};\n"
        f"  --font-code: {code};\n"
        f"  --font-label: {label};"
    )
    if base_css is None:
        base_css = BASE_CSS.read_text(encoding="utf-8")

    parts = [
        f"/* generated by theme.py - theme={theme_name} layout={cfg.get('layout','normal')} */",
        faces,
        root,
        ":root {\n" + ramp + "\n}",
        "@page {\n" + page_bg + "}",
        (base_css or "").strip(),
    ]
    return "\n\n".join(p for p in parts if p)


def _copy_fonts(cfg: dict, out_dir: Path) -> list[str]:
    """Copy every bundled woff2 the cfg's roles reference into <out>/fonts/.

    Without this the @font-face URLs 404 and the whole guide silently falls
    back to Georgia / Segoe UI â€” the page still renders, so the failure is
    invisible unless you read the embedded font names back out of the PDF.
    """
    import shutil

    dest = out_dir / "fonts"
    copied = []
    for role in ("heading", "body", "code", "label"):
        spec = (cfg.get("fonts") or {}).get(role) or {}
        if spec.get("source") == "local":
            continue                      # a local family is not ours to ship
        manifest = BUNDLED.get(spec.get("family"))
        if not manifest:
            continue
        for filename in manifest["files"].values():
            src = FONTS / filename
            if not src.exists():
                continue
            dest.mkdir(parents=True, exist_ok=True)
            target = dest / filename
            if not target.exists() or target.read_bytes() != src.read_bytes():
                shutil.copyfile(src, target)
            copied.append(f"fonts/{filename}")
    # the label italic is not in any manifest dict, so copy it explicitly
    label_fam = (((cfg.get("fonts") or {}).get("label") or {}).get("family")
                 or "Guide Serif")
    if label_fam in BUNDLED:
        src = FONTS / LABEL_ITALIC
        if src.exists():
            dest.mkdir(parents=True, exist_ok=True)
            target = dest / LABEL_ITALIC
            if not target.exists() or target.read_bytes() != src.read_bytes():
                shutil.copyfile(src, target)
            copied.append(f"fonts/{LABEL_ITALIC}")
    return copied


def build(cfg: dict, out_dir: Path, base_css: str | None = None) -> None:
    """Write theme.css and grain.png (plus grain-patch.png when a patch is set)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    theme_name = "light" if "light" in (cfg.get("themes") or []) and "dark" not in (cfg.get("themes") or []) else "dark"
    (out_dir / "theme.css").write_text(emit_css(cfg, theme_name, base_css), encoding="utf-8")
    make_grain(cfg, out_dir / "grain.png")
    make_grain_patch(cfg, out_dir / "grain-patch.png")
    _copy_fonts(cfg, out_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build assets from a bundled study-guide preset.")
    parser.add_argument("target", type=Path)
    parser.add_argument("--preset", required=True, choices=sorted(p.stem for p in PRESETS.glob("*.json")))
    args = parser.parse_args()
    cfg = json.loads((PRESETS / f"{args.preset}.json").read_text(encoding="utf-8"))
    build(cfg, args.target)
    print(f"wrote {args.preset} theme assets to {args.target}")
