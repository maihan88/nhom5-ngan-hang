import pandas as pd
import streamlit as st

from src import config as cf
from web import bieu_do as bd
from web import du_lieu as dl
from web import giao_dien as gd
from web.giao_dien import so

ds = dl.tat_ca()
b4 = ds["tong_hop"]
ac, ky = dl.anh_chup()
ds_ky = dl.ds_ky()
ky_truoc = ds_ky[-2]
quy, nam = int(ky[-1]), int(ky[:4])
ngay_cuoi = pd.Period(ky, freq="Q").end_time
nhan_truoc = f"Q{ky_truoc[-1]}/{ky_truoc[:4]}"

# ---- Số liệu ngành ---------------------------------------------------------------------------
tb = b4.groupby("ky")[["roe", "nim", "npl", "ty_suat_sinh_loi_quy"]].mean().reindex(ds_ky)
d_roe = tb.loc[ky, "roe"] - tb.loc[ky_truoc, "roe"]
d_npl = tb.loc[ky, "npl"] - tb.loc[ky_truoc, "npl"]
q = ac.set_index("ma_nh")
cp_tot, cp_kem = q["ty_suat_sinh_loi_quy"].idxmax(), q["ty_suat_sinh_loi_quy"].idxmin()

y_roe = "sinh lời hạ nhiệt" if d_roe < -0.3 else ("sinh lời cải thiện" if d_roe > 0.3 else "sinh lời đi ngang")
y_npl = "nợ xấu nhích lên" if d_npl > 0.05 else ("nợ xấu giảm" if d_npl < -0.05 else "nợ xấu ổn định")

gd.dau_trang("Tổng quan ngành", f"Bản tin quý {quy}/{nam}",
             f"Bình quân 8 ngân hàng · số liệu tài chính đến {ngay_cuoi:%d/%m/%Y}")
gd.nhan_dinh(f"{gd.hoa_dau(y_roe)}, {y_npl}.", f"Nhận định · Quý {quy}/{nam}",
             ben_phai=gd.vien(f"{cp_tot} {so(q.loc[cp_tot, 'ty_suat_sinh_loi_quy'], dau=True)} · tăng mạnh nhất",
                              "tot" if q.loc[cp_tot, "ty_suat_sinh_loi_quy"] >= 0 else "xau")
             + gd.vien(f"{cp_kem} {so(q.loc[cp_kem, 'ty_suat_sinh_loi_quy'], dau=True)} · "
                       f"{'giảm sâu nhất' if q.loc[cp_kem, 'ty_suat_sinh_loi_quy'] < 0 else 'tăng ít nhất'}",
                       "xau" if q.loc[cp_kem, "ty_suat_sinh_loi_quy"] < 0 else ""))

o = []
for cs, nhan, chieu in [("roe", "ROE bình quân", 1), ("nim", "Biên lãi NIM bình quân", 1),
                        ("npl", "Tỷ lệ nợ xấu bình quân", -1), ("ty_suat_sinh_loi_quy", "Giá cổ phiếu trong quý", 0)]:
    hien_tai, truoc = tb.loc[ky, cs], tb.loc[ky_truoc, cs]
    gia = cs == "ty_suat_sinh_loi_quy"
    o.append({"nhan": nhan, "so": so(hien_tai, dau=gia),
              "phu": gd.vien(f"{nhan_truoc}: {so(truoc, dau=True)}") if gia else gd.bien_dong(hien_tai - truoc, chieu),
              "ghi": "12 quý gần nhất" if gia else f"so với {nhan_truoc}",
              "spark": gd.sparkline(tb[cs].tolist()[-12:])})
gd.the_so(o)

# ---- Bảng xếp hạng ---------------------------------------------------------------------------------
TIEU_CHI = {"ROE": ("roe", False), "Biên lãi": ("nim", False), "Nợ xấu thấp": ("npl", True),
            "Giá 12 tháng": ("thay_doi_12t", False), "Tín hiệu quý tới": ("xac_suat", False)}
