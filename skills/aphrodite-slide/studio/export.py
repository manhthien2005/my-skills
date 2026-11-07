"""Unified multi-format export pipeline: HTML + PDF (vector/image) + PNG + Visual QA + native PPTX + PPTX QA."""
from __future__ import annotations

import json
from pathlib import Path

from .html import build as build_html
from .pptx import export as export_pptx
from .qa import evaluate as evaluate_html_qa
from .qa.pptx_qa import inspect_pptx, render_pptx
from .render import render as render_html
from .spec import audit, load_theme, normalize


def export_all(deck: dict, out_dir: Path, theme_name: str | None = None, animation: str | None = None,
               assets_root: Path | None = None, single_file: bool = False, pdf: str = 'vector',
               pptx_enabled: bool = True, transitions: bool = True, entrances: bool = False,
               render_pptx_previews: bool = False, strict: bool = False) -> dict:
    """Build HTML, render PNGs/PDF + QA (when Playwright is available), and export native PPTX + QA."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    d = normalize(deck)
    if theme_name:
        d['theme'] = theme_name
    theme = load_theme(d['theme'], overrides=d.get('theme_overrides'))
    content_audit = audit(d, strict=strict, assets_root=assets_root, theme=theme)

    html_res = build_html(d, out_dir, theme_name=theme_name, assets_root=assets_root,
                          single_file=single_file, animation=animation, strict=strict)
    summary: dict = {'out_dir': str(out_dir), 'html': html_res, 'render': None, 'qa': None, 'pptx': None, 'pptx_qa': None}

    try:
        ren = render_html(out_dir, pdf=pdf, motion=(animation or d.get('animation', 'professional')) != 'none')
        qa = evaluate_html_qa(ren, content=content_audit, folder=out_dir)
        summary['render'] = {'files': ren.get('files', {}), 'slides': len(ren.get('slides', []))}
        summary['qa'] = {'ok': qa['ok'], 'visual_errors': qa['visual_errors'], 'visual_warnings': qa['visual_warnings'],
                         'report': str(out_dir / 'qa-report.json'), 'markdown': str(out_dir / 'qa-report.md')}
    except RuntimeError as ex:
        summary['render'] = {'skipped': True, 'reason': str(ex)}

    if pptx_enabled:
        pptx_path = out_dir / 'deck.pptx'
        px = export_pptx(d, pptx_path, theme_name=theme_name, assets_root=assets_root,
                         transitions=transitions, entrances=entrances, strict=strict)
        pqa = inspect_pptx(pptx_path, out_report=out_dir / 'pptx-qa.json')
        if render_pptx_previews:
            pqa['visual_render'] = render_pptx(pptx_path, out_dir)
            (out_dir / 'pptx-qa.json').write_text(json.dumps(pqa, ensure_ascii=False, indent=2), encoding='utf-8')
        summary['pptx'] = px
        summary['pptx_qa'] = pqa

    (out_dir / 'export-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary

