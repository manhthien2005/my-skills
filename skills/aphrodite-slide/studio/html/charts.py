"""Theme-aware SVG charts for HTML slides. Zero baseline for bars, direct labels, at most 4 gridlines,
no 3D/shadows. Every mark carries animation classes consumed by deck.js/deck.css."""
from __future__ import annotations

import math

from ..common import esc, fmt_num


def nice_max(v: float) -> float:
    if v <= 0:
        return 1
    exp = 10 ** math.floor(math.log10(v))
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if m * exp >= v:
            return m * exp
    return 10 * exp


def series_colors(chart: dict, theme: dict) -> list[str]:
    pal = theme['colors']['series']
    return [se.get('color') or pal[i % len(pal)] for i, se in enumerate(chart['series'])]


def svg_chart(chart: dict, theme: dict, lang: str, width: int = 1664, height: int = 520) -> str:
    kind = chart.get('type', 'column')
    fn = {'column': _column, 'stacked': _column, 'bar': _bar, 'line': _line, 'donut': _donut}.get(kind, _column)
    return fn(chart, theme, lang, width, height)


def _legend(chart, theme):
    if len(chart['series']) < 2 or chart.get('type') == 'donut':
        return ''
    cols = series_colors(chart, theme)
    return '<div class="legend">' + ''.join(f'<span><i style="background:{c}"></i>{esc(se.get("name", ""))}</span>'
                                            for se, c in zip(chart['series'], cols)) + '</div>'


def _grid(theme, x0, x1, y0, plot_h, top, ticks, lang, unit):
    c = theme['colors']
    out = []
    for j in range(ticks + 1):
        y = y0 + plot_h * (1 - j / ticks)
        out.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{c["line"]}" stroke-width="{2 if j == 0 else 1.2}"/>')
        out.append(f'<text x="{x0 - 14}" y="{y + 7:.1f}" font-size="19" fill="{c["subtle"]}" text-anchor="end">'
                   f'{esc(fmt_num(top * j / ticks, lang))}</text>')
    return ''.join(out)


def _hl_index(chart):
    h = chart.get('highlight')
    if h is None:
        return None
    if isinstance(h, int):
        return h
    try:
        return [str(x) for x in chart['categories']].index(str(h))
    except ValueError:
        return None


def _column(chart, theme, lang, W, H):
    c = theme['colors']
    cats, series = chart['categories'], chart['series']
    stacked = chart.get('type') == 'stacked'
    unit = chart.get('unit', '')
    cols = series_colors(chart, theme)
    hl = _hl_index(chart)
    if stacked:
        top = nice_max(max(sum((se['values'][i] or 0) for se in series) for i in range(len(cats))))
    else:
        top = nice_max(max(max(se['values']) for se in series))
    x0, x1, y0, y1 = 70, W - 10, 46, H - 64
    plot_w, plot_h = x1 - x0, y1 - y0
    n, m = len(cats), (1 if stacked else len(series))
    group = plot_w / n * (0.56 if m == 1 else 0.72)
    bw = group / m
    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(chart.get("title", "chart"))}">',
             _grid(theme, x0, x1, y0, plot_h, top, 4, lang, unit)]
    k = 0
    for i, cat in enumerate(cats):
        gx = x0 + plot_w * (i + .5) / n - group / 2
        base = y1
        total = 0
        for si, se in enumerate(series):
            v = se['values'][i] or 0
            h = plot_h * max(v, 0) / top
            color = cols[si]
            if hl is not None and m == 1 and not stacked:
                color = c['accent_strong'] if i == hl else c['line'] if theme.get('scheme') != 'dark' else c['surface_alt']
            if stacked:
                x, y = gx, base - h
                base -= h
                total += v
            else:
                x, y = gx + si * bw, y1 - h
            parts.append(f'<rect class="a a-grow-y" style="--i:{k}" x="{x + (2 if m > 1 else 0):.1f}" y="{y:.1f}" '
                         f'width="{bw - (4 if m > 1 else 0):.1f}" height="{max(h, 0.5):.1f}" rx="3" fill="{color}"/>')
            if stacked:
                if h > 34:
                    parts.append(f'<text class="a" style="--i:{k + 3}" x="{x + bw / 2:.1f}" y="{y + h / 2 + 8:.1f}" text-anchor="middle" '
                                 f'font-size="20" font-weight="700" fill="#fff">{esc(fmt_num(v, lang))}</text>')
            else:
                fs = 26 if m == 1 else 19
                parts.append(f'<text class="a" style="--i:{k + 3}" x="{x + bw / 2:.1f}" y="{y - 12:.1f}" text-anchor="middle" '
                             f'font-size="{fs}" font-weight="800" fill="{c["ink"]}">{esc(fmt_num(v, lang, unit))}</text>')
            k += 1
        if stacked:
            parts.append(f'<text class="a" style="--i:{k + 3}" x="{gx + bw / 2:.1f}" y="{base - 12:.1f}" text-anchor="middle" font-size="24" '
                         f'font-weight="800" fill="{c["ink"]}">{esc(fmt_num(total, lang, unit))}</text>')
        parts.append(f'<text x="{x0 + plot_w * (i + .5) / n:.1f}" y="{H - 24}" text-anchor="middle" font-size="22" font-weight="600" '
                     f'fill="{c["muted"]}">{esc(cat)}</text>')
    parts.append('</svg>')
    return _legend(chart, theme) + ''.join(parts)


