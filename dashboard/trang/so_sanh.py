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

st.html("<div class='muc dau'><div class='kicker'>So sánh</div><h2 style='font-size:2.3rem'>Đặt các ngân hàng cạnh nhau</h2>"
        "<p class='dek'>Chọn vài ngân hàng để làm nổi bật – các ngân hàng còn lại hiện màu xám để làm nền so sánh.</p></div>")
mac_dinh = list(dict.fromkeys([st.session_state.get("ma", "VCB"), "TCB" if st.session_state.get("ma") != "TCB" else "VCB"]))
c1, c2 = st.columns([3, 1.3], vertical_alignment="bottom")
chon = c1.pills("Ngân hàng", cf.DS_NGAN_HANG, selection_mode="multi", default=mac_dinh, key="ss_nh") or mac_dinh
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
    o = "".join(f"<td style='{'font-weight:700' if m == tot else 'color:var(--muc2)'}'>"
                f"{so(gt[m], dau=c == 'ty_suat_sinh_loi_quy')}{' ●' if m == tot else ''}</td>" for m in chon)
    dong.append(f"<tr><td class='trai'>{ten_tc[c]}</td>{o}<td style='color:var(--nhat)'>{so(q[c].median())}</td></tr>")
dan_dau = max(thang, key=thang.get)
if len(chon) == 2:
    khac = [m for m in chon if m != dan_dau][0]
    tieu = (f"{cf.TEN_DAY_DU[dan_dau]} nhỉnh hơn {cf.TEN_DAY_DU[khac]} ở {thang[dan_dau]}/{len(TC)} tiêu chí"
            if thang[dan_dau] != thang[khac] else f"{cf.TEN_DAY_DU[chon[0]]} và {cf.TEN_DAY_DU[chon[1]]} ngang ngửa nhau")
elif len(chon) > 2:
    tieu = f"{cf.TEN_DAY_DU[dan_dau]} dẫn đầu {thang[dan_dau]}/{len(TC)} tiêu chí trong nhóm chọn"
else:
    tieu = f"{cf.TEN_DAY_DU[chon[0]]} trong quý {ky[-1]}/{ky[:4]}"
gd.muc(f"Đối đầu · quý {ky[-1]}/{ky[:4]}", tieu, "Chấm ● đánh dấu ngân hàng tốt nhất ở mỗi tiêu chí (nợ xấu: thấp hơn là tốt). "
       "LDR không chấm điểm vì không có mức “tốt” chung.")
st.html("<div class='cuon'><table class='bang'><thead><tr><th>Tiêu chí</th>"
        + "".join(f"<th>{gd.chip(m)}</th>" for m in chon) + "<th>Trung vị 8 NH</th></tr></thead><tbody>"
        + "".join(dong) + "</tbody></table></div>")

# ---- Xu hướng chỉ số -------------------------------------------------------------------------------------------
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
    tieu = (f"{mh.TEN_BIEN[chi_so]} của {cf.TEN_DAY_DU[m]} {'tăng' if cuoi > dau else 'giảm'} từ {so(dau)} lên {so(cuoi)}"
            if cuoi > dau else f"{mh.TEN_BIEN[chi_so]} của {cf.TEN_DAY_DU[m]} giảm từ {so(dau)} xuống {so(cuoi)}")
    tieu += f" trong {nam[0]}–{nam[1]}"
else:
    tieu = f"Diễn biến {mh.TEN_BIEN[chi_so]}"
gd.muc("Xu hướng", tieu, cf.NHAN_CHI_SO[chi_so] + (" – số công bố cuối năm." if chi_so == "car" else
       " theo quý, năm hóa." if chi_so in ("roa", "roe", "nim") else " theo quý.") + " Đường chấm: trung vị 8 ngân hàng.")
st.pills("Chỉ số", cf.DS_CHI_SO, default="roe", format_func=mh.TEN_BIEN.get, key="ss_cs", label_visibility="collapsed")
bd.ve(bd.duong(d, "moc", chi_so, chon, nhan_tat_ca=True), key="ss_duong")

