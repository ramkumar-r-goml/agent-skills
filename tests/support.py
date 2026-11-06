"""Shared paths and helpers for the skill's tests. Standard library only."""
import contextlib
import io
import os
import stat
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "writing-technical-documentation")
SCRIPTS = os.path.join(SKILL, "scripts")
FIXTURE = os.path.join(ROOT, "evals", "writing-technical-documentation", "files", "orderflow")
FIXTURE_SECRET = "orderflow-fixture-secret-7f3a9c"

sys.dont_write_bytecode = True
sys.path.insert(0, SCRIPTS)


def run_main(main, argv):
    """Call a script's main() in process. Returns (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def write_files(root, files):
    for rel, content in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)


def git(root, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
    subprocess.run(["git", "-C", root] + list(args), check=True, capture_output=True, env=env)


def temp_repo(files, commit=True):
    """Create a throwaway git repo. Returns a TemporaryDirectory; use .name for its path."""
    tmp = tempfile.TemporaryDirectory()
    write_files(tmp.name, files)
    git(tmp.name, "init", "-q", "-b", "main")
    if commit:
        git(tmp.name, "add", "-A")
        git(tmp.name, "commit", "-q", "-m", "first")
    return tmp


def make_executable(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
