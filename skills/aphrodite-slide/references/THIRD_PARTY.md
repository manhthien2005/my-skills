# Third-Party Provenance & Licensing (`THIRD_PARTY.md`)

Aphrodite-slide v2 is 100% local and offline-first, requiring **no paid APIs or external CDN calls**. Every bundled asset has verified open-source licensing.

## 1. Original Studio Code & Templates
- **`studio/`, `scripts/`, `assets/runtime/`, `assets/themes/`, `assets/templates/`, `assets/layouts/`, `references/`, `examples/`, `tests/`**: Original Aphrodite-slide v1/v2 engineering and design tokens, licensed under the **MIT License** (`LICENSE`).
- **Author's `slide-kit` heritage**: Editorial typography rules, Vietnamese number formatting conventions, flat editorial column aesthetics, and warm palette inspiration in `editorial-warm` were ported with explicit permission from the repository owner (original author of `slide-kit`). The raw `slide-kit.zip` archive itself is excluded from Git tracking.

## 2. Bundled Fonts (`assets/fonts/`) — SIL Open Font License 1.1
Subsetted `.woff2` web fonts covering Latin, Latin Extended, Vietnamese (`U+0102–01B0`, `U+1EA0–1EF9`), Greek, subscripts/superscripts, arrows, and mathematical operators. Full license texts are included in `assets/fonts/licenses/`:
- **Be Vietnam Pro** — `assets/fonts/licenses/bevietnampro-OFL.txt` (SIL OFL 1.1)
- **Cormorant Garamond** — `assets/fonts/licenses/cormorantgaramond-OFL.txt` (SIL OFL 1.1)
- **Inter** — `assets/fonts/licenses/inter-OFL.txt` (SIL OFL 1.1)
- **JetBrains Mono** — `assets/fonts/licenses/jetbrainsmono-OFL.txt` (SIL OFL 1.1)
- **Lexend** — `assets/fonts/licenses/lexend-OFL.txt` (SIL OFL 1.1)
- **Plus Jakarta Sans** — `assets/fonts/licenses/plusjakartasans-OFL.txt` (SIL OFL 1.1)
- **Source Serif 4** — `assets/fonts/licenses/sourceserif4-OFL.txt` (SIL OFL 1.1)

## 3. Bundled Icons (`assets/icons/`) — ISC License
- **Lucide Icons** (`icons.json` SVG paths + white PNG renders in `assets/icons/png/` for PowerPoint): Licensed under the **ISC License** (`assets/icons/LICENSE-lucide.txt`).

## 4. External Repositories Studied (Architectural Principles Only — Zero Code Copied)
During Phase 1 research, the following open ecosystems were studied for presentation workflow and QA concepts without vendoring or copying their codebases:
- `agentskills/agentskills` (Apache-2.0) — Single-skill `SKILL.md` progressive disclosure specification.
- `zarazhangrui/frontend-slides` (MIT) — Style preview discovery and CSS/JS presentation ergonomics.
- `Rich627/slides-skill` (MIT) — Content-vs-layout JSON separation and deterministic theme tokens.
- `hunkim/slide-skill` (MIT) — One-message-per-slide and anti-clutter storytelling discipline.
- `anthropics/skills` (`skills/pptx` is Source-Available / Proprietary) — **No code, prompt text, or templates copied**; only general OOXML/PowerPoint structural QA concepts (checking native editable shapes and visually inspecting rendered slides) were independently implemented.

## 5. Optional Runtime Packages (Not Bundled)
- `playwright` (Apache-2.0), `Pillow` (MIT-CMU), `python-pptx` (MIT), `PyYAML` (MIT) — installed optionally by the user in their Python environment when rendering PNG/PDF or exporting `.pptx`.
