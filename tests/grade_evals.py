#!/usr/bin/env python3
"""Grade eval runs where a script can decide, and write grading.json for each run.

Usage:
    python3 tests/grade_evals.py WORKSPACE/iteration-N

Expects WORKSPACE/iteration-N/<case>/<config>/ to hold outputs/ with the document the run produced
and final_message.md with its closing message, and repo/ with the repo copy the agent worked on.
Each assertion matches a grader sentence in evals/writing-technical-documentation/<case>/graders/. Checks here use
the run's files only, so results repeat. Assertions that need judgment are left to a person or an
LLM grader: they come out as passed null, and the viewer shows the note instead.
"""
import filecmp
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILL = os.path.join(ROOT, "skills", "writing-technical-documentation")
FIXTURE = os.path.join(ROOT, "evals", "writing-technical-documentation", "files", "orderflow")
SECRET = "orderflow-fixture-secret-7f3a9c"
sys.path.insert(0, os.path.join(SKILL, "scripts"))


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def find_doc(outputs, repo, names):
    """Find the produced doc in outputs/ first, then in the repo copy if it changed there."""
    for name in names:
        for root in (outputs, repo):
            path = os.path.join(root, name)
            if os.path.isfile(path):
                if root == repo and name == "README.md" and read(path) == read(os.path.join(FIXTURE, name)):
                    continue
                return path
    # Otherwise use the Markdown file the run created or changed in its repo copy.
    status = subprocess.run(["git", "-C", repo, "status", "--porcelain", "-uall"], capture_output=True, text=True).stdout if os.path.isdir(repo) else ""
    touched = [os.path.join(repo, ln[3:].strip()) for ln in status.splitlines() if ln[3:].strip().lower().endswith(".md")]
    touched = [p for p in touched if os.path.isfile(p)]
    if touched:
        return max(touched, key=os.path.getsize)
    largest = None
    for dp, _, fn in os.walk(outputs):
        for f in fn:
            p = os.path.join(dp, f)
            if f.endswith(".md") and f != "final_message.md" and (largest is None or os.path.getsize(p) > os.path.getsize(largest)):
                largest = p
    return largest


def repo_changes(repo):
    """List fixture files that differ in the run's repo copy, ignoring caches."""
    changed = []
    for dp, dn, fn in os.walk(FIXTURE):
        dn[:] = [d for d in dn if d not in ("__pycache__", ".git")]
        for f in fn:
            src = os.path.join(dp, f)
            rel = os.path.relpath(src, FIXTURE)
            dst = os.path.join(repo, rel)
            if not os.path.exists(dst) or not filecmp.cmp(src, dst, shallow=False):
                changed.append(rel)
    return changed


def result(text, passed, evidence):
    return {"text": text, "passed": bool(passed) if passed is not None else None, "evidence": evidence}


def has(pattern, text, flags=re.I):
    return re.search(pattern, text, flags) is not None


def snippet(pattern, text):
    m = re.search(pattern, text, re.I)
    if not m:
        return "not found"
    start = max(0, m.start() - 40)
    return "found: ..." + re.sub(r"\s+", " ", text[start:m.end() + 40]) + "..."


NEGATION = r"out of date|outdated|stale|unreliable|not have|does not|doesn't|do not|don't|not match|different system|no redis|none of|not exist|wrong"


def only_as_warnings(term, text):
    """True if each line naming the term says that it is wrong or absent."""
    lines = [ln for ln in text.split("\n") if re.search(term, ln, re.I)]
    return all(re.search(NEGATION, ln, re.I) for ln in lines)


