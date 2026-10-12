import streamlit as st

st.set_page_config(page_title="Mung's Trading", page_icon="📈", layout="wide")

# 새 코드가 올라왔는데 서버가 예전 lib 모듈을 메모리에 들고 있으면 ImportError/AttributeError가 남.
# 파일 수정 시각이 바뀌었으면 다시 불러와서 항상 최신 코드로 실행되게 함.
import importlib  # noqa: E402
import os  # noqa: E402

import lib.data  # noqa: E402
import lib.ui  # noqa: E402

for _m in (lib.data, lib.ui):
    _mt = os.path.getmtime(_m.__file__)
    if getattr(_m, "_loaded_mtime", _mt) != _mt:
        importlib.reload(_m)
    _m._loaded_mtime = _mt

lib.ui.inject_css()

pages = [
    st.Page("views/history.py", title="매매 히스토리", default=True),
    st.Page("views/chart.py", title="차트"),
    st.Page("views/market.py", title="시장", url_path="market"),
]
st.navigation(pages, position="hidden").run()
