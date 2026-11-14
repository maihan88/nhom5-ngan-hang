# Pipeline thu thập & làm sạch dữ liệu – Nhóm 5 PTDL

Phụ trách: **Nguyễn Ngọc Mai Hân** (giai đoạn thu thập & làm sạch).
Bàn giao cho: Hoàng Ngọc Gia Nghi (thống kê) và Hoàng Mạnh Quân (Machine Learning).

Phạm vi: 8 ngân hàng (VCB, BID, CTG, TCB, MBB, ACB, STB, VPB), từ Q1/2021 đến quý gần nhất đã qua hạn công bố
BCTC (cuối quý + 45 ngày). Bản dùng cho báo cáo chốt ở Q1/2021 – Q2/2026 (176 dòng), giá đến 28/10/2026; tái lập đúng bộ đó
bằng biến môi trường `PTDL_DEN_QUY` và `PTDL_GIA_DEN` (xem mục 2).

## 1. Nguồn dữ liệu đã chọn và lý do

| Dữ liệu | Nguồn | Lý do chọn |
|---|---|---|
| BCTC quý (tổng TS, VCSH, LNST, dư nợ, thu nhập lãi…) | API công khai của **dstock (VNDirect)** `api-finfo.vndirect.com.vn/v4/financial_statements` | Trả JSON có cấu trúc, dùng đúng mẫu BCTC ngân hàng (TT49), mã chỉ tiêu cố định. CafeF/Vietstock trả HTML hay đổi giao diện, Vietstock còn cần token đăng nhập. |
| NPL | VNDirect `/v4/ratios` | BCTC dạng bảng không có phân loại nợ (nằm trong thuyết minh PDF). VNDirect đã tổng hợp sẵn. |
| CAR (31/12 mỗi năm) | **Báo cáo công bố thông tin tỷ lệ an toàn vốn** của ngân hàng, bản PDF Vietstock lưu theo link cố định (`crawler/car_reports.py`); dự phòng: VNDirect `/v4/ratios` | Số gốc của ngân hàng. VNDirect từng ghi sai (8,00 cho BID, CTG 2022–2024; 10,02 cho MBB 2021) và không cập nhật từ năm 2025. |
| Giá cổ phiếu ngày | VNDirect `/v4/stock_prices` | Có cả giá **đã điều chỉnh** (adClose). Cần giá này vì ngân hàng chia cổ tức bằng cổ phiếu gần như năm nào cũng có. |
| Sự kiện tăng vốn | VNDirect `/v4/events` | Dữ liệu sự kiện quyền có cấu trúc, ngày công bố chính xác. |
| Tin/công bố thông tin doanh nghiệp | **CafeF**, mục tin theo mã (`Events_RelatedNews_New.aspx`) | Có lịch sử đủ từ 2021, mỗi tin có ngày giờ và link gốc. Tin VNDirect **chỉ có từ khoảng 2025** nên chỉ dùng bổ sung. |

## 2. Cài đặt và chạy

```bash
pip install -r requirements.txt
python run_pipeline.py            # lần đầu: tải dữ liệu, có nghỉ ~0.8s giữa các request
python run_pipeline.py --xlsx     # xuất thêm file .xlsx
python run_pipeline.py --offline  # chỉ dùng cache, không gửi request nào
python run_pipeline.py --refresh  # bỏ cache, tải lại hết
```

Phản hồi gốc được lưu vào `data/raw/`, nên chạy lại sẽ không phải tải lại và vẫn truy vết được số liệu.

Kỳ cuối tự tăng khi có quý mới; khóa cache gắn theo kỳ cuối nên quý mới được tải về chứ không đọc cache cũ.
Quý cuối thường chưa có nhãn `xu_huong_quy_sau` (chưa tới mốc giá của quý sau) – ô trống đó là đúng.
Tái lập đúng bộ dữ liệu của báo cáo, không cần mạng (PowerShell). Cần chốt cả ngày cuối của giá, vì khóa cache giá
có ghi ngày cuối, còn mặc định ngày này trượt theo hôm nay:

```powershell
$env:PTDL_DEN_QUY = "2026Q3"; $env:PTDL_GIA_DEN = "2026-11-14"; py run_pipeline.py --offline --xlsx; Remove-Item Env:PTDL_DEN_QUY, Env:PTDL_GIA_DEN
```

## 3. Kết quả (`data/output/`)

| File | Nội dung |
|---|---|
| `bang1_tai_chinh_quy.csv` | Bảng 1: số liệu gốc (tỷ đồng) và ROA, ROE, NIM, NPL, CAR, LDR (%) |
| `bang2a_gia_ngay.csv` | Bảng 2: giá theo ngày |
| `bang2b_gia_quy.csv` | Bảng 2: gộp theo quý, gồm `ty_suat_sinh_loi_quy` và biến mục tiêu `xu_huong_quy_sau` |
| `bang3a_su_kien_chi_tiet.csv` | Bảng 3: từng sự kiện kèm ngày, tiêu đề và link (dùng để rà soát) |
| `bang3b_su_kien_quy.csv` | Bảng 3: theo quý, gồm `co_su_kien`, `so_luong_su_kien`, `loai_su_kien`, `sk_*` |
| `bang4_tong_hop.csv` | **Bảng 4 bàn giao**: 176 dòng × 40 cột, mỗi dòng là 1 ngân hàng × 1 quý |
| `mo_ta_du_lieu.md` | **Đọc đầu tiên**: mỗi file / mỗi cột nói về chuyện gì, viết bằng lời thường, kèm gợi ý cột cho từng câu hỏi nghiên cứu |
| `data_dictionary.csv/.md` | Giải thích **mọi cột của mọi file**: ý nghĩa, đơn vị, công thức, vai trò (khóa / biến phân tích / nhãn / đối chiếu…), dùng cho câu hỏi nào, lưu ý và thống kê nhanh (ô trống, min, max, trung bình, ví dụ) |
| `bao_cao_kiem_tra.md` | Kiểm tra chất lượng: độ phủ, ô thiếu, đối chiếu LNST năm, đối chiếu ROA/ROE/NIM với VNDirect, giá trị bất thường |

