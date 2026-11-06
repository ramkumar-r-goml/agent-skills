"""Tests for export_doc.py.

Logic tests use a fake pandoc, so they run anywhere. The classes marked skipUnless run the real
pipeline and only execute where pandoc, or a PDF engine, is installed.
"""
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib
from unittest import mock
from xml.dom import minidom

from support import SKILL, make_executable, run_main

import export_doc

ASSETS = os.path.join(SKILL, "assets", "pandoc")

STYLES = """<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults><w:rPrDefault><w:rPr><w:sz w:val="24" /></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="200" /></w:pPr></w:pPrDefault></w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal" /></w:style>
  <w:style w:type="paragraph" w:styleId="BodyText"><w:name w:val="Body Text" /><w:basedOn w:val="Normal" /><w:pPr><w:spacing w:before="180" /></w:pPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1" /><w:rPr><w:sz w:val="40" /></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title" /></w:style>
  <w:style w:type="character" w:styleId="VerbatimChar"><w:name w:val="Verbatim Char" /></w:style>
  <w:style w:type="table" w:default="1" w:styleId="Table"><w:name w:val="Table" /><w:tblPr><w:tblInd w:w="0" w:type="dxa" /></w:tblPr><w:tblStylePr w:type="firstRow"><w:tcPr><w:vAlign w:val="bottom"/></w:tcPr></w:tblStylePr></w:style>
</w:styles>
"""
DOCUMENT = """<?xml version="1.0" encoding="utf-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p /><w:sectPr><w:footnotePr><w:numRestart w:val="eachSect" /></w:footnotePr></w:sectPr></w:body></w:document>
"""
RELS = '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
TYPES = '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>'


