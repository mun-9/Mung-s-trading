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
.block-container { padding-top: 1.2rem; max-width: 1240px; }
[data-testid="stHeader"] { display: none !important; }

/* 상단 메뉴 바 */
div[class*="st-key-topnav_"] { gap: 6px !important; padding: 6px 0 14px; margin-bottom: 10px; border-bottom: 1px solid #E5E8EB; }
div[class*="st-key-topnav_dark"] { border-bottom-color: #2A2E39; margin-bottom: 6px; padding: 2px 0 10px; }
.nav-logo { font-size: 17px; font-weight: 800; color: #191F28; letter-spacing: -0.02em; white-space: nowrap; line-height: 42px; margin: 0; }
div[class*="st-key-topnav_"] [data-testid="stMarkdownContainer"] { margin: 0 !important; }
div[class*="st-key-topnav_"] > div:has(div[class*="st-key-navlink_history"]) { margin-left: auto !important; }
div[class*="st-key-topnav_dark"] .nav-logo { color: #D1D4DC; }
div[class*="st-key-navlink_"] a { padding: 9px 20px !important; border-radius: 999px !important; min-height: 0 !important; }
div[class*="st-key-navlink_"] a p, div[class*="st-key-navlink_"] a span { font-size: 15px !important; font-weight: 700 !important; color: #6B7684 !important; }
div[class*="st-key-navlink_"] a:hover { background: rgba(49,130,246,0.08) !important; }
div[class*="st-key-navlink_"][class*="_on"] a { background: #191F28 !important; }
div[class*="st-key-navlink_"][class*="_on"] a p, div[class*="st-key-navlink_"][class*="_on"] a span { color: #FFFFFF !important; }
div[class*="st-key-topnav_dark"] div[class*="st-key-navlink_"] a p, div[class*="st-key-topnav_dark"] div[class*="st-key-navlink_"] a span { color: #787B86 !important; }
div[class*="st-key-topnav_dark"] div[class*="st-key-navlink_"][class*="_on"] a { background: #2962FF !important; }
div[class*="st-key-topnav_dark"] div[class*="st-key-navlink_"][class*="_on"] a p { color: #FFFFFF !important; }
div[class*="st-key-topnav_dark"] div[class*="st-key-navlink_"] a:hover { background: #2A2E39 !important; }
[data-testid="stToolbarActions"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"] { display: none !important; }

/* 상단 메뉴 */
[data-testid="stTopNavLinkContainer"] a, [data-testid="stNavSectionHeader"] { border-radius: 999px !important; }
[data-testid="stTopNavLinkContainer"] a span { font-weight: 700 !important; font-size: 14.5px !important; }

.sec-title { font-size: 19px; font-weight: 800; color: #191F28; margin: 30px 0 14px; display:flex; align-items:baseline; gap:10px; }
.sec-sub { font-size: 12.5px; font-weight: 500; color: #8B95A1; }

.card { background:#ffffff; border-radius:20px; box-shadow:0 2px 14px rgba(15,23,42,0.05); padding:22px 24px; }
.card-title { display:flex; justify-content:space-between; font-size:13px; font-weight:700; color:#191F28; }
.card-title span:last-child { color:#8B95A1; font-weight:500; }

.kpi-grid { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 0; }
.kpi { padding: 14px 16px; border-left: 1px solid #F2F4F6; }
.kpi:nth-child(4n+1) { border-left: none; padding-left: 0; }
.kpi-label { font-size: 12.5px; color:#8B95A1; font-weight:600; margin-bottom: 8px; }
.kpi-value { font-size: 21px; font-weight: 800; letter-spacing:-0.02em; }
.kpi-sub { font-size: 11.5px; color:#8B95A1; margin-top: 4px; }

.bd-row { display:flex; justify-content:space-between; align-items:center; padding: 11px 0; font-size: 14px; border-bottom: 1px solid #F2F4F6; }
.bd-row span:first-child { color:#4E5968; font-weight:600; }
.bd-row b { font-weight: 700; }
.bd-total { display:flex; justify-content:space-between; align-items:baseline; padding-top: 14px; }
.bd-total span { font-size: 14px; font-weight: 800; color:#191F28; }
.bd-total b { font-size: 26px; font-weight: 800; letter-spacing:-0.02em; }
.bd-note { font-size: 11.5px; color:#8B95A1; margin-top: 10px; line-height: 1.6; }

.badge { line-height: normal; background:#ffffff; padding:6px 12px; border-radius:999px; box-shadow:0 2px 10px rgba(15,23,42,0.04); display:inline-flex; align-items:center; gap:6px; white-space:nowrap; }
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
    box-shadow: 0 2px 14px rgba(15,23,42,0.05) !important; padding: 22px 24px 14px !important; margin-bottom: 18px !important;
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
    .nav-logo { font-size: 15px; }
    div[class*="st-key-navlink_"] a { padding: 8px 14px !important; }
    .pos-divider { border-left: none !important; border-top: 1px solid rgba(15,23,42,0.06) !important; padding-top: 14px !important; margin-top: 6px !important; }
    .hide-on-mobile { display: none !important; }
    .kpi-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
    .kpi { border-left: none !important; padding-left: 0 !important; border-top: 1px solid #F2F4F6; }
}
</style>
""")


NAV_PAGES = [("history", "views/history.py", "매매 히스토리"), ("chart", "views/chart.py", "차트")]


def nav(current, dark=False):
    """페이지 상단 메뉴 바 (로고 + 큰 탭 버튼)."""
    mode = "dark" if dark else "light"
    with st.container(key=f"topnav_{mode}", horizontal=True, vertical_alignment="center"):
        html(f"<div class='nav-logo'>📈 Mung's Trading</div>")
        for key, path, label in NAV_PAGES:
            with st.container(key=f"navlink_{key}_{'on' if key == current else 'off'}", width="content"):
                st.page_link(path, label=label)
