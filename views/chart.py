import json

import streamlit as st
import streamlit.components.v1 as components

from lib import data as D
from lib.ui import GREEN, GREEN_SOFT, RED, RED_SOFT, SUB, TEXT, html, money

INTERVALS = {"1분": "1", "3분": "3", "5분": "5", "15분": "15", "30분": "30", "1시간": "60", "4시간": "240", "1일": "D"}
LAYOUTS = ["3분할", "2분할", "1개"]
SOURCES = {"Bitget": "BITGET", "Binance": "BINANCE", "Bybit": "BYBIT"}

keys = D.get_keys()
positions, _, _ = D.fetch_positions(keys)
pos_syms = list(dict.fromkeys(p["symbol"] for p in positions))
symbols = list(dict.fromkeys(pos_syms + D.BASE_SYMBOLS))

# 페이지를 오가도 선택값 유지
S = st.session_state
S.setdefault("cv_sym", symbols[0])
S.setdefault("cv_src", "Bitget")
S.setdefault("cv_layout", "3분할")
S.setdefault("cv_theme", "다크")
S.setdefault("cv_iv", ["3분", "1시간", "4시간"])


def pick(label, options, store_key, **kw):
    cur = S[store_key] if S[store_key] in options else options[0]
    val = st.selectbox(label, options, index=options.index(cur), **kw)
    S[store_key] = val
    return val


html("<style>.block-container{max-width:1680px !important;}</style>")
html(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;"><span style="font-size:22px;">🕯️</span>
<span style="font-size:21px;font-weight:800;color:{TEXT};letter-spacing:-0.02em;">차트</span></div>""")

c1, c2, c3, c4 = st.columns([1.6, 1, 1, 1])
with c1:
    sym_labels = [f"{s.replace('/USDT', '')} {'· 보유 중' if s in pos_syms else ''}".strip() for s in symbols]
    cur_idx = symbols.index(S["cv_sym"]) if S["cv_sym"] in symbols else 0
    chosen = st.selectbox("종목", range(len(symbols)), index=cur_idx, format_func=lambda i: sym_labels[i])
    S["cv_sym"] = symbols[chosen]
with c2:
    src = pick("데이터 거래소", list(SOURCES), "cv_src")
with c3:
    layout = pick("레이아웃", LAYOUTS, "cv_layout")
with c4:
    theme = pick("테마", ["다크", "라이트"], "cv_theme")

sym = S["cv_sym"]
n_panels = {"3분할": 3, "2분할": 2, "1개": 1}[layout]
iv_cols = st.columns(3)
for i in range(3):
    with iv_cols[i]:
        if i < n_panels:
            name = ["메인 차트", "오른쪽 위", "오른쪽 아래"][i] if layout == "3분할" else ["왼쪽", "오른쪽", ""][i] if layout == "2분할" else "차트"
            opts = list(INTERVALS)
            cur = S["cv_iv"][i] if S["cv_iv"][i] in opts else "3분"
            S["cv_iv"][i] = st.selectbox(f"{name} 분봉", opts, index=opts.index(cur), key=f"cv_iv_{i}_{layout}")

# 선택 종목의 보유 포지션 요약 (TradingView 위젯에는 내 진입가를 그릴 수 없어서 위에 표시)
mine = [p for p in positions if p["symbol"] == sym]
if mine:
    chips = []
    for p in mine:
        sc, ss = (GREEN, GREEN_SOFT) if p["side"] == "LONG" else (RED, RED_SOFT)
        pc = GREEN if p["unrealized_pnl"] >= 0 else RED
        chips.append(f"<div style='display:flex;align-items:center;gap:10px;background:#fff;border-radius:14px;padding:10px 14px;box-shadow:0 2px 10px rgba(15,23,42,0.04);'>"
                     f"<span class='pill' style='background:{ss};color:{sc};'>{p['side']} {p['leverage']}x</span>"
                     f"<span style='font-size:13px;color:{SUB};'>진입 <b style='color:{TEXT};'>${p['entry_price']:,.2f}</b></span>"
                     f"<span style='font-size:13px;color:{SUB};'>청산가 <b style='color:{TEXT};'>${p['liq_price']:,.2f}</b></span>"
                     f"<span style='font-size:13px;font-weight:800;color:{pc};'>{money(p['unrealized_pnl'])} ({p['roe']:+.1f}%)</span></div>")
    html(f"<div style='display:flex;flex-wrap:wrap;gap:10px;margin:4px 0 12px;'>{''.join(chips)}</div>")


def tv_widget(symbol, interval, height, toolbar=True):
    cfg = {
        "autosize": True, "symbol": f"{SOURCES[src]}:{symbol.replace('/', '')}.P", "interval": interval,
        "timezone": "Asia/Seoul", "theme": "dark" if theme == "다크" else "light", "style": "1", "locale": "kr",
        "allow_symbol_change": True, "hide_side_toolbar": not toolbar, "hide_top_toolbar": False,
        "save_image": False, "calendar": False, "withdateranges": toolbar,
        "support_host": "https://www.tradingview.com",
    }
    bg = "#131722" if theme == "다크" else "#ffffff"
    components.html(f"""
<style>html,body{{margin:0;padding:0;height:100%;background:{bg};}}
.wrap{{height:{height - 4}px;width:100%;border-radius:14px;overflow:hidden;}}</style>
<div class="wrap"><div class="tradingview-widget-container" style="height:100%;width:100%">
<div class="tradingview-widget-container__widget" style="height:100%;width:100%"></div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
{json.dumps(cfg)}
</script></div></div>""", height=height)


iv = [INTERVALS[S["cv_iv"][i]] for i in range(3)]
if layout == "3분할":
    left, right = st.columns([2.1, 1], gap="small")
    with left:
        tv_widget(sym, iv[0], 788)
    with right:
        tv_widget(sym, iv[1], 386, toolbar=False)
        tv_widget(sym, iv[2], 386, toolbar=False)
elif layout == "2분할":
    a, b = st.columns(2, gap="small")
    with a:
        tv_widget(sym, iv[0], 700)
    with b:
        tv_widget(sym, iv[1], 700)
else:
    tv_widget(sym, iv[0], 800)

html(f"<div class='note-text'>TradingView 차트 · 차트 안에서 지표를 추가할 수 있지만 새로고침하면 초기화돼 · 내 체결 표시는 매매 히스토리 페이지 차트에 있어</div>")
