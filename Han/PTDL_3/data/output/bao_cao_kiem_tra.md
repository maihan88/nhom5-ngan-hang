# Báo cáo kiểm tra chất lượng dữ liệu

- Số dòng Bảng 4: **184** (kỳ vọng 184)

## 1. Số quý có dữ liệu theo ngân hàng

| ma_nh | có BCTC | có giá | có NPL | có CAR thật (báo cáo ngân hàng / VNDirect) |
|---|---|---|---|---|
| ACB | 23 | 23 | 23 | 5 |
| BID | 23 | 23 | 23 | 5 |
| CTG | 23 | 23 | 23 | 5 |
| MBB | 23 | 23 | 23 | 5 |
| STB | 23 | 23 | 23 | 5 |
| TCB | 23 | 23 | 23 | 5 |
| VCB | 23 | 23 | 23 | 5 |
| VPB | 23 | 23 | 23 | 5 |

## 2. Số ô thiếu theo cột (Bảng 4)

- `ty_suat_sinh_loi_quy_sau`: 16
- `xu_huong_quy_sau`: 16
- `loai_su_kien`, `ngay_cong_bo`, `mo_ta_ngan`, `nguon`: mỗi cột trống 76 ô, đúng bằng 76 quý không có sự kiện (`co_su_kien = 0`). Đây là ô trống hợp lệ, không phải thiếu dữ liệu.
- `car`: 184 ô có giá trị, nhưng chỉ 40 ô là số thật (40 số từ báo cáo tỷ lệ an toàn vốn của ngân hàng, 0 số VNDirect; năm 2021, 2022, 2023, 2024, 2025); còn lại được điền từ số thật gần nhất trước đó (xem `car_nguon`).
- `ty_suat_sinh_loi_quy_sau`, `xu_huong_quy_sau`: tính từ mốc dự báo, dùng giá đến 2026-11-14 (VNDirect); xem mục 8.

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
- TCB Q3/2026: `ldr` = 131.310 (ngoài [40, 130])
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
- VPB Q3/2026: `ldr` = 152.846 (ngoài [40, 130])

## 4b. CAR 31/12: nguồn từng năm và việc cần làm

Ưu tiên số hợp nhất trong báo cáo tỷ lệ an toàn vốn của ngân hàng (tự đọc từ PDF có lớp text, hoặc nhập tay vào `data/manual/car_bao_cao_ngan_hang.csv` với bản scan); chưa có thì dùng số VNDirect; quý khác điền tiếp.

Ký hiệu: **T** tự đọc · **N** nhập tay · **V** VNDirect · **–** chưa có số (đang điền tiếp từ năm trước).

| ma_nh | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| ACB | 11.23 N | 12.80 N | 12.48 N | 11.82 N | 12.45 N |
| BID | 8.97 T | 9.34 T | 9.18 T | 9.03 T | 9.18 T |
| CTG | 9.14 N | 8.98 N | 9.31 N | 9.54 N | 9.89 N |
| MBB | 11.28 T | 11.53 T | 10.75 N | 11.76 T | 11.02 T |
| STB | 9.93 N | 9.49 N | 9.11 N | 10.14 N | 9.20 N |
| TCB | 15.04 T | 15.18 T | 14.35 T | 15.40 T | 14.61 T |
| VCB | 9.31 N | 9.95 N | 11.39 N | 12.16 N | 11.56 N |
| VPB | 14.27 T | 14.90 T | 17.07 T | 15.50 T | 14.35 T |

**Việc cần làm:**

- Không có. Mọi năm đã có số từ báo cáo của ngân hàng.

**Đối chiếu với VNDirect** (lệch > 0,3 điểm %):

- BID 31/12/2022: báo cáo ngân hàng 9.34 khác VNDirect 8.00 (đang dùng số báo cáo ngân hàng).
- BID 31/12/2023: báo cáo ngân hàng 9.18 khác VNDirect 8.00 (đang dùng số báo cáo ngân hàng).
- BID 31/12/2024: báo cáo ngân hàng 9.03 khác VNDirect 8.00 (đang dùng số báo cáo ngân hàng).
- CTG 31/12/2022: báo cáo ngân hàng 8.98 khác VNDirect 8.00 (đang dùng số báo cáo ngân hàng).
- CTG 31/12/2023: báo cáo ngân hàng 9.31 khác VNDirect 8.00 (đang dùng số báo cáo ngân hàng).
- CTG 31/12/2024: báo cáo ngân hàng 9.54 khác VNDirect 8.00 (đang dùng số báo cáo ngân hàng).
- MBB 31/12/2021: báo cáo ngân hàng 11.28 khác VNDirect 10.02 (đang dùng số báo cáo ngân hàng).

