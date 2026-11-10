# Mô tả dữ liệu trong `data/output`

Phạm vi: 8 ngân hàng, từ Q1/2021 đến Q2/2026 (176 ngân hàng × quý). Mỗi bảng chỉ giữ các cột phục vụ 5 câu hỏi nghiên cứu, nguyên liệu để tính chỉ số, cột đối chiếu hoặc cột truy vết; các chỉ tiêu BCTC khác vẫn còn nguyên trong `data/raw/`.

| Mã | Ngân hàng | Loại hình |
|---|---|---|
| VCB | Vietcombank | Quốc doanh |
| BID | BIDV | Quốc doanh |
| CTG | VietinBank | Quốc doanh |
| TCB | Techcombank | Tư nhân |
| MBB | MB | Tư nhân |
| ACB | ACB | Tư nhân |
| STB | Sacombank | Tư nhân |
| VPB | VPBank | Tư nhân |

**Quy ước chung**

- Nối các bảng bằng 3 cột `ma_nh` + `quy` + `nam`. Riêng bảng giá ngày nối bằng `ma_nh` + `ngay`.
- Đơn vị: tiền là **tỷ đồng**, giá cổ phiếu là **nghìn đồng**, tỷ lệ là **%**.
- Ô trống nghĩa là nguồn không có số liệu, không tự điền 0. Riêng các cột mô tả sự kiện trống khi quý đó không có sự kiện.
- File `.xlsx` cùng tên có nội dung giống file `.csv`.

## Tổng quan các file

| File | Mỗi dòng là | Số dòng × cột | Dùng để |
|---|---|---|---|
| `bang1_tai_chinh_quy.csv` | 1 ngân hàng × 1 quý | 176 × 22 | Xem sức khỏe tài chính |
| `bang2a_gia_ngay.csv` | 1 cổ phiếu × 1 phiên giao dịch | 11.771 × 7 | Vẽ biểu đồ giá |
| `bang2b_gia_quy.csv` | 1 cổ phiếu × 1 quý | 176 × 12 | Xem giá tăng/giảm trong quý, nhãn dự báo |
| `bang3a_su_kien_chi_tiet.csv` | 1 sự kiện | 146 × 11 | Xem từng sự kiện kèm link tin |
| `bang3b_su_kien_quy.csv` | 1 ngân hàng × 1 quý | 176 × 15 | Đếm sự kiện theo quý |
| `bang4_tong_hop.csv` | 1 ngân hàng × 1 quý | 176 × 43 | **File bàn giao chính**: ghép bảng 1 + 2b + 3b |

---

## 1. `bang1_tai_chinh_quy.csv` – Sức khỏe tài chính từng quý

Mỗi dòng là kết quả tài chính của 1 ngân hàng trong 1 quý, lấy từ báo cáo tài chính (BCTC) quý hợp nhất.

**Nhận diện**

| Cột | Ý nghĩa |
|---|---|
| `ma_nh` | Mã cổ phiếu của ngân hàng (xem bảng đầu trang) |
| `quy`, `nam` | Quý (Q1–Q4) và năm của số liệu |
| `ngay_bctc` | Ngày chốt số liệu của báo cáo, tức ngày cuối quý |
| `loai_hinh_so_huu` | Quốc doanh (Nhà nước chi phối) hay Tư nhân |

**Số liệu gốc để tính chỉ số** (tỷ đồng)

| Cột | Ý nghĩa |
|---|---|
| `tong_tai_san` | Tổng tài sản cuối quý, mẫu số của ROA |
| `von_chu_so_huu` | Vốn của cổ đông cuối quý, mẫu số của ROE |
| `tong_du_no` | Tổng tiền đang cho khách hàng vay, chưa trừ dự phòng. Tử số của LDR, một phần tài sản sinh lãi |
| `tien_gui_khach_hang` | Tổng tiền khách hàng đang gửi tại ngân hàng, mẫu số của LDR |
| `loi_nhuan_sau_thue` | Lãi ròng trong quý, sau thuế, gồm cả công ty con. Tử số của ROA, ROE; dùng đối chiếu với LNST năm trên BCTC |
| `thu_nhap_lai_thuan` | Lãi thu từ cho vay và đầu tư, trừ đi lãi trả cho người gửi. Tử số của NIM |
| `tai_san_sinh_lai` | Tài sản sinh lãi (cho vay, tiền gửi ở ngân hàng khác, chứng khoán…), dùng để tính NIM |

