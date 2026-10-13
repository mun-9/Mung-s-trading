"""사이트 왼쪽 아래 LP 음악 플레이어 (유튜브 재생).

사이트 본문(부모 문서)에 한 번만 붙여 넣기 때문에 페이지를 옮겨 다녀도 노래가 끊기지 않음.
곡을 추가하려면 TRACKS에 유튜브 영상 ID를 넣으면 됨 (제목·채널명은 자동).
"""
import json
import re
import urllib.parse
import urllib.request

import streamlit as st
import streamlit.components.v1 as components

# 플레이리스트: 유튜브 영상 ID만 넣으면 제목·채널명은 자동으로 가져옴 (title을 적으면 그걸 우선 사용)
TRACKS = [
    {"id": "SHFTHDncw0g", "title": "Lost Sky - Dreams"},
    {"id": "7RU1l8GtGOc", "title": "Lost Sky - Vision"},
    {"id": "9rujCfYXhQc", "title": "Lost Sky - Fearless"},
    {"id": "U9pGr6KMdyg", "title": "Lost Sky - Where We Started (feat. Jex)"},
    {"id": "9iHM6X6uUH8", "title": "Jim Yosef - Link"},
    {"id": "p7ZsBPK656s", "title": "Disfigure - Blank"},
    {"id": "__CRWE-L45k", "title": "Electro-Light - Symbolism"},
    {"id": "x_OwcYTNbHs", "title": "Jim Yosef - Firefly"},
    {"id": "vBGiFtb8Rpw", "title": "Culture Code - Make Me Move (feat. Karra)"},
]


@st.cache_data(ttl=86400, show_spinner=False)
def _meta(vid):
    """유튜브 oEmbed로 제목·채널명 가져오기 (실패하면 빈 값)."""
    try:
        url = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}")
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=5) as r:
            j = json.loads(r.read().decode("utf-8"))
        return {"title": j.get("title", ""), "author": j.get("author_name", "")}
    except Exception:
        return {"title": "", "author": ""}


def _clean(title):
    # 'Lost Sky - Dreams | Trap | NCS - Copyright Free Music' → 'Lost Sky - Dreams'
    return re.sub(r"\s*[\|\[].*$", "", title).strip() or title


def _tracks():
    out = []
    for t in TRACKS:
        m = _meta(t["id"])
        title = t.get("title") or _clean(m["title"]) or "Untitled"
        # '가수 - 곡명' → 곡명은 크게, 가수는 아래 작게 (유튜브 채널명은 안 씀)
        artist, song = (title.split(" - ", 1) + [""])[:2] if " - " in title else ("", title)
        out.append({"id": t["id"], "song": song.strip(), "artist": artist.strip()})
    return out


