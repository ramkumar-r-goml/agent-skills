# Redesign notes

## Keep, change, drop (step 1)

1. Keep: the evidence-first rule and `references/verification.md`. It is the skill's main defense against invented facts.
2. Keep: `references/slop-catalog.md`, `scripts/slop_scan.py`, `references/style-rules.md`, `references/senior-engineer-writing.md`. Add only patterns the catalog lacks.
3. Keep: the 21 type files in `references/types/`, `verify_refs.py`, the evals, and the gotchas list.
4. Change: the 9-step checklist with "skip nothing" becomes a 5-stage flow (intake, evidence, draft, check, deliver) that the developer can shorten.
5. Change: intake moves from four chat questions to an editable `docs-brief.md`, with chat questions as the fallback.
6. Change: "document everything" stops being a bullet under "Push back". A single overall technical document becomes the default for a vague request.
7. Change: the evidence ledger becomes a light claim-and-source habit. Unknowns are marked `To confirm` and listed at the end.
8. Change: `references/diagrams.md` covers three cases: existing diagrams, new diagrams, no diagrams.
9. Add: `references/doc-styles.md` (about 30 styles mapped to the type files), `references/outlines.md` (default tables of contents and the rules for a developer's own), `templates/`, `docs/sources-and-licenses.md`, `NOTICE`.
10. Drop from SKILL.md, keep in references: the long pattern list, script flags, and the plan gate. Scripts become optional everywhere.