**Chỉ số tài chính** (%)

| Cột | Ý nghĩa |
|---|---|
| `roa` | Lợi nhuận trên tổng tài sản: 100 đồng tài sản sinh ra bao nhiêu đồng lãi mỗi năm. Đo hiệu quả dùng tài sản |
| `roe` | Lợi nhuận trên vốn chủ sở hữu: 100 đồng vốn cổ đông sinh ra bao nhiêu đồng lãi mỗi năm. Đo khả năng sinh lời cho cổ đông |
| `nim` | Biên lãi thuần: phần chênh lệch lãi suất ngân hàng thu được, tính theo % tài sản sinh lãi |
| `npl` | Tỷ lệ nợ xấu: bao nhiêu % dư nợ là khoản vay khó đòi (nhóm 3–5). Càng thấp càng tốt |
| `car` | Hệ số an toàn vốn: vốn đủ để chịu rủi ro đến mức nào. NHNN yêu cầu tối thiểu 8%. Nguồn VNDirect chỉ có 1 số/năm |
| `car_nguon` | `cong_bo` là số CAR VNDirect có đúng kỳ đó. `tra_thu_cong` là số nhóm tự tra (BID, CTG 2022–2024, link nguồn trong `data/manual/car_tra_thu_cong.csv`). `dien_tiep_ky_truoc` là lấy lại số thật gần nhất trước đó |
| `ldr` | Cho vay / tiền gửi khách hàng: ngân hàng đem bao nhiêu % tiền gửi đi cho vay. Cao nghĩa là cho vay mạnh, thanh khoản căng hơn |

`roa`, `roe`, `nim` là số **năm hóa**: lấy số của 1 quý nhân 4 để quy ra cả năm.

**Đối chiếu** (chỉ để kiểm tra chéo, không dùng cùng lúc với cột chính)

| Cột | Ý nghĩa |
|---|---|
| `roa_ttm_vnd`, `roe_ttm_vnd`, `nim_ttm_vnd` | ROA, ROE, NIM do VNDirect tính theo 4 quý gần nhất |

Không giữ LDR của VNDirect: số này trùng với `ldr` tự tính (lệch tối đa 0,026 điểm %), không thêm thông tin.

---

## 2. `bang2a_gia_ngay.csv` – Giá cổ phiếu từng ngày

Mỗi dòng là giao dịch của 1 cổ phiếu trong 1 phiên. Dữ liệu chạy từ 1/12/2020 đến 28/10/2026. Các phiên nằm ngoài Q1/2021 – Q2/2026 chỉ dùng để tính giá đầu kỳ và nhãn dự báo, nên lọc bỏ khi vẽ biểu đồ.

| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| `ma_nh`, `ngay` | Mã cổ phiếu và ngày giao dịch | |
| `gia_dong_cua` | Giá đóng cửa thực tế hiển thị trên bảng điện hôm đó | nghìn đồng |
| `gia_dong_cua_dieu_chinh` | Giá đóng cửa **đã điều chỉnh**, dùng khi so sánh giá qua thời gian | nghìn đồng |
| `gia_cao_nhat_dieu_chinh` | Giá cao nhất trong phiên, đã điều chỉnh | nghìn đồng |
| `gia_thap_nhat_dieu_chinh` | Giá thấp nhất trong phiên, đã điều chỉnh | nghìn đồng |
| `khoi_luong_gd` | Số cổ phiếu khớp lệnh trong phiên | cổ phiếu |

