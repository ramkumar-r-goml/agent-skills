# agent-skills

[Agent Skills](https://agentskills.io/specification) for coding agents. Each skill is a folder under `skills/` with a `SKILL.md`, in a format read by Claude Code, Cursor, Codex, GitHub Copilot, Windsurf, Gemini CLI, and others.

| Skill | What it does |
|---|---|
| [writing-technical-documentation](skills/writing-technical-documentation/SKILL.md) | Writes, rewrites, audits, and exports technical docs from evidence in the code. Includes tools that inventory a repo, check a doc's references against it, flag AI writing patterns, audit a doc set, list docs a diff affects, and convert to Word, PDF, or HTML through pandoc. |

## Install

With the [skills CLI](https://skills.sh), which needs Node.js:

```bash
npx skills add ramkumar-r-goml/agent-skills --skill writing-technical-documentation
```

Add `-g` to install for your user instead of the current project, and `-a claude-code` to choose an agent.

Or clone this repo and run [install.sh](install.sh), which links each skill into your user directory for agents that read `.agents/skills` and for Claude Code:

```bash
./install.sh
./install.sh --project ~/code/myrepo --copy
```

Where each agent looks, if you prefer to copy a folder by hand:

| Agent | Project | User |
|---|---|---|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Cursor | `.agents/skills/` or `.cursor/skills/` | `~/.agents/skills/` or `~/.cursor/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| GitHub Copilot | `.agents/skills/` or `.github/skills/` | `~/.agents/skills/` or `~/.copilot/skills/` |
| Gemini CLI | `.agents/skills/` | `~/.gemini/skills/` |
| Windsurf | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` |

Cursor and Copilot also read `.claude/skills/`, so a skill installed in both places can appear twice.

For a tool with no skills support, copy [AGENTS.md](AGENTS.md) into your repo. It tells any agent to read the skill first.

## Update

Find and install newer versions:

```bash
npx skills check
npx skills update writing-technical-documentation
```

Pin a release if you need one to stay fixed: `npx skills add ramkumar-r-goml/agent-skills@v2.0.0 --skill writing-technical-documentation`. See [CHANGELOG.md](CHANGELOG.md) for what changed.

## Develop

Run the tests before pushing. They need only Python 3.11 or later, and git:

```bash
python3 -m unittest discover -s tests
```

Tests that run real conversions are skipped unless pandoc and Typst are installed. CI installs both and runs them on pull requests and on pushes to `main`.

To add a skill, create `skills/<name>/SKILL.md` with `name` (matching the folder, lowercase kebab-case) and `description` frontmatter, and keep it under 500 lines by moving detail to `references/`. [tests/test_skill_format.py](tests/test_skill_format.py) checks this for every skill.

To test a skill's effect on an agent's output, see [docs/evaluating.md](docs/evaluating.md). The research behind this skill's rules is in [docs/research.md](docs/research.md).

## License

[MIT](LICENSE)