def _bar(chart, theme, lang, W, H):
    c = theme['colors']
    cats, se = chart['categories'], chart['series'][0]
    unit = chart.get('unit', '')
    hl = _hl_index(chart)
    vals = se['values']
    top = nice_max(max(vals))
    label_w = min(420, max(160, int(max(len(str(x)) for x in cats) * 13.5)))
    x0, x1 = label_w + 24, W - 110
    n = len(cats)
    row = (H - 20) / n
    bh = min(56, row * 0.62)
    color = series_colors(chart, theme)[0]
    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(chart.get("title", "chart"))}">',
             f'<line x1="{x0}" y1="0" x2="{x0}" y2="{H - 10}" stroke="{c["line"]}" stroke-width="2"/>']
    for i, (cat, v) in enumerate(zip(cats, vals)):
        y = 10 + row * i + (row - bh) / 2
        w = (x1 - x0) * max(v or 0, 0) / top
        col = color if hl is None else (c['accent_strong'] if i == hl else c['line'] if theme.get('scheme') != 'dark' else c['surface_alt'])
        parts.append(f'<text x="{x0 - 20}" y="{y + bh / 2 + 8:.1f}" text-anchor="end" font-size="23" font-weight="600" fill="{c["ink"]}">{esc(cat)}</text>')
        parts.append(f'<rect class="a a-grow-x" style="--i:{i}" x="{x0}" y="{y:.1f}" width="{max(w, .5):.1f}" height="{bh:.1f}" rx="3" fill="{col}"/>')
        parts.append(f'<text class="a" style="--i:{i + 3}" x="{x0 + w + 14:.1f}" y="{y + bh / 2 + 9:.1f}" font-size="25" font-weight="800" '
                     f'fill="{c["ink"]}">{esc(fmt_num(v, lang, unit))}</text>')
    parts.append('</svg>')
    return ''.join(parts)


def _line(chart, theme, lang, W, H):
    c = theme['colors']
    cats, series = chart['categories'], chart['series']
    unit = chart.get('unit', '')
    cols = series_colors(chart, theme)
    allv = [v for se in series for v in se['values']]
    lo = min(0, min(allv))
    top = nice_max(max(allv))
    x0, x1, y0, y1 = 70, W - 90, 40, H - 64
    plot_w, plot_h = x1 - x0, y1 - y0
    n = len(cats)

    def xy(i, v):
        return x0 + (plot_w * i / (n - 1) if n > 1 else plot_w / 2), y1 - plot_h * (v - lo) / (top - lo)
    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(chart.get("title", "chart"))}">',
             _grid(theme, x0, x1 + 50, y0, plot_h, top, 4, lang, unit)]
    for i, cat in enumerate(cats):
        x, _ = xy(i, 0)
        parts.append(f'<text x="{x:.1f}" y="{H - 24}" text-anchor="middle" font-size="22" font-weight="600" fill="{c["muted"]}">{esc(cat)}</text>')
    for si, se in enumerate(series):
        pts = [xy(i, v) for i, v in enumerate(se['values'])]
        d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        parts.append(f'<path class="a a-draw" style="--i:{si * 2}" pathLength="1" d="{d}" fill="none" stroke="{cols[si]}" stroke-width="6" '
                     f'stroke-linejoin="round" stroke-linecap="round"/>')
        for i, (x, y) in enumerate(pts):
            last = i == len(pts) - 1
            parts.append(f'<circle class="a" style="--i:{si * 2 + 4 + i * .3:.1f}" cx="{x:.1f}" cy="{y:.1f}" r="{9 if last else 6}" '
                         f'fill="{cols[si] if last else theme["colors"]["bg"]}" stroke="{cols[si]}" stroke-width="4"/>')
            if last or len(series) == 1 and n <= 8:
                parts.append(f'<text class="a" style="--i:{si * 2 + 6}" x="{x + (16 if last else 0):.1f}" y="{y - 18:.1f}" '
                             f'text-anchor="{"start" if last else "middle"}" font-size="{25 if last else 20}" font-weight="800" '
                             f'fill="{cols[si] if last else c["ink"]}">{esc(fmt_num(se["values"][i], lang, unit if last else ""))}</text>')
    parts.append('</svg>')
    return _legend(chart, theme) + ''.join(parts)


