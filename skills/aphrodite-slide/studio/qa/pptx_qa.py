"""Structural, geometry and visual QA for exported PowerPoint (.pptx) files."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

EMU_PER_IN = 914400


def _box_in(shp) -> tuple[float, float, float, float]:
    x = (shp.left or 0) / EMU_PER_IN
    y = (shp.top or 0) / EMU_PER_IN
    w = (shp.width or 0) / EMU_PER_IN
    h = (shp.height or 0) / EMU_PER_IN
    return x, y, x + w, y + h


def _is_orb_or_bleed(shp, sw: float, sh: float) -> bool:
    x0, y0, x1, y1 = _box_in(shp)
    if shp.shape_type == MSO_SHAPE_TYPE.PICTURE and (y1 - y0) >= sh - 0.1:
        return True
    if not shp.has_text_frame or not shp.text_frame.text.strip():
        # Decorative orb or background scrim
        if x0 < -0.2 or y0 < -0.2 or x1 > sw + 0.2 or y1 > sh + 0.2:
            return True
    return False


def inspect_pptx(pptx_path: Path, out_report: Path | None = None) -> dict:
    """Validate structure, fonts, bounds, overlaps, native charts/tables and notes of a .pptx file."""
    pptx_path = Path(pptx_path)
    prs = Presentation(str(pptx_path))
    sw = prs.slide_width / EMU_PER_IN
    sh = prs.slide_height / EMU_PER_IN
    issues: list[dict] = []

    def flag(sev: str, slide_idx: int | str, code: str, msg: str):
        issues.append({'severity': sev, 'slide': slide_idx, 'code': code, 'message': msg})

    if abs(sw / sh - 16 / 9) > 0.02:
        flag('error', 'deck', 'pptx-aspect-ratio', f'Slide size is {sw:.2f}x{sh:.2f}in (expected 16:9)')

    native_charts = 0
    native_tables = 0
    notes_slides = 0
    transitions = 0
    timings = 0
    unassigned_runs = 0

    for idx, slide in enumerate(prs.slides, 1):
        sld = slide._element
        if sld.find(qn('p:transition')) is not None:
            transitions += 1
        if sld.find(qn('p:timing')) is not None:
            timings += 1
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            notes_slides += 1

        text_boxes: list[tuple[tuple[float, float, float, float], str, float]] = []
        editable_text_count = 0
        full_bleed_pics = 0

        for shp in slide.shapes:
            x0, y0, x1, y1 = _box_in(shp)
            if shp.has_chart:
                native_charts += 1
            if shp.has_table:
                native_tables += 1
                editable_text_count += 1
                for row in shp.table.rows:
                    for cell in row.cells:
                        for p in cell.text_frame.paragraphs:
                            for r in p.runs:
                                if r.text.strip():
                                    if not r.font.name:
                                        unassigned_runs += 1
                                    elif r.font.name.lower() == 'georgia':
                                        flag('error', idx, 'pptx-banned-font', 'Table run uses Georgia (breaks Vietnamese stacked diacritics)')

            if shp.shape_type == MSO_SHAPE_TYPE.PICTURE and (x1 - x0) >= sw * 0.95 and (y1 - y0) >= sh * 0.95:
                full_bleed_pics += 1

            is_content = shp.has_chart or shp.has_table or (shp.has_text_frame and bool(shp.text_frame.text.strip()))
            if is_content and not _is_orb_or_bleed(shp, sw, sh):
                if x0 < -0.08 or y0 < -0.08 or x1 > sw + 0.08 or y1 > sh + 0.08:
                    txt_preview = shp.text_frame.text.strip()[:40] if shp.has_text_frame else shp.name
                    flag('error', idx, 'pptx-outside-slide', f'Shape extends outside slide ({x0:.2f},{y0:.2f})-({x1:.2f},{y1:.2f}): "{txt_preview}"')

            if shp.has_text_frame and shp.text_frame.text.strip():
                editable_text_count += 1
                max_pt = 12.0
                for p in shp.text_frame.paragraphs:
                    for r in p.runs:
                        if not r.text.strip():
                            continue
                        if r.font.size:
                            max_pt = max(max_pt, r.font.size.pt)
                        if not r.font.name:
                            unassigned_runs += 1
                        elif r.font.name.lower() == 'georgia':
                            flag('error', idx, 'pptx-banned-font', f'Text run uses Georgia: "{r.text[:30]}"')
                # Exclude giant background watermark numbers (>=90pt) from overlap checks
                if max_pt < 90:
                    text_boxes.append(((x0, y0, x1, y1), shp.text_frame.text.strip().replace('\n', ' ')[:36], max_pt))

        if full_bleed_pics > 0 and editable_text_count == 0:
            flag('error', idx, 'pptx-rasterized-slide', 'Slide contains only a full-bleed picture with zero editable text shapes')

        # Pairwise text-box overlap check
        for i in range(len(text_boxes)):
            (ax0, ay0, ax1, ay1), atxt, _ = text_boxes[i]
            a_area = max(0.001, (ax1 - ax0) * (ay1 - ay0))
            for j in range(i + 1, len(text_boxes)):
                (bx0, by0, bx1, by1), btxt, _ = text_boxes[j]
                ix = max(0.0, min(ax1, bx1) - max(ax0, bx0))
                iy = max(0.0, min(ay1, by1) - max(ay0, by0))
                inter = ix * iy
                if inter <= 0.01:
                    continue
                b_area = max(0.001, (bx1 - bx0) * (by1 - by0))
                if inter / min(a_area, b_area) > 0.22:
                    flag('error', idx, 'pptx-text-overlap', f'Text boxes overlap: "{atxt}" × "{btxt}"')

    if unassigned_runs > 0:
        flag('warning', 'deck', 'pptx-unassigned-font', f'{unassigned_runs} text runs rely on PowerPoint master default font')

    errors = sum(1 for x in issues if x['severity'] == 'error')
    warnings = sum(1 for x in issues if x['severity'] == 'warning')
    report = {
        'ok': errors == 0,
        'pptx': str(pptx_path),
        'slides': len(prs.slides),
        'size_in': [round(sw, 3), round(sh, 3)],
        'native_charts': native_charts,
        'native_tables': native_tables,
        'notes_slides': notes_slides,
        'transitions': transitions,
        'entrances': timings,
        'error_count': errors,
        'warning_count': warnings,
        'issues': issues,
    }
    if out_report:
        Path(out_report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def render_pptx(pptx_path: Path, out_dir: Path, width: int = 1920, height: int = 1080) -> dict:
    """Render a .pptx file into per-slide PNGs + contact sheet using PowerPoint COM (Windows) or LibreOffice."""
    pptx_path = Path(pptx_path).resolve()
    out_dir = Path(out_dir).resolve()
    slides_dir = out_dir / 'pptx-previews'
    slides_dir.mkdir(parents=True, exist_ok=True)
    for old in slides_dir.glob('slide-*.png'):
        old.unlink()

    engine = None
    err_msg = None

    # 1. Try Microsoft PowerPoint COM on Windows (stage through short temp dir to avoid 255-char COM path limits)
    if shutil.which('powershell'):
        import os
        import tempfile
        with tempfile.TemporaryDirectory(prefix='aph_pptx_') as tmp:
            tmp_dir = Path(tmp)
            tmp_in = tmp_dir / 'deck.pptx'
            tmp_out = tmp_dir / 'out'
            tmp_out.mkdir()
            shutil.copy2(pptx_path, tmp_in)
            ps_script = (
                "$ErrorActionPreference = 'Stop'\n"
                "$inPath = $env:APH_PPTX_IN; $outDir = $env:APH_PPTX_OUT\n"
                "$w = [int]$env:APH_PPTX_W; $h = [int]$env:APH_PPTX_H\n"
                "$app = New-Object -ComObject PowerPoint.Application\n"
                "$pres = $null\n"
                "try {\n"
                "  $pres = $app.Presentations.Open($inPath, -1, 0, 0)\n"
                "  $i = 1\n"
                "  foreach ($s in $pres.Slides) {\n"
                "    $dest = Join-Path $outDir ('slide-{0:D2}.png' -f $i)\n"
                "    $s.Export($dest, 'PNG', $w, $h)\n"
                "    $i++\n"
                "  }\n"
                "} finally {\n"
                "  if ($pres -ne $null) { $pres.Close() }\n"
                "  if ($app.Presentations.Count -eq 0) { $app.Quit() }\n"
                "}\n"
            )
            env = dict(os.environ, APH_PPTX_IN=str(tmp_in), APH_PPTX_OUT=str(tmp_out), APH_PPTX_W=str(width), APH_PPTX_H=str(height))
            proc = subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_script],
                capture_output=True, text=True, timeout=180, env=env
            )
            if proc.returncode == 0 and any(tmp_out.glob('slide-*.png')):
                for p in sorted(tmp_out.glob('slide-*.png')):
                    shutil.copy2(p, slides_dir / p.name)
                engine = 'powerpoint-com'
            else:
                err_msg = (proc.stderr or proc.stdout or '').strip()[:300]

    # 2. Fallback to LibreOffice + PyMuPDF
    if engine is None and shutil.which('soffice'):
        proc = subprocess.run(
            ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', str(slides_dir), str(pptx_path)],
            capture_output=True, text=True, timeout=120
        )
        pdf_cand = slides_dir / (pptx_path.stem + '.pdf')
        if proc.returncode == 0 and pdf_cand.exists():
            try:
                import fitz
                doc = fitz.open(str(pdf_cand))
                for i, page in enumerate(doc, 1):
                    pix = page.get_pixmap(dpi=150)
                    pix.save(str(slides_dir / f'slide-{i:02d}.png'))
                doc.close()
                pdf_cand.unlink(missing_ok=True)
                engine = 'libreoffice'
            except Exception as exc:  # noqa: BLE001
                err_msg = str(exc)

    pngs = sorted(slides_dir.glob('slide-*.png'))
    contact = None
    if pngs:
        from PIL import Image, ImageDraw
        cols, tw = 4, 460
        th = int(tw * 9 / 16)
        rows = (len(pngs) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * (tw + 16) + 16, rows * (th + 40) + 16), '#E7E8EC')
        dr = ImageDraw.Draw(sheet)
        for k, f in enumerate(pngs):
            im = Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS)
            x, y = 16 + (k % cols) * (tw + 16), 16 + (k // cols) * (th + 40)
            sheet.paste(im, (x, y))
            dr.text((x, y + th + 8), f.stem, fill='#222222')
        contact = out_dir / 'pptx-contact-sheet.jpg'
        sheet.save(contact, quality=88)

    return {
        'rendered': bool(pngs),
        'engine': engine,
        'slides': [str(p) for p in pngs],
        'contact_sheet': str(contact) if contact else None,
        'error': None if pngs else (err_msg or 'Neither Microsoft PowerPoint nor LibreOffice is available'),
    }
