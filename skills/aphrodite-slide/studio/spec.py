"""Deck spec v2: loading, v1 compatibility, theme resolution and content validation.

The deck spec is the single source of truth shared by every renderer (HTML, PPTX, PDF/PNG).
Content lives in the spec; geometry, typography and colour live in themes/layouts.
"""
from __future__ import annotations

import copy
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from . import paths

DATA_STATUS = {'real', 'estimate', 'illustrative'}
DENSITY_WORDS = {'speaker': 55, 'reading': 120}

FILLER_VI = ['hãy cùng', 'khám phá', 'đột phá', 'toàn diện', 'vượt trội', 'kỷ nguyên mới', 'hành trình', 'không chỉ',
             'thay đổi cuộc chơi', 'tối ưu hóa mọi', 'giải pháp hoàn hảo', 'mở ra cánh cửa', 'trong thời đại', 'ngày càng phát triển']
FILLER_EN = ['unlock', 'seamless', 'game-changer', 'game changer', 'revolutionize', 'cutting-edge', 'next-level', "let's dive",
             'delve', 'in today\'s fast-paced', 'harness the power', 'leverage synergies', 'world-class', 'paradigm shift']
GENERIC_TITLES = {'gioi thieu', 'tong quan', 'noi dung', 'ket luan', 'ket qua', 'phuong phap', 'du lieu', 'van de',
                  'introduction', 'overview', 'conclusion', 'results', 'method', 'methods', 'data', 'problem', 'background',
                  'boi canh', 'muc tieu', 'objectives', 'summary', 'tom tat'}
ALLOW_GENERIC = {'agenda', 'section', 'closing', 'references', 'cover', 'learning-objectives', 'definition', 'quote'}
NUMERIC_CLAIM = re.compile(r'\d+(?:[.,]\d+)*\s?(?:%|‰|triệu|tỷ|nghìn|ngàn|million|billion|thousand|usd|vnd|đồng|lần|x\b)', re.I)
PLACEHOLDER_SOURCES = {'source', 'nguồn', 'tbd', 'placeholder', 'todo', 'n/a', '?', 'xxx'}


def strip_accents(text: str) -> str:
    text = unicodedata.normalize('NFD', str(text)).replace('đ', 'd').replace('Đ', 'D')
    return ''.join(c for c in text if not unicodedata.combining(c)).lower()


# --------------------------------------------------------------------------- loading

def load_deck(path: str | Path) -> dict:
    path = Path(path)
    raw = path.read_text(encoding='utf-8')
    if path.suffix.lower() in ('.yaml', '.yml'):
        try:
            import yaml
        except ImportError as ex:
            raise RuntimeError('Install PyYAML for YAML decks (pip install pyyaml); JSON needs no dependency.') from ex
        data = yaml.safe_load(raw)
    else:
        data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('Deck root must be an object')
    return data


def normalize(deck: dict) -> dict:
    """Return a v2 deck. Accepts v1 decks (type/columns/summary/data/chart_type/illustrative)."""
    d = copy.deepcopy(deck)
    d = {k: unicodedata.normalize('NFC', v) if isinstance(v, str) else v for k, v in d.items()}
    d['spec_version'] = 2
    d.setdefault('language', 'vi')
    d['theme'] = resolve_theme_id(d.get('theme') or paths.profile().get('default_theme', 'editorial-warm'))
    d.setdefault('animation', paths.profile().get('animation', 'professional'))
    slides = d.get('slides') or []
    out = []
    for i, s in enumerate(slides, 1):
        if not isinstance(s, dict):
            out.append(s); continue
        s = _nfc(s)
        raw_layout = s.pop('type', None) if 'layout' not in s else s.get('layout')
        s['layout'] = paths.layout_id(raw_layout) or raw_layout
        s.setdefault('id', f's{i:02d}')
        if s.get('illustrative') is True and not s.get('data_status'):
            s['data_status'] = 'illustrative'
        if d.get('demo') and not s.get('data_status'):
            s['data_status'] = 'illustrative'
        lay = s['layout']
        if lay == 'cards':
            for it in s.get('items', []) or []:
                if isinstance(it, dict) and 'body' not in it:
                    it['body'] = it.get('detail') or it.get('description') or ''
        if lay == 'chart' and 'chart' not in s and 'data' in s:
            rows = s.get('data') or []
            kind = s.get('chart_type', 'bar')
            s['chart'] = {'type': {'bar': 'column'}.get(kind, kind),
                          'categories': [str(r.get('label', '')) for r in rows],
                          'series': [{'name': s.get('series_name', ''), 'values': [_num(r.get('value')) for r in rows]}]}
        if lay == 'process' and 'steps' not in s and 'items' in s:
            s['steps'] = s['items']
        out.append(s)
    d['slides'] = out
    return d


