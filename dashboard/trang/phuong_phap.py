import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src import config as cf
from web import du_lieu as dl
from web import giao_dien as gd
from web.giao_dien import e, so

ds = dl.tat_ca()
GOC = Path(__file__).resolve().parents[1]
kq = dl.du_bao()
nam_test = kq["nam_test"]
b4 = ds["tong_hop"]

gd.dau_trang("Phương pháp", "Dữ liệu, phương pháp và giới hạn",
             f"{gd.TEN} – sản phẩm của Nhóm 5, môn Phân tích dữ liệu cho môi trường doanh nghiệp")
gd.nhan_dinh("Năm câu hỏi, ba nhóm phương pháp, một lệnh chạy lại toàn bộ khi có quý mới.", "Tóm tắt",
             phu=f"Thu thập tự động báo cáo tài chính, giá cổ phiếu và tin doanh nghiệp của 8 ngân hàng niêm yết giai đoạn "
                 f"{dl.giai_doan()}, phân tích và dự báo bằng Python.")

sk = ds["su_kien_chi_tiet"]
gd.the_so([
    {"nhan": "Ngân hàng niêm yết", "so": "8", "ghi": "3 quốc doanh · 5 tư nhân"},
    {"nhan": "Quý dữ liệu", "so": str(b4["ky"].nunique()), "ghi": dl.giai_doan()},
    {"nhan": "Ngân hàng–quý", "so": so(len(b4), 0, ""), "ghi": "1 dòng bảng tổng hợp"},
    {"nhan": "Phiên giá cổ phiếu", "so": so(len(ds["gia_ngay"]), 0, ""), "ghi": "giá ngày đã điều chỉnh"},
    {"nhan": "Sự kiện doanh nghiệp", "so": so(len(sk), 0, ""), "ghi": "6 loại, có rà soát tay"},
], rong=170)

# ---- Năm câu hỏi -----------------------------------------------------------------------------------------
CAU = [
    ("1", "Ngân hàng nào sinh lời (ROA, ROE) cao nhất, vị trí dẫn đầu có ổn định không?",
     "Thống kê mô tả, xếp hạng theo năm", "Bản tin · So sánh", "so_sanh", "Gia Nghi"),
    ("2", "Quốc doanh và tư nhân có khác biệt về NIM, nợ xấu, CAR không?",
     "Kiểm định t / Welch / Mann–Whitney", "So sánh", "so_sanh", "Gia Nghi"),
    ("3", "Chỉ số tài chính nào liên hệ rõ nhất với biến động giá cổ phiếu trong quý?",
     "Tương quan Pearson, Spearman, hiệu chỉnh Holm", "Dự báo", "du_bao", "Gia Nghi"),
    ("4", "Dự đoán được giá quý sau tăng hay không? Thêm sự kiện doanh nghiệp có giúp không?",
     "Logistic Regression có / không biến sự kiện", "Dự báo", "du_bao", "Mạnh Quân"),
    ("5", "Gom theo đặc điểm tài chính có hình thành nhóm rõ ràng không?", "K-Means, PCA", "Phân nhóm", "phan_nhom", "Mạnh Quân"),
]
with gd.the("cau-hoi"):
    gd.tieu_the("Câu hỏi nghiên cứu", "Mỗi câu hỏi được trả lời ở một trang của web")
    st.html("<div class='cuon'><table class='bang' style='min-width:760px'><thead><tr><th>#</th><th class='trai'>Câu hỏi</th>"
            "<th class='trai'>Phương pháp</th><th class='trai'>Xem ở</th><th class='trai'>Phụ trách</th></tr></thead><tbody>"
            + "".join(f"<tr><td><span class='num' style='display:inline-flex;width:26px;height:26px;border-radius:7px;"
                      f"background:var(--nhan-nhat);color:var(--nhan-chu);align-items:center;justify-content:center;"
                      f"font-weight:700'>{a}</span></td><td class='trai chu' style='font-weight:500'>{b}</td>"
                      f"<td class='trai chu' style='color:var(--muc2)'>{c}</td><td class='trai chu'><a href='{lk}' "
                      f"target='_self' style='color:var(--nhan-chu);font-weight:600'>{d}</a></td>"
                      f"<td class='trai chu'>{ng}</td></tr>" for a, b, c, d, lk, ng in CAU)
            + "</tbody></table></div>")
    gd.nguon("Thu thập, làm sạch dữ liệu và xây dựng web: Nguyễn Ngọc Mai Hân.")

