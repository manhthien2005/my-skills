# Repository Guidelines (`my-skills`)

This repository stores personal Agent Skills following the open `SKILL.md` standard.

## Structure & Conventions

- **Canonical skill path:** Place each skill in its own directory at `skills/<skill-name>/`.
- **Single entrypoint per skill:** Every skill directory must have exactly one `SKILL.md` at `skills/<skill-name>/SKILL.md`, whose YAML frontmatter `name` matches `<skill-name>` (`[a-z0-9]+(-[a-z0-9]+)*`).
- **No unnecessary duplication:** Keep `skills/<skill-name>/` as the single source of truth. Do not duplicate skill trees into `.claude/skills/` or `.agents/skills/`; use discovery manifests (such as `.claude-plugin/marketplace.json` and `.agents/skills.json`) to reference `./skills/<skill-name>`.
- **Internal references stay internal:** Keep playbooks/guides inside `skills/<skill-name>/references/` without adding nested `SKILL.md` files.
- **Portable paths:** Scripts and instructions inside a skill must resolve resources relative to that skill's directory (`SKILL_DIR`), never assuming CWD is the repository root.

## Safety & Maintenance Rules

- Do **not** modify, overwrite, or delete unrelated skills when adding or updating a skill.
- Do **not** commit third-party assets, templates, or kits whose redistribution license is unclear.
- Run each skill's validation scripts and automated tests before committing changes.
