"""HTML deck builder: one self-contained index.html (CSS/JS inline, fonts local or embedded)."""
from __future__ import annotations

import base64
import json
import mimetypes
import re
import shutil
from pathlib import Path

from .. import paths
from ..common import esc, rgba, L, lang_of
from ..spec import normalize, audit, load_theme, safe_local_image
from .layouts import RENDERERS, Seq

GENERIC_FALLBACK = {'serif': "Georgia, 'Times New Roman', serif", 'sans': "'Segoe UI', Arial, 'Helvetica Neue', sans-serif",
                    'mono': "Consolas, 'Courier New', monospace"}
SERIF_FAMILIES = {'Cormorant Garamond', 'Source Serif 4'}


def font_stack(family: str, role: str) -> str:
    kind = 'mono' if role == 'mono' else ('serif' if family in SERIF_FAMILIES else 'sans')
    # Fallbacks deliberately exclude Georgia for serif text: it lacks stacked Vietnamese diacritics on Windows.
    fb = "'Times New Roman', Cambria, serif" if kind == 'serif' else GENERIC_FALLBACK[kind]
    return f"'{family}', {fb}"


def presets() -> dict:
    return paths.read_json(paths.ASSETS / 'animations' / 'presets.json')['presets']


def theme_css(t: dict) -> str:
    c, ty, sp, f, m = t['colors'], t['type'], t['spacing'], t['fonts'], t.get('motion', {})
    orbs = (t.get('background') or {}).get('orbs') or [['accent', .10], ['accent2', .08]]
    dorbs = (t.get('background') or {}).get('dark_orbs') or [['accent', .22], ['accent2', .16]]
    dark = t.get('scheme') == 'dark'
    v = {
        'bg': c['bg'], 'surface': c['surface'], 'surface-alt': c['surface_alt'], 'ink': c['ink'], 'muted': c['muted'], 'subtle': c['subtle'],
        'line': c['line'], 'accent': c['accent'], 'accent-strong': c['accent_strong'], 'accent-soft': c['accent_soft'], 'on-accent': c['on_accent'],
        'accent2': c['accent2'], 'dark-bg': c['dark_bg'], 'dark-surface': c['dark_surface'], 'dark-ink': c['dark_ink'], 'dark-muted': c['dark_muted'],
        'dark-accent': c['dark_accent'], 'pos': c['positive'], 'neg': c['negative'], 'warn': c['warning'],
        'f-display': font_stack(f['display'], 'display'), 'f-body': font_stack(f['body'], 'body'), 'f-mono': font_stack(f['mono'], 'mono'),
        'w-display': f.get('display_weight', 700), 'w-body': f.get('body_weight', 400), 'track-display': f.get('display_tracking', '-0.02em'),
        'lh-display': f.get('display_line', 1.05),
        't-display': f"{ty['display']}px", 't-title': f"{ty['title']}px", 't-title-min': f"{ty['title_min']}px", 't-lead': f"{ty['lead']}px",
        't-body': f"{ty['body']}px", 't-small': f"{ty['small']}px", 't-caption': f"{ty['caption']}px", 't-eyebrow': f"{ty['eyebrow']}px",
        't-number': f"{ty['number']}px", 't-hero': f"{ty['number_hero']}px",
        'pad-x': f"{sp['pad_x']}px", 'pad-top': f"{sp['pad_top']}px", 'pad-bottom': f"{sp['pad_bottom']}px", 'gap': f"{sp['gap']}px",
        'radius': f"{sp['radius']}px", 'img-radius': f"{(t.get('image') or {}).get('radius', sp['radius'])}px",
        'ease': m.get('easing', 'cubic-bezier(.2,.7,.2,1)'), 'dur': f"{m.get('duration', 700)}ms", 'stagger': f"{m.get('stagger', 80)}ms",
        'dist': f"{m.get('distance', 24)}px",
        'orb1': rgba(c[orbs[0][0]], orbs[0][1] if not dark else .18), 'orb2': rgba(c[orbs[1][0] if len(orbs) > 1 else 'accent2'], orbs[1][1] if len(orbs) > 1 else .08),
        'orb1d': rgba(c[dorbs[0][0]], dorbs[0][1]), 'orb2d': rgba(c[dorbs[1][0] if len(dorbs) > 1 else 'accent2'], dorbs[1][1] if len(dorbs) > 1 else .16),
        'dot': rgba(c['accent'], .16), 'grid': rgba(c['ink'], .05),
    }
    return ':root{' + ';'.join(f'--{k}:{val}' for k, val in v.items()) + ';--speed:1}'


