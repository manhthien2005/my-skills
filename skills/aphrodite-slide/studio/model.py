"""Data model, content safety and narrative preflight."""
from __future__ import annotations
import json, re
from pathlib import Path

SUPPORTED = {'cover','section','statement','metrics','columns','process','comparison','timeline','chart','quote','summary','closing','image-split'}
FILLER = {'hãy cùng khám phá','đột phá','seamless','game-changer','tương lai của','hành trình khám phá'}


def load_deck(path: str | Path) -> dict:
    path = Path(path)
    raw = path.read_text(encoding='utf-8')
    if path.suffix.lower() in ('.yaml','.yml'):
        try:
            import yaml
        except ImportError as ex:
            raise RuntimeError('Install PyYAML for YAML: pip install pyyaml; JSON works with no dependency.') from ex
        result = yaml.safe_load(raw)
    else:
        result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError('Deck root must be an object')
    return result


def audit(deck: dict, strict: bool = False) -> dict:
    issues=[]
    def issue(level, key, message): issues.append({'severity':level,'slide':key,'message':message})
    slides=deck.get('slides')
    if not isinstance(slides,list) or not slides: issue('error','deck','slides must be a nonempty list'); slides=[]
    if not deck.get('title'): issue('error','deck','title is required')
    if not deck.get('audience'): issue('warning','deck','audience is not specified')
    if not deck.get('takeaway'): issue('warning','deck','takeaway is not specified')
    ids=set()
    for i,s in enumerate(slides,1):
        if not isinstance(s,dict): issue('error',str(i),'slide must be an object');continue
        sid = str(s.get('id',f'{i:02}'))
        if sid in ids: issue('error',sid,'duplicate slide id')
        ids.add(sid)
        typ=s.get('type')
        if typ not in SUPPORTED: issue('error',sid,f'unsupported type {typ!r}')
        title=s.get('title','')
        if not isinstance(title,str) or not title.strip(): issue('error',sid,'missing meaningful title')
        if len(str(title))>98: issue('warning',sid,'title longer than 98 characters')
        if re.match(r'^[^:]{2,30}:\s',str(title)): issue('warning',sid,'label-like title; turn into a takeaway')
        body=json.dumps(s,ensure_ascii=False)
        if len(body.split())>220: issue('warning',sid,'slide may be too dense; review manually')
        for phrase in FILLER:
            if phrase.lower() in body.lower(): issue('warning',sid,f'filler phrase: {phrase}')
        if typ=='chart' and not s.get('data'): issue('error',sid,'chart has no data')
        if typ in ('metrics','columns','process','comparison','timeline') and not (s.get('items') or s.get('steps') or s.get('left')):
            issue('error',sid,f'{typ} needs content items')
        if typ=='image-split' and not s.get('image'): issue('error',sid,'image-split requires local image')
        text_for_number=' '.join(str(s.get(k,'')) for k in ('title','subtitle','body','quote'))+' '+json.dumps(s.get('items',[]),ensure_ascii=False)
        # Numbers likely used as evidence; demo / explicitly hypothetical data is exempt but must be labeled.
        has_number=bool(re.search(r'(?<!\w)(?:\d+[.,]?\d*%?|\d{4})(?!\w)',text_for_number))
        if typ=='chart': has_number=True
        if has_number and not s.get('sources') and not s.get('illustrative',False) and not deck.get('demo',False):
            issue('error' if strict else 'warning',sid,'numeric claim needs sources or illustrative=true')
        if s.get('illustrative') and not (deck.get('demo') or s.get('note')):
            issue('warning',sid,'mark illustration visibly as simulated; include note')
        for source in s.get('sources',[]):
            if isinstance(source,str) and source.strip().lower() in ('source','nguồn','tbd','placeholder'):
                issue('warning',sid,'source is a placeholder')
    errors=sum(x['severity']=='error' for x in issues)
    return {'slide_count':len(slides),'issue_count':len(issues),'error_count':errors,'issues':issues,'ok':errors==0}
