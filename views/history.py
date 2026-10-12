from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import data as D
from lib.ui import (BLUE, DIVIDER, GRAY, GRAY_SOFT, GREEN, GREEN_SOFT, LINE_COLOR, RED, RED_SOFT, SUB, TEXT,
                    html, kpi, money, nav, pnl_color, section, title_row, LOADER_HTML)

nav("history")

# 차트 확대·이동 끄기 (휴대폰에서 스크롤하다 차트가 확대되는 문제)
PLOT_CFG = {"displayModeBar": False, "scrollZoom": False, "doubleClick": False, "staticPlot": False, "showAxisDragHandles": False}


def no_zoom(fig):
    fig.update_layout(dragmode=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig
KST = D.KST
keys = D.get_keys()
_loader = st.empty()
_loader.markdown(LOADER_HTML, unsafe_allow_html=True)
hist = D.fetch_history(keys)
_loader.empty()
trades_all, events_all = hist["trades"], hist["events"]

def clear_all():
    D.fetch_positions.clear(); D.fetch_history.clear(); D.fetch_usdt_krw.clear(); D.fetch_live_ohlcv.clear()
    st.rerun()


if hist["errors"]:
    shown = "<br>".join(hist["errors"][:5])
    more = f"<br>외 {len(hist['errors']) - 5}건" if len(hist["errors"]) > 5 else ""
    html(f"<div class='err-box'><b>일부 데이터를 불러오지 못했어요</b><br>{shown}{more}</div>")

# -----------------------------------------------------------------------------
# 보유 포지션 (10초 갱신)
# -----------------------------------------------------------------------------
if hist["demo"]:
    badge = f"<span class='dot' style='background:#F5A623;'></span><span style='font-size:12.5px;font-weight:700;color:{TEXT};'>데모 데이터</span>"
else:
    badge = (f"<span class='dot' style='background:{GREEN};'></span><span style='font-size:12.5px;font-weight:700;color:{TEXT};'>Bitget</span>"
             f"<span class='hide-on-mobile' style='font-size:11.5px;color:{SUB};'>실시간 연동 · {hist['loaded_at'].strftime('%H:%M')} 기준</span>")
title_row("보유 포지션", f"<span class='badge'>{badge}</span>", clear_all)


@st.fragment(run_every=10)
def live_positions():
    positions, wallet, err = D.fetch_positions(keys)
    if err:
        html(f"<div class='err-box'><b>포지션을 불러오지 못했어요</b> — API 키·권한 또는 거래소 응답을 확인해줘.<br>{err}</div>")
        return
    if not positions:
        html(f"<div class='card' style='text-align:center;color:{SUB};font-size:14px;padding:32px;margin-bottom:22px;'>현재 진행 중인 포지션이 없습니다</div>")
        return

    groups = {}
    for p in positions:
        groups.setdefault(p["symbol"], []).append(p)

    for sym, plist in groups.items():
        safe = sym.replace("/", "_")
        with st.container(key=f"pos_container_{safe}"):
            for i, p in enumerate(plist):
                sc, ss = (GREEN, GREEN_SOFT) if p["side"] == "LONG" else (RED, RED_SOFT)
                pc = GREEN if p["unrealized_pnl"] >= 0 else RED
                sign = "+" if p["unrealized_pnl"] >= 0 else ""
                coin = sym.split("/")[0]
                ratio = (p["margin"] / wallet * 100) if wallet > 0 else 0
                pend = hist["pending_fees"].get(f"{sym}|{p['side']}", 0.0)
                pend_html = (f"<div style='font-size:11.5px;color:{SUB};margin-top:6px;'>진입 수수료 -${pend:,.2f} · 청산 시 반영</div>"
                             if pend > 0 else "")
                html(f"""<div style="display:flex;flex-wrap:wrap;margin-bottom:5px;">
<div class="pos-box" style="padding-left:0;"><div style='font-size:12.5px;color:{SUB};font-weight:600;margin-bottom:9px;'>종목 · 방향</div>
<div style='font-size:22px;font-weight:800;color:{TEXT};'>{sym} <span class='pill' style='background:{ss};color:{sc};font-size:12px;padding:4px 10px;'>{p['side']} {p['leverage']}x</span></div>
<div style='font-size:13px;color:{SUB};margin-top:8px;'>{p['size']} {coin} ≈ ${p['size'] * p['entry_price']:,.2f}</div></div>
<div class="pos-box pos-divider"><div style='font-size:12.5px;color:{SUB};font-weight:600;margin-bottom:12px;'>진입가 · 현재가</div>
<div style='display:flex;align-items:baseline;gap:8px;margin-bottom:6px;'><span style='width:42px;font-size:11.5px;color:{SUB};'>진입가</span><span style='font-size:17px;font-weight:700;color:{TEXT};'>${p['entry_price']:,.2f}</span></div>
<div style='display:flex;align-items:baseline;gap:8px;'><span style='width:42px;font-size:11.5px;color:{SUB};'>현재가</span><span style='font-size:17px;font-weight:700;color:{BLUE};'>${p['mark_price']:,.2f}</span></div></div>
<div class="pos-box pos-divider"><div style='font-size:12.5px;color:{SUB};font-weight:600;margin-bottom:12px;'>미실현 손익 · ROI</div>
<div style='font-size:24px;font-weight:800;color:{pc};margin-bottom:-4px;'>{sign}${p['unrealized_pnl']:,.2f}</div>
<div style='font-size:14px;font-weight:700;color:{pc};'>({sign}{p['roe']:.2f}%)</div>{pend_html}</div>
<div class="pos-box pos-divider" style="padding-right:0;"><div style='font-size:12.5px;color:{SUB};font-weight:600;margin-bottom:12px;'>증거금 <span style="color:{BLUE};">(비중%)</span> · 청산가</div>
<div style='display:flex;align-items:baseline;gap:8px;margin-bottom:6px;'><span style='width:42px;font-size:11.5px;color:{SUB};'>증거금</span><span style='font-size:17px;font-weight:700;color:{TEXT};'>${p['margin']:,.2f} <span style='font-size:13px;color:{BLUE};'>({ratio:.1f}%)</span></span></div>
<div style='display:flex;align-items:baseline;gap:8px;'><span style='width:42px;font-size:11.5px;color:{SUB};'>청산가</span><span style='font-size:17px;font-weight:700;color:#4b5563;'>${p['liq_price']:,.2f}</span></div></div></div>""")
                if i < len(plist) - 1:
                    html(f"<div style='border-top:1px solid {DIVIDER};margin:10px 0 15px;'></div>")

            html(f"<div style='border-top:1px solid {DIVIDER};margin:16px 0 15px;'></div>")
            tf = st.segmented_control("분봉", ["3분봉", "5분봉", "15분봉", "1시간봉"], default="3분봉",
                                      label_visibility="collapsed", key=f"tf_{safe}") or "3분봉"
            df = D.fetch_live_ohlcv(sym, {"3분봉": "3m", "5분봉": "5m", "15분봉": "15m", "1시간봉": "1h"}[tf], 120)
            if df.empty:
                st.caption("차트 데이터를 불러오지 못했어요")
                continue
            fig = go.Figure(go.Candlestick(
                x=df["datetime"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
                increasing_line_color=GREEN, increasing_fillcolor=GREEN,
                decreasing_line_color=RED, decreasing_fillcolor=RED, line=dict(width=1), name="Price"))
            for p in plist:
                c = GREEN if p["side"] == "LONG" else RED
                fig.add_hline(y=p["entry_price"], line_dash="dot", line_width=1.3, line_color=c, opacity=0.6)
                fig.add_annotation(x=0.01, xref="paper", y=p["entry_price"], text=f" {p['side']} ${p['entry_price']:,.2f} ",
                                   showarrow=False, font=dict(color="#fff", size=10), bgcolor=c, borderpad=3,
                                   xanchor="left", yanchor="bottom")
            if not trades_all.empty:
                st_ = trades_all[(trades_all["symbol"] == sym) & (trades_all["datetime"] >= df["datetime"].min())]
                if not st_.empty:
                    buy = ((st_["side"] == "LONG") & (st_["bucket"] == "증가")) | ((st_["side"] == "SHORT") & (st_["bucket"] == "축소"))
                    off = ((df["high"].max() - df["low"].min()) or df["close"].iloc[-1] * 0.01) * 0.05
                    for mask, sym_m, col, name, dy in ((buy, "triangle-up", GREEN, "매수", -off), (~buy, "triangle-down", RED, "매도", off)):
                        part = st_[mask]
                        if not part.empty:
                            fig.add_trace(go.Scatter(
                                x=part["datetime"], y=part["price"] + dy, mode="markers", customdata=part["price"],
                                marker=dict(symbol=sym_m, size=11, color=col, line=dict(width=1, color="#fff")),
                                name=name, hovertemplate=f"<b>{name} 체결</b><br>%{{x}}<br>$%{{customdata:,.2f}}<extra></extra>"))
            fig.update_layout(
                height=350, margin=dict(t=15, b=10, l=10, r=45), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis_rangeslider_visible=False, showlegend=False, hovermode="x unified",
                xaxis=dict(showgrid=True, gridcolor="#F8F9FA", tickformat="%H:%M", tickfont=dict(color=GRAY, size=11)),
                yaxis=dict(showgrid=True, gridcolor="#F0F3F6", side="right", tickfont=dict(color=GRAY, size=11)),
                hoverlabel=dict(bgcolor="#fff", bordercolor="#F2F4F6", font=dict(color=TEXT, size=12)))
            st.plotly_chart(no_zoom(fig), width="stretch", config=PLOT_CFG, key=f"poschart_{safe}")


live_positions()

# -----------------------------------------------------------------------------
# 상단 손익 카드
# -----------------------------------------------------------------------------
now = datetime.now(KST)
today_str, month_start = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-01")


def top_card(title, value, sub, krw_rate):
    color = GREEN if value >= 0 else RED
    krw = value * krw_rate
    krw_str = f"+ ₩{krw:,.0f}" if krw >= 0 else f"- ₩{abs(krw):,.0f}"
    return f"""<div class="card" style="min-height:150px;display:flex;flex-direction:column;">
<div class="card-title"><span>{title}</span><span></span></div>
<div style="display:flex;align-items:baseline;gap:8px;margin:14px 0 2px;flex-wrap:wrap;">
<span style="font-size:30px;font-weight:800;color:{color};letter-spacing:-0.02em;">{money(value)}</span>
<span style="font-size:13px;font-weight:600;color:{SUB};">{krw_str}</span></div>
<div style="font-size:12px;color:{SUB};margin-top:auto;padding-top:10px;">{sub}</div></div>"""


rate = D.fetch_usdt_krw()
c1, c2, c3 = st.columns(3)
with c1:
    t, e, _ = D.period_slice(hist, today_str, today_str)
    b = D.breakdown(t, e)
    html(top_card("오늘 순손익", b["net"], f"수수료 -${b['fee']:,.2f} · 펀딩 {money(b['funding'])} · 페이백 {money(b['payback'])}", rate))
with c2:
    t, e, _ = D.period_slice(hist, month_start, today_str)
    b = D.breakdown(t, e)
    html(top_card("이번 달 순손익", b["net"], f"수수료 -${b['fee']:,.2f} · 펀딩 {money(b['funding'])} · 페이백 {money(b['payback'])}", rate))
with c3:
    @st.fragment(run_every=10)
    def unrealized_card():
        pos, _, _ = D.fetch_positions(keys)
        u = sum(p["unrealized_pnl"] for p in pos) if pos else 0.0
        open_keys = {f"{p['symbol']}|{p['side']}" for p in pos} if pos else set()
        pend = sum(v for k, v in hist["pending_fees"].items() if k in open_keys)
        sub = f"진입 수수료 -${pend:,.2f} 별도 · 10초 갱신" if pend > 0 else "전체 포지션 합계 · 10초 갱신"
        html(top_card("현재 미실현손익", u, sub, D.fetch_usdt_krw()))
    unrealized_card()

html(f"<div class='note-text'>순손익 = 청산 손익 − 수수료 + 펀딩비 + 페이백 · 진입 수수료는 청산할 때 그 거래에서 함께 차감 · 미실현손익은 합계에 미포함</div>")

# -----------------------------------------------------------------------------
# 기간 선택
# -----------------------------------------------------------------------------
section("매매 동향")
today_d = now.date()
dash_start = datetime.strptime(D.DASHBOARD_START_DATE, "%Y-%m-%d").date()
if "date_range" not in st.session_state:
    st.session_state.date_range = (max(dash_start, today_d - timedelta(days=30)), today_d)


RANGES = {"오늘": "today", "7일": "week", "이번 달": "month", "최근 30일": "30d"}


def set_range():
    mode = RANGES.get(st.session_state.get("quick_range"))
    if not mode:
        return
    starts = {"today": today_d, "week": today_d - timedelta(days=6), "month": today_d.replace(day=1),
              "30d": today_d - timedelta(days=30)}
    st.session_state.date_range = (max(dash_start, starts[mode]), today_d)


def clear_quick():
    st.session_state.quick_range = None


cd, cq = st.columns([1.3, 1])
with cq:
    st.segmented_control("빠른 기간", list(RANGES), key="quick_range", on_change=set_range, label_visibility="collapsed")
with cd:
    dates = st.date_input("기간", key="date_range", min_value=dash_start, max_value=today_d, label_visibility="collapsed",
                          on_change=clear_quick)

if isinstance(dates, (tuple, list)):
    start_d, end_d = (dates[0], dates[-1]) if len(dates) else (today_d, today_d)
else:
    start_d = end_d = dates
start_str, end_str = max(start_d, dash_start).strftime("%Y-%m-%d"), end_d.strftime("%Y-%m-%d")
f_trades, f_events, f_ledger = D.period_slice(hist, start_str, end_str)
bd = D.breakdown(f_trades, f_events)
perf = D.performance(f_trades)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 주문 횟수 · 롱숏 · 승률 추이
# -----------------------------------------------------------------------------
col_t1, col_t2, col_t3 = st.columns([1, 1, 1.2])
total = len(f_trades)
incr = int((f_trades["bucket"] == "증가").sum()) if total else 0
closes = f_trades[f_trades["bucket"] == "축소"] if total else f_trades
decr = len(closes)
wins = int((closes["result"] == "익절").sum()) if decr else 0
losses = int((closes["result"] == "손절").sum()) if decr else 0
win_rate = (wins / (wins + losses) * 100) if (wins + losses) else 0
lg = int((closes["side"] == "LONG").sum()) if decr else 0
sh = int((closes["side"] == "SHORT").sum()) if decr else 0
lp = (lg / (lg + sh) * 100) if (lg + sh) else 0
long_net = float(closes.loc[closes["side"] == "LONG", "net"].sum()) if decr else 0.0
short_net = float(closes.loc[closes["side"] == "SHORT", "net"].sum()) if decr else 0.0
card_style = "background:#fff;border-radius:20px;padding:22px;box-shadow:0 2px 14px rgba(15,23,42,0.05);height:320px;display:flex;flex-direction:column;justify-content:space-between;"


def pair(l1, v1, c1, l2, v2, c2):
    return (f"<div style='display:flex;font-size:13px;'><div style='flex:1;display:flex;justify-content:space-between;padding-right:15px;'>"
            f"<span style='color:{SUB};'>{l1}</span><b style='color:{c1};'>{v1}</b></div>"
            f"<div style='flex:1;display:flex;justify-content:space-between;padding-left:15px;'>"
            f"<span style='color:{SUB};'>{l2}</span><b style='color:{c2};'>{v2}</b></div></div>")


with col_t1:
    html(f"""<div style="{card_style}"><div><div class="card-title"><span>총 주문 횟수</span><span>선택 기간</span></div>
<div style='display:flex;align-items:baseline;margin:14px 0 22px;'><span style='font-size:34px;font-weight:800;color:{TEXT};'>{total}</span><span style='font-size:13px;font-weight:600;color:{SUB};margin-left:4px;'>회</span></div>
<div style='display:flex;flex-direction:column;gap:14px;'>{pair('진입', f'{incr} 회', TEXT, '청산', f'{decr} 회', TEXT)}{pair('익절', f'{wins} 회', GREEN, '손절', f'{losses} 회', RED)}</div></div>
<div style='border-top:1px solid {DIVIDER};padding-top:14px;display:flex;justify-content:space-between;align-items:center;'>
<span style='font-size:13px;color:{SUB};font-weight:600;'>기간 승률 <span style='font-weight:500;'>(수수료 차감 후)</span></span><b style='color:{BLUE};font-size:17px;'>{win_rate:.1f}%</b></div></div>""")

with col_t2:
    grad = f"conic-gradient({GREEN} 0% {lp}%, {RED} {lp}% 100%)" if (lg + sh) else "conic-gradient(#EEF0F4 0% 100%)"
    html(f"""<div style="{card_style}"><div class="card-title"><span>LONG / SHORT</span><span>청산 횟수 · 순손익</span></div>
<div style="display:flex;justify-content:center;align-items:center;flex-grow:1;"><div style="width:118px;height:118px;border-radius:50%;background:{grad};display:flex;justify-content:center;align-items:center;">
<div style="width:86px;height:86px;background:#fff;border-radius:50%;display:flex;flex-direction:column;justify-content:center;align-items:center;">
<span style="font-size:11.5px;color:{SUB};font-weight:600;">총 청산</span><b style="font-size:22px;color:{TEXT};">{decr}건</b></div></div></div>
<div><div style='display:flex;justify-content:space-between;font-size:13px;margin-bottom:8px;'><span style='color:{GREEN};font-weight:700;'>LONG {lg}건 · {lp:.0f}%</span><b style='color:{pnl_color(long_net)};'>{money(long_net)}</b></div>
<div style='display:flex;justify-content:space-between;font-size:13px;'><span style='color:{RED};font-weight:700;'>SHORT {sh}건 · {100 - lp if (lg + sh) else 0:.0f}%</span><b style='color:{pnl_color(short_net)};'>{money(short_net)}</b></div></div></div>""")

with col_t3:
    labels, vals, tw, tl = [], [], 0, 0
    for i in range(6, -1, -1):
        d = now - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        labels.append(d.strftime("%m/%d"))
        dc = trades_all[(trades_all["date"] == ds) & (trades_all["bucket"] == "축소")] if not trades_all.empty else trades_all
        w, l = int((dc["result"] == "익절").sum()), int((dc["result"] == "손절").sum())
        tw += w; tl += l
        vals.append(w / (w + l) * 100 if (w + l) else None)
    r7 = round(tw / (tw + tl) * 100) if (tw + tl) else 0
    step = 280 / 6
    runs, cur = [], []
    for i, v in enumerate(vals):
        if v is None:
            if cur: runs.append(cur); cur = []
        else:
            cur.append((i * step, 110 - v / 100 * 85, v))
    if cur: runs.append(cur)
    lines = "".join(f"<polyline points='{' '.join(f'{x:.1f},{y:.1f}' for x, y, _ in r)}' fill='none' stroke='{BLUE}' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'/>" for r in runs if len(r) > 1)
    dots = "".join(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='4' fill='{BLUE}'/><text x='{x:.1f}' y='{y - 12:.1f}' font-size='12' font-weight='bold' fill='{BLUE}' text-anchor='middle'>{v:.0f}%</text>" for r in runs for x, y, v in r)
    dashes = "".join(f"<text x='{i * step:.1f}' y='60' font-size='13' fill='#D1D6DB' text-anchor='middle'>―</text>" for i, v in enumerate(vals) if v is None)
    days = "".join(f"<text x='{i * step:.1f}' y='130' font-size='10' fill='{SUB}' text-anchor='middle'>{labels[i]}</text>" for i in range(7))
    html(f"""<div style="{card_style}"><div class="card-title"><span>승률 추이</span><span>최근 7일 · 오늘 포함</span></div>
<div style="display:flex;align-items:baseline;gap:10px;margin-top:10px;"><span style="font-size:30px;font-weight:800;color:{BLUE};">{r7}%</span><span style="font-size:12px;color:{SUB};">익절 {tw} · 손절 {tl}</span></div>
<div style="flex-grow:1;display:flex;flex-direction:column;justify-content:flex-end;"><svg viewBox='-15 -15 310 150' style='width:100%;height:130px;display:block;'>{lines}{dots}{dashes}{days}</svg></div></div>""")

st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 기간 손익 차트
# -----------------------------------------------------------------------------
daily = D.daily_net(f_trades, f_events, start_str, end_str)


def style_fig(fig, height=330, category=True, ticks=None):
    fig.update_layout(
        template="plotly_white", margin=dict(t=20, b=10, l=10, r=10), height=height,
        font=dict(family="Pretendard, sans-serif", size=13, color="#6B7684"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified", showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, type="category" if category else None,
                   tickmode="array" if ticks is not None else None, tickvals=ticks, tickfont=dict(size=13, color="#6B7684")),
        yaxis=dict(showgrid=True, gridcolor="#F2F4F6", zeroline=True, zerolinecolor="#E5E8EB", zerolinewidth=1.5, nticks=5,
                   tickfont=dict(size=13, color="#6B7684")),
        hoverlabel=dict(bgcolor="#fff", bordercolor="#F2F4F6", font=dict(color=TEXT, size=12)))
    return fig


n_pay = int((f_events["kind"] == "payback").sum()) if not f_events.empty else 0
bd_chips = "".join(
    f"<span>{k} <b style='color:{c};'>{v}</b></span>" for k, v, c in [
        ("청산 손익", money(bd["gross"]), pnl_color(bd["gross"])),
        ("수수료", money(-bd["fee"]), RED if bd["fee"] > 0 else SUB),
        ("펀딩비", money(bd["funding"]), pnl_color(bd["funding"])),
        (f"페이백 {n_pay}건", money(bd["payback"]), pnl_color(bd["payback"])),
    ])

with st.container(key="pnl_card"):
    last_v = daily["pnl"].iloc[-1] if not daily.empty else 0.0
    html(f"""<div style='display:flex;justify-content:space-between;align-items:baseline;'><span style='font-size:17px;color:{TEXT};font-weight:800;letter-spacing:-0.02em;'>기간 순손익</span>
<span style='font-size:12px;color:{SUB};'>{end_str} <b style='color:{pnl_color(last_v)};'>{money(last_v)}</b></span></div>
<div style='font-size:30px;font-weight:800;color:{pnl_color(bd["net"])};margin-top:8px;'>{money(bd["net"])} <span style='font-size:14px;color:{SUB};font-weight:600;'>USDT</span></div>
<div class='bd-chips' style='font-size:13.5px;'>{bd_chips}</div>
<div style="border-bottom:1px solid {DIVIDER};margin:14px 0 6px;"></div>""")
    tab1, tab2 = st.tabs(["일별 손익", "기간 누적"])
    n = len(daily)
    ticks = list(daily["date"]) if n <= 10 else [daily["date"].iloc[i] for i in sorted(set(range(0, n, max(1, n // 6))) | {n - 1})]
    with tab1:
        fig = go.Figure(go.Bar(x=daily["date"], y=daily["pnl"], marker=dict(color=[GREEN if v >= 0 else RED for v in daily["pnl"]], line_width=0, cornerradius=8),
                               hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"))
        st.plotly_chart(no_zoom(style_fig(fig, ticks=ticks)), width="stretch", config=PLOT_CFG)
    with tab2:
        fig = go.Figure(go.Scatter(x=daily["date"], y=daily["cum"], mode="lines+markers", line=dict(color=BLUE, width=3, shape="spline", smoothing=0.4),
                                   marker=dict(size=5), fill="tozeroy", fillcolor="rgba(49,130,246,0.08)",
                                   hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"))
        st.plotly_chart(no_zoom(style_fig(fig, ticks=ticks)), width="stretch", config=PLOT_CFG)
ledger_net = float(f_ledger["net"].sum()) if not f_ledger.empty else None
if ledger_net is not None:
    html(f"<div class='note-text'>검증용 · 거래소 장부 합계 {money(ledger_net)} (페이백 제외, 진입 수수료를 진입 시점에 바로 뺀 값)</div>")

# -----------------------------------------------------------------------------
# 성과 지표
# -----------------------------------------------------------------------------
st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)


def perf_html(p):
    pf = p["profit_factor"]
    pf_txt = f"{pf:.2f}" if pf is not None else "∞"
    pf_col = GREEN if (pf is None or pf >= 1) else RED
    pf_w = 100 if pf is None else min(pf, 3) / 3 * 100
    rr_txt = f"{p['rr']:.2f}" if p["rr"] is not None else "-"
    mx = max(p["avg_win"], p["avg_loss"]) or 1
    streak = p["max_loss_streak"]
    n_dots = min(max(streak, 6), 12)
    dots = "".join(f"<span class='sd' style='background:{RED if i < streak else '#E5E8EB'};'></span>" for i in range(n_dots))
    dd = p["dd"]
    spark = ""
    if len(dd) > 1:
        lo = min(dd) or -1
        pts = " ".join(f"{i / (len(dd) - 1) * 200:.1f},{(v / lo) * 40:.1f}" for i, v in enumerate(dd))
        spark = (f"<svg viewBox='0 -2 200 44' preserveAspectRatio='none' style='width:100%;height:44px;display:block;'>"
                 f"<polygon points='0,0 {pts} 200,0' fill='rgba(240,68,82,0.10)'/>"
                 f"<polyline points='{pts}' fill='none' stroke='{RED}' stroke-width='1.6' vector-effect='non-scaling-stroke'/></svg>")
    return f"""<div class="card"><div class="card-title"><span>성과 지표</span><span>수수료 차감 후 · 청산 {p['count']}건</span></div>
<div class="pt-grid">
<div class="pt"><div class="pt-label">Profit Factor</div><div class="pt-value" style="color:{pf_col};">{pf_txt}</div>
  <div class="gauge"><div class="gauge-fill" style="width:{pf_w:.0f}%;background:{pf_col};"></div><div class="gauge-mark" style="left:33.33%;"></div></div>
  <div class="pt-foot"><span>0</span><span>1.0 이상이면 수익</span><span>3+</span></div></div>
<div class="pt"><div class="pt-label">손익비</div><div class="pt-value">{rr_txt}</div>
  <div class="bar-row"><span>평균 익절</span><div class="bar"><div style="width:{p['avg_win'] / mx * 100:.0f}%;background:{GREEN};"></div></div><b style="color:{GREEN};">{money(p['avg_win'])}</b></div>
  <div class="bar-row"><span>평균 손절</span><div class="bar"><div style="width:{p['avg_loss'] / mx * 100:.0f}%;background:{RED};"></div></div><b style="color:{RED};">{money(-p['avg_loss'])}</b></div></div>
<div class="pt"><div class="pt-label">최대 연속 손절</div><div class="pt-value">{streak}<span class="pt-unit">회</span></div>
  <div class="streak">{dots}</div>
  <div class="pt-foot"><span>최고 <b style="color:{GREEN};">{money(p['best'])}</b></span><span>최악 <b style="color:{RED};">{money(p['worst'])}</b></span></div></div>
<div class="pt"><div class="pt-label">최대 낙폭</div><div class="pt-value" style="color:{RED if p['mdd'] < 0 else TEXT};">{money(p['mdd'])}</div>
  {spark}<div class="pt-foot"><span>누적 순손익 고점 대비 하락폭</span></div></div>
</div></div>"""


if perf:
    html(perf_html(perf))
else:
    html(f"<div class='card' style='color:{SUB};text-align:center;padding:40px;'>선택한 기간에 청산 거래가 없어서 성과 지표를 계산할 수 없어요</div>")
st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 시간대별 손익
# -----------------------------------------------------------------------------
with st.container(key="chart_card_hour"):
    html(f"<div class='card-title'><span>시간대별 순손익</span><span>청산 시각 · KST</span></div>")
    if decr:
        hrs = closes.assign(h=pd.to_datetime(closes["datetime"]).dt.hour).groupby("h")["net"].agg(["sum", "size"]).reindex(range(24), fill_value=0)
        fig = go.Figure(go.Bar(x=[f"{h}시" for h in hrs.index], y=hrs["sum"],
                               marker=dict(color=[GREEN if v >= 0 else RED for v in hrs["sum"]], line_width=0, cornerradius=4),
                               customdata=hrs["size"], hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT · %{customdata}건<extra></extra>"))
        fig = style_fig(fig, height=280, ticks=[f"{h}시" for h in range(0, 24, 2)])
        fig.update_layout(hovermode="closest")
        st.plotly_chart(no_zoom(fig), width="stretch", config=PLOT_CFG)
    else:
        st.caption("청산 거래가 없습니다")

# -----------------------------------------------------------------------------
# 상세 매매 내역
# -----------------------------------------------------------------------------
section("상세 매매 내역")
fc1, fc2 = st.columns([2.2, 1])
with fc1:
    kind = st.segmented_control("종류", ["전체", "청산", "진입", "페이백", "펀딩비"], default="전체",
                                label_visibility="collapsed", key="log_kind") or "전체"
with fc2:
    sym_opts = ["전체 종목"] + sorted(f_trades["symbol"].unique().tolist()) if not f_trades.empty else ["전체 종목"]
    sym_pick = st.selectbox("종목", sym_opts, label_visibility="collapsed")

rows = []
tview = f_trades if sym_pick == "전체 종목" else f_trades[f_trades["symbol"] == sym_pick]
if kind in ("전체", "청산", "진입") and not tview.empty:
    if kind != "전체":
        tview = tview[tview["bucket"] == ("축소" if kind == "청산" else "증가")]
    for r in tview.itertuples(index=False):
        rows.append(("trade", r.datetime, r))
if kind in ("전체", "페이백", "펀딩비") and not f_events.empty:
    want = {"전체": ["payback"], "페이백": ["payback"], "펀딩비": ["funding"]}[kind]
    ev = f_events[f_events["kind"].isin(want)]
    if sym_pick != "전체 종목":
        ev = ev[(ev["symbol"] == sym_pick) | (ev["kind"] == "payback")] if kind != "펀딩비" else ev[ev["symbol"] == sym_pick]
    for r in ev.itertuples(index=False):
        rows.append(("event", r.datetime, r))
rows.sort(key=lambda x: x[1], reverse=True)

if not rows:
    html(f"<div class='card' style='text-align:center;color:{SUB};padding:32px;'>표시할 내역이 없습니다</div>")
else:
    out = []
    for typ, dt, r in rows[:150]:
        dt_str = pd.Timestamp(dt).strftime("%m.%d %H:%M")
        if typ == "event":
            is_pay = r.kind == "payback"
            name = "수수료 페이백" if is_pay else f"펀딩비 · {r.symbol}"
            badge, tag = ("💰", "입금") if is_pay else ("⏱", "펀딩")
            c = pnl_color(r.amount)
            out.append(f"<div class='log-row'><div class='log-left'><div class='sym-badge' style='background:{GREEN_SOFT if r.amount >= 0 else RED_SOFT};color:{c};'>{badge}</div>"
                       f"<div><div class='row-title'>{name} <span class='pill' style='background:{GRAY_SOFT};color:{SUB};'>{tag}</span></div>"
                       f"<div class='row-sub'>{dt_str}</div></div></div>"
                       f"<div class='row-right'><div class='row-pnl' style='color:{c};'>{money(r.amount)}</div></div></div>")
            continue
        sc, ss = (GREEN, GREEN_SOFT) if r.side == "LONG" else (RED, RED_SOFT)
        price = f"${r.price:,.2f}" if r.price > 0 else "-"
        coin = r.symbol.split("/")[0]
        qty_txt = f"{r.amount:,.6g} {coin}"
        notional = r.amount * r.price
        if r.bucket == "증가":
            right = (f"<div class='row-price'>≈ ${notional:,.2f}</div>"
                     f"<div class='row-pnl' style='color:{TEXT};font-weight:600;font-size:14px;'>{qty_txt}<span class='chip' style='background:{ss};color:{sc};'>진입</span></div>")
        else:
            c = pnl_color(r.net) if r.result in ("익절", "손절") else SUB
            chip_bg = GREEN_SOFT if r.result == "익절" else (RED_SOFT if r.result == "손절" else GRAY_SOFT)
            right = (f"<div class='row-price'>손익 {money(r.gross)} · 수수료 -${r.fee:,.2f}</div>"
                     f"<div class='row-pnl' style='color:{c};'>{money(r.net) if r.has_pnl else '-'}<span class='chip' style='background:{chip_bg};color:{c};'>{r.result}</span></div>")
        out.append(f"<div class='log-row'><div class='log-left'><div class='sym-badge' style='background:{ss};color:{sc};'>{coin[:1]}</div>"
                   f"<div><div class='row-title'>{r.symbol} <span class='pill' style='background:{ss};color:{sc};'>{r.side}</span></div>"
                   f"<div class='row-sub'>{dt_str} · {'진입' if r.bucket == '증가' else '청산'} {qty_txt} @ {price}</div></div></div>"
                   f"<div class='row-right'>{right}</div></div>")
    html("<div class='card' style='padding:6px 20px;max-height:620px;overflow-y:auto;'>" + "".join(out) + "</div>")
    if len(rows) > 150:
        html(f"<div class='note-text'>최근 150건만 표시 (전체 {len(rows)}건)</div>")
