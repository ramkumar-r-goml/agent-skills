# Skills

This repo holds Agent Skills packages (https://agentskills.io/specification) under `skills/`.

| Skill | Use it when |
|---|---|
| `skills/writing-technical-documentation/` | Writing, rewriting or auditing READMEs, architecture overviews, design docs, ADRs, API/CLI reference, runbooks, onboarding guides, postmortems, migration guides, docstrings, or AGENTS.md files; or making existing docs sound less like AI. |

How to use a skill: read its `SKILL.md` first. Load files in its `references/` folder only when `SKILL.md` points to them.

Helper scripts for writing-technical-documentation (Python 3, standard library only), run from the repo root:
- `python3 skills/writing-technical-documentation/scripts/repo_inventory.py <repo>` lists manifests, entry points and instruction files.
- `python3 skills/writing-technical-documentation/scripts/verify_refs.py <doc> --repo <repo>` checks that paths and commands named in a doc exist.
- `python3 skills/writing-technical-documentation/scripts/slop_scan.py <doc>` flags AI writing patterns.
