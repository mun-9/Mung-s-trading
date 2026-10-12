import streamlit as st

st.set_page_config(page_title="Mung's Trading", page_icon="📈", layout="wide")

from lib.ui import inject_css  # noqa: E402

inject_css()

pages = [
    st.Page("views/history.py", title="매매 히스토리", default=True),
    st.Page("views/chart.py", title="차트"),
    st.Page("views/market.py", title="시장", url_path="market"),
]
st.navigation(pages, position="hidden").run()
