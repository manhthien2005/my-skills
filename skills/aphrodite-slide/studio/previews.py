"""Real rendered previews for templates/themes (never mock images)."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .html import build
from .registry import sample_deck, apply_template
from .render import render


def pick_slides(deck: dict, signature: list[str], n: int = 4) -> list[int]:
    slides = deck['slides']
    picks = [1]
    for lay in signature:
        for i, s in enumerate(slides, 1):
            if (s.get('layout') or s.get('type')) == lay and i not in picks:
                picks.append(i); break
        if len(picks) >= n:
            break
    for i in range(2, len(slides) + 1):
        if len(picks) >= n:
            break
        if i not in picks:
            picks.append(i)
    return sorted(picks[:n])


def composite(images: list[Path], out: Path, w: int = 1600):
    from PIL import Image
    gap = 10
    cw = (w - gap * 3) // 2
    ch = int(cw * 9 / 16)
    sheet = Image.new('RGB', (w, ch * 2 + gap * 3), '#D9DBE1')
    for k, f in enumerate(images[:4]):
        im = Image.open(f).convert('RGB').resize((cw, ch), Image.LANCZOS)
        sheet.paste(im, (gap + (k % 2) * (cw + gap), gap + (k // 2) * (ch + gap)))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=82, optimize=True)
    return out


def render_preview(deck: dict, out_jpg: Path, theme: str | None = None, assets_root: Path | None = None,
                   slides: list[int] | None = None, signature: list[str] | None = None) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix='aphro-prev-'))
    try:
        build(deck, tmp, theme_name=theme, assets_root=assets_root)
        picks = slides or pick_slides(deck, signature or [])
        res = render(tmp, pdf='none', motion=False, only=picks)
        imgs = [tmp / s['image'] for s in res['slides']]
        return composite(imgs, Path(out_jpg))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def template_previews(t: dict, themes: list[str] | None = None) -> list[Path]:
    deck = apply_template(sample_deck(t), t)
    tdir = Path(t['_dir'])
    assets = tdir / 'assets'
    outs = []
    for th in themes or t.get('compatible_themes') or [t['default_theme']]:
        p = render_preview(deck, tdir / 'previews' / f'{th}.jpg', theme=th, assets_root=assets if assets.is_dir() else None,
                           signature=t.get('signature_layouts', []))
        outs.append(p)
        if th == t.get('default_theme'):
            shutil.copy2(p, tdir / t.get('preview', 'preview.jpg'))
    return outs

