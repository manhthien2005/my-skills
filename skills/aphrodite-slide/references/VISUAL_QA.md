# Visual QA

**Two gates:** content QA before render; image QA after render.

1. Run `python scripts/studio.py validate DECK --strict` to detect missing titles, duplicate IDs, unsupported layouts, missing evidence, placeholder citations and content overload.
2. Build, then run `python scripts/studio.py render BUILD_DIR --strict`.
3. Open `contact-sheet.jpg` **and** inspect all slide previews at native resolution. Look for lone-word wraps, low contrast, misaligned grids, crowded page or awkward whitespace; automatic geometry tests cannot see all of these.
4. Inspect `qa-report.json` per slide. Fix overflow/footer clashes and re-render. Do not waive severe errors without documenting why.
5. Review Vietnamese font rendering and show a screenshot of the difficult slide types (large titles, timelines, charts, two-column comparisons).
6. Deliver QA status accurately: validation passed, screenshot capture passed, manual visual review status, and any unverified issues.

Use native HTML for source editing. If a native editable PPTX is also exported, independently review that output; HTML validation does not guarantee PowerPoint fidelity.
