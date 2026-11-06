# Document types

Contents
1. Choosing a type (Diataxis compass)
2. The four modes
3. README
4. Architecture overview
5. Design doc
6. RFC
7. ADR
8. Runbook
9. API reference
10. CLI reference
11. Onboarding guide
12. Troubleshooting guide
13. Changelog and release notes
14. Migration and upgrade guide
15. Postmortem
16. CONTRIBUTING and SECURITY
17. Glossary
18. Docstrings and code comments
19. AGENTS.md, CLAUDE.md, llms.txt
20. Docs for AI, ML, and agentic systems
21. Infrastructure and operations docs
22. Splitting and linking documents

## 1. Choosing a type

Ask two questions about the reader's moment.

- Are they acting or studying? Acting: they need to get something done. Studying: they need to learn or understand.
- Do they need practice or knowledge? Practice: steps. Knowledge: facts and explanation.

| | Practice | Knowledge |
|---|---|---|
| Studying | Tutorial | Explanation |
| Acting | How-to guide | Reference |

A page that tries to be two of these fails both readers. Split it and link.

## 2. The four modes

**Tutorial.** Purpose: a learner gains skill by doing a guided, safe exercise that works every time. Voice: "we" or "you", encouraging but not chatty. Content: one path, small visible wins, expected output after each step, no choices, no theory beyond one line each. Ends with what they built and where to go next.

**How-to guide.** Purpose: a competent user completes a specific task. Title starts with a verb or "How to". Content: prerequisites, numbered steps, expected results, verification, common failures. Assumes knowledge. No background lectures. Links to reference and explanation.

**Reference.** Purpose: look up exact facts. Structure mirrors the thing described (alphabetical flags, one entry per endpoint, one row per config key). Content: names, types, defaults, constraints, errors, examples. Neutral voice. Complete and consistent. No opinion, no tutorial narrative. Generate from code or schemas where possible.

**Explanation.** Purpose: build understanding of why and how it fits together. Content: context, concepts, design reasons, alternatives and trade-offs, history where it explains the present. Prose is fine here. Can take a position. Avoid steps.

## 3. README

Reader: someone who landed on the repo and has 30 seconds. Answer in order:
1. What it is, in one or two sentences with concrete nouns.
2. Who should use it and when not to.
3. Fastest working path: prerequisites with versions, install, run, expected output.
4. Minimal usage example that does something real.
5. Where to go next: docs, config reference, architecture, contributing.
6. Status and support: maturity, supported versions, license, how to get help.

Keep it a front door. Move depth to `docs/`. Do not include a feature-list of adjectives, badges as decoration, or a table of contents on short files. Every command must run as written from a fresh clone.

## 4. Architecture overview

Reader: a new engineer or reviewer who needs the map. Content:
- One paragraph: the system's purpose and its main constraint.
- Context: users, upstream and downstream systems, trust boundaries.
- Components: each with one sentence of responsibility, its main technology, and its owner or path.
- Key flows: two or three, as numbered paths with file or service references.
- Data: stores, key entities, ownership, retention, consistency model.
- Deployment: environments, regions, how a change ships.
- Cross-cutting: auth, errors, observability, config, scaling limits, cost drivers, security.
- Decisions and trade-offs: link ADRs.
- Known gaps and risks.
A diagram helps if it shows real components and real directions of data. Label arrows with what flows. One diagram per question. Keep a text description beside it for accessibility and diffs. Mermaid or PlantUML source in the repo beats an exported image.

## 5. Design doc

Reader: reviewers deciding whether to approve a plan. Written before building. Length: as short as the decision allows (often 2 to 10 pages). Sections:
- Context and problem, with the evidence that it is a problem (numbers, incidents).
- Goals, and non-goals. A non-goal is something a reader could reasonably expect that you will not do. "Won't make the system crash" is not a non-goal.
- Proposed design with enough detail to implement and to disagree with: components, data model, interfaces, flows, failure handling.
- Alternatives considered, each with the reason it lost.
- Cross-cutting concerns: security, privacy, cost, observability, testing, rollout and rollback, migration, compatibility.
- Risks, open questions, and what would change the decision.
- Milestones if the work is large.
Take a position. A design doc that lists options without choosing is a survey.

## 6. RFC

A design doc with a formal review process and an explicit decision. Add: status (draft, in review, accepted, rejected, withdrawn), authors, reviewers, decision date, and a decision summary at the top.

## 7. ADR (architecture decision record)

One decision per file. Short, dated, numbered, and immutable once accepted. A changed decision gets a new ADR that supersedes the old one, and the old one's status is updated to "superseded by ADR-NNNN". Sections: Title (the decision as a noun phrase or verb phrase), Status, Context (forces and constraints, facts only), Decision (active voice: "We will use..."), Consequences (good, bad, and neutral, including what becomes harder), and optionally Alternatives. A reader a year later should understand why without asking anyone. Write ADRs when a decision is hard to reverse, costly, or likely to be questioned. Store in `docs/adr/NNNN-title.md` unless the repo has a convention.

## 8. Runbook

Reader: an on-call engineer under stress. Rules:
- Start with the trigger: the alert name or symptom this runbook handles.
- State impact and urgency in one line.
- Give diagnosis steps as commands with expected outputs and what each result means.
- Give mitigation first, root cause later. Include rollback.
- Mark dangerous steps. Put the confirmation or the blast radius before the command.
- Include who to escalate to and when, with channels, not personal numbers.
- Include verification: how to know it is fixed.
- Include links to dashboards and logs by exact name or query.
- No prose paragraphs where a numbered step works. Each step is one action.
- Record `last_verified` date and who ran it.
Test the runbook by following it on a non-production system.

