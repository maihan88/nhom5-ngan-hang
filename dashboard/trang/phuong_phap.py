import json
from pathlib import Path

import streamlit as st

from src import config as cf
from web import du_lieu as dl
from web import giao_dien as gd

ds = dl.tat_ca()
GOC = Path(__file__).resolve().parents[1]

gd.muc("Về bản tin này", "Dữ liệu, phương pháp và giới hạn đằng sau mỗi con số",
       f"{gd.TEN} là sản phẩm của Nhóm 5, môn Phân tích dữ liệu cho môi trường doanh nghiệp: thu thập tự động báo cáo tài chính, "
       f"giá cổ phiếu và tin doanh nghiệp của 8 ngân hàng niêm yết giai đoạn {dl.giai_doan()}, phân tích và dự báo bằng Python.", dau=True)

# ---- Năm câu hỏi -----------------------------------------------------------------------------------------
gd.muc("Câu hỏi nghiên cứu", "Năm câu hỏi và nơi trả lời trong bản tin")
CAU = [
    ("1", "Ngân hàng nào sinh lời (ROA, ROE) cao nhất, vị trí dẫn đầu có ổn định không?",
     "Thống kê mô tả, xếp hạng theo năm", "Bản tin · So sánh", "Gia Nghi"),
    ("2", "Quốc doanh và tư nhân có khác biệt về NIM, nợ xấu, CAR không?",
     "Kiểm định t / Welch / Mann–Whitney", "So sánh", "Gia Nghi"),
    ("3", "Chỉ số tài chính nào liên hệ rõ nhất với biến động giá cổ phiếu trong quý?",
     "Tương quan Pearson, Spearman, hiệu chỉnh Holm", "Dự báo", "Gia Nghi"),
    ("4", "Dự đoán được giá quý sau tăng hay không? Thêm sự kiện doanh nghiệp có giúp không?",
     "Logistic Regression có / không biến sự kiện", "Dự báo", "Mạnh Quân"),
    ("5", "Gom theo đặc điểm tài chính có hình thành nhóm rõ ràng không?", "K-Means, PCA", "Phân nhóm", "Mạnh Quân"),
]
st.html("<div class='cuon'><table class='bang'><thead><tr><th>#</th><th class='trai'>Câu hỏi</th><th class='trai'>Phương pháp</th>"
        "<th class='trai'>Xem ở mục</th><th class='trai'>Phụ trách</th></tr></thead><tbody>"
        + "".join(f"<tr><td style='color:var(--nhat)'>{a}</td><td class='trai'>{b}</td><td class='trai'>{c}</td>"
                  f"<td class='trai'><b>{d}</b></td><td class='trai'>{e}</td></tr>" for a, b, c, d, e in CAU)
        + "</tbody></table></div>")
gd.nguon("Thu thập, làm sạch dữ liệu và xây dựng bản tin: Nguyễn Ngọc Mai Hân.")

# ---- Quy trình -------------------------------------------------------------------------------------------------
gd.muc("Quy trình", "Từ dữ liệu thô đến bản tin",
       "Nhóm chạy lại pipeline khi có quý mới; bản tin đọc thẳng bộ dữ liệu sạch nên tự cập nhật, kể cả mô hình.")
so_do = GOC / "assets" / "SoDoKienTruc.png"
if so_do.exists():
    st.image(str(so_do), width="stretch")
