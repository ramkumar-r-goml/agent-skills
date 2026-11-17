# Sources and licenses

Every outside source this skill draws on, its license, and what was taken. Last updated 2026-11-17. This is a record for maintainers, not legal advice.

## Rules

- Permissive licenses (MIT, Apache-2.0, BSD, CC0, CC BY) may be reused with the attribution they require.
- Share-alike or copyleft licenses (CC BY-SA, GPL), non-commercial or no-derivatives licenses, and sources with no stated license are never copied. Ideas only, rewritten in this skill's words.
- "Idea only" means: the concept or the name of a pattern or section was used. No sentences, tables, or examples were copied.
- "Checked" says how the license was confirmed: `page` (read on the source), `search` (reported by search results on 2026-11-17), or `memory` (not re-checked in this pass, confirm before relying on it).

## Added in the redesign: documentation styles

Used for `references/doc-styles.md`.

| Source | License | Checked | What was taken |
|---|---|---|---|
| [arc42](https://arc42.org/overview) | CC BY-SA 4.0 | search | Idea only: that the template has twelve areas and what each covers, in this skill's words. Exact headings are left to the developer's template |
| [C4 model](https://c4model.com/) | CC BY 4.0 | search (secondary sources) | Idea only: the four levels and the supporting diagram kinds |
| IEEE 1016-2009, Software design descriptions | Copyright IEEE, paid standard | search | Idea only: the kinds of content an SDD holds and the names of common viewpoints. Its status is inactive |
| ISO/IEC/IEEE 29148:2018, Requirements engineering | Copyright ISO/IEC/IEEE, paid standard | search | Idea only: the general shape of an SRS. It replaced IEEE 830 |
| ISO/IEC/IEEE 29119-3:2021, Test documentation | Copyright ISO/IEC/IEEE, paid standard | search | Idea only: the kinds of test document |
| ISO/IEC/IEEE 15289:2019, Content of life-cycle information items | Copyright ISO/IEC/IEEE, paid standard | search | Idea only: confirmed that document kinds are meant to be selected and tailored |
| ISO/IEC/IEEE 42010, Architecture description; Kruchten, "4+1 view model" (1995) | Copyright ISO/IEC/IEEE; journal article | memory | Idea only: stakeholders, concerns, viewpoints, views; the five view names |
| [MIL-STD-498](https://en.wikipedia.org/wiki/MIL-STD-498) | US Department of Defense standard, cancelled 1998 | search | Idea only: document acronyms (SDD, IDD, DBDD, SVD, SUM, STP, STR) and that the set is tailored per project |
| OWASP threat modeling material; Threat Modeling Manifesto | OWASP content is generally CC BY-SA 4.0 | memory | Idea only: data flow diagram elements, trust boundaries, STRIDE as a checklist |
| Data dictionary guides (university and open-data handbooks found by search) | Mixed, not checked | search | Idea only: the usual per-field attributes |
| [Write the Docs: Docs as Code](https://www.writethedocs.org/guide/docs-as-code/) | Not checked | search | Idea only: the workflow elements |
| HLD and LLD, handover checklists, SDK documentation guides (vendor blogs found by search) | Mixed, mostly all rights reserved | search | Idea only: common section names. No text used |

## Added in the redesign: AI writing patterns

Used for the additions planned in `references/slop-catalog.md`. Each new pattern is described and exemplified in this skill's own words.

| Source | License | Checked | What was taken |
|---|---|---|---|
| [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) | MIT | page | Idea only: false agency, narrator-at-a-distance voice |
| [tropes.fyi, tropes.md](https://tropes.fyi/tropes-md) | None stated | page | Idea only: tie-back endings, self-echo, compulsive counting, appeal to familiarity, forced analogies, premise stacking, one-point dilution, question-word headings, "despite its challenges" formula, false vulnerability. No text copied, because there is no license |

## Back-filled: sources already listed in `docs/research.md`

`docs/research.md` describes these as sources of rules and ideas. This table adds the license.

| Source | License | Checked | What was taken |
|---|---|---|---|
| [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) | CC BY-SA 4.0 (Wikipedia text) | memory | Idea only, per `research.md`: pattern categories and the list of unreliable indicators. See open question 1 |
| [blader/humanizer](https://github.com/blader/humanizer) | MIT | search | Idea only, per `research.md` (read through a summary): strength tiers, voice calibration, when not to act |
| [anthropics/skills, doc-coauthoring](https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring) | Apache-2.0 | memory | Idea only: the reader test |
| [Diataxis](https://diataxis.fr/) | CC BY-SA 4.0 | memory | Idea only: the four documentation kinds |
| [Google developer documentation style guide](https://developers.google.com/style) and docguide | CC BY 4.0 | memory | Idea only: procedure and placeholder rules |
| [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/welcome/) | Copyright Microsoft | memory | Idea only |
| [Write the Docs guide](https://www.writethedocs.org/guide/) | Not checked | memory | Idea only |
| [Google SRE book](https://sre.google/sre-book/postmortem-culture/); Software Engineering at Google | CC BY-NC-ND 4.0 | memory | Idea only |
| [MADR](https://adr.github.io/madr/) | MIT or CC0-1.0 | memory | Adapted: the ADR template's section names in `references/types/adr.md` |
| [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) | MIT | memory | Adapted: change categories in `references/types/changelog.md` |
| [Command Line Interface Guidelines](https://clig.dev/) | CC BY-SA 4.0 | memory | Idea only |
| [Agent Skills specification](https://agentskills.io/specification) and vendor skill docs | Not checked | memory | Idea only: format limits |
| arXiv 2602.11988; GitHub blog on agents.md; agents.md; llmstxt.org; AWS prescriptive guidance; DORA; OpenAPI best practices; pandoc manual | Mixed | memory | Facts and findings cited, no text used |

## Attribution text

Nothing is copied verbatim, so no license here requires a notice. The `NOTICE` file credits the two adapted templates and the pattern sources as a courtesy.

- MADR: "ADR template adapted from MADR (https://adr.github.io/madr/), MIT or CC0-1.0."
- Keep a Changelog: "Change categories follow Keep a Changelog 1.1.0 (https://keepachangelog.com), MIT, by Olivier Lacan."
- humanizer: "Some pattern ideas come from blader/humanizer (MIT)."
- stop-slop: "Some pattern ideas come from hardikpandya/stop-slop (MIT), by Hardik Pandya."

## Open questions

1. `references/slop-catalog.md` was written before this register existed. It has not been compared line by line with the Wikipedia page. Word lists and pattern names are not a concern. If any full sentences or examples were copied from Wikipedia, that file would need CC BY-SA attribution and share-alike terms, or a rewrite of those lines.
2. Rows marked `memory` should be confirmed on the source before a public release.
3. arc42 headings: this skill paraphrases the twelve areas. Using the exact arc42 heading names with credit is common practice, but the template is CC BY-SA 4.0, so that choice is left to the maintainer.