## 9. API reference

Per endpoint or function: purpose in one line, method and path or signature, auth, parameters (name, type, required, default, constraints), request example, response example, status codes or errors with causes and fixes, rate limits, idempotency, pagination, side effects, version or deprecation. Generate from OpenAPI, protobuf, GraphQL schema, or type annotations when available, then add what the schema cannot say: semantics, ordering guarantees, gotchas, and examples. Examples must be tested. Keep field descriptions factual ("Unix time in seconds, UTC"), not "the timestamp".

## 10. CLI reference

Name and one-line purpose, synopsis, arguments and flags (name, short form, type, default, env var equivalent), exit codes, stdout versus stderr, examples from common to rare, config file locations and precedence (flags, env, file, defaults), and failure messages with fixes. Verify with `--help` output.

## 11. Onboarding guide

Reader: a new teammate in their first week. Order: what the system does and why it matters, access they need (list what to request and from whom), set up the dev environment (tested commands), run the tests, make a first small change and ship it, map of the codebase, who owns what, where decisions are made, glossary, first-week tasks. Say how long each step takes. Fix drift as you walk it.

## 12. Troubleshooting guide

Organize by symptom as the user sees it (exact error text), not by internal cause. Each entry: symptom, likely causes in order of probability, how to confirm each, fix. Include "if none of these work, collect X and ask Y".

## 13. Changelog and release notes

Changelog (for developers): follows Keep a Changelog style by default: Added, Changed, Deprecated, Removed, Fixed, Security, per version with date. Entries say what changed for the user, not what files were edited. Link issues or PRs. Release notes (for users): highlights, breaking changes first, upgrade steps, known issues.

## 14. Migration and upgrade guide

Start with who must act and the deadline. List breaking changes with before and after code. Provide ordered steps, a rollback path, a way to verify, and common errors. State supported source and target versions exactly. Provide a codemod or script if one exists.

## 15. Postmortem (blameless)

Sections: summary (impact, duration, detection, resolution), timeline in UTC with timestamps, impact (users, requests, money, data), root cause and contributing factors (systems and process, never people), detection and response (what worked, what did not), what went well, where we got lucky, action items with owner, priority, and due date, lessons. Facts first, then analysis. No blame language, no "human error" as a root cause: ask why the system allowed it.

## 16. CONTRIBUTING and SECURITY

CONTRIBUTING: how to set up, run tests, style and commit conventions, branch and PR process, review expectations, how to propose large changes, code of conduct link. SECURITY: supported versions, how to report a vulnerability privately, response time expectations, disclosure policy. Do not invent contact addresses or timelines. Ask or mark unverified.

## 17. Glossary

Alphabetical. Term, one-sentence definition, where it appears in code (path or identifier), and the terms not to use as synonyms. Include project-specific meanings of common words.

## 18. Docstrings and code comments

Docstrings document the contract: what it does (one line, imperative or third person per project convention), parameters with types and units, return value, errors raised, side effects, thread-safety or idempotency when it matters, and one example for non-obvious use. Do not restate the signature in words ("Gets the user. Takes an id and returns a user.").

Comments explain why, not what: hidden constraints, workarounds with the issue link, invariants, surprising behavior, performance trade-offs. Delete comments that narrate the code. Never leave a comment that says what a good name could say. Do not change source comments in a documentation task without approval.

## 19. AGENTS.md, CLAUDE.md, llms.txt

AGENTS.md or CLAUDE.md is an instruction file for coding agents. Keep it short (usually under 150 lines) because every line costs context on every task. Include, in order: one-paragraph project description; exact commands to install, build, test, lint, run (with the single-test form); repo map with directory purposes; conventions not enforced by tooling; things to avoid and why; testing expectations; pointers to deeper docs. Use imperative, concrete, checkable rules. Do not paste long docs or style guides. Do not include things a linter enforces. Do not include secrets. Prefer "run `pnpm test --filter api`" over "run the tests". Nest more specific files in subdirectories when conventions differ there.

llms.txt: a Markdown index at the site root with a title, a short summary, and sections of links with one-line descriptions, so models find the right page. Provide clean Markdown versions of key pages.

## 20. Docs for AI, ML, and agentic systems

Model card or system card: intended use and non-use, model and version, training or fine-tuning data summary, evaluation setup and results with numbers, known limitations and failure modes, safety measures, bias findings, cost and latency, update policy. Prompt documentation: purpose, inputs and variables, expected output format, versioning, tests, known failure cases. Agent documentation: goal, tools with permissions and side effects, loop and stop conditions, memory, human approval points, escalation, evaluation, cost per run, failure handling. Retrieval documentation: sources, chunking, embedding model, index settings, refresh, evaluation of retrieval quality. Say what is non-deterministic.

## 21. Infrastructure and operations docs

Resources and their purpose, naming conventions, environments, deployment pipeline, access model, networking, secrets handling (names only), backups and recovery objectives (RPO and RTO), scaling limits and quotas, cost drivers, monitoring and alerts with thresholds, disaster recovery steps. Use placeholders for account IDs, ARNs, and hostnames unless the user wants them.

## 22. Splitting and linking documents

- One page, one type, one purpose. Link instead of repeating.
- Single source of truth for each fact. If a fact appears twice it will diverge.
- Link text names the destination ("see the retry configuration reference"), not "click here".
- Put reference tables near the code they describe or generate them.
- Add a short index page for a doc set that lists each page with one line.
- Date or version anything that can go stale and give it an owner.