**Vì sao cần giá điều chỉnh:** khi ngân hàng chia cổ tức bằng cổ phiếu, số cổ phiếu tăng lên. Giá trên bảng điện vì thế "rơi" đột ngột, dù nhà đầu tư không hề lỗ. Giá điều chỉnh xóa cú rơi giả này.

---

## 3. `bang2b_gia_quy.csv` – Diễn biến giá theo quý

Mỗi dòng là diễn biến giá của 1 cổ phiếu trong 1 quý, tính trên giá đã điều chỉnh.

| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| `ma_nh`, `quy`, `nam` | Cổ phiếu và quý | |
| `ngay_dau`, `ngay_cuoi` | Phiên giao dịch đầu tiên và cuối cùng của quý | ngày |
| `so_phien_gd` | Số phiên giao dịch trong quý | phiên |
| `gia_dau_quy` | Giá lúc bắt đầu quý, tức giá đóng cửa cuối quý trước | nghìn đồng |
| `gia_cuoi_quy` | Giá đóng cửa cuối quý | nghìn đồng |
| `ty_suat_sinh_loi_quy` | Cổ phiếu tăng hay giảm bao nhiêu % trong quý, nếu giữ từ đầu đến cuối quý | % |
| `bien_dong_gia_max_min` | Khoảng cách giữa giá cao nhất và thấp nhất trong quý (giá điều chỉnh), đo mức biến động | % |
| `ty_suat_sinh_loi_quy_sau` | Lãi/lỗ nếu mua cổ phiếu vào **ngày thứ 45 sau khi quý kết thúc** (lúc BCTC quý đã công bố) và giữ đúng 1 quý | % |
| `xu_huong_quy_sau` | **Nhãn cho mô hình dự báo**: 1 là giá tăng trong khoảng thời gian trên, 0 là không tăng | 0/1 |

**Vì sao tính từ ngày thứ 45:** các ngân hàng có tối đa 45 ngày để công bố BCTC quý. Tính từ mốc này thì mô hình chỉ dùng thông tin đã được công khai lúc dự báo, không "nhìn trước tương lai". `ty_suat_sinh_loi_quy_sau` là nguồn tạo ra nhãn, nên **không được đưa vào mô hình làm biến đầu vào**.

---

## 4. `bang3a_su_kien_chi_tiet.csv` – Danh sách từng sự kiện

Mỗi dòng là 1 sự kiện phi tài chính. Các tin cùng nói về một chuyện đã được gộp làm một.

| Cột | Ý nghĩa |
|---|---|
| `ma_nh`, `quy`, `nam` | Ngân hàng, và quý/năm xảy ra sự kiện |
| `ngay_cong_bo` | Thời điểm tin đầu tiên được đăng. Giờ 00:00 nghĩa là nguồn chỉ ghi ngày |
| `loai_su_kien` | Mã loại sự kiện (xem bảng các loại bên dưới) |
| `loai_su_kien_nhan` | Tên loại sự kiện bằng tiếng Việt |
| `mo_ta_ngan` | Tiêu đề của tin đại diện |
| `nguon` | Link của tin đại diện |
| `nguon_du_lieu` | Tin lấy từ đâu: CafeF, VNDirect, hay bổ sung thủ công |
| `so_tin_gop` | Có bao nhiêu tin cùng nói về sự kiện này |
| `nguon_khac` | Link của các tin còn lại |

**Các loại sự kiện**

| Mã | Nghĩa là |
|---|---|
| `tang_von` | Tăng vốn điều lệ: phát hành cổ phiếu, chia cổ tức bằng cổ phiếu, bán vốn cho nhà đầu tư chiến lược… |
| `chuyen_doi_so` | Chuyển đổi số, tiền số: ra mắt ngân hàng số, ứng dụng công nghệ… |
| `hop_tac_trung_thau` | Ký hợp tác chiến lược, hoặc bắt đầu / chấm dứt quan hệ đối tác lớn |
| `doi_lanh_dao` | Thay Chủ tịch HĐQT, Tổng giám đốc, thành viên HĐQT |
| `chinh_sach_nhnn` | Quyết định của Ngân hàng Nhà nước tác động riêng tới ngân hàng: room tín dụng, thanh tra… |
| `khac` | Sáp nhập, M&A, nhận chuyển giao bắt buộc ngân hàng yếu |

