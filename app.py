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

# 🇰🇷 시간대 설정
KST = timezone(timedelta(hours=9))
UTC = timezone.utc

# 🎨 색상 상수 (🔥 트레이딩뷰 오리지널 컬러로 전면 교체)
GREEN, RED, BLUE, GRAY = "#089981", "#F23645", "#2563eb", "#9ca3af"

# -----------------------------------------------------------------------------
# 1. 페이지 설정 & UI 완벽 통합 CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Trading Journal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #f4f5f7; }

    /* 🔥 PNL 카드 배경 */
    div[class*="st-key-pnl_card"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        padding: 20px !important;
    }

    /* 🔥 포지션 & 차트 통합 컨테이너 */
    div[class*="st-key-pos_container_"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        padding: 20px 20px 10px 20px !important; 
        margin-bottom: 20px !important;
    }

    /* 라디오 버튼(분봉 선택) 탭 스타일링 */
    div[class*="st-key-tf_radio_"] label[data-baseweb="radio"] {
        background-color: #f3f4f6; padding: 4px 12px; border-radius: 6px; margin-right: 5px; cursor: pointer;
    }
    div[class*="st-key-tf_radio_"] label[data-baseweb="radio"] div:first-child { display: none; }
    div[class*="st-key-tf_radio_"] label[data-baseweb="radio"][aria-checked="true"] { background-color: #2563eb; }
    div[class*="st-key-tf_radio_"] label[data-baseweb="radio"][aria-checked="true"] p { color: #ffffff !important; font-weight: 700; }
    div[class*="st-key-tf_radio_"] label[data-baseweb="radio"] p { color: #6b7280; font-size: 13px; margin: 0; font-weight: 600; }

    /* 모바일 탭 및 내부 속성 */
    button[data-baseweb="tab"] p { color: #6b7280 !important; font-weight: 600 !important; font-size: 15px !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #2563eb !important; font-weight: 800 !important; }
    div[data-baseweb="tab-highlight"] { background-color: #2563eb !important; }

    .pos-box { padding: 5px 10px; flex: 1 1 200px; }
    .pos-divider { border-left: 1px solid #f3f4f6; }
    @media (max-width: 768px) {
        .pos-divider { border-left: none !important; border-top: 1px solid #f3f4f6 !important; padding-top: 15px !important; margin-top: 5px !important; }
    }

    .stButton>button { height: 38px; padding: 0 8px; border-radius: 8px; border: 1px solid #d1d5db; background-color: #ffffff; color: #374151; font-weight: 500; white-space: nowrap; }
    .stButton>button:hover { border-color: #2563eb; color: #2563eb; }
    .note-text { font-size:11.5px; line-height:1.7; color:#9ca3af; margin:14px 2px 0; }
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
    g = df.groupby(["order_id", "symbol", "side", "date"], as_index=False).agg(
        pnl=("pnl", "sum"), price=("price", "mean"), datetime=("datetime", "last"),
        bucket=("bucket", lambda s: s.mode().iat[0]), has_pnl=("has_pnl", "max")
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
        pnl = rnd.choice([rnd.uniform(50, 900), rnd.uniform(50, 900), rnd.uniform(-700, -40), 0.0]) if is_close else 0.0
        sym = rnd.choice(["BTC/USDT", "ETH/USDT"])
        rows.append({
            "order_id": f"DEMO_{i}", "datetime": (t + timedelta(hours=9)).replace(tzinfo=None),
            "date": t.strftime("%Y-%m-%d"), "symbol": sym, "side": rnd.choice(["LONG", "SHORT"]),
            "bucket": "축소" if is_close else "증가", "has_pnl": True, "pnl": round(pnl, 2),
            "price": round(rnd.uniform(62000, 65000) if "BTC" in sym else rnd.uniform(2000, 3000), 2)
        })
    df = finalize(rows) 
    return df[df["date"] >= DASHBOARD_START_DATE]


# -----------------------------------------------------------------------------
# 3. 실시간 유틸 (환율 및 OHLCV)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def fetch_usdt_krw():
    try: return float(ccxt.upbit({'enableRateLimit': True}).fetch_ticker('USDT/KRW').get('last', 1350.0))
    except: return 1350.0

@st.cache_data(ttl=30, show_spinner=False)
def fetch_live_ohlcv(exchange_name, symbol, timeframe, limit=120):
    if exchange_name == "Demo (샘플 데이터)":
        now = datetime.now(UTC)
        minutes_map = {"3m": 3, "5m": 5, "1h": 60}
        dates = [now - timedelta(minutes=minutes_map.get(timeframe, 5)*i) for i in range(limit)]
        dates.reverse()
        base_p = 64800.0 if "BTC" in symbol else 2500.0
        data = []
        for d in dates:
            o = base_p + random.uniform(-10, 10)
            c = o + random.uniform(-20, 20)
            h, l = max(o, c) + random.uniform(2, 15), min(o, c) - random.uniform(2, 15)
            data.append([int(d.timestamp()*1000), o, h, l, c, 100])
            base_p = c
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
        return df

    try:
        ex = None
        if exchange_name == "Bitget": ex = ccxt.bitget({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
        elif exchange_name == "Binance": ex = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'future'}})
        elif exchange_name == "Bybit": ex = ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'linear'}})
        if not ex: return pd.DataFrame()
        
        fetch_sym = symbol + ":USDT" if exchange_name == "Bitget" else symbol
        try: bars = ex.fetch_ohlcv(fetch_sym, timeframe, limit=limit)
        except: 
            try: bars = ex.fetch_ohlcv(fetch_sym, '5m', limit=limit) 
            except: return pd.DataFrame()
            
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
        return df
    except:
        return pd.DataFrame()


# -----------------------------------------------------------------------------
# 4. API 데이터 로드
# -----------------------------------------------------------------------------
@st.cache_data(ttl=10, show_spinner=False)
def fetch_fast_data(exchange_name, api_key, secret, pwd):
    if not api_key or not secret or exchange_name == "Demo (샘플 데이터)":
        return [{"symbol": "BTC/USDT", "side": "SHORT", "leverage": 20, "entry_price": 65100.0, "mark_price": 64800.0, "size": 0.5, "margin": 1581.25, "liq_price": 68200.0, "unrealized_pnl": 150.0, "roe": 9.4}], 10000.0
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
                    "entry_price": entry, "mark_price": mark, "size": size, "margin": margin, "liq_price": float(p.get("liquidationPrice") or 0), "unrealized_pnl": unreal_pnl, "roe": roe
                })
        return active_positions, total_balance
    except: return [], 0.0

@st.cache_data(ttl=3600, show_spinner="거래 내역 불러오는 중...")
def fetch_slow_data(exchange_name, api_key, secret, pwd):
    if not api_key or not secret or exchange_name == "Demo (샘플 데이터)": return demo_trades()
    try:
        if exchange_name == "Bitget": exchange = ccxt.bitget({'apiKey': api_key, 'secret': secret, 'password': pwd, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
        elif exchange_name == "Binance": exchange = ccxt.binance({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'future'}})
        elif exchange_name == "Bybit": exchange = ccxt.bybit({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'linear'}})
        exchange.load_markets()
        rows = []
        for sym in ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "XRP/USDT:USDT"]:
            if sym not in exchange.markets: continue
            try:
                for t in exchange.fetch_my_trades(symbol=sym, limit=200):
                    t_utc = datetime.fromtimestamp(t["timestamp"] / 1000, tz=UTC)
                    side, is_close, has_pnl, pnl, price = classify_fill(t)
                    rows.append({"order_id": str(t.get("order") or t["timestamp"]), "datetime": t_utc.astimezone(KST).replace(tzinfo=None), "date": t_utc.strftime("%Y-%m-%d"), "symbol": t["symbol"].replace(":USDT", ""), "side": side, "bucket": "축소" if is_close else "증가", "has_pnl": has_pnl, "pnl": pnl, "price": price})
            except: continue
        df = finalize(rows)
        return df[df["date"] >= DASHBOARD_START_DATE] if not df.empty else df
    except: return pd.DataFrame(columns=TRADE_COLS)


# -----------------------------------------------------------------------------
# 5. 사이드바
# -----------------------------------------------------------------------------
st.sidebar.title("⚙️ 대시보드 설정")
exchange_choice = st.sidebar.selectbox("거래소 선택", ["Bitget", "Binance", "Bybit", "Demo (샘플 데이터)"])
st.sidebar.markdown(f"<div style='font-size:13px; color:{GREEN}; margin-bottom:15px;'>✅ API 보안 금고 연동 완료</div><div style='font-size:12px; color:{BLUE}; margin-bottom:15px;'>🟢 실시간 자동 업데이트 작동 중 (10초 단위)</div>", unsafe_allow_html=True)
if st.sidebar.button("🔄 수동 새로고침"):
    fetch_fast_data.clear(); fetch_slow_data.clear(); fetch_usdt_krw.clear(); fetch_live_ohlcv.clear(); st.rerun()

df_trades = fetch_slow_data(exchange_choice, MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)

# -----------------------------------------------------------------------------
# 6. 메인 타이틀
# -----------------------------------------------------------------------------
st.markdown("""<div style="margin-top: -10px; margin-bottom: 25px;"><h1 style="font-size: 32px; font-weight: 900; color: #111827; margin: 0; padding: 0; letter-spacing: -0.5px;">Trading History</h1><div style="width: 40px; height: 4px; background-color: #2563eb; margin-top: 10px; border-radius: 2px;"></div></div>""", unsafe_allow_html=True)
st.markdown("""<div style="display: flex; align-items: center; justify-content: space-between; padding-bottom: 15px; border-bottom: 2px solid #e5e7eb; margin-bottom: 25px;"><div style="display: flex; align-items: center; gap: 10px;"><div style="width: 32px; height: 32px; background: linear-gradient(135deg, #3182f6, #1b64da); border-radius: 10px; display: flex; justify-content: center; align-items: center; box-shadow: 0 2px 6px rgba(49,130,246,0.3); font-size: 16px;">📈</div><span style="font-size: 22px; font-weight: 900; color: #111827; letter-spacing: -0.5px;">Trading Journal</span></div></div>""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. [FRAGMENT] 🎯 현재 보유 포지션 & 실시간 차트
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 20px; font-weight: 800; color: #111827; margin-bottom: 10px;'>🎯 현재 보유 포지션</div>", unsafe_allow_html=True)

@st.fragment(run_every=10)
def show_live_positions():
    current_positions, wallet_balance = fetch_fast_data(exchange_choice, MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)
    
    if not current_positions:
        st.markdown("<div style='background-color:#ffffff; border:1px solid #e5e7eb; border-radius:12px; padding:24px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); text-align: center; color: #9ca3af; font-size: 15px; margin-bottom: 25px;'>현재 진행 중인 포지션이 없습니다.</div>", unsafe_allow_html=True)
    else:
        # 🔥 Duplicate Key Error 해결: enumerate를 사용해 고유 인덱스(idx) 부여
        for idx, pos in enumerate(current_positions):
            safe_sym = pos['symbol'].replace("/", "_")
            pos_side = pos["side"]
            
            # 고유 키 생성 (심볼 + 방향 + 인덱스)
            unique_key = f"{safe_sym}_{pos_side}_{idx}"
            
            side_color = GREEN if pos_side == "LONG" else RED
            side_bg = "rgba(8,153,129,0.1)" if pos_side == "LONG" else "rgba(242,54,69,0.1)"
            pnl_val, roe_val = pos["unrealized_pnl"], pos["roe"]
            pnl_color, pnl_sign = (GREEN, "+") if pnl_val >= 0 else (RED, "")
            base_coin = pos['symbol'].split('/')[0] if '/' in pos['symbol'] else pos['symbol']
            pos_usdt_value = pos['size'] * pos['entry_price']
            margin_ratio = (pos['margin'] / wallet_balance * 100) if wallet_balance > 0 else 0

            with st.container(key=f"pos_container_{unique_key}"):
                
                pos_html = f"""<div style="display: flex; flex-wrap: wrap; margin-bottom: 10px;"><div class="pos-box" style="padding-left:0;"><div style='font-size: 13px; color: #6b7280; font-weight: 600; margin-bottom: 8px;'>종목 / 방향 및 규모</div><div style='font-size: 24px; font-weight: 800; color: #111827;'>{pos['symbol']} <span style='font-size: 13px; font-weight: 700; color: {side_color}; background-color: {side_bg}; padding: 4px 8px; border-radius: 6px; margin-left: 5px; vertical-align: middle;'>{pos_side} {pos['leverage']}x</span></div><div style='font-size: 14px; color: #4b5563; font-weight: 600; margin-top: 8px;'>{pos['size']} {base_coin} ≈ ${pos_usdt_value:,.2f}</div></div><div class="pos-box pos-divider"><div style='font-size: 13px; color: #6b7280; font-weight: 600; margin-bottom: 12px;'>진입가 / 현재가</div><div style='display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px;'><span style='width: 45px; font-size: 12px; color: #9ca3af;'>진입가</span><span style='font-size: 18px; font-weight: 700; color: #111827;'>${pos['entry_price']:,.2f}</span></div><div style='display: flex; align-items: baseline; gap: 8px;'><span style='width: 45px; font-size: 12px; color: #9ca3af;'>현재가</span><span style='font-size: 18px; font-weight: 700; color: #2563eb;'>${pos['mark_price']:,.2f}</span></div></div><div class="pos-box pos-divider"><div style='font-size: 13px; color: #6b7280; font-weight: 600; margin-bottom: 12px;'>미실현 손익 / 수익률(ROI)</div><div style='font-size: 26px; font-weight: 800; color: {pnl_color}; margin-bottom: -5px;'>{pnl_sign}${pnl_val:,.2f}</div><div style='font-size: 15px; font-weight: 700; color: {pnl_color};'>({pnl_sign}{roe_val:.2f}%)</div></div><div class="pos-box pos-divider" style="padding-right:0;"><div style='font-size: 13px; color: #6b7280; font-weight: 600; margin-bottom: 12px;'>증거금 <span style="color:#2563eb;">(비중%)</span> / 청산가</div><div style='display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px;'><span style='width: 45px; font-size: 12px; color: #9ca3af;'>증거금</span><span style='font-size: 18px; font-weight: 700; color: #111827;'>${pos['margin']:,.2f} <span style='font-size:14px; color:#2563eb;'>({margin_ratio:.1f}%)</span></span></div><div style='display: flex; align-items: baseline; gap: 8px;'><span style='width: 45px; font-size: 12px; color: #9ca3af;'>청산가</span><span style='font-size: 18px; font-weight: 700; color: #4b5563;'>${pos['liq_price']:,.2f}</span></div></div></div>"""
                st.markdown(pos_html, unsafe_allow_html=True)
                
                st.markdown("<div style='border-top:1px dashed #e5e7eb; margin: 5px 0 15px 0;'></div>", unsafe_allow_html=True)

                tf_selected = st.radio("분봉 선택", ["3분봉", "5분봉", "1시간봉"], horizontal=True, label_visibility="collapsed", key=f"tf_radio_{unique_key}")
                tf_map = {"3분봉": "3m", "5분봉": "5m", "1시간봉": "1h"}
                
                df_ohlcv = fetch_live_ohlcv(exchange_choice, pos['symbol'], tf_map[tf_selected], limit=120)
                
                if not df_ohlcv.empty:
                    fig = go.Figure()
                    
                    fig.add_trace(go.Candlestick(
                        x=df_ohlcv['datetime'], open=df_ohlcv['open'], high=df_ohlcv['high'],
                        low=df_ohlcv['low'], close=df_ohlcv['close'],
                        increasing_line_color=GREEN, increasing_fillcolor=GREEN,
                        decreasing_line_color=RED, decreasing_fillcolor=RED,
                        name="Price"
                    ))

                    fig.add_hline(y=pos['entry_price'], line_dash="dash", line_width=1.5, line_color=side_color, opacity=0.8)
                    fig.add_annotation(
                        x=1, xref="paper", y=pos['entry_price'],
                        text=f"  {pos_side} Entry: ${pos['entry_price']:,.2f} ", showarrow=False,
                        font=dict(color="#ffffff", size=11, family="Arial"), bgcolor=side_color,
                        xanchor='left', yanchor='middle'
                    )

                    if not df_trades.empty:
                        sym_trades = df_trades[df_trades['symbol'] == pos['symbol']]
                        if not sym_trades.empty:
                            min_dt = df_ohlcv['datetime'].min()
                            recent_trades = sym_trades[sym_trades['datetime'] >= min_dt]
                            
                            buys = recent_trades[((recent_trades['side'] == 'LONG') & (recent_trades['bucket'] == '증가')) | ((recent_trades['side'] == 'SHORT') & (recent_trades['bucket'] == '축소'))]
                            sells = recent_trades[((recent_trades['side'] == 'SHORT') & (recent_trades['bucket'] == '증가')) | ((recent_trades['side'] == 'LONG') & (recent_trades['bucket'] == '축소'))]
                            
                            if not buys.empty:
                                fig.add_trace(go.Scatter(
                                    x=buys['datetime'], y=buys['price'], mode='markers+text',
                                    marker=dict(symbol='circle', size=18, color='#3b82f6', line=dict(width=2, color='white')),
                                    text="<b>B</b>", textfont=dict(color="white", size=11, family="Arial"),
                                    name='Buy', hovertemplate="<b>Buy</b><br>%{x}<br>$%{y:,.2f}<extra></extra>"
                                ))
                            if not sells.empty:
                                fig.add_trace(go.Scatter(
                                    x=sells['datetime'], y=sells['price'], mode='markers+text',
                                    marker=dict(symbol='circle', size=18, color='#a855f7', line=dict(width=2, color='white')),
                                    text="<b>S</b>", textfont=dict(color="white", size=11, family="Arial"),
                                    name='Sell', hovertemplate="<b>Sell</b><br>%{x}<br>$%{y:,.2f}<extra></extra>"
                                ))

                    fig.update_layout(
                        height=380, margin=dict(t=5, b=5, l=5, r=60),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        xaxis_rangeslider_visible=False, showlegend=False,
                        xaxis=dict(showgrid=True, gridcolor="#f8f9fa", zeroline=False, tickformat="%H:%M", tickfont=dict(color=GRAY)),
                        yaxis=dict(showgrid=True, gridcolor="#f0f3f6", griddash="solid", zeroline=False, side="right", tickfont=dict(color=GRAY)),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
show_live_positions()

# -----------------------------------------------------------------------------
# 8. 상단 PNL 카드
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 11px; color: #9ca3af; margin-bottom: 10px; margin-top: 15px;'>미실현손익은 일별·월별 추정 PNL 합계에 포함하지 않습니다.</div>", unsafe_allow_html=True)
col_s1, col_s2, col_s3 = st.columns(3)

def make_top_card(title, value, sub_left, sub_right="", krw_rate=1350.0):
    val_color, sign = (GREEN, "+") if value >= 0 else (RED, "")
    krw_val = value * krw_rate
    krw_str = f"+ ₩ {krw_val:,.0f}" if krw_val >= 0 else f"- ₩ {abs(krw_val):,.0f}"
    return f"""<div style="background-color:#ffffff; border:1px solid #e5e7eb; border-radius:12px; padding:24px; min-height: 155px; display:flex; flex-direction:column; box-shadow: 0 1px 3px rgba(0,0,0,0.02);"><div><div style="display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;"><span>{title}</span> <span style="color:#9ca3af; font-weight:400;">{sub_right}</span></div><div style="font-size:32px; font-weight:800; color:{val_color}; margin:15px 0;">{sign}${value:,.2f} <span style="font-size:14px; font-weight:600; color:{GREEN};">USDT</span> <span style="font-size:14px; font-weight:500; color:#9ca3af;">{krw_str}</span></div></div><div style="font-size:12px; color:#9ca3af; margin-top:auto;">{sub_left}</div></div>"""

with col_s1:
    @st.fragment(run_every=3600)
    def render_today_pnl():
        k_rate = fetch_usdt_krw()
        today_str = datetime.now(UTC).strftime("%Y-%m-%d")
        today_pnl = df_trades[df_trades["date"] == today_str]["pnl"].sum() if not df_trades.empty else 0.0
        st.markdown(make_top_card("오늘 추정 PNL", today_pnl, "1시간 마다 갱신(KST)", "", k_rate), unsafe_allow_html=True)
    render_today_pnl()

with col_s2:
    @st.fragment(run_every=3600)
    def render_month_pnl():
        k_rate = fetch_usdt_krw()
        month_str = datetime.now(UTC).strftime("%Y-%m")
        month_pnl = df_trades[df_trades["date"].str.startswith(month_str)]["pnl"].sum() if not df_trades.empty else 0.0
        st.markdown(make_top_card("이번 달 추정 PNL", month_pnl, "1시간 마다 갱신(KST)", "", k_rate), unsafe_allow_html=True)
    render_month_pnl()

with col_s3:
    @st.fragment(run_every=10)
    def render_unrealized_pnl():
        k_rate = fetch_usdt_krw()
        pos, bal = fetch_fast_data(exchange_choice, MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)
        unrealized = sum([p.get("unrealized_pnl", 0.0) for p in pos]) if pos else 0.0
        st.markdown(make_top_card("현재 미실현손익", unrealized, "전체 포지션의 미실현손익 합계", "10초마다 갱신", k_rate), unsafe_allow_html=True)
    render_unrealized_pnl()

st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 9. 수익 히스토리 필터
# -----------------------------------------------------------------------------
st.markdown("<div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:10px;'><span style='font-size:20px; font-weight:800; color:#111827;'>수익 히스토리</span></div>", unsafe_allow_html=True)

if not df_trades.empty and "date" in df_trades.columns:
    df_trades["date_obj"] = pd.to_datetime(df_trades["date"]).dt.date
    oldest_date = df_trades["date_obj"].min()
else:
    df_trades["date_obj"] = pd.Series(dtype=object)
    oldest_date = datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").date()

c_d1, c_d2, c_btn1, c_btn2, c_btn3, c_space = st.columns([1.5, 1.5, 0.8, 0.9, 1.1, 5.5])
with c_d1: start_date = st.date_input("s", value=oldest_date, label_visibility="collapsed")
with c_d2: end_date = st.date_input("e", value=datetime.now(UTC).date(), label_visibility="collapsed")
with c_btn1: btn_today = st.button("오늘", use_container_width=True)
with c_btn2: btn_month = st.button("이번 달", use_container_width=True)
with c_btn3: btn_30d = st.button("최근 30일", use_container_width=True)

if btn_today: start_date, end_date = datetime.now(UTC).date(), datetime.now(UTC).date()
elif btn_month: start_date, end_date = datetime.now(UTC).date().replace(day=1), datetime.now(UTC).date()
elif btn_30d: start_date, end_date = datetime.now(UTC).date() - timedelta(days=30), datetime.now(UTC).date()

filter_start_date = max(start_date, datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").date())
filtered_df = df_trades[(df_trades["date_obj"] >= filter_start_date) & (df_trades["date_obj"] <= end_date)] if not df_trades.empty else df_trades

# -----------------------------------------------------------------------------
# 10. [FRAGMENT] 매매 동향
# -----------------------------------------------------------------------------
st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
st.markdown("<div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:10px;'><span style='font-size:16px; font-weight:800; color:#111827; margin-left:5px;'>매매 동향</span><span style='font-size:12px; color:#9ca3af;'>관측 기록 기준</span></div>", unsafe_allow_html=True)

@st.fragment(run_every=3600)
def render_trade_stats(f_df):
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
        html_t1 = f"""<div style="{card_style}"><div><div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>총 주문 횟수</span><span style='color:#9ca3af; font-weight:400;'>선택 기간</span></div><div style='display:flex; align-items:baseline; margin:15px 0 24px;'><span style='font-size:36px; font-weight:800; color:#111827;'>{total}</span><span style='font-size:14px; font-weight:600; color:#6b7280; margin-left:4px;'>회</span></div><div style='display:flex; flex-direction:column; gap:14px;'><div style='display:flex; justify-content:space-between; font-size:13px;'><div style='flex:1; display:flex; justify-content:space-between; padding-right:15px; border-right:1px solid #e5e7eb;'><span style='color:#6b7280;'>증가 수</span><b style='color:#111827;'>{incr} 회</b></div><div style='flex:1; display:flex; justify-content:space-between; padding-left:15px;'><span style='color:#6b7280;'>축소 수</span><b style='color:#111827;'>{decr} 회</b></div></div><div style='display:flex; justify-content:space-between; font-size:13px;'><div style='flex:1; display:flex; justify-content:space-between; padding-right:15px; border-right:1px solid #e5e7eb;'><span style='color:#6b7280;'>익절 수</span><b style='color:{GREEN};'>{wins} 회</b></div><div style='flex:1; display:flex; justify-content:space-between; padding-left:15px;'><span style='color:#6b7280;'>손절 수</span><b style='color:{RED};'>{losses} 회</b></div></div></div><div style='border-top:1px solid #9ca3af; padding-top:15px; margin-top:20px;'><div style='display:flex; justify-content:space-between; align-items:center;'><span style='font-size:13px; color:#6b7280; font-weight:600;'>기간 승률</span><b style='color:{BLUE}; font-size:18px;'>{rate:.1f}%</b></div></div></div></div>"""
        st.markdown(html_t1, unsafe_allow_html=True)

    with col_t2:
        bg_gradient = f"conic-gradient({GREEN} 0% {lp}%, {RED} {lp}% 100%)" if (lg + sh) > 0 else "conic-gradient(#e5e7eb 0% 100%)"
        html_t2 = f"""<div style="{card_style}"><div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>LONG / SHORT</span><span style='color:#9ca3af; font-weight:400;'>청산 횟수 비율</span></div><div style="display:flex; justify-content:center; align-items:center; flex-grow:1;"><div style="width: 125px; height: 125px; border-radius: 50%; background: {bg_gradient}; display:flex; justify-content:center; align-items:center;"><div style="width: 90px; height: 90px; background-color: #ffffff; border-radius: 50%; display:flex; flex-direction:column; justify-content:center; align-items:center; box-shadow: inset 0 0 5px rgba(0,0,0,0.02);"><span style="font-size:12px; color:#6b7280; font-weight:500;">총 청산</span><b style="font-size:24px; color:#111827; margin-top:-2px;">{decr}건</b></div></div></div><div><div style='display:flex; justify-content:space-between; font-size:13px; margin-bottom:8px;'><span style='color:{GREEN}; font-weight:700;'>LONG</span><b style='color:{GREEN};'>{lg}건 · {lp:.1f}%</b></div><div style='display:flex; justify-content:space-between; font-size:13px;'><span style='color:{RED}; font-weight:700;'>SHORT</span><b style='color:{RED};'>{sh}건 · {sp:.1f}%</b></div></div></div>"""
        st.markdown(html_t2, unsafe_allow_html=True)

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

        html_t3 = f"""<div style="{card_style}"><div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>승률 추이</span><span style='color:#9ca3af; font-weight:400;'>최근 7일 · 오늘 포함</span></div><div style="display:flex; align-items:baseline; gap:10px; margin-top:10px;"><span style="font-size:32px; font-weight:800; color:{BLUE};">{r_rate}%</span><span style="font-size:12px; color:#6b7280;">익절 {tot_w7} · 손절 {tot_l7}</span></div><div style="flex-grow:1; display:flex; flex-direction:column; justify-content:flex-end;">{svg_html}</div></div>"""
        st.markdown(html_t3, unsafe_allow_html=True)

render_trade_stats(filtered_df)

# -----------------------------------------------------------------------------
# 11. [FRAGMENT] 선택 기간 PNL 박스
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

    with st.container(key="pnl_card"):
        html_pnl = f"""<div style='display:flex; justify-content:space-between; align-items:baseline;'><span style='font-size:12px; color:#9ca3af; font-weight:600;'>선택 기간 추정 PNL</span><span style='font-size:12px; color:#9ca3af;'>{last_date} <b style='color:{GREEN if last_val >= 0 else RED};'>{last_sign}${last_val:,.2f}</b></span></div><div style='font-size:32px; font-weight:800; color:{pnl_color}; margin-top:5px;'>{pnl_sign}${period_sum:,.2f} <span style='font-size:14px; color:{GREEN}; font-weight:600;'>USDT</span></div><div style="border-bottom: 1px solid #e5e7eb; margin: 15px 0 5px 0;"></div>"""
        st.markdown(html_pnl, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["일별 손익", "기간 누적"])
        tickvals = [daily_pnl["date_str"].iloc[i] for i in sorted({0, len(daily_pnl) // 2, len(daily_pnl) - 1})] if not daily_pnl.empty else []

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
                st.plotly_chart(style(go.Figure(go.Bar(x=daily_pnl["date_str"], y=daily_pnl["pnl"], marker_color=daily_pnl["color"], name="일별 수익", hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"))), use_container_width=True, config={"displayModeBar": False})
            else: st.caption("선택한 기간에 거래가 없습니다.")

        with tab2:
            if not daily_pnl.empty:
                st.plotly_chart(style(go.Figure(go.Scatter(x=daily_pnl["date_str"], y=daily_pnl["cum"], mode="lines+markers", line=dict(color=BLUE, width=3), fill="tozeroy", fillcolor="rgba(37, 99, 235, 0.08)", name="누적 수익", hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"))), use_container_width=True, config={"displayModeBar": False})

render_pnl_charts(filtered_df)

st.markdown("<div style='font-size:11px; color:#9ca3af; margin: 10px 0 30px 0;'>추정 PNL · USDT · UTC 기준 (한국시간 오전 9시 날짜 전환) · 기간 누적은 선택한 기간의 시작을 0으로 계산합니다.</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 12. 매매 상세 내역 로그 (🔥 마크다운 버그 원천 차단: 좌측 정렬)
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 18px; font-weight: 800; color: #111827; margin-bottom: 15px;'>📝 상세 매매 내역</div>", unsafe_allow_html=True)

@st.fragment(run_every=3600)
def render_trade_logs(f_df):
    if not f_df.empty:
        html_parts = []
        # 파이썬 안에서 HTML을 작성할 때 들여쓰기(띄어쓰기 4칸)를 하면 
        # 마크다운 코드 블록으로 인식하는 버그를 피하기 위해 들여쓰기 제거
        html_parts.append("""
<style>
.log-table { width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
.log-table th { padding: 14px 15px; border-bottom: 1px solid #e5e7eb; color: #9ca3af; font-size: 13px; font-weight: 600; text-align: left; background-color: #ffffff; position: sticky; top: 0; z-index: 2; }
.log-table td { padding: 18px 15px; border-bottom: 1px solid #f3f4f6; font-size: 14px; color: #111827; vertical-align: middle; }
.log-table tbody tr:hover { background-color: #f9fafb; }
.log-long { color: #089981; font-weight: 700; }
.log-short { color: #F23645; font-weight: 700; }
.pnl-win { color: #089981; font-weight: 700; font-size: 15px; text-align: right; }
.pnl-loss { color: #F23645; font-weight: 700; font-size: 15px; text-align: right; }
.pnl-neutral { color: #6b7280; font-weight: 600; font-size: 15px; text-align: right; }
.tag-win { color: #089981; font-size: 12px; font-weight: 600; display: block; margin-top: 4px; text-align: right; }
.tag-loss { color: #F23645; font-size: 12px; font-weight: 600; display: block; margin-top: 4px; text-align: right; }
.tag-neutral { color: #9ca3af; font-size: 12px; font-weight: 500; display: block; margin-top: 4px; text-align: right; }
</style>
<div style="background-color:#ffffff; border:1px solid #e5e7eb; border-radius:12px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); overflow: hidden; margin-bottom: 30px;">
<div style="max-height: 500px; overflow-y: auto;">
<table class="log-table">
<thead>
<tr>
<th>시간 (KST)</th>
<th>종목</th>
<th>방향</th>
<th>구분</th>
<th style="text-align: right;">체결 가격</th>
<th style="text-align: right;">PNL (결과)</th>
</tr>
</thead>
<tbody>
""")
        
        for _, r in f_df.head(100).iterrows():
            dt_str = r['datetime'].strftime('%y. %m. %d. %H:%M')
            sym = r['symbol']
            side_cls = "log-long" if r['side'] == 'LONG' else "log-short"
            side_txt = r['side']
            bucket = r['bucket']
            price = f"${r['price']:,.2f}" if pd.notnull(r['price']) and r['price'] > 0 else "-"
            
            pnl_val = r['pnl']
            res = r['result']
            
            if res == '익절':
                pnl_html = f'<div class="pnl-win">+{pnl_val:,.2f}</div><span class="tag-win">익절</span>'
            elif res == '손절':
                pnl_html = f'<div class="pnl-loss">{pnl_val:,.2f}</div><span class="tag-loss">손절</span>'
            elif res == '본전':
                pnl_html = f'<div class="pnl-neutral">0.00</div><span class="tag-neutral">본전</span>'
            else:
                pnl_html = f'<div class="pnl-neutral">-</div><span class="tag-neutral">-</span>'
                
            html_parts.append(f"""<tr>
<td style="color:#6b7280;">{dt_str}</td>
<td style="font-weight:600;">{sym}</td>
<td class="{side_cls}">{side_txt}</td>
<td style="color:#4b5563;">{bucket}</td>
<td style="text-align: right; font-weight:600;">{price}</td>
<td style="text-align: right;">{pnl_html}</td>
</tr>
""")
            
        html_parts.append("""</tbody>
</table>
</div>
</div>
""")
        st.markdown("".join(html_parts), unsafe_allow_html=True)
    else:
        st.info("새로운 출발을 응원합니다! (아직 등록된 거래 내역이 없습니다)")

render_trade_logs(filtered_df)
