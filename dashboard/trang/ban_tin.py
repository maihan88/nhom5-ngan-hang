import pandas as pd
import streamlit as st

from src import config as cf
from web import bieu_do as bd
from web import du_lieu as dl
from web import giao_dien as gd
from web.giao_dien import e, so

ds = dl.tat_ca()
b4 = ds["tong_hop"]
ac, ky = dl.anh_chup()
ds_ky = dl.ds_ky()
ky_truoc = ds_ky[-2]
quy, nam = int(ky[-1]), int(ky[:4])
ngay_cuoi = pd.Period(ky, freq="Q").end_time

# ---- Số liệu ngành ---------------------------------------------------------------------------
tb = b4.groupby("ky")[["roe", "nim", "npl", "ty_suat_sinh_loi_quy"]].mean().reindex(ds_ky)
d_roe = tb.loc[ky, "roe"] - tb.loc[ky_truoc, "roe"]
d_npl = tb.loc[ky, "npl"] - tb.loc[ky_truoc, "npl"]
r_cp = tb.loc[ky, "ty_suat_sinh_loi_quy"]
q = ac.set_index("ma_nh")
cp_tot, cp_kem = q["ty_suat_sinh_loi_quy"].idxmax(), q["ty_suat_sinh_loi_quy"].idxmin()

y_roe = "sinh lời hạ nhiệt" if d_roe < -0.3 else ("sinh lời cải thiện" if d_roe > 0.3 else "sinh lời đi ngang")
y_npl = "nợ xấu nhích lên" if d_npl > 0.05 else ("nợ xấu giảm" if d_npl < -0.05 else "nợ xấu ổn định")
y_cp = "giảm" if r_cp < 0 else "tăng"

st.html(f"<div class='dau-bao'><div class='ten'>{gd.TEN}</div>"
        f"<div class='ngay'>Bản tin quý {quy}/{nam} · số liệu đến {ngay_cuoi:%d/%m/%Y}</div></div>"
        f"<div class='tit'>Quý {quy}/{nam}: {y_roe}, {y_npl}</div>"
        f"<p class='sapo'>ROE bình quân của 8 ngân hàng niêm yết lớn nhất còn {so(tb.loc[ky, 'roe'])}, tỷ lệ nợ xấu "
        f"{so(tb.loc[ky, 'npl'])}. Cổ phiếu ngân hàng {y_cp} bình quân {so(abs(r_cp))} trong quý – "
        f"{cf.TEN_DAY_DU[cp_tot]} giữ giá tốt nhất ({so(q.loc[cp_tot, 'ty_suat_sinh_loi_quy'], dau=True)}), "
        f"{cf.TEN_DAY_DU[cp_kem]} giảm sâu nhất ({so(q.loc[cp_kem, 'ty_suat_sinh_loi_quy'], dau=True)}).</p>")

o = []
for cs, nhan, chieu in [("roe", "ROE bình quân", 1), ("nim", "Biên lãi NIM bình quân", 1),
                        ("npl", "Tỷ lệ nợ xấu bình quân", -1), ("ty_suat_sinh_loi_quy", "Giá cổ phiếu trong quý", 1)]:
    hien_tai, truoc = tb.loc[ky, cs], tb.loc[ky_truoc, cs]
    o.append({"nhan": nhan, "so": so(hien_tai, dau=cs == "ty_suat_sinh_loi_quy"),
              "phu": f"{gd.bien_dong(hien_tai - truoc, chieu)}&nbsp;so với quý trước" if cs != "ty_suat_sinh_loi_quy"
              else f"quý trước {so(truoc, dau=True)}",
              "spark": gd.sparkline(tb[cs].tolist()[-12:])})
gd.day_so(o)
gd.nguon("Bình quân 8 ngân hàng. ROE, NIM năm hóa từ số liệu quý. Đường nhỏ: 12 quý gần nhất.")

# ---- Bảng xếp hạng ---------------------------------------------------------------------------------
roe_max, npl_min = q["roe"].idxmax(), q["npl"].idxmin()
gd.muc(f"Bảng xếp hạng · quý {quy}/{nam}",
       f"{cf.TEN_DAY_DU[roe_max]} sinh lời tốt nhất, {cf.TEN_DAY_DU[npl_min]} có nợ xấu thấp nhất"
       if roe_max != npl_min else f"{cf.TEN_DAY_DU[roe_max]} vừa sinh lời tốt nhất vừa có nợ xấu thấp nhất",
       "Bấm tên ngân hàng để xem hồ sơ chi tiết.")
TIEU_CHI = {"ROE": ("roe", False), "Biên lãi": ("nim", False), "Nợ xấu thấp": ("npl", True),
            "Giá 12 tháng": ("thay_doi_12t", False), "Tín hiệu quý tới": ("xac_suat", False)}
tieu_chi = st.segmented_control("Xếp theo", list(TIEU_CHI), default="ROE", key="bt_xep") or "ROE"
cot, tang_dan = TIEU_CHI[tieu_chi]
bang = ac.sort_values(cot, ascending=tang_dan).reset_index(drop=True)

