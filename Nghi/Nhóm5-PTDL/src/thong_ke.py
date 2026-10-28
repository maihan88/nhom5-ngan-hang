"""
thong_ke.py – Các hàm tính toán thống kê dùng chung (Nhóm 5 PTDL)

Phần 3 (câu 1):
  mo_ta, bang_mo_ta         : thống kê mô tả → đúng cấu trúc thong_ke_mo_ta.csv
  tinh_chi_so_nam            : ROA/ROE năm = tổng LNST 4 quý / TB (tổng TS | VCSH) cuối 4 quý
  xep_hang                   : xếp hạng 8 NH mỗi năm → đúng cấu trúc xep_hang_nam.csv
  thong_ke_vi_tri            : số năm đứng đầu / top 3, hạng TB, độ dao động hạng
  dan_dau_tung_nam           : NH hạng 1, hạng 2 và khoảng cách mỗi năm
  tuong_quan_hang_lien_ke    : Spearman, Kendall giữa 2 năm liền kề
  kendall_w                  : mức thống nhất thứ hạng qua cả 5 năm
"""
import numpy as np
import pandas as pd
from scipy import stats

from . import config as cf


def _str(d):
    d = d.copy()
    for c in ["ma_nh", "quy", "loai_hinh_so_huu"]:
        if c in d:
            d[c] = d[c].astype(str)
    return d


# ============================================================================
# THỐNG KÊ MÔ TẢ
# ============================================================================
def mo_ta(df, chi_so, theo=None, mau_du_lieu="quy"):
    """Thống kê mô tả 1 chỉ số.

    theo: None (toàn bộ) | 'ma_nh' | 'nam' | 'loai_hinh_so_huu' | ['ma_nh', 'nam']
    Trả về DataFrame đúng cột của thong_ke_mo_ta.csv.
    """
    d = _str(df)
    if theo is None:
        nhom, cap_do = [], "toan_bo"
    elif isinstance(theo, str):
        nhom, cap_do = [theo], theo
    else:
        nhom, cap_do = list(theo), "_".join(theo)

    ham = dict(so_quan_sat="count", trung_binh="mean", trung_vi="median",
               do_lech_chuan="std", nho_nhat="min", lon_nhat="max")
    if nhom:
        kq = d.groupby(nhom)[chi_so].agg(list(ham.values())).reset_index()
        kq.columns = nhom + list(ham.keys())
    else:
        kq = d[chi_so].agg(list(ham.values())).to_frame().T
        kq.columns = list(ham.keys())

    for c in ["ma_nh", "nam", "loai_hinh_so_huu"]:
        if c not in kq:
            kq[c] = np.nan
    kq.insert(0, "chi_so", chi_so)
    kq.insert(1, "cap_do", cap_do)
    kq["mau_du_lieu"] = mau_du_lieu
    kq["don_vi"] = "%"
    kq["so_quan_sat"] = kq["so_quan_sat"].astype(int)
    return kq


def bang_mo_ta(df, ds_chi_so, cac_cap_do=(None, "ma_nh", "nam"), mau_du_lieu="quy"):
    """Ghép thống kê mô tả của nhiều chỉ số × nhiều cấp độ thành 1 bảng dài."""
    return pd.concat([mo_ta(df, cs, theo, mau_du_lieu)
                      for cs in ds_chi_so for theo in cac_cap_do], ignore_index=True)


def bang_rong(kq, chi_so, hang="ma_nh", cot="trung_binh"):
    """Xoay bảng mô tả dạng dài → bảng rộng dễ đọc (vd hàng = ngân hàng, cột = thống kê)."""
    d = kq[(kq["chi_so"] == chi_so) & (kq["cap_do"] == hang)]
    return d.set_index(hang)[["so_quan_sat", "trung_binh", "trung_vi", "do_lech_chuan",
                              "nho_nhat", "lon_nhat"]].round(2)


