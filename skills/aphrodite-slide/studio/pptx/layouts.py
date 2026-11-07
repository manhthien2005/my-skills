"""All 25 slide layouts rendered as native editable PowerPoint shapes, tables, pictures and charts."""
from __future__ import annotations

import math
from lxml import etree
from pptx.enum.text import MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from ..common import L, contrast, mix, plain, runs as split_runs
from .charts import add_native_chart, draw_sparkline
from .draw import Canvas, fit_size, rgb, wrap_lines

W, H = 13.3333, 7.5
X0, W_IN = 0.88, 11.5733
Y_TOP, Y_MAX = 0.66, 6.58


def _pal(cv: Canvas, i: int) -> str:
    s = cv.t['colors']['series']
    return s[i % len(s)]


def _card(cv: Canvas, x: float, y: float, w: float, h: float, hl: bool = False):
    style = cv.t.get('cards', {}).get('style', 'line')
    rad = min(0.22, cv.t['spacing']['radius'] / 144)
    if cv.dark:
        fill = mix(cv.c['surface'], cv.c['accent'], 0.14) if hl else cv.c['surface']
        line = cv.c['accent_strong'] if hl else cv.c['line']
        return cv.rect(x, y, w, h, fill=fill, line=line, radius=rad, line_w=1.5 if hl else 0.9)
    if style == 'tint':
        fill = cv.c['accent_soft'] if hl else cv.c['surface_alt']
        line = cv.c['accent_strong'] if hl else None
    elif style in ('paper', 'glass'):
        fill = mix(cv.c['surface'], cv.c['accent_soft'], 0.35) if hl else cv.c['surface']
        line = cv.c['accent_strong'] if hl else cv.c['line']
    else:
        fill = mix(cv.c['surface'], cv.c['accent_soft'], 0.30) if hl else cv.c['surface']
        line = cv.c['accent_strong'] if hl else cv.c['line']
    return cv.rect(x, y, w, h, fill=fill, line=line, radius=rad, line_w=1.6 if hl else 0.9)


def _eyebrow(cv: Canvas, text: str | None, x: float, y: float, w: float = 8.0) -> float:
    if not text:
        return y
    style = cv.t.get('eyebrow', {}).get('style', 'caps')
    col = cv.c['dark_accent'] if cv.dark else cv.c['accent_strong']
    label = str(text).strip()
    if style == 'dot':
        cv.oval(x, y + 0.065, 0.09, 0.09, fill=col)
        cv.text(x + 0.16, y, w - 0.16, 0.24, label, 9.5, color=col, bold=True, caps=True, tracking=120, check=False)
    elif style == 'line':
        cv.rect(x, y + 0.095, 0.28, 0.025, fill=col)
        cv.text(x + 0.36, y, w - 0.36, 0.24, label, 9.5, color=col, bold=True, caps=True, tracking=120, check=False)
    elif style == 'pill':
        tw = min(w, max(0.9, len(label) * 0.095 + 0.34))
        cv.rect(x, y - 0.01, tw, 0.26, fill=cv.c['accent_soft'], radius=0.13)
        cv.text(x + 0.14, y, tw - 0.28, 0.24, label, 9.0, color=col, bold=True, caps=True, align='c', anchor='m', tracking=90, check=False)
    elif style == 'code':
        cv.text(x, y, w, 0.24, f'// {label}', 9.5, color=col, bold=True, font='mono', caps=True, tracking=90, check=False)
    else:
        cv.text(x, y, w, 0.24, label, 9.5, color=col, bold=True, caps=True, tracking=120, check=False)
    return y + 0.30


def header(cv: Canvas, s: dict, ctx: dict, x: float = X0, y: float = Y_TOP, w: float = W_IN, title_pt: float = 32, min_pt: float = 21) -> float:
    """Draw eyebrow + title + subtitle and return the Y coordinate where body content begins."""
    cv.group()
    cy = _eyebrow(cv, s.get('eyebrow'), x, y, w=w * 0.82)
    if s.get('title'):
        fname = cv.f['display']
        sz, lines, _ = fit_size(s['title'], fname, title_pt, min_pt, w, 1.32, bold=True, spacing=1.06, max_lines=2)
        th = max(0.52, lines * sz * 1.10 / 72 + 0.06)
        cv.text(x, cy, w, th, s['title'], sz, bold=True, font='display', min_size=min_pt, spacing=1.05, max_lines=2)
        cy += th + 0.06
    if s.get('subtitle'):
        fname = cv.f['body']
        sz, lines, _ = fit_size(s['subtitle'], fname, 14.5, 11.5, w * 0.92, 0.66, spacing=1.18, max_lines=2)
        sh = max(0.28, lines * sz * 1.22 / 72 + 0.04)
        cv.text(x, cy, w * 0.92, sh, s['subtitle'], sz, color=cv.c['muted'], min_size=11.5, spacing=1.18)
        cy += sh + 0.06
    return cy + 0.14


def _bullet_list(cv: Canvas, items: list, x: float, y: float, w: float, h: float, tone: str = 'positive', font_pt: float = 13.0):
    if not items:
        return
    n = len(items)
    mark = {'positive': '✓', 'negative': '✕', 'neutral': '→'}.get(tone, '•')
    mcol = {'positive': cv.c['positive'], 'negative': cv.c['negative'], 'neutral': cv.c['accent_strong']}.get(tone, cv.c['accent_strong'])
    gap = 0.08
    slot_h = (h - gap * max(0, n - 1)) / n
    fname = cv.f['body']
    # Pick uniform size across bullets so all bullets share consistent typography
    pt = font_pt
    for it in items:
        s_fit, _, _ = fit_size(str(it), fname, pt, 10.0, w - 0.34, slot_h, spacing=1.15)
        pt = min(pt, s_fit)
    cy = y
    for it in items:
        lines = wrap_lines(str(it), fname, pt, w - 0.34)
        bh = min(slot_h, max(0.28, lines * pt * 1.20 / 72 + 0.04))
        cv.text(x, cy, 0.26, 0.28, mark, pt, color=mcol, bold=True, check=False)
        cv.text(x + 0.30, cy, w - 0.30, slot_h, str(it), pt, color=cv.c['ink'], min_size=9.5, spacing=1.15)
        cy += max(bh + 0.08, slot_h if n <= 4 else bh + 0.06)
        if cy > y + h - 0.12:
            break


