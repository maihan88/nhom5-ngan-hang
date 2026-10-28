# Data Dictionary – Bộ dữ liệu Nhóm 5 PTDL

Bản đầy đủ (mọi cột của mọi file, kèm vai trò, dùng cho câu hỏi nào, lưu ý và thống kê nhanh: số ô trống, nhỏ nhất, lớn nhất, trung bình, ví dụ) nằm trong `data_dictionary.csv`. CH1..CH5 = 5 câu hỏi nghiên cứu trong đề xuất.

**Quy ước dữ liệu thiếu:** ô trống (NaN) = không có dữ liệu từ nguồn; KHÔNG tự điền 0 cho biến tài chính/giá. Riêng biến sự kiện: quý không tìm thấy sự kiện = 0.

**Khóa nối bảng:** `ma_nh` + `quy` + `nam`. Mỗi dòng Bảng 4 = 1 ngân hàng × 1 quý.

**Các cột mô tả sự kiện** (`loai_su_kien`, `ngay_cong_bo`, `mo_ta_ngan`, `nguon`) để trống khi quý đó không có sự kiện (`co_su_kien = 0`). Đây là ô trống hợp lệ, không phải thiếu dữ liệu.

**Lưu ý khi dùng cho mô hình (câu hỏi 4):**
- **Nhãn, KHÔNG được dùng làm biến đầu vào:** `xu_huong_quy_sau` (nhãn) và `ty_suat_sinh_loi_quy_sau` (nhãn được tạo trực tiếp từ cột này; dùng làm đầu vào là rò rỉ dữ liệu 100%).
- **Chỉ để đối chiếu, trùng thông tin với cột chính:** `roa_ttm_vnd`, `roe_ttm_vnd`, `nim_ttm_vnd`, `ldr_vnd`.
- **Cột mô tả, không phải biến số:** `ngay_bctc`, `ngay_dau`, `ngay_cuoi`, `car_nguon`, `loai_su_kien`, `ngay_cong_bo`, `mo_ta_ngan`, `nguon`.
- **Nhãn đã căn thời điểm:** nhãn tính từ mốc dự báo (cuối quý + 45 ngày), sau khi BCTC quý đã công bố, nên các biến tài chính và sự kiện của quý t đều đã biết tại mốc dự báo.
- **Riêng `car`:** CAR năm Y chỉ công bố cùng báo cáo năm, sau mốc dự báo của Q4/Y. Nếu dùng `car` làm biến đầu vào dự báo, dòng Q4 phải lấy giá trị `car` của dòng Q3 cùng năm.
- **Chia train/test theo thời gian:** nhãn của quý t đã có vào đúng mốc dự báo của quý t+1, nên khi kiểm tra quý t có thể huấn luyện bằng mọi quý trước đó mà không nhìn trước tương lai.
- **Hạn chế:** VNDirect chỉ lưu bản số liệu BCTC sau cùng (đã soát xét/kiểm toán). Không có bản công bố ban đầu nên không đo được mức điều chỉnh so với số liệu thị trường biết tại mốc dự báo.

## Bảng 1 – Tài chính quý (`bang1_tai_chinh_quy.csv`)

