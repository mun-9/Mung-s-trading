import streamlit as st

st.set_page_config(page_title="Mung9_ Trading", page_icon="static/favicon.png", layout="wide")

# 새 코드가 올라왔는데 서버가 예전 lib 모듈을 메모리에 들고 있으면 ImportError/AttributeError가 남.
# 파일 수정 시각이 바뀌었으면 다시 불러와서 항상 최신 코드로 실행되게 함.
import importlib  # noqa: E402
import os  # noqa: E402

import lib.data  # noqa: E402
import lib.ui  # noqa: E402
import lib.music  # noqa: E402
import lib.theme  # noqa: E402
import lib.alerts  # noqa: E402

for _m in (lib.data, lib.ui, lib.music, lib.theme, lib.alerts):
    _mt = os.path.getmtime(_m.__file__)
    if getattr(_m, "_loaded_mtime", _mt) != _mt:
        importlib.reload(_m)
    _m._loaded_mtime = _mt

lib.ui.inject_css()

# 왼쪽 아래 LP 음악 플레이어 (사이트에 한 번만 붙어서 페이지를 옮겨도 계속 재생)
st.html("<style>div[class*='st-key-mg_music_host']{position:absolute !important;height:0 !important;overflow:hidden;}</style>")
with st.container(key="mg_music_host"):
    lib.theme.inject()
    lib.alerts.inject()
    lib.music.inject()

pages = [
    st.Page("views/history.py", title="매매 히스토리", default=True),
    st.Page("views/chart.py", title="차트"),
    st.Page("views/market.py", title="시장", url_path="market"),
    st.Page("views/coins.py", title="코인", url_path="coins"),
    st.Page("views/tools.py", title="도구", url_path="tools"),
]
st.navigation(pages, position="hidden").run()
