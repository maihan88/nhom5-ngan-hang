import streamlit as st

from src import config as cf
from web import bieu_do as bd
from web import du_lieu as dl
from web import giao_dien as gd
from web import mo_hinh as mh
from web.giao_dien import so

ds = dl.tat_ca()
b4 = ds["tong_hop"]
ds_ky = dl.ds_ky()

gd.dau_trang("So sánh", "Đặt các ngân hàng cạnh nhau",
             "Ngân hàng không được chọn hiện màu xám làm nền")
mac_dinh = list(dict.fromkeys([st.session_state.get("ma", "VCB"), "TCB" if st.session_state.get("ma") != "TCB" else "VCB"]))
with gd.the("chon"):
    c1, c2 = st.columns([2.4, 1.6], vertical_alignment="bottom", gap="large")
    chon = c1.pills("Ngân hàng (chọn nhiều)", cf.DS_NGAN_HANG, selection_mode="multi", default=mac_dinh, key="ss_nh") or mac_dinh
    nam = c2.select_slider("Giai đoạn", options=cf.DS_NAM, value=(cf.DS_NAM[0], cf.DS_NAM[-1]), key="ss_nam")
ds_nam = list(range(nam[0], nam[1] + 1))
ky_loc = [k for k in ds_ky if int(k[:4]) in ds_nam]
ky = ky_loc[-1]
chon = [m for m in cf.DS_NGAN_HANG if m in chon]

# ---- Đối đầu ----------------------------------------------------------------------------------------------
q = b4[b4["ky"] == ky].set_index("ma_nh")
TC = [c for c in cf.DS_CHI_SO if cf.CHIEU_TOT[c]] + ["ty_suat_sinh_loi_quy"]
chieu = {**cf.CHIEU_TOT, "ty_suat_sinh_loi_quy": 1}
ten_tc = {**mh.TEN_BIEN, "ty_suat_sinh_loi_quy": "Giá trong quý", "ldr": "LDR"}
thang = {m: 0 for m in chon}
dong = []
for c in TC + ["ldr"]:
    gt = q.loc[chon, c]
    tot = (gt.idxmax() if chieu[c] > 0 else gt.idxmin()) if chieu[c] and len(chon) > 1 else None
    if tot and c in TC:
        thang[tot] += 1
    lon = gt.abs().max() or 1
    o = "".join(
        f"<td><div style='display:flex;align-items:center;justify-content:flex-end;gap:10px'>"
        f"<span style='display:inline-block;height:8px;border-radius:2px;width:{abs(gt[m]) / lon * 70:.0f}px;"
        f"background:var(--nh-{m.lower()});opacity:{1 if m == tot or not tot else .4}'></span>"
        f"<span style='{'font-weight:700' if m == tot else 'color:var(--muc2)'};min-width:64px'>"
        f"{so(gt[m], dau=c == 'ty_suat_sinh_loi_quy')}{' ●' if m == tot else ''}</span></div></td>" for m in chon)
    dong.append(f"<tr><td class='trai chu'>{ten_tc[c]}</td>{o}<td style='color:var(--nhat)'>"
                f"{so(q[c].median(), dau=c == 'ty_suat_sinh_loi_quy')}</td></tr>")
dan_dau = max(thang, key=thang.get)
if len(chon) == 2:
    khac = [m for m in chon if m != dan_dau][0]
    cau = (f"{cf.TEN_DAY_DU[dan_dau]} nhỉnh hơn {cf.TEN_DAY_DU[khac]} ở {thang[dan_dau]}/{len(TC)} tiêu chí."
           if thang[dan_dau] != thang[khac] else f"{cf.TEN_DAY_DU[chon[0]]} và {cf.TEN_DAY_DU[chon[1]]} ngang ngửa nhau.")
elif len(chon) > 2:
    cau = f"{cf.TEN_DAY_DU[dan_dau]} dẫn đầu {thang[dan_dau]}/{len(TC)} tiêu chí trong nhóm đã chọn."
else:
    cau = f"Chọn thêm ít nhất một ngân hàng để so sánh với {cf.TEN_DAY_DU[chon[0]]}."
gd.nhan_dinh(cau, f"Nhận định · Quý {ky[-1]}/{ky[:4]}")

with gd.the("doi-dau"):
    gd.tieu_the(f"Đối đầu · quý {ky[-1]}/{ky[:4]}", "● tốt nhất ở tiêu chí đó (nợ xấu: thấp là tốt; LDR không chấm)")
    st.html("<div class='cuon'><table class='bang' style='min-width:640px'><thead><tr><th>Tiêu chí</th>"
            + "".join(f"<th>{gd.chip(m)}</th>" for m in chon) + "<th>Trung vị 8 NH</th></tr></thead><tbody>"
            + "".join(dong) + "</tbody></table></div>")

# ---- Xu hướng chỉ số -------------------------------------------------------------------------------------------
with gd.the("xu-huong"):
    chi_so = st.session_state.get("ss_cs") or "roe"
    d = b4[b4["ky"].isin(ky_loc)]
    if chi_so == "car":
        d = d[d["car_cong_bo"]].copy()
        d["moc"] = d["nam"]
    else:
        d = d.copy()
        d["moc"] = d["ky"]
    bien = []
    for m in chon:
        s = d[d["ma_nh"] == m].sort_values("moc")[chi_so].dropna()
        if len(s) > 1:
            bien.append((abs(s.iloc[-1] - s.iloc[0]), m, s.iloc[0], s.iloc[-1]))
    if bien:
        _, m, dau, cuoi = max(bien)
        phu = f"{m} {'tăng' if cuoi > dau else 'giảm'} từ {so(dau)} {'lên' if cuoi > dau else 'xuống'} {so(cuoi)} trong {nam[0]}–{nam[1]}"
    else:
        phu = f"Diễn biến {mh.TEN_BIEN[chi_so]}"
    gd.tieu_the("Xu hướng", phu)
    st.segmented_control("Chỉ số", cf.DS_CHI_SO, default="roe", format_func=mh.TEN_BIEN.get, key="ss_cs",
                         label_visibility="collapsed")
    bd.ve(bd.duong(d, "moc", chi_so, chon, nhan_tat_ca=True), key="ss_duong")
    gd.nguon(cf.NHAN_CHI_SO[chi_so] + (" – số công bố cuối năm" if chi_so == "car" else
             " theo quý, đã năm hóa" if chi_so in ("roa", "roe", "nim") else " theo quý") + " · nét chấm: trung vị 8 ngân hàng")

