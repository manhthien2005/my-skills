# HTML Slide Builder

## Input and output

Input: UTF-8 JSON with top-level `title`, `audience`, `takeaway`, `theme`, `slides`. Example: `examples/logistics/deck.json`.
Output: `build/<name>/{index.html,slides/*.html,deck.json,manifest.json}`. Rendering adds `previews/*.jpg`, `contact-sheet.jpg`, `deck.pdf`, `qa-report.json`.

```bash
python scripts/studio.py themes
python scripts/studio.py build examples/logistics/deck.json --out build/logistics --theme editorial-cream
python scripts/studio.py render build/logistics --strict
```

Default rendering uses native local fonts; no paid APIs, frontend frameworks or cloud hosting. The interactive viewer supports arrow keys, page controls and fullscreen. The original `optional local `legacy/slide-kit/` (not included in public package)` remains available for advanced custom manual HTML layouts and its five Python tools. It is not used at runtime by the JSON-to-HTML generator.

To create custom code per slide, edit copied output, not generated templates; rerunning build will overwrite generated HTML. For long-term custom layouts add a new renderer in `studio/html.py` and test it.

## Assets

Only local relative paths under a deck's `assets/` are allowed; do not invent external URL-based images. Sources appear in the visible footer. `demo: true` watermarks demo content in each footer as simulated evidence.