| Cột | Mô tả | Đơn vị | Nguồn / Công thức | Vai trò |
|---|---|---|---|---|
| `ma_nh` | Mã cổ phiếu ngân hàng | - | VCB, BID, CTG, TCB, MBB, ACB, STB, VPB | Khóa nối bảng |
| `quy` | Quý | - | Q1..Q4 | Khóa nối bảng |
| `nam` | Năm | - | 2021..2025 | Khóa nối bảng |
| `ngay_bctc` | Ngày kết thúc kỳ BCTC | yyyy-mm-dd | VNDirect financial_statements | Mô tả / truy vết |
| `loai_hinh_so_huu` | Loại hình sở hữu | - | Quốc doanh (VCB, BID, CTG) / Tư nhân (còn lại) | Biến nhóm |
| `tong_tai_san` | Tổng tài sản cuối quý | tỷ đồng | BCĐKT – TỔNG CỘNG TÀI SẢN (mã 12700) | Số liệu gốc |
| `von_chu_so_huu` | Vốn chủ sở hữu cuối quý | tỷ đồng | BCĐKT – Vốn chủ sở hữu (mã 14000) | Số liệu gốc |
| `loi_nhuan_sau_thue` | LNST trong quý (hợp nhất) | tỷ đồng | KQKD – LNST TNDN (mã 23003), số phát sinh trong quý | Số liệu gốc |
| `tong_du_no` | Dư nợ cho vay khách hàng (gộp, trước dự phòng) | tỷ đồng | BCĐKT mã 412100 | Số liệu gốc |
| `no_xau` | Nợ xấu (ƯỚC TÍNH) | tỷ đồng | npl/100 × tong_du_no | Số liệu gốc (ước tính) |
| `roa` | ROA năm hóa | % | LNST quý × 4 / bình quân(Tổng TS đầu quý, cuối quý) × 100 | Biến phân tích chính |
| `roe` | ROE năm hóa | % | LNST quý × 4 / bình quân(VCSH đầu quý, cuối quý) × 100 | Biến phân tích chính |
| `nim` | NIM năm hóa | % | Thu nhập lãi thuần quý × 4 / bình quân(TS sinh lãi đầu, cuối quý) × 100 | Biến phân tích chính |
| `npl` | Tỷ lệ nợ xấu (nhóm 3–5 / tổng dư nợ) | % | VNDirect ratio BAD_LOANS_RATIO_AQ (tổng hợp từ thuyết minh BCTC) | Biến phân tích chính |
| `car` | Hệ số an toàn vốn | % | VNDirect ratio BANK_CAR_AQ. **VNDirect chỉ có 1 số/năm (cuối năm)**; riêng BID, CTG 2022–2024 (VNDirect ghi đúng 8,00) được thay bằng số tra thủ công có link nguồn trong `data/manual/car_tra_thu_cong.csv`. Các quý khác (kể cả năm chưa có số) được điền bằng số thật gần nhất trước đó. Xem cột `car_nguon` và báo cáo kiểm tra | Biến phân tích chính |
| `car_nguon` | Cách có giá trị CAR | - | cong_bo = số VNDirect đúng kỳ; tra_thu_cong = số nhóm tự tra từ nguồn ngân hàng / công ty chứng khoán (xem data/manual/car_tra_thu_cong.csv); dien_tiep_ky_truoc = điền tiếp số thật gần nhất | Mô tả / truy vết |
| `ldr` | Tỷ lệ cho vay / tiền gửi KH (hệ số thanh khoản) | % | tong_du_no / tien_gui_khach_hang × 100 | Biến phân tích chính |
| `lnst_cong_ty_me` | LNST của cổ đông công ty mẹ trong quý | tỷ đồng | KQKD mã 23000 | Số liệu gốc |
| `loi_nhuan_truoc_thue` | Lợi nhuận trước thuế trong quý | tỷ đồng | KQKD mã 23800 | Số liệu gốc |
| `thu_nhap_lai_thuan` | Thu nhập lãi thuần trong quý | tỷ đồng | KQKD mã 421900 | Số liệu gốc |
| `tong_thu_nhap_hoat_dong` | Tổng thu nhập hoạt động trong quý | tỷ đồng | KQKD mã 421701 | Số liệu gốc |
| `chi_phi_hoat_dong` | Chi phí hoạt động (quản lý) trong quý | tỷ đồng | KQKD mã 22200 | Số liệu gốc |
| `chi_phi_du_phong` | Chi phí dự phòng rủi ro tín dụng trong quý | tỷ đồng | KQKD mã 422900 | Số liệu gốc |
| `tien_gui_khach_hang` | Tiền gửi của khách hàng | tỷ đồng | BCĐKT mã 413300 | Số liệu gốc |
| `du_phong_cho_vay` | Dự phòng rủi ro cho vay KH (số âm) | tỷ đồng | BCĐKT mã 412200 | Số liệu gốc |
| `earning_assets` | Tài sản sinh lãi cuối quý | tỷ đồng | Tiền gửi NHNN + Tiền gửi & cho vay TCTD + CK kinh doanh + Cho vay KH + CK đầu tư + Mua nợ | Thành phần tính toán |
| `roa_ttm_vnd` | ROAA 4 quý gần nhất (VNDirect, đối chiếu) | % | VNDirect ROAA_TR_AVG5Q | Chỉ để đối chiếu |
| `roe_ttm_vnd` | ROAE 4 quý gần nhất (VNDirect, đối chiếu) | % | VNDirect ROAE_TR_AVG5Q | Chỉ để đối chiếu |
| `nim_ttm_vnd` | NIM 4 quý gần nhất (VNDirect, đối chiếu) | % | VNDirect NET_INTEREST_MARGIN_TR_AVG5Q | Chỉ để đối chiếu |
| `ldr_vnd` | LDR (VNDirect, đối chiếu) | % | VNDirect LOANS_TO_DEPOSIT_AQ | Chỉ để đối chiếu |