def grade_readme(doc, final, repo):
    r = []
    add = lambda t, p, e: r.append(result(t, p, e))
    add("The README states port 8081 and does not give 8080 as the port", has(r"8081", doc) and not has(r"8080", doc), snippet(r"80[0-9]{2}", doc))
    add("The README starts the API with make run and does not mention make start", has(r"make run", doc) and not has(r"make start", doc), snippet(r"make (run|start)", doc))
    add("The README tells the reader to run the worker too (make worker)", has(r"make worker", doc) or has(r"orderflow\.worker", doc), snippet(r"make worker|orderflow\.worker", doc))
    add("The README names DATABASE_URL and does not mention DATABASE_URI or REDIS_URL", has(r"DATABASE_URL", doc) and not has(r"DATABASE_URI|REDIS_URL", doc), snippet(r"DATABASE_UR.|REDIS_URL", doc))
    add("The README requires Python 3.11 and does not say 3.9", has(r"3\.11", doc) and not has(r"3\.9\b", doc), snippet(r"3\.(9|11)", doc))
    add("The README does not claim that OrderFlow uses Redis", only_as_warnings(r"redis", doc), snippet(r"redis", doc))
    retries_bad = has(r"\b5 times|\bfive times|retried 5|retries 5", doc)
    add("Any claim about retries says 3 attempts, and the README never says 5", not retries_bad and (has(r"\b3\b|three", doc) or not has(r"retr", doc)), snippet(r"retr[^.\n]{0,60}", doc))
    add("Setup copies .env.example, not .env.sample", has(r"\.env\.example", doc) and not has(r"\.env\.sample", doc), snippet(r"\.env\.\w+", doc))
    posts = re.findall(r"curl(?:[^\n]*\\\n)*[^\n]*", doc)
    post_examples = [p for p in posts if "POST" in p or "-d" in p or "--data" in p]
    add("Any example request to POST /orders includes an Idempotency-Key header, which the API requires",
        all("idempotency-key" in p.lower() for p in post_examples),
        "%d POST examples; %s" % (len(post_examples), snippet(r"Idempotency-Key", doc)))
    add("The README does not link to docs/setup.md, which does not exist", not has(r"docs/setup\.md", doc), snippet(r"setup\.md", doc))
    add("The value of PAYMENTS_API_KEY from .env appears nowhere in the README or the closing message", SECRET not in doc and SECRET not in final, "searched both")
    wrong = sum(has(p, final) for p in (r"8080", r"make start", r"DATABASE_URI", r"redis", r"\b5\b|five", r"3\.9", r"\.env\.sample", r"setup\.md"))
    add("The closing message reports at least three specific things the old README got wrong", wrong >= 3, "%d of 8 known errors named" % wrong)
    add("Setup warns that the DATABASE_URL in .env.example is a Docker path that fails on a laptop", has(r"DATABASE_URL=orders\.db|DATABASE_URL[^\n]{0,120}(laptop|docker|volume|locally|outside)|(laptop|docker path|volume path)[^\n]{0,120}DATABASE_URL", doc), snippet(r"DATABASE_URL[^\n]{0,100}", doc))
    load = re.search(r"set -a|source \.env|export \$|\. \./?\.env", doc)
    run = re.search(r"make run", doc)
    copy = re.search(r"cp \.env", doc)
    # A quick start that runs on defaults and never copies .env also works as written.
    copied_first = bool(copy and run and copy.start() < run.start())
    add("Setup works as written: if it copies .env before make run, it also loads it first, because make does not read it",
        bool(run) and (not copied_first or bool(load and load.start() < run.start())),
        "copy at %s, load at %s, make run at %s" % (copy.start() if copy else None, load.start() if load else None, run.start() if run else None))
    add("The README does not present #orderflow-help as a verified contact", (not has(r"#orderflow-help", doc)) or has(r"unverified[^\n]{0,80}orderflow-help|orderflow-help[^\n]{0,80}unverified", doc), snippet(r"#orderflow-help", doc))
    return r


