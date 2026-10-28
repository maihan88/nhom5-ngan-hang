"""
Nhịp Ngân Hàng – bản tin dữ liệu 8 ngân hàng niêm yết (Nhóm 5 · Phân tích dữ liệu cho môi trường doanh nghiệp)

Chạy:  streamlit run app.py   (trong thư mục dashboard/)
"""
from pathlib import Path

import streamlit as st

from web import giao_dien as gd

GOC = Path(__file__).parent
st.set_page_config(page_title=f"{gd.TEN} – {gd.KHAU_HIEU}", page_icon=str(GOC / "assets/icon.svg"), layout="wide")
st.logo(str(GOC / "assets/logo.svg"), icon_image=str(GOC / "assets/icon.svg"), size="large")
gd.nap_css()

trang = st.navigation([
    st.Page("trang/ban_tin.py", title="Bản tin", default=True),
    st.Page("trang/ngan_hang.py", title="Ngân hàng"),
    st.Page("trang/so_sanh.py", title="So sánh"),
    st.Page("trang/du_bao.py", title="Dự báo"),
    st.Page("trang/phan_nhom.py", title="Phân nhóm"),
    st.Page("trang/phuong_phap.py", title="Phương pháp"),
], position="top")
trang.run()
