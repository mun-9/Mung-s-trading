"""가격 알림 (사이트 어느 화면에 있든 동작).

- 알림 목록은 브라우저 localStorage('mung_alerts')에 저장: [{id, sym, price, dir: 'above'|'below', note, ts}]
- Bitget 선물 실시간 시세를 받아서 가격이 닿으면 화면 오른쪽 위 알림 + (허용했으면) 휴대폰/PC 알림 + 짧은 소리
- 알림을 추가·삭제하는 화면(코인 상세 창, 도구 화면)은 window.mgAlerts 를 써서 바꿈
"""
import json

import streamlit.components.v1 as components

_CSS = r"""
#mg-toasts { position: fixed; top: 84px; right: 16px; z-index: 999995; display: flex; flex-direction: column; gap: 10px; pointer-events: none; }
.mg-toast { pointer-events: auto; width: min(340px, calc(100vw - 32px)); display: flex; gap: 12px; align-items: flex-start; padding: 14px 16px; border-radius: 16px;
  background: rgba(20,24,31,.94); color: #fff; box-shadow: 0 14px 40px rgba(0,0,0,.35); border: 1px solid rgba(255,255,255,.08);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); font-family: 'Pretendard', -apple-system, sans-serif;
  animation: mg-tin .45s cubic-bezier(.2,1.3,.4,1); }
.mg-toast.out { animation: mg-tout .3s ease forwards; }
.mg-toast .ic { width: 36px; height: 36px; border-radius: 11px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.mg-toast .ic.up { background: rgba(8,153,129,.2); } .mg-toast .ic.down { background: rgba(240,68,82,.2); } .mg-toast .ic.nw { background: rgba(91,141,255,.2); }
.mg-toast b { display: block; font-size: 14.5px; font-weight: 800; letter-spacing: -.01em; }
.mg-toast span { display: block; font-size: 12.5px; color: rgba(255,255,255,.65); margin-top: 3px; line-height: 1.45; }
.mg-toast button { margin-left: auto; border: 0; background: transparent; color: rgba(255,255,255,.5); font-size: 16px; cursor: pointer; padding: 0 0 0 6px; }
@keyframes mg-tin { from { transform: translateX(30px); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes mg-tout { to { transform: translateX(30px); opacity: 0; } }
@media (max-width: 768px) { #mg-toasts { top: auto; bottom: 86px; right: 10px; left: 10px; align-items: center; } }
"""