# ============================================================================
# ROA / ROE NĂM
# ============================================================================
def tinh_chi_so_nam(b1):
    """ROA/ROE năm cho từng ngân hàng – năm.

    roa_nam = tổng LNST 4 quý / trung bình tổng tài sản cuối 4 quý × 100
    roe_nam = tổng LNST 4 quý / trung bình VCSH cuối 4 quý × 100
    Ưu điểm: không cần số dư cuối 2020, không bị phóng đại như ROA quý × 4.
    """
    d = _str(b1)
    g = d.groupby(["ma_nh", "nam"]).agg(
        so_quy=("quy", "size"),
        lnst_nam=("loi_nhuan_sau_thue", "sum"),
        tong_tai_san_tb=("tong_tai_san", "mean"),
        vcsh_tb=("von_chu_so_huu", "mean"),
    ).reset_index()
    if (g["so_quy"] != 4).any():
        raise ValueError("Có ngân hàng–năm không đủ 4 quý:\n" + g[g["so_quy"] != 4].to_string())
    g["roa_nam"] = g["lnst_nam"] / g["tong_tai_san_tb"] * 100
    g["roe_nam"] = g["lnst_nam"] / g["vcsh_tb"] * 100
    g["loai_hinh_so_huu"] = g["ma_nh"].map(cf.NHOM_CUA_NH)
    g["ma_nh"] = pd.Categorical(g["ma_nh"], cf.DS_NGAN_HANG, ordered=True)
    return g.sort_values(["ma_nh", "nam"]).reset_index(drop=True)


# ============================================================================
# XẾP HẠNG
# ============================================================================
def xep_hang(nam_df, chi_so="roe_nam"):
    """Xếp hạng 8 NH trong từng năm (1 = cao nhất). Trả về đúng cột xep_hang_nam.csv.
    thay_doi_hang = hang − hang_nam_truoc: dương = tụt hạng, âm = lên hạng."""
    d = _str(nam_df)[["ma_nh", "nam", "loai_hinh_so_huu", chi_so]].rename(columns={chi_so: "gia_tri"})
    d["hang"] = d.groupby("nam")["gia_tri"].rank(ascending=False, method="min").astype(int)
    d = d.sort_values(["ma_nh", "nam"])
    d["hang_nam_truoc"] = d.groupby("ma_nh")["hang"].shift(1)
    d["thay_doi_hang"] = d["hang"] - d["hang_nam_truoc"]
    d.insert(0, "chi_so", chi_so)
    return d.sort_values(["nam", "hang"]).reset_index(drop=True)


def bang_hang(xh):
    """Bảng rộng: hàng = ngân hàng (xếp theo hạng TB), cột = năm, ô = hạng."""
    b = xh.pivot(index="ma_nh", columns="nam", values="hang")
    b["hang_tb"] = b.mean(axis=1)
    return b.sort_values("hang_tb")


# ============================================================================
# ĐÁNH GIÁ ĐỘ ỔN ĐỊNH
# ============================================================================
def thong_ke_vi_tri(xh):
    """Mỗi ngân hàng: số năm hạng 1, số năm top 3, hạng TB, tốt nhất, kém nhất, độ lệch chuẩn hạng."""
    g = xh.groupby("ma_nh")["hang"]
    kq = pd.DataFrame({
        "so_nam_hang_1": g.apply(lambda s: (s == 1).sum()),
        "so_nam_top_3": g.apply(lambda s: (s <= 3).sum()),
        "hang_tb": g.mean().round(2),
        "hang_tot_nhat": g.min(),
        "hang_kem_nhat": g.max(),
        "do_lech_chuan_hang": g.std().round(2),
    })
    return kq.sort_values(["so_nam_hang_1", "hang_tb"], ascending=[False, True])


def dan_dau_tung_nam(xh):
    """Mỗi năm: ngân hàng hạng 1, hạng 2 và khoảng cách giá trị (điểm %)."""
    dong = []
    for nam, g in xh.groupby("nam"):
        g = g.sort_values("gia_tri", ascending=False)
        dong.append({"nam": nam,
                     "hang_1": g.iloc[0]["ma_nh"], "gia_tri_1": g.iloc[0]["gia_tri"],
                     "hang_2": g.iloc[1]["ma_nh"], "gia_tri_2": g.iloc[1]["gia_tri"],
                     "chenh_lech_diem_pct": g.iloc[0]["gia_tri"] - g.iloc[1]["gia_tri"],
                     "trung_binh_8_nh": g["gia_tri"].mean()})
    return pd.DataFrame(dong).round(2)


