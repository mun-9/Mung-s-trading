"""공통 디자인: 색상, CSS, 작은 HTML 컴포넌트."""
import streamlit as st

GREEN, RED, BLUE, GRAY = "#089981", "#F04452", "#3182F6", "#8B95A1"
TEXT, SUB, DIVIDER = "#191F28", "#8B95A1", "#F2F4F6"
LINE_COLOR = "#D1D6DB"
GREEN_SOFT, RED_SOFT, BLUE_SOFT = "rgba(8,153,129,0.10)", "rgba(240,68,82,0.10)", "rgba(49,130,246,0.10)"
GRAY_SOFT = "rgba(139,149,161,0.12)"


def money(v, sign=True, digits=2):
    if v is None:
        return "-"
    s = f"${abs(v):,.{digits}f}"
    if not sign:
        return s if v >= 0 else f"-{s}"
    return f"+{s}" if v > 0 else (f"-{s}" if v < 0 else s)


def pnl_color(v):
    return GREEN if v > 0 else (RED if v < 0 else SUB)


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def section(title, sub=""):
    sub_html = f"<span class='sec-sub'>{sub}</span>" if sub else ""
    html(f"<div class='sec-title'>{title}{sub_html}</div>")


def kpi(label, value, color=TEXT, sub=""):
    sub_html = f"<div class='kpi-sub'>{sub}</div>" if sub else ""
    return (f"<div class='kpi'><div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value' style='color:{color};'>{value}</div>{sub_html}</div>")


