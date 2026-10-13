"""최신 코인 뉴스를 사이트 전체 알림 기능(window.mgNews)에 넘겨줌.

뉴스 RSS는 브라우저에서 바로 못 읽어서(CORS) 서버가 2분마다 받아두고,
이 칸이 90초마다 다시 그려지면서 최신 목록을 부모 화면으로 전달함 → 중요 뉴스 알림 · 급변 이유 표시에 사용.
"""
import json

import streamlit as st
import streamlit.components.v1 as components

from lib import data as D


@st.fragment(run_every=90)
def feed():
    try:
        items = D.fetch_news()
    except Exception:
        items = []
    payload = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    components.html(f"""<script>
(function () {{
  const items = {payload};
  const P = window.parent;
  try {{ if (P.mgNews) P.mgNews.update(items); else P.__mgNewsPending = items; }} catch (e) {{}}
}})();
</script>""", height=0)
