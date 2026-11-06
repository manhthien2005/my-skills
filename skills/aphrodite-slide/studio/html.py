"""Original data-driven HTML slide renderer, isolated from the preserved legacy Slide Kit."""
from __future__ import annotations
import html, json, math, os, re, shutil
from pathlib import Path
from urllib.parse import urlsplit
from .model import audit

BASE = Path(__file__).resolve().parents[1]

def esc(value) -> str:
    return html.escape(str(value if value is not None else ''),quote=True)

def safe_local_image(value) -> str:
    """Avoid script and remote URL injection in image src; only relative local assets."""
    p=str(value or '')
    if not p or p.startswith('/') or '\\' in p or '..' in Path(p).parts or ':' in p or '?' in p or '#' in p:
        raise ValueError('Images must use safe relative paths inside the deck assets directory')
    if not p.lower().endswith(('.png','.jpg','.jpeg','.webp','.svg')):
        raise ValueError('Unsupported image extension')
    return p

def h(text,cls=''): return f'<div class="{cls}">{esc(text)}</div>'

def item_desc(item): return esc(item.get('body') or item.get('detail') or item.get('description') or '')

def css(theme):
    t=theme
    return """*{box-sizing:border-box}html,body{margin:0;background:#d5d6d6} .slide{position:relative;width:1920px;height:1080px;overflow:hidden;padding:104px 122px 115px;background:var(--bg);color:var(--ink);font:30px/1.35 var(--body);-webkit-font-smoothing:antialiased}
    .slide::after{content:'';position:absolute;width:560px;height:560px;border:1px solid var(--line);border-radius:100%;right:-220px;top:-300px;opacity:.50;pointer-events:none}
    .slide[data-layout=cover]::after{width:850px;height:850px;border:2px solid var(--accent);right:-260px;top:220px;opacity:.30}
    .kicker{font-size:20px;letter-spacing:.21em;font-weight:700;text-transform:uppercase;color:var(--accent);margin-bottom:28px}
    h1{font-family:var(--display);font-size:102px;font-weight:700;line-height:1.02;letter-spacing:-.045em;max-width:1500px;margin:0 0 40px}
    h2{font-family:var(--display);font-size:82px;font-weight:700;line-height:1.08;letter-spacing:-.036em;max-width:1600px;margin:0 0 38px}
    .subtitle{font-size:33px;color:var(--muted);line-height:1.42;max-width:1300px}.content{position:relative;z-index:2}
    .foot{position:absolute;bottom:40px;left:122px;right:122px;display:flex;align-items:center;justify-content:space-between;gap:35px;color:var(--muted);font:19px var(--body);border-top:1px solid var(--line);padding-top:16px}
    .source{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:1180px}.foot .page{font-weight:700;flex:none}.pill{display:inline-block;border-radius:100px;padding:10px 25px;background:var(--accent);color:var(--bg);font-weight:700;font-size:22px}
    .hero{margin-top:110px;max-width:1340px}.hero h1{font-size:135px}.cover-rule{width:170px;height:8px;background:var(--accent);margin:55px 0 35px}
    .statement{font-family:var(--display);font-size:100px;line-height:1.12;letter-spacing:-.035em;max-width:1480px;padding-top:60px}
    .small-note{font-size:21px;color:var(--muted);margin-top:35px;max-width:1100px}
    .metric-grid{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:50px;margin-top:100px}
    .metric{border-top:3px solid var(--ink);padding-top:35px}.metric .value{font-size:120px;font-weight:800;letter-spacing:-.055em;color:var(--accent);line-height:1.04}.metric .metric-label{font-size:30px;font-weight:700;margin-top:22px}.metric .detail{font-size:24px;color:var(--muted);margin-top:15px}
    .column-grid{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:45px;margin-top:74px}
    .column{padding-top:26px;border-top:2px solid var(--ink)}.column .idx{font-size:30px;color:var(--accent);font-weight:800}.column h3{font-size:42px;line-height:1.15;margin:30px 0 23px}.column p{font-size:28px;line-height:1.43;color:var(--muted)}
    .process-track{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:20px;margin-top:110px}.step{min-height:340px;border-top:4px solid var(--accent);padding:30px 20px 0 0;position:relative}.step .idx{font-weight:800;font-size:62px;color:var(--accent)}.step h3{font-size:35px;margin:40px 0 10px}.step p{font-size:23px;color:var(--muted);line-height:1.45}
    .compare{display:grid;grid-template-columns:1fr 1fr;gap:34px;margin-top:40px}.compare article{border:1px solid var(--line);padding:47px;background:var(--surface);min-height:510px}.compare h3{font-size:42px;margin:0 0 35px}.compare ul{padding-left:30px;font-size:29px;line-height:1.6}.compare li{margin-bottom:16px}.highlight{color:var(--accent)}
    .timeline{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:20px;margin-top:124px;border-top:3px solid var(--ink)}.milestone{padding:30px 16px 0 0;position:relative}.milestone::before{content:'';position:absolute;top:-15px;left:0;width:24px;height:24px;border-radius:50%;background:var(--accent)}.milestone .date{color:var(--accent);font-weight:800;font-size:30px}.milestone h3{font-size:34px;margin:30px 0 15px}.milestone p{font-size:22px;line-height:1.45;color:var(--muted)}
    .chart-wrap{margin-top:38px;padding:15px 0}.chart-svg{width:100%;height:490px}.chart-caption{font-size:22px;color:var(--muted);margin-top:8px}
    .quote{font:italic 91px/1.2 var(--display);max-width:1540px;margin:108px 0 35px}.attribution{font-size:27px;color:var(--accent)}
    .summary-list{list-style:none;padding:20px 0;margin:15px 0;max-width:1500px}.summary-list li{display:flex;gap:30px;padding:25px 0;border-bottom:1px solid var(--line);font-size:40px;font-weight:650}.summary-list li b{color:var(--accent)}
    .closing{padding-top:190px}.closing h1{font-size:164px}.closing .subtitle{font-size:38px}
    .image-layout{display:grid;grid-template-columns:52% 45%;gap:3%;align-items:center}.image-layout img{width:100%;height:660px;object-fit:cover;border:1px solid var(--line)}.image-layout h2{font-size:73px}.image-layout .subtitle{font-size:29px}
    """ + "\n:root{"+";".join(f'--{k}:{v}' for k,v in {'bg':t['background'],'surface':t['surface'],'ink':t['ink'],'muted':t['muted'],'accent':t['accent'],'accent2':t['accent_alt'],'line':t['line'],'dark':t['dark'],'display':t['display_font'],'body':t['body_font']}.items())+";}"

