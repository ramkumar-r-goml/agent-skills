#!/usr/bin/env python3
"""Inventory a repository in documentation reading order.

Usage:
    python3 repo_inventory.py REPO [--json] [--max-files N]

Lists, in reading order: instruction files, existing docs, manifests, runtime and
deploy config, entry points, route and env var hints, tests, source layout, and a
git summary. Skips vendored, generated, and build directories. Read-only. Never
prints the values of environment or secret files, only their names.
Standard library only.
"""
import argparse
import json
import os
import re
import subprocess
import sys

SKIP_DIRS = {
    ".git", "node_modules", "vendor", ".venv", "venv", "env", "__pycache__", "target",
    "build", "dist", "out", ".next", ".nuxt", ".gradle", "Pods", ".idea", ".vscode",
    ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", "coverage", ".terraform",
    "cdk.out", ".serverless", ".cache", "bower_components", ".dart_tool", "site-packages",
}
SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Cargo.lock",
    "go.sum", "Gemfile.lock", "composer.lock", "Pipfile.lock", "uv.lock",
}
SKIP_SUFFIXES = (
    ".min.js", ".min.css", ".map", ".pb.go", "_pb2.py", ".generated.ts", ".snap",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2", ".ttf",
    ".zip", ".tar", ".gz", ".jar", ".class", ".pyc", ".so", ".dll", ".exe", ".bin",
    ".pdf", ".mp4", ".mov",
)

INSTRUCTION = [
    "AGENTS.md", "CLAUDE.md", ".cursorrules", "CONTRIBUTING.md", "CODEOWNERS",
    "SECURITY.md", "CODE_OF_CONDUCT.md", ".editorconfig", "GEMINI.md",
]
INSTRUCTION_PATHS = [".claude", ".github/copilot-instructions.md", ".github/CODEOWNERS", ".cursor/rules"]
DOC_NAMES = ["README", "CHANGELOG", "UPGRADING", "MIGRATION", "HISTORY", "ARCHITECTURE", "DESIGN", "LICENSE"]
DOC_DIRS = ["docs", "doc", "documentation", "wiki", "adr", "ADR", "rfcs", "rfc", "design", "decisions"]
MANIFESTS = [
    "package.json", "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile",
    "environment.yml", "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts",
    "settings.gradle", "Gemfile", "composer.json", "Makefile", "justfile", "Taskfile.yml",
    "tox.ini", "pytest.ini", "tsconfig.json", "turbo.json", "nx.json", "lerna.json",
    "pnpm-workspace.yaml", "go.work", "dvc.yaml", "MLproject", ".nvmrc", ".python-version",
    ".tool-versions", "global.json", "Package.swift", "Podfile",
]
CONFIG_NAMES = [
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml",
    ".env.example", ".env.sample", ".env.template", "Procfile", "serverless.yml", "template.yaml",
    "template.yml", "cdk.json", "samconfig.toml", "buildspec.yml", "Jenkinsfile", ".gitlab-ci.yml",
    "azure-pipelines.yml", "Chart.yaml", "values.yaml", "kustomization.yaml", "nginx.conf",
    "terraform.tfvars.example", "app.yaml", "vercel.json", "netlify.toml", "fly.toml",
    "openapi.yaml", "openapi.yml", "openapi.json", "swagger.json", "schema.graphql",
]
CONFIG_DIRS = [".github/workflows", ".circleci", "k8s", "kubernetes", "helm", "terraform", "infra", "deploy", "config", "configs"]
ENTRY_NAMES = [
    "main.py", "__main__.py", "app.py", "manage.py", "wsgi.py", "asgi.py", "server.py", "cli.py",
    "index.js", "index.ts", "main.ts", "main.js", "server.js", "server.ts", "app.js", "app.ts",
    "main.go", "main.rs", "lib.rs", "Program.cs", "Startup.cs", "Main.java", "Application.java",
    "handler.py", "lambda_function.py", "handler.js", "handler.ts", "config.ru",
]
TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs", "e2e", "integration", "cypress"}
TEST_FILE_RE = re.compile(r"(?:^test_.*\.py$|.*_test\.(?:py|go)$|.*\.(?:test|spec)\.(?:js|ts|jsx|tsx)$|.*Test\.java$|.*_spec\.rb$)")
AI_HINTS = {
    "prompts": re.compile(r"(?:^|/)(?:prompts?|templates?)(?:/|$)|\.prompt$|\.jinja2?$|system_prompt", re.I),
    "evals": re.compile(r"(?:^|/)(?:evals?|evaluation|benchmarks?)(?:/|$)", re.I),
    "agents_tools": re.compile(r"(?:^|/)(?:agents?|tools?|skills?|mcp)(?:/|$)", re.I),
    "retrieval": re.compile(r"(?:^|/)(?:rag|retriev\w*|embeddings?|vectorstores?|indexing)(?:/|$)", re.I),
    "notebooks": re.compile(r"\.ipynb$"),
}

