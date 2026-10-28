"""
kiem_tra.py – Kiểm tra dữ liệu nhận từ khâu Thu thập & làm sạch (Nhóm 5 PTDL)

    from src.data_loader import doc_tat_ca
    from src.kiem_tra import kiem_tra_du_lieu
    bao_cao = kiem_tra_du_lieu(doc_tat_ca(loc_giai_doan=False))

Kết quả mỗi dòng: ĐẠT / LỖI / LƯU Ý.
  LỖI   = sai so với quy ước bàn giao, phải báo Hân sửa trước khi phân tích.
  LƯU Ý = dữ liệu hợp lệ nhưng ảnh hưởng tới cách phân tích/diễn giải.
"""
import numpy as np
import pandas as pd

from . import config as cf

KHOA = ["ma_nh", "quy", "nam"]
COT_CHINH = ["roa", "roe", "nim", "npl", "car", "ldr", "car_nguon", "loai_hinh_so_huu",
             "loi_nhuan_sau_thue", "tong_tai_san", "von_chu_so_huu",
             "ty_suat_sinh_loi_quy", "bien_dong_gia_max_min",
             "co_su_kien", "so_luong_su_kien", "xu_huong_quy_sau"]
MOC_DU_BAO_NGAY = 45   # mốc dự báo = cuối quý + 45 ngày (LABEL_LAG_DAYS bên pipeline thu thập)


class _SoGhi:
    def __init__(self):
        self.dong = []

    def ghi(self, nhom, noi_dung, dat, chi_tiet="", muc_loi="LỖI"):
        self.dong.append({"nhom_kiem_tra": nhom, "noi_dung": noi_dung,
                          "ket_qua": "ĐẠT" if dat else muc_loi, "chi_tiet": chi_tiet})

    def luu_y(self, nhom, noi_dung, chi_tiet):
        self.dong.append({"nhom_kiem_tra": nhom, "noi_dung": noi_dung,
                          "ket_qua": "LƯU Ý", "chi_tiet": chi_tiet})


def _s(df):
    """Bỏ Categorical để so sánh/merge an toàn."""
    d = df.copy()
    for c in ["ma_nh", "quy", "loai_hinh_so_huu"]:
        if c in d:
            d[c] = d[c].astype(str)
    return d


