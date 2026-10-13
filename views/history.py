from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import data as D
from lib.ui import (BLUE, DIVIDER, GRAY, GRAY_SOFT, GREEN, GREEN_SOFT, LINE_COLOR, RED, RED_SOFT, SUB, TEXT,
                    html, kpi, money, nav, pnl_color, section, title_row)
from lib import ui as _ui

nav("history")

# 차트 확대·이동 끄기 (휴대폰에서 스크롤하다 차트가 확대되는 문제)
PLOT_CFG = {"displayModeBar": False, "scrollZoom": False, "doubleClick": False, "staticPlot": False, "showAxisDragHandles": False}


def no_zoom(fig):
    fig.update_layout(dragmode=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig
KST = D.KST
# 차트 말풍선: 라이트·다크 둘 다 잘 보이게 어두운 색으로 고정
HOVER = dict(bgcolor="rgba(23,27,34,0.94)", bordercolor="rgba(255,255,255,0.08)", font=dict(color="#ECEEF2", size=12))
keys = D.get_keys()
# 처음 들어왔을 때·새로고침 버튼을 눌렀을 때만 로딩 화면을 보여주고, 그동안 예전 화면은 숨김
_full_load = st.session_state.pop("_full_reload", False) or "hist_seen" not in st.session_state
_loader = st.empty()
if _full_load:
    _loader.markdown("<style>[data-stale='true']{display:none !important;}</style>" + getattr(_ui, "LOADER_HTML", ""),
                     unsafe_allow_html=True)
hist = D.fetch_history(keys)
st.session_state["hist_seen"] = True
_loader.empty()
trades_all, events_all = hist["trades"], hist["events"]

def clear_all():
    D.fetch_positions.clear(); D.fetch_history.clear(); D.fetch_usdt_krw.clear(); D.fetch_live_ohlcv.clear()
    st.session_state["_full_reload"] = True
    st.session_state["_pos_ready"] = False
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
    badge = (f"<span class='dot' style='background:{GREEN};'></span><span style='font-size:13px;font-weight:700;color:{TEXT};'>Bitget</span>"
             f"<span class='hide-on-mobile' style='font-size:12px;color:{SUB};'>{hist['loaded_at'].strftime('%H:%M')} 기준</span>")
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
                pend = D.pending_fee_for(hist["pending_fees"], sym, p["side"], p["size"])
                pend_html = (f"<div style='font-size:11.5px;color:{SUB};margin-top:6px;'>진입 수수료 -${pend:,.2f} · 청산 시 반영</div>"
                             if pend > 0 else "")
                html(f"""<div class="pos-wrap" style="display:flex;flex-wrap:wrap;margin-bottom:5px;">
<div class="pos-box pb-sym" style="padding-left:0;"><div style='font-size:12.5px;color:{SUB};font-weight:600;margin-bottom:9px;'>종목 · 방향</div>
<div style='font-size:22px;font-weight:800;color:{TEXT};'>{sym} <span class='pill' style='background:{ss};color:{sc};font-size:12px;padding:4px 10px;'>{p['side']} {p['leverage']}x</span></div>
<div style='font-size:13px;color:{SUB};margin-top:8px;'>{p['size']} {coin} ≈ ${p['size'] * p['entry_price']:,.2f}</div></div>
<div class="pos-box pos-divider pb-px"><div style='font-size:12.5px;color:{SUB};font-weight:600;margin-bottom:12px;'>진입가 · 현재가</div>
<div style='display:flex;align-items:baseline;gap:8px;margin-bottom:6px;'><span style='width:42px;font-size:11.5px;color:{SUB};'>진입가</span><span style='font-size:17px;font-weight:700;color:{TEXT};'>${p['entry_price']:,.2f}</span></div>
<div style='display:flex;align-items:baseline;gap:8px;'><span style='width:42px;font-size:11.5px;color:{SUB};'>현재가</span><span style='font-size:17px;font-weight:700;color:{BLUE};'>${p['mark_price']:,.2f}</span></div></div>
<div class="pos-box pos-divider pb-pnl"><div style='font-size:12.5px;color:{SUB};font-weight:600;margin-bottom:12px;'>미실현 손익 · ROI</div>
<div style='font-size:24px;font-weight:800;color:{pc};margin-bottom:-4px;'>{sign}${p['unrealized_pnl']:,.2f}</div>
<div style='font-size:14px;font-weight:700;color:{pc};'>({sign}{p['roe']:.2f}%)</div>{pend_html}</div>
<div class="pos-box pos-divider pb-mg" style="padding-right:0;"><div style='font-size:12.5px;color:{SUB};font-weight:600;margin-bottom:12px;'>증거금 <span style="color:{BLUE};">(비중%)</span> · 청산가</div>
<div style='display:flex;align-items:baseline;gap:8px;margin-bottom:6px;'><span style='width:42px;font-size:11.5px;color:{SUB};'>증거금</span><span style='font-size:17px;font-weight:700;color:{TEXT};'>${p['margin']:,.2f} <span style='font-size:13px;color:{BLUE};'>({ratio:.1f}%)</span></span></div>
<div style='display:flex;align-items:baseline;gap:8px;'><span style='width:42px;font-size:11.5px;color:{SUB};'>청산가</span><span style='font-size:17px;font-weight:700;color:var(--mg-mid);'>${p['liq_price']:,.2f}</span></div></div></div>""")
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
                xaxis=dict(showgrid=True, gridcolor="rgba(139,149,161,0.14)", tickformat="%H:%M", tickfont=dict(color=GRAY, size=11)),
                yaxis=dict(showgrid=True, gridcolor="rgba(139,149,161,0.14)", side="right", tickfont=dict(color=GRAY, size=11)),
                hoverlabel=HOVER)
            st.plotly_chart(no_zoom(fig), width="stretch", config=PLOT_CFG, key=f"poschart_{safe}")