def tuong_quan_hang_lien_ke(xh):
    """Spearman ρ và Kendall τ giữa thứ hạng 2 năm liền kề (n = 8 ngân hàng).
    ρ, τ gần 1: thứ hạng gần như giữ nguyên; gần 0: xáo trộn; âm: đảo ngược."""
    b = xh.pivot(index="ma_nh", columns="nam", values="gia_tri")
    nam = sorted(b.columns)
    dong = []
    for a, c in zip(nam[:-1], nam[1:]):
        rho, p_rho = stats.spearmanr(b[a], b[c])
        tau, p_tau = stats.kendalltau(b[a], b[c])
        dong.append({"cap_nam": f"{a}–{c}", "so_ngan_hang": len(b),
                     "spearman_rho": rho, "spearman_p": p_rho,
                     "kendall_tau": tau, "kendall_p": p_tau})
    return pd.DataFrame(dong).round(3)


def kendall_w(xh):
    """Hệ số thống nhất Kendall W cho thứ hạng qua tất cả các năm.

    W ∈ [0, 1]: 1 = mọi năm xếp hạng y hệt; 0 = không có quy luật.
    Kiểm định: χ² = m(n−1)W với n−1 bậc tự do (m = số năm, n = số ngân hàng).
    """
    b = xh.pivot(index="ma_nh", columns="nam", values="gia_tri")
    hang = b.rank(ascending=False)            # hạng trong từng năm
    n, m = hang.shape
    tong = hang.sum(axis=1)
    s = ((tong - tong.mean()) ** 2).sum()
    w = 12 * s / (m ** 2 * (n ** 3 - n))
    chi2 = m * (n - 1) * w
    p = stats.chi2.sf(chi2, n - 1)
    return {"kendall_w": round(float(w), 3), "chi2": round(float(chi2), 2), "bac_tu_do": n - 1,
            "p_value": round(float(p), 4), "so_nam": m, "so_ngan_hang": n}


# ============================================================================
# PHẦN 4 – CÂU 2: SO SÁNH QUỐC DOANH vs TƯ NHÂN
# ============================================================================
NHOM_A, NHOM_B = cf.NHOM_QUOC_DOANH, cf.NHOM_TU_NHAN


def du_lieu_cau2(b4):
    """Chuẩn bị 3 bộ dữ liệu cho kiểm định câu 2.

    nh_nam : NIM, NPL trung bình 4 quý theo ngân hàng–năm (40 quan sát: 15 QD, 25 TN)
    car    : 32 giá trị CAR thật (12 QD, 20 TN) – số VNDirect công bố + 6 số tra thủ công
    nh     : trung bình cả giai đoạn theo ngân hàng (8 quan sát: 3 QD, 5 TN) – để kiểm tra lại
    """
    d = _str(b4)
    nh_nam = d.groupby(["loai_hinh_so_huu", "ma_nh", "nam"], as_index=False)[["nim", "npl"]].mean()
    car = d[d["car_nguon"].isin(cf.CAR_NGUON_SO_THAT)][["loai_hinh_so_huu", "ma_nh", "nam", "car", "car_nguon"]].reset_index(drop=True)
    nh = nh_nam.groupby(["loai_hinh_so_huu", "ma_nh"], as_index=False)[["nim", "npl"]].mean()
    nh = nh.merge(car.groupby("ma_nh", as_index=False)["car"].mean(), on="ma_nh")
    return {"nh_nam": nh_nam, "car": car, "nh": nh}


def _hieu_ung_cohen_d(a, b):
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return (a.mean() - b.mean()) / sp