# ---- Quy trình -------------------------------------------------------------------------------------------------
nam_car = sorted(b4.loc[b4["car_nguon"].isin(["cong_bo", "tra_thu_cong"]), "nam"].unique())
nam_cuoi = int(b4["nam"].max())
BUOC = [
    ("01", "Thu thập", "Mai Hân", "API công khai VNDirect (báo cáo tài chính quý, NPL, CAR, giá ngày đã điều chỉnh, sự kiện quyền) "
     "và tin công bố thông tin trên CafeF; lưu phản hồi gốc để truy vết."),
    ("02", "Làm sạch", "Mai Hân", "Chuẩn hóa đơn vị; tính ROA, ROE, NIM, LDR; CAR giữa các kỳ công bố lấy số gần nhất trước đó; "
     "phân loại tin thành 6 nhóm sự kiện bằng từ khóa, có rà soát."),
    ("03", "Gán nhãn", "Mai Hân", "Giá “tăng” nếu giá tại mốc cuối quý sau + 45 ngày cao hơn mốc cuối quý này + 45 ngày "
     "(lúc báo cáo tài chính đã công bố)."),
    ("04", "Thống kê", "Gia Nghi", "Thống kê mô tả, xếp hạng ROA/ROE năm, kiểm định quốc doanh – tư nhân, tương quan có "
     "hiệu chỉnh Holm."),
    ("05", "Mô hình", "Mạnh Quân", f"Logistic Regression học trên {b4['nam'].min()}–{nam_test - 1}, kiểm chứng trên {nam_test}; "
     "so sánh có và không có biến sự kiện. K-Means và PCA để phân nhóm. Lưu 3 mô hình .pkl."),
    ("06", "Web", "Mai Hân", "Streamlit và Plotly. Nạp mô hình từ .pkl; dữ liệu mới hơn file thì tự huấn luyện lại theo đúng "
     "thiết kế, nên con số luôn khớp dữ liệu."),
]
with gd.the("quy-trinh"):
    gd.tieu_the("Quy trình", "Web đọc thẳng dữ liệu và kết quả nên tự cập nhật, kể cả mô hình")
    st.html("<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:6px'>"
            + "".join(f"<div style='border:1px solid var(--ke);border-radius:10px;padding:14px;background:var(--mat2);"
                      f"display:flex;flex-direction:column;gap:6px'><div style='display:flex;justify-content:space-between'>"
                      f"<b class='num' style='font-size:.78rem;color:var(--nhan-chu)'>{n}</b><span class='nguon'>{ng}</span></div>"
                      f"<b>{t}</b><span style='font-size:.84rem;color:var(--muc2);line-height:1.5'>{mt}</span></div>"
                      for n, t, ng, mt in BUOC) + "</div>"
            "<div style='display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:12px;padding:10px 14px;"
            "border:1px dashed var(--ke2);border-radius:10px;font-size:.84rem;color:var(--nhat)'>Chạy lại toàn bộ: "
            "<code>py chay_tat_ca.py --mo-web</code> · tái lập dữ liệu báo cáo: "
            "<code>--den-quy 2026Q2 --gia-den 2026-10-28 --offline</code></div>")
    so_do = GOC / "assets" / "so_do_kien_truc_web.png"   # vẽ bằng ve_so_do.py
    if so_do.exists():
        with st.expander("Sơ đồ kiến trúc"):
            st.image(str(so_do), width="stretch", output_format="PNG")

# ---- Dữ liệu · mô hình · nhóm ----------------------------------------------------------------------------------
BANG = [("tong_hop", "Bảng tổng hợp", "1 dòng = 1 ngân hàng × 1 quý; chỉ số, giá, sự kiện, nhãn dự báo"),
        ("tai_chinh_quy", "Tài chính quý", "Số liệu báo cáo tài chính (tỷ đồng) và chỉ số (%)"),
        ("gia_ngay", "Giá theo ngày", "Giá đóng cửa, giá điều chỉnh, khối lượng"),
        ("gia_quy", "Giá theo quý", "Lợi suất quý, biên độ, nhãn xu hướng quý sau"),
        ("su_kien_chi_tiet", "Sự kiện chi tiết", "Mỗi dòng 1 tin: ngày, loại, tiêu đề, link nguồn"),
        ("su_kien_quy", "Sự kiện theo quý", "Cờ có sự kiện, số sự kiện theo loại")]
c1, c2 = st.columns([1.7, 1], gap="medium")
with c1, gd.the("du-lieu"):
    gd.tieu_the("Dữ liệu", "Tải về để tự kiểm tra · ô trống nghĩa là nguồn không có dữ liệu – nhóm không tự điền 0")
    for ten, nhan, mo_ta in BANG:
        # Đưa nguyên file CSV bàn giao (không phải bảng đã lọc giai đoạn / thêm cột phụ để vẽ) để khớp báo cáo
        tep = cf.THU_MUC_DATA / cf.TEN_FILE[ten]
        so_dong, so_cot = pd.read_csv(tep).shape
        a, b = st.columns([4, 1], vertical_alignment="center")
        a.html(f"<div style='padding-top:10px;border-top:1px solid var(--ke)'><b>{nhan}</b>"
               f"<div class='nguon' style='font-size:.84rem'>{mo_ta} · <span class='num'>{so(so_dong, 0, '')} dòng · "
               f"{so_cot} cột</span></div></div>")
        b.download_button("CSV", tep.read_bytes(), file_name=cf.TEN_FILE[ten], icon=":material/download:",
                          mime="text/csv", key=f"tai_{ten}", width="stretch")
    if ds["tu_dien"] is not None:
        with st.expander("Từ điển dữ liệu – ý nghĩa, đơn vị, công thức của từng cột"):
            a, b = st.columns(2)
            f = a.selectbox("File", ds["tu_dien"]["file"].unique(), key="pp_file")
            tim = b.text_input("Tìm cột", placeholder="vd: npl, lợi suất, sự kiện…", key="pp_tim")
            t = ds["tu_dien"][ds["tu_dien"]["file"] == f]
            if tim:
                t = t[t["cot"].str.contains(tim, case=False, na=False) | t["mo_ta"].str.contains(tim, case=False, na=False)]
            st.dataframe(t[["cot", "mo_ta", "don_vi", "nguon_cong_thuc", "luu_y"]], hide_index=True, width="stretch",
                         height=420, column_config={"cot": "Cột", "mo_ta": "Ý nghĩa", "don_vi": "Đơn vị",
                                                    "nguon_cong_thuc": "Nguồn / công thức", "luu_y": "Lưu ý"})

