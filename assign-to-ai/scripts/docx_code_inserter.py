#!/usr/bin/env python3
"""Insert "Code:" / "Output:" blocks into a Word document.

Each block inserts, after an anchor paragraph:

    <blank>
    Code:                      (bold, Times New Roman 12)
    <blank>
    <code>                     (dark background, syntax highlighted)
    <blank>
    Output:                    (bold, Times New Roman 12)
    <image>                    (the cropped screenshot)

Usage:
    python -I docx_code_inserter.py --spec spec.json
    python -I docx_code_inserter.py --probe shot.png --band 470 570

Spec:
{
  "doc": "Lab_Manual.docx",
  "lang": "c",                     // c | python | r | plain
  "image_width_in": 5.6,
  "blocks": [
    {
      "after": "State the time and space complexity.",   // substring of the
                                                         // paragraph to insert after
      "code": "task1_insertion_sort.c",                  // file, or "text": "..."
      "image": "shot1.png",
      "crop": [300, 505, 1015, 543]                      // left, top, right, bottom
    }
  ]
}

Requires: python-docx, Pillow.
"""

import argparse
import json
import os
import shutil
import sys

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from PIL import Image

# ---------------------------------------------------------------- palette ----
# TextMate-flavoured dark palette, matched to a VS Code terminal theme.
PRE = "A8CC7C"      # preprocessor directive        (#include)
KW = "82D2CE"       # keywords, operators, [] type marker
NUM = "EBC88D"      # numeric literals
STR = "E394DC"      # string literals
PLAIN = "E4E4E4"    # default text, whitespace, call names, subscripts
IDENT = "D6D6DD"    # identifiers, punctuation
COM = "6A9955"      # comments

FILL = "181818"     # code block background
CODE_FONT = "Courier New"
CODE_HALF_PT = "20"  # w:sz is half-points -> 10pt
TEXT_FONT = "Times New Roman"
TEXT_PT = 12

KEYWORDS = {
    "c": {
        "int", "void", "if", "else", "while", "for", "return", "char", "float",
        "double", "long", "short", "unsigned", "signed", "struct", "union",
        "enum", "typedef", "static", "const", "do", "switch", "case", "default",
        "break", "continue", "goto", "sizeof", "extern", "register", "volatile",
    },
    "python": {
        "def", "class", "if", "elif", "else", "for", "while", "return", "import",
        "from", "as", "with", "try", "except", "finally", "lambda", "in", "is",
        "not", "and", "or", "pass", "break", "continue", "yield", "global",
        "nonlocal", "assert", "del", "raise", "None", "True", "False", "async",
        "await", "match",
    },
    "r": {
        "if", "else", "for", "while", "function", "return", "in", "next", "break",
        "repeat", "TRUE", "FALSE", "NULL", "NA", "Inf", "NaN", "library",
        "require", "source",
    },
    "plain": set(),
}

TWOCHAR = {"==", "!=", "<=", ">=", "++", "--", "+=", "-=", "*=", "/=",
           "<<", ">>", "<-", "->", "&&", "||"}


# ------------------------------------------------------------- highlighter ---
def push(out, color, text):
    if not text:
        return
    if out and out[-1][0] == color:
        out[-1][1] += text
    else:
        out.append([color, text])


