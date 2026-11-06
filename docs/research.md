# Research behind writing-technical-documentation

What each rule in the skill rests on, checked on 2026-11-06. Update this page when a source changes. Sources marked "summary" were read through a fetch tool's summary rather than in full, so check the original before quoting a number from them.

## Skill format and authoring

| Source | What changed in the skill |
|---|---|
| [Agent Skills specification](https://agentskills.io/specification) | Frontmatter limits, 500-line and 5,000-token budget, `references/` loaded on demand |
| [Best practices for skill creators](https://agentskills.io/skill-creation/best-practices) | Gotchas section, checklist, validation loops, defaults over menus, saying when to read each file |
| [Using scripts in skills](https://agentskills.io/skill-creation/using-scripts) | Scripts are non-interactive, explain themselves with `--help`, separate data from diagnostics, have distinct exit codes and bounded output |
| [Optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) | Description states user intent, and adds a boundary (not for marketing copy or essays) |
| [Evaluating skills](https://agentskills.io/skill-creation/evaluating-skills) | Evals with a baseline, and assertions added after seeing output |
| [Claude skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Third-person description, one level of references, contents on long files, scripts that solve problems instead of deferring them |
| [skills CLI docs](https://github.com/vercel-labs/skills/blob/main/docs/commands.md) and [agent paths](https://github.com/vercel-labs/skills/blob/main/docs/agents.md) | Install and update commands. Its installer copies dotfiles and excludes only `metadata.json`, `.git`, and `__pycache__` |
| [Cursor](https://cursor.com/docs/context/skills), [Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), [Codex](https://learn.chatgpt.com/docs/build-skills) docs | Install table in the README. All three read `.agents/skills/`. Cursor and Copilot also read `.claude/skills/`. Codex budgets its skill list to about 2 percent of context, which favors shorter descriptions |

## Documentation practice

| Source | What changed in the skill |
|---|---|
| [Diataxis](https://diataxis.fr/) and its [workflow](https://diataxis.fr/how-to-use-diataxis/) | Type chooser; no empty structure up front; improve one page at a time |
| [Google documentation best practices](https://google.github.io/styleguide/docguide/best_practices.html) | Minimum viable docs, update docs with code, delete dead docs, where each fact belongs |
| [Google developer style guide](https://developers.google.com/style/highlights): [procedures](https://developers.google.com/style/procedures), [placeholders](https://developers.google.com/style/placeholders) | Order of a complex step; no "run the following command"; placeholder format, which corrected the old `YOUR_API_KEY` example |
| [Microsoft style: top 10 tips](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice) | Confirms sentence case, serial comma, get to the point. The skill's no-em-dash rule is its own choice, and differs from both guides |
| [Write the Docs principles](https://www.writethedocs.org/guide/writing/docs-principles/) | Current, nearby, unique, discoverable; outdated docs are worse than missing ones |
| [DORA documentation quality](https://dora.dev/capabilities/documentation-quality/) (summary) | Audit dimensions of clear, findable, and reliable; measuring through a short survey |
| [Software Engineering at Google, chapter 10](https://abseil.io/resources/swe-book/html/ch10.html) (summary) | Seekers and stumblers; three kinds of review; owners and freshness dates; landing pages as navigation |
| [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/) (summary) | When to skip a design doc, length, what a non-goal is, alternatives as a key section, docs as records after shipping |
| [MADR 4.0](https://adr.github.io/madr/) (summary) | ADR template, `docs/decisions/` location and naming, status values |
| [C4 model](https://c4model.com/diagrams) and [notation](https://c4model.com/diagrams/notation) (summary) | Context and container diagrams are enough for most teams; title, key, type, technology, one-way labeled arrows |
| [Mermaid accessibility](https://mermaid.js.org/config/accessibility.html), [syntax](https://mermaid.js.org/intro/syntax-reference.html) | `accTitle` and `accDescr`; quoting rules; the `end` keyword trap |
| [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) | Changelog rules, including Unreleased, ISO dates, and yanked releases |
| [Google SRE: postmortem culture](https://sre.google/sre-book/postmortem-culture/) | When to write one, blameless rules, keeping out user identity, review checks |
| [Command Line Interface Guidelines](https://clig.dev/) | CLI reference leads with examples; configuration precedence; stdout and stderr |
| [OpenAPI best practices](https://learn.openapis.org/best-practices.html) | One source of truth; source control; CI validation; a hand-edited generated file becomes the source |

## Docs for agents

| Source | What changed in the skill |
|---|---|
| [Gloaguen and colleagues, "Evaluating AGENTS.md", arXiv 2602.11988](https://arxiv.org/abs/2602.11988) (summary) | Context files generally did not improve task success and raised inference cost by over 20 percent. Agents follow them, and repository overviews do not help. This reversed the old advice to include a repo map |
| [GitHub: lessons from over 2,500 agents.md files](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) (summary) | Commands early, one real snippet, three-tier boundaries. It reports patterns, not measured outcomes |
| [agents.md](https://agents.md/), [llmstxt.org](https://llmstxt.org/) | Nearest file wins; llms.txt format and testing it with a question |
| [AWS: documentation for RAG](https://docs.aws.amazon.com/prescriptive-guidance/latest/writing-best-practices-rag/best-practices.html) | Stand-alone sections and defined abbreviations. Its advice on per-section summaries and avoiding tables is scoped to retrieval-first documents, since it conflicts with human-reader rules |

## AI writing patterns

| Source | What changed in the skill |
|---|---|
| [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) | Vocabulary by model era; "Y rather than X"; paired headings; tool artifacts; placeholder dates. Its list of ineffective indicators moved transition words out of the score |
| [Humanizer skill](https://github.com/blader/humanizer) (summary) | Strength tiers, voice calibration, staged run-ups, restated headings, and when not to act |
| [Anthropic doc-coauthoring skill](https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring) (summary) | Reader test: predict reader questions, and answer them with no context |

## Pandoc

Read from the [manual](https://pandoc.org/MANUAL.html) and [changelog](https://github.com/jgm/pandoc/blob/main/changelog.md) at version 3.13, and the default `reference.docx` source.

| Fact | Version |
|---|---|
| `--embed-resources` replaces `--self-contained` | 2.19 |
| `custom-style` on tables | 2.19 in the reader, 3.4 in the docx writer |
| Typst writer and PDF engine | 3.1.2 |
| `alerts` extension, on by default for `gfm` | 3.1.10 |
| `--figure-caption-position` and `--table-caption-position` | 3.4 |
| `--syntax-highlighting` replaces `--highlight-style` and `--no-highlight` | 3.8 |

A forum answer and an older issue both say tables cannot take a custom style. The manual and changelog show that this is out of date, so the skill follows those.

The claim that pandoc's Source Code style turns word wrap off comes from reading pandoc's writer behavior, and the export tests check it in the output.

Tested on macOS (arm64) with pandoc 3.12.1 and Typst 0.15.1, and Vale 3.24.0 for the Vale kit. Word output was checked by reading its XML, reading it back with pandoc, and rendering it with macOS preview. WeasyPrint, XeLaTeX, a real `mmdc`, the Word application, and the GitHub Actions workflows have not been run: the Mermaid path was tested with a stub renderer.

## Scanner calibration

`tests/calibrate_slop_scan.py` measured `slop_scan.py` on 115 human-written documents of at least 150 words: 42 READMEs from npm packages and 73 pages of npm's reference docs.

| Scoring | Median | Clean | Rewrite band |
|---|---|---|---|
| Old rules, READMEs only | 19.2 | 3 of 43 | 27 of 43 |
| Old rules, reference pages only | 13.5 | 6 of 75 | 28 of 75 |
| New rules, all 115 | 0.0 | 104 (90 percent) | 4 (3 percent) |

The old score mostly measured ordinary style: "just", "in order to", thin reference headings, and repeated phrases. The new score moves those to style notes, caps each category at a weight of 8 so one habit cannot dominate, and counts transition words only by density.

Limits: this corpus is small, skews toward JavaScript tooling, and has no labeled AI-written set. It shows the false-alarm rate on human text. It does not measure how much AI text the scanner catches. Any score is a prompt to read closely, and never evidence of authorship.

## Agent evaluation

Fresh agents on Sonnet 5.5 ran four tasks on the fixture repo, once with the previous skill and once with this one. `tests/grade_evals.py` scored them on assertions, and the outputs were also read by hand.

| Task | Previous skill | This skill, first run | After fixes |
|---|---|---|---|
| Rewrite a stale README | 14 of 15 | 13 of 15 | 15 of 15 |
| Audit docs before a handover | 12 of 15 | 15 of 15 | not rerun |
| Write a runbook | 10 of 10 | 9 of 10 | 10 of 10 |
| Add an AGENTS.md | 7 of 9 | 9 of 9 | not rerun |
| Total | 43 of 49 | 46 of 49 | |

Both versions caught every seeded fact error, including the double-charge risk, so the previous skill was already good at evidence. This version's gain is structure: audit findings with severity and `file:line` evidence and a list of what was not checked, and an AGENTS.md of 35 lines with no repository tour against 52 lines with one. Cost was about the same, at about 53,000 tokens and 70 seconds per run.

The first run also found two weaknesses, now fixed in the gotchas. The README agent tested against a scratch database, so it missed a Docker-only path in `.env.example`. The runbook agent wrote a `last_verified` date when its `docker compose` commands had not run.

Limits: one run per configuration, on a single small fixture, so read this as a direction and not a measurement. The same author wrote the skill and the assertions, and some assertions were added after reading outputs. The "after fixes" runs repeat only the two tasks that lost.
