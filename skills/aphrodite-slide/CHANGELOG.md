# Changelog

## 2.0.0 — Personal AI Presentation Studio

- **3-Layer Template Architecture**: Added 5 distinct use-case templates (`academic-defense`, `lecture-teaching`, `medical-briefing`, `tech-product`, `business-review`), 5 full-token themes (`editorial-warm`, `corporate-premium`, `infographic-modern`, `clinical-clean`, `keynote-night` + v1 aliases), and 25 purpose-built layouts with real rendered previews and compact `assets/registry.json`.
- **Smart Template Recommendation Engine**: Added deterministic metadata scoring (`studio.py recommend`) with bilingual keyword/synonym matching, rationale output, preview paths, and custom-style option.
- **Content-First Gated Workflow**: Added human-editable `outline.md` parser, Vietnamese/English content-quality & citation linter, approval baseline snapshotting with history (`outline approve`), slide-level diffing (`outline diff`), and `deck.json` drift guard.
- **Offline Vietnamese Typography Fix**: Replaced broken Windows `Georgia` serif rendering with 7 bundled SIL OFL `.woff2` font families covering stacked Vietnamese diacritics (`Cormorant Garamond`, `Plus Jakarta Sans`, `Be Vietnam Pro`, `Inter`, `Source Serif 4`, `Lexend`, `JetBrains Mono`) and automated glyph coverage auditing.
- **HTML Viewer & Animation System v2**: Replaced multi-file iframe viewer with a single fixed-stage 1920×1080 offline viewer (`--single-file` supported) featuring `none`, `subtle`, `professional`, and `cinematic` presets, SVG chart/timeline draw, count-up numbers, optional click builds, presenter notes/timer drawer (`N`), overview grid (`O`), fullscreen (`F`), `?static`, and `prefers-reduced-motion`.
- **Native Editable PPTX v2**: Rebuilt PowerPoint exporter from scratch with all 25 layouts, native editable charts (`column`, `stacked`, `bar`, `line`, `donut`), native tables, PIL real-metric text fitting, cover-cropped images, Lucide PNG icon badges, speaker notes, native slide transitions, optional OOXML group fade entrances, and structural/COM QA (`studio/qa/pptx_qa.py`).
- **Visual QA v2**: Added `probe.js` DOM/Range geometry, WCAG contrast, font-load, broken-image, orphan-word, and animation final-state checks alongside mandatory contact-sheet visual review.
- **Custom Design & Personal Template Library**: Added derived theme generator (`themes new` with contrast/glyph gates), style previewer (`preview`), privacy-scrubbed versioned template saver (`templates save` with PII detection and `--bump` protection), and template reuse tester (`templates test`).

## 1.1.0 — Single-skill GitHub packaging
- Repackage independent multi-skill repository into a single spec-compliant `aphrodite-slide` skill.
- Move five specialist skill instructions to internal `references/` (not separately discovered).
- Make CLI and templates self-contained and portable after copy installation.
- Add environment doctor, release tests, and license notes.

## 1.0.0
- HTML/PDF slide engine, optional editable PPTX beta, visual QA and three themes.
