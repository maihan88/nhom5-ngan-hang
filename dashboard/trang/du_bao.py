import streamlit as st

from src import config as cf
from web import bieu_do as bd
from web import du_lieu as dl
from web import giao_dien as gd
from web import mo_hinh as mh
from web.giao_dien import so

ds = dl.tat_ca()
kq = dl.du_bao()
d = kq["du_lieu"]
dg = kq["danh_gia"].set_index("mo_hinh")
nam_test, n_test = kq["nam_test"], kq["n_test"]
ds_ky = [k for k in dl.ds_ky() if k in set(d["ky"])]
ky = ds_ky[-1]
q_toi, n_toi = (int(ky[-1]) % 4 + 1, int(ky[:4]) + (ky[-1] == "4"))

gd.dau_trang("Dự báo", f"Tín hiệu quý {q_toi}/{n_toi}",
             f"Dựa trên số liệu tài chính và sự kiện của quý {ky[-1]}/{ky[:4]}")
st.segmented_control("Dữ liệu dùng để dự báo", list(mh.MO_HINH), default=mh.MAC_DINH, format_func=mh.TEN_VIET.get,
                     key="db_mh")
ten_mh = st.session_state.get("db_mh") or mh.MAC_DINH
t = kq["du_doan_test"]
t = t[t["mo_hinh"] == ten_mh].copy()
t["dung"] = (t["xac_suat"] >= 0.5) == (t[mh.NHAN] == 1)
so_dung = int(t["dung"].sum())

gd.canh_bao(f"<b>Độ tin cậy thấp.</b> Thử trên năm {nam_test}, mô hình đoán đúng chiều giá {so_dung}/{len(t)} lần, "
            "chỉ nhỉnh hơn đoán bừa. Chỉ để tham khảo, không phải khuyến nghị đầu tư.")

moi = d[d["ky"] == ky].copy()
moi["xac_suat"] = mh.xac_suat(kq, ten_mh, moi)
n_tang = int((moi["xac_suat"] >= 0.5).sum())
gd.nhan_dinh(f"Mô hình nghiêng về tăng giá cho {n_tang}/{len(moi)} ngân hàng.", f"Nhận định · Quý {q_toi}/{n_toi}")

# ---- Tín hiệu quý tới · vì sao khó dự báo --------------------------------------------------------------------
c1, c2 = st.columns(2, gap="medium")
with c1, gd.the("xac-suat"):
    gd.tieu_the("Khả năng giá tăng quý tới", "Trên 50%: mô hình nghiêng về tăng")
    bd.ve(bd.xac_suat(moi, cao=340), key="db_xs")
    gd.nguon("“Tăng”: giá 45 ngày sau khi kết thúc quý tới (lúc báo cáo tài chính đã công bố) cao hơn cùng mốc của quý này.")

tq = ds["tuong_quan"]
if tq is not None:
    with c2, gd.the("tuong-quan"):
        chinh = tq[tq["mau_du_lieu"] == "chinh"]
        manh = chinh.loc[chinh["spearman_rho"].abs().idxmax()]
        co_y_nghia = int((chinh["spearman_p_hieu_chinh"] < 0.05).sum())
        gd.tieu_the("Vì sao khó dự báo",
                    "Chỉ số tài chính gần như không đi cùng giá cổ phiếu trong quý" if co_y_nghia == 0
                    else f"{co_y_nghia} chỉ số có liên hệ rõ với giá cổ phiếu trong quý")
        bd.ve(bd.tuong_quan(chinh, cao=340), key="db_tq")
        gd.nguon("Mức độ đi cùng nhau từ −1 (ngược chiều hoàn toàn) đến +1 (cùng chiều hoàn toàn). Mạnh nhất là "
                 f"{cf.TEN_NGAN[manh['chi_so']]} với {so(manh['spearman_rho'], 2, '', dau=True)} – gần như bằng 0.")

