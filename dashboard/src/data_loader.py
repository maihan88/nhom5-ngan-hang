"""
data_loader.py – Hàm đọc dữ liệu dùng chung (Nhóm 5 PTDL)

Cách dùng nhanh:
    from src.data_loader import doc_tat_ca, doc_tong_hop, doc_gia_ngay
    ds = doc_tat_ca()              # dict 6 bảng, đã lọc 2021–2025
    b4 = doc_tong_hop()            # bảng phân tích chính (160 dòng)
    gia = doc_gia_ngay()           # giá ngày, chỉ 2021-01-01 → 2025-12-31

Mọi bảng trả về đều có thêm:
    ky          : chuỗi "2021Q1" để làm trục x (bảng theo quý)
    ky_so       : số thứ tự quý 1..20 (để sắp xếp, tính tương quan hạng...)
    ngay_ky     : ngày cuối quý (Timestamp) nếu cần trục thời gian thật
    ma_nh, quy  : kiểu Categorical có thứ tự cố định theo config
"""
from pathlib import Path
import pandas as pd

from . import config as cf

KHOA = ["ma_nh", "quy", "nam"]


# ----------------------------------------------------------------------------
# Tiện ích
# ----------------------------------------------------------------------------
def _duong_dan(ten_bang, thu_muc=None):
    if ten_bang not in cf.TEN_FILE:
        raise KeyError(f"Không có bảng '{ten_bang}'. Chọn một trong: {list(cf.TEN_FILE)}")
    return Path(thu_muc or cf.THU_MUC_DATA) / cf.TEN_FILE[ten_bang]


def _ep_kieu_thu_tu(df):
    """ma_nh, quy, loai_hinh_so_huu -> Categorical có thứ tự, để groupby/biểu đồ
    luôn ra đúng thứ tự VCB, BID, CTG, ... và Q1..Q4."""
    if "ma_nh" in df:
        df["ma_nh"] = pd.Categorical(df["ma_nh"], categories=cf.DS_NGAN_HANG, ordered=True)
    if "quy" in df:
        df["quy"] = pd.Categorical(df["quy"], categories=cf.DS_QUY, ordered=True)
    if "loai_hinh_so_huu" in df:
        df["loai_hinh_so_huu"] = pd.Categorical(df["loai_hinh_so_huu"],
                                                categories=cf.DS_NHOM, ordered=True)
    return df


def them_cot_thoi_gian(df):
    """Thêm ky ('2021Q1'), ky_so (1..20) và ngay_ky (ngày cuối quý) cho bảng theo quý."""
    so_quy = df["quy"].astype(str).str[1].astype(int)
    df["ky"] = df["nam"].astype(str) + "Q" + so_quy.astype(str)
    df["ky_so"] = (df["nam"] - cf.NAM_BAT_DAU) * 4 + so_quy
    df["ngay_ky"] = pd.PeriodIndex(df["ky"], freq="Q").to_timestamp(how="end").normalize()
    return df


def them_nhom_so_huu(df):
    """Bảng nào thiếu loai_hinh_so_huu (2a, 2b, 3a, 3b) thì thêm vào từ config."""
    if "loai_hinh_so_huu" not in df and "ma_nh" in df:
        df["loai_hinh_so_huu"] = df["ma_nh"].astype(str).map(cf.NHOM_CUA_NH)
    return df


def thu_tu_ky():
    """Danh sách kỳ '2021Q1'.. kỳ cuối trong dữ liệu – truyền vào category_orders của plotly."""
    return [f"{n}Q{q}" for n in cf.DS_NAM for q in range(1, 5)
            if (n, q) <= (cf.NAM_KET_THUC, cf.QUY_CUOI)]


