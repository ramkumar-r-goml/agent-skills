# agent-skills

A collection of [Agent Skills](https://agentskills.io/specification) for coding agents. Each skill is a folder under `skills/` with a `SKILL.md`, and works in Claude Code, Cursor, Codex CLI, Copilot, Windsurf, Gemini CLI and other tools that read the format.

## Skills

| Skill | What it does |
|---|---|
| [writing-technical-documentation](skills/writing-technical-documentation/SKILL.md) | Writes, rewrites and audits READMEs, architecture docs, ADRs, API/CLI reference, runbooks and postmortems. Reads the codebase in a fixed order, traces claims to evidence, and strips AI writing patterns. Includes a repo inventory script, a reference checker and a prose scanner. |

## Install

With the [skills CLI](https://skills.sh):

```bash
npx skills add ramkumar-r-goml/agent-skills                                        # choose from the list
npx skills add ramkumar-r-goml/agent-skills --skill writing-technical-documentation
npx skills add ramkumar-r-goml/agent-skills --skill writing-technical-documentation -a claude-code -g
```

Manually, copy or symlink a skill folder into your agent's skills directory:

| Agent | Project | User |
|---|---|---|
| Claude Code | `.claude/skills/<name>/` | `~/.claude/skills/<name>/` |
| Cursor | `.cursor/skills/<name>/` | `~/.cursor/skills/<name>/` |
| Codex CLI | `.agents/skills/<name>/` | `~/.agents/skills/<name>/` |

`./install.sh` does this for you (`./install.sh --help`).

For tools without skills support, copy [AGENTS.md](AGENTS.md) into your repo. Cursor users can also copy `.cursor/rules/writing-technical-documentation.mdc`.

## Adding a skill

Create `skills/<name>/SKILL.md` with `name` (matching the folder, lowercase kebab-case) and `description` frontmatter, keep it under about 500 lines, and put detail in `references/`.

## License

MIT
