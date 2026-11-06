# my-skills

Personal collection of reusable Agent Skills compatible with **OpenAI Codex**, **Claude Code**, **Google Antigravity**, and the open `SKILL.md` ecosystem.

## Available Skills

| Skill | Path | Version | Description |
| :--- | :--- | :--- | :--- |
| **[aphrodite-slide](./skills/aphrodite-slide/SKILL.md)** | `skills/aphrodite-slide` | `1.1.0` | Create polished Vietnamese or English presentation slides (HTML deck, PDF/contact-sheet QA, and beta editable `.pptx`) from documents, research, data, or a brief. |

## Repository Layout

```text
my-skills/
├── .agents/
│   └── skills.json              # Workspace skill discovery for Antigravity / compatible agents
├── .claude-plugin/
│   └── marketplace.json         # Plugin & skill registry for Claude Code
├── skills/                      # Canonical skill packages (single source of truth)
│   └── aphrodite-slide/
│       ├── SKILL.md             # Single Agent Skill entrypoint
│       ├── configs/
│       ├── examples/
│       ├── references/          # Internal specialist playbooks (not separate skills)
│       ├── scripts/
│       ├── studio/
│       └── tests/
├── AGENTS.md                    # Repository rules for coding agents
└── README.md
```

## Installation & Discovery

### 1. Universal Skills CLI (`npx skills` — Claude Code, Codex, Antigravity, Cursor, etc.)

```bash
npx skills add manhthien2005/my-skills --list
npx skills add manhthien2005/my-skills --skill aphrodite-slide
```

### 2. Claude Code

Register this repository as a plugin marketplace or copy/link into `.claude/skills`:

```text
/plugin marketplace add manhthien2005/my-skills
/plugin install aphrodite-slide@my-skills
```

### 3. OpenAI Codex

- Install from GitHub using Codex's built-in `$skill-installer` (`manhthien2005/my-skills`, path `skills/aphrodite-slide`), or
- Copy/link `skills/aphrodite-slide` into `~/.agents/skills/aphrodite-slide` (global) or `<project>/.agents/skills/aphrodite-slide` (project-scoped).

### 4. Google Antigravity

- Automatically discovered in this workspace via [`.agents/skills.json`](./.agents/skills.json).
- For global access across workspaces, add this repository's `skills` directory to `~/.gemini/config/skills.json`.
