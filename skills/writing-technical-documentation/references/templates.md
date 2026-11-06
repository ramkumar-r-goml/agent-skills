# Templates

Skeletons only. Each bracketed item must be replaced with a verified fact or the section removed. Delete sections that do not apply; do not fill them with filler. Placeholders in angle brackets show what kind of fact goes there.

Contents
1. README
2. Architecture overview
3. ADR
4. Design doc
5. Runbook
6. API reference entry
7. CLI reference entry
8. Onboarding guide
9. How-to guide
10. Tutorial
11. Troubleshooting entry
12. Postmortem
13. Migration guide
14. Changelog
15. CONTRIBUTING
16. SECURITY
17. AGENTS.md / CLAUDE.md
18. Model or system card
19. Agent or LLM flow doc
20. Module docstring and function docstring
21. Front matter for freshness

## 1. README

````markdown
# <project-name>

<One or two sentences: what it does, for whom, the main constraint or limit.>
<When not to use it, and the alternative.>

## Quick start

Prerequisites: <runtime and version>, <tool and version>.

```bash
<install command>
<run command>
```

Expected output:

```text
<captured output>
```

## Usage

<Smallest real example, tested.>

## Configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `<KEY>` | <type> | `<default>` | <what it controls, units> |

## Documentation

- [Architecture](docs/architecture.md)
- [API reference](docs/api.md)
- [Runbook](docs/runbook.md)

## Development

```bash
<test command>
<lint command>
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Status and support

<Maturity, supported versions, license, where to ask.>
````

## 2. Architecture overview

````markdown
# <System> architecture

Last verified: <YYYY-MM-DD> against <commit or version>.

<Purpose and main constraint in two sentences.>

## Context

<Users and systems that interact with it. Trust boundaries.>

## Components

| Component | Responsibility | Tech | Location |
|---|---|---|---|
| <name> | <one sentence> | <language, runtime, service> | `<path>` |

## Flow: <name of main flow>

1. <Actor> sends <what> to <component> (`<file:line>`).
2. <Component> validates <what> and writes <what> to <store>.
3. <Next hop>.

Failure handling: <what happens on error, retry, timeout>.

## Data

<Stores, key entities, ownership, retention, consistency.>

## Deployment

<Environments, regions, pipeline, rollback.>

## Cross-cutting concerns

- Auth: <mechanism>
- Observability: <logs, metrics, traces, where>
- Scaling limits and cost drivers: <numbers>
- Security: <controls>

## Decisions

- [ADR-0003 <title>](adr/0003-<slug>.md)

## Known gaps

- <gap, with issue link if any>
````

## 3. ADR

````markdown
# ADR-<NNNN>: <Decision as a short phrase>

- Status: <proposed | accepted | superseded by ADR-NNNN | deprecated>
- Date: <YYYY-MM-DD>
- Deciders: <names or roles>

## Context

<Facts and constraints that forced a decision: numbers, deadlines, existing systems.>

## Decision

We will <do X>.

## Consequences

- Good: <result>
- Bad: <cost, what becomes harder>
- Neutral: <side effects to watch>

## Alternatives considered

- <Option A>: rejected because <reason>.
- <Option B>: rejected because <reason>.
````

## 4. Design doc

````markdown
# <Title>

- Author: <name>
- Reviewers: <names>
- Status: <draft | in review | approved | implemented>
- Last updated: <YYYY-MM-DD>

## Summary

<Problem, proposed solution, and the decision needed, in four sentences.>

## Context and problem

<What is wrong now, with evidence.>

## Goals

- <measurable goal>

## Non-goals

- <thing a reader could reasonably expect that this does not do>

## Design

### Overview
<Components and flow.>

### Data model
<Schemas.>

### Interfaces
<APIs or events with examples.>

### Failure handling
<What breaks and what happens.>

## Alternatives considered

| Option | Why not |
|---|---|
| <A> | <reason> |

## Cross-cutting concerns

Security, privacy, cost, observability, testing, rollout, rollback, compatibility.

## Risks and open questions

- <risk, mitigation>
- <question, owner, due>

## Milestones

1. <deliverable and date>
````

## 5. Runbook

````markdown
# Runbook: <alert or symptom>

Last verified: <YYYY-MM-DD> by <name>.

Trigger: <exact alert name or symptom>.
Impact: <who or what is affected>.
Urgency: <page now | business hours>.

## Quick mitigation

1. <Action.> Expected: <result>.
2. <Action.>

## Diagnose

1. Check <thing>:
   ```bash
   <command>
   ```
   If the output shows <A>, go to <section>. If <B>, go to <section>.

## Fix: <cause A>

1. <Step.>

Warning: <blast radius> before running <command>.

## Roll back

1. <Step.>

## Verify

<Command or dashboard and the expected value.>

## Escalate

If not resolved in <time>, contact <team or channel>.

## Links

- Dashboard: <name>
- Logs: <query or log group>
````

## 6. API reference entry

````markdown
### `<METHOD> <path>`

<One line: what it does.>

Auth: <scheme and scope>.

**Parameters**

| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `<name>` | <path/query/body> | <type> | <yes/no> | <meaning, units, constraints, default> |

**Request**

```bash
curl -X <METHOD> https://api.example.com<path> \
  -H "Authorization: Bearer <TOKEN>" \
  -d '<body>'
