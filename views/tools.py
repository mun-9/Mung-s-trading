from pathlib import Path

import streamlit.components.v1 as components

from lib.ui import html, nav

nav("tools")
html("<div class='ph-title' style='margin:2px 0 4px;'>도구</div>"
     "<div style='font-size:14px;color:var(--mg-sub);margin-bottom:14px;'>진입 전에 계산부터. 가격 알림 · 포지션 크기 · 청산가 · 목표가 · 평단 · 수수료 · 기대값.</div>")

page = (Path(__file__).parent / "tools_app.html").read_text(encoding="utf-8")
# 높이는 화면 안에서 내용 길이에 맞춰 자동으로 늘어남
components.html(page.replace("__DATA__", "{}"), height=1800)