_CSS = r"""
#mg-music { position: fixed; left: 0; bottom: 22px; z-index: 999990; display: flex; align-items: center; gap: 10px;
  font-family: 'Pretendard', -apple-system, sans-serif; transform: translateX(-140%); opacity: 0;
  transition: transform .7s cubic-bezier(.2,1.3,.4,1), opacity .5s ease; pointer-events: none;
  --mp-bg: rgba(20,24,31,.86); --mp-line: rgba(255,255,255,.08); --mp-sub: rgba(255,255,255,.55); --mp-acc: #5B8DFF; }
/* 컴퓨터: LP 전체가 보임 / 휴대폰(아래 @media): 왼쪽 벽에 반쯤 숨어 있다가 누르면 쏙 나옴 */
#mg-music.in { transform: translateX(18px); opacity: 1; pointer-events: auto; }
#mg-music.in.open { transform: translateX(18px); }

/* LP */
#mg-music .disc { position: relative; width: 60px; height: 60px; border-radius: 50%; cursor: pointer; flex-shrink: 0;
  background: repeating-radial-gradient(circle, #16161a 0 1.6px, #24242b 1.6px 3px);
  box-shadow: 0 8px 24px rgba(0,0,0,.38), inset 0 0 0 2px rgba(255,255,255,.05); animation: mg-spin 3.2s linear infinite; animation-play-state: paused; }
#mg-music.playing .disc { animation-play-state: running; }
#mg-music.in .disc:hover { filter: brightness(1.15); }
#mg-music .disc::after { content: ''; position: absolute; inset: 0; border-radius: 50%; pointer-events: none;
  background: conic-gradient(from 30deg, transparent 0 12%, rgba(255,255,255,.16) 18%, transparent 26% 62%, rgba(255,255,255,.10) 68%, transparent 76%); }
#mg-music .label { position: absolute; inset: 19px; border-radius: 50%; background: #3182F6 center/cover; box-shadow: 0 0 0 2px #0d0d10; }
#mg-music .label::after { content: ''; position: absolute; left: 50%; top: 50%; width: 5px; height: 5px; margin: -2.5px; border-radius: 50%; background: #0d0d10; }
#mg-music .hint { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; border-radius: 50%;
  background: rgba(0,0,0,.35); color: #fff; transition: opacity .2s; }
#mg-music.playing .hint { opacity: 0; }
#mg-music .disc:hover .hint { opacity: 1; }
#mg-music .hint svg { width: 18px; height: 18px; }
/* 재생 중일 때 LP 뒤로 은은한 빛 */
#mg-music .glow { position: absolute; left: -6px; top: 50%; width: 72px; height: 72px; margin-top: -36px; border-radius: 50%;
  background: radial-gradient(circle, rgba(91,141,255,.45), transparent 65%); opacity: 0; transition: opacity .6s; pointer-events: none; animation: mg-pulse 2.4s ease-in-out infinite; }
#mg-music.playing .glow { opacity: 1; }

/* 지금 재생 카드 */
#mg-music .np { display: flex; flex-direction: column; justify-content: center; gap: 6px; width: 0; opacity: 0; overflow: hidden;
  height: 86px; padding: 0; border-radius: 20px; background: var(--mp-bg); color: #fff; border: 1px solid var(--mp-line);
  backdrop-filter: blur(16px) saturate(1.4); -webkit-backdrop-filter: blur(16px) saturate(1.4); box-shadow: 0 10px 30px rgba(0,0,0,.28);
  transition: width .45s cubic-bezier(.2,1,.3,1), opacity .3s ease, padding .45s ease; }
#mg-music.open .np { width: 300px; opacity: 1; padding: 0 10px 0 16px; }
#mg-music .np-top, #mg-music .np-ctl { display: flex; align-items: center; gap: 4px; width: 274px; }
#mg-music .np-ctl { gap: 2px; }
#mg-music .np-ctl .cur, #mg-music .np-ctl .dur { font-size: 10.5px; color: var(--mp-sub); font-variant-numeric: tabular-nums; width: 30px; text-align: center; flex-shrink: 0; }
#mg-music .np-ctl .cur { margin-left: 4px; }
#mg-music .np-tx { flex: 1; min-width: 0; }
#mg-music .np-t { font-size: 13px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; letter-spacing: -.01em; }
#mg-music .np-a { font-size: 11px; color: var(--mp-sub); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 1px; }
#mg-music .np-bar { position: relative; flex: 1; height: 4px; border-radius: 2px; background: rgba(255,255,255,.14); cursor: pointer; }
#mg-music .np-bar::before { content: ''; position: absolute; left: 0; right: 0; top: -6px; bottom: -6px; }
#mg-music .np-bar i { position: absolute; left: 0; top: 0; bottom: 0; width: 0; border-radius: 2px; background: linear-gradient(90deg, #5B8DFF, #9DB8FF); }
#mg-music button { border: 0; background: transparent; color: #fff; width: 30px; height: 30px; border-radius: 50%; cursor: pointer;
  display: flex; align-items: center; justify-content: center; padding: 0; flex-shrink: 0; transition: background .15s, color .15s; }
#mg-music button:hover { background: rgba(255,255,255,.12); }
#mg-music button svg { width: 16px; height: 16px; }
#mg-music button.pp { width: 32px; height: 32px; background: #fff; color: #111; }
#mg-music button.pp svg { width: 15px; height: 15px; }
#mg-music .np-ctl button:not(.pp) svg { width: 15px; height: 15px; }
#mg-music button.pp:hover { background: #E8EEFF; }
#mg-music button.on { color: var(--mp-acc); }

/* 플레이리스트 */
#mg-music .pl { position: absolute; left: 0; bottom: 98px; width: 330px; max-height: 0; opacity: 0; overflow: hidden; border-radius: 18px;
  background: var(--mp-bg); border: 1px solid var(--mp-line); color: #fff; box-shadow: 0 16px 40px rgba(0,0,0,.35);
  backdrop-filter: blur(16px) saturate(1.4); -webkit-backdrop-filter: blur(16px) saturate(1.4);
  transform: translateY(8px); transition: max-height .4s ease, opacity .25s ease, transform .3s ease; pointer-events: none; }
#mg-music.list .pl { max-height: 380px; opacity: 1; transform: none; pointer-events: auto; }
#mg-music .pl-h { display: flex; align-items: center; justify-content: space-between; padding: 16px 18px 10px; }
#mg-music .pl-h b { font-size: 11px; font-weight: 800; letter-spacing: .14em; color: var(--mp-sub); }
#mg-music .pl-h span { font-size: 11px; font-weight: 700; color: #9DB8FF; background: rgba(91,141,255,.14); padding: 3px 8px; border-radius: 999px; }
#mg-music .pl-ul { max-height: 318px; overflow-y: auto; padding: 0 8px 10px; scrollbar-width: none; }
#mg-music .pl-ul::-webkit-scrollbar { display: none; }
#mg-music .pl-li { position: relative; display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 12px; cursor: pointer; transition: background .15s; }
#mg-music .pl-li + .pl-li::before { content: ''; position: absolute; left: 46px; right: 12px; top: 0; height: 1px; background: rgba(255,255,255,.05); }
#mg-music .pl-li:hover { background: rgba(255,255,255,.06); }
#mg-music .pl-li.cur { background: linear-gradient(90deg, rgba(91,141,255,.22), rgba(91,141,255,.06)); }
#mg-music .pl-li.cur::before, #mg-music .pl-li.cur + .pl-li::before { display: none; }
#mg-music .pl-li.cur::after { content: ''; position: absolute; left: 0; top: 10px; bottom: 10px; width: 3px; border-radius: 2px; background: #5B8DFF; }
/* 왼쪽 칸: 번호 → 마우스 올리면 재생 아이콘 → 지금 곡이면 움직이는 막대 */
#mg-music .pl-k { position: relative; width: 22px; height: 22px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
#mg-music .pl-n { font-size: 12px; font-weight: 600; color: var(--mp-sub); font-variant-numeric: tabular-nums; }
#mg-music .pl-p { display: none; color: #fff; } #mg-music .pl-p svg { width: 13px; height: 13px; }
#mg-music .pl-li:not(.cur):hover .pl-n { display: none; } #mg-music .pl-li:not(.cur):hover .pl-p { display: flex; }
#mg-music .eq { display: none; align-items: flex-end; gap: 2px; height: 13px; }
#mg-music .pl-li.cur .pl-n { display: none; } #mg-music .pl-li.cur .eq { display: flex; }
#mg-music .eq i { width: 3px; height: 13px; border-radius: 1px; background: #7FA3FF; transform-origin: bottom; transform: scaleY(.35); }
#mg-music.playing .pl-li.cur .eq i { animation: mg-eq .9s ease-in-out infinite; }
#mg-music .eq i:nth-child(2) { animation-delay: .25s !important; } #mg-music .eq i:nth-child(3) { animation-delay: .5s !important; }
#mg-music .pl-tx { flex: 1; min-width: 0; }
#mg-music .pl-t { font-size: 13.5px; font-weight: 650; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; letter-spacing: -.01em; }
#mg-music .pl-li.cur .pl-t { color: #fff; font-weight: 750; }
#mg-music .pl-a { font-size: 11.5px; color: var(--mp-sub); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px; }
#mg-music .pl-li.cur .pl-a { color: #9DB8FF; }

#mg-music .yt { position: fixed; left: -9999px; top: 0; width: 200px; height: 200px; }
/* 인스타·카톡 같은 앱 안 브라우저: 유튜브 플레이어를 LP 위에 투명하게 겹쳐서, 손가락이 플레이어를 직접 누르게 함 */
#mg-music.inapp .yt { position: absolute; left: 0; top: 50%; width: 60px; height: 60px; margin-top: -30px; overflow: hidden;
  border-radius: 50%; opacity: .011; z-index: 3; }
#mg-music.inapp .yt iframe { width: 200px; height: 200px; transform: scale(.3); transform-origin: 0 0; }
#mg-music .tip { position: absolute; left: 0; bottom: 76px; width: 240px; padding: 10px 12px; border-radius: 12px; background: rgba(25,31,40,.94);
  color: #fff; font-size: 12px; line-height: 1.5; box-shadow: 0 6px 20px rgba(0,0,0,.25); display: none; }
#mg-music.showtip .tip { display: block; }
@keyframes mg-spin { to { transform: rotate(360deg); } }
@keyframes mg-eq { 0%,100% { transform: scaleY(.3); } 50% { transform: scaleY(1); } }
@keyframes mg-pulse { 0%,100% { transform: scale(.92); } 50% { transform: scale(1.08); } }
@media (max-width: 768px) {
  #mg-music { bottom: 14px; }
  #mg-music.in { transform: translateX(-27px); } #mg-music.in.open { transform: translateX(10px); }
  #mg-music .disc { width: 52px; height: 52px; } #mg-music .label { inset: 16px; }
  #mg-music.open .np { width: min(290px, calc(100vw - 84px)); padding: 0 8px 0 14px; }
  #mg-music .np-top, #mg-music .np-ctl { width: min(268px, calc(100vw - 106px)); }
  #mg-music .pl { bottom: 96px; }
  #mg-music .pl { width: calc(100vw - 20px); }
  #mg-music.inapp .yt { width: 52px; height: 52px; margin-top: -26px; } #mg-music.inapp .yt iframe { transform: scale(.26); }
}
"""