ROUTE_RES = [
    re.compile(r"@(?:app|router|bp|blueprint|api)\.(?:get|post|put|patch|delete|route)\(\s*['\"]([^'\"]+)"),
    re.compile(r"\b(?:app|router|server)\.(?:get|post|put|patch|delete|use)\(\s*['\"`]([^'\"`]+)"),
    re.compile(r"@(?:Get|Post|Put|Patch|Delete|Request)Mapping\(\s*(?:value\s*=\s*)?\{?\s*['\"]([^'\"]+)"),
    re.compile(r"\.(?:GET|POST|PUT|PATCH|DELETE)\(\s*\"([^\"]+)"),
    re.compile(r"\bpath\(\s*['\"]([^'\"]*)['\"]\s*,"),
]
ENV_RES = [
    re.compile(r"os\.environ(?:\.get)?\(?\[?\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
    re.compile(r"os\.getenv\(\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]{2,})"),
    re.compile(r"process\.env\[\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
    re.compile(r"(?:System\.getenv|os\.Getenv|std::env::var|ENV\.fetch|getenv)\(\s*\"([A-Z][A-Z0-9_]{2,})\""),
]
CODE_SUFFIXES = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".cs", ".sh")


def walk(repo, max_files):
    files = []
    for root, dirs, names in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.endswith(".egg-info"))
        for n in sorted(names):
            if n in SKIP_FILES or n.endswith(SKIP_SUFFIXES):
                continue
            files.append(os.path.relpath(os.path.join(root, n), repo))
            if len(files) >= max_files:
                return files, True
    return files, False


def read_text(path, limit=400000):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except OSError:
        return ""


def size_of(repo, rel):
    try:
        return os.path.getsize(os.path.join(repo, rel))
    except OSError:
        return 0


def under(rel, prefix):
    rel = rel.replace(os.sep, "/")
    return rel == prefix or rel.startswith(prefix.rstrip("/") + "/")


def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def package_scripts(repo):
    p = os.path.join(repo, "package.json")
    if not os.path.isfile(p):
        return {}
    try:
        data = json.loads(read_text(p))
    except ValueError:
        return {}
    return {
        "name": data.get("name"), "version": data.get("version"), "main": data.get("main"),
        "bin": data.get("bin"), "engines": data.get("engines"), "scripts": data.get("scripts", {}),
        "workspaces": data.get("workspaces"),
        "dependencies": sorted((data.get("dependencies") or {}).keys())[:40],
    }


def pyproject_info(repo):
    p = os.path.join(repo, "pyproject.toml")
    if not os.path.isfile(p):
        return {}
    t = read_text(p)
    info = {}
    m = re.search(r"^name\s*=\s*\"([^\"]+)\"", t, re.M)
    if m:
        info["name"] = m.group(1)
    m = re.search(r"requires-python\s*=\s*\"([^\"]+)\"", t)
    if m:
        info["requires_python"] = m.group(1)
    m = re.search(r"\[project\.scripts\](.*?)(?:\n\[|\Z)", t, re.S)
    if m:
        info["console_scripts"] = [l.strip() for l in m.group(1).strip().splitlines() if "=" in l]
    return info


def makefile_targets(repo):
    p = os.path.join(repo, "Makefile")
    if not os.path.isfile(p):
        return []
    return sorted(set(re.findall(r"^([A-Za-z0-9_.-]+)\s*:(?!=)", read_text(p), re.M)))[:40]


