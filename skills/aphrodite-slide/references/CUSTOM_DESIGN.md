# Custom Design & Personal Template Library (`CUSTOM_DESIGN.md`)

Users are never locked into default templates. Support designing from scratch, from a brand guide, from reference screenshots, or by remixing existing themes/templates.

## 1. Creating or Deriving a Custom Theme

Inspect any reference image or brand specification (canvas mood, primary/secondary hex colors, serif vs geometric sans, card style, dark vs light bookends), then create a derived theme:

```bash
python "<SKILL_DIR>/scripts/studio.py" themes new emerald-editorial \
  --base editorial-warm \
  --scope user \
  --name "Emerald Editorial" \
  --description "Warm cream paper with deep forest emerald accents" \
  --set colors.accent=#15803D \
  --set colors.accent_strong=#166534 \
  --set colors.accent_soft=#DCFCE7 \
  --set colors.dark_bg=#0C1A14 \
  --set colors.dark_surface=#142920 \
  --set colors.dark_accent=#6EE7B7
```

- **Built-in Quality Gates**: `themes new` automatically enforces WCAG contrast (`ink` ≥ 7:1, `muted`/`subtle` ≥ 4.5:1, `on_accent` on `accent_strong` ≥ 3:1) and verifies that `display` and `body` fonts are bundled in `assets/fonts/coverage.json` so Vietnamese glyphs never break.
- **Hybrid Scope**:
  - `--scope user` *(default)*: Saves to `~/.aphrodite-slide/themes/` (`APHRODITE_HOME`) — safe for private/client brand kits outside Git.
  - `--scope repo`: Saves to `skills/aphrodite-slide/assets/themes/` — for clean, reusable themes meant to commit to Git.

## 2. Mandatory Style Preview Before Full Build

Whenever designing a new style, render a 4-slide composite preview (`cover`, `cards`, `chart`, `closing`) and inspect/show it to the user **before** producing the entire deck:

```bash
python "<SKILL_DIR>/scripts/studio.py" preview \
  --theme emerald-editorial \
  --title "Xem trước phong cách thiết kế mới" \
  --out "<out_dir>/style-preview.jpg"
```

## 3. Opt-In Template Saving After Delivery

After completing a custom or customized deck and confirming the user is happy with the result, ask:

> **"Anh có muốn lưu phong cách thiết kế này thành template để sử dụng cho những lần sau không?"**

**Only save if the user says yes.** Then run:

```bash
python "<SKILL_DIR>/scripts/studio.py" templates save "<out_dir>/deck.json" \
  --id my-emerald-brief \
  --name "Emerald Executive Brief" \
  --name-vi "Báo cáo Điều hành Emerald" \
  --use-cases "business,executive" \
  --tags "emerald,editorial,executive,kpi" \
  --description "Phong cách editorial ấm kết hợp xanh ngọc lục bảo cho báo cáo điều hành" \
  --scope user
```

### Privacy, Versioning & Reuse Verification Guarantees
1. **Privacy-scrubbed by default**: Without `--include-content`, `templates save` strips all user text/numbers and generates a neutral sample deck (`studio/samples.py`) matching the deck's storyline and layout rhythm. If `--include-content` is requested, an automated PII scanner blocks emails, phone numbers, URLs, and ID numbers unless `--allow-sensitive` is explicitly confirmed by the user.
2. **Real thumbnail & registry**: Automatically renders `preview.jpg` and updates `assets/registry.json` (when `--scope repo`; user templates in `~/.aphrodite-slide/templates` are merged dynamically at runtime).
3. **No silent overwrite**: Updating an existing template ID fails unless `--bump patch|minor|major` is passed; previous versions are archived under `versions/<old_semver>/`.
4. **Verify reuse on another topic**:
   ```bash
   python "<SKILL_DIR>/scripts/studio.py" templates test my-emerald-brief \
     --other "<SKILL_DIR>/examples/logistics/deck.json"
   ```

