"""HTML layout renderers. Each returns the inner markup of one slide; geometry/typography come from deck.css + theme vars."""
from __future__ import annotations

import math

from ..common import esc, rt, plain, icon_svg, L, title_class, fmt_num
from .charts import svg_chart, sparkline


class Seq:
    """Animation sequencer: assigns stagger index (--i) and optional click build steps (data-step)."""

    def __init__(self, build: bool = False):
        self.i, self.build, self.step = 0, build, 0

    def __call__(self, kind: str = 'a-rise', step: bool = False, extra: str = '', style: str = '') -> str:
        attrs = f' class="a {kind}{(" " + extra) if extra else ""}" style="--i:{self.i}{(";" + style) if style else ""}"'
        self.i += 1
        if step and self.build:
            self.step += 1
            attrs += f' data-step="{self.step}"'
        return attrs


def header(s, A, ctx, title=True, cls='title', limit=58):
    out = ''
    if s.get('eyebrow'):
        out += f'<div class="eyebrow a a-fade" style="--i:{A.i}">{esc(s["eyebrow"])}</div>'
        A.i += 1
    if title and s.get('title'):
        mask = 'a-mask' if ctx['anim'] == 'cinematic' else 'a-rise'
        long_cls = ' long' if title_class(s['title'], limit) else ''
        out += f'<h1{A(mask, extra=cls + long_cls)}>{rt(s["title"])}</h1>'
    if s.get('subtitle'):
        out += f'<p{A("a-rise", extra="lead")}>{rt(s["subtitle"])}</p>'
    return out


def badge(name, color=None, num=None):
    style = f' style="--c:{color}"' if color else ''
    inner = icon_svg(name) if name else (f'<span class="idx" style="font-size:24px;color:inherit">{num}</span>' if num else '')
    return f'<span class="badge"{style}>{inner}</span>'


def pal(ctx, i):
    p = ctx['theme']['colors']['series']
    return p[i % len(p)]


# ----------------------------------------------------------------------------- layouts

def cover(s, A, ctx):
    meta = ''
    if s.get('meta'):
        cells = ''
        for m in s['meta']:
            k, _, v = str(m).partition(':') if ':' in str(m) else ('', '', str(m))
            cells += f'<div{A("a-rise")}>' + (f'<span class="k">{esc(k.strip())}</span>' if k else '') + f'<span class="v">{rt(v.strip())}</span></div>'
        meta = f'<div class="cover-meta">{cells}</div>'
    mask = 'a-mask' if ctx['anim'] == 'cinematic' else 'a-rise'
    eb = f'<div class="eyebrow a a-fade" style="--i:0">{esc(s["eyebrow"])}</div>' if s.get('eyebrow') else ''
    A.i += 1
    text = (f'{eb}<h1{A(mask, extra="display" + title_class(s["title"], 44))}>{rt(s["title"])}</h1>'
            + (f'<p{A("a-rise", extra="lead")}>{rt(s["subtitle"])}</p>' if s.get('subtitle') else '') + meta)
    if s.get('image'):
        return (f'<div class="cover-split"><div style="position:relative;display:flex;flex-direction:column;justify-content:flex-end;height:100%">{text}</div>'
                f'<div{A("a-scale", extra="media")}><img src="{ctx["img"](s["image"])}" alt="{esc(s.get("image_alt", ""))}"></div></div>')
    return text


def agenda(s, A, ctx):
    items = s.get('items') or []
    two = len(items) > 4
    rows = ''
    for i, it in enumerate(items, 1):
        it = it if isinstance(it, dict) else {'title': it}
        rows += (f'<div{A("a-rise", step=True, extra="row")}><span class="idx">{i:02d}</span><div><h3>{rt(it.get("title", ""))}</h3>'
                 + (f'<p>{rt(it["detail"])}</p>' if it.get('detail') else '') + '</div></div>')
    return header(s, A, ctx) + f'<div class="body"><div class="agenda{" two" if two else ""}">{rows}</div></div>'


