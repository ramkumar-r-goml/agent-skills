# Skills

This repo holds Agent Skills packages (https://agentskills.io/specification) under `skills/`.

| Skill | Use it when |
|---|---|
| `skills/writing-technical-documentation/` | Preparing one overall technical document for a project, with the developer's own table of contents or a default; writing, rewriting, or auditing READMEs, architecture overviews, design docs, ADRs, API or CLI reference, runbooks, onboarding guides, postmortems, migration guides, docstrings, or AGENTS.md files; making docs sound less like AI; converting docs to or from Word, PDF, or HTML. |
| `skills/developer-handover-from-proposal/` | Given a client proposal, SOW, or scope document, writing a developer handover or kickoff brief (3 pages maximum) for the engineer who will build the project. |

Read a skill's `SKILL.md` first. Read files in its `references/` folder only when `SKILL.md` points to them.

## Working on this repo

- Test: `python3 -m unittest discover -s tests`
- Test one file: `python3 -m unittest discover -s tests -p "test_slop_scan.py"`
- Scripts use the Python standard library only. Do not add dependencies, because users run them with no install step.
- Keep `SKILL.md` frontmatter to `name` and `description`, since some agents ignore other keys.
- `evals/writing-technical-documentation/files/orderflow/` is a fixture with seeded errors, including a fake secret in `.env`. Do not fix it.
- After changing a rule in `slop_scan.py`, run `tests/calibrate_slop_scan.py` on human-written docs.