## Bảng 2a – Giá ngày (`bang2a_gia_ngay.csv`)

| Cột | Mô tả | Đơn vị | Nguồn / Công thức | Vai trò |
|---|---|---|---|---|
| `ma_nh` | Mã cổ phiếu ngân hàng | - | VCB, BID, CTG, TCB, MBB, ACB, STB, VPB | Khóa nối bảng |
| `ngay` | Ngày giao dịch (bảng giá ngày) | yyyy-mm-dd | VNDirect stock_prices, từ 2020-12-01 đến 2026-05-15. Các phiên ngoài 2021–2025 chỉ dùng để tính giá đầu quý Q1/2021 và nhãn quý sau; khi vẽ biểu đồ nên lọc theo giai đoạn nghiên cứu | Khóa nối bảng |
| `gia_dong_cua` | Giá đóng cửa chưa điều chỉnh (bảng giá ngày) | nghìn đồng | close | Chỉ để đối chiếu |
| `gia_dong_cua_dieu_chinh` | Giá đóng cửa đã điều chỉnh (bảng giá ngày) | nghìn đồng | adClose | Dữ liệu giá |
| `gia_mo_cua_dieu_chinh` | Giá mở cửa đã điều chỉnh (bảng giá ngày) | nghìn đồng | adOpen | Dữ liệu giá |
| `gia_cao_nhat_dieu_chinh` | Giá cao nhất trong phiên, đã điều chỉnh (bảng giá ngày) | nghìn đồng | adHigh | Dữ liệu giá |
| `gia_thap_nhat_dieu_chinh` | Giá thấp nhất trong phiên, đã điều chỉnh (bảng giá ngày) | nghìn đồng | adLow | Dữ liệu giá |
| `khoi_luong_gd` | Khối lượng khớp lệnh (bảng giá ngày) | cổ phiếu | nmVolume | Dữ liệu giá |
| `khoi_luong_thoa_thuan` | Khối lượng giao dịch thỏa thuận (bảng giá ngày) | cổ phiếu | ptVolume | Dữ liệu giá |
| `gia_tri_gd_ty` | Giá trị giao dịch khớp lệnh (bảng giá ngày) | tỷ đồng | nmValue / 1e9 | Dữ liệu giá |

## Bảng 2b – Giá quý (`bang2b_gia_quy.csv`)

