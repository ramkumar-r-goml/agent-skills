#!/usr/bin/env python3
"""Check a Markdown document's references against a repository.

Usage:
    python3 verify_refs.py DOC.md --repo REPO [--json] [--strict]

Checks:
  - relative links and images resolve to files
  - #anchors resolve to headings (in the doc or the linked Markdown file)
  - paths in backticks that look like repo paths exist
  - `npm run X`, `yarn X`, `pnpm X`, `make X` targets exist
  - UPPER_CASE env var names in backticks appear somewhere in the repo
  - code identifiers in backticks (functions, classes) appear in the repo
  - fenced bash blocks: first word of each command is a known script or tool path
Reports unresolved items as problems. A hit means "could not find"; confirm by
hand before concluding the doc is wrong. Exit 1 if problems exist and --strict.
Standard library only.
"""
import argparse
import json
import os
import re
import sys

SKIP_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "__pycache__", "target", "build", "dist", ".next", ".terraform", "cdk.out"}
TEXT_SUFFIXES = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".cs", ".sh", ".yml", ".yaml", ".json", ".toml", ".md", ".txt", ".cfg", ".ini", ".env", ".tf", ".sql", ".proto", ".graphql", ".html", ".css", ".conf", "Makefile", "Dockerfile")
PATH_RE = re.compile(r"^(?:\./)?[\w@.\-]+(?:/[\w@.\-*{}]+)+/?$|^(?:\./)?[\w.\-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|kt|rb|php|cs|sh|ya?ml|json|toml|md|txt|cfg|ini|tf|sql|proto|graphql|html|css|conf)$")
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*(?:\(\))?$")
ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]{3,}$")
COMMON_WORDS = {
    "true", "false", "null", "none", "undefined", "string", "int", "bool", "list", "dict", "json", "yaml", "http", "https",
    "get", "post", "put", "patch", "delete", "main", "test", "tests", "src", "docs", "self", "this", "args", "kwargs",
    "id", "name", "type", "value", "key", "data", "error", "result", "response", "request", "config", "env",
}
COMMON_ENV = {"PATH", "HOME", "USER", "PWD", "SHELL", "LANG", "TERM", "TMPDIR", "DEBUG", "CI", "TZ", "EDITOR", "PYTHONPATH", "NODE_ENV", "GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "JSON", "HTTP", "HTTPS", "TODO", "NOTE", "WARNING", "SELECT", "FROM", "WHERE", "NULL", "TRUE", "FALSE"}


def slugify(heading):
    h = heading.strip().lower()
    h = re.sub(r"[`*_~]", "", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = re.sub(r"[^\w\s-]", "", h, flags=re.U)
    h = re.sub(r"\s+", "-", h)
    return h


def headings(text):
    slugs, counts = set(), {}
    in_code = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if m:
            s = slugify(m.group(1))
            n = counts.get(s, 0)
            slugs.add(s if n == 0 else "%s-%d" % (s, n))
            counts[s] = n + 1
    for m in re.finditer(r'<a\s+(?:name|id)="([^"]+)"', text):
        slugs.add(m.group(1))
    return slugs


class Repo:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.files = []
        self.blob = None
        for dp, dn, fn in os.walk(self.root):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            for f in fn:
                self.files.append(os.path.relpath(os.path.join(dp, f), self.root).replace(os.sep, "/"))
        self.fileset = set(self.files)

    def exists(self, rel):
        rel = rel.strip("/").lstrip("./") if rel.startswith("./") else rel.strip("/")
        if rel in self.fileset:
            return True
        p = os.path.join(self.root, rel)
        return os.path.exists(p)

    def glob_exists(self, pattern):
        rx = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
        rx = re.sub(r"\\\{[^}]*\\\}", ".*", rx)
        r = re.compile("^" + rx + "$")
        return any(r.match(f) for f in self.files)

    def text(self):
        if self.blob is None:
            parts = []
            for f in self.files:
                if f.endswith(TEXT_SUFFIXES) or "/" not in f:
                    p = os.path.join(self.root, f)
                    try:
                        if os.path.getsize(p) < 1_500_000:
                            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                                parts.append(fh.read())
                    except OSError:
                        pass
            self.blob = "\n".join(parts)
        return self.blob

    def package_scripts(self):
        p = os.path.join(self.root, "package.json")
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as fh:
                    return set((json.load(fh).get("scripts") or {}).keys())
            except (OSError, ValueError):
                return set()
        return set()

    def make_targets(self):
        p = os.path.join(self.root, "Makefile")
        if os.path.isfile(p):
            with open(p, encoding="utf-8", errors="ignore") as fh:
                return set(re.findall(r"^([A-Za-z0-9_.-]+)\s*:(?!=)", fh.read(), re.M))
        return set()


def split_code(text):
    """Return (prose_with_code_blanked, list of (lang, body, start_line))."""
    blocks = []
    out = []
    in_code, lang, buf, start = False, "", [], 0
    for i, line in enumerate(text.splitlines(), 1):
        if re.match(r"^\s*(```|~~~)", line):
            if not in_code:
                in_code, lang, buf, start = True, line.strip().lstrip("`~").strip().lower(), [], i
            else:
                blocks.append((lang, "\n".join(buf), start))
                in_code = False
            out.append("")
            continue
        if in_code:
            buf.append(line)
            out.append("")
        else:
            out.append(line)
    return "\n".join(out), blocks


def check(doc_path, repo_path):
    problems, notes = [], []
    with open(doc_path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    repo = Repo(repo_path)
    doc_dir = os.path.dirname(os.path.abspath(doc_path))
    prose, blocks = split_code(text)
    own_slugs = headings(text)

    def add(kind, line, item, msg):
        problems.append({"kind": kind, "line": line, "item": item, "message": msg})

    # Links
    for i, line in enumerate(prose.splitlines(), 1):
        for m in re.finditer(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", line):
            target = m.group(1)
            if re.match(r"^(?:https?:|mailto:|tel:|data:)", target):
                notes.append({"kind": "external-link", "line": i, "item": target, "message": "external link not checked offline; fetch to confirm"})
                continue
            path, _, frag = target.partition("#")
            if not path:
                if frag and frag not in own_slugs:
                    add("anchor", i, target, "no heading in this document produces this anchor")
                continue
            full = os.path.normpath(os.path.join(doc_dir, path))
            if not os.path.exists(full):
                alt = os.path.normpath(os.path.join(repo.root, path.lstrip("/")))
                if not os.path.exists(alt):
                    add("link", i, target, "file does not exist")
                    continue
                full = alt
            if frag and full.endswith(".md") and os.path.isfile(full):
                with open(full, encoding="utf-8", errors="replace") as fh:
                    if frag not in headings(fh.read()):
                        add("anchor", i, target, "anchor not found in linked file")

    # Inline code tokens
    seen = set()
    for i, line in enumerate(prose.splitlines(), 1):
        for m in re.finditer(r"`([^`\n]+)`", line):
            tok = m.group(1).strip()
            if tok in seen:
                continue
            seen.add(tok)
            cm = re.match(r"^(npm run|yarn|pnpm(?: run)?|bun run)\s+([\w:.-]+)", tok)
            if cm:
                scripts = repo.package_scripts()
                if scripts and cm.group(2) not in scripts and cm.group(2) not in ("install", "test", "start", "build", "add", "init", "ci"):
                    add("npm-script", i, tok, "script not in package.json (found: %s)" % ", ".join(sorted(scripts)[:8]))
                continue
            cm = re.match(r"^make\s+([\w.-]+)", tok)
            if cm:
                targets = repo.make_targets()
                if targets and cm.group(1) not in targets:
                    add("make-target", i, tok, "target not in Makefile (found: %s)" % ", ".join(sorted(targets)[:8]))
                continue
            if " " in tok or tok.startswith(("-", "$", "http", "<", "/")) and not PATH_RE.match(tok):
                continue
            if PATH_RE.match(tok):
                if any(c in tok for c in "<>$"):
                    continue
                if "*" in tok or "{" in tok:
                    if not repo.glob_exists(tok.lstrip("./")):
                        add("path", i, tok, "no files match this pattern")
                elif not repo.exists(tok):
                    base = os.path.basename(tok.rstrip("/"))
                    similar = [f for f in repo.files if f.endswith("/" + base) or f == base][:3]
                    hint = " (similar: %s)" % ", ".join(similar) if similar else ""
                    add("path", i, tok, "path not found in repo" + hint)
                continue
            if ENV_RE.match(tok) and tok not in COMMON_ENV:
                if tok not in repo.text():
                    add("env-var", i, tok, "name does not appear anywhere in repo files")
                continue
            if IDENT_RE.match(tok) and tok.lower().rstrip("()") not in COMMON_WORDS and len(tok) > 3:
                name = tok.rstrip("()").split(".")[-1]
                if not re.search(r"\b" + re.escape(name) + r"\b", repo.text()):
                    add("identifier", i, tok, "identifier not found in repo files")

    # Bash blocks
    for lang, body, start in blocks:
        if lang not in ("bash", "sh", "shell", "console", "zsh", ""):
            continue
        for j, line in enumerate(body.splitlines()):
            cmd = line.strip().lstrip("$ ").strip()
            if not cmd or cmd.startswith("#"):
                continue
            first = cmd.split()[0]
            if first.startswith(("./", "scripts/", "bin/")) or re.match(r"^[\w./-]+\.(?:sh|py)$", first):
                if "<" in first or "$" in first:
                    continue
                if not repo.exists(first):
                    add("script", start + j + 1, first, "script path not found in repo")
            cm = re.match(r"^(?:npm run|yarn|pnpm run|pnpm)\s+([\w:.-]+)", cmd)
            if cm:
                scripts = repo.package_scripts()
                if scripts and cm.group(1) not in scripts and cm.group(1) not in ("install", "test", "start", "build", "add", "init", "ci", "i"):
                    add("npm-script", start + j + 1, cmd, "script not in package.json")
            cm = re.match(r"^make\s+([\w.-]+)", cmd)
            if cm:
                targets = repo.make_targets()
                if targets and cm.group(1) not in targets:
                    add("make-target", start + j + 1, cmd, "target not in Makefile")
            for flag_file in re.findall(r"(?:-f|--file|--config|-c)\s+([\w./-]+\.(?:ya?ml|json|toml|ini|conf))", cmd):
                if not repo.exists(flag_file):
                    add("path", start + j + 1, flag_file, "file referenced by command not found")
        notes.append({"kind": "code-block", "line": start, "item": lang or "(no language)", "message": "run this block when safe; this script does not execute code"})
        if not lang:
            add("style", start, "(fence)", "code block has no language tag")

    return {"doc": doc_path, "repo": repo.root, "problems": problems, "notes_count": len(notes), "checked_tokens": len(seen)}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verify a Markdown doc's references against a repo.")
    ap.add_argument("doc")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 when problems are found")
    args = ap.parse_args(argv)
    if not os.path.isfile(args.doc) or not os.path.isdir(args.repo):
        print("error: doc must be a file and --repo a directory", file=sys.stderr)
        return 2
    res = check(args.doc, args.repo)
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print("Doc: %s\nRepo: %s\nTokens checked: %d   problems: %d" % (res["doc"], res["repo"], res["checked_tokens"], len(res["problems"])))
        for p in sorted(res["problems"], key=lambda x: x["line"]):
            print("  L%-4d %-12s %s -> %s" % (p["line"], p["kind"], p["item"], p["message"]))
        if not res["problems"]:
            print("  no unresolved references")
        print("Note: external URLs and code execution are not checked here. Fetch links and run examples separately.")
    return 1 if (res["problems"] and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
