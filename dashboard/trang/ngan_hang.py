import pandas as pd
import streamlit as st

from src import config as cf
from web import bieu_do as bd
from web import du_lieu as dl
from web import giao_dien as gd
from web import mo_hinh as mh
from web.giao_dien import e, so

ds = dl.tat_ca()
b4 = ds["tong_hop"]
ds_ky = dl.ds_ky()
kq, pn = dl.du_bao(), dl.phan_nhom()

# ---- Chọn ngân hàng (đồng bộ với ?ma= trên địa chỉ để bảng xếp hạng link sang được) -------------------
qp = st.query_params.get("ma")
mac_dinh = qp if qp in cf.DS_NGAN_HANG else st.session_state.get("ma", "VCB")
c1, c2 = st.columns([5, 1], vertical_alignment="bottom")
ma = c1.pills("Ngân hàng", cf.DS_NGAN_HANG, default=mac_dinh, key="nh_ma", label_visibility="collapsed") or mac_dinh
ky = c2.selectbox("Kỳ", ds_ky[::-1], format_func=lambda k: f"Quý {k[-1]}/{k[:4]}", key="nh_ky",
                  label_visibility="collapsed")
st.session_state["ma"] = ma
if st.query_params.get("ma") != ma:
    st.query_params["ma"] = ma

vt = ds_ky.index(ky)
ky_truoc = ds_ky[vt - 1] if vt else None
nganh = b4[b4["ky"] == ky].set_index("ma_nh")
dong = nganh.loc[ma]
nh = b4[b4["ma_nh"] == ma].set_index("ky").reindex(ds_ky)

# ---- Nhận định một câu: điểm mạnh nhất / yếu nhất theo thứ hạng -----------------------------------------
DIEM = {"roe": ("sinh lời trên vốn", 1), "nim": ("biên lãi", 1), "npl": ("nợ xấu", -1), "car": ("vốn đệm CAR", 1)}
hang = {cs: int(nganh[cs].rank(ascending=chieu < 0, method="min")[ma]) for cs, (_, chieu) in DIEM.items()}
manh = min(hang, key=hang.get)
yeu = max(hang, key=hang.get)


def _cum(cs):
    ten, chieu = DIEM[cs]
    h, n = hang[cs], len(nganh)
    tot, xau = ("thấp", "cao") if chieu < 0 else ("cao", "thấp")
    if h <= 2:
        return f"{ten} {tot} {'nhất' if h == 1 else 'thứ nhì'} ngành"
    if h >= n - 1:
        return f"{ten} {xau} {'nhất' if h == n else 'thứ nhì'} ngành"
    return f"{ten} xếp {h}/{n}"


if hang[yeu] >= 6 and yeu != manh:
    nhan_dinh = f"{gd.hoa_dau(_cum(manh))}, nhưng {_cum(yeu)}."
elif hang[manh] <= 2:
    nhan_dinh = f"{gd.hoa_dau(_cum(manh))}; các chỉ số khác quanh mức trung bình ngành."
else:
    nhan_dinh = "Các chỉ số chính đều quanh mức trung bình ngành."

# ---- Đầu hồ sơ -------------------------------------------------------------------------------------------------
ngay_ky = pd.Period(ky, freq="Q").end_time
g12 = dl.gia_12_thang(ds["gia_ngay"], den=ngay_ky)
thay_doi_12t = g12[g12["ma_nh"] == ma]["thay_doi"].iloc[-1]
st.html("<div style='border-top:2px solid var(--muc);margin-top:6px'></div>")
trai, phai = st.columns([2.3, 1], vertical_alignment="bottom")
trai.html(
    f"<div class='muc dau' style='border-top:none;padding-top:4px'><div class='kicker'>{cf.NHOM_CUA_NH[ma]} · {ma} · quý {ky[-1]}/{ky[:4]}</div>"
    f"<h2 style='font-size:2.6rem;margin-top:10px'>{e(cf.TEN_DAY_DU[ma])}</h2>"
    f"<p class='dek' style='font-size:1.08rem'>{nhan_dinh}</p></div>")
