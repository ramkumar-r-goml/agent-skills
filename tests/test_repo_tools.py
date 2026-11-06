"""Tests for repo_inventory.py and doc_audit.py."""
import json
import os
import tempfile
import unittest

from support import FIXTURE, FIXTURE_SECRET, git, run_main, temp_repo, write_files

import doc_audit
import doclib
import repo_inventory


class Inventory(unittest.TestCase):
    def setUp(self):
        self.inv = repo_inventory.inventory(FIXTURE)

    def test_never_exposes_secret_values(self):
        for args in ([FIXTURE], [FIXTURE, "--json"], [FIXTURE, "--all"]):
            _, out, _ = run_main(repo_inventory.main, args)
            self.assertNotIn(FIXTURE_SECRET, out)
            self.assertIn(".env", out)

    def test_finds_the_reading_order_facts(self):
        self.assertIn("README.md", self.inv["2_existing_docs"])
        self.assertIn("Makefile", self.inv["3_manifests"])
        self.assertEqual(self.inv["3_manifest_summary"]["pyproject"]["requires_python"], ">=3.11")
        self.assertEqual(self.inv["3_manifest_summary"]["makefile_targets"], ["lint", "run", "test", "worker"])
        self.assertIn("docker-compose.yml", self.inv["4_runtime_and_deploy_config"])
        self.assertEqual(self.inv["4_secret_files_names_only"], [".env"])
        self.assertEqual(self.inv["languages"]["Python"], 8)

    def test_entry_points_include_files_with_a_main_guard(self):
        self.assertIn("src/orderflow/api.py", self.inv["5_entry_points"])
        self.assertIn("src/orderflow/worker.py", self.inv["5_entry_points"])

    def test_env_vars_come_from_code_and_examples(self):
        self.assertIn("WORKER_MAX_RETRIES", self.inv["5_env_vars_read"])
        self.assertIn("PORT", self.inv["5_env_vars_in_examples"])

    def test_not_a_directory(self):
        self.assertEqual(run_main(repo_inventory.main, ["nope"])[0], 2)

    def test_long_sections_collapse_and_all_expands(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        write_files(tmp.name, {"svc%d/Dockerfile" % i: "FROM x\n" for i in range(40)})
        _, short, _ = run_main(repo_inventory.main, [tmp.name, "--limit", "5"])
        self.assertIn("Dockerfile (40 copies)", short)
        _, full, _ = run_main(repo_inventory.main, [tmp.name, "--all"])
        self.assertIn("svc39/Dockerfile", full)
        self.assertNotIn("copies", full)

    def test_build_output_is_skipped_without_git(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        write_files(tmp.name, {
            "App/bin/Debug/net8.0/appsettings.json": "{}", "App/obj/Debug/x.cs": "", "App/Program.cs": "",
            "bin/run.sh": "#!/bin/sh\n", "node_modules/x/index.js": "", "yarn.lock": "",
        })
        files, _, source = doclib.list_repo_files(tmp.name)
        self.assertEqual(source, "walk")
        self.assertEqual(files, ["App/Program.cs", "bin/run.sh"])

    def test_git_listing_respects_gitignore(self):
        tmp = temp_repo({".gitignore": "out.txt\n", "a.py": "", "out.txt": ""})
        self.addCleanup(tmp.cleanup)
        files, _, source = doclib.list_repo_files(tmp.name)
        self.assertEqual(source, "git")
        self.assertEqual(files, [".gitignore", "a.py"])


class Audit(unittest.TestCase):
    def test_fixture_findings(self):
        res = doc_audit.audit(doclib.RepoIndex(FIXTURE))
        items = {(f["kind"], f["item"]) for f in res["findings"]}
        self.assertIn(("make-target", "make start"), items)
        self.assertIn(("env-var", "DATABASE_URI"), items)
        self.assertIn(("missing-doc", "Runbook"), items)
        self.assertEqual({d["doc"] for d in res["documents"]}, {"README.md", "docs/architecture.md"})
        self.assertTrue(all(d["band"] == "rewrite from evidence" for d in res["documents"]))
        order = [doc_audit.SEVERITIES[f["severity"]] for f in res["findings"]]
        self.assertEqual(order, sorted(order))

    def test_never_exposes_secret_values(self):
        _, out, _ = run_main(doc_audit.main, [FIXTURE, "--json"])
        self.assertNotIn(FIXTURE_SECRET, out)

    def test_agent_skills_are_not_audited_as_project_docs(self):
        tmp = temp_repo({"README.md": "# R\n", "skills/x/SKILL.md": "---\nname: x\n---\n", "skills/x/references/a.md": "See `references/gone.md`.\n"})
        self.addCleanup(tmp.cleanup)
        res = doc_audit.audit(doclib.RepoIndex(tmp.name))
        self.assertEqual([d["doc"] for d in res["documents"]], ["README.md"])

    def test_skill_and_test_files_do_not_count_as_coverage(self):
        tmp = temp_repo({"README.md": "# R\n", "app.py": "", "skills/x/SKILL.md": "---\nname: x\n---\n", "skills/x/references/runbook.md": "# R\n",
                         "evals/cases/runbook-test/prompt.md": "write a runbook\n", "docs/ops/runbook-orders.md": "# Runbook\n"})
        self.addCleanup(tmp.cleanup)
        rows = {r["type"]: r["found"] for r in doc_audit.audit(doclib.RepoIndex(tmp.name))["coverage"]}
        self.assertEqual(rows["Runbook"], ["docs/ops/runbook-orders.md"])

    def test_coverage_requires_a_root_readme(self):
        tmp = temp_repo({"sub/README.md": "# Sub\n", "a.py": ""})
        self.addCleanup(tmp.cleanup)
        res = doc_audit.audit(doclib.RepoIndex(tmp.name))
        root = next(r for r in res["coverage"] if r["type"] == "Root README")
        self.assertEqual(root["found"], [])
        self.assertTrue(any(f["item"] == "Root README" and f["severity"] == "warning" for f in res["findings"]))

    def test_helper_scripts_do_not_count_as_a_product_cli(self):
        tmp = temp_repo({"scripts/gen.py": "import argparse\nargparse.ArgumentParser()\n"})
        self.addCleanup(tmp.cleanup)
        self.assertFalse(doc_audit.repo_signals(doclib.RepoIndex(tmp.name))["cli"])

    def test_duplicates_across_docs(self):
        para = " ".join("word%d" % i for i in range(40))
        tmp = temp_repo({"a.md": "# A\n\n%s\n" % para, "b.md": "# B\n\n%s\n" % para})
        self.addCleanup(tmp.cleanup)
        res = doc_audit.audit(doclib.RepoIndex(tmp.name))
        self.assertTrue(any(f["kind"] == "duplicate" for f in res["findings"]))

    def test_drift_flags_code_changed_after_the_doc(self):
        tmp = temp_repo({"src/app.py": "x = 1\n", "doc.md": "# D\n\nSee `src/app.py`.\n"})
        self.addCleanup(tmp.cleanup)
        # Commit times have one-second resolution, so force the second commit into the future.
        write_files(tmp.name, {"src/app.py": "x = 2\n"})
        git(tmp.name, "add", "-A")
        os.environ["GIT_COMMITTER_DATE"] = "2099-01-01T00:00:00"
        self.addCleanup(os.environ.pop, "GIT_COMMITTER_DATE", None)
        git(tmp.name, "commit", "-q", "-m", "change code")
        res = doc_audit.audit(doclib.RepoIndex(tmp.name))
        self.assertTrue(any(f["kind"] == "drift" and f["doc"] == "doc.md" for f in res["findings"]))

    def test_old_last_verified_date_is_flagged(self):
        tmp = temp_repo({"run.md": "---\nlast_verified: 2020-01-01\n---\n# Runbook\n"})
        self.addCleanup(tmp.cleanup)
        res = doc_audit.audit(doclib.RepoIndex(tmp.name))
        self.assertTrue(any(f["kind"] == "freshness" for f in res["findings"]))

    def test_not_run_is_reported_as_never_verified(self):
        tmp = temp_repo({"run.md": "---\nlast_verified: not run; read against abc123\n---\n# Runbook\n"})
        self.addCleanup(tmp.cleanup)
        res = doc_audit.audit(doclib.RepoIndex(tmp.name))
        finding = next(f for f in res["findings"] if f["kind"] == "freshness")
        self.assertIn("never run", finding["message"])

    def test_fail_on_exit_codes(self):
        self.assertEqual(run_main(doc_audit.main, [FIXTURE])[0], 0)
        self.assertEqual(run_main(doc_audit.main, [FIXTURE, "--fail-on", "error"])[0], 1)
        self.assertEqual(run_main(doc_audit.main, ["nope"])[0], 2)


class ChangedSince(unittest.TestCase):
    def setUp(self):
        tmp = temp_repo({
            "src/worker.py": "import os\n\ndef charge_order():\n    return os.environ['PAY_TOKEN']\n",
            "src/other.py": "VALUE = 1\n",
            "docs/ops.md": "Run `charge_order` with `PAY_TOKEN` set. See `src/worker.py`.\n",
            "docs/unrelated.md": "Nothing relevant here.\n",
        })
        self.addCleanup(tmp.cleanup)
        self.repo = tmp.name
        git(self.repo, "branch", "base")

    def commit(self, files):
        write_files(self.repo, files)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "change")

    def test_doc_mentioning_a_changed_file_is_listed(self):
        self.commit({"src/worker.py": "import os\n\ndef charge_order():\n    return os.environ['PAY_TOKEN'] + 'x'\n"})
        res, err = doc_audit.changed_since(doclib.RepoIndex(self.repo), "base")
        self.assertIsNone(err)
        docs = {d["doc"]: d for d in res["impacted_docs"]}
        self.assertIn("docs/ops.md", docs)
        self.assertNotIn("docs/unrelated.md", docs)
        self.assertEqual(docs["docs/ops.md"]["mentions_changed_files"], ["src/worker.py"])

    def test_removed_names_are_reported(self):
        self.commit({"src/worker.py": "import os\n\ndef settle_order():\n    return os.environ['PAY_SECRET']\n"})
        res, _ = doc_audit.changed_since(doclib.RepoIndex(self.repo), "base")
        self.assertEqual(res["names_removed_from_code"], ["PAY_TOKEN", "charge_order"])
        doc = next(d for d in res["impacted_docs"] if d["doc"] == "docs/ops.md")
        self.assertEqual(doc["mentions_removed_names"], ["PAY_TOKEN", "charge_order"])

    def test_a_name_still_defined_elsewhere_is_not_removed(self):
        self.commit({"src/worker.py": "VALUE = 2\n", "src/other.py": "import os\n\ndef charge_order():\n    return os.environ['PAY_TOKEN']\n"})
        res, _ = doc_audit.changed_since(doclib.RepoIndex(self.repo), "base")
        self.assertEqual(res["names_removed_from_code"], [])

    def test_uncommitted_changes_count(self):
        write_files(self.repo, {"src/worker.py": "VALUE = 3\n"})
        res, _ = doc_audit.changed_since(doclib.RepoIndex(self.repo), "base")
        self.assertIn("charge_order", res["names_removed_from_code"])

    def test_bad_ref_is_a_usage_error(self):
        code, _, err = run_main(doc_audit.main, [self.repo, "--changed-since", "no-such-ref"])
        self.assertEqual(code, 2)
        self.assertIn("no-such-ref", err)

    def test_fail_on_when_a_doc_still_mentions_a_removed_name(self):
        self.commit({"src/worker.py": "VALUE = 2\n"})
        self.assertEqual(run_main(doc_audit.main, [self.repo, "--changed-since", "base", "--fail-on", "error"])[0], 1)
        _, out, _ = run_main(doc_audit.main, [self.repo, "--changed-since", "base"])
        self.assertIn("still mentions removed", out)


if __name__ == "__main__":
    unittest.main()
