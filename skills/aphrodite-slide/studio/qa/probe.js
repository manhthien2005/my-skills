/* In-page QA probe for one slide (index passed as arg). Returns geometry/typography/contrast findings.
   Runs on the static (final-state) rendering so entrance transforms cannot create false positives. */
(idx) => {
  const slide = document.querySelectorAll('.stage > .slide')[idx];
  const S = slide.getBoundingClientRect();
  const out = { overflow: [], overlap: [], footer: [], small_text: [], contrast: [], images: [], orphans: [], clipped: [], fill: null, words: 0 };
  const isDecor = el => el.closest('.bg, .sec-num, .notes, .credit, svg, .shade, .qmark, .statement-mark') && !el.matches('svg');
  const visible = el => { const cs = getComputedStyle(el); return cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity > 0.05; };
  const label = el => (el.className && el.className.baseVal === undefined ? el.className : el.tagName).toString().split(' ').filter(c => c && c !== 'a' && c !== 'in').slice(0, 3).join('.') || el.tagName;
  const textOf = el => (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60);
  // bounds of the element's own text (not its block box), so full-width blocks don't create false overlaps
  const textRect = el => {
    let l = Infinity, t = Infinity, r = -Infinity, b = -Infinity;
    el.childNodes.forEach(n => {
      if (n.nodeType !== 3 || !n.textContent.trim()) return;
      const rg = document.createRange(); rg.selectNodeContents(n);
      Array.from(rg.getClientRects()).forEach(q => { if (q.width < 1) return; l = Math.min(l, q.left); t = Math.min(t, q.top); r = Math.max(r, q.right); b = Math.max(b, q.bottom); });
    });
    // Range rects span the font's full ascent+descent; inset by 0.15em so tight display line-heights don't read as overlaps.
    const fs = parseFloat(getComputedStyle(el).fontSize) || 0, k = 0.15 * fs;
    return isFinite(l) ? { left: l, top: t + k, right: r, bottom: b - k, width: r - l, height: Math.max(1, b - t - 2 * k) } : el.getBoundingClientRect();
  };

  // text leaves: elements with own non-empty text nodes
  const leaves = [];
  slide.querySelectorAll('*').forEach(el => {
    if (isDecor(el) || !visible(el)) return;
    const own = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && !el.closest('svg')) leaves.push(el);
  });
  const foot = slide.querySelector('.foot');
  const F = foot ? foot.getBoundingClientRect() : null;
  const tol = 2;
  // 1. outside slide bounds / clipped by container
  slide.querySelectorAll('*').forEach(el => {
    if (isDecor(el) || !visible(el) || el.closest('.foot')) return;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return;
    if (el.closest('.media, .l-full-bleed-image .media')) return;
    if (r.right > S.right + tol || r.left < S.left - tol || r.bottom > S.bottom + tol || r.top < S.top - tol)
      out.overflow.push({ el: label(el), text: textOf(el), box: [Math.round(r.left - S.left), Math.round(r.top - S.top), Math.round(r.width), Math.round(r.height)] });
  });
  // 2. text overflowing its own box (scroll size beyond client size)
  leaves.forEach(el => {
    const cs = getComputedStyle(el);
    if (el.closest('.foot')) return;
    if ((el.scrollHeight > el.clientHeight + 3 && cs.overflowY !== 'visible') || (el.scrollWidth > el.clientWidth + 3 && cs.overflowX !== 'visible' && cs.textOverflow !== 'ellipsis'))
      out.clipped.push({ el: label(el), text: textOf(el) });
  });
  // 3. content colliding with footer
  if (F) leaves.forEach(el => {
    if (el.closest('.foot')) return;
    const r = textRect(el);
    if (r.bottom > F.top - 8 && r.right > F.left && r.left < F.right) out.footer.push({ el: label(el), text: textOf(el) });
  });
  // 4. text-on-text overlap (pairs of leaves that are not ancestor/descendant)
  const rects = leaves.filter(el => !el.closest('.foot')).map(el => ({ el, r: textRect(el) }));
  for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) {
    const a = rects[i], b = rects[j];
    if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
    const w = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left);
    const h = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top);
    if (w > 4 && h > 4 && w * h > 0.15 * Math.min(a.r.width * a.r.height, b.r.width * b.r.height))
      out.overlap.push({ a: label(a.el) + ': ' + textOf(a.el).slice(0, 30), b: label(b.el) + ': ' + textOf(b.el).slice(0, 30) });
    if (out.overlap.length > 8) break;
  }
  // 5. min font size + contrast
  const parseRGB = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(',').map(x => parseFloat(x)); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const blend = (top, bot) => ({ r: top.r * top.a + bot.r * (1 - top.a), g: top.g * top.a + bot.g * (1 - top.a), b: top.b * top.a + bot.b * (1 - top.a), a: 1 });
  const bgOf = el => {
    const layers = [];
    for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
      const c = parseRGB(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0) { layers.push(c); if (c.a >= 0.99) break; }
      if (n === slide) break;
    }
    let base = { r: 255, g: 255, b: 255, a: 1 };
    for (let k = layers.length - 1; k >= 0; k--) base = blend(layers[k], base);
    return base;
  };
  const onImage = slide.matches('.photo');
  leaves.forEach(el => {
    const cs = getComputedStyle(el);
    const size = parseFloat(cs.fontSize);
    if (size < 16) out.small_text.push({ el: label(el), size, text: textOf(el) });
    if (onImage || el.closest('.media')) return; // background is an image: contrast must be judged visually
    const fg = parseRGB(cs.color); if (!fg) return;
    const bg = bgOf(el);
    const f = blend(fg, bg);
    const L1 = lum(f), L2 = lum(bg);
    const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    const large = size >= 24 || (size >= 18.6 && +cs.fontWeight >= 700);
    const need = large ? 3 : 4.5;
    if (ratio < need) out.contrast.push({ el: label(el), ratio: Math.round(ratio * 100) / 100, need, size, text: textOf(el) });
  });
  // 6. broken images
  slide.querySelectorAll('img').forEach(img => { if (!img.complete || img.naturalWidth === 0) out.images.push(img.getAttribute('src').slice(0, 80)); });
  // 7. orphan word on last line of headlines
  slide.querySelectorAll('.title, .display, .statement').forEach(h => {
    const range = document.createRange(); range.selectNodeContents(h);
    const lines = []; Array.from(range.getClientRects()).forEach(r => { const l = lines.find(x => Math.abs(x.top - r.top) < 6); if (l) { l.w += r.width; } else lines.push({ top: r.top, w: r.width }); });
    if (lines.length > 1) { const max = Math.max(...lines.map(l => l.w)); const last = lines[lines.length - 1]; if (last.w < max * 0.18) out.orphans.push(textOf(h)); }
  });
  // 8. fill ratio: how much of the content area is used
  const inner = slide.querySelector('.slide-inner, .split .text');
  if (inner) {
    let top = Infinity, bottom = -Infinity;
    leaves.concat(Array.from(slide.querySelectorAll('svg:not(.links), .card, img'))).forEach(el => {
      if (el.closest('.foot, .bg, .notes')) return; const r = el.getBoundingClientRect(); if (r.height < 1) return; top = Math.min(top, r.top); bottom = Math.max(bottom, r.bottom);
    });
    const I = inner.getBoundingClientRect();
    out.fill = isFinite(top) ? Math.round((bottom - top) / Math.max(1, (F ? F.top : S.bottom) - S.top - 80) * 100) / 100 : 0;
  }
  out.words = (slide.querySelector('.slide-inner, .split') || slide).innerText.split(/\s+/).filter(Boolean).length;
  return out;
}