def _donut(chart, theme, lang, W, H):
    c = theme['colors']
    cats, vals = chart['categories'], chart['series'][0]['values']
    unit = chart.get('unit', '')
    pal = theme['colors']['series']
    total = sum(vals) or 1
    cx, cy, r, sw = H / 2, H / 2, H / 2 - 40, 64
    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(chart.get("title", "chart"))}">']
    acc = 0.0
    gap = 0.004 if len(vals) > 1 else 0
    for i, v in enumerate(vals):
        a0 = acc / total * 2 * math.pi - math.pi / 2
        acc += v
        a1 = acc / total * 2 * math.pi - math.pi / 2 - gap * 2 * math.pi
        large = 1 if a1 - a0 > math.pi else 0
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        parts.append(f'<path class="a a-draw" style="--i:{i * 2}" pathLength="1" d="M{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f}" '
                     f'fill="none" stroke="{pal[i % len(pal)]}" stroke-width="{sw}"/>')
    center = chart.get('center_label') or fmt_num(total, lang, unit)
    parts.append(f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" font-size="58" font-weight="800" fill="{c["ink"]}">{esc(center)}</text>')
    if chart.get('center_caption'):
        parts.append(f'<text x="{cx}" y="{cy + 46}" text-anchor="middle" font-size="21" fill="{c["muted"]}">{esc(chart["center_caption"])}</text>')
    lx = H + 70
    row = min(76, (H - 40) / max(1, len(cats)))
    y = (H - row * len(cats)) / 2 + row / 2
    for i, (cat, v) in enumerate(zip(cats, vals)):
        pct = v / total * 100
        parts.append(f'<g class="a" style="--i:{i + 2}"><rect x="{lx}" y="{y - 14:.1f}" width="28" height="28" rx="6" fill="{pal[i % len(pal)]}"/>'
                     f'<text x="{lx + 46}" y="{y + 9:.1f}" font-size="25" font-weight="600" fill="{c["ink"]}">{esc(cat)}</text>'
                     f'<text x="{W - 10}" y="{y + 9:.1f}" text-anchor="end" font-size="27" font-weight="800" fill="{c["ink"]}">'
                     f'{esc(fmt_num(pct, lang, "%", 0))}</text>'
                     f'<line x1="{lx}" y1="{y + row / 2:.1f}" x2="{W - 10}" y2="{y + row / 2:.1f}" stroke="{c["line"]}"/></g>')
        y += row
    parts.append('</svg>')
    return ''.join(parts)


def sparkline(values, color: str, w: int = 460, h: int = 64) -> str:
    """Trend line for KPI tiles. Uses a real-proportion viewBox (no non-scaling-stroke: it breaks pathLength-based drawing)."""
    if not values or len(values) < 2:
        return ''
    lo, hi = min(values), max(values)
    rng = (hi - lo) or 1
    pts = [(8 + (w - 16) * i / (len(values) - 1), h - 8 - (h - 16) * (v - lo) / rng) for i, v in enumerate(values)]
    d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    lx, ly = pts[-1]
    return (f'<svg class="spark" viewBox="0 0 {w} {h}"><path class="a a-draw" style="--i:4" pathLength="1" d="{d}" '
            f'fill="none" stroke="{color}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle class="a" style="--i:8" cx="{lx:.1f}" cy="{ly:.1f}" r="6" fill="{color}"/></svg>')

