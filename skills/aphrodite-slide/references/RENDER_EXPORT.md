# Multi-Format Rendering & Export (`RENDER_EXPORT.md`)

All outputs are generated from a single `deck.json` without any paid APIs or internet access.

## 1. One-Shot Unified Export

```bash
python "<SKILL_DIR>/scripts/studio.py" export "<out_dir>/deck.json" \
  --out "<out_dir>/dist" \
  --pdf both \
  --strict
```

Produces inside `<out_dir>/dist/`:
- `index.html` (+ local `fonts/` and `assets/`, or pass `--single-file` to inline everything as base64 in a single `.html` file).
- `previews/01-<id>.png` … `NN-<id>.png` (1920×1080 16:9 PNGs) + `contact-sheet.jpg`.
- `deck.pdf` (vector PDF with selectable text & embedded web fonts) and/or `deck-image.pdf` (pixel-exact raster PDF when `--pdf image` or `--pdf both`).
- `deck.pptx` (native editable 16:9 PowerPoint presentation).
- `qa-report.json`, `qa-report.md`, `pptx-qa.json`, and `export-summary.json`.

## 2. Format Capabilities & Tradeoffs

| Format | Role | Editable? | Offline Fonts | Animation | Dependencies |
|---|---|---|---|---|---|
| **HTML (`index.html`)** | Primary presentation format | Via `deck.json` rebuild | Bundled `.woff2` (exact) | Full (`none` / `subtle` / `professional` / `cinematic`) + presenter notes/timer | Python 3.10+ stdlib only |
| **PowerPoint (`deck.pptx`)** | Editable handoff & collaboration | **Yes** — native text boxes, shapes, tables, Excel-backed charts, speaker notes | Office-safe Vietnamese fonts (`Cambria`/`Calibri`/`Segoe UI`), or `--use-theme-fonts` | Native `fade`/`push` slide transitions + optional `--entrances` group fades | `python-pptx`, `Pillow` |
| **Vector PDF (`deck.pdf`)** | Email / archival / LMS upload | Selectable text | Embedded by Chromium | Static final state | `playwright` + local Chromium/Edge/Chrome |
| **Image PDF / PNGs** | Pixel-locked review & thumbnails | Raster | Baked-in exact pixels | Static final state | `playwright` + `Pillow` |

## 3. Individual Export Commands

- **HTML only (zero external packages)**:
  ```bash
  python "<SKILL_DIR>/scripts/studio.py" build deck.json --out ./dist --single-file
  ```
- **Render HTML → PNG / PDF / QA**:
  ```bash
  python "<SKILL_DIR>/scripts/studio.py" render ./dist --pdf vector --strict
  ```
- **PowerPoint only (+ structural QA & optional PowerPoint/LibreOffice visual render)**:
  ```bash
  python "<SKILL_DIR>/scripts/studio.py" pptx deck.json --out ./dist/deck.pptx --qa --render-previews
  ```

