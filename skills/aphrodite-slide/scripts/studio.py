#!/usr/bin/env python3
"""CLI for Personal Slide Studio. Run `python tools/studio.py --help`."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from studio.model import audit,load_deck
from studio.html import build
from studio.quality import capture
from studio.pptx import export

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description='Personal Slide Studio 1.0 - offline-first modular slide production')
    sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('validate',help='Review content, statistics, source completeness and layout type');p.add_argument('deck');p.add_argument('--strict',action='store_true')
    p=sub.add_parser('build',help='Create responsive local HTML viewer and slide HTML files');p.add_argument('deck');p.add_argument('--out');p.add_argument('--theme')
    p=sub.add_parser('render',help='Screenshot each slide, produce PDF and visual QA report');p.add_argument('folder');p.add_argument('--strict',action='store_true')
    p=sub.add_parser('pptx',help='Export editable PPTX (beta, approximate layouts)');p.add_argument('deck');p.add_argument('--out');p.add_argument('--theme')
    p=sub.add_parser('themes',help='List themes')
    args=parser.parse_args()
    if args.cmd=='themes':
        print('\n'.join(p.stem for p in (ROOT/'configs/themes').glob('*.json')));return
    if args.cmd=='render':
        report=capture(Path(args.folder),strict=args.strict)
        sys.exit(0 if report['ok'] else 2)
    deck=load_deck(args.deck)
    report=audit(deck,strict=args.cmd!='validate' or args.strict)
    if args.cmd=='validate':
        print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if report['ok'] else 2)
    if not report['ok']:
        print(json.dumps(report['issues'],ensure_ascii=False,indent=2));sys.exit('Deck failed preflight')
    if args.cmd=='build':
        out=Path(args.out) if args.out else ROOT/'build'/Path(args.deck).stem
        names=build(deck,out,args.theme,Path(args.deck).parent/'assets')
        print(f'Built {len(names)} slides at {out.resolve()}; open {out/"index.html"}')
    if args.cmd=='pptx':
        out=Path(args.out) if args.out else ROOT/'build'/(Path(args.deck).stem+'.pptx')
        print('PPTX editable beta:',export(deck,out,args.theme))

if __name__=='__main__':main()
