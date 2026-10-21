"""가격 작은 창 (PiP): 다른 탭·앱을 써도 화면 위에 떠 있는 실시간 시세.

- 메뉴 오른쪽(다크 모드 버튼 옆) 버튼 → 코인 고르기 → '띄우기'
- 컴퓨터(크롬·엣지): 진짜 작은 창(Document PiP)으로 띄움
- 휴대폰(안드로이드 크롬·삼성 인터넷): 시세를 그린 그림을 '영상 PiP'로 띄움 → 다른 앱 위에도 떠 있음
- 내 포지션이 있으면 맨 위에 자동으로 넣고, 진입가 기준 수익률(레버리지 반영)도 같이 보여줌
- 시세는 Bitget 공개 실시간 스트림(USDT 무기한)
"""
import json

import streamlit.components.v1 as components

_JS = r"""
(function () {
  const d = document, W = window, KEY = 'mung_pip';
  let TOP = W; try { if (W.top.document) TOP = W.top; } catch (e) {}
  let S = { syms: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'], pos: [] };
  try { Object.assign(S, JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} };
  const ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="4" width="19" height="15" rx="2.5"/><rect x="12" y="11" width="7" height="5.5" rx="1.2" fill="currentColor" stroke="none"/></svg>';
  const base = s => s.replace(/USDT$/, '');
  const fmt = v => { if (v == null || !isFinite(v)) return '-'; const a = Math.abs(v), dg = a >= 1000 ? 1 : a >= 10 ? 2 : a >= 1 ? 3 : a >= 0.01 ? 4 : 6;
    return v.toLocaleString('en-US', { minimumFractionDigits: dg, maximumFractionDigits: dg }); };
  const pc = v => v == null ? '' : (v >= 0 ? '+' : '') + v.toFixed(2) + '%';
  const UP = '#13C296', DN = '#FF5468';

  // ---- 포지션 (히스토리 화면이 10초마다 넘겨줌) ----
  W.addEventListener('mg-pos', () => { S.pos = W.__mgPos || []; save(); if (open) { subscribe(); render(); } refreshSheet(); });
  const posOf = s => (S.pos || []).find(p => p.s === s);
  const rows = () => { const out = []; (S.pos || []).forEach(p => { if (!out.includes(p.s)) out.push(p.s); }); S.syms.forEach(s => { if (!out.includes(s)) out.push(s); }); return out.slice(0, 5); };

  // ---- 실시간 시세 ----
  const T = {}; let ws = null, subs = new Set(), pingT = null, open = false;
  function connect() {
    if (ws && ws.readyState <= 1) return;
    try { ws = new WebSocket('wss://ws.bitget.com/v2/ws/public'); } catch (e) { return; }
    subs = new Set();
    ws.onopen = () => { subscribe(); clearInterval(pingT); pingT = setInterval(() => { try { ws.send('ping'); } catch (e) {} }, 25000); };
    ws.onmessage = ev => { if (ev.data === 'pong') return; let m; try { m = JSON.parse(ev.data); } catch (e) { return; }
      if (!m.data || !m.arg || m.arg.channel !== 'ticker') return;
      for (const x of m.data) { const s = x.instId || m.arg.instId, last = +x.lastPr; if (!last) continue;
        const o = T[s] || {}; T[s] = { last, prev: o.last, pct: x.change24h != null ? +x.change24h * 100 : o.pct, t: Date.now() }; }
      render(); };
    ws.onclose = () => { clearInterval(pingT); if (open) setTimeout(connect, 2000); };
  }
  function subscribe() {
    if (!ws || ws.readyState !== 1) return;
    const want = rows().filter(s => !subs.has(s));
    if (want.length) { ws.send(JSON.stringify({ op: 'subscribe', args: want.map(s => ({ instType: 'USDT-FUTURES', channel: 'ticker', instId: s })) })); want.forEach(s => subs.add(s)); }
  }
  const roe = (p, last) => p && p.e ? (last / p.e - 1) * (p.side === 'SHORT' ? -1 : 1) * (p.lev || 1) * 100 : null;

  // ---- 그리기 ----
  let pipWin = null, video = null, canvas = null, lastDraw = 0, drawT = null;
  function render() {
    if (!open) return;
    const now = Date.now(); if (now - lastDraw < 250) { clearTimeout(drawT); drawT = setTimeout(render, 260); return; } lastDraw = now;
    if (pipWin) renderDoc(); else if (canvas) renderCanvas();
  }
  function renderDoc() {
    const b = pipWin.document.getElementById('rows'); if (!b) return;
    b.innerHTML = rows().map(s => { const t = T[s] || {}, p = posOf(s), r = p && t.last ? roe(p, t.last) : null;
      const fl = t.prev && t.last !== t.prev ? (t.last > t.prev ? 'fu' : 'fd') : '';
      return `<div class="r"><div class="l"><b>${base(s)}</b>${p ? `<em class="${p.side === 'SHORT' ? 'dn' : 'up'}">${p.side === 'SHORT' ? '숏' : '롱'} ${p.lev}x</em>` : ''}</div>
        <div class="v"><b class="${fl}">${fmt(t.last)}</b><span class="${(t.pct || 0) >= 0 ? 'up' : 'dn'}">${pc(t.pct)}${r != null ? ` · <i class="${r >= 0 ? 'up' : 'dn'}">내 ${pc(r)}</i>` : ''}</span></div></div>`; }).join('');
  }
  function renderCanvas() {
    const list = rows(), Wd = 600, rh = 104, H = Math.max(Math.round(Wd / 2.3), list.length * rh + 24);
    if (canvas.height !== H) canvas.height = H;
    const c = canvas.getContext('2d');
    c.fillStyle = '#0D1015'; c.fillRect(0, 0, Wd, H);
    const y0 = (H - list.length * rh) / 2;
    list.forEach((s, i) => { const t = T[s] || {}, p = posOf(s), r = p && t.last ? roe(p, t.last) : null, y = y0 + i * rh;
      if (i) { c.fillStyle = 'rgba(255,255,255,.07)'; c.fillRect(28, y, Wd - 56, 2); }
      c.textBaseline = 'middle';
      c.fillStyle = '#fff'; c.font = '800 38px Pretendard, -apple-system, Roboto, sans-serif'; c.textAlign = 'left'; c.fillText(base(s), 30, y + rh / 2 - (p ? 14 : 0));
      if (p) { c.fillStyle = p.side === 'SHORT' ? DN : UP; c.font = '700 26px Pretendard, -apple-system, Roboto, sans-serif'; c.fillText((p.side === 'SHORT' ? '숏 ' : '롱 ') + p.lev + 'x', 30, y + rh / 2 + 24); }
      const up = (t.pct || 0) >= 0;
      c.textAlign = 'right';
      c.fillStyle = t.prev && t.last !== t.prev ? (t.last > t.prev ? UP : DN) : '#fff'; c.font = '800 44px Pretendard, -apple-system, Roboto, sans-serif';
      c.fillText(fmt(t.last), Wd - 30, y + rh / 2 - 14);
      c.font = '700 26px Pretendard, -apple-system, Roboto, sans-serif';
      let x = Wd - 30;
      if (r != null) { c.fillStyle = r >= 0 ? UP : DN; const tx = '내 ' + pc(r); c.fillText(tx, x, y + rh / 2 + 26); x -= c.measureText(tx).width + 18; }
      c.fillStyle = up ? UP : DN; c.fillText(pc(t.pct), x, y + rh / 2 + 26);
    });
  }

  const DOC_CSS = `*{box-sizing:border-box;margin:0}body{background:#0D1015;color:#fff;font-family:Pretendard,-apple-system,'Segoe UI',sans-serif;padding:6px 14px;user-select:none}
    .r{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:9px 0}.r+.r{border-top:1px solid rgba(255,255,255,.07)}
    .l b{display:block;font-size:15px;font-weight:800}.l em{display:block;font-style:normal;font-size:11px;font-weight:700;margin-top:1px}
    .v{text-align:right}.v b{display:block;font-size:18px;font-weight:800;font-variant-numeric:tabular-nums;transition:color .4s}.v span{display:block;font-size:11.5px;font-weight:700;font-variant-numeric:tabular-nums;margin-top:1px}
    .v i{font-style:normal}.up{color:${UP}}.dn{color:${DN}}.fu{color:${UP}}.fd{color:${DN}}`;

  async function start() {
    open = true; connect(); subscribe(); setBtn();
    const n = rows().length;
    // 1) 컴퓨터 크롬·엣지: 진짜 작은 창
    const dp = TOP.documentPictureInPicture;
    if (dp && !matchMedia('(pointer: coarse)').matches) {
      try {
        pipWin = await dp.requestWindow({ width: 250, height: Math.min(360, 22 + n * 58) });
        const st = pipWin.document.createElement('style'); st.textContent = DOC_CSS; pipWin.document.head.appendChild(st);
        pipWin.document.title = 'Mung9_ 시세';
        pipWin.document.body.innerHTML = '<div id="rows"></div>';
        pipWin.addEventListener('pagehide', stop);
        render(); return;
      } catch (e) { pipWin = null; }
    }
    // 2) 휴대폰 등: 시세 그림을 영상으로 만들어 영상 PiP
    try {
      canvas = d.createElement('canvas'); canvas.width = 600; canvas.height = 260; renderCanvas();
      video = d.createElement('video'); video.muted = true; video.playsInline = true; video.autoplay = true;
      video.style.cssText = 'position:fixed;left:0;bottom:0;width:2px;height:2px;opacity:0;pointer-events:none;z-index:-1';
      d.body.appendChild(video);
      video.srcObject = canvas.captureStream(4);
      await video.play();
      await video.requestPictureInPicture();
      video.addEventListener('leavepictureinpicture', stop);
      clearInterval(W.__mgPipTick); W.__mgPipTick = setInterval(() => { if (canvas) renderCanvas(); }, 1000);  // 시세가 조용해도 화면이 멈춰 보이지 않게
    } catch (e) { stop(); toast('이 브라우저는 작은 창 띄우기를 지원하지 않아요 (크롬 권장)'); }
  }
  function stop() {
    open = false; clearInterval(W.__mgPipTick);
    try { if (pipWin) pipWin.close(); } catch (e) {} pipWin = null;
    try { if (d.pictureInPictureElement) d.exitPictureInPicture(); } catch (e) {}
    if (video) { try { video.srcObject = null; video.remove(); } catch (e) {} } video = null; canvas = null;
    try { if (ws) ws.close(); } catch (e) {} ws = null;
    setBtn(); refreshSheet();
  }
  function toast(msg) { const t = d.createElement('div'); t.className = 'mg-pip-toast'; t.textContent = msg; d.body.appendChild(t); setTimeout(() => t.remove(), 3200); }

  // ---- 메뉴 버튼 + 고르는 창 ----
  function setBtn() { d.querySelectorAll('.mg-pip-btn').forEach(b => b.classList.toggle('on', open)); }
  function fill() {
    d.querySelectorAll('.mg-theme-slot').forEach(slot => {
      if (slot.querySelector('.mg-pip-btn')) return;
      const b = d.createElement('button'); b.type = 'button'; b.className = 'mg-pip-btn' + (open ? ' on' : ''); b.title = '가격 작은 창'; b.setAttribute('aria-label', '가격 작은 창'); b.innerHTML = ICON;
      slot.insertBefore(b, slot.firstChild);
    });
  }
  let sheet = null;
  function refreshSheet() {
    if (!sheet) return;
    const pos = (S.pos || []).map(p => p.s);
    sheet.querySelector('.ps-chips').innerHTML = rows().map(s => `<span class="ps-chip${pos.includes(s) ? ' pos' : ''}">${base(s)}${pos.includes(s) ? '<em>포지션</em>' : `<button data-rm="${s}" aria-label="빼기">✕</button>`}</span>`).join('')
      + (rows().length < 5 ? '' : '<span class="ps-max">최대 5개</span>');
    sheet.querySelector('.ps-go').textContent = open ? '작은 창 닫기' : '띄우기';
    sheet.querySelector('.ps-go').classList.toggle('off', open);
  }
  function openSheet() {
    if (sheet) { closeSheet(); return; }
    sheet = d.createElement('div'); sheet.id = 'mg-pip-sheet';
    sheet.innerHTML = `<div class="ps-h"><b>가격 작은 창</b><span>다른 앱·탭을 써도 화면 위에 시세가 떠 있어요</span></div>
      <div class="ps-chips"></div>
      <form class="ps-add"><input placeholder="코인 추가 (예: SUI, DOGE)" autocomplete="off" autocapitalize="characters"><button type="submit">추가</button></form>
      <div class="ps-err"></div>
      <button class="ps-go" type="button">띄우기</button>`;
    d.body.appendChild(sheet);
    refreshSheet();
    sheet.addEventListener('click', e => {
      const rm = e.target.closest('[data-rm]');
      if (rm) { S.syms = S.syms.filter(s => s !== rm.dataset.rm); save(); refreshSheet(); if (open) render(); return; }
      if (e.target.closest('.ps-go')) { if (open) stop(); else { closeSheet(); start(); } }
    });
    sheet.querySelector('.ps-add').addEventListener('submit', async e => {
      e.preventDefault();
      const inp = sheet.querySelector('input'), err = sheet.querySelector('.ps-err');
      let s = inp.value.trim().toUpperCase().replace(/[^A-Z0-9]/g, ''); if (!s) return; if (!s.endsWith('USDT')) s += 'USDT';
      if (rows().includes(s)) { inp.value = ''; return; }
      if (rows().length >= 5) { err.textContent = '최대 5개까지 띄울 수 있어요'; return; }
      try { const j = await (await fetch(`https://api.bitget.com/api/v2/mix/market/ticker?productType=USDT-FUTURES&symbol=${s}`)).json();
        if (!j.data || !j.data.length) throw 0; } catch (x) { err.textContent = `${base(s)} 은(는) Bitget 무기한 선물에 없어요`; return; }
      err.textContent = ''; inp.value = ''; S.syms.push(s); save(); refreshSheet(); if (open) { subscribe(); render(); }
    });
    setTimeout(() => d.addEventListener('pointerdown', outside, true), 0);
  }
  function outside(e) { if (sheet && !sheet.contains(e.target) && !e.target.closest('.mg-pip-btn')) closeSheet(); }
  function closeSheet() { if (sheet) sheet.remove(); sheet = null; d.removeEventListener('pointerdown', outside, true); }
  d.addEventListener('click', e => { if (e.target.closest('.mg-pip-btn')) openSheet(); });

  const css = d.createElement('style');
  css.textContent = `
  .mg-theme-slot { gap: 8px; }
  .mg-pip-btn { width: 38px; height: 38px; border-radius: 12px; border: 1px solid var(--mg-border); background: var(--mg-card); color: var(--mg-text);
    display: flex; align-items: center; justify-content: center; cursor: pointer; padding: 0; transition: border-color .15s, transform .15s, color .15s; }
  .mg-pip-btn:hover { border-color: var(--mg-accent); } .mg-pip-btn:active { transform: scale(.94); }
  .mg-pip-btn svg { width: 18px; height: 18px; }
  .mg-pip-btn.on { color: #fff; background: var(--mg-accent, #3182F6); border-color: transparent; }
  #mg-pip-sheet { position: fixed; top: 74px; right: 18px; z-index: 999995; width: 320px; padding: 18px; border-radius: 18px; background: var(--mg-card, #fff); color: var(--mg-text, #191F28);
    border: 1px solid var(--mg-border, #E5E8EB); box-shadow: 0 18px 48px rgba(0,0,0,.22); font-family: Pretendard, -apple-system, sans-serif; animation: mg-ps .22s ease; }
  @keyframes mg-ps { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: none; } }
  #mg-pip-sheet .ps-h b { display: block; font-size: 16px; font-weight: 800; } #mg-pip-sheet .ps-h span { display: block; font-size: 12.5px; color: var(--mg-sub, #8B95A1); margin-top: 3px; }
  #mg-pip-sheet .ps-chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 14px 0 10px; }
  #mg-pip-sheet .ps-chip { display: inline-flex; align-items: center; gap: 4px; height: 30px; padding: 0 6px 0 11px; border-radius: 9px; background: var(--mg-soft, #F2F4F6); font-size: 13px; font-weight: 700; }
  #mg-pip-sheet .ps-chip.pos { padding-right: 10px; } #mg-pip-sheet .ps-chip em { font-style: normal; font-size: 10.5px; font-weight: 800; color: var(--mg-accent, #3182F6); }
  #mg-pip-sheet .ps-chip button { border: 0; background: transparent; color: var(--mg-sub, #8B95A1); width: 20px; height: 20px; border-radius: 6px; cursor: pointer; font-size: 11px; padding: 0; }
  #mg-pip-sheet .ps-chip button:hover { background: rgba(0,0,0,.08); }
  #mg-pip-sheet .ps-max { font-size: 11.5px; color: var(--mg-sub, #8B95A1); align-self: center; }
  #mg-pip-sheet .ps-add { display: flex; gap: 6px; }
  #mg-pip-sheet .ps-add input { flex: 1; min-width: 0; height: 38px; padding: 0 12px; border-radius: 10px; border: 1px solid var(--mg-border, #E5E8EB); background: transparent; color: inherit; font: inherit; font-size: 13.5px; outline: 0; }
  #mg-pip-sheet .ps-add input:focus { border-color: var(--mg-accent, #3182F6); }
  #mg-pip-sheet .ps-add button { height: 38px; padding: 0 14px; border: 0; border-radius: 10px; background: var(--mg-soft, #F2F4F6); color: inherit; font: inherit; font-size: 13px; font-weight: 700; cursor: pointer; }
  #mg-pip-sheet .ps-err { font-size: 12px; color: #F04452; min-height: 6px; margin: 6px 2px 0; }
  #mg-pip-sheet .ps-go { width: 100%; height: 44px; margin-top: 8px; border: 0; border-radius: 12px; background: #3182F6; color: #fff; font: inherit; font-size: 14.5px; font-weight: 800; cursor: pointer; }
  #mg-pip-sheet .ps-go.off { background: var(--mg-soft, #F2F4F6); color: inherit; }
  .mg-pip-toast { position: fixed; left: 50%; top: 84px; transform: translateX(-50%); z-index: 999996; padding: 11px 16px; border-radius: 12px; background: rgba(20,24,31,.95); color: #fff; font: 600 13px Pretendard, -apple-system, sans-serif; box-shadow: 0 10px 30px rgba(0,0,0,.3); }
  @media (max-width: 768px) {
    .mg-pip-btn { width: 34px; height: 34px; border-radius: 10px; }
    #mg-pip-sheet { left: 12px; right: 12px; top: 64px; width: auto; }
  }`;
  d.head.appendChild(css);
  let q = false;
  new MutationObserver(() => { if (q) return; q = true; requestAnimationFrame(() => { q = false; fill(); setBtn(); }); }).observe(d.body, { childList: true, subtree: true });
  fill();
})();
"""


def inject():
    """사이트(부모 문서)에 한 번만 붙음."""
    components.html(
        f"""<script>
(function () {{
  const d = window.parent.document;
  if (d.getElementById('mg-pip-js')) return;
  const sc = d.createElement('script'); sc.id = 'mg-pip-js'; sc.textContent = {json.dumps(_JS)}; d.body.appendChild(sc);
}})();
</script>""",
        height=0,
    )


def push_positions(pos):
    """히스토리 화면에서 10초마다: 내 포지션(심볼·방향·레버리지·진입가)을 작은 창에 넘겨줌."""
    lst = [{"s": p["symbol"].replace("/", ""), "side": p["side"], "lev": p["leverage"], "e": p["entry_price"]} for p in (pos or [])]
    components.html(f"<script>try{{const P=window.parent;P.__mgPos={json.dumps(lst)};P.dispatchEvent(new P.CustomEvent('mg-pos'));}}catch(e){{}}</script>", height=0)
