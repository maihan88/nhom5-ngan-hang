# Giải thích bài toán và quy trình làm sạch dữ liệu – Nhóm 5 PTDL

> Tài liệu này dựa trên bản đề xuất `Nhóm 5_PTDL 6.docx` và **code + dữ liệu thực tế** trong thư mục `PTDL_3` (pipeline `run_pipeline.py`, thư mục `crawler/`, kết quả trong `data/output/`). Mọi con số dưới đây lấy từ lần chạy pipeline gần nhất.

---

## 1. Đây là bài toán gì?

**Đề tài:** Phân tích tài chính các ngân hàng niêm yết (Banking Stock & Financial Analytics).

**Vấn đề thực tế:** Nhà đầu tư cá nhân muốn đánh giá "sức khỏe" một ngân hàng phải tự gom số liệu từ nhiều báo cáo tài chính (BCTC) rời rạc, rồi tự đối chiếu với giá cổ phiếu. Nhóm xây dựng một **pipeline** hoàn chỉnh:

```
Thu thập  →  Làm sạch & chuẩn hóa  →  Phân tích thống kê / ML  →  Web dashboard (Streamlit)
```

**Phạm vi:** 8 ngân hàng (VCB, BID, CTG – quốc doanh; TCB, MBB, ACB, STB, VPB – tư nhân), Q1/2021 – Q4/2025 → **8 × 20 quý = 160 quan sát**.

Về mặt phân tích dữ liệu, đề tài là **tổ hợp của nhiều dạng bài toán**:

| # | Câu hỏi | Dạng bài toán | Biến chính |
|---|---|---|---|
| CH1 | Ngân hàng nào sinh lời cao nhất, có ổn định không? | Thống kê mô tả, xếp hạng | `roa`, `roe` |
| CH2 | Quốc doanh vs tư nhân có khác nhau về NIM, NPL, CAR? | Kiểm định giả thuyết (t-test / Mann-Whitney) | `nim`, `npl`, `car`, `loai_hinh_so_huu` |
| CH3 | Chỉ số tài chính nào liên hệ rõ nhất với biến động giá? | Phân tích tương quan | chỉ số tài chính ↔ `ty_suat_sinh_loi_quy` |
| CH4 | Dự đoán giá quý sau tăng hay không? Thêm sự kiện có giúp không? | **Phân loại nhị phân** (Logistic Regression) | đầu vào: chỉ số + `co_su_kien`, `sk_*`; nhãn: `xu_huong_quy_sau` |
| CH5 | Các ngân hàng có tạo thành nhóm rõ ràng không? | **Phân cụm** (K-Means) + giảm chiều (PCA) | các chỉ số tài chính |

Trọng tâm "học máy có giám sát" là **CH4 – bài toán phân loại nhị phân** (1 = giá tăng, 0 = không tăng).

---

## 2. Có lấy được dữ liệu không?

**Có – và đã lấy xong.** Pipeline đã chạy thành công, cho đủ **160/160 dòng**, không thiếu quý nào.

### 2.1. Nguồn dữ liệu đã dùng

| Dữ liệu | Nguồn | Cách lấy | Vì sao chọn |
|---|---|---|---|
| BCTC quý (tổng TS, VCSH, LNST, dư nợ, thu nhập lãi…) | API công khai **VNDirect (dstock)** `/v4/financial_statements` | `requests` → JSON | Có cấu trúc, đúng mẫu BCTC ngân hàng (TT49), mã chỉ tiêu cố định |
| NPL, CAR | VNDirect `/v4/ratios` | JSON | NPL/CAR nằm trong thuyết minh PDF, BCTC dạng bảng không có → dùng số VNDirect đã tổng hợp |
| Giá cổ phiếu theo ngày | VNDirect `/v4/stock_prices` | JSON | Có sẵn **giá đã điều chỉnh** (`adClose`) |
| Sự kiện tăng vốn | VNDirect `/v4/events` | JSON | Dữ liệu sự kiện quyền có cấu trúc, ngày công bố chính xác |
| Tin tức / công bố thông tin | **CafeF** (tin theo mã) | `requests` + `BeautifulSoup` (HTML) | Có lịch sử đủ 2021–2025, mỗi tin có ngày giờ + link |
| Tin doanh nghiệp bổ sung | VNDirect `/v4/news` | JSON | Chỉ có từ ~2025 → dùng bổ sung |
| (Thử nghiệm) | Vietstock | POST + token | Đang thử, **chưa đưa vào kết quả chính** |

