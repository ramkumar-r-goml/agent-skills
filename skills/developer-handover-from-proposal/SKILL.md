---
name: developer-handover-from-proposal
description: 'Turns a client project proposal into a developer handover document of at most 3 pages that tells the developer what to build, with what, in what order, and how done is checked. Use when the user provides a proposal, SOW, or scope document and asks for a developer handover, implementation guide, or kickoff brief for the engineer who will build it.'
---

# Developer handover from a proposal

The proposal is written for leadership. The handover is written for the developer who will build the project. A developer who has not read the proposal must be able to start on day 1 and know what to build, why, with what, in what order, and how done is checked.

## Inputs

- Required: the proposal (docx or pdf). Read all of it, including diagrams. Open each image and read it.
- Optional: a prerequisite tracker, kickoff notes, API docs, accelerator docs, earlier handovers. Anything agreed after the proposal is a post-proposal decision.
- If the proposal is missing, ask for it. Do not write from memory or from a similar project.

## Process

1. Read the proposal and its diagrams. Build a private fact sheet: goal, users and actors, data sources, integrations, stack, milestones, deliverables, success criteria, out of scope, assumptions, dependencies, prerequisites.
2. Compare the proposal text with its diagrams. Note mismatches and any component that appears only in a diagram.
3. Classify every item:
   - FIXED: stated in the proposal or confirmed by the customer.
   - RECOMMENDED: a delivery-team choice at developer level.
   - OPEN: not decided.
   - POST-PROPOSAL: agreed later. Needs a source and a date.
4. List the gaps a developer would hit in week 1: undefined metrics or formulas, missing values (timezone, schedule, recipients, IDs), unclear roles or approval flow, unnamed owners, unresolved choices.
5. If the user is present, ask about the gaps that block the draft, in one batch. Otherwise write them into the doc as OPEN items.
6. Draft, check against the rules below, then build the document.

## Structure (3 pages maximum)

1. **Context and success.** 4 to 6 lines: the client, the problem, who consumes the output, and what a successful final demo looks like. Give the reason behind key constraints. Example: shared multi-tenant data is why account isolation is strict.
2. **Resources and contacts.** A table of links (API docs, samples, templates, repos, cloud accounts) and owners on both sides. Use TBD for unknowns. Never include secrets.
3. **Architecture.** The components and flow from the proposal diagram, as a short list. Mark each stack choice FIXED or RECOMMENDED. If the team's own accelerators are part of the solution, say where their docs are and who decides whether a part applies. Never write "use if applicable" without naming the decider.
4. **Data, logic and outputs.** Sources and fields. Draft metric definitions with formulas, marked pending customer approval. Time window and timezone. A short sample of the expected output so the quality bar is visible.
5. **Workflow and behavior.** Roles, approval states as a short state list, run triggers, duplicate-run and failure handling, what is automatic and what is gated.
6. **Non-negotiables and non-goals.** One short list each. List only non-goals a developer might plausibly build.
7. **Milestones.** A table of build tasks with one checkable exit criterion per milestone. Match the proposal timeline.
8. **Risks, open items and tests.** Open decisions with a default, an owner and a date. Customer dependencies. Acceptance tests a person can run.

## Rules

- Derive everything from the proposal and the supplied sources. Never invent requirements, values, names, or links. For a missing value write TBD and name an owner.
- Tag post-proposal decisions with source and date, for example: "Email via SES (tracker, 20 Nov)".
- Turn vague wording into a decision or an OPEN item. Avoid "consider", "if possible", and "as applicable".
- Make every acceptance check verifiable. Replace "grounded" or "valid" with a method. Examples: every number in the output matches a computed metric; the HTML passes a named validator.
- State each rule once. Do not repeat scope across sections. Leave project status items such as repo invitations and demo scheduling out of the document.
- Give the reason for important constraints, not only the constraint.
- If the proposal promises a findings or next-phase document, add an instruction to keep a running findings log from week 1.
- Keep the proposal's names and numbering. Do not skip section numbers.
- Style: plain professional English, short sentences, tables for lookups, bullets for lists, no filler, no em-dashes.

## Output

- A Word document (.docx) of at most 3 pages. Write the content in Markdown, then convert with pandoc or the available Word tooling. Convert to PDF and count pages before delivering.
- Title block: client, phase, document name, team, month.
- After delivering, list the OPEN items and anything you could not source, so the author can resolve them.

## Final check

- Could a developer who never saw the proposal start building from this?
- Does every FIXED item trace to the proposal or a named source?
- Does every OPEN item have a default, an owner and a date?
- Do all diagram components appear in the architecture section?
- Are the metrics, window, roles and approval states defined?
- Is it within 3 pages, with no duplicated content?
