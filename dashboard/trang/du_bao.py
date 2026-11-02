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

gd.dau_trang("Dự báo · Logistic Regression", f"Tín hiệu quý {q_toi}/{n_toi}",
             f"Dựa trên số liệu tài chính và sự kiện của quý {ky[-1]}/{ky[:4]}")
st.segmented_control("Phiên bản mô hình", list(mh.MO_HINH), default=mh.MAC_DINH, format_func=mh.TEN_VIET.get,
                     key="db_mh", label_visibility="collapsed")
ten_mh = st.session_state.get("db_mh") or mh.MAC_DINH
acc, auc = dg.loc[ten_mh, "Accuracy"], dg.loc[ten_mh, "ROC-AUC"]
t = kq["du_doan_test"]
t = t[t["mo_hinh"] == ten_mh].copy()
t["dung"] = (t["xac_suat"] >= 0.5) == (t[mh.NHAN] == 1)
so_dung = int(t["dung"].sum())

gd.canh_bao(f"<b>Độ tin cậy thấp.</b> Kiểm chứng trên năm {nam_test}, mô hình đoán đúng chiều {so_dung}/{len(t)} lần "
            f"({so(acc * 100, 1)}), chỉ nhỉnh hơn đoán bừa. Chỉ để tham khảo, không phải khuyến nghị đầu tư.")

moi = d[d["ky"] == ky].copy()
moi["xac_suat"] = mh.xac_suat(kq, ten_mh, moi)
n_tang = int((moi["xac_suat"] >= 0.5).sum())
gd.nhan_dinh(f"Mô hình nghiêng về tăng giá cho {n_tang}/{len(moi)} ngân hàng.", f"Nhận định · Quý {q_toi}/{n_toi}")

gd.the_so([
    {"nhan": f"Tỷ lệ đúng năm {nam_test}", "so": so(acc * 100, 1), "ghi": "đoán bừa: 50%"},
    {"nhan": "ROC-AUC", "so": so(auc, 2, ""), "ghi": "0,5 = ngẫu nhiên · 1 = hoàn hảo"},
    {"nhan": "Dữ liệu học", "so": str(kq["n_train"]), "ghi": f"ngân hàng–quý, {ds_ky[0][:4]}–{nam_test - 1}"},
    {"nhan": "Dữ liệu kiểm chứng", "so": str(n_test), "ghi": f"ngân hàng–quý, năm {nam_test}"},
])

# ---- Tín hiệu quý tới · vì sao khó dự báo --------------------------------------------------------------------
c1, c2 = st.columns(2, gap="medium")
with c1, gd.the("xac-suat"):
    gd.tieu_the("Khả năng giá tăng quý tới", f"{mh.TEN_VIET[ten_mh]} · vạch dọc: ngưỡng 50%")
    bd.ve(bd.xac_suat(moi, cao=340), key="db_xs")
    gd.nguon("“Tăng” = giá tại mốc 45 ngày sau khi kết thúc quý tới cao hơn mốc tương ứng của quý này. "
             f"Thiết kế mô hình: Hoàng Mạnh Quân · {kq['nguon']}.")

