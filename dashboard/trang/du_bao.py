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

ten_mh = st.session_state.get("db_mh") or mh.MAC_DINH
acc, auc = dg.loc[ten_mh, "Accuracy"], dg.loc[ten_mh, "ROC-AUC"]

# ---- Tín hiệu quý tới ---------------------------------------------------------------------------------------
moi = d[d["ky"] == ky].copy()
moi["xac_suat"] = mh.xac_suat(kq, ten_mh, moi)
n_tang = int((moi["xac_suat"] >= 0.5).sum())
gd.muc(f"Tín hiệu quý tới · dựa trên số liệu quý {ky[-1]}/{ky[:4]}",
       f"Mô hình nghiêng về tăng giá cho {n_tang}/{len(moi)} ngân hàng trong quý tới",
       f"Nhưng hãy thận trọng: kiểm chứng trên năm {nam_test}, mô hình chỉ đúng {so(acc * 100, 1)} số lần – "
       f"nhỉnh hơn một chút so với đoán bừa (50%).", dau=True)
st.segmented_control("Phiên bản mô hình", list(mh.MO_HINH), default=mh.MAC_DINH, format_func=mh.TEN_VIET.get,
                     key="db_mh")
bd.ve(bd.xac_suat(moi), key="db_xs")
gd.nguon(f"Logistic Regression ({mh.TEN_VIET[ten_mh].lower()}), học trên dữ liệu {ds_ky[0][:4]}–{nam_test - 1}. "
         "“Tăng” = giá tại mốc 45 ngày sau khi kết thúc quý tới cao hơn mốc tương ứng của quý này. "
         f"Thiết kế mô hình: Hoàng Mạnh Quân · {kq['nguon']}.")

# ---- Vì sao khó dự báo --------------------------------------------------------------------------------------------
tq = ds["tuong_quan"]
if tq is not None:
    chinh = tq[tq["mau_du_lieu"] == "chinh"]
    manh = chinh.loc[chinh["spearman_rho"].abs().idxmax()]
    co_y_nghia = int((chinh["spearman_p_hieu_chinh"] < 0.05).sum())
    gd.muc("Vì sao khó dự báo",
           "Chỉ số tài chính trong quý gần như không đi cùng giá cổ phiếu" if co_y_nghia == 0
           else f"{co_y_nghia} chỉ số có liên hệ rõ với giá cổ phiếu trong quý",
           f"Hệ số tương quan giữa từng chỉ số và biến động giá trong cùng quý ({int(manh['so_quan_sat'])} ngân hàng–quý). "
           f"Mạnh nhất là {cf.TEN_NGAN[manh['chi_so']]} với {so(manh['spearman_rho'], 2, '', dau=True)} – rất yếu.")
    bd.ve(bd.tuong_quan(chinh), key="db_tq")
    gd.nguon("Tương quan hạng Spearman; " + ("không chỉ số nào có ý nghĩa thống kê sau hiệu chỉnh Holm. "
             if co_y_nghia == 0 else "") + "Phân tích: Hoàng Ngọc Gia Nghi.")

# ---- Kiểm chứng ----------------------------------------------------------------------------------------------------
t = kq["du_doan_test"]
t = t[t["mo_hinh"] == ten_mh].copy()
t["dung"] = (t["xac_suat"] >= 0.5) == (t[mh.NHAN] == 1)
gd.muc(f"Kiểm chứng năm {nam_test}",
       f"Mô hình đoán đúng chiều {int(t['dung'].sum())}/{len(t)} lần, so với {int(round(dg.loc['Baseline', 'Accuracy'] * len(t)))} "
       "lần nếu lúc nào cũng đoán “tăng”",
       f"Mô hình học trên dữ liệu {ds_ky[0][:4]}–{nam_test - 1} rồi được thử trên năm {nam_test} – năm nó chưa từng thấy. "
       "Mỗi ô: khả năng tăng mô hình đưa ra và kết quả thực tế quý sau.")
quy = sorted(t["quy"].unique())
dong = []
for m in cf.DS_NGAN_HANG:
    o = []
    for q_ in quy:
        r = t[(t["ma_nh"] == m) & (t["quy"] == q_)]
        if r.empty:
            o.append("<td>–</td>")
            continue
        r = r.iloc[0]
        dung = bool(r["dung"])
        o.append(f"<td style='background:{'#E4EFE6' if dung else '#F5E2DE'}'>"
                 f"<span class='{'len' if dung else 'xuong'}'>{'✓' if dung else '✗'}</span> {r['xac_suat']:.0%}"
                 f"<span style='color:var(--nhat);font-size:.78rem'> · thực tế {so(r['ty_suat_sinh_loi_quy_sau'], 1, dau=True)}</span></td>")
    dong.append(f"<tr><td class='trai'>{gd.chip(m, ten=True)}</td>{''.join(o)}</tr>")