def _meta_strip(cv: Canvas, items: list, x: float, y: float, w: float):
    if not items:
        return
    cv.group()
    cv.line(x, y, x + min(w, len(items) * 2.5), y, cv.c['line'], width=0.8)
    cw = min(2.6, w / max(1, len(items)))
    for i, m in enumerate(items[:4]):
        s = str(m)
        k, _, v = s.partition(':') if ':' in s else ('', '', s)
        cx = x + i * cw
        if k:
            cv.text(cx, y + 0.10, cw - 0.15, 0.20, k.strip(), 8.5, color=cv.c['muted'], bold=True, caps=True, tracking=90, check=False)
            cv.text(cx, y + 0.31, cw - 0.15, 0.34, v.strip(), 12.0, color=cv.c['ink'], bold=True, min_size=10)
        else:
            cv.text(cx, y + 0.16, cw - 0.15, 0.34, v.strip(), 12.0, color=cv.c['ink'], bold=True, min_size=10)


# ----------------------------------------------------------------------------- 25 Layouts

def cover(cv: Canvas, s: dict, ctx: dict):
    has_img = bool(s.get('image'))
    tw = 6.15 if has_img else 10.6
    cv.group()
    _eyebrow(cv, s.get('eyebrow'), X0, Y_TOP, w=tw)
    title_y = 1.85 if not has_img else 1.55
    fname = cv.f['display']
    sz, lines, _ = fit_size(s.get('title', ''), fname, 48 if not has_img else 38, 26, tw, 2.35, bold=True, spacing=1.03, max_lines=3)
    th = max(0.95, lines * sz * 1.07 / 72 + 0.08)
    cv.text(X0, title_y, tw, th, s.get('title', ''), sz, bold=True, font='display', min_size=26, spacing=1.03)
    cy = title_y + th + 0.14
    if s.get('subtitle'):
        cv.text(X0, cy, tw * 0.92, 0.85, s['subtitle'], 15.5, color=cv.c['muted'], min_size=12, spacing=1.22)
    if s.get('meta'):
        _meta_strip(cv, s['meta'], X0, 5.68, tw)
    if has_img:
        cv.group()
        p = ctx['img_path'](s['image'])
        if p and p.is_file():
            cv.picture(p, 7.38, 0.68, 5.07, 5.82)
        else:
            _card(cv, 7.38, 0.68, 5.07, 5.82)


