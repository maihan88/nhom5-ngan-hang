# Quy ước định dạng – Trực quan hóa & Thống kê ↔ Dashboard

Người soạn: Gia Nghi · Người xác nhận: Mai Hân · Áp dụng cho: notebook phân tích, `viz.py`, app Streamlit.

Mọi giá trị dưới đây đã được viết thành code trong `src/config.py` và `src/ket_qua.py`. Khi cần đổi, sửa trong code (một chỗ duy nhất) rồi cập nhật lại văn bản này.

## 1. Dữ liệu đầu vào và cách đọc

Mọi phần đều đọc dữ liệu qua `src/data_loader.py`, không gọi `pd.read_csv` trực tiếp. Hàm đọc tự động lọc từ Q1/2021 đến kỳ cuối có trong dữ liệu (hiện Q2/2026; bảng giá ngày lọc 01/01/2021 → ngày cuối kỳ đó), thêm cột `ky` dạng `"2021Q1"` làm trục x, `ky_so` (1..số quý, hiện 22) để sắp xếp, `ngay_ky` (ngày cuối quý), và ép `ma_nh`, `quy`, `loai_hinh_so_huu` về kiểu có thứ tự cố định. Bảng 4 có thêm cờ `car_cong_bo` (True ở 32 dòng CAR công bố thật).

Thư mục dữ liệu mặc định là `data/`; trên Streamlit Cloud đặt biến môi trường `PTDL_DATA_DIR` nếu để ở chỗ khác.

## 2. Bảng màu cố định

Thứ tự hiển thị luôn là quốc doanh trước, tư nhân sau: **VCB, BID, CTG, TCB, MBB, ACB, STB, VPB**.

| Mã | Tên | Nhóm | Màu |
|---|---|---|---|
| VCB | Vietcombank | Quốc doanh | `#0B3C6E` xanh navy đậm |
| BID | BIDV | Quốc doanh | `#2F6DB5` xanh dương vừa |
| CTG | VietinBank | Quốc doanh | `#7CB3E6` xanh dương nhạt |
| TCB | Techcombank | Tư nhân | `#C8323C` đỏ |
| MBB | MB Bank | Tư nhân | `#E69F00` cam hổ phách |
| ACB | ACB | Tư nhân | `#009E73` xanh lục |
| STB | Sacombank | Tư nhân | `#7B4EA3` tím |
| VPB | VPBank | Tư nhân | `#8C6D31` nâu ô liu |

| Nhóm sở hữu | Màu |
|---|---|
| Quốc doanh | `#2F6DB5` xanh dương |
| Tư nhân | `#E07B39` cam |

Lý do: ba ngân hàng quốc doanh dùng ba sắc độ cùng tông xanh dương nên người xem nhận ra ngay là một nhóm; năm ngân hàng tư nhân dùng màu khác tông hẳn. Không dùng màu thương hiệu vì phần lớn các ngân hàng đều dùng xanh dương. Màu phụ: xám `#7F7F7F` cho đường trung bình ngành / tham chiếu, xanh lá `#2CA02C` và đỏ `#D62728` cho lợi suất dương/âm. Màu cho 6 loại sự kiện nằm trong `MAU_SU_KIEN`.

Trong code: `color_discrete_map=cf.MAU_NGAN_HANG` (hoặc `cf.MAU_NHOM`) và `category_orders={"ma_nh": cf.DS_NGAN_HANG, "ky": thu_tu_ky()}`.

## 3. Tên chỉ số, đơn vị, định dạng số

Tiêu đề trục lấy từ `cf.NHAN_CHI_SO`, ví dụ `roe` → "ROE (%)", `npl` → "Tỷ lệ nợ xấu – NPL (%)". Mọi tỷ lệ tính bằng %, làm tròn 2 chữ số khi hiển thị; giá tính bằng nghìn đồng; số tiền tính bằng tỷ đồng. Kỳ luôn viết `2021Q1`, năm viết `2021`. Tiêu đề biểu đồ viết tiếng Việt, câu ngắn, nêu chỉ số + phạm vi (ví dụ "ROE theo quý, 8 ngân hàng, 2021–2025").

## 4. Cách viết hàm vẽ (hợp đồng giữa `viz.py` và Streamlit)

