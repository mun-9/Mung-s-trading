import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from lib import data as D
from lib.ui import html, nav

nav("coins")
html("<div class='ph-title' style='margin:2px 0 4px;'>코인</div>"
     "<div style='font-size:14px;color:var(--mg-sub);margin-bottom:14px;'>시가총액 상위 200개 코인의 시세·김프·펀딩비·뉴스를 한눈에. 코인을 누르면 상세 정보가 열려요.</div>")

# 코인 상세 창의 '차트 터미널에서 보기' 버튼이 대신 눌러주는 숨은 링크
with st.container(key="hidden_nav_chart"):
    st.page_link("views/chart.py", label="차트")

# 코드가 막 바뀐 직후 서버가 예전 모듈을 들고 있으면 새 함수가 없을 수 있어서, 그 경우 다시 불러옴
if not hasattr(D, "fetch_cg_markets"):
    import importlib
    importlib.reload(D)

bitget = D.fetch_tickers() or {}
funding = {s.split("/")[0]: v.get("funding") for s, v in bitget.items() if v.get("funding") is not None}
upbit = D.fetch_upbit_krw() or {}

payload = {
    "markets": D.fetch_cg_markets(),
    "trending": D.fetch_cg_trending(),
    "news": D.fetch_news(),
    "funding": funding,
    "upbit": {k: {"last": v.get("last")} for k, v in upbit.items() if v.get("last")},
    "usdkrw": D.fetch_usdkrw(),
}
page = (Path(__file__).parent / "coins_app.html").read_text(encoding="utf-8")
# 높이는 화면 안에서 내용 길이에 맞춰 자동으로 늘어남
components.html(page.replace("__DATA__", json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")), height=2400)
