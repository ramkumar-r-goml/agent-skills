# Changelog

All notable changes to this repo are documented here. This project follows [Semantic Versioning](https://semver.org/). A skill's file layout counts as its public interface.

## [Unreleased]

### Added

- `developer-handover-from-proposal`: turns a client proposal into a developer handover document of at most 3 pages, with a fixed section structure, FIXED / RECOMMENDED / OPEN / POST-PROPOSAL tagging, and checkable acceptance tests.
- `writing-technical-documentation`: one overall technical document as the default for a vague request (`references/types/technical-document.md`), with a table of contents built from the developer's own outline or a default by project kind (`references/outlines.md`).
- `assets/templates/docs-brief.md`, an editable intake file the agent writes and the developer edits before drafting.
- `references/doc-styles.md`, about 35 documentation types and standards (arc42, C4, HLD, LLD, IEEE 1016, SRS, test documentation, threat model, data dictionary, handover, and more) mapped to the type files.
- Diagram guidance for three cases: existing diagrams, new diagrams, none.
- Six AI-writing patterns in `references/slop-catalog.md` (false agency, analogy in place of mechanism, tie-back ending, and others).
- `docs/sources-and-licenses.md` and `NOTICE`. Two eval cases: a vague request and a developer-supplied table of contents.

### Changed

- The nine-step checklist is now five stages with one stop. Scripts are optional, and every check has a by-hand route.
- Unknowns are marked `[To confirm: ...]`. `[unverified: ...]` is still accepted.

## [2.0.0] - 2026-11-06

### Added

- `writing-technical-documentation`: audit, update, and plan modes, with `scripts/doc_audit.py` for reference problems, staleness, drift, duplicates, and missing document types. `--changed-since` lists docs that a diff affects, including docs that still mention a name the diff removed.
- `scripts/export_doc.py`, a pandoc wrapper that converts Markdown to Word, PDF, or HTML, imports old documents, builds Word style templates, and reports missing images and dropped text. `assets/pandoc/` holds its defaults files, Lua filter, and styles.
- `references/pandoc.md`, `references/diagrams.md`, `references/audit-and-maintain.md`, and `references/docs-ci.md`.
- `assets/ci/`: a GitHub Actions workflow, Vale configuration, and an AISlop Vale style.
- `verify_refs.py`: checks `path:line` citations, flags passed to local scripts, compose services, and just and task targets; follows `cd`; lists commands with a risk class; checks evidence ledgers; optionally fetches URLs.
- `slop_scan.py`: directory scans, CI annotations, an allow list, regions marked off, and checks for paired headings, restated headings, uniform sections, hedge density, and newer model vocabulary.
- `repo_inventory.py`: language and doc tooling summaries, CLI and boundary hints, env vars from example files, and main-guard entry points.
- Tests, repo CI, and evals with a seeded fixture repo. Evals stay outside the skill folder, so installs carry about 55 files and no test data.

### Changed

- Split `references/doc-types.md` and `references/templates.md` into one file per document type under `references/types/`, so an agent loads about 50 lines instead of 845.
- `SKILL.md` now routes by mode, carries a checklist and a gotchas section, and scales effort to the size of the request.
- `slop_scan.py` scores AI-writing signals only, and lists style notes separately. Bands are now 8 and 20, calibrated on human-written docs. Under the old scoring, most human READMEs landed in the rewrite band.
- AGENTS.md guidance follows a 2026 study: fewer lines, no repository overviews, and no unedited generated files.
- ADR template follows MADR 4.0. Placeholder rules follow the Google style guide.
- `install.sh` targets `.agents/skills` and `.claude/skills`, and refuses to replace a real folder without `--force`.

### Fixed

- `verify_refs.py` searched the document under check and all other docs, so a made-up name always counted as found. It now searches non-doc files only.
- `verify_refs.py` looked for make targets only in the root Makefile, and treated `application/json` as a file path and trailing shell comments as arguments.
- Anchors for headings with punctuation, setext headings, reference-style links, and nested code fences now parse correctly.
- `repo_inventory.py` no longer lists .NET build output, and its output no longer grows without limit on large repos.

## [1.0.0] - 2026-11-06

First public release.

[Unreleased]: https://github.com/ramkumar-r-goml/agent-skills/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/ramkumar-r-goml/agent-skills/compare/1beec12...v2.0.0
[1.0.0]: https://github.com/ramkumar-r-goml/agent-skills/commit/1beec12
