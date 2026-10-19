import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from lib import data as D
from lib.ui import html, nav

nav("market")
html("<div class='ph-title' style='margin:2px 0 4px;'>시장</div>"
     "<div style='font-size:14px;color:var(--mg-sub);margin-bottom:14px;'>공포·탐욕, 김프, 펀딩비, 청산, 롱숏 비율을 한 화면에서.</div>")

# 코드가 막 바뀐 직후 서버가 예전 모듈을 들고 있으면 새 함수가 없을 수 있어서, 그 경우 다시 불러옴
if not hasattr(D, "fetch_ls_external") or not hasattr(D, "fetch_options_all"):
    import importlib
    importlib.reload(D)

try:
    ls_ext = D.fetch_ls_external(("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"))
except Exception:
    ls_ext = {}

try:
    macro = D.fetch_macro()
except Exception:
    macro = []

payload = {"usdkrw": D.fetch_usdkrw(), "lsExt": ls_ext, "macro": macro}
page = (Path(__file__).parent / "market_app.html").read_text(encoding="utf-8")
components.html(page.replace("__DATA__", json.dumps(payload)), height=2600)


# 맨 위 시세 줄(코스피 · S&P500 ...)은 서버가 1분마다 새로 받아서 화면에 넘겨줌 (브라우저에서 직접 못 읽는 시세라서)
@st.fragment(run_every=60)
def _macro_feed():
    try:
        m = D.fetch_macro()
    except Exception:
        return
    components.html(f"<script>try{{const P=window.parent;P.__mgMkt={json.dumps(m)};P.dispatchEvent(new P.CustomEvent('mg-mkt'));}}catch(e){{}}</script>", height=0)


with st.container(key="mg_hidden_mkt"):
    _macro_feed()


# 옵션 지도(QQQ · SOXX · SOXL): CBOE 옵션 체인이 커서 화면을 먼저 띄운 뒤 받아서 넘겨줌 (5분마다 새로)
@st.fragment(run_every=300)
def _opt_feed():
    try:
        o = D.fetch_options_all()
    except Exception:
        return
    components.html(f"<script>try{{const P=window.parent;P.__mgOpt={json.dumps(o)};P.dispatchEvent(new P.CustomEvent('mg-opt'));}}catch(e){{}}</script>", height=0)


with st.container(key="mg_hidden_opt"):
    _opt_feed()