def _nfc(obj):
    if isinstance(obj, str):
        return unicodedata.normalize('NFC', obj)
    if isinstance(obj, list):
        return [_nfc(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _nfc(v) for k, v in obj.items()}
    return obj


def _num(v):
    try:
        return float(str(v).replace(',', '.')) if not isinstance(v, (int, float)) else v
    except ValueError:
        return 0


# --------------------------------------------------------------------------- themes

def theme_dirs(extra: list[Path] | None = None) -> list[Path]:
    dirs = list(extra or [])
    dirs += [paths.user_home() / 'themes', paths.THEMES]
    return dirs


def resolve_theme_id(name: str) -> str:
    aliases = paths.read_json(paths.THEMES / 'aliases.json')
    return aliases.get(name, name)


def load_theme(name: str, extra_dirs: list[Path] | None = None, overrides: dict | None = None) -> dict:
    name = resolve_theme_id(name)
    for base in theme_dirs(extra_dirs):
        p = Path(base) / f'{name}.json'
        if p.exists():
            theme = paths.read_json(p)
            theme.setdefault('id', name)
            theme['_path'] = str(p)
            return deep_merge(theme, overrides or {})
    raise ValueError(f'Unknown theme {name!r}. Run `studio.py themes` to list available themes.')


def list_themes(extra_dirs=None) -> list[dict]:
    seen, out = set(), []
    for base in theme_dirs(extra_dirs):
        for p in sorted(Path(base).glob('*.json')) if Path(base).exists() else []:
            if p.stem == 'aliases' or p.stem in seen:
                continue
            seen.add(p.stem)
            t = paths.read_json(p)
            out.append({'id': p.stem, 'name': t.get('name', p.stem), 'scheme': t.get('scheme'), 'tags': t.get('tags', []),
                        'scope': 'user' if paths.user_home() in p.parents else 'repo', 'description': t.get('description', '')})
    return out


def deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


# --------------------------------------------------------------------------- fonts

@lru_cache(maxsize=1)
def _coverage() -> dict:
    p = paths.FONTS / 'coverage.json'
    user = paths.user_home() / 'fonts' / 'coverage.json'
    data = paths.read_json(p) if p.exists() else {}
    if user.exists():
        data.update(paths.read_json(user))
    return data


def missing_glyphs(text: str, family: str) -> set[str] | None:
    """Characters in text that the bundled font cannot draw. None = font not bundled (unknown)."""
    ranges = _coverage().get(family)
    if ranges is None:
        return None
    missing = set()
    for ch in set(text):
        cp = ord(ch)
        if cp < 32 or ch in '\n\t' or unicodedata.category(ch).startswith('Z') and cp != 0x20 and cp != 0xA0:
            continue
        if not any(a <= cp <= b for a, b in ranges):
            missing.add(ch)
    return missing


# --------------------------------------------------------------------------- text helpers

def slide_texts(slide: dict, include_notes: bool = False) -> list[str]:
    skip = {'id', 'layout', 'image', 'icon', 'data_status', 'animation', 'build', 'side', 'variant', 'status', 'state',
            'beat', 'style', 'tone', 'highlight', 'type', 'notes' if not include_notes else '__none__'}
    out = []

    def walk(v, key=None):
        if key in skip:
            return
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, (int, float)) and not isinstance(v, bool) and key not in ('values',):
            out.append(str(v))
        elif isinstance(v, list):
            for x in v:
                walk(x, key)
        elif isinstance(v, dict):
            for k, x in v.items():
                walk(x, k)
    walk(slide)
    return out


def word_count(slide: dict) -> int:
    body = dict(slide)
    for k in ('sources', 'notes', 'eyebrow', 'image_credit'):
        body.pop(k, None)
    return sum(len(t.split()) for t in slide_texts(body))


# --------------------------------------------------------------------------- validation

