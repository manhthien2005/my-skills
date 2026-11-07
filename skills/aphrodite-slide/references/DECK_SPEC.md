# Deck Specification v2 (`DECK_SPEC.md`)

`deck.json` is the single source of truth shared by HTML, PDF/PNG, and native PowerPoint exporters. (Legacy v1 decks using `type`, `illustrative`, or `data` arrays normalize automatically.)

## 1. Root Schema

```json
{
  "spec_version": 2,
  "title": "Deck Title",
  "audience": "Target audience",
  "purpose": "Goal of the presentation",
  "takeaway": "Single sentence the audience must remember",
  "language": "vi",
  "template": "academic-defense",
  "theme": "editorial-warm",
  "animation": "professional",
  "density": "speaker",
  "build": false,
  "brand": "FOOTER BRAND LABEL",
  "demo": false,
  "theme_overrides": {},
  "slides": []
}
```

- `language`: `"vi"` | `"en"` | `"bilingual"`.
- `density`: `"speaker"` (≤ 55 words/slide) | `"reading"` (≤ 120 words/slide).
- `demo`: Set `true` when using sample/benchmark data so every slide displays an explicit illustrative-data badge.

## 2. Common Slide Fields

Every object in `slides` supports:
- `id` *(string, unique)*: Slug identifier, e.g. `"s03-method"`.
- `layout` *(string, required)*: One of the 25 layouts in `assets/layouts/catalog.json`.
- `eyebrow` *(string)*: Short uppercase kicker above the headline.
- `title` *(string)*: Action headline (`**bold**` highlights key words in the theme's accent color).
- `subtitle` *(string)*: Optional 1-sentence lead under `title`.
- `sources` *(list[string])*: Explicit citations, e.g. `["WHO (2025)", "Bộ Y tế (2024)"]`.
- `data_status` *(string)*: `"real"` | `"estimate"` | `"illustrative"`.
- `notes` *(string)*: Speaker notes (shown in HTML presenter drawer `N` and exported to PowerPoint speaker notes).
- `dark` *(bool, optional)*: Override theme default dark/light surface for this slide.
- `build` *(bool, optional)*: Override click-build step mode for this slide.

## 3. Layout-Specific Payloads (Quick Examples)

- **`chart`**:
  ```json
  {
    "id": "gpa-chart",
    "layout": "chart",
    "eyebrow": "Kết quả 1",
    "title": "Nhóm ngủ **7–8 giờ** đạt GPA trung bình cao nhất",
    "chart": {
      "type": "column",
      "categories": ["< 6 giờ", "6–7 giờ", "7–8 giờ", "> 8 giờ"],
      "series": [{"name": "GPA", "values": [2.71, 2.94, 3.21, 3.05]}],
      "highlight": "7–8 giờ",
      "unit": ""
    },
    "insights": ["Chênh lệch +0,50 điểm so với nhóm ngủ dưới 6 giờ", "Duy trì ý nghĩa thống kê sau hồi quy đa biến"],
    "caption": "GPA thang 4,0 (n = 412).",
    "data_status": "illustrative"
  }
  ```
- **`kpi-dashboard`**: `items: [{"label": "Doanh thu", "value": "128 tỷ", "delta": "+6% KH", "status": "up", "trend": [96, 108, 112, 119, 128], "target": "121 tỷ"}]`, optional `period: "Q3/2026"`.
- **`comparison`**: `highlight: "left"|"right"`, `left: {"title": "...", "tag": "Đề xuất", "bullets": [...]}`, `right: {...}`, `verdict: "..."`.
- **`problem-solution`**: `problem: {"title": "...", "points": [...]}`, `solution: {"title": "...", "points": [...]}`.
- **`table`**: `columns: ["Tiêu chí", "A", "B"]`, `rows: [["Chi phí", "4,5 tr", "4,3 tr"]]`, `highlight: "A"`, `note: "..."`.
- **`methodology`**: `facts: [{"value": "412", "label": "mẫu khảo sát"}]`, `steps: [{"title": "Chọn mẫu", "detail": "..."}]`.
- **`diagram`**: `variant: "hub"|"cycle"`, `center: "Trung tâm"`, `nodes: [{"title": "...", "detail": "...", "icon": "brain"}]`.
- **`image-split` / `full-bleed-image`**: `image: "photo.jpg"` (relative to deck's `assets/` folder — never remote `http://` URLs or `..` traversal), `image_alt: "..."`, `image_credit: "..."`.

