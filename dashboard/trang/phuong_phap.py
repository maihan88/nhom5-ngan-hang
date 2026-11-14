from pathlib import Path

import pandas as pd
import streamlit as st

from src import config as cf
from web import du_lieu as dl
from web import giao_dien as gd
from web.giao_dien import so

ds = dl.tat_ca()
GOC = Path(__file__).resolve().parents[1]
kq = dl.du_bao()
nam_test = kq["nam_test"]
b4 = ds["tong_hop"]

gd.dau_trang("Phương pháp", "Dữ liệu, phương pháp và giới hạn",
             f"{gd.TEN} – sản phẩm của Nhóm 5, môn Phân tích dữ liệu cho môi trường doanh nghiệp")
gd.nhan_dinh("Năm câu hỏi về sinh lời, an toàn và giá cổ phiếu của 8 ngân hàng niêm yết.", "Tóm tắt",
             phu=f"Báo cáo tài chính, giá cổ phiếu và tin doanh nghiệp giai đoạn {dl.giai_doan()}, tự cập nhật khi có quý mới.")

sk = ds["su_kien_chi_tiet"]
gd.the_so([
    {"nhan": "Ngân hàng niêm yết", "so": "8", "ghi": "3 quốc doanh · 5 tư nhân"},
    {"nhan": "Quý dữ liệu", "so": str(b4["ky"].nunique()), "ghi": dl.giai_doan()},
    {"nhan": "Phiên giá cổ phiếu", "so": so(len(ds["gia_ngay"]), 0, ""), "ghi": "giá ngày đã điều chỉnh"},
    {"nhan": "Tin doanh nghiệp", "so": so(len(sk), 0, ""), "ghi": "6 loại, có rà soát tay"},
], rong=200)

# ---- Năm câu hỏi -----------------------------------------------------------------------------------------
CAU = [
    ("1", "Ngân hàng nào sinh lời (ROA, ROE) cao nhất, vị trí dẫn đầu có ổn định không?",
     "Xếp hạng ROA, ROE cả năm", "Bản tin · So sánh", "so_sanh", "Gia Nghi"),
    ("2", "Quốc doanh và tư nhân có khác biệt về NIM, nợ xấu, CAR không?",
     "So sánh bình quân hai nhóm, kiểm định thống kê", "So sánh", "so_sanh", "Gia Nghi"),
    ("3", "Chỉ số tài chính nào liên hệ rõ nhất với biến động giá cổ phiếu trong quý?",
     "Đo mức độ đi cùng nhau (tương quan)", "Dự báo", "du_bao", "Gia Nghi"),
    ("4", "Dự đoán được giá quý sau tăng hay không? Thêm sự kiện doanh nghiệp có giúp không?",
     "Mô hình xác suất tăng giá (hồi quy logistic), có và không có dữ liệu sự kiện", "Dự báo", "du_bao", "Mạnh Quân"),
    ("5", "Gom theo đặc điểm tài chính có hình thành nhóm rõ ràng không?", "Gom nhóm theo mức tương đồng (K-Means)",
     "Phân nhóm", "phan_nhom", "Mạnh Quân"),
]
with gd.the("cau-hoi"):
    gd.tieu_the("Câu hỏi nghiên cứu")
    st.html("<div class='cuon'><table class='bang' style='min-width:760px'><thead><tr><th>#</th><th class='trai'>Câu hỏi</th>"
            "<th class='trai'>Phương pháp</th><th class='trai'>Xem ở</th><th class='trai'>Phụ trách</th></tr></thead><tbody>"
            + "".join(f"<tr><td><span class='num' style='display:inline-flex;width:26px;height:26px;border-radius:7px;"
                      f"background:var(--nhan-nhat);color:var(--nhan-chu);align-items:center;justify-content:center;"
                      f"font-weight:700'>{a}</span></td><td class='trai chu' style='font-weight:500'>{b}</td>"
                      f"<td class='trai chu' style='color:var(--muc2)'>{c}</td><td class='trai chu'><a href='{lk}' "
                      f"target='_self' style='color:var(--nhan-chu);font-weight:600'>{d}</a></td>"
                      f"<td class='trai chu'>{ng}</td></tr>" for a, b, c, d, lk, ng in CAU)
            + "</tbody></table></div>")