---

## 5. `bang3b_su_kien_quy.csv` – Sự kiện theo quý

Mỗi dòng là 1 ngân hàng × 1 quý, **kể cả quý không có sự kiện**. Bảng này đếm lại dữ liệu của bảng 3a theo quý.

| Cột | Ý nghĩa |
|---|---|
| `ma_nh`, `quy`, `nam` | Ngân hàng và quý |
| `co_su_kien` | Quý này có ít nhất 1 sự kiện đáng chú ý không (1 = có, 0 = không) |
| `so_luong_su_kien` | Quý này có bao nhiêu sự kiện |
| `loai_su_kien` | Các loại sự kiện xảy ra trong quý |
| `sk_tang_von` | Quý có đợt tăng vốn không (1/0). Mọi thông báo của cùng một đợt chỉ tính 1 lần |
| `sk_chuyen_doi_so` | Số sự kiện chuyển đổi số trong quý |
| `sk_hop_tac_trung_thau` | Số sự kiện hợp tác trong quý |
| `sk_doi_lanh_dao` | Số lần đổi lãnh đạo trong quý |
| `sk_chinh_sach_nhnn` | Số sự kiện chính sách NHNN trong quý |
| `sk_khac` | Số sự kiện khác (M&A, sáp nhập…) trong quý |
| `ngay_cong_bo`, `mo_ta_ngan`, `nguon` | Ngày, tiêu đề và link của các sự kiện trong quý, nối bằng `;` hoặc `\|`. Trống khi `co_su_kien = 0` |

---

## 6. `bang4_tong_hop.csv` – Bảng bàn giao chính

Mỗi dòng là 1 ngân hàng × 1 quý. Bảng này ghép 3 bảng lại, ý nghĩa từng cột giống ở bảng gốc:

- **Khóa:** `ma_nh`, `quy`, `nam`
- **Từ Bảng 1 (tài chính, 19 cột):** từ `ngay_bctc` đến `nim_ttm_vnd`
- **Từ Bảng 2b (giá quý, 9 cột):** từ `ngay_dau` đến `xu_huong_quy_sau`
- **Từ Bảng 3b (sự kiện, 12 cột):** từ `co_su_kien` đến `nguon`

**Gợi ý cột cho từng câu hỏi nghiên cứu**

| Câu hỏi | Cột dùng |
|---|---|
| 1. Ngân hàng nào sinh lời tốt nhất | `roa`, `roe` theo `ma_nh`, `nam` |
| 2. Quốc doanh và tư nhân có khác nhau không | `nim`, `npl`, `car`, `loai_hinh_so_huu`. Với CAR chỉ lấy các dòng `car_nguon` là `cong_bo` hoặc `tra_thu_cong` |
| 3. Chỉ số nào liên quan tới giá | `roa`, `roe`, `nim`, `npl`, `car`, `ldr` so với `ty_suat_sinh_loi_quy` |
| 4. Dự báo giá quý sau (Logistic Regression) | Biến đầu vào: các chỉ số tài chính, cộng thêm `co_su_kien` / `so_luong_su_kien` / `sk_tang_von`, `sk_doi_lanh_dao`, `sk_hop_tac_trung_thau`. Nhãn: `xu_huong_quy_sau`. **Không** dùng `ty_suat_sinh_loi_quy_sau` |
| 5. Phân nhóm ngân hàng (K-Means, PCA) | Các chỉ số tài chính, chuẩn hóa trước khi phân cụm |

---

## Các file khác

- `data_dictionary.csv` / `.md`: từ điển kỹ thuật, gồm công thức, mã chỉ tiêu BCTC và thống kê từng cột.
- `bao_cao_kiem_tra.md`: báo cáo kiểm tra chất lượng dữ liệu (độ phủ, ô thiếu, đối chiếu, giá trị bất thường).