def chart_svg(slide, theme):
    rows=slide.get('data',[])
    vals=[]
    for r in rows:
        try: val=float(r.get('value',0))
        except (TypeError,ValueError): val=0
        vals.append(max(0,val))
    top=max(vals+[1]); n=len(rows)
    if n==0: return ''
    width=1640; height=580; lx=50; rx=55; upper=45; lower=125
    plot_width=width-lx-rx; plot_height=height-upper-lower
    parts=[f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(slide.get("title","chart"))}">']
    for j in range(5):
        v=top*j/4
        y=upper+plot_height*(1-j/4)
        parts.append(f'<line x1="{lx}" y1="{y:.1f}" x2="{width-rx}" y2="{y:.1f}" stroke="{theme["line"]}" stroke-width="2"/>')
        parts.append(f'<text x="{lx-12}" y="{y-7:.1f}" font-size="20" fill="{theme["muted"]}" text-anchor="end">{v:.0f}</text>')
    if slide.get('chart_type','bar')=='line' and n>1:
        pts=[(lx+plot_width*i/(n-1),upper+plot_height*(1-vals[i]/top)) for i in range(n)]
        line=' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)
        parts.append(f'<polyline points="{line}" fill="none" stroke="{theme["accent"]}" stroke-width="9" stroke-linejoin="round"/>')
        for i,(x,y) in enumerate(pts):
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="{theme["accent"]}"/>')
            parts.append(f'<text x="{x:.1f}" y="{y-24:.1f}" text-anchor="middle" font-size="27" font-weight="700" fill="{theme["ink"]}">{esc(rows[i].get("value"))}</text>')
            parts.append(f'<text x="{x:.1f}" y="{height-70}" text-anchor="middle" font-size="25" fill="{theme["muted"]}">{esc(rows[i].get("label"))}</text>')
    else:
        bw=min(250,plot_width/n*.65)
        for i,row in enumerate(rows):
            x=lx+(i+.5)*plot_width/n-bw/2
            bh=plot_height*vals[i]/top
            y=upper+plot_height-bh
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="0" fill="{theme["accent"]}"/>')
            parts.append(f'<text x="{x+bw/2:.1f}" y="{max(32,y-20):.1f}" text-anchor="middle" font-size="29" font-weight="700" fill="{theme["ink"]}">{esc(row.get("value"))}</text>')
            parts.append(f'<text x="{x+bw/2:.1f}" y="{height-70}" text-anchor="middle" font-size="25" fill="{theme["muted"]}">{esc(row.get("label"))}</text>')
    parts.append('</svg>');return ''.join(parts)