# ---- Quy trình -------------------------------------------------------------------------------------------------
nam_car = sorted(b4.loc[b4["car_nguon"].isin(cf.CAR_NGUON_SO_THAT), "nam"].unique())
nam_cuoi = int(b4["nam"].max())
BUOC = [
    ("01", "Thu thập", "Mai Hân", "Báo cáo tài chính quý, nợ xấu, giá cổ phiếu và sự kiện quyền từ VNDirect; CAR từ báo cáo tỷ lệ an toàn vốn của ngân hàng (PDF); "
     "tin công bố thông tin từ CafeF. Lưu bản gốc để đối chiếu."),
    ("02", "Làm sạch", "Mai Hân", "Thống nhất đơn vị; tính ROA, ROE, NIM, LDR; quý chưa có CAR công bố dùng số cuối năm gần nhất; "
     "xếp tin vào 6 loại sự kiện, có rà soát tay."),
    ("03", "Định nghĩa “tăng”", "Mai Hân", "Giá 45 ngày sau khi kết thúc quý sau (lúc báo cáo tài chính đã công bố) "
     "cao hơn cùng mốc của quý này."),
    ("04", "Thống kê", "Gia Nghi", "Xếp hạng ROA, ROE cả năm; so sánh quốc doanh – tư nhân; đo mức độ đi cùng nhau giữa chỉ số "
     "tài chính và giá cổ phiếu."),
    ("05", "Mô hình", "Mạnh Quân", f"Mô hình xác suất tăng giá học từ {b4['nam'].min()}–{nam_test - 1}, thử trên {nam_test}; "
     "gom ngân hàng thành nhóm theo đặc điểm tài chính."),
    ("06", "Bản tin", "Mai Hân", "Khi có quý mới, số liệu, câu nhận định và mô hình đều được tính lại tự động."),
]
with gd.the("quy-trinh"):
    gd.tieu_the("Quy trình")
    st.html("<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:6px'>"
            + "".join(f"<div style='border:1px solid var(--ke);border-radius:10px;padding:14px;background:var(--mat2);"
                      f"display:flex;flex-direction:column;gap:6px'><div style='display:flex;justify-content:space-between'>"
                      f"<b class='num' style='font-size:.78rem;color:var(--nhan-chu)'>{n}</b><span class='nguon'>{ng}</span></div>"
                      f"<b>{t}</b><span style='font-size:.84rem;color:var(--muc2);line-height:1.5'>{mt}</span></div>"
                      for n, t, ng, mt in BUOC) + "</div>")
    so_do = GOC / "assets" / "so_do_kien_truc_web.png"   # vẽ bằng ve_so_do.py
    if so_do.exists():
        with st.expander("Sơ đồ quy trình"):
            st.image(str(so_do), width="stretch", output_format="PNG")

# ---- Dữ liệu · mô hình · nhóm ----------------------------------------------------------------------------------
BANG = [("tong_hop", "Bảng tổng hợp", "Mỗi dòng là một ngân hàng trong một quý: chỉ số, giá, sự kiện"),
        ("tai_chinh_quy", "Tài chính quý", "Số liệu báo cáo tài chính (tỷ đồng) và chỉ số (%)"),
        ("gia_ngay", "Giá theo ngày", "Giá đóng cửa, giá điều chỉnh, khối lượng"),
        ("gia_quy", "Giá theo quý", "Lợi suất quý, biên độ giá, giá quý sau tăng hay không"),
        ("su_kien_chi_tiet", "Tin doanh nghiệp", "Mỗi dòng một tin: ngày, loại, tiêu đề, đường dẫn nguồn"),
        ("su_kien_quy", "Sự kiện theo quý", "Có sự kiện hay không, số tin theo từng loại")]
