/* Aphrodite-slide runtime: fixed-stage viewer, navigation, build steps, counters, notes, overview.
   No dependencies, works offline from file://. Exposes window.__deck for the renderer/QA. */
(function () {
  'use strict';
  var body = document.body, stage = document.querySelector('.stage');
  var slides = Array.prototype.slice.call(document.querySelectorAll('.stage > .slide'));
  var params = new URLSearchParams(location.search);
  var isStatic = params.has('static') || params.has('print');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var speed = parseFloat(params.get('speed') || '1') || 1;
  document.documentElement.style.setProperty('--speed', String(speed));
  if (isStatic) body.classList.add('static');
  var animOn = body.classList.contains('anim-on') && !isStatic && !reduce;
  var cur = -1, step = 0, t0 = null;
  var hud = document.querySelector('.hud i'), counter = document.querySelector('.counter');
  var drawer = document.querySelector('.drawer'), overview = document.querySelector('.overview');

  slides.forEach(function (s) {
    var max = 0;
    s.querySelectorAll('.a[data-step]').forEach(function (el) { max = Math.max(max, +el.dataset.step || 0); });
    s.dataset.steps = String(max);
  });

  function fit() {
    if (isStatic) { stage.style.transform = 'none'; return; }
    var k = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
    stage.style.transform = 'scale(' + k + ')';
  }

  function parseNum(txt) {
    var m = /^(\D*?)(-?\d[\d.,\s]*)(.*)$/.exec(txt.trim());
    if (!m) return null;
    var raw = m[2].trim(), dec = null;
    var lastComma = raw.lastIndexOf(','), lastDot = raw.lastIndexOf('.');
    var vi = document.documentElement.lang === 'vi';
    if (vi) { if (lastComma > -1) dec = ','; }
    else if (lastDot > -1 && raw.length - lastDot - 1 !== 3) dec = '.';
    else if (lastComma > -1 && raw.length - lastComma - 1 !== 3) dec = ',';
    var grp = dec === ',' ? '.' : (dec === '.' ? ',' : (vi ? '.' : ','));
    var clean = raw.split(grp).join('').replace(/\s/g, '').replace(',', '.');
    var val = parseFloat(clean);
    if (isNaN(val)) return null;
    var decimals = dec ? (raw.length - raw.lastIndexOf(dec) - 1) : 0;
    return { pre: m[1], val: val, post: m[3], decimals: decimals, dec: dec || (vi ? ',' : '.'), grp: grp, grouped: raw.indexOf(grp) > -1 };
  }
  function fmt(p, v) {
    var s = v.toFixed(p.decimals), parts = s.split('.');
    var int = parts[0];
    if (p.grouped) int = int.replace(/\B(?=(\d{3})+(?!\d))/g, p.grp);
    return p.pre + int + (parts[1] ? p.dec + parts[1] : '') + p.post;
  }
  function runCounters(s, animate) {
    s.querySelectorAll('[data-count]').forEach(function (el) {
      var final = el.getAttribute('data-count');
      var p = parseNum(final);
      if (!p || !animate) { el.textContent = final; return; }
      var start = null, dur = 1100 * speed, delay = 250 * speed;
      el.textContent = fmt(p, 0);
      function tick(ts) {
        if (start === null) start = ts + delay;
        var x = Math.min(1, Math.max(0, (ts - start) / dur));
        var e = 1 - Math.pow(1 - x, 3);
        el.textContent = x >= 1 ? final : fmt(p, p.val * e);
        if (x < 1 && s.classList.contains('active')) requestAnimationFrame(tick); else el.textContent = final;
      }
      requestAnimationFrame(tick);
    });
  }

  function setStep(s, k) {
    s.querySelectorAll('.a').forEach(function (el) {
      var st = +el.dataset.step || 0;
      el.classList.toggle('in', st <= k);
    });
  }

  function go(i, opts) {
    opts = opts || {};
    i = Math.max(0, Math.min(slides.length - 1, i));
    var prev = slides[cur];
    var next = slides[i];
    if (prev && prev !== next) {
      prev.classList.remove('active');
      if (animOn) { prev.classList.add('leaving'); setTimeout(function () { prev.classList.remove('leaving'); setStep(prev, -1); }, 900 * speed); }
      else setStep(prev, -1);
    }
    cur = i;
    var full = +next.dataset.steps;
    step = opts.allSteps ? full : 0;
    next.classList.add('active');
    if (animOn) {
      setStep(next, -1);
      void next.offsetWidth; // restart transitions
      requestAnimationFrame(function () { requestAnimationFrame(function () { setStep(next, step); }); });
    } else setStep(next, isStatic ? full : step);
    runCounters(next, animOn && !opts.allSteps);
    if (hud) hud.style.width = ((i + 1) / slides.length * 100) + '%';
    if (counter) counter.textContent = (i + 1) + ' / ' + slides.length;
    if (!isStatic) history.replaceState(null, '', '#/' + (i + 1));
    renderNotes();
  }
  function nextStep() {
    var s = slides[cur];
    if (step < +s.dataset.steps) { step++; setStep(s, step); return; }
    if (cur < slides.length - 1) go(cur + 1);
  }
  function prevStep() {
    if (cur > 0) go(cur - 1, { allSteps: true });
  }
  function finish() { var s = slides[cur]; step = +s.dataset.steps; setStep(s, step); runCounters(s, false); }

  function renderNotes() {
    if (!drawer) return;
    var n = slides[cur] && slides[cur].querySelector('.notes');
    var txt = n ? n.innerHTML : '';
    drawer.querySelector('.content').innerHTML = txt || '<em>(Không có ghi chú / no notes)</em>';
  }
  function tickTimer() {
    if (!drawer || t0 === null) return;
    var sec = Math.floor((Date.now() - t0) / 1000);
    drawer.querySelector('.timer').textContent = String(Math.floor(sec / 60)).padStart(2, '0') + ':' + String(sec % 60).padStart(2, '0');
  }
  function toggleNotes() { if (!drawer) return; drawer.classList.toggle('open'); if (t0 === null) { t0 = Date.now(); setInterval(tickTimer, 1000); } }

  function toggleOverview() {
    if (!overview) return;
    if (!overview.dataset.built) {
      slides.forEach(function (s, i) {
        var t = document.createElement('div'); t.className = 'thumb'; t.dataset.i = i;
        var inner = document.createElement('div'); inner.className = 'inner';
        var c = s.cloneNode(true); c.classList.add('active'); inner.appendChild(c); t.appendChild(inner);
        var lab = document.createElement('span'); lab.textContent = (i + 1); t.appendChild(lab);
        t.addEventListener('click', function () { overview.classList.remove('open'); go(i, { allSteps: true }); });
        overview.appendChild(t);
      });
      overview.dataset.built = '1';
    }
    overview.classList.toggle('open');
    overview.querySelectorAll('.thumb').forEach(function (t) {
      t.classList.toggle('cur', +t.dataset.i === cur);
      var inner = t.querySelector('.inner'); inner.style.transform = 'scale(' + (t.clientWidth / 1920) + ')';
    });
  }

  window.addEventListener('resize', fit);
  window.addEventListener('keydown', function (e) {
    if (e.target && /input|textarea/i.test(e.target.tagName)) return;
    var k = e.key;
    if (['ArrowRight', 'PageDown', ' ', 'Enter'].indexOf(k) > -1) { e.preventDefault(); nextStep(); }
    else if (['ArrowLeft', 'PageUp', 'Backspace'].indexOf(k) > -1) { e.preventDefault(); prevStep(); }
    else if (k === 'Home') go(0); else if (k === 'End') go(slides.length - 1, { allSteps: true });
    else if (k === 'f' || k === 'F') { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen && document.documentElement.requestFullscreen(); }
    else if (k === 'n' || k === 'N') toggleNotes();
    else if (k === 'o' || k === 'O') toggleOverview();
    else if (k === 'Escape') { overview && overview.classList.remove('open'); drawer && drawer.classList.remove('open'); }
  });
  var tx = null;
  window.addEventListener('touchstart', function (e) { tx = e.touches[0].clientX; }, { passive: true });
  window.addEventListener('touchend', function (e) {
    if (tx === null) return; var dx = e.changedTouches[0].clientX - tx; tx = null;
    if (Math.abs(dx) > 50) { if (dx < 0) nextStep(); else prevStep(); }
  });
  stage.addEventListener('click', function (e) { if (!e.target.closest('a')) nextStep(); });

  var start = 0, m = /#\/(\d+)/.exec(location.hash);
  if (params.get('slide')) start = (+params.get('slide') || 1) - 1; else if (m) start = (+m[1] || 1) - 1;
  fit();
  go(start, { allSteps: isStatic });
  window.__deck = { count: slides.length, go: function (i, all) { go(i, { allSteps: !!all }); }, finish: finish,
    current: function () { return cur; }, steps: function (i) { return +slides[i].dataset.steps; }, static: isStatic, ready: true };
})();

