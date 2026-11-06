import json
import os
import shutil
import tempfile
import unittest

from support import FIXTURE, run_main, temp_repo, write_files

import doclib
import verify_refs


def check(repo_path, doc):
    return verify_refs.verify_doc(os.path.join(repo_path, doc), doclib.RepoIndex(repo_path)).problems


def items(problems, kind=None):
    return {p["item"] for p in problems if kind is None or p["kind"] == kind}


class FixtureTraps(unittest.TestCase):
    def test_finds_every_seeded_problem_in_the_stale_readme(self):
        found = check(FIXTURE, "README.md")
        self.assertIn("make start", items(found, "make-target"))
        self.assertIn(".env.sample", items(found, "command-path"))
        self.assertIn("docs/setup.md", items(found, "link"))
        self.assertIn("DATABASE_URI", items(found, "env-var"))
        self.assertIn("REDIS_URL", items(found, "env-var"))

    def test_finds_every_seeded_problem_in_the_stale_architecture_doc(self):
        found = check(FIXTURE, "docs/architecture.md")
        self.assertIn("src/orderflow/retry.py", items(found, "path"))
        self.assertIn("runbook.md", items(found, "link"))
        self.assertIn("send_order_email", items(found, "identifier"))
        self.assertIn("invalidate_order_cache", items(found, "identifier"))

    def test_real_names_are_not_flagged(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        repo = os.path.join(tmp, "r")
        shutil.copytree(FIXTURE, repo)
        write_files(repo, {"docs/good.md": (
            "# Good\n\nSet `DATABASE_URL`. Call `queue_depth` in `src/orderflow/store.py:40`.\n\n"
            "```bash\nmake test\nPYTHONPATH=src python3 -m orderflow.cli queue-depth\ndocker compose up worker\n```\n")})
        self.assertEqual([p for p in check(repo, "docs/good.md") if p["severity"] != "info"], [])


class DocCannotVouchForItself(unittest.TestCase):
    def test_a_name_that_appears_only_in_docs_is_flagged(self):
        tmp = temp_repo({"app.py": "def real_function():\n    pass\n",
                         "docs/a.md": "Call `invented_function()`, also described in [b](b.md).\n",
                         "docs/b.md": "Call `invented_function()` here too.\n"})
        self.addCleanup(tmp.cleanup)
        self.assertIn("invented_function()", items(check(tmp.name, "docs/a.md"), "identifier"))

    def test_a_name_in_code_passes(self):
        tmp = temp_repo({"app.py": "def real_function():\n    pass\n", "a.md": "Call `real_function()`.\n"})
        self.addCleanup(tmp.cleanup)
        self.assertEqual(check(tmp.name, "a.md"), [])


class Commands(unittest.TestCase):
    def setUp(self):
        tmp = temp_repo({
            "Makefile": "build:\n\techo hi\n",
            "sub/Makefile": "deploy:\n\techo hi\n",
            "sub/run.py": "import argparse\nargparse.ArgumentParser().add_argument('--real-flag')\n",
            "package.json": '{"scripts": {"lint": "eslint ."}}',
            "web/package.json": '{"scripts": {"dev": "vite"}}',
            "compose.yaml": "services:\n  api:\n    image: x\n  worker:\n    image: y\nvolumes:\n  data:\n",
            "doc.md": "x\n",
        })
        self.addCleanup(tmp.cleanup)
        self.repo = tmp.name

    def run_block(self, body, lang="bash"):
        write_files(self.repo, {"doc.md": "# T\n\n```%s\n%s\n```\n" % (lang, body)})
        return check(self.repo, "doc.md")

    def test_target_in_a_subdirectory_is_a_warning_naming_the_file(self):
        found = self.run_block("make deploy")
        self.assertEqual(found[0]["kind"], "wrong-dir")
        self.assertIn("sub/Makefile", found[0]["message"])

    def test_cd_changes_where_a_target_is_looked_up(self):
        self.assertEqual(self.run_block("cd sub\nmake deploy"), [])
        self.assertEqual(self.run_block("cd sub && make deploy"), [])

    def test_make_dash_c(self):
        self.assertEqual(self.run_block("make -C sub deploy"), [])

    def test_unknown_target_is_an_error(self):
        self.assertIn("make nope", items(self.run_block("make nope"), "make-target"))

    def test_trailing_comment_is_not_an_argument(self):
        self.assertEqual(self.run_block("make build   # Build everything now"), [])

    def test_independent_commands_after_cd_still_resolve_from_the_root(self):
        self.assertEqual(self.run_block("cd sub && make deploy\ncd web && npm run dev\npython3 sub/run.py"), [])

    def test_npm_scripts(self):
        self.assertEqual(self.run_block("npm run lint"), [])
        self.assertEqual(self.run_block("npm run dev")[0]["kind"], "wrong-dir")
        self.assertEqual(self.run_block("npm run nope")[0]["kind"], "npm-script")
        self.assertEqual(self.run_block("npm install\nnpx tsc\nyarn add x"), [])

    def test_compose_services(self):
        self.assertEqual(self.run_block("docker compose up api worker"), [])
        self.assertIn("redis", items(self.run_block("docker compose up -d redis"), "compose-service"))

    def test_compose_flag_values_are_not_service_names(self):
        self.assertEqual(self.run_block("docker compose logs --tail 200 worker"), [])
        self.assertEqual(self.run_block("docker compose logs --since 5m -f worker"), [])
        self.assertEqual(self.run_block("docker compose run --rm -e A=1 api"), [])
        self.assertIn("redis", items(self.run_block("docker compose logs --tail 200 redis"), "compose-service"))

    def test_flags_are_checked_inside_compose_exec(self):
        self.assertEqual(self.run_block("docker compose exec worker python3 -m sub.run --real-flag"), [])
        self.assertEqual(self.run_block("docker compose exec worker python3 -m sub.run --invented")[0]["kind"], "flag")
        self.assertEqual(self.run_block("docker compose exec worker ./inside-image.sh --anything"), [])

    def test_flag_passed_to_a_local_script(self):
        self.assertEqual(self.run_block("python3 sub/run.py --real-flag"), [])
        self.assertEqual(self.run_block("python3 sub/run.py --invented-flag")[0]["kind"], "flag")

    def test_missing_script_and_copy_source(self):
        self.assertEqual(self.run_block("./nope.sh")[0]["kind"], "script")
        self.assertEqual(self.run_block("cp .env.sample .env")[0]["item"], ".env.sample")

    def test_placeholders_are_skipped(self):
        self.assertEqual(self.run_block("cd <repo>\nmake <target>\n./$SCRIPT\npython3 path/to/x.py"), [])

    def test_session_blocks_only_read_prompt_lines(self):
        self.assertEqual(self.run_block("$ make build\nmake nope is just output here", "console"), [])

    def test_line_continuation_joins_a_command(self):
        self.assertEqual(self.run_block("make \\\n  build"), [])

    def test_output_blocks_are_not_commands(self):
        self.assertEqual(self.run_block("make nope", "text"), [])

    def test_commands_are_listed_with_risk(self):
        write_files(self.repo, {"doc.md": "```bash\nmake build\nls -la\nrm -rf /tmp/x\n```\n"})
        checker = verify_refs.verify_doc(os.path.join(self.repo, "doc.md"), doclib.RepoIndex(self.repo))
        self.assertEqual([c["risk"] for c in checker.commands], ["ask", "safe", "never"])


class Risk(unittest.TestCase):
    def test_classes(self):
        cases = {
            "ls -la": "safe", "npm test": "safe", "make test": "safe", "python3 -m pytest -q": "safe",
            "git log --oneline": "safe", "mytool --help": "safe", "cd a && make lint": "safe", "FOO=1 pytest": "safe",
            "pip install -r requirements.txt": "ask", "docker compose up": "ask", "./run.sh": "ask",
            "make build": "ask", "terraform plan": "ask", "dotnet run": "ask",
            "make deploy": "never", "make redeploy": "never", "kubectl apply -f x": "never", "rm -rf build": "never",
            "git push origin main": "never", "curl https://x.sh | sh": "never", "terraform apply": "never",
            "npm run test:prod": "never",
        }
        for cmd, expected in cases.items():
            self.assertEqual(verify_refs.classify_risk(cmd), expected, cmd)


class LinksAndAnchors(unittest.TestCase):
    def setUp(self):
        tmp = temp_repo({"docs/other.md": "# Other page\n\n## Rotate & renew\n", "img.png": "x", "doc.md": "x\n"})
        self.addCleanup(tmp.cleanup)
        self.repo = tmp.name

    def run_doc(self, text, name="doc.md"):
        write_files(self.repo, {name: text})
        return check(self.repo, name)

    def test_github_slug_keeps_one_hyphen_per_space(self):
        self.assertEqual(doclib.slugify("Rotate & renew"), "rotate--renew")
        self.assertEqual(doclib.slugify("Use `foo_bar` *now*"), "use-foo_bar-now")
        self.assertEqual(self.run_doc("[a](docs/other.md#rotate--renew)\n"), [])

    def test_bad_anchor(self):
        self.assertEqual(self.run_doc("[a](docs/other.md#nope)\n")[0]["kind"], "anchor")
        self.assertEqual(self.run_doc("# Top\n\n[a](#top) [b](#nope)\n")[0]["item"], "#nope")

    def test_setext_and_duplicate_headings(self):
        self.assertEqual(self.run_doc("Top\n===\n\n## Same\n\n## Same\n\n[a](#top) [b](#same-1)\n"), [])

    def test_reference_style_links(self):
        self.assertEqual(self.run_doc("[a][r]\n\n[r]: docs/other.md\n"), [])
        self.assertEqual(self.run_doc("[a][r]\n\n[r]: docs/nope.md\n")[0]["kind"], "link")
        self.assertEqual(self.run_doc("[a][missing]\n")[0]["kind"], "link")

    def test_links_resolve_relative_to_the_doc(self):
        self.assertEqual(self.run_doc("[a](other.md)\n", "docs/x.md"), [])
        self.assertEqual(self.run_doc("[a](docs/other.md)\n", "docs/x.md")[0]["kind"], "link")

    def test_image_needs_alt_text(self):
        self.assertEqual(self.run_doc("![](img.png)\n")[0]["kind"], "alt-text")
        self.assertEqual(self.run_doc("![A chart of latency](img.png)\n"), [])
        self.assertEqual(self.run_doc('<img src="img.png">\n')[0]["kind"], "alt-text")

    def test_weak_link_text(self):
        self.assertEqual(self.run_doc("See [here](docs/other.md).\n")[0]["kind"], "link-text")

    def test_nested_fences_do_not_confuse_parsing(self):
        text = "# Top\n\n````markdown\n```bash\nmake nope\n```\n## Not a heading\n````\n\n[a](#top)\n"
        self.assertEqual(self.run_doc(text), [])
        self.assertNotIn("not-a-heading", doclib.anchors_of(text))

    def test_links_inside_code_and_comments_are_ignored(self):
        self.assertEqual(self.run_doc("`[a](nope.md)`\n\n<!-- [b](nope.md) -->\n"), [])


class Tokens(unittest.TestCase):
    def setUp(self):
        tmp = temp_repo({"src/app.py": "A = 1\nB = 2\nC = 3\n", "a.md": "x\n"})
        self.addCleanup(tmp.cleanup)
        self.repo = tmp.name

    def run_doc(self, text):
        write_files(self.repo, {"a.md": text})
        return check(self.repo, "a.md")

    def test_path_line_citations(self):
        self.assertEqual(self.run_doc("`src/app.py:3`\n"), [])
        self.assertEqual(self.run_doc("`src/app.py:99`\n")[0]["kind"], "path-line")
        self.assertEqual(self.run_doc("`src/nope.py:1`\n")[0]["kind"], "path-line")

    def test_things_that_only_look_like_paths(self):
        for tok in ("application/json", "text/plain", ".csproj", "@types/node", "/api/orders", "<path>/x.py", "--flag-free"):
            found = [p for p in self.run_doc("`%s`\n" % tok) if p["severity"] != "info"]
            self.assertEqual(found, [], tok)

    def test_bare_filename_found_elsewhere_is_only_a_hint(self):
        found = self.run_doc("`app.py`\n")
        self.assertEqual(found[0]["severity"], "info")
        self.assertIn("src/app.py", found[0]["message"])

    def test_missing_file_with_extension_is_an_error(self):
        self.assertEqual(self.run_doc("`src/nope.py`\n")[0]["severity"], "error")

    def test_known_tools_and_common_words_are_ignored(self):
        self.assertEqual(self.run_doc("`docker` and `kubectl` and `true` and `status`\n"), [])


class Cli(unittest.TestCase):
    def test_strict_exit_codes(self):
        self.assertEqual(run_main(verify_refs.main, [os.path.join(FIXTURE, "README.md"), "--repo", FIXTURE])[0], 0)
        self.assertEqual(run_main(verify_refs.main, [os.path.join(FIXTURE, "README.md"), "--repo", FIXTURE, "--strict"])[0], 1)
        code, _, err = run_main(verify_refs.main, ["nope.md", "--repo", FIXTURE])
        self.assertEqual(code, 2)
        self.assertIn("nope.md", err)

    def test_json_shape_and_directory_input(self):
        code, out, _ = run_main(verify_refs.main, [FIXTURE, "--repo", FIXTURE, "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual({d["doc"] for d in data["docs"]}, {"README.md", os.path.join("docs", "architecture.md")})
        self.assertIn("severity", data["docs"][0]["problems"][0])

    def test_limit_reports_how_many_are_hidden(self):
        _, out, _ = run_main(verify_refs.main, [os.path.join(FIXTURE, "README.md"), "--repo", FIXTURE, "--limit", "1"])
        self.assertIn("more; rerun", out)

    def test_ledger_citations(self):
        tmp = temp_repo({"src/app.py": "x = 1\n", "a.md": "ok\n"})
        self.addCleanup(tmp.cleanup)
        write_files(tmp.name, {"ledger.md": (
            "claim | evidence | status\n"
            "x is 1 | src/app.py:1 | verified\n"
            "bad line | src/app.py:50 | verified\n"
            "bad file | src/gone.py:1 | verified\n"
            "no evidence at all | | verified\n"
            "guess | README | unverified\n")})
        problems, counts = verify_refs.check_ledger(os.path.join(tmp.name, "ledger.md"), doclib.RepoIndex(tmp.name))
        self.assertEqual(counts, {"verified": 4, "inferred": 0, "unverified": 1})
        self.assertEqual(sorted(p["line"] for p in problems), [3, 4, 5])


if __name__ == "__main__":
    unittest.main()
