"""Checks every skill in skills/ against the Agent Skills spec and this repo's own rules."""
import ast
import os
import re
import unittest

from support import ROOT, SKILL

import slop_scan

SKILLS_DIR = os.path.join(ROOT, "skills")
ALLOWED_FIELDS = {"name", "description"}  # Other fields are legal, but some agents ignore them.
AGENT_SPECIFIC = re.compile(r"\b(?:Bash tool|Read tool|Edit tool|Write tool|Glob tool|Grep tool|TodoWrite|mcp__\w+)\b")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def skill_dirs():
    return [os.path.join(SKILLS_DIR, d) for d in sorted(os.listdir(SKILLS_DIR)) if os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md"))]


def parse(path):
    text = read(path)
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, "%s has no frontmatter" % path
    return m.group(1), text[m.end():]


class Spec(unittest.TestCase):
    def test_there_is_at_least_one_skill(self):
        self.assertTrue(skill_dirs())

    def test_frontmatter(self):
        for d in skill_dirs():
            front, _ = parse(os.path.join(d, "SKILL.md"))
            fields = set(re.findall(r"^([a-z-]+):", front, re.M))
            self.assertTrue(fields <= ALLOWED_FIELDS, "%s: extra fields %s" % (d, fields - ALLOWED_FIELDS))
            name = re.search(r"^name:\s*(\S+)", front, re.M).group(1)
            self.assertRegex(name, r"^[a-z0-9]+(-[a-z0-9]+)*$")
            self.assertLessEqual(len(name), 64)
            self.assertEqual(name, os.path.basename(d))
            self.assertNotRegex(name, r"anthropic|claude")
            desc = re.search(r"^description:\s*(.*)$", front, re.M | re.S).group(1).strip().strip("'\"")
            self.assertTrue(0 < len(desc) <= 1024, "description is %d characters" % len(desc))
            self.assertNotIn("<", desc)
            self.assertIn("Use when", desc)

    def test_body_budget(self):
        for d in skill_dirs():
            _, body = parse(os.path.join(d, "SKILL.md"))
            self.assertLess(body.count("\n"), 500)
            # The spec recommends under 5,000 tokens. About 3.8 characters per token for this text.
            self.assertLess(len(body) / 3.8, 5000)

    def test_no_agent_specific_tool_names(self):
        for d in skill_dirs():
            for dp, _, fn in os.walk(d):
                for f in fn:
                    if f.endswith(".md"):
                        self.assertIsNone(AGENT_SPECIFIC.search(read(os.path.join(dp, f))), os.path.join(dp, f))


class Packaging(unittest.TestCase):
    def test_no_test_data_ships_with_a_skill(self):
        for d in skill_dirs():
            self.assertFalse(os.path.exists(os.path.join(d, "evals")), "%s/evals would install into users' projects" % d)
            for dp, _, fn in os.walk(d):
                for f in fn:
                    self.assertFalse(f == ".env" or f.endswith((".pyc", ".docx", ".pdf")), os.path.join(dp, f))


class ThisSkill(unittest.TestCase):
    def setUp(self):
        _, self.body = parse(os.path.join(SKILL, "SKILL.md"))

    def test_every_path_in_skill_md_exists(self):
        paths = set(re.findall(r"`((?:references|scripts|assets)/[\w./-]+)`", self.body))
        self.assertTrue(paths)
        for rel in paths:
            self.assertTrue(os.path.exists(os.path.join(SKILL, rel.rstrip("/"))), rel)

    def test_paths_in_references_exist(self):
        root = os.path.join(SKILL, "references")
        for dp, _, fn in os.walk(root):
            for f in fn:
                text = read(os.path.join(dp, f))
                for rel in re.findall(r"`((?:references|scripts|assets)/[\w./-]+\.\w+)`", text):
                    self.assertTrue(os.path.exists(os.path.join(SKILL, rel)), "%s: %s" % (f, rel))

    def test_every_reference_file_is_reachable_from_skill_md(self):
        root = os.path.join(SKILL, "references")
        for dp, _, fn in os.walk(root):
            for f in fn:
                rel = os.path.relpath(os.path.join(dp, f), SKILL).replace(os.sep, "/")
                self.assertIn("`%s`" % rel, self.body, "%s is never mentioned, so an agent cannot find it" % rel)

    def test_every_script_is_listed(self):
        for f in os.listdir(os.path.join(SKILL, "scripts")):
            if f.endswith(".py") and f != "doclib.py":
                self.assertIn("`scripts/%s`" % f, self.body)

    def test_long_references_have_contents(self):
        root = os.path.join(SKILL, "references")
        for dp, _, fn in os.walk(root):
            for f in fn:
                text = read(os.path.join(dp, f))
                if text.count("\n") > 100:
                    self.assertIn("Contents", text[:800], f)

    def test_doc_type_files_stay_small(self):
        root = os.path.join(SKILL, "references", "types")
        for f in os.listdir(root):
            self.assertLess(read(os.path.join(root, f)).count("\n"), 120, f)

    def test_the_skill_passes_its_own_scanner(self):
        targets = [os.path.join(SKILL, "SKILL.md")]
        for dp, _, fn in os.walk(os.path.join(SKILL, "references")):
            targets += [os.path.join(dp, f) for f in fn]
        for path in targets:
            self.assertLess(slop_scan.scan(read(path))["score"], slop_scan.BAND_PASS, path)

    def test_no_em_dashes_or_smart_quotes_in_instructions(self):
        text = read(os.path.join(SKILL, "SKILL.md"))
        self.assertNotRegex(text, "[—‘’“”]")

    def test_scripts_explain_themselves_and_use_no_third_party_imports(self):
        allowed = {
            "argparse", "json", "os", "re", "statistics", "subprocess", "sys", "time", "shutil", "tempfile", "zipfile",
            "urllib", "concurrent", "doclib", "slop_scan", "verify_refs",
        }
        for f in os.listdir(os.path.join(SKILL, "scripts")):
            if f.endswith(".py"):
                text = read(os.path.join(SKILL, "scripts", f))
                self.assertTrue(text.startswith("#!/usr/bin/env python3\n\"\"\""), f)
                imports = set()
                for node in ast.walk(ast.parse(text)):
                    if isinstance(node, ast.Import):
                        imports.update(a.name.split(".")[0] for a in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        imports.add(node.module.split(".")[0])
                self.assertTrue(imports <= allowed, "%s: %s" % (f, imports - allowed))
                if f != "doclib.py":
                    self.assertIn("Exit codes:", text, f)
                    self.assertIn("Examples:", text, f)


if __name__ == "__main__":
    unittest.main()
