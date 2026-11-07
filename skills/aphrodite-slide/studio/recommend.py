"""Smart template recommendation: deterministic metadata scoring with human-readable reasons.

The agent extracts what it knows (brief text, audience, purpose, density, tone) and calls
`studio.py recommend`; the script ranks templates from the registry, never at random.
"""
from __future__ import annotations

import re

from . import paths
from .registry import list_templates
from .spec import strip_accents

# Extra synonyms per use case (accent-insensitive). Templates contribute their own tags on top.
SYNONYMS = {
    'academic': ['luan van', 'luan an', 'khoa luan', 'do an', 'bao ve', 'hoi dong', 'nghien cuu', 'de tai', 'hoi thao', 'thesis',
                 'dissertation', 'capstone', 'defense', 'defence', 'research', 'paper', 'conference', 'journal', 'nckh'],
    'education': ['bai giang', 'giang day', 'lop hoc', 'hoc sinh', 'sinh vien', 'mon hoc', 'tiet hoc', 'giao an', 'dao tao', 'tap huan',
                  'lecture', 'lesson', 'teaching', 'course', 'class', 'training', 'workshop', 'tutorial', 'students', 'learners'],
    'medical': ['y te', 'suc khoe', 'benh', 'benh vien', 'bac si', 'dieu duong', 'duoc', 'lam sang', 'dich te', 'phong benh', 'dieu tri',
                'chan doan', 'nguoi benh', 'tiem chung', 'vaccine', 'medical', 'health', 'clinical', 'patient', 'disease', 'hospital', 'nursing'],
    'technology': ['san pham', 'cong nghe', 'phan mem', 'ung dung', 'app', ' ai ', 'nen tang', 'ra mat', 'demo', 'startup', 'saas', 'he thong',
                   'product', 'launch', 'software', 'platform', 'feature', 'tech', 'api', 'cloud', 'machine learning', 'chatbot'],
    'business': ['kinh doanh', 'doanh thu', 'loi nhuan', 'kpi', 'bao cao quy', 'bao cao thang', 'ban giam doc', 'chien luoc', 'ngan sach',
                 'van hanh', 'logistics', 'tai chinh', 'business', 'revenue', 'quarterly', 'executive', 'board', 'budget', 'sales', 'finance'],
}
USECASE_OF = {'academic': ['academic', 'research', 'thesis', 'defense'], 'education': ['education', 'teaching', 'training', 'workshop'],
              'medical': ['medical', 'healthcare', 'health-education', 'clinical'], 'technology': ['technology', 'product', 'demo', 'startup'],
              'business': ['business', 'corporate', 'finance', 'operations']}


def _norm(text: str) -> str:
    return ' ' + re.sub(r'\s+', ' ', strip_accents(text or '')) + ' '


def detect_use_cases(brief: str) -> dict[str, int]:
    b = _norm(brief)
    hits = {}
    for uc, words in SYNONYMS.items():
        n = sum(1 for w in words if (' ' + w.strip() + ' ' if len(w.strip()) <= 3 else w) in b)
        if n:
            hits[uc] = n
    return hits