with c2:
    tt_mh = GOC / "mo_hinh" / "thong_tin.json"
    if tt_mh.exists():
        tt = json.loads(tt_mh.read_text(encoding="utf-8"))
        with gd.the("mo-hinh"):
            gd.tieu_the("Mô hình đã lưu", f"Xuất ngày {tt['ngay_xuat']} · scikit-learn {tt['scikit_learn']}")
            st.html("".join(
                f"<div style='padding:8px 0;border-top:1px solid var(--ke)'><code style='font-size:.78rem'>{e(m['file'])}</code>"
                f"<div style='font-size:.86rem;margin-top:2px'>{e(m['ten'])} · {len(m['bien'])} biến</div>"
                f"<div class='nguon num'>Tỷ lệ đúng {so(m['accuracy_test'] * 100, 1)} · AUC {so(m['auc_test'], 2, '')}</div></div>"
                for m in tt["mo_hinh"].values()))
            with st.expander("Danh sách và thứ tự biến đầu vào"):
                st.dataframe([{"File": m["file"], "Biến đầu vào (đúng thứ tự)": ", ".join(m["bien"])} for m in tt["mo_hinh"].values()],
                             hide_index=True, width="stretch")
                st.caption(f"Web hiện dùng: {kq['nguon']}.")
    with gd.the("nhom"):
        gd.tieu_the("Nhóm thực hiện")
        st.html("".join(
            f"<div style='display:flex;align-items:center;gap:12px;padding:8px 0;border-top:1px solid var(--ke)'>"
            f"<span style='width:36px;height:36px;border-radius:50%;background:var(--nhan-nhat);color:var(--nhan-chu);"
            f"display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.8rem;flex:none'>{v}</span>"
            f"<div><b style='font-size:.92rem'>{t}</b><div class='nguon'>{r}</div></div></div>"
            for v, t, r in [("MH", "Nguyễn Ngọc Mai Hân", "Thu thập, làm sạch dữ liệu · xây dựng web"),
                            ("GN", "Hoàng Ngọc Gia Nghi", "Thống kê, kiểm định, trực quan hóa"),
                            ("MQ", "Hoàng Mạnh Quân", "Logistic Regression, K-Means, PCA")]))

# ---- Giới hạn -----------------------------------------------------------------------------------------------------
GIOI_HAN = [
    ("CAR chỉ có số cuối năm", f"Số công bố {nam_car[0]}–{nam_car[-1]}; các quý khác là số gần nhất trước đó."
     + (f" Năm {nam_car[-1] + 1}–{nam_cuoi} chưa có số công bố." if nam_car[-1] < nam_cuoi else "")),
    ("ROA, ROE, NIM theo quý được năm hóa", "Nhân 4 nên dao động hơn số cả năm; phần xếp hạng dùng số cả năm."),
    ("Sự kiện phân loại theo từ khóa", "Tin hợp tác, chuyển đổi số 2021–2024 có thể bị thiếu; sự kiện từ 2026 chưa rà soát tay."),
    ("Mô hình học trên ít dữ liệu", f"{kq['n_train']} trường hợp học, {kq['n_test']} trường hợp kiểm chứng – kết quả chỉ để "
     "tham khảo, không phải khuyến nghị đầu tư."),
    ("Số liệu có thể được điều chỉnh hồi tố", "VNDirect có thể dùng bản sau kiểm toán; giá điều chỉnh đổi khi có cổ tức mới."),
]
with gd.the("gioi-han"):
    gd.tieu_the("Giới hạn khi đọc số liệu")
    st.html("<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px;margin-top:6px'>"
            + "".join(f"<div style='display:flex;gap:12px;padding:12px 14px;border-radius:10px;background:var(--mat2)'>"
                      f"<span class='i-tron'>i</span><div><b style='font-size:.9rem'>{t}</b>"
                      f"<div style='font-size:.84rem;color:var(--muc2);margin-top:2px'>{mt}</div></div></div>"
                      for t, mt in GIOI_HAN) + "</div>")

gd.chan_trang()
