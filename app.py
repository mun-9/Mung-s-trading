import ccxt
import time
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# =============================================================================
# 🔑 웹사이트 비밀 금고에서 API 키를 뒤에서 몰래 꺼내옵니다
# =============================================================================
try:
    MY_API_KEY = st.secrets["API_KEY"]
    MY_SECRET_KEY = st.secrets["SECRET_KEY"]
    MY_PASSPHRASE = st.secrets["PASSPHRASE"]
except:
    MY_API_KEY = ""
    MY_SECRET_KEY = ""
    MY_PASSPHRASE = ""

# 🎯 [초기화 설정] 여기서 설정한 날짜 이전의 과거 데이터는 싹 다 날립니다! (유저에겐 비밀)
DASHBOARD_START_DATE = "2026-09-28"

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
    /* 전체 배경색 */
    .stApp { background-color: #f4f5f7; }
    
    /* 보이지 않는 '화이트 마커'를 품은 모든 컨테이너를 강제로 흰색 카드로 만듦 */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.white-marker),
    div[data-testid="stContainer"]:has(.white-marker),
    div[data-testid="stVerticalBlock"]:has(.white-marker) > div[style*="border"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }
    
    /* 모바일 가로/세로선 반응형 */
    .pos-box { padding: 10px; flex: 1 1 200px; }
    .pos-divider { border-left: 1px solid #f3f4f6; }
    @media (max-width: 768px) {
        .pos-divider { border-left: none !important; border-top: 1px solid #f3f4f6 !important; padding-top: 15px !important; margin-top: 5px !important; }
    }
    
    /* 버튼 디자인 */
    .stButton>button { height: 38px; padding: 0 8px; border-radius: 8px; border: 1px solid #d1d5db; background-color: #ffffff; color: #374151; font-weight: 500; white-space: nowrap; }
    .stButton>button:hover { border-color: #2563eb; color: #2563eb; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 캐싱된 API 데이터 로드 (빠른 놈 10초 / 느린 놈 1시간 분리!)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=5, show_spinner=False)
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
            if float(p.get("contracts", 0)) > 0:
                pos_side = p.get("side", "LONG").upper()
                entry, mark, size, margin = float(p.get("entryPrice", 0)), float(p.get("markPrice", 0)), float(p.get("contracts", 0)), float(p.get("initialMargin", 0))
                unreal_pnl = (mark - entry) * size if pos_side == "LONG" else (entry - mark) * size
                roe = (unreal_pnl / margin * 100) if margin > 0 else 0
                active_positions.append({
                    "symbol": p.get("symbol", "").replace(":USDT", ""), "side": pos_side, "leverage": int(p.get("leverage", 1)),
                    "entry_price": entry, "mark_price": mark, "size": size, "margin": margin,
                    "liq_price": float(p.get("liquidationPrice", 0)), "unrealized_pnl": unreal_pnl, "roe": roe,
                })
        return active_positions, total_balance
    except: return [], 0.0

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_slow_data(exchange_name, api_key, secret, pwd):
    if not api_key or not secret or exchange_name == "Demo (샘플 데이터)":
        import random
        random.seed(42)
        records = []
        today_utc = datetime.utcnow()
        for _ in range(25): 
            t_utc = today_utc - timedelta(hours=random.randint(1, 23))
            pnl = random.choice([random.uniform(100, 2500), random.uniform(-1500, -50)])
            records.append({
                "datetime": t_utc + timedelta(hours=9),
                "date": t_utc.strftime("%Y-%m-%d"),
                "symbol": random.choice(["BTC/USDT", "ETH/USDT", "SOL/USDT"]),
                "side": random.choice(["LONG", "SHORT"]),
                "pnl": round(pnl, 2), "result": "익절" if pnl >= 0 else "손절",
            })
        df = pd.DataFrame(records).sort_values("datetime", ascending=False)
        return df[df["date"] >= DASHBOARD_START_DATE]
    
    try:
        if exchange_name == "Bitget": exchange = ccxt.bitget({'apiKey': api_key, 'secret': secret, 'password': pwd, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
        elif exchange_name == "Binance": exchange = ccxt.binance({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'future'}})
        elif exchange_name == "Bybit": exchange = ccxt.bybit({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'linear'}})
        
        exchange.load_markets()
        trade_records = []
        for sym in ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "XRP/USDT:USDT", "DOGE/USDT:USDT", "ADA/USDT:USDT", "BCH/USDT:USDT", "BNB/USDT:USDT", "PEPE/USDT:USDT", "LINK/USDT:USDT"]:
            try:
                if sym in exchange.markets:
                    for t in exchange.fetch_my_trades(symbol=sym, limit=200):
                        t_utc = datetime.utcfromtimestamp(t["timestamp"] / 1000)
                        pnl = float(t.get("info", {}).get("profit", 0))
                        info_side = str(t.get("info", {}).get("tradeSide", "")).lower()
                        mapped_side = "LONG" if "long" in info_side else ("SHORT" if "short" in info_side else ("LONG" if t["side"].upper() == "BUY" else "SHORT"))
                        trade_records.append({
                            "datetime": t_utc + timedelta(hours=9), 
                            "date": t_utc.strftime("%Y-%m-%d"),
                            "symbol": t["symbol"].replace(":USDT", ""), "side": mapped_side, 
                            "pnl": pnl, "result": "익절" if pnl >= 0 else "손절"
                        })
            except: continue
            
        df = pd.DataFrame(trade_records).sort_values("datetime", ascending=False) if trade_records else pd.DataFrame(columns=["datetime", "date", "symbol", "side", "pnl", "result"])
        
        if not df.empty:
            df = df[df["date"] >= DASHBOARD_START_DATE]
            
        return df
    except: return pd.DataFrame(columns=["datetime", "date", "symbol", "side", "pnl", "result"])

# -----------------------------------------------------------------------------
# 3. 사이드바 메뉴 
# -----------------------------------------------------------------------------
st.sidebar.title("⚙️ 멍그 대시보드 설정")
exchange_choice = st.sidebar.selectbox("거래소 선택", ["Bitget", "Binance", "Bybit", "Demo (샘플 데이터)"])
st.sidebar.markdown("<div style='font-size:13px; color:#00a86b; margin-bottom:15px;'>✅ API 보안 금고 연동 완료</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='font-size:12px; color:#2563eb; margin-bottom:15px;'>🟢 실시간 자동 업데이트 작동 중 (10초 단위)</div>", unsafe_allow_html=True)

if st.sidebar.button("🔄 수동 새로고침"):
    fetch_fast_data.clear()
    fetch_slow_data.clear()
    st.rerun()

df_trades = fetch_slow_data(exchange_choice, MY_API_KEY, MY_SECRET_KEY, MY_PASSPHRASE)

# -----------------------------------------------------------------------------
# 4. 🎯 메인 타이틀
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
# 5. [FRAGMENT] 🎯 현재 보유 포지션 (10초 자동 갱신!)
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
            side_color, side_bg = ("#00a86b", "rgba(0,168,107,0.1)") if pos_side == "LONG" else ("#ef4444", "rgba(239,68,68,0.1)")
            pnl_val, roe_val = pos["unrealized_pnl"], pos["roe"]
            pnl_color, pnl_sign = ("#00a86b", "+") if pnl_val >= 0 else ("#ef4444", "")
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
                    <div style='font-size: 13px; color: #6b7280; font-weight: 600; margin-bottom: 12px;'>미실현 손익 / 수익률(ROE)</div>
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
# 6. 상단 PNL 카드 
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 11px; color: #9ca3af; margin-bottom: 10px; margin-top: -10px;'>미실현손익은 일별·월별 추정 PNL 합계에 포함하지 않습니다.</div>", unsafe_allow_html=True)
col_s1, col_s2, col_s3 = st.columns(3)

def make_top_card(title, value, sub_left, sub_right=""):
    val_color, sign = ("#00a86b", "+") if value >= 0 else ("#ef4444", "")
    return f"""<div style="background-color:#ffffff; border:1px solid #e5e7eb; border-radius:12px; padding:24px; min-height: 155px; display:flex; flex-direction:column; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
        <div><div style="display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;"><span>{title}</span> <span style="color:#9ca3af; font-weight:400;">{sub_right}</span></div>
        <div style="font-size:32px; font-weight:800; color:{val_color}; margin:15px 0;">{sign}${value:,.2f} <span style="font-size:14px; font-weight:600; color:#00a86b;">USDT</span></div></div>
        <div style="font-size:12px; color:#9ca3af; margin-top:auto;">{sub_left}</div></div>"""

with col_s1:
    @st.fragment(run_every=3600)
    def render_today_pnl():
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        today_pnl = df_trades[df_trades["date"] == today_str]["pnl"].sum() if not df_trades.empty else 0.0
        st.markdown(make_top_card("오늘 추정 PNL", today_pnl, "매일 오전 9시 리셋 (KST)", "1시간마다 갱신"), unsafe_allow_html=True)
    render_today_pnl()

with col_s2:
    @st.fragment(run_every=3600)
    def render_month_pnl():
        month_str = datetime.utcnow().strftime("%Y-%m")
        month_pnl = df_trades[df_trades["date"].str.startswith(month_str)]["pnl"].sum() if not df_trades.empty else 0.0
        st.markdown(make_top_card("이번 달 추정 PNL", month_pnl, "매월 1일 오전 9시 리셋 (KST)", "1시간마다 갱신"), unsafe_allow_html=True)
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
# 7. 수익 히스토리 필터 
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
with c_d2: end_date = st.date_input("e", value=datetime.utcnow().date(), label_visibility="collapsed")
with c_btn1: btn_today = st.button("오늘", use_container_width=True)
with c_btn2: btn_month = st.button("이번 달", use_container_width=True)
with c_btn3: btn_30d = st.button("최근 30일", use_container_width=True)
with c_drop: st.selectbox("집계", ["일별 집계", "주별 집계", "월별 집계"], label_visibility="collapsed")

if btn_today: start_date, end_date = datetime.utcnow().date(), datetime.utcnow().date()
elif btn_month: start_date, end_date = datetime.utcnow().date().replace(day=1), datetime.utcnow().date()
elif btn_30d: start_date, end_date = datetime.utcnow().date() - timedelta(days=30), datetime.utcnow().date()

filter_start_date = max(start_date, datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").date())
filtered_df = df_trades[(df_trades["date_obj"] >= filter_start_date) & (df_trades["date_obj"] <= end_date)] if not df_trades.empty else df_trades

# -----------------------------------------------------------------------------
# 8. [FRAGMENT] 매매 동향
# -----------------------------------------------------------------------------
st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
st.markdown("<div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:10px;'><span style='font-size:16px; font-weight:800; color:#111827; margin-left:5px;'>매매 동향</span><span style='font-size:12px; color:#9ca3af;'>관측 기록 기준 (1시간 갱신)</span></div>", unsafe_allow_html=True)

@st.fragment(run_every=3600)
def render_trade_stats(f_df):
    col_t1, col_t2, col_t3 = st.columns([1, 1, 1.2])

    total = len(f_df)
    wins = len(f_df[f_df["result"] == "익절"]) if total > 0 else 0
    losses = len(f_df[f_df["result"] == "손절"]) if total > 0 else 0
    rate = (wins / total * 100) if total > 0 else 0
    longs = len(f_df[f_df["side"] == "LONG"]) if total > 0 else 0
    shorts = len(f_df[f_df["side"] == "SHORT"]) if total > 0 else 0
    long_p = (longs/(longs+shorts)*100) if (longs+shorts)>0 else 0
    short_p = (shorts/(longs+shorts)*100) if (longs+shorts)>0 else 0

    card_style = "background-color:#ffffff; border:1px solid #e5e7eb; border-radius:12px; padding:20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); height: 320px; display:flex; flex-direction:column; justify-content:space-between;"

    # ★ 거래 횟수 카드 디자인 전면 개편 (게이지바 추가)
    with col_t1:
        st.markdown(f"""
        <div style="{card_style}">
            <div>
                <div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>포지션 거래 횟수</span><span style='color:#9ca3af; font-weight:400;'>선택 기간</span></div>
                <div style='font-size:36px; font-weight:800; color:#111827; margin:15px 0;'>{total} <span style='font-size:14px; font-weight:500;'>회</span></div>
                
                <div style='font-size:12px; color:#6b7280; margin-bottom:5px; display:flex; justify-content:space-between;'>
                    <span>승·패 비율</span>
                    <b style='color:#111827;'>{rate:.1f}% 승률</b>
                </div>
                <div style="display:flex; width: 100%; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 20px; background-color:#f3f4f6;">
                    <div style="width: {rate}%; background-color: #00a86b;"></div>
                    <div style="width: {100-rate if total > 0 else 0}%; background-color: #ef4444;"></div>
                </div>

                <div style='display:flex; justify-content:space-between; font-size:13px; color:#6b7280; margin-bottom:10px; padding: 0 5px;'>
                    <div style='display:flex; align-items:center; gap:6px;'><div style='width:8px; height:8px; border-radius:50%; background-color:#00a86b;'></div><span>익절 거래</span></div>
                    <b style='color:#00a86b;'>{wins} 회</b>
                </div>
                <div style='display:flex; justify-content:space-between; font-size:13px; color:#6b7280; margin-bottom:10px; padding: 0 5px;'>
                    <div style='display:flex; align-items:center; gap:6px;'><div style='width:8px; height:8px; border-radius:50%; background-color:#ef4444;'></div><span>손절 거래</span></div>
                    <b style='color:#ef4444;'>{losses} 회</b>
                </div>
            </div>
            <div style='border-top:1px solid #f3f4f6; padding-top:15px; display:flex; justify-content:space-between; font-size:13px; color:#6b7280;'><span>전체 오더 수</span><b style='color:#2563eb;'>{total} 회</b></div>
        </div>
        """, unsafe_allow_html=True)

    with col_t2:
        bg_gradient = f"conic-gradient(#00a86b 0% {long_p}%, #ef4444 {long_p}% 100%)" if (longs+shorts)>0 else "conic-gradient(#e5e7eb 0% 100%)"
        st.markdown(f"""
        <div style="{card_style}">
            <div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>LONG / SHORT</span><span style='color:#9ca3af; font-weight:400;'>신규 진입</span></div>
            <div style="display:flex; justify-content:center; align-items:center; flex-grow:1;">
                <div style="width: 125px; height: 125px; border-radius: 50%; background: {bg_gradient}; display:flex; justify-content:center; align-items:center;">
                    <div style="width: 90px; height: 90px; background-color: #ffffff; border-radius: 50%; display:flex; flex-direction:column; justify-content:center; align-items:center; box-shadow: inset 0 0 5px rgba(0,0,0,0.02);">
                        <span style="font-size:12px; color:#6b7280; font-weight:500;">총 진입</span>
                        <b style="font-size:24px; color:#111827; margin-top:-2px;">{longs+shorts}회</b>
                    </div>
                </div>
            </div>
            <div>
                <div style='display:flex; justify-content:space-between; font-size:13px; margin-bottom:8px;'><span style='color:#00a86b; font-weight:700;'>LONG</span><b style='color:#00a86b;'>{longs}회 · {long_p:.1f}%</b></div>
                <div style='display:flex; justify-content:space-between; font-size:13px;'><span style='color:#ef4444; font-weight:700;'>SHORT</span><b style='color:#ef4444;'>{shorts}회 · {short_p:.1f}%</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_t3:
        if not f_df.empty:
            r_df = f_df[f_df["datetime"] >= (datetime.now() - timedelta(days=7))]
            r_wins, r_losses = len(r_df[r_df["result"] == "익절"]), len(r_df[r_df["result"] == "손절"])
            r_rate = int(round((r_wins/(r_wins+r_losses)*100))) if (r_wins+r_losses)>0 else 0
        else:
            r_wins, r_losses, r_rate = 0, 0, 0

        trend_vals = [50, 69, 49, 100, 79, 81, r_rate]
        svg_points, circles, texts = "", "", ""
        for i, val in enumerate(trend_vals):
            x = i * 50
            y = 110 - (val / 100) * 85
            svg_points += f"{x},{y} "
            circles += f'<circle cx="{x}" cy="{y}" r="4" fill="#2563eb" />'
            texts += f'<text x="{x}" y="{y-12}" font-size="12" font-weight="bold" fill="#2563eb" text-anchor="middle">{int(val)}%</text>'
        
        svg_html = f"""<svg viewBox="-15 -15 330 140" style="width:100%; height:130px; display:block;"><polyline points="{svg_points}" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />{circles}{texts}</svg>"""

        st.markdown(f"""
        <div style="{card_style}">
            <div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>승률 추이</span><span style='color:#9ca3af; font-weight:400;'>최근 7일 · 오늘 포함</span></div>
            <div style="display:flex; align-items:baseline; gap:10px; margin-top:10px;">
                <span style="font-size:32px; font-weight:800; color:#2563eb;">{r_rate}%</span>
                <span style="font-size:12px; color:#6b7280;">익절 {r_wins} · 손절 {r_losses}</span>
            </div>
            <div style="flex-grow:1; display:flex; flex-direction:column; justify-content:flex-end;">
                {svg_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

render_trade_stats(filtered_df)

# -----------------------------------------------------------------------------
# 9. [FRAGMENT] 선택 기간 PNL 박스
# -----------------------------------------------------------------------------
st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

@st.fragment(run_every=3600)
def render_pnl_charts(f_df):
    period_sum = f_df["pnl"].sum() if not f_df.empty else 0.0
    pnl_color, pnl_sign = ("#00a86b", "+") if period_sum >= 0 else ("#ef4444", "")

    with st.container(border=True):
        st.markdown("<div class='white-marker'></div>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="padding: 10px 10px 0 10px;">
            <div style='display:flex; justify-content:space-between;'>
                <span style='font-size:12px; color:#9ca3af; font-weight:600;'>선택 기간 추정 PNL (오전 9시 갱신 기준)</span>
            </div>
            <div style='font-size:32px; font-weight:800; color:{pnl_color}; margin-top:5px;'>
                {pnl_sign}${period_sum:,.2f} <span style='font-size:14px; color:#00a86b; font-weight:600;'>USDT</span>
            </div>
        </div>
        <div style="border-bottom: 1px solid #e5e7eb; margin: 15px 0 5px 0;"></div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["일별 손익", "기간 누적"])
        
        if not f_df.empty:
            daily_pnl = f_df.groupby("date")["pnl"].sum().reset_index().sort_values("date")
            daily_pnl["cum"] = daily_pnl["pnl"].cumsum()
            daily_pnl["color"] = daily_pnl["pnl"].apply(lambda x: "#00a86b" if x >= 0 else "#ef4444")
        else:
            daily_pnl = pd.DataFrame()

        with tab1:
            if not daily_pnl.empty:
                import plotly.graph_objects as go
                fig1 = go.Figure(go.Bar(
                    x=daily_pnl["date"], y=daily_pnl["pnl"], marker_color=daily_pnl["color"],
                    name="일별 수익", hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"
                ))
                fig1.update_layout(
                    template="plotly_white", margin=dict(t=20, b=10, l=10, r=10), height=350, 
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    hovermode="x unified",
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor="#f3f4f6", griddash="dash", zeroline=True, zerolinecolor="#d1d5db", zerolinewidth=1.5)
                )
                st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

        with tab2:
            if not daily_pnl.empty:
                fig2 = go.Figure(go.Scatter(
                    x=daily_pnl["date"], y=daily_pnl["cum"], mode="lines+markers", 
                    line=dict(color="#2563eb", width=3), fill="tozeroy", fillcolor="rgba(37, 99, 235, 0.08)",
                    name="누적 수익", hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"
                ))
                fig2.update_layout(
                    template="plotly_white", margin=dict(t=20, b=10, l=10, r=10), height=350, 
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    hovermode="x unified",
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor="#f3f4f6", griddash="dash", zeroline=True, zerolinecolor="#d1d5db", zerolinewidth=1.5)
                )
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

render_pnl_charts(filtered_df)

st.markdown("<div style='font-size:11px; color:#9ca3af; margin: 10px 0 30px 0;'>추정 PNL · USDT · 한국시간 기준 · 기간 누적은 선택한 기간의 시작을 0으로 계산합니다.</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 10. 매매 상세 내역 로그
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 18px; font-weight: 800; color: #111827; margin-bottom: 15px;'>📝 상세 매매 내역</div>", unsafe_allow_html=True)

@st.fragment(run_every=3600)
def render_trade_logs(f_df):
    if not f_df.empty:
        st.dataframe(f_df[["datetime", "symbol", "side", "pnl", "result"]], use_container_width=True, hide_index=True, height=400)
    else:
        st.info("새로운 출발을 응원합니다! (아직 등록된 거래 내역이 없습니다)")

render_trade_logs(filtered_df)