def kiem_tra_du_lieu(ds):
    """ds: dict từ doc_tat_ca(loc_giai_doan=False). Trả về DataFrame báo cáo."""
    sg = _SoGhi()
    b1, b2a, b2b = _s(ds["tai_chinh_quy"]), _s(ds["gia_ngay"]), _s(ds["gia_quy"])
    b3a, b3b, b4 = _s(ds["su_kien_chi_tiet"]), _s(ds["su_kien_quy"]), _s(ds["tong_hop"])
    bang_quy = {"bang1": b1, "bang2b": b2b, "bang3b": b3b, "bang4": b4}

    # ---- 1. Cấu trúc ---------------------------------------------------------
    so_dong = len(cf.DS_NGAN_HANG) * cf.SO_QUY
    for ten, d in bang_quy.items():
        sg.ghi("1. Cấu trúc", f"{ten}: đủ {so_dong} dòng", len(d) == so_dong, f"{len(d)} dòng")
        sg.ghi("1. Cấu trúc", f"{ten}: không trùng khóa ma_nh+quy+nam",
               not d.duplicated(KHOA).any(), f"{d.duplicated(KHOA).sum()} dòng trùng")
        du = d.groupby("ma_nh").size()
        sg.ghi("1. Cấu trúc", f"{ten}: đủ {len(cf.DS_NGAN_HANG)} ngân hàng × {cf.SO_QUY} quý",
               set(du.index) == set(cf.DS_NGAN_HANG) and (du == cf.SO_QUY).all(),
               ", ".join(f"{k}={v}" for k, v in du.items()))
    sg.ghi("1. Cấu trúc", "bang2a: không trùng ma_nh+ngay",
           not b2a.duplicated(["ma_nh", "ngay"]).any())

    # ---- 2. Thiếu dữ liệu ----------------------------------------------------
    # Nhãn quý t chỉ biết khi đã có giá tới mốc dự báo của quý t+1 (cuối quý t+1 + 45 ngày).
    # Các quý mới nhất chưa tới mốc đó thiếu nhãn là ĐÚNG: đó là các dòng cần dự báo.
    moc_sau = ((pd.PeriodIndex(b4["nam"].astype(str) + b4["quy"], freq="Q") + 1).end_time.normalize()
               + pd.Timedelta(days=MOC_DU_BAO_NGAY))
    chua_co_nhan = pd.Series(moc_sau > b2a["ngay"].max(), index=b4.index)
    thieu = b4[COT_CHINH].isna().sum()
    thieu["xu_huong_quy_sau"] = (b4["xu_huong_quy_sau"].isna() & ~chua_co_nhan).sum()
    sg.ghi("2. Thiếu dữ liệu", "bang4: các cột chính không có ô trống", thieu.sum() == 0,
           "không thiếu" if thieu.sum() == 0 else thieu[thieu > 0].to_dict())
    if chua_co_nhan.any():
        ky = sorted(set(b4.loc[chua_co_nhan, "quy"] + "/" + b4.loc[chua_co_nhan, "nam"].astype(str)))
        sg.luu_y("2. Thiếu dữ liệu", f"{int(chua_co_nhan.sum())} dòng chưa có nhãn xu_huong_quy_sau",
                 f"{', '.join(ky)}: chưa tới mốc dự báo quý sau → là các dòng cần dự báo, "
                 "không dùng để huấn luyện/đánh giá mô hình")
    rong_hop_le = b4.loc[b4["co_su_kien"] == 0, "loai_su_kien"].isna().all()
    sg.ghi("2. Thiếu dữ liệu", "Cột mô tả sự kiện chỉ trống khi co_su_kien = 0", rong_hop_le,
           f"{b4['loai_su_kien'].isna().sum()} ô trống hợp lệ")

    # ---- 3. CAR ---------------------------------------------------------------
    cb = b4[b4["car_nguon"].isin(cf.CAR_NGUON_SO_THAT)]
    dem_nguon = cb["car_nguon"].value_counts().to_dict()
    sg.ghi("3. CAR", "Có đúng 32 giá trị CAR thật (công bố + tra thủ công)", len(cb) == 32,
           f"{len(cb)} giá trị: " + ", ".join(f"{k} = {v}" for k, v in dem_nguon.items()))
    la = set(b4["car_nguon"].unique()) - set(cf.CAR_NGUON_SO_THAT) - {"dien_tiep_ky_truoc"}
    sg.ghi("3. CAR", "car_nguon chỉ gồm các giá trị đã biết", not la, f"giá trị lạ: {la}" if la else "")
    sg.ghi("3. CAR", "CAR công bố chỉ nằm ở Q4", set(cb["quy"]) == {"Q4"},
           f"quý: {sorted(set(cb['quy']))}")
    sg.ghi("3. CAR", "Mỗi ngân hàng có 4 năm công bố (2021–2024)",
           (cb.groupby("ma_nh").size() == 4).all(),
           f"năm có số công bố: {sorted(int(x) for x in cb['nam'].unique())}")
    tc = cb[cb["car_nguon"] == "tra_thu_cong"]
    if len(tc):
        sg.luu_y("3. CAR", f"{len(tc)} giá trị CAR tra thủ công (không phải số VNDirect)",
                 "; ".join(f"{r.ma_nh} {r.nam}: {r.car:.2f}" for r in tc.sort_values(["ma_nh", "nam"]).itertuples())
                 + " – nguồn trong data/manual/car_tra_thu_cong.csv")
    sg.luu_y("3. CAR", "Năm 2025 chưa có CAR công bố",
             "CAR cả 4 quý 2025 = số Q4/2024 điền tiếp → không dùng cho so sánh năm 2025")
    lap = cb.groupby("ma_nh")["car"].agg(lambda s: s.round(2).value_counts().max())
    nghi_van = cb[cb["ma_nh"].isin(lap[lap >= 3].index)]
    if len(nghi_van):
        chi_tiet = "; ".join(f"{nh}: {', '.join(f'{v:.2f}' for v in g.sort_values('nam')['car'])}"
                             for nh, g in nghi_van.groupby("ma_nh"))
        sg.luu_y("3. CAR", "Giá trị CAR lặp y hệt ≥ 3 năm (nghi là giá trị mặc định của nguồn)",
                 chi_tiet + " → cần đối chiếu BCTC năm/BCTN trước khi kiểm định câu 2")

    # ---- 4. Nhóm sở hữu -------------------------------------------------------
    nhom = b4.groupby("loai_hinh_so_huu")["ma_nh"].unique().apply(sorted).to_dict()
    dung = all(cf.NHOM_CUA_NH[nh] == g for g, ds_nh in nhom.items() for nh in ds_nh)
    sg.ghi("4. Nhóm sở hữu", "Quốc doanh = VCB, BID, CTG; còn lại Tư nhân", dung, str(nhom))

    # ---- 5. Nhất quán giữa các bảng -----------------------------------------
    def so_khop(bang_goc, ten, cot):
        m = b4.merge(bang_goc, on=KHOA, suffixes=("", "_g"))
        lech = [c for c in cot if not np.allclose(m[c], m[c + "_g"], equal_nan=True)]
        sg.ghi("5. Nhất quán", f"bang4 khớp {ten}", not lech, "lệch: " + ", ".join(lech) if lech else "khớp")
    so_khop(b1, "bang1", ["roa", "roe", "nim", "npl", "car", "ldr", "loi_nhuan_sau_thue", "tong_tai_san"])
    so_khop(b2b, "bang2b", ["ty_suat_sinh_loi_quy", "bien_dong_gia_max_min", "gia_dau_quy", "gia_cuoi_quy"])
    so_khop(b3b, "bang3b", ["so_luong_su_kien", "co_su_kien"] + [c for c in b3b if c.startswith("sk_")])

    dem_3a = b3a.groupby(KHOA).size().rename("dem")
    m = b3b.set_index(KHOA).join(dem_3a).fillna({"dem": 0})
    sg.ghi("5. Nhất quán", "Số sự kiện bang3b = số dòng bang3a theo quý",
           (m["dem"] == m["so_luong_su_kien"]).all(), f"tổng {int(m['dem'].sum())} sự kiện")

    # ---- 6. Công thức ---------------------------------------------------------
    r = (b4["gia_cuoi_quy"] / b4["gia_dau_quy"] - 1) * 100
    sg.ghi("6. Công thức", "ty_suat_sinh_loi_quy = (giá cuối/giá đầu − 1)×100",
           np.allclose(r, b4["ty_suat_sinh_loi_quy"], atol=1e-2))
    s = b4.sort_values(["ma_nh", "nam", "quy"])
    lien_ke = s.groupby("ma_nh")["gia_cuoi_quy"].shift(1)
    ok = np.allclose(lien_ke.dropna(), s.loc[lien_ke.notna(), "gia_dau_quy"], atol=1e-3)
    sg.ghi("6. Công thức", "Giá đầu quý t = giá cuối quý t−1", ok)
    sg.ghi("6. Công thức", "co_su_kien = 1 khi so_luong_su_kien > 0",
           ((b4["so_luong_su_kien"] > 0).astype(int) == b4["co_su_kien"]).all())
    co_nhan = b4[b4["xu_huong_quy_sau"].notna()]
    sg.ghi("6. Công thức", "xu_huong_quy_sau = 1 khi ty_suat_sinh_loi_quy_sau > 0",
           ((co_nhan["ty_suat_sinh_loi_quy_sau"] > 0).astype(int) == co_nhan["xu_huong_quy_sau"]).all())

    # ---- 7. Giá ngày ----------------------------------------------------------
    sg.ghi("7. Giá ngày", "Giá > 0 và cao nhất ≥ thấp nhất",
           (b2a["gia_dong_cua_dieu_chinh"] > 0).all()
           and (b2a["gia_cao_nhat_dieu_chinh"] >= b2a["gia_thap_nhat_dieu_chinh"]).all())
    phien = b2a.groupby("ma_nh")["ngay"].nunique()
    if phien.nunique() > 1:
        ngay_du = set(b2a["ngay"])
        thieu_txt = []
        for nh in phien[phien < phien.max()].index:
            t = sorted(ngay_du - set(b2a.loc[b2a["ma_nh"] == nh, "ngay"]))
            thieu_txt.append(f"{nh} thiếu {len(t)} phiên ({t[0]:%d/%m/%Y} → {t[-1]:%d/%m/%Y})")
        ngoai = all(pd.Timestamp(x) < pd.Timestamp(cf.NGAY_BAT_DAU)
                    for nh in phien[phien < phien.max()].index
                    for x in (set(b2a["ngay"]) - set(b2a.loc[b2a["ma_nh"] == nh, "ngay"])))
        sg.luu_y("7. Giá ngày", "Số phiên không đều giữa các mã",
                 "; ".join(thieu_txt) + (" – nằm ngoài giai đoạn, không ảnh hưởng" if ngoai else ""))
    ngay_2021 = b2a[b2a["ngay"] >= cf.NGAY_BAT_DAU].groupby("ma_nh")["ngay"].min()
    sg.ghi("7. Giá ngày", "Mọi mã có phiên đầu năm 2021 chung (mốc chuẩn hóa = 100)",
           ngay_2021.nunique() == 1, f"phiên gốc: {ngay_2021.iloc[0]:%d/%m/%Y}")

    # ---- 8. Ngoại lai (chỉ ghi nhận, không xóa) -------------------------------
    for c in cf.DS_CHI_SO + ["ty_suat_sinh_loi_quy"]:
        q1, q3 = b4[c].quantile([.25, .75])
        iqr = q3 - q1
        ngoai = b4[(b4[c] < q1 - 3 * iqr) | (b4[c] > q3 + 3 * iqr)]
        if len(ngoai):
            sg.luu_y("8. Ngoại lai (ngoài 3×IQR)", c,
                     "; ".join(f"{r.ma_nh} {r.quy}/{r.nam} = {r[c]:.2f}" for _, r in ngoai.iterrows()))
    am = b4[b4["loi_nhuan_sau_thue"] < 0]
    if len(am):
        sg.luu_y("8. Ngoại lai (ngoài 3×IQR)", "Quý lỗ (LNST < 0)",
                 "; ".join(f"{r.ma_nh} {r.quy}/{r.nam}: LNST {r.loi_nhuan_sau_thue:,.0f} tỷ, "
                           f"ROA {r.roa:.2f}%, NPL {r.npl:.2f}%" for _, r in am.iterrows()))

    return pd.DataFrame(sg.dong)


def tom_tat(bao_cao):
    """Đếm số dòng ĐẠT / LỖI / LƯU Ý."""
    return bao_cao["ket_qua"].value_counts().reindex(["ĐẠT", "LỖI", "LƯU Ý"], fill_value=0)
