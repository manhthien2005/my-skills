"""Visual QA: turn render probes into a severity-ranked report (qa-report.json + qa-report.md).

Automated checks never replace looking at the slides. The report says so, and the agent must open
contact-sheet.jpg and the individual previews before calling a deck finished.
"""
from __future__ import annotations

import json
from pathlib import Path

CONTENT_LAYOUTS = {'agenda', 'metrics', 'kpi-dashboard', 'cards', 'process', 'timeline', 'comparison', 'table', 'chart',
                   'evidence-levels', 'problem-solution', 'methodology', 'diagram', 'learning-objectives', 'key-takeaways'}


def evaluate(render: dict, content: dict | None = None, folder: Path | None = None) -> dict:
    slides = []
    totals = {'error': 0, 'warning': 0}

    def add(lst, sev, code, msg):
        lst.append({'severity': sev, 'code': code, 'message': msg})
        totals[sev] += 1

    for s in render.get('slides', []):
        iss = []
        for o in s['overflow']:
            add(iss, 'error', 'outside-slide', f"{o['el']} extends beyond the 16:9 frame: \"{o['text']}\"")
        for o in s['clipped']:
            add(iss, 'error', 'text-clipped', f"text clipped inside {o['el']}: \"{o['text']}\"")
        for o in s['footer']:
            add(iss, 'error', 'footer-collision', f"content touches the footer: \"{o['text']}\"")
        for o in s['overlap']:
            add(iss, 'error', 'overlap', f"overlapping text: {o['a']} × {o['b']}")
        for o in s['small_text']:
            add(iss, 'error', 'text-too-small', f"{o['size']}px text (min 16): \"{o['text']}\"")
        for o in s['contrast']:
            sev = 'error' if o['ratio'] < o['need'] * 0.85 else 'warning'
            add(iss, sev, 'low-contrast', f"contrast {o['ratio']}:1 < {o['need']}:1 ({o['size']}px) \"{o['text']}\"")
        for src in s['images']:
            add(iss, 'error', 'broken-image', f'image failed to load: {src}')
        for t in s['orphans']:
            add(iss, 'warning', 'orphan-word', f'headline ends with a lone short line: "{t}"')
        fill = s.get('fill')
        if fill is not None and s['layout'] in CONTENT_LAYOUTS and fill < 0.5:
            add(iss, 'warning', 'empty-space', f'content uses {int(fill * 100)}% of the available height; enlarge or rebalance')
        slides.append({'index': s['index'], 'id': s['id'], 'layout': s['layout'], 'image': s['image'], 'fill': fill,
                       'words': s.get('words'), 'issues': iss})
    deck_issues = []
    for e in render.get('js_errors', []):
        add(deck_issues, 'error', 'js-error', e)
    for face, status in (render.get('fonts') or {}).items():
        if status == 'error':
            add(deck_issues, 'error', 'font-failed', f'font failed to load: {face}')
    mo = render.get('motion')
    if mo:
        for f in mo['failures']:
            add(deck_issues, 'error', 'animation-final-state', f"slide {f['slide']}: elements not fully visible after animation: {f['issues']}")
        if not mo['keyboard_ok']:
            add(deck_issues, 'error', 'keyboard-nav', 'Home/End keyboard navigation did not reach first/last slide')
    if folder:
        try:
            from PIL import Image
            for s in slides[:1]:
                with Image.open(Path(folder) / s['image']) as im:
                    w, h = im.size
                if abs(w / h - 16 / 9) > 0.01:
                    add(deck_issues, 'error', 'aspect-ratio', f'preview is {w}x{h}, not 16:9')
        except Exception:  # noqa: BLE001
            pass
    report = {
        'ok': totals['error'] == 0 and (content or {}).get('ok', True),
        'visual_errors': totals['error'], 'visual_warnings': totals['warning'],
        'content': content, 'deck_issues': deck_issues, 'slides': slides, 'motion': mo, 'files': render.get('files', {}),
        'manual_review_required': True,
        'note': 'Automated geometry/contrast/font/animation checks passed or failed as listed. They cannot judge taste, hierarchy, '
                'or whether the visual fits the message: open contact-sheet.jpg and every flagged slide before delivering.',
    }
    if folder:
        Path(folder, 'qa-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        Path(folder, 'qa-report.md').write_text(markdown(report), encoding='utf-8')
    return report


def markdown(r: dict) -> str:
    lines = ['# QA report', '', f"- Result: **{'PASS' if r['ok'] else 'NEEDS FIXES'}**",
             f"- Visual errors: {r['visual_errors']} · warnings: {r['visual_warnings']}"]
    c = r.get('content')
    if c:
        lines.append(f"- Content audit: {c['error_count']} errors · {c.get('warning_count', 0)} warnings")
    mo = r.get('motion')
    if mo:
        lines.append(f"- Animation: {'animated' if mo['animated'] else 'static'}; final-state failures: {len(mo['failures'])}; "
                     f"keyboard: {'ok' if mo['keyboard_ok'] else 'FAIL'}")
    lines += ['- Manual visual review: **required** (open `contact-sheet.jpg` and flagged slides)', '']
    if r['deck_issues']:
        lines += ['## Deck', ''] + [f"- **{x['severity']}** `{x['code']}` {x['message']}" for x in r['deck_issues']] + ['']
    if c and c.get('issues'):
        lines += ['## Content', ''] + [f"- **{x['severity']}** [{x['slide']}] `{x['code']}` {x['message']}" + (f" → {x['hint']}" if x.get('hint') else '')
                                      for x in c['issues']] + ['']
    flagged = [s for s in r['slides'] if s['issues']]
    if flagged:
        lines += ['## Slides', '']
        for s in flagged:
            lines.append(f"### {s['index']:02d} · {s['id']} ({s['layout']})")
            lines += [f"- **{x['severity']}** `{x['code']}` {x['message']}" for x in s['issues']] + ['']
    return '\n'.join(lines) + '\n'