def font_faces(t: dict, dest: Path | None, embed: bool) -> str:
    meta = paths.read_json(paths.FONTS / 'fonts.json')['faces']
    want = {t['fonts']['display'], t['fonts']['body'], t['fonts']['mono']}
    user_fonts = paths.user_home() / 'fonts'
    if (user_fonts / 'fonts.json').exists():
        meta = meta + [dict(x, _user=True) for x in paths.read_json(user_fonts / 'fonts.json')['faces']]
    css = []
    for face in meta:
        if face['family'] not in want:
            continue
        src_path = (user_fonts if face.get('_user') else paths.FONTS) / face['file']
        if not src_path.exists():
            continue
        if embed:
            url = 'data:font/woff2;base64,' + base64.b64encode(src_path.read_bytes()).decode()
        else:
            (dest / 'fonts').mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest / 'fonts' / face['file'])
            url = 'fonts/' + face['file']
        css.append(f"@font-face{{font-family:'{face['family']}';src:url({url}) format('woff2');font-weight:{face['weight']};"
                   f"font-style:{face['style']};font-display:block}}")
    return ''.join(css)


def _footer(s, i, n, deck, ctx):
    srcs = [str(x) for x in (s.get('sources') or [])]
    status = s.get('data_status')
    tag = ''
    if status == 'illustrative':
        tag = f'<span class="demo">{esc(L(deck, "demo"))}</span>'
    elif status == 'estimate':
        tag = f'<span class="demo">{esc(L(deck, "estimate"))}</span>'
    src = (f'{esc(L(deck, "source"))}: ' + esc(' · '.join(srcs))) if srcs else ''
    page = '' if s['layout'] == 'cover' else f'{i:02d} <span>/ {n:02d}</span>'
    return (f'<footer class="foot"><div class="brand">{esc(deck.get("brand", ""))}</div>'
            f'<div class="source" title="{esc(" · ".join(srcs))}">{tag}{src}</div><div class="page">{page}</div></footer>')


def render_slide(s: dict, i: int, n: int, deck: dict, theme: dict, ctx: dict) -> str:
    lay = s['layout']
    A = Seq(build=bool(s.get('build', deck.get('build', False))))
    inner = RENDERERS[lay](s, A, ctx)
    dark = s.get('dark')
    if dark is None:
        dark = lay in (theme.get('dark_layouts') or [])
    classes = ['slide', f'l-{lay}']
    if dark:
        classes.append('is-dark')
    if lay == 'image-split' and s.get('side') == 'left':
        classes.append('media-left')
    if lay in ('full-bleed-image',):
        classes.append('photo')
    media = ''
    if '__MEDIA__' in inner:
        media, inner = inner.split('__ENDMEDIA__', 1)
        media = media.replace('__MEDIA__', '')
    bg = '' if lay in ('image-split', 'full-bleed-image') else '<div class="bg"></div>'
    if lay == 'image-split':
        content = inner
    else:
        content = f'<div class="slide-inner">{inner}</div>'
    notes = f'<aside class="notes">{esc(s["notes"]).replace(chr(10), "<br>")}</aside>' if s.get('notes') else ''
    return (f'<section class="{" ".join(classes)}" data-layout="{esc(lay)}" data-id="{esc(s["id"])}" data-index="{i}" '
            f'aria-label="{esc(i)} / {esc(n)}">{bg}{media}{content}{_footer(s, i, n, deck, ctx)}{notes}</section>')