def audit(deck: dict, strict: bool = False, assets_root: Path | None = None, theme: dict | None = None) -> dict:
    """Content + capacity + evidence + glyph checks. Returns {ok, issues[], ...}."""
    d = normalize(deck)
    issues = []

    def issue(sev, sid, code, msg, hint=''):
        issues.append({'severity': sev, 'slide': sid, 'code': code, 'message': msg, 'hint': hint})

    cat = paths.catalog()['layouts']
    slides = d.get('slides')
    if not isinstance(slides, list) or not slides:
        issue('error', 'deck', 'no-slides', 'slides must be a non-empty list'); slides = []
    if not d.get('title'):
        issue('error', 'deck', 'no-title', 'deck title is required')
    for key in ('audience', 'takeaway'):
        if not d.get(key):
            issue('warning', 'deck', f'no-{key}', f'{key} is not specified')
    if d.get('language') not in ('vi', 'en', 'bilingual'):
        issue('warning', 'deck', 'language', 'language should be vi, en or bilingual')
    density = d.get('density') or 'speaker'
    if theme is None:
        try:
            theme = load_theme(d['theme'], overrides=d.get('theme_overrides'))
        except ValueError as ex:
            issue('error', 'deck', 'theme', str(ex)); theme = None

    ids, prev_layouts = set(), []
    for i, s in enumerate(slides, 1):
        if not isinstance(s, dict):
            issue('error', str(i), 'slide-type', 'slide must be an object'); continue
        sid = str(s.get('id'))
        if sid in ids:
            issue('error', sid, 'duplicate-id', 'duplicate slide id')
        ids.add(sid)
        lay = s.get('layout')
        spec = cat.get(lay)
        if not spec:
            issue('error', sid, 'layout', f'unsupported layout {lay!r}', 'see assets/layouts/catalog.json'); continue
        for f in spec['required']:
            if not s.get(f):
                issue('error', sid, 'required', f'{lay} requires "{f}"')
        _capacity(s, lay, spec, sid, issue)
        title = str(s.get('title') or s.get('term') or s.get('quote') or '')
        if re.match(r'^[^:]{2,28}:\s', title):
            issue('warning', sid, 'label-title', 'label-like title ("Nhãn: câu")', 'move the label to eyebrow; title states the finding')
        if lay not in ALLOW_GENERIC and strip_accents(title).strip(' .') in GENERIC_TITLES:
            issue('warning', sid, 'generic-title', f'generic title "{title}"', 'write what the slide shows or proves')
        blob = ' '.join(slide_texts(s)).lower()
        for ph in FILLER_VI + FILLER_EN:
            if ph in blob:
                issue('warning', sid, 'filler', f'filler phrase "{ph}"', 'replace with a number or concrete comparison')
        words = word_count(s)
        limit = DENSITY_WORDS.get(s.get('density', density), 55)
        if words > limit and lay not in ('references', 'table'):
            issue('warning', sid, 'dense', f'{words} words on slide (limit {limit} for {density} density)',
                  'split into two slides or move explanation to notes')
        status = s.get('data_status')
        if status and status not in DATA_STATUS:
            issue('error', sid, 'data-status', f'data_status must be one of {sorted(DATA_STATUS)}')
        numeric = spec.get('numeric') or bool(NUMERIC_CLAIM.search(' '.join(slide_texts({k: v for k, v in s.items() if k not in ('sources', 'notes')}))))
        if numeric and not s.get('sources') and status != 'illustrative' and not d.get('demo'):
            issue('error' if strict else 'warning', sid, 'unsourced-number', 'numeric claim needs sources or data_status="illustrative"',
                  'never invent sources; mark sample data as illustrative')
        if status == 'estimate' and not s.get('sources') and not s.get('notes'):
            issue('warning', sid, 'estimate-basis', 'estimate without basis', 'state the assumption in notes or sources')
        for src in s.get('sources', []) or []:
            if isinstance(src, str) and src.strip().lower() in PLACEHOLDER_SOURCES:
                issue('error' if strict else 'warning', sid, 'placeholder-source', f'placeholder source "{src}"')
        for key in ('image',):
            if s.get(key):
                try:
                    safe_local_image(s[key])
                    if assets_root and not (Path(assets_root) / s[key]).is_file():
                        issue('error', sid, 'image-missing', f'image not found: {s[key]}')
                except ValueError as ex:
                    issue('error', sid, 'image-path', str(ex))
        if s.get('image') and not s.get('image_alt'):
            issue('warning', sid, 'image-alt', 'image has no image_alt text')
        if lay == 'chart':
            _check_chart(s.get('chart') or {}, sid, issue)
        if lay == 'table':
            cols = s.get('columns') or []
            for r in s.get('rows') or []:
                if len(r) != len(cols):
                    issue('error', sid, 'table-shape', 'every row must have one cell per column'); break
        prev_layouts.append(lay)
        if len(prev_layouts) >= 3 and len(set(prev_layouts[-3:])) == 1 and lay not in ('section',):
            issue('warning', sid, 'repeat-layout', f'layout "{lay}" used 3 times in a row', 'vary the visual form')
        if theme:
            text = ' '.join(slide_texts(s))
            for role in ('display', 'body'):
                fam = theme['fonts'][role]
                miss = missing_glyphs(text, fam)
                if miss is None:
                    issue('warning', sid, 'font-unverified', f'font "{fam}" is not bundled; glyph coverage unverified')
                elif miss:
                    issue('error', sid, 'missing-glyph', f'font "{fam}" cannot draw: {"".join(sorted(miss))}',
                          'choose a theme/font that covers these characters')
    errors = sum(x['severity'] == 'error' for x in issues)
    return {'slide_count': len(slides), 'issue_count': len(issues), 'error_count': errors,
            'warning_count': sum(x['severity'] == 'warning' for x in issues), 'issues': issues, 'ok': errors == 0}


