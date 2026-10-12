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
</style>""")

keys = D.get_keys()
positions, _, _ = D.fetch_positions(keys)
tickers = D.fetch_tickers()
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
    "usdkrw": D.fetch_usdkrw(),
    "krw": D.fetch_usdt_krw(),
}

page = (Path(__file__).parent / "chart_app.html").read_text(encoding="utf-8")
components.html(page.replace("__DATA__", json.dumps(payload)), height=900)
