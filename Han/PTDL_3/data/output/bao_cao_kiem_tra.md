# Báo cáo kiểm tra chất lượng dữ liệu

- Số dòng Bảng 4: **176** (kỳ vọng 176)

## 1. Số quý có dữ liệu theo ngân hàng

| ma_nh | có BCTC | có giá | có NPL | có CAR thật (công bố / tra thủ công) |
|---|---|---|---|---|
| ACB | 22 | 22 | 22 | 4 |
| BID | 22 | 22 | 22 | 4 |
| CTG | 22 | 22 | 22 | 4 |
| MBB | 22 | 22 | 22 | 4 |
| STB | 22 | 22 | 22 | 4 |
| TCB | 22 | 22 | 22 | 4 |
| VCB | 22 | 22 | 22 | 4 |
| VPB | 22 | 22 | 22 | 4 |

## 2. Số ô thiếu theo cột (Bảng 4)

- `ty_suat_sinh_loi_quy_sau`: 8
- `xu_huong_quy_sau`: 8
- `loai_su_kien`, `ngay_cong_bo`, `mo_ta_ngan`, `nguon`: mỗi cột trống 74 ô, đúng bằng 74 quý không có sự kiện (`co_su_kien = 0`). Đây là ô trống hợp lệ, không phải thiếu dữ liệu.
- `car`: 176 ô có giá trị, nhưng chỉ 32 ô là số thật (26 số VNDirect công bố, 6 số tra thủ công; năm 2021, 2022, 2023, 2024); còn lại được điền từ số thật gần nhất trước đó (xem `car_nguon`).
- `ty_suat_sinh_loi_quy_sau`, `xu_huong_quy_sau`: tính từ mốc dự báo, dùng giá đến 2026-10-28 (VNDirect); xem mục 8.

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
- TCB Q1/2026: `ldr` = 132.853 (ngoài [40, 130])
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
- VPB Q1/2026: `ldr` = 152.466 (ngoài [40, 130])
- VPB Q2/2026: `ldr` = 158.469 (ngoài [40, 130])

## 4b. CAR: số nghi bị gán và số tra thủ công

Kiểm tra theo khoảng ở mục 4 không bắt được số "tròn đẹp bất thường". CAR công bố đúng 8,00 (ngưỡng tối thiểu của NHNN) thường là do nguồn ghi ngưỡng khi ngân hàng chỉ công bố "tuân thủ".

- Không còn số CAR công bố nào đúng 8,00.
- Số tra thủ công đang dùng (Q4 từng năm): BID 2022 = 8.92, BID 2023 = 9.18, BID 2024 = 9.03, CTG 2022 = 8.90, CTG 2023 = 9.30, CTG 2024 = 9.60

## 5. Đối chiếu ROA, ROE, NIM tự tính với số VNDirect công bố

Số VNDirect là số 4 quý gần nhất (TTM): tổng 4 quý / bình quân 5 thời điểm cuối quý. Để so cùng cách, pipeline tính lại ROA, ROE, NIM theo đúng cách đó từ số liệu gốc của nhóm. Số VNDirect chỉ dùng ở mục này, không xuất ra bảng dữ liệu; biến phân tích vẫn là `roa`, `roe`, `nim` năm hóa từ 1 quý.

| Chỉ số | Số quý so được | Lệch trung vị (điểm %) | 90% số quý lệch dưới | Lệch lớn nhất | Quý lệch nhiều nhất |
|---|---|---|---|---|---|
| ROA | 152 | 0.013 | 0.075 | 0.432 | VPB Q2/2023 |
| ROE | 152 | 0.149 | 0.542 | 2.716 | VPB Q2/2023 |
| NIM | 152 | 0.357 | 0.514 | 0.659 | VPB Q3/2025 |

Lệch trung vị theo ngân hàng (điểm %):

| ma_nh | ROA | ROE | NIM |
|---|---|---|---|
| ACB | 0.000 | 0.000 | 0.426 |
| BID | 0.018 | 0.340 | 0.216 |
| CTG | 0.008 | 0.116 | 0.335 |
| MBB | 0.049 | 0.506 | 0.255 |
| STB | 0.000 | 0.000 | 0.251 |
| TCB | 0.032 | 0.199 | 0.377 |
| VCB | 0.001 | 0.059 | 0.421 |
| VPB | 0.060 | 0.416 | 0.546 |

- Lệch nhỏ nghĩa là số liệu gốc (LNST, tổng tài sản, vốn chủ sở hữu, thu nhập lãi thuần) lấy đúng.
- Lệch đều ở mọi ngân hàng thường do khác định nghĩa (vd tài sản sinh lãi của NIM; VNDirect không công bố chi tiết), không phải lỗi dữ liệu. Chỉ lệch bất thường ở vài quý mới cần tra lại.

## 6. Quý có ít phiên giao dịch (< 50)

- Không có.

## 7. Sự kiện phi tài chính

| ma_nh | chinh_sach_nhnn | chuyen_doi_so | doi_lanh_dao | hop_tac_trung_thau | khac | tang_von |
|---|---|---|---|---|---|---|
| ACB | 0 | 1 | 1 | 2 | 0 | 7 |
| BID | 1 | 0 | 9 | 3 | 0 | 11 |
| CTG | 0 | 0 | 7 | 1 | 0 | 8 |
| MBB | 0 | 1 | 6 | 0 | 2 | 11 |
| STB | 0 | 0 | 6 | 1 | 0 | 0 |
| TCB | 1 | 2 | 1 | 6 | 0 | 13 |
| VCB | 0 | 0 | 9 | 3 | 3 | 6 |
| VPB | 0 | 3 | 1 | 6 | 1 | 13 |

Phân loại bằng từ khóa trên tiêu đề -> NÊN rà soát `bang3a_su_kien_chi_tiet.csv` và ghi điều chỉnh vào thư mục `data/manual/` rồi chạy lại `python run_pipeline.py --offline --xlsx`.

## 8. Căn thời điểm cho nhãn dự báo

- Mốc dự báo = ngày cuối quý + 45 ngày; nhãn = giá tăng hay không từ mốc của quý t đến mốc của quý t+1.
- Ngày VNDirect nhập BCTC quý (lần đầu) trễ sau kỳ: trung vị 29 ngày, muộn nhất 39 ngày.
- Số kỳ BCTC nhập SAU mốc dự báo: **0**
- Số dòng thiếu nhãn: **8** -> ACB Q2/2026, BID Q2/2026, CTG Q2/2026, MBB Q2/2026, STB Q2/2026, TCB Q2/2026, VCB Q2/2026, VPB Q2/2026
- Tỷ lệ nhãn 'tăng': 54.2%