def inject_css():
    html("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

html, body, .stApp { background-color: #F2F4F6 !important; }
.stApp, .stApp p, .stApp div, .stApp label, .stApp button, .stApp span:not([class*='material']):not([data-testid='stIconMaterial']) { font-family:'Pretendard',-apple-system,BlinkMacSystemFont,sans-serif; letter-spacing:-0.01em; }
.block-container { padding-top: 0 !important; max-width: 1240px; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stMain"] { overflow-x: hidden; }
/* <style>만 들어있는 빈 요소가 차지하는 여백 제거 */
div[data-testid="stElementContainer"]:has(div[data-testid="stMarkdownContainer"] > style:only-child) { display: none !important; }
[data-testid="stToolbarActions"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"] { display: none !important; }

/* 칸(column) 안의 카드가 아래 카드와 겹치지 않게 */
div[data-testid="stColumn"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
/* 분봉·종류 선택 버튼: 한 줄 유지 */
div[data-testid="stButtonGroup"] div[role="radiogroup"] { flex-wrap: nowrap !important; overflow-x: auto; scrollbar-width: none; max-width: 100%; }
div[data-testid="stButtonGroup"] div[role="radiogroup"]::-webkit-scrollbar { display: none; }
div[data-testid="stButtonGroup"] button { white-space: nowrap !important; flex-shrink: 0; }
div[data-testid="stElementContainer"]:has(> div[data-testid="stButtonGroup"]) { max-width: 100%; }

/* 휴대폰: 차트 위에서도 페이지 스크롤이 되게 */
.js-plotly-plot .nsewdrag, .js-plotly-plot .draglayer, .js-plotly-plot .main-svg { touch-action: pan-y !important; }

/* 새로고침 중 회색으로 흐려지는 효과 끄기 */
div[data-stale="true"], [data-stale="true"] { opacity: 1 !important; transition: none !important; filter: none !important; }

/* 상단 헤더 (전체 폭, 스크롤해도 위에 고정) */
div[class*="st-key-topnav_"] {
    position: sticky; top: 0; z-index: 999; height: 72px; gap: 30px !important;
    margin-left: calc(50% - 50vw) !important; margin-right: calc(50% - 50vw) !important;
    width: 100vw !important; max-width: none !important; min-width: 100vw !important; flex: none !important;
    padding: 0 max(80px, calc(50vw - 540px)) !important;
    background: rgba(255,255,255,0.93); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid #E7EBF1; margin-bottom: 0;
}
div[class*="st-key-topnav_dark"] { background: #0F121A; border-bottom-color: #1E222D; margin-bottom: 8px; padding: 0 14px !important; height: 50px; }
div[class*="st-key-topnav_dark"] .nav-logo .word { font-size: 17px; }
div[class*="st-key-topnav_"] [data-testid="stMarkdownContainer"] { margin: 0 !important; }
.nav-logo { display: flex; align-items: center; gap: 9px; margin: 0; white-space: nowrap; }
.nav-logo { gap: 8px !important; }
.nav-logo .word { font-size: 20px; font-weight: 800; color: #172033; letter-spacing: -0.6px; }
.nav-logo .tag { font-size: 11px; font-weight: 700; color: #2459ED; background: rgba(36,89,237,0.08); padding: 3px 7px; border-radius: 6px; letter-spacing: 0.2px; }
div[class*="st-key-topnav_dark"] .nav-logo .tag { background: rgba(41,98,255,0.18); color: #7FA3FF; }
div[class*="st-key-topnav_dark"] .nav-logo .word { color: #D1D4DC; }
div[class*="st-key-navlink_"] a { padding: 8px 4px !important; min-height: 0 !important; background: transparent !important; border-radius: 0 !important; }
div[class*="st-key-navlink_"] a p, div[class*="st-key-navlink_"] a span { font-size: 15px !important; font-weight: 600 !important; color: #172033 !important; }
div[class*="st-key-navlink_"] a:hover p { color: #2459ED !important; }
div[class*="st-key-navlink_"][class*="_on"] a p { color: #2459ED !important; font-weight: 750 !important; }
div[class*="st-key-topnav_dark"] div[class*="st-key-navlink_"] a p { color: #9598A1 !important; }
div[class*="st-key-topnav_dark"] div[class*="st-key-navlink_"][class*="_on"] a p { color: #FFFFFF !important; }
div[class*="st-key-topnav_dark"] div[class*="st-key-navlink_"] a:hover p { color: #FFFFFF !important; }

/* 섹션 제목 줄 (보유 포지션 + 배지 + 새로고침) */
div[class*="st-key-page_head"] { margin: -4px 0 2px; min-height: 40px; }
div[class*="st-key-page_head"] [data-testid="stElementContainer"], div[class*="st-key-page_head"] [data-testid="stMarkdownContainer"] { margin: 0 !important; }
div[class*="st-key-page_head"] .ph-title { line-height: 36px; }
div[class*="st-key-page_head"] p { margin: 0 !important; line-height: 0; }
div[class*="st-key-page_head"] [data-testid="stMarkdown"] { display: flex; align-items: center; }
div[class*="st-key-pnl_head"] { justify-content: space-between !important; }
div[class*="st-key-pnl_view_box"] { margin-left: auto !important; }
div[class*="st-key-page_head"] > div:last-child { gap: 8px !important; align-items: center !important; }
div[class*="st-key-page_head"] > div:last-child { margin-left: auto !important; }
.ph-title { font-size: 24px; font-weight: 800; color: #191F28; letter-spacing: -0.03em; }
div[class*="st-key-refresh_btn"] button { width: 36px !important; height: 36px !important; min-height: 36px !important; padding: 0 !important; border-radius: 12px !important; box-shadow: 0 2px 8px rgba(15,23,42,0.03);
    background: #fff !important; border: 1px solid rgba(15,23,42,0.08) !important; }
div[class*="st-key-refresh_btn"] button:hover { border-color: #2459ED !important; }
div[class*="st-key-refresh_btn"] button span { color: #172033 !important; }

.sec-title { font-size: 19px; font-weight: 800; color: #191F28; margin: 30px 0 14px; display:flex; align-items:baseline; gap:10px; }
.sec-sub { font-size: 12.5px; font-weight: 500; color: #8B95A1; }

.card { background:#ffffff; border-radius:20px; box-shadow:0 2px 14px rgba(15,23,42,0.05); padding:22px 24px; }
.card-title { display:flex; justify-content:space-between; align-items:baseline; gap:10px; font-size:17px; font-weight:800; color:#191F28; letter-spacing:-0.02em; }
.card-title span:last-child { color:#8B95A1; font-weight:500; font-size:12.5px; letter-spacing:0; }

.kpi-grid { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 0; }
.kpi { padding: 14px 16px; border-left: 1px solid #F2F4F6; }
.kpi:nth-child(4n+1) { border-left: none; padding-left: 0; }
.kpi-label { font-size: 12.5px; color:#8B95A1; font-weight:600; margin-bottom: 8px; }
.kpi-value { font-size: 21px; font-weight: 800; letter-spacing:-0.02em; }
.kpi-sub { font-size: 11.5px; color:#8B95A1; margin-top: 4px; }

.pt-grid { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 12px; margin-top: 16px; }
.pt { background: #F7F8FA; border-radius: 16px; padding: 18px 18px 16px; display: flex; flex-direction: column; gap: 10px; min-height: 176px; }
.pt-label { font-size: 14px; font-weight: 700; color: #4E5968; }
.pt-value { font-size: 30px; font-weight: 800; color: #191F28; letter-spacing: -0.03em; line-height: 1.1; }
.pt-unit { font-size: 15px; font-weight: 700; color: #8B95A1; margin-left: 3px; }
.pt-foot { display: flex; justify-content: space-between; gap: 8px; font-size: 12.5px; color: #8B95A1; margin-top: auto; }
.gauge { position: relative; height: 8px; background: #E5E8EB; border-radius: 4px; overflow: visible; margin-top: auto; }
.gauge-fill { height: 100%; border-radius: 4px; }
.gauge-mark { position: absolute; top: -3px; width: 2px; height: 14px; background: #191F28; opacity: .35; border-radius: 1px; }
.bar-row { display: grid; grid-template-columns: 62px 1fr auto; align-items: center; gap: 8px; font-size: 13px; color: #6B7684; }
.bar-row b { font-size: 13.5px; font-weight: 700; }
.bar { height: 8px; background: #E5E8EB; border-radius: 4px; overflow: hidden; }
.bar > div { height: 100%; border-radius: 4px; }
.streak { display: flex; gap: 5px; flex-wrap: wrap; margin-top: auto; }
.streak .sd { width: 14px; height: 14px; border-radius: 4px; }
.bd-chips { display: flex; flex-wrap: wrap; gap: 6px 16px; margin-top: 10px; font-size: 12.5px; color: #8B95A1; }
.bd-chips b { font-weight: 700; margin-left: 2px; }

.acct { display:grid; grid-template-columns: 1fr 1fr; gap: 28px; align-items:center; }
.acct-r /* 상단 PNL 카드 */
.topc { min-height: 132px; display:flex; flex-direction:column; justify-content:center; padding: 20px 24px !important; }
.topc-h { display:flex; justify-content:space-between; align-items:center; gap:10px; }
.topc-t { font-size:15px; font-weight:800; color:#4E5968; letter-spacing:-0.01em; }
.topc-chip { font-size:12px; font-weight:600; color:#6B7684; background:#F2F4F6; padding:4px 10px; border-radius:999px; white-space:nowrap; }
.topc-v { font-size:32px; font-weight:800; letter-spacing:-0.03em; margin-top:12px; line-height:1.1; }
.topc-k { font-size:14px; font-weight:600; color:#8B95A1; margin-top:4px; }

/* 기간 선택 줄 */
div[class*="st-key-range_row"] { flex-wrap: wrap !important; row-gap: 8px !important; }
div[class*="st-key-range_date"] { width: 300px !important; max-width: 100%; }
div[class*="st-key-range_date"] [data-baseweb="input"] { height: 42px; border-radius: 12px !important; border: 1px solid rgba(15,23,42,0.07) !important; background: #fff !important; box-shadow: 0 2px 8px rgba(15,23,42,0.03); }
div[class*="st-key-range_date"] [data-baseweb="input"] > div { background: #fff !important; }
div[class*="st-key-range_date"] input { font-weight: 600 !important; color: #191F28 !important; }
div[class*="st-key-range_row"] div[role="radiogroup"], div[class*="st-key-pnl_view_box"] div[role="radiogroup"] {
  background:#fff; border-radius:12px; padding:4px; gap:2px !important; border:1px solid rgba(15,23,42,0.07); box-shadow:0 2px 8px rgba(15,23,42,0.03); }
div[class*="st-key-pnl_view_box"] div[role="radiogroup"] { background:#F2F4F6; border:0; box-shadow:none; }
div[class*="st-key-range_row"] button[data-variant="segmented_control"], div[class*="st-key-pnl_view_box"] button[data-variant="segmented_control"] {
  border:0 !important; background:transparent !important; border-radius:9px !important; min-height:32px !important; height:32px; padding:0 14px !important; box-shadow:none !important; }
div[class*="st-key-range_row"] button[data-variant="segmented_control"] p, div[class*="st-key-pnl_view_box"] button[data-variant="segmented_control"] p { font-size:13.5px !important; font-weight:600 !important; color:#6B7684 !important; }
div[class*="st-key-range_row"] button[aria-checked="true"] { background:#EEF3FF !important; }
div[class*="st-key-range_row"] button[aria-checked="true"] p { color:#2459ED !important; font-weight:800 !important; }
div[class*="st-key-pnl_view_box"] button[aria-checked="true"] { background:#fff !important; box-shadow:0 1px 4px rgba(15,23,42,0.08) !important; }
div[class*="st-key-pnl_view_box"] button[aria-checked="true"] p { color:#191F28 !important; font-weight:800 !important; }
div[class*="st-key-pnl_card"] > div:first-child { justify-content: space-between !important; }
@media (max-width: 768px) {
  div[class*="st-key-range_date"] { width: 100% !important; }
  .topc { min-height: 0; }
  .topc-v { font-size: 28px; }
}

.bd-row { padding: 8px 0; font-size: 13.5px; }
@media (max-width: 768px) { .acct { grid-template-columns: 1fr; gap: 10px; } }

.bd-row { display:flex; justify-content:space-between; align-items:center; padding: 11px 0; font-size: 14px; border-bottom: 1px solid #F2F4F6; }
.bd-row span:first-child { color:#4E5968; font-weight:600; }
.bd-row b { font-weight: 700; }
.bd-total { display:flex; justify-content:space-between; align-items:baseline; padding-top: 14px; }
.bd-total span { font-size: 14px; font-weight: 800; color:#191F28; }
.bd-total b { font-size: 26px; font-weight: 800; letter-spacing:-0.02em; }
.bd-note { font-size: 11.5px; color:#8B95A1; margin-top: 10px; line-height: 1.6; }

.badge { line-height: normal; background:#ffffff; height:36px; padding:0 14px; border-radius:12px; border:1px solid rgba(15,23,42,0.08); box-shadow:0 2px 8px rgba(15,23,42,0.03); display:inline-flex; align-items:center; gap:7px; white-space:nowrap; box-sizing:border-box; }
.dot { width:7px; height:7px; border-radius:50%; display:inline-block; }

div[class*="st-key-pos_header_row"] { position: relative !important; min-height: 36px; margin: 6px 0 12px; }
div[class*="st-key-pos_header_row"] div[class*="st-key-manual_refresh_main"] { position: absolute !important; top: 0 !important; right: 0 !important; width: auto !important; }
div[class*="st-key-manual_refresh_main"] button {
    width: 36px !important; height: 36px !important; min-width: 36px !important; min-height: 36px !important;
    padding: 0 !important; margin: 0 !important; border-radius: 12px !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    background-color: #ffffff !important; border: 1px solid rgba(15,23,42,0.08) !important;
    box-shadow: 0 2px 8px rgba(15,23,42,0.03) !important;
}
div[class*="st-key-manual_refresh_main"] button:hover { border-color: #3182F6 !important; background-color: #F8FAFC !important; }

[data-testid="stSpinner"] {
    background: #ffffff; padding: 18px 26px; border-radius: 18px;
    box-shadow: 0 8px 28px rgba(15,23,42,0.08); border: 1px solid rgba(15,23,42,0.04);
    margin: 24px auto; display: flex; align-items: center; justify-content: center; max-width: 420px;
}

div[class*="st-key-pnl_card"], div[class*="st-key-chart_card_"] {
    background-color: #ffffff !important; border-radius: 20px !important;
    box-shadow: 0 2px 14px rgba(15,23,42,0.05) !important; padding: 22px 24px !important;
}
div[class*="st-key-pos_container_"] {
    background-color: #ffffff !important; border-radius: 20px !important;
    box-shadow: 0 2px 14px rgba(15,23,42,0.05) !important; padding: 14px 24px 14px !important; margin-bottom: 18px !important;
}

button[data-baseweb="tab"] p { color: #8B95A1 !important; font-weight: 600 !important; font-size: 14.5px !important; }
button[data-baseweb="tab"][aria-selected="true"] p { color: #3182F6 !important; font-weight: 800 !important; }
div[data-baseweb="tab-highlight"] { background-color: #3182F6 !important; }

.pos-box { padding: 4px 14px; flex: 1 1 190px; }
.pos-divider { border-left: 1px solid rgba(15,23,42,0.06); }

.stButton>button { height: 38px; padding: 0 16px; border-radius: 999px; border: 1px solid rgba(15,23,42,0.08); background-color: #ffffff; color: #191F28; font-weight: 600; white-space: nowrap; box-shadow:none; }
.stButton>button:hover { border-color: #3182F6; color: #3182F6; }

.pill { display:inline-block; font-size:11px; font-weight:800; padding:3px 9px; border-radius:999px; vertical-align:middle; }
.note-text { font-size:11.5px; line-height:1.7; color:#B0B8C1; margin:6px 2px 0; }
.err-box { background:#FFF4F4; border:1px solid rgba(240,68,82,0.25); color:#C0303D; border-radius:14px; padding:12px 16px; font-size:13px; margin-bottom:14px; line-height:1.6; }

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
    .block-container { padding-top: 0.8rem; }
    div[class*="st-key-topnav_"] { height: 60px; gap: 16px !important; margin-bottom: 20px; padding: 0 16px !important; }
    .nav-logo .word { font-size: 18px; }
    .nav-logo .tag { display: none; }
    div[class*="st-key-navlink_"] a p { font-size: 14px !important; }
    .ph-title { font-size: 21px; }
    .pos-divider { border-left: none !important; border-top: 1px solid rgba(15,23,42,0.06) !important; padding-top: 14px !important; margin-top: 6px !important; }
    .hide-on-mobile { display: none !important; }
    .kpi-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
    .pt-grid { grid-template-columns: repeat(2, minmax(0,1fr)); gap: 8px; }
    div[data-testid="stButtonGroup"] button { padding: 0 10px !important; min-height: 34px !important; }
    div[data-testid="stButtonGroup"] button p { font-size: 13px !important; }
    .pt { padding: 14px; min-height: 150px; }
    .pt-value { font-size: 22px; }
    .bar-row { grid-template-columns: 1fr auto; }
    .bar-row .bar { display: none; }
    .kpi { border-left: none !important; padding-left: 0 !important; border-top: 1px solid #F2F4F6; }
}
</style>
""")


NAV_PAGES = [("history", "views/history.py", "매매 히스토리"), ("chart", "views/chart.py", "차트"), ("market", "views/market.py", "시장")]


def nav(current, dark=False):
    """전체 폭 상단 헤더: 로고 + 메뉴."""
    mode = "dark" if dark else "light"
    with st.container(key=f"topnav_{mode}", horizontal=True, vertical_alignment="center"):
        html("<div class='nav-logo'><svg viewBox='0 0 24 24' width='22' height='22'><rect x='3' y='12' width='4' height='9' rx='1.5' fill='#2459ED' opacity='.45'/>"
             "<rect x='10' y='7' width='4' height='14' rx='1.5' fill='#2459ED' opacity='.7'/><rect x='17' y='3' width='4' height='18' rx='1.5' fill='#2459ED'/></svg>"
             "<span class='word'>Mungge</span><span class='tag'>Trading</span></div>")
        for key, path, label in NAV_PAGES:
            with st.container(key=f"navlink_{key}_{'on' if key == current else 'off'}", width="content"):
                st.page_link(path, label=label)


def title_row(title, right_html, on_refresh):
    """섹션 제목 (왼쪽) + 상태 배지·새로고침 버튼 (오른쪽)."""
    with st.container(key="page_head", horizontal=True, vertical_alignment="center"):
        html(f"<div class='ph-title'>{title}</div>")
        with st.container(horizontal=True, vertical_alignment="center", width="content", gap="small"):
            html(right_html)
            with st.container(key="refresh_btn", width="content"):
                if st.button("", icon=":material/refresh:", help="모든 데이터 새로고침"):
                    on_refresh()


# 처음 거래 내역을 불러올 때 보여주는 로딩 화면
LOADER_HTML = """
<style>
@keyframes mg-bar { 0%,100% { transform: scaleY(.45); opacity: .45; } 50% { transform: scaleY(1); opacity: 1; } }
@keyframes mg-shine { 0% { background-position: -400px 0; } 100% { background-position: 400px 0; } }
@keyframes mg-prog { 0% { left: -40%; } 100% { left: 100%; } }
.mg-load { background:#fff; border-radius:20px; box-shadow:0 2px 14px rgba(15,23,42,0.05); padding:30px 28px 26px; margin: 14px 0 18px;
  display:flex; flex-direction:column; align-items:center; text-align:center; }
.mg-bars { display:flex; align-items:flex-end; gap:5px; height:34px; margin-bottom:16px; }
.mg-bars i { display:block; width:8px; border-radius:3px; background:#2459ED; transform-origin:bottom; animation: mg-bar 1s ease-in-out infinite; }
.mg-bars i:nth-child(1) { height:16px; opacity:.5; animation-delay: 0s; }
.mg-bars i:nth-child(2) { height:24px; opacity:.75; animation-delay: .15s; }
.mg-bars i:nth-child(3) { height:34px; animation-delay: .3s; }
.mg-t { font-size:17px; font-weight:800; color:#191F28; letter-spacing:-0.02em; }
.mg-s { font-size:13px; color:#8B95A1; margin-top:6px; line-height:1.6; }
.mg-prog { position:relative; width:220px; max-width:70%; height:4px; border-radius:2px; background:#EEF1F5; overflow:hidden; margin-top:18px; }
.mg-prog::after { content:''; position:absolute; top:0; width:40%; height:100%; border-radius:2px; background:#2459ED; animation: mg-prog 1.2s ease-in-out infinite; }
.mg-sk { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; width:100%; margin-top:22px; }
.mg-sk div { height:86px; border-radius:16px; background:linear-gradient(90deg,#F2F4F6 0%,#F8F9FB 40%,#F2F4F6 80%); background-size:800px 100%; animation: mg-shine 1.4s linear infinite; }
@media (max-width:768px) { .mg-sk { grid-template-columns:1fr; } .mg-sk div:nth-child(n+2) { display:none; } }
</style>
<div class="mg-load">
  <div class="mg-bars"><i></i><i></i><i></i></div>
  <div class="mg-t">거래 내역을 불러오고 있어요</div>
  <div class="mg-s">Bitget에서 체결 · 펀딩비 · 입금 내역을 확인하는 중이에요<br>보통 5~20초 걸려요</div>
  <div class="mg-prog"></div>
  <div class="mg-sk"><div></div><div></div><div></div></div>
</div>
"""