def section(s, A, ctx):
    num = s.get('section_number')
    big = f'<div class="sec-num" aria-hidden="true">{esc(num)}</div>' if num and len(str(num)) <= 3 else ''
    eb = s.get('eyebrow') or (f'{num}' if num and len(str(num)) > 3 else '')
    out = (f'<div class="eyebrow a a-fade" style="--i:0">{esc(eb)}</div>' if eb else '')
    A.i += 1
    mask = 'a-mask' if ctx['anim'] == 'cinematic' else 'a-rise'
    out += f'<h1{A(mask, extra="display" + title_class(s["title"], 40))}>{rt(s["title"])}</h1>'
    if s.get('subtitle'):
        out += f'<p{A("a-rise", extra="lead")}>{rt(s["subtitle"])}</p>'
    if s.get('chips'):
        out += '<div class="chips">' + ''.join(f'<span{A("a-rise", extra="chip")}>{esc(c)}</span>' for c in s['chips']) + '</div>'
    return big + out


def statement(s, A, ctx):
    out = f'<div{A("a-grow-x", extra="statement-mark")}></div>'
    if s.get('eyebrow'):
        out = f'<div class="eyebrow a a-fade" style="--i:{A.i}">{esc(s["eyebrow"])}</div>' + out; A.i += 1
    long = ' long' if len(plain(s['title'])) > 80 else ''
    out += f'<p{A("a-mask" if ctx["anim"] == "cinematic" else "a-rise", extra="statement" + long)}>{rt(s["title"])}</p>'
    if s.get('subtitle'):
        out += f'<p{A("a-rise", extra="lead")}>{rt(s["subtitle"])}</p>'
    if s.get('note'):
        out += f'<p{A("a-fade", extra="note")}>{rt(s["note"])}</p>'
    return out


def metrics(s, A, ctx):
    items = s.get('items') or []
    tiles = ''
    for i, it in enumerate(items):
        color = pal(ctx, i) if ctx['theme']['icons']['style'] == 'color-circle' or ctx['theme']['id'] == 'editorial-warm' else None
        style = f'--c:{color}' if color else ''
        tiles += (f'<div{A("a-rise", step=True, extra="card tile", style=style)}><span class="num" data-count="{esc(it.get("value", ""))}">{esc(it.get("value", ""))}</span>'
                  f'<span class="label">{rt(it.get("label", ""))}</span>'
                  + (f'<span class="detail">{rt(it.get("detail") or it.get("body") or "")}</span>' if (it.get('detail') or it.get('body')) else '') + '</div>')
    return header(s, A, ctx) + f'<div class="body"><div class="tiles n{len(items)}" style="--n:{max(1, len(items))}">{tiles}</div></div>'


def kpi_dashboard(s, A, ctx):
    items = s.get('items') or []
    n = len(items)
    cols = n if n <= 4 else 3
    th = ctx['theme']['colors']
    cells = ''
    for it in items:
        status = it.get('status', 'flat')
        cls = {'up': 'good', 'good': 'good', 'down': 'bad', 'bad': 'bad'}.get(status, 'flat')
        arrow = {'good': '▲', 'bad': '▼', 'flat': '•'}[cls] if not it.get('arrow') else it['arrow']
        if status in ('down',) and it.get('down_is_good'):
            cls = 'good'
        delta = f'<span class="delta {cls}">{arrow} {esc(it["delta"])}</span>' if it.get('delta') else ''
        spark = sparkline(it.get('trend'), th['positive'] if cls == 'good' else th['negative'] if cls == 'bad' else th['accent']) if it.get('trend') else ''
        detail = it.get('detail') or (f'{L(ctx["deck"], "target")}: {it["target"]}' if it.get('target') else '')
        cells += (f'<div{A("a-rise", step=True, extra="card kpi")}><span class="k">{esc(it.get("label", ""))}</span>'
                  f'<div class="row"><span class="num" data-count="{esc(it.get("value", ""))}">{esc(it.get("value", ""))}</span>{delta}</div>'
                  f'{spark}' + (f'<span class="detail">{rt(detail)}</span>' if detail else '') + '</div>')
    period = f'<span class="chip period a a-fade" style="--i:1">{esc(s["period"])}</span>' if s.get('period') else ''
    return (f'<div style="position:relative">{header(s, A, ctx)}{period}</div>'
            f'<div class="body"><div class="kpis" style="--cols:{cols}">{cells}</div></div>')


