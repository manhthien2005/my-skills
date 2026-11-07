# Visual Quality Assurance (`VISUAL_QA.md`)

Mandatory quality loop for every deck:
**Generate → Render → Inspect → Fix → Re-render**

Never claim a deck is "clean", "balanced", or "ready" without rendering it and visually inspecting the images when rendering tools are available.

## 1. Automated Preflight & DOM/Motion Probe (`qa-report.md`)

`studio.py validate` and `studio.py render` check:
- **Content & Citations**: Required slots, capacity limits, density word counts, generic/label titles, VI/EN AI-filler phrases, unsourced numeric claims, placeholder citations, 3× consecutive layout repetition, and baseline drift against `outline.md`.
- **Vietnamese & Symbol Glyph Coverage**: Checks every character in the deck against `assets/fonts/coverage.json` (`missing-glyph` error for missing letters/diacritics; `fallback-glyph` warning for math/arrow symbols).
- **16:9 Geometry & Collisions (`probe.js`)**: Slide boundary overflow (`outside-slide`), container clipping (`text-clipped`), footer collision (`footer-collision`), Range-level text-on-text overlap (`overlap`), `<16px` micro-text (`text-too-small`), orphan 1-word headline wraps (`orphan-word`), and `<50%` underfilled content layouts (`empty-space`).
- **Contrast, Assets & Runtime**: WCAG contrast ratios (`4.5:1` body, `3.0:1` large display), broken `<img>` loads, WebFont load status, and JS console errors.
- **Animation Final State (`motion_check`)**: Steps through every click-build and verifies all animated elements finish at `opacity >= 0.98`, plus `Home`/`End` keyboard navigation.

## 2. Native PowerPoint QA (`pptx-qa.json`)

`studio.py pptx --qa` (and `--render-previews` when PowerPoint or LibreOffice is installed) verifies:
- 16:9 widescreen dimensions (`13.333 × 7.5 in`).
- Zero full-slide rasterization (every slide has editable text/table/chart shapes).
- Explicit Vietnamese-safe font names on runs and zero `Georgia` runs.
- Zero out-of-bounds content shapes and zero pairwise textbox overlaps.
- Native chart, native table, speaker notes, and `<p:transition>` / `<p:timing>` counts.

## 3. Mandatory Human / Agent Vision Inspection

Automated probes cannot judge visual taste. Always open `contact-sheet.jpg` **and** full-resolution PNGs of data-heavy or complex slides (`chart`, `kpi-dashboard`, `diagram`, `table`, `comparison`, `image-split`) to verify:
1. Stacked Vietnamese diacritics (`ề`, `ố`, `ẩ`, `ữ`, `ệ`) are crisp and unclipped.
2. Chart bars, labels, legends, and donut center text do not collide.
3. Visual weight feels intentional — neither cramped near the footer nor floating in an empty lower half.
4. Dark and light slides maintain clear contrast over ambient orbs or photos.

## 4. How to Fix Common Issues

- **Overflow / dense slide / `pptx-text-fit` warning**: Shorten copy, move detail to `notes`, or **split into two slides** — never shrink font tokens below minimums.
- **Overlapping chart/diagram labels**: Shorten category names, switch `column` → horizontal `bar` for long labels, or move explanatory text into `insights` / `caption`.
- **If Playwright/PowerPoint is absent on a host**: Disclose explicitly in your handoff that visual rendering could not be executed on that machine and only static/structural validation ran.
