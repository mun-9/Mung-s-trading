import ccxt
import time
import random
from datetime import datetime, timedelta, timezone
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import calendar  # 캘린더 생성을 위한 모듈 추가

# =============================================================================
# 🔑 웹사이트 비밀 금고에서 API 키를 가져옵니다
# =============================================================================
try:
    MY_API_KEY = st.secrets["API_KEY"]
    MY_SECRET_KEY = st.secrets["SECRET_KEY"]
    MY_PASSPHRASE = st.secrets["PASSPHRASE"]
except Exception:
    MY_API_KEY = ""
    MY_SECRET_KEY = ""
    MY_PASSPHRASE = ""

# 🎯 [초기화 설정] 대시보드 기준 날짜
DASHBOARD_START_DATE = "2026-09-28"

# 🇰🇷 시간대 설정 (모든 기준을 한국 시간으로 통일)
KST = timezone(timedelta(hours=9))
UTC = timezone.utc

# 🎨 색상 상수 — 토스 팔레트 + 트레이딩 그린/레드
GREEN, RED, BLUE, GRAY = "#089981", "#F04452", "#3182F6", "#8B95A1"
TEXT, SUB, DIVIDER = "#191F28", "#8B95A1", "#F2F4F6"
LINE_COLOR = "#D1D6DB"
GREEN_SOFT, RED_SOFT, BLUE_SOFT = "rgba(8,153,129,0.10)", "rgba(240,68,82,0.10)", "rgba(49,130,246,0.10)"

# -----------------------------------------------------------------------------
# 1. 페이지 설정 & 토스 스타일 디자인 시스템
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Trading Journal",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

