import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from lib import data as D
from lib.ui import html, nav

nav("market")
html("<div class='ph-title' style='margin:2px 0 4px;'>시장</div>"
     "<div style='font-size:14px;color:var(--mg-sub);margin-bottom:14px;'>공포·탐욕, 김프, 펀딩비, 청산, 롱숏 비율을 한 화면에서.</div>")

# 코드가 막 바뀐 직후 서버가 예전 모듈을 들고 있으면 새 함수가 없을 수 있어서, 그 경우 다시 불러옴
if not hasattr(D, "fetch_ls_external"):
    import importlib
    importlib.reload(D)

try:
    ls_ext = D.fetch_ls_external(("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"))
except Exception:
    ls_ext = {}

payload = {"usdkrw": D.fetch_usdkrw(), "lsExt": ls_ext}
page = (Path(__file__).parent / "market_app.html").read_text(encoding="utf-8")
components.html(page.replace("__DATA__", json.dumps(payload)), height=2600)
