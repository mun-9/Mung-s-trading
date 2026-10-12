import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from lib import data as D
from lib.ui import html, nav

nav("market")
html("<div class='ph-title' style='margin:2px 0 4px;'>시장</div>"
     "<div style='font-size:14px;color:#8B95A1;margin-bottom:14px;'>공포·탐욕, 김프, 펀딩비, 청산, 롱숏 비율을 한 화면에서. 시세는 자동으로 갱신돼요.</div>")

payload = {"usdkrw": D.fetch_usdkrw(),
           "lsExt": D.fetch_ls_external(("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"))}
page = (Path(__file__).parent / "market_app.html").read_text(encoding="utf-8")
components.html(page.replace("__DATA__", json.dumps(payload)), height=2600)