def fake_base_docx(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/document.xml", DOCUMENT)
        z.writestr("word/_rels/document.xml.rels", RELS)
        z.writestr("[Content_Types].xml", TYPES)


FAKE_PANDOC = """#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
if "--version" in args:
    print("pandoc VERSION")
    sys.exit(0)
if "--to" in args and args[args.index("--to") + 1] == "plain":
    print("one two three four five")
    sys.exit(0)
with open(os.environ["FAKE_PANDOC_LOG"], "a") as fh:
    fh.write(json.dumps(args) + "\\n")
for a in args:
    if a.startswith("--log="):
        with open(a[6:], "w") as fh:
            fh.write(os.environ.get("FAKE_PANDOC_ENTRIES", "[]"))
if "--output" in args or "-o" in args:
    target = args[args.index("--output" if "--output" in args else "-o") + 1]
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    with open(target, "w") as fh:
        fh.write("output")
sys.exit(int(os.environ.get("FAKE_PANDOC_EXIT", "0")))
"""


class WithFakePandoc(unittest.TestCase):
    version = "3.13"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = self.tmp.name
        self.bin = os.path.join(self.dir, "bin")
        os.mkdir(self.bin)
        self.pandoc = os.path.join(self.bin, "pandoc")
        make_executable(self.pandoc, FAKE_PANDOC.replace("VERSION", self.version).replace("/usr/bin/env python3", sys.executable))
        self.log = os.path.join(self.dir, "calls.jsonl")
        env = {"PANDOC": self.pandoc, "FAKE_PANDOC_LOG": self.log, "PATH": self.bin}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        real_make_reference = mock.patch.object(export_doc, "make_reference", return_value=0)
        real_make_reference.start()
        self.addCleanup(real_make_reference.stop)
        self.doc = os.path.join(self.dir, "doc.md")
        self.write(self.doc, "# Title\n\n## One\n\nBody text here.\n")

    def write(self, path, text):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def export(self, *extra):
        return run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", os.path.join(self.dir, "out.docx")] + list(extra))

    def last_args(self):
        with open(self.log, encoding="utf-8") as fh:
            calls = [json.loads(ln) for ln in fh]
        return next(c for c in reversed(calls) if "--defaults" in c)


class ExportCommand(WithFakePandoc):
    def test_uses_the_defaults_file_and_the_gfm_reader(self):
        self.assertEqual(self.export()[0], 0)
        args = self.last_args()
        self.assertTrue(args[args.index("--defaults") + 1].endswith(os.path.join("defaults", "docx.yaml")))
        self.assertEqual(args[args.index("--from") + 1], "gfm")

    def test_lone_h1_becomes_the_title(self):
        self.export()
        self.assertIn("--shift-heading-level-by=-1", self.last_args())

    def test_two_h1s_are_left_alone(self):
        self.write(self.doc, "# A\n\ntext\n\n# B\n\ntext\n")
        self.export()
        self.assertNotIn("--shift-heading-level-by=-1", self.last_args())

    def test_front_matter_title_is_left_alone(self):
        self.write(self.doc, "---\ntitle: Real title\n---\n\n# A\n\ntext\n")
        self.export()
        self.assertNotIn("--shift-heading-level-by=-1", self.last_args())

    def test_h1_inside_a_code_block_does_not_count(self):
        self.write(self.doc, "# A\n\n```bash\n# a comment\n```\n")
        self.export()
        self.assertIn("--shift-heading-level-by=-1", self.last_args())

    def test_short_doc_gets_no_contents_and_long_doc_does(self):
        self.export()
        self.assertNotIn("--toc", self.last_args())
        self.write(self.doc, "# T\n\n" + "".join("## H%d\n\n%s\n\n" % (i, "word " * 300) for i in range(6)))
        self.export()
        self.assertIn("--toc", self.last_args())

    def test_toc_flag_overrides_auto(self):
        self.export("--toc", "yes")
        self.assertIn("--toc", self.last_args())

    def test_resource_path_lists_the_input_folder_and_working_directory(self):
        self.export()
        arg = next(a for a in self.last_args() if a.startswith("--resource-path="))
        self.assertEqual(arg, "--resource-path=" + os.pathsep.join([os.path.abspath(self.dir), os.getcwd()]))

    def test_inputs_are_relative_so_links_between_them_resolve(self):
        self.export()
        self.assertEqual(self.last_args()[-1], "doc.md")

    def test_metadata_flags(self):
        self.export("--title", "T", "--author", "A", "--author", "B", "--link-base", "https://x/y", "--mermaid", "off")
        args = self.last_args()
        for value in ("title=T", "author=A", "author=B", "doc-export-link-base=https://x/y", "doc-export-mermaid=off"):
            self.assertIn(value, args)

    def test_sandbox_is_passed_through(self):
        self.export("--sandbox")
        self.assertIn("--sandbox", self.last_args())

    def test_custom_reference_doc_skips_generation(self):
        ref = os.path.join(self.dir, "brand.docx")
        self.write(ref, "x")
        self.export("--reference-doc", ref)
        self.assertIn("--reference-doc=" + ref, self.last_args())
        export_doc.make_reference.assert_not_called()

    def test_default_output_name(self):
        code, out, _ = run_main(export_doc.main, ["export", self.doc, "--to", "html"])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.dir, "doc.html")))
        self.assertIn("doc.html", out)


