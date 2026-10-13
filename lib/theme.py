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