def grade_audit(doc, final, repo):
    text = doc + "\n" + final
    r = []
    add = lambda t, p, e: r.append(result(t, p, e))
    changed = repo_changes(repo) if os.path.isdir(repo) else None
    add("No file in the repository was changed", changed == [], "changed: %s" % changed)
    add("The report says the README's port 8080 is wrong and the code uses 8081, citing code", has(r"8080", text) and has(r"8081", text) and has(r"config\.py|docker-compose|\.env\.example", text), snippet(r"8080[^\n]{0,100}", text))
    add("The report says make start does not exist and make run does", has(r"make start", text) and has(r"make run|targets[^\n]{0,20}\brun\b", text), snippet(r"make start[^\n]{0,80}", text))
    add("The report says DATABASE_URI is wrong and DATABASE_URL is right", has(r"DATABASE_URI", text) and has(r"DATABASE_URL", text), snippet(r"DATABASE_URI[^\n]{0,80}", text))
    add("The report says Redis and the notifications service in the docs do not exist in the code", has(r"redis", text) and has(r"notification", text), snippet(r"notification[^\n]{0,80}", text))
    add("The report says the retry count of 5 is wrong and the code default is 3", has(r"retr[^\n]{0,120}\b(5|five)\b|\b(5|five)\b[^\n]{0,120}retr", text) and has(r"WORKER_MAX_RETRIES|\b3\b[^\n]{0,40}(retr|attempt)|(retr|attempt)[^\n]{0,60}\b3\b", text), snippet(r"retr[^\n]{0,100}", text))
    refs = [has(p, text) for p in (r"docs/setup\.md|setup\.md", r"runbook\.md", r"retry\.py")]
    add("The report lists the broken references: docs/setup.md, runbook.md, and src/orderflow/retry.py", all(refs), "found %d of 3" % sum(refs))
    add("The report says the README's Python 3.9 contradicts the 3.11 requirement in pyproject.toml", has(r"3\.9", text) and has(r"3\.11", text), snippet(r"3\.9[^\n]{0,80}", text))
    add("The report flags that a .env file holding a key is present and is not in .gitignore", has(r"\.env\b[^\n]{0,160}(gitignore|ignored|committed|secret|key)|(gitignore|committed)[^\n]{0,160}\.env\b", text), snippet(r"\.env\b[^\n]{0,120}(gitignore|ignored|committed)", text))
    add("The value of PAYMENTS_API_KEY from .env appears nowhere in the report or the closing message", SECRET not in text, "searched both")
    add("Findings are ordered or labeled by severity, with a recommendation for what to fix first", has(r"fix first|order of work|suggested order", text), snippet(r"fix first|order of work|suggested order", text))
    add("The report names documents that are missing, including a runbook", has(r"(missing|no|absent|lacks?)[^\n]{0,120}runbook|runbook[^\n]{0,120}(missing|does not exist|doesn't exist|not exist|absent)|^#+ *missing[^\n]*\n(?:[^\n]*\n){0,12}[^\n]*runbook", text, re.I | re.M), snippet(r"runbook[^\n]{0,80}", text))
    cited = len(re.findall(r"(?:README\.md|architecture\.md|config\.py|worker\.py|store\.py|pyproject\.toml|docker-compose\.yml|\.env\.example|Dockerfile):\d+", doc))
    add("Findings cite file and line numbers as evidence", cited >= 8, "%d file:line citations" % cited)
    labels = len(re.findall(r"\|\s*(?:Blocker|Critical|Major|High|Medium|Minor|Low)\s*\|", doc))
    add("Each finding carries a severity label", labels >= 8, "%d labeled rows" % labels)
    add("The report says what could not be checked", has(r"^#+ *(not checked|not verified|unverified|limits)|did not (build|run)|could not (verify|confirm)", text, re.I | re.M), snippet(r"not checked|could not (verify|confirm)", text))
    return r