Mỗi biểu đồ là một hàm trong `viz.py` tuân theo 6 quy tắc:

1. Tên bắt đầu bằng `ve_`, ví dụ `ve_duong_chi_so`, `ve_bump_xep_hang`.
2. Tham số đầu tiên là DataFrame đã đọc qua `data_loader`; các tham số lọc có tên thống nhất: `ma_nh` (str hoặc list), `nam` (int hoặc list), `chi_so` (str trong `cf.DS_CHI_SO`), `nhom`. Giá trị `None` nghĩa là "lấy tất cả". Mọi tham số lọc đều có giá trị mặc định để hàm chạy được khi gọi không tham số.
3. Lọc bằng hàm chung `loc(df, ma_nh, nam, nhom)`, không tự viết điều kiện lọc riêng.
4. Trả về `plotly.graph_objects.Figure`. Hàm **không** gọi `fig.show()`, **không** ghi file, **không** in ra màn hình.
5. Gọi `cf.ap_dung_giao_dien(fig, tieu_de, truc_x, truc_y)` ngay trước `return`.
6. Không sửa DataFrame đầu vào (dùng `.copy()` nếu cần thêm cột).

Mẫu:

```python
def ve_duong_chi_so(df, chi_so="roe", ma_nh=None, nam=None):
    d = loc(df, ma_nh=ma_nh, nam=nam).copy()
    d["ma_nh"] = d["ma_nh"].astype(str)
    fig = px.line(d, x="ky", y=chi_so, color="ma_nh", markers=True,
                  color_discrete_map=cf.MAU_NGAN_HANG,
                  category_orders={"ma_nh": cf.DS_NGAN_HANG, "ky": thu_tu_ky()})
    return cf.ap_dung_giao_dien(fig, f"{cf.NHAN_CHI_SO[chi_so]} theo quý",
                                "Quý", cf.NHAN_CHI_SO[chi_so])
```

Phía Streamlit chỉ cần:

```python
chi_so = st.selectbox("Chỉ số", cf.DS_CHI_SO, format_func=cf.NHAN_CHI_SO.get)
ma_nh  = st.multiselect("Ngân hàng", cf.DS_NGAN_HANG, default=cf.DS_NGAN_HANG)
st.plotly_chart(ve_duong_chi_so(b4, chi_so=chi_so, ma_nh=ma_nh), use_container_width=True)
```

Xuất PNG cho báo cáo làm riêng trong notebook bằng `cf.luu_hinh(fig, "ten_file")` (1000×560, scale 2). Tên file PNG đặt theo dạng `<phần>_<nội dung>`, ví dụ `p3_bump_roe.png`.

## 5. Cấu trúc 4 file bảng kết quả

Cả 4 file ở dạng dài, mã hóa `utf-8-sig`, ghi bằng `xuat_ket_qua(df, ten)` (hàm tự báo lỗi nếu thiếu cột). Cột không áp dụng để trống. Dashboard đọc: `pd.read_csv("outputs/<ten>.csv", encoding="utf-8-sig")`. Có thể lấy khung rỗng bằng `khung_rong(ten)` để dựng trang trước.

**`thong_ke_mo_ta.csv`** – thống kê mô tả (câu 1, 2 và mô tả chung)
`chi_so, cap_do, ma_nh, nam, loai_hinh_so_huu, mau_du_lieu, so_quan_sat, trung_binh, trung_vi, do_lech_chuan, nho_nhat, lon_nhat, don_vi`
`cap_do` ∈ {`toan_bo`, `ma_nh`, `nam`, `loai_hinh_so_huu`, `ma_nh_nam`}; `mau_du_lieu` ∈ {`quy`, `car_cong_bo`}.

**`xep_hang_nam.csv`** – xếp hạng sinh lời theo năm (câu 1)
`chi_so, nam, ma_nh, loai_hinh_so_huu, gia_tri, hang, hang_nam_truoc, thay_doi_hang`
`chi_so` ∈ {`roa_nam`, `roe_nam`}; `hang` = 1 là cao nhất; `thay_doi_hang` dương = tụt hạng.