st.html("<div class='cuon'><table class='bang'><thead><tr><th>Ngân hàng</th>"
        + "".join(f"<th>{q_}/{nam_test}</th>" for q_ in quy) + "</tr></thead><tbody>" + "".join(dong) + "</tbody></table></div>")
gd.nguon(f"✓ đúng chiều · ✗ sai chiều. Tỷ lệ đúng {so(acc * 100, 1)}, AUC {so(auc, 2, '')} "
         f"(0,5 = ngẫu nhiên, 1 = hoàn hảo). Với {n_test} trường hợp, mỗi lần đúng/sai làm tỷ lệ đổi {so(100 / n_test, 1, ' điểm')}.")

# ---- Sự kiện doanh nghiệp có giúp không ----------------------------------------------------------------------------
tc, sk = dg.loc["Financial Only"], dg.loc["Financial + General Event"]
gd.muc("Thêm dữ liệu sự kiện có giúp không",
       "Thêm thông tin sự kiện doanh nghiệp cải thiện nhẹ, nhưng chưa đủ chắc chắn" if sk["ROC-AUC"] > tc["ROC-AUC"]
       else "Thêm thông tin sự kiện doanh nghiệp chưa cải thiện dự báo",
       f"Khi biết quý đó ngân hàng có sự kiện (tăng vốn, đổi lãnh đạo, hợp tác…), tỷ lệ đúng tăng từ {so(tc['Accuracy'] * 100, 1)} "
       f"lên {so(sk['Accuracy'] * 100, 1)}, AUC từ {so(tc['ROC-AUC'], 2, '')} lên {so(sk['ROC-AUC'], 2, '')}. Chênh lệch chỉ vài "
       f"trường hợp trên {n_test}, nên chưa thể khẳng định.")
bd.ve(bd.so_sanh_mo_hinh(kq["danh_gia"]), key="db_ss")

# ---- Giải thích từng ngân hàng ------------------------------------------------------------------------------------
gd.muc("Giải thích theo ngân hàng", "Yếu tố nào kéo tín hiệu lên hoặc xuống?",
       "Chỉ số tài chính được so với mức trung bình lịch sử: càng khác thường, tác động càng lớn. Đây là liên hệ thống kê, "
       "không phải quan hệ nhân quả.")
a, b = st.columns([4, 1], vertical_alignment="bottom")
ma = a.pills("Ngân hàng", cf.DS_NGAN_HANG, default=st.session_state.get("ma", "VCB"), key="db_ma",
             label_visibility="collapsed") or st.session_state.get("ma", "VCB")
st.session_state["ma"] = ma
ky_xem = b.selectbox("Kỳ", ds_ky[::-1], format_func=lambda k: f"Số liệu quý {k[-1]}/{k[:4]}", key="db_ky",
                     label_visibility="collapsed")
dong_xem = d[(d["ma_nh"] == ma) & (d["ky"] == ky_xem)]
p = float(mh.xac_suat(kq, ten_mh, dong_xem)[0])
dg_ma, chan = mh.dong_gop(kq, ten_mh, dong_xem)
c1, c2 = st.columns([1.15, 1], gap="large")
with c1:
    st.html(f"<div style='font-weight:600;margin-bottom:-4px'>{gd.chip(ma, ten=True)} · khả năng tăng "
            f"<b style='font-size:1.15rem'>{p:.0%}</b></div>")
    bd.ve(bd.dong_gop(dg_ma), key="db_dg")
with c2:
    st.html("<div style='font-weight:600;margin-bottom:-4px'>Tín hiệu qua các quý</div>")
    ls = d[d["ma_nh"] == ma].copy()
    ls["p"] = mh.xac_suat(kq, ten_mh, ls)
    bd.ve(bd.lich_su_tin_hieu(ls, ma, nam_test, mh.NHAN), key="db_ls")
    gd.nguon(f"Chấm xanh: đúng chiều · ✕ đỏ: sai chiều. Vùng xám: năm kiểm chứng {nam_test}; các năm trước mô hình đã học "
             "nên không phải dự báo thật.")

gd.chan_trang()
