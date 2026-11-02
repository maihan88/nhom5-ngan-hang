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
c1, c2 = st.columns([5, 1.2], vertical_alignment="bottom")
ma = c1.pills("Ngân hàng", cf.DS_NGAN_HANG, default=mac_dinh, key="nh_ma", label_visibility="collapsed") or mac_dinh
ky = c2.selectbox("Kỳ", ds_ky[::-1], format_func=lambda k: f"Quý {k[-1]}/{k[:4]}", key="nh_ky",
                  label_visibility="collapsed")
st.session_state["ma"] = ma
if st.query_params.get("ma") != ma:
    st.query_params["ma"] = ma

vt = ds_ky.index(ky)
ky_truoc = ds_ky[vt - 1] if vt else None
nhan_ky = f"Q{ky[-1]}/{ky[:4]}"
nganh = b4[b4["ky"] == ky].set_index("ma_nh")
dong = nganh.loc[ma]
nh = b4[b4["ma_nh"] == ma].set_index("ky").reindex(ds_ky)

# ---- Nhận định một câu: điểm mạnh nhất / yếu nhất theo thứ hạng -----------------------------------------
DIEM = {"roe": ("ROE", 1), "nim": ("biên lãi", 1), "npl": ("nợ xấu", -1), "car": ("vốn đệm CAR", 1)}
hang = {cs: int(nganh[cs].rank(ascending=chieu < 0, method="min")[ma]) for cs, (_, chieu) in DIEM.items()}
xep = sorted(hang, key=hang.get)
n = len(nganh)


def _cum(cs):
    ten, chieu = DIEM[cs]
    h = hang[cs]
    tot, xau = ("thấp", "cao") if chieu < 0 else ("cao", "thấp")
    if h <= 2:
        return f"{ten} {tot} {'nhất' if h == 1 else 'thứ nhì'} ngành"
    if h >= n - 1:
        return f"{ten} {xau} {'nhất' if h == n else 'thứ nhì'} ngành"
    return f"{ten} xếp {h}/{n}"


manh = [c for c in xep if hang[c] <= 2][:2]
yeu = xep[-1]
if manh and hang[yeu] > 2:
    nhan_dinh = f"{gd.hoa_dau(', '.join(_cum(c) for c in manh))}; {_cum(yeu)}."
elif manh:
    nhan_dinh = f"{gd.hoa_dau(', '.join(_cum(c) for c in manh))}."
else:
    nhan_dinh = f"{gd.hoa_dau(_cum(xep[0]))}; {_cum(yeu)}."

# ---- Đầu hồ sơ -------------------------------------------------------------------------------------------------
ngay_ky = pd.Period(ky, freq="Q").end_time
g12 = dl.gia_12_thang(ds["gia_ngay"], den=ngay_ky)
thay_doi_12t = g12[g12["ma_nh"] == ma]["thay_doi"].iloc[-1]
nhom = pn["du_lieu"].set_index(["ma_nh", "ky"]).loc[(ma, ky)]
st.html(
    "<div class='nhan-dinh' style='align-items:flex-end'><div style='flex:1 1 460px;min-width:0'>"
    f"<div style='display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px'><span class='the'>{cf.NHOM_CUA_NH[ma]}</span>"
    f"<span class='the'>{ma} · HOSE</span><span class='the'>Nhóm {nhom['nhom']}</span></div>"
    f"<h1 style='font-size:2.1rem;font-weight:700;margin:0;padding:0;display:flex;align-items:center;gap:12px'>"
    f"<span style='width:14px;height:14px;border-radius:4px;background:var(--nh-{ma.lower()})'></span>{e(cf.TEN_DAY_DU[ma])}</h1>"
    f"<div class='nho' style='margin-top:14px'>Nhận định · Quý {ky[-1]}/{ky[:4]}</div><p class='cau'>{nhan_dinh}</p></div>"
    "<div style='display:flex;flex-direction:column;align-items:flex-end;gap:6px'>"
    "<span class='nguon'>Giá cuối quý · nghìn đồng</span>"
    f"<span class='num' style='font-size:2.5rem;font-weight:700;letter-spacing:-.02em;line-height:1'>{so(dong['gia_cuoi_quy'], dv='')}</span>"
    f"<div style='display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end'>"
    f"{gd.bien_dong(dong['ty_suat_sinh_loi_quy'], 1, 1, '%')}<span class='nguon'>trong quý</span>"
    f"{gd.bien_dong(thay_doi_12t, 1, 0, '%')}<span class='nguon'>12 tháng</span></div></div></div>")

o = []
for cs in cf.DS_CHI_SO:
    chieu = cf.CHIEU_TOT[cs]
    o.append({"nhan": mh.TEN_BIEN[cs],
              "hang": f"hạng {int(nganh[cs].rank(ascending=chieu < 0, method='min')[ma])}/8" if chieu else "",
              "so": so(dong[cs]),
              "phu": gd.bien_dong(dong[cs] - nh.loc[ky_truoc, cs], chieu) if ky_truoc else "",
              "spark": gd.sparkline(nh[cs].iloc[max(0, vt - 7): vt + 1].tolist(), gd.mau_nh(ma), 72, 30, vung=False)})
