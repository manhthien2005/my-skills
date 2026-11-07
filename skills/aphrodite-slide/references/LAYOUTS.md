# Slide Layout Catalog (`LAYOUTS.md`)

Run `python "<SKILL_DIR>/scripts/studio.py" layouts` for full JSON slot definitions. Choose each slide's layout to serve its message:

## 1. Opening, Transitions & Closing
- **`cover`**: Title slide (`title`, optional `eyebrow`, `subtitle`, `meta` list `["Key: Value"]`, optional split `image`).
- **`agenda`**: Numbered table of contents (`items`: 3–7 `{title, detail}`), auto 2-column when > 4 items.
- **`section`**: Chapter divider (`title`, optional `section_number`, `eyebrow`, `subtitle`, `chips`).
- **`statement`**: Single bold thesis or takeaway (`title` up to ~140 chars, optional `subtitle`, `note`).
- **`closing`**: Final Q&A / contact slide (`title`, optional `eyebrow`, `subtitle`, `meta`).

## 2. Quantitative & Analytical
- **`metrics`**: 2–4 big-number stat tiles (`items`: `{value, label, detail}`).
- **`kpi-dashboard`**: 3–6 executive KPI cards (`items`: `{label, value, delta, status: up|down|flat, down_is_good, trend: [...], target}`, optional `period`).
- **`chart`**: Data visualization (`chart`: `{type: column|bar|line|stacked|donut, categories, series: [{name, values}], unit, highlight, center_label, center_caption}`, optional `insights` list of 1–3 takeaways, `caption`).
- **`table`**: Structured comparison matrix (`columns`: 2–6 headers, `rows`: 2–6 rows, optional `highlight` column name/index, `note`). Exports as a **native editable table** in PPTX.
- **`case`**: Hero figure + real/illustrative case narrative (`value`, `value_label`, `body`).

## 3. Structure, Process & Mechanisms
- **`cards`**: 2–4 parallel concepts (`items`: `{title, body, icon, highlight}`, `style`: `panels` or editorial flat `columns`).
- **`process`**: 3–5 sequential steps (`steps`: `{title, detail, icon}`) along a horizontal rail.
- **`timeline`**: 3–6 chronological milestones (`items`: `{date, title, detail, state: done|now|next}`).
- **`diagram`**:
  - `variant: "hub"`: Central concept (`center`) connected to 3–6 radial `nodes` (`{title, detail, icon}`).
  - `variant: "cycle"`: 3–5 circular stages (`nodes`) with directional curved arrows + optional `center`.
- **`methodology`**: Research/engineering design (`facts`: 2–4 `{value, label}` cards on left + `steps`: 2–5 `{title, detail}` vertical steps on right).

## 4. Argumentation, Pedagogy & Evidence
- **`comparison`**: Side-by-side option evaluation (`left` & `right`: `{title, tag, bullets, tone}`, optional `highlight: "left"|"right"`, bottom `verdict`).
- **`problem-solution`**: Pain points (`problem.points`) → directional bridge → interventions (`solution.points`).
- **`evidence-levels`**: 3–5 tiered confidence/evidence bars (`levels`: `{label, detail}`, optional `note`).
- **`learning-objectives`**: 3–6 action-verb outcomes (`items`: strings or `{text, icon}`, optional `lead`).
- **`definition`**: Concept spotlight (`term`, `definition`, optional `pronunciation`, `example` card, `note`).
- **`quote`**: Short attributed quotation (`quote`, `attribution`).
- **`key-takeaways`**: 3–5 numbered conclusion cards (`bullets`).
- **`references`**: 2–10 formatted citations (`items`), auto 2-column when > 5 items.

## 5. Visual & Media
- **`image-split`**: 50/50 split between narrative (`title`, `subtitle`, `bullets`) and full-height local image (`image`, `image_alt`, optional `image_credit`, `side: "right"|"left"`).
- **`full-bleed-image`**: Full-canvas photo (`image`, `image_alt`, `image_credit`) with dark gradient scrim and high-contrast headline.