_JS = r"""
(function () {
  const KEY = 'mung_alerts', d = document, W = window;
  const load = () => { try { const a = JSON.parse(localStorage.getItem(KEY) || '[]'); return Array.isArray(a) ? a : []; } catch (e) { return []; } };
  const store = a => { try { localStorage.setItem(KEY, JSON.stringify(a)); } catch (e) {} };
  const fmt = v => { const a = Math.abs(v), dg = a >= 1000 ? 2 : a >= 1 ? 4 : a >= 0.01 ? 6 : 8; return '$' + (+v).toLocaleString('en-US', { maximumFractionDigits: dg }); };
  const box = d.createElement('div'); box.id = 'mg-toasts'; d.body.appendChild(box);
  function toast(title, body, dir, icon, link) {
    const t = d.createElement('div'); t.className = 'mg-toast';
    t.innerHTML = `<div class="ic ${dir === 'above' ? 'up' : dir === 'below' ? 'down' : 'nw'}">${icon || (dir === 'above' ? '🚀' : '🔻')}</div><div><b></b><span></span></div><button title="닫기">✕</button>`;
    t.querySelector('b').textContent = title; t.querySelector('span').textContent = body;
    const close = () => { t.classList.add('out'); setTimeout(() => t.remove(), 300); };
    t.querySelector('button').onclick = ev => { ev.stopPropagation(); close(); };
    if (link) { t.style.cursor = 'pointer'; t.onclick = () => { W.open(link, '_blank', 'noopener'); close(); }; }
    box.appendChild(t); setTimeout(close, link ? 20000 : 12000);
  }
  function beep() {
    try { const C = new (W.AudioContext || W.webkitAudioContext)(), o = C.createOscillator(), g = C.createGain();
      o.type = 'sine'; o.frequency.setValueAtTime(880, C.currentTime); o.frequency.setValueAtTime(1320, C.currentTime + .12);
      g.gain.setValueAtTime(.0001, C.currentTime); g.gain.exponentialRampToValueAtTime(.18, C.currentTime + .02); g.gain.exponentialRampToValueAtTime(.0001, C.currentTime + .45);
      o.connect(g); g.connect(C.destination); o.start(); o.stop(C.currentTime + .5); } catch (e) {}
  }
  function notify(title, body) {
    try { if ('Notification' in W && Notification.permission === 'granted') new Notification(title, { body, icon: '' }); } catch (e) {}
  }
  const last = {};
  let ws = null, subs = new Set(), retry = 0;
  // ---------- 설정 (도구 화면에서 켜고 끔) ----------
  const CFG_KEY = 'mung_alert_cfg';
  const cfg = () => { let c = {}; try { c = JSON.parse(localStorage.getItem(CFG_KEY) || '{}'); } catch (e) {} return Object.assign({ news: true, moves: true }, c); };
  const MOVE_SYMS = ['BTC', 'ETH', 'SOL', 'XRP'];
  const TH = { BTC: 1.0, ETH: 1.5, SOL: 2.5, XRP: 2.5 };  // 5분 안에 이만큼(%) 움직이면 '급변'
  function wanted() { const w = new Set(load().map(a => a.sym)); if (cfg().moves) MOVE_SYMS.forEach(s => w.add(s)); return w; }
  function connect() {
    const want = wanted();
    if (!want.size) { if (ws) { try { ws.close(); } catch (e) {} ws = null; } subs = new Set(); return; }
    if (ws && ws.readyState <= 1) {
      if (ws.readyState !== 1) return;
      const add = [...want].filter(s => !subs.has(s)), del = [...subs].filter(s => !want.has(s));
      if (add.length) ws.send(JSON.stringify({ op: 'subscribe', args: add.map(s => ({ instType: 'USDT-FUTURES', channel: 'ticker', instId: s + 'USDT' })) }));
      if (del.length) ws.send(JSON.stringify({ op: 'unsubscribe', args: del.map(s => ({ instType: 'USDT-FUTURES', channel: 'ticker', instId: s + 'USDT' })) }));
      add.forEach(s => subs.add(s)); del.forEach(s => subs.delete(s)); return;
    }
    try { ws = new WebSocket('wss://ws.bitget.com/v2/ws/public'); } catch (e) { return; }
    subs = new Set();
    ws.onopen = () => { retry = 0; connect(); ws._p = setInterval(() => { try { ws.send('ping'); } catch (e) {} }, 25000); };
    ws.onmessage = ev => {
      if (ev.data === 'pong') return; let m; try { m = JSON.parse(ev.data); } catch (e) { return; }
      if (!m.data || !m.arg || m.arg.channel !== 'ticker') return;
      for (const x of m.data) {
        const sym = String(x.instId || m.arg.instId).replace(/USDT$/, ''), px = +x.lastPr; if (!px) continue;
        last[sym] = px; check(sym, px); track(sym, px);
      }
    };
    ws.onclose = () => { clearInterval(ws && ws._p); ws = null; retry = Math.min(retry + 1, 5); setTimeout(connect, 1000 * 2 ** retry); };
  }
  function check(sym, px) {
    const all = load(); let hit = false, changed = false;
    const keep = all.filter(a => {
      if (a.sym !== sym) return true;
      if (a.dir === 'pending') { a.dir = a.price >= px ? 'above' : 'below'; changed = true; return true; }  // 현재가를 몰랐을 때: 첫 가격으로 방향 결정
      const ok = a.dir === 'above' ? px >= a.price : px <= a.price;
      if (!ok) return true;
      hit = true;
      const title = `${sym} ${fmt(a.price)} ${a.dir === 'above' ? '돌파' : '이탈'}`;
      const body = `지금 ${fmt(px)} · ${a.dir === 'above' ? '설정한 가격 위로 올라갔어요' : '설정한 가격 아래로 내려갔어요'}${a.note ? ' · ' + a.note : ''}`;
      toast(title, body, a.dir); notify(title, body); beep();
      return false; // 한 번 울리면 끝
    });
    if (hit || changed) { store(keep); W.dispatchEvent(new Event('mg-alerts-changed')); }
  }
  // ---------- 급변 감지: 5분 안에 크게 움직이면 알림 + 그 시간대 뉴스 ----------
  const MKEY = 'mung_moves', hist = {}, lastMove = {};
  const loadMoves = () => { try { const a = JSON.parse(localStorage.getItem(MKEY) || '[]'); return Array.isArray(a) ? a : []; } catch (e) { return []; } };
  function track(sym, px) {
    if (!TH[sym] || !cfg().moves) return;
    const now = Date.now(), h = hist[sym] = hist[sym] || [];
    if (!h.length || now - h[h.length - 1][0] >= 3000) h.push([now, px]);
    while (h.length && now - h[0][0] > 6 * 60000) h.shift();
    const ref = h.find(x => now - x[0] <= 5 * 60000); if (!ref || now - h[0][0] < 2 * 60000) return;  // 데이터가 2분 이상 쌓인 뒤부터
    const lo = Math.min(...h.map(x => x[1])), hi = Math.max(...h.map(x => x[1]));
    const up = (px / lo - 1) * 100, dn = (px / hi - 1) * 100;
    const pct = Math.abs(up) >= Math.abs(dn) ? up : dn;
    if (Math.abs(pct) < TH[sym] || now - (lastMove[sym] || 0) < 20 * 60000) return;
    lastMove[sym] = now;
    const rel = relatedNews(now);
    const ev = { id: now.toString(36) + sym, sym, pct: +pct.toFixed(2), from: pct > 0 ? lo : hi, to: px, ts: now, news: rel.slice(0, 3) };
    const all = loadMoves(); all.unshift(ev); try { localStorage.setItem(MKEY, JSON.stringify(all.slice(0, 30))); } catch (e) {}
    W.dispatchEvent(new Event('mg-moves-changed'));
    const title = `${sym} 5분 새 ${pct > 0 ? '+' : ''}${pct.toFixed(2)}% ${pct > 0 ? '급등' : '급락'}`;
    const body = rel.length ? '같은 시간대 뉴스: ' + rel[0].title : `지금 ${fmt(px)} · 아직 관련 뉴스가 없어요 (차트 화면 '이슈' 탭에서 업데이트)`;
    toast(title, body, pct > 0 ? 'above' : 'below', pct > 0 ? '📈' : '📉', rel.length ? rel[0].link : null); notify(title, body); beep();
  }
  // ---------- 뉴스: 서버가 90초마다 넘겨주는 최신 목록 ----------
  let NEWS = [];
  // 정말 시장을 흔드는 뉴스만 (일상적인 ETF 자금 흐름 · 금리 기사는 제외)
  const IMPORTANT = /속보|긴급|ETF\s?(최종\s?)?승인|SEC.{0,12}(승인|소송|기소|제소)|해킹|탈취|상장\s?폐지|상폐|파산|FOMC|기준금리|금리\s?(인상|인하|동결)|CPI.{0,6}(발표|예상)|트럼프.{0,20}(코인|비트코인|가상자산|암호화폐|관세)|대규모\s?청산|비상사태|전쟁/;
  const isImportant = n => IMPORTANT.test(n.title || '');
  function relatedNews(now) {
    // 최근 3시간 뉴스 중 중요 뉴스 먼저, 최신순
    const r = NEWS.filter(n => n.ts && now / 1000 - n.ts <= 3 * 3600);
    return r.sort((a, b) => (isImportant(b) - isImportant(a)) || (b.ts - a.ts));
  }
  const SKEY = 'mung_news_seen';
  function updateNews(items) {
    if (!Array.isArray(items) || !items.length) return;
    NEWS = items;
    let seen; try { seen = JSON.parse(localStorage.getItem(SKEY) || 'null'); } catch (e) { seen = null; }
    const first = !Array.isArray(seen); seen = new Set(seen || []);
    const fresh = items.filter(n => !seen.has(n.link));
    items.forEach(n => seen.add(n.link));
    try { localStorage.setItem(SKEY, JSON.stringify([...seen].slice(-300))); } catch (e) {}
    W.dispatchEvent(new Event('mg-news-changed'));
    if (first || !cfg().news) return;  // 처음 들어왔을 때 예전 뉴스로 알림 폭탄 방지
    fresh.filter(isImportant).filter(n => !n.ts || Date.now() / 1000 - n.ts < 3 * 3600).slice(0, 2).forEach(n => {
      toast('📰 중요 뉴스 · ' + n.src, n.title, null, '📰', n.link); notify('📰 ' + n.title, n.src); beep();
    });
  }
  W.mgNews = { update: updateNews, list: () => NEWS, isImportant };
  if (W.__mgNewsPending) { updateNews(W.__mgNewsPending); W.__mgNewsPending = null; }
  W.mgFeed = { cfg, setCfg(k, v) { const c = cfg(); c[k] = v; try { localStorage.setItem(CFG_KEY, JSON.stringify(c)); } catch (e) {} connect(); W.dispatchEvent(new Event('mg-moves-changed')); },
    moves: loadMoves, clearMoves() { try { localStorage.removeItem(MKEY); } catch (e) {} W.dispatchEvent(new Event('mg-moves-changed')); }, TH, MOVE_SYMS };

  // 다른 화면(코인 상세 · 도구)이 쓰는 함수
  W.mgAlerts = {
    list: load,
    price: sym => last[sym] || null,
    add(sym, price, note) {
      sym = String(sym || '').toUpperCase().replace(/USDT$/, '').replace('/', ''); price = +price;
      if (!sym || !(price > 0)) return null;
      const cur = last[sym];
      const a = { id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), sym, price, dir: cur ? (price >= cur ? 'above' : 'below') : 'pending', note: note || '', ts: Date.now() };
      const all = load(); all.push(a); store(all); connect(); W.dispatchEvent(new Event('mg-alerts-changed'));
      try { if ('Notification' in W && Notification.permission === 'default') Notification.requestPermission(); } catch (e) {}
      return a;
    },
    _feed(sym, px) { last[sym] = px; check(sym, px); track(sym, px); },
    remove(id) { store(load().filter(a => a.id !== id)); connect(); W.dispatchEvent(new Event('mg-alerts-changed')); },
    subscribe(sym) { sym = String(sym || '').toUpperCase(); if (!sym) return; const want = wanted(); if (!want.has(sym) && ws && ws.readyState === 1 && !subs.has(sym)) { ws.send(JSON.stringify({ op: 'subscribe', args: [{ instType: 'USDT-FUTURES', channel: 'ticker', instId: sym + 'USDT' }] })); subs.add(sym); } },
  };
  W.addEventListener('storage', e => { if (e.key === KEY) connect(); });
  connect();
})();
"""


def inject():
    """사이트(부모 문서)에 한 번만 붙음."""
    components.html(
        f"""<script>
(function () {{
  const d = window.parent.document;
  if (d.getElementById('mg-alerts-js')) return;
  const st = d.createElement('style'); st.textContent = {json.dumps(_CSS)}; d.head.appendChild(st);
  const sc = d.createElement('script'); sc.id = 'mg-alerts-js'; sc.textContent = {json.dumps(_JS)}; d.body.appendChild(sc);
}})();
</script>""",
        height=0,
    )
