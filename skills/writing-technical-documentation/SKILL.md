---
name: writing-technical-documentation
description: 'Writes, rewrites, audits, and exports technical documentation for software projects from evidence in the code: READMEs, architecture overviews, design docs, ADRs, API and CLI reference, runbooks, onboarding guides, tutorials, how-tos, postmortems, migration guides, changelogs, docstrings, and AGENTS.md or CLAUDE.md files. Use when the user asks to document, explain in writing, or write up code, a repo, a system, an API, a decision, a process, or an incident; to check docs that may be stale or wrong, or update them after a code change; to make docs sound less like AI; or to convert docs to or from Word, PDF, or HTML with pandoc. Applies even if they never say "technical documentation". Not for marketing copy, blog posts, or general essays.'
---

# Writing technical documentation

Every sentence must carry a fact, a decision, an instruction, or a warning the reader can act on or check. AI-sounding prose is the symptom of having no specific facts, so the order of work is: gather evidence, write only what it supports, then scan for leftover patterns. A sentence that would still be true of a different project is empty: give it a name, number, path, command, or failure mode from this project, or delete it.

A short correct document beats a long one that drifts. Outdated docs are worse than missing ones, because readers trust them.

## Running the scripts

Paths in this skill are relative to this skill's folder. Agents usually run from the user's project, so put this folder's path in front: `python3 <skill-dir>/scripts/repo_inventory.py .`. The scripts use only the Python standard library, are read-only unless noted, and explain themselves with `--help`. If Python is unavailable, do the same checks by hand from the reference files.

## Choose the mode

| The user wants | Mode | Do this |
|---|---|---|
| A new or rewritten document | Write | The full workflow below |
| A small change: one docstring, one section, a fix | Small edit | Read the code it touches, make the change, run the checks in steps 5 and 6. Skip the plan gate |
| To know what is wrong with existing docs | Audit | Read-only. Follow `references/audit-and-maintain.md` section 1 |
| Docs brought in line with a code change | Update | `scripts/doc_audit.py <repo> --changed-since <ref>`, then `references/audit-and-maintain.md` section 3 |
| To know which docs a repo needs | Plan | `references/audit-and-maintain.md` section 2 |
| Prose that sounds less like AI | Clean | See "Cleaning a draft" below |
| Word, PDF, or HTML output, or old files turned into Markdown | Convert | `scripts/export_doc.py doctor`, then `references/pandoc.md` |
| Docs checks in CI | Automate | Suggest from `references/docs-ci.md`; add only with approval |

## Write workflow

Copy this checklist and track it. Skip nothing except what the mode table allows, because each step catches what the others miss.

```
- [ ] 0. Intake: type, reader, scope, destination
- [ ] 1. Inventory the repo, then read in order
- [ ] 2. Keep an evidence ledger
- [ ] 3. Plan and get approval (anything over a page)
- [ ] 4. Draft from the ledger and the type's template
- [ ] 5. Verify: run verify_refs, run commands, fix, repeat until clean
- [ ] 6. Prose pass: run slop_scan, manual tests, fix, rescan
- [ ] 7. Reader test, then cut
- [ ] 8. Confirm the path, deliver, report
```

### 0. Intake

Infer what you can from the request and the repo. Ask about the rest in one short message, with at most four questions. Settle the document type (table below), the reader and their next action ("on-call engineer at 2 a.m.", "client architect reviewing a design"), the scope, and where it goes. A project's own style guide, glossary, or template overrides this skill's defaults: use it and note where they differ.

### 1. Read the code in order

```bash
python3 scripts/repo_inventory.py <repo>
```

Read in this order, and stop each tier once you have what the document needs. Details and per-ecosystem files are in `references/reading-order.md`.

1. Agent and contributor instructions
2. README and existing docs, as claims to verify and never as facts
3. Manifests and build definitions
4. Runtime and deploy config, IaC, CI
5. Boundaries: entry points, routes, CLI, events, what it reads, writes, and calls
6. Tests: names, fixtures, and assertions show intended behavior
7. Core logic, along one execution path at a time
8. Git history for odd code, to learn why