# ---- Xếp hạng sinh lời -----------------------------------------------------------------------------------------------
loai = st.session_state.get("ss_xh") or "roe_nam"
xh = ds["xep_hang"][loai]
xh = xh[xh["nam"].isin(ds_nam)]
cau = []
for m in chon[:3]:
    s = xh[xh["ma_nh"] == m].sort_values("nam")
    h0, h1 = int(s["hang"].iloc[0]), int(s["hang"].iloc[-1])
    cau.append(f"{m} {'lên' if h1 < h0 else 'xuống' if h1 > h0 else 'giữ'} hạng #{h0} → #{h1}" if h0 != h1
               else f"{m} giữ hạng #{h0}")
gd.muc("Xếp hạng sinh lời", "; ".join(cau) if len(ds_nam) > 1 else "Xếp hạng trong năm",
       f"Thứ hạng {'ROE' if loai == 'roe_nam' else 'ROA'} cả năm (lợi nhuận 4 quý / bình quân "
       f"{'vốn chủ sở hữu' if loai == 'roe_nam' else 'tổng tài sản'}), {nam[0]}–{nam[1]}.")
st.segmented_control("Thước đo", ["roe_nam", "roa_nam"], default="roe_nam", key="ss_xh", label_visibility="collapsed",
                     format_func={"roe_nam": "ROE cả năm", "roa_nam": "ROA cả năm"}.get)
bd.ve(bd.bump(xh, chon), key="ss_bump")

# ---- Quốc doanh vs tư nhân ---------------------------------------------------------------------------------------------
kd = ds["kiem_dinh_nhom"]
if kd is not None:
    chinh = kd[kd["phan_tich"] == "chinh"].set_index("chi_so")
    ten = {"nim": "Biên lãi NIM", "npl": "Nợ xấu", "car": "Vốn đệm CAR"}
    ten_thuong = {"nim": "biên lãi", "npl": "nợ xấu", "car": "vốn đệm CAR"}
    co, khong = [], []
    for c in ["nim", "npl", "car"]:
        r = chinh.loc[c]
        cao_hon = "tư nhân" if r["tb_tu_nhan"] > r["tb_quoc_doanh"] else "quốc doanh"
        (co if r["bac_bo_H0"] else khong).append((ten_thuong[c], cao_hon))
    phan = []
    for nhom_cao in sorted({n for _, n in co}, reverse=True):
        phan.append(f"ngân hàng {nhom_cao} có {' và '.join(t for t, n in co if n == nhom_cao)} cao hơn rõ rệt")
    if khong:
        phan.append(f"{' và '.join(t for t, _ in khong)} chưa khác biệt đáng kể")
    nam_car = sorted(b4.loc[b4["car_nguon"].isin(["cong_bo", "tra_thu_cong"]), "nam"].unique())
    gd.muc("Quốc doanh và tư nhân", gd.hoa_dau("; ".join(phan)),
           f"Quốc doanh: VCB, BID, CTG · Tư nhân: TCB, MBB, ACB, STB, VPB. Trung bình theo năm, {dl.giai_doan()} "
           f"(CAR: số công bố cuối năm {nam_car[0]}–{nam_car[-1]}).")
    gd.dumbbell([{"ten": ten[c], "qd": chinh.loc[c, "tb_quoc_doanh"], "tn": chinh.loc[c, "tb_tu_nhan"],
                  "y_nghia": bool(chinh.loc[c, "bac_bo_H0"])} for c in ["nim", "npl", "car"]],
                cf.MAU_NHOM[cf.NHOM_QUOC_DOANH], cf.MAU_NHOM[cf.NHOM_TU_NHAN])
    gd.nguon("“Khác biệt rõ”: có ý nghĩa thống kê ở mức 5%. "
             + " · ".join(f"{ten[c]}: {chinh.loc[c, 'kiem_dinh']}, p {'< 0,001' if chinh.loc[c, 'p_value'] < 0.001 else '= ' + so(chinh.loc[c, 'p_value'], 3, '')}"
                          for c in ["nim", "npl", "car"]) + ". Phân tích: Hoàng Ngọc Gia Nghi.")
    with st.expander("Chi tiết kiểm định và kiểm tra lại"):
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
        st.caption("Chọn kiểm định: cả hai nhóm phân phối chuẩn → t-test (Student/Welch theo phương sai), ngược lại → "
                   "Mann–Whitney U. Kết luận đáng tin hơn khi giữ nguyên qua các mẫu kiểm tra lại.")

gd.chan_trang()
