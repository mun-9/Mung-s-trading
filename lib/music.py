"""사이트 왼쪽 아래 LP 음악 플레이어 (유튜브 재생).

사이트 본문(부모 문서)에 한 번만 붙여 넣기 때문에 페이지를 옮겨 다녀도 노래가 끊기지 않음.
곡을 추가하려면 TRACKS에 유튜브 영상 ID와 제목을 넣으면 됨.
"""
import json

import streamlit.components.v1 as components

TRACKS = [
    {"id": "SHFTHDncw0g", "title": "Lost Sky - Dreams"},
]

_CSS = r"""
#mg-music { position: fixed; left: 0; bottom: 22px; z-index: 999990; display: flex; align-items: center; gap: 10px;
  font-family: 'Pretendard', -apple-system, sans-serif; transform: translateX(-140%); opacity: 0;
  transition: transform .7s cubic-bezier(.2,1.3,.4,1), opacity .5s ease; pointer-events: none; }
/* 평소: 왼쪽 벽에 반쯤 숨어 있음 → 누르면 쏙 나옴 */
#mg-music.in { transform: translateX(-31px); opacity: 1; pointer-events: auto; }
#mg-music.in:not(.open):hover { transform: translateX(-24px); }
#mg-music.in.open { transform: translateX(14px); }
#mg-music .disc { position: relative; width: 58px; height: 58px; border-radius: 50%; cursor: pointer; flex-shrink: 0;
  background: repeating-radial-gradient(circle, #1b1b1f 0 2px, #26262c 2px 3px);
  box-shadow: 0 6px 20px rgba(0,0,0,.35), inset 0 0 0 2px rgba(255,255,255,.06); animation: mg-spin 3.2s linear infinite; animation-play-state: paused; }
#mg-music.playing .disc { animation-play-state: running; }
#mg-music .disc::after { content: ''; position: absolute; inset: 0; border-radius: 50%;
  background: linear-gradient(135deg, rgba(255,255,255,.18), transparent 45%); pointer-events: none; }
#mg-music .label { position: absolute; inset: 18px; border-radius: 50%; background: #3182F6 center/cover; box-shadow: 0 0 0 2px #111; }
#mg-music .label::after { content: ''; position: absolute; left: 50%; top: 50%; width: 5px; height: 5px; margin: -2.5px; border-radius: 50%; background: #111; }
#mg-music .hint { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; border-radius: 50%;
  background: rgba(0,0,0,.35); color: #fff; transition: opacity .2s; animation: mg-spin 3.2s linear infinite reverse; animation-play-state: inherit; }
#mg-music.playing .hint { opacity: 0; }
#mg-music .disc:hover .hint { opacity: 1; }
#mg-music .hint svg { width: 18px; height: 18px; }
#mg-music .pill { display: flex; align-items: center; gap: 4px; height: 40px; padding: 0 6px 0 14px; border-radius: 999px;
  background: rgba(25,31,40,.88); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); color: #fff;
  box-shadow: 0 6px 20px rgba(0,0,0,.25); max-width: 0; overflow: hidden; opacity: 0; padding-left: 0; padding-right: 0;
  transition: max-width .45s ease, opacity .3s ease, padding .45s ease; }
#mg-music.open .pill { max-width: 260px; opacity: 1; padding: 0 6px 0 14px; }
#mg-music .t { width: 120px; overflow: hidden; white-space: nowrap; font-size: 12.5px; font-weight: 600; }
#mg-music .t span { display: inline-block; padding-right: 30px; }
#mg-music.playing .t span { animation: mg-marq 9s linear infinite; }
#mg-music button { border: 0; background: transparent; color: #fff; width: 30px; height: 30px; border-radius: 50%; cursor: pointer;
  display: flex; align-items: center; justify-content: center; padding: 0; flex-shrink: 0; }
#mg-music button:hover { background: rgba(255,255,255,.12); }
#mg-music button svg { width: 16px; height: 16px; }
#mg-music .yt { position: fixed; left: -9999px; top: 0; width: 200px; height: 200px; }
@keyframes mg-spin { to { transform: rotate(360deg); } }
@keyframes mg-marq { to { transform: translateX(-100%); } }
@media (max-width: 768px) { #mg-music { bottom: 14px; } #mg-music.in { transform: translateX(-27px); } #mg-music.in.open { transform: translateX(10px); } #mg-music .disc { width: 50px; height: 50px; } #mg-music .label { inset: 15px; } }
"""