html, body, .stApp { background-color: #F2F4F6 !important; }
.stApp, .stApp p, .stApp span, .stApp div, .stApp label { font-family:'Pretendard',-apple-system,BlinkMacSystemFont,sans-serif; letter-spacing:-0.01em; }

.block-container { padding-top: 2rem; max-width: 1240px; }
[data-testid="stHeader"] { background-color: transparent !important; }
[data-testid="stToolbar"] { display: none !important; }

/* 🌟 "보유 포지션" 제목 + 새로고침 버튼 — 컬럼 대신 절대위치로 고정해서
   화면 폭(PC/모바일)과 상관없이 항상 컨테이너의 진짜 오른쪽 끝에 붙게 함 */
div[class*="st-key-pos_header_row"] {
    position: relative !important;
    min-height: 36px;
    margin-bottom: 12px;
}
div[class*="st-key-pos_header_row"] div[class*="st-key-manual_refresh_main"] {
    position: absolute !important;
    top: 0 !important;
    right: 0 !important;
    width: auto !important;
}

/* 새로고침 버튼 디자인 */
div[class*="st-key-manual_refresh_main"] button {
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    min-height: 36px !important;
    padding: 0 !important;
    margin: 0 !important;
    border-radius: 12px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background-color: #ffffff !important;
    border: 1px solid rgba(15,23,42,0.08) !important;
    box-shadow: 0 2px 8px rgba(15,23,42,0.03) !important;
    transition: all 0.15s ease !important;
}
div[class*="st-key-manual_refresh_main"] button:hover { border-color: #3182F6 !important; background-color: #F8FAFC !important; }

/* 🌟 로딩 스피너 디자인 */
[data-testid="stSpinner"] {
    background: #ffffff; padding: 18px 26px; border-radius: 18px;
    box-shadow: 0 8px 28px rgba(15,23,42,0.08); border: 1px solid rgba(15,23,42,0.04);
    margin: 24px auto; display: flex; align-items: center; justify-content: center; max-width: 420px;
}
[data-testid="stSpinner"] svg { width: 22px; height: 22px; color: #3182F6 !important; }
[data-testid="stSpinner"] > div > div:last-child {
    color: #191F28 !important; font-weight: 700 !important; font-size: 14px !important; margin-left: 12px !important;
}

.card { background:#ffffff; border-radius:20px; box-shadow:0 2px 14px rgba(15,23,42,0.05); padding:22px 24px; }

div[class*="st-key-pnl_card"] {
    background-color: #ffffff !important; border: none !important; border-radius: 20px !important;
    box-shadow: 0 2px 14px rgba(15,23,42,0.05) !important; padding: 22px 24px !important;
}
div[class*="st-key-pos_container_"] {
    background-color: #ffffff !important; border: none !important; border-radius: 20px !important;
    box-shadow: 0 2px 14px rgba(15,23,42,0.05) !important; padding: 22px 24px 14px !important; margin-bottom: 18px !important;
}

/* 🌟 분봉 라디오 버튼 */
div[class*="st-key-tf_radio_"] { margin-bottom: 12px; overflow: visible !important; }
div[class*="st-key-tf_radio_"] div[role="radiogroup"] { display: flex !important; flex-wrap: wrap !important; gap: 8px !important; }
div[class*="st-key-tf_radio_"] label[data-baseweb="radio"] {
    background-color: #F2F4F6 !important; color: #6b7280 !important; padding: 8px 16px !important;
    border-radius: 999px; margin: 0 !important; cursor: pointer; transition: background .15s; height: auto !important;
}
div[class*="st-key-tf_radio_"] label[data-baseweb="radio"] p {
    color: #6b7280 !important; font-size: 13.5px !important; margin: 0 !important; font-weight: 600 !important;
    line-height: 1.4 !important; white-space: nowrap !important; opacity: 1 !important;
}
div[class*="st-key-tf_radio_"] label[data-baseweb="radio"] div:first-child { display: none; }
div[class*="st-key-tf_radio_"] label[data-baseweb="radio"][aria-checked="true"] { background-color: #3182F6 !important; color: #ffffff !important; }
div[class*="st-key-tf_radio_"] label[data-baseweb="radio"][aria-checked="true"] p { color: #ffffff !important; font-weight: 700 !important; }

button[data-baseweb="tab"] p { color: #8B95A1 !important; font-weight: 600 !important; font-size: 14.5px !important; }
button[data-baseweb="tab"][aria-selected="true"] p { color: #3182F6 !important; font-weight: 800 !important; }
div[data-baseweb="tab-highlight"] { background-color: #3182F6 !important; }

.pos-box { padding: 4px 14px; flex: 1 1 190px; }
.pos-divider { border-left: 1px solid rgba(15,23,42,0.06); }

.stButton>button { height: 38px; padding: 0 16px; border-radius: 999px; border: 1px solid rgba(15,23,42,0.08); background-color: #ffffff; color: #191F28; font-weight: 600; white-space: nowrap; box-shadow:none; }
.stButton>button:hover { border-color: #3182F6; color: #3182F6; }

.pill { display:inline-block; font-size:11px; font-weight:800; padding:3px 9px; border-radius:999px; vertical-align:middle; }
.note-text { font-size:11.5px; line-height:1.7; color:#B0B8C1; margin:16px 2px 0; }

.log-row { display:flex; justify-content:space-between; align-items:center; padding:15px 6px; border-bottom:1px solid #F2F4F6; }
.log-row:last-child { border-bottom:none; }
.log-left { display:flex; align-items:center; gap:13px; }
.sym-badge { width:38px; height:38px; min-width:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:13px; }
.row-title { font-size:14.5px; font-weight:700; color:#191F28; }
.row-sub { font-size:12px; color:#8B95A1; margin-top:3px; }
.row-right { text-align:right; }
.row-price { font-size:12px; color:#8B95A1; margin-bottom:4px; }
.row-pnl { font-size:14.5px; font-weight:800; }
.chip { display:inline-block; font-size:10.5px; font-weight:700; padding:2px 8px; border-radius:999px; margin-left:4px; }

/* 📱 모바일 환경(768px 이하) 대응 CSS */
@media (max-width: 768px) {
    .pos-divider { border-left: none !important; border-top: 1px solid rgba(15,23,42,0.06) !important; padding-top: 14px !important; margin-top: 6px !important; }
    .hide-on-mobile { display: none !important; }
    .hdr-title-text { font-size: 19px !important; }
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 체결 분류 유틸
# -----------------------------------------------------------------------------
def classify_fill(t):
    info = t.get("info", {}) or {}
    ts = str(info.get("tradeSide", "")).lower()
    ro = info.get("reduceOnly", t.get("reduceOnly"))
    raw = info.get("profit", info.get("realizedPnl"))
    has_pnl = raw not in (None, "")
    pnl = float(raw or 0)
    price = float(t.get("price") or t.get("average") or 0.0)

    if "open" in ts: is_close = False
    elif "close" in ts: is_close = True
    elif ro is True: is_close = True
    elif ro is False: is_close = False
    else: is_close = has_pnl and pnl != 0

    if "long" in ts: side = "LONG"
    elif "short" in ts: side = "SHORT"
    else: side = "LONG" if t["side"].upper() == "BUY" else "SHORT"

    return side, is_close, has_pnl, pnl, price

def result_of(bucket, has_pnl, pnl):
    if bucket == "증가": return "진입"
    if not has_pnl: return "미확인"
    if pnl > 0: return "익절"
    if pnl < 0: return "손절"
    return "본전"

TRADE_COLS = ["order_id", "datetime", "date", "symbol", "side", "bucket", "has_pnl", "pnl", "price", "result"]

def finalize(rows):
    if not rows: return pd.DataFrame(columns=TRADE_COLS)
    df = pd.DataFrame(rows)

    if "trade_id" in df.columns:
        df = df.drop_duplicates(subset=["trade_id"])

    g = df.groupby(["order_id", "symbol", "side", "date"], as_index=False).agg(
        pnl=("pnl", "sum"), price=("price", "mean"), datetime=("datetime", "last"),
        bucket=("bucket", lambda s: s.mode().iat[0]), has_pnl=("has_pnl", "max")
    )
    g["result"] = g.apply(lambda r: result_of(r.bucket, r.has_pnl, r.pnl), axis=1)
    return g.sort_values("datetime", ascending=False)

# -----------------------------------------------------------------------------
# 3. 실시간 유틸 (환율 및 OHLCV)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def fetch_usdt_krw():
    try: return float(ccxt.upbit({'enableRateLimit': True}).fetch_ticker('USDT/KRW').get('last', 1350.0))
    except Exception: return 1350.0

@st.cache_data(ttl=30, show_spinner=False)
def fetch_live_ohlcv(symbol, timeframe, limit=120):
    try:
        ex = ccxt.bitget({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
        fetch_sym = symbol + ":USDT"
        try:
            bars = ex.fetch_ohlcv(fetch_sym, timeframe, limit=limit)
        except Exception:
            try:
                bars = ex.fetch_ohlcv(fetch_sym, '5m', limit=limit)
            except Exception:
                return pd.DataFrame()

        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
        return df
    except Exception:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# 4. API 데이터 로드
# -----------------------------------------------------------------------------
@st.cache_data(ttl=10, show_spinner=False)
def fetch_fast_data(api_key, secret, pwd):
    if not api_key or not secret:
        return [
            {"symbol": "BTC/USDT", "side": "LONG", "leverage": 20, "entry_price": 63200.0, "mark_price": 64800.0, "size": 0.3, "margin": 948.0, "liq_price": 60100.0, "unrealized_pnl": 480.0, "roe": 50.6},
            {"symbol": "BTC/USDT", "side": "SHORT", "leverage": 20, "entry_price": 65100.0, "mark_price": 64800.0, "size": 0.5, "margin": 1581.25, "liq_price": 68200.0, "unrealized_pnl": 150.0, "roe": 9.4}
        ], 10000.0
    try:
        exchange = ccxt.bitget({'apiKey': api_key, 'secret': secret, 'password': pwd, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
        bal = exchange.fetch_balance({'type': 'swap'})
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
                    "entry_price": entry, "mark_price": mark, "size": size, "margin": margin, "liq_price": float(p.get("liquidationPrice") or 0), "unrealized_pnl": unreal_pnl, "roe": roe
                })
        return active_positions, total_balance
    except Exception:
        return [], 0.0

BASE_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT",
    "BNB/USDT", "ADA/USDT", "SUI/USDT", "1000PEPE/USDT", "WIF/USDT"
]

@st.cache_data(ttl=3600, show_spinner="거래 내역을 불러오고 있어요...")
def fetch_slow_data(api_key, secret, pwd):
    if not api_key or not secret:
        rnd = random.Random(42)
        now = datetime.now(UTC)
        rows = []
        for i in range(300):
            t = now - timedelta(hours=rnd.randint(1, 900))
            t_kst = t.astimezone(KST)
            is_close = rnd.random() < 0.55
            pnl = rnd.choice([rnd.uniform(50, 900), rnd.uniform(50, 900), rnd.uniform(-700, -40), 0.0]) if is_close else 0.0
            sym = rnd.choice(["BTC/USDT", "ETH/USDT"])
            trade_id = f"DEMO_TRADE_{i}"
            rows.append({
                "trade_id": trade_id, "order_id": f"DEMO_ORDER_{i}", "datetime": t_kst.replace(tzinfo=None),
                "date": t_kst.strftime("%Y-%m-%d"), "symbol": sym, "side": rnd.choice(["LONG", "SHORT"]),
                "bucket": "축소" if is_close else "증가", "has_pnl": True, "pnl": round(pnl, 2),
                "price": round(rnd.uniform(62000, 65000) if "BTC" in sym else rnd.uniform(2000, 3000), 2)
            })
        df = finalize(rows)
        return df[df["date"] >= DASHBOARD_START_DATE]

    try:
        exchange = ccxt.bitget({'apiKey': api_key, 'secret': secret, 'password': pwd, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
        pop_syms = [f"{s}:USDT" for s in BASE_SYMBOLS]

        exchange.load_markets()

        start_dt = datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").replace(tzinfo=KST)
        since_ts = int(start_dt.timestamp() * 1000)
        now_ts = int(datetime.now(UTC).timestamp() * 1000)
        chunk_ms = 2 * 24 * 60 * 60 * 1000

        try:
            open_pos, _ = fetch_fast_data(api_key, secret, pwd)
            extra_syms = [f"{p['symbol']}:USDT" for p in open_pos]
        except Exception:
            extra_syms = []

        symbols = list(dict.fromkeys(pop_syms + extra_syms))
        rows, errs = [], []

        for sym in symbols:
            if sym not in exchange.markets: continue

            current_since = since_ts
            while current_since < now_ts:
                chunk_until = min(current_since + chunk_ms, now_ts)
                try:
                    params = {'endTime': chunk_until, 'until': chunk_until}
                    trades = exchange.fetch_my_trades(symbol=sym, since=current_since, limit=1000, params=params)

                    for t in trades:
                        t_utc = datetime.fromtimestamp(t["timestamp"] / 1000, tz=UTC)
                        t_kst = t_utc.astimezone(KST)
                        side, is_close, has_pnl, pnl, price = classify_fill(t)

                        trade_id = str(t.get("id") or f"{t.get('order')}_{t['timestamp']}")
                        order_id = str(t.get("order") or t["timestamp"])

                        rows.append({
                            "trade_id": trade_id, "order_id": order_id, "datetime": t_kst.replace(tzinfo=None),
                            "date": t_kst.strftime("%Y-%m-%d"), "symbol": t["symbol"].replace(":USDT", ""),
                            "side": side, "bucket": "축소" if is_close else "증가", "has_pnl": has_pnl,
                            "pnl": pnl, "price": price
                        })
                except Exception:
                    try:
                        trades = exchange.fetch_my_trades(symbol=sym, since=current_since, limit=1000)
                        for t in trades:
                            t_utc = datetime.fromtimestamp(t["timestamp"] / 1000, tz=UTC)
                            t_kst = t_utc.astimezone(KST)
                            side, is_close, has_pnl, pnl, price = classify_fill(t)
                            trade_id = str(t.get("id") or f"{t.get('order')}_{t['timestamp']}")
                            order_id = str(t.get("order") or t["timestamp"])
                            rows.append({
                                "trade_id": trade_id, "order_id": order_id, "datetime": t_kst.replace(tzinfo=None),
                                "date": t_kst.strftime("%Y-%m-%d"), "symbol": t["symbol"].replace(":USDT", ""),
                                "side": side, "bucket": "축소" if is_close else "증가", "has_pnl": has_pnl,
                                "pnl": pnl, "price": price
                            })
                    except Exception as e2:
                        errs.append(f"{sym}: {e2}")

                current_since = chunk_until

        try:
            payback_start_ts = int(datetime(2026, 10, 1, tzinfo=KST).timestamp() * 1000)
            deposits = exchange.fetch_deposits(since=payback_start_ts)
            for d in deposits:
                status = str(d.get("status", "")).lower()
                if status in ("ok", "success", "completed", "1"):
                    curr = str(d.get("currency", "")).upper()
                    if curr == "USDT":
                        d_utc = datetime.fromtimestamp(d["timestamp"] / 1000, tz=UTC)
                        d_kst = d_utc.astimezone(KST)
                        amount = float(d.get("amount", 0) or 0)
                        if amount > 0:
                            dep_id = f"DEPOSIT_{d.get('id', d['timestamp'])}"
                            rows.append({
                                "trade_id": dep_id, "order_id": dep_id, "datetime": d_kst.replace(tzinfo=None),
                                "date": d_kst.strftime("%Y-%m-%d"), "symbol": "FEE/PAYBACK", "side": "LONG",
                                "bucket": "축소", "has_pnl": True, "pnl": amount, "price": 0.0
                            })
        except Exception:
            pass

        if errs:
            st.session_state["_slow_fetch_errors"] = errs
        else:
            st.session_state.pop("_slow_fetch_errors", None)

        df = finalize(rows)
        return df[df["date"] >= DASHBOARD_START_DATE] if not df.empty else df
    except Exception as e:
        st.session_state["_slow_fetch_errors"] = [f"전체 조회 실패: {e}"]
        return pd.DataFrame(columns=TRADE_COLS)

# -----------------------------------------------------------------------------
# 5. 메인 헤더 & 우측 상단 Bitget 실시간 연동 배지
# -----------------------------------------------------------------------------
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; flex-wrap:nowrap;">
    <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:22px;">📈</span>
        <span class="hdr-title-text" style="font-size:21px; font-weight:800; color:{TEXT}; letter-spacing:-0.02em; white-space:nowrap;">Trading Journal</span>
    </div>
    <div style="background:#ffffff; padding:6px 12px; border-radius:999px; box-shadow:0 2px 10px rgba(15,23,42,0.04); display:flex; align-items:center; gap:6px; white-space:nowrap; flex-shrink:0;">
        <span style="width:7px; height:7px; background:{GREEN}; border-radius:50%; display:inline-block; flex-shrink:0;"></span>
        <span style="font-size:12.5px; font-weight:700; color:{TEXT};">Bitget</span>
        <span class="hide-on-mobile" style="font-size:11.5px; color:{SUB}; font-weight:500;">실시간 연동</span>
    </div>
</div>
""", unsafe_allow_html=True)

df_trades = fetch_slow_data(MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)

st.markdown(f"<div style='border-top:1px solid {LINE_COLOR}; margin: 6px 0 20px 0;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. [FRAGMENT] 🎯 현재 보유 포지션 & 실시간 차트
# -----------------------------------------------------------------------------
with st.container(key="pos_header_row"):
    st.markdown(f"<div style='font-size: 19px; font-weight: 800; color: {TEXT}; line-height: 36px;'> 보유 포지션</div>", unsafe_allow_html=True)
    if st.button("🔄", key="manual_refresh_main"):
        fetch_fast_data.clear(); fetch_slow_data.clear(); fetch_usdt_krw.clear(); fetch_live_ohlcv.clear(); st.rerun()

@st.fragment(run_every=10)
def show_live_positions():
    current_positions, wallet_balance = fetch_fast_data(MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)

    if not current_positions:
        st.markdown(f"<div class='card' style='text-align: center; color: {SUB}; font-size: 14px; padding:32px;'>현재 진행 중인 포지션이 없습니다</div>", unsafe_allow_html=True)
    else:
        symbol_groups = {}
        for pos in current_positions:
            symbol_groups.setdefault(pos['symbol'], []).append(pos)

        for sym, pos_list in symbol_groups.items():
            safe_sym = sym.replace("/", "_")

            with st.container(key=f"pos_container_{safe_sym}"):
                for idx, pos in enumerate(pos_list):
                    pos_side = pos["side"]
                    side_color = GREEN if pos_side == "LONG" else RED
                    side_soft = GREEN_SOFT if pos_side == "LONG" else RED_SOFT
                    pnl_val, roe_val = pos["unrealized_pnl"], pos["roe"]
                    pnl_color, pnl_sign = (GREEN, "+") if pnl_val >= 0 else (RED, "")
                    base_coin = pos['symbol'].split('/')[0] if '/' in pos['symbol'] else pos['symbol']
                    pos_usdt_value = pos['size'] * pos['entry_price']
                    margin_ratio = (pos['margin'] / wallet_balance * 100) if wallet_balance > 0 else 0

                    pos_html = f"""<div style="display: flex; flex-wrap: wrap; margin-bottom: 5px;"><div class="pos-box" style="padding-left:0;"><div style='font-size: 12.5px; color: {SUB}; font-weight: 600; margin-bottom: 9px;'>종목 · 방향</div><div style='font-size: 22px; font-weight: 800; color: {TEXT};'>{pos['symbol']} <span class='pill' style='background:{side_soft}; color:{side_color}; font-size:12px; padding:4px 10px;'>{pos_side} {pos['leverage']}x</span></div><div style='font-size: 13px; color: {SUB}; font-weight: 500; margin-top: 8px;'>{pos['size']} {base_coin} ≈ ${pos_usdt_value:,.2f}</div></div><div class="pos-box pos-divider"><div style='font-size: 12.5px; color: {SUB}; font-weight: 600; margin-bottom: 12px;'>진입가 · 현재가</div><div style='display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px;'><span style='width: 42px; font-size: 11.5px; color: {SUB};'>진입가</span><span style='font-size: 17px; font-weight: 700; color: {TEXT};'>${pos['entry_price']:,.2f}</span></div><div style='display: flex; align-items: baseline; gap: 8px;'><span style='width: 42px; font-size: 11.5px; color: {SUB};'>현재가</span><span style='font-size: 17px; font-weight: 700; color: {BLUE};'>${pos['mark_price']:,.2f}</span></div></div><div class="pos-box pos-divider"><div style='font-size: 12.5px; color: {SUB}; font-weight: 600; margin-bottom: 12px;'>미실현 손익 · ROI</div><div style='font-size: 24px; font-weight: 800; color: {pnl_color}; margin-bottom: -4px;'>{pnl_sign}${pnl_val:,.2f}</div><div style='font-size: 14px; font-weight: 700; color: {pnl_color};'>({pnl_sign}{roe_val:.2f}%)</div></div><div class="pos-box pos-divider" style="padding-right:0;"><div style='font-size: 12.5px; color: {SUB}; font-weight: 600; margin-bottom: 12px;'>증거금 <span style="color:{BLUE};">(비중%)</span> · 청산가</div><div style='display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px;'><span style='width: 42px; font-size: 11.5px; color: {SUB};'>증거금</span><span style='font-size: 17px; font-weight: 700; color: {TEXT};'>${pos['margin']:,.2f} <span style='font-size:13px; color:{BLUE};'>({margin_ratio:.1f}%)</span></span></div><div style='display: flex; align-items: baseline; gap: 8px;'><span style='width: 42px; font-size: 11.5px; color: {SUB};'>청산가</span><span style='font-size: 17px; font-weight: 700; color: #4b5563;'>${pos['liq_price']:,.2f}</span></div></div></div>"""
                    st.markdown(pos_html, unsafe_allow_html=True)

                    if idx < len(pos_list) - 1:
                        st.markdown(f"<div style='border-top:1px solid {DIVIDER}; margin: 10px 0 15px 0;'></div>", unsafe_allow_html=True)

                st.markdown(f"<div style='border-top:1px solid {DIVIDER}; margin: 16px 0 15px 0;'></div>", unsafe_allow_html=True)

                tf_selected = st.radio("분봉 선택", ["3분봉", "5분봉", "1시간봉"], horizontal=True, label_visibility="collapsed", key=f"tf_radio_{safe_sym}")
                tf_map = {"3분봉": "3m", "5분봉": "5m", "1시간봉": "1h"}

                df_ohlcv = fetch_live_ohlcv(sym, tf_map[tf_selected], limit=120)

                if not df_ohlcv.empty:
                    fig = go.Figure()

                    fig.add_trace(go.Candlestick(
                        x=df_ohlcv['datetime'], open=df_ohlcv['open'], high=df_ohlcv['high'],
                        low=df_ohlcv['low'], close=df_ohlcv['close'],
                        increasing_line_color=GREEN, increasing_fillcolor=GREEN,
                        decreasing_line_color=RED, decreasing_fillcolor=RED,
                        line=dict(width=1),
                        name="Price"
                    ))

                    for pos in pos_list:
                        side_color = GREEN if pos["side"] == "LONG" else RED
                        fig.add_hline(y=pos['entry_price'], line_dash="dot", line_width=1.3, line_color=side_color, opacity=0.6)

                        fig.add_annotation(
                            x=0.01, xref="paper", y=pos['entry_price'],
                            text=f" {pos['side']} ${pos['entry_price']:,.2f} ", showarrow=False,
                            font=dict(color="#ffffff", size=10, family="Pretendard, Arial"),
                            bgcolor=side_color, borderpad=3,
                            xanchor='left', yanchor='bottom'
                        )

                    if not df_trades.empty:
                        sym_trades = df_trades[df_trades['symbol'] == sym]
                        if not sym_trades.empty:
                            min_dt = df_ohlcv['datetime'].min()
                            recent_trades = sym_trades[sym_trades['datetime'] >= min_dt]

                            buys = recent_trades[((recent_trades['side'] == 'LONG') & (recent_trades['bucket'] == '증가')) | ((recent_trades['side'] == 'SHORT') & (recent_trades['bucket'] == '축소'))]
                            sells = recent_trades[((recent_trades['side'] == 'SHORT') & (recent_trades['bucket'] == '
