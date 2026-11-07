"""Template registry: repo templates (assets/templates) + private user templates (~/.aphrodite-slide/templates)."""
from __future__ import annotations

import json
from pathlib import Path

from . import paths

COMPACT_KEYS = ('id', 'name', 'name_vi', 'version', 'description', 'use_cases', 'tags', 'best_for', 'avoid_for', 'audience',
                'formality', 'density', 'data_intensity', 'default_theme', 'compatible_themes', 'animation', 'signature_layouts')


def template_roots() -> list[tuple[str, Path]]:
    return [('user', paths.user_home() / 'templates'), ('repo', paths.TEMPLATES)]


def list_templates() -> list[dict]:
    seen, out = set(), []
    for scope, root in template_roots():
        if not root.exists():
            continue
        for tj in sorted(root.glob('*/template.json')):
            t = paths.read_json(tj)
            tid = t.get('id', tj.parent.name)
            if tid in seen:
                continue
            seen.add(tid)
            t['scope'] = scope
            t['_dir'] = str(tj.parent)
            prev = tj.parent / t.get('preview', 'preview.jpg')
            t['preview_path'] = str(prev) if prev.exists() else None
            out.append(t)
    return out


def get_template(tid: str) -> dict:
    for t in list_templates():
        if t['id'] == tid:
            return t
    raise ValueError(f'Unknown template {tid!r}. Run `studio.py templates` to list templates.')


def sample_deck(t: dict) -> dict:
    p = Path(t['_dir']) / t.get('sample', 'sample.json')
    return paths.read_json(p)


def build_registry() -> Path:
    """Regenerate assets/registry.json (repo templates only, compact metadata for agent search)."""
    items = []
    for t in list_templates():
        if t['scope'] != 'repo':
            continue
        item = {k: t[k] for k in COMPACT_KEYS if k in t}
        item['preview'] = f"assets/templates/{t['id']}/{t.get('preview', 'preview.jpg')}"
        item['storyline'] = [b['beat'] for b in t.get('storyline', [])]
        items.append(item)
    reg = {'version': 1, 'generated_by': 'studio.py registry build',
           'note': 'Compact index. Read a template.json only after shortlisting. Private user templates live in ~/.aphrodite-slide/templates and are merged at runtime.',
           'templates': items}
    out = paths.ASSETS / 'registry.json'
    out.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding='utf-8')
    return out


def apply_template(deck: dict, t: dict) -> dict:
    """Fill deck-level defaults from a template without overriding explicit choices."""
    d = dict(deck)
    d.setdefault('template', t['id'])
    d.setdefault('theme', t.get('default_theme'))
    d.setdefault('animation', t.get('animation', 'professional'))
    d.setdefault('density', t.get('density', 'speaker'))
    if t.get('build') and 'build' not in d:
        d['build'] = True
    return d