with gd.the("xep-hang"):
    gd.tieu_the(f"Xếp hạng quý {quy}/{nam}", "Bấm tên ngân hàng để mở hồ sơ")
    tieu_chi = st.segmented_control("Xếp theo", list(TIEU_CHI), default="ROE", key="bt_xep",
                                    label_visibility="collapsed") or "ROE"
    cot, tang_dan = TIEU_CHI[tieu_chi]
    bang = ac.sort_values(cot, ascending=tang_dan).reset_index(drop=True)
    dong = []
    for i, r in bang.iterrows():
        p = r["xac_suat"]
        thanh = (f"<span style='display:inline-block;width:56px;height:6px;background:var(--mat2);border-radius:3px;"
                 f"vertical-align:middle;margin-right:8px;position:relative'><span style='position:absolute;left:0;top:0;"
                 f"height:6px;border-radius:3px;width:{p * 56:.0f}px;background:{'var(--nhan)' if p >= 0.5 else 'var(--nen-xam)'}'>"
                 f"</span></span><b>{p:.0%}</b>")
        lop_q = "len" if r["ty_suat_sinh_loi_quy"] >= 0 else "xuong"
        lop_12 = "len" if r["thay_doi_12t"] >= 0 else "xuong"
        dong.append(
            f"<tr><td style='color:var(--nhat);width:28px'>{i + 1}</td>"
            f"<td class='trai chu'><a href='ngan_hang?ma={r['ma_nh']}' target='_self'>{gd.chip(r['ma_nh'], ten=True)}</a></td>"
            f"<td>{so(r['gia_cuoi_quy'], dv='')}</td><td class='{lop_q}'>{so(r['ty_suat_sinh_loi_quy'], 1, dau=True)}</td>"
            f"<td>{gd.sparkline(r['gia_12t'], gd.mau_nh(r['ma_nh']), 84, 24, vung=False)}&nbsp;"
            f"<span class='{lop_12}'>{so(r['thay_doi_12t'], 0, dau=True)}</span></td>"
            f"<td>{so(r['roe'])}</td><td>{so(r['nim'])}</td><td>{so(r['npl'])}</td><td>{so(r['car'])}</td>"
            f"<td class='trai'>{thanh}</td></tr>")
    st.html("<div class='cuon'><table class='bang' style='min-width:900px'><thead><tr><th>#</th><th class='trai'>Ngân hàng</th>"
            "<th>Giá (nghìn đ)</th><th>Trong quý</th><th>12 tháng</th><th>ROE</th><th>NIM</th><th>Nợ xấu</th><th>CAR</th>"
            "<th class='trai'>Tín hiệu quý tới</th></tr></thead><tbody>" + "".join(dong) + "</tbody></table></div>")
    gd.nguon("Giá đã điều chỉnh cổ tức, chia tách. CAR chỉ công bố cuối năm – các quý khác là số gần nhất trước đó. "
             "Tín hiệu quý tới: khả năng giá tăng theo mô hình thống kê, độ tin cậy thấp – xem Dự báo.")

# ---- Sinh lời qua các năm · cổ phiếu -------------------------------------------------------------
with gd.the("bump"):
    xh = ds["xep_hang"]["roe_nam"]
    dau = xh[xh["hang"] == 1].sort_values("nam")
    so_lan = dau["ma_nh"].value_counts()
    vua_qua = dau.iloc[-1]
    a = so_lan.index[0]
    noi_bat = list(dict.fromkeys([a, vua_qua["ma_nh"]]))
    phu = (f"{a} số 1 trong {so_lan.iloc[0]}/{len(dau)} năm"
           + (f" · {vua_qua['ma_nh']} vượt lên năm {int(vua_qua['nam'])}" if vua_qua["ma_nh"] != a else ""))
    gd.tieu_the("Thứ hạng ROE theo năm", phu, f"{int(xh['nam'].min())}–{int(xh['nam'].max())} · ROE cả năm")
    bd.ve(bd.bump(xh, noi_bat, cao=360), key="bt_bump")

with gd.the("co-phieu"):
    ky_gia = st.session_state.get("bt_kygia") or "Trong quý"
    tot, kem = q["thay_doi_12t"].idxmax(), q["thay_doi_12t"].idxmin()
    gd.tieu_the("Giá cổ phiếu",
                f"Bình quân {so(tb.loc[ky, 'ty_suat_sinh_loi_quy'], dau=True)} trong quý {quy}/{nam}" if ky_gia == "Trong quý"
                else f"12 tháng qua: {tot} {so(q.loc[tot, 'thay_doi_12t'], 0, dau=True)}, "
                     f"{kem} {so(q.loc[kem, 'thay_doi_12t'], 0, dau=True)}",
                "Đã điều chỉnh cổ tức, chia tách")
    st.segmented_control("Kỳ", ["Trong quý", "12 tháng"], default="Trong quý", key="bt_kygia",
                         label_visibility="collapsed")
    if ky_gia == "Trong quý":
        bd.ve(bd.loi_suat_quy(ac, cao=360), key="bt_quy")
    else:
        gia = dl.gia_12_thang(ds["gia_ngay"])
        bd.ve(bd.duong(gia, "ngay", "thay_doi", [tot, kem], trung_vi=False, le=0, nhan_tat_ca=True, dau=True, cao=440),
              key="bt_gia")

# ---- Tin doanh nghiệp --------------------------------------------------------------------------------------
sk = ds["su_kien_chi_tiet"]
sk_q = sk[sk["ky"] == ky]
loai = sk_q["loai_su_kien_nhan"].value_counts()
with gd.the("tin"):
    gd.tieu_the("Tin doanh nghiệp", f"{len(sk_q)} sự kiện trong quý {quy}/{nam} · lọc từ công bố thông tin CafeF, VNDirect",
                " ".join(f"<span class='the'>{gd.e(t)} · {n}</span>" for t, n in loai.items()))
    st.html(gd.ds_tin(sk.sort_values("ngay_cong_bo", ascending=False).head(6).itertuples()))

gd.chan_trang()