c1, c2 = st.columns(2, gap="large")
c1.markdown("""
**1 · Thu thập** – API công khai VNDirect (báo cáo tài chính quý, NPL, CAR, giá ngày đã điều chỉnh, sự kiện quyền)
và tin công bố thông tin theo mã trên CafeF; phản hồi gốc được lưu lại để truy vết.

**2 · Làm sạch** – chuẩn hóa đơn vị, tính ROA, ROE, NIM, LDR; CAR giữa các kỳ công bố lấy số gần nhất trước đó;
phân loại tin thành 6 nhóm sự kiện bằng từ khóa, có rà soát.

**3 · Nhãn dự báo** – giá “tăng” nếu giá tại mốc cuối quý sau + 45 ngày cao hơn mốc cuối quý này + 45 ngày
(lúc báo cáo tài chính đã công bố).
""")
kq = dl.du_bao()
nam_test = kq["nam_test"]
b4 = ds["tong_hop"]
nam_car = sorted(b4.loc[b4["car_nguon"].isin(["cong_bo", "tra_thu_cong"]), "nam"].unique())
nam_cuoi = int(b4["nam"].max())
c2.markdown(f"""
**4 · Thống kê** – thống kê mô tả, xếp hạng ROA/ROE năm, kiểm định quốc doanh – tư nhân, tương quan có hiệu chỉnh Holm.

**5 · Mô hình** – Logistic Regression học trên {b4["nam"].min()}–{nam_test - 1}, kiểm chứng trên {nam_test}; so sánh có và không có biến sự kiện.
K-Means và PCA để phân nhóm. Ba mô hình dự báo được lưu thành file .pkl kèm danh sách, thứ tự biến đầu vào.

**6 · Bản tin** – Streamlit và Plotly. Bản tin nạp mô hình từ file .pkl; nếu dữ liệu mới hơn file thì tự huấn luyện lại
theo đúng thiết kế, nên con số luôn khớp dữ liệu.
""")
tt_mh = GOC / "mo_hinh" / "thong_tin.json"
if tt_mh.exists():
    tt = json.loads(tt_mh.read_text(encoding="utf-8"))
    with st.expander("Mô hình đã lưu (.pkl) – danh sách và thứ tự biến đầu vào"):
        st.caption(f"Xuất ngày {tt['ngay_xuat']} bằng scikit-learn {tt['scikit_learn']} · bản tin hiện dùng: "
                   f"{dl.du_bao()['nguon']}.")
        st.dataframe(
            [{"File": m["file"], "Phiên bản": m["ten"], "Biến đầu vào (đúng thứ tự)": ", ".join(m["bien"]),
              f"Tỷ lệ đúng {tt['nam_test']}": m["accuracy_test"], f"AUC {tt['nam_test']}": m["auc_test"]} for m in tt["mo_hinh"].values()],
            hide_index=True, width="stretch")

# ---- Dữ liệu ----------------------------------------------------------------------------------------------------
gd.muc("Dữ liệu", "Tải về để tự kiểm tra", "Ô trống nghĩa là nguồn không có dữ liệu – nhóm không tự điền 0.")
BANG = [("tong_hop", "Bảng tổng hợp", "1 dòng = 1 ngân hàng × 1 quý; chỉ số, giá, sự kiện, nhãn dự báo"),
        ("tai_chinh_quy", "Tài chính quý", "Số liệu báo cáo tài chính (tỷ đồng) và chỉ số (%)"),
        ("gia_ngay", "Giá theo ngày", "Giá đóng cửa, giá điều chỉnh, khối lượng"),
        ("gia_quy", "Giá theo quý", "Lợi suất quý, biên độ, nhãn xu hướng quý sau"),
        ("su_kien_chi_tiet", "Sự kiện chi tiết", "Mỗi dòng 1 tin: ngày, loại, tiêu đề, link nguồn"),
        ("su_kien_quy", "Sự kiện theo quý", "Cờ có sự kiện, số sự kiện theo loại")]
for ten, nhan, mo_ta in BANG:
    df = ds[ten].drop(columns=[c for c in ["ky_so", "ngay_ky"] if c in ds[ten]])
    a, b, c = st.columns([1.3, 3, 1], vertical_alignment="center")
    a.html(f"<b>{nhan}</b>")
    b.html(f"<span style='color:var(--muc2);font-size:.9rem'>{mo_ta} · {gd.so(len(df), 0, '')} dòng × {df.shape[1]} cột</span>")
    c.download_button("Tải CSV", df.to_csv(index=False).encode("utf-8-sig"), file_name=cf.TEN_FILE[ten],
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

# ---- Giới hạn -----------------------------------------------------------------------------------------------------
gd.muc("Giới hạn", "Những điều cần biết khi đọc các con số")
st.markdown(f"""
- **CAR** chỉ có số công bố cuối năm ({nam_car[0]}–{nam_car[-1]}); các quý khác là số gần nhất trước đó.{f" Năm {nam_car[-1] + 1}–{nam_cuoi} chưa có số công bố." if nam_car[-1] < nam_cuoi else ""}
- **ROA, ROE, NIM theo quý** được năm hóa (×4) nên dao động hơn số cả năm; phần xếp hạng dùng số cả năm.
- **Sự kiện doanh nghiệp** được phân loại theo từ khóa trên tiêu đề tin; tin hợp tác, chuyển đổi số 2021–2024 có thể bị thiếu.
- **Mô hình dự báo** học trên {kq["n_train"]} trường hợp và kiểm chứng trên {kq["n_test"]} – kết quả chỉ để tham khảo, không phải khuyến nghị đầu tư.
- Số liệu VNDirect có thể là bản sau kiểm toán; giá điều chỉnh có thể được điều chỉnh hồi tố khi có cổ tức mới.
""")

gd.chan_trang()
