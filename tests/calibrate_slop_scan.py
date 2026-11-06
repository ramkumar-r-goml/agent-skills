#!/usr/bin/env python3
"""Show how slop_scan scores a corpus, to set BAND_CLEAN and BAND_PASS and spot noisy rules.

Usage:
    python3 tests/calibrate_slop_scan.py MIN_WORDS GLOB [GLOB ...]

Example, using READMEs that ship with an npm install:
    python3 tests/calibrate_slop_scan.py 150 "$(npm root -g)/**/README.md"

Run this on human-written docs after changing a rule. Most should land under BAND_CLEAN. If a
category fires across many of them, it measures ordinary style, so make it a style note.
"""
import collections
import glob
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "skills", "writing-technical-documentation", "scripts"))
import doclib  # noqa: E402
import slop_scan  # noqa: E402

MATCH_CATEGORIES = {"vocabulary-high", "vocabulary", "vocabulary-weak", "filler-word", "phrase", "wordy-phrase", "negative-parallelism", "placeholder"}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    min_words = int(sys.argv[1])
    paths = sorted({p for pat in sys.argv[2:] for p in glob.glob(os.path.expanduser(pat), recursive=True) if os.path.isfile(p)})
    scores, weights, docs_with, terms = [], collections.Counter(), collections.Counter(), collections.Counter()
    worst = []
    for path in paths:
        res = slop_scan.scan(doclib.read_text(path))
        if res["words"] < min_words:
            continue
        scores.append(res["score"])
        worst.append((res["score"], res["words"], path))
        for cat, val in res["by_category"].items():
            weights[cat] += val["weight"]
            docs_with[cat] += 1
        for hit in res["hits"]:
            if hit["category"] in MATCH_CATEGORIES:
                terms[(hit["category"], hit["match"].lower())] += 1
    if not scores:
        print("No documents with at least %d words." % min_words)
        return 1
    scores.sort()

    def pct(f):
        return scores[int(f * (len(scores) - 1))]

    print("docs: %d" % len(scores))
    print("score p10 %.1f, p25 %.1f, median %.1f, p75 %.1f, p90 %.1f, max %.1f" % (pct(.1), pct(.25), pct(.5), pct(.75), pct(.9), scores[-1]))
    clean = sum(s < slop_scan.BAND_CLEAN for s in scores)
    rewrite = sum(s >= slop_scan.BAND_PASS for s in scores)
    print("bands: clean %d (%d%%), pass %d, rewrite %d (%d%%)" % (clean, 100 * clean / len(scores), len(scores) - clean - rewrite, rewrite, 100 * rewrite / len(scores)))
    print("\ncategory, total weight, docs (s = style note, not scored)")
    for cat, weight in weights.most_common(25):
        print("  %-24s %6d %5d %s" % (cat, weight, docs_with[cat], "s" if cat in slop_scan.STYLE_CATEGORIES else ""))
    print("\nmost common terms")
    for (cat, term), n in terms.most_common(25):
        print("  %-20s %-30s %d" % (cat, term[:30], n))
    print("\nhighest scores")
    for score, words, path in sorted(worst, reverse=True)[:8]:
        print("  %6.1f %6d %s" % (score, words, path[-80:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
