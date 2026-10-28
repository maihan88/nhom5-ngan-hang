"""
ket_qua.py – Cấu trúc CỐ ĐỊNH của 4 file bảng kết quả bàn giao cho dashboard.

Hân đọc các file này bằng pd.read_csv(..., encoding="utf-8-sig").
Mọi bảng ở dạng "dài" (long format): mỗi dòng 1 kết quả, có cột để lọc theo
chỉ số / ngân hàng / năm → gắn thẳng vào ô chọn của Streamlit.
Cột không áp dụng cho dòng đó thì để trống (NaN), KHÔNG điền 0.
"""
import pandas as pd

from . import config as cf

CAU_TRUC = {
    # ---- Câu 1 + mô tả chung -------------------------------------------------
    "thong_ke_mo_ta": [
        "chi_so",            # roa, roe, nim, npl, car, ldr, ty_suat_sinh_loi_quy
        "cap_do",            # 'ma_nh' | 'nam' | 'loai_hinh_so_huu' | 'ma_nh_nam' | 'toan_bo'
        "ma_nh", "nam", "loai_hinh_so_huu",   # trống nếu cấp độ không dùng cột đó
        "mau_du_lieu",       # 'quy' (160 dòng) | 'car_cong_bo' (32 số CAR thật)
        "so_quan_sat", "trung_binh", "trung_vi", "do_lech_chuan", "nho_nhat", "lon_nhat",
        "don_vi",            # '%'
    ],
    # ---- Câu 1: xếp hạng --------------------------------------------------------
    "xep_hang_nam": [
        "chi_so",            # 'roa_nam' | 'roe_nam'
        "nam", "ma_nh", "loai_hinh_so_huu",
        "gia_tri",           # % – tổng LNST 4 quý / TB tổng TS (VCSH) cuối 4 quý × 100
        "hang",              # 1 = cao nhất
        "hang_nam_truoc", "thay_doi_hang",   # trống ở năm 2021
    ],
    # ---- Câu 2: kiểm định nhóm --------------------------------------------------
    "kiem_dinh_nhom": [
        "chi_so",            # nim, npl, car
        "mau_du_lieu",       # 'chinh' | 'khong_VPB' | 'car_chi_so_vndirect' | 'cap_ngan_hang'
        "don_vi_quan_sat",   # 'ngan_hang_nam' | 'ngan_hang_nam_cong_bo' | 'ngan_hang'
        "phan_tich",         # 'chinh' | 'kiem_tra_lai'
        "n_quoc_doanh", "n_tu_nhan",
        "tb_quoc_doanh", "tb_tu_nhan", "trung_vi_quoc_doanh", "trung_vi_tu_nhan",
        "shapiro_p_quoc_doanh", "shapiro_p_tu_nhan", "levene_p",
        "kiem_dinh",         # 'Student t' | 'Welch t' | 'Mann-Whitney U'
        "thong_ke", "p_value", "muc_y_nghia",
        "bac_bo_H0",         # True/False
        "gia_thuyet_H0", "gia_thuyet_H1", "ket_luan",
        "chenh_lech_tb",     # tb_quoc_doanh − tb_tu_nhan (điểm %)
        "ten_hieu_ung",      # 'Cohen d' | 'biserial hạng r'
        "do_lon_hieu_ung",   # dương = quốc doanh cao hơn
    ],
    # ---- Câu 3: tương quan ------------------------------------------------------
    "tuong_quan": [
        "chi_so",            # roa ... ldr
        "bien_so_sanh",      # 'ty_suat_sinh_loi_quy'
        "mau_du_lieu",       # 'chinh' (160) | 'car_cong_bo' | 'q4_2021_2024' | 'loai_bien_dong_chung'
                             # | 'thay_doi_chi_so' | 'cap_ngan_hang'
        "phan_tich",         # 'chinh' | 'kiem_tra_lai'
        "so_quan_sat",
        "pearson_r", "pearson_p", "pearson_p_hieu_chinh",
        "spearman_rho", "spearman_p", "spearman_p_hieu_chinh",
        "phuong_phap_hieu_chinh",   # vd 'holm'
        "xep_hang_do_manh",         # theo |spearman_rho|, 1 = mạnh nhất
    ],
}


def xuat_ket_qua(df, ten_bang, thu_muc=None):
    """Kiểm tra đủ cột, sắp đúng thứ tự cột rồi ghi CSV (utf-8-sig để Excel đọc được tiếng Việt)."""
    if ten_bang not in CAU_TRUC:
        raise KeyError(f"Tên bảng phải là một trong {list(CAU_TRUC)}")
    cot = CAU_TRUC[ten_bang]
    thieu = [c for c in cot if c not in df.columns]
    if thieu:
        raise ValueError(f"{ten_bang}: thiếu cột {thieu}")
    thu_muc = cf.THU_MUC_KET_QUA if thu_muc is None else thu_muc
    thu_muc.mkdir(parents=True, exist_ok=True)
    duong_dan = thu_muc / f"{ten_bang}.csv"
    ra = df[cot].copy()
    for c in ["ma_nh", "loai_hinh_so_huu"]:
        if c in ra:
            ra[c] = ra[c].astype("object")
    ra.to_csv(duong_dan, index=False, encoding="utf-8-sig", float_format="%.4f")
    return duong_dan


def khung_rong(ten_bang):
    """DataFrame rỗng đúng cấu trúc – Hân dùng để dựng trang dashboard trước khi có số."""
    return pd.DataFrame(columns=CAU_TRUC[ten_bang])
