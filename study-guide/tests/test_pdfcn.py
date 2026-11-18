import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pymupdf


SKILL = Path(__file__).resolve().parents[1]


class PdfcnThemeTests(unittest.TestCase):
    def test_pdfcn_renders_numbered_bands_with_bundled_font_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "guide.json"
            artwork = folder / "diagram.svg"
            artwork.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 30">'
                '<rect x="2" y="2" width="56" height="26" fill="#345678"/></svg>',
                encoding="utf-8",
            )
            source.write_text(json.dumps({
                "meta": {"title": "Memory systems"},
                "theme": "pdfcn",
                "mode": "full",
                "sections": [{
                    "title": "Cache",
                    "items": [
                        {"h2": "Why a cache saves time"},
                        {"p": "A cache holds frequently accessed memory blocks."},
                        {"h3": "Follow one access"},
                        {"p": "A hit reads the cached block."},
                        {"fig": {"file": artwork.name, "caption": "Original diagram.", "width": "30mm"}},
                    ],
                }],
            }), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SKILL / "build.py"), str(source), "--keep"],
                env=dict(os.environ, SF_PRO_DISPLAY_DIR=str(folder / "missing"), PYTHONIOENCODING="utf-8"),
                capture_output=True, encoding="utf-8", check=True,
            )
            self.assertIn("checks passed", result.stdout)
            copied, = (folder / "guide.build" / "figs").glob("*.svg")
            self.assertEqual(copied.read_bytes(), artwork.read_bytes())

            with pymupdf.open(source.with_suffix(".pdf")) as pdf:
                self.assertEqual(len(pdf), 2)
                self.assertIn("Contents", pdf[0].get_text())
                self.assertTrue(all(link["page"] == 1 for link in pdf[0].get_links()))
                self.assertTrue(any("Guide-Sans" in entry[3] for entry in pdf[0].get_fonts()))
                spans = [span for block in pdf[1].get_text("dict")["blocks"]
                         for line in block.get("lines", []) for span in line["spans"]]
                number = next(span for span in spans if span["text"].strip() == "1.1")
                self.assertEqual(number["color"], 0x1764C0)
                self.assertIn("Follow one access", pdf[1].get_text())
                self.assertIn("Original diagram.", pdf[1].get_text())
