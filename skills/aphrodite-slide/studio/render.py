"""Render a built HTML deck: per-slide PNG, contact sheet, PDF (vector and/or image), QA probe + motion check."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .browser import launch, playwright

PROBE = (Path(__file__).parent / 'qa' / 'probe.js').read_text(encoding='utf-8')


def _url(index: Path, query: str = '') -> str:
    return index.resolve().as_uri() + query


def render(folder: Path, pdf: str = 'vector', motion: bool = True, scale: float = 1.0, only: list[int] | None = None) -> dict:
    """Returns {'slides': [...], 'errors': [...], 'motion': {...}, 'files': {...}}."""
    folder = Path(folder).resolve()
    index = folder / 'index.html'
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    prev = folder / 'previews'
    prev.mkdir(exist_ok=True)
    result = {'slides': [], 'js_errors': [], 'motion': None, 'files': {}, 'fonts': {}}
    with playwright() as p:
        browser = launch(p)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080}, device_scale_factor=scale)
        page.on('pageerror', lambda e: result['js_errors'].append(str(e)[:300]))
        page.on('console', lambda m: m.type == 'error' and result['js_errors'].append('console: ' + m.text[:300]))
        page.goto(_url(index, '?static'), wait_until='load')
        page.evaluate('document.fonts.ready')
        page.wait_for_function('window.__deck && window.__deck.ready')
        result['fonts'] = page.evaluate('''() => { const r = {}; document.fonts.forEach(f => { r[f.family.replace(/["']/g,'') + ' ' + f.weight + ' ' + f.style] = f.status; }); return r; }''')
        n = page.evaluate('window.__deck.count')
        names = []
        for i in range(n):
            if only and (i + 1) not in only:
                continue
            page.evaluate(f'window.__deck.go({i}, true)')
            page.wait_for_timeout(60)
            meta = manifest['slides'][i]
            name = f"{i + 1:02d}-{meta['id']}"
            shot = prev / f'{name}.png'
            page.screenshot(path=str(shot), type='png')
            probe = page.evaluate(PROBE, i)
            result['slides'].append({'index': i + 1, 'id': meta['id'], 'layout': meta['layout'], 'image': f'previews/{name}.png', **probe})
            names.append(shot)
        if pdf in ('vector', 'both') and not only:
            page.emulate_media(media='print')
            page.pdf(path=str(folder / 'deck.pdf'), width='1920px', height='1080px', print_background=True, prefer_css_page_size=True)
            page.emulate_media(media='screen')
            result['files']['pdf'] = 'deck.pdf'
        if motion and not only:
            result['motion'] = motion_check(page, index, n)
        browser.close()
    from PIL import Image, ImageDraw
    if names:
        cols, tw = 4, 460
        th = int(tw * 9 / 16)
        rows = (len(names) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * (tw + 16) + 16, rows * (th + 40) + 16), '#E7E8EC')
        dr = ImageDraw.Draw(sheet)
        for k, f in enumerate(names):
            im = Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS)
            x, y = 16 + (k % cols) * (tw + 16), 16 + (k // cols) * (th + 40)
            sheet.paste(im, (x, y))
            dr.text((x, y + th + 8), f.stem, fill='#222222')
        sheet.save(folder / 'contact-sheet.jpg', quality=88)
        result['files']['contact_sheet'] = 'contact-sheet.jpg'
        if pdf in ('image', 'both') and not only:
            ims = [Image.open(f).convert('RGB') for f in names]
            ims[0].save(folder / 'deck-image.pdf', format='PDF', save_all=True, append_images=ims[1:], resolution=96 * scale)
            result['files']['image_pdf'] = 'deck-image.pdf'
    return result


def motion_check(page, index: Path, n: int) -> dict:
    """Play every slide with animations (fast speed) through all build steps and verify the final state is fully visible."""
    failures = []
    page.goto(_url(index, '?speed=0.15'), wait_until='load')
    page.evaluate('document.fonts.ready')
    t0 = time.time()
    animated = page.evaluate("document.body.classList.contains('anim-on')")
    for i in range(n):
        page.evaluate(f'window.__deck.go({i}, false)')
        steps = page.evaluate(f'window.__deck.steps({i})')
        for _ in range(steps):
            page.keyboard.press('ArrowRight')
            page.wait_for_timeout(40)
        page.wait_for_timeout(700)
        bad = page.evaluate('''(i) => { const s = document.querySelectorAll('.stage > .slide')[i]; const out = [];
            s.querySelectorAll('.a').forEach(el => { const cs = getComputedStyle(el);
              if (!el.classList.contains('in') || +cs.opacity < 0.98) out.push((el.className.baseVal ?? el.className) + ' op=' + cs.opacity); });
            return {bad: out.slice(0, 5), active: s.classList.contains('active')}; }''', i)
        if bad['bad'] or not bad['active']:
            failures.append({'slide': i + 1, 'issues': bad['bad'], 'active': bad['active']})
    # keyboard navigation sanity
    page.keyboard.press('Home')
    page.wait_for_timeout(50)
    first = page.evaluate('window.__deck.current()')
    page.keyboard.press('End')
    page.wait_for_timeout(50)
    last = page.evaluate('window.__deck.current()')
    return {'animated': animated, 'failures': failures, 'keyboard_ok': first == 0 and last == n - 1, 'seconds': round(time.time() - t0, 1)}

