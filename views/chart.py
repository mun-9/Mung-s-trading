import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from lib import data as D
from lib.ui import html

# 차트 페이지는 화면 전체를 차트 터미널이 채움 (메뉴는 터미널 맨 위 줄에 있음)
html("""<style>
html, body, .stApp { background-color: #0F1219 !important; }
.block-container { max-width: 100% !important; padding: 0 !important; }
.block-container div[data-testid="stVerticalBlock"] { gap: 0 !important; }
iframe { display: block; border: 0; }
div[class*="st-key-hidden_nav_"] { display: none !important; }
</style>""")

# 차트 화면의 '매매 히스토리' 버튼이 대신 눌러주는 숨은 링크 (페이지 이동은 Streamlit 링크로만 가능)
with st.container(key="hidden_nav_history"):
    st.page_link("views/history.py", label="매매 히스토리")
with st.container(key="hidden_nav_market"):
    st.page_link("views/market.py", label="시장")

_boot = st.empty()
_boot.markdown("""<style>@keyframes mgp{0%,100%{transform:scaleY(.55);opacity:.55}50%{transform:scaleY(1);opacity:1}}</style>
<div style="height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;background:radial-gradient(ellipse at 50% 40%,#182038 0%,#0D1018 70%);">
<div style="display:flex;align-items:flex-end;gap:6px;height:44px;filter:drop-shadow(0 0 14px rgba(41,98,255,.7));">
<i style="display:block;width:10px;height:20px;border-radius:3px;background:#2962FF;transform-origin:bottom;animation:mgp 1.1s infinite"></i>
<i style="display:block;width:10px;height:31px;border-radius:3px;background:#2962FF;transform-origin:bottom;animation:mgp 1.1s .15s infinite"></i>
<i style="display:block;width:10px;height:44px;border-radius:3px;background:#2962FF;transform-origin:bottom;animation:mgp 1.1s .3s infinite"></i></div>
<div style="font-size:15px;letter-spacing:6px;color:#9AA4BF;font-weight:600;">MUNGGE <b style="color:#EDF0F5;">TERMINAL</b></div>
<div style="font-size:12.5px;color:#787B86;">시장 데이터 준비 중</div></div>""", unsafe_allow_html=True)

keys = D.get_keys()
positions, _, _ = D.fetch_positions(keys)
# 차트·시세 모두 OKX 기준 (OKX 조회가 막히면 Bitget 시세를 초기값으로만 사용, 브라우저가 OKX 실시간으로 덮어씀)
bitget = D.fetch_tickers()
tickers = (D.fetch_okx_tickers() if hasattr(D, "fetch_okx_tickers") else {}) or bitget
upbit = D.fetch_upbit_krw()

pos_syms = list(dict.fromkeys(p["symbol"] for p in positions))
if tickers:
    by_vol = sorted(tickers, key=lambda s: tickers[s].get("qv") or 0, reverse=True)[:300]
    symbols = list(dict.fromkeys(pos_syms + [s for s in D.WATCH_SYMBOLS if s in tickers] + by_vol))
else:
    symbols = list(dict.fromkeys(pos_syms + D.WATCH_SYMBOLS))

bases = {s.split("/")[0].replace("1000", "") for s in symbols} | {"USDT"}
payload = {
    "symbols": symbols,
    "byId": {s.replace("/", ""): s for s in symbols},
    "initial": pos_syms[0] if pos_syms else "BTC/USDT",
    "tickers": {s: tickers[s] for s in symbols if s in tickers},
    "positions": [{k: p[k] for k in ("symbol", "side", "leverage", "entry_price", "mark_price", "size", "margin", "liq_price")}
                  for p in positions],
    "upbit": {b: v for b, v in upbit.items() if b in bases},
    "bgfund": {s: {"funding": bitget[s].get("funding")} for s in symbols if s in bitget},
    "usdkrw": D.fetch_usdkrw(),
    "krw": D.fetch_usdt_krw(),
}

_boot.empty()
page = (Path(__file__).parent / "chart_app.html").read_text(encoding="utf-8")
components.html(page.replace("__DATA__", json.dumps(payload)), height=900)
