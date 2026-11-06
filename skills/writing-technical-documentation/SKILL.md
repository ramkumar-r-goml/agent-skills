---
name: writing-technical-documentation
description: 'Writes, rewrites, and audits technical documentation for software projects the way a senior engineer would: READMEs, architecture overviews, design docs, ADRs, API and CLI reference, runbooks, onboarding guides, how-tos, tutorials, postmortems, migration guides, docstrings, AGENTS.md and CLAUDE.md files. Reads the codebase in a fixed order (instructions, manifests, config, boundaries, tests, core logic), traces every claim to evidence, and strips AI writing patterns (stock vocabulary, negative parallelism, significance inflation, hedging, empty summaries, bold-lead bullets, em-dash overuse) with an exhaustive catalog and a scanner script. Use whenever the user asks to document, explain in writing, or write up code, a repo, a system, an API, an architecture, a decision, a process, or an incident, or asks to make existing docs sound less like AI, even if they never say "technical documentation".'
---

# Writing technical documentation

## Core principle

Every sentence must carry a fact, a decision, an instruction, or a warning that the reader can act on or check. AI-sounding prose is the visible symptom of a deeper failure: the writer did not have specific facts, so the text stayed general. Banned-word lists catch symptoms. Specificity fixes the cause. So the work is in this order: gather evidence, then write only what the evidence supports, then scan for leftover patterns.

A sentence that would still be true if you swapped in a different project is empty. Rewrite it with a name, a number, a path, a command, or a failure mode from this project, or delete it.

## Workflow

Follow the phases in order. Two approval gates exist because documentation written from a wrong assumption is expensive to unwind and easy to trust. Do not skip them for anything beyond a few lines of change.

### Phase 0: Intake (ask only what the repo cannot answer)

Settle these. Infer what you can from the request and repo, ask about the rest in one short message with at most four questions.

1. Document type (see `references/doc-types.md`). If the request names one, use it. If it could fit several, pick the one that serves the reader's moment: learning (tutorial), doing a task (how-to), looking up a fact (reference), understanding why (explanation).
2. Reader: who they are, what they already know, what they are trying to do next. Examples: new teammate on day one, on-call engineer at 2 a.m., client architect reviewing a design, external API consumer.
3. Scope: whole repo, one service, one module, one flow, one decision.
4. Destination and conventions: where the file goes, existing docs layout, existing style guide, house terms. If the project has a style guide or glossary, it overrides `references/style-rules.md`.

If the user supplied a template, client format, or house style, use it and note where this skill's defaults differ.

### Phase 1: Read the code in order

Run the inventory script first. It lists files in reading order and skips noise.

```bash
python3 scripts/repo_inventory.py <repo-path>            # human-readable
python3 scripts/repo_inventory.py <repo-path> --json     # machine-readable
```

Then read in this order, stopping each tier once you have what the document needs. Full detail, per-ecosystem file names, and the skip list are in `references/reading-order.md`.