### 2.2. Thu thập được bao nhiêu?

| Loại | Số lượng |
|---|---|
| BCTC quý | 8 NH × 20 quý (+ Q4/2020 để tính bình quân) |
| Giá theo ngày | **10.851 phiên** (01/12/2020 → 15/05/2026) |
| Tin thô | **5.636 tin** (CafeF 5.225; VNDirect-news 376; VNDirect-events 34; thủ công 1) |
| Sự kiện sau làm sạch | **121 sự kiện** (gộp từ 290 tin; cập nhật 03/10/2026) |

### 2.3. Cách thu thập "có trách nhiệm" (file `http_client.py`)

- **Nghỉ 0,8 giây giữa các request** để không làm quá tải server.
- **Tự thử lại** khi gặp lỗi 429/5xx (tối đa 4 lần, chờ 2s → 4s → 8s…).
- **Cache toàn bộ phản hồi gốc** vào `data/raw/` → chạy lại không phải tải lại, và **truy vết được** số liệu gốc khi thấy bất thường.
- Chế độ `--offline`: chỉ dùng cache, không gửi request nào (dùng sau khi rà soát thủ công).
- Nếu API trả sai cấu trúc → **báo lỗi rõ ràng**, không âm thầm ghi dữ liệu sai.

---

## 3. Dữ liệu có vấn đề gì? Có làm sạch được không?

**Có vấn đề – và đã xử lý được.** Dữ liệu tài chính thực tế gần như không bao giờ "sạch" ngay. Bảng dưới tóm tắt các vấn đề đã gặp và cách giải quyết; chi tiết ở Mục 4.

| # | Vấn đề | Ảnh hưởng nếu không xử lý | Cách xử lý |
|---|---|---|---|
| 1 | Dữ liệu API ở dạng "dài" (mỗi chỉ tiêu 1 dòng), mã số khó hiểu | Không phân tích được | Lọc mã chỉ tiêu cần, **pivot** thành bảng rộng, đặt tên cột tiếng Việt |
| 2 | Một chỉ tiêu có nhiều bản (BCTC điều chỉnh/kiểm toán lại) | Trùng dòng, số sai | Giữ **bản sửa sau cùng** theo `modifiedDate` |
| 3 | Đơn vị VND quá lớn; NPL/CAR ở dạng thập phân | Khó đọc, dễ nhầm | Quy đổi → **tỷ đồng**; tỷ lệ → **%** |
| 4 | Không có sẵn ROA/ROE/NIM đúng định nghĩa | Thiếu biến phân tích | **Tự tính** theo công thức minh bạch, đối chiếu với VNDirect |
| 5 | **CAR chỉ công bố cuối năm** (thiếu 3/4 số quý) | 128/160 ô trống | **Điền tiếp giá trị gần nhất đã công bố** (forward-fill), đánh dấu bằng `car_nguon` |
| 6 | **Giá bị "rơi" ở ngày chia cổ tức bằng cổ phiếu** | Lợi suất sai, nhãn sai | Dùng **giá đã điều chỉnh** (`adClose`) |
| 7 | Thiếu phiên / quý giá | Lệch giá đầu quý | Tra giá đầu quý theo kỳ (Period), không dùng `shift` |
| 8 | **Rò rỉ thông tin tương lai** khi tạo nhãn | Mô hình "ăn gian", kết quả ảo | Tính nhãn từ **mốc dự báo = cuối quý + 45 ngày** |
| 9 | Tin tức rất nhiễu (5.636 tin, phần lớn là tin thường quy) | Biến sự kiện vô nghĩa | Lọc loại trừ → phân loại theo từ khóa |
| 10 | Tin gắn nhầm mã / tin toàn ngành | Gán sự kiện sai ngân hàng | Gắn cờ `tin_nganh_hoac_sai_ma` và loại |
| 11 | **Một sự kiện được đăng nhiều lần** | Đếm trùng | Gộp tin trùng (cửa sổ 3 ngày; tăng vốn 1 lần/quý) |
| 12 | Phân loại tự động có sai sót | Nhãn sự kiện sai | **Rà soát thủ công** qua 3 file trong `data/manual/` |
| 13 | Giá trị bất thường (VPB, TCB…) | Có thể là lỗi | **Chỉ cảnh báo, không tự sửa** – kiểm tra và giải thích nguyên nhân |

