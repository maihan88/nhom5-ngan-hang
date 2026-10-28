# Pipeline thu thập & làm sạch dữ liệu – Nhóm 5 PTDL

Phụ trách: **Nguyễn Ngọc Mai Hân** (giai đoạn thu thập & làm sạch).
Bàn giao cho: Hoàng Ngọc Gia Nghi (thống kê) và Hoàng Mạnh Quân (Machine Learning).

Phạm vi: 8 ngân hàng (VCB, BID, CTG, TCB, MBB, ACB, STB, VPB), Q1/2021 – Q4/2025.

## 1. Nguồn dữ liệu đã chọn và lý do

| Dữ liệu | Nguồn | Lý do chọn |
|---|---|---|
| BCTC quý (tổng TS, VCSH, LNST, dư nợ, thu nhập lãi…) | API công khai của **dstock (VNDirect)** `api-finfo.vndirect.com.vn/v4/financial_statements` | Trả JSON có cấu trúc, dùng đúng mẫu BCTC ngân hàng (TT49), mã chỉ tiêu cố định. CafeF/Vietstock trả HTML hay đổi giao diện, Vietstock còn cần token đăng nhập. |
| NPL, CAR | VNDirect `/v4/ratios` | BCTC dạng bảng không có phân loại nợ và vốn tự có (nằm trong thuyết minh PDF). VNDirect đã tổng hợp sẵn. |
| Giá cổ phiếu ngày | VNDirect `/v4/stock_prices` | Có cả giá **đã điều chỉnh** (adClose). Cần giá này vì ngân hàng chia cổ tức bằng cổ phiếu gần như năm nào cũng có. |
| Sự kiện tăng vốn | VNDirect `/v4/events` | Dữ liệu sự kiện quyền có cấu trúc, ngày công bố chính xác. |
| Tin/công bố thông tin doanh nghiệp | **CafeF**, mục tin theo mã (`Events_RelatedNews_New.aspx`) | Có lịch sử đủ 2021–2025, mỗi tin có ngày giờ và link gốc. Tin VNDirect **chỉ có từ khoảng 2025** nên chỉ dùng bổ sung. |

## 2. Cài đặt và chạy

```bash
pip install -r requirements.txt
python run_pipeline.py            # lần đầu: tải dữ liệu, có nghỉ ~0.8s giữa các request
python run_pipeline.py --xlsx     # xuất thêm file .xlsx
python run_pipeline.py --offline  # chỉ dùng cache, không gửi request nào
python run_pipeline.py --refresh  # bỏ cache, tải lại hết
```

Phản hồi gốc được lưu vào `data/raw/`, nên chạy lại sẽ không phải tải lại và vẫn truy vết được số liệu.

## 3. Kết quả (`data/output/`)

| File | Nội dung |
|---|---|
| `bang1_tai_chinh_quy.csv` | Bảng 1: số liệu gốc (tỷ đồng) và ROA, ROE, NIM, NPL, CAR, LDR (%) |
| `bang2a_gia_ngay.csv` | Bảng 2: giá theo ngày |
| `bang2b_gia_quy.csv` | Bảng 2: gộp theo quý, gồm `ty_suat_sinh_loi_quy` và biến mục tiêu `xu_huong_quy_sau` |
| `bang3a_su_kien_chi_tiet.csv` | Bảng 3: từng sự kiện kèm ngày, tiêu đề và link (dùng để rà soát) |
| `bang3b_su_kien_quy.csv` | Bảng 3: theo quý, gồm `co_su_kien`, `so_luong_su_kien`, `loai_su_kien`, `sk_*` |
| `bang4_tong_hop.csv` | **Bảng 4 bàn giao**: 160 dòng, mỗi dòng là 1 ngân hàng × 1 quý |
| `mo_ta_du_lieu.md` | **Đọc đầu tiên**: mỗi file / mỗi cột nói về chuyện gì, viết bằng lời thường, kèm gợi ý cột cho từng câu hỏi nghiên cứu |
| `data_dictionary.csv/.md` | Giải thích **mọi cột của mọi file**: ý nghĩa, đơn vị, công thức, vai trò (khóa / biến phân tích / nhãn / đối chiếu…), dùng cho câu hỏi nào, lưu ý và thống kê nhanh (ô trống, min, max, trung bình, ví dụ) |
| `bao_cao_kiem_tra.md` | Kiểm tra chất lượng: độ phủ, ô thiếu, đối chiếu LNST năm, giá trị bất thường |

**Quy ước dữ liệu thiếu:** ô trống (NaN) nghĩa là nguồn không có dữ liệu. Không điền 0 cho biến tài chính hay giá. Riêng biến sự kiện thì quý không có sự kiện ghi 0.

## 4. Rà soát thủ công (nên làm trước khi bàn giao)

**CAR tra thủ công:** `data/manual/car_tra_thu_cong.csv` (cột `ma_nh, nam, car, loai_car, nguon, ngay_tra, ly_do`) thay số CAR cuối năm của VNDirect khi số đó không đáng tin. Hiện có 6 dòng: BID và CTG năm 2022–2024, vì VNDirect ghi đúng 8,00 (ngưỡng tối thiểu) ba năm liền. Ô `car` để trống = bỏ số nguồn, để bước điền tiếp xử lý. Báo cáo kiểm tra (mục 4b) tự cảnh báo nếu còn số CAR công bố đúng 8,00.

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

- **CAR**: VNDirect chỉ có số cuối năm (dù một số ngân hàng tự công bố theo quý/nửa năm). Quý không có số được điền bằng số thật gần nhất trước đó (cột `car_nguon`: `cong_bo`, `tra_thu_cong`, `dien_tiep_ky_truoc`). Cách này không dùng số của tương lai nên không làm rò rỉ thông tin vào mô hình. Số tra thủ công của CTG là nguồn thứ cấp (công ty chứng khoán) vì VietinBank chỉ ghi "tuân thủ"; năm 2025 chưa thay vì một số ngân hàng đã đổi cách tính CAR theo Thông tư 14/2025 nên không so sánh được với các năm trước.
- **no_xau** là số **ước tính**, tính bằng NPL × dư nợ cho vay KH.
- **ROA/ROE/NIM** được năm hóa từ số liệu một quý (×4) nên dao động hơn số TTM. Các cột `*_ttm_vnd` để đối chiếu.
- Tin hợp tác/chuyển đổi số giai đoạn 2021–2024 có thể bị thiếu vì CafeF chủ yếu đăng công bố thông tin chính thức. Nên bổ sung bằng tay qua `su_kien_bo_sung.csv`.
- API VNDirect là API công khai không có tài liệu chính thức. Nếu cấu trúc thay đổi, chương trình sẽ báo lỗi rõ ràng chứ không âm thầm ghi dữ liệu sai.
