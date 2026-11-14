import importlib.util
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

import yaml

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL))
import assemble

spec = importlib.util.spec_from_file_location("guide_build", SKILL / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class PaperXContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(data), encoding="utf-8")

    def fragments(self, numbers=None):
        for i, name in enumerate(("one", "two")):
            chapter = self.base / name
            (chapter / "assets").mkdir(parents=True)
            (chapter / "code").mkdir()
            (chapter / "assets" / "figure.svg").write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40"><text x="5" y="20">{name}</text></svg>')
            (chapter / "code" / "example.py").write_text(f'print("{name}")')
            section = {"title": name, "items": [
                {"fig": {"file": "assets/figure.svg", "caption": name}},
                {"code": {"file": "example.py", "lang": "python"}}]}
            if numbers:
                section["num"] = numbers[i]
            self.write(chapter / "chapter.yaml", {"sections": [section]})
        manifest = self.base / "manifest.yaml"
        self.write(manifest, {"theme": "paperx", "chapters": ["two/chapter.yaml", "one/chapter.yaml"]})
        return manifest

    def test_order_and_local_paths_survive_assembly(self):
        result = assemble.assemble(self.fragments())
        self.assertEqual([s["title"] for s in result["sections"]], ["two", "one"])
        for section in result["sections"]:
            fig, code = section["items"]
            self.assertEqual(Path(fig["fig"]["file"]).read_text().count(section["title"]), 1)
            self.assertEqual(Path(code["code"]["file"]).parent.name, "code")
            self.assertIn(section["title"], Path(code["code"]["file"]).read_text())

    def test_same_basename_figures_do_not_overwrite(self):
        result = assemble.assemble(self.fragments())
        dest = self.base / "copied"
        math = build.Math("#171717")
        for section in result["sections"]:
            fig = section["items"][0]
            source = Path(fig["fig"]["file"])
            build.copy_figure(source, dest)
            markup = build.render_block(fig, math, self.base)[1]
            self.assertIn(build.figure_name(source), markup)
        self.assertEqual(len(list(dest.iterdir())), 2)
        self.assertNotEqual(*[p.read_bytes() for p in dest.iterdir()])

    def test_duplicate_section_identifiers_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate section number"):
            assemble.assemble(self.fragments(numbers=[1, 1]))

    def test_absolute_code_path_is_not_printed(self):
        result = assemble.assemble(self.fragments())
        code = result["sections"][0]["items"][1]["code"]
        rendered = build.code_card(code, self.base, build.Math("#171717"))
        self.assertIn("example.py", rendered)
        self.assertNotIn(str(self.base), rendered)
        rendered = build.code_card(dict(code, title="Chosen label"), self.base, build.Math("#171717"))
        self.assertIn("Chosen label", rendered)

    def test_invalid_or_nonportable_svg_is_not_silently_copied(self):
        source = self.base / "bad.svg"
        dest = self.base / "figs"
        for markup in ('<svg><text>0 < 1</text></svg>',
                       '<svg><script>doSomething()</script></svg>',
                       '<svg><image href="https://example.com/chart.png"/></svg>'):
            source.write_text(markup)
            with self.assertRaises(SystemExit):
                build.copy_figure(source, dest)

    def test_new_blocks_escape_prose_and_enforce_shape(self):
        math = build.Math("#171717")
        rendered = build.render_block({"theory": {"paragraphs": ["x < y"], "points": ["**Term**"]}}, math, self.base)[1]
        self.assertIn("x &lt; y", rendered)
        self.assertIn('<strong class="keyword">Term</strong>', rendered)
        for item in ({"theory": {"points": "not a list"}}, {"exam": {"rows": [["one cell"]]}},
                     {"fig": {"file": "chart.svg", "width": "101%"}}):
            with self.assertRaises(SystemExit):
                build.render_block(item, math, self.base)
        generic = {"note": {"title": "Remember", "text": "Keep the condition."}}
        custom = {"note": {"title": "Assumption", "text": "Keep the condition."}}
        self.assertNotIn('class="nt"', build.render_block(generic, math, self.base, paperx=True)[1])
        self.assertIn("Assumption", build.render_block(custom, math, self.base, paperx=True)[1])
        self.assertNotIn('class="nt"', build.render_block(generic, math, self.base)[1])

    def test_removed_blocks_and_types_do_not_remain_as_hidden_modes(self):
        for kind in ("qa", "qna", "question", "answer", "fn", "function", "explain", "exam"):
            with self.assertRaises(SystemExit):
                build.render_block({kind: {}}, build.Math("#171717"), self.base)
        for key in ("type", "depth"):
            source = self.base / "old.yaml"
            self.write(source, {key: "full", "sections": []})
            result = subprocess.run([sys.executable, str(SKILL / "build.py"), str(source)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mode: full", result.stderr)

    def test_steps_and_headings_are_not_artificially_added(self):
        math = build.Math("#171717")
        markup = build.algo_card({"steps": ["Read n", "Return n squared"]}, math)
        self.assertNotIn("Start", markup)
        self.assertNotIn("Stop", markup)
        self.assertNotIn("Algorithm", markup)
        markup = build.render_block({"work": {"steps": ["2 × 2 = 4"]}}, math, self.base)[1]
        self.assertNotIn("Worked example", markup)
        markup = build.render_block({"work": {"title": "Squaring two", "steps": ["2 × 2 = 4"]}}, math, self.base)[1]
        self.assertIn("Squaring two", markup)

    def test_only_full_and_quick_are_cli_modes(self):
        result = subprocess.run([sys.executable, str(SKILL / "build.py"), "--help"],
                                capture_output=True, text=True)
        self.assertIn("--mode {full,quick}", result.stdout)
        self.assertNotIn("--type", result.stdout)
        self.assertNotIn("--depth", result.stdout)
        self.assertNotIn("--lax", result.stdout)
        for flag in ("--type", "--depth"):
            result = subprocess.run([sys.executable, str(SKILL / "build.py"), flag, "full"],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)

    def test_pdf_has_contents_only_and_both_chapters_figures(self):
        import pymupdf

        content = assemble.assemble(self.fragments())
        content["meta"] = {"title": "Cover title must be absent", "contents_blurb": "No preliminary blurb"}
        source = self.base / "guide.yaml"
        self.write(source, content)
        result = subprocess.run([sys.executable, str(SKILL / "build.py"), str(source)],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("checks passed", result.stdout)
        with pymupdf.open(source.with_suffix(".pdf")) as doc:
            text = ''.join(page.get_text() for page in doc)
            self.assertNotIn("Cover title must be absent", text)
            self.assertNotIn("No preliminary blurb", text)
            self.assertNotIn(str(self.base), text)
            self.assertIn("Contents", doc[0].get_text())
            self.assertTrue(all(link["page"] >= 1 for link in doc[0].get_links()))
            body = ''.join(page.get_text() for page in list(doc)[1:])
            self.assertGreaterEqual(body.count("two"), 3)
            self.assertGreaterEqual(body.count("one"), 3)


if __name__ == "__main__":
    unittest.main()