---

## 4. Chi tiết: dữ liệu đã được làm sạch như thế nào?

Dữ liệu đi qua 3 luồng xử lý song song rồi ghép lại:

```
BCTC + ratios (VNDirect) ──► Bảng 1: Tài chính quý ─────┐
Giá ngày (VNDirect)      ──► Bảng 2: Giá ngày + giá quý ─┼──► Bảng 4: Tổng hợp (160 dòng) ──► bàn giao
Tin CafeF + VNDirect     ──► Bảng 3: Sự kiện quý ────────┘
```

### 4.1. Bảng 1 – Dữ liệu tài chính (file `financials.py`)

**Bước 1 – Chọn đúng chỉ tiêu.** API trả hàng trăm chỉ tiêu, mỗi chỉ tiêu là một mã số. Pipeline chỉ lấy các mã cần thiết, cấu hình tập trung trong `config.py`:

| Mã | Tên cột | Ý nghĩa |
|---|---|---|
| 12700 | `tong_tai_san` | Tổng tài sản |
| 14000 | `von_chu_so_huu` | Vốn chủ sở hữu |
| 412100 | `tong_du_no` | Cho vay khách hàng (trước dự phòng) |
| 413300 | `tien_gui_khach_hang` | Tiền gửi khách hàng |
| 421900 | `thu_nhap_lai_thuan` | Thu nhập lãi thuần |
| 23003 | `loi_nhuan_sau_thue` | LNST |
| … | … | (xem Data Dictionary) |

**Bước 2 – Khử trùng lặp.** Khi ngân hàng công bố lại BCTC (soát xét, kiểm toán), cùng một chỉ tiêu có nhiều bản. Pipeline sắp xếp theo `modifiedDate` và **giữ bản cuối cùng** cho mỗi bộ (mã NH, kỳ, loại báo cáo, mã chỉ tiêu).

**Bước 3 – Chuyển dạng dài → rộng (pivot).** Mỗi dòng = 1 ngân hàng × 1 quý, mỗi cột = 1 chỉ tiêu. Nếu một chỉ tiêu không có trong nguồn, cột vẫn được tạo và để **trống (NaN)** – không bao giờ tự điền 0.

**Bước 4 – Chuẩn hóa đơn vị.** Tiền: VND ÷ 10⁹ → **tỷ đồng**. NPL, CAR từ VNDirect ở dạng thập phân (0,012) → × 100 → **%**.

**Bước 5 – Tự tính chỉ số (công thức minh bạch):**

| Chỉ số | Công thức | Ghi chú |
|---|---|---|
| ROA | LNST quý × 4 / bình quân(Tổng TS đầu & cuối quý) × 100 | Năm hóa |
| ROE | LNST quý × 4 / bình quân(VCSH đầu & cuối quý) × 100 | Năm hóa |
| NIM | Thu nhập lãi thuần × 4 / bình quân(TS sinh lãi) × 100 | TS sinh lãi = tiền gửi NHNN + tiền gửi/cho vay TCTD + CK kinh doanh + cho vay KH + CK đầu tư + mua nợ |
| LDR | Dư nợ / Tiền gửi KH × 100 | Tỷ lệ đơn giản |
| Nợ xấu | NPL × Dư nợ | **Ước tính**, không phải số công bố |

Vì sao lấy thêm dữ liệu Q4/2020? → Để có "số dư đầu kỳ" cho Q1/2021 khi tính bình quân.

**Bước 6 – Xử lý thiếu CAR (điểm quan trọng nhất).** VNDirect chỉ có CAR cuối năm → chỉ 32/160 ô có số thật. *(Cập nhật 03/10/2026: 6 số trong đó của BID, CTG 2022–2024 bị VNDirect ghi đúng 8,00 nên đã thay bằng số tra thủ công có link nguồn – `data/manual/car_tra_thu_cong.csv`, `car_nguon = tra_thu_cong`.)* Cách xử lý:

- Dùng **forward-fill theo từng ngân hàng**: quý chưa có số lấy giá trị **đã công bố gần nhất trước đó**.
- **Không dùng giá trị tương lai** (không backward-fill, không nội suy) → tránh rò rỉ thông tin cho mô hình dự báo.
- Thêm cột **`car_nguon`** = `cong_bo` (26 dòng), `tra_thu_cong` (6 dòng) hoặc `dien_tiep_ky_truoc` (128 dòng) để người phân tích biết ô nào là số thật. Với CH2 (kiểm định), nên **chỉ dùng dòng `cong_bo` và `tra_thu_cong`**.

**Bước 7 – Giữ cột đối chiếu.** Các cột `roa_ttm_vnd`, `roe_ttm_vnd`, `nim_ttm_vnd`, `ldr_vnd` (số VNDirect tự tính) được giữ lại để **kiểm tra chéo**, nhưng không đưa vào mô hình (tránh đa cộng tuyến).

### 4.2. Bảng 2 – Giá cổ phiếu (file `prices.py`)

**Vấn đề lớn nhất: giá chưa điều chỉnh.** Ngân hàng Việt Nam chia cổ tức bằng cổ phiếu gần như mỗi năm. Ví dụ chia 20% → giá trên bảng điện tự "rơi" ~17% vào ngày giao dịch không hưởng quyền, dù nhà đầu tư không hề lỗ. Nếu tính lợi suất bằng giá này → sai hoàn toàn.

→ Trong dữ liệu, **87,5% số phiên** có giá điều chỉnh khác giá chưa điều chỉnh – cho thấy vấn đề này rất phổ biến.

**Cách xử lý:**

1. Khử trùng lặp phiên (cùng mã, cùng ngày → giữ 1 dòng).
2. **Mọi phép tính lợi suất dùng giá đã điều chỉnh** (`adClose`, `adHigh`, `adLow`). Giá chưa điều chỉnh vẫn giữ để đối chiếu.
3. Gộp theo quý: giá cuối quý, giá max/min, số phiên, khối lượng bình quân…
4. **Giá đầu quý** = giá đóng cửa phiên cuối của quý trước, tra theo kỳ (Period + 1) chứ không dùng `shift()` → không bị lệch nếu thiếu một quý.
5. Lấy thêm giá từ 12/2020 → có giá đầu quý cho Q1/2021.

**Tạo biến mục tiêu `xu_huong_quy_sau` – chống rò rỉ dữ liệu:**

Sai lầm thường gặp: dùng BCTC quý t để dự đoán giá từ *cuối quý t*. Nhưng vào ngày cuối quý, **BCTC quý đó chưa được công bố** (hạn chót là 45 ngày sau, theo TT96/2020). Mô hình như vậy đang "nhìn trước tương lai".

Cách làm đúng:

```
Mốc dự báo quý t   = ngày cuối quý t   + 45 ngày   (BCTC quý t đã công bố)
Mốc dự báo quý t+1 = ngày cuối quý t+1 + 45 ngày

ty_suat_sinh_loi_quy_sau = giá(mốc t+1) / giá(mốc t) − 1
xu_huong_quy_sau         = 1 nếu > 0, ngược lại 0
```

- Giá tại mốc = giá đóng cửa điều chỉnh của **phiên gần nhất trước hoặc đúng ngày mốc** (`merge_asof`, hướng backward) → xử lý được mốc rơi vào cuối tuần/ngày lễ.
- Nếu mốc vượt quá dữ liệu giá đang có → để trống, không tạo nhãn giả.
- Vì vậy phải lấy giá đến **15/05/2026** để có nhãn cho Q4/2025.
- **Kiểm chứng:** ngày VNDirect nhập BCTC trễ trung vị 29 ngày, muộn nhất 39 ngày → **0 kỳ** BCTC nhập sau mốc 45 ngày. Mốc chọn là an toàn.

Kết quả: 160/160 dòng có nhãn; **90 tăng (56,2%) / 70 không tăng** → khá cân bằng, phù hợp cho Logistic Regression.

### 4.3. Bảng 3 – Sự kiện phi tài chính (file `events.py`)