def cards(s, A, ctx):
    items = s.get('items') or []
    style = s.get('style') or ('panels' if ctx['theme']['cards']['style'] in ('paper', 'tint', 'glass-dark') or any(
        isinstance(it, dict) and it.get('icon') for it in items) else 'columns')
    out = ''
    for i, it in enumerate(items, 1):
        it = it if isinstance(it, dict) else {'title': it}
        color = pal(ctx, i - 1)
        b = badge(it.get('icon'), color) if it.get('icon') else ''
        body = it.get('body') or it.get('detail') or ''
        if style == 'columns':
            head = b or f'<span class="idx">{i:02d}</span>'
            out += f'<div{A("a-rise", step=True, extra="col")}>{head}<h3>{rt(it.get("title", ""))}</h3><p>{rt(body)}</p></div>'
        else:
            head = b or f'<span class="idx">{i:02d}</span>'
            out += f'<div{A("a-rise", step=True, extra="card panel" + (" hl" if it.get("highlight") else ""))}>{head}<h3>{rt(it.get("title", ""))}</h3><p>{rt(body)}</p></div>'
    grid = 'cols' if style == 'columns' else 'panels'
    return header(s, A, ctx) + f'<div class="body"><div class="{grid}" style="--n:{max(1, len(items))}">{out}</div></div>'


def process(s, A, ctx):
    steps = s.get('steps') or s.get('items') or []
    rail = f'<div class="rail"><i class="a a-grow-x" style="--i:{A.i}"></i></div>'
    A.i += 1
    out = ''
    for i, st in enumerate(steps, 1):
        st = st if isinstance(st, dict) else {'title': st}
        node = icon_svg(st['icon']) if st.get('icon') else f'{i:02d}'
        out += (f'<div{A("a-rise", step=True, extra="step")}><span class="node">{node}</span><h3>{rt(st.get("title", ""))}</h3>'
                + (f'<p>{rt(st.get("detail") or st.get("body") or "")}</p>' if (st.get('detail') or st.get('body')) else '') + '</div>')
    return header(s, A, ctx) + f'<div class="body"><div class="process" style="--n:{max(1, len(steps))}">{rail}{out}</div></div>'


def timeline(s, A, ctx):
    items = s.get('items') or []
    axis = f'<div class="axis"><i class="a a-grow-x" style="--i:{A.i}"></i></div>'
    A.i += 1
    out = ''
    for it in items:
        state = it.get('state', 'done')
        tag = f'<span class="state">{esc(L(ctx["deck"], "now"))}</span>' if state == 'now' else ''
        out += (f'<div{A("a-rise", step=True, extra="ms " + state)}><span class="dot"></span><div class="date">{esc(it.get("date", ""))}{tag}</div>'
                f'<h3>{rt(it.get("title", ""))}</h3>' + (f'<p>{rt(it.get("detail") or it.get("body") or "")}</p>' if (it.get('detail') or it.get('body')) else '') + '</div>')
    return header(s, A, ctx) + f'<div class="body"><div class="timeline" style="--n:{max(1, len(items))}">{axis}{out}</div></div>'


def _blist(points, tone='positive'):
    icon = {'positive': 'check', 'negative': 'x', 'neutral': 'arrow-right'}.get(tone, 'check')
    cls = {'negative': ' neg', 'neutral': ' neutral'}.get(tone, '')
    return f'<ul class="blist{cls}">' + ''.join(f'<li>{icon_svg(icon)}<span>{rt(p)}</span></li>' for p in points) + '</ul>'


def comparison(s, A, ctx):
    hl = s.get('highlight')
    panels = ''
    for key in ('left', 'right'):
        side = s.get(key) or {}
        tone = side.get('tone', 'neutral' if not hl else ('positive' if hl == key else 'neutral'))
        tag = f'<span class="chip tag">{esc(side["tag"])}</span>' if side.get('tag') else ''
        panels += (f'<div{A("a-left" if key == "left" else "a-rise", step=True, extra="card" + (" hl" if hl == key else ""))}>'
                   f'<h3>{rt(side.get("title", ""))}{tag}</h3>{_blist(side.get("bullets") or [], tone)}</div>')
    verdict = (f'<div{A("a-rise", step=True, extra="verdict")}>{icon_svg("lightbulb")}<span>{rt(s["verdict"])}</span></div>' if s.get('verdict') else '')
    return header(s, A, ctx) + f'<div class="body"><div class="compare">{panels}</div>{verdict}</div>'


