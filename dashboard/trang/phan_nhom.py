import streamlit as st

from src import config as cf
from web import bieu_do as bd
from web import du_lieu as dl
from web import giao_dien as gd
from web import mo_hinh as mh
from web.giao_dien import e, so

ds = dl.tat_ca()
pn = dl.phan_nhom()
d = pn["du_lieu"]
ho_so = pn["ho_so"]
ds_ky = [k for k in dl.ds_ky() if k in set(d["ky"])]

# Thành viên chính của mỗi nhóm: ngân hàng có quá nửa số quý thuộc nhóm đó
ty_le = d.groupby("ma_nh")["nhom"].value_counts(normalize=True).rename("tl").reset_index()
thanh_vien = {n: [m for m in cf.DS_NGAN_HANG if ((ty_le["ma_nh"] == m) & (ty_le["nhom"] == n) & (ty_le["tl"] > 0.5)).any()]
              for n in ho_so["nhom"]}
nho = ho_so.sort_values("so_quan_sat").iloc[0]
tv_nho = thanh_vien[nho["nhom"]]
tieu = (f"{' và '.join(cf.TEN_DAY_DU[m] for m in tv_nho)} đứng riêng một nhóm: {nho['ten_nhom'].lower()}"
        if tv_nho and len(tv_nho) <= 3 else f"Tám ngân hàng chia thành {pn['k']} nhóm đặc điểm tài chính")
gd.muc("Phân nhóm theo đặc điểm tài chính", tieu,
       f"Gom {len(d)} ngân hàng–quý theo 6 chỉ số (ROA, ROE, NIM, nợ xấu, CAR, LDR). Trên bản đồ, chấm càng gần nhau thì "
       "“dáng” tài chính càng giống nhau; chữ là vị trí trung bình của từng ngân hàng.", dau=True)

c1, c2 = st.columns([3.2, 1], gap="large")
with c2:
    noi_bat = st.selectbox("Vẽ đường đi của", ["Không"] + cf.DS_NGAN_HANG, key="pn_nb")
    for _, r in ho_so.iterrows():
        tv = " ".join(gd.chip(m) for m in thanh_vien[r["nhom"]]) or "<span class='nguon'>–</span>"
        st.html(
            f"<div style='border-top:3px solid {bd.MAU_NHOM[r['nhom']]};padding-top:10px;margin-top:14px'>"
            f"<div style='font-weight:600;font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;"
            f"color:{bd.MAU_NHOM[r['nhom']]}'>Nhóm {r['nhom']} · {int(r['so_quan_sat'])} ngân hàng–quý</div>"
            f"<div style='font-family:Fraunces,Georgia,serif;font-size:1.15rem;font-weight:600;margin:6px 0'>"
            f"{e(r['ten_nhom'])}</div><div style='margin-bottom:8px'>{tv}</div>"
            "<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:6px 10px;font-size:.84rem'>"
            + "".join(f"<div><div style='color:var(--nhat);font-size:.72rem'>{mh.TEN_BIEN[b]}</div>"
                      f"<b>{so(r[b])}</b></div>" for b in mh.FIN) + "</div></div>")
with c1:
    bd.ve(bd.ban_do(pn, None if noi_bat == "Không" else noi_bat), key="pn_bd")
tt = pn["tai_trong"]
truc = {pc: ", ".join(mh.TEN_BIEN[b] for b in tt[pc].abs().nlargest(3).index) for pc in ["PC1", "PC2"]}
gd.nguon(f"Trục ngang chủ yếu phản ánh {truc['PC1']}; trục dọc phản ánh {truc['PC2']}. Hai trục giữ "
         f"{so(pn['phuong_sai'].sum() * 100, 0)} thông tin của 6 chỉ số (PCA). Phân nhóm: K-Means, Hoàng Mạnh Quân.")

# ---- Khác biệt giữa các nhóm ----------------------------------------------------------------------------------
z = pn["z"]
lech = z.loc[nho["nhom"]].abs().nlargest(2)
gd.muc("Khác biệt giữa các nhóm",
       f"Nhóm {nho['nhom']} khác biệt nhất ở {mh.TEN_DE_HIEU[lech.index[0]]} và {mh.TEN_DE_HIEU[lech.index[1]]}",
       f"Mỗi nhóm lệch bao nhiêu so với trung bình {len(d)} ngân hàng–quý, đo bằng độ lệch chuẩn (0 = đúng mức trung bình).")
bd.ve(bd.lech_nhom(z), key="pn_lech")

# ---- Theo thời gian --------------------------------------------------------------------------------------------
o = d.sort_values(["ma_nh", "ky_so"])
truoc = o.groupby("ma_nh")["nhom"].shift()
so_doi = int((truoc.notna() & (truoc != o["nhom"])).sum())
gd.muc("Qua từng quý",
       f"Chỉ {so_doi} lần đổi nhóm trong {len(ds_ky)} quý – nhóm phản ánh đặc điểm bền vững của mỗi ngân hàng"
       if so_doi <= 3 else f"{so_doi} lần đổi nhóm trong {len(ds_ky)} quý",
       "Mỗi ô là một quý của một ngân hàng, tô theo nhóm.")
bd.ve(bd.luoi_nhom(d, ds_ky), key="pn_luoi")

with st.expander("Phương pháp chọn số nhóm"):
    ck = ds["chon_k_quan"] if ds["chon_k_quan"] is not None else pn["chon_k"].rename(columns={"Nhóm nhỏ nhất": "smallest_cluster"})
    st.markdown(f"Chuẩn hóa 6 chỉ số trên toàn bộ mẫu, chạy K-Means với K = 2…6 và chọn K có hệ số silhouette (độ tách "
                f"biệt giữa các nhóm) cao nhất: **K = {pn['k']}**. K = 5, 6 tạo nhóm chỉ vài quan sát – quá nhỏ để có ý nghĩa.")
    a, b = st.columns(2)
    with a:
        bd.ve(bd.duong_nho(ck["K"], ck["Silhouette"], "Silhouette – cao là tách tốt"), key="pn_sil")
    with b:
        bd.ve(bd.duong_nho(ck["K"], ck["Inertia"], "Inertia – tổng khoảng cách trong nhóm", mau=gd.MAU["nhat"]), key="pn_ine")

gd.chan_trang()