dong = []
for i, r in bang.iterrows():
    p = r["xac_suat"]
    thanh = (f"<span style='display:inline-block;width:64px;height:6px;background:var(--ke);border-radius:3px;"
             f"vertical-align:middle;margin-right:8px;position:relative'><span style='position:absolute;left:0;top:0;"
             f"height:6px;border-radius:3px;width:{p * 64:.0f}px;background:{gd.MAU['muc'] if p >= 0.5 else gd.MAU['nen_xam']}'>"
             f"</span></span>{p:.0%}")
    lop_q = "len" if r["ty_suat_sinh_loi_quy"] >= 0 else "xuong"
    lop_12 = "len" if r["thay_doi_12t"] >= 0 else "xuong"
    dong.append(
        f"<tr><td style='color:var(--nhat);width:28px'>{i + 1}</td>"
        f"<td class='trai'><a href='ngan_hang?ma={r['ma_nh']}' target='_self'>{gd.chip(r['ma_nh'], ten=True)}</a></td>"
        f"<td>{so(r['gia_cuoi_quy'], dv='')}</td><td class='{lop_q}'>{so(r['ty_suat_sinh_loi_quy'], 1, dau=True)}</td>"
        f"<td>{gd.sparkline(r['gia_12t'], cf.MAU_NGAN_HANG[r['ma_nh']], 84, 24)}&nbsp;"
        f"<span class='{lop_12}'>{so(r['thay_doi_12t'], 0, dau=True)}</span></td>"
        f"<td>{so(r['roe'])}</td><td>{so(r['nim'])}</td><td>{so(r['npl'])}</td><td>{so(r['car'])}</td>"
        f"<td class='trai'>{thanh}</td></tr>")
st.html("<div class='cuon'><table class='bang'><thead><tr><th>#</th><th class='trai'>Ngân hàng</th><th>Giá (nghìn đ)</th>"
        "<th>Trong quý</th><th>12 tháng</th><th>ROE</th><th>NIM</th><th>Nợ xấu</th><th>CAR</th>"
        "<th class='trai'>Tín hiệu quý tới</th></tr></thead><tbody>" + "".join(dong) + "</tbody></table></div>")
gd.nguon("Giá đã điều chỉnh cổ tức, chia tách. CAR chỉ công bố cuối năm – các quý khác là số gần nhất trước đó. "
         "Tín hiệu quý tới: khả năng giá tăng theo mô hình thống kê, độ tin cậy thấp – xem mục Dự báo.")

# ---- Sinh lời qua các năm ------------------------------------------------------------------------
xh = ds["xep_hang"]["roe_nam"]
dau = xh[xh["hang"] == 1].sort_values("nam")
so_lan = dau["ma_nh"].value_counts()
vua_qua = dau.iloc[-1]
a = so_lan.index[0]
noi_bat = list(dict.fromkeys([a, vua_qua["ma_nh"]]))
tieu = (f"{cf.TEN_DAY_DU[a]} đứng đầu về sinh lời {so_lan.iloc[0]}/{len(dau)} năm"
        + (f", năm {int(vua_qua['nam'])} {cf.TEN_DAY_DU[vua_qua['ma_nh']]} vượt lên" if vua_qua["ma_nh"] != a else ""))
gd.muc("Sinh lời qua các năm", tieu,
       "Thứ hạng ROE cả năm của 8 ngân hàng (lợi nhuận 4 quý / vốn chủ sở hữu bình quân).")
bd.ve(bd.bump(xh, noi_bat), key="bt_bump")

# ---- Cổ phiếu 12 tháng ---------------------------------------------------------------------------------
gia = dl.gia_12_thang(ds["gia_ngay"])
tot, kem = q["thay_doi_12t"].idxmax(), q["thay_doi_12t"].idxmin()
gd.muc("Cổ phiếu 12 tháng",
       f"12 tháng qua, {cf.TEN_DAY_DU[tot]} tăng {so(q.loc[tot, 'thay_doi_12t'], 0)}, "
       f"{cf.TEN_DAY_DU[kem]} {'tăng' if q.loc[kem, 'thay_doi_12t'] >= 0 else 'giảm'} {so(abs(q.loc[kem, 'thay_doi_12t']), 0)}",
       "Thay đổi giá so với phiên đầu kỳ, đã điều chỉnh cổ tức và chia tách.")
bd.ve(bd.duong(gia, "ngay", "thay_doi", [tot, kem], trung_vi=False, le=0, nhan_tat_ca=True, dau=True), key="bt_gia")

# ---- Tin doanh nghiệp --------------------------------------------------------------------------------------
sk = ds["su_kien_chi_tiet"]
sk_q = sk[sk["ky"] == ky]
loai = sk_q["loai_su_kien_nhan"].value_counts()
gd.muc("Tin doanh nghiệp",
       f"{len(sk_q)} sự kiện đáng chú ý trong quý {quy}/{nam}" + (f", nhiều nhất là {loai.index[0].lower()}" if len(loai) else ""),
       "Tăng vốn, thay đổi lãnh đạo, hợp tác, chuyển đổi số… lọc từ công bố thông tin trên CafeF và VNDirect.")
tin = []
for r in sk.sort_values("ngay_cong_bo", ascending=False).head(6).itertuples():
    tin.append(f"<div class='tin'><div class='ngay'>{r.ngay_cong_bo:%d/%m/%Y}</div><div>"
               f"<div class='meta'>{gd.chip(r.ma_nh)} &nbsp;·&nbsp; {e(r.loai_su_kien_nhan)}</div>"
               f"<div class='tieu'><a href='{e(r.nguon)}' target='_blank'>{e(r.mo_ta_ngan)}</a></div></div></div>")
st.html("".join(tin))

gd.chan_trang()