def problem_solution(s, A, ctx):
    p, so = s.get('problem') or {}, s.get('solution') or {}
    left = (f'<div{A("a-left", step=True, extra="card")}><h3>{badge("circle-question-mark", ctx["theme"]["colors"]["negative"])}{rt(p.get("title") or L(ctx["deck"], "problem"))}</h3>'
            f'{_blist(p.get("points") or p.get("bullets") or [], "negative")}</div>')
    arrow = f'<div{A("a-scale", extra="ps-arrow")}><span>{icon_svg("arrow-right")}</span></div>'
    right = (f'<div{A("a-rise", step=True, extra="card hl")}><h3>{badge("lightbulb")}{rt(so.get("title") or L(ctx["deck"], "solution"))}</h3>'
             f'{_blist(so.get("points") or so.get("bullets") or [], "positive")}</div>')
    return header(s, A, ctx) + f'<div class="body"><div class="compare ps">{left}{arrow}{right}</div></div>'


def table(s, A, ctx):
    cols = s.get('columns') or []
    hl = s.get('highlight')
    hli = cols.index(hl) if isinstance(hl, str) and hl in cols else (hl if isinstance(hl, int) else None)
    th = ''.join(f'<th class="{"hl" if j == hli else ""}">{esc(c)}</th>' for j, c in enumerate(cols))
    rows = ''
    for r in s.get('rows') or []:
        rows += f'<tr{A("a-rise", step=True)}>' + ''.join(f'<td class="{"hl" if j == hli else ""}">{rt(c)}</td>' for j, c in enumerate(r)) + '</tr>'
    note = f'<p class="tnote">{rt(s["note"])}</p>' if s.get('note') else ''
    return header(s, A, ctx) + f'<div class="body"><div{A("a-fade", extra="card")} style="padding:30px 36px"><table class="mtable"><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table></div>{note}</div>'


def chart(s, A, ctx):
    ch = dict(s.get('chart') or {})
    ch.setdefault('title', plain(s.get('title', '')))
    ins = s.get('insights') or []
    w = 1088 if ins else 1664
    svg = svg_chart(ch, ctx['theme'], ctx['lang'], width=w, height=500 if not s.get('subtitle') else 440)
    cap = f'<p class="chart-cap">{rt(s["caption"])}</p>' if s.get('caption') else ''
    side = ''
    if ins:
        side = '<div class="insights">' + ''.join(
            f'<div{A("a-rise", step=True, extra="ins")}><span class="idx">{i:02d}</span><span>{rt(t)}</span></div>' for i, t in enumerate(ins, 1)) + '</div>'
    return (header(s, A, ctx) + f'<div class="body top" style="margin-top:36px"><div class="chart-grid{" with-insights" if ins else ""}">'
            f'<div class="chart-box">{svg}{cap}</div>{side}</div></div>')


def case(s, A, ctx):
    out = header(s, A, ctx)
    story = f'<p{A("a-rise", extra="story")}>{rt(s.get("body", ""))}</p>' if s.get('body') else ''
    out += (f'<div class="body" style="justify-content:flex-end"><div class="case"><div{A("a-rise")}><div class="num hero" data-count="{esc(s.get("value", ""))}">{esc(s.get("value", ""))}</div>'
            + (f'<div class="vlabel">{rt(s["value_label"])}</div>' if s.get('value_label') else '') + f'</div>{story}</div></div>')
    return out


def evidence_levels(s, A, ctx):
    levels = s.get('levels') or []
    n = len(levels)
    th = ctx['theme']['colors']
    from ..common import mix, contrast
    rows = ''
    for i, lv in enumerate(levels):
        lv = lv if isinstance(lv, dict) else {'label': lv}
        t = i / max(1, n - 1)
        color = mix(th['accent_strong'], th['subtle'], t * 0.75)
        dark_txt = th['bg'] if ctx['theme'].get('scheme') == 'dark' else th['ink']
        txt = '#FFFFFF' if contrast('#FFFFFF', color) >= contrast(dark_txt, color) else dark_txt
        width = 100 - i * (30 / max(1, n - 1))
        rows += (f'<div class="level a a-left" style="--i:{A.i + (n - 1 - i)};--w:760px;--c:{color}"><div class="bar" style="width:{width:.0f}%;color:{txt}"><b>{i + 1}</b><span>{rt(lv.get("label", ""))}</span></div>'
                 f'<p>{rt(lv.get("detail", ""))}</p></div>')
    A.i += n
    note = f'<p class="tnote">{rt(s["note"])}</p>' if s.get('note') else ''
    return header(s, A, ctx) + f'<div class="body"><div class="levels">{rows}</div>{note}</div>'


