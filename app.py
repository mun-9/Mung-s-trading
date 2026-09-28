import random
from datetime import datetime, timedelta, timezone

import ccxt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

START = "2026-09-28"  # 이 날짜(UTC = KST 09:00 기준) 이전 데이터는 표시 안 함
UP, DN, ACC = "#0E9F6E", "#E5484D", "#2F5BEA"  # 수익 / 손실 / 강조 (한국식 적상승이면 UP↔DN 교체)
DEMO = "Demo (샘플 데이터)"
EX = {"Bitget": (ccxt.bitget, "swap"), "Binance": (ccxt.binance, "future"), "Bybit": (ccxt.bybit, "linear")}
SYMBOLS = [f"{c}/USDT:USDT" for c in ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "BCH", "BNB", "PEPE", "LINK"]]
COLS = ["datetime", "date", "symbol", "side", "pnl", "result"]
DEMO_POS = [dict(symbol="BTC/USDT", side="LONG", lev=20, entry=63250.0, mark=64800.0, size=0.5,
                 margin=1581.25, liq=60200.0, pnl=775.0, roe=49.0)]

st.set_page_config(page_title="멍그 Trading Journal", page_icon="📈", layout="wide")
st.markdown("""<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
.stApp,.stApp button,.stApp input{font-family:Pretendard,-apple-system,sans-serif}
.block-container{max-width:1180px;padding-top:2.2rem}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}
.top b{font-size:22px;font-weight:800;letter-spacing:-.03em;color:#0F1B33}
.top span{font-size:13px;color:#667085}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#0E9F6E;margin-right:6px;animation:p 2s infinite}
@keyframes p{0%,100%{opacity:1}50%{opacity:.25}}
.hero{display:grid;grid-template-columns:1.5fr 1fr 1fr;background:#0F1B33;border-radius:20px;color:#fff;overflow:hidden}
.hero>div{padding:26px 28px}
.hero>div+div{border-left:1px solid #26365a}
.hero .k,.hero small{color:#9db0d4}
.hero .v{font-size:28px}
.hero>div:first-child .v{font-size:40px}
@media(max-width:768px){.hero{grid-template-columns:1fr}.hero>div+div{border-left:0;border-top:1px solid #26365a}}
.card{background:#fff;border:1px solid #E4E7EC;border-radius:14px;padding:20px}
.k{font-size:13px;color:#667085;font-weight:600}
.v{font-size:30px;font-weight:800;letter-spacing:-.03em;font-variant-numeric:tabular-nums;margin:8px 0 4px}
.v small{font-size:13px;font-weight:600;color:#98a2b3}
.m{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums;margin:8px 0 4px}
.s{font-size:12px;color:#667085}
.pill{display:inline-block;padding:3px 9px;border-radius:999px;font-size:12px;font-weight:700;vertical-align:middle}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:20px}
.h{font-size:16px;font-weight:700;color:#0F1B33;margin:32px 0 12px}
.sc{min-height:300px}
.bar{display:flex;height:8px;border-radius:4px;overflow:hidden;background:#EEF0F4;margin:14px 0}
.bar i{display:block}
.r{display:flex;justify-content:space-between;font-size:13px;color:#667085;padding:6px 0}
.donut{width:120px;height:120px;border-radius:50%;margin:18px auto;display:grid;place-items:center}
.donut>div{width:86px;height:86px;border-radius:50%;background:#fff;display:grid;place-items:center;font-weight:800;color:#0F1B33}
[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-radius:14px}
.stButton>button{border-radius:10px;height:38px;white-space:nowrap}
</style>""", unsafe_allow_html=True)


# ---------- 유틸 ----------
def num(v): return float(v or 0)
def clr(v): return UP if v >= 0 else DN
def hc(v): return "#34D399" if v >= 0 else "#FB7185"
def money(v): return f"{'+' if v >= 0 else '-'}${abs(v):,.2f}"
def pill(t, c): return f"<span class='pill' style='color:{c};background:{c}22'>{t}</span>"
def today(): return datetime.now(timezone.utc).date()
def html(s): st.markdown(" ".join(x.strip() for x in s.splitlines()), unsafe_allow_html=True)