_JS = r"""
(function () {
  const TRACKS = __TRACKS__;
  const P = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
  const PA = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 5h4v14H7zM13 5h4v14h-4z"/></svg>';
  const NX = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 6l8.5 6L6 18zM16 6h2v12h-2z"/></svg>';
  const CL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M15 6l-6 6 6 6"/></svg>';
  const root = document.createElement('div');
  root.id = 'mg-music';
  root.innerHTML = `<div class="disc" title="눌러서 재생"><div class="label"></div><div class="hint">${P}</div></div>
    <div class="pill"><div class="t"><span></span></div><button class="pp">${P}</button>${TRACKS.length > 1 ? `<button class="nx" title="다음 곡">${NX}</button>` : ''}<button class="cl" title="넣기">${CL}</button></div>
    <div class="yt"><div id="mg-yt"></div></div>`;
  document.body.appendChild(root);
  let idx = 0, player = null, ready = false, playing = false, want = false;
  const $ = s => root.querySelector(s);
  function show() {
    const t = TRACKS[idx];
    $('.label').style.backgroundImage = `url(https://i.ytimg.com/vi/${t.id}/hqdefault.jpg)`;
    $('.t span').textContent = t.title;
  }
  function setPlaying(v) {
    playing = v; root.classList.toggle('playing', v);
    $('.pp').innerHTML = v ? PA : P; $('.hint').innerHTML = v ? PA : P;
  }
  function play() { want = true; root.classList.add('open'); if (ready) player.playVideo(); }
  function pause() { want = false; if (ready) player.pauseVideo(); }
  function next() { idx = (idx + 1) % TRACKS.length; show(); if (ready) { player.loadVideoById(TRACKS[idx].id); want = true; } }
  // 숨어 있을 때 누르면: 나오면서 재생 / 나와 있을 때 누르면: 재생·일시정지
  $('.disc').onclick = () => { if (!root.classList.contains('open')) { root.classList.add('open'); if (!playing) play(); } else if (playing) pause(); else play(); };
  $('.pp').onclick = () => playing ? pause() : play();
  if ($('.nx')) $('.nx').onclick = next;
  $('.cl').onclick = () => root.classList.remove('open'); // 다시 벽 속으로 (노래는 계속)
  show();
  function init() {
    player = new YT.Player('mg-yt', {
      width: 200, height: 200, videoId: TRACKS[idx].id,
      playerVars: { playsinline: 1, controls: 0, rel: 0 },
      events: {
        onReady: () => { ready = true; player.setVolume(60); if (want) player.playVideo(); },
        onStateChange: e => {
          if (e.data === 1) setPlaying(true);
          else if (e.data === 2) setPlaying(false);
          else if (e.data === 0) { if (TRACKS.length > 1) next(); else { player.seekTo(0); player.playVideo(); } }
        },
        onError: () => { if (TRACKS.length > 1) next(); },
      },
    });
  }
  if (window.YT && window.YT.Player) init();
  else {
    const prev = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => { if (prev) prev(); init(); };
    const s = document.createElement('script'); s.src = 'https://www.youtube.com/iframe_api'; document.head.appendChild(s);
  }
  setTimeout(() => root.classList.add('in'), 1200);
})();
"""


def inject():
    """한 번만 붙음 (이미 있으면 아무것도 안 함). 보이지 않는 0px 높이 칸으로 넣음."""
    js = _JS.replace("__TRACKS__", json.dumps(TRACKS, ensure_ascii=False))
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