| Cột | Mô tả | Đơn vị | Nguồn / Công thức | Vai trò |
|---|---|---|---|---|
| `ma_nh` | Mã cổ phiếu ngân hàng | - | VCB, BID, CTG, TCB, MBB, ACB, STB, VPB | Khóa nối bảng |
| `quy` | Quý | - | Q1..Q4 | Khóa nối bảng |
| `nam` | Năm | - | 2021..2025 | Khóa nối bảng |
| `ngay_dau` | Phiên giao dịch đầu tiên của quý | yyyy-mm-dd |  | Mô tả / truy vết |
| `ngay_cuoi` | Phiên giao dịch cuối cùng của quý | yyyy-mm-dd |  | Mô tả / truy vết |
| `so_phien_gd` | Số phiên giao dịch trong quý | phiên |  | Mô tả / truy vết |
| `gia_dau_quy` | Giá đầu quý (điều chỉnh) | nghìn đồng | Giá đóng cửa điều chỉnh phiên cuối của quý trước | Thành phần tính toán |
| `gia_cuoi_quy` | Giá cuối quý (điều chỉnh) | nghìn đồng | Giá đóng cửa điều chỉnh phiên cuối của quý | Thành phần tính toán |
| `gia_cuoi_quy_chua_dieu_chinh` | Giá cuối quý chưa điều chỉnh | nghìn đồng | close phiên cuối quý | Chỉ để đối chiếu |
| `ty_suat_sinh_loi_quy` | Tỷ suất sinh lời cổ phiếu trong quý | % | (gia_cuoi_quy / gia_dau_quy − 1) × 100 | Biến phân tích chính |
| `bien_dong_gia_max_min` | Biên độ dao động giá trong quý | % | (giá cao nhất − giá thấp nhất) / giá thấp nhất × 100, giá điều chỉnh | Biến bổ sung |
| `gia_max` | Giá cao nhất trong quý (điều chỉnh) | nghìn đồng | max adHigh | Biến bổ sung |
| `gia_min` | Giá thấp nhất trong quý (điều chỉnh) | nghìn đồng | min adLow | Biến bổ sung |
| `kl_gd_tb_phien` | KL khớp lệnh bình quân phiên | cổ phiếu |  | Biến bổ sung |
| `tong_kl_gd_quy` | Tổng KL khớp lệnh trong quý | cổ phiếu |  | Biến bổ sung |
| `ty_suat_sinh_loi_quy_sau` | Tỷ suất sinh lời kỳ tiếp theo, tính từ MỐC DỰ BÁO | % | Mốc dự báo của quý t = ngày cuối quý t + 45 ngày (khi BCTC quý t đã công bố). Lợi suất = giá tại mốc của quý t+1 / giá tại mốc của quý t − 1, × 100; giá tại mốc = giá đóng cửa điều chỉnh của phiên cuối cùng trước hoặc đúng ngày mốc. KHÁC `ty_suat_sinh_loi_quy` của quý sau (tính theo quý lịch). Giá dùng tính nhãn có đủ trong `bang2a_gia_ngay` (đến 2026-05-15). **Không dùng làm biến đầu vào** | Nguồn của nhãn |
| `xu_huong_quy_sau` | Biến mục tiêu: giá kỳ tiếp theo (từ mốc dự báo) tăng? | 0/1 | 1 nếu ty_suat_sinh_loi_quy_sau > 0, ngược lại 0 | Biến mục tiêu (nhãn) |

## Bảng 3a – Sự kiện chi tiết (`bang3a_su_kien_chi_tiet.csv`)

| Cột | Mô tả | Đơn vị | Nguồn / Công thức | Vai trò |
|---|---|---|---|---|
| `ma_nh` | Mã cổ phiếu ngân hàng | - | VCB, BID, CTG, TCB, MBB, ACB, STB, VPB | Khóa nối bảng |
| `quy` | Quý của ngày công bố sự kiện | - | Q1..Q4 | Khóa nối bảng |
| `nam` | Năm của ngày công bố sự kiện | - | 2021..2025 | Khóa nối bảng |
| `ngay_cong_bo` | Ngày giờ đăng tin đầu tiên của sự kiện | yyyy-mm-dd HH:MM | Tin sớm nhất trong cụm tin đã gộp; 00:00 = nguồn chỉ ghi ngày, không ghi giờ | Mô tả / truy vết |
| `loai_su_kien` | Mã loại sự kiện | - | tang_von / chuyen_doi_so / hop_tac_trung_thau / doi_lanh_dao / chinh_sach_nhnn / khac. Phân loại bằng từ khóa trên tiêu đề + rà soát thủ công (data/manual) | Mô tả / truy vết |
| `loai_su_kien_nhan` | Tên loại sự kiện (tiếng Việt) | - | Tăng vốn; Chuyển đổi số - tiền số; Hợp tác chiến lược - trúng thầu; Đổi lãnh đạo; Chính sách NHNN; Khác | Mô tả / truy vết |
| `mo_ta_ngan` | Tiêu đề tin đại diện của sự kiện | - | Tin sớm nhất trong cụm | Mô tả / truy vết |
| `nguon` | Link tin đại diện | URL |  | Mô tả / truy vết |
| `nguon_du_lieu` | Nguồn của tin đại diện | - | CafeF / VNDirect-news/<tên báo> / VNDirect-events (sự kiện quyền) / Bổ sung thủ công | Mô tả / truy vết |
| `so_tin_gop` | Số tin thô được gộp thành sự kiện này | tin | Cùng NH, cùng loại, cách nhau ≤ 3 ngày; riêng tăng vốn: cùng quý | Mô tả / truy vết |
| `nguon_khac` | Link các tin còn lại trong cụm (cách nhau bởi ;) | URL | Để truy vết; trống nếu so_tin_gop = 1 | Mô tả / truy vết |

