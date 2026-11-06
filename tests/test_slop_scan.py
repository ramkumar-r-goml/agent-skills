import json
import os
import tempfile
import unittest

from support import FIXTURE, run_main

import slop_scan


def cats(text, **kw):
    return slop_scan.scan(text, **kw)["by_category"]


AI_TEXT = """# Our Amazing Platform

## Overview

In today's fast-paced world, this comprehensive guide will delve into the robust, seamless platform.
It isn't just a cache; it's a performance layer, ensuring optimal results. Let's dive in!

- **Speed:** blazing fast
- **Scale:** highly scalable
- **Security:** enterprise-grade

Here is a revised draft for you. Let me know if you need more.
"""

HUMAN_TEXT = """# orderflow

The API writes orders to SQLite and the worker charges them one at a time. Set `DATABASE_URL`
before starting either process. If a charge fails, the worker waits 0.2 s, then 0.4 s, then 0.8 s.
After 3 failures the order moves to the `dead` state and stays there until someone runs
`orderflow requeue`. Start with `make run`, which listens on port 8081.
"""


class Detection(unittest.TestCase):
    def test_ai_text_scores_in_the_rewrite_band(self):
        res = slop_scan.scan(AI_TEXT)
        self.assertGreater(res["score"], slop_scan.BAND_PASS)
        self.assertEqual(slop_scan.band_of(res["score"]), "rewrite from evidence")

    def test_specific_text_scores_clean(self):
        res = slop_scan.scan(HUMAN_TEXT)
        self.assertLess(res["score"], slop_scan.BAND_CLEAN)
        self.assertEqual(slop_scan.band_of(res["score"]), "clean")

    def test_fixture_docs_score_high(self):
        for name in ("README.md", "docs/architecture.md"):
            with open(os.path.join(FIXTURE, name), encoding="utf-8") as fh:
                self.assertGreater(slop_scan.scan(fh.read())["score"], slop_scan.BAND_PASS, name)

    def test_negative_parallelism_counts_once_per_sentence(self):
        self.assertEqual(cats("It isn't just a cache; it's a layer of the system.\n")["negative-parallelism"]["count"], 1)

    def test_bold_lead_bullet_reports_its_own_line(self):
        res = slop_scan.scan("# T\n\nintro\n\n- **Speed:** fast\n")
        hit = next(h for h in res["hits"] if h["category"] == "bold-lead-bullet")
        self.assertEqual(hit["line"], 5)

    def test_leaked_artifact_inside_a_url_is_found(self):
        self.assertIn("leaked-artifact", cats("See [docs](https://x.example/?utm_source=chatgpt.com).\n"))
        self.assertIn("leaked-artifact", cats("Done. contentReference[oaicite:0]\n"))

    def test_placeholders(self):
        self.assertIn("placeholder", cats("Contact [Your Name] about this.\n"))
        self.assertIn("placeholder", cats("TODO write this section.\n"))
        self.assertIn("placeholder", cats("Accessed on 2025-XX-XX.\n"))
        self.assertNotIn("placeholder", cats("See [Link to docs](docs/a.md).\n"))

    def test_unverified_markers_are_collected_without_penalty(self):
        res = slop_scan.scan("Port 8081. [unverified: needs a staging run]\n")
        self.assertEqual(res["unverified_markers"][0]["line"], 1)
        self.assertEqual(res["score"], 0.0)

    def test_filler_and_paired_headings(self):
        self.assertIn("filler-heading", cats("## Overview\n\ntext\n"))
        self.assertIn("filler-heading", cats("## Challenges and Opportunities\n\ntext\n"))
        self.assertNotIn("filler-heading", cats("## Rotate the signing key\n\ntext\n"))

    def test_heading_restated_in_first_sentence(self):
        self.assertIn("heading-restated", cats("## Retry policy\n\nRetry policy is set in config.\n"))

    def test_uniform_sections(self):
        section = "## S%d\n\n- one\n- two\n- three\n\n"
        self.assertIn("uniform-sections", cats("".join(section % i for i in range(5))))

    def test_dramatic_fragments(self):
        self.assertIn("dramatic-fragments", cats("Simple. Fast. Secure. It runs on one host and needs nothing else.\n"))

    def test_parallel_lists_are_not_repeated_openers(self):
        text = "".join("- The tool does thing %d.\n" % i for i in range(5))
        self.assertNotIn("repeated-opener", cats(text))