def inventory(repo, max_files=20000):
    files, truncated = walk(repo, max_files)
    inv = {"repo": os.path.abspath(repo), "truncated": truncated, "file_count": len(files)}
    lower = {f.replace(os.sep, "/"): f for f in files}

    def top_level_matches(names):
        return [f for f in lower if "/" not in f and f in names]

    inv["1_instructions"] = sorted(
        {f for f in lower if os.path.basename(f) in INSTRUCTION and f.count("/") <= 2}
        | {f for f in lower if any(under(f, p) for p in INSTRUCTION_PATHS)}
    )

    docs = set()
    for f in lower:
        base = os.path.basename(f)
        stem = os.path.splitext(base)[0].upper()
        if f.count("/") == 0 and stem in DOC_NAMES:
            docs.add(f)
        if any(under(f, d) for d in DOC_DIRS) and f.lower().endswith((".md", ".rst", ".txt", ".adoc", ".mmd", ".puml", ".drawio", ".yaml", ".yml", ".json")):
            docs.add(f)
        if base.lower().endswith((".proto", ".graphql")) or base in ("openapi.yaml", "openapi.yml", "openapi.json", "swagger.json"):
            docs.add(f)
    inv["2_existing_docs"] = sorted(docs)

    inv["3_manifests"] = sorted(f for f in lower if os.path.basename(f) in MANIFESTS and f.count("/") <= 3)
    inv["3_manifest_summary"] = {
        "package_json": package_scripts(repo),
        "pyproject": pyproject_info(repo),
        "makefile_targets": makefile_targets(repo),
    }

    cfg = set()
    for f in lower:
        base = os.path.basename(f)
        if base in CONFIG_NAMES or re.match(r"docker-compose.*\.ya?ml$", base) or base.endswith((".tf", ".tfvars.example")):
            cfg.add(f)
        if any(under(f, d) for d in CONFIG_DIRS) and f.lower().endswith((".yml", ".yaml", ".json", ".toml", ".ini", ".tf", ".conf", ".env")):
            cfg.add(f)
        if re.match(r"\.env(\..+)?$", base) and base not in (".env.example", ".env.sample", ".env.template"):
            cfg.add(f + "  (name only; contents not read)")
    inv["4_runtime_and_deploy_config"] = sorted(cfg)

    entries = []
    for f in lower:
        base = os.path.basename(f)
        if base in ENTRY_NAMES and f.count("/") <= 4:
            entries.append(f)
        if re.match(r"cmd/[^/]+/main\.go$", f) or f.startswith("bin/") and f.count("/") == 1:
            entries.append(f)
    inv["5_entry_points"] = sorted(set(entries))

    routes, envs = {}, {}
    scanned = 0
    for f in lower:
        if not f.endswith(CODE_SUFFIXES) or size_of(repo, lower[f]) > 400000:
            continue
        if TEST_FILE_RE.match(os.path.basename(f)) or any(part in TEST_DIR_NAMES for part in f.split("/")):
            continue
        scanned += 1
        if scanned > 4000:
            break
        text = read_text(os.path.join(repo, lower[f]))
        for rx in ROUTE_RES:
            for m in rx.finditer(text):
                routes.setdefault(m.group(1), set()).add(f)
        for rx in ENV_RES:
            for m in rx.finditer(text):
                envs.setdefault(m.group(1), set()).add(f)
    inv["5_route_hints"] = {k: sorted(v)[:3] for k, v in sorted(routes.items())[:80]}
    inv["5_env_vars_read"] = {k: sorted(v)[:3] for k, v in sorted(envs.items())[:80]}

    tests = [f for f in lower if TEST_FILE_RE.match(os.path.basename(f)) or any(part in TEST_DIR_NAMES for part in f.split("/")[:-1])]
    inv["6_tests"] = {"count": len(tests), "sample": sorted(tests)[:25]}

    layout = {}
    for f in lower:
        parts = f.split("/")
        key = parts[0] if len(parts) > 1 else "."
        layout[key] = layout.get(key, 0) + 1
    inv["7_source_layout"] = dict(sorted(layout.items(), key=lambda x: -x[1])[:40])

    ai = {}
    for label, rx in AI_HINTS.items():
        m = [f for f in lower if rx.search(f)]
        if m:
            ai[label] = sorted(m)[:15]
    inv["7_ai_ml_hints"] = ai

    large = sorted(((size_of(repo, lower[f]), f) for f in lower if f.endswith(CODE_SUFFIXES)), reverse=True)[:8]
    inv["7_largest_source_files"] = [{"path": f, "bytes": s} for s, f in large]

    if os.path.isdir(os.path.join(repo, ".git")):
        inv["8_git"] = {
            "branch": git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
            "head": git(repo, "rev-parse", "--short", "HEAD"),
            "recent_commits": git(repo, "log", "--oneline", "-15").splitlines(),
            "top_authors": git(repo, "shortlog", "-sn", "--no-merges", "HEAD").splitlines()[:5],
            "churn_last_6_months": git(repo, "log", "--since=6 months ago", "--name-only", "--pretty=format:").splitlines(),
        }
        churn = {}
        for f in inv["8_git"]["churn_last_6_months"]:
            if f:
                churn[f] = churn.get(f, 0) + 1
        inv["8_git"]["churn_last_6_months"] = sorted(churn.items(), key=lambda x: -x[1])[:12]
    else:
        inv["8_git"] = {}
    inv["skipped_dirs_present"] = sorted(d for d in SKIP_DIRS if os.path.isdir(os.path.join(repo, d)))
    return inv