def methodology(s, A, ctx):
    facts = ''.join(f'<div{A("a-rise", extra="card fact")}><div class="num">{esc(f.get("value", ""))}</div><div class="k">{rt(f.get("label", ""))}</div></div>'
                    for f in (s.get('facts') or []))
    rail = f'<div class="rail"><i class="a a-grow-down" style="--i:{A.i}"></i></div>'
    A.i += 1
    steps = ''
    for i, st in enumerate(s.get('steps') or [], 1):
        steps += (f'<div{A("a-rise", step=True, extra="vstep")}><span class="node">{i:02d}</span><div><h3>{rt(st.get("title", ""))}</h3>'
                  f'<p>{rt(st.get("detail", ""))}</p></div></div>')
    grid = f'<div class="method"><div class="facts">{facts}</div><div class="vsteps">{rail}{steps}</div></div>' if facts else \
        f'<div class="vsteps" style="max-width:1300px">{rail}{steps}</div>'
    return header(s, A, ctx) + f'<div class="body">{grid}</div>'


def diagram(s, A, ctx):
    nodes = [nd if isinstance(nd, dict) else {'title': nd} for nd in (s.get('nodes') or [])]
    n = len(nodes)
    variant = s.get('variant', 'hub' if s.get('center') else 'cycle')
    th = ctx['theme']['colors']
    W, H = 1664, 600
    if variant == 'cycle':
        return header(s, A, ctx) + f'<div class="body">{_cycle(s, nodes, A, ctx, W, H)}</div>'
    cx, cy, rx, ry = W / 2, H / 2, 620, 232
    pos = [(cx + rx * math.cos(-math.pi / 2 + 2 * math.pi * i / n), cy + ry * math.sin(-math.pi / 2 + 2 * math.pi * i / n)) for i in range(n)]
    links = f'<svg class="links" viewBox="0 0 {W} {H}">'
    for i, (x, y) in enumerate(pos):
        links += (f'<line class="a a-draw" style="--i:{1 + i * .5}" pathLength="1" x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" '
                  f'stroke="{th["line"]}" stroke-width="3"/>')
    links += '</svg>'
    center = f'<div class="center a a-scale" style="--i:0;left:{cx}px;top:{cy}px">{rt(s.get("center", ""))}</div>'
    boxes = ''
    for i, (nd, (x, y)) in enumerate(zip(nodes, pos)):
        b = badge(nd.get('icon'), pal(ctx, i), num=None if nd.get('icon') else f'{i + 1}')
        boxes += (f'<div class="node-pos" style="left:{x:.0f}px;top:{y:.0f}px"><div class="card node a a-rise" style="--i:{2 + i}">{b}<div><h3>{rt(nd.get("title", ""))}</h3>'
                  + (f'<p>{rt(nd["detail"])}</p>' if nd.get('detail') else '') + '</div></div></div>')
    A.i += n + 2
    return header(s, A, ctx) + f'<div class="body"><div class="diagram">{links}{center}{boxes}</div></div>'


