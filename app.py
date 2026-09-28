import ccxt
import time
from datetime import datetime, timedelta, timezone
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import random

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
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.white-marker),
    div[data-testid="stContainer"]:has(.white-marker),
    div[data-testid="stVerticalBlock"]:has(.white-marker) > div[style*="border"] {
        background-color: #ffffff !important; border: 1px solid #e5e7eb !important; border-radius: 12px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }
    .pos-box { padding: 10px; flex: 1 1 200px; }
    .pos-divider { border-left: 1px solid #f3f4f6; }
    @media (max-width: 768px) { .pos-divider { border-left: none !important; border-top: 1px solid #f3f4f6 !important; padding-top: 15px !important; margin-top: 5px !important; } }
    .stButton>button { height: 38px; padding: 0 8px; border-radius: 8px; border: 1px solid #d1d5db; background-color: #ffffff; color: #374151; font-weight: 500; white-space: nowrap; }
    .stButton>button:hover { border-color: #2563eb; color: #2563eb; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🔐 2. 보안 게이트 (누구나 내 포지션을 보지 못하게 막음!)
# =============================================================================
st.sidebar.title("🔐 보안 설정")
# secrets.toml에 ADMIN_PWD = "내비밀번호" 형태로 저장하세요. 없으면 기본값 1234
ADMIN_PWD = st.secrets.get("ADMIN_PWD", "1313")
user_pwd = st.sidebar.text_input("대시보드 암호", type="password")

if user_pwd != ADMIN_PWD:
    st.warning("🚨 권한이 없습니다. 올바른 비밀번호를 입력해주세요.")
    st.stop() # 비밀번호가 틀리면 여기서 화면 렌더링 멈춤!

# 🎯 [초기화 설정] 여기서 설정한 날짜 이전의 과거 데이터는 싹 다 날립니다!
DASHBOARD_START_DATE = "2026-09-28"

# -----------------------------------------------------------------------------
# 3. 데이터 로드 헬퍼 함수 및 API 분리 세팅
# -----------------------------------------------------------------------------
def get_api_keys(exc_name):
    """거래소별로 독립적인 API 키를 가져옵니다."""
    prefix = exc_name.upper().replace(" ", "_")
    return (
        st.secrets.get(f"{prefix}_API_KEY", ""),
        st.secrets.get(f"{prefix}_SECRET_KEY", ""),
        st.secrets.get(f"{prefix}_PASSPHRASE", "")
    )

def safe_float(val):
    """None, 빈 문자열로 인해 크래시(에러)가 나는 것을 방지하는 안전망"""
    if val is None or val == "": return 0.0
    try: return float(val)
    except: return 0.0

# KST(한국 시간) 설정을 통일하여 시간대 불일치 버그 방지
KST = timezone(timedelta(hours=9))

# -----------------------------------------------------------------------------
# 4. 캐싱된 API 데이터 로드 (에러 캐싱 방지 & 로직 최적화)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=5, show_spinner=False)
def fetch_fast_data(exchange_name, api_key, secret, pwd):
    if not api_key or not secret or exchange_name == "Demo":
        return [], 0.0
    
    # 캐시 함수 내에서 try-except를 빼서, 에러가 나면 캐시하지 않도록 함 (에러 고착 방지)
    if exchange_name == "Bitget": exchange = ccxt.bitget({'apiKey': api_key, 'secret': secret, 'password': pwd, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
    elif exchange_name == "Binance": exchange = ccxt.binance({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'future'}})
    elif exchange_name == "Bybit": exchange = ccxt.bybit({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'linear'}})
    
    bal = exchange.fetch_balance({'type': 'swap'}) if exchange_name == "Bitget" else exchange.fetch_balance()
    total_balance = safe_float(bal.get('USDT', {}).get('total', 0))
    
    active_positions = [] 
    for p in exchange.fetch_positions():
        if safe_float(p.get("contracts", 0)) > 0:
            pos_side = p.get("side", "LONG").upper()
            entry = safe_float(p.get("entryPrice"))
            mark = safe_float(p.get("markPrice"))
            size = safe_float(p.get("contracts"))
            margin = safe_float(p.get("initialMargin"))
            # 거래소에서 주는 미실현손익 값을 직접 가져오고, 없으면 계산
            unreal_pnl = safe_float(p.get("unrealizedPnl") or p.get("info", {}).get("unrealizedPnl"))
            if unreal_pnl == 0.0:
                unreal_pnl = (mark - entry) * size if pos_side == "LONG" else (entry - mark) * size
                
            roe = (unreal_pnl / margin * 100) if margin > 0 else 0
            # liquidationPrice가 None일 때 터지는 버그 완벽 수정 (safe_float 활용)
            active_positions.append({
                "symbol": p.get("symbol", "").replace(":USDT", ""), "side": pos_side, "leverage": int(p.get("leverage", 1)),
                "entry_price": entry, "mark_price": mark, "size": size, "margin": margin,
                "liq_price": safe_float(p.get("liquidationPrice")), "unrealized_pnl": unreal_pnl, "roe": roe,
            })
    return active_positions, total_balance

@st.cache_data(ttl=3600, show_spinner="거래내역 및 시장 데이터를 동기화 중입니다...")
def fetch_slow_data(exchange_name, api_key, secret, pwd):
    if not api_key or not secret or exchange_name == "Demo":
        records = []
        today_kst = datetime.now(KST)
        for _ in range(40): 
            t_kst = today_kst - timedelta(hours=random.randint(1, 48))
            pnl = random.choice([0, 0, random.uniform(100, 2500), random.uniform(-1500, -50)])
            records.append({
                "order_id": f"DEMO_{random.randint(1000,9999)}",
                "datetime": t_kst, "date": t_kst.strftime("%Y-%m-%d"),
                "symbol": random.choice(["BTC/USDT", "ETH/USDT", "SOL/USDT"]),
                "side": random.choice(["LONG", "SHORT"]),
                "pnl": round(pnl, 2)
            })
        df = pd.DataFrame(records).sort_values("datetime", ascending=False)
        return df[df["date"] >= DASHBOARD_START_DATE]
    
    if exchange_name == "Bitget": exchange = ccxt.bitget({'apiKey': api_key, 'secret': secret, 'password': pwd, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
    elif exchange_name == "Binance": exchange = ccxt.binance({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'future'}})
    elif exchange_name == "Bybit": exchange = ccxt.bybit({'apiKey': api_key, 'secret': secret, 'enableRateLimit': True, 'options': {'defaultType': 'linear'}})
    
    markets = exchange.load_markets()
    # 활성화된 선물/스왑 마켓 심볼만 동적으로 수집 (하드코딩 제거)
    active_symbols = [s for s in markets.keys() if markets[s].get('swap') or markets[s].get('future')]
    
    since_ts = int(datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
    trade_records = []
    
    for sym in active_symbols[:20]: # 속도 제한을 위해 최대 20개 종목만 순회
        try:
            trades = exchange.fetch_my_trades(symbol=sym, since=since_ts, limit=500)
            for t in trades:
                t_utc = datetime.fromtimestamp(t["timestamp"] / 1000, tz=timezone.utc)
                t_kst = t_utc.astimezone(KST)
                
                info = t.get("info", {})
                fee = safe_float(t.get("fee", {}).get("cost", 0))
                # 바이낸스/바이비트/비트겟 통합 호환 PNL 추출 및 수수료 차감
                raw_pnl = safe_float(info.get("profit") or info.get("realizedPnl") or info.get("closedPnl") or 0)
                net_pnl = raw_pnl - fee if raw_pnl != 0 else 0 
                
                info_side = str(info.get("tradeSide", "")).lower()
                mapped_side = "LONG" if "long" in info_side else ("SHORT" if "short" in info_side else ("LONG" if t["side"].upper() == "BUY" else "SHORT"))
                
                trade_records.append({
                    "order_id": t.get("order") or t.get("id"), # 분할 체결 병합을 위한 ID
                    "datetime": t_kst, "date": t_kst.strftime("%Y-%m-%d"),
                    "symbol": t["symbol"].replace(":USDT", ""), "side": mapped_side, 
                    "pnl": net_pnl
                })
        except: continue
        
    df = pd.DataFrame(trade_records)
    if not df.empty:
        # 분할 체결(하나의 오더가 여러 번 쪼개짐)로 인한 승률 뻥튀기 방지를 위해 order_id 기준으로 합산
        df = df.groupby(["order_id", "symbol", "side", "date"]).agg({"pnl": "sum", "datetime": "last"}).reset_index()
        # 합산된 최종 PNL을 기준으로 결과를 도출
        df["result"] = df["pnl"].apply(lambda p: "익절" if p > 0.001 else ("손절" if p < -0.001 else "진입"))
        df = df.sort_values("datetime", ascending=False)
        df = df[df["date"] >= DASHBOARD_START_DATE]
        
    return df if not df.empty else pd.DataFrame(columns=["datetime", "date", "symbol", "side", "pnl", "result"])

# -----------------------------------------------------------------------------
# 5. 사이드바 세팅
# -----------------------------------------------------------------------------
exchange_choice = st.sidebar.selectbox("거래소 선택", ["Bitget", "Binance", "Bybit", "Demo"])
API_KEY, SECRET_KEY, PASSPHRASE = get_api_keys(exchange_choice)

if API_KEY and SECRET_KEY:
    st.sidebar.markdown("<div style='font-size:13px; color:#00a86b; margin-bottom:15px;'>✅ API 연동 완료</div>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<div style='font-size:13px; color:#ef4444; margin-bottom:15px;'>⚠️ API 미등록 (Demo 모드)</div>", unsafe_allow_html=True)

if st.sidebar.button("🔄 수동 새로고침"):
    fetch_fast_data.clear()
    fetch_slow_data.clear()
    st.rerun()

# 에러가 발생해도 사이트가 멈추지 않도록 밖에서 예외 처리 (에러 캐싱 방지)
try:
    df_trades = fetch_slow_data(exchange_choice, API_KEY, SECRET_KEY, PASSPHRASE)
except Exception as e:
    st.error(f"데이터를 불러오는 중 문제가 발생했습니다: {e}")
    df_trades = pd.DataFrame(columns=["datetime", "date", "symbol", "side", "pnl", "result"])

# -----------------------------------------------------------------------------
# 6. 🎯 메인 타이틀
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
# 7. [FRAGMENT] 🎯 현재 보유 포지션 (10초만 갱신!)
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 16px; font-weight: 800; color: #111827; margin-bottom: 10px;'>🎯 현재 보유 포지션</div>", unsafe_allow_html=True)

@st.fragment(run_every=10)
def show_live_positions():
    try:
        current_positions, wallet_balance = fetch_fast_data(exchange_choice, API_KEY, SECRET_KEY, PASSPHRASE)
    except:
        current_positions, wallet_balance = [], 0.0
        
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
# 8. 상단 PNL 카드 (Fragment는 실시간 PNL에만 적용하여 꼬임 방지)
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 11px; color: #9ca3af; margin-bottom: 10px; margin-top: -10px;'>미실현손익은 일별·월별 추정 PNL 합계에 포함하지 않습니다.</div>", unsafe_allow_html=True)
col_s1, col_s2, col_s3 = st.columns(3)

def make_top_card(title, value, sub_left):
    val_color, sign = ("#00a86b", "+") if value >= 0 else ("#ef4444", "")
    return f"""<div style="background-color:#ffffff; border:1px solid #e5e7eb; border-radius:12px; padding:24px; min-height: 155px; display:flex; flex-direction:column; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
        <div><div style="display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;"><span>{title}</span></div>
        <div style="font-size:32px; font-weight:800; color:{val_color}; margin:15px 0;">{sign}${value:,.2f} <span style="font-size:14px; font-weight:600; color:#00a86b;">USDT</span></div></div>
        <div style="font-size:12px; color:#9ca3af; margin-top:auto;">{sub_left}</div></div>"""

with col_s1:
    today_str = datetime.now(KST).strftime("%Y-%m-%d")
    today_pnl = df_trades[df_trades["date"] == today_str]["pnl"].sum() if not df_trades.empty else 0.0
    st.markdown(make_top_card("오늘 추정 PNL", today_pnl, "매일 오전 0시 리셋 (KST)"), unsafe_allow_html=True)

with col_s2:
    month_str = datetime.now(KST).strftime("%Y-%m")
    month_pnl = df_trades[df_trades["date"].str.startswith(month_str)]["pnl"].sum() if not df_trades.empty else 0.0
    st.markdown(make_top_card("이번 달 추정 PNL", month_pnl, "매월 1일 리셋 (KST)"), unsafe_allow_html=True)

with col_s3:
    @st.fragment(run_every=10)
    def render_unrealized_pnl():
        try: pos, bal = fetch_fast_data(exchange_choice, API_KEY, SECRET_KEY, PASSPHRASE)
        except: pos = []
        unrealized = sum([p.get("unrealized_pnl", 0.0) for p in pos]) if pos else 0.0
        st.markdown(make_top_card("현재 미실현손익", unrealized, "전체 포지션의 미실현손익 합계"), unsafe_allow_html=True)
    render_unrealized_pnl()

st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 9. 수익 히스토리 필터 (Session State 활용하여 버튼 버그 픽스)
# -----------------------------------------------------------------------------
st.markdown("<div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:10px;'><span style='font-size:20px; font-weight:800; color:#111827;'>수익 히스토리</span></div>", unsafe_allow_html=True)

if "filter_sd" not in st.session_state:
    if not df_trades.empty and "date" in df_trades.columns:
        st.session_state.filter_sd = pd.to_datetime(df_trades["date"]).dt.date.min()
    else:
        st.session_state.filter_sd = datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").date()
if "filter_ed" not in st.session_state:
    st.session_state.filter_ed = datetime.now(KST).date()

c_d1, c_d2, c_btn1, c_btn2, c_btn3, c_space = st.columns([1.5, 1.5, 0.8, 0.9, 1.1, 5.5])
with c_btn1:
    if st.button("오늘", use_container_width=True):
        st.session_state.filter_sd = datetime.now(KST).date()
        st.session_state.filter_ed = datetime.now(KST).date()
with c_btn2:
    if st.button("이번 달", use_container_width=True):
        st.session_state.filter_sd = datetime.now(KST).date().replace(day=1)
        st.session_state.filter_ed = datetime.now(KST).date()
with c_btn3:
    if st.button("최근 30일", use_container_width=True):
        st.session_state.filter_sd = datetime.now(KST).date() - timedelta(days=30)
        st.session_state.filter_ed = datetime.now(KST).date()

with c_d1:
    start_date = st.date_input("s", value=st.session_state.filter_sd, label_visibility="collapsed")
with c_d2:
    end_date = st.date_input("e", value=st.session_state.filter_ed, label_visibility="collapsed")

filter_start_date = max(start_date, datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").date())
if not df_trades.empty:
    df_trades["date_obj"] = pd.to_datetime(df_trades["date"]).dt.date
    filtered_df = df_trades[(df_trades["date_obj"] >= filter_start_date) & (df_trades["date_obj"] <= end_date)]
else:
    filtered_df = df_trades

# -----------------------------------------------------------------------------
# 10. 매매 동향
# -----------------------------------------------------------------------------
st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
st.markdown("<div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:10px;'><span style='font-size:16px; font-weight:800; color:#111827; margin-left:5px;'>매매 동향</span><span style='font-size:12px; color:#9ca3af;'>관측 기록 기준</span></div>", unsafe_allow_html=True)

col_t1, col_t2, col_t3 = st.columns([1, 1, 1.2])

total = len(filtered_df)
wins = len(filtered_df[filtered_df["result"] == "익절"]) if total > 0 else 0
losses = len(filtered_df[filtered_df["result"] == "손절"]) if total > 0 else 0
entries = len(filtered_df[filtered_df["result"] == "진입"]) if total > 0 else 0

closed_trades = wins + losses
rate = (wins / closed_trades * 100) if closed_trades > 0 else 0

longs = len(filtered_df[filtered_df["side"] == "LONG"]) if total > 0 else 0
shorts = len(filtered_df[filtered_df["side"] == "SHORT"]) if total > 0 else 0
long_p = (longs/(longs+shorts)*100) if (longs+shorts)>0 else 0
short_p = (shorts/(longs+shorts)*100) if (longs+shorts)>0 else 0

card_style = "background-color:#ffffff; border:1px solid #e5e7eb; border-radius:12px; padding:20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); height: 320px; display:flex; flex-direction:column; justify-content:space-between;"

with col_t1:
    st.markdown(f"""<div style="{card_style}"><div><div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>총 체결 건수 (분할병합 기준)</span><span style='color:#9ca3af; font-weight:400;'>선택 기간</span></div><div style='font-size:36px; font-weight:800; color:#111827; margin:15px 0;'>{total} <span style='font-size:14px; font-weight:500;'>건</span></div><div style='font-size:12px; color:#6b7280; margin-bottom:5px; display:flex; justify-content:space-between;'><span>승·패 비율 (청산 기준)</span><b style='color:#111827;'>{rate:.1f}% 승률</b></div><div style="display:flex; width: 100%; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 20px; background-color:#f3f4f6;"><div style="width: {rate}%; background-color: #00a86b;"></div><div style="width: {100-rate if closed_trades > 0 else 0}%; background-color: #ef4444;"></div></div><div style='display:flex; justify-content:space-between; font-size:13px; color:#6b7280; margin-bottom:10px; padding: 0 5px;'><div style='display:flex; align-items:center; gap:6px;'><div style='width:8px; height:8px; border-radius:50%; background-color:#00a86b;'></div><span>익절 청산</span></div><b style='color:#00a86b;'>{wins} 건</b></div><div style='display:flex; justify-content:space-between; font-size:13px; color:#6b7280; margin-bottom:10px; padding: 0 5px;'><div style='display:flex; align-items:center; gap:6px;'><div style='width:8px; height:8px; border-radius:50%; background-color:#ef4444;'></div><span>손절 청산</span></div><b style='color:#ef4444;'>{losses} 건</b></div></div><div style='border-top:1px solid #f3f4f6; padding-top:15px; display:flex; justify-content:space-between; font-size:13px; color:#6b7280;'><span>신규 진입 (단순 오더)</span><b style='color:#2563eb;'>{entries} 건</b></div></div>""", unsafe_allow_html=True)

with col_t2:
    bg_gradient = f"conic-gradient(#00a86b 0% {long_p}%, #ef4444 {long_p}% 100%)" if (longs+shorts)>0 else "conic-gradient(#e5e7eb 0% 100%)"
    st.markdown(f"""
    <div style="{card_style}">
        <div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>LONG / SHORT</span><span style='color:#9ca3af; font-weight:400;'>총 진입/청산</span></div>
        <div style="display:flex; justify-content:center; align-items:center; flex-grow:1;">
            <div style="width: 125px; height: 125px; border-radius: 50%; background: {bg_gradient}; display:flex; justify-content:center; align-items:center;">
                <div style="width: 90px; height: 90px; background-color: #ffffff; border-radius: 50%; display:flex; flex-direction:column; justify-content:center; align-items:center; box-shadow: inset 0 0 5px rgba(0,0,0,0.02);">
                    <span style="font-size:12px; color:#6b7280; font-weight:500;">총 체결</span>
                    <b style="font-size:24px; color:#111827; margin-top:-2px;">{longs+shorts}건</b>
                </div>
            </div>
        </div>
        <div>
            <div style='display:flex; justify-content:space-between; font-size:13px; margin-bottom:8px;'><span style='color:#00a86b; font-weight:700;'>LONG</span><b style='color:#00a86b;'>{longs}건 · {long_p:.1f}%</b></div>
            <div style='display:flex; justify-content:space-between; font-size:13px;'><span style='color:#ef4444; font-weight:700;'>SHORT</span><b style='color:#ef4444;'>{shorts}건 · {short_p:.1f}%</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_t3:
    # ★ 가짜 데이터 하드코딩 제거: 진짜 7일간의 날짜별 승률 데이터 추출
    trend_vals = []
    now_kst = datetime.now(KST)
    for i in range(6, -1, -1):
        target_date = (now_kst - timedelta(days=i)).strftime("%Y-%m-%d")
        if not df_trades.empty:
            day_df = df_trades[df_trades["date"] == target_date]
            d_w = len(day_df[day_df["result"] == "익절"])
            d_l = len(day_df[day_df["result"] == "손절"])
            trend_vals.append(int(round(d_w / (d_w + d_l) * 100)) if (d_w + d_l) > 0 else 0)
        else:
            trend_vals.append(0)

    svg_points, circles, texts = "", "", ""
    for i, val in enumerate(trend_vals):
        x = i * 50
        y = 110 - (val / 100) * 85
        svg_points += f"{x},{y} "
        circles += f'<circle cx="{x}" cy="{y}" r="4" fill="#2563eb" />'
        texts += f'<text x="{x}" y="{y-12}" font-size="12" font-weight="bold" fill="#2563eb" text-anchor="middle">{int(val)}%</text>'
    
    svg_html = f"""<svg viewBox="-15 -15 330 140" style="width:100%; height:130px; display:block;"><polyline points="{svg_points}" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />{circles}{texts}</svg>"""

    st.markdown(f"""<div style="{card_style}"><div style='display:flex; justify-content:space-between; font-size:13px; font-weight:600; color:#111827;'><span>승률 추이</span><span style='color:#9ca3af; font-weight:400;'>최근 7일 · 오늘 포함</span></div><div style="display:flex; align-items:baseline; gap:10px; margin-top:10px;"><span style="font-size:32px; font-weight:800; color:#2563eb;">{trend_vals[-1]}%</span><span style="font-size:12px; color:#6b7280;">오늘의 승률</span></div><div style="flex-grow:1; display:flex; flex-direction:column; justify-content:flex-end;">{svg_html}</div></div>""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 11. 선택 기간 PNL 박스
# -----------------------------------------------------------------------------
st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

period_sum = filtered_df["pnl"].sum() if not filtered_df.empty else 0.0
pnl_color, pnl_sign = ("#00a86b", "+") if period_sum >= 0 else ("#ef4444", "")

with st.container(border=True):
    st.markdown("<div class='white-marker'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="padding: 10px 10px 0 10px;">
        <div style='display:flex; justify-content:space-between;'>
            <span style='font-size:12px; color:#9ca3af; font-weight:600;'>선택 기간 실현 PNL (KST 기준)</span>
        </div>
        <div style='font-size:32px; font-weight:800; color:{pnl_color}; margin-top:5px;'>
            {pnl_sign}${period_sum:,.2f} <span style='font-size:14px; color:#00a86b; font-weight:600;'>USDT</span>
        </div>
    </div>
    <div style="border-bottom: 1px solid #e5e7eb; margin: 15px 0 5px 0;"></div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["일별 손익", "기간 누적"])
    
    if not filtered_df.empty:
        daily_pnl = filtered_df.groupby("date")["pnl"].sum().reset_index().sort_values("date")
        daily_pnl["cum"] = daily_pnl["pnl"].cumsum()
        daily_pnl["color"] = daily_pnl["pnl"].apply(lambda x: "#00a86b" if x >= 0 else "#ef4444")
    else:
        daily_pnl = pd.DataFrame()

    with tab1:
        if not daily_pnl.empty:
            fig1 = go.Figure(go.Bar(
                x=daily_pnl["date"], y=daily_pnl["pnl"], marker_color=daily_pnl["color"],
                name="일별 수익", hovertemplate="<b>%{x}</b><br>%{y:,.2f} USDT<extra></extra>"
            ))
            fig1.update_layout(
                template="plotly_white", margin=dict(t=20, b=10, l=10, r=10), height=350, 
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
                xaxis=dict(showgrid=False, zeroline=False, type='category'),
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
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
                xaxis=dict(showgrid=False, zeroline=False, type='category'),
                yaxis=dict(showgrid=True, gridcolor="#f3f4f6", griddash="dash", zeroline=True, zerolinecolor="#d1d5db", zerolinewidth=1.5)
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='font-size:11px; color:#9ca3af; margin: 10px 0 30px 0;'>추정 PNL · USDT · 수수료가 차감된 순수 실현 수익입니다.</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 12. 매매 상세 내역 로그
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 18px; font-weight: 800; color: #111827; margin-bottom: 15px;'>📝 상세 매매 내역</div>", unsafe_allow_html=True)

if not filtered_df.empty:
    st.dataframe(filtered_df[["datetime", "symbol", "side", "pnl", "result", "order_id"]], use_container_width=True, hide_index=True, height=400)
else:
    st.info("새로운 출발을 응원합니다! (아직 등록된 거래 내역이 없습니다)")
