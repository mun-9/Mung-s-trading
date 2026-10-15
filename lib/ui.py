"""공통 디자인: 색상, CSS, 작은 HTML 컴포넌트."""
import streamlit as st

GREEN, RED, BLUE, GRAY = "#089981", "#F04452", "#3182F6", "#8B95A1"
# 화면 글자·선 색은 CSS 변수 → 라이트/다크 모드에 따라 자동으로 바뀜 (차트(plotly) 안에는 쓰지 말 것)
TEXT, SUB, DIVIDER = "var(--mg-text)", "var(--mg-sub)", "var(--mg-soft)"
LINE_COLOR = "var(--mg-line2)"
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


THEME_CSS = r"""
:root { --mg-bg:#F2F4F6; --mg-card:#FFFFFF; --mg-raise:#FFFFFF; --mg-text:#191F28; --mg-sub:#8B95A1; --mg-mid:#4E5968; --mg-mid2:#6B7684;
  --mg-line:#E5E8EB; --mg-line2:#D1D6DB; --mg-soft:#F2F4F6; --mg-tile:#F7F8FA; --mg-border:rgba(15,23,42,0.08); --mg-nav:rgba(255,255,255,0.72);
  --mg-navline:#E7EBF1; --mg-hover:rgba(255,255,255,0.75); --mg-sk1:#EEF1F5; --mg-sk2:#F8F9FB; --mg-faint:#B0B8C1; --mg-sel:#EEF3FF;
  --mg-errbg:#FFF4F4; --mg-accent:#2459ED; --mg-glow1:rgba(49,130,246,0.15); --mg-glow2:rgba(124,92,255,0.11); --mg-glow3:rgba(8,153,129,0.07); --mg-side1:rgba(49,130,246,0.20); --mg-side2:rgba(124,92,255,0.16); --mg-shadow:0 2px 14px rgba(15,23,42,0.05); }
html[data-mg-theme="dark"] { --mg-bg:#0D1015; --mg-card:#171B22; --mg-raise:#2A303A; --mg-text:#ECEEF2; --mg-sub:#8A93A2; --mg-mid:#B4BBC6; --mg-mid2:#9AA3B0;
  --mg-line:#272C35; --mg-line2:#353B46; --mg-soft:#20252D; --mg-tile:#1E232B; --mg-border:rgba(255,255,255,0.07); --mg-nav:rgba(13,16,21,0.70);
  --mg-navline:#1E232B; --mg-hover:rgba(255,255,255,0.06); --mg-sk1:#20252D; --mg-sk2:#2A303A; --mg-faint:#5F6774; --mg-sel:rgba(76,141,255,0.16);
  --mg-errbg:rgba(240,68,82,0.12); --mg-accent:#5B8DFF; --mg-glow1:rgba(49,110,246,0.20); --mg-glow2:rgba(124,92,255,0.14); --mg-glow3:rgba(8,153,129,0.08); --mg-side1:rgba(49,110,246,0.22); --mg-side2:rgba(124,92,255,0.16); --mg-shadow:0 2px 14px rgba(0,0,0,0.35); }
@media (prefers-color-scheme: dark) { html:not([data-mg-theme="light"]) { --mg-bg:#0D1015; --mg-card:#171B22; --mg-raise:#2A303A; --mg-text:#ECEEF2; --mg-sub:#8A93A2; --mg-mid:#B4BBC6; --mg-mid2:#9AA3B0;
  --mg-line:#272C35; --mg-line2:#353B46; --mg-soft:#20252D; --mg-tile:#1E232B; --mg-border:rgba(255,255,255,0.07); --mg-nav:rgba(13,16,21,0.70);
  --mg-navline:#1E232B; --mg-hover:rgba(255,255,255,0.06); --mg-sk1:#20252D; --mg-sk2:#2A303A; --mg-faint:#5F6774; --mg-sel:rgba(76,141,255,0.16);
  --mg-errbg:rgba(240,68,82,0.12); --mg-accent:#5B8DFF; --mg-glow1:rgba(49,110,246,0.20); --mg-glow2:rgba(124,92,255,0.14); --mg-glow3:rgba(8,153,129,0.08); --mg-side1:rgba(49,110,246,0.22); --mg-side2:rgba(124,92,255,0.16); --mg-shadow:0 2px 14px rgba(0,0,0,0.35); } }
html[data-mg-theme="dark"] .stApp, html[data-mg-theme="dark"] .stApp p, html[data-mg-theme="dark"] .stMarkdown { color: var(--mg-text); }
html[data-mg-theme="dark"] [data-testid="stCaptionContainer"], html[data-mg-theme="dark"] .stCaption { color: var(--mg-sub) !important; }
html[data-mg-theme="dark"] .card, html[data-mg-theme="dark"] div[class*="st-key-pnl_card"], html[data-mg-theme="dark"] div[class*="st-key-chart_card_"], html[data-mg-theme="dark"] div[class*="st-key-pos_container_"], html[data-mg-theme="dark"] .mg-load, html[data-mg-theme="dark"] .psk { box-shadow: var(--mg-shadow) !important; }
html[data-mg-theme="dark"] div[data-testid="stButtonGroup"] button { border-color: var(--mg-border) !important; }
html[data-mg-theme="dark"] div[data-testid="stButtonGroup"] button p { color: var(--mg-mid2) !important; }
html[data-mg-theme="dark"] div[data-testid="stButtonGroup"] button[aria-checked="true"] { background: var(--mg-raise) !important; }
html[data-mg-theme="dark"] div[data-testid="stButtonGroup"] button[aria-checked="true"] p { color: var(--mg-text) !important; }
html[data-mg-theme="dark"] div[class*="st-key-range_row"] button[data-variant="segmented_control"], html[data-mg-theme="dark"] div[class*="st-key-pnl_view_box"] button[data-variant="segmented_control"] { background: transparent !important; border: 0 !important; }
html[data-mg-theme="dark"] div[class*="st-key-pnl_view_box"] button[aria-checked="true"] { background: var(--mg-raise) !important; }
html[data-mg-theme="dark"] div[class*="st-key-pnl_view_box"] button[aria-checked="true"] p { color: var(--mg-text) !important; }
html[data-mg-theme="dark"] [data-baseweb="input"], html[data-mg-theme="dark"] [data-baseweb="input"] > div, html[data-mg-theme="dark"] [data-baseweb="select"] > div, html[data-mg-theme="dark"] [data-baseweb="base-input"] { background: var(--mg-card) !important; border-color: var(--mg-border) !important; color: var(--mg-text) !important; }
html[data-mg-theme="dark"] [data-baseweb="input"] input, html[data-mg-theme="dark"] [data-baseweb="select"] div, html[data-mg-theme="dark"] [data-baseweb="select"] span { color: var(--mg-text) !important; }
html[data-mg-theme="dark"] [data-baseweb="select"] svg, html[data-mg-theme="dark"] [data-baseweb="input"] svg { fill: var(--mg-sub) !important; color: var(--mg-sub) !important; }
html[data-mg-theme="dark"] [data-baseweb="popover"] > div, html[data-mg-theme="dark"] [data-baseweb="popover"] ul, html[data-mg-theme="dark"] [data-baseweb="menu"], html[data-mg-theme="dark"] [data-baseweb="calendar"], html[data-mg-theme="dark"] [data-baseweb="calendar"] > div, html[data-mg-theme="dark"] [data-baseweb="datepicker"] { background: var(--mg-card) !important; color: var(--mg-text) !important; }
html[data-mg-theme="dark"] [data-baseweb="popover"] li, html[data-mg-theme="dark"] [data-baseweb="calendar"] div, html[data-mg-theme="dark"] [data-baseweb="calendar"] button { color: var(--mg-text) !important; }
html[data-mg-theme="dark"] [data-baseweb="popover"] li:hover, html[data-mg-theme="dark"] [data-baseweb="popover"] li[aria-selected="true"] { background: var(--mg-soft) !important; }
html[data-mg-theme="dark"] [data-baseweb="calendar"] [aria-selected="true"] div, html[data-mg-theme="dark"] [data-baseweb="calendar"] [aria-selected="true"]::after { color: #fff !important; }
html[data-mg-theme="dark"] [data-baseweb="calendar"] select, html[data-mg-theme="dark"] [data-baseweb="calendar"] [role="presentation"] { background: var(--mg-card) !important; }
html[data-mg-theme="dark"] .stButton>button { color: var(--mg-text); }
html[data-mg-theme="dark"] .err-box { color: #FF8A93; }
html[data-mg-theme="dark"] .nav-logo .tag { background: rgba(91,141,255,0.16); }
html[data-mg-theme="dark"] ::-webkit-scrollbar-thumb { background: #2A303A; }
@media (prefers-color-scheme: dark) {
html:not([data-mg-theme="light"]) .stApp, html:not([data-mg-theme="light"]) .stApp p, html:not([data-mg-theme="light"]) .stMarkdown { color: var(--mg-text); }
html:not([data-mg-theme="light"]) [data-testid="stCaptionContainer"], html:not([data-mg-theme="light"]) .stCaption { color: var(--mg-sub) !important; }
html:not([data-mg-theme="light"]) .card, html:not([data-mg-theme="light"]) div[class*="st-key-pnl_card"], html:not([data-mg-theme="light"]) div[class*="st-key-chart_card_"], html:not([data-mg-theme="light"]) div[class*="st-key-pos_container_"], html:not([data-mg-theme="light"]) .mg-load, html:not([data-mg-theme="light"]) .psk { box-shadow: var(--mg-shadow) !important; }
html:not([data-mg-theme="light"]) div[data-testid="stButtonGroup"] button { border-color: var(--mg-border) !important; }
html:not([data-mg-theme="light"]) div[data-testid="stButtonGroup"] button p { color: var(--mg-mid2) !important; }
html:not([data-mg-theme="light"]) div[data-testid="stButtonGroup"] button[aria-checked="true"] { background: var(--mg-raise) !important; }
html:not([data-mg-theme="light"]) div[data-testid="stButtonGroup"] button[aria-checked="true"] p { color: var(--mg-text) !important; }
html:not([data-mg-theme="light"]) div[class*="st-key-range_row"] button[data-variant="segmented_control"], html:not([data-mg-theme="light"]) div[class*="st-key-pnl_view_box"] button[data-variant="segmented_control"] { background: transparent !important; border: 0 !important; }
html:not([data-mg-theme="light"]) div[class*="st-key-pnl_view_box"] button[aria-checked="true"] { background: var(--mg-raise) !important; }
html:not([data-mg-theme="light"]) div[class*="st-key-pnl_view_box"] button[aria-checked="true"] p { color: var(--mg-text) !important; }
html:not([data-mg-theme="light"]) [data-baseweb="input"], html:not([data-mg-theme="light"]) [data-baseweb="input"] > div, html:not([data-mg-theme="light"]) [data-baseweb="select"] > div, html:not([data-mg-theme="light"]) [data-baseweb="base-input"] { background: var(--mg-card) !important; border-color: var(--mg-border) !important; color: var(--mg-text) !important; }
html:not([data-mg-theme="light"]) [data-baseweb="input"] input, html:not([data-mg-theme="light"]) [data-baseweb="select"] div, html:not([data-mg-theme="light"]) [data-baseweb="select"] span { color: var(--mg-text) !important; }
html:not([data-mg-theme="light"]) [data-baseweb="select"] svg, html:not([data-mg-theme="light"]) [data-baseweb="input"] svg { fill: var(--mg-sub) !important; color: var(--mg-sub) !important; }
html:not([data-mg-theme="light"]) [data-baseweb="popover"] > div, html:not([data-mg-theme="light"]) [data-baseweb="popover"] ul, html:not([data-mg-theme="light"]) [data-baseweb="menu"], html:not([data-mg-theme="light"]) [data-baseweb="calendar"], html:not([data-mg-theme="light"]) [data-baseweb="calendar"] > div, html:not([data-mg-theme="light"]) [data-baseweb="datepicker"] { background: var(--mg-card) !important; color: var(--mg-text) !important; }
html:not([data-mg-theme="light"]) [data-baseweb="popover"] li, html:not([data-mg-theme="light"]) [data-baseweb="calendar"] div, html:not([data-mg-theme="light"]) [data-baseweb="calendar"] button { color: var(--mg-text) !important; }
html:not([data-mg-theme="light"]) [data-baseweb="popover"] li:hover, html:not([data-mg-theme="light"]) [data-baseweb="popover"] li[aria-selected="true"] { background: var(--mg-soft) !important; }
html:not([data-mg-theme="light"]) [data-baseweb="calendar"] [aria-selected="true"] div, html:not([data-mg-theme="light"]) [data-baseweb="calendar"] [aria-selected="true"]::after { color: #fff !important; }
html:not([data-mg-theme="light"]) [data-baseweb="calendar"] select, html:not([data-mg-theme="light"]) [data-baseweb="calendar"] [role="presentation"] { background: var(--mg-card) !important; }
html:not([data-mg-theme="light"]) .stButton>button { color: var(--mg-text); }
html:not([data-mg-theme="light"]) .err-box { color: #FF8A93; }
html:not([data-mg-theme="light"]) .nav-logo .tag { background: rgba(91,141,255,0.16); }
html:not([data-mg-theme="light"]) ::-webkit-scrollbar-thumb { background: #2A303A; }
}
.stApp { transition: background-color .25s ease; }
/* 다크 모드 버튼 (메뉴 오른쪽) */
.mg-theme-slot { display: flex; align-items: center; }
.mg-theme-btn { width: 38px; height: 38px; border-radius: 12px; border: 1px solid var(--mg-border); background: var(--mg-card); color: var(--mg-text);
  display: flex; align-items: center; justify-content: center; cursor: pointer; padding: 0; transition: border-color .15s, transform .15s; }
.mg-theme-btn:hover { border-color: var(--mg-accent); }
.mg-theme-btn:active { transform: scale(.94); }
.mg-theme-btn svg { width: 18px; height: 18px; }
/* 다크: 날짜 입력칸 안쪽 흰 배경 제거 */
html[data-mg-theme="dark"] [data-testid="stDateInputCalendar"] { background-color: var(--mg-card) !important; color: var(--mg-text) !important; border: 1px solid var(--mg-border) !important; box-shadow: 0 10px 30px rgba(0,0,0,0.45) !important; }
html[data-mg-theme="dark"] [data-testid="stDateInputCalendar"] * { color: var(--mg-text); border-color: var(--mg-border); }
html[data-mg-theme="dark"] [data-testid="stDateInputCalendar"] [aria-disabled="true"], html[data-mg-theme="dark"] [data-testid="stDateInputCalendar"] [data-disabled], html[data-mg-theme="dark"] [data-testid="stDateInputCalendar"] [data-outside-month] { color: var(--mg-faint) !important; }
html[data-mg-theme="dark"] [data-testid="stDateInputCalendar"] [data-selected] { background-color: rgba(91,141,255,0.18); }
html[data-mg-theme="dark"] [data-testid="stDateInputCalendar"] [data-selection-start], html[data-mg-theme="dark"] [data-testid="stDateInputCalendar"] [data-selection-end] { color: #fff !important; }
html[data-mg-theme="dark"] [data-testid="stDateInputCalendar"] select, html[data-mg-theme="dark"] [data-testid="stDateInputCalendar"] button { background-color: transparent; }
@media (prefers-color-scheme: dark) {
html:not([data-mg-theme="light"]) [data-testid="stDateInputCalendar"] { background-color: var(--mg-card) !important; color: var(--mg-text) !important; border: 1px solid var(--mg-border) !important; box-shadow: 0 10px 30px rgba(0,0,0,0.45) !important; }
html:not([data-mg-theme="light"]) [data-testid="stDateInputCalendar"] * { color: var(--mg-text); border-color: var(--mg-border); }
html:not([data-mg-theme="light"]) [data-testid="stDateInputCalendar"] [aria-disabled="true"], html:not([data-mg-theme="light"]) [data-testid="stDateInputCalendar"] [data-disabled], html:not([data-mg-theme="light"]) [data-testid="stDateInputCalendar"] [data-outside-month] { color: var(--mg-faint) !important; }
html:not([data-mg-theme="light"]) [data-testid="stDateInputCalendar"] [data-selected] { background-color: rgba(91,141,255,0.18); }
html:not([data-mg-theme="light"]) [data-testid="stDateInputCalendar"] [data-selection-start], html:not([data-mg-theme="light"]) [data-testid="stDateInputCalendar"] [data-selection-end] { color: #fff !important; }
html:not([data-mg-theme="light"]) [data-testid="stDateInputCalendar"] select, html:not([data-mg-theme="light"]) [data-testid="stDateInputCalendar"] button { background-color: transparent; }
}
html[data-mg-theme="dark"] [data-testid="stSelectbox"] [role="group"] { background-color: var(--mg-card) !important; border-color: var(--mg-border) !important; color: var(--mg-text) !important; }
html[data-mg-theme="dark"] [data-testid="stSelectbox"] *, html[data-mg-theme="dark"] [data-testid="stSelectbox"] svg { color: var(--mg-text) !important; }
html[data-mg-theme="dark"] [role="listbox"], html[data-mg-theme="dark"] [data-rac][role="dialog"], html[data-mg-theme="dark"] .react-aria-Popover { background-color: var(--mg-card) !important; color: var(--mg-text) !important; border-color: var(--mg-border) !important; }
html[data-mg-theme="dark"] [role="option"] { color: var(--mg-text) !important; background-color: transparent !important; }
html[data-mg-theme="dark"] [role="option"][data-focused], html[data-mg-theme="dark"] [role="option"][data-hovered], html[data-mg-theme="dark"] [role="option"][aria-selected="true"] { background-color: var(--mg-soft) !important; }
html[data-mg-theme="dark"] [role="dialog"] [role="gridcell"], html[data-mg-theme="dark"] [role="dialog"] button, html[data-mg-theme="dark"] [role="dialog"] th, html[data-mg-theme="dark"] [role="dialog"] h2 { color: var(--mg-text) !important; }
@media (prefers-color-scheme: dark) {
html:not([data-mg-theme="light"]) [data-testid="stSelectbox"] [role="group"] { background-color: var(--mg-card) !important; border-color: var(--mg-border) !important; color: var(--mg-text) !important; }
html:not([data-mg-theme="light"]) [data-testid="stSelectbox"] *, html:not([data-mg-theme="light"]) [data-testid="stSelectbox"] svg { color: var(--mg-text) !important; }
html:not([data-mg-theme="light"]) [role="listbox"], html:not([data-mg-theme="light"]) [data-rac][role="dialog"], html:not([data-mg-theme="light"]) .react-aria-Popover { background-color: var(--mg-card) !important; color: var(--mg-text) !important; border-color: var(--mg-border) !important; }
html:not([data-mg-theme="light"]) [role="option"] { color: var(--mg-text) !important; background-color: transparent !important; }
html:not([data-mg-theme="light"]) [role="option"][data-focused], html:not([data-mg-theme="light"]) [role="option"][data-hovered], html:not([data-mg-theme="light"]) [role="option"][aria-selected="true"] { background-color: var(--mg-soft) !important; }
html:not([data-mg-theme="light"]) [role="dialog"] [role="gridcell"], html:not([data-mg-theme="light"]) [role="dialog"] button, html:not([data-mg-theme="light"]) [role="dialog"] th, html:not([data-mg-theme="light"]) [role="dialog"] h2 { color: var(--mg-text) !important; }
}
html[data-mg-theme="dark"] [data-testid="stDateInputField"], html[data-mg-theme="dark"] [data-testid="stDateInput"] input { background-color: var(--mg-card) !important; color: var(--mg-text) !important; border-color: var(--mg-border) !important; }
html[data-mg-theme="dark"] [data-testid="stDateInput"] span { color: var(--mg-text) !important; } html[data-mg-theme="dark"] [data-testid="stDateInput"] svg { color: var(--mg-sub) !important; }
@media (prefers-color-scheme: dark) {
html:not([data-mg-theme="light"]) [data-testid="stDateInputField"], html:not([data-mg-theme="light"]) [data-testid="stDateInput"] input { background-color: var(--mg-card) !important; color: var(--mg-text) !important; border-color: var(--mg-border) !important; }
html:not([data-mg-theme="light"]) [data-testid="stDateInput"] span { color: var(--mg-text) !important; } html:not([data-mg-theme="light"]) [data-testid="stDateInput"] svg { color: var(--mg-sub) !important; }
}
html[data-mg-theme="dark"] [data-baseweb="input"] input, html[data-mg-theme="dark"] [data-baseweb="input"] div, html[data-mg-theme="dark"] div[class*="st-key-range_date"] [data-baseweb="input"] * { background-color: transparent !important; }
html[data-mg-theme="dark"] div[class*="st-key-range_date"] [data-baseweb="input"] { background: var(--mg-card) !important; }
@media (prefers-color-scheme: dark) {
html:not([data-mg-theme="light"]) [data-baseweb="input"] input, html:not([data-mg-theme="light"]) [data-baseweb="input"] div, html:not([data-mg-theme="light"]) div[class*="st-key-range_date"] [data-baseweb="input"] * { background-color: transparent !important; }
html:not([data-mg-theme="light"]) div[class*="st-key-range_date"] [data-baseweb="input"] { background: var(--mg-card) !important; }
}
"""


