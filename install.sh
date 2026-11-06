#!/usr/bin/env bash
# Install skills from this repo for coding agents.
# Usage: ./install.sh [--project DIR | --user] [--copy] [--skill NAME] [claude cursor codex ...]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SCOPE=user; DIR=""; MODE=link; ONLY=""; AGENTS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --project) SCOPE=project; DIR="${2:?dir required}"; shift 2;;
    --user) SCOPE=user; shift;;
    --copy) MODE=copy; shift;;
    --skill) ONLY="${2:?name required}"; shift 2;;
    -h|--help) sed -n '2,3p' "$0"; exit 0;;
    *) AGENTS+=("$1"); shift;;
  esac
done
[ ${#AGENTS[@]} -eq 0 ] && AGENTS=(claude cursor codex)
base=$([ "$SCOPE" = project ] && echo "$DIR" || echo "$HOME")
for src in "$HERE"/skills/*/; do
  name="$(basename "$src")"
  [ -n "$ONLY" ] && [ "$ONLY" != "$name" ] && continue
  for a in "${AGENTS[@]}"; do
    case "$a" in
      claude) sub=".claude/skills";; cursor) sub=".cursor/skills";; codex) sub=".agents/skills";;
      *) echo "unknown agent: $a" >&2; exit 1;;
    esac
    dest="$base/$sub"; mkdir -p "$dest"; rm -rf "$dest/$name"
    if [ "$MODE" = copy ]; then cp -R "${src%/}" "$dest/"; else ln -s "${src%/}" "$dest/$name"; fi
    echo "$a: $dest/$name ($MODE)"
  done
done
