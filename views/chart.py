import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from lib import data as D
from lib.ui import html, nav

# 차트 페이지는 어두운 전체 화면 레이아웃
html("""<style>
html, body, .stApp { background-color: #0F121A !important; }
.block-container { max-width: 100% !important; padding: 0.7rem 1rem 0 !important; }
iframe[title="st.iframe"], .stIFrame, iframe { border-radius: 12px; }
</style>""")
nav("chart", dark=True)

keys = D.get_keys()
positions, _, _ = D.fetch_positions(keys)
tickers = D.fetch_tickers()

pos_syms = list(dict.fromkeys(p["symbol"] for p in positions))
symbols = [s for s in dict.fromkeys(pos_syms + D.WATCH_SYMBOLS) if not tickers or s in tickers or s in pos_syms]

payload = {
    "symbols": symbols,
    "byId": {s.replace("/", ""): s for s in symbols},
    "initial": pos_syms[0] if pos_syms else "BTC/USDT",
    "tickers": {s: tickers[s] for s in symbols if s in tickers},
    "positions": [{k: p[k] for k in ("symbol", "side", "leverage", "entry_price", "mark_price", "size", "margin", "liq_price")}
                  for p in positions],
    "krw": D.fetch_usdt_krw(),
}

page = (Path(__file__).parent / "chart_app.html").read_text(encoding="utf-8")
components.html(page.replace("__DATA__", json.dumps(payload)), height=860)
