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

/* 🌟 새로고침 버튼 스타일 및 우측 정렬 */
div[class*="st-key-manual_refresh_main"] {
    display: flex !important;
    justify-content: flex-end !important;
}
div[class*="st-key-manual_refresh_main"] button {
    width: 36px !important; height: 36px !important; min-height: 36px !important; padding: 0 !important;
    border-radius: 12px !important; display: flex !important; align-items: center !important; justify-content: center !important;
    background-color: #ffffff !important; border: 1px solid rgba(15,23,42,0.08) !important;
    box-shadow: 0 2px 8px rgba(15,23,42,0.03) !important; transition: all 0.15s ease !important;
    margin-left: 0 !important;
}
div[class*="st-key-manual_refresh_main"] button:hover { border-color: #3182F6 !important; background-color: #F8FAFC !important; }

/* 🌟 "보유 포지션" 제목 + 새로고침 버튼 행 — 비트겟 배지와 오른쪽 라인 일치화 */
div[class*="st-key-pos_header_row"] [data-testid="stHorizontalBlock"] {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    gap: 0 !important;
    width: 100% !important;
}
div[class*="st-key-pos_header_row"] [data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    padding: 0 !important;
}
div[class*="st-key-pos_header_row"] [data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
    flex: 1 1 auto !important; min-width: 0 !important;
}
div[class*="st-key-pos_header_row"] [data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
    flex: 0 0 auto !important; width: auto !important; display: flex !important; justify-content: flex-end !important;
}

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
    border-radius: 999px;