def highlight(line, lang):
    """Return a list of (color, text) runs for one source line."""
    if lang == "plain":
        return [[PLAIN, line]]

    out = []
    n = len(line)
    i = 0
    kw = KEYWORDS[lang]
    comment_prefix = "#" if lang in ("python", "r") else None
    stmt = line.rstrip().endswith(";")
    calls = []
    after_include = False

    while i < n:
        c = line[i]

        if c == " ":
            j = i
            while j < n and line[j] == " ":
                j += 1
            push(out, PLAIN, line[i:j])
            i = j
            continue

        if c == "\t":
            push(out, PLAIN, "\t")
            i += 1
            continue

        if comment_prefix and c == comment_prefix:
            push(out, COM, line[i:])
            break

        if lang == "c" and c == "#":
            j = i + 1
            while j < n and (line[j].isalnum() or line[j] == "_"):
                j += 1
            push(out, PRE, line[i:j])
            after_include = True
            i = j
            continue

        if after_include and c == "<":
            j = line.find(">", i)
            j = n if j == -1 else j + 1
            push(out, STR, line[i:j])
            after_include = False
            i = j
            continue

        if c in "\"'":
            quote = c
            seg = i
            j = i + 1
            while j < n:
                if line[j] == "\\":
                    push(out, STR, line[seg:j])
                    push(out, IDENT, line[j:j + 2])
                    j += 2
                    seg = j
                elif line[j] == quote:
                    j += 1
                    break
                else:
                    j += 1
            push(out, STR, line[seg:j])
            i = j
            continue

        if c.isdigit():
            j = i
            while j < n and (line[j].isdigit() or line[j] == "."):
                j += 1
            push(out, NUM, line[i:j])
            i = j
            continue

        if c.isalpha() or c == "_" or c == ".":
            j = i
            while j < n and (line[j].isalnum() or line[j] in "_."):
                j += 1
            word = line[i:j]
            k = j
            while k < n and line[k] == " ":
                k += 1
            if word in kw:
                push(out, KW, word)
            elif lang == "c" and k < n and line[k] == "(" and k + 1 < n and line[k + 1] == ")":
                push(out, PLAIN, word)
                push(out, IDENT, "()")
                i = k + 2
                continue
            elif lang == "c" and k < n and line[k] == "(":
                push(out, PLAIN, word)
                push(out, PLAIN, "(")
                calls.append(len(out) - 1)
                i = k + 1
                continue
            else:
                push(out, IDENT, word)
            i = j
            continue

        if c == ")":
            col = PLAIN if (lang == "c" and calls and stmt) else IDENT
            if calls:
                calls.pop()
            push(out, col, ")")
            i += 1
            continue

        if lang == "c" and c == "[" and i + 1 < n and line[i + 1] == "]":
            push(out, KW, "[]")
            i += 2
            continue

        if lang == "c" and c in "[]":
            push(out, PLAIN, c)
            i += 1
            continue

        if c in "(){};,:":
            push(out, IDENT, c)
            i += 1
            continue

        two = line[i:i + 2]
        if two in TWOCHAR:
            push(out, KW if two != "&&" and two != "||" else IDENT, two)
            i += 2
            continue

        if c in "=+-*/<>%!&|^~":
            push(out, KW, c)
            i += 1
            continue

        push(out, IDENT, c)
        i += 1

    return out


# -------------------------------------------------------- docx primitives ----
def new_para_after(anchor):
    el = OxmlElement("w:p")
    anchor._p.addnext(el)
    return docx.text.paragraph.Paragraph(el, anchor._parent)


def text_par(anchor, text, bold=False):
    p = new_para_after(anchor)
    run = p.add_run(text)
    run.font.size = Pt(TEXT_PT)
    run.font.bold = bold
    rPr = run._r.get_or_add_rPr()
    rf = OxmlElement("w:rFonts")
    rf.set(qn("w:ascii"), TEXT_FONT)
    rf.set(qn("w:hAnsi"), TEXT_FONT)
    rf.set(qn("w:cs"), TEXT_FONT)
    rPr.insert(0, rf)
    return p