def build(deck: dict, dest: Path, theme_name: str | None = None, assets_root: Path | None = None, single_file: bool = False,
          animation: str | None = None, strict: bool = False, theme_dirs: list[Path] | None = None) -> dict:
    d = normalize(deck)
    if theme_name:
        d['theme'] = theme_name
    theme = load_theme(d['theme'], extra_dirs=theme_dirs, overrides=d.get('theme_overrides'))
    report = audit(d, strict=strict, assets_root=assets_root, theme=theme)
    if not report['ok']:
        raise ValueError('Deck preflight failed:\n' + '\n'.join(f"  [{x['slide']}] {x['code']}: {x['message']}"
                                                                for x in report['issues'] if x['severity'] == 'error'))
    anim = animation or d.get('animation') or 'professional'
    pre = presets().get(anim)
    if not pre:
        raise ValueError(f'Unknown animation preset {anim!r}: choose one of {sorted(presets())}')
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    def img(rel: str) -> str:
        rel = safe_local_image(rel)
        src = Path(assets_root or '.') / rel
        if single_file and src.is_file():
            mime = mimetypes.guess_type(src.name)[0] or 'image/png'
            return f'data:{mime};base64,' + base64.b64encode(src.read_bytes()).decode()
        return esc('assets/' + rel)

    ctx = {'theme': theme, 'deck': d, 'lang': lang_of(d), 'anim': anim, 'img': img}
    slides = d['slides']
    n = len(slides)
    html_slides = ''.join(render_slide(s, i, n, d, theme, ctx) for i, s in enumerate(slides, 1))
    body_cls = [f"bg-{theme['background']['style']}", f"cards-{theme['cards']['style']}", f"eb-{theme['eyebrow']['style']}",
                f"ic-{theme['icons']['style']}", f'anim-{anim}', f"tr-{theme.get('motion', {}).get('transition', 'fade')}"] + pre['body']
    css = (paths.RUNTIME / 'deck.css').read_text(encoding='utf-8')
    js = (paths.RUNTIME / 'deck.js').read_text(encoding='utf-8')
    speed = pre.get('speed', 1)
    doc = (f'<!doctype html><html lang="{lang_of(d)}"><head><meta charset="utf-8">'
           f'<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="generator" content="aphrodite-slide 2">'
           f'<title>{esc(d.get("title", ""))}</title><style>{font_faces(theme, dest, single_file)}{theme_css(theme)}'
           f':root{{--speed:{speed}}}{css}</style></head>'
           f'<body class="{" ".join(body_cls)}"><div class="viewport"><div class="stage">{html_slides}</div></div>'
           f'<div class="hud"><i></i></div><div class="counter"></div><div class="help">{esc(L(d, "help"))}</div>'
           f'<div class="drawer"><span class="timer">00:00</span><h4>Notes</h4><div class="content"></div></div><div class="overview"></div>'
           f'<script>{js}</script></body></html>')
    (dest / 'index.html').write_text(doc, encoding='utf-8')
    if assets_root and Path(assets_root).is_dir() and not single_file:
        shutil.copytree(assets_root, dest / 'assets', dirs_exist_ok=True)
    (dest / 'deck.json').write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest = {'format': 'aphrodite-slide/2', 'title': d.get('title'), 'theme': theme['id'], 'animation': anim, 'language': d['language'],
                'slides': [{'index': i, 'id': s['id'], 'layout': s['layout'], 'title': s.get('title') or s.get('term') or ''} for i, s in enumerate(slides, 1)],
                'single_file': single_file, 'warnings': [x for x in report['issues'] if x['severity'] == 'warning']}
    (dest / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'index': str(dest / 'index.html'), 'slides': n, 'theme': theme['id'], 'animation': anim, 'audit': report}