def slide_body(s,theme):
    typ=s['type']; subtitle=f'<p class="subtitle">{esc(s["subtitle"])}</p>' if s.get('subtitle') else ''
    if typ=='cover': return f'<div class="hero"><div class="cover-rule"></div><h1>{esc(s["title"])}</h1>{subtitle}</div>'
    if typ=='section': return f'<div class="hero"><span class="pill">{esc(s.get("section_number", "PHẦN MỚI"))}</span><h1 style="margin-top:60px">{esc(s["title"])}</h1>{subtitle}</div>'
    if typ=='statement': return f'<div class="statement">{esc(s["title"])}</div>{subtitle}<div class="small-note">{esc(s.get("note",""))}</div>'
    if typ=='metrics':
        items=s.get('items',[])[:4]; return f'<h2>{esc(s["title"])}</h2>{subtitle}<div class="metric-grid" style="--n:{max(1,len(items))}">'+''.join(f'<div class="metric"><div class="value">{esc(a.get("value",""))}</div><div class="metric-label">{esc(a.get("label",""))}</div><div class="detail">{item_desc(a)}</div></div>' for a in items)+'</div>'
    if typ=='columns':
        items=s.get('items',[])[:4];return f'<h2>{esc(s["title"])}</h2>{subtitle}<div class="column-grid" style="--n:{max(1,len(items))}">'+''.join(f'<div class="column"><div class="idx">{i:02d}</div><h3>{esc(a.get("title",""))}</h3><p>{item_desc(a)}</p></div>' for i,a in enumerate(items,1))+'</div>'
    if typ=='process':
        items=s.get('steps',s.get('items',[]))[:6];return f'<h2>{esc(s["title"])}</h2>{subtitle}<div class="process-track" style="--n:{max(1,len(items))}">'+''.join(f'<div class="step"><div class="idx">{i:02d}</div><h3>{esc(a.get("title",""))}</h3><p>{item_desc(a)}</p></div>' for i,a in enumerate(items,1))+'</div>'
    if typ=='timeline':
        items=s.get('items',[])[:5];return f'<h2>{esc(s["title"])}</h2>{subtitle}<div class="timeline" style="--n:{max(1,len(items))}">'+''.join(f'<div class="milestone"><div class="date">{esc(a.get("date",""))}</div><h3>{esc(a.get("title",""))}</h3><p>{item_desc(a)}</p></div>' for a in items)+'</div>'
    if typ=='comparison':
        sides=[s.get('left',{}),s.get('right',{})];inner=''.join('<article>'+f'<h3>{esc(a.get("title",""))}</h3><ul>'+''.join(f'<li>{esc(b)}</li>' for b in a.get('bullets',[])[:5])+'</ul></article>' for a in sides)
        return f'<h2>{esc(s["title"])}</h2>{subtitle}<div class="compare">{inner}</div>'
    if typ=='chart':return f'<h2>{esc(s["title"])}</h2>{subtitle}<div class="chart-wrap">{chart_svg(s,theme)}</div><div class="chart-caption">{esc(s.get("caption",""))}</div>'
    if typ=='quote':return f'<h2>{esc(s["title"])}</h2><div class="quote">“{esc(s.get("quote",""))}”</div><div class="attribution">{esc(s.get("attribution",""))}</div>'
    if typ=='summary':return f'<h2>{esc(s["title"])}</h2>{subtitle}<ul class="summary-list">'+''.join(f'<li><b>{i:02d}.</b><span>{esc(v)}</span></li>' for i,v in enumerate(s.get('bullets',[])[:4],1))+'</ul>'
    if typ=='closing':return f'<div class="closing"><h1>{esc(s["title"])}</h1>{subtitle}</div>'
    if typ=='image-split':
        image=safe_local_image(s.get('image'))
        return f'<div class="image-layout"><div><h2>{esc(s["title"])}</h2>{subtitle}<p class="small-note">{esc(s.get("image_credit",""))}</p></div><img src="{esc("../assets/"+image)}" alt="{esc(s.get("image_alt",""))}"></div>'
    return f'<h2>{esc(s.get("title",""))}</h2>'

