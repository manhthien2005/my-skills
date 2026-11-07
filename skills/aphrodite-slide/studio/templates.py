"""Custom themes and saving designs as reusable templates (versioned, privacy-scrubbed, never silently overwritten)."""
from __future__ import annotations

import datetime as _dt
import json
import re
import shutil
from pathlib import Path

from . import paths
from .spec import load_theme, normalize, deep_merge, slide_texts, resolve_theme_id

SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
PII = {'email': re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'), 'phone': re.compile(r'(?:\+?84|0)\d{8,10}\b'),
       'url': re.compile(r'https?://\S+'), 'id_number': re.compile(r'\b\d{9}(?:\d{3})?\b')}


def scope_root(scope: str) -> Path:
    if scope == 'repo':
        return paths.ASSETS
    if scope == 'user':
        return paths.user_home()
    raise ValueError('scope must be "repo" (clean, shareable) or "user" (private/brand, outside the repo)')


def bump_version(v: str, part: str) -> str:
    major, minor, patch = (int(x) for x in (v or '1.0.0').split('.')[:3])
    if part == 'major':
        return f'{major + 1}.0.0'
    if part == 'minor':
        return f'{major}.{minor + 1}.0'
    if part == 'patch':
        return f'{major}.{minor}.{patch + 1}'
    raise ValueError('bump must be patch, minor or major')


def _archive(target: Path, version: str):
    arch = target / 'versions' / version
    arch.mkdir(parents=True, exist_ok=True)
    for f in target.iterdir():
        if f.is_file():
            shutil.copy2(f, arch / f.name)
    return arch


def create_theme(new_id: str, base: str, sets: dict, scope: str = 'user', name: str | None = None, description: str = '',
                 bump: str | None = None) -> Path:
    """Derive a theme: `sets` uses dotted keys, e.g. {'colors.accent': '#0A7', 'fonts.display': 'Lexend'}."""
    if not SLUG.match(new_id):
        raise ValueError('theme id must be lowercase-hyphenated')
    t = load_theme(base)
    t.pop('_path', None)
    over = {}
    for k, v in sets.items():
        cur = over
        parts = k.split('.')
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        try:
            v = json.loads(v) if isinstance(v, str) and v[:1] in '[{0123456789-' and not v.startswith('#') else v
        except ValueError:
            pass
        cur[parts[-1]] = v
    t = deep_merge(t, over)
    root = scope_root(scope) / 'themes'
    root.mkdir(parents=True, exist_ok=True)
    out = root / f'{new_id}.json'
    if out.exists():
        old = json.loads(out.read_text(encoding='utf-8'))
        if not bump:
            raise FileExistsError(f'theme {new_id} exists (v{old.get("version")}); pass --bump patch|minor|major to version it')
        hist = root / 'versions'
        hist.mkdir(exist_ok=True)
        shutil.copy2(out, hist / f'{new_id}@{old.get("version", "1.0.0")}.json')
        t['version'] = bump_version(old.get('version', '1.0.0'), bump)
    else:
        t['version'] = '1.0.0'
    t.update({'id': new_id, 'name': name or new_id.replace('-', ' ').title(), 'description': description or f'Derived from {base}',
              'derived_from': base, 'updated': _dt.date.today().isoformat()})
    _check_theme(t)
    out.write_text(json.dumps(t, ensure_ascii=False, indent=2), encoding='utf-8')
    return out


def _check_theme(t: dict):
    from .common import contrast
    c = t['colors']
    problems = []
    for k, need in (('ink', 7), ('muted', 4.5), ('subtle', 4.5)):
        r = contrast(c[k], c['bg'])
        if r < need:
            problems.append(f'{k} on bg = {r:.2f}:1 (< {need})')
    if contrast(c['on_accent'], c['accent_strong']) < 3:
        problems.append('on_accent on accent_strong < 3:1')
    cov = json.loads((paths.FONTS / 'coverage.json').read_text(encoding='utf-8'))
    for role in ('display', 'body'):
        if t['fonts'][role] not in cov:
            problems.append(f'font "{t["fonts"][role]}" is not bundled (Vietnamese coverage unverified); bundled: {", ".join(sorted(cov))}')
    if problems:
        raise ValueError('theme fails quality gates:\n  ' + '\n  '.join(problems))


def privacy_scan(deck: dict) -> list[str]:
    hits = []
    for s in deck.get('slides', []):
        for t in slide_texts(s, include_notes=True):
            for kind, rx in PII.items():
                if rx.search(t):
                    hits.append(f'{s.get("id")}: {kind} → "{rx.search(t).group(0)[:40]}"')
    return hits