## Bảng 3b – Sự kiện quý (`bang3b_su_kien_quy.csv`)

| Cột | Mô tả | Đơn vị | Nguồn / Công thức | Vai trò |
|---|---|---|---|---|
| `ma_nh` | Mã cổ phiếu ngân hàng | - | VCB, BID, CTG, TCB, MBB, ACB, STB, VPB | Khóa nối bảng |
| `quy` | Quý | - | Q1..Q4 | Khóa nối bảng |
| `nam` | Năm | - | 2021..2025 | Khóa nối bảng |
| `co_su_kien` | Có sự kiện phi tài chính đáng chú ý trong quý | 0/1 | 1 nếu so_luong_su_kien > 0 | Biến phân tích chính |
| `so_luong_su_kien` | Số sự kiện trong quý (sau khi gộp tin trùng) | sự kiện | Tin cùng loại cách nhau ≤ 3 ngày tính là 1; riêng tăng vốn tính tối đa 1 lần/quý | Biến phân tích chính |
| `loai_su_kien` | Các loại sự kiện trong quý | - | Tăng vốn; Chuyển đổi số - tiền số; Hợp tác chiến lược - trúng thầu; Đổi lãnh đạo; Chính sách NHNN; Khác | Mô tả / truy vết |
| `sk_tang_von` | Có sự kiện loại 'Tăng vốn' trong quý hay không | 0/1 | Mọi thông báo của cùng một đợt tăng vốn trong quý (nghị quyết, phát hành, kết quả…) gộp làm 1, nên cột này là biến có/không, KHÔNG phải số đợt tăng vốn | Biến phân tích chính |
| `sk_chuyen_doi_so` | Số sự kiện loại 'Chuyển đổi số - tiền số' trong quý | sự kiện | dùng làm biến giả/biến đếm theo nhóm | Biến phân tích (hiếm) |
| `sk_hop_tac_trung_thau` | Số sự kiện loại 'Hợp tác chiến lược - trúng thầu' trong quý | sự kiện | dùng làm biến giả/biến đếm theo nhóm | Biến phân tích chính |
| `sk_doi_lanh_dao` | Số sự kiện loại 'Đổi lãnh đạo' trong quý | sự kiện | dùng làm biến giả/biến đếm theo nhóm | Biến phân tích chính |
| `sk_chinh_sach_nhnn` | Số sự kiện loại 'Chính sách NHNN' trong quý | sự kiện | dùng làm biến giả/biến đếm theo nhóm | Biến phân tích (hiếm) |
| `sk_khac` | Số sự kiện loại 'Khác' trong quý | sự kiện | dùng làm biến giả/biến đếm theo nhóm | Biến phân tích (hiếm) |
| `ngay_cong_bo` | Ngày công bố từng sự kiện (cách nhau bởi ;) | yyyy-mm-dd |  | Mô tả / truy vết |
| `mo_ta_ngan` | Tiêu đề/tóm tắt từng sự kiện (cách nhau bởi \|) | - |  | Mô tả / truy vết |
| `nguon` | Link nguồn từng sự kiện (cách nhau bởi ;) | URL | CafeF / VNDirect | Mô tả / truy vết |

## Bảng 4 – Tổng hợp (bàn giao) (`bang4_tong_hop.csv`)

Ghép Bảng 1 + Bảng 2b + Bảng 3b theo `ma_nh` + `quy` + `nam`: 56 cột, mỗi dòng = 1 ngân hàng × 1 quý. Ý nghĩa từng cột giống ở bảng gốc phía trên; cột `lay_tu_bang` trong `data_dictionary.csv` cho biết cột lấy từ bảng nào.
