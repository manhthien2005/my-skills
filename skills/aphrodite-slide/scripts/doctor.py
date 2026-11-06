#!/usr/bin/env python3
"""Validate self-contained single-skill package, no third-party deps required."""
from __future__ import annotations
import importlib.util
import re
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]

def main():
    main_md=HERE/'SKILL.md'
    content=main_md.read_text(encoding='utf-8')
    m=re.match(r'\A---\n(.*?)\n---',content,re.S)
    if not m: raise SystemExit('FAIL: SKILL.md frontmatter missing')
    match=re.search(r'^name:\s*([^\s]+)\s*$',m.group(1),re.M)
    name=match.group(1) if match else None
    if name!=HERE.name or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name or ''):
        raise SystemExit(f'FAIL: invalid skill name {name!r} for {HERE.name}')
    if not re.search(r'^description:\s*\S+',m.group(1),re.M):
        raise SystemExit('FAIL: description missing')
    unexpected=[p for p in HERE.rglob('SKILL.md') if p.resolve()!=main_md.resolve()]
    if unexpected: raise SystemExit('FAIL: multiple SKILL.md: '+str(unexpected))
    mandatory=['scripts/studio.py','studio/html.py','studio/model.py','studio/quality.py','studio/pptx.py',
               'configs/themes/editorial-cream.json','configs/themes/keynote-night.json','configs/themes/swiss-contrast.json',
               'examples/logistics/deck.json','references/THIRD_PARTY.md']
    missing=[v for v in mandatory if not (HERE/v).is_file()]
    if missing: raise SystemExit('FAIL: missing files '+str(missing))
    print('PASS: skill metadata, single entrypoint, and mandatory local resources')
    print('Python:',sys.version.split()[0])
    for dep in ['playwright','PIL','pptx']:
        print(f'Optional {dep}:', 'available' if importlib.util.find_spec(dep) else 'not installed')
    print('Folder:',HERE)

if __name__=='__main__': main()