def kiem_dinh_hai_nhom(a, b, alpha=0.05, bat_buoc=None):
    """Chọn và chạy kiểm định so sánh 2 nhóm độc lập theo quy tắc của kế hoạch:

      1. Shapiro-Wilk từng nhóm: p ≥ alpha → coi là phân phối chuẩn
      2. Cả hai chuẩn → Levene: p ≥ alpha → Student t (phương sai bằng nhau), ngược lại Welch t
      3. Có nhóm không chuẩn → Mann-Whitney U
    bat_buoc: 'Mann-Whitney U' | 'Welch t' | 'Student t' để ép dùng 1 kiểm định (vd mẫu quá nhỏ).
    Độ lớn hiệu ứng: t-test → Cohen d; Mann-Whitney → tương quan hạng biserial r (−1..1).
    """
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    sh_a, sh_b = stats.shapiro(a).pvalue, stats.shapiro(b).pvalue
    lev = stats.levene(a, b).pvalue
    if bat_buoc:
        ten = bat_buoc
    elif sh_a >= alpha and sh_b >= alpha:
        ten = "Student t" if lev >= alpha else "Welch t"
    else:
        ten = "Mann-Whitney U"

    if ten == "Mann-Whitney U":
        kq = stats.mannwhitneyu(a, b, alternative="two-sided")
        hieu_ung, ten_hu = 1 - 2 * kq.statistic / (len(a) * len(b)), "biserial hạng r"
        hieu_ung = -hieu_ung        # dương khi nhóm a (quốc doanh) cao hơn
    else:
        kq = stats.ttest_ind(a, b, equal_var=(ten == "Student t"))
        hieu_ung, ten_hu = _hieu_ung_cohen_d(a, b), "Cohen d"
    return {"shapiro_p_quoc_doanh": sh_a, "shapiro_p_tu_nhan": sh_b, "levene_p": lev,
            "kiem_dinh": ten, "thong_ke": float(kq.statistic), "p_value": float(kq.pvalue),
            "ten_hieu_ung": ten_hu, "do_lon_hieu_ung": float(hieu_ung)}


TEN_CHI_SO_NGAN = {"nim": "NIM", "npl": "NPL", "car": "CAR"}


def kiem_dinh_nhom(df, chi_so, mau_du_lieu, don_vi_quan_sat, phan_tich="chinh", alpha=0.05, bat_buoc=None):
    """Kiểm định quốc doanh vs tư nhân cho 1 chỉ số → 1 dòng đúng cấu trúc kiem_dinh_nhom.csv."""
    a = df.loc[df["loai_hinh_so_huu"] == NHOM_A, chi_so]
    b = df.loc[df["loai_hinh_so_huu"] == NHOM_B, chi_so]
    kq = kiem_dinh_hai_nhom(a, b, alpha, bat_buoc)
    ten = TEN_CHI_SO_NGAN.get(chi_so, chi_so.upper())
    if kq["kiem_dinh"] == "Mann-Whitney U":
        h0 = f"Phân phối {ten} của nhóm quốc doanh và tư nhân như nhau"
        h1 = f"Phân phối {ten} của hai nhóm khác nhau"
    else:
        h0 = f"{ten} trung bình của nhóm quốc doanh bằng nhóm tư nhân"
        h1 = f"{ten} trung bình của hai nhóm khác nhau"
    bac_bo = kq["p_value"] < alpha
    p_txt = "p < 0.001" if kq["p_value"] < 0.001 else f"p = {kq['p_value']:.3f}"
    cao_hon = NHOM_A if a.median() > b.median() else NHOM_B
    ket_luan = (f"Bác bỏ H0 ({p_txt} < {alpha}): {ten} hai nhóm khác biệt có ý nghĩa, "
                f"nhóm {cao_hon.lower()} cao hơn." if bac_bo else
                f"Chưa đủ cơ sở bác bỏ H0 ({p_txt} ≥ {alpha}): "
                f"chưa thấy khác biệt có ý nghĩa về {ten}.")
    return {"chi_so": chi_so, "mau_du_lieu": mau_du_lieu, "don_vi_quan_sat": don_vi_quan_sat,
            "phan_tich": phan_tich, "n_quoc_doanh": len(a), "n_tu_nhan": len(b),
            "tb_quoc_doanh": a.mean(), "tb_tu_nhan": b.mean(),
            "trung_vi_quoc_doanh": a.median(), "trung_vi_tu_nhan": b.median(),
            **{k: kq[k] for k in ["shapiro_p_quoc_doanh", "shapiro_p_tu_nhan", "levene_p",
                                   "kiem_dinh", "thong_ke", "p_value"]},
            "muc_y_nghia": alpha, "bac_bo_H0": bac_bo,
            "gia_thuyet_H0": h0, "gia_thuyet_H1": h1, "ket_luan": ket_luan,
            "chenh_lech_tb": a.mean() - b.mean(),
            "ten_hieu_ung": kq["ten_hieu_ung"], "do_lon_hieu_ung": kq["do_lon_hieu_ung"]}


