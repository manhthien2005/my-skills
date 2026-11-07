"""Headless Chromium discovery (Playwright). Optional dependency; core build/validate never needs it."""
from __future__ import annotations

import glob
import os
from pathlib import Path


class RenderUnavailable(RuntimeError):
    pass


def _candidates():
    exe = os.environ.get('CHROMIUM_EXECUTABLE')
    if exe:
        yield {'executable_path': exe}
    yield {}
    for ch in ('msedge', 'chrome'):
        yield {'channel': ch}
    roots = [Path(os.environ.get('LOCALAPPDATA', '')) / 'ms-playwright', Path.home() / '.cache' / 'ms-playwright',
             Path.home() / 'Library' / 'Caches' / 'ms-playwright']
    pats = ['chromium-*/chrome-win*/chrome.exe', 'chromium-*/chrome-linux*/chrome', 'chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium']
    for root in roots:
        for pat in pats:
            for p in sorted(glob.glob(str(root / pat)), reverse=True):
                yield {'executable_path': p}
    for p in ('/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome'):
        if Path(p).exists():
            yield {'executable_path': p}


def launch(p):
    errors = []
    for opts in _candidates():
        try:
            return p.chromium.launch(headless=True, args=['--no-sandbox', '--font-render-hinting=none'], **opts)
        except Exception as ex:  # noqa: BLE001 - try the next candidate
            errors.append(f'{opts or "default"}: {str(ex).splitlines()[0][:120]}')
    raise RenderUnavailable('No usable Chromium found. Install with `python -m playwright install chromium` or set '
                            'CHROMIUM_EXECUTABLE.\n' + '\n'.join(errors[:6]))


def playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as ex:
        raise RenderUnavailable('Rendering needs Playwright + Pillow: pip install -r requirements-render.txt') from ex
    return sync_playwright()