class FalsePositiveGuards(unittest.TestCase):
    def test_code_is_masked(self):
        text = "Run `delve`.\n\n```python\n# delve into the tapestry\n```\n"
        self.assertEqual(slop_scan.scan(text)["hits"], [])

    def test_four_backtick_blocks_mask_nested_fences(self):
        text = "````markdown\n```\ndelve\n```\ntapestry\n````\n"
        self.assertEqual(slop_scan.scan(text)["hits"], [])

    def test_off_region_is_skipped(self):
        text = "Fine text.\n\n<!-- slop-scan: off -->\ndelve into the tapestry\n<!-- slop-scan: on -->\n"
        self.assertEqual(slop_scan.scan(text)["hits"], [])

    def test_front_matter_is_skipped_and_line_numbers_hold(self):
        res = slop_scan.scan("---\ntitle: delve\n---\n\nwe delve here\n")
        self.assertEqual([h["line"] for h in res["hits"]], [5])

    def test_allow_list(self):
        self.assertNotIn("vocabulary-weak", cats("The plugin ecosystem has 40 packages.\n", allow=["ecosystem"]))

    def test_transition_words_alone_are_not_scored(self):
        self.assertEqual(slop_scan.scan("Additionally, the worker retries 3 times.\n")["score"], 0.0)

    def test_style_notes_do_not_raise_the_score(self):
        res = slop_scan.scan("Just run it, very simply, in order to start. It is just easy.\n")
        self.assertGreater(res["stats"]["style_notes"], 0)
        self.assertEqual(res["score"], 0.0)

    def test_one_habit_cannot_dominate(self):
        one_habit = "".join("- **Item %d:** a fact about port %d.\n" % (i, i) for i in range(40))
        self.assertLessEqual(slop_scan.scan(one_habit)["score"], slop_scan.CATEGORY_WEIGHT_CAP / slop_scan.SCORE_WORD_FLOOR * 1000 + 15)

    def test_short_text_uses_the_word_floor(self):
        self.assertEqual(slop_scan.scan("The robust tool.\n")["score"], round(2 / slop_scan.SCORE_WORD_FLOOR * 1000, 1))

    def test_underscores_the_character_is_fine(self):
        self.assertNotIn("vocabulary", cats("Names use underscores between words.\n"))


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bad = os.path.join(self.tmp.name, "bad.md")
        with open(self.bad, "w", encoding="utf-8") as fh:
            fh.write(AI_TEXT)

    def test_max_score_sets_exit_code(self):
        self.assertEqual(run_main(slop_scan.main, [self.bad, "--max-score", "1000", "--quiet"])[0], 0)
        self.assertEqual(run_main(slop_scan.main, [self.bad, "--max-score", "5", "--quiet"])[0], 1)

    def test_missing_file_is_usage_error(self):
        code, _, err = run_main(slop_scan.main, ["nope.md"])
        self.assertEqual(code, 2)
        self.assertIn("nope.md", err)

    def test_json_and_github_formats(self):
        _, out, _ = run_main(slop_scan.main, [self.bad, "--json"])
        self.assertIn(self.bad, json.loads(out))
        _, out, _ = run_main(slop_scan.main, [self.bad, "--format", "github"])
        self.assertTrue(out.startswith("::"))
        self.assertIn("file=%s,line=" % self.bad, out)

    def test_directory_scan_prints_a_ranked_table(self):
        _, out, _ = run_main(slop_scan.main, [self.tmp.name, "--quiet"])
        self.assertIn("Score", out)
        self.assertIn("bad.md", out)

    def test_limit_hides_low_weight_findings_first(self):
        _, out, _ = run_main(slop_scan.main, [self.bad, "--limit", "2"])
        self.assertIn("lower-weight findings hidden", out)


if __name__ == "__main__":
    unittest.main()