**`kiem_dinh_nhom.csv`** – kiểm định quốc doanh vs tư nhân (câu 2)
`chi_so, mau_du_lieu, don_vi_quan_sat, phan_tich, n_quoc_doanh, n_tu_nhan, tb_quoc_doanh, tb_tu_nhan, trung_vi_quoc_doanh, trung_vi_tu_nhan, shapiro_p_quoc_doanh, shapiro_p_tu_nhan, levene_p, kiem_dinh, thong_ke, p_value, muc_y_nghia, bac_bo_H0, gia_thuyet_H0, gia_thuyet_H1, ket_luan, chenh_lech_tb, ten_hieu_ung, do_lon_hieu_ung`
`phan_tich` ∈ {`chinh`, `kiem_tra_lai`} – dashboard hiển thị dòng `chinh`, các dòng `kiem_tra_lai` để ở phần mở rộng. `mau_du_lieu` ∈ {`chinh`, `khong_VPB`, `car_2021_2024`, `cap_ngan_hang`}. `chenh_lech_tb` = TB quốc doanh − TB tư nhân; `do_lon_hieu_ung` dương = quốc doanh cao hơn. *(Cập nhật ở Phần 4: thêm `phan_tich` và 3 cột cuối.)*

**`tuong_quan.csv`** – tương quan chỉ số với lợi suất quý (câu 3)
`chi_so, bien_so_sanh, mau_du_lieu, phan_tich, so_quan_sat, pearson_r, pearson_p, pearson_p_hieu_chinh, spearman_rho, spearman_p, spearman_p_hieu_chinh, phuong_phap_hieu_chinh, xep_hang_do_manh`
`phan_tich` ∈ {`chinh`, `kiem_tra_lai`} – dashboard hiển thị dòng `chinh`. `mau_du_lieu` ∈ {`chinh`, `car_cong_bo`, `q4_2021_2024`, `loai_bien_dong_chung`, `thay_doi_chi_so`, `cap_ngan_hang`}. `xep_hang_do_manh` xếp theo |spearman_rho| trong cùng một mẫu. *(Cập nhật ở Phần 5: thêm cột `phan_tich`.)*

## 6. Lưu ý dữ liệu đã thống nhất (từ bước kiểm tra)

Kết quả kiểm tra dữ liệu bản cập nhật: 30 mục đạt, 0 lỗi, 7 lưu ý. Các lưu ý ảnh hưởng đến phân tích:

- **CAR:** 1 số thật mỗi ngân hàng mỗi năm (Q4, 31/12), hiện 40 giá trị 2021–2025. Số lấy từ báo cáo tỷ lệ an toàn vốn của chính ngân hàng (`car_nguon = bao_cao_ngan_hang`); năm chưa có báo cáo thì dùng VNDirect (`vndirect`). Code coi cả hai là số thật qua `cf.CAR_NGUON_SO_THAT`; cờ `car_cong_bo` trong bảng 4 đã tính cả hai. Từ 2025 có ngân hàng tính CAR theo Thông tư 14/2025 nên kiểm định CH2 có thêm bản kiểm tra lại chỉ 2021–2024 (`car_2021_2024`).
- **STB Q4/2025:** quý lỗ (LNST −2.752 tỷ, ROE −17,96%, NPL 6,41%). Giữ nguyên, không xóa; ghi chú khi diễn giải xếp hạng 2025 và tương quan.
- **VPB:** NPL cao hơn hẳn phần còn lại gần như suốt giai đoạn (4–6,5%), do hợp nhất công ty tài chính tiêu dùng. Đây là lý do có bước kiểm tra lại NPL không có VPB. VPB Q1/2022 có ROA 6,42% (ngoại lai).
- **ACB** thiếu 5 phiên đầu tháng 12/2020 – ngoài giai đoạn nghiên cứu, không ảnh hưởng. Mốc chuẩn hóa giá = 100 là phiên 04/01/2021, chung cho cả 8 mã.

## 7. Môi trường

Python ≥ 3.10, các gói trong `requirements.txt`. Xuất PNG bằng kaleido bản 1.x cần Google Chrome trên máy; nếu báo lỗi `ChromeNotFoundError` thì chạy `plotly_get_chrome` một lần. Streamlit chỉ dùng biểu đồ tương tác nên không cần kaleido.
