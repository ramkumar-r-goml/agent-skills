#!/usr/bin/env bash
# Link or copy the skills in this repo into an agent's skills directory.
# Usage: ./install.sh [--project DIR | --user] [--copy] [--force] [--skill NAME] [AGENT ...]
#   AGENT is one of: agents claude windsurf kiro roo (default: agents claude)
#   "agents" is .agents/skills, read by Codex, Cursor, Copilot, Gemini CLI, Cline, OpenCode, and Amp.
#   --project also installs into a repo for the whole team; the default is your user directory.
#   --force replaces an existing copy; otherwise only an existing link is replaced.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SCOPE=user; DIR=""; MODE=link; ONLY=""; FORCE=0; AGENTS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --project) SCOPE=project; DIR="${2:?--project needs a directory}"; shift 2;;
    --user) SCOPE=user; shift;;
    --copy) MODE=copy; shift;;
    --force) FORCE=1; shift;;
    --skill) ONLY="${2:?--skill needs a name}"; shift 2;;
    -h|--help) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    -*) echo "unknown option: $1 (see --help)" >&2; exit 2;;
    *) AGENTS+=("$1"); shift;;
  esac
done
[ ${#AGENTS[@]} -eq 0 ] && AGENTS=(agents claude)
base=$([ "$SCOPE" = project ] && echo "$DIR" || echo "$HOME")
[ -d "$base" ] || { echo "not a directory: $base" >&2; exit 2; }
found=0
for src in "$HERE"/skills/*/; do
  name="$(basename "$src")"
  [ -n "$ONLY" ] && [ "$ONLY" != "$name" ] && continue
  found=1
  for a in "${AGENTS[@]}"; do
    case "$a" in
      agents) sub=".agents/skills";;
      claude) sub=".claude/skills";;
      windsurf) sub=".windsurf/skills";;
      kiro) sub=".kiro/skills";;
      roo) sub=".roo/skills";;
      *) echo "unknown agent: $a (use agents, claude, windsurf, kiro, or roo)" >&2; exit 2;;
    esac
    dest="$base/$sub/$name"
    mkdir -p "$base/$sub"
    if [ -e "$dest" ] && [ ! -L "$dest" ] && [ "$FORCE" -ne 1 ]; then
      echo "$dest exists and is not a link; pass --force to replace it" >&2
      exit 1
    fi
    rm -rf "$dest"
    if [ "$MODE" = copy ]; then cp -R "${src%/}" "$dest"; else ln -s "${src%/}" "$dest"; fi
    echo "$a: $dest ($MODE)"
  done
done
[ "$found" -eq 1 ] || { echo "no skill named $ONLY" >&2; exit 2; }