def _cycle(s, nodes, A, ctx, W, H):
    n = len(nodes)
    th = ctx['theme']['colors']
    cx, cy, R, nr = W / 2, H / 2, 250, 62
    ang = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
    pos = [(cx + R * math.cos(a), cy + R * math.sin(a)) for a in ang]
    gap = (nr + 18) / R
    svg = (f'<svg class="links" viewBox="0 0 {W} {H}"><defs><marker id="arr" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" '
           f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{th["accent_strong"]}"/></marker></defs>'
           f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{th["line"]}" stroke-width="2" stroke-dasharray="4 10"/>')
    for i in range(n):
        a0, a1 = ang[i] + gap, ang[i] + 2 * math.pi / n - gap
        x0, y0 = cx + R * math.cos(a0), cy + R * math.sin(a0)
        x1, y1 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        large = 1 if (a1 - a0) > math.pi else 0
        svg += (f'<path class="a a-draw" style="--i:{2 + i * 1.2:.1f}" pathLength="1" d="M{x0:.1f},{y0:.1f} A{R},{R} 0 {large} 1 {x1:.1f},{y1:.1f}" '
                f'fill="none" stroke="{th["accent_strong"]}" stroke-width="4" marker-end="url(#arr)"/>')
    svg += '</svg>'
    out = svg
    if s.get('center'):
        out += f'<div class="cyc-center-pos" style="left:{cx}px;top:{cy}px"><div class="cyc-center a a-fade" style="--i:1">{rt(s["center"])}</div></div>'
    for i, (nd, (x, y), a) in enumerate(zip(nodes, pos, ang)):
        inner = icon_svg(nd['icon']) if nd.get('icon') else f'<span>{i + 1}</span>'
        out += f'<div class="cyc-node a a-scale" style="--i:{1.5 + i * 1.2:.1f};left:{x:.0f}px;top:{y:.0f}px;--c:{pal(ctx, i)}">{inner}</div>'
        c, sn = math.cos(a), math.sin(a)
        side = 'l' if c < -0.3 else 'r'
        lx = x - nr - 28 if side == 'l' else x + nr + 28
        # near-vertical nodes: arcs leave/arrive just below (top node) or above (bottom node) centre, so lift/drop the label clear of them
        vpos = ' up' if abs(c) <= 0.3 and sn < 0 else (' down' if abs(c) <= 0.3 else '')
        out += (f'<div class="cyc-pos {side}{vpos}" style="left:{lx:.0f}px;top:{y:.0f}px"><div class="cyc-label a a-rise" style="--i:{1.8 + i * 1.2:.1f}">'
                f'<h3>{rt(nd.get("title", ""))}</h3>'
                + (f'<p>{rt(nd["detail"])}</p>' if nd.get('detail') else '') + '</div></div>')
    A.i += n * 2 + 2
    return f'<div class="diagram">{out}</div>'


def learning_objectives(s, A, ctx):
    items = s.get('items') or []
    two = len(items) > 3
    out = ''
    for i, it in enumerate(items):
        text = it if isinstance(it, str) else it.get('text', '')
        icon = None if isinstance(it, str) else it.get('icon')
        words = plain(text).split(' ', 1)
        body = f'<b>{esc(words[0])}</b> {esc(words[1]) if len(words) > 1 else ""}' if '**' not in text else rt(text)
        out += f'<div{A("a-rise", step=True, extra="obj")}>{badge(icon or "circle-check", pal(ctx, i))}<span>{body}</span></div>'
    s2 = dict(s)
    if not s2.get('subtitle'):
        s2['subtitle'] = s.get('lead') or L(ctx['deck'], 'objectives_lead')
    return header(s2, A, ctx) + f'<div class="body"><div class="objectives{" two" if two else ""}">{out}</div></div>'


def definition(s, A, ctx):
    eb = f'<div class="eyebrow a a-fade" style="--i:0">{esc(s.get("eyebrow") or s.get("title") or "")}</div>' if (s.get('eyebrow') or s.get('title')) else ''
    A.i += 1
    left = (f'{eb}<div{A("a-mask" if ctx["anim"] == "cinematic" else "a-rise", extra="term" + (" long" if len(plain(s.get("term", ""))) > 9 else ""))}>{rt(s.get("term", ""))}</div>'
            + (f'<div class="pron">{esc(s["pronunciation"])}</div>' if s.get('pronunciation') else '')
            + f'<p{A("a-rise", extra="defn")}>{rt(s.get("definition", ""))}</p>')
    right = ''
    if s.get('example'):
        right += f'<div{A("a-rise", extra="card example")}><span class="kicker">{esc(L(ctx["deck"], "example"))}</span><p>{rt(s["example"])}</p></div>'
    if s.get('note'):
        right += f'<div{A("a-fade", extra="dnote")}>{icon_svg("info")}<span>{rt(s["note"])}</span></div>'
    return f'<div class="body" style="margin-top:0"><div class="definition"><div>{left}</div><div>{right}</div></div></div>'


def image_split(s, A, ctx):
    credit = f'<span class="credit">{esc(s["image_credit"])}</span>' if s.get('image_credit') else ''
    media = f'<div{A("a-zoom" if ctx["anim"] == "cinematic" else "a-fade", extra="media")}><img src="{ctx["img"](s["image"])}" alt="{esc(s.get("image_alt", ""))}">{credit}</div>'
    bl = _blist(s['bullets'], 'neutral') if s.get('bullets') else ''
    text = f'<div class="text">{header(s, A, ctx, limit=40)}{bl}</div>'
    return f'<div class="split">{text}{media}</div>'


def full_bleed_image(s, A, ctx):
    credit = f'<span class="credit">{esc(s["image_credit"])}</span>' if s.get('image_credit') else ''
    media = f'<div class="media"><img class="a a-zoom" style="--i:0" src="{ctx["img"](s["image"])}" alt="{esc(s.get("image_alt", ""))}"></div><div class="shade"></div>{credit}'
    A.i += 1
    eb = f'<div class="eyebrow a a-fade" style="--i:1">{esc(s["eyebrow"])}</div>' if s.get('eyebrow') else ''
    text = (eb + f'<h1{A("a-rise", extra="display")}>{rt(s["title"])}</h1>'
            + (f'<p{A("a-rise", extra="lead")}>{rt(s["subtitle"])}</p>' if s.get('subtitle') else ''))
    return ('__MEDIA__' + media + '__ENDMEDIA__') + text


def quote(s, A, ctx):
    eb = f'<div class="eyebrow a a-fade" style="--i:0">{esc(s.get("title") or s.get("eyebrow") or "")}</div>' if (s.get('title') or s.get('eyebrow')) else ''
    A.i += 1
    return (eb + f'<div{A("a-fade", extra="qmark")}>“</div><blockquote{A("a-rise", extra="quote")}>{rt(s.get("quote", ""))}</blockquote>'
            f'<div{A("a-rise", extra="attrib")}>{rt(s.get("attribution", ""))}</div>')


def key_takeaways(s, A, ctx):
    items = ''.join(f'<li{A("a-rise", step=True)}><span class="idx">{i:02d}</span><span>{rt(b)}</span></li>' for i, b in enumerate(s.get('bullets') or [], 1))
    return header(s, A, ctx) + f'<div class="body"><ol class="takeaways">{items}</ol></div>'


def references(s, A, ctx):
    items = s.get('items') or []
    lis = ''.join(f'<li><span>{rt(x)}</span></li>' for x in items)
    s2 = dict(s)
    s2.setdefault('title', L(ctx['deck'], 'references'))
    return header(s2, A, ctx) + f'<div class="body top"><ol{A("a-fade", extra="refs" + (" two" if len(items) > 4 else ""))}>{lis}</ol></div>'


def closing(s, A, ctx):
    eb = f'<div class="eyebrow a a-fade" style="--i:0">{esc(s["eyebrow"])}</div>' if s.get('eyebrow') else ''
    A.i += 1
    out = eb + f'<h1{A("a-mask" if ctx["anim"] == "cinematic" else "a-rise", extra="display")}>{rt(s["title"])}</h1>'
    if s.get('subtitle'):
        out += f'<p{A("a-rise", extra="lead")}>{rt(s["subtitle"])}</p>'
    if s.get('meta'):
        cells = ''
        for m in s['meta']:
            k, _, v = str(m).partition(':') if ':' in str(m) else ('', '', str(m))
            cells += f'<div{A("a-rise")}>' + (f'<span class="k">{esc(k.strip())}</span>' if k else '') + f'<span>{rt(v.strip())}</span></div>'
        out += f'<div class="closing-meta">{cells}</div>'
    return out


RENDERERS = {
    'cover': cover, 'agenda': agenda, 'section': section, 'statement': statement, 'metrics': metrics, 'kpi-dashboard': kpi_dashboard,
    'cards': cards, 'process': process, 'timeline': timeline, 'comparison': comparison, 'table': table, 'chart': chart, 'case': case,
    'evidence-levels': evidence_levels, 'problem-solution': problem_solution, 'methodology': methodology, 'diagram': diagram,
    'learning-objectives': learning_objectives, 'definition': definition, 'image-split': image_split, 'full-bleed-image': full_bleed_image,
    'quote': quote, 'key-takeaways': key_takeaways, 'references': references, 'closing': closing,
}