# 포지션은 거래소에서 바로 받아와야 해서 조금 늦음 → 자리만 먼저 잡고(로딩 카드), 아래 화면을 먼저 그린 뒤 맨 마지막에 채움
# 로딩 카드는 이 화면을 처음 열 때(또는 새로고침)만 → 이미 포지션을 받아온 뒤 다시 그릴 때는 바로 그 자리에 그림
_pos_ready = st.session_state.get("_pos_ready", False)
# 로딩 카드와 포지션이 '같은 한 칸'을 번갈아 씀 → 포지션이 그려지는 순간 로딩 카드가 그 자리에서 바뀜 (둘이 겹쳐 보일 수 없음)
pos_ph = st.empty()
if _pos_ready:
    with pos_ph.container():
        live_positions()
else:
    pos_ph.markdown(_ui.POS_SKELETON, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 상단 손익 카드
# -----------------------------------------------------------------------------
now = datetime.now(KST)
today_str, month_start = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-01")


def top_card(title, value, chip, krw_rate):
    color = GREEN if value >= 0 else RED
    krw = value * krw_rate
    krw_str = f"+₩{krw:,.0f}" if krw >= 0 else f"-₩{abs(krw):,.0f}"
    return f"""<div class="card topc">
<div class="topc-h"><span class="topc-t">{title}</span><span class="topc-chip">{chip}</span></div>
<div class="topc-v" style="color:{color};">{money(value)}</div>
<div class="topc-k">{krw_str}</div></div>"""


def day_chip(t):
    c = t[t["bucket"] == "축소"] if not t.empty else t
    if c.empty:
        return "거래 없음"
    w = int((c["result"] == "익절").sum()); l = int((c["result"] == "손절").sum())
    rate = f" · 승률 {w / (w + l) * 100:.0f}%" if (w + l) else ""
    return f"청산 {len(c)}건{rate}"


rate = D.fetch_usdt_krw()
c1, c2, c3 = st.columns(3)
with c1:
    t, e, _ = D.period_slice(hist, today_str, today_str)
    today_net = D.breakdown(t, e)["net"]
    html(top_card("오늘 PNL", today_net, day_chip(t), rate))
with c2:
    t, e, _ = D.period_slice(hist, month_start, today_str)
    month_net = D.breakdown(t, e)["net"]
    html(top_card("이번 달 PNL", month_net, day_chip(t), rate))
with c3:
    @st.fragment(run_every=10)
    def unrealized_card():
        pos, _, _ = D.fetch_positions(keys)
        u = sum(p["unrealized_pnl"] for p in pos) if pos else 0.0
        chip = f"포지션 {len(pos)}개 · 실시간" if pos else "포지션 없음"
        html(top_card("미실현 PNL", u, chip, D.fetch_usdt_krw()))
    u_ph = st.empty()
    if _pos_ready:
        with u_ph.container():
            unrealized_card()
    else:
        u_ph.markdown(_ui.TOPCARD_SKELETON.replace("{title}", "미실현 PNL"), unsafe_allow_html=True)

html(f"<div class='note-text' style='margin-top:-8px;'>PNL = 청산 손익 − 수수료 + 펀딩비 + 페이백 · 진입 수수료는 청산할 때 그 거래에서 함께 차감 · 미실현은 합계에 미포함</div>")

# 이번 달 목표 (값은 이 브라우저에 저장)
import calendar as _calendar
import json as _json
from pathlib import Path as _Path
import streamlit.components.v1 as _components
_goal = {"month": round(month_net, 2), "today": round(today_net, 2),
         "daysLeft": _calendar.monthrange(now.year, now.month)[1] - now.day}
st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
with st.container(key="goal_box"):
    _components.html((_Path(__file__).parent / "goal_card.html").read_text(encoding="utf-8").replace("__DATA__", _json.dumps(_goal)), height=130)

transfers = hist.get("transfers", [])

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


with st.container(key="range_row", horizontal=True, vertical_alignment="center", gap="small"):
    with st.container(key="range_date", width="content"):
        dates = st.date_input("기간", key="date_range", min_value=dash_start, max_value=today_d, label_visibility="collapsed",
                              on_change=clear_quick)
    st.segmented_control("빠른 기간", list(RANGES), key="quick_range", on_change=set_range, label_visibility="collapsed")

if isinstance(dates, (tuple, list)):
    start_d, end_d = (dates[0], dates[-1]) if len(dates) else (today_d, today_d)
else:
    start_d = end_d = dates
start_str, end_str = max(start_d, dash_start).strftime("%Y-%m-%d"), end_d.strftime("%Y-%m-%d")
f_trades, f_events, f_ledger = D.period_slice(hist, start_str, end_str)
bd = D.breakdown(f_trades, f_events)
perf = D.performance(f_trades)

html("""<div class='jumps'><button class='jump' data-mg-jump='div[class*="st-key-pnl_card"]'>손익 그래프</button><button class='jump' data-mg-jump='div[class*="st-key-cal_card"]'>캘린더</button><button class='jump' data-mg-jump='.pt-grid'>성과 지표</button><button class='jump' data-mg-jump='.ins-list'>습관 리포트</button><button class='jump' data-mg-jump='div[class*="st-key-share_box"]'>수익 카드</button><button class='jump' data-mg-jump='div[class*="st-key-chart_card_hour"]'>시간대</button><button class='jump' data-mg-jump='.log-card'>상세 내역</button></div>""")

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
card_style = "background:var(--mg-card);border-radius:20px;padding:22px;box-shadow:var(--mg-shadow);display:flex;flex-direction:column;justify-content:space-between;"


def pair(l1, v1, c1, l2, v2, c2):
    return (f"<div style='display:flex;font-size:13px;'><div style='flex:1;display:flex;justify-content:space-between;padding-right:15px;'>"
            f"<span style='color:{SUB};'>{l1}</span><b style='color:{c1};'>{v1}</b></div>"
            f"<div style='flex:1;display:flex;justify-content:space-between;padding-left:15px;'>"
            f"<span style='color:{SUB};'>{l2}</span><b style='color:{c2};'>{v2}</b></div></div>")


with col_t1:
    html(f"""<div class="tcard" style="{card_style}"><div><div class="card-title"><span>총 주문 횟수</span><span>선택 기간</span></div>
<div style='display:flex;align-items:baseline;margin:14px 0 22px;'><span style='font-size:34px;font-weight:800;color:{TEXT};'>{total}</span><span style='font-size:13px;font-weight:600;color:{SUB};margin-left:4px;'>회</span></div>
<div style='display:flex;flex-direction:column;gap:14px;'>{pair('진입', f'{incr} 회', TEXT, '청산', f'{decr} 회', TEXT)}{pair('익절', f'{wins} 회', GREEN, '손절', f'{losses} 회', RED)}</div></div>
<div style='border-top:1px solid var(--mg-line);padding-top:14px;display:flex;justify-content:space-between;align-items:center;'>
<span style='font-size:13px;color:{SUB};font-weight:600;'>기간 승률 <span style='font-weight:500;'>(수수료 차감 후)</span></span><b style='color:{BLUE};font-size:17px;'>{win_rate:.1f}%</b></div></div>""")

with col_t2:
    grad = f"conic-gradient({GREEN} 0% {lp}%, {RED} {lp}% 100%)" if (lg + sh) else "conic-gradient(var(--mg-soft) 0% 100%)"
    html(f"""<div class="tcard" style="{card_style}"><div class="card-title"><span>LONG / SHORT</span><span>청산 횟수 · 순손익</span></div>
<div style="display:flex;justify-content:center;align-items:center;flex-grow:1;"><div style="width:118px;height:118px;border-radius:50%;background:{grad};display:flex;justify-content:center;align-items:center;">
<div style="width:86px;height:86px;background:var(--mg-card);border-radius:50%;display:flex;flex-direction:column;justify-content:center;align-items:center;">
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
    dashes = "".join(f"<text x='{i * step:.1f}' y='60' font-size='13' style='fill:var(--mg-line2)' text-anchor='middle'>―</text>" for i, v in enumerate(vals) if v is None)
    days = "".join(f"<text x='{i * step:.1f}' y='130' font-size='10' style='fill:{SUB}' text-anchor='middle'>{labels[i]}</text>" for i in range(7))
    html(f"""<div class="tcard" style="{card_style}"><div class="card-title"><span>승률 추이</span><span>최근 7일 · 오늘 포함</span></div>
<div style="display:flex;align-items:baseline;gap:10px;margin-top:10px;"><span style="font-size:30px;font-weight:800;color:{BLUE};">{r7}%</span><span style="font-size:12px;color:{SUB};">익절 {tw} · 손절 {tl}</span></div>
<div style="flex-grow:1;display:flex;flex-direction:column;justify-content:flex-end;"><svg viewBox='-15 -15 310 150' style='width:100%;height:130px;display:block;'>{lines}{dots}{dashes}{days}</svg></div></div>""")

st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 기간 손익 차트
# -----------------------------------------------------------------------------
daily = D.daily_net(f_trades, f_events, start_str, end_str)


def style_fig(fig, height=330, category=True, ticks=None):
    fig.update_layout(
        margin=dict(t=20, b=10, l=10, r=10), height=height,
        font=dict(family="Pretendard, sans-serif", size=13, color=GRAY),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified", showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, type="category" if category else None,
                   tickmode="array" if ticks is not None else None, tickvals=ticks,
                   ticktext=[f"{t[5:7]}/{t[8:10]}" if isinstance(t, str) and len(t) == 10 else t for t in ticks] if ticks is not None else None,
                   tickangle=0, tickfont=dict(size=13, color=GRAY)),
        yaxis=dict(showgrid=True, gridcolor="rgba(139,149,161,0.14)", zeroline=True, zerolinecolor="rgba(139,149,161,0.35)", zerolinewidth=1.5, nticks=5,
                   tickfont=dict(size=13, color=GRAY)),
        hoverlabel=HOVER)
    return fig


with st.container(key="pnl_card"):
    last_v = daily["pnl"].iloc[-1] if not daily.empty else 0.0
    win_days = int((daily["pnl"] > 0).sum()) if not daily.empty else 0
    loss_days = int((daily["pnl"] < 0).sum()) if not daily.empty else 0
    with st.container(key="pnl_head", horizontal=True, vertical_alignment="center"):
        html(f"<div style='font-size:17px;color:{TEXT};font-weight:800;letter-spacing:-0.02em;line-height:40px;'>기간 PNL</div>")
        with st.container(key="pnl_view_box", width="content"):
            view = st.segmented_control("보기", ["일별", "누적"], default="일별", key="pnl_view", label_visibility="collapsed") or "일별"
    html(f"""<div style='border-top:1px solid var(--mg-line2);margin:-6px 0 14px;'></div>
<div style='display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;'><span style='font-size:30px;font-weight:800;color:{pnl_color(bd["net"])};letter-spacing:-0.02em;'>{money(bd["net"])}</span>
<span style='font-size:14px;color:{SUB};font-weight:600;'>USDT</span></div>
<div style='font-size:13px;color:{SUB};margin-top:4px;'>Win <b style='color:{GREEN};'>{win_days} days</b> · Loss <b style='color:{RED};'>{loss_days} days</b></div>
<div style='border-top:1px solid var(--mg-line);margin:16px 0 0;'></div>""")
    n = len(daily)
    # 날짜 눈금: 최대 5개를 고르게 (마지막 날 포함), 'MM/DD'로 짧게 → 휴대폰에서도 눕지 않음
    k = min(5, n)
    idx = sorted({round(j * (n - 1) / (k - 1)) for j in range(k)}) if k > 1 else [0]
    ticks = [daily["date"].iloc[i] for i in idx]
    if view == "일별":
        fig = go.Figure(go.Bar(x=daily["date"], y=daily["pnl"], marker=dict(color=[GREEN if v >= 0 else RED for v in daily["pnl"]], line_width=0, cornerradius=8),
                               hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"))
    else:
        fig = go.Figure(go.Scatter(x=daily["date"], y=daily["cum"], mode="lines+markers", line=dict(color=BLUE, width=3, shape="spline", smoothing=0.4),
                                   marker=dict(size=5), fill="tozeroy", fillcolor="rgba(49,130,246,0.08)",
                                   hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"))
    st.plotly_chart(no_zoom(style_fig(fig, ticks=ticks)), width="stretch", config=PLOT_CFG)
ledger_net = float(f_ledger["net"].sum()) if not f_ledger.empty else None
if ledger_net is not None:
    html(f"<div class='note-text' style='margin-top:-8px;'>검증용 · 거래소 장부 합계 {money(ledger_net)} (페이백 제외, 진입 수수료를 진입 시점에 바로 뺀 값)</div>")

# -----------------------------------------------------------------------------
# PNL 캘린더 (한 달을 달력으로: 날마다 순손익이 색으로 보임)
# -----------------------------------------------------------------------------
st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)


def _cal_amt(v):
    a = abs(v)
    s = f"{a / 1000:.1f}k" if a >= 1000 else (f"{a:.0f}" if a >= 10 else f"{a:.1f}")
    return ("+" if v > 0 else "-") + s


def calendar_html(year, month):
    import calendar as _cal
    first = datetime(year, month, 1).date()
    last = datetime(year, month, _cal.monthrange(year, month)[1]).date()
    lo = max(first, dash_start)
    t, e, _ = D.period_slice(hist, lo.strftime("%Y-%m-%d"), last.strftime("%Y-%m-%d"))
    dn = D.daily_net(t, e, lo.strftime("%Y-%m-%d"), last.strftime("%Y-%m-%d")) if lo <= last else pd.DataFrame(columns=["date", "pnl"])
    pnl = dict(zip(dn["date"], dn["pnl"])) if not dn.empty else {}
    cl = t[t["bucket"] == "축소"] if not t.empty else t
    cnt = cl.groupby("date").size().to_dict() if not cl.empty else {}
    vals = [abs(v) for v in pnl.values() if v]
    mx = max(vals) if vals else 1
    total = sum(pnl.values())
    wd = sum(1 for v in pnl.values() if v > 0); ld = sum(1 for v in pnl.values() if v < 0)
    cells = []
    for _ in range((first.weekday() + 1) % 7):  # 일요일 시작
        cells.append("<div class='cal-c empty'></div>")
    for d in range(1, last.day + 1):
        day = datetime(year, month, d).date()
        ds = day.strftime("%Y-%m-%d")
        v = pnl.get(ds, 0.0)
        cls = ["cal-c"]
        if day > today_d or day < dash_start:
            cls.append("off")
        if day == today_d:
            cls.append("today")
        style = ""
        if v:
            a = 0.14 + 0.66 * min(1.0, abs(v) / mx)
            style = f"background:rgba({'8,153,129' if v > 0 else '240,68,82'},{a:.2f});"
            # 옅은 칸은 글자를 색으로, 진한 칸은 흰 글자로 (잘 보이게)
            cls.append(("pos" if v > 0 else "neg") + ("" if a >= 0.42 else "-lt"))
        amt = f"<b>{_cal_amt(v)}</b>" if v else ""
        n = f"<i>{cnt[ds]}건</i>" if cnt.get(ds) else ""
        cells.append(f"<div class='{' '.join(cls)}' style='{style}' title='{ds} · {money(v)}'><span>{d}</span>{amt}{n}</div>")
    head = "".join(f"<div class='cal-h{' sun' if i == 0 else ' sat' if i == 6 else ''}'>{w}</div>" for i, w in enumerate("일월화수목금토"))
    return (f"<div class='cal-sum'><span class='{'up' if total > 0 else 'down' if total < 0 else ''}'>{money(total)}</span>"
            f"<small>수익 {wd}일 · 손실 {ld}일</small></div><div class='cal'>{head}{''.join(cells)}</div>")


if "cal_ym" not in st.session_state:
    st.session_state.cal_ym = (today_d.year, today_d.month)


def _cal_move(step):
    y, m = st.session_state.cal_ym
    m += step
    y, m = (y - 1, 12) if m < 1 else (y + 1, 1) if m > 12 else (y, m)
    if (y, m) <= (today_d.year, today_d.month) and (y, m) >= (dash_start.year, dash_start.month):
        st.session_state.cal_ym = (y, m)


with st.container(key="cal_card"):
    cy, cm = st.session_state.cal_ym
    with st.container(key="cal_head", horizontal=True, vertical_alignment="center"):
        html("<div class='cal-title'>PNL 캘린더</div>")
        with st.container(key="cal_nav", horizontal=True, vertical_alignment="center", width="content", gap="small"):
            st.button("", icon=":material/chevron_left:", key="cal_prev", on_click=_cal_move, args=(-1,),
                      disabled=(cy, cm) <= (dash_start.year, dash_start.month))
            html(f"<div class='cal-ym'>{cy}.{cm:02d}</div>")
            st.button("", icon=":material/chevron_right:", key="cal_next", on_click=_cal_move, args=(1,),
                      disabled=(cy, cm) >= (today_d.year, today_d.month))
    html(calendar_html(cy, cm))

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
    dots = "".join(f"<span class='sd' style='background:{RED if i < streak else 'var(--mg-line)'};'></span>" for i in range(n_dots))
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
# 매매 습관 리포트 (숫자를 보고 자동으로 짚어주는 코멘트)
# -----------------------------------------------------------------------------
def habit_insights():
    c = f_trades[(f_trades["bucket"] == "축소") & f_trades["has_pnl"]].sort_values("datetime") if not f_trades.empty else f_trades
    if c.empty or len(c) < 3:
        return []
    out = []
    pf = perf or {}
    aw, al = pf.get("avg_win", 0.0), pf.get("avg_loss", 0.0)
    wr = (c["net"] > 0).mean() * 100
    # 1) 손익비 · 본전 승률
    if aw > 0 and al > 0:
        rr_ = aw / al
        be = 100 / (1 + rr_)
        if rr_ < 1:
            out.append(("bad", "⚖️", f"평균 손절이 평균 익절의 {al / aw:.1f}배예요",
                        f"평균 익절 {money(aw)} · 평균 손절 {money(-al)}. 이 손익비면 승률이 {be:.0f}% 이상이어야 본전인데, 지금 승률은 {wr:.0f}%예요. "
                        + ("손절을 더 짧게 잡거나 익절을 조금 더 길게 가져가 보세요." if wr < be else "승률로 버티고 있지만, 손절 한 번이 크니 손절 폭부터 줄여보세요.")))
        else:
            out.append(("good", "⚖️", f"손익비 {rr_:.2f} — 이기면 크게, 지면 작게 하고 있어요",
                        f"이 손익비면 승률 {be:.0f}%만 넘어도 수익이에요. 지금 승률은 {wr:.0f}%" + ("라 수익 구조예요." if wr >= be else "로 조금 모자라요. 진입을 더 골라서 해보세요.")))
    # 2) 수수료 부담
    gp = float(c.loc[c["net"] > 0, "gross"].sum()) if "gross" in c else 0.0
    if bd["fee"] > 0:
        share = bd["fee"] / gp * 100 if gp > 0 else None
        tone = "bad" if (share or 0) >= 30 else "info"
        out.append((tone, "🧾", f"수수료로 {money(bd['fee'], sign=False)}를 냈어요",
                    (f"수익 난 거래에서 번 돈의 {share:.0f}%가 수수료로 나갔어요. " if share else "")
                    + (f"페이백으로 {money(bd['payback'], sign=False)}를 돌려받았어요. " if bd["payback"] > 0 else "")
                    + ("지정가(메이커) 진입을 늘리면 수수료를 크게 줄일 수 있어요." if tone == "bad" else "")))
    # 3) 롱 vs 숏
    ln = float(c.loc[c["side"] == "LONG", "net"].sum()); sn = float(c.loc[c["side"] == "SHORT", "net"].sum())
    lc_, sc_ = int((c["side"] == "LONG").sum()), int((c["side"] == "SHORT").sum())
    if lc_ and sc_ and abs(ln - sn) > 1:
        better, worse = ("롱", "숏") if ln > sn else ("숏", "롱")
        out.append(("info", "🧭", f"{better}이 {worse}보다 {money(abs(ln - sn), sign=False)} 더 벌었어요",
                    f"롱 {lc_}번 {money(ln)} · 숏 {sc_}번 {money(sn)}. " + (f"{worse} 쪽은 진입 기준을 다시 점검해보세요." if min(ln, sn) < 0 else "")))
    # 4) 손절 직후 다시 들어간 매매
    t = c.reset_index(drop=True)
    after_loss = []
    for i in range(1, len(t)):
        prev = t.iloc[i - 1]
        if prev["net"] < 0 and (pd.Timestamp(t.iloc[i]["datetime"]) - pd.Timestamp(prev["datetime"])).total_seconds() <= 1800:
            after_loss.append(t.iloc[i]["net"])
    if len(after_loss) >= 3:
        w2 = sum(1 for v in after_loss if v > 0) / len(after_loss) * 100
        tot = sum(after_loss)
        if w2 < wr - 5 or tot < 0:
            out.append(("bad", "😤", f"손절 후 30분 안에 다시 들어간 매매 승률 {w2:.0f}%",
                        f"{len(after_loss)}번, 합계 {money(tot)}. 평소 승률({wr:.0f}%)보다 낮아요 — 손절 직후엔 잠깐 쉬어가는 게 좋아요."))
        else:
            out.append(("good", "🧊", f"손절 후에도 침착해요 (재진입 승률 {w2:.0f}%)", f"손절 30분 안에 다시 들어간 {len(after_loss)}번, 합계 {money(tot)}."))
    # 5) 하루 매매 횟수와 손익
    per_day = c.groupby("date").agg(n=("net", "size"), pnl=("net", "sum"))
    if len(per_day) >= 4:
        med = per_day["n"].median()
        busy, calm = per_day[per_day["n"] > med], per_day[per_day["n"] <= med]
        if len(busy) and len(calm) and busy["pnl"].mean() < calm["pnl"].mean() - 1:
            out.append(("bad", "🔁", "많이 매매한 날일수록 손익이 나빠요",
                        f"하루 {med:.0f}번 넘게 청산한 날 평균 {money(busy['pnl'].mean())} · 그 이하인 날 평균 {money(calm['pnl'].mean())}. 과매매를 조심하세요."))
    # 6) 가장 잘 버는 시간대
    hrs = c.assign(h=pd.to_datetime(c["datetime"]).dt.hour // 4 * 4).groupby("h")["net"].sum()
    if len(hrs) >= 2:
        hb, hw = hrs.idxmax(), hrs.idxmin()
        if hrs[hb] > 0 and hrs[hw] < 0:
            out.append(("info", "🕐", f"{hb}~{hb + 4}시에 가장 잘 벌고, {hw}~{hw + 4}시에 가장 많이 잃어요",
                        f"{hb}~{hb + 4}시 {money(hrs[hb])} · {hw}~{hw + 4}시 {money(hrs[hw])}. 약한 시간대엔 매매를 줄여보는 것도 방법이에요."))
    return out[:5]


_ins = habit_insights()
if _ins:
    items = "".join(f"<div class='ins {tone}'><div class='ins-ic'>{ic}</div><div><b>{tt}</b><p>{body}</p></div></div>" for tone, ic, tt, body in _ins)
    html(f"<div class='card'><div class='card-title'><span>매매 습관 리포트</span><span>선택 기간 · 자동 분석</span></div><div class='ins-list'>{items}</div></div>")
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 수익 인증 카드 (이미지로 저장 · 공유)
# -----------------------------------------------------------------------------
_principal = sum(D.principal_list()) or 1.0
_share = {
    "period": f"{start_str.replace('-', '.')} ~ {end_str.replace('-', '.')}", "start": start_str, "end": end_str,
    "net": round(bd["net"], 2), "roi": bd["net"] / _principal * 100,
    "wins": wins, "losses": losses, "wr": win_rate if (wins + losses) else None, "count": decr,
    "pf": perf["profit_factor"] if perf else None, "best": perf["best"] if perf else None,
    "bestPct": (perf["best"] / _principal * 100) if perf else None,
    "wd": win_days, "ld": loss_days, "cum": [round(v, 2) for v in daily["cum"].tolist()] if not daily.empty else [],
}
from pathlib import Path as _Path
import json as _json
import streamlit.components.v1 as _components
with st.container(key="share_box"):
    _components.html((_Path(__file__).parent / "share_card.html").read_text(encoding="utf-8").replace("__DATA__", _json.dumps(_share)), height=560)
st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 시간대별 손익
# -----------------------------------------------------------------------------
with st.container(key="chart_card_hour"):
    with st.container(key="hour_head", horizontal=True, vertical_alignment="center"):
        html(f"<div style='font-size:17px;color:{TEXT};font-weight:800;letter-spacing:-0.02em;line-height:40px;'>언제 잘 벌까?</div>")
        with st.container(key="hour_view_box", width="content"):
            hview = st.segmented_control("기준", ["시간대별", "요일별"], default="시간대별", key="hour_view", label_visibility="collapsed") or "시간대별"
    if decr:
        dtc = pd.to_datetime(closes["datetime"])
        if hview == "시간대별":
            grp = closes.assign(k=dtc.dt.hour).groupby("k")["net"].agg(["sum", "size"]).reindex(range(24), fill_value=0)
            xs = [f"{h}시" for h in grp.index]
            ticks_h = [f"{h}시" for h in range(0, 24, 3)]
        else:
            grp = closes.assign(k=dtc.dt.weekday).groupby("k")["net"].agg(["sum", "size"]).reindex(range(7), fill_value=0)
            xs = list("월화수목금토일")
            ticks_h = xs
        best = grp["sum"].idxmax() if grp["sum"].max() > 0 else None
        worst = grp["sum"].idxmin() if grp["sum"].min() < 0 else None
        lab = (lambda k: f"{k}시" if hview == "시간대별" else "월화수목금토일"[k] + "요일")
        html("<div class='hour-sum'>" + (f"<span>가장 잘 번 {'시간' if hview == '시간대별' else '요일'} <b class='up'>{lab(best)} {money(grp['sum'][best])}</b></span>" if best is not None else "")
             + (f"<span>가장 많이 잃은 {'시간' if hview == '시간대별' else '요일'} <b class='down'>{lab(worst)} {money(grp['sum'][worst])}</b></span>" if worst is not None else "")
             + "<span>청산 시각 · KST</span></div>")
        fig = go.Figure(go.Bar(x=xs, y=grp["sum"],
                               marker=dict(color=[GREEN if v >= 0 else RED for v in grp["sum"]], line_width=0, cornerradius=4 if hview == "시간대별" else 8),
                               customdata=grp["size"], hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT · %{customdata}건<extra></extra>"))
        fig = style_fig(fig, height=260, ticks=ticks_h)
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
    kind = st.segmented_control("종류", ["전체", "청산", "진입", "입출금", "펀딩비"], default="전체",
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
if kind == "입출금":
    for t in transfers:
        rows.append(("transfer", t["datetime"], t))
if kind in ("전체", "펀딩비") and not f_events.empty:
    want = {"전체": ["payback"], "펀딩비": ["funding"]}[kind]
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
    # 날짜별로 묶어서 '10월 13일 (화) · 그날 순손익' 머리줄을 넣음
    def _amt(typ, r):
        if typ == "trade":
            return float(r.net) if (r.bucket == "축소" and r.has_pnl) else 0.0
        if typ == "event":
            return float(r.amount)
        return 0.0
    day_sum = {}
    for typ, dt, r in rows[:150]:
        k = pd.Timestamp(dt).strftime("%Y-%m-%d")
        day_sum[k] = day_sum.get(k, 0.0) + _amt(typ, r)
    prev_day = None
    for typ, dt, r in rows[:150]:
        ts_ = pd.Timestamp(dt)
        k = ts_.strftime("%Y-%m-%d")
        if k != prev_day:
            prev_day = k
            v = day_sum.get(k, 0.0)
            wd_ = "월화수목금토일"[ts_.weekday()]
            lab = "오늘" if k == today_str else ("어제" if k == (now - timedelta(days=1)).strftime("%Y-%m-%d") else f"{ts_.month}월 {ts_.day}일")
            out.append(f"<div class='log-day'><span>{lab} <small>({wd_})</small></span>"
                       f"<b style='color:{pnl_color(v)};'>{money(v) if v else ''}</b></div>")
        dt_str = ts_.strftime("%H:%M")
        if typ == "transfer":
            label, tag, c, icon = {"principal": ("원금 입금", "원금", BLUE, "🏦"), "payback": ("수수료 페이백", "페이백", GREEN, "💰"),
                                   "withdraw": ("출금", "출금", RED, "↗")}[r["kind"]]
            sign = -1 if r["kind"] == "withdraw" else 1
            out.append(f"<div class='log-row'><div class='log-left'><div class='sym-badge' style='background:{GRAY_SOFT};color:{c};'>{icon}</div>"
                       f"<div><div class='row-title'>{label} <span class='pill' style='background:{GRAY_SOFT};color:{c};'>{tag}</span></div>"
                       f"<div class='row-sub'>{pd.Timestamp(dt).strftime('%Y.%m.%d %H:%M')}</div></div></div>"
                       f"<div class='row-right'><div class='row-pnl' style='color:{c};'>{money(sign * r['amount'])}</div></div></div>")
            continue
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
            right = (f"<div class='row-price'><span>손익 {money(r.gross)}</span><span class='rs-sep'> · </span><span class='rs-d'>수수료 -${r.fee:,.2f}</span></div>"
                     f"<div class='row-pnl' style='color:{c};'>{money(r.net) if r.has_pnl else '-'}<span class='chip' style='background:{chip_bg};color:{c};'>{r.result}</span></div>")
        out.append(f"<div class='log-row'><div class='log-left'><div class='sym-badge' style='background:{ss};color:{sc};'>{coin[:1]}</div>"
                   f"<div><div class='row-title'>{r.symbol} <span class='pill' style='background:{ss};color:{sc};'>{r.side}</span></div>"
                   f"<div class='row-sub'><span>{dt_str}</span><span class='rs-sep'> · </span><span class='rs-d'>{'진입' if r.bucket == '증가' else '청산'} {qty_txt} @ {price}</span></div></div></div>"
                   f"<div class='row-right'>{right}</div></div>")
    html("<div class='card log-card' style='padding:0 20px 6px;max-height:680px;overflow-y:auto;'>" + "".join(out) + "</div>")
    if len(rows) > 150:
        html(f"<div class='note-text'>최근 150건만 표시 (전체 {len(rows)}건)</div>")

# -----------------------------------------------------------------------------
# 늦게 오는 포지션 정보를 맨 마지막에 채우기
# -----------------------------------------------------------------------------
if not _pos_ready:
    with pos_ph.container():
        live_positions()
    with u_ph.container():
        unrealized_card()
    st.session_state["_pos_ready"] = True
