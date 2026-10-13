"""라이트/다크 모드 전환.

- 처음에는 휴대폰·PC 설정(시스템 다크 모드)을 그대로 따라감
- 메뉴 오른쪽 해/달 버튼을 누르면 바뀌고, 브라우저에 기억됨 (다음에 들어와도 유지)
- 색은 lib/ui.py 의 CSS 변수(--mg-*)로 정해져 있어서, <html data-mg-theme="dark|light"> 만 바꾸면 화면 전체가 바뀜
"""
import json

import streamlit.components.v1 as components

_JS = r"""
(function () {
  const d = document, root = d.documentElement, KEY = 'mg_theme';
  const MQ = window.matchMedia('(prefers-color-scheme: dark)');
  const SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>';
  const MOON = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.2 14.6A8.5 8.5 0 0 1 9.4 3.8a.6.6 0 0 0-.8-.7A9.5 9.5 0 1 0 20.9 15.4a.6.6 0 0 0-.7-.8z"/></svg>';
  function apply(t) { if (t === 'dark' || t === 'light') root.setAttribute('data-mg-theme', t); else root.removeAttribute('data-mg-theme'); }
  const isDark = () => { const t = root.getAttribute('data-mg-theme'); return t ? t === 'dark' : MQ.matches; };
  let saved = null; try { saved = localStorage.getItem(KEY); } catch (e) {}
  apply(saved);
  // 메뉴 오른쪽 빈 자리에 버튼 채우기 (페이지를 옮기면 메뉴가 새로 그려지므로 계속 지켜봄)
  function fill() {
    const icon = isDark() ? SUN : MOON, title = isDark() ? '라이트 모드로' : '다크 모드로';
    d.querySelectorAll('.mg-theme-slot').forEach(slot => {
      let b = slot.querySelector('.mg-theme-btn');
      if (!b) { b = d.createElement('button'); b.className = 'mg-theme-btn'; b.type = 'button'; slot.appendChild(b); }
      if (b.dataset.icon !== (isDark() ? 'sun' : 'moon')) { b.innerHTML = icon; b.dataset.icon = isDark() ? 'sun' : 'moon'; b.title = title; b.setAttribute('aria-label', title); }
    });
  }
  // 휴대폰: 아래로 스크롤하면 메뉴 윗줄(로고·다크모드)을 접어서 화면을 넓게
  d.addEventListener('scroll', e => {
    const t = e.target; if (!t || !t.getAttribute || t.getAttribute('data-testid') !== 'stMain') return;
    const on = t.scrollTop > 80; if (d.body.classList.contains('mg-scrolled') !== on) d.body.classList.toggle('mg-scrolled', on);
  }, true);
  // 히스토리 화면 '바로가기' 칩: 누르면 그 카드로 부드럽게 스크롤
  d.addEventListener('click', e => {
    const j = e.target.closest('[data-mg-jump]'); if (!j) return;
    const el = d.querySelector(j.getAttribute('data-mg-jump')); if (!el) return;
    const box = el.closest('.card, [class*="st-key-"]') || el;
    const main = d.querySelector('[data-testid="stMain"]');
    const navH = (d.querySelector('[class*="st-key-topnav_"]') || { offsetHeight: 70 }).offsetHeight;
    if (main) main.scrollTo({ top: main.scrollTop + box.getBoundingClientRect().top - navH - 12, behavior: 'smooth' });
    else box.scrollIntoView({ behavior: 'smooth' });
  });
  d.addEventListener('click', e => {
    if (!e.target.closest('.mg-theme-btn')) return;
    const t = isDark() ? 'light' : 'dark';
    apply(t); try { localStorage.setItem(KEY, t); } catch (err) {}
    fill();
  });
  MQ.addEventListener && MQ.addEventListener('change', fill);
  let q = false;
  new MutationObserver(() => { if (q) return; q = true; requestAnimationFrame(() => { q = false; fill(); }); })
    .observe(d.body, { childList: true, subtree: true });
  fill();

  // 휴대폰 '홈 화면에 추가' 하면 앱처럼 열리게 (아이콘 · 이름 · 상단 색)
  try {
    const base = location.pathname.includes('/~/+/') ? location.origin + location.pathname.split('/~/+/')[0] + '/~/+/' : location.origin + '/';
    const st = base + 'app/static/';
    const docs = [d]; try { if (window.top !== window && window.top.document) docs.push(window.top.document); } catch (e) {}
    for (const doc of docs) {
      if (doc.getElementById('mg-pwa')) continue;
      // Streamlit Cloud가 넣어둔 기본 앱 정보(이름 'Streamlit')는 빼고 우리 것으로
      doc.querySelectorAll('link[rel="manifest"], link[rel="apple-touch-icon"]').forEach(el => el.remove());
      const add = (tag, attrs) => { const el = doc.createElement(tag); for (const k in attrs) el.setAttribute(k, attrs[k]); doc.head.appendChild(el); return el; };
      add('link', { id: 'mg-pwa', rel: 'manifest', href: st + 'manifest.json' });
      add('link', { rel: 'apple-touch-icon', href: st + 'apple-touch-icon.png' });
      add('meta', { name: 'apple-mobile-web-app-capable', content: 'yes' });
      add('meta', { name: 'mobile-web-app-capable', content: 'yes' });
      add('meta', { name: 'apple-mobile-web-app-title', content: 'Mung9_' });
      add('meta', { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' });
      const tc = add('meta', { name: 'theme-color', content: isDark() ? '#0D1015' : '#FFFFFF' });
      new MutationObserver(() => tc.setAttribute('content', isDark() ? '#0D1015' : '#FFFFFF')).observe(root, { attributes: true, attributeFilter: ['data-mg-theme'] });
    }
  } catch (e) {}

  // 휴대폰에서 처음 온 사람에게 한 번만: '홈 화면에 추가' 안내 (닫으면 다시 안 뜸)
  try {
    const TOP = (() => { try { return window.top.document ? window.top : window; } catch (e) { return window; } })();
    let deferred = null;
    TOP.addEventListener('beforeinstallprompt', e => { e.preventDefault(); deferred = e; });
    const standalone = matchMedia('(display-mode: standalone)').matches || navigator.standalone;
    const seen = (() => { try { return localStorage.getItem('mg_a2hs'); } catch (e) { return '1'; } })();
    const inapp = /Instagram|FBAN|FBAV|KAKAOTALK|NAVER\(inapp|; wv\)/i.test(navigator.userAgent);
    if (!standalone && !seen && !inapp && matchMedia('(max-width: 768px)').matches) setTimeout(() => {
      const ios = /iPhone|iPad|iPod/i.test(navigator.userAgent);
      const st = d.createElement('style');
      st.textContent = '#mg-a2hs{position:fixed;left:12px;right:12px;bottom:84px;z-index:999992;display:flex;align-items:center;gap:12px;padding:14px 14px 14px 16px;border-radius:18px;background:rgba(20,24,31,.95);color:#fff;box-shadow:0 14px 40px rgba(0,0,0,.35);font-family:Pretendard,-apple-system,sans-serif;animation:mg-a2 .5s cubic-bezier(.2,1.3,.4,1)}'
        + '#mg-a2hs img{width:42px;height:42px;border-radius:11px}#mg-a2hs b{display:block;font-size:14px;font-weight:800}#mg-a2hs span{display:block;font-size:12px;color:rgba(255,255,255,.65);margin-top:2px;line-height:1.45}'
        + '#mg-a2hs button{border:0;border-radius:10px;font-family:inherit;font-weight:800;cursor:pointer}#mg-a2hs .go{background:#3182F6;color:#fff;padding:9px 12px;font-size:13px;white-space:nowrap}#mg-a2hs .no{background:transparent;color:rgba(255,255,255,.5);font-size:16px;padding:4px}'
        + '@keyframes mg-a2{from{transform:translateY(30px);opacity:0}to{transform:none;opacity:1}}';
      d.head.appendChild(st);
      const box = d.createElement('div'); box.id = 'mg-a2hs';
      const ico = (location.pathname.includes('/~/+/') ? location.pathname.split('/~/+/')[0] + '/~/+/' : '/') + 'app/static/icon-192.png';
      box.innerHTML = `<img src="${ico}" alt=""><div style="flex:1;min-width:0"><b>앱처럼 쓰기</b><span>${ios ? '아래 공유 버튼 → ‘홈 화면에 추가’를 누르면 앱처럼 열려요' : '홈 화면에 추가하면 앱처럼 바로 열려요'}</span></div>${ios ? '' : '<button class="go">추가</button>'}<button class="no" title="닫기">✕</button>`;
      d.body.appendChild(box);
      const done = () => { try { localStorage.setItem('mg_a2hs', '1'); } catch (e) {} box.remove(); };
      box.querySelector('.no').onclick = done;
      const go = box.querySelector('.go');
      if (go) go.onclick = async () => { if (deferred) { deferred.prompt(); try { await deferred.userChoice; } catch (e) {} done(); } else { box.querySelector('span').textContent = '브라우저 메뉴(⋮) → ‘홈 화면에 추가’ 또는 ‘앱 설치’를 눌러주세요'; go.remove(); } };
    }, 15000);
  } catch (e) {}
})();
"""


def inject():
    """사이트(부모 문서)에 한 번만 붙음."""
    components.html(
        f"""<script>
(function () {{
  const d = window.parent.document;
  if (d.getElementById('mg-theme-js')) return;
  const sc = d.createElement('script'); sc.id = 'mg-theme-js'; sc.textContent = {json.dumps(_JS)}; d.body.appendChild(sc);
}})();
</script>""",
        height=0,
    )