Đây là phần "bẩn" nhất: từ **5.636 tin thô** phải lọc ra những sự kiện thật sự có ý nghĩa. Quy trình gồm 6 tầng lọc:

```
5.636 tin thô
  │ ① Loại tin thường quy (BCTC, họp ĐHCĐ, giao dịch cổ đông, trái phiếu…)
  │ ② Phân loại theo từ khóa (6 nhóm)             → 322 tin được phân loại
  │ ③ Loại tin sai mã / tin toàn ngành            → 103 tin bị gắn cờ
  │ ④ Rà soát thủ công (loại/sửa/bổ sung)          → 310 tin giữ lại
  │ ⑤ Gộp tin trùng                                → 290 tin gộp thành
  ▼
121 sự kiện  ──⑥ Tổng hợp theo quý──►  160 dòng (88 quý có sự kiện, 72 quý không)
```

**① Loại tin thường quy.** Trước khi phân loại, các tin có tiêu đề chứa những cụm như "báo cáo tài chính", "giải trình", "người nội bộ", "chốt danh sách", "trái phiếu", "chi nhánh", "niêm yết bổ sung", "lưu ký"… bị loại. Đây là tin hành chính định kỳ, không phải sự kiện.

**② Phân loại bằng quy tắc từ khóa.** Mỗi nhóm có 3 loại mẫu (regex):

- `any` – khớp ít nhất 1 mẫu thì là ứng viên;
- `require` – phải khớp thêm mẫu này (vd đổi lãnh đạo phải nhắc "chủ tịch/tổng giám đốc/HĐQT");
- `deny` – khớp thì **không** thuộc nhóm (vd "phó tổng giám đốc", "bổ nhiệm lại", tin về công ty con).

Các nhóm xét theo thứ tự ưu tiên: tăng vốn → đổi lãnh đạo → khác (M&A) → chính sách NHNN → hợp tác/trúng thầu → chuyển đổi số. Mẫu được viết để bắt cả hai kiểu bỏ dấu tiếng Việt (hóa/hoá, hủy/huỷ).

Ví dụ xử lý tinh tế:
- "Giải tỏa hạn chế chuyển nhượng ESOP" → **không** phải tăng vốn (chỉ là thủ tục).
- "Thông báo UBCKNN nhận đủ hồ sơ tăng vốn" → **không** đếm là sự kiện mới (giấy tờ của đợt tăng vốn đã có).
- "Chứng khoán ACB tăng vốn" → **loại** (công ty con, không phải chính ngân hàng).

**③ Loại tin không đúng ngân hàng.** Gắn cờ `tin_nganh_hoac_sai_ma` khi:
- Tiêu đề dạng `XXX: …` nhưng XXX là mã khác (CafeF đôi khi gắn nhầm mã);
- Tin nhắc tới **≥ 3 ngân hàng** → tin tổng hợp toàn ngành, không gán cho riêng ai.

Với tin VNDirect, chỉ giữ tin mà **tiêu đề** nhắc tên ngân hàng (vì tagCodes thường gắn nhiều mã).

**④ Rà soát thủ công** (trong `data/manual/`), áp dụng trên **từng tin thô, trước khi gộp** – để loại 1 tin không kéo theo các tin hợp lệ cùng cụm:

| File | Số dòng | Tác dụng | Ví dụ |
|---|---|---|---|
| `su_kien_loai_bo.csv` | 63 (khớp 74 tin) | Bỏ tin phân loại sai | Bài PR/phỏng vấn/giải thưởng bị nhận nhầm là "chuyển đổi số" |
| `su_kien_sua_loai.csv` | 7 (khớp 10 tin) | Sửa loại sự kiện | Nghị quyết VPB ký với SMBC → sửa thành **tăng vốn** (SMBC mua cổ phần riêng lẻ) |
| `su_kien_bo_sung.csv` | 1 | Thêm sự kiện bị sót | ACB ra mắt ngân hàng số ACB ONE (14/02/2022) |

Mỗi dòng đều có cột **`ly_do`** giải thích → minh bạch, có thể kiểm chứng. Giá trị loại sự kiện không hợp lệ bị loại kèm cảnh báo.

