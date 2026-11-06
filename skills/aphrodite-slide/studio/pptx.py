"""Editable native PowerPoint adapter (beta). Prioritizes editable text/shapes over HTML fidelity."""
from __future__ import annotations
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]

def export(deck:dict,out:Path,theme_name:str|None=None):
    try:
        from pptx import Presentation
        from pptx.util import Inches,Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN,MSO_ANCHOR
        from pptx.enum.shapes import MSO_SHAPE
    except ImportError as ex:
        raise RuntimeError('Editable PPTX requires python-pptx: pip install python-pptx') from ex
    theme=json.loads((BASE/'configs/themes'/f'{theme_name or deck.get("theme","editorial-cream")}.json').read_text(encoding='utf-8'))
    c=lambda s:RGBColor.from_string(s.lstrip('#'))
    bg,ink,accent,muted,surface,line=map(lambda k:c(theme[k]),['background','ink','accent','muted','surface','line'])
    prs=Presentation();prs.slide_width=Inches(13.3333);prs.slide_height=Inches(7.5)
    def shape(sl, x,y,w,h,color,round=False):
        sh=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if round else MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));sh.fill.solid();sh.fill.fore_color.rgb=color;sh.line.fill.background();return sh
    def tb(sl,text,x,y,w,h,size,color=ink,bold=False,font='Arial',align=None):
        sh=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame;tf.clear();tf.word_wrap=True
        p=tf.paragraphs[0];p.text=str(text);p.font.name=font;p.font.size=Pt(size);p.font.color.rgb=color;p.font.bold=bold
        if align:p.alignment=align
        return sh
    def bullet_list(sl,txts,x,y,w,size=18,dy=.60,color=ink):
        for i,txt in enumerate(txts[:6]):
            shape(sl,x,y+i*dy+.13,.07,.07,accent)
            tb(sl,str(txt),x+.22,y+i*dy,w-.25,dy+.10,size,color)
    for number,s in enumerate(deck['slides'],1):
        slide=prs.slides.add_slide(prs.slide_layouts[6]);shape(slide,0,0,13.34,7.5,bg)
        typ=s['type'];tb(slide,s.get('eyebrow','PERSONAL SLIDE STUDIO').upper(),.83,.40,11,.35,12,accent,True)
        title=s.get('title','');hfont=theme['display_font'].split(',')[0].strip(" '")
        if typ in ('cover','section','statement','closing'):
            tb(slide,title,.84,1.45,11.6,2.8,55 if len(title)<55 else 42,ink,True,hfont)
            if s.get('subtitle'):tb(slide,s['subtitle'],.87,4.4,10.7,1.25,25,muted)
            shape(slide,.86,1.18,1.3,.055,accent)
        else:
            tb(slide,title,.84,1.10,11.6,1.12,36 if len(title)<64 else 30,ink,True,hfont)
            if s.get('subtitle'):tb(slide,s['subtitle'],.86,2.19,11.5,.56,18,muted)
            if typ=='metrics':
                items=s.get('items',[])[:4];width=11.7/max(1,len(items))
                for i,a in enumerate(items):
                    x=.84+i*width;shape(slide,x,3.0,width-.20,.035,accent)
                    tb(slide,a.get('value',''),x,3.23,width-.30,1.10,47,accent,True)
                    tb(slide,a.get('label',''),x,4.35,width-.30,.85,19,ink,True)
                    tb(slide,a.get('detail',a.get('body','')),x,5.22,width-.30,1.15,14,muted)
            elif typ in ('columns','process','timeline'):
                items=s.get('steps',s.get('items',[]))[:5];width=11.8/max(1,len(items))
                for i,a in enumerate(items):
                    x=.84+i*width;shape(slide,x,3.05,width-.2,.035,accent)
                    tb(slide,a.get('date',f'{i+1:02d}'),x,3.28,width-.25,.55,26,accent,True)
                    tb(slide,a.get('title',''),x,4.05,width-.24,.80,21,ink,True)
                    tb(slide,a.get('detail',a.get('body','')),x,4.98,width-.24,1.25,15,muted)
            elif typ=='comparison':
                for j,side in enumerate((s.get('left',{}),s.get('right',{}))):
                    x=.84+j*5.96;shape(slide,x,2.92,5.72,3.48,surface)
                    tb(slide,side.get('title',''),x+.30,3.19,5,.60,24,ink,True)
                    bullet_list(slide,side.get('bullets',[]),x+.32,3.95,5.05,16,.46)
            elif typ=='chart':
                rows=s.get('data',[])[:8];mx=max([float(r.get('value',0)) for r in rows]+[1]);width=11.7/max(1,len(rows))
                for i,a in enumerate(rows):
                    v=max(float(a.get('value',0)),0);bh=2.85*v/mx;x=.84+i*width
                    shape(slide,x+width*.20,6.05-bh,width*.55,max(bh,.008),accent)
                    tb(slide,a.get('label',''),x+.05,6.13,width-.10,.45,13,muted,align=PP_ALIGN.CENTER)
                    tb(slide,a.get('value',''),x+.05,5.85-bh,width-.10,.35,13,ink,True,align=PP_ALIGN.CENTER)
            elif typ=='quote':
                tb(slide,'“'+s.get('quote','')+'”',.84,3.07,11.65,2.25,38,ink,False,hfont)
                tb(slide,s.get('attribution',''),.84,5.75,10,.45,16,accent)
            elif typ=='image-split':
                # Keep editable text; image may be added from a safe local path when available.
                tb(slide,s.get('subtitle',''),.84,3.2,7.0,2.0,25,muted)
                tb(slide,'Hình minh họa: '+s.get('image_alt',''),8.2,3.3,4.0,1.5,17,muted)
            else:bullet_list(slide,s.get('bullets',[]),1.05,3.0,10.9,24,.85)
        shape(slide,.85,7.04,11.6,.012,line)
        src=' · '.join(map(str,s.get('sources',[])))
        if s.get('illustrative') or deck.get('demo'):src=(src+' · ' if src else '')+'MINH HỌA / SIMULATED'
        tb(slide,deck.get('brand','PERSONAL SLIDE STUDIO'),.85,7.14,2.7,.22,9,muted)
        tb(slide,src,3.1,7.14,8.1,.22,8,muted)
        tb(slide,f'{number:02d} / {len(deck["slides"]):02d}',11.8,7.14,.7,.22,9,ink,True)
    out.parent.mkdir(parents=True,exist_ok=True);prs.save(out);return out