# ============================================================================
# PHẦN 5 – CÂU 3: TƯƠNG QUAN CHỈ SỐ TÀI CHÍNH ↔ LỢI SUẤT CỔ PHIẾU QUÝ
# ============================================================================
BIEN_LOI_SUAT = "ty_suat_sinh_loi_quy"


def tuong_quan_voi_loi_suat(df, ds_chi_so=None, bien=BIEN_LOI_SUAT, mau_du_lieu="chinh",
                            phan_tich="chinh", hieu_chinh="holm"):
    """Pearson + Spearman giữa từng chỉ số và lợi suất quý, kèm p-value hiệu chỉnh
    cho nhiều kiểm định (mặc định Holm). Trả về đúng cấu trúc tuong_quan.csv.

    Vì sao hiệu chỉnh: kiểm định 6 chỉ số cùng lúc thì xác suất 'tình cờ' có ít nhất 1 chỉ số
    p < 0,05 lên tới ~26%. Holm nâng p-value lên để giữ tổng sai lầm ở mức 5%.
    """
    from statsmodels.stats.multitest import multipletests
    ds_chi_so = ds_chi_so or cf.DS_CHI_SO
    dong = []
    for cs in ds_chi_so:
        x = df[[cs, bien]].dropna()
        pr, pp = stats.pearsonr(x[cs], x[bien])
        sr, sp = stats.spearmanr(x[cs], x[bien])
        dong.append({"chi_so": cs, "bien_so_sanh": bien, "mau_du_lieu": mau_du_lieu,
                     "phan_tich": phan_tich, "so_quan_sat": len(x),
                     "pearson_r": pr, "pearson_p": pp, "spearman_rho": sr, "spearman_p": sp})
    kq = pd.DataFrame(dong)
    if len(kq) > 1:
        kq["pearson_p_hieu_chinh"] = multipletests(kq["pearson_p"], method=hieu_chinh)[1]
        kq["spearman_p_hieu_chinh"] = multipletests(kq["spearman_p"], method=hieu_chinh)[1]
    else:
        kq["pearson_p_hieu_chinh"], kq["spearman_p_hieu_chinh"] = kq["pearson_p"], kq["spearman_p"]
    kq["phuong_phap_hieu_chinh"] = hieu_chinh
    kq["xep_hang_do_manh"] = kq["spearman_rho"].abs().rank(ascending=False, method="min").astype(int)
    return kq


def loai_bien_dong_chung(df, cot, theo="ky"):
    """Trừ trung bình 8 ngân hàng trong cùng quý → chỉ còn phần 'hơn/kém các ngân hàng khác'.
    Dùng để tách ảnh hưởng của thị trường chung (cả ngành cùng tăng/giảm)."""
    d = df.copy()
    for c in cot:
        d[c] = d[c] - d.groupby(theo, observed=True)[c].transform("mean")
    return d


def thay_doi_so_voi_quy_truoc(df, cot):
    """Chỉ số → mức thay đổi so với quý trước (cùng ngân hàng). Quý đầu mỗi ngân hàng bị trống."""
    d = df.sort_values(["ma_nh", "ky_so"]).copy()
    for c in cot:
        d[c] = d.groupby("ma_nh", observed=True)[c].diff()
    return d


def ty_trong_bien_dong_chung(df, bien=BIEN_LOI_SUAT, theo="ky"):
    """% phương sai của lợi suất được giải thích bởi 'quý nào' (biến động chung của cả ngành).
    = 1 − tổng bình phương trong từng quý / tổng bình phương toàn bộ."""
    y = df[bien]
    trong_quy = (y - df.groupby(theo, observed=True)[bien].transform("mean")) ** 2
    return 1 - trong_quy.sum() / ((y - y.mean()) ** 2).sum()
