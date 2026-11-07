"""Native editable PowerPoint (.pptx) exporter v2."""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from .. import paths
from ..common import L, lang_of, plain
from ..spec import audit, load_theme, normalize, safe_local_image
from .draw import Canvas, add_entrances, add_transition, rgb
from .layouts import H, RENDERERS, W, W_IN, X0

SAFE_PPTX_FONTS = {'display': 'Cambria', 'body': 'Calibri', 'mono': 'Consolas'}


def _resolve_fonts(theme: dict, use_theme_fonts: bool) -> dict:
    if use_theme_fonts:
        tf = theme.get('fonts') or {}
        return {
            'display': tf.get('display', SAFE_PPTX_FONTS['display']),
            'body': tf.get('body', SAFE_PPTX_FONTS['body']),
            'mono': tf.get('mono', SAFE_PPTX_FONTS['mono']),
        }
    pf = dict(SAFE_PPTX_FONTS)
    pf.update(theme.get('pptx_fonts') or {})
    # Never allow Georgia on Vietnamese/bilingual slides due to detached stacked diacritics on Windows
    for k, v in list(pf.items()):
        if str(v).strip().lower() == 'georgia':
            pf[k] = 'Cambria'
    return pf


def _draw_background(cv: Canvas, s: dict):
    bg = cv.s.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = rgb(cv.c['bg'])
    if s['layout'] in ('full-bleed-image',):
        return
    bcfg = cv.t.get('background') or {}
    if bcfg.get('style') == 'orbs':
        orbs = bcfg.get('dark_orbs' if cv.dark else 'orbs') or []
        coords = {'top-right': (11.6, 1.1, 3.2), 'bottom-right': (11.4, 6.4, 2.8), 'top-left': (1.6, 1.2, 3.0), 'bottom-left': (1.8, 6.3, 2.8)}
        for idx, entry in enumerate(orbs[:2]):
            ckey = entry[0] if entry else 'accent'
            alpha = float(entry[1]) if len(entry) > 1 else (0.18 if cv.dark else 0.09)
            pos = entry[2] if len(entry) > 2 else ('top-right' if idx == 0 else 'bottom-right')
            cx, cy, r = coords.get(pos, (11.5, 1.2 if idx == 0 else 6.3, 2.9))
            col = cv.c.get(ckey, cv.c['accent'])
            cv.orb(cx, cy, r, col, min(0.30, alpha))


def _draw_footer(cv: Canvas, s: dict, idx: int, total: int, deck: dict):
    # Track footer nowhere in animation groups so headers/footers stay steady
    prev_g = cv._g
    cv._g = None
    try:
        lay = s['layout']
        over_photo = lay == 'full-bleed-image'
        split_left = lay == 'image-split' and s.get('side') == 'left'
        split_right = lay == 'image-split' and s.get('side') != 'left'
        fy = 6.94
        brand = str(deck.get('brand') or '')
        if brand:
            bcol = '#E5E7EB' if (over_photo or split_left) else cv.c['subtle']
            bw_box = 2.45 if split_right else 3.40
            if split_left:
                bw = min(3.4, len(brand) * 0.075 + 0.28)
                cv.rect(X0 - 0.10, fy - 0.02, bw, 0.26, fill='#000000', radius=0.13, alpha=0.50)
            cv.text(X0, fy, bw_box, 0.24, brand, 8.0, color=bcol, bold=True, caps=True, tracking=70, check=False)

        srcs = [str(x) for x in (s.get('sources') or [])]
        status = s.get('data_status')
        parts = []
        if status == 'illustrative':
            parts.append(f"● {L(deck, 'demo').upper()}")
        elif status == 'estimate':
            parts.append(f"● {L(deck, 'estimate').upper()}")
        if srcs:
            parts.append(f"{L(deck, 'source')}: {' · '.join(srcs)}")
        if parts:
            scol = '#E5E7EB' if over_photo else cv.c['subtle']
            if split_left:
                sx, sw, align = 6.72, 4.45, 'l'
            elif split_right:
                sx, sw, align = (X0 + 2.55 if brand else X0), (3.25 if brand else 5.70), 'l'
            elif not brand:
                sx, sw, align = X0, 8.50, 'l'
            else:
                sx, sw, align = 4.45, 5.80, 'c'
            cv.text(sx, fy, sw, 0.24, '   '.join(parts), 8.0, color=scol, align=align, check=False)

        if lay != 'cover':
            pcol = '#FFFFFF' if (over_photo or split_right) else cv.c['subtle']
            if split_right:
                cv.rect(X0 + W_IN - 0.86, fy - 0.02, 0.92, 0.26, fill='#000000', radius=0.13, alpha=0.50)
            cv.text(X0 + W_IN - 0.80, fy, 0.80, 0.24, f'{idx:02d} / {total:02d}', 8.5,
                    color=pcol, bold=True, font='mono', align='r', check=False)
    finally:
        cv._g = prev_g