```

**Response `<status>`**

```json
<captured response>
```

**Errors**

| Status | Code | Cause | Fix |
|---|---|---|---|
| <4xx> | `<code>` | <cause> | <fix> |

Notes: <idempotency, rate limit, pagination, side effects>.
````

## 7. CLI reference entry

````markdown
## `<tool> <subcommand>`

<One line purpose.>

```text
<tool> <subcommand> [options] <args>
```

| Option | Default | Env var | Description |
|---|---|---|---|
| `--<flag>` | `<default>` | `<ENV>` | <meaning> |

Exit codes: `0` success, `<n>` <meaning>.

Examples:

```bash
<common case>
```
````

## 8. Onboarding guide

````markdown
# Onboarding: <team or service>

Time to first merged change: about <n> hours.

## 1. What this is
<Two paragraphs: purpose, users.>

## 2. Get access
- <system>: request from <who/how>.

## 3. Set up
```bash
<tested commands>
```
Expected: <result>.

## 4. Run the tests
```bash
<command>
```

## 5. Make your first change
<Small real task with steps.>

## 6. Map of the code
| Path | What lives there |
|---|---|

## 7. Who owns what
<Roles and channels.>

## 8. Glossary
<Terms.>
````

## 9. How-to guide

````markdown
# How to <task>

<One sentence: what you will have at the end.>

## Before you begin

- <prerequisite with version>

## Steps

1. <Action.>
   Expected: <result>.
2. <Action.>

## Verify

<Command and expected output.>

## Troubleshooting

- <Error text>: <cause and fix>.

## Related

- <links to reference and explanation>
````

## 10. Tutorial

````markdown
# Tutorial: <build or learn X>

By the end you will have <concrete result>. It takes about <n> minutes.

## What you need
<Exact tools and versions.>

## Step 1: <outcome-named step>
<Action.>

```bash
<command>
```

You should see:

```text
<output>
```

## Step 2: ...

## What you built
<Two sentences.>

## Next
<One or two links.>
````

## 11. Troubleshooting entry

````markdown
### `<exact error message>`

Cause: <most likely cause>.

Confirm:

```bash
<command>
```

Fix: <steps>.

If it persists, collect <logs or output> and <where to ask>.
````

## 12. Postmortem

````markdown
# Postmortem: <incident title> (<YYYY-MM-DD>)

Status: <draft | final>. Severity: <level>.

## Summary
<Impact, duration, detection, resolution.>

## Impact
<Users affected, requests failed, data lost, money.>

## Timeline (UTC)
| Time | Event |
|---|---|
| <hh:mm> | <fact> |

## Root cause and contributing factors
<System and process causes. No individual blame.>

## Detection and response
- Worked: <>
- Did not: <>
- Lucky: <>

## Action items
| Action | Owner | Priority | Due | Link |
|---|---|---|---|---|

## Lessons
<Specific, not generic.>
````

## 13. Migration guide

````markdown
# Migrate from <vA> to <vB>

Who must act: <who>. Deadline: <date or version>.

## Breaking changes

### <Change>
Before:
```<lang>
<code>
```
After:
```<lang>
<code>
```

## Steps

1. <Action.>

## Roll back
<Steps.>

## Verify
<Check.>

## Common errors
- `<error>`: <fix>.
````

## 14. Changelog

````markdown
# Changelog

## [<version>] - <YYYY-MM-DD>

### Added
- <what the user can now do> (#<issue>)

### Changed
- <behavior change>

### Deprecated
### Removed
### Fixed
### Security
````

## 15. CONTRIBUTING

````markdown
# Contributing

## Set up
<commands>

## Test
<commands, single-test form>

## Style
<formatter, linter, naming, commit message format>

## Pull requests
<branching, size, review, CI requirements>

## Larger changes
<Open an issue or RFC first.>
````

## 16. SECURITY

````markdown
# Security policy

Supported versions: <table>.

Report a vulnerability: <private channel>. Do not open public issues.

Response: <what is promised, only if the owner confirmed>.
````

## 17. AGENTS.md / CLAUDE.md

````markdown
# <Project>

<One paragraph: what this is.>

## Commands

- Install: `<cmd>`
- Build: `<cmd>`
- Test all: `<cmd>`
- Test one: `<cmd> <path>::<name>`
- Lint: `<cmd>`
- Run: `<cmd>`

## Layout

- `<dir>/`: <purpose>

## Conventions

- <rule that tooling does not enforce>

## Do not

- <thing to avoid, with reason>

## More

- Architecture: `docs/architecture.md`
````

## 18. Model or system card

````markdown
# <Model or system> card

- Version: <id>
- Intended use: <>
- Out of scope: <>
- Data: <sources, size, dates, licenses>
- Evaluation: <datasets, metrics, numbers, date>
- Limitations and failure modes: <>
- Safety and bias findings: <>
- Cost and latency: <numbers, setup>
- Update policy: <>
````

## 19. Agent or LLM flow doc

````markdown
# <Flow name>

Goal: <>
Input: <>
Model: <provider, model ID, region, temperature, max tokens>
System prompt: `<path>` (version <>)
Tools:
| Tool | Schema | Side effects | Permissions |
|---|---|---|---|
Loop: <steps, max iterations, stop conditions>
Validation: <output checks>
Failure handling: <>
Human approval: <where>
Evaluation: <dataset, metric, threshold, CI>
Cost per run: <number and basis>
Non-deterministic parts: <>
````

## 20. Docstrings

Module docstring: one line stating purpose, then what the module owns and what it depends on, only if non-obvious.

Function docstring (Google style example):

```python
def retry(fn, attempts=3, base_delay_s=0.2):
    """Call fn, retrying on TimeoutError with exponential backoff.

    Args:
        fn: Zero-argument callable.
        attempts: Total tries including the first. Must be >= 1.
        base_delay_s: Delay before the second try; doubles each time.

    Returns:
        The return value of fn.

    Raises:
        TimeoutError: If every attempt times out.
    """
```

## 21. Front matter for freshness

```yaml
---
title: <title>
last_verified: <YYYY-MM-DD>
verified_against: <commit or version>
owner: <team>
---
```