1. Agent and contributor instructions: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.cursorrules`, `docs/CONTRIBUTING*`
2. `README.md` and existing `docs/`, `ADR`, `rfcs/` folders. Treat every statement as a claim to verify, never as fact.
3. Manifests: `package.json`, `pyproject.toml`, `requirements*.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle*`, `Makefile`, `justfile`, `Taskfile.yml`
4. Runtime and deploy config: `Dockerfile`, `docker-compose*.yml`, `.env.example`, CI workflows, IaC (Terraform, CDK, SAM, CloudFormation, Helm, Kubernetes manifests)
5. Boundaries: entry points, public API surface, CLI arguments, routes, event handlers, scheduled jobs, what the system reads, writes, and calls
6. Tests: names, fixtures, and assertions show intended behavior and edge cases that matter
7. Core logic along one execution path at a time, not file by file
8. Git history for odd code: `git log -S`, `git blame`, merged PR titles, to learn why

Skip lockfiles, generated code, vendored dependencies, build output, minified assets, binaries, and snapshots unless a claim depends on them. Read ranges of large files after grepping, never whole files blindly. Never copy secret values from `.env` or config into notes or docs. Use placeholders.

Read-only by default. Do not run installs, migrations, servers, or anything with side effects without approval. Running tests and `--help` on local tools is normally fine; say what you ran.

### Phase 2: Keep an evidence ledger

While reading, record each fact you may use in a scratch file (not in the repo) with its evidence. Format:

```
claim | evidence (path:line, command + output, test name) | status
```

Status is `verified` (seen in code or output), `inferred` (reasoned from code, not observed), or `unverified` (from existing docs or assumption). Only `verified` claims go into the document as plain statements. `inferred` claims are worded as inference. `unverified` claims either get verified, get marked `[unverified: <what is needed>]`, or are dropped. Never fill a gap with a plausible guess. Details and claim-type rules are in `references/verification.md`.

### Phase 3: Plan, then gate

Produce a short plan and show it to the user before drafting anything longer than a page:

- Document type, reader, and purpose in one sentence each
- Outline with one line per section stating the fact or decision it will carry
- Open questions and `unverified` items that block sections
- Files you will create or change, and files you will not touch
- Anything you found that the doc should not paper over (dead code, drift between README and code, missing tests, security smell). Say it plainly in the plan.

**Gate 1:** Wait for approval of the plan. If the user already said to proceed without checking, state your assumptions in two lines and continue.

### Phase 4: Draft

Write from the ledger using the rules below, the template in `references/templates.md`, and the style rules in `references/style-rules.md`. For how senior engineers structure and phrase documents, read `references/senior-engineer-writing.md` before drafting any explanation, design doc, or ADR.

**Structure rules**
- One document type per page. Do not mix steps, reference tables, and rationale in one flow. Link between them.
- Answer first. The first lines say what this is, who it is for, and what to do or know. No preamble, no table of contents narration.
- Put the first working command or the main decision near the top.
- Put conditions before instructions. One action per step. State the expected result after steps that can fail.
- Use a table for facts that vary along two axes. Use a list for parallel items or sequences. Use prose for reasoning. Do not put a list under every heading.
- Use headings that name the content ("Rotate the signing key"), in sentence case. Not "Overview of Key Considerations".
- Match depth to the reader. Define a term once, where the reader first needs it, then use that exact term every time.

**Content rules**
- State decisions with their reason and the rejected alternative. State non-goals that someone might reasonably expect.
- Give exact values: versions, defaults, limits, units, ports, env var names, error strings, exit codes, timeouts.
- Show failure modes: what breaks, how it looks, how to fix it.
- Prefer the real thing over a description of it: a command and its output, a config excerpt with the path, a request and response.
- Say what you did not verify and why. Honest gaps beat invented detail.
- Explain why in comments and prose. The code already says what.
- Write timeless text. No "currently", "new", "now", "soon", "latest", "in the future" in product or system docs. Use versions or dates when time matters.
- Do not document planned features as if they exist.

### Phase 5: Verify

1. Run the reference checker on the draft. It checks paths, links, anchors, env vars, identifiers, and `npm run` or `make` targets against the repo.
   ```bash
   python3 scripts/verify_refs.py <doc.md> --repo <repo-path>
   ```
2. Execute every command and code sample you can run safely. For the rest, check flags with `--help` or the source. Record what ran.
3. Re-derive every number, default, and name from source. Compare your claim list to the ledger.
4. Fix or mark anything missing. Zero fabricated paths, flags, functions, packages, versions, quotes, or URLs is the bar.

### Phase 6: Pattern scan and structure pass

Run the scanner, then do the manual passes it cannot do.

```bash
python3 scripts/slop_scan.py <doc.md>              # report with fixes
python3 scripts/slop_scan.py <doc.md> --max-score 10   # nonzero exit if too high
```

Fix findings by replacing the vague claim with the specific fact, not by swapping a synonym. Swapping "delve" for "dive" keeps the emptiness and hides the evidence. Then read `references/slop-catalog.md` sections on structure, tone, and technical-doc patterns and check the draft for the patterns no script can see: synonym cycling, restated points, invented concept labels, fractal summaries, unproven adjectives, euphemisms, fake experience.

Do the tests from `references/senior-engineer-writing.md`: delete test, interchangeability test, so-what test, false-work test, term inventory.

### Phase 7: Cut, then deliver

Delete every sentence that fails the delete test. Reread once, aloud in your head, for rhythm: sentence length should vary naturally, paragraphs should follow the idea and not a template.

**Gate 2:** Before writing into the repo, confirm path and filename unless the user already specified them. Create new files. Do not overwrite or restructure existing docs, and do not edit source comments, without approval. When updating an existing doc, change what is wrong or missing, keep the author's structure and voice, and show the diff summary.

Deliver the file in the format the host environment calls for, defaulting to Markdown in the project's docs location. Then report in a few lines: what was written, what was verified and how, what remains `unverified`, and any problems found in the code or old docs. No recap of the document.

## Pattern rules to apply while drafting

The exhaustive catalog is `references/slop-catalog.md`. Keep these in working memory while writing so you avoid them in the first place:

1. No stock vocabulary: delve, tapestry, landscape (abstract), realm, testament, pivotal, crucial, vital, robust, seamless, comprehensive, multifaceted, nuanced, vibrant, meticulous, intricate, foster, leverage, harness, showcase, underscore, highlight (as verb), streamline, unlock, empower, elevate, embark, navigate (abstract), ecosystem, paradigm, synergy, journey, beacon, cornerstone, interplay, groundbreaking, transformative, cutting-edge, game-changer.
2. No negative parallelism ("It's not X, it's Y", "Not X. Not Y. Just Z.", "not only X but also Y" used as flourish). State the true thing.
3. No self-answered questions ("The result? Faster builds.").
4. No trailing participle filler (", highlighting its importance", ", ensuring robust performance").
5. No significance inflation ("marks a pivotal moment", "plays a crucial role", "serves as a testament"). Give the fact that earns the weight.
6. Use "is" and "has". Not "serves as", "stands as", "boasts", "features" for plain statements.
7. No preamble ("In this section we will...") and no recap ("In summary", "Overall", "Key takeaways").
8. No hedge stacks, no filler openers ("It's worth noting", "It's important to note", "Needless to say").
9. No vague attribution ("experts say", "studies show", "industry reports"). Name the source or own the claim.
10. No rule of three by default. Use the number of items that exist.
11. No bold-lead bullets, no bold in running prose, no emojis, no title case headings, no unicode arrows or curly quotes in source files.
12. Em dashes: none by default. Use a period, comma, colon, or parentheses.
13. No synonym cycling. One name per concept, used everywhere.
14. No amplifiers (very, truly, incredibly, really) and no unproven adjectives (robust, scalable, elegant, powerful) without the number or behavior that earns them.
15. No condescension (simply, just, easy, obviously, of course, straightforward).
16. No euphemism. "It broke" and "it lost two hours of data" beat "encountered challenges".
17. No invented experience or feelings ("I find this fascinating", "we were thrilled").
18. No marketing phrases (best-in-class, end-to-end solution, enterprise-grade, battle-tested, production-ready without a definition).
19. No time parasites ("In today's fast-paced world", "now more than ever", "in the age of AI").
20. No leaked assistant text ("Would you like me to", "I hope this helps", "As an AI").

One instance of a pattern in a long document is a yellow flag. Clusters are the signal. Do not over-police: perfect grammar, a formal register, or a single transition word is not a defect.

## When to push back or limit scope

- If the code does not support a claim the user wants documented, say so and document what is true.
- If the repo has no tests, no entry-point clarity, or contradicting config, record that as a finding. Do not smooth it over.
- If the request is a full documentation set for a large repo, propose a prioritized order (README, architecture overview, runbook for the riskiest flow, reference generated from code) and build it one document at a time. Generated reference from typed contracts (OpenAPI, type hints, schemas) beats hand-written prose for lookup facts.
- If documentation will not be maintained, say what would rot fastest and put it in generated or tested form (runnable examples, generated reference, tests that double as examples).
- Suggest, but never add without approval, docs checks in CI: a prose linter such as Vale, link checking, and executable examples. A sample config is in `references/verification.md`.

## Documentation for AI agents

When the target reader is an agent (AGENTS.md, CLAUDE.md, llms.txt, per-page Markdown): put build, test, lint, and run commands first and exact; list architecture in one short section with directory purposes; state conventions that are not obvious from code; state what not to touch; link to deeper docs instead of pasting them. Keep it short, since every line costs context. See `references/doc-types.md`.

## Output format for the final message

Keep the closing message to these lines, and drop any that do not apply:

```
Wrote: <path> (<doc type>, <approx length>)
Verified by: <what you ran or traced>
Unverified: <list, with what would confirm each>
Found in code or old docs: <problems worth the user's attention>
```

## Reference index

Read a reference file when its trigger applies. Each has a table of contents.

| File | Read it when |
|---|---|
| `references/reading-order.md` | Starting Phase 1; unfamiliar stack; monorepo; AI or AWS projects; deciding what to skip |
| `references/doc-types.md` | Choosing or structuring a document type; docstrings; AGENTS.md; runbooks; postmortems |
| `references/templates.md` | Drafting a README, architecture overview, ADR, design doc, runbook, API reference, onboarding guide, how-to, tutorial, postmortem, migration guide, changelog, model card |
| `references/style-rules.md` | Any drafting; procedures, code samples, headings, inclusive and accessible wording |
| `references/senior-engineer-writing.md` | Any explanation, design doc, ADR, or review; before-and-after rewrites; the quality tests |
| `references/verification.md` | Phase 2 and Phase 5; commands, numbers, links, staleness, docs checks in CI |
| `references/slop-catalog.md` | Phase 6; auditing existing text; cleaning a user's draft |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/repo_inventory.py` | Inventory a repo in reading order: instruction files, docs, manifests, config, entry points, routes, tests, source layout, env vars, git summary |
| `scripts/verify_refs.py` | Check a Markdown doc against a repo: paths, links, anchors, identifiers, env vars, package scripts, make targets |
| `scripts/slop_scan.py` | Scan prose for AI patterns, style issues, and structure statistics; weighted score; JSON output; exit code for CI |

All scripts use only the Python standard library. Run with `--help` for options.

## Cleaning a user's existing draft

When asked to "make this sound less like AI" or to edit text the user wrote or generated:

1. Run `scripts/slop_scan.py` on it and read the report.
2. Find the vague claims behind the patterns. Ask the user for the missing facts if the repo or context cannot supply them. Never invent them to fill the hole.
3. Rewrite with specifics, keep their meaning, structure, and voice where the voice is human, and show before and after for the largest changes.
4. Rescan. Report the score change and what facts were still missing.