tq = ds["tuong_quan"]
if tq is not None:
    with c2, gd.the("tuong-quan"):
        chinh = tq[tq["mau_du_lieu"] == "chinh"]
        manh = chinh.loc[chinh["spearman_rho"].abs().idxmax()]
        co_y_nghia = int((chinh["spearman_p_hieu_chinh"] < 0.05).sum())
        gd.tieu_the("Chỉ số tài chính và giá cổ phiếu",
                    f"Tương quan hạng Spearman, cùng quý · {int(manh['so_quan_sat'])} ngân hàng–quý · mạnh nhất "
                    f"{cf.TEN_NGAN[manh['chi_so']]} {so(manh['spearman_rho'], 2, '', dau=True)}")
        bd.ve(bd.tuong_quan(chinh, cao=340), key="db_tq")
        gd.nguon(("Không chỉ số nào có ý nghĩa thống kê sau hiệu chỉnh Holm. " if co_y_nghia == 0
                  else f"{co_y_nghia} chỉ số có ý nghĩa sau hiệu chỉnh Holm. ") + "Phân tích: Hoàng Ngọc Gia Nghi.")

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
    gd.tieu_the(f"Kiểm chứng năm {nam_test}",
                f"Học trên {ds_ky[0][:4]}–{nam_test - 1}, thử trên {nam_test} · đúng {so_dung}/{len(t)}, luôn đoán “tăng” được "
                f"{int(round(dg.loc['Baseline', 'Accuracy'] * len(t)))}/{len(t)}",
                "<span class='len'>✓ đúng chiều</span> &nbsp; <span class='xuong'>✗ sai chiều</span>")
    st.html(f"<div class='cuon'><div style='min-width:640px;display:grid;grid-template-columns:110px "
            f"repeat({len(quy)},minmax(0,1fr));gap:6px'><span></span>{o}</div></div>")
    gd.nguon(f"Mỗi ô: khả năng tăng mô hình đưa ra · biến động giá thực tế quý sau. Với {n_test} trường hợp, mỗi lần "
             f"đúng/sai làm tỷ lệ đổi {so(100 / n_test, 1, ' điểm')}.")

# ---- So sánh phiên bản · giải thích ------------------------------------------------------------------------------
c1, c2 = st.columns(2, gap="medium")
with c1, gd.the("phien-ban"):
    tc, sk = dg.loc["Financial Only"], dg.loc["Financial + General Event"]
    gd.tieu_the("Thêm dữ liệu sự kiện có giúp không",
                ("Cải thiện nhẹ nhưng chưa đủ chắc chắn" if sk["ROC-AUC"] > tc["ROC-AUC"] else "Chưa cải thiện dự báo")
                + f" · tỷ lệ đúng {so(tc['Accuracy'] * 100, 1)} → {so(sk['Accuracy'] * 100, 1)}, AUC {so(tc['ROC-AUC'], 2, '')} → "
                f"{so(sk['ROC-AUC'], 2, '')}")
    bd.ve(bd.so_sanh_mo_hinh(kq["danh_gia"], cao=260), key="db_ss")
    gd.nguon(f"Chênh lệch chỉ vài trường hợp trên {n_test}, nên chưa thể khẳng định.")

with c2, gd.the("giai-thich"):
    a, b = st.columns([1.3, 1], vertical_alignment="bottom")
    ma = a.selectbox("Ngân hàng", cf.DS_NGAN_HANG, index=cf.DS_NGAN_HANG.index(st.session_state.get("ma", "VCB")),
                     key="db_ma", format_func=lambda m: f"{m} · {cf.TEN_DAY_DU[m]}")
    st.session_state["ma"] = ma
    ky_xem = b.selectbox("Kỳ", ds_ky[::-1], format_func=lambda k: f"Số liệu Q{k[-1]}/{k[:4]}", key="db_ky")
    dong_xem = d[(d["ma_nh"] == ma) & (d["ky"] == ky_xem)]
    p = float(mh.xac_suat(kq, ten_mh, dong_xem)[0])
    dg_ma, chan = mh.dong_gop(kq, ten_mh, dong_xem)
    gd.tieu_the("Yếu tố kéo tín hiệu", f"{ma} · khả năng tăng {p:.0%} · liên hệ thống kê, không phải nhân quả")
    bd.ve(bd.dong_gop(dg_ma, cao=260), key="db_dg")

with gd.the("lich-su"):
    gd.tieu_the(f"Tín hiệu qua các quý · {ma}",
                f"Chấm xanh: đúng chiều · ✕ đỏ: sai chiều · vùng xám: năm kiểm chứng {nam_test}; các năm trước mô hình đã "
                "học nên không phải dự báo thật")
    ls = d[d["ma_nh"] == ma].copy()
    ls["p"] = mh.xac_suat(kq, ten_mh, ls)
    bd.ve(bd.lich_su_tin_hieu(ls, ma, nam_test, mh.NHAN), key="db_ls")

gd.chan_trang()