def recommend(brief: str = '', use_case: str | None = None, audience: str = '', density: str | None = None,
              formality: str | None = None, scheme: str | None = None, top: int = 3) -> dict:
    prof = paths.profile()
    b = _norm(' '.join([brief, audience, use_case or '']))
    detected = detect_use_cases(' '.join([brief, audience, use_case or '']))
    liked = set(prof.get('liked_themes', []))
    results = []
    for t in list_templates():
        score, reasons = 0.0, []
        ucs = set(t.get('use_cases', []))
        if use_case and use_case in ucs:
            score += 40; reasons.append(f'use case "{use_case}" khớp')
        for uc, n in detected.items():
            if ucs & set(USECASE_OF.get(uc, [uc])):
                pts = min(36, 12 + 6 * n)
                score += pts; reasons.append(f'nhận diện nhóm "{uc}" từ {n} từ khóa')
        tag_hits = [tag for tag in t.get('tags', []) if len(strip_accents(tag)) > 2 and _norm(tag).strip() in b]
        if tag_hits:
            score += min(24, 4 * len(tag_hits)); reasons.append('từ khóa: ' + ', '.join(tag_hits[:5]))
        aud_hits = [a for a in t.get('audience', []) if _norm(a).strip() in b]
        if aud_hits:
            score += min(12, 6 * len(aud_hits)); reasons.append('đối tượng: ' + ', '.join(aud_hits[:3]))
        if density and t.get('density') == density:
            score += 6; reasons.append(f'mật độ {density}')
        if formality and t.get('formality') == formality:
            score += 6; reasons.append(f'mức trang trọng {formality}')
        if scheme:
            from .spec import load_theme
            try:
                if load_theme(t['default_theme']).get('scheme') == scheme:
                    score += 4; reasons.append(f'nền {scheme}')
            except ValueError:
                pass
        if t.get('default_theme') in liked:
            score += 3; reasons.append('theme nằm trong phong cách anh thích')
        if t.get('scope') == 'user':
            score += 2; reasons.append('template cá nhân')
        results.append({'id': t['id'], 'name': t.get('name'), 'name_vi': t.get('name_vi'), 'version': t.get('version'), 'scope': t['scope'],
                        'score': round(score, 1), 'reasons': reasons, 'best_for': t.get('best_for'), 'default_theme': t.get('default_theme'),
                        'compatible_themes': t.get('compatible_themes', []), 'animation': t.get('animation'),
                        'density': t.get('density'), 'signature_layouts': t.get('signature_layouts', []),
                        'storyline': [x['beat'] for x in t.get('storyline', [])], 'preview': t.get('preview_path')})
    results.sort(key=lambda r: (-r['score'], r['id']))
    if results and results[0]['score'] < 10:
        order = prof.get('preferred_use_cases', [])
        results.sort(key=lambda r: next((i for i, uc in enumerate(order) if set(USECASE_OF.get(uc, [uc])) & set(
            next((t.get('use_cases', []) for t in list_templates() if t['id'] == r['id']), []))), 99))
    top_list = results[:top]
    best = top_list[0] if top_list else None
    confident = bool(best and best['score'] >= 30 and (len(results) < 2 or best['score'] - results[1]['score'] >= 10))
    # Visual options shown to the user (each with a real rendered preview):
    # clear match -> the matched template in its compatible themes; otherwise the top templates in their default themes.
    options = []
    if confident:
        t = next(x for x in list_templates() if x['id'] == best['id'])
        for th in (t.get('compatible_themes') or [t['default_theme']])[:3]:
            options.append(_option(t, th, 'recommended' if th == t['default_theme'] else 'alternative-theme'))
        for r in results[1:]:
            if len(options) >= 3:
                break
            tt = next(x for x in list_templates() if x['id'] == r['id'])
            options.append(_option(tt, tt['default_theme'], 'alternative-template'))
    else:
        for r in top_list:
            tt = next(x for x in list_templates() if x['id'] == r['id'])
            options.append(_option(tt, tt['default_theme'], 'candidate'))
    return {'detected_use_cases': detected, 'recommendations': top_list, 'recommended': best['id'] if best else None,
            'confident': confident, 'options': options,
            'custom_option': {'id': 'custom', 'label_vi': 'Tôi muốn thiết kế một phong cách mới',
                              'label_en': 'Design a new style', 'how': 'studio.py theme new + studio.py preview (see references/CUSTOM_DESIGN.md)'}}


def _option(t: dict, theme: str, role: str) -> dict:
    from pathlib import Path
    p = Path(t['_dir']) / 'previews' / f'{theme}.jpg'
    if not p.exists() and theme == t.get('default_theme') and t.get('preview_path'):
        p = Path(t['preview_path'])
    return {'template': t['id'], 'theme': theme, 'role': role, 'animation': t.get('animation'),
            'preview': str(p) if p.exists() else None}
