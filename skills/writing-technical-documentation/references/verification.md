# Verification

Contents
1. Why verification is the main defense
2. Evidence by claim type
3. What you may run
4. Hallucination checklist
5. Evidence ledger format
6. Marking unverified items
7. Links and references
8. Staleness and drift
9. Second-pass reviewer protocol
10. Docs checks in CI (suggest only with approval)
11. Sample Vale config
12. Final verification report

## 1. Why verification is the main defense

AI-written documentation fails in two ways: it sounds generic, and it states things that are false with full confidence. The second does more damage. A fluent wrong flag name costs a reader an hour. Verify before polishing. A well-polished wrong sentence is worse than a rough true one.

## 2. Evidence by claim type

| Claim | Acceptable evidence | Not acceptable |
|---|---|---|
| Command works | Ran it, saw output; or source of the CLI definition plus `--help` | Memory, similar tools |
| Flag, option, parameter | CLI definition, `--help`, schema, function signature | Docs of a different version |
| File or path exists | `ls`, glob, the inventory script | Assumed convention |
| Function, class, endpoint | grep result with file and line | Name that sounds right |
| Default value | Config schema or code line | README |
| Version, runtime | Manifest, CI config, lockfile for exact resolved version | "Latest" |
| Env var | Code reading it, or `.env.example` | Naming convention |
| Behavior | Code path trace, test, or run | Reading a function name |
| Performance number | Benchmark output with date and setup | Estimate presented as fact |
| Cost number | Pricing page seen today, with date and region | Memory |
| Security property | Code and config evidence for each part | "Follows best practices" |
| Dependency behavior | Official docs for the pinned version | Training memory |
| Architecture diagram | Config, IaC, or deployed service list | Old diagram |
| Quote or citation | The source text seen | Paraphrase presented as quote |
| URL | Fetched and seen | Constructed from a pattern |
| Ownership, SLA, contact | The user or an owner file | Invented |
| Date or history | Git log, PR, ADR | Guess |

## 3. What you may run

Normally safe without asking: `ls`, `cat`, grep, `git log`/`blame`/`show`, `--help`, `--version`, listing tests, linting, type-checking, running unit tests that do not touch external systems, running the doc scripts in this skill.

Ask first: installs, builds that download artifacts, starting servers or containers, running integration tests, any command that contacts external systems, writes outside scratch space, or uses credentials, migrations, scripts of unknown effect, anything that costs money (cloud APIs, LLM calls at scale).

Never: run commands that delete, deploy, publish, or modify production; use secrets you found; paste secret values into output.

Say in the final report what you ran and in what environment. If you could not run something, say so and mark dependent claims `unverified`.

## 4. Hallucination checklist

Check each of these in every draft:
- Invented flags, options, subcommands, config keys, env vars
- Invented functions, classes, modules, files, directories
- Packages that do not exist, or exist under a different name (typosquat risk when suggesting installs)
- Wrong versions, wrong default values, wrong units
- Endpoints, status codes, or error messages that do not appear in code
- Features from a similar tool attributed to this one
- Behavior from a different version
- Example output that was written from imagination, not captured
- Fabricated statistics, benchmarks, dates, quotes, citations, URLs
- Fabricated ownership, contacts, SLAs, compliance claims (SOC 2, HIPAA, GDPR)
- Claims about security or reliability without mechanisms
- Described architecture that does not match the deployed one
- Steps that skip a prerequisite you had set up on your machine
- Planned work described as shipped

## 5. Evidence ledger format

Keep a scratch file outside the repo:

```
| # | Claim | Evidence | Status |
|---|---|---|---|
| 1 | Service listens on port 8080 | src/server.ts:14 | verified |
| 2 | Retries 3 times | src/client.ts:52 (MAX_RETRIES = 3) | verified |
| 3 | Uses exponential backoff | inferred from delay calc at client.ts:58 | inferred |
| 4 | p99 under 50 ms | README only | unverified |
```

Only verified claims appear as plain statements. Inferred claims use careful wording once. Unverified claims are verified, marked, or removed.

## 6. Marking unverified items

Inline: `[unverified: <what is needed to confirm>]`. Keep them few and specific. Collect them in the final report. A doc delivered for publication should have none, or each should be agreed with the user. Do not use hedge words as a substitute for marking.

## 7. Links and references

- `scripts/verify_refs.py` checks relative links, anchors, repo paths, code identifiers in backticks, env vars, package scripts, and make targets.
- For external URLs: fetch with the web tools when available and confirm content matches the claim. Report broken or unverifiable links. Never include a URL you did not see.
- For citations: confirm title, author, and date from the source. If you cannot, cite less.

## 8. Staleness and drift

- Add a `last_verified: YYYY-MM-DD` line (front matter or footer) to runbooks, setup guides, and architecture overviews, plus the commit hash or version it was verified against.
- Prefer generated reference (OpenAPI, CLI help dumps, schema docs, typedoc, pydoc) over hand-copied tables.
- Prefer executable docs: doctests, tested code blocks, notebooks that run in CI.
- Co-locate docs with code. A PR that changes behavior changes the doc.
- Say what rots fastest in the final report: version numbers, screenshots, step lists, diagrams, hardcoded names.
- Delete wrong docs. A short correct doc beats a long wrong one.
- Drift detection tools exist (code-linked docs checkers, stale-docs bots). Mention only if the user wants maintenance advice.

## 9. Second-pass reviewer protocol

For high-stakes documents (security, runbooks for production, public API reference), run a second pass that did not write the draft. If subagents are available and the user wants the extra pass, give the reviewer only the draft and the repo path, and ask it to:
1. Pick 15 claims at random, including every command, number, and path in the first screen, and verify each.
2. Follow the main procedure literally on a clean copy.
3. Report each failure with evidence, and any claim it could not verify.
4. Flag generic sentences that fail the interchangeability test.
Do not let the reviewer rewrite. Fix the findings yourself. Without subagents, do the same in a separate pass with fresh eyes: switch to the reader's role and use only the doc.

## 10. Docs checks in CI (suggest only with approval)

Propose, do not add, unless the user asks:
- Markdown lint (markdownlint) for structure.
- Vale for style rules, with a project vocabulary file.
- Link checker (lychee, markdown-link-check) for dead links.
- Code block tests (pytest `--doctest-glob`, mdtest, `cargo test --doc`, Go examples).
- Spell check (codespell, cspell) with a project dictionary.
- OpenAPI validation (spectral).
- A check that fails when public API changes without a docs change.
- A scheduled job that reruns setup instructions on a clean runner.

## 11. Sample Vale config

```ini
# .vale.ini
StylesPath = .vale/styles
MinAlertLevel = suggestion
Vocab = Project

Packages = Google

[*.md]
BasedOnStyles = Vale, Google
Google.Passive = suggestion
Google.Will = warning
Google.Contractions = NO
Google.Headings = warning
Google.WordList = warning
```

Put project terms in `.vale/styles/config/vocabularies/Project/accept.txt` (words to accept) and `reject.txt` (words to flag). Add custom rules for AI patterns if desired, for example a `substitution` or `existence` rule listing words such as delve, tapestry, seamless, and robust.

## 12. Final verification report

Short, in the closing message:
- Verified by: commands run and files traced
- Unverified: each item with what would confirm it
- Not run, and why
- Drift found: old doc claims that the code contradicts
- Fast-rotting content: what to regenerate or retest, and when
