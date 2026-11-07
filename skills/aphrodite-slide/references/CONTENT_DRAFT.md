# Content-First Workflow & Baseline (`CONTENT_DRAFT.md`)

Default production pipeline:
**Input → Content Analysis → Storyline → `outline.md` Draft → User Approval (Baseline) → Visual Production**

## 1. Authoring `outline.md`

Scaffold from the chosen template or write `<out_dir>/outline.md` directly so the user can open and edit the file:

```bash
python "<SKILL_DIR>/scripts/studio.py" outline scaffold --template academic-defense --out "<out_dir>/outline.md"
```

### `outline.md` Structure

```markdown
---
title: Giấc ngủ và kết quả học tập của sinh viên năm nhất
audience: Hội đồng chấm khóa luận
purpose: Bảo vệ kết quả nghiên cứu cắt ngang 12 phút
takeaway: Sinh viên ngủ đủ 7–8 giờ có GPA cao hơn có ý nghĩa thống kê sau khi kiểm soát khoa và giới.
template: academic-defense
theme: editorial-warm
language: vi
density: speaker
duration_minutes: 12
---

## 01 · Giấc ngủ và **kết quả học tập** của sinh viên năm nhất
- layout: cover
- beat: title
- message: Nghiên cứu cắt ngang trên 412 sinh viên năm nhất kết hợp nhật ký ngủ 14 ngày.
- content:
  - Sinh viên: Nguyễn Văn A
  - Giảng viên hướng dẫn: TS. Trần Thị B
- status: illustrative
- notes: Chào hội đồng, nêu câu hỏi trung tâm trong 20 giây đầu.

## 06 · Điểm trung bình cao nhất ở nhóm ngủ 7–8 giờ mỗi đêm
- layout: chart
- beat: results
- message: GPA trung bình đạt 3,21 ở nhóm ngủ 7–8 giờ, cao hơn nhóm ngủ dưới 6 giờ (2,71).
- content:
  - Khác biệt duy trì sau hồi quy đa biến (p < 0,01)
  - Ngủ trên 8 giờ không làm tăng thêm GPA (3,05)
- data: <6h: 2,71 | 6-7h: 2,94 | 7-8h: 3,21 | >8h: 3,05
- status: illustrative
- visual: Biểu đồ cột đơn tô nổi nhóm 7–8 giờ kèm 2 insight bên phải
- sources: Khảo sát mẫu minh họa (2026)
- notes: Nhấn mạnh đây là tương quan cắt ngang, chưa kết luận nhân quả.
```

## 2. Lint & Gate 1 (Mandatory Approval)

```bash
python "<SKILL_DIR>/scripts/studio.py" outline lint "<out_dir>/outline.md"
```

Fix any lint errors (`no-message`, `unsourced` numbers without `status: illustrative`), review warnings (`generic-title`, `label-title`, `dense`, `filler`), then **stop and ask the user to approve `<out_dir>/outline.md`** (skipping Gate 1 only when the user explicitly asked for immediate generation).

## 3. Baseline Lock & Controlled Revisions

Once approved:
```bash
python "<SKILL_DIR>/scripts/studio.py" outline approve "<out_dir>/outline.md" --note "Approved by user"
```

- Snapshots `<out_dir>/.aphrodite/outline.baseline.json` (archiving previous baselines with timestamps).
- When the user edits `outline.md` or requests content changes later:
  1. Run `python "<SKILL_DIR>/scripts/studio.py" outline diff "<out_dir>/outline.md"`.
  2. Update **only** the changed slides in `deck.json` and check impact on takeaway/summary slides.
  3. Never silently rewrite unrequested slides; `studio.py validate deck.json --outline outline.md` flags any off-baseline drift.