def save_html_slide(slide, index, n, deck, theme, output):
    sources=slide.get('sources') or []
    src=' · '.join(str(x) for x in sources)
    if slide.get('illustrative') or deck.get('demo'):
        src=((src+' · ') if src else '')+'DỮ LIỆU MINH HỌA / KHÔNG PHẢI SỐ LIỆU THỰC TẾ'
    head=f'<div class="kicker">{esc(slide.get("eyebrow",deck.get("brand","PRESENTATION")))}</div>'
    body=slide_body(slide,theme)
    styles=css(theme)
    markup=f'''<!doctype html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=1920"><title>{esc(slide.get('title',''))}</title><style>{styles}</style></head>
<body><main class="slide" data-layout="{esc(slide['type'])}" data-slide-id="{esc(slide.get('id',str(index)))}"><div class="content">{head}{body}</div>
<footer class="foot"><div>{esc(deck.get('brand','PERSONAL SLIDE STUDIO'))}</div><div class="source">{esc(src)}</div><div class="page">{index:02d} / {n:02d}</div></footer></main></body></html>'''
    output.write_text(markup,encoding='utf-8')

def viewer(slide_filenames, title):
    names=json.dumps([f'slides/{n}' for n in slide_filenames],ensure_ascii=False)
    return f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><style>
    html,body{{margin:0;height:100%;background:#0c1018;color:white;font:17px Arial,sans-serif;overflow:hidden}}#viewport{{position:absolute;inset:0 0 48px;overflow:hidden;display:flex;align-items:center;justify-content:center}}iframe{{width:1920px;height:1080px;border:0;transform-origin:top left;position:absolute;top:0;left:0;pointer-events:none}}#toolbar{{position:absolute;bottom:0;height:48px;width:100%;background:#151c2c;display:flex;gap:18px;justify-content:center;align-items:center}}button{{background:transparent;border:1px solid #70778b;border-radius:8px;color:white;padding:4px 20px;cursor:pointer}}span{{min-width:90px;text-align:center}}</style></head><body>
<div id="viewport"><iframe id="deck" title="Presentation slide" allowfullscreen></iframe></div><div id="toolbar"><button id="prev">← Trước</button><span id="counter"></span><button id="next">Sau →</button><button id="full">Toàn màn hình</button></div><script>
const slides={names};let idx=0;const frame=document.querySelector('#deck');const vp=document.querySelector('#viewport');
function fit(){{let k=Math.min(vp.clientWidth/1920,vp.clientHeight/1080);frame.style.transform=`scale(${{k}})`;frame.style.left=((vp.clientWidth-1920*k)/2)+'px';frame.style.top=((vp.clientHeight-1080*k)/2)+'px'}}
function show(i){{idx=Math.max(0,Math.min(slides.length-1,i));frame.src=slides[idx];document.querySelector('#counter').textContent=`${{idx+1}} / ${{slides.length}}`;fit()}}
window.addEventListener('resize',fit);document.querySelector('#prev').onclick=()=>show(idx-1);document.querySelector('#next').onclick=()=>show(idx+1);document.querySelector('#full').onclick=()=>document.documentElement.requestFullscreen();
window.addEventListener('keydown',e=>{{if(['ArrowRight','PageDown',' '].includes(e.key))show(idx+1);if(['ArrowLeft','PageUp'].includes(e.key))show(idx-1)}});show(0);
</script></body></html>'''

def build(deck:dict, dest:Path, theme_name:str | None = None, assets_root:Path | None = None):
    r=audit(deck,strict=True)
    if not r['ok']: raise ValueError('Deck preflight failed: '+json.dumps(r['issues'],ensure_ascii=False))
    theme_name=theme_name or deck.get('theme','editorial-cream')
    theme_path=BASE/'configs'/'themes'/f'{theme_name}.json'
    if not theme_path.exists():raise ValueError(f'Unknown theme {theme_name}')
    theme=json.loads(theme_path.read_text(encoding='utf-8'))
    (dest/'slides').mkdir(parents=True,exist_ok=True);(dest/'assets').mkdir(parents=True,exist_ok=True)
    slides=deck['slides']; names=[]
    for i,s in enumerate(slides,1):
        name=f'{i:02d}-{re.sub("[^a-z0-9-]","-",str(s.get("id",i)).lower()).strip("-")}.html';names.append(name)
        save_html_slide(s,i,len(slides),deck,theme,dest/'slides'/name)
    (dest/'index.html').write_text(viewer(names,deck['title']),encoding='utf-8')
    (dest/'deck.json').write_text(json.dumps(deck,ensure_ascii=False,indent=2),encoding='utf-8')
    (dest/'manifest.json').write_text(json.dumps({'slides':names,'title':deck['title'],'theme':theme_name},ensure_ascii=False,indent=2),encoding='utf-8')
    if assets_root and assets_root.is_dir():
        shutil.copytree(assets_root,dest/'assets',dirs_exist_ok=True)
    return names
