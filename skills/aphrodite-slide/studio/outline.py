"""Content-first workflow: outline.md (human-editable draft) → lint → approve (baseline) → diff → deck.json scaffold.

outline.md format (Vietnamese or English keys):

    ---
    title: ...
    audience: ...
    purpose: ...
    takeaway: one sentence the audience must remember
    template: academic-defense
    theme: editorial-warm
    language: vi
    density: speaker
    duration_minutes: 12
    ---

    ## 01 · Action title stating what the slide shows
    - layout: chart
    - message: the single point of this slide
    - content:
      - supporting point
    - data: 62% ngủ dưới 7 giờ
    - status: real | estimate | illustrative
    - visual: column chart comparing groups
    - sources: Author (2025); Survey (2026)
    - notes: what the speaker says
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
from pathlib import Path

from . import paths
from .spec import FILLER_VI, FILLER_EN, GENERIC_TITLES, DENSITY_WORDS, DATA_STATUS, NUMERIC_CLAIM, strip_accents

KEYS = {'layout': 'layout', 'bố cục': 'layout', 'bo cuc': 'layout', 'message': 'message', 'thông điệp': 'message', 'thong diep': 'message',
        'content': 'content', 'nội dung': 'content', 'noi dung': 'content', 'data': 'data', 'dữ liệu': 'data', 'du lieu': 'data',
        'status': 'data_status', 'data_status': 'data_status', 'trạng thái': 'data_status', 'trang thai': 'data_status',
        'visual': 'visual', 'trình bày': 'visual', 'hình thức': 'visual', 'hinh thuc': 'visual', 'trinh bay': 'visual',
        'sources': 'sources', 'source': 'sources', 'nguồn': 'sources', 'nguon': 'sources', 'notes': 'notes', 'ghi chú': 'notes',
        'ghi chu': 'notes', 'beat': 'beat', 'vai trò': 'beat'}
STATUS_ALIASES = {'thật': 'real', 'that': 'real', 'thực': 'real', 'thuc': 'real', 'ước tính': 'estimate', 'uoc tinh': 'estimate',
                  'giả định': 'estimate', 'minh họa': 'illustrative', 'minh hoa': 'illustrative', 'demo': 'illustrative'}
HEAD = re.compile(r'^##\s+(\d+[a-z]?)\s*[·.\-:|]\s*(.+?)\s*$')


def parse(text: str) -> dict:
    meta, slides, cur, key = {}, [], None, None
    lines = text.replace('\r\n', '\n').split('\n')
    i = 0
    if lines and lines[0].strip() == '---':
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            if ':' in lines[i]:
                k, v = lines[i].split(':', 1)
                meta[k.strip()] = v.strip()
            i += 1
        i += 1
    for line in lines[i:]:
        m = HEAD.match(line)
        if m:
            cur = {'num': m.group(1), 'title': m.group(2).strip(), 'content': [], 'sources': []}
            slides.append(cur); key = None
            continue
        if line.startswith('# ') and not cur:
            meta.setdefault('takeaway_heading', line[2:].strip())
            continue
        if cur is None:
            continue
        mk = re.match(r'^-\s*([^:]{2,24}):\s*(.*)$', line)
        if mk and mk.group(1).strip().lower() in KEYS:
            key = KEYS[mk.group(1).strip().lower()]
            val = mk.group(2).strip()
            if key == 'sources':
                cur['sources'] = [x.strip() for x in re.split(r';|\s\|\s', val) if x.strip()]
            elif key == 'content':
                if val:
                    cur['content'].append(val)
            elif key == 'data_status':
                v = val.lower()
                cur['data_status'] = STATUS_ALIASES.get(v, v)
            else:
                cur[key] = val
            continue
        sub = re.match(r'^\s{2,}[-*]\s+(.*)$', line)
        if sub and key in ('content', 'sources', 'notes'):
            if key == 'notes':
                cur['notes'] = (cur.get('notes', '') + '\n' + sub.group(1)).strip()
            else:
                cur[key].append(sub.group(1).strip())
            continue
        if line.strip() and key == 'notes':
            cur['notes'] = (cur.get('notes', '') + '\n' + line.strip()).strip()
    for s in slides:
        if 'data' in s and '| status:' in s['data']:
            d, st = s['data'].split('| status:', 1)
            s['data'] = d.strip(); s['data_status'] = STATUS_ALIASES.get(st.strip().lower(), st.strip().lower())
    return {'meta': meta, 'slides': slides}


def load(path: str | Path) -> dict:
    return parse(Path(path).read_text(encoding='utf-8'))


def lint(o: dict) -> dict:
    issues = []
    meta, slides = o['meta'], o['slides']

    def add(sev, sid, code, msg, hint=''):
        issues.append({'severity': sev, 'slide': sid, 'code': code, 'message': msg, 'hint': hint})
    for k in ('title', 'audience', 'purpose', 'takeaway'):
        if not meta.get(k):
            add('warning', 'meta', f'no-{k}', f'front matter is missing "{k}"')
    if not slides:
        add('error', 'meta', 'no-slides', 'no slides found (use "## 01 · Title")')
    density = meta.get('density', 'speaker')
    try:
        mins = float(meta.get('duration_minutes', 0))
    except ValueError:
        mins = 0
    if mins and slides and not (0.5 * mins <= len(slides) <= 1.6 * mins + 2):
        add('warning', 'meta', 'pacing', f'{len(slides)} slides for {mins:g} minutes', 'aim for roughly one slide per minute')
    titles = {}
    cat = paths.catalog()
    for s in slides:
        sid = s['num']
        t = s['title']
        if strip_accents(t).strip(' .') in GENERIC_TITLES and (s.get('layout') or '').split('|')[0] not in ('agenda', 'section', 'closing', 'references', 'cover'):
            add('warning', sid, 'generic-title', f'generic title "{t}"', 'state what the slide shows')
        if re.match(r'^[^:]{2,28}:\s', t):
            add('warning', sid, 'label-title', 'label-like title', 'put the label in eyebrow; title states the finding')
        if t.lower() in titles:
            add('warning', sid, 'duplicate', f'same title as slide {titles[t.lower()]}', 'merge or differentiate')
        titles[t.lower()] = sid
        msg = s.get('message', '')
        if not msg:
            add('error', sid, 'no-message', 'slide has no message', 'write the one point of this slide in one sentence')
        elif len(re.findall(r'[.!?](\s|$)', msg)) >= 2 and len(msg) > 120:
            add('warning', sid, 'two-messages', 'message looks like two points', 'split into two slides')
        if len(s['content']) > 5:
            add('warning', sid, 'too-many-points', f"{len(s['content'])} content points", 'split the slide or move detail to notes')
        words = sum(len(x.split()) for x in s['content']) + len(msg.split())
        if words > DENSITY_WORDS.get(density, 55):
            add('warning', sid, 'dense', f'{words} words planned for {density} density', 'split or move to notes; never shrink fonts')
        lay = (s.get('layout') or '').split('|')[0].strip()
        if lay and not paths.layout_id(lay):
            add('warning', sid, 'layout', f'unknown layout "{lay}"', 'see studio.py layouts')
        if not lay:
            add('warning', sid, 'no-layout', 'no layout proposed')
        blob = ' '.join([t, msg] + s['content']).lower()
        for ph in FILLER_VI + FILLER_EN:
            if ph in blob:
                add('warning', sid, 'filler', f'filler phrase "{ph}"', 'replace with a concrete fact or comparison')
        status = s.get('data_status')
        if status and status not in DATA_STATUS:
            add('error', sid, 'status', f'status must be one of {sorted(DATA_STATUS)}')
        has_data = bool(s.get('data')) or bool(NUMERIC_CLAIM.search(blob))
        if has_data and not s['sources'] and status != 'illustrative':
            add('error', sid, 'unsourced', 'data without source', 'add a source, or mark status: illustrative / estimate with basis')
    errors = sum(x['severity'] == 'error' for x in issues)
    return {'ok': errors == 0, 'slides': len(slides), 'error_count': errors,
            'warning_count': sum(x['severity'] == 'warning' for x in issues), 'issues': issues}


# ----------------------------------------------------------------------------- baseline / diff

def _slide_hash(s: dict) -> str:
    keys = ('title', 'layout', 'message', 'content', 'data', 'data_status', 'visual', 'sources')
    return hashlib.sha1(json.dumps({k: s.get(k) for k in keys}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def _baseline_path(outline_path: Path) -> Path:
    return outline_path.parent / '.aphrodite' / (outline_path.stem + '.baseline.json')


def approve(outline_path: str | Path, note: str = '') -> dict:
    p = Path(outline_path)
    text = p.read_text(encoding='utf-8')
    o = parse(text)
    rep = lint(o)
    base = {'approved_at': _dt.datetime.now().isoformat(timespec='seconds'), 'note': note, 'file': p.name,
            'sha1': hashlib.sha1(text.encode()).hexdigest(), 'meta': o['meta'],
            'slides': [{'num': s['num'], 'title': s['title'], 'hash': _slide_hash(s), 'data': s} for s in o['slides']],
            'lint_errors': rep['error_count']}
    bp = _baseline_path(p)
    bp.parent.mkdir(exist_ok=True)
    if bp.exists():  # keep history, never silently overwrite an approval
        old = json.loads(bp.read_text(encoding='utf-8'))
        hist = bp.parent / (p.stem + f".baseline.{old['approved_at'].replace(':', '')}.json")
        hist.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding='utf-8')
    bp.write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding='utf-8')
    return {'baseline': str(bp), 'slides': len(o['slides']), 'lint': rep}


def diff(outline_path: str | Path) -> dict:
    p = Path(outline_path)
    bp = _baseline_path(p)
    if not bp.exists():
        return {'approved': False, 'message': 'No baseline yet: run `studio.py outline approve` after the user approves the draft.'}
    base = json.loads(bp.read_text(encoding='utf-8'))
    cur = parse(p.read_text(encoding='utf-8'))
    old = {b['num']: b for b in base['slides']}
    new = {s['num']: s for s in cur['slides']}
    changed, added, removed = [], [], []
    for num, s in new.items():
        if num not in old:
            added.append({'num': num, 'title': s['title']})
        elif _slide_hash(s) != old[num]['hash']:
            fields = [k for k in ('title', 'layout', 'message', 'content', 'data', 'data_status', 'visual', 'sources')
                      if s.get(k) != old[num]['data'].get(k)]
            major = bool({'message', 'title', 'data'} & set(fields))
            changed.append({'num': num, 'title': s['title'], 'fields': fields, 'major': major})
    for num, b in old.items():
        if num not in new:
            removed.append({'num': num, 'title': b['title']})
    return {'approved': True, 'approved_at': base['approved_at'], 'unchanged': len(new) - len(changed) - len(added),
            'changed': changed, 'added': added, 'removed': removed,
            'major_change': any(c['major'] for c in changed) or bool(added or removed)}


def guard(deck: dict, outline_path: str | Path) -> list[dict]:
    """Warn when deck.json drifts from the approved outline (titles/order) - prevents silent rewrites."""
    bp = _baseline_path(Path(outline_path))
    if not bp.exists():
        return [{'severity': 'warning', 'slide': 'deck', 'code': 'no-baseline', 'message': 'outline not approved yet', 'hint': 'run outline approve'}]
    base = json.loads(bp.read_text(encoding='utf-8'))
    approved = [strip_accents(b['title']).replace('*', '').strip() for b in base['slides']]
    issues = []
    for s in deck.get('slides', []):
        t = strip_accents(s.get('title') or s.get('term') or s.get('quote') or '').replace('*', '').strip()
        if t and t not in approved and (s.get('layout') or s.get('type')) not in ('statement',):
            issues.append({'severity': 'warning', 'slide': s.get('id'), 'code': 'off-baseline',
                           'message': f'title not in approved outline: "{t[:60]}"', 'hint': 'declare the change to the user or restore the approved wording'})
    if len(deck.get('slides', [])) != len(approved):
        issues.append({'severity': 'warning', 'slide': 'deck', 'code': 'slide-count', 'message': f"{len(deck.get('slides', []))} slides vs {len(approved)} approved"})
    return issues


# ----------------------------------------------------------------------------- scaffolds

def scaffold_outline(template: dict, meta: dict | None = None) -> str:
    meta = meta or {}
    lines = ['---', f"title: {meta.get('title', '')}", f"audience: {meta.get('audience', '')}", f"purpose: {meta.get('purpose', '')}",
             f"takeaway: {meta.get('takeaway', '')}", f"template: {template['id']}", f"theme: {template.get('default_theme')}",
             f"language: {meta.get('language', 'vi')}", f"density: {template.get('density', 'speaker')}",
             f"duration_minutes: {meta.get('duration_minutes', len(template.get('storyline', [])))}", '---', '']
    for i, b in enumerate(template.get('storyline', []), 1):
        lines += [f"## {i:02d} · <tiêu đề nói điều slide chứng minh>", f"- layout: {b['layout']}", f"- beat: {b['beat']}",
                  f"- message: <{b.get('purpose', '')}>", '- content:', '  - <ý hỗ trợ>', '- data:', '- status:', '- visual:', '- sources:',
                  '- notes:', '']
    return '\n'.join(lines)


def _slug(text: str, used: set) -> str:
    base = re.sub(r'[^a-z0-9]+', '-', strip_accents(text))[:32].strip('-') or 'slide'
    sid, k = base, 2
    while sid in used:
        sid = f'{base}-{k}'; k += 1
    used.add(sid)
    return sid


def _split_item(text: str):
    for sep in (' — ', ' – ', ': ', ' | '):
        if sep in text:
            a, b = text.split(sep, 1)
            return a.strip(), b.strip()
    return text.strip(), ''


def to_spec(o: dict) -> dict:
    """Deterministic first draft of deck.json from an approved outline. The agent then completes layout-specific fields
    (chart data, comparison sides...) and `validate` lists anything still missing."""
    meta = o['meta']
    deck = {k: meta[k] for k in ('title', 'audience', 'purpose', 'takeaway', 'template', 'theme', 'language', 'density', 'brand') if meta.get(k)}
    if meta.get('duration_minutes'):
        try:
            deck['duration_minutes'] = float(meta['duration_minutes'])
        except ValueError:
            pass
    used, slides = set(), []
    for s in o['slides']:
        lay = paths.layout_id((s.get('layout') or 'statement').split('|')[0].strip()) or 'statement'
        c = s['content']
        sl = {'id': _slug(s['title'], used), 'layout': lay, 'title': s['title']}
        if s.get('beat'):
            sl['beat'] = s['beat']
        msg = s.get('message', '')
        if lay in ('cover', 'section', 'closing'):
            sl['subtitle'] = msg
            if c and lay in ('cover', 'closing'):
                sl['meta'] = c
        elif lay == 'statement':
            sl['title'] = msg or s['title']
            sl['eyebrow'] = s['title'] if msg else ''
        elif lay in ('key-takeaways',):
            sl['bullets'] = c
        elif lay in ('learning-objectives', 'references'):
            sl['items'] = c
        elif lay == 'agenda':
            sl['items'] = [dict(zip(('title', 'detail'), _split_item(x))) for x in c]
        elif lay == 'cards':
            sl['items'] = [{'title': a, 'body': b} for a, b in map(_split_item, c)]
        elif lay in ('process',):
            sl['steps'] = [{'title': a, 'detail': b} for a, b in map(_split_item, c)]
        elif lay == 'methodology':
            sl['steps'] = [{'title': a, 'detail': b} for a, b in map(_split_item, c)]
        elif lay == 'timeline':
            sl['items'] = []
            for x in c:
                a, b = _split_item(x)
                t2, d2 = _split_item(b) if b else (b, '')
                sl['items'].append({'date': a, 'title': t2, 'detail': d2})
        elif lay in ('metrics', 'kpi-dashboard'):
            sl['items'] = [{'value': a, 'label': b} for a, b in map(_split_item, c)]
        elif lay == 'diagram':
            sl['nodes'] = [{'title': a, 'detail': b} for a, b in map(_split_item, c)]
        elif lay == 'evidence-levels':
            sl['levels'] = [{'label': a, 'detail': b} for a, b in map(_split_item, c)]
        elif lay == 'definition':
            sl['term'] = s['title']; sl['definition'] = msg
            if c:
                sl['example'] = c[0]
            sl.pop('title', None)
        elif lay == 'quote':
            sl['quote'] = c[0] if c else msg
            sl['attribution'] = c[1] if len(c) > 1 else ''
        elif lay in ('problem-solution',):
            half = max(1, len(c) // 2)
            sl['problem'] = {'points': c[:half]}; sl['solution'] = {'points': c[half:]}
        elif lay == 'comparison':
            half = max(1, len(c) // 2)
            sl['left'] = {'title': 'A', 'bullets': c[:half]}; sl['right'] = {'title': 'B', 'bullets': c[half:]}
        elif lay == 'chart':
            sl['chart'] = {'type': 'column', 'categories': [], 'series': [{'name': '', 'values': []}]}
            sl['_todo'] = 'fill chart.categories/series from the approved data: ' + (s.get('data') or '')
            if c:
                sl['insights'] = c[:3]
        elif lay in ('image-split', 'full-bleed-image'):
            sl['subtitle'] = msg
            sl['image'] = ''
            sl['_todo'] = 'add a local licence-cleared image under assets/'
            if c and lay == 'image-split':
                sl['bullets'] = c
        elif lay == 'case':
            sl['body'] = msg
            sl['value'] = (s.get('data') or '').split(' ')[0]
        elif lay == 'table':
            sl['columns'], sl['rows'] = [], []
            sl['_todo'] = 'fill columns/rows'
        if msg and lay not in ('cover', 'section', 'closing', 'statement', 'definition', 'case', 'image-split', 'full-bleed-image') and 'subtitle' not in sl:
            sl['subtitle'] = msg if len(msg) <= 140 else ''
        if s['sources']:
            sl['sources'] = s['sources']
        if s.get('data_status'):
            sl['data_status'] = s['data_status']
        notes = s.get('notes', '')
        if s.get('visual'):
            notes = (notes + '\n[visual] ' + s['visual']).strip()
        if notes:
            sl['notes'] = notes
        slides.append(sl)
    deck['slides'] = slides
    return deck