Skip lockfiles, generated and vendored code, and build output. Stay read-only by default: tests and `--help` are normally fine, but ask before installs, servers, migrations, or anything with side effects. Never copy secret values from `.env` or config into notes or docs.

### 2. Keep an evidence ledger

Record each fact you may use in a scratch file outside the repo:

```
claim | evidence (path:line, command and output, test name) | status
Server listens on port 8081 | src/server.py:14 | verified
Worker retries with backoff | inferred from delay calc at worker.py:58 | inferred
p99 under 50 ms | README only | unverified
```

Only `verified` claims go in as plain statements. Word `inferred` claims as inference. `unverified` claims get verified, get marked `[unverified: what is needed]` in the draft, or get dropped. Never fill a gap with a plausible guess. See `references/verification.md` for what counts as evidence.

### 3. Plan, then wait

For anything over a page, show the plan before drafting, because a document built on a wrong assumption is expensive to unwind and easy to trust:

- Type, reader, and purpose, in a sentence each
- Outline, with one line per section stating the fact or decision it carries
- Open questions and `unverified` items that block sections
- Files you will create or change
- What the doc should not paper over: dead code, drift between docs and code, missing tests, a security smell

Wait for approval. If the user already said to proceed without checking, state your assumptions in two lines and continue.

### 4. Draft

Read the type's file from the table, and read `references/style-rules.md`. For any explanation, design doc, or ADR, read `references/senior-engineer-writing.md` too. Templates are starting points: delete sections with no project-specific content, and never fill a section to satisfy a template.

- One document type per page. Link between tutorial, how-to, reference, and explanation.
- Answer first. The first lines say what this is, who it is for, and what to do or know. Put the first working command or the main decision near the top.
- Conditions before instructions. One action per step. State the expected result after steps that can fail.
- Use tables for facts along two axes, lists for parallel items and sequences, and prose for reasoning.
- Give exact values: versions, defaults, limits, units, ports, env var names, error strings, exit codes.
- State decisions with the reason and the rejected alternative. Show failure modes: what breaks, how it looks, how to fix it.
- Prefer the real thing to a description: a command and its output, a config excerpt with its path.
- Write timeless text. Use versions or dates in place of "currently", "new", "now", or "soon".
- Add a diagram only when relationships are the point: read `references/diagrams.md`.

### 5. Verify, in a loop

```bash
python3 scripts/verify_refs.py <doc.md> --repo <repo> --commands
```

1. Fix each error and warning, or confirm it is a false alarm, and rerun until clean. A clean run only proves that names exist. It does not prove sentences about them are true.
2. Execute every command and code sample you can run safely (the `--commands` list gives each a risk class). For the rest, check flags against `--help` or the source. Record what ran and what did not.
3. Walk the setup path as the reader will, in the order written, starting from the files the doc names. See the first gotcha.
4. Re-derive every number, default, and name from source, and compare the draft with the ledger.

Zero fabricated paths, flags, functions, packages, versions, quotes, or URLs is the bar. See `references/verification.md`.

### 6. Prose pass, in a loop

```bash
python3 scripts/slop_scan.py <doc.md>
```

Fix findings by replacing the vague claim with the specific fact, because swapping one stock word for another keeps the emptiness. Then read the structure, tone, and technical-doc sections of `references/slop-catalog.md`, and check what no script can see: synonym cycling, restated points, invented concept labels, unproven adjectives, euphemisms. Rewrites often add new tells, so rescan.

Apply these tests from `references/senior-engineer-writing.md`: delete test (what does the reader lose without this sentence?), interchangeability test, so-what test, and term inventory (one name per concept).

### 7. Reader test, then cut

For anything over a page, write 5 to 10 questions a real reader would ask, and answer them using only the document. A fresh subagent is the best reader if you have one and the user is fine with the cost. Each wrong answer is a gap: see `references/verification.md` section 9. For setup steps, follow them from a clean clone with approval. Then delete every sentence that fails the delete test.

### 8. Deliver and report

Confirm path and filename unless the user gave them. Create new files, and do not restructure existing docs or edit source comments without approval. When updating a doc, change what is wrong or missing, keep the author's structure and voice, and summarize the diff. Close with these lines, dropping any that do not apply:

```
Wrote: <path> (<doc type>, <approx length>)
Verified by: <what you ran or traced>
Unverified: <list, with what would confirm each>
Found in code or old docs: <problems worth the user's attention>
```

## Document types

To choose, ask what the reader is doing right now. Learning by doing: tutorial. Getting a task done: how-to. Looking up a fact: reference. Understanding why: explanation. A page that tries to be two of these fails both readers.

| Type | Read |
|---|---|
| README | `references/types/readme.md` |
| Architecture overview | `references/types/architecture.md` |
| Design doc, RFC | `references/types/design-doc.md` |
| ADR | `references/types/adr.md` |
| Runbook | `references/types/runbook.md` |
| API reference | `references/types/api-reference.md` |
| CLI reference | `references/types/cli-reference.md` |
| Onboarding guide | `references/types/onboarding.md` |
| Tutorial | `references/types/tutorial.md` |
| How-to guide | `references/types/how-to.md` |
| Explanation or concept page | `references/types/explanation.md` |
| Troubleshooting guide | `references/types/troubleshooting.md` |
| Changelog, release notes | `references/types/changelog.md` |
| Migration or upgrade guide | `references/types/migration.md` |
| Postmortem | `references/types/postmortem.md` |
| CONTRIBUTING, SECURITY | `references/types/contributing-security.md` |
| Glossary | `references/types/glossary.md` |
| Docstrings, code comments | `references/types/docstrings.md` |
| AGENTS.md, CLAUDE.md, llms.txt, docs for RAG | `references/types/agent-instructions.md` |
| Model card, LLM or agent flow | `references/types/ai-systems.md` |
| Infrastructure and operations | `references/types/infrastructure.md` |

## Patterns to avoid while drafting

Models write these by default, so keep them in mind from the first sentence. The full catalog is `references/slop-catalog.md`.

<!-- slop-scan: off -->
1. Stock vocabulary: delve, tapestry, landscape, realm, testament, pivotal, crucial, robust, seamless, comprehensive, leverage, harness, showcase, underscore, foster, streamline, unlock, empower, ecosystem, journey, cutting-edge.
2. Negative parallelism: "It's not X, it's Y", "not just X but Y", and "Y rather than X" as a habit. State the true thing.
3. Self-answered questions ("The result? Faster builds.") and dramatic fragments.
4. Trailing participle filler: ", ensuring robust performance", ", highlighting its importance".
5. Significance inflation: "plays a crucial role", "marks a pivotal moment". Give the fact that earns the weight.
6. Copula avoidance: use "is" and "has" in place of "serves as", "stands as", "boasts".
7. Preamble and recap: "This guide covers", "In summary", "Key takeaways". Start with content, and end when it ends.
8. Filler openers and hedge stacks: "It's worth noting", "can potentially help".
9. Vague attribution: "experts say", "studies show", "industry best practice". Name the source or own the claim.
10. Rule of three by default. Use the number of items that exist.
11. Formatting tells: bold-lead bullets ("**Speed:** ..."), bold in running prose, emojis, title case headings, em dashes, unicode arrows, curly quotes.
12. Synonym cycling. One name per concept, and use the code's name.
13. Unproven adjectives and amplifiers: fast, scalable, secure, elegant, very, truly. Give the number or the mechanism.
14. Condescension: simply, just, easy, obviously. Euphemism: "encountered challenges" means it broke.
15. Invented experience and leaked assistant text: "we were thrilled", "I hope this helps", "Would you like me to".
<!-- slop-scan: on -->

Do not over-police. Correct grammar, a formal register, a table, or one transition word is not a defect. Clusters are the signal.

## Gotchas

Each of these has misled agents writing documentation.