_JS = r"""
(function () {
  const TRACKS = __TRACKS__;
  const I = {
    play: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.5-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5z"/></svg>',
    pause: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6.5" y="5" width="4" height="14" rx="1.2"/><rect x="13.5" y="5" width="4" height="14" rx="1.2"/></svg>',
    next: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M5 6.5v11a1 1 0 0 0 1.55.83L14 13.2V17.5a1 1 0 0 0 2 0v-11a1 1 0 0 0-2 0v4.3L6.55 5.67A1 1 0 0 0 5 6.5z" transform="translate(1.5 0)"/></svg>',
    prev: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.5v11a1 1 0 0 1-1.55.83L10 13.2V17.5a1 1 0 0 1-2 0v-11a1 1 0 0 1 2 0v4.3l7.45-5.13A1 1 0 0 1 19 6.5z" transform="translate(-1.5 0)"/></svg>',
    list: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 6h11M4 12h11M4 18h7"/><path d="M18 14v6" /><circle cx="16.5" cy="19.5" r="2" fill="currentColor" stroke="none"/><path d="M18 14l3-1"/></svg>',
    close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M15 6l-6 6 6 6"/></svg>',
  };
  const thumb = id => `https://i.ytimg.com/vi/${id}/hqdefault.jpg`;
  const esc = s => String(s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const root = document.createElement('div');
  root.id = 'mg-music';
  root.innerHTML = `<div class="glow"></div>
    <div class="disc" title="눌러서 재생"><div class="label"></div><div class="hint">${I.play}</div></div>
    <div class="np">
      <div class="np-top"><div class="np-tx"><div class="np-t"></div><div class="np-a"></div></div>
        <button class="ls" title="플레이리스트">${I.list}</button><button class="cl" title="접기">${I.close}</button></div>
      <div class="np-ctl">${TRACKS.length > 1 ? `<button class="pv" title="이전 곡">${I.prev}</button>` : ''}<button class="pp" title="재생">${I.play}</button>${TRACKS.length > 1 ? `<button class="nx" title="다음 곡">${I.next}</button>` : ''}
        <span class="cur">0:00</span><div class="np-bar"><i></i></div><span class="dur">0:00</span></div>
    </div>
    <div class="pl"><div class="pl-h"><b>PLAYLIST</b><span>${TRACKS.length}곡</span></div><div class="pl-ul">${TRACKS.map((t, i) => `
      <div class="pl-li" data-i="${i}"><div class="pl-k"><span class="pl-n">${String(i + 1).padStart(2, '0')}</span><span class="pl-p">${I.play}</span><span class="eq"><i></i><i></i><i></i></span></div>
        <div class="pl-tx"><div class="pl-t">${esc(t.song)}</div>${t.artist ? `<div class="pl-a">${esc(t.artist)}</div>` : ''}</div></div>`).join('')}</div></div>
    <div class="yt"><div id="mg-yt"></div></div><div class="tip">인스타·카톡 앱 안에서는 노래가 막힐 수 있어요.<br>오른쪽 위 <b>⋮</b> → <b>외부 브라우저로 열기</b>로 들어와 주세요.</div>`;
  document.body.appendChild(root);
  const INAPP = /Instagram|FBAN|FBAV|FB_IAB|KAKAOTALK|NAVER\(inapp|DaumApps|Line\/|; wv\)/i.test(navigator.userAgent);
  if (INAPP) root.classList.add('inapp');
  let idx = 0, player = null, ready = false, playing = false, want = false;
  const $ = s => root.querySelector(s);
  const fmt = t => { t = Math.max(0, Math.floor(t || 0)); return Math.floor(t / 60) + ':' + String(t % 60).padStart(2, '0'); };
  function show() {
    const t = TRACKS[idx];
    $('.label').style.backgroundImage = `url(${thumb(t.id)})`;
    $('.np-t').textContent = t.song; $('.np-a').textContent = t.artist || '';
    root.querySelectorAll('.pl-li').forEach(li => li.classList.toggle('cur', +li.dataset.i === idx));
    $('.np-bar i').style.width = '0%'; $('.cur').textContent = '0:00'; $('.dur').textContent = '0:00';
  }
  function setPlaying(v) {
    playing = v; root.classList.toggle('playing', v);
    $('.pp').innerHTML = v ? I.pause : I.play; $('.hint').innerHTML = v ? I.pause : I.play;
  }
  function play() { want = true; root.classList.add('open'); if (ready) player.playVideo(); }
  function pause() { want = false; if (ready) player.pauseVideo(); }
  function go(i) { idx = (i + TRACKS.length) % TRACKS.length; show(); want = true; root.classList.add('open'); if (ready) player.loadVideoById(TRACKS[idx].id); }
  // 숨어 있을 때 누르면: 나오면서 재생 / 나와 있을 때 누르면: 재생·일시정지
  $('.disc').onclick = () => { if (!root.classList.contains('open')) { root.classList.add('open'); if (!playing) play(); } else if (playing) pause(); else play(); };
  $('.pp').onclick = () => playing ? pause() : play();
  if ($('.nx')) $('.nx').onclick = () => go(idx + 1);
  if ($('.pv')) $('.pv').onclick = () => (ready && player.getCurrentTime() > 3) ? player.seekTo(0, true) : go(idx - 1);
  $('.ls').onclick = e => { e.stopPropagation(); root.classList.toggle('list'); $('.ls').classList.toggle('on', root.classList.contains('list')); };
  $('.cl').onclick = () => { root.classList.remove('open', 'list'); $('.ls').classList.remove('on'); }; // 접기 (노래는 계속)
  root.querySelectorAll('.pl-li').forEach(li => li.onclick = () => { const i = +li.dataset.i; if (i === idx && ready) { playing ? pause() : play(); } else go(i); });
  $('.np-bar').onclick = e => { if (!ready) return; const r = e.currentTarget.getBoundingClientRect(), d = player.getDuration() || 0; player.seekTo(d * Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)), true); };
  document.addEventListener('click', e => { if (root.classList.contains('list') && !root.contains(e.target)) { root.classList.remove('list'); $('.ls').classList.remove('on'); } });
  setInterval(() => {
    if (!ready || !player.getDuration) return;
    const d = player.getDuration() || 0, c = player.getCurrentTime() || 0;
    if (d) { $('.np-bar i').style.width = (c / d * 100).toFixed(2) + '%'; $('.cur').textContent = fmt(c); $('.dur').textContent = fmt(d); }
  }, 500);
  show();
  function init() {
    player = new YT.Player('mg-yt', {
      width: 200, height: 200, videoId: TRACKS[idx].id,
      playerVars: { playsinline: 1, controls: 0, rel: 0 },
      events: {
        onReady: () => { ready = true; player.setVolume(60); if (want) player.playVideo(); },
        onStateChange: e => {
          if (e.data === 1) { setPlaying(true); root.classList.add('open'); root.classList.remove('showtip'); }
          else if (e.data === 2) setPlaying(false);
          else if (e.data === 0) { if (TRACKS.length > 1) go(idx + 1); else { player.seekTo(0); player.playVideo(); } }
        },
        onError: () => { if (TRACKS.length > 1) go(idx + 1); },
      },
    });
  }
  if (window.YT && window.YT.Player) init();
  else {
    const prev = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => { if (prev) prev(); init(); };
    const s = document.createElement('script'); s.src = 'https://www.youtube.com/iframe_api'; document.head.appendChild(s);
  }
  // 앱 안 브라우저: 플레이어를 눌렀는데 3초 안에 재생이 안 되면 외부 브라우저 안내
  if (INAPP) window.addEventListener('blur', () => setTimeout(() => {
    if (document.activeElement && document.activeElement.tagName === 'IFRAME' && root.contains(document.activeElement)) {
      setTimeout(() => { if (!playing) { root.classList.add('showtip'); setTimeout(() => root.classList.remove('showtip'), 7000); } }, 3000);
    }
  }, 0));
  setTimeout(() => root.classList.add('in'), 1200);
})();
"""


