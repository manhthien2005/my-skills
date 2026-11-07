# Professional Design System (`DESIGN_SYSTEM.md`)

Aphrodite-slide separates five concepts cleanly so you can mix and match without visual chaos:

1. **Use-case Template** (`assets/templates/<id>/template.json`): Narrative arc (`storyline`), default density, content rules, and recommended layout sequence (`academic-defense`, `lecture-teaching`, `medical-briefing`, `tech-product`, `business-review`).
2. **Visual Theme** (`assets/themes/<id>.json`): Typography pairing, color tokens, spacing, card surface treatment, background style, eyebrow style, icon badge style, dark-slide rhythm, and motion timing.
3. **Slide Layout** (`assets/layouts/catalog.json`): Structural composition, required slots, character/item limits, and PPTX fidelity (`25` layouts).
4. **Visual Style**: The emergent aesthetic direction (Editorial, Corporate Swiss, Modern Infographic, Clinical Minimal, Keynote Dark).
5. **Animation Preset** (`assets/animations/presets.json`): Motion choreography (`none`, `subtle`, `professional`, `cinematic`).

---

## Bundled Visual Themes

| Theme ID | Aesthetic Direction | Display / Body Fonts (OFL) | PPTX Safe Fallback | Best Paired With |
|---|---|---|---|---|
| `editorial-warm` | Warm paper canvas (`#FFFAF6`), soft ambient orbs, coral accent (`#E9462D`), dark bookend slides, refined editorial hierarchy (ported from author's Slide Kit) | `Cormorant Garamond` + `Plus Jakarta Sans` | `Cambria` + `Calibri` | Academic defense, research, keynote storytelling |
| `corporate-premium` | Crisp slate canvas, deep navy (`#163A6B`) + warm gold (`#B68A2E`), ruled eyebrow, executive precision | `Source Serif 4` + `Inter` | `Cambria` + `Calibri` | Business reviews, board packs, finance, operations |
| `infographic-modern` | Subtle dot-grid canvas, cobalt (`#2845D6`) + semantic multi-hue icon badges, rounded friendly hierarchy | `Lexend` + `Be Vietnam Pro` | `Segoe UI Semibold` + `Segoe UI` | Teaching lectures, workshops, onboarding, explainers |
| `clinical-clean` | High-clarity white/ice canvas, clinical teal (`#0F766E`), calm hierarchy, high WCAG contrast | `Be Vietnam Pro` + `Inter` | `Segoe UI Semibold` + `Calibri` | Medical briefings, clinical guidelines, public health |
| `keynote-night` | Deep obsidian grid (`#090D16`), emerald/mint glow (`#34D399`), glass-dark cards, dramatic contrast | `Plus Jakarta Sans` + `Inter` | `Segoe UI Semibold` + `Segoe UI` | Tech product launches, AI/software demos, startup pitch |

*(Legacy v1 aliases `editorial-cream` → `editorial-warm` and `swiss-contrast` → `corporate-premium` resolve automatically.)*

---

## Art Direction Rules

- **Rhythm & Variety**: Never use the same layout 3 times consecutively (`repeat-layout` warning). Alternate structured grids (`cards`, `methodology`), quantitative evidence (`chart`, `kpi-dashboard`, `table`), and breathing-room beats (`section`, `statement`, `case`, `image-split`).
- **Semantic Color Discipline**: Accent color marks the **hero bar, key phrase, or active milestone** — never paint every card border in thick rainbow stripes. Reserve `positive` (green) and `negative` (red) strictly for directional deltas or good/bad comparisons.
- **Typography & Vietnamese Diacritics**: Only use fonts verified in `assets/fonts/coverage.json` for Vietnamese decks. Never set `Georgia` on Windows (missing precomposed stacked Vietnamese glyphs).

