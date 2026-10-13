import json
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from lib import data as D
from lib.ui import html, nav

nav("tools")
html("<div class='ph-title' style='margin:2px 0 4px;'>도구</div>"
     "<div style='font-size:14px;color:var(--mg-sub);margin-bottom:14px;'>진입 전에 계산부터. 가격 알림 · 포지션 크기 · 청산가 · 목표가 · 평단 · 수수료 · 기대값.</div>")

page = (Path(__file__).parent / "tools_app.html").read_text(encoding="utf-8")
# 높이는 화면 안에서 내용 길이에 맞춰 자동으로 늘어남


def _fx():
    try:
        return {"usdt": D.fetch_usdt_live(), "usdkrw": D.fetch_usdkrw_live()}
    except Exception:
        return {"usdt": None, "usdkrw": None}


components.html(page.replace("__DATA__", json.dumps(_fx())), height=1800)


# 테더 가격은 브라우저에서 업비트를 직접 못 읽어서, 서버가 20초마다 받아서 계산기에 넘겨줌
@st.fragment(run_every=20)
def _fx_feed():
    components.html(f"<script>try{{const P=window.parent;P.__mgFx={json.dumps({**_fx(), 'ts': int(time.time())})};P.dispatchEvent(new P.CustomEvent('mg-fx'));}}catch(e){{}}</script>", height=0)


with st.container(key="mg_hidden_fx"):
    _fx_feed()