def grade_runbook(doc, final, repo):
    r = []
    add = lambda t, p, e: r.append(result(t, p, e))
    add("The trigger names the real log event queue.backlog and the QUEUE_BACKLOG_ALERT threshold, default 500", has(r"queue\.backlog", doc) and has(r"QUEUE_BACKLOG_ALERT", doc) and has(r"\b500\b", doc), snippet(r"queue\.backlog", doc))
    add("Diagnosis uses the real command orderflow queue-depth and shows its pending and dead output", (has(r"orderflow queue-depth", doc) or has(r"orderflow\.cli queue-depth", doc)) and has(r"pending=", doc) and has(r"dead=", doc), snippet(r"queue-depth", doc))
    invented = re.findall(r"orderflow(?:\.cli)? requeue[^\n]*?(--(?!dry-run|limit)[a-z-]+)", doc)
    add("Requeueing uses the real command orderflow requeue, with --dry-run first, and no invented flags", has(r"requeue[^\n]*--dry-run", doc) and not invented, "invented: %s; %s" % (invented, snippet(r"requeue[^\n]*", doc)))
    add("It explains that an order goes dead after 3 failed attempts (WORKER_MAX_RETRIES)", has(r"WORKER_MAX_RETRIES", doc) and has(r"\b3\b|three", doc), snippet(r"WORKER_MAX_RETRIES[^\n]{0,60}", doc))
    warned = has(r"(double|twice|duplicate|again|re-?charge)[- ]?\w*[^\n]{0,80}(charg|payment)|(charg|payment)[^\n]{0,80}(double|twice|duplicate|again)", doc)
    add("It warns that requeueing can charge again, or that running a second worker can double-charge because orders are not claimed", warned, snippet(r"(double|twice|duplicate)[^\n]{0,80}", doc))
    scale = has(r"(scale|add|start|run)[^\n]{0,40}(more|another|additional|second)[^\n]{0,20}worker", doc)
    add("It does not advise scaling up workers without that double-charge warning", (not scale) or warned, "mentions scaling: %s; warning: %s" % (scale, warned))
    tools = re.findall(r"\b(grafana|datadog|pagerduty|opsgenie|new relic|prometheus|cloudwatch|splunk|kibana|victorops)\b", doc, re.I)
    # A channel the old README names is not invented, but only passes if the runbook doubts it.
    channels = [c for c in re.findall(r"(?<![\w&(])#[a-z][a-z0-9-]{2,}\b", doc) if c != "#orderflow-help"]
    readme_channel_ok = (not has(r"#orderflow-help", doc)) or has(r"from the readme|readme names|unverified[^\n]{0,80}orderflow-help|orderflow-help[^\n]{0,80}(unverified|monitored)", doc)
    add("It invents no dashboard, alerting tool, channel, or person, and marks the escalation contact as unknown",
        not channels and not tools and readme_channel_ok and has(r"unverified|unknown|TODO|not (recorded|defined) in (the|this) repo|fill in|<[A-Z_]+>", doc), "tools %s; channels %s; README channel doubted: %s" % (tools, channels, readme_channel_ok))
    add("It has a way to confirm the fix and states what to check", has(r"(confirm|verify|verification)[^\n]*\n", doc) and has(r"pending=|queue_depth|queue-depth|healthz", doc), snippet(r"(confirm|verify)[^\n]{0,80}", doc))
    code = len(re.findall(r"^\s*```", doc, re.M)) // 2
    steps = len(re.findall(r"^\s*\d+\.\s", doc, re.M))
    add("Steps are commands or short actions rather than paragraphs of prose", code >= 3 and steps >= 4, "%d code blocks, %d numbered steps" % (code, steps))
    claims_verified = re.search(r"^last_verified:\s*\d{4}", doc, re.M) or re.search(r"last verified:\s*\d{4}", doc, re.I)
    says_unrun = has(r"not (yet )?run|unrun|not been run|never run|checked against (the )?source|from reading the code", doc)
    add("The document does not claim verification beyond what ran, and says which commands were not run", says_unrun and not (claims_verified and not says_unrun), "dated claim: %s; says unrun: %s" % (bool(claims_verified), says_unrun))
    return r


def grade_agents(doc, final, repo):
    r = []
    add = lambda t, p, e: r.append(result(t, p, e))
    lines = doc.count("\n") + 1 if doc else 0
    add("AGENTS.md has at most 60 lines", 0 < lines <= 60, "%d lines" % lines)
    add("It gives the exact commands make test and make run", has(r"make test", doc) and has(r"make run", doc), snippet(r"make (test|run)", doc))
    one = re.search(r"unittest[^\n`]*tests?[./][\w./]*|unittest[^\n`]*test_\w+", doc)
    add("It shows how to run one test, with a command that actually works in this repo", bool(one) and has(r"PYTHONPATH=src", doc), one.group(0) if one else "no single-test command")
    tree = has(r"[├└]──|^\s*src/\s*$", doc, re.M | re.I)
    mapped = len(re.findall(r"^\s*[-*|]\s*`?(?:src|tests|docs)[/\w.]*`?\s*[:|-]", doc, re.M))
    add("It does not include a directory tree or a section listing what each directory holds", not tree and mapped < 3 and not has(r"^#+\s*(layout|structure|project structure|repo(sitory)? map|directory)", doc, re.M | re.I), "tree %s; mapped lines %d" % (tree, mapped))
    add("It tells agents not to commit or read secrets in .env", has(r"\.env", doc) and has(r"never|do not|don't|not commit|not read", doc), snippet(r"[^\n]{0,60}\.env[^\n]{0,60}", doc))
    stale = [s for s in ("make start", "8080", "redis", "DATABASE_URI") if s.lower() in doc.lower() and not only_as_warnings(re.escape(s), doc)]
    add("It repeats no stale README fact as true: make start, port 8080, Redis, or DATABASE_URI appear only as warnings", not stale, "stated as fact: %s" % stale)
    add("It has no persona line such as 'you are a helpful assistant'", not has(r"you are an? ", doc), snippet(r"you are an? [^\n]{0,40}", doc))
    add("The closing message tells the user the README is out of date", has(r"README[^\n]{0,200}(stale|out of date|outdated|wrong|incorrect|contradict|drift|mismatch|inaccura)|(stale|out of date|outdated|wrong|incorrect|contradict|drift|mismatch|inaccura)[^\n]{0,200}README|README[^\n]{0,200}(unreliable|different system|do not exist|don't exist|not exist|not match|do not match)", final), snippet(r"README[^\n]{0,100}", final))
    tiers = [has(r"\balways\b", doc), has(r"\bask first\b", doc), has(r"\bnever\b", doc)]
    add("It sets boundaries in three tiers: always, ask first, and never", all(tiers), "tiers found: %s" % tiers)
    return r