def secret(k, default=""):
    try: return st.secrets[k]
    except Exception: return default


def creds(ex):  # 거래소별 섹션 [BITGET] 우선, 없으면 최상위 키 사용
    try: s = st.secrets[ex.upper()]
    except Exception: s = {}
    return tuple(s.get(k) or secret(k) for k in ("API_KEY", "SECRET_KEY", "PASSPHRASE"))


pw = secret("APP_PASSWORD")  # secrets에 APP_PASSWORD 넣으면 비밀번호 잠금
if pw and not st.session_state.get("ok"):
    if st.text_input("비밀번호", type="password") == pw:
        st.session_state.ok = True
        st.rerun()
    st.stop()


def make_ex(name, key, sec, pwd):
    cls, t = EX[name]
    return cls({"apiKey": key, "secret": sec, "password": pwd, "enableRateLimit": True, "options": {"defaultType": t}})


def finalize(rows):  # 분할 체결을 주문 단위로 묶어 승률 왜곡 방지
    if not rows: return pd.DataFrame(columns=COLS)
    df = pd.DataFrame(rows).groupby(["order", "symbol", "side"], as_index=False).agg(
        datetime=("datetime", "max"), date=("date", "max"), gross=("gross", "sum"), pnl=("pnl", "sum"))
    df["result"] = df.apply(lambda r: "진입" if r.gross == 0 else ("익절" if r.pnl > 0 else "손절"), axis=1)
    return df.sort_values("datetime", ascending=False)[COLS]


def demo_trades():
    rnd, now, rows = random.Random(42), datetime.now(timezone.utc), []
    for i in range(60):
        t = now - timedelta(hours=rnd.randint(1, 240))
        g = rnd.choice([0, rnd.uniform(80, 900), rnd.uniform(80, 900), rnd.uniform(-600, -40)])
        rows.append(dict(order=i, symbol=rnd.choice(["BTC/USDT", "ETH/USDT", "SOL/USDT"]), side=rnd.choice(["LONG", "SHORT"]),
                         datetime=(t + timedelta(hours=9)).replace(tzinfo=None), date=t.strftime("%Y-%m-%d"), gross=g, pnl=g - 0.5))
    return finalize(rows), []


# ---------- 데이터 (실패는 예외로 올려 캐시에 저장되지 않게 함) ----------
@st.cache_data(ttl=5, show_spinner=False)
def fetch_fast(name, key, sec, pwd):
    if not key or name == DEMO: return DEMO_POS, 10000.0
    ex = make_ex(name, key, sec, pwd)
    bal = ex.fetch_balance({"type": "swap"} if name == "Bitget" else {})
    out = []
    for p in ex.fetch_positions():
        if num(p.get("contracts")) <= 0: continue
        m, u = num(p.get("initialMargin")), num(p.get("unrealizedPnl"))
        out.append(dict(symbol=(p.get("symbol") or "").replace(":USDT", ""), side=(p.get("side") or "long").upper(),
                        lev=int(num(p.get("leverage")) or 1), entry=num(p.get("entryPrice")), mark=num(p.get("markPrice")),
                        size=num(p.get("contracts")), margin=m, liq=num(p.get("liquidationPrice")), pnl=u,
                        roe=u / m * 100 if m else 0))
    return out, num((bal.get("USDT") or {}).get("total"))