def _capacity(s, lay, spec, sid, issue):
    lim = spec.get('limits', {})
    list_keys = {'items': 'items', 'steps': 'steps', 'levels': 'levels', 'nodes': 'nodes', 'bullets': 'bullets',
                 'facts': 'facts', 'insights': 'insights', 'meta': 'meta', 'columns': 'columns', 'rows': 'rows'}
    for key, lk in list_keys.items():
        if key in lim and isinstance(s.get(lk), list):
            rng = lim[key]
            lo, hi = (rng if isinstance(rng, list) else [0, rng])
            n = len(s[lk])
            if n > hi:
                issue('warning', sid, 'capacity', f'{lay}: {n} {key} (max {hi})', 'split the slide; do not shrink text')
            if n < lo:
                issue('warning', sid, 'capacity', f'{lay}: {n} {key} (min {lo})', 'use another layout')
    checks = {'title': [s.get('title')], 'subtitle': [s.get('subtitle')], 'term': [s.get('term')],
              'definition': [s.get('definition')], 'example': [s.get('example')], 'quote': [s.get('quote')],
              'verdict': [s.get('verdict')], 'body': [s.get('body')], 'value': [s.get('value')]}
    for coll in ('items', 'steps', 'levels', 'nodes'):
        for it in s.get(coll) or []:
            if isinstance(it, dict):
                for k, v in it.items():
                    checks.setdefault({'title': 'item_title', 'detail': 'item_detail', 'body': 'item_body'}.get(k, k), []).append(v)
                    if coll == 'steps':
                        checks.setdefault({'title': 'step_title', 'detail': 'step_detail'}.get(k, k), []).append(v)
                    if coll in ('nodes',):
                        checks.setdefault({'title': 'node_title', 'detail': 'node_detail'}.get(k, k), []).append(v)
            elif isinstance(it, str):
                checks.setdefault('item', []).append(it)
    for b in s.get('bullets') or []:
        checks.setdefault('bullet', []).append(b)
    for side in ('left', 'right', 'problem', 'solution'):
        for b in (s.get(side) or {}).get('bullets', []) + (s.get(side) or {}).get('points', []):
            checks.setdefault('bullet', []).append(b); checks.setdefault('point', []).append(b)
    for ins in s.get('insights') or []:
        checks.setdefault('insight', []).append(ins)
    for key, vals in checks.items():
        if key in lim and not isinstance(lim[key], list):
            for v in vals:
                if isinstance(v, str) and len(v) > lim[key]:
                    issue('warning', sid, 'too-long', f'{key} is {len(v)} chars (max {lim[key]}): "{v[:50]}…"',
                          'shorten or move detail to notes')


def _check_chart(ch, sid, issue):
    kinds = {'bar', 'column', 'line', 'stacked', 'donut'}
    if ch.get('type') not in kinds:
        issue('error', sid, 'chart-type', f'chart.type must be one of {sorted(kinds)}')
    cats = ch.get('categories') or []
    series = ch.get('series') or []
    if not cats or not series:
        issue('error', sid, 'chart-data', 'chart needs categories and series'); return
    for se in series:
        vals = se.get('values') or []
        if len(vals) != len(cats):
            issue('error', sid, 'chart-shape', f'series "{se.get("name", "")}" has {len(vals)} values for {len(cats)} categories')
        if any(not isinstance(v, (int, float)) for v in vals):
            issue('error', sid, 'chart-values', 'chart values must be numbers')
    if ch.get('type') == 'donut' and (len(series) != 1 or any((v or 0) < 0 for v in series[0].get('values', []))):
        issue('error', sid, 'chart-donut', 'donut needs exactly one series of non-negative values')
    if ch.get('type') == 'donut' and len(cats) > 6:
        issue('warning', sid, 'chart-donut', 'donut with more than 6 parts is hard to read; use a bar chart')
    if ch.get('type') in ('bar', 'column') and any(v < 0 for se in series for v in se.get('values', []) if isinstance(v, (int, float))):
        issue('warning', sid, 'chart-negative', 'negative values: check the zero baseline is meaningful')


def safe_local_image(value) -> str:
    """Images must be relative paths inside the deck's assets/ directory (no URLs, no traversal)."""
    p = str(value or '')
    if not p or p.startswith(('/', '\\')) or '\\' in p or '..' in Path(p).parts or ':' in p or '?' in p or '#' in p:
        raise ValueError('Images must use safe relative paths inside the deck assets directory')
    if not p.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
        raise ValueError('Unsupported image extension')
    return p

