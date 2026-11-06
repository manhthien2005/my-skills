# Aphrodite-slide

A single, self-contained Agent Skill for creating polished Vietnamese and English presentation decks. Technical name: `aphrodite-slide`.

- Entry point: `SKILL.md` (there are **no other** `SKILL.md` files).
- Internal methods: `references/` (storytelling, design direction, HTML, PPTX beta, visual QA).
- Production code: `scripts/studio.py`, `studio/`, `configs/`.
- Example source: `examples/logistics/deck.json`; previews: `assets/previews/`.
- Output: HTML slide deck and optional PNG/PDF, editable PPTX beta.
- No mandatory paid services or external APIs.

## Basic usage (after agent discovers the skill)

```bash
python scripts/studio.py themes
python scripts/studio.py validate examples/logistics/deck.json --strict
python scripts/studio.py build examples/logistics/deck.json --out ./output/logistics
python -m unittest discover -s tests -v
python scripts/doctor.py
```

For optional slide rendering: `requirements-render.txt`; for optional native PowerPoint: `requirements-pptx.txt`. Both are described in their respective internal playbooks.

## Limits and provenance

The PPTX renderer is beta; PDF and screenshot rendering require optional local dependencies. The original user-supplied legacy Slide Kit and other GitHub skill source trees are not embedded here. See `references/THIRD_PARTY.md` for licensing notes.
