# Animation System & PPTX Fallbacks (`ANIMATION.md`)

Animations in Aphrodite-slide serve **reading order, emphasis, and pacing** — never gratuitous spin or bounce. Everything runs 100% locally in `assets/runtime/deck.css` + `deck.js` using GPU-composited `transform`, `opacity`, `clip-path`, and SVG `stroke-dashoffset`.

## 1. Animation Presets (`assets/animations/presets.json`)

| Preset | Behaviour | Recommended For |
|---|---|---|
| `none` | Instant slide switch, zero element transitions | Print-first handouts, strict institutional settings |
| `subtle` | Gentle slide crossfade only; elements appear immediately | Medical briefings, dense analytical reports |
| `professional` *(default)* | Reading-order stagger (`a-rise`, `a-fade`, `a-left`), column/bar chart grow, SVG line/donut/timeline stroke draw, big-number count-up, optional click-build steps | Academic defense, teaching lectures, business reviews |
| `cinematic` | Headline clip-path mask reveal (`a-mask`), subtle Ken Burns image zoom (`a-zoom`), `push` section transitions, slightly richer timing | Tech product launches, keynote talks, demos |

Set deck-level `"animation": "professional"` in `deck.json` or pass `--animation <preset>` to `studio.py build` / `export`.

## 2. Click-Build Choreography (`build: true`)

- Set `"build": true` at the deck level or on individual slides (`"build": true`) to reveal list items, process steps, cards, KPI tiles, comparison columns, or chart insights **one step per click / `→` key**.
- During `studio.py render`, `motion_check` automatically plays every slide through all build steps and verifies that every `.a` element reaches `opacity >= 0.98` in its final state.

## 3. Accessibility & Viewer Controls

- **`prefers-reduced-motion: reduce`**: Automatically disables transitions and reveals final states immediately.
- **Query flags**: `?static` forces static final state for screenshots/PDF; `?speed=0.15` accelerates transitions for automated QA.
- **Presenter shortcuts**: `←` / `→` / `Space` / `PageDown` (advance step or slide), `Home` / `End` (first/last slide), `F` (fullscreen), `N` (speaker notes + live elapsed timer drawer), `O` (thumbnail overview grid).

## 4. Honest PowerPoint (`.pptx`) Fallback Contract

Never promise identical animations between HTML and PowerPoint:

| HTML Motion Feature | PowerPoint (`.pptx`) Equivalent / Fallback |
|---|---|
| Slide fade / section push | **Native OOXML `<p:transition>`** (`fade` / `push`, enabled by default; disable with `--no-transitions`) |
| Intra-slide reading-order stagger | Off by default for maximum compatibility; optional **experimental OOXML `<p:timing>` group fades** via `--entrances` (auto stagger or click-build when `build: true`) |
| SVG line/donut/timeline stroke draw | **Static final state** (editable native chart or vector connector) |
| Number count-up (`data-count`) | **Static final number** |
| Headline clip-path mask / Ken Burns zoom | **Static final headline / cropped picture** |

Always mention this distinction briefly when delivering both HTML and `.pptx` for an animated deck.

