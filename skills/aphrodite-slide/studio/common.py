"""Shared helpers for renderers: escaping, inline rich text, icons, colours, number format, i18n."""
from __future__ import annotations

import html
import json
import re
from functools import lru_cache

from . import paths

BOLD = re.compile(r'\*\*(.+?)\*\*')

LABELS = {
    'vi': {'demo': 'Dữ liệu minh họa', 'estimate': 'Ước tính', 'now': 'Hiện tại', 'done': 'Đã xong', 'next': 'Sắp tới',
           'example': 'Ví dụ', 'problem': 'Vấn đề', 'solution': 'Giải pháp', 'target': 'Mục tiêu', 'objectives_lead': 'Sau phần này, người học có thể:',
           'references': 'Tài liệu tham khảo', 'source': 'Nguồn', 'notes_none': 'Không có ghi chú', 'help': '← → chuyển · F toàn màn hình · N ghi chú · O tổng quan',
           'ai_image': 'Ảnh minh họa tạo bằng AI'},
    'en': {'demo': 'Illustrative data', 'estimate': 'Estimate', 'now': 'Now', 'done': 'Done', 'next': 'Next',
           'example': 'Example', 'problem': 'Problem', 'solution': 'Solution', 'target': 'Target', 'objectives_lead': 'After this part, learners can:',
           'references': 'References', 'source': 'Source', 'notes_none': 'No notes', 'help': '← → navigate · F fullscreen · N notes · O overview',
           'ai_image': 'AI-generated illustration'},
}


def lang_of(deck: dict) -> str:
    return 'en' if deck.get('language') == 'en' else 'vi'


def L(deck: dict, key: str) -> str:
    return LABELS[lang_of(deck)].get(key, key)


def esc(v) -> str:
    return html.escape('' if v is None else str(v), quote=True)


def rt(v) -> str:
    """Escape, then allow **bold** emphasis (rendered with the accent colour in titles)."""
    return BOLD.sub(r'<strong>\1</strong>', esc(v)).replace('\n', '<br>')


def plain(v) -> str:
    return BOLD.sub(r'\1', '' if v is None else str(v))


def runs(v):
    """Split '**x**' markup into [(text, bold)] runs for PPTX."""
    s = '' if v is None else str(v)
    out, pos = [], 0
    for m in BOLD.finditer(s):
        if m.start() > pos:
            out.append((s[pos:m.start()], False))
        out.append((m.group(1), True))
        pos = m.end()
    if pos < len(s):
        out.append((s[pos:], False))
    return out or [('', False)]


@lru_cache(maxsize=1)
def _icons() -> dict:
    p = paths.ICONS / 'icons.json'
    return paths.read_json(p) if p.exists() else {}


def icon_names() -> list[str]:
    return sorted(_icons())


def icon_svg(name: str | None, size: int | None = None) -> str:
    if not name:
        return ''
    inner = _icons().get(str(name))
    if not inner:
        return ''
    dim = f' width="{size}" height="{size}"' if size else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg"{dim} viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{inner}</svg>')


def hex_rgb(h: str):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgba(h: str, a: float) -> str:
    r, g, b = hex_rgb(h)
    return f'rgba({r},{g},{b},{a})'


def mix(a: str, b: str, t: float) -> str:
    ra, rb = hex_rgb(a), hex_rgb(b)
    return '#' + ''.join(f'{round(x + (y - x) * t):02X}' for x, y in zip(ra, rb))


def luminance(h: str) -> float:
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hex_rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def fmt_num(v, lang: str = 'vi', unit: str = '', decimals: int | None = None) -> str:
    if v is None:
        return ''
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if decimals is None:
        decimals = 0 if abs(f - round(f)) < 1e-9 else (1 if abs(f * 10 - round(f * 10)) < 1e-9 else 2)
    s = f'{f:,.{decimals}f}'
    if lang == 'vi':
        s = s.replace(',', '§').replace('.', ',').replace('§', '.')
    if unit:
        s += unit if unit in ('%', '‰', '°', '°C', 'x', '×', 'pp') else f' {unit}'
    return s


def title_class(text: str, limit: int = 58) -> str:
    return ' long' if len(plain(text)) > limit else ''


def data_json(obj) -> str:
    return esc(json.dumps(obj, ensure_ascii=False))