def render(inv):
    o = []
    o.append("Repo: %s   files scanned: %d%s" % (inv["repo"], inv["file_count"], " (truncated)" if inv["truncated"] else ""))
    o.append("Skipped (present): %s" % (", ".join(inv["skipped_dirs_present"]) or "none"))

    def section(title, items):
        o.append("")
        o.append(title)
        if not items:
            o.append("  (none found)")
        for i in items:
            o.append("  " + str(i))

    section("1. Instructions for humans and agents (read fully)", inv["1_instructions"])
    section("2. Existing docs (treat as claims; verify)", inv["2_existing_docs"])
    section("3. Manifests and build definitions", inv["3_manifests"])
    ms = inv["3_manifest_summary"]
    if ms["package_json"]:
        pj = ms["package_json"]
        o.append("  package.json: name=%s version=%s main=%s engines=%s" % (pj.get("name"), pj.get("version"), pj.get("main"), pj.get("engines")))
        for k, v in (pj.get("scripts") or {}).items():
            o.append("    npm run %s -> %s" % (k, v))
    if ms["pyproject"]:
        o.append("  pyproject: %s" % ms["pyproject"])
    if ms["makefile_targets"]:
        o.append("  make targets: %s" % ", ".join(ms["makefile_targets"]))
    section("4. Runtime and deploy config", inv["4_runtime_and_deploy_config"])
    section("5. Entry points", inv["5_entry_points"])
    section("5b. Route hints (verify in code)", ["%s  (%s)" % (k, ", ".join(v)) for k, v in inv["5_route_hints"].items()])
    section("5c. Env vars read in code", ["%s  (%s)" % (k, ", ".join(v)) for k, v in inv["5_env_vars_read"].items()])
    t = inv["6_tests"]
    section("6. Tests (%d files)" % t["count"], t["sample"])
    section("7. Source layout (files per top-level dir)", ["%s: %d" % (k, v) for k, v in inv["7_source_layout"].items()])
    if inv["7_ai_ml_hints"]:
        section("7b. AI/ML hints", ["%s: %s" % (k, ", ".join(v[:6])) for k, v in inv["7_ai_ml_hints"].items()])
    section("7c. Largest source files (grep, then read ranges)", ["%s (%d bytes)" % (x["path"], x["bytes"]) for x in inv["7_largest_source_files"]])
    g = inv["8_git"]
    if g:
        section("8. Git", ["branch %s @ %s" % (g["branch"], g["head"])] + g["recent_commits"][:10] + ["hot files (6 months): " + ", ".join("%s(%d)" % x for x in g["churn_last_6_months"][:8])])
    return "\n".join(o)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Inventory a repo in documentation reading order.")
    ap.add_argument("repo", help="path to the repository root")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--max-files", type=int, default=20000)
    args = ap.parse_args(argv)
    if not os.path.isdir(args.repo):
        print("error: not a directory: %s" % args.repo, file=sys.stderr)
        return 2
    inv = inventory(args.repo, args.max_files)
    print(json.dumps(inv, indent=2) if args.json else render(inv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