@st.cache_data(ttl=3600, show_spinner="거래 내역 불러오는 중...")
def fetch_slow(name, key, sec, pwd):
    if not key or name == DEMO: return demo_trades()
    ex = make_ex(name, key, sec, pwd)
    ex.load_markets()
    since0 = int(datetime.strptime(START, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
    rows, errs = [], []
    for sym in SYMBOLS:
        if sym not in ex.markets: continue
        since = since0
        try:
            for _ in range(20):  # since 이후 100건씩 페이지네이션
                batch = ex.fetch_my_trades(sym, since=since, limit=100)
                for t in batch:
                    info = t.get("info") or {}
                    gross = num(info.get("profit") or info.get("realizedPnl"))  # Bitget / Binance
                    fee = num((t.get("fee") or {}).get("cost"))
                    ts = datetime.fromtimestamp(t["timestamp"] / 1000, timezone.utc)
                    ts_side = str(info.get("tradeSide", "")).lower()
                    side = "LONG" if "long" in ts_side else "SHORT" if "short" in ts_side else ("LONG" if t["side"] == "buy" else "SHORT")
                    rows.append(dict(order=t.get("order") or t["id"], symbol=t["symbol"].replace(":USDT", ""), side=side,
                                     datetime=(ts + timedelta(hours=9)).replace(tzinfo=None), date=ts.strftime("%Y-%m-%d"),
                                     gross=gross, pnl=gross - fee))
                if len(batch) < 100: break
                since = batch[-1]["timestamp"] + 1
        except Exception:
            errs.append(sym.split("/")[0])
    df = finalize(rows)
    return (df[df.date >= START] if not df.empty else df), errs


# ---------- 사이드바 ----------
name = st.sidebar.selectbox("거래소", [*EX, DEMO])
key, sec, pwd = creds(name)
A = (name, key, sec, pwd)
st.sidebar.caption("데모 데이터 표시 중" if name == DEMO or not key else "API 연동됨 (읽기 전용 키 권장)")
if st.sidebar.button("🔄 새로고침"):
    fetch_fast.clear(); fetch_slow.clear(); st.rerun()


def get_df(show=False):
    try:
        df, errs = fetch_slow(*A)
        if show and errs: st.warning("조회 실패 심볼: " + ", ".join(errs))
        return df
    except Exception as e:
        if show: st.error(f"거래내역 로드 실패: {e}")
        return pd.DataFrame(columns=COLS)


def get_pos():
    try: return (*fetch_fast(*A), None)
    except Exception as e: return [], 0.0, str(e)


def sel(a, b):
    df = get_df()
    return df[(df.date >= str(a)) & (df.date <= str(b))]


# ---------- 헤더 + 핵심 지표 ----------
html("<div class='top'><b>멍그 Trading Journal</b><span><i class='dot'></i>실시간 · 10초 갱신</span></div>")
get_df(show=True)


@st.fragment(run_every=10)
def kpis():
    df, (pos, _, _) = get_df(), (get_pos())
    t = today()
    d = df[df.date == str(t)].pnl.sum()
    m = df[df.date.str.startswith(t.strftime("%Y-%m"))].pnl.sum()
    u = sum(p["pnl"] for p in pos)

    def cell(title, v, foot):
        return (f"<div><div class='k'>{title}</div><div class='v' style='color:{hc(v)}'>{money(v)} <small>USDT</small></div>"
                f"<div class='s' style='color:#9db0d4'>{foot}</div></div>")
    html(f"<div class='hero'>{cell('오늘 추정 PNL', d, '매일 09:00(KST) 리셋')}"
         f"{cell('이번 달 추정 PNL', m, '매월 1일 09:00(KST) 리셋')}{cell('미실현 손익', u, '보유 포지션 합계, 일·월 PNL에는 미포함')}</div>")


kpis()

# ---------- 보유 포지션 ----------
html("<div class='h'>보유 포지션</div>")


@st.fragment(run_every=10)
def positions():
    pos, bal, err = get_pos()
    if err: st.error(f"포지션 조회 실패: {err}")
    elif not pos: html("<div class='card s' style='text-align:center;padding:28px'>진행 중인 포지션이 없습니다</div>")
    for p in pos:
        sc, pc = (UP if p["side"] == "LONG" else DN), clr(p["pnl"])
        tag, roe = pill(f"{p['side']} {p['lev']}x", sc), pill(f"{p['roe']:+.2f}%", pc)
        ratio = p["margin"] / bal * 100 if bal else 0
        dist = abs(p["mark"] - p["liq"]) / p["mark"] * 100 if p["liq"] and p["mark"] else 0
        html(f"""<div class='card grid' style='margin-bottom:12px'>
        <div><div class='k'>종목</div><div class='m'>{p['symbol']} {tag}</div><div class='s'>{p['size']} ≈ ${p['size'] * p['entry']:,.2f}</div></div>
        <div><div class='k'>진입가</div><div class='m'>${p['entry']:,.2f}</div><div class='s'>현재가 <b style='color:{ACC}'>${p['mark']:,.2f}</b></div></div>
        <div><div class='k'>미실현 손익</div><div class='m' style='color:{pc}'>{money(p['pnl'])} {roe}</div></div>
        <div><div class='k'>증거금</div><div class='m'>${p['margin']:,.2f} <span class='s'>({ratio:.1f}%)</span></div><div class='s'>청산가 ${p['liq']:,.2f}, 현재가와 {dist:.1f}% 차이</div></div>
        </div>""")


positions()

# ---------- 기간 필터 ----------
ss, lo = st.session_state, datetime.strptime(START, "%Y-%m-%d").date()
ss.setdefault("d0", lo)
ss.setdefault("d1", today())


def preset(a, b): ss.d0, ss.d1 = max(a, lo), b


html("<div class='h'>수익 히스토리</div>")
c = st.columns([1.4, 1.4, .8, .9, 1.1, 3, 1.3])
c[0].date_input("시작", key="d0", min_value=lo, label_visibility="collapsed")
c[1].date_input("종료", key="d1", label_visibility="collapsed")
c[2].button("오늘", on_click=preset, args=(today(), today()), use_container_width=True)
c[3].button("이번 달", on_click=preset, args=(today().replace(day=1), today()), use_container_width=True)
c[4].button("최근 30일", on_click=preset, args=(today() - timedelta(30), today()), use_container_width=True)
mode = c[6].selectbox("집계", ["일별", "주별", "월별"], label_visibility="collapsed")
d0, d1 = ss.d0, ss.d1


# ---------- 매매 동향 ----------
@st.fragment(run_every=60)
def stats(d0, d1):
    f, full = sel(d0, d1), get_df()
    w, l, e = (f.result == "익절").sum(), (f.result == "손절").sum(), (f.result == "진입").sum()
    n = w + l
    rate = w / n * 100 if n else 0
    lg, sh = (f.side == "LONG").sum(), (f.side == "SHORT").sum()
    lp = lg / (lg + sh) * 100 if lg + sh else 0
    bg = f"conic-gradient({UP} 0 {lp}%,{DN} {lp}% 100%)" if lg + sh else "#EEF0F4"

    vals = []  # 최근 7일 일별 승률 (청산 없는 날은 건너뜀)
    for i in range(6, -1, -1):
        x = full[full.date == str(today() - timedelta(i))]
        a, b = (x.result == "익절").sum(), (x.result == "손절").sum()
        vals.append(a / (a + b) * 100 if a + b else None)
    pts = [(10 + i * 46.7, 95 - v * .75, v) for i, v in enumerate(vals) if v is not None]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)
    dots = "".join(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3.5' fill='{ACC}'/><text x='{x:.1f}' y='{y - 9:.1f}' font-size='11' font-weight='700' fill='{ACC}' text-anchor='middle'>{v:.0f}%</text>" for x, y, v in pts)
    days = "".join(f"<text x='{10 + i * 46.7:.1f}' y='120' font-size='10' fill='#98a2b3' text-anchor='middle'>{(today() - timedelta(6 - i)).month}/{(today() - timedelta(6 - i)).day}</text>" for i in range(7))
    svg = f"<svg viewBox='0 0 300 125' style='width:100%;margin-top:14px'><polyline points='{line}' fill='none' stroke='{ACC}' stroke-width='2.5' stroke-linejoin='round'/>{dots}{days}</svg>"

    c1, c2, c3 = st.columns([1, 1, 1.2])
    with c1:
        html(f"""<div class='card sc'><div class='k'>체결 주문 {len(f)}건 (선택 기간)</div><div class='v'>{rate:.1f}% <small>승률</small></div>
        <div class='bar'><i style='width:{rate}%;background:{UP}'></i><i style='width:{100 - rate if n else 0}%;background:{DN}'></i></div>
        <div class='r'><span>익절 청산</span><b style='color:{UP}'>{w}건</b></div><div class='r'><span>손절 청산</span><b style='color:{DN}'>{l}건</b></div>
        <div class='r'><span>신규 진입</span><b style='color:{ACC}'>{e}건</b></div></div>""")
    with c2:
        html(f"""<div class='card sc'><div class='k'>롱 / 숏</div><div class='donut' style='background:{bg}'><div>{lg + sh}건</div></div>
        <div class='r'><span style='color:{UP};font-weight:700'>LONG</span><b>{lg}건 ({lp:.1f}%)</b></div>
        <div class='r'><span style='color:{DN};font-weight:700'>SHORT</span><b>{sh}건 ({100 - lp if lg + sh else 0:.1f}%)</b></div></div>""")
    with c3:
        html(f"<div class='card sc'><div class='k'>최근 7일 승률 추이</div>{svg}</div>")


stats(d0, d1)


# ---------- PNL 차트 ----------
def style(fig):
    fig.update_layout(template="plotly_white", height=340, margin=dict(t=10, b=10, l=10, r=10), hovermode="x unified",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(type="category", showgrid=False), yaxis=dict(gridcolor="#EEF0F4", zerolinecolor="#D0D5DD"))
    return fig


@st.fragment(run_every=60)
def charts(d0, d1, mode):
    f = sel(d0, d1).copy()
    total = f.pnl.sum()
    with st.container(border=True):
        html(f"<div class='k'>선택 기간 추정 PNL</div><div class='v' style='color:{clr(total)}'>{money(total)} <small>USDT</small></div>")
        if f.empty:
            st.caption("선택한 기간에 거래가 없습니다")
            return
        d = pd.to_datetime(f.date)
        f["b"] = {"일별": d.dt.strftime("%Y-%m-%d"), "주별": d.dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d"),
                  "월별": d.dt.strftime("%Y-%m")}[mode]
        g = f.groupby("b").pnl.sum().reset_index().sort_values("b")
        g["cum"] = g.pnl.cumsum()
        t1, t2 = st.tabs([f"{mode} 손익", "기간 누적"])
        with t1:
            st.plotly_chart(style(go.Figure(go.Bar(x=g.b, y=g.pnl, marker_color=[clr(v) for v in g.pnl]))),
                            use_container_width=True, config={"displayModeBar": False})
        with t2:
            st.plotly_chart(style(go.Figure(go.Scatter(x=g.b, y=g.cum, mode="lines+markers", line=dict(color=ACC, width=3),
                                                       fill="tozeroy", fillcolor="rgba(47,91,234,.10)"))),
                            use_container_width=True, config={"displayModeBar": False})


charts(d0, d1, mode)
html("<div class='s' style='margin:10px 0'>추정 PNL은 수수료를 반영한 USDT 기준이며, 하루는 09:00(KST)에 시작해. 기간 누적은 선택 기간 시작을 0으로 계산해.</div>")


# ---------- 상세 내역 ----------
@st.fragment(run_every=60)
def logs(d0, d1):
    f = sel(d0, d1)
    if f.empty:
        st.info("아직 등록된 거래 내역이 없습니다")
        return
    st.dataframe(f, hide_index=True, height=400, column_config={
        "datetime": st.column_config.DatetimeColumn("시간 (KST)", format="YYYY-MM-DD HH:mm"),
        "date": None, "symbol": "종목", "side": "방향",
        "pnl": st.column_config.NumberColumn("PNL (USDT)", format="%.2f"), "result": "결과"})


html("<div class='h'>상세 매매 내역</div>")
logs(d0, d1)
