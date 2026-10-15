"""내 포지션 체결을 사이트 알림으로 (켜고 끄기는 각 브라우저에서: 도구 > 알림 설정, 히스토리 위 종 버튼).

체결 기록은 거래소 키가 있는 서버만 읽을 수 있어서, 서버가 3초마다 최근 체결을 받아 화면으로 넘겨줌.
알림을 켠 브라우저에서만 소리·팝업이 뜸 (기본은 꺼짐 → 사이트를 구경하는 다른 사람에게는 안 뜸).
"""
import json

import streamlit as st
import streamlit.components.v1 as components

from lib import data as D


@st.fragment(run_every=3)
def feed():
    keys = D.get_keys()
    if D.is_demo(keys):
        return
    try:
        items = D.fetch_recent_fills(keys)
    except Exception:
        items = []
    payload = json.dumps(items).replace("</", "<\\/")
    components.html(f"""<script>
(function () {{
  const items = {payload};
  const P = window.parent;
  try {{ if (P.mgFills) P.mgFills.update(items); else P.__mgFillsPending = items; }} catch (e) {{}}
}})();
</script>""", height=0)