def inject_css():
    html(("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
__THEME_VARS__

html, body, .stApp { background-color: var(--mg-bg) !important; }
/* 은은한 배경: 양쪽 위 구석에 아주 옅은 빛 (스크롤해도 제자리) */
.stApp { background-image:
    radial-gradient(1100px 700px at -8% -12%, var(--mg-glow1), transparent 62%),
    radial-gradient(900px 650px at 108% 4%, var(--mg-glow2), transparent 60%),
    radial-gradient(1000px 600px at 50% 118%, var(--mg-glow3), transparent 65%) !important;
  background-attachment: fixed !important; }
/* PC(넓은 화면): 내용 양옆 빈 공간에 세로로 길게 빛을 더 깔아서 옆이 허전하지 않게 */
@media (min-width: 1280px) {
  .stApp { background-image:
      radial-gradient(560px 1000px at 0% 40%, var(--mg-side1), transparent 70%),
      radial-gradient(560px 1000px at 100% 60%, var(--mg-side2), transparent 70%),
      radial-gradient(1100px 700px at -8% -12%, var(--mg-glow1), transparent 62%),
      radial-gradient(900px 650px at 108% 4%, var(--mg-glow2), transparent 60%),
      radial-gradient(1000px 600px at 50% 118%, var(--mg-glow3), transparent 65%) !important; }
}
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stBottom"] { background: transparent !important; }
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
[data-testid="stLayoutWrapper"]:has(> div[class*="st-key-topnav_"]) { position: sticky; top: 0; z-index: 999; }
div[class*="st-key-topnav_"] {
    position: sticky; top: 0; z-index: 999; height: 72px; gap: 30px !important;
    margin-left: calc(50% - 50vw) !important; margin-right: calc(50% - 50vw) !important;
    width: 100vw !important; max-width: none !important; min-width: 100vw !important; flex: none !important;
    padding: 0 max(80px, calc(50vw - 540px)) !important;
    background: var(--mg-nav); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--mg-navline); margin-bottom: 0;
}
div[class*="st-key-topnav_dark"] { background: #0F121A; border-bottom-color: #1E222D; margin-bottom: 8px; padding: 0 14px !important; height: 50px; }
div[class*="st-key-topnav_dark"] .nav-logo .word { font-size: 17px; }
div[class*="st-key-topnav_"] [data-testid="stMarkdownContainer"] { margin: 0 !important; }
.nav-logo { display: flex; align-items: center; gap: 9px; margin: 0; white-space: nowrap; }
.nav-logo { gap: 8px !important; }
.nav-logo .word { font-size: 20px; font-weight: 800; color: var(--mg-text); letter-spacing: -0.6px; }
.nav-logo .tag { font-size: 11px; font-weight: 700; color: var(--mg-accent); background: rgba(36,89,237,0.08); padding: 3px 7px; border-radius: 6px; letter-spacing: 0.2px; }
div[class*="st-key-topnav_dark"] .nav-logo .tag { background: rgba(41,98,255,0.18); color: #7FA3FF; }
div[class*="st-key-topnav_dark"] .nav-logo .word { color: #D1D4DC; }
/* 메뉴: 회색 바 안에 탭 버튼 3개 (지금 있는 페이지는 흰 버튼으로 떠 있음) → 눌러서 이동하는 메뉴인 게 한눈에 보이게 */
div[class*="st-key-topnav_"] { justify-content: space-between !important; flex-wrap: nowrap !important; }
div[class*="st-key-topnav_"] > [data-testid="stLayoutWrapper"]:has(div[class*="st-key-navtabs"]) { margin-left: auto !important; flex: none !important; width: auto !important; }
div[class*="st-key-topnav_"] > [data-testid="stElementContainer"]:has(.mg-theme-slot) { width: auto !important; flex: none !important; }
div[class*="st-key-navtabs"] { background: var(--mg-soft); padding: 4px !important; border-radius: 13px; gap: 2px !important; flex-wrap: nowrap !important; border: 1px solid var(--mg-border); }
div[class*="st-key-navlink_"] a { padding: 7px 14px !important; min-height: 0 !important; background: transparent !important; border-radius: 9px !important;
    display: flex !important; align-items: center; gap: 6px; transition: background .15s ease, box-shadow .15s ease; }
div[class*="st-key-navlink_"] a p, div[class*="st-key-navlink_"] a span { font-size: 14.5px !important; font-weight: 650 !important; color: var(--mg-mid2) !important; white-space: nowrap; }
div[class*="st-key-navlink_"] a [data-testid="stIconMaterial"] { font-size: 18px !important; }
div[class*="st-key-navlink_"] a:hover { background: var(--mg-hover) !important; }
div[class*="st-key-navlink_"] a:hover p, div[class*="st-key-navlink_"] a:hover span { color: var(--mg-text) !important; }
div[class*="st-key-navlink_"][class*="_on"] a { background: var(--mg-raise) !important; box-shadow: 0 1px 4px rgba(15,23,42,0.10); }
div[class*="st-key-navlink_"][class*="_on"] a p, div[class*="st-key-navlink_"][class*="_on"] a span { color: var(--mg-accent) !important; font-weight: 750 !important; }

/* 섹션 제목 줄 (보유 포지션 + 배지 + 새로고침) */
div[class*="st-key-hidden_nav_"] { display: none !important; }
div[class*="st-key-page_head"] { margin: 10px 0 4px; min-height: 40px; }
div[class*="st-key-page_head"] [data-testid="stElementContainer"], div[class*="st-key-page_head"] [data-testid="stMarkdownContainer"] { margin: 0 !important; }
div[class*="st-key-page_head"] .ph-title { line-height: 36px; font-size: 26px; padding-left: 0.3em; }
div[class*="st-key-page_head"] p { margin: 0 !important; line-height: 0; }
div[class*="st-key-page_head"] [data-testid="stMarkdown"] { display: flex; align-items: center; }
div[class*="st-key-pnl_head"] { justify-content: space-between !important; }
div[class*="st-key-pnl_head"] [data-testid="stMarkdownContainer"] { margin: 0 !important; }
div[class*="st-key-pnl_view_box"] { margin-left: auto !important; }
div[class*="st-key-page_head"] > div:last-child { gap: 8px !important; align-items: center !important; }
div[class*="st-key-page_head"] > div:last-child { margin-left: auto !important; }
.ph-title { font-size: 24px; font-weight: 800; color: var(--mg-text); letter-spacing: -0.03em; }
div[class*="st-key-refresh_btn"] button { width: 36px !important; height: 36px !important; min-height: 36px !important; padding: 0 !important; border-radius: 12px !important; box-shadow: 0 2px 8px rgba(15,23,42,0.03);
    background: var(--mg-card) !important; border: 1px solid var(--mg-border) !important; }
div[class*="st-key-refresh_btn"] button:hover { border-color: var(--mg-accent) !important; }
div[class*="st-key-refresh_btn"] button span { color: var(--mg-text) !important; }

.sec-title { font-size: 19px; font-weight: 800; color: var(--mg-text); margin: 30px 0 14px; display:flex; align-items:baseline; gap:10px; }
.sec-sub { font-size: 12.5px; font-weight: 500; color: var(--mg-sub); }

.card { background:var(--mg-card); border-radius:20px; box-shadow:0 2px 14px rgba(15,23,42,0.05); padding:22px 24px; }
.card-title { display:flex; justify-content:space-between; align-items:baseline; gap:10px; font-size:17px; font-weight:800; color:var(--mg-text); letter-spacing:-0.02em; }
.card-title span:last-child { color:var(--mg-sub); font-weight:500; font-size:12.5px; letter-spacing:0; }

.kpi-grid { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 0; }
.kpi { padding: 14px 16px; border-left: 1px solid var(--mg-soft); }
.kpi:nth-child(4n+1) { border-left: none; padding-left: 0; }
.kpi-label { font-size: 12.5px; color:var(--mg-sub); font-weight:600; margin-bottom: 8px; }
.kpi-value { font-size: 21px; font-weight: 800; letter-spacing:-0.02em; }
.kpi-sub { font-size: 11.5px; color:var(--mg-sub); margin-top: 4px; }

.pt-grid { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 12px; margin-top: 16px; }
.pt { background: var(--mg-tile); border-radius: 16px; padding: 18px 18px 16px; display: flex; flex-direction: column; gap: 10px; min-height: 176px; }
.pt-label { font-size: 14px; font-weight: 700; color: var(--mg-mid); }
.pt-value { font-size: 30px; font-weight: 800; color: var(--mg-text); letter-spacing: -0.03em; line-height: 1.1; }
.pt-unit { font-size: 15px; font-weight: 700; color: var(--mg-sub); margin-left: 3px; }
.pt-foot { display: flex; justify-content: space-between; gap: 8px; font-size: 12.5px; color: var(--mg-sub); margin-top: auto; }
.gauge { position: relative; height: 8px; background: var(--mg-line); border-radius: 4px; overflow: visible; margin-top: auto; }
.gauge-fill { height: 100%; border-radius: 4px; }
.gauge-mark { position: absolute; top: -3px; width: 2px; height: 14px; background: var(--mg-text); opacity: .35; border-radius: 1px; }
.bar-row { display: grid; grid-template-columns: 62px 1fr auto; align-items: center; gap: 8px; font-size: 13px; color: var(--mg-mid2); }
.bar-row b { font-size: 13.5px; font-weight: 700; }
.bar { height: 8px; background: var(--mg-line); border-radius: 4px; overflow: hidden; }
.bar > div { height: 100%; border-radius: 4px; }
.streak { display: flex; gap: 5px; flex-wrap: wrap; margin-top: auto; }
.streak .sd { width: 14px; height: 14px; border-radius: 4px; }
/* 상세 매매 내역: 주문 종류 배지 (시장가 / 지정가 / 익절·손절 주문) */
.ot { display:inline-flex; align-items:center; gap:4px; }
.ot b { display:inline-block; font-size:10.5px; font-weight:800; letter-spacing:.04em; padding:3px 7px; border-radius:6px; line-height:1.1; }
.ot .m { background:rgba(245,158,11,.16); color:#D97706; }
.ot .l { background:rgba(49,130,246,.14); color:#3182F6; }
.ot .tp { background:rgba(8,153,129,.14); color:#089981; }
.ot .sl { background:rgba(240,68,82,.13); color:#F04452; }
.ot .lq { background:rgba(240,68,82,.9); color:#fff; }
.ot small { font-size:11.5px; color:var(--mg-sub); font-weight:600; margin-left:2px; }
html[data-mg-theme="dark"] .ot .m { color:#FBBF24; } html[data-mg-theme="dark"] .ot .l { color:#7FA8FF; }
@media (prefers-color-scheme: dark) { html:not([data-mg-theme="light"]) .ot .m { color:#FBBF24; } html:not([data-mg-theme="light"]) .ot .l { color:#7FA8FF; } }
/* 체결 알림 종 버튼 (보유 포지션 제목 줄) */
.mg-fillbell { display:inline-flex; align-items:center; justify-content:center; width:36px; height:36px; border-radius:12px; cursor:pointer; box-sizing:border-box;
  border:1px solid var(--mg-border); background:var(--mg-card); color:var(--mg-sub); box-shadow:0 2px 8px rgba(15,23,42,0.03); transition:all .15s; vertical-align:middle; }
.mg-fillbell svg { width:17px; height:17px; }
.mg-fillbell:hover { color:var(--mg-text); }
.mg-fillbell:hover { border-color: var(--mg-accent); }
.mg-fillbell.on { color:var(--mg-accent); background:var(--mg-card); border-color:var(--mg-border); }
.mg-fillbell.on svg { fill: currentColor; fill-opacity: .18; }
/* 포지션 있을 때: 메뉴 바로 밑에 딱 붙는 긴급 띠 (배경 줄무늬가 계속 흐르고, 빛이 지나감) */
.mg-brk { position:relative; overflow:hidden; display:flex; align-items:center; justify-content:center; gap:12px; height:38px;
  width:100vw; margin:-16px calc(50% - 50vw) 14px; color:#fff;
  background-color:#D7263A;
  background-image:linear-gradient(135deg, rgba(0,0,0,.16) 25%, transparent 25%, transparent 50%, rgba(0,0,0,.16) 50%, rgba(0,0,0,.16) 75%, transparent 75%);
  background-size:38px 38px; animation: mg-stripe .8s linear infinite; box-shadow: 0 6px 18px rgba(215,38,58,.28); }
.mg-brk::after { content:''; position:absolute; top:0; bottom:0; left:-30%; width:30%; pointer-events:none;
  background:linear-gradient(90deg, transparent, rgba(255,255,255,.28), transparent); animation: mg-sweep 2.4s ease-in-out infinite; }
@keyframes mg-stripe { from { background-position: 0 0; } to { background-position: 38px 0; } }
@keyframes mg-sweep { 0% { left:-30%; } 60%, 100% { left:110%; } }
.mg-brk .tag { display:flex; align-items:center; gap:6px; padding:3px 9px; border-radius:6px; background:#fff; color:#D7263A;
  font-size:11.5px; font-weight:900; letter-spacing:.1em; position:relative; z-index:1; }
.mg-brk .tag i { width:7px; height:7px; border-radius:50%; background:#D7263A; animation: mg-blink 1s steps(2, start) infinite; }
@keyframes mg-blink { to { visibility:hidden; } }
.mg-brk .msg { position:relative; z-index:1; font-size:15px; font-weight:900; letter-spacing:-.01em; text-shadow:0 1px 2px rgba(0,0,0,.25); white-space:nowrap; }
.mg-brk .msg em { font-style:normal; font-weight:700; font-size:12.5px; opacity:.85; margin-left:8px; }
@media (max-width:768px) { .mg-brk { height:34px; margin-top:-36px; gap:9px; } .mg-brk .msg { font-size:13.5px; } .mg-brk .msg em { font-size:11.5px; } }
@media (prefers-reduced-motion: reduce) { .mg-brk, .mg-brk::after { animation-duration: 4s; } }
.mg-fillbell.on svg { animation: mg-ring 1.6s ease-in-out 1; transform-origin: 50% 10%; }
@keyframes mg-ring { 0%,100% { transform: rotate(0); } 15% { transform: rotate(14deg); } 30% { transform: rotate(-12deg); } 45% { transform: rotate(8deg); } 60% { transform: rotate(-4deg); } }
/* 계좌 점검 */
.acc-grid { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 10px; margin-top: 16px; }
.acc-t { background: var(--mg-tile); border-radius: 14px; padding: 14px 16px; min-width: 0; }
.acc-t > span { display: block; font-size: 12.5px; font-weight: 700; color: var(--mg-mid); }
.acc-t b { display: block; font-size: 21px; font-weight: 800; letter-spacing: -.02em; margin-top: 6px; font-variant-numeric: tabular-nums; }
.acc-t small { display: block; font-size: 11.5px; color: var(--mg-sub); margin-top: 4px; line-height: 1.45; }
.acc-t.hl { background: var(--mg-sel, rgba(49,130,246,.08)); box-shadow: inset 0 0 0 1.5px rgba(49,130,246,.35); }
.acc-diff { display: flex; align-items: flex-start; gap: 10px; margin-top: 12px; padding: 12px 14px; border-radius: 12px; background: var(--mg-tile); font-size: 13px; line-height: 1.6; color: var(--mg-mid); }
.acc-diff b { color: var(--mg-text); }
.acc-v { margin-top: 10px; font-size: 12.5px; color: var(--mg-sub); line-height: 1.6; }
.acc-v b { color: var(--mg-mid); }
.m-only { display: none; }
.bd-chips { display: flex; flex-wrap: wrap; gap: 6px 16px; margin-top: 10px; font-size: 12.5px; color: var(--mg-sub); }
.bd-chips b { font-weight: 700; margin-left: 2px; }

.acct { display:grid; grid-template-columns: 1fr 1fr; gap: 28px; align-items:center; }
.acct-r /* 상단 PNL 카드 */
.topc { min-height: 132px; display:flex; flex-direction:column; justify-content:center; padding: 20px 24px !important; }
.topc-h { display:flex; justify-content:space-between; align-items:center; gap:10px; }
.topc-t { font-size:15px; font-weight:800; color:var(--mg-mid); letter-spacing:-0.01em; }
.topc-chip { font-size:12px; font-weight:600; color:var(--mg-mid2); background:var(--mg-soft); padding:4px 10px; border-radius:999px; white-space:nowrap; }
.topc-v { font-size:32px; font-weight:800; letter-spacing:-0.03em; margin-top:12px; line-height:1.1; }
.topc-k { font-size:14px; font-weight:600; color:var(--mg-sub); margin-top:4px; }

/* 기간 선택 줄 */
div[class*="st-key-range_row"] { flex-wrap: wrap !important; row-gap: 8px !important; }
div[class*="st-key-range_date"] { width: 300px !important; max-width: 100%; }
div[class*="st-key-range_date"] [data-baseweb="input"] { height: 42px; border-radius: 12px !important; border: 1px solid var(--mg-border) !important; background: var(--mg-card) !important; box-shadow: 0 2px 8px rgba(15,23,42,0.03); }
div[class*="st-key-range_date"] [data-baseweb="input"] > div { background: var(--mg-card) !important; }
div[class*="st-key-range_date"] input { font-weight: 600 !important; color: var(--mg-text) !important; }
div[class*="st-key-range_row"] div[role="radiogroup"], div[class*="st-key-pnl_view_box"] div[role="radiogroup"] {
  background:var(--mg-card); border-radius:12px; padding:4px; gap:2px !important; border:1px solid var(--mg-border); box-shadow:0 2px 8px rgba(15,23,42,0.03); }
div[class*="st-key-pnl_view_box"] div[role="radiogroup"] { background:var(--mg-soft); border:0; box-shadow:none; }
div[class*="st-key-range_row"] button[data-variant="segmented_control"], div[class*="st-key-pnl_view_box"] button[data-variant="segmented_control"] {
  border:0 !important; background:transparent !important; border-radius:9px !important; min-height:32px !important; height:32px; padding:0 14px !important; box-shadow:none !important; }
div[class*="st-key-range_row"] button[data-variant="segmented_control"] p, div[class*="st-key-pnl_view_box"] button[data-variant="segmented_control"] p { font-size:13.5px !important; font-weight:600 !important; color:var(--mg-mid2) !important; }
div[class*="st-key-range_row"] button[aria-checked="true"] { background:var(--mg-sel) !important; }
div[class*="st-key-range_row"] button[aria-checked="true"] p { color:var(--mg-accent) !important; font-weight:800 !important; }
div[class*="st-key-pnl_view_box"] button[aria-checked="true"] { background:var(--mg-raise) !important; box-shadow:0 1px 4px var(--mg-border) !important; }
div[class*="st-key-pnl_view_box"] button[aria-checked="true"] p { color:var(--mg-text) !important; font-weight:800 !important; }
div[class*="st-key-pnl_card"] > div:first-child { justify-content: space-between !important; }
@media (max-width: 768px) {
  div[class*="st-key-range_date"] { width: 100% !important; }
  .topc { min-height: 0; }
  .topc-v { font-size: 28px; }
}

.bd-row { padding: 8px 0; font-size: 13.5px; }
@media (max-width: 768px) { .acct { grid-template-columns: 1fr; gap: 10px; } }

.bd-row { display:flex; justify-content:space-between; align-items:center; padding: 11px 0; font-size: 14px; border-bottom: 1px solid var(--mg-soft); }
.bd-row span:first-child { color:var(--mg-mid); font-weight:600; }
.bd-row b { font-weight: 700; }
.bd-total { display:flex; justify-content:space-between; align-items:baseline; padding-top: 14px; }
.bd-total span { font-size: 14px; font-weight: 800; color:var(--mg-text); }
.bd-total b { font-size: 26px; font-weight: 800; letter-spacing:-0.02em; }
.bd-note { font-size: 11.5px; color:var(--mg-sub); margin-top: 10px; line-height: 1.6; }

.badge { line-height: normal; background:var(--mg-card); height:36px; padding:0 14px; border-radius:12px; border:1px solid var(--mg-border); box-shadow:0 2px 8px rgba(15,23,42,0.03); display:inline-flex; align-items:center; gap:7px; white-space:nowrap; box-sizing:border-box; }
.dot { width:7px; height:7px; border-radius:50%; display:inline-block; }

div[class*="st-key-pos_header_row"] { position: relative !important; min-height: 36px; margin: 6px 0 12px; }
div[class*="st-key-pos_header_row"] div[class*="st-key-manual_refresh_main"] { position: absolute !important; top: 0 !important; right: 0 !important; width: auto !important; }
div[class*="st-key-manual_refresh_main"] button {
    width: 36px !important; height: 36px !important; min-width: 36px !important; min-height: 36px !important;
    padding: 0 !important; margin: 0 !important; border-radius: 12px !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    background-color: var(--mg-card) !important; border: 1px solid var(--mg-border) !important;
    box-shadow: 0 2px 8px rgba(15,23,42,0.03) !important;
}
div[class*="st-key-manual_refresh_main"] button:hover { border-color: #3182F6 !important; background-color: var(--mg-soft) !important; }

[data-testid="stSpinner"] {
    background: var(--mg-card); padding: 18px 26px; border-radius: 18px;
    box-shadow: 0 8px 28px var(--mg-border); border: 1px solid rgba(15,23,42,0.04);
    margin: 24px auto; display: flex; align-items: center; justify-content: center; max-width: 420px;
}

div[class*="st-key-pnl_card"], div[class*="st-key-chart_card_"] {
    background-color: var(--mg-card) !important; border-radius: 20px !important;
    box-shadow: 0 2px 14px rgba(15,23,42,0.05) !important; padding: 22px 24px !important;
}
/* 기본 선택 버튼(분봉 · 내역 종류 등)도 알약 모양으로 통일 */
div[data-testid="stButtonGroup"] div[role="radiogroup"] { background: var(--mg-soft); border-radius: 12px; padding: 4px; gap: 2px !important; width: fit-content; }
div[data-testid="stButtonGroup"] button[data-variant="segmented_control"] { border: 0 !important; background: transparent !important; border-radius: 9px !important; min-height: 32px !important; height: 32px; padding: 0 13px !important; box-shadow: none !important; }
div[data-testid="stButtonGroup"] button[data-variant="segmented_control"] p { font-size: 13.5px !important; font-weight: 600 !important; color: var(--mg-mid2) !important; }
div[data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"] { background: var(--mg-raise) !important; box-shadow: 0 1px 4px rgba(15,23,42,0.08) !important; }
div[data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"] p { color: var(--mg-text) !important; font-weight: 800 !important; }
/* 빈 화면 안내 */
.es { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 6px; padding: 14px 8px; }
.es .ei { width: 48px; height: 48px; border-radius: 16px; background: var(--mg-soft); display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 4px; }
.es b { font-size: 15px; font-weight: 800; color: var(--mg-text); letter-spacing: -0.02em; }
.es span { font-size: 13px; color: var(--mg-sub); line-height: 1.6; }
.es-card { padding: 26px 20px !important; }
/* 맨 아래 안내 */
.mg-foot { margin: 40px 0 10px; padding: 22px 4px 90px; border-top: 1px solid var(--mg-line); display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--mg-faint); text-align: center; }
.mg-foot b { color: var(--mg-sub); font-weight: 800; }
/* 바로가기 칩 */
.jumps { display: flex; gap: 6px; overflow-x: auto; scrollbar-width: none; margin: 10px 0 14px; padding-bottom: 2px; }
.jumps::-webkit-scrollbar { display: none; }
.jump { flex-shrink: 0; border: 1px solid var(--mg-border); background: var(--mg-card); color: var(--mg-mid); font-family: inherit; font-size: 12.5px; font-weight: 700; padding: 7px 12px; border-radius: 999px; cursor: pointer; white-space: nowrap; }
.jump:hover { color: var(--mg-accent); border-color: var(--mg-accent); }
/* 매매 습관 리포트 */
.ins-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }
.ins { display: flex; gap: 12px; padding: 14px 16px; border-radius: 14px; background: var(--mg-tile); border-left: 3px solid transparent; }
.ins.bad { border-left-color: #F04452; } .ins.good { border-left-color: #089981; } .ins.info { border-left-color: var(--mg-accent); }
.ins-ic { font-size: 20px; line-height: 1.2; }
.ins b { display: block; font-size: 14.5px; font-weight: 800; color: var(--mg-text); letter-spacing: -0.02em; line-height: 1.4; }
.ins p { margin: 5px 0 0; font-size: 12.5px; color: var(--mg-mid2); line-height: 1.6; }
@media (max-width: 768px) { .ins-list { grid-template-columns: 1fr; } .ins { padding: 12px 13px; } .ins b { font-size: 14px; } }
/* PNL 캘린더 */
div[class*="st-key-cal_card"] { background-color: var(--mg-card) !important; border-radius: 20px !important; box-shadow: var(--mg-shadow) !important; padding: 20px 24px 22px !important; }
div[class*="st-key-cal_head"] { justify-content: space-between !important; }
div[class*="st-key-cal_head"] [data-testid="stMarkdownContainer"] { margin: 0 !important; }
div[class*="st-key-cal_nav"] { gap: 4px !important; }
div[class*="st-key-cal_nav"] button { width: 32px !important; height: 32px !important; min-height: 32px !important; padding: 0 !important; border-radius: 10px !important; background: var(--mg-soft) !important; border: 0 !important; }
div[class*="st-key-cal_nav"] button:disabled { opacity: .35; }
.cal-title { font-size: 17px; font-weight: 800; color: var(--mg-text); letter-spacing: -0.02em; line-height: 36px; }
.cal-ym { font-size: 14.5px; font-weight: 800; color: var(--mg-text); min-width: 64px; text-align: center; font-variant-numeric: tabular-nums; }
.cal-sum { display: flex; align-items: baseline; gap: 10px; margin: 6px 0 14px; }
.cal-sum span { font-size: 24px; font-weight: 800; letter-spacing: -0.02em; color: var(--mg-text); }
.cal-sum span.up { color: #089981; } .cal-sum span.down { color: #F04452; }
.cal-sum small { font-size: 12.5px; color: var(--mg-sub); font-weight: 600; }
.cal { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; }
.cal-h { font-size: 11.5px; font-weight: 700; color: var(--mg-sub); text-align: center; padding-bottom: 2px; }
.cal-h.sun { color: #F04452; } .cal-h.sat { color: #3182F6; }
.cal-c { position: relative; min-height: 64px; border-radius: 12px; background: var(--mg-tile); padding: 7px 8px; display: flex; flex-direction: column; gap: 2px; overflow: hidden; }
.cal-c.empty { background: transparent; }
.cal-c.off { opacity: .45; }
.cal-c.today { box-shadow: inset 0 0 0 2px var(--mg-accent); }
.cal-c span { font-size: 11.5px; font-weight: 700; color: var(--mg-sub); }
.cal-c b { font-size: 13px; font-weight: 800; color: var(--mg-text); margin-top: auto; font-variant-numeric: tabular-nums; letter-spacing: -0.02em; white-space: nowrap; }
.cal-c.pos b, .cal-c.neg b, .cal-c.pos span, .cal-c.neg span { color: #fff; }
.cal-c.pos-lt b { color: #067A67; } .cal-c.neg-lt b { color: #D23343; }
html[data-mg-theme="dark"] .cal-c.pos-lt b { color: #3DDBB8; } html[data-mg-theme="dark"] .cal-c.neg-lt b { color: #FF7A86; }
@media (prefers-color-scheme: dark) { html:not([data-mg-theme="light"]) .cal-c.pos-lt b { color: #3DDBB8; } html:not([data-mg-theme="light"]) .cal-c.neg-lt b { color: #FF7A86; } }
.cal-c.pos-lt i, .cal-c.neg-lt i { color: var(--mg-sub); }
/* 언제 잘 벌까 카드 */
div[class*="st-key-hour_head"] { justify-content: space-between !important; }
div[class*="st-key-hour_head"] [data-testid="stMarkdownContainer"] { margin: 0 !important; }
div[class*="st-key-hour_view_box"] div[role="radiogroup"] { background: var(--mg-soft); border-radius: 12px; padding: 4px; gap: 2px !important; }
div[class*="st-key-hour_view_box"] button[data-variant="segmented_control"] { border: 0 !important; background: transparent !important; border-radius: 9px !important; min-height: 32px !important; height: 32px; padding: 0 14px !important; box-shadow: none !important; }
div[class*="st-key-hour_view_box"] button[data-variant="segmented_control"] p { font-size: 13.5px !important; font-weight: 600 !important; color: var(--mg-mid2) !important; }
div[class*="st-key-hour_view_box"] button[aria-checked="true"] { background: var(--mg-raise) !important; box-shadow: 0 1px 4px rgba(15,23,42,0.08) !important; }
div[class*="st-key-hour_view_box"] button[aria-checked="true"] p { color: var(--mg-text) !important; font-weight: 800 !important; }
.hour-sum { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 12.5px; color: var(--mg-sub); margin: 4px 0 2px; }
.hour-sum b { font-weight: 800; margin-left: 4px; } .hour-sum .up { color: #089981; } .hour-sum .down { color: #F04452; }
.cal-c i { font-style: normal; font-size: 10px; color: rgba(255,255,255,.85); font-weight: 600; }
@media (max-width: 768px) {
  div[class*="st-key-cal_card"] { padding: 16px 14px 16px !important; }
  .cal { gap: 4px; } .cal-c { min-height: 48px; padding: 5px 4px; border-radius: 9px; align-items: center; }
  .cal-c span { font-size: 10.5px; } .cal-c b { font-size: 10.5px; } .cal-c i { display: none; }
  .cal-sum span { font-size: 21px; }
}
div[class*="st-key-pos_container_"] {
    background-color: var(--mg-card) !important; border-radius: 20px !important;
    box-shadow: 0 2px 14px rgba(15,23,42,0.05) !important; padding: 14px 24px 14px !important; margin-bottom: 18px !important;
}

button[data-baseweb="tab"] p { color: var(--mg-sub) !important; font-weight: 600 !important; font-size: 14.5px !important; }
button[data-baseweb="tab"][aria-selected="true"] p { color: #3182F6 !important; font-weight: 800 !important; }
div[data-baseweb="tab-highlight"] { background-color: #3182F6 !important; }

.pos-box { padding: 4px 14px; flex: 1 1 190px; }
.tcard { height: 320px; }
.pos-divider { border-left: 1px solid var(--mg-border); }

.stButton>button { height: 38px; padding: 0 16px; border-radius: 999px; border: 1px solid var(--mg-border); background-color: var(--mg-card); color: var(--mg-text); font-weight: 600; white-space: nowrap; box-shadow:none; }
.stButton>button:hover { border-color: #3182F6; color: #3182F6; }

.pill { display:inline-block; font-size:11px; font-weight:800; padding:3px 9px; border-radius:999px; vertical-align:middle; }
.note-text { font-size:12px; line-height:1.7; color:var(--mg-sub); margin:6px 2px 0; }
.err-box { background:var(--mg-errbg); border:1px solid rgba(240,68,82,0.25); color:#C0303D; border-radius:14px; padding:12px 16px; font-size:13px; margin-bottom:14px; line-height:1.6; }

.log-day { position: sticky; top: 0; z-index: 1; display: flex; justify-content: space-between; align-items: baseline; padding: 14px 4px 8px; background: var(--mg-card); border-bottom: 1px solid var(--mg-line); }
.log-day span { font-size: 13.5px; font-weight: 800; color: var(--mg-text); } .log-day small { font-size: 12px; color: var(--mg-sub); font-weight: 600; }
.log-day b { font-size: 13.5px; font-weight: 800; font-variant-numeric: tabular-nums; }
.log-day + .log-row { padding-top: 12px; }
.log-row { display:flex; justify-content:space-between; align-items:center; padding:15px 6px; border-bottom:1px solid var(--mg-soft); }
.log-row:last-child { border-bottom:none; }
.log-left { display:flex; align-items:center; gap:13px; }
.sym-badge { width:38px; height:38px; min-width:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:13px; }
.row-title { font-size:14.5px; font-weight:700; color:var(--mg-text); }
.row-sub { font-size:12px; color:var(--mg-sub); margin-top:3px; }
.row-right { text-align:right; }
.row-price { font-size:12px; color:var(--mg-sub); margin-bottom:4px; }
.row-pnl { font-size:14.5px; font-weight:800; white-space:nowrap; }
.log-left { min-width:0; }
.log-left > div:last-child { min-width:0; }
.row-right { flex-shrink:0; padding-left:10px; }
.row-price { white-space:nowrap; }
.chip { display:inline-block; font-size:10.5px; font-weight:700; padding:2px 8px; border-radius:999px; margin-left:4px; }

@media (max-width: 768px) {
    .block-container { padding-top: 0.8rem; }
    div[class*="st-key-topnav_"] { height: 60px; gap: 16px !important; margin-bottom: 20px; padding: 0 16px !important; }
    .nav-logo .word { font-size: 18px; }
    .nav-logo .tag { display: none; }
    div[class*="st-key-navlink_"] a { padding: 6px 8px !important; gap: 4px; }
    div[class*="st-key-navlink_"] a p { font-size: 13px !important; }
    div[class*="st-key-navlink_"] a > span:has([data-testid="stIconMaterial"]) { display: none !important; }
    /* 휴대폰 메뉴: 윗줄 로고 + 다크 모드, 아랫줄 메뉴 5개를 꽉 차게 */
    div[class*="st-key-topnav_"] { height: auto !important; flex-wrap: wrap !important; row-gap: 10px !important; column-gap: 10px !important; justify-content: space-between; padding: 10px 14px 12px !important; }
    div[class*="st-key-topnav_"] > [data-testid="stElementContainer"]:has(.mg-theme-slot) { order: 2; margin-left: auto; }
    div[class*="st-key-topnav_"] > [data-testid="stLayoutWrapper"]:has(div[class*="st-key-navtabs"]) { order: 3; margin-left: 0 !important; width: 100% !important; flex: 1 1 100% !important; }
    div[class*="st-key-navtabs"] { width: 100% !important; padding: 3px !important; }
    div[class*="st-key-navtabs"] > div[class*="st-key-navlink_"], div[class*="st-key-navtabs"] > [data-testid="stLayoutWrapper"] { flex: 1 1 0 !important; width: auto !important; min-width: 0; }
    div[class*="st-key-navtabs"] > [data-testid="stLayoutWrapper"] > div[class*="st-key-navlink_"] { width: 100% !important; }
    div[class*="st-key-navlink_"] a { width: 100% !important; }
    div[class*="st-key-navlink_"], div[class*="st-key-navlink_"] [data-testid="stElementContainer"], div[class*="st-key-navlink_"] [data-testid="stPageLink"], div[class*="st-key-navlink_"] [data-testid="stPageLink"] > div { width: 100% !important; max-width: none !important; }
    div[class*="st-key-navlink_"] a > span { margin: 0 auto; }
    div[class*="st-key-navlink_"] a { justify-content: center; }
    body.mg-scrolled div[class*="st-key-topnav_"] > [data-testid="stElementContainer"] { display: none !important; }
    body.mg-scrolled div[class*="st-key-topnav_"] { padding: 8px 14px !important; row-gap: 0 !important; }
    .nav-logo .word { font-size: 16.5px !important; }
    .nav-logo svg { width: 18px; height: 18px; }
    .mg-theme-btn { width: 34px; height: 34px; border-radius: 10px; }
    .ph-title { font-size: 21px; }
    .pos-divider { border-left: none !important; border-top: 1px solid var(--mg-border) !important; padding-top: 14px !important; margin-top: 6px !important; }
    .hide-on-mobile { display: none !important; }
    /* 보유 포지션: 휴대폰에서는 2칸 격자로 촘촘하게 (종목 → 미실현 손익 → 가격 | 증거금) */
    .pos-wrap { display: grid !important; grid-template-columns: 1fr 1fr; gap: 12px 10px; }
    .pos-wrap .pos-box { padding: 0 !important; border: 0 !important; margin: 0 !important; }
    .pos-wrap .pb-sym { grid-column: 1 / -1; order: 1; }
    .pos-wrap .pb-pnl { grid-column: 1 / -1; order: 2; background: var(--mg-tile); border-radius: 14px; padding: 12px 14px !important; }
    .pos-wrap .pb-pnl > div:first-child { margin-bottom: 6px !important; }
    .pos-wrap .pb-px { order: 3; } .pos-wrap .pb-mg { order: 4; }
    .pos-wrap .pb-px > div:first-child, .pos-wrap .pb-mg > div:first-child { margin-bottom: 8px !important; font-size: 11.5px !important; }
    .pos-wrap .pb-px span[style*="width: 42px"], .pos-wrap .pb-mg span[style*="width: 42px"] { width: 34px !important; font-size: 11px !important; }
    .pos-wrap .pb-px span[style*="font-size: 17px"], .pos-wrap .pb-mg span[style*="font-size: 17px"] { font-size: 14.5px !important; }
    .pos-wrap .pb-sym div[style*="font-size: 22px"] { font-size: 19px !important; }
    .pos-wrap .pb-mg span[style*="font-size: 13px"] { display: none; }
    div[class*="st-key-pos_container_"] { padding: 14px 16px 12px !important; }
    /* 상단 PNL 카드: 오늘 · 이번 달은 나란히, 미실현은 아래 한 줄 */
    div[data-testid="stHorizontalBlock"]:has(.topc) { flex-wrap: wrap !important; gap: 10px !important; flex-direction: row !important; }
    div[data-testid="stHorizontalBlock"]:has(.topc) > div[data-testid="stColumn"] { flex: 1 1 calc(50% - 5px) !important; min-width: calc(50% - 5px) !important; width: calc(50% - 5px) !important; }
    div[data-testid="stHorizontalBlock"]:has(.topc) > div[data-testid="stColumn"]:nth-child(3) { flex-basis: 100% !important; width: 100% !important; }
    .topc { padding: 14px 15px !important; border-radius: 16px !important; }
    /* 카드 머리: 제목 아래에 보조 정보를 회색 한 줄로, 왼쪽 정렬 통일 (알약 배경 X) */
    .topc-h { flex-direction: column; align-items: flex-start; gap: 3px; }
    .topc-t { font-size: 13.5px; }
    .topc-chip { background: none !important; padding: 0 !important; border-radius: 0; font-size: 11.5px; font-weight: 600; color: var(--mg-sub); }
    .topc-v { font-size: 22px !important; margin-top: 10px; } .topc-k { font-size: 12px; }
    /* 미실현 PNL(아래 넓은 카드)은 예전처럼 제목 오른쪽에 알약 배지 */
    div[data-testid="stHorizontalBlock"]:has(.topc) > div[data-testid="stColumn"]:nth-child(3) .topc-h { flex-direction: row; align-items: center; justify-content: space-between; }
    div[data-testid="stHorizontalBlock"]:has(.topc) > div[data-testid="stColumn"]:nth-child(3) .topc-chip { background: var(--mg-soft) !important; padding: 4px 10px !important; border-radius: 999px; color: var(--mg-mid2); }
    .card-title { flex-direction: column; align-items: flex-start; gap: 3px; font-size: 16px; }
    .card-title span:last-child { font-size: 11.5px; font-weight: 600; }
    /* 주문 횟수 · 롱숏 · 승률 카드: 높이 자동 */
    .tcard { height: auto !important; gap: 14px; }
    /* 상세 매매 내역: 휴대폰에서는 날짜 / 수량·가격, 손익 / 수수료를 줄을 나눠서 깔끔하게 */
    .log-row { padding: 13px 2px; align-items: flex-start; }
    .log-left { gap: 10px; align-items: flex-start; }
    .sym-badge { width: 32px; height: 32px; min-width: 32px; font-size: 12px; margin-top: 2px; }
    .row-title { font-size: 14px; white-space: nowrap; }
    .row-title .pill { font-size: 10px; padding: 2px 7px; }
    .row-sub { font-size: 11.5px; line-height: 1.55; }
    .row-sub .rs-sep, .row-price .rs-sep { display: none; }
    .row-sub .rs-d, .row-price .rs-d { display: block; }
    .row-price { font-size: 11px; line-height: 1.5; margin-bottom: 3px; }
    .row-pnl { font-size: 14px; }
    .row-pnl .chip { font-size: 10px; padding: 2px 6px; }
    .kpi-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
    .pt-grid { grid-template-columns: repeat(2, minmax(0,1fr)); gap: 8px; }
    div[data-testid="stButtonGroup"] button { padding: 0 10px !important; min-height: 34px !important; }
    div[data-testid="stButtonGroup"] button p { font-size: 13px !important; }
    .pt { padding: 14px; min-height: 150px; }
    .pt-value { font-size: 22px; }
    .acc-grid { grid-template-columns: repeat(2, minmax(0,1fr)); gap: 8px; } .acc-t { padding: 12px 13px; } .acc-t b { font-size: 17px; } .acc-t > span { font-size: 11.5px; }
    /* 성과 지표 칸: 글자 줄바꿈 없이 깔끔하게 */
    .d-only { display: none !important; } .m-only { display: inline !important; }
    .pt-label { font-size: 13px; }
    .pt-foot { font-size: 11.5px; }
    .pt-foot > span { display: flex; flex-direction: column; gap: 2px; }
    .pt-foot > span:last-child:not(:first-child) { text-align: right; align-items: flex-end; }
    .streak { flex-wrap: nowrap; gap: 3px; }
    .streak .sd { flex: 1 1 0; width: auto; max-width: 14px; height: 12px; border-radius: 3px; }
    .bar-row { grid-template-columns: 1fr auto; }
    .bar-row .bar { display: none; }
    .kpi { border-left: none !important; padding-left: 0 !important; border-top: 1px solid var(--mg-soft); }
}
</style>
""").replace("__THEME_VARS__", THEME_CSS))


NAV_PAGES = [("history", "views/history.py", "히스토리", ":material/receipt_long:"),
             ("chart", "views/chart.py", "차트", ":material/candlestick_chart:"),
             ("market", "views/market.py", "시장", ":material/public:"),
             ("coins", "views/coins.py", "코인", ":material/currency_bitcoin:"),
             ("tools", "views/tools.py", "도구", ":material/calculate:")]


def nav(current, dark=False):
    """전체 폭 상단 헤더: 로고 + 메뉴."""
    mode = "dark" if dark else "light"
    with st.container(key=f"topnav_{mode}", horizontal=True, vertical_alignment="center"):
        html("<div class='nav-logo'><svg viewBox='0 0 24 24' width='22' height='22'><rect x='3' y='12' width='4' height='9' rx='1.5' fill='#2459ED' opacity='.45'/>"
             "<rect x='10' y='7' width='4' height='14' rx='1.5' fill='#2459ED' opacity='.7'/><rect x='17' y='3' width='4' height='18' rx='1.5' fill='#2459ED'/></svg>"
             "<span class='word'>Mung9_</span><span class='tag'>Trading</span></div>")
        # 컴퓨터: [로고] ...... [메뉴 탭][다크 모드]  /  휴대폰: 윗줄 [로고 ... 다크 모드], 아랫줄 메뉴 탭 (CSS order)
        # 다크 모드 버튼은 lib/theme.py 스크립트가 빈 자리에 채워 넣음
        with st.container(key="navtabs", horizontal=True, vertical_alignment="center", width="content"):
            for key, path, label, icon in NAV_PAGES:
                with st.container(key=f"navlink_{key}_{'on' if key == current else 'off'}", width="content"):
                    st.page_link(path, label=label, icon=icon)
        html("<div class='mg-theme-slot'></div>")


def empty_state(icon, title, sub=""):
    """빈 화면 안내: 아이콘 + 굵은 한 줄 + 설명."""
    return (f"<div class='es'><div class='ei'>{icon}</div><b>{title}</b>"
            + (f"<span>{sub}</span>" if sub else "") + "</div>")


def footer():
    """모든 화면 맨 아래: 데이터 출처 · 안내."""
    html("<div class='mg-foot'><div><b>Mung9_</b> Trading Journal</div>"
         "<div>데이터 Bitget · CoinGecko · Upbit · Binance · Bybit · OKX · TradingView</div>"
         "<div>정보 제공용이며 투자 판단과 책임은 본인에게 있어요</div></div>")


def breaking_html(n_pos):
    """긴급 띠: 글씨는 가만히, 뒤 배경 줄무늬가 계속 흐름."""
    return (f"<div class='mg-brk'><div class='tag'><i></i>LIVE</div>"
            f"<div class='msg'>🚨 인생배팅 / 승부 보는 중<em>포지션 {n_pos}개</em></div></div>")


def title_row(title, right_html, on_refresh):
    """섹션 제목 (왼쪽) + 상태 배지·새로고침 버튼 (오른쪽)."""
    with st.container(key="page_head", horizontal=True, vertical_alignment="center"):
        html(f"<div class='ph-title'>{title}</div>")
        with st.container(horizontal=True, vertical_alignment="center", width="content", gap="small"):
            html(right_html)
            with st.container(key="refresh_btn", width="content"):
                # 누르는 순간(화면을 그리기 전에) 실행 → 예전 화면을 한 번 더 그리지 않고 바로 로딩 화면으로
                st.button("", icon=":material/refresh:", help="모든 데이터 새로고침", on_click=on_refresh)


# 처음 거래 내역을 불러올 때 보여주는 로딩 화면
# 로딩 화면 가운데 영상/움짤 자리.
# Streamlit Secrets에 LOADER_MEDIA = "https://....gif" (또는 .mp4 / .webm) 를 넣으면 그걸 보여줌.
# 없으면 static/loader.gif, 그것도 없으면 캔들이 하나씩 그려지는 짧은 애니메이션.
_CANDLES = [(30, 18, 1), (40, 22, 1), (34, 16, 0), (48, 26, 1), (44, 14, 0), (58, 30, 1), (52, 18, 0),
            (66, 28, 1), (60, 16, 0), (74, 30, 1), (70, 14, 0), (84, 26, 1)]


def _loader_media():
    try:
        url = str(st.secrets.get("LOADER_MEDIA", "") or "").strip()
    except Exception:
        url = ""
    if not url:
        # 사이트에 넣어둔 로딩 움짤 (static/loader.gif) 이 있으면 그걸 씀
        from pathlib import Path as _P
        if (_P(__file__).parent.parent / "static" / "loader.gif").exists():
            return '<img src="app/static/loader.gif" alt="" style="aspect-ratio:540/316">'
    if url:
        u = url.split("?")[0].lower()
        if u.endswith((".mp4", ".webm", ".mov")):
            return f'<video src="{url}" autoplay muted loop playsinline></video>'
        return f'<img src="{url}" alt="">'
    bars = []
    for k, (top, h, up) in enumerate(_CANDLES):
        x = 14 + k * 26
        y = 120 - top
        c = "#0ECB81" if up else "#F6465D"
        bars.append(f'<g class="cd" style="animation-delay:{k * 0.12:.2f}s"><line x1="{x + 7}" y1="{y - 8}" x2="{x + 7}" y2="{y + h + 8}" stroke="{c}" stroke-width="2"/>'
                    f'<rect x="{x}" y="{y}" width="14" height="{h}" rx="3" fill="{c}"/></g>')
    pts = " ".join(f"{14 + k * 26 + 7},{120 - top + (0 if up else h)}" for k, (top, h, up) in enumerate(_CANDLES))
    return (f'<svg viewBox="0 0 330 130" preserveAspectRatio="xMidYMid meet">{"".join(bars)}'
            f'<polyline class="ln" points="{pts}" fill="none" stroke="var(--mg-accent)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>')


_LOADER_CSS = """
<style>
@keyframes mg-bar { 0%,100% { transform: scaleY(.45); opacity: .45; } 50% { transform: scaleY(1); opacity: 1; } }
@keyframes mg-prog { 0% { left: -40%; } 100% { left: 100%; } }
@keyframes mg-cd { 0% { opacity: 0; transform: scaleY(.2); } 12%, 82% { opacity: 1; transform: scaleY(1); } 100% { opacity: 0; transform: scaleY(1); } }
@keyframes mg-ln { 0% { stroke-dashoffset: 700; } 70%, 100% { stroke-dashoffset: 0; } }
.mg-load { background:var(--mg-card); border-radius:20px; box-shadow:var(--mg-shadow); padding:28px 28px 26px; margin: 14px 0 18px;
  display:flex; flex-direction:column; align-items:center; text-align:center; }
.mg-t { font-size:17px; font-weight:800; color:var(--mg-text); letter-spacing:-0.02em; }
.mg-s { font-size:13px; color:var(--mg-sub); margin-top:6px; line-height:1.6; }
.mg-prog { position:relative; width:220px; max-width:70%; height:4px; border-radius:2px; background:var(--mg-sk1); overflow:hidden; margin-top:16px; }
.mg-prog::after { content:''; position:absolute; top:0; width:40%; height:100%; border-radius:2px; background:var(--mg-accent); animation: mg-prog 1.2s ease-in-out infinite; }
/* 가운데 영상·움짤 자리: 16:9 상자에 꽉 맞게 */
.mg-media { width:100%; max-width:420px; aspect-ratio:16/9; border-radius:16px; overflow:hidden; background:var(--mg-tile); margin-bottom:20px;
  display:flex; align-items:center; justify-content:center; }
.mg-media img, .mg-media video { width:100%; height:100%; object-fit:cover; display:block; }
.mg-media svg { width:88%; height:auto; }
.mg-media .cd { transform-box: fill-box; transform-origin: bottom; animation: mg-cd 2.6s ease-out infinite both; }
.mg-media .ln { stroke-dasharray: 700; animation: mg-ln 2.6s ease-in infinite; animation-delay: .25s; opacity:.85; }
@media (max-width:768px) { .mg-load { padding:22px 18px 22px; } .mg-media { max-width:100%; } }
</style>
"""


def loader_html():
    return (_LOADER_CSS + '<div class="mg-load"><div class="mg-media">' + _loader_media() + '</div>'
            '<div class="mg-t">거래 내역을 불러오고 있어요</div>'
            '<div class="mg-s">Bitget 체결 · 펀딩비 · 입금 내역 확인 중</div>'
            '<div class="mg-prog"></div></div>')


LOADER_HTML = loader_html()  # 예전 코드 호환용 (기본 애니메이션)


# 포지션 불러오는 동안 보여주는 자리 표시 카드
_SK = "background:linear-gradient(90deg,var(--mg-sk1) 0%,var(--mg-sk2) 40%,var(--mg-sk1) 80%);background-size:800px 100%;animation:mg-shine 1.3s linear infinite;border-radius:8px;"
POS_SKELETON = f"""
<style>@keyframes mg-shine {{ 0% {{ background-position: -400px 0; }} 100% {{ background-position: 400px 0; }} }}
@keyframes mg-dot {{ 0%,100% {{ opacity:.3; transform:scale(.8); }} 50% {{ opacity:1; transform:scale(1); }} }}
.psk {{ background:var(--mg-card); border-radius:20px; box-shadow:0 2px 14px rgba(15,23,42,0.05); padding:18px 24px 20px; margin-bottom:18px; }}
.psk-row {{ display:grid; grid-template-columns:repeat(4,1fr); gap:0; }}
.psk-col {{ padding:6px 14px; border-left:1px solid var(--mg-border); display:flex; flex-direction:column; gap:10px; }}
.psk-col:first-child {{ border-left:none; padding-left:0; }}
.psk-st {{ display:flex; align-items:center; gap:8px; margin-top:16px; padding-top:14px; border-top:1px solid var(--mg-soft); font-size:12.5px; color:var(--mg-sub); font-weight:600; }}
.psk-st i {{ width:6px; height:6px; border-radius:50%; background:#3182F6; animation:mg-dot 1s ease-in-out infinite; }}
.psk-st i:nth-child(2) {{ animation-delay:.15s; }} .psk-st i:nth-child(3) {{ animation-delay:.3s; margin-right:4px; }}
@media (max-width:768px) {{ .psk-row {{ grid-template-columns:1fr 1fr; row-gap:14px; }} .psk-col:nth-child(3) {{ border-left:none; padding-left:0; }} }}
</style>
<div class="psk"><div class="psk-row">
<div class="psk-col"><div style="{_SK}width:60px;height:11px;"></div><div style="{_SK}width:150px;height:24px;"></div><div style="{_SK}width:110px;height:11px;"></div></div>
<div class="psk-col"><div style="{_SK}width:80px;height:11px;"></div><div style="{_SK}width:130px;height:18px;"></div><div style="{_SK}width:130px;height:18px;"></div></div>
<div class="psk-col"><div style="{_SK}width:90px;height:11px;"></div><div style="{_SK}width:120px;height:26px;"></div><div style="{_SK}width:70px;height:13px;"></div></div>
<div class="psk-col"><div style="{_SK}width:100px;height:11px;"></div><div style="{_SK}width:120px;height:18px;"></div><div style="{_SK}width:120px;height:18px;"></div></div>
</div>
<div class="psk-st"><i></i><i></i><i></i>Bitget에서 실시간 포지션 확인 중</div></div>
"""

TOPCARD_SKELETON = f"""<div class="card topc">
<div class="topc-h"><span class="topc-t">{{title}}</span><span style="{_SK}width:96px;height:22px;border-radius:999px;"></span></div>
<div style="{_SK}width:150px;height:32px;margin-top:12px;"></div>
<div style="{_SK}width:80px;height:14px;margin-top:8px;"></div></div>"""
