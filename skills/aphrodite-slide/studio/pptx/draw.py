"""PPTX drawing primitives on python-pptx: real-metric text fitting, shapes without default shadows, pictures with
cover-crop, soft orbs, alpha fills, arrowheads, native slide transitions and (experimental) entrance timing."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from lxml import etree
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt, Emu

from ..common import runs as split_runs, plain

PX = 1 / 144  # 1920px stage == 13.333in -> 144 px per inch; font px -> pt is px/2
WIN_FONTS = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
FONT_FILES = {('Calibri', False): 'calibri.ttf', ('Calibri', True): 'calibrib.ttf', ('Cambria', False): 'cambria.ttc',
              ('Cambria', True): 'cambriab.ttf', ('Segoe UI', False): 'segoeui.ttf', ('Segoe UI', True): 'segoeuib.ttf',
              ('Segoe UI Semibold', False): 'seguisb.ttf', ('Segoe UI Semibold', True): 'segoeuib.ttf', ('Arial', False): 'arial.ttf',
              ('Arial', True): 'arialbd.ttf', ('Consolas', False): 'consola.ttf', ('Consolas', True): 'consolab.ttf',
              ('Times New Roman', False): 'times.ttf', ('Times New Roman', True): 'timesbd.ttf'}


def rgb(h: str) -> RGBColor:
    return RGBColor.from_string(h.lstrip('#')[:6].upper())


@lru_cache(maxsize=64)
def _pil_font(name: str, bold: bool, size100: int):
    try:
        from PIL import ImageFont
    except ImportError:
        return None
    f = FONT_FILES.get((name, bold)) or FONT_FILES.get((name, False))
    for base in (WIN_FONTS, Path('/usr/share/fonts/truetype/msttcorefonts'), Path('/Library/Fonts')):
        if f and (base / f).exists():
            try:
                return ImageFont.truetype(str(base / f), size100)
            except OSError:
                pass
    return None


def text_width_in(text: str, font: str, size_pt: float, bold: bool = False) -> float:
    pf = _pil_font(font, bold, 100)
    if pf is None:
        return len(text) * size_pt * (0.55 if bold else 0.5) / 72
    return pf.getlength(text) / 100 * size_pt / 72


def wrap_lines(text: str, font: str, size_pt: float, width_in: float, bold: bool = False) -> int:
    n = 0
    for para in plain(text).split('\n'):
        words, line = para.split(' '), ''
        n += 1
        for w in words:
            cand = (line + ' ' + w).strip()
            if text_width_in(cand, font, size_pt, bold) <= width_in or not line:
                line = cand
            else:
                n += 1
                line = w
    return n


def fit_size(text: str, font: str, size: float, min_size: float, w: float, h: float, bold=False, spacing=1.12, max_lines=None):
    """Largest size in [min_size, size] whose wrapped text fits w x h (inches). Returns (size, lines, fits)."""
    s = size
    while True:
        lines = wrap_lines(text, font, s, w, bold)
        need = lines * s * spacing / 72
        if (need <= h and (not max_lines or lines <= max_lines)) or s <= min_size:
            return s, lines, need <= h + 0.02
        s = max(min_size, s - 2)


class Canvas:
    """One slide + theme; tracks shapes per build group and fit warnings."""

    def __init__(self, slide, theme: dict, fonts: dict, dark: bool, warnings: list, sid: str):
        self.s, self.t, self.f, self.dark, self.warn, self.sid = slide, theme, fonts, dark, warnings, sid
        c = theme['colors']
        self.c = dict(c)
        if dark:
            self.c.update({'bg': c['dark_bg'], 'surface': c['dark_surface'], 'surface_alt': c['dark_surface'], 'ink': c['dark_ink'],
                           'muted': c['dark_muted'], 'subtle': c['dark_muted'], 'accent_strong': c['dark_accent'],
                           'line': _mix(c['dark_bg'], '#FFFFFF', .18), 'accent_soft': _mix(c['dark_bg'], '#FFFFFF', .08)})
        self.groups: list[list[int]] = []
        self._g = None

    # -- grouping for entrance animations
    def group(self):
        self._g = []
        self.groups.append(self._g)
        return self

    def _track(self, shp):
        if self._g is not None:
            self._g.append(shp.shape_id)
        return shp

    # -- primitives
    def rect(self, x, y, w, h, fill=None, line=None, radius=None, line_w=1.0, shape=None, alpha=None):
        kind = shape or (MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE)
        shp = self.s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
        shp.shadow.inherit = False
        if radius and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
            shp.adjustments[0] = max(0.0, min(0.5, radius / max(0.01, min(w, h))))
        if fill:
            shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fill)
            if alpha is not None:
                set_alpha(shp, alpha)
        else:
            shp.fill.background()
        if line:
            shp.line.color.rgb = rgb(line); shp.line.width = Pt(line_w)
        else:
            shp.line.fill.background()
        if shp.has_text_frame:
            shp.text_frame.text = ''
        return self._track(shp)

    def oval(self, x, y, w, h, fill=None, line=None, line_w=1.5, dash=False):
        shp = self.rect(x, y, w, h, fill=fill, line=line, line_w=line_w, shape=MSO_SHAPE.OVAL)
        if dash and line:
            ln = shp.line._get_or_add_ln()
            prst = etree.SubElement(ln, qn('a:prstDash')); prst.set('val', 'dash')
        return shp

    def line(self, x1, y1, x2, y2, color, width=1.5, arrow=False, dash=False):
        c = self.s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        c.shadow.inherit = False
        c.line.color.rgb = rgb(color); c.line.width = Pt(width)
        ln = c.line._get_or_add_ln()
        if dash:
            etree.SubElement(ln, qn('a:prstDash')).set('val', 'dash')
        if arrow:
            te = etree.SubElement(ln, qn('a:tailEnd')); te.set('type', 'triangle'); te.set('w', 'med'); te.set('len', 'med')
        return self._track(c)

    def text(self, x, y, w, h, text, size, color=None, bold=False, font='body', align='l', anchor='t', italic=False,
             min_size=None, spacing=1.12, caps=False, tracking=None, accent_bold=True, max_lines=None, check=True):
        fname = self.f[font] if font in self.f else font
        text = '' if text is None else str(text)
        if caps:
            text = text.upper()
        s = size
        if min_size and text:
            s, lines, fits = fit_size(text, fname, size, min_size, w, h, bold, spacing, max_lines)
            if not fits and check:
                self.warn.append({'slide': self.sid, 'code': 'pptx-text-fit', 'message': f'text may overflow box at {s:g}pt: "{plain(text)[:50]}"'})
        elif text and check:
            lines = wrap_lines(text, fname, s, w, bold)
            if lines * s * spacing / 72 > h + 0.05:
                self.warn.append({'slide': self.sid, 'code': 'pptx-text-fit', 'message': f'text may overflow box at {s:g}pt: "{plain(text)[:50]}"'})
        tb = self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}[anchor]
        bodyPr = tf._txBody.find(qn('a:bodyPr'))
        for child in list(bodyPr):
            bodyPr.remove(child)
        etree.SubElement(bodyPr, qn('a:noAutofit'))
        col = rgb(color or self.c['ink'])
        for pi, para_text in enumerate(text.split('\n')):
            p = tf.paragraphs[0] if pi == 0 else tf.add_paragraph()
            p.alignment = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER, 'r': PP_ALIGN.RIGHT}[align]
            p.line_spacing = spacing
            for seg, b in split_runs(para_text):
                r = p.add_run()
                r.text = seg
                r.font.size = Pt(s); r.font.name = fname; r.font.bold = bold or b; r.font.italic = italic
                r.font.color.rgb = rgb(self.c['accent_strong']) if (b and accent_bold) else col
                if tracking:
                    r.font._element.set('spc', str(int(tracking)))
        return self._track(tb)

    def picture(self, path: Path, x, y, w, h):
        from PIL import Image
        pic = self.s.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
        with Image.open(path) as im:
            iw, ih = im.size
        box, img = w / h, iw / ih
        if img > box:  # crop left/right
            cut = (1 - box / img) / 2
            pic.crop_left = pic.crop_right = cut
        else:
            cut = (1 - img / box) / 2
            pic.crop_top = pic.crop_bottom = cut
        return self._track(pic)

    def icon(self, name: str, x, y, d, bg=None, fg_png_dir: Path | None = None, num=None):
        """Coloured circle with a white Lucide icon (PNG) - or a number when the icon is unavailable."""
        circ = self.oval(x, y, d, d, fill=bg or self.c['accent_strong'])
        png = (fg_png_dir / f'{name}.png') if (name and fg_png_dir) else None
        if png and png.exists():
            k = d * 0.5
            self._track(self.s.shapes.add_picture(str(png), Inches(x + (d - k) / 2), Inches(y + (d - k) / 2), Inches(k), Inches(k)))
        elif num is not None:
            self.text(x, y, d, d, str(num), d * 72 * 0.38, color='#FFFFFF', bold=True, align='c', anchor='m', check=False)
        return circ

    def orb(self, cx, cy, r, color, alpha):
        """Soft radial-gradient orb (mimics the blurred HTML background)."""
        shp = self.s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r), Inches(cy - r), Inches(2 * r), Inches(2 * r))
        shp.shadow.inherit = False
        shp.line.fill.background()
        spPr = shp._element.spPr
        for tag in ('a:solidFill', 'a:noFill', 'a:gradFill'):
            for el in spPr.findall(qn(tag)):
                spPr.remove(el)
        grad = etree.fromstring(
            f'<a:gradFill xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" rotWithShape="1"><a:gsLst>'
            f'<a:gs pos="0"><a:srgbClr val="{color.lstrip("#")}"><a:alpha val="{int(alpha * 100000)}"/></a:srgbClr></a:gs>'
            f'<a:gs pos="100000"><a:srgbClr val="{color.lstrip("#")}"><a:alpha val="0"/></a:srgbClr></a:gs></a:gsLst>'
            f'<a:path path="circle"><a:fillToRect l="50000" t="50000" r="50000" b="50000"/></a:path></a:gradFill>')
        geom = spPr.find(qn('a:prstGeom'))
        geom.addnext(grad)
        return shp


def set_alpha(shp, alpha: float):
    fill = shp._element.spPr.find(qn('a:solidFill'))
    if fill is not None and len(fill):
        a = etree.SubElement(fill[0], qn('a:alpha'))
        a.set('val', str(int(alpha * 100000)))


def _mix(a: str, b: str, t: float) -> str:
    from ..common import mix
    return mix(a, b, t)


def add_transition(slide, kind: str | None, speed: str = 'med'):
    """Native slide transition (fade or push), inserted in schema order after <p:clrMapOvr>."""
    if not kind:
        return
    sld = slide._element
    for old in sld.findall(qn('p:transition')):
        sld.remove(old)
    tr = etree.Element(qn('p:transition'))
    tr.set('spd', speed)
    el = etree.SubElement(tr, qn('p:push' if kind == 'push' else 'p:fade'))
    if kind == 'push':
        el.set('dir', 'l')
    anchor = sld.find(qn('p:clrMapOvr'))
    (anchor if anchor is not None else sld.find(qn('p:cSld'))).addnext(tr)


def _effect(ids, spid: int, node: str, delay_ms: int, dur_ms: int) -> str:
    e1, e2, e3 = next(ids), next(ids), next(ids)
    return (f'<p:par><p:cTn id="{e1}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" nodeType="{node}">'
            f'<p:stCondLst><p:cond delay="{delay_ms}"/></p:stCondLst><p:childTnLst>'
            f'<p:set><p:cBhvr><p:cTn id="{e2}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:to><p:strVal val="visible"/></p:to></p:set>'
            f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{e3}" dur="{dur_ms}"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
            f'</p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>')


def add_entrances(slide, groups: list[list[int]], on_click: bool = False, dur_ms: int = 450, stagger_ms: int = 180):
    """Fade-in entrance per content group (experimental; QA opens the file in PowerPoint to verify).

    auto  (default): one automatic sequence after the slide transition; group k starts k*stagger_ms later
                     (PowerPoint shows: first "After Previous", the rest "With Previous" + delay).
    click (build):   one click per group, shapes inside a group fade together.
    """
    groups = [g for g in groups if g]
    if not groups:
        return
    ids = iter(range(3, 100000))
    pars = []
    if on_click:
        for g in groups:
            outer, inner = next(ids), next(ids)
            eff = ''.join(_effect(ids, spid, 'clickEffect' if k == 0 else 'withEffect', 0, dur_ms) for k, spid in enumerate(g))
            pars.append(f'<p:par><p:cTn id="{outer}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>'
                        f'<p:par><p:cTn id="{inner}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{eff}'
                        f'</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
    else:
        outer, inner = next(ids), next(ids)
        eff = ''
        for gi, g in enumerate(groups):
            for k, spid in enumerate(g):
                node = 'afterEffect' if (gi == 0 and k == 0) else 'withEffect'
                eff += _effect(ids, spid, node, gi * stagger_ms, dur_ms)
        pars.append(f'<p:par><p:cTn id="{outer}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
                    f'<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>'
                    f'<p:par><p:cTn id="{inner}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{eff}'
                    f'</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
    xml = ('<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:tnLst><p:par>'
           '<p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
           '<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
           + ''.join(pars) +
           '</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
           '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
           '</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')
    timing = etree.fromstring(xml)
    sld = slide._element
    for old in sld.findall(qn('p:timing')):
        sld.remove(old)
    tr = sld.find(qn('p:transition'))
    anchor = tr if tr is not None else sld.find(qn('p:clrMapOvr'))
    anchor.addnext(timing)