def save_template(deck: dict, tid: str, name: str, use_cases: list[str], scope: str = 'user', description: str = '',
                  tags: list[str] | None = None, bump: str | None = None, include_content: bool = False,
                  allow_sensitive: bool = False, render: bool = True, name_vi: str | None = None) -> dict:
    """Save the deck's *design* (theme, layout rhythm, motion, density) as a template. Content is excluded unless asked."""
    if not SLUG.match(tid):
        raise ValueError('template id must be lowercase-hyphenated, e.g. "my-brand-pitch"')
    d = normalize(deck)
    root = scope_root(scope) / 'templates'
    target = root / tid
    version = '1.0.0'
    if (target / 'template.json').exists():
        old = json.loads((target / 'template.json').read_text(encoding='utf-8'))
        if not bump:
            raise FileExistsError(f'template {tid} already exists (v{old.get("version")}). Nothing was changed. '
                                  'Re-run with --bump patch|minor|major to save a new version (old one is archived).')
        _archive(target, old.get('version', '1.0.0'))
        version = bump_version(old.get('version', '1.0.0'), bump)
    if include_content:
        hits = privacy_scan(d)
        if hits and not allow_sensitive:
            raise PermissionError('possible personal/confidential data found; not saved:\n  ' + '\n  '.join(hits[:10]) +
                                  '\nRemove it, or re-run with --allow-sensitive after the user explicitly agrees.')
    # theme: custom overrides become a stored theme in the same scope
    theme_id = d['theme']
    if d.get('theme_overrides'):
        base = load_theme(theme_id)
        base.pop('_path', None)
        merged = deep_merge(base, d['theme_overrides'])
        theme_id = f'{tid}-theme'
        merged.update({'id': theme_id, 'name': f'{name} theme', 'version': version, 'derived_from': d['theme']})
        _check_theme(merged)
        (scope_root(scope) / 'themes').mkdir(parents=True, exist_ok=True)
        (scope_root(scope) / 'themes' / f'{theme_id}.json').write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')
    elif scope == 'repo':
        src = Path(load_theme(theme_id)['_path'])
        if paths.user_home() in src.parents:
            raise ValueError(f'theme {theme_id} is private (user scope); save the template with --scope user or copy the theme to the repo first')
    layouts = [s['layout'] for s in d['slides']]
    storyline = [{'beat': s.get('beat') or s['layout'], 'layout': s['layout'], 'purpose': ''} for s in d['slides']]
    target.mkdir(parents=True, exist_ok=True)
    tmpl = {
        'id': tid, 'name': name, 'name_vi': name_vi or name, 'version': version, 'description': description or f'Custom template saved from "{d.get("title", "")}"',
        'use_cases': use_cases, 'tags': tags or [], 'best_for': description, 'avoid_for': '', 'audience': [],
        'formality': d.get('formality', 'medium'), 'density': d.get('density', 'speaker'), 'data_intensity': 'medium',
        'default_theme': theme_id, 'compatible_themes': [theme_id], 'animation': d.get('animation', 'professional'),
        'storyline': storyline, 'signature_layouts': sorted(set(layouts) - {'cover', 'closing', 'section', 'agenda'})[:4],
        'content_rules': [], 'preview': 'preview.jpg', 'sample': 'sample.json', 'source': 'custom',
        'contains_user_content': bool(include_content), 'updated': _dt.date.today().isoformat(),
    }
    if include_content:
        sample = d
    else:
        from .samples import neutral_deck
        sample = neutral_deck(layouts, title=name, language=d.get('language', 'vi'))
        sample['brand'] = 'TEMPLATE · ' + name.upper()
        if any(s.get('image') for s in sample['slides']):
            (target / 'assets').mkdir(exist_ok=True)
            shutil.copy2(paths.ASSETS / 'samples' / 'sample.jpg', target / 'assets' / '__sample__.jpg')
    sample['template'] = tid
    sample['theme'] = theme_id
    (target / 'template.json').write_text(json.dumps(tmpl, ensure_ascii=False, indent=2), encoding='utf-8')
    (target / 'sample.json').write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding='utf-8')
    result = {'id': tid, 'version': version, 'scope': scope, 'dir': str(target), 'theme': theme_id, 'preview': None}
    if render:
        from .registry import get_template
        from .previews import template_previews
        try:
            outs = template_previews(get_template(tid))
            result['preview'] = str(outs[0]) if outs else None
        except Exception as ex:  # noqa: BLE001 - rendering is optional
            result['preview_error'] = str(ex).splitlines()[0]
    if scope == 'repo':
        from .registry import build_registry
        build_registry()
    return result


def test_template(tid: str, other_deck: dict | None = None) -> dict:
    """Prove a template is reusable: build its sample AND a different content deck with its theme/motion."""
    import tempfile
    from .registry import get_template, sample_deck, apply_template
    from .html import build
    t = get_template(tid)
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        assets = Path(t['_dir']) / 'assets'
        r1 = build(apply_template(sample_deck(t), t), Path(tmp) / 'sample', assets_root=assets if assets.is_dir() else None)
        out['sample'] = {'ok': r1['audit']['ok'], 'slides': r1['slides']}
        if other_deck:
            d = dict(other_deck)
            for k in ('theme', 'animation', 'template', 'theme_overrides'):
                d.pop(k, None)
            r2 = build(apply_template(d, t), Path(tmp) / 'other')
            out['other_content'] = {'ok': r2['audit']['ok'], 'slides': r2['slides'], 'theme': r2['theme']}
    return out