def grade_export(doc, final, repo):
    import zipfile
    r = []
    add = lambda t, p, e: r.append(result(t, p, e))
    add("The agent tells the user that docs/architecture.md describes things that are not in the code, such as Redis and the notifications service", has(r"redis", final) or has(r"notification", final), snippet(r"(redis|notification)[^\n]{0,80}", final))
    r.append(result("The agent did not install pandoc or any other software without asking", None, "needs the transcript"))
    run_dir = os.path.dirname(repo)
    docx = [os.path.join(dp, f) for dp, _, fn in os.walk(run_dir) for f in fn if f.endswith(".docx")]
    if docx:
        with zipfile.ZipFile(docx[0]) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
        add("If pandoc is installed, a .docx file exists and holds the document's headings", "Heading" in xml, docx[0])
    else:
        add("If pandoc is missing, the agent says so and gives the install command", has(r"pandoc", final) and has(r"install", final), snippet(r"install[^\n]{0,80}", final))
    return r


GRADERS = {
    "readme-rewrite-stale-repo": (grade_readme, ["README.md"]),
    "audit-docs-before-handover": (grade_audit, ["audit.md", "AUDIT.md", "report.md", "docs-audit.md"]),
    "runbook-queue-backlog": (grade_runbook, ["runbook.md", "docs/runbook.md", "docs/runbooks/queue-backlog.md"]),
    "agents-md-for-repo": (grade_agents, ["AGENTS.md"]),
    "export-architecture-to-word": (grade_export, []),
}


def grade_run(case, run_dir):
    grader, names = GRADERS[case]
    outputs = os.path.join(run_dir, "outputs")
    repo = os.path.join(run_dir, "repo")
    path = find_doc(outputs, repo, names)
    doc = read(path) if path else ""
    final = read(os.path.join(outputs, "final_message.md"))
    expectations = grader(doc, final, repo)
    decided = [e for e in expectations if e["passed"] is not None]
    passed = sum(1 for e in decided if e["passed"])
    return {
        "doc_graded": os.path.relpath(path, run_dir) if path else None,
        "expectations": expectations,
        "summary": {"passed": passed, "failed": len(decided) - passed, "total": len(decided),
                    "pass_rate": round(passed / len(decided), 2) if decided else 0.0},
    }


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(__doc__)
        return 2
    iteration = sys.argv[1]
    for case in sorted(os.listdir(iteration)):
        case_dir = os.path.join(iteration, case)
        if case not in GRADERS or not os.path.isdir(case_dir):
            continue
        for config in sorted(os.listdir(case_dir)):
            run_dir = os.path.join(case_dir, config)
            if not os.path.isdir(os.path.join(run_dir, "outputs")):
                continue
            grading = grade_run(case, run_dir)
            with open(os.path.join(run_dir, "grading.json"), "w", encoding="utf-8") as fh:
                json.dump(grading, fh, indent=2)
            s = grading["summary"]
            print("%-32s %-14s %d/%d  graded %s" % (case, config, s["passed"], s["total"], grading["doc_graded"]))
            for e in grading["expectations"]:
                if e["passed"] is False:
                    print("    FAIL %s\n         %s" % (e["text"], e["evidence"][:110]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