phai.html(
    "<div style='text-align:right;padding-bottom:6px'><div class='nguon' style='margin:0'>Giá cuối quý · nghìn đồng</div>"
    f"<div style='font-size:2.3rem;font-weight:650;letter-spacing:-.02em'>{so(dong['gia_cuoi_quy'], dv='')}</div>"
    f"<div style='font-size:.86rem'>{gd.bien_dong(dong['ty_suat_sinh_loi_quy'], 1, 1, '%')} trong quý · "
    f"{gd.bien_dong(thay_doi_12t, 1, 0, '%')} 12 tháng</div></div>")

o = []
for cs in cf.DS_CHI_SO:
    chieu = cf.CHIEU_TOT[cs]
    h = f" · hạng {int(nganh[cs].rank(ascending=chieu < 0, method='min')[ma])}/8" if chieu else ""
    o.append({"nhan": f"{mh.TEN_BIEN[cs]}{h}", "so": so(dong[cs]),
              "phu": gd.bien_dong(dong[cs] - nh.loc[ky_truoc, cs], chieu) + " so với quý trước" if ky_truoc else "",
              "spark": gd.sparkline(nh[cs].iloc[max(0, vt - 7): vt + 1].tolist(), cf.MAU_NGAN_HANG[ma], 70, 26)})
gd.day_so(o, hep=True)
gd.nguon("ROA, ROE, NIM năm hóa từ số liệu quý. CAR chỉ công bố cuối năm – các quý khác là số gần nhất trước đó.")

# ---- So với mặt bằng ngành --------------------------------------------------------------------------------------
p = b4.pivot_table(index="ky", columns="ma_nh", values=cf.DS_CHI_SO).reindex(ds_ky)
ty_le = {}
for cs in ["roe", "nim", "npl", "car"]:
    tren = p[cs][ma] > p[cs].median(axis=1)
    ty_le[cs] = (int(tren.sum()), len(tren))
noi_bat = sorted(ty_le, key=lambda c: -abs(ty_le[c][0] / ty_le[c][1] - 0.5))[:2]
(c1_, (n1, tong)), (c2_, (n2, _)) = [(c, ty_le[c]) for c in noi_bat]
h1, h2 = ("cao" if n1 >= tong / 2 else "thấp"), ("cao" if n2 >= tong / 2 else "thấp")
m1, m2 = max(n1, tong - n1), max(n2, tong - n2)
if h1 == h2 and m1 == m2:
    cau_tieu = (f"{ma}: {DIEM[c1_][0]} và {DIEM[c2_][0]} {'luôn ' if m1 == tong else ''}{h1} hơn trung vị ngành "
                f"({m1}/{tong} quý)")
else:
    cau_tieu = (f"{ma}: {DIEM[c1_][0]} {h1} hơn trung vị ngành {m1}/{tong} quý, "
                f"{DIEM[c2_][0]} {h2} hơn {m2}/{tong} quý")
gd.muc("So với mặt bằng ngành", cau_tieu,
       "Dải xám: khoảng giá trị của 8 ngân hàng mỗi quý · đường chấm: trung vị · đường màu: " + ma + ".")
hang_hinh = st.columns(3, gap="medium") + st.columns(3, gap="medium")
for c, cs in zip(hang_hinh, cf.DS_CHI_SO):
    with c:
        st.html(f"<div style='font-weight:600;font-size:.9rem;margin-bottom:-6px'>{mh.TEN_BIEN[cs]} "
                f"<span style='color:var(--nhat);font-weight:400'>· {so(dong[cs])}</span></div>")
        bd.ve(bd.dai_nganh(b4, ma, cs, ds_ky, ky), key=f"nh_dai_{cs}")

# ---- Giá & sự kiện -------------------------------------------------------------------------------------------------
sk = ds["su_kien_chi_tiet"]
sk_nh = sk[sk["ma_nh"] == ma]
sk_12 = sk_nh[(sk_nh["ngay_cong_bo"] > ngay_ky - pd.Timedelta(days=365)) & (sk_nh["ngay_cong_bo"] <= ngay_ky + pd.Timedelta(days=1))]
gd.muc("Cổ phiếu & sự kiện",
       f"Giá {ma} {'tăng' if thay_doi_12t >= 0 else 'giảm'} {so(abs(thay_doi_12t), 0)} trong 12 tháng đến quý {ky[-1]}/{ky[:4]}, "
       f"kèm {len(sk_12)} tin doanh nghiệp",
       "Giá đã điều chỉnh cổ tức, chia tách. Chấm đen: ngày công bố tin – rê chuột để đọc tiêu đề.")