def export(deck: dict, out_path: Path, theme_name: str | None = None, assets_root: Path | None = None,
           transitions: bool = True, entrances: bool = False, use_theme_fonts: bool = False,
           strict: bool = False, theme_dirs: list[Path] | None = None) -> dict:
    """Export normalized deck spec to a native editable .pptx file."""
    d = normalize(deck)
    if theme_name:
        d['theme'] = theme_name
    theme = load_theme(d['theme'], extra_dirs=theme_dirs, overrides=d.get('theme_overrides'))
    report = audit(d, strict=strict, assets_root=assets_root, theme=theme)
    if not report['ok']:
        raise ValueError('Deck preflight failed:\n' + '\n'.join(
            f"  [{x['slide']}] {x['code']}: {x['message']}" for x in report['issues'] if x['severity'] == 'error'))

    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    blank = prs.slide_layouts[6]

    fonts = _resolve_fonts(theme, use_theme_fonts=use_theme_fonts)
    warnings: list[dict] = []
    anim = d.get('animation') or 'professional'
    tr_default = (theme.get('motion') or {}).get('transition', 'fade')
    icons_png = paths.ICONS / 'png'

    def img_path(rel: str) -> Path | None:
        if not rel:
            return None
        clean = safe_local_image(rel)
        cand = Path(assets_root or '.') / clean
        return cand if cand.exists() else None

    ctx = {'deck': d, 'theme': theme, 'lang': lang_of(d), 'img_path': img_path, 'icons_png': icons_png}
    slides = d['slides']
    total = len(slides)
    chart_count = 0
    table_count = 0
    notes_count = 0

    for idx, s in enumerate(slides, 1):
        lay = s['layout']
        dark = s.get('dark')
        if dark is None:
            dark = (theme.get('scheme') == 'dark') or (lay in (theme.get('dark_layouts') or []))
        slide = prs.slides.add_slide(blank)
        cv = Canvas(slide, theme, fonts, dark=bool(dark), warnings=warnings, sid=s['id'])
        _draw_background(cv, s)
        RENDERERS[lay](cv, s, ctx)
        _draw_footer(cv, s, idx, total, d)

        if lay == 'chart':
            chart_count += 1
        elif lay == 'table':
            table_count += 1

        if s.get('notes'):
            ns = slide.notes_slide
            ns.notes_text_frame.text = plain(s['notes'])
            notes_count += 1

        if transitions and anim != 'none':
            kind = 'push' if (lay == 'section' and (anim == 'cinematic' or tr_default == 'push')) else ('push' if tr_default == 'push' else 'fade')
            add_transition(slide, kind, speed='med')
        if entrances and anim not in ('none', 'subtle'):
            add_entrances(slide, cv.groups, on_click=bool(s.get('build', d.get('build', False))))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))

    fallback_notes = []
    if anim in ('professional', 'cinematic'):
        fallback_notes.append('HTML count-up numbers, SVG path draw, and clip-path mask/zoom effects export in their final static state in PPTX.')
    if not entrances and anim not in ('none', 'subtle'):
        fallback_notes.append('Slide transitions are enabled; intra-slide fade entrances are off by default (pass --entrances to enable experimental OOXML group fades).')
    if not use_theme_fonts:
        fallback_notes.append(f"PPTX uses Office-safe Vietnamese-capable fonts ({fonts['display']} / {fonts['body']}) so slides open cleanly on machines without bundled web fonts.")

    return {
        'pptx': str(out_path),
        'slides': total,
        'theme': theme['id'],
        'fonts': fonts,
        'native_charts': chart_count,
        'native_tables': table_count,
        'notes_slides': notes_count,
        'transitions': bool(transitions and anim != 'none'),
        'entrances': bool(entrances and anim not in ('none', 'subtle')),
        'warnings': warnings,
        'motion_fallback': fallback_notes,
    }
