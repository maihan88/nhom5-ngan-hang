# Báo cáo kiểm tra chất lượng dữ liệu

- Số dòng Bảng 4: **160** (kỳ vọng 160)

## 1. Số quý có dữ liệu theo ngân hàng

| ma_nh | có BCTC | có giá | có NPL | có CAR thật (công bố / tra thủ công) |
|---|---|---|---|---|
| ACB | 20 | 20 | 20 | 4 |
| BID | 20 | 20 | 20 | 4 |
| CTG | 20 | 20 | 20 | 4 |
| MBB | 20 | 20 | 20 | 4 |
| STB | 20 | 20 | 20 | 4 |
| TCB | 20 | 20 | 20 | 4 |
| VCB | 20 | 20 | 20 | 4 |
| VPB | 20 | 20 | 20 | 4 |

## 2. Số ô thiếu theo cột (Bảng 4)

- Các biến số (tài chính, giá, biến đếm sự kiện, nhãn): **không có ô thiếu**.
- `loai_su_kien`, `ngay_cong_bo`, `mo_ta_ngan`, `nguon`: mỗi cột trống 72 ô, đúng bằng 72 quý không có sự kiện (`co_su_kien = 0`). Đây là ô trống hợp lệ, không phải thiếu dữ liệu.
- `car`: 160 ô có giá trị, nhưng chỉ 32 ô là số thật (26 số VNDirect công bố, 6 số tra thủ công; năm 2021, 2022, 2023, 2024); còn lại được điền từ số thật gần nhất trước đó (xem `car_nguon`).
- `ty_suat_sinh_loi_quy_sau`, `xu_huong_quy_sau`: tính từ mốc dự báo, dùng giá đến 2026-05-15 (VNDirect); xem mục 8.

## 3. Đối chiếu tổng LNST 4 quý với BCTC năm

Chênh lệch lớn có thể do số quý bị lũy kế hoặc BCTC năm kiểm toán điều chỉnh.

| ma_nh | nam | tổng 4 quý | BCTC năm | lệch % |
|---|---|---|---|---|
| – | – | – | – | Tất cả lệch ≤ 2% |

## 4. Giá trị nằm ngoài khoảng hợp lý (cần kiểm tra thủ công, KHÔNG tự sửa)

- VPB Q1/2022: `roa` = 6.418 (ngoài [-3, 5])
- VPB Q1/2021: `nim` = 9.088 (ngoài [0.5, 8])
- VPB Q2/2021: `nim` = 8.918 (ngoài [0.5, 8])
- TCB Q2/2025: `ldr` = 130.314 (ngoài [40, 130])
- VPB Q2/2021: `ldr` = 133.075 (ngoài [40, 130])
- VPB Q3/2021: `ldr` = 132.559 (ngoài [40, 130])
- VPB Q4/2021: `ldr` = 146.909 (ngoài [40, 130])
- VPB Q1/2022: `ldr` = 136.589 (ngoài [40, 130])
- VPB Q2/2022: `ldr` = 132.863 (ngoài [40, 130])
- VPB Q3/2022: `ldr` = 145.139 (ngoài [40, 130])
- VPB Q4/2022: `ldr` = 144.594 (ngoài [40, 130])
- VPB Q1/2023: `ldr` = 139.943 (ngoài [40, 130])
- VPB Q2/2024: `ldr` = 132.445 (ngoài [40, 130])
- VPB Q3/2024: `ldr` = 133.537 (ngoài [40, 130])
- VPB Q4/2024: `ldr` = 143.673 (ngoài [40, 130])
- VPB Q1/2025: `ldr` = 132.151 (ngoài [40, 130])
- VPB Q2/2025: `ldr` = 138.010 (ngoài [40, 130])
- VPB Q3/2025: `ldr` = 153.015 (ngoài [40, 130])
- VPB Q4/2025: `ldr` = 150.292 (ngoài [40, 130])

## 4b. CAR: số nghi bị gán và số tra thủ công

Kiểm tra theo khoảng ở mục 4 không bắt được số "tròn đẹp bất thường". CAR công bố đúng 8,00 (ngưỡng tối thiểu của NHNN) thường là do nguồn ghi ngưỡng khi ngân hàng chỉ công bố "tuân thủ".

- Không còn số CAR công bố nào đúng 8,00.
- Số tra thủ công đang dùng (Q4 từng năm): BID 2022 = 8.92, BID 2023 = 9.18, BID 2024 = 9.03, CTG 2022 = 8.90, CTG 2023 = 9.30, CTG 2024 = 9.60

## 5. Đối chiếu NIM tự tính với NIM VNDirect (TTM)

- Chênh lệch tuyệt đối trung vị: 0.327 điểm %; lớn nhất: 1.750 điểm %
- NIM tự tính là năm hóa từ 1 quý nên dao động hơn NIM TTM – đây là khác biệt phương pháp.

## 6. Quý có ít phiên giao dịch (< 50)

- Không có.

## 7. Sự kiện phi tài chính

| ma_nh | chinh_sach_nhnn | chuyen_doi_so | doi_lanh_dao | hop_tac_trung_thau | khac | tang_von |
|---|---|---|---|---|---|---|
| ACB | 0 | 1 | 1 | 1 | 0 | 6 |
| BID | 1 | 0 | 7 | 2 | 0 | 9 |
| CTG | 0 | 0 | 7 | 0 | 0 | 8 |
| MBB | 0 | 1 | 4 | 0 | 2 | 10 |
| STB | 0 | 0 | 3 | 1 | 0 | 0 |
| TCB | 1 | 1 | 1 | 5 | 0 | 11 |
| VCB | 0 | 0 | 9 | 2 | 3 | 6 |
| VPB | 0 | 1 | 1 | 4 | 1 | 11 |

Phân loại bằng từ khóa trên tiêu đề -> NÊN rà soát `bang3a_su_kien_chi_tiet.csv` và ghi điều chỉnh vào thư mục `data/manual/` rồi chạy lại `python run_pipeline.py --offline --xlsx`.

## 8. Căn thời điểm cho nhãn dự báo

- Mốc dự báo = ngày cuối quý + 45 ngày; nhãn = giá tăng hay không từ mốc của quý t đến mốc của quý t+1.
- Ngày VNDirect nhập BCTC quý (lần đầu) trễ sau kỳ: trung vị 29 ngày, muộn nhất 39 ngày.
- Số kỳ BCTC nhập SAU mốc dự báo: **0**
- Số dòng thiếu nhãn: **0**
- Tỷ lệ nhãn 'tăng': 56.2%