ky_han = st.segmented_control("Kỳ hạn", ["1 năm", "3 năm", "Toàn bộ"], default="3 năm", key="nh_kh",
                              label_visibility="collapsed") or "3 năm"
tu = {"1 năm": ngay_ky - pd.Timedelta(days=365), "3 năm": ngay_ky - pd.Timedelta(days=3 * 365), "Toàn bộ": None}[ky_han]
g = ds["gia_ngay"] if tu is None else ds["gia_ngay"][ds["gia_ngay"]["ngay"] >= tu]
s = sk if tu is None else sk[sk["ngay_cong_bo"] >= tu]
bd.ve(bd.gia_su_kien(g, s, ma), key="nh_gia")

# ---- Tín hiệu & nhóm -----------------------------------------------------------------------------------------------
dong_db = kq["du_lieu"][(kq["du_lieu"]["ma_nh"] == ma) & (kq["du_lieu"]["ky"] == ky)]
p_tang = float(mh.xac_suat(kq, mh.MAC_DINH, dong_db)[0])
nhom = pn["du_lieu"].set_index(["ma_nh", "ky"]).loc[(ma, ky)]
gd.muc("Góc nhìn mô hình",
       f"Mô hình {'nghiêng về tăng' if p_tang >= 0.5 else 'nghiêng về không tăng'} cho quý kế tiếp ({p_tang:.0%})",
       f"Ước lượng từ chỉ số tài chính và sự kiện của quý {ky[-1]}/{ky[:4]}. Độ tin cậy thấp – xem mục Dự báo.")
c1, c2 = st.columns(2, gap="large")
thuc_te = dong_db[mh.NHAN].iloc[0]
with c1:
    chu = ""
    if thuc_te == thuc_te:
        dung = (p_tang >= 0.5) == (thuc_te == 1)
        chu = (f"Thực tế quý sau giá {'tăng' if thuc_te == 1 else 'không tăng'} "
               f"({so(dong_db['ty_suat_sinh_loi_quy_sau'].iloc[0], 1, dau=True)}) – mô hình "
               f"<b class='{'len' if dung else 'xuong'}'>{'đúng' if dung else 'sai'}</b>.")
    gd.ghi_chu(f"<span class='ket-luan'>{p_tang:.0%} khả năng giá quý sau cao hơn hiện tại.</span><br>{chu}")
with c2:
    gd.ghi_chu(f"<span class='ket-luan'>Nhóm {nhom['nhom']}: {e(nhom['ten_nhom'].lower())}.</span><br>"
               "Nhóm đặc điểm tài chính theo phân cụm K-Means – xem mục Phân nhóm.")

# ---- Tin gần đây -----------------------------------------------------------------------------------------------------
sk_den_ky = sk_nh[sk_nh["ngay_cong_bo"] <= ngay_ky + pd.Timedelta(days=1)].sort_values("ngay_cong_bo", ascending=False)
gd.muc("Tin doanh nghiệp", f"{len(sk_den_ky)} sự kiện của {ma} từ 2021 đến quý {ky[-1]}/{ky[:4]}")
tin = [f"<div class='tin'><div class='ngay'>{r.ngay_cong_bo:%d/%m/%Y}</div><div>"
       f"<div class='meta'>{e(r.loai_su_kien_nhan)}</div>"
       f"<div class='tieu'><a href='{e(r.nguon)}' target='_blank'>{e(r.mo_ta_ngan)}</a></div></div></div>"
       for r in sk_den_ky.itertuples()]
SO_TIN_HIEN = 6
if tin:
    st.html("".join(tin[:SO_TIN_HIEN]))
if len(tin) > SO_TIN_HIEN:
    with st.expander(f"Xem thêm {len(tin) - SO_TIN_HIEN} sự kiện cũ hơn"):
        st.html("".join(tin[SO_TIN_HIEN:]))

gd.chan_trang()
