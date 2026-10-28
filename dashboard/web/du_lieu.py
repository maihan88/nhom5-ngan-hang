"""
du_lieu.py – Đọc dữ liệu, kết quả thống kê và mô hình cho mọi trang (có cache).

Dữ liệu đọc qua src/data_loader.py của Nghi nên quy ước (giai đoạn, thứ tự ngân hàng, màu) giống notebook.
Cache tự làm mới khi file CSV trong data/ hoặc outputs/ đổi (khóa = thời điểm sửa file), nên chỉ cần
chạy lại pipeline + dong_bo_du_lieu.py là web cập nhật, kể cả mô hình.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from src import config as cf
from src import data_loader as dl
from src import thong_ke as tk
from web import mo_hinh as mh

GOC = Path(__file__).resolve().parents[1]
THU_MUC_KQ = GOC / "outputs"
THU_MUC_MO_HINH = GOC / "mo_hinh"


def _van_tay(*thu_muc):
    """Tên + thời điểm sửa của mọi CSV/.pkl/.json – làm khóa cache (tham số không gạch dưới để Streamlit băm)."""
    return tuple(sorted((p.name, p.stat().st_mtime_ns) for t in thu_muc for duoi in ("*.csv", "*.pkl", "*.json")
                        for p in Path(t).glob(duoi)))


@st.cache_data(show_spinner="Đang đọc dữ liệu…")
def _doc(van_tay):
    ds = dl.doc_tat_ca()
    for ten in ds:
        if "ma_nh" in ds[ten]:
            ds[ten]["ma_nh"] = ds[ten]["ma_nh"].astype(str)
        if "loai_hinh_so_huu" in ds[ten]:
            ds[ten]["loai_hinh_so_huu"] = ds[ten]["loai_hinh_so_huu"].astype(str)
    nam = tk.tinh_chi_so_nam(ds["tai_chinh_quy"])
    nam["ma_nh"] = nam["ma_nh"].astype(str)
    ds["chi_so_nam"] = nam
    ds["xep_hang"] = {c: tk.xep_hang(nam, c) for c in ["roe_nam", "roa_nam"]}
    for f in ["thong_ke_mo_ta", "kiem_dinh_nhom", "tuong_quan"]:
        p = THU_MUC_KQ / f"{f}.csv"
        ds[f] = pd.read_csv(p, encoding="utf-8-sig") if p.exists() else None
    p = cf.THU_MUC_DATA / "data_dictionary.csv"
    ds["tu_dien"] = pd.read_csv(p, encoding="utf-8-sig") if p.exists() else None
    p = THU_MUC_KQ / "ml" / "k_selection.csv"
    ds["chon_k_quan"] = pd.read_csv(p, encoding="utf-8-sig") if p.exists() else None
    return ds


def tat_ca():
    """dict các bảng: tai_chinh_quy, gia_ngay, gia_quy, su_kien_chi_tiet, su_kien_quy, tong_hop, chi_so_nam,
    xep_hang {roe_nam, roa_nam}, thong_ke_mo_ta, kiem_dinh_nhom, tuong_quan, tu_dien, chon_k_quan."""
    return _doc(_van_tay(cf.THU_MUC_DATA, THU_MUC_KQ, THU_MUC_KQ / "ml"))


@st.cache_resource(show_spinner="Đang huấn luyện mô hình…")
def _mo_hinh(van_tay):
    b4 = tat_ca()["tong_hop"]
    return mh.nap_hoac_huan_luyen(b4, THU_MUC_MO_HINH), mh.phan_nhom(b4)


def du_bao():
    return _mo_hinh(_van_tay(cf.THU_MUC_DATA, THU_MUC_MO_HINH))[0]


def phan_nhom():
    return _mo_hinh(_van_tay(cf.THU_MUC_DATA, THU_MUC_MO_HINH))[1]


@st.cache_data
def _anh_chup(van_tay):
    ds, kq, pn = tat_ca(), du_bao(), phan_nhom()
    b4 = ds["tong_hop"]
    ky = b4["ky"].max()
    moi = b4[b4["ky"] == ky].copy()
    dong_db = kq["du_lieu"][kq["du_lieu"]["ky"] == ky]
    moi = moi.merge(dong_db[["ma_nh"]].assign(xac_suat=mh.xac_suat(kq, mh.MAC_DINH, dong_db)), on="ma_nh")
    moi = moi.merge(pn["du_lieu"][pn["du_lieu"]["ky"] == ky][["ma_nh", "nhom", "ten_nhom"]], on="ma_nh", how="left")

    g12 = gia_12_thang(ds["gia_ngay"])
    tuan = g12.set_index("ngay").groupby("ma_nh")["gia_dong_cua_dieu_chinh"].resample("W").last().dropna()
    moi["gia_12t"] = moi["ma_nh"].map(lambda m: tuan.loc[m].tolist() if m in tuan.index else [])
    moi["thay_doi_12t"] = moi["ma_nh"].map(g12.groupby("ma_nh")["thay_doi"].last())
    moi["ten"] = moi["ma_nh"].map(cf.TEN_DAY_DU)
    return moi.reset_index(drop=True), ky


def anh_chup():
    """Quý mới nhất của 8 ngân hàng: chỉ số, giá, chuỗi giá tuần 12 tháng, xác suất tăng quý tới
    (mô hình mặc định), nhóm. Trả về (DataFrame, ky)."""
    return _anh_chup(_van_tay(cf.THU_MUC_DATA, THU_MUC_MO_HINH))


def gia_12_thang(gia, den=None):
    """Giá ngày trong 12 tháng tính đến `den` (mặc định phiên cuối), bắt đầu từ phiên cuối cùng trước mốc 365 ngày,
    kèm cột thay_doi (%) so với phiên đầu. Dùng chung cho bảng xếp hạng, biểu đồ và hồ sơ để số khớp nhau."""
    den = gia["ngay"].max() if den is None else den
    g = gia[gia["ngay"] <= den]
    truoc = g[g["ngay"] <= den - pd.Timedelta(days=365)]["ngay"]
    moc = truoc.max() if len(truoc) else g["ngay"].min()
    g = g[g["ngay"] >= moc].sort_values(["ma_nh", "ngay"]).copy()
    g["thay_doi"] = (g["gia_dong_cua_dieu_chinh"] / g.groupby("ma_nh")["gia_dong_cua_dieu_chinh"].transform("first") - 1) * 100
    return g


def ds_ky():
    """Danh sách kỳ '2021Q1'.. kỳ cuối, đúng thứ tự."""
    return dl.thu_tu_ky()


def giai_doan():
    """Giai đoạn dữ liệu để ghi trong câu chữ: '2021–2025' khi năm cuối đủ 4 quý, ngược lại 'Q1/2021–Q2/2026'."""
    ky = ds_ky()
    dau, cuoi = ky[0], ky[-1]
    if cuoi.endswith("4"):
        return f"{dau[:4]}–{cuoi[:4]}"
    return f"Q{dau[-1]}/{dau[:4]}–Q{cuoi[-1]}/{cuoi[:4]}"
