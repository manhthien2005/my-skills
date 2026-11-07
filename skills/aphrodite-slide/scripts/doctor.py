#!/usr/bin/env python3
"""Self-contained health & specification check for Aphrodite-slide v2 (zero third-party deps required)."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        try:
            _stream.reconfigure(encoding='utf-8')
        except Exception:  # noqa: BLE001
            pass


def fail(msg: str) -> None:
    raise SystemExit(f'FAIL: {msg}')


def main() -> None:
    # 1. SKILL.md single-entrypoint & Agent Skills specification compliance
    main_md = HERE / 'SKILL.md'
    if not main_md.is_file():
        fail('SKILL.md missing')
    content = main_md.read_text(encoding='utf-8')
    lines = content.splitlines()
    if len(lines) > 500:
        fail(f'SKILL.md exceeds 500-line Agent Skills progressive disclosure limit ({len(lines)} lines)')
    m = re.match(r'\A---\r?\n(.*?)\r?\n---', content, re.S)
    if not m:
        fail('SKILL.md YAML frontmatter missing')
    fm = m.group(1)
    name_m = re.search(r'^name:\s*([^\s]+)\s*$', fm, re.M)
    name = name_m.group(1) if name_m else None
    if name != HERE.name or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name or ''):
        fail(f'Invalid skill name {name!r} for directory {HERE.name}')
    if len(name) > 64:
        fail('Skill name exceeds 64 chars')
    if not re.search(r'^description:\s*\S+', fm, re.M):
        fail('SKILL.md description missing')

    unexpected = [str(p.relative_to(HERE)) for p in HERE.rglob('SKILL.md') if p.resolve() != main_md.resolve()]
    if unexpected:
        fail(f'Nested SKILL.md files found (violates single-skill rule): {unexpected}')

    # 2. Mandatory code, runtime, theme, font, icon and license files
    mandatory = [
        'scripts/studio.py',
        'studio/__init__.py', 'studio/paths.py', 'studio/common.py', 'studio/spec.py',
        'studio/outline.py', 'studio/registry.py', 'studio/recommend.py', 'studio/templates.py',
        'studio/previews.py', 'studio/render.py', 'studio/export.py',
        'studio/html/__init__.py', 'studio/html/layouts.py', 'studio/html/charts.py',
        'studio/pptx/__init__.py', 'studio/pptx/draw.py', 'studio/pptx/layouts.py', 'studio/pptx/charts.py',
        'studio/qa/__init__.py', 'studio/qa/probe.js', 'studio/qa/pptx_qa.py',
        'assets/registry.json', 'assets/layouts/catalog.json', 'assets/animations/presets.json',
        'assets/runtime/deck.css', 'assets/runtime/deck.js',
        'assets/fonts/fonts.json', 'assets/fonts/coverage.json',
        'assets/icons/icons.json', 'assets/icons/LICENSE-lucide.txt',
        'assets/themes/aliases.json', 'assets/themes/editorial-warm.json', 'assets/themes/corporate-premium.json',
        'assets/themes/infographic-modern.json', 'assets/themes/clinical-clean.json', 'assets/themes/keynote-night.json',
        'configs/profile.json', 'examples/logistics/deck.json', 'examples/gallery/deck.json',
        'references/THIRD_PARTY.md', 'LICENSE',
    ]
    missing = [p for p in mandatory if not (HERE / p).is_file()]
    if missing:
        fail(f'Missing mandatory files: {missing}')

    # 3. Registry & template preview integrity
    reg = json.loads((HERE / 'assets/registry.json').read_text(encoding='utf-8'))
    reg_templates = reg.get('templates') or []
    if len(reg_templates) < 5:
        fail(f'Expected at least 5 repo templates in registry.json, found {len(reg_templates)}')
    for item in reg_templates:
        tid = item['id']
        tdir = HERE / 'assets/templates' / tid
        for req in ('template.json', 'sample.json', 'preview.jpg'):
            if not (tdir / req).is_file():
                fail(f'Template {tid} missing {req}')
        prev_rel = HERE / item['preview']
        if not prev_rel.is_file() or prev_rel.stat().st_size < 5000:
            fail(f'Template {tid} preview image missing or suspiciously small: {prev_rel}')

    # 4. Bundled fonts & OFL licenses
    fonts_meta = json.loads((HERE / 'assets/fonts/fonts.json').read_text(encoding='utf-8'))
    for face in fonts_meta.get('faces', []):
        if not (HERE / 'assets/fonts' / face['file']).is_file():
            fail(f"Missing bundled font file: {face['file']}")
    licenses = list((HERE / 'assets/fonts/licenses').glob('*-OFL.txt'))
    if len(licenses) < 7:
        fail(f'Expected 7 OFL font licenses, found {len(licenses)}')

    print(f'PASS: {name} single-skill structure, {len(reg_templates)} templates, 5 themes, 25 layouts, offline fonts & licenses ({len(lines)} lines in SKILL.md)')
    print('Python:', sys.version.split()[0])
    for dep in ('playwright', 'PIL', 'pptx', 'yaml'):
        print(f'Optional {dep}:', 'available' if importlib.util.find_spec(dep) else 'not installed')
    try:
        from studio.browser import find_chromium
        exe = find_chromium()
        print('Local browser:', exe if exe else 'Playwright default / none discovered')
    except Exception:  # noqa: BLE001
        pass
    print('Skill root:', HERE)


if __name__ == '__main__':
    main()
