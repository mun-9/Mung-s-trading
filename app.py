import ccxt
import time
import random
from datetime import datetime, timedelta, timezone
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# 🔑 웹사이트 비밀 금고에서 API 키를 뒤에서 몰래 꺼내옵니다
# =============================================================================
try:
    MY_API_KEY = st.secrets["API_KEY"]
    MY_SECRET_KEY = st.secrets["SECRET_KEY"]
    MY_PASSPHRASE = st.secrets["PASSPHRASE"]
except Exception:
    MY_API_KEY = ""
    MY_SECRET_KEY = ""
    MY_PASSPHRASE = ""

# 🎯 [초기화 설정] 여기서 설정한 날짜 이전의 과거 데이터는 싹 다 날립니다!
DASHBOARD_START_DATE = "2026-09-28"

# 🇰🇷 표시용 한국시간 (UTC+9) / 날짜 구분은 UTC 기준 (= KST 오전 9시에 날짜가 바뀜)
KST = timezone(timedelta(hours=9))
UTC = timezone.utc

# 🎨 색상 상수 (여기만 바꾸면 전체 톤이 바뀜)
GREEN, RED, BLUE, GRAY = "#00a86b", "#ef4444", "#2563eb", "#9ca3af"

# -----------------------------------------------------------------------------
# 1. 페이지 설정 & 모바일 완벽 대응 CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="멍그 Trading Journal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #f4f5f7; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        padding: 20px !important;
    }

    /* 🔥 10초·1시간 자동 새로고침(st.fragment) 때 화면이 하얗게 깜빡이는 현상 억제 */
    div[data-testid="stVerticalBlock"], div[data-testid="element-container"],
    div[data-testid="stMarkdownContainer"] {
        opacity: 1 !important;
        transition: none !important;
    }

    .pos-box { padding: 10px; flex: 1 1 200px; }
    .pos-divider { border-left: 1px solid #f3f4f6; }
    @media (max-width: 768px) {
        .pos-divider { border-left: none !important; border-top: 1px solid #f3f4f6 !important; padding-top: 15px !important; margin-top: 5px !important; }
    }

    .stButton>button { height: 38px; padding: 0 8px; border-radius: 8px; border: 1px solid #d1d5db; background-color: #ffffff; color: #374151; font-weight: 500; white-space: nowrap; }
    .stButton>button:hover { border-color: #2563eb; color: #2563eb; }

    /* 매매 동향 카드 통계 그리드 */
    .note-text { font-size:11.5px; line-height:1.7; color:#9ca3af; margin:14px 2px 0; }
    .pnl-box { padding: 0 !important; }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. 체결 분류 유틸 — 증가(신규·추가 진입) / 축소(부분·전체 청산)
# -----------------------------------------------------------------------------
def classify_fill(t):
    """거래소 원본 필드로 증가/축소, 승·패를 판별합니다.
    Bitget: info.tradeSide 에 open/close 가 그대로 들어와 정확히 판별됩니다.
    Binance/Bybit: reduceOnly 가 없으면 realizedPnl 유무로 추정합니다(참고용)."""
    info = t.get("info", {}) or {}
    ts = str(info.get("tradeSide", "")).lower()
    ro = info.get("reduceOnly", t.get("reduceOnly"))
    raw = info.get("profit", info.get("realizedPnl"))
    has_pnl = raw not in (None, "")
    pnl = float(raw or 0)

    if "open" in ts:
        is_close = False
    elif "close" in ts:
        is_close = True
    elif ro is True:
        is_close = True
    elif ro is False:
        is_close = False
    else:
        is_close = has_pnl and pnl != 0  # 마지막 수단: 실현손익이 찍히면 축소로 간주

    if "long" in ts:
        side = "LONG"
    elif "short" in ts:
        side = "SHORT"
    else:
        side = "LONG" if t["side"].upper() == "BUY" else "SHORT"

    return side, is_close, has_pnl, pnl


def result_of(bucket, has_pnl, pnl):
    if bucket == "증가":
        return "진입"
    if not has_pnl:
        return "미확인"
    if pnl > 0:
        return "익절"
    if pnl < 0:
        return "손절"
    return "본전"


TRADE_COLS = ["order_id", "datetime", "date", "symbol", "side", "bucket", "has_pnl", "pnl", "result"]


def finalize(rows):
    """분할 체결을 주문 단위로 묶어서 승률 왜곡을 막습니다."""
    if not rows:
        return pd.DataFrame(columns=TRADE_COLS)
    df = pd.DataFrame(rows)
    g = df.groupby(["order_id", "symbol", "side", "date"], as_index=False).agg(
        pnl=("pnl", "sum"),
        datetime=("datetime", "last"),
        bucket=("bucket", lambda s: s.mode().iat[0]),
        has_pnl=("has_pnl", "max"),
    )
    g["result"] = g.apply(lambda r: result_of(r.bucket, r.has_pnl, r.pnl), axis=1)
    return g.sort_values("datetime", ascending=False)


def demo_trades():
    rnd = random.Random(42)
    now = datetime.now(UTC)
    rows = []
    for i in range(300):
        t = now - timedelta(hours=rnd.randint(1, 900))
        is_close = rnd.random() < 0.55
        pnl = (rnd.choice([rnd.uniform(50, 900), rnd.uniform(50, 900), rnd.uniform(-700, -40), 0.0])
               if is_close else 0.0)
        rows.append({
            "order_id": f"DEMO_{i}",
            "datetime": (t + timedelta(hours=9)).replace(tzinfo=None),
            "date": t.strftime("%Y-%m-%d"),
            "symbol": rnd.choice(["BTC/USDT", "ETH/USDT", "SOL/USDT"]),
            "side": rnd.choice(["LONG", "SHORT"]),
            "bucket": "축소" if is_close else "증가",
            "has_pnl": True,
            "pnl": round(pnl, 2),
        })
    df = finalize(rows)  # order_id 가 이미 고유해서 그룹핑은 통과만 시킴
    return df[df["date"] >= DASHBOARD_START_DATE]


# -----------------------------------------------------------------------------
# 3. 캐싱된 API 데이터 로드 (포지션 10초 / 체결내역 1시간 분리)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=10, show_spinner=False)
def fetch_fast_data(exchange_name, api_key, secret, pwd):
    if not api_key or not secret or exchange_name == "Demo (샘플 데이터)":
        return [{
            "symbol": "BTC/USDT", "side": "LONG", "leverage": 20,
            "entry_price": 63250.0, "mark_price": 64800.0, "size": 0.5,
            "margin": 1581.25, "liq_price": 60200.0, "unrealized_pnl": 775.0, "roe": 49.0
        }], 10000.0
    try:
        if exchange_name == "Bitget": exchange = ccxt.bitget({'apiKey': api_key, 'secret': secret, 'password': pwd, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
        elif exchange_name == "Binance": exchange = ccxt.binance({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'future'}})
        elif exchange_name == "Bybit": exchange = ccxt.bybit({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'linear'}})

        bal = exchange.fetch_balance({'type': 'swap'}) if exchange_name == "Bitget" else exchange.fetch_balance()
        total_balance = float(bal.get('USDT', {}).get('total', 0))

        active_positions = []
        for p in exchange.fetch_positions():
            if float(p.get("contracts", 0) or 0) > 0:
                pos_side = (p.get("side") or "LONG").upper()
                entry, mark = float(p.get("entryPrice", 0) or 0), float(p.get("markPrice", 0) or 0)
                size, margin = float(p.get("contracts", 0) or 0), float(p.get("initialMargin", 0) or 0)
                unreal_pnl = float(p.get("unrealizedPnl") or ((mark - entry) * size if pos_side == "LONG" else (entry - mark) * size))
                roe = (unreal_pnl / margin * 100) if margin > 0 else 0
                active_positions.append({
                    "symbol": (p.get("symbol") or "").replace(":USDT", ""), "side": pos_side, "leverage": int(p.get("leverage", 1) or 1),
                    "entry_price": entry, "mark_price": mark, "size": size, "margin": margin,
                    "liq_price": float(p.get("liquidationPrice") or 0), "unrealized_pnl": unreal_pnl, "roe": roe,
                })
        return active_positions, total_balance
    except Exception:
        return [], 0.0


@st.cache_data(ttl=3600, show_spinner="거래 내역 불러오는 중...")
def fetch_slow_data(exchange_name, api_key, secret, pwd):
    if not api_key or not secret or exchange_name == "Demo (샘플 데이터)":
        return demo_trades()

    try:
        if exchange_name == "Bitget": exchange = ccxt.bitget({'apiKey': api_key, 'secret': secret, 'password': pwd, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
        elif exchange_name == "Binance": exchange = ccxt.binance({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'future'}})
        elif exchange_name == "Bybit": exchange = ccxt.bybit({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'linear'}})

        exchange.load_markets()
        rows = []
        for sym in ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "XRP/USDT:USDT", "DOGE/USDT:USDT", "ADA/USDT:USDT", "BCH/USDT:USDT", "BNB/USDT:USDT", "PEPE/USDT:USDT", "LINK/USDT:USDT"]:
            if sym not in exchange.markets:
                continue
            try:
                for t in exchange.fetch_my_trades(symbol=sym, limit=200):
                    t_utc = datetime.fromtimestamp(t["timestamp"] / 1000, tz=UTC)
                    t_kst = t_utc.astimezone(KST)
                    side, is_close, has_pnl, pnl = classify_fill(t)
                    order_id = str(t.get("order") or t.get("id") or t["timestamp"])
                    rows.append({
                        "order_id": order_id,
                        "datetime": t_kst.replace(tzinfo=None),
                        "date": t_utc.strftime("%Y-%m-%d"),  # UTC 날짜 = KST 오전 9시에 날짜 전환
                        "symbol": t["symbol"].replace(":USDT", ""), "side": side,
                        "bucket": "축소" if is_close else "증가",
                        "has_pnl": has_pnl, "pnl": pnl,
                    })
            except Exception:
                continue

        df = finalize(rows)
        return df[df["date"] >= DASHBOARD_START_DATE] if not df.empty else df
    except Exception:
        return pd.DataFrame(columns=TRADE_COLS)


# -----------------------------------------------------------------------------
# 4. 사이드바 메뉴
# -----------------------------------------------------------------------------
st.sidebar.title("⚙️ 멍그 대시보드 설정")
exchange_choice = st.sidebar.selectbox("거래소 선택", ["Bitget", "Binance", "Bybit", "Demo (샘플 데이터)"])
st.sidebar.markdown(f"<div style='font-size:13px; color:{GREEN}; margin-bottom:15px;'>✅ API 보안 금고 연동 완료</div>", unsafe_allow_html=True)
st.sidebar.markdown(f"<div style='font-size:12px; color:{BLUE}; margin-bottom:15px;'>🟢 실시간 자동 업데이트 작동 중 (10초 단위)</div>", unsafe_allow_html=True)

if st.sidebar.button("🔄 수동 새로고침"):
    fetch_fast_data.clear()
    fetch_slow_data.clear()
    st.rerun()

df_trades = fetch_slow_data(exchange_choice, MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)

# -----------------------------------------------------------------------------
# 5. 🎯 메인 타이틀
# -----------------------------------------------------------------------------
st.markdown("""
<div style="margin-top: -10px; margin-bottom: 25px;">
    <h1 style="font-size: 32px; font-weight: 900; color: #111827; margin: 0; padding: 0; letter-spacing: -0.5px;">Trading History</h1>
    <div style="width: 40px; height: 4px; background-color: #2563eb; margin-top: 10px; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; padding-bottom: 15px; border-bottom: 2px solid #e5e7eb; margin-bottom: 25px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="background: linear-gradient(135deg, #00a86b, #059669); color: white; font-weight: 900; padding: 6px 14px; border-radius: 8px; font-size: 18px; box-shadow: 0 2px 4px rgba(0,168,107,0.3);">멍그</span>
        <span style="font-size: 22px; font-weight: 900; color: #111827; letter-spacing: -0.5px;">MUNGGE TRADING JOURNAL</span>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. [FRAGMENT] 🎯 현재 보유 포지션
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 16px; font-weight: 800; color: #111827; margin-bottom: 10px;'>🎯 현재 보유 포지션</div>", unsafe_allow_html=True)

@st.fragment(run_every=10)
def show_live_positions():
    current_positions, wallet_balance = fetch_fast_data(exchange_choice, MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)
    if not current_positions:
        st.markdown("<div style='background-color:#ffffff; border:1px solid #e5e7eb; border-radius:12px; padding:24px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); text-align: center; color: #9ca3af; font-size: 15px; margin-bottom: 25px;'>현재 진행 중인 포지션이 없습니다.</div>", unsafe_allow_html=True)
    else:
        for pos in current_positions:
            pos_side = pos["side"]
            side_color, side_bg = (GREEN, "rgba(0,168,107,0.1)") if pos_side == "LONG" else (RED, "rgba(239,68,68,0.1)")
            pnl_val, roe_val = pos["unrealized_pnl"], pos["roe"]
            pnl_color, pnl_sign = (GREEN, "+") if pnl_val >= 0 else (RED, "")
            base_coin = pos['symbol'].split('/')[0] if '/' in pos['symbol'] else pos['symbol']
            pos_usdt_value = pos['size'] * pos['entry_price']
            margin_ratio = (pos['margin'] / wallet_balance * 100) if wallet_balance > 0 else 0

            st.markdown(f"""
            <div style="background-color:#ffffff; border:1px solid #e5e7eb; border-radius:12px; padding:15px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); display: flex; flex-wrap: wrap; margin-bottom: 15px;">
                <div class="pos-box">
                    <div style='font-size: 13px; color: #6b7280; font-weight: 600; margin-bottom: 8px;'>종목 / 방향 및 규모</div>
                    <div style='font-size: 24px; font-weight: 800; color: #111827;'>{pos['symbol']} <span style='font-size: 13px; font-weight: 700; color: {side_color}; background-color: {side_bg}; padding: 4px 8px; border-radius: 6px; margin-left: 5px; vertical-align: middle;'>{pos_side} {pos['leverage']}x</span></div>
                    <div style='font-size: 14px; color: #4b5563; font-weight: 600; margin-top: 8px;'>{pos['size']} {base_coin} ≈ ${pos_usdt_value:,.2f}</div>
                </div>
                <div class="pos-box pos-divider">
                    <div style='font-size: 13px; color: #6b7280; font-weight: 600; margin-bottom: 12px;'>진입가 / 현재가</div>
                    <div style='display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px;'><span style='width: 45px; font-size: 12px; color: #9ca3af;'>진입가</span><span style='font-size: 18px; font-weight: 700; color: #111827;'>${pos['entry_price']:,.2f}</span></div>
                    <div style='display: flex; align-items: baseline; gap: 8px;'><span style='width: 45px; font-size: 12px; color: #9ca3af;'>현재가</span><span style='font-size: 18px; font-weight: 700; color: #2563eb;'>${pos['mark_price']:,.2f}</span></div>
                </div>
                <div class="pos-box pos-divider">
                    <div style='font-size: 13px; color: #6b7280; font-weight: 600; margin-bottom: 12px;'>미실현 손익 / 수익률(ROI)</div>
                    <div style='font-size: 26px; font-weight: 800; color: {pnl_color}; margin-bottom: -5px;'>{pnl_sign}${pnl_val:,.2f}</div>
                    <div style='font-size: 15px; font-weight: 700; color: {pnl_color};'>({pnl_sign}{roe_val:.2f}%)</div>
                </div>
                <div class="pos-box pos-divider">
                    <div style='font-size: 13px; color: #6b7280; font-weight: 600; margin-bottom: 12px;'>증거금 <span style="color:#2563eb;">(비중%)</span> / 청산가</div>
                    <div style='display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px;'><span style='width: 45px; font-size: 12px; color: #9ca3af;'>증거금</span><span style='font-size: 18px; font-weight: 700; color: #111827;'>${pos['margin']:,.2f} <span style='font-size:14px; color:#2563eb;'>({margin_ratio:.1f}%)</span></span></div>
                    <div style='display: flex; align-items: baseline; gap: 8px;'><span style='width: 45px; font-size: 12px; color: #9ca3af;'>청산가</span><span style='font-size: 18px; font-weight: 700; color: #4b5563;'>${pos['liq_price']:,.2f}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
show_live_positions()

# -----------------------------------------------------------------------------
# 7. 상단 PNL 카드 (날짜 기준: UTC = KST 오전 9시 전환)
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 11px; color: #9ca3af; margin-bottom: 10px; margin-top: -10px;'>미실현손익은 일별·월별 추정 PNL 합계에 포함하지 않습니다.</div>", unsafe_allow_html=True)
col_s1, col_s2, col_s3 = st.columns(3)

def make_top_card(title, value, sub_left, sub_right=""):
    val_color, sign = (GREEN, "+") if value >= 0 else (RED, "")
    return f"""<div style="background-color:#ffffff; border:1px solid #e5e7eb; border-radius:12px; padding:24px; min-height: 155px; display:flex; flex-direction:column; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
        <div><div style="display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;"><span>{title}</span> <span style="color:#9ca3af; font-weight:400;">{sub_right}</span></div>
        <div style="font-size:32px; font-weight:800; color:{val_color}; margin:15px 0;">{sign}${value:,.2f} <span style="font-size:14px; font-weight:600; color:#00a86b;">USDT</span></div></div>
        <div style="font-size:12px; color:#9ca3af; margin-top:auto;">{sub_left}</div></div>"""

with col_s1:
    @st.fragment(run_every=3600)
    def render_today_pnl():
        today_str = datetime.now(UTC).strftime("%Y-%m-%d")
        today_pnl = df_trades[df_trades["date"] == today_str]["pnl"].sum() if not df_trades.empty else 0.0
        st.markdown(make_top_card("오늘 추정 PNL", today_pnl, "매일 오전 9시 리셋 (KST)"), unsafe_allow_html=True)
    render_today_pnl()

with col_s2:
    @st.fragment(run_every=3600)
    def render_month_pnl():
        month_str = datetime.now(UTC).strftime("%Y-%m")
        month_pnl = df_trades[df_trades["date"].str.startswith(month_str)]["pnl"].sum() if not df_trades.empty else 0.0
        st.markdown(make_top_card("이번 달 추정 PNL", month_pnl, "매월 1일 오전 9시 리셋 (KST)"), unsafe_allow_html=True)
    render_month_pnl()

with col_s3:
    @st.fragment(run_every=10)
    def render_unrealized_pnl():
        pos, bal = fetch_fast_data(exchange_choice, MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)
        unrealized = sum([p.get("unrealized_pnl", 0.0) for p in pos]) if pos else 0.0
        st.markdown(make_top_card("현재 미실현손익", unrealized, "전체 포지션의 미실현손익 합계", "10초마다 갱신"), unsafe_allow_html=True)
    render_unrealized_pnl()

st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 8. 수익 히스토리 필터
# -----------------------------------------------------------------------------
st.markdown("<div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:10px;'><span style='font-size:20px; font-weight:800; color:#111827;'>수익 히스토리</span></div>", unsafe_allow_html=True)

if not df_trades.empty and "date" in df_trades.columns:
    df_trades["date_obj"] = pd.to_datetime(df_trades["date"]).dt.date
    oldest_date = df_trades["date_obj"].min()
else:
    df_trades["date_obj"] = pd.Series(dtype=object)
    oldest_date = datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").date()

c_d1, c_d2, c_btn1, c_btn2, c_btn3, c_space, c_drop = st.columns([1.5, 1.5, 0.8, 0.9, 1.1, 4, 1.5])
with c_d1: start_date = st.date_input("s", value=oldest_date, label_visibility="collapsed")
with c_d2: end_date = st.date_input("e", value=datetime.now(UTC).date(), label_visibility="collapsed")
with c_btn1: btn_today = st.button("오늘", use_container_width=True)
with c_btn2: btn_month = st.button("이번 달", use_container_width=True)
with c_btn3: btn_30d = st.button("최근 30일", use_container_width=True)
with c_drop: agg_mode = st.selectbox("집계", ["일별 집계", "주별 집계", "월별 집계"], label_visibility="collapsed")

if btn_today: start_date, end_date = datetime.now(UTC).date(), datetime.now(UTC).date()
elif btn_month: start_date, end_date = datetime.now(UTC).date().replace(day=1), datetime.now(UTC).date()
elif btn_30d: start_date, end_date = datetime.now(UTC).date() - timedelta(days=30), datetime.now(UTC).date()

filter_start_date = max(start_date, datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").date())
filtered_df = df_trades[(df_trades["date_obj"] >= filter_start_date) & (df_trades["date_obj"] <= end_date)] if not df_trades.empty else df_trades

# -----------------------------------------------------------------------------
# 9. [FRAGMENT] 매매 동향 — 총 주문 횟수(증가/축소) · LONG-SHORT(청산 기준) · 승률 추이
# -----------------------------------------------------------------------------
st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
st.markdown("<div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:10px;'><span style='font-size:16px; font-weight:800; color:#111827; margin-left:5px;'>매매 동향</span><span style='font-size:12px; color:#9ca3af;'>관측 기록 기준</span></div>", unsafe_allow_html=True)

@st.fragment(run_every=3600)
def render_trade_stats(f_df):
    # 최근 7일 승률 추이는 상단 기간 필터와 무관하게 항상 '지금'을 기준으로 고정 (캐시라 추가 API 호출 없음)
    all_df = fetch_slow_data(exchange_choice, MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)

    col_t1, col_t2, col_t3 = st.columns([1, 1, 1.2])

    total = len(f_df)
    incr = int((f_df["bucket"] == "증가").sum()) if total else 0
    closes = f_df[f_df["bucket"] == "축소"] if total else f_df
    decr = len(closes)
    wins = int((closes["result"] == "익절").sum())
    losses = int((closes["result"] == "손절").sum())
    rate = (wins / (wins + losses) * 100) if (wins + losses) else 0

    lg = int((closes["side"] == "LONG").sum())
    sh = int((closes["side"] == "SHORT").sum())
    lp = (lg / (lg + sh) * 100) if (lg + sh) else 0
    sp = 100 - lp if (lg + sh) else 0

    card_style = "background-color:#ffffff; border:1px solid #e5e7eb; border-radius:12px; padding:20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); height: 320px; display:flex; flex-direction:column; justify-content:space-between;"

    with col_t1:
        incr_p = (incr / total * 100) if total else 0
        decr_p = 100 - incr_p if total else 0
        st.markdown(f"""<div style="{card_style}">
            <div>
                <div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>총 주문 횟수</span><span style='color:#9ca3af; font-weight:400;'>선택 기간</span></div>
                <div style='font-size:36px; font-weight:800; color:#111827; margin:15px 0 10px;'>{total} <span style='font-size:14px; font-weight:500;'>회</span></div>
                <div style="display:flex; width:100%; height:8px; border-radius:4px; overflow:hidden; background-color:#eef0f4;">
                    <div style="width:{incr_p}%; background-color:{BLUE};"></div>
                    <div style="width:{decr_p}%; background-color:#c7ccd6;"></div>
                </div>
                <div style='display:flex; justify-content:space-between; font-size:12px; color:#6b7280; margin:8px 0 16px;'>
                    <span><span style='display:inline-block;width:7px;height:7px;border-radius:50%;background:{BLUE};margin-right:5px;'></span>증가 <b style='color:#111827;'>{incr}건</b></span>
                    <span><span style='display:inline-block;width:7px;height:7px;border-radius:50%;background:#c7ccd6;margin-right:5px;'></span>축소 <b style='color:#111827;'>{decr}건</b></span>
                </div>
            </div>
            <div style='border-top:1px solid #f3f4f6; padding-top:14px;'>
                <div style='display:flex; justify-content:space-between; font-size:13px; color:#6b7280; margin-bottom:10px;'>
                    <span>익절 <b style='color:{GREEN};'>{wins}건</b></span><span>손절 <b style='color:{RED};'>{losses}건</b></span>
                </div>
                <div style='display:flex; justify-content:space-between; font-size:13px; color:#6b7280;'><span>기간 승률</span><b style='color:{BLUE}; font-size:16px;'>{rate:.1f}%</b></div>
            </div>
        </div>""", unsafe_allow_html=True)

    with col_t2:
        bg_gradient = f"conic-gradient({GREEN} 0% {lp}%, {RED} {lp}% 100%)" if (lg + sh) > 0 else "conic-gradient(#e5e7eb 0% 100%)"
        st.markdown(f"""
        <div style="{card_style}">
            <div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>LONG / SHORT</span><span style='color:#9ca3af; font-weight:400;'>청산 횟수 비율</span></div>
            <div style="display:flex; justify-content:center; align-items:center; flex-grow:1;">
                <div style="width: 125px; height: 125px; border-radius: 50%; background: {bg_gradient}; display:flex; justify-content:center; align-items:center;">
                    <div style="width: 90px; height: 90px; background-color: #ffffff; border-radius: 50%; display:flex; flex-direction:column; justify-content:center; align-items:center; box-shadow: inset 0 0 5px rgba(0,0,0,0.02);">
                        <span style="font-size:12px; color:#6b7280; font-weight:500;">총 청산</span>
                        <b style="font-size:24px; color:#111827; margin-top:-2px;">{decr}건</b>
                    </div>
                </div>
            </div>
            <div>
                <div style='display:flex; justify-content:space-between; font-size:13px; margin-bottom:8px;'><span style='color:{GREEN}; font-weight:700;'>LONG</span><b style='color:{GREEN};'>{lg}건 · {lp:.1f}%</b></div>
                <div style='display:flex; justify-content:space-between; font-size:13px;'><span style='color:{RED}; font-weight:700;'>SHORT</span><b style='color:{RED};'>{sh}건 · {sp:.1f}%</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_t3:
        now_utc = datetime.now(UTC)
        day_labels, vals = [], []
        tot_w7, tot_l7 = 0, 0
        for i in range(6, -1, -1):
            d = now_utc - timedelta(days=i)
            ds = d.strftime("%Y-%m-%d")
            day_labels.append(d.strftime("%m/%d"))
            day_closes = all_df[(all_df["date"] == ds) & (all_df["bucket"] == "축소")] if not all_df.empty else pd.DataFrame()
            w, l = int((day_closes["result"] == "익절").sum()), int((day_closes["result"] == "손절").sum())
            tot_w7 += w; tot_l7 += l
            vals.append(w / (w + l) * 100 if (w + l) else None)
        r_rate = round(tot_w7 / (tot_w7 + tot_l7) * 100) if (tot_w7 + tot_l7) else 0

        step_x = 280 / 6
        runs, cur = [], []
        for i, v in enumerate(vals):
            if v is None:
                if cur: runs.append(cur); cur = []
            else:
                cur.append((i * step_x, 110 - (v / 100) * 85, v))
        if cur: runs.append(cur)

        lines = "".join(
            f"<polyline points='{' '.join(f'{x:.1f},{y:.1f}' for x, y, _ in run)}' fill='none' stroke='{BLUE}' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'/>"
            for run in runs if len(run) > 1
        )
        dots = "".join(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='4' fill='{BLUE}'/><text x='{x:.1f}' y='{y-12:.1f}' font-size='12' font-weight='bold' fill='{BLUE}' text-anchor='middle'>{v:.0f}%</text>"
            for run in runs for x, y, v in run
        )
        empty_x = {i * step_x for i, v in enumerate(vals) if v is None}
        dashes = "".join(f"<text x='{x:.1f}' y='60' font-size='13' fill='#d1d5db' text-anchor='middle'>―</text>" for x in empty_x)
        days = "".join(f"<text x='{i * step_x:.1f}' y='130' font-size='10' fill='#9ca3af' text-anchor='middle'>{day_labels[i]}</text>" for i in range(7))
        svg_html = f"<svg viewBox='-15 -15 310 150' style='width:100%; height:130px; display:block;'>{lines}{dots}{dashes}{days}</svg>"

        st.markdown(f"""<div style="{card_style}">
            <div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>승률 추이</span><span style='color:#9ca3af; font-weight:400;'>최근 7일 · 오늘 포함</span></div>
            <div style="display:flex; align-items:baseline; gap:10px; margin-top:10px;"><span style="font-size:32px; font-weight:800; color:{BLUE};">{r_rate}%</span><span style="font-size:12px; color:#6b7280;">익절 {tot_w7} · 손절 {tot_l7}</span></div>
            <div style="flex-grow:1; display:flex; flex-direction:column; justify-content:flex-end;">{svg_html}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown(
        "<div class='note-text'>총 주문 횟수는 포지션 증가(신규·추가 진입)와 축소(부분·전체 청산) 이벤트의 합계이며, "
        "분할 체결은 같은 주문으로 묶어서 1건으로 셉니다. 거래소가 표시하는 주문 건수와 다를 수 있습니다. "
        "익절·손절·본전·미확인은 모두 축소 이벤트에 포함되고, 승률은 익절 ÷ (익절 + 손절)로 계산해 본전·미확인은 제외합니다. "
        "LONG/SHORT 비율은 축소(청산) 이벤트 기준입니다. 익절·손절이 없는 날은 그래프에 ―로 표시합니다.</div>",
        unsafe_allow_html=True,
    )

render_trade_stats(filtered_df)

# -----------------------------------------------------------------------------
# 10. [FRAGMENT] 선택 기간 PNL 박스
# -----------------------------------------------------------------------------
st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

@st.fragment(run_every=3600)
def render_pnl_charts(f_df):
    period_sum = f_df["pnl"].sum() if not f_df.empty else 0.0
    pnl_color, pnl_sign = (GREEN, "+") if period_sum >= 0 else (RED, "")

    if not f_df.empty:
        daily_pnl = f_df.groupby("date")["pnl"].sum().reset_index()
        daily_pnl["date_obj"] = pd.to_datetime(daily_pnl["date"]).dt.date
        full_dates = pd.date_range(start=filter_start_date, end=end_date).date
        daily_pnl = pd.merge(pd.DataFrame({"date_obj": full_dates}), daily_pnl, on="date_obj", how="left").fillna({"pnl": 0})
        daily_pnl["date_str"] = pd.to_datetime(daily_pnl["date_obj"]).dt.strftime("%Y-%m-%d")
        daily_pnl["cum"] = daily_pnl["pnl"].cumsum()
        daily_pnl["color"] = daily_pnl["pnl"].apply(lambda x: GREEN if x >= 0 else RED)
        last_date, last_val = daily_pnl["date_str"].iloc[-1], daily_pnl["pnl"].iloc[-1]
    else:
        daily_pnl = pd.DataFrame()
        last_date, last_val = end_date.strftime("%Y-%m-%d"), 0.0

    last_sign = "+" if last_val >= 0 else ""

    with st.container(border=True):
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; align-items:baseline;'>
            <span style='font-size:12px; color:#9ca3af; font-weight:600;'>선택 기간 추정 PNL</span>
            <span style='font-size:12px; color:#9ca3af;'>{last_date} <b style='color:{GREEN if last_val >= 0 else RED};'>{last_sign}${last_val:,.2f}</b></span>
        </div>
        <div style='font-size:32px; font-weight:800; color:{pnl_color}; margin-top:5px;'>
            {pnl_sign}${period_sum:,.2f} <span style='font-size:14px; color:#00a86b; font-weight:600;'>USDT</span>
        </div>
        <div style="border-bottom: 1px solid #e5e7eb; margin: 15px 0 5px 0;"></div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["일별 손익", "기간 누적"])

        tickvals = []
        if not daily_pnl.empty:
            n = len(daily_pnl)
            idxs = sorted({0, n // 2, n - 1})
            tickvals = [daily_pnl["date_str"].iloc[i] for i in idxs]

        def style(fig):
            fig.update_layout(
                template="plotly_white", margin=dict(t=20, b=10, l=10, r=10), height=350,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
                xaxis=dict(showgrid=False, zeroline=False, type='category', tickmode='array', tickvals=tickvals),
                yaxis=dict(showgrid=True, gridcolor="#f3f4f6", griddash="dash", zeroline=True, zerolinecolor="#d1d5db", zerolinewidth=1.5, nticks=5),
            )
            return fig

        with tab1:
            if not daily_pnl.empty:
                fig1 = go.Figure(go.Bar(
                    x=daily_pnl["date_str"], y=daily_pnl["pnl"], marker_color=daily_pnl["color"],
                    name="일별 수익", hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"
                ))
                st.plotly_chart(style(fig1), use_container_width=True, config={"displayModeBar": False})
            else:
                st.caption("선택한 기간에 거래가 없습니다.")

        with tab2:
            if not daily_pnl.empty:
                fig2 = go.Figure(go.Scatter(
                    x=daily_pnl["date_str"], y=daily_pnl["cum"], mode="lines+markers",
                    line=dict(color=BLUE, width=3), fill="tozeroy", fillcolor="rgba(37, 99, 235, 0.08)",
                    name="누적 수익", hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"
                ))
                st.plotly_chart(style(fig2), use_container_width=True, config={"displayModeBar": False})

render_pnl_charts(filtered_df)

st.markdown("<div style='font-size:11px; color:#9ca3af; margin: 10px 0 30px 0;'>추정 PNL · USDT · UTC 기준 (한국시간 오전 9시 날짜 전환) · 기간 누적은 선택한 기간의 시작을 0으로 계산합니다.</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 11. 매매 상세 내역 로그
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 18px; font-weight: 800; color: #111827; margin-bottom: 15px;'>📝 상세 매매 내역</div>", unsafe_allow_html=True)

@st.fragment(run_every=3600)
def render_trade_logs(f_df):
    if not f_df.empty:
        st.dataframe(
            f_df[["datetime", "symbol", "side", "bucket", "pnl", "result"]],
            use_container_width=True, hide_index=True, height=400,
            column_config={
                "datetime": st.column_config.DatetimeColumn("시간 (KST)", format="YYYY-MM-DD HH:mm"),
                "symbol": "종목", "side": "방향", "bucket": "구분",
                "pnl": st.column_config.NumberColumn("PNL (USDT)", format="%.2f"),
                "result": "결과",
            },
        )
    else:
        st.info("새로운 출발을 응원합니다! (아직 등록된 거래 내역이 없습니다)")

render_trade_logs(filtered_df)