- Test the reader's path, not your shortcut. A scratch database or a variable you set yourself makes a broken quick start look fine. Follow the steps in the order written, using the config file the doc tells the reader to copy. Example files often hold values that work in only one environment, such as a container path, and task runners often do not load `.env`. If you cannot run a step, trace it: what does each step set, and what does the next one read? Anything a command needs goes before that command.
- `last_verified` means you ran it. If you only read the code, write `last_verified: not run; read against <commit>`, and say which commands did not run, because a reader at 2 a.m. will trust a date.
- The README is usually the least reliable file in the repo. Check its ports, commands, env vars, and service names against code, and report each contradiction as a finding, even when the user asked only for a rewrite.
- Finding a name in a doc is not evidence. Search source and config. A second document repeating a claim is the same claim.
- Example output must be captured. Output written from imagination reads as real, so if you cannot run the command, say the block is illustrative, or leave the output out.
- Runbooks, SECURITY files, and onboarding guides tempt you to invent owners, channels, dashboards, SLAs, and response times. Mark the gap, and never guess: a false contact costs more than a blank.
- Never paste secrets. Name variables and leave values out, even in examples, and tell the user if you find a committed secret.
- A task runner in a subdirectory is not a root command. Say which directory each command runs from.
- Get today's date from the system before writing a date into a document.
- Do not narrate your process in the document. "Verified by", ledger notes, and what you ran go in your closing message. The document keeps marked gaps and one `last_verified` line, which is the only place to say what did not run.
- A generated or long AGENTS.md can hurt. A 2026 study measured higher cost and no better success, so keep it to commands and non-standard rules: see `references/types/agent-instructions.md`.
- A low `slop_scan` score does not make a document good, and a high one does not prove AI wrote it. Never accuse an author.

## Push back or limit scope

- If the code does not support a claim the user wants documented, say so and document what is true.
- If the repo has no tests, no clear entry point, or contradicting config, record that as a finding.
- If asked to document everything, propose a prioritized order and build one document at a time: `references/audit-and-maintain.md` section 2.
- For lookup facts, prefer reference generated from contracts (OpenAPI, type hints, schemas). Say what would rot fastest if a doc will not be maintained.

## Cleaning a draft

For "make this sound less like AI", or editing text someone wrote or generated:

1. Run `scripts/slop_scan.py` and read the report. If there is a repo, check facts against it as well.
2. Find the vague claims behind the patterns. Ask for missing facts when the repo or context cannot supply them. Never invent them.
3. Rewrite with specifics. Keep the meaning and every supported claim, keep the voice where it is human, and leave quotations, names, and identifiers alone.
4. Rescan, show before and after for the largest changes, and report the score change and the facts still missing.

## Reference files

Read a file when its trigger applies. Do not read them all.

| File | Read it when |
|---|---|
| `references/types/<type>.md` | Writing that document type; see the table above |
| `references/reading-order.md` | Step 1; unfamiliar stack, monorepo, AI or AWS project; deciding what to skip |
| `references/verification.md` | Steps 2, 5, and 7; deciding what you may run |
| `references/style-rules.md` | Drafting; procedures, code samples, headings, placeholders, accessibility |
| `references/senior-engineer-writing.md` | Any explanation, design doc, or ADR; before-and-after rewrites; the quality tests |
| `references/slop-catalog.md` | Step 6; cleaning a draft; auditing prose |
| `references/diagrams.md` | Adding a diagram; Mermaid syntax and alt text |
| `references/audit-and-maintain.md` | Auditing, planning a doc set, updating for a code change, pruning |
| `references/pandoc.md` | Word, PDF, or HTML output; importing old documents; pandoc in a pipeline |
| `references/docs-ci.md` | A team wants docs checks in CI |

| Script | Use |
|---|---|
| `scripts/repo_inventory.py` | List a repo in reading order: languages, instructions, docs, manifests, config, entry points, routes, env vars, tests, git |
| `scripts/verify_refs.py` | Check a doc against a repo: links, anchors, paths, names, flags, make and npm targets, compose services, ledger citations; list commands with risk classes |
| `scripts/slop_scan.py` | Scan prose for AI patterns and style notes; score, clusters, CI annotations |
| `scripts/doc_audit.py` | Audit a whole doc set, or list docs affected by a diff |
| `scripts/export_doc.py` | Convert with pandoc: Markdown to Word, PDF, or HTML; old documents to Markdown; Word style templates |
| `assets/pandoc/`, `assets/ci/` | Pandoc defaults, filter, and styles; docs CI workflow and Vale rules, to copy into a project |
