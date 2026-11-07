#!/usr/bin/env python3
"""Unified CLI for Aphrodite-slide v2 (Personal AI Presentation Studio).

Portable: resolves all skill assets relative to SKILL_DIR, never assuming CWD.
Run `python scripts/studio.py --help` from anywhere.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        try:
            _stream.reconfigure(encoding='utf-8')
        except Exception:  # noqa: BLE001
            pass

from studio import __version__, paths
from studio.export import export_all
from studio.html import build as build_html
from studio.outline import approve as approve_outline, diff as diff_outline, guard as guard_outline, lint as lint_outline, load as load_outline, scaffold_outline, to_spec
from studio.pptx import export as export_pptx
from studio.previews import render_preview
from studio.qa import evaluate as evaluate_qa
from studio.qa.pptx_qa import inspect_pptx, render_pptx
from studio.recommend import recommend
from studio.registry import apply_template, build_registry, get_template, list_templates, sample_deck
from studio.render import render as render_html
from studio.samples import neutral_deck
from studio.spec import audit, list_themes, load_deck, load_theme, normalize
from studio.templates import create_theme, save_template, test_template


def _dump(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _default_assets(deck_path: Path, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit)
    cand = deck_path.parent / 'assets'
    return cand if cand.is_dir() else deck_path.parent


def cmd_recommend(args) -> int:
    res = recommend(
        brief=args.brief or '',
        use_case=args.use_case,
        audience=args.audience or '',
        density=args.density,
        formality=args.formality,
        scheme=args.scheme,
        top=args.top,
    )
    _dump(res)
    return 0


def cmd_themes(args) -> int:
    sub = args.themes_cmd or 'list'
    if sub == 'list':
        aliases = paths.read_json(paths.THEMES / 'aliases.json')
        _dump({'themes': list_themes(), 'aliases': aliases})
        return 0
    if sub == 'new':
        sets = {}
        for item in args.set or []:
            if '=' not in item:
                raise SystemExit(f'--set expects key=value, got {item!r}')
            k, v = item.split('=', 1)
            sets[k.strip()] = v.strip()
        out = create_theme(args.id, base=args.base, sets=sets, scope=args.scope,
                           name=args.name, description=args.description or '', bump=args.bump)
        _dump({'created': str(out), 'id': args.id, 'scope': args.scope})
        return 0
    return 1


def cmd_layouts(_args) -> int:
    _dump(paths.catalog())
    return 0


def cmd_templates(args) -> int:
    sub = args.templates_cmd or 'list'
    if sub == 'list':
        items = [
            {'id': t['id'], 'name': t.get('name'), 'name_vi': t.get('name_vi'), 'version': t.get('version'),
             'scope': t['scope'], 'use_cases': t.get('use_cases', []), 'default_theme': t.get('default_theme'),
             'compatible_themes': t.get('compatible_themes', []), 'animation': t.get('animation'),
             'preview': t.get('preview_path')}
            for t in list_templates()
        ]
        _dump({'templates': items})
        return 0
    if sub == 'show':
        _dump(get_template(args.id))
        return 0
    if sub == 'save':
        deck = load_deck(args.deck)
        ucs = [x.strip() for x in args.use_cases.split(',') if x.strip()]
        tags = [x.strip() for x in (args.tags or '').split(',') if x.strip()]
        res = save_template(
            deck=deck, tid=args.id, name=args.name, use_cases=ucs, scope=args.scope,
            description=args.description or '', tags=tags, bump=args.bump,
            include_content=args.include_content, allow_sensitive=args.allow_sensitive,
            render=not args.no_render, name_vi=args.name_vi,
        )
        _dump(res)
        return 0
    if sub == 'test':
        other = load_deck(args.other) if args.other else None
        res = test_template(args.id, other_deck=other)
        _dump(res)
        return 0 if res['sample']['ok'] and (not other or res['other_content']['ok']) else 2
    return 1


def cmd_outline(args) -> int:
    sub = args.outline_cmd
    if sub == 'scaffold':
        tmpl = get_template(args.template)
        meta = {'title': args.title or '', 'audience': args.audience or '', 'purpose': args.purpose or '',
                'takeaway': args.takeaway or '', 'language': args.language}
        if args.duration:
            meta['duration_minutes'] = args.duration
        txt = scaffold_outline(tmpl, meta=meta)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(txt, encoding='utf-8')
        _dump({'outline': str(out), 'template': tmpl['id'], 'slides': len(tmpl.get('storyline', []))})
        return 0
    if sub == 'lint':
        rep = lint_outline(load_outline(args.outline))
        _dump(rep)
        return 0 if rep['ok'] else 2
    if sub == 'approve':
        res = approve_outline(args.outline, note=args.note or '')
        _dump(res)
        return 0 if res['lint']['ok'] else 2
    if sub == 'diff':
        _dump(diff_outline(args.outline))
        return 0
    if sub == 'to-spec':
        spec = to_spec(load_outline(args.outline))
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
        _dump({'deck': str(out), 'slides': len(spec.get('slides', []))})
        return 0
    return 1


def cmd_validate(args) -> int:
    dp = Path(args.deck)
    deck = load_deck(dp)
    rep = audit(deck, strict=args.strict, assets_root=_default_assets(dp, args.assets))
    if args.outline:
        drift = guard_outline(deck, args.outline)
        rep['baseline_drift'] = drift
        rep['issues'].extend(drift)
        rep['warning_count'] = sum(1 for x in rep['issues'] if x['severity'] == 'warning')
        rep['issue_count'] = len(rep['issues'])
    _dump(rep)
    return 0 if rep['ok'] else 2


def cmd_preview(args) -> int:
    assets_root = Path(args.assets) if args.assets else None
    sig = ['cards', 'chart', 'kpi-dashboard']
    if args.deck:
        dp = Path(args.deck)
        deck = load_deck(dp)
        assets_root = assets_root or _default_assets(dp, None)
    elif args.outline:
        deck = to_spec(load_outline(args.outline))
        # Ensure placeholder chart/table slides don't fail preflight during quick style preview
        deck = neutral_deck(['cover', 'cards', 'chart', 'closing'], title=deck.get('title') or 'Style Preview',
                            language=deck.get('language', 'vi'))
    elif args.template:
        t = get_template(args.template)
        deck = apply_template(sample_deck(t), t)
        t_assets = Path(t['_dir']) / 'assets'
        assets_root = assets_root or (t_assets if t_assets.is_dir() else None)
        sig = t.get('signature_layouts', sig)
    else:
        deck = neutral_deck(['cover', 'cards', 'chart', 'closing'], title=args.title or 'Xem trước phong cách thiết kế',
                            language=args.language)
    picks = [int(x) for x in args.slides.split(',') if x.strip()] if args.slides else None
    out = render_preview(deck, Path(args.out), theme=args.theme, assets_root=assets_root, slides=picks, signature=sig)
    _dump({'preview': str(out), 'theme': args.theme or deck.get('theme')})
    return 0


def cmd_build(args) -> int:
    dp = Path(args.deck)
    deck = load_deck(dp)
    out = Path(args.out) if args.out else (SKILL_DIR / 'build' / dp.stem)
    res = build_html(deck, out, theme_name=args.theme, assets_root=_default_assets(dp, args.assets),
                     single_file=args.single_file, animation=args.animation, strict=args.strict)
    _dump(res)
    return 0


def cmd_render(args) -> int:
    folder = Path(args.folder)
    only = [int(x) for x in args.only.split(',') if x.strip()] if args.only else None
    ren = render_html(folder, pdf=args.pdf, motion=not args.no_motion, scale=args.scale, only=only)
    content = None
    dj = folder / 'deck.json'
    if dj.is_file():
        d = load_deck(dj)
        assets_dir = folder / 'assets'
        content = audit(d, strict=args.strict, assets_root=assets_dir if assets_dir.is_dir() else folder)
    qa = evaluate_qa(ren, content=content, folder=folder)
    _dump({'ok': qa['ok'], 'visual_errors': qa['visual_errors'], 'visual_warnings': qa['visual_warnings'],
           'files': ren.get('files', {}), 'qa_report': str(folder / 'qa-report.md')})
    return 0 if qa['ok'] else 2


def cmd_pptx(args) -> int:
    dp = Path(args.deck)
    deck = load_deck(dp)
    out = Path(args.out) if args.out else (SKILL_DIR / 'build' / f'{dp.stem}.pptx')
    res = export_pptx(
        deck, out, theme_name=args.theme, assets_root=_default_assets(dp, args.assets),
        transitions=not args.no_transitions, entrances=args.entrances,
        use_theme_fonts=args.use_theme_fonts, strict=args.strict,
    )
    if args.qa or args.render_previews:
        q = inspect_pptx(out, out_report=out.with_suffix('.qa.json'))
        if args.render_previews:
            q['visual_render'] = render_pptx(out, out.parent)
            out.with_suffix('.qa.json').write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding='utf-8')
        res['qa'] = q
        _dump(res)
        return 0 if q['ok'] else 2
    _dump(res)
    return 0


def cmd_export(args) -> int:
    dp = Path(args.deck)
    deck = load_deck(dp)
    out = Path(args.out) if args.out else (SKILL_DIR / 'build' / dp.stem)
    res = export_all(
        deck, out, theme_name=args.theme, animation=args.animation,
        assets_root=_default_assets(dp, args.assets), single_file=args.single_file,
        pdf=args.pdf, pptx_enabled=not args.no_pptx, transitions=not args.no_transitions,
        entrances=args.entrances, render_pptx_previews=args.render_pptx, strict=args.strict,
    )
    _dump(res)
    qa_ok = (res['qa'] is None or res['qa']['ok']) and (res['pptx_qa'] is None or res['pptx_qa']['ok'])
    return 0 if qa_ok else 2


def cmd_registry(args) -> int:
    if args.registry_cmd == 'build':
        out = build_registry()
        _dump({'registry': str(out)})
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='studio.py', description=f'Aphrodite-slide v{__version__} — Personal AI Presentation Studio CLI')
    p.add_argument('--version', action='version', version=f'aphrodite-slide {__version__}')
    sub = p.add_subparsers(dest='cmd', required=True)

    # recommend
    r = sub.add_parser('recommend', help='Rank top templates & themes for a brief with previews')
    r.add_argument('--brief', default='', help='Topic, context or user request text')
    r.add_argument('--use-case', help='Explicit use case (academic, education, medical, technology, business)')
    r.add_argument('--audience', default='', help='Target audience description')
    r.add_argument('--density', choices=['speaker', 'reading'])
    r.add_argument('--formality', choices=['low', 'medium', 'high'])
    r.add_argument('--scheme', choices=['light', 'dark'])
    r.add_argument('--top', type=int, default=3)
    r.set_defaults(func=cmd_recommend)

    # themes
    th = sub.add_parser('themes', help='List themes or create a derived theme')
    th_sub = th.add_subparsers(dest='themes_cmd')
    th_sub.add_parser('list', help='List available repo and user themes')
    th_new = th_sub.add_parser('new', help='Create a new theme from a base theme')
    th_new.add_argument('id', help='Lowercase-hyphenated theme id')
    th_new.add_argument('--base', default='editorial-warm', help='Base theme id')
    th_new.add_argument('--set', action='append', help='Override token dotted key=value (repeatable)')
    th_new.add_argument('--scope', choices=['user', 'repo'], default='user')
    th_new.add_argument('--name', help='Display name')
    th_new.add_argument('--description', help='Short description')
    th_new.add_argument('--bump', choices=['patch', 'minor', 'major'])
    th.set_defaults(func=cmd_themes)

    # layouts
    lay = sub.add_parser('layouts', help='Inspect slide layout catalog and capacity limits')
    lay.set_defaults(func=cmd_layouts)

    # templates
    tp = sub.add_parser('templates', help='List, inspect, save, or test reusable templates')
    tp_sub = tp.add_subparsers(dest='templates_cmd')
    tp_sub.add_parser('list', help='List all templates (repo + user)')
    tp_show = tp_sub.add_parser('show', help='Show full metadata for one template')
    tp_show.add_argument('id')
    tp_save = tp_sub.add_parser('save', help='Save a deck design as a versioned, privacy-scrubbed template')
    tp_save.add_argument('deck', help='Source deck.json')
    tp_save.add_argument('--id', required=True, help='Lowercase-hyphenated template id')
    tp_save.add_argument('--name', required=True, help='Template display name')
    tp_save.add_argument('--name-vi', help='Vietnamese display name')
    tp_save.add_argument('--use-cases', required=True, help='Comma-separated use cases')
    tp_save.add_argument('--scope', choices=['user', 'repo'], default='user')
    tp_save.add_argument('--description', default='')
    tp_save.add_argument('--tags', default='', help='Comma-separated tags')
    tp_save.add_argument('--bump', choices=['patch', 'minor', 'major'], help='Required to update an existing template')
    tp_save.add_argument('--include-content', action='store_true', help='Keep deck text (runs PII scan)')
    tp_save.add_argument('--allow-sensitive', action='store_true', help='Explicitly permit PII when user confirmed')
    tp_save.add_argument('--no-render', action='store_true', help='Skip rendering preview.jpg')
    tp_test = tp_sub.add_parser('test', help='Verify a template builds cleanly on sample + another deck')
    tp_test.add_argument('id')
    tp_test.add_argument('--other', help='Optional unrelated deck.json to test reuse')
    tp.set_defaults(func=cmd_templates)

    # outline
    ol = sub.add_parser('outline', help='Content-first outline workflow (scaffold, lint, approve, diff, to-spec)')
    ol_sub = ol.add_subparsers(dest='outline_cmd', required=True)
    ol_sc = ol_sub.add_parser('scaffold', help='Create an outline.md skeleton from a template storyline')
    ol_sc.add_argument('--template', required=True)
    ol_sc.add_argument('--out', required=True)
    ol_sc.add_argument('--title', default='')
    ol_sc.add_argument('--audience', default='')
    ol_sc.add_argument('--purpose', default='')
    ol_sc.add_argument('--takeaway', default='')
    ol_sc.add_argument('--language', default='vi')
    ol_sc.add_argument('--duration', type=int)
    ol_li = ol_sub.add_parser('lint', help='Validate content quality, action titles, density and citations')
    ol_li.add_argument('outline')
    ol_ap = ol_sub.add_parser('approve', help='Snapshot user-approved outline baseline (archives previous baselines)')
    ol_ap.add_argument('outline')
    ol_ap.add_argument('--note', default='')
    ol_df = ol_sub.add_parser('diff', help='Compare current outline.md against approved baseline')
    ol_df.add_argument('outline')
    ol_ts = ol_sub.add_parser('to-spec', help='Convert approved outline.md into a starter deck.json')
    ol_ts.add_argument('outline')
    ol_ts.add_argument('--out', required=True)
    ol.set_defaults(func=cmd_outline)

    # validate
    va = sub.add_parser('validate', help='Validate deck.json schema, capacities, citations, glyphs and baseline drift')
    va.add_argument('deck')
    va.add_argument('--strict', action='store_true')
    va.add_argument('--outline', help='Optional approved outline.md to check for silent drift')
    va.add_argument('--assets', help='Assets directory override')
    va.set_defaults(func=cmd_validate)

    # preview
    pv = sub.add_parser('preview', help='Render a 4-slide visual style preview image before full production')
    pv.add_argument('--deck', help='Deck JSON to preview')
    pv.add_argument('--outline', help='Outline MD (uses title/language with neutral preview slides)')
    pv.add_argument('--template', help='Template ID to preview')
    pv.add_argument('--theme', help='Theme ID override')
    pv.add_argument('--title', help='Title when generating a neutral preview')
    pv.add_argument('--language', default='vi')
    pv.add_argument('--slides', help='Comma-separated 1-based slide indices')
    pv.add_argument('--assets', help='Assets directory override')
    pv.add_argument('--out', required=True, help='Output .jpg path')
    pv.set_defaults(func=cmd_preview)

    # build
    bd = sub.add_parser('build', help='Build offline-capable animated HTML deck')
    bd.add_argument('deck')
    bd.add_argument('--out', help='Output folder')
    bd.add_argument('--theme', help='Theme override')
    bd.add_argument('--animation', choices=['none', 'subtle', 'professional', 'cinematic'])
    bd.add_argument('--single-file', action='store_true', help='Embed fonts & images into a single portable index.html')
    bd.add_argument('--strict', action='store_true')
    bd.add_argument('--assets', help='Assets directory override')
    bd.set_defaults(func=cmd_build)

    # render
    rn = sub.add_parser('render', help='Render built HTML deck to PNGs, contact sheet, PDF, and run Visual + Motion QA')
    rn.add_argument('folder')
    rn.add_argument('--pdf', choices=['vector', 'image', 'both', 'none'], default='vector')
    rn.add_argument('--no-motion', action='store_true', help='Skip animation final-state & keyboard verification')
    rn.add_argument('--only', help='Comma-separated 1-based slide indices')
    rn.add_argument('--scale', type=float, default=1.0)
    rn.add_argument('--strict', action='store_true')
    rn.set_defaults(func=cmd_render)

    # pptx
    px = sub.add_parser('pptx', help='Export native editable PowerPoint (.pptx) with charts, tables, notes & transitions')
    px.add_argument('deck')
    px.add_argument('--out', help='Output .pptx file path')
    px.add_argument('--theme', help='Theme override')
    px.add_argument('--no-transitions', action='store_true', help='Disable native slide transitions')
    px.add_argument('--entrances', action='store_true', help='Enable experimental OOXML group fade-in entrances')
    px.add_argument('--use-theme-fonts', action='store_true', help='Use web theme font names instead of Office-safe fallbacks')
    px.add_argument('--qa', action='store_true', help='Run structural & overlap QA on the exported .pptx')
    px.add_argument('--render-previews', action='store_true', help='Render .pptx slides via PowerPoint/LibreOffice if installed')
    px.add_argument('--strict', action='store_true')
    px.add_argument('--assets', help='Assets directory override')
    px.set_defaults(func=cmd_pptx)

    # export
    ex = sub.add_parser('export', help='One-shot pipeline: HTML + PNGs + PDF + QA + native PPTX + PPTX QA')
    ex.add_argument('deck')
    ex.add_argument('--out', help='Output folder')
    ex.add_argument('--theme', help='Theme override')
    ex.add_argument('--animation', choices=['none', 'subtle', 'professional', 'cinematic'])
    ex.add_argument('--single-file', action='store_true')
    ex.add_argument('--pdf', choices=['vector', 'image', 'both', 'none'], default='vector')
    ex.add_argument('--no-pptx', action='store_true')
    ex.add_argument('--no-transitions', action='store_true')
    ex.add_argument('--entrances', action='store_true')
    ex.add_argument('--render-pptx', action='store_true', help='Also render PPTX PNGs via PowerPoint/LibreOffice')
    ex.add_argument('--strict', action='store_true')
    ex.add_argument('--assets', help='Assets directory override')
    ex.set_defaults(func=cmd_export)

    # registry
    rg = sub.add_parser('registry', help='Rebuild compact template registry index')
    rg_sub = rg.add_subparsers(dest='registry_cmd', required=True)
    rg_sub.add_parser('build', help='Regenerate assets/registry.json from repo templates')
    rg.set_defaults(func=cmd_registry)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == '__main__':
    main()
