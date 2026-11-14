# Rà soát dữ liệu – tuần 11 (14/11/2026)

Việc 01 trong kế hoạch GL2: đối chiếu các giá trị bị cảnh báo bất thường (mục 4 của `data/output/bao_cao_kiem_tra.md`) với BCTC gốc, và kiểm lại CAR.

## 1. Giá trị bị cảnh báo bất thường

**Kết luận: không có lỗi dữ liệu. Cả 22 cảnh báo đều là số thật**, do đặc thù của ngân hàng hoặc do cách định nghĩa chỉ số. Không cần sửa số nào.

| Cảnh báo | Số của nhóm | Đối chiếu | Kết luận |
|---|---|---|---|
| VPB Q1/2022 `roa` = 6,42 | LNST quý 8.916,8 tỷ | VPBank công bố LNST hợp nhất Q1/2022 khoảng 8.900 tỷ, LNTT 11.146 tỷ. Trong quý có khoản phí trả trước bancassurance của AIA trên 5.000 tỷ, ghi nhận một lần ([Vietcap](https://iq.vietcap.com.vn/report-detail/en/vpb-upfront-fee-parent-bank-make-up-for-fec-s-slow-quarter-earnings-flash), [Báo Đầu tư](https://baodautu.vn/loi-nhuan-quy-i2022-cua-vpbank-tang-gap-3-cung-ky-da-but-pha-manh-me-d164397)) | Đúng. Đây là **thu nhập bất thường một lần**. ROE quý này là 39,3%, cũng vì lý do đó |
| VPB Q1, Q2/2021 `nim` = 9,09; 8,92 | | MBS ghi NIM hợp nhất 6 tháng đầu 2021 là 9,15%, và Q4/2021 là 7,39% (số của nhóm: 7,16) ([MBS 11/2021](https://mbs.com.vn/media/2d4ncotg/vpb-mua-cập-nhật_08-11-2021-22-00.pdf), [MBS FY2021](https://mbs.com.vn/media/ho4hesur/vpb_mua_cập-nhật_fy2021.pdf)) | Đúng. NIM hợp nhất cao vì có FE Credit (cho vay tiêu dùng, NIM trên 20%) |
| LDR > 130: VPB (18 quý), TCB Q2/2025, Q1/2026 | TCB Q2/2026: dư nợ 847.335,6 tỷ; tiền gửi KH 662.447,7 tỷ | Khớp tuyệt đối với [BCTC hợp nhất Q2/2026 của TCB](https://techcombank.com/content/dam/techcombank/public-site/documents/techcombank-vas-consolidated-financial-statements-2q26-searchable.pdf): cho vay khách hàng 847.335.568 triệu, tiền gửi KH 662.447.730 triệu, tổng tài sản 1.273.076.923 triệu. Số Q4/2025 cũng khớp | Đúng số học. TCB tự công bố LDR là 80,1% ([thông cáo 2Q26](https://techcombank.com/content/dam/techcombank/public-site/documents/2q26-press-release-eng.pdf)) vì LDR theo Thông tư 22 cộng thêm giấy tờ có giá và vốn vay trung dài hạn vào mẫu số. LDR của nhóm là **cho vay / tiền gửi khách hàng**. VPB và TCB huy động nhiều qua giấy tờ có giá và liên ngân hàng, nên tỷ lệ này cao hơn 130 |

Kiểm tra bổ sung:
- VCSH của VPB cuối 2021 là 86.451,5 tỷ, khớp số báo chí nêu sau thương vụ bán 49% FE Credit cho SMBC (86.451 tỷ).
- Mục 3 của báo cáo kiểm tra: tổng LNST 4 quý lệch BCTC năm (đã kiểm toán) không quá 2% ở cả 8 ngân hàng. Như vậy số quý không bị lũy kế sai.

Đề xuất (chưa làm):
- Ghi chú các ô này trong báo cáo kiểm tra là "đã đối chiếu, giữ nguyên", để lần chạy sau không bị cảnh báo lại.
- Trong báo cáo cuối kỳ, nói rõ LDR của nhóm **không phải** LDR theo Thông tư 22, nên không so được với số ngân hàng tự công bố.
- VPB Q1/2022 là điểm ngoại lai thật: cân nhắc dùng thống kê bền (trung vị, Spearman) hoặc ghi chú khi nói về ROA/ROE năm 2022.

## 2. CAR

### 2.1 Vấn đề
- VNDirect (`BANK_CAR_AQ`) chỉ có 1 số/năm (31/12) và **không còn cập nhật từ năm 2025** (đã quét toàn bộ chỉ số VNDirect ngày 14/11/2026, không có mã CAR nào khác). Vì vậy Q4/2025–Q2/2026 đang dùng lại CAR năm 2024.
- VNDirect từng ghi sai: 8,00 (đúng ngưỡng tối thiểu) cho BID, CTG 2022–2024; 10,02 cho MBB 2021, trong khi báo cáo của MBB ghi hợp nhất 11,28, riêng lẻ 11,02.
- Không có nguồn API miễn phí nào khác: TCBS chặn (403), API Vietcap trả rỗng, trang chỉ số của Vietstock cần đăng nhập, FiinGroup thu phí.

### 2.2 Giải pháp: thêm nguồn crawl CAR riêng (`crawler/car_reports.py`)
- Nguồn: **báo cáo công bố thông tin tỷ lệ an toàn vốn 31/12** của chính ngân hàng, bản PDF Vietstock lưu theo link cố định (`config.CAR_REPORT_URL`).
- Vẫn **1 số/năm, quý 4**, như cách cũ. Lấy số **hợp nhất**.
- Thứ tự ưu tiên: số nhập tay > số tự đọc từ báo cáo > VNDirect > điền tiếp.
- **Tự động:** tải PDF; đọc số với file có lớp text (BID, MBB, TCB, VPB) theo quy tắc cột trong `config.CAR_COT_HOP_NHAT`. Cả 19 số tự đọc 2021–2025 khớp số đã kiểm bằng mắt.
- **Nhập tay:** ACB, CTG, STB, VCB chỉ nộp bản scan; MBB 2023 bị lỗi font. Hiện có 21 số trong `data/manual/car_bao_cao_ngan_hang.csv`, mỗi số kèm link. Từ nay mỗi năm khoảng 4 số, khi báo cáo 31/12 được đăng (tháng 3–4).
- **Không âm thầm sai:** bản scan, ngân hàng đổi mẫu báo cáo, số ngoài 5–25%, chưa có file sau 31/5 năm sau, hay số nhập tay khác số tự đọc đều được ghi rõ trong `bao_cao_kiem_tra.md` mục 4b. Lệch so với VNDirect hơn 0,3 điểm cũng được liệt kê.
- Cache: kết quả đọc lưu ở `data/raw/car_bao_cao/*.json` (có trên Git, nên `--offline` chạy được ở máy khác); PDF nằm trong `data/raw/car_bao_cao/pdf/` (đã đưa vào `.gitignore`). Đã thử: tải mới từ mạng, `--offline` không có PDF, thiếu số nhập tay. Cả ba đều chạy đúng.
- Cần thêm thư viện `pymupdf` (đã ghi vào `requirements.txt`).

### 2.3 Kết quả
- Số ô CAR thật: **32 → 40** (thêm năm 2025 cho cả 8 ngân hàng). Mọi số 31/12 từ 2021 đến 2025 đều lấy từ báo cáo của ngân hàng (`car_nguon = bao_cao_ngan_hang`). Các cột khác trong bảng không đổi.
- Số thay đổi so với trước: BID 2022 8,92 → 9,34 (trước dùng số riêng lẻ); CTG 2022/2023/2024: 8,90/9,30/9,60 → 8,98/9,31/9,54; MBB 2021: 10,02 → 11,28; TCB 2024: 15,30 → 15,40 (VNDirect làm tròn); cộng thêm 8 số năm 2025.
- ACB ghi rõ năm 2025 tính theo Thông tư 14/2025. TT14 cho phép chọn TT14 hoặc TT41 tới hết 2029, nên khi so CAR 2025 với các năm trước cần ghi chú.

### 2.4 Đã cập nhật phần của Nghi, Quân và dashboard
- **Code của Nghi** (`src/`; dashboard chép lại qua `dong_bo_du_lieu.py`):
  - `CAR_NGUON_SO_THAT = ("bao_cao_ngan_hang", "vndirect")`.
  - `kiem_tra.py` mục 3 không còn ghi cứng "32 giá trị / 2021–2024", mà kiểm tra "mọi quý 4 có CAR thật". Đã thêm lưu ý về Thông tư 14.
  - Notebook 04: phép kiểm tra lại "chỉ số VNDirect" (giờ rỗng) thay bằng **"CAR 2021–2024"**, tức bỏ năm 2025 vì đổi cách tính.
  - Sửa các chú thích ghi "32"; sửa `QUY_UOC.md`.
- **Dashboard:** trang Phương pháp và So sánh dùng `cf.CAR_NGUON_SO_THAT` thay cho nhãn ghi cứng; mô tả nguồn CAR và nhãn mẫu kiểm tra lại đã sửa.
- **Quân:** sửa câu cảnh báo trong `data_validation.py`.
- Đã chạy lại toàn bộ bằng `py chay_tat_ca.py --den-quy 2026Q2 --gia-den 2026-10-28 --offline`: cả 5 bước qua, kiểm tra dữ liệu của Nghi 0 lỗi, dữ liệu qua kiểm tra của Quân.

### 2.5 Kết quả trước / sau
| Kết quả | Trước | Sau |
|---|---|---|
| CH2 – CAR (mẫu chính) | 12 QD / 20 TN; 9,65% vs 12,64%; p = 0,0003 | 15 QD / 25 TN; 9,80% vs 12,63%; p = 0,0001 |
| CH2 – kiểm tra lại | "chỉ số VNDirect": 6 / 20, p = 0,024 | "CAR 2021–2024": 12 / 20, p = 0,0003 |
| CH2 – cấp ngân hàng (3 vs 5) | p = 0,071 | p = 0,071 |
| CH3 – CAR vs lợi suất, mẫu chính (176 quý) | ρ = −0,039 | ρ = −0,030 |
| CH3 – chỉ số CAR thật | 32 số, ρ = −0,52 (p hiệu chỉnh 0,003) | 40 số, ρ = −0,47 (p hiệu chỉnh 0,002) |
| Logistic – AUC (3 mô hình) | 0,535 / 0,570 / 0,547 | 0,531 / 0,555 / 0,535 |
| Logistic – Accuracy | 0,500 / 0,625 / 0,594 | không đổi |
| K-Means | — | 0/176 dòng đổi cụm |

**Không kết luận nào đổi chiều.** NIM, NPL, ROA, ROE không đổi. Nếu báo cáo hoặc slide có ghi các con số CAR ở trên (trung bình nhóm, p-value, AUC) thì cần cập nhật theo.

## 3. Cập nhật bộ dữ liệu lên Q3/2026 (14/11/2026)
- Đã chạy `py chay_tat_ca.py` (có mạng). Kỳ cuối tự lên **Q3/2026**: Bảng 4 có **184 dòng**, giá đến 14/11/2026. VNDirect đã nhập BCTC Q3 của cả 8 ngân hàng (muộn nhất ngày 30/10). Cả 5 bước chạy qua; kiểm tra của Nghi 0 lỗi; dữ liệu qua kiểm tra của Quân.
- Lệnh tái lập không cần mạng đổi thành `py chay_tat_ca.py --den-quy 2026Q3 --gia-den 2026-11-14 --offline` (đã sửa trong các README). Đã thử chạy lại: ra bảng giống hệt.
- **Nhãn dự báo Q2 và Q3/2026 đang trống.** Mốc dự báo của Q3 là 14/11, rơi vào thứ Bảy, mà giá mới có đến 13/11. Pipeline không tạo nhãn khi ngày cần giá vượt quá dữ liệu giá đang có. Chạy lại từ thứ Hai 16/11 thì nhãn Q2 sẽ có.
- 176 dòng cũ không đổi, trừ 1 ô thứ tự loại sự kiện (MBB Q2/2026). CAR Q3/2026 điền tiếp từ số 31/12/2025.
- **Tin sự kiện quý 3/2026 mới được phân loại tự động, chưa rà soát tay.**
- Báo cáo kiểm tra có thêm 2 cảnh báo LDR > 130 ở Q3/2026 (TCB 131,3; VPB 152,8). Cùng loại với các cảnh báo đã giải thích ở mục 1: đây là số thật.
- Kết quả thống kê gần như không đổi so với bản Q2: NIM QD/TN 2,81/4,48%, p < 0,001; NPL p = 0,14, chưa khác biệt; CAR không đổi vì Q3 là số điền tiếp; tương quan với lợi suất vẫn ≈ 0. Mô hình vẫn kiểm chứng trên năm 2025, AUC không đổi; web có thêm dự báo cho quý 4/2026.