## 5. Đối chiếu ROA, ROE, NIM tự tính với số VNDirect công bố

Số VNDirect là số 4 quý gần nhất (TTM): tổng 4 quý / bình quân 5 thời điểm cuối quý. Để so cùng cách, pipeline tính lại ROA, ROE, NIM theo đúng cách đó từ số liệu gốc của nhóm. Số VNDirect chỉ dùng ở mục này, không xuất ra bảng dữ liệu; biến phân tích vẫn là `roa`, `roe`, `nim` năm hóa từ 1 quý.

| Chỉ số | Số quý so được | Lệch trung vị (điểm %) | 90% số quý lệch dưới | Lệch lớn nhất | Quý lệch nhiều nhất |
|---|---|---|---|---|---|
| ROA | 160 | 0.013 | 0.076 | 0.432 | VPB Q2/2023 |
| ROE | 160 | 0.149 | 0.548 | 2.716 | VPB Q2/2023 |
| NIM | 160 | 0.353 | 0.517 | 0.659 | VPB Q3/2025 |

Lệch trung vị theo ngân hàng (điểm %):

| ma_nh | ROA | ROE | NIM |
|---|---|---|---|
| ACB | 0.000 | 0.000 | 0.408 |
| BID | 0.018 | 0.334 | 0.218 |
| CTG | 0.007 | 0.116 | 0.348 |
| MBB | 0.048 | 0.506 | 0.262 |
| STB | 0.000 | 0.000 | 0.263 |
| TCB | 0.036 | 0.229 | 0.372 |
| VCB | 0.001 | 0.059 | 0.422 |
| VPB | 0.061 | 0.430 | 0.556 |

- Lệch nhỏ nghĩa là số liệu gốc (LNST, tổng tài sản, vốn chủ sở hữu, thu nhập lãi thuần) lấy đúng.
- Lệch đều ở mọi ngân hàng thường do khác định nghĩa (vd tài sản sinh lãi của NIM; VNDirect không công bố chi tiết), không phải lỗi dữ liệu. Chỉ lệch bất thường ở vài quý mới cần tra lại.

## 6. Quý có ít phiên giao dịch (< 50)

- Không có.

## 7. Sự kiện phi tài chính

| ma_nh | chinh_sach_nhnn | chuyen_doi_so | doi_lanh_dao | hop_tac_trung_thau | khac | tang_von |
|---|---|---|---|---|---|---|
| ACB | 0 | 1 | 1 | 2 | 0 | 7 |
| BID | 1 | 0 | 9 | 3 | 0 | 12 |
| CTG | 0 | 0 | 7 | 1 | 0 | 9 |
| MBB | 0 | 1 | 6 | 0 | 2 | 12 |
| STB | 0 | 0 | 8 | 1 | 0 | 0 |
| TCB | 1 | 2 | 1 | 6 | 0 | 14 |
| VCB | 0 | 0 | 9 | 3 | 3 | 6 |
| VPB | 0 | 3 | 2 | 7 | 1 | 14 |

Phân loại bằng từ khóa trên tiêu đề -> NÊN rà soát `bang3a_su_kien_chi_tiet.csv` và ghi điều chỉnh vào thư mục `data/manual/` rồi chạy lại `python run_pipeline.py --offline --xlsx`.

## 8. Căn thời điểm cho nhãn dự báo

- Mốc dự báo = ngày cuối quý + 45 ngày; nhãn = giá tăng hay không từ mốc của quý t đến mốc của quý t+1.
- Ngày VNDirect nhập BCTC quý (lần đầu) trễ sau kỳ: trung vị 29 ngày, muộn nhất 39 ngày.
- Số kỳ BCTC nhập SAU mốc dự báo: **0**
- Số dòng thiếu nhãn: **16** -> ACB Q2/2026, ACB Q3/2026, BID Q2/2026, BID Q3/2026, CTG Q2/2026, CTG Q3/2026, MBB Q2/2026, MBB Q3/2026, STB Q2/2026, STB Q3/2026, TCB Q2/2026, TCB Q3/2026, VCB Q2/2026, VCB Q3/2026, VPB Q2/2026, VPB Q3/2026
- Tỷ lệ nhãn 'tăng': 54.2%
