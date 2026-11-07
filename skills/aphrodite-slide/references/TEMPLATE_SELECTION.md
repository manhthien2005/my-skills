# Smart Template Recommendation (`TEMPLATE_SELECTION.md`)

Once topic and purpose are understood, recommend ~3 concrete visual/structural options using deterministic metadata scoring — never pick a theme at random.

## 1. Run the Recommendation Engine

```bash
python "<SKILL_DIR>/scripts/studio.py" recommend \
  --brief "<topic, goal, domain keywords>" \
  --audience "<target audience>" \
  --density speaker
```

Optional filters: `--use-case <academic|education|medical|technology|business>`, `--formality <low|medium|high>`, `--scheme <light|dark>`.

The engine scores both repo templates (`assets/templates/`) and saved user templates (`~/.aphrodite-slide/templates/`) across use-case match, bilingual domain keywords, audience, density, formality, colour scheme, and user profile preferences (`configs/profile.json`).

## 2. How to Present the ~3 Options

For each option returned in `options` / `recommendations`, show:
1. **Template & Theme name** (highlighting **Phương án đề xuất tối ưu** first).
2. **Best-fit scenario** (`best_for`) — why it fits this specific talk or report.
3. **Design style** — typography, palette mood, light/dark canvas.
4. **Layout & storyline characteristics** — e.g., `methodology` + `evidence-levels` for research; `kpi-dashboard` + `comparison` for business review.
5. **Animation preset** — `professional`, `subtle`, or `cinematic` (with honest note on PPTX static fallback).
6. **Real rendered preview image** — link or embed the actual composite preview (`assets/templates/<id>/preview.jpg` or `assets/templates/<id>/previews/<theme>.jpg`).

## 3. Always Offer Custom Style Creation

Every recommendation turn **must** include the fourth choice:

> **"Tôi muốn thiết kế một phong cách mới."**

Never force the user into the built-in templates. If the user selects a custom style, provides a brand palette/logo, or shares a reference screenshot, switch to `references/CUSTOM_DESIGN.md` and generate a preview image before building the full deck.