gd.the_so(o, rong=145, hep=True)
gd.nguon("ROA, ROE, NIM năm hóa từ số liệu quý. CAR chỉ công bố cuối năm – các quý khác là số gần nhất trước đó. "
         "Đường nhỏ: 8 quý gần nhất.")

# ---- So với mặt bằng ngành --------------------------------------------------------------------------------------
p = b4.pivot_table(index="ky", columns="ma_nh", values=cf.DS_CHI_SO).reindex(ds_ky)
ty_le = {}
for cs in ["roe", "nim", "npl", "car"]:
    tren = p[cs][ma] > p[cs].median(axis=1)
    ty_le[cs] = (int(tren.sum()), len(tren))
noi_bat = max(ty_le, key=lambda c: abs(ty_le[c][0] / ty_le[c][1] - 0.5))
n1, tong = ty_le[noi_bat]
cao_hon = n1 >= tong / 2
with gd.the("nganh"):
    gd.tieu_the("So với mặt bằng ngành",
                f"{DIEM[noi_bat][0][:1].upper() + DIEM[noi_bat][0][1:]} {'cao' if cao_hon else 'thấp'} hơn trung vị ngành "
                f"{max(n1, tong - n1)}/{tong} quý",
                "Dải xám: khoảng 8 ngân hàng · đường chấm: trung vị · đường màu: " + ma)
    hang_hinh = st.columns(3, gap="medium") + st.columns(3, gap="medium")
    for c, cs in zip(hang_hinh, cf.DS_CHI_SO):
        with c:
            st.html(f"<div style='display:flex;justify-content:space-between;font-size:.86rem;margin-bottom:-8px'>"
                    f"<b>{mh.TEN_BIEN[cs]}</b><span class='num' style='color:var(--nhat)'>{so(dong[cs])}</span></div>")
            bd.ve(bd.dai_nganh(b4, ma, cs, ds_ky, ky), key=f"nh_dai_{cs}")

# ---- Giá & sự kiện -------------------------------------------------------------------------------------------------
sk = ds["su_kien_chi_tiet"]
sk_nh = sk[sk["ma_nh"] == ma]
sk_12 = sk_nh[(sk_nh["ngay_cong_bo"] > ngay_ky - pd.Timedelta(days=365)) & (sk_nh["ngay_cong_bo"] <= ngay_ky + pd.Timedelta(days=1))]
with gd.the("gia"):
    gd.tieu_the("Cổ phiếu & sự kiện",
                f"{'Tăng' if thay_doi_12t >= 0 else 'Giảm'} {so(abs(thay_doi_12t), 0)} trong 12 tháng đến {nhan_ky}, "
                f"kèm {len(sk_12)} tin doanh nghiệp · chấm tròn: ngày công bố tin, rê chuột để đọc")
    ky_han = st.segmented_control("Kỳ hạn", ["1 năm", "3 năm", "Toàn bộ"], default="3 năm", key="nh_kh",
                                  label_visibility="collapsed") or "3 năm"
    tu = {"1 năm": ngay_ky - pd.Timedelta(days=365), "3 năm": ngay_ky - pd.Timedelta(days=3 * 365), "Toàn bộ": None}[ky_han]
    g = ds["gia_ngay"] if tu is None else ds["gia_ngay"][ds["gia_ngay"]["ngay"] >= tu]
    s = sk if tu is None else sk[sk["ngay_cong_bo"] >= tu]
    bd.ve(bd.gia_su_kien(g, s, ma), key="nh_gia")