def agenda(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    items = [it if isinstance(it, dict) else {'title': str(it)} for it in (s.get('items') or [])]
    if not items:
        return
    two = len(items) > 4
    cols = 2 if two else 1
    rows = math.ceil(len(items) / cols)
    cw = (W_IN - (0.55 if two else 0)) / cols
    rh = min(1.02, (Y_MAX - by) / max(1, rows))
    for idx, it in enumerate(items):
        cv.group()
        c = idx // rows if two else 0
        r = idx % rows if two else idx
        x = X0 + c * (cw + 0.55)
        y = by + r * rh
        cv.line(x, y, x + cw, y, cv.c['line'], width=0.75)
        cv.text(x, y + 0.12, 0.62, rh - 0.16, f'{idx + 1:02d}', 18, color=cv.c['accent_strong'], bold=True, font='display', check=False)
        has_det = bool(it.get('detail'))
        cv.text(x + 0.68, y + 0.12, cw - 0.72, (0.36 if has_det else rh - 0.20), it.get('title', ''), 14.5, bold=True, min_size=11.5)
        if has_det:
            cv.text(x + 0.68, y + 0.48, cw - 0.72, max(0.28, rh - 0.52), it['detail'], 11.5, color=cv.c['muted'], min_size=9.5)


def section(cv: Canvas, s: dict, ctx: dict):
    num = s.get('section_number')
    cv.group()
    if num and len(str(num)) <= 3:
        cv.text(8.6, 1.5, 3.85, 3.4, str(num), 120, color=mix(cv.c['bg'], cv.c['ink'], 0.12), bold=True, font='display', align='r', check=False)
    eb = s.get('eyebrow') or (str(num) if num and len(str(num)) > 3 else None)
    _eyebrow(cv, eb, X0, 2.05, w=9.5)
    sz, lines, _ = fit_size(s.get('title', ''), cv.f['display'], 44, 26, 9.8, 2.1, bold=True, spacing=1.04, max_lines=3)
    th = max(0.85, lines * sz * 1.08 / 72 + 0.08)
    cv.text(X0, 2.45, 9.8, th, s.get('title', ''), sz, bold=True, font='display', min_size=26, spacing=1.04)
    cy = 2.45 + th + 0.14
    if s.get('subtitle'):
        cv.text(X0, cy, 8.8, 0.75, s['subtitle'], 15.5, color=cv.c['muted'], min_size=12)
        cy += 0.78
    if s.get('chips'):
        cv.group()
        cx = X0
        for ch in s['chips'][:5]:
            tw = min(3.2, max(1.0, len(str(ch)) * 0.095 + 0.36))
            if cx + tw > X0 + W_IN:
                break
            cv.rect(cx, cy + 0.1, tw, 0.34, fill=cv.c['surface'], line=cv.c['line'], radius=0.17)
            cv.text(cx + 0.14, cy + 0.1, tw - 0.28, 0.34, str(ch), 10.5, color=cv.c['ink'], bold=True, align='c', anchor='m', check=False)
            cx += tw + 0.14


def statement(cv: Canvas, s: dict, ctx: dict):
    cv.group()
    cy = 1.65
    if s.get('eyebrow'):
        cy = _eyebrow(cv, s['eyebrow'], X0, cy, w=9.5) + 0.06
    cv.rect(X0, cy, 0.72, 0.055, fill=cv.c['accent_strong'])
    cy += 0.26
    txt = s.get('title', '')
    base_pt = 28 if len(plain(txt)) > 85 else 36
    sz, lines, _ = fit_size(txt, cv.f['display'], base_pt, 20, 10.6, 2.65, bold=True, spacing=1.12, max_lines=4)
    th = max(0.95, lines * sz * 1.15 / 72 + 0.08)
    cv.text(X0, cy, 10.6, th, txt, sz, bold=True, font='display', min_size=20, spacing=1.12)
    cy += th + 0.18
    if s.get('subtitle'):
        cv.text(X0, cy, 9.6, 0.75, s['subtitle'], 15.0, color=cv.c['muted'], min_size=12)
        cy += 0.75
    if s.get('note'):
        cv.text(X0, min(6.15, cy + 0.1), 9.6, 0.38, s['note'], 11.0, color=cv.c['subtle'], min_size=9.5)


def metrics(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    items = s.get('items') or []
    n = max(1, len(items))
    gap = 0.26
    cw = (W_IN - gap * (n - 1)) / n
    ch = min(3.55, Y_MAX - by)
    cy = by + (Y_MAX - by - ch) * 0.35
    for i, it in enumerate(items):
        cv.group()
        x = X0 + i * (cw + gap)
        _card(cv, x, cy, cw, ch)
        ncol = _pal(cv, i) if (cv.t['icons']['style'] == 'color-circle' or cv.t['id'] == 'editorial-warm') else cv.c['accent_strong']
        cv.text(x + 0.28, cy + 0.30, cw - 0.56, 1.05, str(it.get('value', '')), 42 if n <= 3 else 34,
                color=ncol, bold=True, font='display', min_size=22, max_lines=1)
        cv.text(x + 0.28, cy + 1.42, cw - 0.56, 0.62, str(it.get('label', '')), 14.0, bold=True, min_size=11)
        det = it.get('detail') or it.get('body')
        if det:
            cv.text(x + 0.28, cy + 2.10, cw - 0.56, ch - 2.32, str(det), 11.5, color=cv.c['muted'], min_size=9.5)


def kpi_dashboard(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx, w=W_IN - (1.5 if s.get('period') else 0))
    if s.get('period'):
        cv.rect(X0 + W_IN - 1.35, Y_TOP, 1.35, 0.32, fill=cv.c['surface_alt'], line=cv.c['line'], radius=0.16)
        cv.text(X0 + W_IN - 1.35, Y_TOP, 1.35, 0.32, str(s['period']), 9.5, color=cv.c['ink'], bold=True, align='c', anchor='m', check=False)
    items = s.get('items') or []
    n = max(1, len(items))
    cols = n if n <= 4 else 3
    rows = math.ceil(n / cols)
    gx, gy = 0.24, 0.22
    cw = (W_IN - gx * (cols - 1)) / cols
    ch = (Y_MAX - by - gy * (rows - 1)) / rows
    for idx, it in enumerate(items):
        cv.group()
        r, c = divmod(idx, cols)
        x, y = X0 + c * (cw + gx), by + r * (ch + gy)
        _card(cv, x, y, cw, ch)
        cv.text(x + 0.24, y + 0.18, cw - 0.48, 0.24, str(it.get('label', '')), 9.5, color=cv.c['muted'], bold=True, caps=True, tracking=70, check=False)
        status = it.get('status', 'flat')
        cls = {'up': 'good', 'good': 'good', 'down': 'bad', 'bad': 'bad'}.get(status, 'flat')
        if status == 'down' and it.get('down_is_good'):
            cls = 'good'
        scol = cv.c['positive'] if cls == 'good' else (cv.c['negative'] if cls == 'bad' else cv.c['muted'])
        val_w = (cw - 0.48) * (0.62 if it.get('delta') else 1.0)
        cv.text(x + 0.24, y + 0.44, val_w, 0.66, str(it.get('value', '')), 28 if rows > 1 else 32, bold=True, font='display', min_size=18, max_lines=1)
        if it.get('delta'):
            arrow = it.get('arrow') or {'good': '▲', 'bad': '▼', 'flat': '•'}[cls]
            dtxt = f"{arrow} {it['delta']}"
            dw = min(1.35, max(0.78, len(dtxt) * 0.082 + 0.22))
            dx = x + cw - 0.24 - dw
            cv.rect(dx, y + 0.56, dw, 0.28, fill=mix(cv.c['surface'], scol, 0.15), radius=0.14)
            cv.text(dx + 0.08, y + 0.56, dw - 0.16, 0.28, dtxt, 9.0, color=scol, bold=True, align='c', anchor='m', check=False)
        has_spark = bool(it.get('trend') and len(it['trend']) >= 2)
        det = it.get('detail') or (f"{L(ctx['deck'], 'target')}: {it['target']}" if it.get('target') else '')
        if has_spark:
            sy = y + 1.18
            sh = max(0.28, ch - (1.72 if det else 1.40))
            draw_sparkline(cv, it['trend'], x + 0.26, sy, cw - 0.52, min(0.46, sh), scol if cls != 'flat' else cv.c['accent_strong'])
        if det:
            cv.text(x + 0.24, y + ch - 0.42, cw - 0.48, 0.30, str(det), 10.0, color=cv.c['muted'], min_size=8.5)


def cards(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    items = [it if isinstance(it, dict) else {'title': str(it)} for it in (s.get('items') or [])]
    n = max(1, len(items))
    style = s.get('style') or ('panels' if cv.t['cards']['style'] in ('paper', 'tint', 'glass-dark') or any(it.get('icon') for it in items) else 'columns')
    cols = n if n <= 4 else 3
    rows = math.ceil(n / cols)
    gx, gy = 0.26, 0.24
    cw = (W_IN - gx * (cols - 1)) / cols
    ch = min(3.9, (Y_MAX - by - gy * (rows - 1)) / rows)
    for idx, it in enumerate(items):
        cv.group()
        r, c = divmod(idx, cols)
        x, y = X0 + c * (cw + gx), by + r * (ch + gy)
        if style == 'columns':
            cv.line(x, y, x + cw, y, cv.c['line'], width=1.0)
            pad = 0.06
        else:
            _card(cv, x, y, cw, ch, hl=bool(it.get('highlight')))
            pad = 0.26
        hy = y + (0.20 if style == 'columns' else 0.24)
        if it.get('icon'):
            cv.icon(it['icon'], x + pad, hy, 0.44, bg=_pal(cv, idx), fg_png_dir=ctx['icons_png'], num=idx + 1)
            hy += 0.56
        else:
            cv.text(x + pad, hy, 0.8, 0.34, f'{idx + 1:02d}', 16, color=cv.c['accent_strong'], bold=True, font='display', check=False)
            hy += 0.40
        cv.text(x + pad, hy, cw - 2 * pad, 0.56, it.get('title', ''), 15.0, bold=True, min_size=12, max_lines=2)
        body = it.get('body') or it.get('detail') or ''
        if body:
            cv.text(x + pad, hy + 0.60, cw - 2 * pad, max(0.4, y + ch - (hy + 0.60) - 0.18), body, 12.0, color=cv.c['muted'], min_size=9.5, spacing=1.18)


def process(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    steps = [st if isinstance(st, dict) else {'title': str(st)} for st in (s.get('steps') or s.get('items') or [])]
    n = max(1, len(steps))
    cw = W_IN / n
    rail_y = by + 0.52
    if n > 1:
        cv.line(X0 + 0.30, rail_y, X0 + W_IN - cw + 0.30, rail_y, cv.c['line'], width=1.5)
    for i, st in enumerate(steps):
        cv.group()
        x = X0 + i * cw
        cv.icon(st.get('icon', ''), x, rail_y - 0.26, 0.52, bg=_pal(cv, i) if i == 0 else cv.c['accent_strong'], fg_png_dir=ctx['icons_png'], num=f'{i + 1:02d}')
        cv.text(x, rail_y + 0.42, cw - 0.22, 0.58, st.get('title', ''), 14.5, bold=True, min_size=11.5, max_lines=2)
        det = st.get('detail') or st.get('body') or ''
        if det:
            cv.text(x, rail_y + 1.04, cw - 0.22, max(0.5, Y_MAX - (rail_y + 1.04)), det, 11.5, color=cv.c['muted'], min_size=9.5, spacing=1.18)


def timeline(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    items = s.get('items') or []
    n = max(1, len(items))
    cw = W_IN / n
    ay = by + 0.55
    cv.line(X0, ay, X0 + W_IN, ay, cv.c['line'], width=1.5)
    for i, it in enumerate(items):
        cv.group()
        x = X0 + i * cw
        state = it.get('state', 'done')
        if state == 'now':
            cv.oval(x, ay - 0.11, 0.22, 0.22, fill=cv.c['accent_strong'])
        elif state == 'next':
            cv.oval(x, ay - 0.09, 0.18, 0.18, fill=cv.c['bg'], line=cv.c['muted'], line_w=1.8)
        else:
            cv.oval(x, ay - 0.09, 0.18, 0.18, fill=cv.c['accent'])
        dstr = str(it.get('date', ''))
        if state == 'now':
            nw = min(1.05, cw - 0.24)
            dx = x + min(cw - nw - 0.16, max(0.82, len(dstr) * 0.115 + 0.18))
            cv.text(x, ay + 0.22, max(0.55, dx - x - 0.06), 0.30, dstr, 12.5, color=cv.c['accent_strong'], bold=True, check=False)
            cv.rect(dx, ay + 0.21, nw, 0.24, fill=cv.c['accent_soft'], radius=0.12)
            cv.text(dx, ay + 0.21, nw, 0.24, L(ctx['deck'], 'now'), 8.0, color=cv.c['accent_strong'], bold=True, caps=True, align='c', anchor='m', check=False)
        else:
            cv.text(x, ay + 0.22, cw - 0.20, 0.30, dstr, 12.5, color=cv.c['accent_strong'], bold=True, check=False)
        cv.text(x, ay + 0.58, cw - 0.22, 0.56, it.get('title', ''), 14.5, bold=True, min_size=11.5, max_lines=2)
        det = it.get('detail') or it.get('body') or ''
        if det:
            cv.text(x, ay + 1.18, cw - 0.22, max(0.5, Y_MAX - (ay + 1.18)), det, 11.5, color=cv.c['muted'], min_size=9.5, spacing=1.18)


def comparison(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    hl = s.get('highlight')
    has_v = bool(s.get('verdict'))
    ch = (Y_MAX - by) - (0.68 if has_v else 0.0)
    cw = (W_IN - 0.34) / 2
    for idx, key in enumerate(('left', 'right')):
        cv.group()
        side = s.get(key) or {}
        x = X0 + idx * (cw + 0.34)
        is_hl = hl == key
        _card(cv, x, by, cw, ch, hl=is_hl)
        tag = side.get('tag')
        tw = min(1.45, len(str(tag)) * 0.09 + 0.30) if tag else 0
        cv.text(x + 0.28, by + 0.24, cw - 0.56 - tw, 0.44, side.get('title', ''), 16.5, bold=True, min_size=13)
        if tag:
            cv.rect(x + cw - 0.28 - tw, by + 0.24, tw, 0.28, fill=cv.c['accent_soft'], radius=0.14)
            cv.text(x + cw - 0.28 - tw, by + 0.24, tw, 0.28, str(tag), 8.5, color=cv.c['accent_strong'], bold=True, caps=True, align='c', anchor='m', check=False)
        tone = side.get('tone', 'neutral' if not hl else ('positive' if is_hl else 'neutral'))
        _bullet_list(cv, side.get('bullets') or [], x + 0.28, by + 0.80, cw - 0.56, ch - 1.00, tone=tone)
    if has_v:
        cv.group()
        vy = by + ch + 0.16
        cv.rect(X0, vy, W_IN, 0.50, fill=cv.c['accent_soft'], radius=0.14)
        cv.icon('lightbulb', X0 + 0.14, vy + 0.08, 0.34, bg=cv.c['accent_strong'], fg_png_dir=ctx['icons_png'])
        cv.text(X0 + 0.58, vy + 0.06, W_IN - 0.74, 0.38, s['verdict'], 12.0, bold=True, anchor='m', min_size=10)


def problem_solution(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    ch = Y_MAX - by
    cw = (W_IN - 0.72) / 2
    p, so = s.get('problem') or {}, s.get('solution') or {}
    # Problem card
    cv.group()
    _card(cv, X0, by, cw, ch, hl=False)
    cv.icon('circle-question-mark', X0 + 0.28, by + 0.24, 0.40, bg=cv.c['negative'], fg_png_dir=ctx['icons_png'], num='?')
    cv.text(X0 + 0.78, by + 0.26, cw - 1.06, 0.40, p.get('title') or L(ctx['deck'], 'problem'), 16.5, bold=True, min_size=13)
    _bullet_list(cv, p.get('points') or p.get('bullets') or [], X0 + 0.28, by + 0.84, cw - 0.56, ch - 1.04, tone='negative')
    # Arrow badge
    cx = X0 + cw + 0.36
    cy = by + ch / 2
    cv.icon('arrow-right', cx - 0.23, cy - 0.23, 0.46, bg=cv.c['accent_strong'], fg_png_dir=ctx['icons_png'], num='→')
    # Solution card
    rx = X0 + cw + 0.72
    cv.group()
    _card(cv, rx, by, cw, ch, hl=True)
    cv.icon('lightbulb', rx + 0.28, by + 0.24, 0.40, bg=cv.c['accent_strong'], fg_png_dir=ctx['icons_png'], num='!')
    cv.text(rx + 0.78, by + 0.26, cw - 1.06, 0.40, so.get('title') or L(ctx['deck'], 'solution'), 16.5, bold=True, min_size=13)
    _bullet_list(cv, so.get('points') or so.get('bullets') or [], rx + 0.28, by + 0.84, cw - 0.56, ch - 1.04, tone='positive')


def _set_cell_border(cell, bottom_hex: str, width_pt: float = 0.75):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ('a:lnL', 'a:lnR', 'a:lnT', 'a:lnB'):
        for old in tcPr.findall(qn(tag)):
            tcPr.remove(old)
    for tag in ('a:lnL', 'a:lnR', 'a:lnT'):
        ln = etree.SubElement(tcPr, qn(tag))
        ln.set('w', '12700')
        etree.SubElement(ln, qn('a:noFill'))
    lnB = etree.SubElement(tcPr, qn('a:lnB'))
    lnB.set('w', str(int(width_pt * 12700)))
    lnB.set('cmpd', 'sng')
    sf = etree.SubElement(lnB, qn('a:solidFill'))
    clr = etree.SubElement(sf, qn('a:srgbClr'))
    clr.set('val', bottom_hex.lstrip('#')[:6].upper())


def table(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    cols = s.get('columns') or []
    rows = s.get('rows') or []
    if not cols:
        return
    hl = s.get('highlight')
    hli = cols.index(hl) if isinstance(hl, str) and hl in cols else (hl if isinstance(hl, int) else None)
    has_note = bool(s.get('note'))
    avail_h = (Y_MAX - by) - (0.38 if has_note else 0.0)
    nr, nc = len(rows) + 1, len(cols)
    th = min(avail_h, max(1.6, 0.54 + len(rows) * 0.62))
    cv.group()
    gf = cv._track(cv.s.shapes.add_table(nr, nc, Inches(X0), Inches(by), Inches(W_IN), Inches(th)))
    tbl = gf.table
    # Strip default PowerPoint blue table style so theme colors apply cleanly
    tblPr = tbl._tbl.find(qn('a:tblPr'))
    if tblPr is not None:
        for st in tblPr.findall(qn('a:tableStyleId')):
            tblPr.remove(st)
        tblPr.set('firstRow', '0')
        tblPr.set('bandRow', '0')
    cw = W_IN / nc
    for j in range(nc):
        tbl.columns[j].width = Inches(cw)
    for i in range(nr):
        tbl.rows[i].height = Inches(0.48 if i == 0 else (th - 0.48) / max(1, nr - 1))
        for j in range(nc):
            cell = tbl.cell(i, j)
            is_hl = j == hli
            cell.fill.solid()
            if i == 0:
                cell.fill.fore_color.rgb = rgb(cv.c['accent_soft'] if is_hl else cv.c['surface_alt'])
                _set_cell_border(cell, cv.c['ink'] if not cv.dark else cv.c['accent'], 1.4)
            else:
                cell.fill.fore_color.rgb = rgb(mix(cv.c['surface'], cv.c['accent_soft'], 0.32) if is_hl else cv.c['surface'])
                _set_cell_border(cell, cv.c['line'], 0.65)
            cell.margin_left = cell.margin_right = Inches(0.16)
            cell.margin_top = cell.margin_bottom = Inches(0.08)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            txt = str(cols[j] if i == 0 else (rows[i - 1][j] if j < len(rows[i - 1]) else ''))
            if i == 0:
                r = p.add_run()
                r.text = txt.upper()
                r.font.name = cv.f['body']
                r.font.size = Pt(9.5)
                r.font.bold = True
                r.font.color.rgb = rgb(cv.c['accent_strong'] if is_hl else cv.c['muted'])
            else:
                for seg, b in split_runs(txt):
                    r = p.add_run()
                    r.text = seg
                    r.font.name = cv.f['body']
                    r.font.size = Pt(11.5)
                    r.font.bold = b or (j == 0) or is_hl
                    r.font.color.rgb = rgb(cv.c['accent_strong'] if b else cv.c['ink'])
    if has_note:
        cv.text(X0, by + th + 0.10, W_IN, 0.28, s['note'], 10.0, color=cv.c['subtle'], min_size=8.5)


def chart(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    spec = dict(s.get('chart') or {})
    ins = s.get('insights') or []
    has_cap = bool(s.get('caption'))
    cw = 7.35 if ins else W_IN
    ch = (Y_MAX - by) - (0.34 if has_cap else 0.0)
    cv.group()
    add_native_chart(cv, spec, X0, by, cw, ch, lang=ctx['lang'])
    if has_cap:
        cv.text(X0, by + ch + 0.06, cw, 0.28, s['caption'], 9.5, color=cv.c['subtle'], min_size=8.5)
    if ins:
        ix = X0 + cw + 0.36
        iw = W_IN - cw - 0.36
        ih = min(1.18, (Y_MAX - by - 0.16 * max(0, len(ins) - 1)) / max(1, len(ins)))
        for idx, item in enumerate(ins[:4]):
            cv.group()
            iy = by + idx * (ih + 0.16)
            _card(cv, ix, iy, iw, ih)
            cv.text(ix + 0.20, iy + 0.16, 0.45, 0.34, f'{idx + 1:02d}', 15, color=cv.c['accent_strong'], bold=True, font='display', check=False)
            cv.text(ix + 0.68, iy + 0.16, iw - 0.88, ih - 0.30, str(item), 12.0, min_size=9.5, spacing=1.16)


def case(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    cy = by + 0.35
    cv.group()
    cv.text(X0, cy, 4.7, 1.55, str(s.get('value', '')), 66, color=cv.c['accent_strong'], bold=True, font='display', min_size=36, max_lines=1)
    if s.get('value_label'):
        cv.text(X0, cy + 1.60, 4.7, 0.65, s['value_label'], 14.0, color=cv.c['muted'], bold=True, min_size=11)
    if s.get('body'):
        cv.group()
        _card(cv, X0 + 5.05, by + 0.15, W_IN - 5.05, Y_MAX - by - 0.25)
        cv.text(X0 + 5.38, by + 0.45, W_IN - 5.70, Y_MAX - by - 0.85, s['body'], 15.0, min_size=11.5, spacing=1.26)


def evidence_levels(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    levels = [lv if isinstance(lv, dict) else {'label': str(lv)} for lv in (s.get('levels') or [])]
    n = max(1, len(levels))
    has_note = bool(s.get('note'))
    avail_h = (Y_MAX - by) - (0.36 if has_note else 0.0)
    rh = min(0.86, (avail_h - 0.14 * max(0, n - 1)) / n)
    bar_max = 5.15
    for i, lv in enumerate(levels):
        cv.group()
        y = by + i * (rh + 0.14)
        t = i / max(1, n - 1)
        col = mix(cv.c['accent_strong'], cv.c['subtle'], t * 0.75)
        dark_txt = cv.c['bg'] if cv.dark else cv.c['ink']
        txt = '#FFFFFF' if contrast('#FFFFFF', col) >= contrast(dark_txt, col) else dark_txt
        bw = bar_max * (1.0 - i * (0.38 / max(1, n - 1)))
        cv.rect(X0, y, bw, rh, fill=col, radius=0.10)
        cv.text(X0 + 0.20, y, bw - 0.36, rh, f"{i + 1}   {lv.get('label', '')}", 12.5, color=txt, bold=True, anchor='m', min_size=9.5)
        if lv.get('detail'):
            cv.text(X0 + bar_max + 0.32, y, W_IN - bar_max - 0.32, rh, lv['detail'], 12.0, color=cv.c['muted'], anchor='m', min_size=9.5)
    if has_note:
        cv.text(X0, Y_MAX - 0.28, W_IN, 0.26, s['note'], 10.0, color=cv.c['subtle'], min_size=8.5)


def methodology(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    facts = s.get('facts') or []
    steps = s.get('steps') or []
    sx = X0
    sw = W_IN
    if facts:
        fw = 3.55
        fh = min(1.18, (Y_MAX - by - 0.16 * max(0, len(facts) - 1)) / max(1, len(facts)))
        for i, f in enumerate(facts[:4]):
            cv.group()
            fy = by + i * (fh + 0.16)
            _card(cv, X0, fy, fw, fh)
            cv.text(X0 + 0.24, fy + 0.14, fw - 0.48, 0.56, str(f.get('value', '')), 26, color=cv.c['accent_strong'], bold=True, font='display', min_size=18, max_lines=1)
            cv.text(X0 + 0.24, fy + 0.70, fw - 0.48, fh - 0.78, str(f.get('label', '')), 11.0, color=cv.c['muted'], min_size=9.5)
        sx = X0 + fw + 0.52
        sw = W_IN - fw - 0.52
    if steps:
        ns = len(steps)
        sh = min(1.10, (Y_MAX - by) / ns)
        if ns > 1:
            cv.line(sx + 0.22, by + 0.22, sx + 0.22, by + (ns - 1) * sh + 0.22, cv.c['line'], width=1.4)
        for i, st in enumerate(steps):
            cv.group()
            y = by + i * sh
            cv.oval(sx, y + 0.04, 0.44, 0.44, fill=cv.c['surface'], line=cv.c['accent_strong'], line_w=1.6)
            cv.text(sx, y + 0.04, 0.44, 0.44, f'{i + 1:02d}', 10.5, color=cv.c['accent_strong'], bold=True, align='c', anchor='m', check=False)
            cv.text(sx + 0.62, y + 0.02, sw - 0.62, 0.34, st.get('title', ''), 14.0, bold=True, min_size=11.5)
            if st.get('detail'):
                cv.text(sx + 0.62, y + 0.36, sw - 0.62, max(0.30, sh - 0.42), st['detail'], 11.5, color=cv.c['muted'], min_size=9.5)


def diagram(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    nodes = [nd if isinstance(nd, dict) else {'title': str(nd)} for nd in (s.get('nodes') or [])]
    n = max(1, len(nodes))
    variant = s.get('variant', 'hub' if s.get('center') else 'cycle')
    cx, cy = W / 2, by + (Y_MAX - by) / 2
    if variant == 'cycle':
        R = min(1.55, (Y_MAX - by) * 0.36)
        cv.oval(cx - R, cy - R, 2 * R, 2 * R, line=cv.c['line'], line_w=1.2, dash=True)
        ang = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
        pos = [(cx + R * math.cos(a), cy + R * math.sin(a)) for a in ang]
        nr = 0.34
        for i in range(n):
            x0, y0 = pos[i]
            x1, y1 = pos[(i + 1) % n]
            dx, dy = x1 - x0, y1 - y0
            dist = math.hypot(dx, dy) or 1.0
            ux, uy = dx / dist, dy / dist
            if dist > 2 * nr + 0.16:
                cv.line(x0 + ux * (nr + 0.07), y0 + uy * (nr + 0.07), x1 - ux * (nr + 0.09), y1 - uy * (nr + 0.09),
                        cv.c['accent_strong'], width=1.8, arrow=True)
        if s.get('center'):
            cv.group()
            cv.rect(cx - 0.95, cy - 0.34, 1.90, 0.68, fill=cv.c['surface'], line=cv.c['line'], radius=0.14)
            cv.text(cx - 0.88, cy - 0.30, 1.76, 0.60, str(s['center']), 11.5, bold=True, align='c', anchor='m', min_size=9.5)
        for i, (nd, (px, py), a) in enumerate(zip(nodes, pos, ang)):
            cv.group()
            cv.icon(nd.get('icon', ''), px - nr, py - nr, 2 * nr, bg=_pal(cv, i), fg_png_dir=ctx['icons_png'], num=i + 1)
            c, sn = math.cos(a), math.sin(a)
            lw = 2.75
            if abs(c) <= 0.32:
                lx = px + nr + 0.18
                ly = (py - 0.56) if sn < 0 else (py - 0.14)
                align = 'l'
            elif c < 0:
                lx = px - nr - 0.18 - lw
                ly = py - 0.34
                align = 'r'
            else:
                lx = px + nr + 0.18
                ly = py - 0.34
                align = 'l'
            cv.text(lx, ly, lw, 0.32, nd.get('title', ''), 13.0, bold=True, align=align, min_size=10.5)
            if nd.get('detail'):
                cv.text(lx, ly + 0.32, lw, 0.44, nd['detail'], 10.5, color=cv.c['muted'], align=align, min_size=9.0)
        return

    # Hub & spoke
    rx, ry = 3.85, min(1.58, (Y_MAX - by) * 0.35)
    pos = [(cx + rx * math.cos(-math.pi / 2 + 2 * math.pi * i / n), cy + ry * math.sin(-math.pi / 2 + 2 * math.pi * i / n)) for i in range(n)]
    for px, py in pos:
        cv.line(cx, cy, px, py, cv.c['line'], width=1.4)
    cv.group()
    cr = 0.86
    cv.oval(cx - cr, cy - cr, 2 * cr, 2 * cr, fill=cv.c['accent_strong'])
    cv.text(cx - cr + 0.12, cy - cr + 0.12, 2 * cr - 0.24, 2 * cr - 0.24, str(s.get('center', '')), 13.5,
            color='#FFFFFF', bold=True, align='c', anchor='m', min_size=10)
    nw, nh = 2.85, 0.96
    for i, (nd, (px, py)) in enumerate(zip(nodes, pos)):
        cv.group()
        nx, ny = px - nw / 2, py - nh / 2
        _card(cv, nx, ny, nw, nh)
        cv.icon(nd.get('icon', ''), nx + 0.16, ny + (nh - 0.40) / 2, 0.40, bg=_pal(cv, i), fg_png_dir=ctx['icons_png'], num=i + 1)
        has_d = bool(nd.get('detail'))
        cv.text(nx + 0.66, ny + (0.14 if has_d else 0.28), nw - 0.80, 0.32, nd.get('title', ''), 12.5, bold=True, min_size=10)
        if has_d:
            cv.text(nx + 0.66, ny + 0.46, nw - 0.80, 0.40, nd['detail'], 10.0, color=cv.c['muted'], min_size=8.5)


def learning_objectives(cv: Canvas, s: dict, ctx: dict):
    s2 = dict(s)
    if not s2.get('subtitle'):
        s2['subtitle'] = s.get('lead') or L(ctx['deck'], 'objectives_lead')
    by = header(cv, s2, ctx)
    items = s.get('items') or []
    n = max(1, len(items))
    two = n > 3
    cols = 2 if two else 1
    rows = math.ceil(n / cols)
    gx, gy = 0.34, 0.22
    cw = (W_IN - (gx if two else 0)) / cols
    rh = min(1.06, (Y_MAX - by - gy * max(0, rows - 1)) / rows)
    for i, it in enumerate(items):
        cv.group()
        r = i % rows if two else i
        c = i // rows if two else 0
        x, y = X0 + c * (cw + gx), by + r * (rh + gy)
        _card(cv, x, y, cw, rh)
        txt = it if isinstance(it, str) else it.get('text', '')
        icon = None if isinstance(it, str) else it.get('icon')
        if '**' not in txt:
            parts = plain(txt).split(' ', 1)
            txt = f"**{parts[0]}** {parts[1]}" if len(parts) > 1 else f"**{parts[0]}**"
        cv.icon(icon or 'circle-check', x + 0.22, y + (rh - 0.42) / 2, 0.42, bg=_pal(cv, i), fg_png_dir=ctx['icons_png'], num=i + 1)
        cv.text(x + 0.78, y + 0.14, cw - 0.98, rh - 0.28, txt, 13.0, anchor='m', min_size=10.5, spacing=1.18)


def definition(cv: Canvas, s: dict, ctx: dict):
    cv.group()
    cy = _eyebrow(cv, s.get('eyebrow') or s.get('title'), X0, 1.35, w=5.6) + 0.10
    term = s.get('term', '')
    sz, lines, _ = fit_size(term, cv.f['display'], 46 if len(plain(term)) <= 12 else 36, 24, 5.6, 1.65, bold=True, spacing=1.04, max_lines=2)
    th = max(0.75, lines * sz * 1.08 / 72 + 0.06)
    cv.text(X0, cy, 5.6, th, term, sz, color=cv.c['accent_strong'], bold=True, font='display', min_size=24)
    cy += th + 0.08
    if s.get('pronunciation'):
        cv.text(X0, cy, 5.6, 0.30, s['pronunciation'], 11.5, color=cv.c['muted'], font='mono', check=False)
        cy += 0.36
    if s.get('definition'):
        cv.text(X0, cy + 0.06, 5.6, max(0.8, 6.35 - cy), s['definition'], 14.5, min_size=11.5, spacing=1.24)
    rx, rw = X0 + 6.10, W_IN - 6.10
    ry = 1.85
    if s.get('example'):
        cv.group()
        _card(cv, rx, ry, rw, 2.35)
        cv.text(rx + 0.28, ry + 0.22, rw - 0.56, 0.24, L(ctx['deck'], 'example'), 9.5, color=cv.c['accent_strong'], bold=True, caps=True, tracking=90, check=False)
        cv.text(rx + 0.28, ry + 0.54, rw - 0.56, 1.58, s['example'], 13.5, min_size=10.5, spacing=1.22)
        ry += 2.58
    if s.get('note'):
        cv.group()
        cv.icon('info', rx, ry + 0.04, 0.32, bg=cv.c['subtle'], fg_png_dir=ctx['icons_png'], num='i')
        cv.text(rx + 0.44, ry, rw - 0.44, 0.95, s['note'], 11.0, color=cv.c['muted'], min_size=9.5, spacing=1.20)


def image_split(cv: Canvas, s: dict, ctx: dict):
    left_media = s.get('side') == 'left'
    mx = 0.0 if left_media else 7.05
    mw = 6.28
    tx = 6.72 if left_media else X0
    tw = 5.72
    cv.group()
    p = ctx['img_path'](s.get('image', ''))
    if p and p.is_file():
        cv.picture(p, mx, 0.0, mw, H)
    else:
        cv.rect(mx, 0.0, mw, H, fill=cv.c['surface_alt'])
    if s.get('image_credit'):
        cw = min(3.4, len(str(s['image_credit'])) * 0.075 + 0.30)
        cx = (mx + 0.30) if left_media else (mx + mw - cw - 0.30)
        cv.rect(cx, 6.42, cw, 0.28, fill='#000000', radius=0.14, alpha=0.55)
        cv.text(cx + 0.12, 6.42, cw - 0.24, 0.28, str(s['image_credit']), 8.5, color='#FFFFFF', align='c', anchor='m', check=False)
    by = header(cv, s, ctx, x=tx, y=0.92, w=tw, title_pt=30, min_pt=20)
    if s.get('bullets'):
        cv.group()
        _bullet_list(cv, s['bullets'], tx, by + 0.10, tw, Y_MAX - by - 0.15, tone='neutral', font_pt=13.0)


def full_bleed_image(cv: Canvas, s: dict, ctx: dict):
    p = ctx['img_path'](s.get('image', ''))
    if p and p.is_file():
        cv.picture(p, 0.0, 0.0, W, H)
    else:
        cv.rect(0.0, 0.0, W, H, fill='#141821')
    # Dark scrim over bottom half so white text and footer stay high-contrast
    cv.rect(0.0, 3.35, W, H - 3.35, fill='#0B0E14', alpha=0.72)
    cv.group()
    cy = 4.05
    if s.get('eyebrow'):
        cv.text(X0, cy, 9.5, 0.24, str(s['eyebrow']), 9.5, color='#FFFFFF', bold=True, caps=True, tracking=120, check=False)
        cy += 0.30
    sz, lines, _ = fit_size(s.get('title', ''), cv.f['display'], 40, 24, 10.4, 1.55, bold=True, spacing=1.05, max_lines=2)
    th = max(0.75, lines * sz * 1.08 / 72 + 0.06)
    cv.text(X0, cy, 10.4, th, s.get('title', ''), sz, color='#FFFFFF', bold=True, font='display', min_size=24, accent_bold=False)
    cy += th + 0.08
    if s.get('subtitle'):
        cv.text(X0, cy, 9.4, 0.65, s['subtitle'], 14.5, color='#E5E7EB', min_size=11.5, accent_bold=False)
    if s.get('image_credit'):
        cv.text(W - 4.2, 0.36, 3.32, 0.26, str(s['image_credit']), 8.5, color='#E5E7EB', align='r', check=False)


def quote(cv: Canvas, s: dict, ctx: dict):
    cv.group()
    cy = 1.25
    eb = s.get('title') or s.get('eyebrow')
    if eb:
        cy = _eyebrow(cv, eb, X0, cy, w=9.5) + 0.10
    cv.text(X0, cy - 0.12, 1.0, 0.68, '“', 60, color=cv.c['accent_strong'], bold=True, font='display', check=False)
    cy += 0.64
    q = s.get('quote', '')
    sz, lines, _ = fit_size(q, cv.f['display'], 28, 18, 10.4, 2.75, spacing=1.18, max_lines=5)
    qh = max(1.0, lines * sz * 1.22 / 72 + 0.08)
    cv.text(X0, cy, 10.4, qh, q, sz, font='display', italic=True, min_size=18, spacing=1.18)
    if s.get('attribution'):
        cv.text(X0, cy + qh + 0.22, 9.0, 0.40, f"— {s['attribution']}", 13.0, color=cv.c['muted'], bold=True, min_size=10.5)


def key_takeaways(cv: Canvas, s: dict, ctx: dict):
    by = header(cv, s, ctx)
    bullets = s.get('bullets') or []
    n = max(1, len(bullets))
    rh = min(0.96, (Y_MAX - by - 0.14 * max(0, n - 1)) / n)
    for i, b in enumerate(bullets):
        cv.group()
        y = by + i * (rh + 0.14)
        _card(cv, X0, y, W_IN, rh)
        cv.text(X0 + 0.26, y, 0.60, rh, f'{i + 1:02d}', 20, color=cv.c['accent_strong'], bold=True, font='display', anchor='m', check=False)
        cv.text(X0 + 0.94, y + 0.10, W_IN - 1.20, rh - 0.20, str(b), 13.5, anchor='m', min_size=10.5, spacing=1.18)


def references(cv: Canvas, s: dict, ctx: dict):
    s2 = dict(s)
    s2.setdefault('title', L(ctx['deck'], 'references'))
    by = header(cv, s2, ctx)
    items = s.get('items') or []
    n = max(1, len(items))
    two = n > 5
    cols = 2 if two else 1
    rows = math.ceil(n / cols)
    cw = (W_IN - (0.48 if two else 0)) / cols
    rh = min(0.68, (Y_MAX - by) / max(1, rows))
    for i, it in enumerate(items):
        cv.group()
        r = i % rows if two else i
        c = i // rows if two else 0
        x, y = X0 + c * (cw + 0.48), by + r * rh
        cv.line(x, y + rh - 0.04, x + cw, y + rh - 0.04, cv.c['line'], width=0.5)
        cv.text(x, y + 0.06, 0.44, rh - 0.12, f'[{i + 1}]', 10.5, color=cv.c['accent_strong'], bold=True, font='mono', check=False)
        cv.text(x + 0.48, y + 0.06, cw - 0.52, rh - 0.12, str(it), 10.5, color=cv.c['ink'], min_size=8.5, spacing=1.16)


def closing(cv: Canvas, s: dict, ctx: dict):
    cv.group()
    _eyebrow(cv, s.get('eyebrow'), X0, 1.75, w=9.5)
    sz, lines, _ = fit_size(s.get('title', ''), cv.f['display'], 46, 26, 10.2, 2.15, bold=True, spacing=1.04, max_lines=3)
    th = max(0.90, lines * sz * 1.08 / 72 + 0.08)
    cv.text(X0, 2.20, 10.2, th, s.get('title', ''), sz, bold=True, font='display', min_size=26, spacing=1.04)
    if s.get('subtitle'):
        cv.text(X0, 2.20 + th + 0.16, 9.2, 0.80, s['subtitle'], 15.5, color=cv.c['muted'], min_size=12)
    if s.get('meta'):
        _meta_strip(cv, s['meta'], X0, 5.58, 10.4)


RENDERERS = {
    'cover': cover, 'agenda': agenda, 'section': section, 'statement': statement, 'metrics': metrics,
    'kpi-dashboard': kpi_dashboard, 'cards': cards, 'process': process, 'timeline': timeline, 'comparison': comparison,
    'problem-solution': problem_solution, 'table': table, 'chart': chart, 'case': case, 'evidence-levels': evidence_levels,
    'methodology': methodology, 'diagram': diagram, 'learning-objectives': learning_objectives, 'definition': definition,
    'image-split': image_split, 'full-bleed-image': full_bleed_image, 'quote': quote, 'key-takeaways': key_takeaways,
    'references': references, 'closing': closing,
}