**Quy ước dữ liệu thiếu:** ô trống (NaN) nghĩa là nguồn không có dữ liệu. Không điền 0 cho biến tài chính hay giá. Riêng biến sự kiện thì quý không có sự kiện ghi 0.

## 4. Rà soát thủ công (nên làm trước khi bàn giao)

**CAR – mỗi năm cần nhập tay khoảng 4 số:** pipeline tự tải báo cáo tỷ lệ an toàn vốn 31/12 của 8 ngân hàng và tự đọc số hợp nhất với file có lớp text (BID, MBB, TCB, VPB). ACB, CTG, STB, VCB chỉ nộp bản scan nên phải nhập tay vào `data/manual/car_bao_cao_ngan_hang.csv` (cột `ma_nh, nam, car, nguon, ngay_tra, ly_do`; số **hợp nhất**, đơn vị %). Khi có báo cáo mới (thường tháng 3–4), mục 4b của `bao_cao_kiem_tra.md` ghi "Cần nhập tay …" kèm đường dẫn file PDF; nhập xong chạy lại `python run_pipeline.py --offline`. Số nhập tay được ưu tiên hơn số tự đọc, nên cũng dùng file này để sửa khi tự đọc sai. Kết quả đọc lưu ở `data/raw/car_bao_cao/*.json` (có trên Git); PDF nằm trong `data/raw/car_bao_cao/pdf/` (không đưa lên Git, tải lại được). Nếu ngân hàng đổi mẫu báo cáo, số không khớp quy tắc trong `config.CAR_COT_HOP_NHAT` sẽ bị chuyển sang "cần nhập tay" chứ không bị đoán.

**Sự kiện:**

Sự kiện được phân loại bằng từ khóa trên tiêu đề (cấu hình trong `crawler/config.py`), nên có thể nhầm. Sau lần chạy đầu:

1. Mở `data/output/bang3a_su_kien_chi_tiet.csv` (và `data/interim/tin_tho_da_phan_loai.csv` để tìm tin bị sót).
2. Ghi điều chỉnh vào `data/manual/`. Mỗi dòng áp dụng cho **từng tin riêng lẻ, trước khi gộp tin**, nên loại một tin sẽ không kéo theo các tin khác cùng cụm. Link có thể lấy ở cột `nguon` hoặc `nguon_khac` của `bang3a`. Nếu một link xuất hiện ở nhiều mã, thêm cột `ma_nh` để chỉ áp dụng cho một mã.
   - `su_kien_loai_bo.csv`: link (`nguon`) của tin phân loại sai, cần bỏ
   - `su_kien_sua_loai.csv`: `nguon` và `loai_su_kien` đúng
   - `su_kien_bo_sung.csv`: sự kiện bị sót (ví dụ tin hợp tác hoặc trúng thầu trên báo, không có trong CBTT)
   - Giá trị `loai_su_kien` hợp lệ: `tang_von`, `chuyen_doi_so`, `hop_tac_trung_thau`, `doi_lanh_dao`, `chinh_sach_nhnn`, `khac`
3. Chạy lại `python run_pipeline.py --offline`.

## 5. Hạn chế đã biết (nên ghi vào báo cáo)

- **CAR**: chỉ dùng 1 số/năm (31/12). Quý khác điền bằng số thật gần nhất trước đó (cột `car_nguon`: `bao_cao_ngan_hang`, `vndirect`, `dien_tiep_ky_truoc`). Cách này không dùng số của tương lai, nhưng báo cáo 31/12 thường đăng tháng 3–4, nên khi làm biến dự báo, dòng Q4 dùng CAR của Q3 (xem data dictionary). Thông tư 14/2025 (hiệu lực 15/9/2025) đổi cách tính CAR và cho ngân hàng chọn TT14 hoặc TT41 tới hết 2029. ACB ghi rõ năm 2025 tính theo TT14, nên CAR 2025 so với các năm trước cần thận trọng.
- **ROA/ROE/NIM** được năm hóa từ số liệu một quý (×4) nên dao động hơn số TTM. Số TTM của VNDirect chỉ dùng để đối chiếu trong `bao_cao_kiem_tra.md`, không nằm trong bảng.
- Tin hợp tác/chuyển đổi số giai đoạn 2021–2024 có thể bị thiếu vì CafeF chủ yếu đăng công bố thông tin chính thức. Nên bổ sung bằng tay qua `su_kien_bo_sung.csv`.
- API VNDirect là API công khai không có tài liệu chính thức. Nếu cấu trúc thay đổi, chương trình sẽ báo lỗi rõ ràng chứ không âm thầm ghi dữ liệu sai.
