import ccxt
import time
import random
from datetime import datetime, timedelta, timezone
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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
[data-testid="stSpinner"] svg { display: none !important; }
[data-testid="stSpinner"] > div > div:last-child {
    color: #191F28 !important; font-weight: 700 !important; font-size: 15px !important; margin-left: 0 !important;
}
@keyframes loading_dots {
    0% { content: ""; }
    25% { content: " ·"; }
    50% { content: " ·  ·"; }
    75% { content: " ·  ·  ·"; }
    100% { content: ""; }
}
[data-testid="stSpinner"] > div > div:last-child::after {
    content: ""; display: inline-block; width: 28px; text-align: left; animation: loading_dots 1.5s infinite steps(1);
}

.card { background:#ffffff; border-radius:20px; box-shadow:0 2px 14px rgba(15,23,42,0.05); padding:22px 24px; }
div[class*="st-key-pnl_card"] { background-color: #ffffff !important; border: none !important; border-radius: 20px !important; box-shadow: 0 2px 14px rgba(15,23,42,0.05) !important; padding: 22px 24px !important; }
div[class*="st-key-pos_container_"] { background-color: #ffffff !important; border: none !important; border-radius: 20px !important; box-shadow: 0 2px 14px rgba(15,23,42,0.05) !important; padding: 22px 24px 14px !important; margin-bottom: 18px !important; }

div[class*="st-key-tf_radio_"] { margin-bottom: 12px; overflow: visible !important; }
div[class*="st-key-tf_radio_"] div[role="radiogroup"] { display: flex !important; flex-wrap: wrap !important; gap: 8px !important; }
div[class*="st-key-tf_radio_"] label[data-baseweb="radio"] { background-color: #F2F4F6 !important; color: #6b7280 !important; padding: 8px 16px !important; border-radius: 999px; margin: 0 !important; cursor: pointer; transition: background .15s; height: auto !important; }
div[class*="st-key-tf_radio_"] label[data-baseweb="radio"] p { color: #6b7280 !important; font-size: 13.5px !important; margin: 0 !important; font-weight: 600 !important; line-height: 1.4 !important; white-space: nowrap !important; opacity: 1 !important; }
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

@media (max-width: 768px) {
    .pos-divider { border-left: none !important; border-top: 1px solid rgba(15,23,42,0.06) !important; padding-top: 14px !important; margin-top: 6px !important; }
    .hide-on-mobile { display: none !important; }
    .hdr-title-text { font-size: 19px !important; }
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 체결 분류 유틸 (수수료 차감 포함 Net PNL)
# -----------------------------------------------------------------------------
def classify_fill(t):
    info = t.get("info", {}) or {}
    ts = str(info.get("tradeSide", "")).lower()
    ro = info.get("reduceOnly", t.get("reduceOnly"))
    
    raw = info.get("profit", info.get("realizedPnl"))
    has_pnl = raw not in (None, "")
    gross_pnl = float(raw or 0)
    
    fee_cost = 0.0
    if "fee" in t and isinstance(t["fee"], dict):
        fee_cost = float(t["fee"].get("cost", 0.0))

    if "open" in ts: is_close = False
    elif "close" in ts: is_close = True
    elif ro is True: is_close = True
    elif ro is False: is_close = False
    else: is_close = has_pnl and gross_pnl != 0

    if "long" in ts: side = "LONG"
    elif "short" in ts: side = "SHORT"
    else: side = "LONG" if t["side"].upper() == "BUY" else "SHORT"

    if not is_close:
        pnl = -fee_cost
        has_pnl = fee_cost > 0
    else:
        pnl = gross_pnl - fee_cost

    price = float(t.get("price") or t.get("average") or 0.0)

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
    "BNB/USDT", "ADA/USDT", "SUI/USDT", "1000PEPE/USDT", "WIF/USDT",
    "QQQ/USDT"
]

@st.cache_data(ttl=300, show_spinner="거래 내역을 불러오고 있어요")
def fetch_slow_data(api_key, secret, pwd):
    if not api_key or not secret:
        rnd = random.Random(42)
        now = datetime.now(UTC)
        rows = []
        for i in range(300):
            t = now - timedelta(hours=rnd.randint(1, 900))
            t_kst = t.astimezone(KST)
            is_close = rnd.random() < 0.55
            pnl = rnd.choice([rnd.uniform(50, 900), rnd.uniform(50, 900), rnd.uniform(-700, -40), 0.0]) if is_close else -rnd.uniform(0.1, 2.0)
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
        
        # 🌟 현물(Spot) 계좌 원장(Ledger) 조회를 통한 순수 페이백만 수집!
        try:
            current_since = since_ts
            while current_since < now_ts:
                chunk_until = min(current_since + chunk_ms, now_ts)
                
                try:
                    params = {'endTime': chunk_until, 'until': chunk_until, 'type': 'spot'}
                    ledgers = exchange.fetch_ledger('USDT', since=current_since, limit=1000, params=params)
                    
                    for lg in ledgers:
                        amount = float(lg.get('amount', 0) or 0)
                        if amount > 0:
                            # 🎯 1만불 이상(9900불 이상) 입금건 깔끔하게 제외
                            if amount >= 9900:
                                continue
                                
                            lg_type = str(lg.get('type', '')).lower()
                            info = lg.get('info', {}) or {}
                            biz_type = str(info.get('businessType', info.get('type', ''))).lower()
                            
                            payback_kws = ['rebate', 'rebat', 'commission', 'reward', 'partner', 'bonus']
                            is_payback = any(kw in lg_type for kw in payback_kws) or any(kw in biz_type for kw in payback_kws)
                            
                            if is_payback:
                                lg_time = lg.get('timestamp')
                                if not lg_time: continue
                                t_utc = datetime.fromtimestamp(lg_time / 1000, tz=UTC)
                                t_kst = t_utc.astimezone(KST)
                                
                                trade_id = str(lg.get('id') or f"ledger_spot_{lg_time}_{amount}")
                                
                                rows.append({
                                    "trade_id": trade_id, "order_id": trade_id, "datetime": t_kst.replace(tzinfo=None),
                                    "date": t_kst.strftime("%Y-%m-%d"), "symbol": "FEE/PAYBACK",
                                    "side": "입금", "bucket": "축소", "has_pnl": True,
                                    "pnl": amount, "price": 0.0
                                })
                except Exception:
                    pass
                
                current_since = chunk_until
        except Exception as e_ledger:
            errs.append(f"원장(페이백) 조회 실패: {e_ledger}")

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
        # 🎯 포지션이 없을 때 나타나는 안내 문구 아래에 여백(margin-bottom)을 추가하여 밑의 영역과 분리
        st.markdown(f"<div class='card' style='text-align: center; color: {SUB}; font-size: 14.5px; font-weight: 600; padding: 40px 20px; margin-bottom: 15px;'>현재 진행 중인 포지션이 없습니다</div>", unsafe_allow_html=True)
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True) # 강제 여백 확보
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
                            sells = recent_trades[((recent_trades['side'] == 'SHORT') & (recent_trades['bucket'] == '증가')) | ((recent_trades['side'] == 'LONG') & (recent_trades['bucket'] == '축소'))]

                            price_span = (df_ohlcv['high'].max() - df_ohlcv['low'].min()) or (df_ohlcv['close'].iloc[-1] * 0.01)
                            off = price_span * 0.05

                            if not buys.empty:
                                fig.add_trace(go.Scatter(
                                    x=buys['datetime'], y=buys['price'] - off, mode='markers',
                                    marker=dict(symbol='triangle-up', size=11, color=GREEN, line=dict(width=1, color='#ffffff')),
                                    customdata=buys['price'],
                                    name='매수', hovertemplate="<b>매수 체결</b><br>%{x}<br>$%{customdata:,.2f}<extra></extra>"
                                ))
                            if not sells.empty:
                                fig.add_trace(go.Scatter(
                                    x=sells['datetime'], y=sells['price'] + off, mode='markers',
                                    marker=dict(symbol='triangle-down', size=11, color=RED, line=dict(width=1, color='#ffffff')),
                                    customdata=sells['price'],
                                    name='매도', hovertemplate="<b>매도 체결</b><br>%{x}<br>$%{customdata:,.2f}<extra></extra>"
                                ))

                    fig.update_layout(
                        height=350, margin=dict(t=15, b=10, l=10, r=45),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        xaxis_rangeslider_visible=False, showlegend=False,
                        xaxis=dict(showgrid=True, gridcolor="#F8F9FA", zeroline=False, tickformat="%H:%M", tickfont=dict(color=GRAY, size=11)),
                        yaxis=dict(showgrid=True, gridcolor="#F0F3F6", zeroline=False, side="right", tickfont=dict(color=GRAY, size=11)),
                        hovermode="x unified",
                        hoverlabel=dict(bgcolor="#ffffff", bordercolor="#F2F4F6", font=dict(color=TEXT, size=12, family="Pretendard, Arial")),
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
show_live_positions()

# -----------------------------------------------------------------------------
# 7. 상단 PNL 카드
# -----------------------------------------------------------------------------
col_s1, col_s2, col_s3 = st.columns(3)

def make_top_card(title, value, sub_left, sub_right="", krw_rate=1350.0):
    val_color, sign = (GREEN, "+") if value >= 0 else (RED, "")
    krw_val = value * krw_rate
    krw_str = f"+ ₩{krw_val:,.0f}" if krw_val >= 0 else f"- ₩{abs(krw_val):,.0f}"
    return f"""<div class="card" style="min-height: 150px; display:flex; flex-direction:column;"><div><div style="display:flex; justify-content:space-between; font-size:13px; font-weight:700; color:{TEXT};"><span>{title}</span> <span style="color:{SUB}; font-weight:500;">{sub_right}</span></div><div style="display:flex; align-items:baseline; gap:8px; margin:14px 0 2px;"><span style="font-size:30px; font-weight:800; color:{val_color}; letter-spacing:-0.02em;">{sign}${value:,.2f}</span><span style="font-size:13px; font-weight:600; color:{SUB};">{krw_str}</span></div></div><div style="font-size:12px; color:{SUB}; margin-top:auto; padding-top:10px;">{sub_left}</div></div>"""

with col_s1:
    @st.fragment(run_every=300)
    def render_today_pnl():
        k_rate = fetch_usdt_krw()
        today_str = datetime.now(KST).strftime("%Y-%m-%d")
        today_pnl = df_trades[df_trades["date"] == today_str]["pnl"].sum() if not df_trades.empty else 0.0
        st.markdown(make_top_card("오늘 추정 PNL", today_pnl, "5분마다 갱신 (KST)", "", k_rate), unsafe_allow_html=True)
    render_today_pnl()

with col_s2:
    @st.fragment(run_every=300)
    def render_month_pnl():
        k_rate = fetch_usdt_krw()
        month_str = datetime.now(KST).strftime("%Y-%m")
        month_pnl = df_trades[df_trades["date"].str.startswith(month_str)]["pnl"].sum() if not df_trades.empty else 0.0
        st.markdown(make_top_card("이번 달 추정 PNL", month_pnl, "5분마다 갱신 (KST)", "", k_rate), unsafe_allow_html=True)
    render_month_pnl()

with col_s3:
    @st.fragment(run_every=10)
    def render_unrealized_pnl():
        k_rate = fetch_usdt_krw()
        pos, bal = fetch_fast_data(MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)
        unrealized = sum([p.get("unrealized_pnl", 0.0) for p in pos]) if pos else 0.0
        st.markdown(make_top_card("현재 미실현손익", unrealized, "전체 포지션 합계 · 10초마다 갱신", "", k_rate), unsafe_allow_html=True)
    render_unrealized_pnl()

st.markdown(f"<div style='font-size: 12px; color: {SUB}; margin-top: 10px; margin-bottom: 28px;'> 미실현손익은 일별·월별 추정 PNL 합계에 포함하지 않습니다</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 8. [FRAGMENT] 매매동향 (기본 기간 30일 설정)
# -----------------------------------------------------------------------------
st.markdown(f"<div style='font-size: 19px; font-weight: 800; color: {TEXT}; margin-bottom: 14px;'> 매매동향</div>", unsafe_allow_html=True)

today_kst = datetime.now(KST).date()
dashboard_start = datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").date()
default_start = max(dashboard_start, today_kst - timedelta(days=30))

if "date_range" not in st.session_state:
    st.session_state.date_range = (default_start, today_kst)

def set_range(mode):
    if mode == "today":
        st.session_state.date_range = (today_kst, today_kst)
    elif mode == "month":
        st.session_state.date_range = (today_kst.replace(day=1), today_kst)
    elif mode == "30d":
        st.session_state.date_range = (today_kst - timedelta(days=30), today_kst)

c_d, c_btn1, c_btn2, c_btn3 = st.columns([3, 1, 1, 1.2])
with c_btn1:
    st.button("오늘", on_click=set_range, args=("today",), use_container_width=True)
with c_btn2:
    st.button("이번 달", on_click=set_range, args=("month",), use_container_width=True)
with c_btn3:
    st.button("최근 30일", on_click=set_range, args=("30d",), use_container_width=True)

with c_d:
    dates = st.date_input(
        "기간 선택",
        key="date_range",
        max_value=today_kst,
        label_visibility="collapsed"
    )

if isinstance(dates, tuple) and len(dates) == 2:
    start_date, end_date = dates
elif isinstance(dates, tuple) and len(dates) == 1:
    start_date, end_date = dates[0], dates[0]
else:
    start_date, end_date = dates, dates

filter_start_date = max(start_date, dashboard_start)
filter_start_str = filter_start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

filtered_df = df_trades[(df_trades["date"] >= filter_start_str) & (df_trades["date"] <= end_str)] if not df_trades.empty else df_trades

st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

@st.fragment(run_every=300)
def render_trade_stats(f_df):
    all_df = fetch_slow_data(MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)
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

    card_style = "background-color:#ffffff; border-radius:20px; padding:22px; box-shadow: 0 2px 14px rgba(15,23,42,0.05); height: 320px; display:flex; flex-direction:column; justify-content:space-between;"

    with col_t1:
        html_t1 = f"""<div style="{card_style}"><div><div style='display:flex; justify-content:space-between; font-size:13px; font-weight:700; color:{TEXT};'><span>총 주문 횟수</span><span style='color:{SUB}; font-weight:500;'>선택 기간</span></div><div style='display:flex; align-items:baseline; margin:14px 0 22px;'><span style='font-size:34px; font-weight:800; color:{TEXT}; letter-spacing:-0.02em;'>{total}</span><span style='font-size:13px; font-weight:600; color:{SUB}; margin-left:4px;'>회</span></div><div style='display:flex; flex-direction:column; gap:14px;'><div style='display:flex; justify-content:space-between; font-size:13px;'><div style='flex:1; display:flex; justify-content:space-between; padding-right:15px;'><span style='color:{SUB};'>증가</span><b style='color:{TEXT};'>{incr} 회</b></div><div style='flex:1; display:flex; justify-content:space-between; padding-left:15px;'><span style='color:{SUB};'>축소</span><b style='color:{TEXT};'>{decr} 회</b></div></div><div style='display:flex; justify-content:space-between; font-size:13px;'><div style='flex:1; display:flex; justify-content:space-between; padding-right:15px;'><span style='color:{SUB};'>익절</span><b style='color:{GREEN};'>{wins} 회</b></div><div style='flex:1; display:flex; justify-content:space-between; padding-left:15px;'><span style='color:{SUB};'>손절</span><b style='color:{RED};'>{losses} 회</b></div></div></div><div style='border-top:1px solid {DIVIDER}; padding-top:14px; margin-top:18px;'><div style='display:flex; justify-content:space-between; align-items:center;'><span style='font-size:13px; color:{SUB}; font-weight:600;'>기간 승률</span><b style='color:{BLUE}; font-size:17px;'>{rate:.1f}%</b></div></div></div></div>"""
        st.markdown(html_t1, unsafe_allow_html=True)

    with col_t2:
        bg_gradient = f"conic-gradient({GREEN} 0% {lp}%, {RED} {lp}% 100%)" if (lg + sh) > 0 else "conic-gradient(#EEF0F4 0% 100%)"
        html_t2 = f"""<div style="{card_style}"><div style='display:flex; justify-content:space-between; font-size:13px; font-weight:700; color:{TEXT};'><span>LONG / SHORT</span><span style='color:{SUB}; font-weight:500;'>청산 횟수 비율</span></div><div style="display:flex; justify-content:center; align-items:center; flex-grow:1;"><div style="width: 118px; height: 118px; border-radius: 50%; background: {bg_gradient}; display:flex; justify-content:center; align-items:center;"><div style="width: 86px; height: 86px; background-color: #ffffff; border-radius: 50%; display:flex; flex-direction:column; justify-content:center; align-items:center;"><span style="font-size:11.5px; color:{SUB}; font-weight:600;">총 청산</span><b style="font-size:22px; color:{TEXT}; margin-top:-2px;">{decr}건</b></div></div></div><div><div style='display:flex; justify-content:space-between; font-size:13px; margin-bottom:8px;'><span style='color:{GREEN}; font-weight:700;'>LONG</span><b style='color:{GREEN};'>{lg}건 · {lp:.1f}%</b></div><div style='display:flex; justify-content:space-between; font-size:13px;'><span style='color:{RED}; font-weight:700;'>SHORT</span><b style='color:{RED};'>{sh}건 · {sp:.1f}%</b></div></div></div>"""
        st.markdown(html_t2, unsafe_allow_html=True)

    with col_t3:
        now_kst = datetime.now(KST)
        day_labels, vals = [], []
        tot_w7, tot_l7 = 0, 0
        for i in range(6, -1, -1):
            d = now_kst - timedelta(days=i)
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
        dashes = "".join(f"<text x='{x:.1f}' y='60' font-size='13' fill='#D1D6DB' text-anchor='middle'>―</text>" for x in empty_x)
        days = "".join(f"<text x='{i * step_x:.1f}' y='130' font-size='10' fill='{SUB}' text-anchor='middle'>{day_labels[i]}</text>" for i in range(7))
        svg_html = f"<svg viewBox='-15 -15 310 150' style='width:100%; height:130px; display:block;'>{lines}{dots}{dashes}{days}</svg>"

        html_t3 = f"""<div style="{card_style}"><div style='display:flex; justify-content:space-between; font-size:13px; font-weight:700; color:{TEXT};'><span>승률 추이</span><span style='color:{SUB}; font-weight:500;'>최근 7일 · 오늘 포함</span></div><div style="display:flex; align-items:baseline; gap:10px; margin-top:10px;"><span style="font-size:30px; font-weight:800; color:{BLUE}; letter-spacing:-0.02em;">{r_rate}%</span><span style="font-size:12px; color:{SUB};">익절 {tot_w7} · 손절 {tot_l7}</span></div><div style="flex-grow:1; display:flex; flex-direction:column; justify-content:flex-end;">{svg_html}</div></div>"""
        st.markdown(html_t3, unsafe_allow_html=True)

render_trade_stats(filtered_df)

# -----------------------------------------------------------------------------
# 9. [FRAGMENT] 선택 기간 PNL 박스
# -----------------------------------------------------------------------------
st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)

@st.fragment(run_every=300)
def render_pnl_charts(f_df):
    period_sum = f_df["pnl"].sum() if not f_df.empty else 0.0
    pnl_color, pnl_sign = (GREEN, "+") if period_sum >= 0 else (RED, "")

    if not f_df.empty:
        daily_pnl = f_df.groupby("date")["pnl"].sum().reset_index()
        full_dates = [d.strftime("%Y-%m-%d") for d in pd.date_range(start=filter_start_str, end=end_str)]
        daily_pnl = pd.merge(pd.DataFrame({"date": full_dates}), daily_pnl, on="date", how="left").fillna({"pnl": 0})
        daily_pnl["cum"] = daily_pnl["pnl"].cumsum()
        daily_pnl["color"] = daily_pnl["pnl"].apply(lambda x: GREEN if x >= 0 else RED)
        last_date, last_val = daily_pnl["date"].iloc[-1], daily_pnl["pnl"].iloc[-1]
    else:
        daily_pnl = pd.DataFrame()
        last_date, last_val = end_str, 0.0

    last_sign = "+" if last_val >= 0 else ""

    with st.container(key="pnl_card"):
        html_pnl = f"""<div style='display:flex; justify-content:space-between; align-items:baseline;'><span style='font-size:13px; color:{TEXT}; font-weight:700;'>선택 기간 추정 PNL</span><span style='font-size:12px; color:{SUB};'>{last_date} <b style='color:{GREEN if last_val >= 0 else RED};'>{last_sign}${last_val:,.2f}</b></span></div><div style='font-size:30px; font-weight:800; color:{pnl_color}; margin-top:8px; letter-spacing:-0.02em;'>{pnl_sign}${period_sum:,.2f} <span style='font-size:14px; color:{SUB}; font-weight:600;'>USDT</span></div><div style="border-bottom: 1px solid {DIVIDER}; margin: 16px 0 6px 0;"></div>"""
        st.markdown(html_pnl, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["일별 손익", "기간 누적"])
        n_days = len(daily_pnl)
        if n_days == 0:
            tickvals = []
        elif n_days <= 10:
            tickvals = list(daily_pnl["date"])
        else:
            step = max(1, n_days // 6)
            idxs = sorted(set(range(0, n_days, step)) | {n_days - 1})
            tickvals = [daily_pnl["date"].iloc[i] for i in idxs]

        def style(fig):
            fig.update_layout(
                template="plotly_white", margin=dict(t=20, b=10, l=10, r=10), height=350,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
                xaxis=dict(showgrid=False, zeroline=False, type='category', tickmode='array', tickvals=tickvals),
                yaxis=dict(showgrid=True, gridcolor="#F2F4F6", zeroline=True, zerolinecolor="#E5E8EB", zerolinewidth=1.5, nticks=5),
            )
            return fig

        with tab1:
            if not daily_pnl.empty:
                try:
                    bar = go.Bar(x=daily_pnl["date"], y=daily_pnl["pnl"], marker=dict(color=daily_pnl["color"], line_width=0, cornerradius=8), name="일별 수익", hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>")
                except Exception:
                    bar = go.Bar(x=daily_pnl["date"], y=daily_pnl["pnl"], marker_color=daily_pnl["color"], marker_line_width=0, name="일별 수익", hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>")
                st.plotly_chart(style(go.Figure(bar)), use_container_width=True, config={"displayModeBar": False})
            else: st.caption("선택한 기간에 거래가 없습니다")

        with tab2:
            if not daily_pnl.empty:
                st.plotly_chart(style(go.Figure(go.Scatter(x=daily_pnl["date"], y=daily_pnl["cum"], mode="lines+markers", line=dict(color=BLUE, width=3, shape="spline", smoothing=0.4), marker=dict(size=5), fill="tozeroy", fillcolor="rgba(49,130,246,0.08)", name="누적 수익", hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"))), use_container_width=True, config={"displayModeBar": False})

render_pnl_charts(filtered_df)

# 🎯 그래프 아래 안내 문구 간격을 좁혀주기 위해 margin-top 값을 음수로 수정
st.markdown(f"<div class='note-text' style='margin-top: -15px; margin-bottom: 20px;'>추정 PNL · USDT · KST 기준 · 기간 누적은 선택한 기간의 시작을 0으로 계산합니다</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 10. 상세 매매 내역 — 토스 거래내역 스타일 리스트
# -----------------------------------------------------------------------------
st.markdown(f"<div style='font-size: 17px; font-weight: 800; color: {TEXT}; margin: 32px 0 14px;'>상세 매매 내역</div>", unsafe_allow_html=True)

@st.fragment(run_every=300)
def render_trade_logs(f_df):
    if f_df.empty:
        st.markdown(f"<div class='card' style='text-align:center; color:{SUB}; padding:32px;'>아직 등록된 거래 내역이 없습니다</div>", unsafe_allow_html=True)
        return

    rows = []
    for _, r in f_df.head(100).iterrows():
        dt_str = r['datetime'].strftime('%m.%d %H:%M')

        is_payback = r['symbol'] == "FEE/PAYBACK"
        base = "💰" if is_payback else (r['symbol'].split('/')[0] if '/' in r['symbol'] else r['symbol'])[:1]
        sym_name = "수수료 페이백" if is_payback else r['symbol']
        side_name = "입금" if is_payback else r['side']

        side_color = GREEN if (r['side'] == 'LONG' or is_payback) else RED
        side_soft = GREEN_SOFT if (r['side'] == 'LONG' or is_payback) else RED_SOFT
        price = f"${r['price']:,.2f}" if pd.notnull(r['price']) and r['price'] > 0 else "-"
        pnl_val, res = r['pnl'], r['result']

        if is_payback:
            res = '입금'
            pnl_color, chip_bg, pnl_txt = GREEN, GREEN_SOFT, f"+{pnl_val:,.2f}"
        elif res == '익절':
            pnl_color, chip_bg, pnl_txt = GREEN, GREEN_SOFT, f"+{pnl_val:,.2f}"
        elif res == '손절':
            pnl_color, chip_bg, pnl_txt = RED, RED_SOFT, f"{pnl_val:,.2f}"
        elif res == '본전':
            pnl_color, chip_bg, pnl_txt = SUB, "rgba(139,149,161,0.12)", "0.00"
        elif res == '진입':
            if pnl_val < 0:
                pnl_color, chip_bg, pnl_txt = SUB, "rgba(139,149,161,0.12)", f"{pnl_val:,.3f}" 
            else:
                pnl_color, chip_bg, pnl_txt = SUB, "rgba(139,149,161,0.12)", "-"
        else:
            pnl_color, chip_bg, pnl_txt = SUB, "rgba(139,149,161,0.12)", "-"

        rows.append(
            "<div class='log-row'>"
            f"<div class='log-left'><div class='sym-badge' style='background:{side_soft};color:{side_color};'>{base}</div>"
            f"<div><div class='row-title'>{sym_name} <span class='pill' style='background:{side_soft};color:{side_color};'>{side_name}</span></div>"
            f"<div class='row-sub'>{dt_str} · {r['bucket']}</div></div></div>"
            f"<div class='row-right'><div class='row-price'>{price}</div>"
            f"<div class='row-pnl' style='color:{pnl_color};'>{pnl_txt}<span class='chip' style='background:{chip_bg};color:{pnl_color};'>{res}</span></div></div>"
            "</div>"
        )

    list_html = "<div class='card' style='padding:6px 20px; max-height:560px; overflow-y:auto;'>" + "".join(rows) + "</div>"
    st.markdown(list_html, unsafe_allow_html=True)

render_trade_logs(filtered_df)