# ---- Xếp hạng sinh lời · quốc doanh và tư nhân -----------------------------------------------------------------------
c1, c2 = st.columns(2, gap="medium")
with c1, gd.the("xep-hang"):
    loai = st.session_state.get("ss_xh") or "roe_nam"
    xh = ds["xep_hang"][loai]
    xh = xh[xh["nam"].isin(ds_nam)]
    cau = []
    for m in chon[:3]:
        s = xh[xh["ma_nh"] == m].sort_values("nam")
        h0, h1 = int(s["hang"].iloc[0]), int(s["hang"].iloc[-1])
        cau.append(f"{m} #{h0} → #{h1}" if h0 != h1 else f"{m} giữ #{h0}")
    gd.tieu_the("Xếp hạng sinh lời", " · ".join(cau) if len(ds_nam) > 1 else "Xếp hạng trong năm")
    st.segmented_control("Thước đo", ["roe_nam", "roa_nam"], default="roe_nam", key="ss_xh", label_visibility="collapsed",
                         format_func={"roe_nam": "ROE cả năm", "roa_nam": "ROA cả năm"}.get)
    bd.ve(bd.bump(xh, chon, cao=360), key="ss_bump")

kd = ds["kiem_dinh_nhom"]
if kd is not None:
    with c2, gd.the("qd-tn"):
        chinh = kd[kd["phan_tich"] == "chinh"].set_index("chi_so")
        ten = {"nim": "Biên lãi NIM", "npl": "Nợ xấu", "car": "Vốn đệm CAR"}
        nam_car = sorted(b4.loc[b4["car_nguon"].isin(["cong_bo", "tra_thu_cong"]), "nam"].unique())
        gd.tieu_the("Quốc doanh và tư nhân", f"Bình quân {dl.giai_doan()}")
        st.html("<div style='display:flex;gap:16px;flex-wrap:wrap;font-size:.78rem;color:var(--nhat);margin-bottom:4px'>"
                f"<span><span class='chip'><i style='background:{gd.mau_nhom('A')};border-radius:50%'></i></span> Quốc doanh (QD): VCB, BID, CTG</span>"
                f"<span><span class='chip'><i style='background:{gd.mau_nhom('B')};border-radius:50%'></i></span> Tư nhân (TN): TCB, MBB, ACB, STB, VPB</span></div>")

        dong_kd = []
        for c in ["nim", "npl", "car"]:
            r = chinh.loc[c]
            cao = "tư nhân" if r["tb_tu_nhan"] > r["tb_quoc_doanh"] else "quốc doanh"
            ghi = f"Nhóm {cao} cao hơn" if r["bac_bo_H0"] else "Chênh lệch chưa đủ lớn để kết luận"
            if c == "car":
                ghi += f" · số công bố cuối năm {nam_car[0]}–{nam_car[-1]}"
            dong_kd.append({"ten": ten[c], "qd": r["tb_quoc_doanh"], "tn": r["tb_tu_nhan"], "y_nghia": bool(r["bac_bo_H0"]), "ghi": ghi})
        gd.dumbbell(dong_kd, gd.mau_nhom("A"), gd.mau_nhom("B"))
        with st.expander("Chi tiết thống kê"):
            TEN_MAU = {"chinh": "Mẫu chính", "khong_VPB": "Bỏ VPB", "car_chi_so_vndirect": "CAR theo VNDirect",
                       "cap_ngan_hang": "Trung bình từng ngân hàng (8 quan sát)"}
            x = kd.copy()
            x["Chỉ số"] = x["chi_so"].map(ten)
            x["Mẫu"] = x["mau_du_lieu"].map(TEN_MAU).fillna(x["mau_du_lieu"])
            st.dataframe(x[["Chỉ số", "Mẫu", "n_quoc_doanh", "n_tu_nhan", "tb_quoc_doanh", "tb_tu_nhan", "kiem_dinh", "p_value",
                            "bac_bo_H0"]], hide_index=True, width="stretch", column_config={
                "n_quoc_doanh": "n QD", "n_tu_nhan": "n TN",
                "tb_quoc_doanh": st.column_config.NumberColumn("TB quốc doanh", format="%.2f%%"),
                "tb_tu_nhan": st.column_config.NumberColumn("TB tư nhân", format="%.2f%%"),
                "kiem_dinh": "Kiểm định", "p_value": st.column_config.NumberColumn("p-value", format="%.4f"),
                "bac_bo_H0": st.column_config.CheckboxColumn("Khác biệt rõ")})
            st.caption("“Khác biệt rõ” khi p-value dưới 0,05, tức khả năng chênh lệch chỉ do ngẫu nhiên dưới 5%. "
                       "Kết luận đáng tin hơn khi vẫn giữ nguyên lúc bỏ VPB hoặc đổi nguồn CAR.")

gd.chan_trang()