**⑤ Gộp tin trùng.** Một sự kiện thật thường sinh ra nhiều tin (nghị quyết → thông báo → kết quả…):
- Cùng ngân hàng, cùng tiêu đề, cùng ngày → giữ 1.
- Cùng ngân hàng, cùng loại, cách nhau **≤ 3 ngày** → 1 sự kiện.
- Riêng **tăng vốn: tối đa 1 lần/quý** (cả đợt tăng vốn chỉ là 1 sự kiện).
- Giữ tin **sớm nhất** làm đại diện (ngày thị trường biết tin đầu tiên); link các tin còn lại lưu ở `nguon_khac`, số tin gộp ở `so_tin_gop`.

→ 290 tin gộp thành **121 sự kiện**.

**⑥ Tổng hợp theo quý.** Tạo lưới đủ 8 NH × 20 quý rồi ghép sự kiện vào:
- `co_su_kien` (0/1), `so_luong_su_kien`, `sk_<loại>` (đếm theo loại; riêng `sk_tang_von` là 0/1).
- **Quý không có sự kiện → ghi 0** (đây là thông tin thật "không có sự kiện", khác với "thiếu dữ liệu").
- Các cột mô tả (`mo_ta_ngan`, `nguon`…) để trống khi không có sự kiện – **72 ô trống hợp lệ**.

Phân bố 121 sự kiện: tăng vốn 61, đổi lãnh đạo 33, hợp tác/trúng thầu 15, khác (M&A) 6, chuyển đổi số 4, chính sách NHNN 2.

### 4.4. Bảng 4 – Ghép và bàn giao (file `build.py`)

- Lấy lưới 160 dòng làm khung, **left join** Bảng 1 + Bảng 2b + Bảng 3b theo khóa `ma_nh + quy + nam` → không mất dòng nào kể cả khi một nguồn thiếu.
- Sắp xếp đúng thứ tự thời gian (Q1 < Q2 < Q3 < Q4).
- Làm tròn 4 chữ số, xuất CSV mã hóa **UTF-8-BOM** (Excel hiển thị đúng tiếng Việt) và file `.xlsx`.
- Kết quả: **160 dòng × 56 cột**.

### 4.5. Quy ước dữ liệu thiếu (áp dụng toàn bộ)

| Trường hợp | Cách ghi | Lý do |
|---|---|---|
| Biến tài chính / giá không có trong nguồn | **Để trống (NaN)** | Điền 0 sẽ làm sai thống kê (ROA = 0 khác với "không biết ROA") |
| CAR giữa các kỳ công bố | Điền tiếp số gần nhất + đánh dấu `car_nguon` | Là số "đang có hiệu lực" tại thời điểm đó, không dùng tương lai |
| Quý không có sự kiện | **0** | "Không có sự kiện" là thông tin thật |
| Cột mô tả sự kiện khi không có sự kiện | Để trống | Hợp lệ, không phải thiếu |

---

## 5. Kiểm tra chất lượng sau làm sạch (`bao_cao_kiem_tra.md`)

Pipeline tự sinh báo cáo kiểm tra mỗi lần chạy:

| Kiểm tra | Kết quả |
|---|---|
| Số dòng Bảng 4 | **160 / 160** kỳ vọng ✔ |
| Độ phủ: mỗi NH có BCTC, giá, NPL | **20/20 quý** cho cả 8 NH ✔ |
| Ô thiếu ở biến số (tài chính, giá, sự kiện, nhãn) | **0** ✔ |
| Tổng LNST 4 quý so với BCTC năm | **Tất cả lệch ≤ 2%** ✔ (chứng tỏ số quý không bị lũy kế nhầm) |
| NIM tự tính vs NIM VNDirect | Lệch trung vị 0,33 điểm % (do khác phương pháp: 1 quý năm hóa vs 4 quý) ✔ |
| Quý có ít phiên giao dịch (< 50) | Không có ✔ |
| BCTC công bố sau mốc dự báo 45 ngày | **0 kỳ** ✔ |
| Dòng thiếu nhãn | **0** ✔ |

**Giá trị ngoài khoảng hợp lý – chỉ cảnh báo, KHÔNG tự sửa.** Đã kiểm tra và đều có lý do kinh doanh thật:

| Trường hợp | Giải thích |
|---|---|
| VPB: LDR 130–153% (nhiều quý) | Hợp nhất FE Credit (cho vay tiêu dùng) – dư nợ lớn so với tiền gửi; LDR ở đây là tỷ lệ đơn giản, khác LDR theo quy định NHNN |
| VPB Q1–Q2/2021: NIM ≈ 9% | Cũng do FE Credit (lãi suất cho vay tiêu dùng cao) |
| VPB Q1/2022: ROA 6,4% | Lợi nhuận đột biến trong quý (nhiều khả năng do ghi nhận phí trả trước hợp đồng bancassurance – nên kiểm chứng lại trên BCTC), bị phóng đại khi năm hóa × 4 |
| TCB Q2/2025: LDR 130,3% | Vượt ngưỡng rất nhẹ |

→ Đây là **ngoại lai thật (true outlier)**, không phải lỗi, nên giữ nguyên. Người phân tích cần lưu ý khi chạy K-Means (nên chuẩn hóa) và khi diễn giải.

---

## 6. Hạn chế còn lại (nên ghi vào báo cáo)

1. **CAR** chỉ có 32 số thật (26 từ VNDirect, 6 tra thủ công); phần còn lại là điền tiếp. Năm 2025 dùng số 2024 (một số ngân hàng đã đổi cách tính CAR theo Thông tư 14/2025).
2. **ROA/ROE/NIM** năm hóa từ 1 quý nên dao động mạnh hơn số TTM.
3. **Nợ xấu (`no_xau`)** là số ước tính (NPL × dư nợ).
4. **Tin hợp tác / chuyển đổi số 2021–2024 có thể bị thiếu** vì CafeF chủ yếu đăng công bố thông tin chính thức. Thử nghiệm Vietstock tìm thêm được ~80 sự kiện tiềm năng (chủ yếu hợp tác và chuyển đổi số) – cần rà soát trước khi đưa vào.
5. Phân loại sự kiện dựa trên **tiêu đề**, không đọc nội dung bài → vẫn có thể sót/nhầm.
6. VNDirect chỉ lưu **bản BCTC sau cùng** (đã kiểm toán), không có bản công bố ban đầu.
7. API VNDirect là API công khai **không có tài liệu chính thức** – cấu trúc có thể thay đổi.
8. Mẫu nhỏ: chỉ 3 NH quốc doanh vs 5 tư nhân; các quý của cùng 1 NH không độc lập → cần lưu ý khi kiểm định (CH2).

---

## 7. Lưu ý khi bàn giao cho Nghi & Quân

- **Không dùng `ty_suat_sinh_loi_quy_sau` làm biến đầu vào** – nhãn được tạo trực tiếp từ cột này (rò rỉ 100%).
- **Chia train/test theo thời gian**, không chia ngẫu nhiên.
- Nếu dùng `car` làm đầu vào dự báo: dòng Q4 nên lấy `car` của Q3 cùng năm (CAR năm công bố sau mốc dự báo Q4).
- Các biến `sk_chuyen_doi_so`, `sk_chinh_sach_nhnn`, `sk_khac` rất hiếm (≤ 6 lần) → nên dùng `co_su_kien` / `so_luong_su_kien` thay vì ước lượng hệ số riêng.
- Không đưa các cột `*_ttm_vnd` cùng lúc với cột tự tính vào mô hình.
- Chuẩn hóa (StandardScaler) trước K-Means/PCA vì quy mô các ngân hàng chênh nhau nhiều.

---

## 8. Tóm tắt một câu

Đây là bài toán **phân tích tài chính + phân loại xu hướng giá + phân cụm** cho 8 ngân hàng niêm yết; dữ liệu **lấy được đầy đủ** từ API VNDirect và CafeF, và đã được **làm sạch qua 3 luồng** (tài chính – giá – sự kiện) với các kỹ thuật chính: khử trùng lặp, chuẩn hóa đơn vị, tự tính chỉ số, forward-fill có đánh dấu cho CAR, dùng giá điều chỉnh, căn thời điểm nhãn để chống rò rỉ, lọc – phân loại – gộp – rà soát thủ công tin tức, và kiểm tra chất lượng tự động – cho ra bộ dữ liệu **160 dòng × 56 cột, không thiếu ô nào ở biến số**.
