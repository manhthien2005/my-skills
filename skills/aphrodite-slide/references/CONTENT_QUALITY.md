# Content Quality System (`CONTENT_QUALITY.md`)

Great design cannot rescue vague or bloated slide copy. Apply these rules across Vietnamese, English, and bilingual decks.

## 1. One Message & Action Titles

- **One core claim per slide**: If a slide has two `"and also"` conclusions, split it into two slides.
- **Action titles over topic labels**:
  - Weak: `Kết quả khảo sát` / `Survey Results` / `Bối cảnh: Chi phí vận chuyển`
  - Strong: `Nhóm ngủ 7–8 giờ có điểm GPA cao nhất (3,21/4,0)` / `Cước vận chuyển tăng 14% kéo biên lợi nhuận quý 3 giảm`
  - Put short category labels (`KẾT QUẢ 1`, `Q3/2026`, `PHƯƠNG PHÁP`) into `eyebrow`, never as `Nhãn: Câu` inside `title`.
  - Use `**bold**` on 1–3 key words in `title` to highlight the focal phrase with the theme's accent colour.

## 2. Density Without Shrinking Fonts

- **Speaker-led decks (`density: "speaker"`)**: ≤ 55 words per slide; concise phrases the audience scans in 4 seconds while listening.
- **Reading-first decks (`density: "reading"`)**: ≤ 120 words per slide; self-contained analytical sentences for pre-reads, medical briefings, or board packs.
- **Overflow rule**: When copy exceeds layout capacity limits (`studio.py layouts`), **split the slide** or move explanation into `notes` — never shrink body text below 18px (HTML) / 9.5pt (PPTX).

## 3. Data Honesty & Chart Selection

- **Never fabricate citations or statistics**. Every numeric claim requires `sources: ["Organization (Year)"]`, or explicit `data_status: "illustrative"` (or deck-level `demo: true`), or `data_status: "estimate"` with the estimation basis in `notes`/`sources`.
- **Match chart type to data relationship**:
  - `column`: Comparing 3–8 discrete categories or short time periods (always zero-baselined).
  - `bar`: Ranking categories or long Vietnamese labels (`Ghi âm + tự gõ`, hospital departments).
  - `line`: Continuous trends across ≥ 4 ordered periods.
  - `stacked`: Part-to-whole across categories (`2–4` stacked components).
  - `donut`: Simple share breakdown (`2–5` parts summing to 100%, with center total).
- **Vietnamese number formatting**: HTML charts and prose in `language: "vi"` format decimals with commas (`92,4%`, `3,21`) and thousands with dots (`41.200 đ`).

## 4. Anti-AI-Slop Lexicon

`outline lint` and `validate` actively flag hollow filler in both languages:
- **Avoid (VI)**: *"hãy cùng khám phá"*, *"giải pháp toàn diện"*, *"vượt trội"*, *"đột phá"*, *"kỷ nguyên mới"*, *"thay đổi cuộc chơi"*, *"trong thời đại ngày càng phát triển"*.
- **Avoid (EN)**: *"unlock"*, *"seamless"*, *"game-changer"*, *"revolutionize"*, *"cutting-edge"*, *"delve"*, *"in today's fast-paced world"*, *"paradigm shift"*.
- Replace adjectives with **specific mechanisms, numbers, comparisons, or scope boundaries**.