def code_par(anchor, code, lang):
    """One paragraph per source line. Returns the last inserted paragraph."""
    last = anchor
    for line in code.split("\n"):
        p = new_para_after(last)
        last = p

        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), FILL)

        sp = OxmlElement("w:spacing")
        sp.set(qn("w:after"), "0")
        sp.set(qn("w:line"), "270")
        sp.set(qn("w:lineRule"), "atLeast")

        prPr = OxmlElement("w:rPr")
        prf = OxmlElement("w:rFonts")
        prf.set(qn("w:ascii"), CODE_FONT)
        prf.set(qn("w:hAnsi"), CODE_FONT)
        prf.set(qn("w:cs"), CODE_FONT)
        prPr.append(prf)
        pc = OxmlElement("w:color")
        pc.set(qn("w:val"), PLAIN)
        prPr.append(pc)
        ps = OxmlElement("w:sz")
        ps.set(qn("w:val"), CODE_HALF_PT)
        prPr.append(ps)

        pPr.append(shd)
        pPr.append(sp)
        pPr.append(prPr)

        for color, text in highlight(line, lang):
            run = p.add_run()
            run.font.size = Pt(int(CODE_HALF_PT) / 2)
            rPr = run._r.get_or_add_rPr()
            rf = OxmlElement("w:rFonts")
            rf.set(qn("w:ascii"), CODE_FONT)
            rf.set(qn("w:hAnsi"), CODE_FONT)
            rf.set(qn("w:cs"), CODE_FONT)
            rPr.insert(0, rf)
            col = OxmlElement("w:color")
            col.set(qn("w:val"), color)
            rPr.append(col)
            run.add_text(text)
    return last


def find(doc, needle):
    for p in doc.paragraphs:
        if needle in p.text:
            return p
    return None


# ------------------------------------------------------------------ probe ----
def probe(path, band):
    """Print the ink row profile of a horizontal band, to locate a crop box."""
    grey = Image.open(path).convert("L")
    lo, hi = band
    hi = min(hi, grey.height)
    import numpy as np
    a = np.array(grey)[lo:hi, :].astype(int)
    rows = (a > 90).sum(axis=1)
    cols = (a > 90).sum(axis=0)
    xs = [i for i, v in enumerate(cols) if v > 0]
    for i, v in enumerate(rows):
        print(lo + i, v)
    print("columns with ink:", (xs[0], xs[-1]) if xs else None)


# ------------------------------------------------------------------- main ----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec")
    ap.add_argument("--probe")
    ap.add_argument("--band", nargs=2, type=int, default=[0, 100])
    args = ap.parse_args()

    if args.probe:
        probe(args.probe, args.band)
        return

    if not args.spec:
        ap.error("--spec is required (or use --probe)")

    spec = json.load(open(args.spec, encoding="utf-8"))
    doc_path = spec["doc"]
    lang = spec.get("lang", "c")
    width_in = spec.get("image_width_in", 5.6)

    if not os.path.exists(doc_path):
        sys.exit("document not found: " + doc_path)
    shutil.copyfile(doc_path, doc_path + ".bak")

    doc = docx.Document(doc_path)
    headings = "\n".join(
        "  " + repr(p.text.strip()[:70])
        for p in doc.paragraphs
        if p.text.strip() and len(p.text.strip()) < 90
    )

    for blk in spec["blocks"]:
        anchor = find(doc, blk["after"])
        if anchor is None:
            sys.exit("anchor not found: %r\n\nnote-length paragraphs:\n%s"
                     % (blk["after"], headings))

        code = blk.get("code_text")
        if code is None:
            code = open(blk["code"], encoding="utf-8").read().rstrip("\n")

        p = text_par(anchor, "")
        p = text_par(p, "Code:", bold=True)
        p = text_par(p, "")
        p = code_par(p, code, lang)
        p = text_par(p, "")
        p = text_par(p, "Output:", bold=True)

        image = blk.get("image")
        if image:
            crop = blk.get("crop")
            if crop:
                out = os.path.splitext(image)[0] + "_crop.png"
                Image.open(image).crop(tuple(crop)).save(out)
                image = out
            pic = new_para_after(p)
            pic.add_run().add_picture(image, width=Inches(width_in))

    doc.save(doc_path)
    print("written:", doc_path, "| backup:", doc_path + ".bak")


if __name__ == "__main__":
    main()