# ---- Kiểm chứng ----------------------------------------------------------------------------------------------------
quy = sorted(t["quy"].unique())
o = "".join(f"<span class='nguon' style='font-weight:600'>{q_}/{nam_test}</span>" for q_ in quy)
for m in cf.DS_NGAN_HANG:
    o += f"<span style='display:flex;align-items:center'>{gd.chip(m)}</span>"
    for q_ in quy:
        r = t[(t["ma_nh"] == m) & (t["quy"] == q_)]
        if r.empty:
            o += "<span class='o-nho'>–</span>"
            continue
        r = r.iloc[0]
        dung = bool(r["dung"])
        o += (f"<div class='o-nho {'dung' if dung else 'sai'}'><b><span class='{'len' if dung else 'xuong'}'>"
              f"{'✓' if dung else '✗'}</span> <span class='num'>{r['xac_suat']:.0%}</span></b>"
              f"<span class='num' style='font-size:.74rem;color:var(--nhat)'>thực tế {so(r['ty_suat_sinh_loi_quy_sau'], 1, dau=True)}</span></div>")
with gd.the("kiem-chung"):
    gd.tieu_the(f"Thử trên năm {nam_test}",
                f"Học từ dữ liệu {ds_ky[0][:4]}–{nam_test - 1} rồi đoán cho {nam_test} · đúng {so_dung}/{len(t)} lần, "
                f"nếu lúc nào cũng đoán “tăng” thì đúng {int(round(dg.loc['Baseline', 'Accuracy'] * len(t)))}/{len(t)}",
                "<span class='len'>✓ đúng chiều</span> &nbsp; <span class='xuong'>✗ sai chiều</span>")
    st.html(f"<div class='cuon'><div style='min-width:640px;display:grid;grid-template-columns:110px "
            f"repeat({len(quy)},minmax(0,1fr));gap:6px'><span></span>{o}</div></div>")
    gd.nguon("Mỗi ô: khả năng tăng mô hình đưa ra và biến động giá thực tế quý sau.")

# ---- So sánh phiên bản · giải thích ------------------------------------------------------------------------------
c1, c2 = st.columns(2, gap="medium")
with c1, gd.the("phien-ban"):
    tc, sk = dg.loc["Financial Only"], dg.loc["Financial + General Event"]
    gd.tieu_the("Thêm dữ liệu sự kiện có giúp không",
                ("Có cải thiện nhẹ" if sk["Accuracy"] > tc["Accuracy"] else "Chưa cải thiện")
                + f": đúng {round(tc['Accuracy'] * n_test)}/{n_test} → {round(sk['Accuracy'] * n_test)}/{n_test} lần khi biết "
                "quý đó ngân hàng có tin tăng vốn, đổi lãnh đạo, hợp tác…")
    bd.ve(bd.so_sanh_mo_hinh(kq["danh_gia"], cao=260), key="db_ss")
    gd.nguon("Chênh lệch chỉ vài lần đoán, chưa đủ để khẳng định.")

with c2, gd.the("giai-thich"):
    a, b = st.columns([1.3, 1], vertical_alignment="bottom")
    ma = a.selectbox("Ngân hàng", cf.DS_NGAN_HANG, index=cf.DS_NGAN_HANG.index(st.session_state.get("ma", "VCB")),
                     key="db_ma", format_func=lambda m: f"{m} · {cf.TEN_DAY_DU[m]}")
    st.session_state["ma"] = ma
    ky_xem = b.selectbox("Kỳ", ds_ky[::-1], format_func=lambda k: f"Số liệu Q{k[-1]}/{k[:4]}", key="db_ky")
    dong_xem = d[(d["ma_nh"] == ma) & (d["ky"] == ky_xem)]
    p = float(mh.xac_suat(kq, ten_mh, dong_xem)[0])
    dg_ma, chan = mh.dong_gop(kq, ten_mh, dong_xem)
    gd.tieu_the("Yếu tố kéo tín hiệu", f"{ma} · khả năng tăng {p:.0%} · chỉ là liên hệ thống kê, không phải nhân quả")
    bd.ve(bd.dong_gop(dg_ma, cao=260), key="db_dg")

with gd.the("lich-su"):
    gd.tieu_the(f"Tín hiệu qua các quý · {ma}",
                f"Chấm xanh: đoán đúng · ✕ đỏ: đoán sai · chỉ năm {nam_test} (vùng xám) là dự báo thật, các năm trước mô hình "
                "đã được học")
    ls = d[d["ma_nh"] == ma].copy()
    ls["p"] = mh.xac_suat(kq, ten_mh, ls)
    bd.ve(bd.lich_su_tin_hieu(ls, ma, nam_test, mh.NHAN), key="db_ls")

gd.chan_trang()