# ----------------------------------------------------------------------------
# Hàm đọc chính
# ----------------------------------------------------------------------------
def doc_bang(ten_bang, loc_giai_doan=True, thu_muc=None):
    """Đọc 1 bảng bất kỳ theo tên trong config.TEN_FILE.

    loc_giai_doan=True: bảng quý lọc từ Q1/2021 đến kỳ cuối trong dữ liệu; bảng giá ngày
    lọc đến ngày cuối kỳ đó (giá 12/2020 và giá sau kỳ cuối chỉ để tính nhãn, không vẽ).
    """
    df = pd.read_csv(_duong_dan(ten_bang, thu_muc))

    # Chuẩn hóa cột ngày
    for c in ["ngay", "ngay_bctc", "ngay_dau", "ngay_cuoi"]:
        if c in df:
            df[c] = pd.to_datetime(df[c])
    if ten_bang == "su_kien_chi_tiet":           # bảng 3a có giờ phút
        df["ngay_cong_bo"] = pd.to_datetime(df["ngay_cong_bo"])

    # Lọc giai đoạn
    if loc_giai_doan:
        if "nam" in df:
            ky = df["nam"] * 10 + df["quy"].str[1].astype(int)
            df = df[ky.between(cf.NAM_BAT_DAU * 10 + 1, cf.NAM_KET_THUC * 10 + cf.QUY_CUOI)]
        elif "ngay" in df:
            df = df[df["ngay"].between(cf.NGAY_BAT_DAU, cf.NGAY_KET_THUC)]

    df = df.copy()
    df = them_nhom_so_huu(df)
    if {"quy", "nam"} <= set(df.columns):
        df = them_cot_thoi_gian(df)
    df = _ep_kieu_thu_tu(df)

    sap_xep = [c for c in ["ma_nh", "nam", "quy", "ngay", "ngay_cong_bo"] if c in df]
    return df.sort_values(sap_xep).reset_index(drop=True)


def doc_tong_hop(**kw):
    """Bảng 4 – bảng phân tích chính cho câu 1, 2, 3 (160 dòng = 8 NH × 20 quý)."""
    df = doc_bang("tong_hop", **kw)
    # Cờ lọc 32 giá trị CAR thật (số VNDirect công bố + số nhóm tra thủ công), xem cf.CAR_NGUON_SO_THAT
    df["car_cong_bo"] = df["car_nguon"].isin(cf.CAR_NGUON_SO_THAT)
    return df


def doc_tai_chinh_quy(**kw):
    """Bảng 1 – dùng cho câu 1 (tính ROA/ROE năm từ LNST, tổng TS, VCSH)."""
    return doc_bang("tai_chinh_quy", **kw)


def doc_gia_ngay(**kw):
    """Bảng 2a – giá ngày, dùng cho biểu đồ xu hướng giá."""
    return doc_bang("gia_ngay", **kw)


def doc_gia_quy(**kw):
    return doc_bang("gia_quy", **kw)


def doc_su_kien_chi_tiet(**kw):
    """Bảng 3a – mỗi dòng 1 sự kiện, có ngay_cong_bo (datetime) để đánh dấu trên đường giá."""
    return doc_bang("su_kien_chi_tiet", **kw)


def doc_su_kien_quy(**kw):
    return doc_bang("su_kien_quy", **kw)


def doc_tat_ca(**kw):
    """Đọc cả 6 bảng, trả về dict {tên_bảng: DataFrame}."""
    ham = {
        "tai_chinh_quy": doc_tai_chinh_quy, "gia_ngay": doc_gia_ngay,
        "gia_quy": doc_gia_quy, "su_kien_chi_tiet": doc_su_kien_chi_tiet,
        "su_kien_quy": doc_su_kien_quy, "tong_hop": doc_tong_hop,
    }
    return {ten: f(**kw) for ten, f in ham.items()}


def loc(df, ma_nh=None, nam=None, nhom=None):
    """Bộ lọc dùng chung cho mọi hàm vẽ và cho ô chọn Streamlit.

    ma_nh, nam, nhom nhận 1 giá trị hoặc list; None = không lọc.
    """
    def _list(x):
        return None if x is None else ([x] if isinstance(x, (str, int)) else list(x))

    ma_nh, nam, nhom = _list(ma_nh), _list(nam), _list(nhom)
    m = pd.Series(True, index=df.index)
    if ma_nh is not None and "ma_nh" in df:
        m &= df["ma_nh"].astype(str).isin(ma_nh)
    if nam is not None:
        cot_nam = df["nam"] if "nam" in df else df["ngay"].dt.year
        m &= cot_nam.isin(nam)
    if nhom is not None and "loai_hinh_so_huu" in df:
        m &= df["loai_hinh_so_huu"].astype(str).isin(nhom)
    return df[m]
