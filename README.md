# my-skills

Personal collection of reusable Agent Skills compatible with **OpenAI Codex**, **Claude Code**, **Google Antigravity**, and the open `SKILL.md` ecosystem.

## Repository Layout

```text
my-skills/
├── .agents/
│   └── skills.json              # Workspace skill discovery for Antigravity / compatible agents
├── .claude-plugin/
│   └── marketplace.json         # Plugin & skill registry for Claude Code
├── skills/                      # Canonical skill packages (one folder per skill)
│   └── <skill-name>/
│       └── SKILL.md
├── AGENTS.md                    # Repository rules for coding agents
└── README.md
```

## Installation & Discovery

- **Universal CLI (`skills`):**
  ```bash
  npx skills add manhthien2005/my-skills --list
  npx skills add manhthien2005/my-skills --skill <skill-name>
  ```
- **Claude Code:**
  ```text
  /plugin marketplace add manhthien2005/my-skills
  /plugin install <skill-name>@my-skills
  ```
- **OpenAI Codex:**
  Install via `$skill-installer` from `manhthien2005/my-skills` (`skills/<skill-name>`) or copy/link `skills/<skill-name>` into `~/.agents/skills/<skill-name>`.
- **Google Antigravity:**
  Automatically discovered via `.agents/skills.json` when working in this repository, or reference `skills` in `~/.gemini/config/skills.json`.