class ExportProblems(WithFakePandoc):
    def test_missing_image_exits_4_and_names_it(self):
        entries = json.dumps([{"type": "CouldNotFetchResource", "verbosity": "WARNING", "resource": "img/x.png", "message": "nope"}])
        with mock.patch.dict(os.environ, {"FAKE_PANDOC_ENTRIES": entries}):
            code, _, err = self.export()
        self.assertEqual(code, 4)
        self.assertIn("img/x.png", err)

    def test_allow_warnings_turns_it_into_success(self):
        entries = json.dumps([{"type": "CouldNotFetchResource", "verbosity": "WARNING", "resource": "img/x.png"}])
        with mock.patch.dict(os.environ, {"FAKE_PANDOC_ENTRIES": entries}):
            self.assertEqual(self.export("--allow-warnings")[0], 0)

    def test_pandoc_failure_exits_1(self):
        with mock.patch.dict(os.environ, {"FAKE_PANDOC_EXIT": "43"}):
            self.assertEqual(self.export()[0], 1)

    def test_json_summary(self):
        code, out, _ = self.export("--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["format"], "docx")
        self.assertEqual(data["problems"], [])

    def test_bad_arguments_exit_2(self):
        self.assertEqual(run_main(export_doc.main, ["export", "nope.md", "--to", "docx"])[0], 2)
        self.assertEqual(run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", "x.pdf"])[0], 2)
        self.assertEqual(run_main(export_doc.main, ["export", self.doc, "--to", "pdf", "--reference-doc", self.doc])[0], 2)
        self.assertEqual(run_main(export_doc.main, ["import", "nope.docx", "-o", "x.md"])[0], 2)
        self.assertEqual(run_main(export_doc.main, ["import", self.doc, "-o", "x.txt"])[0], 2)

    def test_dry_run_runs_nothing_and_prints_the_command(self):
        code, out, _ = self.export("--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("--defaults", out)
        self.assertFalse(os.path.exists(self.log))


class PdfEngines(WithFakePandoc):
    def add_engine(self, name):
        make_executable(os.path.join(self.bin, name), "#!/bin/sh\nexit 0\n")

    def pdf(self, *extra):
        return run_main(export_doc.main, ["export", self.doc, "--to", "pdf", "-o", os.path.join(self.dir, "out.pdf")] + list(extra))

    def test_no_engine_exits_3_with_install_help_and_never_installs(self):
        code, _, err = self.pdf()
        self.assertEqual(code, 3)
        self.assertIn("No PDF engine", err)
        self.assertIn("typst", err.lower())
        self.assertIn("--to docx", err)

    def test_typst_is_preferred(self):
        self.add_engine("xelatex")
        self.add_engine("typst")
        self.assertEqual(self.pdf()[0], 0)
        self.assertTrue(self.last_args()[1].endswith("pdf-typst.yaml"))

    def test_falls_back_in_order(self):
        self.add_engine("xelatex")
        self.pdf()
        self.assertTrue(self.last_args()[1].endswith("pdf-xelatex.yaml"))

    def test_lualatex_overrides_the_engine_in_the_latex_defaults(self):
        self.add_engine("lualatex")
        self.pdf()
        args = self.last_args()
        self.assertTrue(args[1].endswith("pdf-xelatex.yaml"))
        self.assertIn("--pdf-engine=lualatex", args)

    def test_paper_size_is_set_once_for_typst(self):
        self.add_engine("typst")
        self.pdf("--paper", "letter")
        args = self.last_args()
        self.assertIn("papersize=us-letter", args)
        with open(args[1], encoding="utf-8") as fh:
            self.assertNotIn("papersize:", fh.read())

    def test_named_engine_that_is_missing_exits_3(self):
        self.add_engine("typst")
        code, _, err = self.pdf("--pdf-engine", "weasyprint")
        self.assertEqual(code, 3)
        self.assertIn("weasyprint is not installed", err)
        self.assertIn("Installed: typst", err)

    def test_dry_run_needs_no_engine(self):
        self.assertEqual(self.pdf("--dry-run")[0], 0)
        self.assertEqual(self.pdf("--dry-run", "--pdf-engine", "xelatex")[0], 0)


class MissingOrOldPandoc(unittest.TestCase):
    def test_missing_pandoc_exits_3_with_install_help(self):
        with mock.patch.dict(os.environ, {"PATH": "/nonexistent"}, clear=False):
            os.environ.pop("PANDOC", None)
            with tempfile.NamedTemporaryFile(suffix=".md") as f:
                code, _, err = run_main(export_doc.main, ["export", f.name, "--to", "docx", "-o", "/tmp/never.docx"])
        self.assertEqual(code, 3)
        self.assertIn("not installed", err)
        self.assertIn("Ask the user", err)

    def test_doctor_reports_without_failing(self):
        with mock.patch.dict(os.environ, {"PATH": "/nonexistent"}, clear=False):
            os.environ.pop("PANDOC", None)
            code, out, _ = run_main(export_doc.main, ["doctor", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertFalse(data["can_export"]["docx"])
        self.assertTrue(data["install"])


class OldPandoc(WithFakePandoc):
    version = "2.17.1"

    def test_too_old_exits_3(self):
        code, _, err = self.export()
        self.assertEqual(code, 3)
        self.assertIn("too old", err)


class TableFormatting(unittest.TestCase):
    TABLE = ('<w:tbl><w:tblPr><w:tblStyle w:val="Table" /><w:tblW w:type="auto" w:w="0" /><w:tblLook w:firstRow="1" /></w:tblPr>'
             '<w:tblGrid><w:gridCol w:w="100" /><w:gridCol w:w="100" /></w:tblGrid>'
             '<w:tr><w:trPr><w:tblHeader w:val="on" /></w:trPr><w:tc><w:tcPr /><w:p><w:r><w:t>Key</w:t></w:r></w:p></w:tc>'
             '<w:tc><w:tcPr /><w:p><w:r><w:rPr><w:rStyle w:val="VerbatimChar" /></w:rPr><w:t>Meaning</w:t></w:r></w:p></w:tc></w:tr>'
             '<w:tr><w:tc><w:tcPr /><w:p><w:r><w:t>a</w:t></w:r></w:p></w:tc><w:tc><w:tcPr /><w:p><w:r><w:t>%s</w:t></w:r></w:p></w:tc></w:tr></w:tbl>')

    def test_output_is_well_formed_and_ordered(self):
        out = export_doc._format_table(self.TABLE % ("long " * 30), 9000)
        minidom.parseString('<x xmlns:w="w">%s</x>' % out)
        self.assertLess(out.index("<w:tblW"), out.index("<w:tblBorders>"))
        self.assertLess(out.index("<w:tblBorders>"), out.index("<w:tblCellMar>"))
        self.assertLess(out.index("<w:tblCellMar>"), out.index("<w:tblLook"))

    def test_rstyle_stays_first_in_run_properties(self):
        out = export_doc._format_table(self.TABLE % "x", 9000)
        self.assertIn('<w:rPr><w:rStyle w:val="VerbatimChar" /><w:b /><w:bCs /></w:rPr>', out)
        self.assertIn("<w:r><w:rPr><w:b /><w:bCs /></w:rPr><w:t>Key</w:t>", out)

    def test_long_column_gets_more_width_within_the_page(self):
        out = export_doc._format_table(self.TABLE % ("long " * 30), 9000)
        widths = [int(w) for w in re.findall(r'<w:gridCol w:w="(\d+)"', out)]
        self.assertLessEqual(sum(widths), 9000)
        self.assertGreater(widths[1], widths[0] * 3)

    def test_merged_cells_are_left_alone(self):
        table = self.TABLE.replace("<w:tcPr />", '<w:tcPr><w:gridSpan w:val="2" /></w:tcPr>', 1)
        self.assertEqual(export_doc._format_table(table, 9000), table)


class ReferenceDoc(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = os.path.join(self.tmp.name, "base.docx")
        self.out = os.path.join(self.tmp.name, "out.docx")
        fake_base_docx(self.base)
        export_doc.build_reference(self.base, self.out, font="Arial", accent="0B6E4F", paper="letter")
        self.zip = zipfile.ZipFile(self.out)
        self.addCleanup(self.zip.close)

    def style(self, sid):
        xml = self.zip.read("word/styles.xml").decode()
        return re.search(r'<w:style\b[^>]*w:styleId="%s"[^>]*>(.*?)</w:style>' % sid, xml, re.S).group(1)

    def test_every_part_is_well_formed(self):
        for name in self.zip.namelist():
            minidom.parseString(self.zip.read(name))

    def test_fonts_and_color_apply(self):
        self.assertIn('w:ascii="Arial"', self.zip.read("word/styles.xml").decode())
        self.assertIn('w:val="0B6E4F"', self.style("Heading1"))

    def test_style_child_order_follows_the_schema(self):
        for sid in ("Heading1", "Title", "BodyText", "SourceCode", "Callout", "CalloutTitle"):
            tags = re.findall(r"<w:(name|basedOn|next|link|qFormat|pPr|rPr)\b", re.sub(r"<w:pPr>.*?</w:pPr>", "<w:pPr/>", self.style(sid), flags=re.S))
            tags = [t for t in tags if t in ("pPr", "rPr")]
            self.assertEqual(tags, sorted(tags), sid)

    def test_table_has_borders_and_a_header_fill(self):
        table = self.style("Table")
        self.assertIn("<w:tblBorders>", table)
        self.assertIn('w:fill="F2F2F2"', table)
        self.assertLess(table.index("<w:tblBorders>"), table.index("<w:tblStylePr"))

    def test_source_code_style_exists_so_pandoc_keeps_wrapping_on(self):
        self.assertIn('<w:name w:val="Source Code" />', self.style("SourceCode"))
        self.assertNotIn("wordWrap", self.style("SourceCode"))

    def test_page_setup_and_footer(self):
        doc = self.zip.read("word/document.xml").decode()
        self.assertIn('<w:pgSz w:w="12240" w:h="15840" />', doc)
        self.assertLess(doc.index("footerReference"), doc.index("footnotePr"))
        self.assertLess(doc.index("footnotePr"), doc.index("pgSz"))
        self.assertIn("xmlns:r=", doc)
        self.assertIn(" PAGE ", self.zip.read("word/footer1.xml").decode())
        self.assertIn('Target="footer1.xml"', self.zip.read("word/_rels/document.xml.rels").decode())
        self.assertIn("/word/footer1.xml", self.zip.read("[Content_Types].xml").decode())


class Assets(unittest.TestCase):
    def test_each_defaults_file_points_at_existing_files(self):
        for name in os.listdir(os.path.join(ASSETS, "defaults")):
            path = os.path.join(ASSETS, "defaults", name)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("from: gfm", text, name)
            for rel in re.findall(r"\$\{\.\}/([\w./-]+)", text):
                self.assertTrue(os.path.isfile(os.path.join(ASSETS, "defaults", rel)), "%s -> %s" % (name, rel))

    def test_every_engine_has_a_defaults_file(self):
        for _, defaults in export_doc.PDF_ENGINES:
            self.assertTrue(os.path.isfile(os.path.join(ASSETS, "defaults", defaults + ".yaml")))


SAMPLE = """# Payments design

Short intro with `inline code` and a [link to the repo file](../src/app.py) and [an external link](https://example.com/).

## Decision

> [!WARNING]
> This step deletes data.

| Option | Why not |
|---|---|
| Kafka | Too much to run |
| SQS | No replay of past events, which the search index rebuild needs on every deploy of the service |

```python
def f():
    return "a very long line of code that must wrap instead of running off the right edge of the page in Word"
```

<!-- pagebreak -->

## Rollout

1. First step.
2. Second step → with an arrow and text in 日本語.

![Latency chart](chart.png)
"""

def tiny_png():
    """Build a valid 1x1 PNG, enough for pandoc and Typst to embed."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff")) + chunk(b"IEND", b"")


PNG = tiny_png()


@unittest.skipUnless(shutil.which("pandoc"), "pandoc is not installed")
class RealPandoc(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = self.tmp.name
        self.doc = os.path.join(self.dir, "design.md")
        with open(self.doc, "w", encoding="utf-8") as fh:
            fh.write(SAMPLE)
        with open(os.path.join(self.dir, "chart.png"), "wb") as fh:
            fh.write(PNG)

    def plain(self, path):
        return subprocess.run(["pandoc", path, "--to", "plain", "--wrap=none", "--standalone"], capture_output=True, text=True).stdout

    def test_docx_end_to_end(self):
        out = os.path.join(self.dir, "out.docx")
        code, stdout, err = run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", out])
        self.assertEqual(code, 0, stdout + err)
        with zipfile.ZipFile(out) as z:
            for name in z.namelist():
                if name.endswith((".xml", ".rels")):
                    minidom.parseString(z.read(name))
            doc = z.read("word/document.xml").decode()
            styles = z.read("word/styles.xml").decode()
            self.assertTrue(any(n.startswith("word/footer") for n in z.namelist()), "footer carried over")
            self.assertTrue(any(n.startswith("word/media/") for n in z.namelist()), "image embedded")
        self.assertIn('w:val="CalloutTitle"', doc)
        self.assertIn('w:val="Callout"', doc)
        self.assertIn('<w:br w:type="page"', doc)
        self.assertIn('w:val="SourceCode"', doc)
        self.assertNotIn("wordWrap", re.search(r'w:styleId="SourceCode".*?</w:style>', styles, re.S).group(0))
        text = self.plain(out)
        self.assertIn("Payments design", text)
        self.assertIn("Too much to run", text)

    def test_tables_carry_direct_formatting_for_viewers_that_ignore_styles(self):
        out = os.path.join(self.dir, "out.docx")
        run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", out])
        with zipfile.ZipFile(out) as z:
            doc = z.read("word/document.xml").decode()
        table = re.search(r"<w:tbl>.*?</w:tbl>", doc, re.S).group(0)
        self.assertIn("<w:tblBorders>", table)
        self.assertIn('w:fill="F2F2F2"', table)
        self.assertIn("<w:cantSplit />", table)
        self.assertIn("<w:tblHeader", table)
        widths = [int(w) for w in re.findall(r'<w:gridCol w:w="(\d+)"', table)]
        self.assertEqual(len(widths), 2)
        self.assertGreater(widths[1], widths[0], "the column with long text gets more room")
        self.assertEqual(table.count('<w:tcW w:w="%d"' % widths[1]), 3)
        header = re.search(r"<w:tr\b.*?</w:tr>", table, re.S).group(0)
        self.assertIn("<w:b />", header)

    def test_own_reference_doc_keeps_control_of_tables(self):
        ref = os.path.join(self.dir, "brand.docx")
        run_main(export_doc.main, ["reference-doc", "-o", ref])
        out = os.path.join(self.dir, "out.docx")
        run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", out, "--reference-doc", ref])
        with zipfile.ZipFile(out) as z:
            self.assertNotIn("<w:tblBorders>", z.read("word/document.xml").decode())

    def test_docx_title_and_dead_link_handling(self):
        out = os.path.join(self.dir, "out.docx")
        code, stdout, err = run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", out, "--json"])
        self.assertEqual(code, 0, stdout + err)
        data = json.loads(stdout)
        self.assertTrue(any("../src/app.py" in n for n in data["notes"]), data)
        with zipfile.ZipFile(out) as z:
            doc = z.read("word/document.xml").decode()
            rels = z.read("word/_rels/document.xml.rels").decode()
        self.assertIn('w:val="Title"', doc)
        self.assertIn('w:val="Heading1"', doc)
        self.assertNotIn("src/app.py", rels)
        self.assertIn("https://example.com/", rels)

    def test_link_base_keeps_repo_links(self):
        out = os.path.join(self.dir, "out.docx")
        run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", out, "--link-base", "https://github.com/o/r/blob/main/docs"])
        with zipfile.ZipFile(out) as z:
            self.assertIn("https://github.com/o/r/blob/main/docs/../src/app.py", z.read("word/_rels/document.xml.rels").decode())

    def test_html_is_self_contained(self):
        out = os.path.join(self.dir, "out.html")
        code, stdout, err = run_main(export_doc.main, ["export", self.doc, "--to", "html", "-o", out])
        self.assertEqual(code, 0, stdout + err)
        with open(out, encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn("data:image/png;base64", html)
        self.assertIn("--accent", html)
        self.assertIn('class="warning"', html)
        self.assertIn('class="page-break"', html)
        self.assertIn("<title>Payments design</title>", html)

    def test_missing_image_is_reported(self):
        os.remove(os.path.join(self.dir, "chart.png"))
        code, _, err = run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", os.path.join(self.dir, "out.docx")])
        self.assertEqual(code, 4, err)
        self.assertIn("chart.png", err)

    def test_multiple_inputs_link_to_each_other(self):
        second = os.path.join(self.dir, "ops.md")
        with open(second, "w", encoding="utf-8") as fh:
            fh.write("# Operations\n\n## Roll back\n\nSteps.\n")
        with open(self.doc, "a", encoding="utf-8") as fh:
            fh.write("\nSee [the rollback steps](ops.md#roll-back).\n")
        out = os.path.join(self.dir, "out.html")
        code, stdout, err = run_main(export_doc.main, ["export", self.doc, second, "--to", "html", "-o", out, "--title", "Handover"])
        self.assertEqual(code, 0, stdout + err)
        with open(out, encoding="utf-8") as fh:
            self.assertRegex(fh.read(), r'href="#[^"]*roll-back"')

    def test_sandbox_blocks_embedding_local_files(self):
        secret = os.path.join(self.dir, "secret.txt")
        with open(secret, "w", encoding="utf-8") as fh:
            fh.write("do-not-leak")
        evil = os.path.join(self.dir, "evil.md")
        with open(evil, "w", encoding="utf-8") as fh:
            fh.write("# T\n\n![x](%s)\n" % secret)
        leaked = os.path.join(self.dir, "leaked.html")
        safe = os.path.join(self.dir, "safe.html")
        run_main(export_doc.main, ["export", evil, "--to", "html", "-o", leaked, "--allow-warnings"])
        run_main(export_doc.main, ["export", evil, "--to", "html", "-o", safe, "--allow-warnings", "--sandbox"])
        with open(leaked, encoding="utf-8") as fh:
            self.assertIn("data:", fh.read())
        with open(safe, encoding="utf-8") as fh:
            self.assertNotIn("data:text", fh.read())

    def test_same_input_gives_identical_word_files(self):
        first, second = os.path.join(self.dir, "1.docx"), os.path.join(self.dir, "2.docx")
        with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
            run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", first])
            run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", second])
        with open(first, "rb") as a, open(second, "rb") as b:
            self.assertEqual(a.read(), b.read())

    def test_import_docx_round_trip(self):
        docx = os.path.join(self.dir, "out.docx")
        run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", docx])
        md = os.path.join(self.dir, "back.md")
        code, stdout, err = run_main(export_doc.main, ["import", docx, "-o", md])
        self.assertEqual(code, 0, stdout + err)
        with open(md, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("## ", text.replace("\n# ", "\n## "))
        self.assertIn("Too much to run", text)
        self.assertTrue(os.path.isdir(os.path.join(self.dir, "back-media")))

    def test_mermaid_renders_with_alt_text_through_mmdc(self):
        stub = os.path.join(self.dir, "fake-mmdc")
        make_executable(stub, "#!%s\nimport sys\na = sys.argv\nopen(a[a.index('--output') + 1], 'wb').write(%r)\n" % (sys.executable, PNG))
        with open(self.doc, "a", encoding="utf-8") as fh:
            fh.write("\n```mermaid\nflowchart LR\n    accTitle: Orders flow\n    accDescr: The API writes to Postgres.\n    a --> b\n```\n")
        out = os.path.join(self.dir, "out.docx")
        with mock.patch.dict(os.environ, {"MERMAID_BIN": stub}):
            code, stdout, err = run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", out])
        self.assertEqual(code, 0, stdout + err)
        with zipfile.ZipFile(out) as z:
            doc = z.read("word/document.xml").decode()
        self.assertIn("Orders flow. The API writes to Postgres.", doc)
        self.assertNotIn("flowchart LR", doc)

    def test_mermaid_stays_as_code_without_mmdc(self):
        with open(self.doc, "a", encoding="utf-8") as fh:
            fh.write("\n```mermaid\nflowchart LR\n    a --> b\n```\n")
        out = os.path.join(self.dir, "out.docx")
        with mock.patch.dict(os.environ, {"MERMAID_BIN": "/nonexistent/mmdc"}):
            code, stdout, err = run_main(export_doc.main, ["export", self.doc, "--to", "docx", "-o", out])
        self.assertEqual(code, 0, stdout + err)
        self.assertIn("could not render Mermaid", err)
        with zipfile.ZipFile(out) as z:
            self.assertIn("flowchart", z.read("word/document.xml").decode())

    def test_reference_doc_command(self):
        out = os.path.join(self.dir, "brand.docx")
        code, stdout, err = run_main(export_doc.main, ["reference-doc", "-o", out, "--font", "Arial", "--accent", "#0B6E4F"])
        self.assertEqual(code, 0, stdout + err)
        with zipfile.ZipFile(out) as z:
            self.assertIn("0B6E4F", z.read("word/styles.xml").decode())


@unittest.skipUnless(shutil.which("pandoc") and shutil.which("typst"), "pandoc and typst are needed")
class RealTypst(unittest.TestCase):
    def test_pdf_with_unicode_alerts_tables_and_page_break(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        doc = os.path.join(tmp.name, "design.md")
        with open(doc, "w", encoding="utf-8") as fh:
            fh.write(SAMPLE)
        with open(os.path.join(tmp.name, "chart.png"), "wb") as fh:
            fh.write(PNG)
        out = os.path.join(tmp.name, "out.pdf")
        code, stdout, err = run_main(export_doc.main, ["export", doc, "--to", "pdf", "-o", out, "--json", "--allow-warnings"])
        self.assertEqual(code, 0, stdout + err)
        with open(out, "rb") as fh:
            self.assertEqual(fh.read(5), b"%PDF-")
        self.assertEqual(json.loads(stdout)["pdf_engine"], "typst")


if __name__ == "__main__":
    unittest.main()