# ---- Tín hiệu & nhóm -----------------------------------------------------------------------------------------------
dong_db = kq["du_lieu"][(kq["du_lieu"]["ma_nh"] == ma) & (kq["du_lieu"]["ky"] == ky)]
p_tang = float(mh.xac_suat(kq, mh.MAC_DINH, dong_db)[0])
ls = kq["du_lieu"][kq["du_lieu"]["ma_nh"] == ma].copy()
ls["p"] = mh.xac_suat(kq, mh.MAC_DINH, ls)
ls = ls[(ls["ky"] <= ky) & ls[mh.NHAN].notna()].tail(5)
c1, c2 = st.columns(2, gap="medium")
with c1, gd.the("tin-hieu"):
    vt_ky = ds_ky.index(ky)
    ky_sau = ds_ky[vt_ky + 1] if vt_ky + 1 < len(ds_ky) else None
    gd.tieu_the("Tín hiệu quý kế tiếp", "Ước lượng từ chỉ số tài chính và sự kiện, độ tin cậy thấp",
                "<a href='du_bao' target='_self'>Xem Dự báo</a>")
    thuc_te = dong_db[mh.NHAN].iloc[0]
    ket = ""
    if thuc_te == thuc_te:
        dung = (p_tang >= 0.5) == (thuc_te == 1)
        ket = (f" · thực tế {'tăng' if thuc_te == 1 else 'không tăng'} "
               f"({so(dong_db['ty_suat_sinh_loi_quy_sau'].iloc[0], 1, dau=True)}), mô hình "
               f"<b class='{'len' if dung else 'xuong'}'>{'đúng' if dung else 'sai'}</b>")
    o_ls = "".join(
        f"<div class='o-nho {'dung' if (r.p >= 0.5) == (getattr(r, mh.NHAN) == 1) else 'sai'}' style='flex:1 1 70px;align-items:center'>"
        f"<span class='nguon'>Q{r.ky[-1]}/{r.ky[2:4]}</span><b class='num'>{r.p:.0%}</b>"
        f"<span style='font-size:.74rem'>{'✓ đúng' if (r.p >= 0.5) == (getattr(r, mh.NHAN) == 1) else '✗ sai'}</span></div>"
        for r in ls.itertuples())
    st.html(f"<div style='display:flex;align-items:baseline;gap:12px;flex-wrap:wrap'><span class='num' "
            f"style='font-size:2.2rem;font-weight:700;line-height:1'>{p_tang:.0%}</span><span style='color:var(--nhat)'>"
            f"khả năng giá tăng · {'nghiêng về tăng' if p_tang >= 0.5 else 'nghiêng về không tăng'}{ket}</span></div>"
            f"<div style='position:relative;height:8px;border-radius:4px;background:var(--mat2);margin:12px 0 14px 0'>"
            f"<div style='position:absolute;left:0;top:0;height:8px;border-radius:4px;width:{p_tang * 100:.0f}%;"
            f"background:{'var(--nhan)' if p_tang >= 0.5 else 'var(--nen-xam)'}'></div><div style='position:absolute;left:50%;"
            f"top:-4px;height:16px;border-left:2px solid var(--muc)'></div></div>"
            f"<div class='nguon' style='margin-bottom:6px'>{len(ls)} quý gần nhất đã có kết quả</div>"
            f"<div style='display:flex;gap:8px;flex-wrap:wrap'>{o_ls}</div>")

with c2, gd.the("nhom"):
    gd.tieu_the("Nhóm đặc điểm tài chính", "Phân cụm K-Means trên 6 chỉ số", "<a href='phan_nhom' target='_self'>Xem Phân nhóm</a>")
    d_pn = pn["du_lieu"]
    so_quy = int((d_pn[d_pn["ma_nh"] == ma]["nhom"] == nhom["nhom"]).sum())
    cung = d_pn[(d_pn["ky"] == ky) & (d_pn["nhom"] == nhom["nhom"]) & (d_pn["ma_nh"] != ma)]["ma_nh"]
    st.html(f"<div style='display:flex;align-items:center;gap:12px;margin:4px 0 14px 0'><span style='width:44px;height:44px;"
            f"border-radius:10px;background:{gd.mau_nhom(nhom['nhom'])};color:#FFFFFF;display:flex;align-items:center;"
            f"justify-content:center;font-weight:700;font-size:1.1rem;flex:none'>{nhom['nhom']}</span><div><b style='font-size:1.02rem'>"
            f"{e(nhom['ten_nhom'])}</b><div class='nguon'>{ma} ở nhóm {nhom['nhom']} {so_quy}/{d_pn['ky'].nunique()} quý</div></div></div>"
            f"<div class='nguon' style='margin-bottom:6px'>Cùng nhóm trong {nhan_ky}</div>"
            f"<div style='display:flex;gap:14px;flex-wrap:wrap'>{' '.join(gd.chip(m) for m in cung) or '–'}</div>")

# ---- Tin gần đây -----------------------------------------------------------------------------------------------------
sk_den_ky = sk_nh[sk_nh["ngay_cong_bo"] <= ngay_ky + pd.Timedelta(days=1)].sort_values("ngay_cong_bo", ascending=False)
with gd.the("tin"):
    gd.tieu_the("Tin doanh nghiệp", f"{len(sk_den_ky)} sự kiện của {ma} từ 2021 đến {nhan_ky}")
    tin = sk_den_ky.assign(ma_nh="")
    SO_TIN_HIEN = 6
    st.html(gd.ds_tin(tin.head(SO_TIN_HIEN).itertuples()) or "<div class='nguon'>Chưa có sự kiện.</div>")
    if len(tin) > SO_TIN_HIEN:
        with st.expander(f"Xem thêm {len(tin) - SO_TIN_HIEN} sự kiện cũ hơn"):
            st.html(gd.ds_tin(tin.iloc[SO_TIN_HIEN:].itertuples()))

gd.chan_trang()
