"""Path resolution. Everything is relative to the skill directory, never the CWD."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS = SKILL_DIR / 'assets'
THEMES = ASSETS / 'themes'
TEMPLATES = ASSETS / 'templates'
LAYOUTS = ASSETS / 'layouts' / 'catalog.json'
FONTS = ASSETS / 'fonts'
ICONS = ASSETS / 'icons'
RUNTIME = ASSETS / 'runtime'
CONFIGS = SKILL_DIR / 'configs'


def user_home() -> Path:
    """Private per-user store for brand/private templates and themes (outside any repo)."""
    return Path(os.environ.get('APHRODITE_HOME') or (Path.home() / '.aphrodite-slide'))


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def catalog() -> dict:
    return read_json(LAYOUTS)


def layout_id(name: str | None) -> str | None:
    if not name:
        return None
    cat = catalog()
    name = str(name).strip()
    if name in cat['layouts']:
        return name
    return cat['aliases'].get(name)


def profile() -> dict:
    """Repo defaults merged with the optional private user profile."""
    data = read_json(CONFIGS / 'profile.json') if (CONFIGS / 'profile.json').exists() else {}
    user = user_home() / 'profile.json'
    if user.exists():
        try:
            data.update(read_json(user))
        except (OSError, ValueError):
            pass
    return data

