#!/usr/bin/env python3
"""Maintainer tool: (re)build bundled offline assets. NOT needed at runtime.

What it does
1. Downloads OFL fonts that cover Vietnamese from github.com/google/fonts,
   subsets them to Latin + Vietnamese + common punctuation, writes WOFF2 files to
   assets/fonts/, copies each OFL licence, and writes assets/fonts/coverage.json
   (code points per family) so the QA step can detect missing glyphs without
   any font library at runtime.
2. Downloads a curated subset of Lucide icons (ISC) into assets/icons/icons.json
   and renders white PNG versions (for PowerPoint, which cannot embed SVG via
   python-pptx) when Playwright is available.

Requires (maintainer only): fonttools, brotli, optionally playwright.
Usage: python scripts/dev/build_assets.py [--skip-fonts] [--skip-icons]
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
FONT_DIR = SKILL_DIR / 'assets' / 'fonts'
ICON_DIR = SKILL_DIR / 'assets' / 'icons'
GF = 'https://raw.githubusercontent.com/google/fonts/main/ofl/'

# family -> list of (source file, css style, output stem); variable fonts keep the wght axis.
FONTS = {
    'Cormorant Garamond': ('cormorantgaramond', [('CormorantGaramond[wght].ttf', 'normal', 'CormorantGaramond'),
                                                 ('CormorantGaramond-Italic[wght].ttf', 'italic', 'CormorantGaramond-Italic')]),
    'Plus Jakarta Sans': ('plusjakartasans', [('PlusJakartaSans[wght].ttf', 'normal', 'PlusJakartaSans')]),
    'Be Vietnam Pro': ('bevietnampro', [('BeVietnamPro-Regular.ttf', 'normal', 'BeVietnamPro-400'),
                                        ('BeVietnamPro-Medium.ttf', 'normal', 'BeVietnamPro-500'),
                                        ('BeVietnamPro-SemiBold.ttf', 'normal', 'BeVietnamPro-600'),
                                        ('BeVietnamPro-Bold.ttf', 'normal', 'BeVietnamPro-700'),
                                        ('BeVietnamPro-ExtraBold.ttf', 'normal', 'BeVietnamPro-800')]),
    'Inter': ('inter', [('Inter[opsz,wght].ttf', 'normal', 'Inter')]),
    'Source Serif 4': ('sourceserif4', [('SourceSerif4[opsz,wght].ttf', 'normal', 'SourceSerif4'),
                                        ('SourceSerif4-Italic[opsz,wght].ttf', 'italic', 'SourceSerif4-Italic')]),
    'Lexend': ('lexend', [('Lexend[wght].ttf', 'normal', 'Lexend')]),
    'JetBrains Mono': ('jetbrainsmono', [('JetBrainsMono[wght].ttf', 'normal', 'JetBrainsMono')]),
}
STATIC_WEIGHT = re.compile(r'-(\d00)$')

UNICODES = (
    'U+0020-007E,U+00A0-00FF,U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,'
    'U+01AF-01B0,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0300-0301,U+0303-0304,'
    'U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+2000-206F,U+20AB,U+20AC,U+2122,U+2190-2199,'
    'U+2212,U+2215,U+2264-2265,U+00B0,U+2030,U+2116,U+2713,U+2717,U+25CF,U+25CB,U+2192,'
    # science/teaching: Greek, super/subscripts, arrows, common math operators
    'U+0370-03FF,U+2070-209F,U+2190-21FF,U+2200-22FF,U+2300-23FF,U+25A0-25FF'
)

ICONS = ['activity', 'chart-column', 'chart-line', 'chart-pie', 'book-open', 'brain', 'briefcase', 'calendar',
         'circle-check', 'clipboard-list', 'clock', 'cloud', 'code', 'cpu', 'database', 'file-text',
         'flask-conical', 'globe', 'graduation-cap', 'heart-pulse', 'layers', 'lightbulb', 'lock', 'microscope',
         'pill', 'rocket', 'search', 'settings', 'shield-check', 'smartphone', 'stethoscope', 'target',
         'trending-up', 'trending-down', 'truck', 'users', 'zap', 'workflow', 'package', 'syringe', 'thermometer',
         'hospital', 'school', 'presentation', 'map-pin', 'message-square', 'git-branch', 'server', 'eye', 'leaf',
         'scale', 'award', 'dna', 'bot', 'gauge', 'list-checks', 'circle-question-mark', 'quote', 'arrow-right',
         'check', 'x', 'puzzle', 'handshake', 'building', 'coins', 'banknote', 'user', 'notebook-pen', 'sigma',
         'test-tube', 'bed', 'ambulance', 'apple', 'dumbbell', 'baby', 'droplet', 'wifi', 'monitor',
         'mouse-pointer-click', 'plug', 'route', 'boxes', 'factory', 'warehouse', 'circle-alert', 'info',
         'book-open-check', 'hand-heart', 'scan-search', 'timer', 'flag', 'goal', 'map', 'shield-alert']


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'aphrodite-slide-asset-builder'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def build_fonts():
    from fontTools import subset
    from fontTools.ttLib import TTFont
    try:
        from fontTools.varLib import instancer
    except ImportError:  # pragma: no cover
        instancer = None
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    (FONT_DIR / 'licenses').mkdir(exist_ok=True)
    coverage, faces = {}, []
    for family, (folder, files) in FONTS.items():
        lic = fetch(GF + folder + '/OFL.txt')
        (FONT_DIR / 'licenses' / f'{folder}-OFL.txt').write_bytes(lic)
        cps = set()
        for src, style, stem in files:
            raw = fetch(GF + folder + '/' + src.replace('[', '%5B').replace(']', '%5D').replace(',', '%2C'))
            font = TTFont(io.BytesIO(raw))
            axes = [a.axisTag for a in font['fvar'].axes] if 'fvar' in font else []
            if 'opsz' in axes and instancer:  # pin optical size to keep files small
                font = instancer.instantiateVariableFont(font, {'opsz': None})
                buf = io.BytesIO(); font.save(buf); buf.seek(0)
                font = TTFont(buf, lazy=False)  # round-trip avoids lazy gvar KeyError in subsetter
            opts = subset.Options()
            opts.flavor = 'woff2'
            opts.layout_features = ['*']
            opts.name_IDs = ['*']
            opts.notdef_outline = True
            sub = subset.Subsetter(options=opts)
            sub.populate(unicodes=subset.parse_unicodes(UNICODES))
            sub.subset(font)
            out = FONT_DIR / f'{stem}.woff2'
            font.flavor = 'woff2'
            font.save(out)
            cps |= set(font.getBestCmap().keys())
            if 'fvar' in font:
                w = [a for a in font['fvar'].axes if a.axisTag == 'wght'][0]
                weight = f'{int(w.minValue)} {int(w.maxValue)}'
            else:
                m = STATIC_WEIGHT.search(stem)
                weight = m.group(1) if m else '400'
            faces.append({'family': family, 'file': out.name, 'style': style, 'weight': weight})
            print(f'  {out.name:36s} {out.stat().st_size/1024:7.1f} KB')
        coverage[family] = compress(sorted(cps))
    (FONT_DIR / 'fonts.json').write_text(json.dumps({'faces': faces}, indent=1), encoding='utf-8')
    (FONT_DIR / 'coverage.json').write_text(json.dumps(coverage), encoding='utf-8')


def compress(cps):
    ranges, start, prev = [], None, None
    for c in cps:
        if start is None:
            start = prev = c
        elif c == prev + 1:
            prev = c
        else:
            ranges.append([start, prev]); start = prev = c
    if start is not None:
        ranges.append([start, prev])
    return ranges


def build_icons():
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    (ICON_DIR / 'LICENSE-lucide.txt').write_bytes(fetch('https://raw.githubusercontent.com/lucide-icons/lucide/main/LICENSE'))
    icons = {}
    for name in ICONS:
        try:
            svg = fetch(f'https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{name}.svg').decode()
        except Exception as ex:  # noqa: BLE001
            print('  skip icon', name, ex); continue
        inner = re.search(r'<svg[^>]*>(.*)</svg>', svg, re.S).group(1)
        inner = re.sub(r'\s+', ' ', inner).strip()
        icons[name] = inner
    (ICON_DIR / 'icons.json').write_text(json.dumps(icons, indent=0, sort_keys=True), encoding='utf-8')
    print(f'  {len(icons)} icons')
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('  playwright missing: PNG icons not rendered'); return
    png_dir = ICON_DIR / 'png'
    png_dir.mkdir(exist_ok=True)
    exe = os.environ.get('CHROMIUM_EXECUTABLE')
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        page = b.new_page(viewport={'width': 192, 'height': 192})
        for name, inner in icons.items():
            html = ('<html><body style="margin:0;background:transparent">'
                    '<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 24 24" fill="none" '
                    'stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + inner + '</svg></body></html>')
            page.set_content(html)
            page.screenshot(path=str(png_dir / f'{name}.png'), omit_background=True)
        b.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-fonts', action='store_true')
    ap.add_argument('--skip-icons', action='store_true')
    a = ap.parse_args()
    if not a.skip_fonts:
        print('Fonts'); build_fonts()
    if not a.skip_icons:
        print('Icons'); build_icons()


if __name__ == '__main__':
    sys.exit(main())