c1, c2 = st.columns([1.7, 1], gap="medium")
with c1, gd.the("du-lieu"):
    gd.tieu_the("Dữ liệu", "Tải về để tự kiểm tra · ô trống: nguồn không có số liệu, nhóm không tự điền")
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
        with st.expander("Giải thích từng cột: ý nghĩa, đơn vị, công thức"):
            a, b = st.columns(2)
            f = a.selectbox("Bảng", ds["tu_dien"]["file"].unique(), key="pp_file")
            tim = b.text_input("Tìm cột", placeholder="vd: npl, lợi suất, sự kiện…", key="pp_tim")
            t = ds["tu_dien"][ds["tu_dien"]["file"] == f]
            if tim:
                t = t[t["cot"].str.contains(tim, case=False, na=False) | t["mo_ta"].str.contains(tim, case=False, na=False)]
            st.dataframe(t[["cot", "mo_ta", "don_vi", "nguon_cong_thuc", "luu_y"]], hide_index=True, width="stretch",
                         height=420, column_config={"cot": "Cột", "mo_ta": "Ý nghĩa", "don_vi": "Đơn vị",
                                                    "nguon_cong_thuc": "Nguồn / công thức", "luu_y": "Lưu ý"})

with c2:
    with gd.the("nhom"):
        gd.tieu_the("Nhóm thực hiện")
        st.html("".join(
            f"<div style='display:flex;align-items:center;gap:12px;padding:8px 0;border-top:1px solid var(--ke)'>"
            f"<span style='width:36px;height:36px;border-radius:50%;background:var(--nhan-nhat);color:var(--nhan-chu);"
            f"display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.8rem;flex:none'>{v}</span>"
            f"<div><b style='font-size:.92rem'>{t}</b><div class='nguon'>{r}</div></div></div>"
            for v, t, r in [("MH", "Nguyễn Ngọc Mai Hân", "Thu thập, làm sạch dữ liệu · xây dựng bản tin"),
                            ("GN", "Hoàng Ngọc Gia Nghi", "Thống kê, kiểm định, trực quan hóa"),
                            ("MQ", "Hoàng Mạnh Quân", "Logistic Regression, K-Means, PCA")]))

# ---- Giới hạn -----------------------------------------------------------------------------------------------------
GIOI_HAN = [
    ("CAR chỉ có số cuối năm", f"Số công bố {nam_car[0]}–{nam_car[-1]}; các quý khác dùng số cuối năm gần nhất."
     + (f" Năm {nam_car[-1] + 1}–{nam_cuoi} chưa có số công bố." if nam_car[-1] < nam_cuoi else "")),
    ("ROA, ROE, NIM theo quý được năm hóa", "Nhân 4 nên dao động hơn số cả năm; phần xếp hạng dùng số cả năm."),
    ("Tin được phân loại tự động", "Tin hợp tác, chuyển đổi số 2021–2024 có thể bị thiếu; tin từ 2026 chưa được rà soát tay."),
    ("Mô hình học trên ít dữ liệu", f"Học từ {kq['n_train']} quý-ngân hàng, thử trên {kq['n_test']} – kết quả chỉ để "
     "tham khảo, không phải khuyến nghị đầu tư."),
    ("Số liệu có thể được điều chỉnh hồi tố", "Báo cáo có thể là bản sau kiểm toán; giá điều chỉnh thay đổi khi có cổ tức mới."),
]
with gd.the("gioi-han"):
    gd.tieu_the("Giới hạn khi đọc số liệu")
    st.html("<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px;margin-top:6px'>"
            + "".join(f"<div style='display:flex;gap:12px;padding:12px 14px;border-radius:10px;background:var(--mat2)'>"
                      f"<span class='i-tron'>i</span><div><b style='font-size:.9rem'>{t}</b>"
                      f"<div style='font-size:.84rem;color:var(--muc2);margin-top:2px'>{mt}</div></div></div>"
                      for t, mt in GIOI_HAN) + "</div>")

gd.chan_trang()