def inject():
    """한 번만 붙음 (이미 있으면 아무것도 안 함). 보이지 않는 0px 높이 칸으로 넣음."""
    js = _JS.replace("__TRACKS__", json.dumps(_tracks(), ensure_ascii=False))
    components.html(
        f"""<script>
// Streamlit Cloud가 화면 오른쪽 아래에 붙이는 배지(만든 사람 프사·'Hosted with Streamlit') 숨기기
(function () {{
  if (window.top === window.parent) return; // 감싸는 화면이 없으면(직접 실행) 할 일 없음
  let top; try {{ top = window.top.document; top.body; }} catch (e) {{ return; }}
  if (top.getElementById('mg-hide-badge')) return;
  const css = top.createElement('style'); css.id = 'mg-hide-badge';
  css.textContent = '[class*="viewerBadge"],[class*="profileContainer"],[class*="ProfileContainer"],a[href*="streamlit.io/cloud"],a[href*="share.streamlit.io/user"]{{display:none !important;}}';
  top.head.appendChild(css);
  const hide = () => top.querySelectorAll('a[href*="streamlit.io"], img[src*="avatars.githubusercontent"]').forEach(el => {{
    let n = el;
    for (let i = 0; i < 6 && n && n !== top.body; i++, n = n.parentElement) {{
      const pos = getComputedStyle(n).position;
      if (pos === 'fixed' || pos === 'absolute') {{ n.style.setProperty('display', 'none', 'important'); return; }}
    }}
  }});
  hide(); new MutationObserver(hide).observe(top.body, {{ childList: true, subtree: true }});
}})();
(function () {{
  const d = window.parent.document;
  if (d.getElementById('mg-music-style')) return;
  const st = d.createElement('style'); st.id = 'mg-music-style'; st.textContent = {json.dumps(_CSS)}; d.head.appendChild(st);
  const sc = d.createElement('script'); sc.textContent = {json.dumps(js)}; d.body.appendChild(sc);
}})();
</script>""",
        height=0,
    )
