# Thử nghiệm Vietstock làm nguồn tin thứ hai

Chưa thay đổi gì trong `data/output`. Cách đọc: cột `ket_qua` của `vietstock_thu_nghiem_tin.csv` cho biết mỗi tin dừng ở cổng nào.

## 1. Tin Vietstock 2021–2025 đi qua các cổng

- Tổng: **11992** tin, trong đó 6819 tin công bố thông tin của sàn (HOSE/HNX/UPCOM), 5173 tin báo chí.

| ma_nh | Trùng tin đã có (giữ quyết định cũ) | Tiêu đề không nhắc tới ngân hàng | Tin thường quy / không thuộc nhóm nào | Tin toàn ngành hoặc gắn nhầm mã | Gộp vào sự kiện đã có (xác nhận) | SỰ KIỆN MỚI |
|---|---|---|---|---|---|---|
| ACB | 190 | 422 | 415 | 1 | 5 | 5 |
| BID | 507 | 728 | 317 | 0 | 11 | 1 |
| CTG | 453 | 631 | 397 | 0 | 8 | 6 |
| MBB | 601 | 700 | 577 | 0 | 16 | 16 |
| STB | 318 | 519 | 530 | 0 | 5 | 22 |
| TCB | 639 | 643 | 537 | 1 | 18 | 8 |
| VCB | 369 | 532 | 304 | 7 | 12 | 13 |
| VPB | 464 | 622 | 398 | 1 | 14 | 9 |
| Tổng | 3541 | 4797 | 3475 | 10 | 89 | 80 |

## 2. Sự kiện mới (chỉ Vietstock có)

| loai_su_kien | 2021 | 2022 | 2023 | 2024 | 2025 | Tổng |
|---|---|---|---|---|---|---|
| chuyen_doi_so | 3 | 5 | 2 | 3 | 8 | 21 |
| doi_lanh_dao | 3 | 0 | 0 | 4 | 3 | 10 |
| hop_tac_trung_thau | 7 | 4 | 6 | 5 | 9 | 31 |
| khac | 2 | 0 | 1 | 0 | 0 | 3 |
| tang_von | 1 | 3 | 1 | 4 | 1 | 10 |

| ma_nh | so_su_kien_moi |
|---|---|
| ACB | 5 |
| BID | 1 |
| CTG | 6 |
| MBB | 15 |
| STB | 21 |
| TCB | 8 |
| VCB | 10 |
| VPB | 9 |

## 3. Ảnh hưởng nếu đưa vào Bảng 3

- Số sự kiện: 120 -> 195
- Số quý đổi `co_su_kien` 0 -> 1: **21** / 160
- Số dòng đổi `so_luong_su_kien`: 56
- Sự kiện cũ bị nối lại với nhau qua tin Vietstock (nên = 0): 0

- Thay đổi tổng `sk_*`: tang_von +10, chuyen_doi_so +21, hop_tac_trung_thau +31, doi_lanh_dao +10, chinh_sach_nhnn +0, khac +3

## 4. Kiểm tra ngưỡng so trùng

- Đăng cùng lúc (≤ 10 phút; tin đã có chỉ ghi ngày thì lệch ≤ 1 ngày) nhưng tiêu đề KHÔNG đủ giống -> coi là khác tin: **2203** (xem mẫu dưới, nếu thực ra là cùng tin thì phải hạ ngưỡng)

| ma_nh | do_giong | tieu_de | tin_gan_nhat_da_co | ket_qua |
|---|---|---|---|---|
| VCB | 0.129 | CBTT về việc đăng ký giao dịch trái phiếu VCB12501 của NGÂN HÀNG TMCP NGOẠI THƯƠNG VIỆT NAM | 2025-12-31 00:00 / không phải sự kiện / VCB: HĐQT phê duyệt nội dung thỏa thuận hợp tác thực hiện giao dịch CCTG giữa VCB và VCBS | khong_nhac_ten_ngan_hang |
| VCB | 0.091 | Phân tích kỹ thuật phiên chiều 25/12: Tiếp tục đà tăng | 2025-12-26 00:00 / không phải sự kiện / VCB: HĐQT phê duyệt tăng vốn điều lệ cho công ty con | khong_nhac_ten_ngan_hang |
| VCB | 0.0 | 10 doanh nghiệp làm thành viên Trung tâm Tài chính quốc tế Việt Nam tại Đà Nẵng | 2025-12-23 00:00 / không phải sự kiện / VCB: Nghị quyết HĐQT phê duyệt chủ trương thay đổi địa điểm trụ sở Chi nhánh Đông Bình Dương | khong_nhac_ten_ngan_hang |
| VCB | 0.0 | Các sự kiện ngân hàng nổi bật năm 2025 | 2025-12-23 00:00 / không phải sự kiện / VCB: Nghị quyết HĐQT phê duyệt chủ trương thay đổi địa điểm trụ sở Chi nhánh Đông Bình Dương | khong_nhac_ten_ngan_hang |
| VCB | 0.0 | Thông báo về việc hủy bỏ đăng ký giao dịch đối với trái phiếu VCB12106 của NGÂN HÀNG TMCP NGOẠI THƯƠNG VIỆT NAM | 2025-12-16 00:00 / không phải sự kiện / VCB: Thông báo nhận được công văn của NHNN Chi nhánh Khu vực 14 về việc thống nhất chủ trương thay đổi Chi nhánh quản lý PGD của VCB tại TP. Cần Thơ | khong_nhac_ten_ngan_hang |
| VCB | 0.0 | Thông báo về việc hủy bỏ đăng ký giao dịch đối với trái phiếu VCB12104 của NGÂN HÀNG TMCP NGOẠI THƯƠNG VIỆT NAM | 2025-12-16 00:00 / không phải sự kiện / VCB: Thông báo nhận được công văn của NHNN Chi nhánh Khu vực 14 về việc thống nhất chủ trương thay đổi Chi nhánh quản lý PGD của VCB tại TP. Cần Thơ | khong_nhac_ten_ngan_hang |
| VCB | 0.0 | Thông báo về việc hủy bỏ đăng ký giao dịch đối với trái phiếu VCB12213 của NGÂN HÀNG TMCP NGOẠI THƯƠNG VIỆT NAM | 2025-12-16 00:00 / không phải sự kiện / VCB: Thông báo nhận được công văn của NHNN Chi nhánh Khu vực 14 về việc thống nhất chủ trương thay đổi Chi nhánh quản lý PGD của VCB tại TP. Cần Thơ | khong_nhac_ten_ngan_hang |
| VCB | 0.0 | Big 4 ngân hàng gia nhập cuộc đua tăng lãi suất tiết kiệm | 2025-12-16 00:00 / không phải sự kiện / VCB: Thông báo nhận được công văn của NHNN Chi nhánh Khu vực 14 về việc thống nhất chủ trương thay đổi Chi nhánh quản lý PGD của VCB tại TP. Cần Thơ | khong_nhac_ten_ngan_hang |
| VCB | 0.067 | IDI, PAN và VCB liệu có khả quan? | 2025-12-16 00:00 / không phải sự kiện / VCB: Thông báo nhận được công văn của NHNN Chi nhánh Khu vực 14 về việc thống nhất chủ trương thay đổi Chi nhánh quản lý PGD của VCB tại TP. Cần Thơ | khong_phai_su_kien |
| VCB | 0.0 | Cổ phiếu vua và VN-Index không còn chung nhịp | 2025-12-01 00:00 / không phải sự kiện / VCB: Thông báo thay đổi địa chỉ trụ sở 01 Chi nhánh và 03 Phòng Giao dịch | khong_nhac_ten_ngan_hang |
| VCB | 0.0 | Đằng sau cuộc đua tăng vốn điều lệ của các ngân hàng | 2025-12-01 00:00 / không phải sự kiện / VCB: Thông báo thay đổi địa chỉ trụ sở 01 Chi nhánh và 03 Phòng Giao dịch | khong_nhac_ten_ngan_hang |
| VCB | 0.154 | Tỷ lệ LDR tăng trở lại: Tín dụng phục hồi, thanh khoản áp lực? | 2025-11-19 00:00 / không phải sự kiện / VCB: Nghị quyết HĐQT phê duyệt giới hạn tín dụng đối với VCB Lào | khong_nhac_ten_ngan_hang |
| VCB | 0.0 | Lợi nhuận ngành ngân hàng tăng trưởng 2 con số trong 9 tháng đầu năm | 2025-11-07 00:00 / không phải sự kiện / VCB: HĐQT phê duyệt giao dịch giữa VCB với VCBM | khong_nhac_ten_ngan_hang |
| VCB | 0.0 | Lãi suất huy động tăng nhẹ trở lại do nhu cầu vốn cuối năm | 2025-11-07 00:00 / không phải sự kiện / VCB: HĐQT phê duyệt giao dịch giữa VCB với VCBM | khong_nhac_ten_ngan_hang |
| VCB | 0.083 | Tăng mạnh dự phòng, Vietcombank tăng 5% lãi trước thuế quý 3 | 2025-10-29 00:00 / không phải sự kiện / VCB: Thông báo thay đổi địa chỉ trụ sở 01 chi nhánh và 02 Phòng giao dịch | khong_phai_su_kien |

- Coi là trùng theo quy tắc 'gần ngày' với độ giống < 0.8: **80** (xem mẫu dưới, nếu thực ra là khác tin thì phải nâng ngưỡng)

| ma_nh | do_giong | lech_phut | tieu_de | tin_gan_nhat_da_co |
|---|---|---|---|---|
| VCB | 0.765 | 1613.0 | Chính phủ đề xuất bổ sung hơn 20 ngàn tỷ đồng vốn điều lệ cho Vietcombank | 2024-09-26 00:00 / đã loại thủ công / Chính phủ đề xuất bổ sung 20.695 tỷ đồng để Ngân hàng Vietcombank (VCB) tăng vốn điều lệ |
| VCB | 0.778 | 3335.0 | VCH: tài liệu báo cáo phát hành cổ phiếu để trả cổ tức của VCB | 2023-07-07 00:00 / sự kiện: tang_von / VCB: CBTT v/v phát hành cổ phiếu để trả cổ tức |
| VCB | 0.727 | 1358.0 | VCH: Hội đồng quản trị phê duyệt chủ trương thay đổi địa điểm trụ sở VCB Đông Hà Nội | 2023-04-06 17:18 / không phải sự kiện / VCB: Nghị quyết HĐQT phê duyệt chủ trương thay đổi địa điểm VCB Đông Hà Nội |
| VCB | 0.714 | 276.0 | VCH: NHNN chấp thuận kế hoạch phát triển mạng lưới năm 2022 của VCB | 2023-03-24 13:45 / không phải sự kiện / VCB: Công văn của Ngân hàng Nhà nước về việc chấp thuận Kế hoạch phát triển mạng lưới năm 2022 |
| VCB | 0.757 | 1447.0 | VCH: Hội đồng quản trị phê duyệt chủ trương thay đổi địa điểm trụ sở VCB Bắc Thanh Hóa | 2023-02-27 16:03 / không phải sự kiện / VCB: Nghị quyết HĐQT v/v phê duyệt chủ trương thay đổi địa điểm trụ sở VCB chi nhánh Bắc Thanh Hóa |
| VCB | 0.706 | 255.0 | VCH: Hội đồng quản trị phê duyệt chủ trương thay đổi địa điểm trụ sở VCB Thanh Xuân | 2022-12-26 09:17 / không phải sự kiện / VCB: Nghị quyết HĐQT v/v phê duyệt chủ trương thay đổi địa điểm trụ sở chi nhánh Thanh Xuân |
| VCB | 0.769 | 30.0 | VCH: Hội đồng quản trị thông qua giao dịch giữa VCB và người liên quan về gói thầu cải tiến ứng dụng CR hệ thống Corebanking | 2022-12-01 16:27 / không phải sự kiện / VCB: Thông qua giao dịch giữ VCB và người LQ về gói thầu cải tiến ứng dụng CR hệ thống CoreBanking |
| VCB | 0.783 | 1438.0 | VCH: Hội đồng quản trị thông qua giao dịch giữa VCB và người có liên quan | 2022-10-05 17:21 / không phải sự kiện / VCB: HĐQT thông qua giao dịch giữa VCB và người có liên quan |
| VCB | 0.759 | 1270.0 | VCH: Hội đồng quản trị thông qua giao dịch tín dụng giữa VCB và người có liên quan | 2022-09-20 17:38 / không phải sự kiện / VCB: Nghị quyết HĐQT thông qua giao dịch tín dụng giữa VCB và người có liên quan |
| VCB | 0.783 | 2865.0 | Vietcombank sắp chia cổ tức bằng cổ phiếu để tăng vốn điều lệ | 2021-10-23 09:14 / sự kiện: tang_von / Vietcombank chuẩn bị chia cổ tức để tăng vốn điều lệ |
| BID | 0.774 | 3900.0 | BID123004: CBTT Văn bản của UBCKNN về việc Báo cáo kết quả phát hành cổ phiếu để trả cổ tức của BID | 2024-12-31 00:00 / không phải sự kiện / BID: Thông báo nhận được công văn của UBCKNN về việc báo cáo kết quả đợt phát hành cổ phiếu để trả cổ tức |
| BID | 0.774 | 3693.0 | BID123003: CBTT Văn bản của UBCKNN về việc Báo cáo kết quả phát hành cổ phiếu để trả cổ tức của BID | 2024-12-31 00:00 / không phải sự kiện / BID: Thông báo nhận được công văn của UBCKNN về việc báo cáo kết quả đợt phát hành cổ phiếu để trả cổ tức |
| BID | 0.774 | 3557.0 | BID123002: CBTT Văn bản của UBCKNN về việc Báo cáo kết quả phát hành cổ phiếu để trả cổ tức của BID | 2024-12-31 00:00 / không phải sự kiện / BID: Thông báo nhận được công văn của UBCKNN về việc báo cáo kết quả đợt phát hành cổ phiếu để trả cổ tức |
| BID | 0.774 | 3556.0 | BID122005: CBTT Văn bản của UBCKNN về việc Báo cáo kết quả phát hành cổ phiếu để trả cổ tức của BID | 2024-12-31 00:00 / không phải sự kiện / BID: Thông báo nhận được công văn của UBCKNN về việc báo cáo kết quả đợt phát hành cổ phiếu để trả cổ tức |
| BID | 0.774 | 3554.0 | BID121028: CBTT Văn bản của UBCKNN về việc Báo cáo kết quả phát hành cổ phiếu để trả cổ tức của BID | 2024-12-31 00:00 / không phải sự kiện / BID: Thông báo nhận được công văn của UBCKNN về việc báo cáo kết quả đợt phát hành cổ phiếu để trả cổ tức |

## 5. Gợi ý rà soát bản CafeF

Tin trùng mà tiêu đề Vietstock được phân loại là sự kiện, nhưng bản đã có đang bị coi là 'không phải sự kiện': **37**. Không tự đếm – nếu đúng là sự kiện thì ghi link bản đã có vào `data/manual/su_kien_sua_loai.csv`.

| ma_nh | phan_loai_tieu_de | tieu_de | tin_gan_nhat_da_co |
|---|---|---|---|
| VCB | tang_von | VCB: Báo cáo kết quả phát hành cổ phiếu để trả cổ tức | 2025-03-27 00:00 / không phải sự kiện / VCB: Đã phát hành 2.766.583.832 cổ phiếu để trả cổ tức |
| VCB | tang_von | VCB: Báo cáo kết quả phát hành cổ phiếu để trả cổ tức | 2023-08-09 00:00 / không phải sự kiện / VCB: Đã phát hành 856.574.691 cổ phiếu để trả cổ tức |
| VCB | tang_von | VCB: Báo cáo kết quả đợt phát hành cổ phiếu để trả cổ tức | 2022-01-06 17:01 / không phải sự kiện / VCB: Đã phát hành 1.023.639.123 cổ phiếu để trả cổ tức |
| BID | tang_von | BID: Thông báo thay đổi số lượng cổ phiếu có quyền biểu quyết đang lưu hành và báo cáo kết quả phát hành cổ phiếu để trả cổ tức | 2024-12-30 00:00 / không phải sự kiện / BID: Số lượng cổ phiếu có quyền biểu quyết đang lưu hành là 6.897.515.268 cp |
| BID | tang_von | BID: Thông báo ngày ĐKCC phát hành cổ phiếu để trả cổ tức | 2023-11-21 00:00 / không phải sự kiện / BID: 28.11.2023, ngày GDKHQ phát hành cổ phiếu để trả cổ tức (tỷ lệ 100:12,69) |
| BID | tang_von | BID: Báo cáo kết quả đợt phát phát hành cổ phiếu để trả cổ tức | 2022-01-14 15:20 / không phải sự kiện / BID: Đã phát phát hành 1.036.505.776 cổ phiếu để trả cổ tức |
| BID | tang_von | BID: Báo cáo kết quả phát hành cổ phiếu để trả cổ tức | 2021-12-30 15:14 / không phải sự kiện / BID: Công văn của UBCKNN về báo cáo kết quả phát hành cổ phiếu để trả cổ tức của BID |
| CTG | tang_von | CTG: Báo cáo kết quả phát hành cổ phiếu để trả cổ tức | 2025-12-25 00:00 / không phải sự kiện / CTG: Đã phát hành 2.396.952.889 cổ phiếu để trả cổ tức |
| CTG | tang_von | CTG: Thông báo về ngày đăng ký cuối cùng phát hành cổ phiếu trả cổ tức | 2025-12-10 00:00 / không phải sự kiện / CTG: 17.12.2025, ngày GDKHQ phát hành cổ phiếu trả cổ tức (tỷ lệ 100 : 44,63658403) |
| CTG | doi_lanh_dao | CTG: Thông báo thay đổi nhân sự Thành viên HĐQT và Thành viên BKS nhiệm kỳ 2024 - 2029 của VietinBank | 2024-05-02 00:00 / không phải sự kiện / CTG: Thông báo thay đổi nhân sự nhiệm kỳ 2024-2029 |
| CTG | tang_von | CTG: Báo cáo kết quả phát hành cổ phiếu để trả cổ tức | 2023-12-13 00:00 / không phải sự kiện / CTG: Đã phát hành 564.241.139 cổ phiếu để trả cổ tức |
| CTG | tang_von | CTG: Thông báo ngày ĐKCC phát hành cổ phiếu để trả cổ tức | 2023-11-24 00:00 / không phải sự kiện / CTG: 30.11.2023, ngày GDKHQ phát hành cổ phiếu để trả cổ tức (tỷ lệ 100:11,7415) |
| CTG | tang_von | CTG: Báo cáo kết quả phát hành cổ phiếu để trả cổ tức | 2021-07-21 13:32 / không phải sự kiện / CTG: Đã phát hành 1.082.346.053 cổ phiếu để trả cổ tức |
| CTG | tang_von | CTG: Thông báo ngày ĐKCC phát hành cổ phiếu để trả cổ tức | 2021-06-29 10:22 / không phải sự kiện / CTG: 7.7.2021, ngày GDKHQ phát hành cổ phiếu để trả cổ tức (tỷ lệ 100:29.0695) |
| CTG | tang_von | CTG: Thông báo phát hành cổ phiếu để trả cổ tức | 2021-06-23 17:48 / không phải sự kiện / CTG: Công văn của UBCKNN v/v phát hành cổ phiếu để trả cổ tức của CTG |
| TCB | tang_von | TCB: Nghị quyết HĐQT về việc ngày ĐKCC chốt DS phát hành cổ phiếu | 2024-06-10 00:00 / không phải sự kiện / TCB: Nghị quyết HĐQT về việc ngày ĐKCC chốt danh sách phát hành cổ phiếu |
| TCB | doi_lanh_dao | TCB: BIÊN BẢN + NGHỊ QUYẾT ĐHĐCĐ + NGHỊ QUYẾT HĐQT VỀ BẦU CHỨC DANH TRONG HĐQT NHIỆM KỲ 2024-2029 | 2024-04-22 00:00 / không phải sự kiện / TCB: Nghị quyết HĐQT về nhân sự HĐQT nhiệm kỳ 2024-2029 |
| TCB | tang_von | TCB: Báo cáo kết quả phát hành cổ phiếu theo chương trình lựa chọn cho người lao động | 2022-09-06 17:11 / không phải sự kiện / TCB: Đã phát hành 6.323.716 cp theo chương trình lựa chọn cho người lao động |
| MBB | tang_von | MBB: Thông báo thay đổi số lượng cổ phiếu có quyền biểu quyết và báo cáo kết quả phát hành cổ phiếu để trả cổ tức | 2025-08-21 00:00 / không phải sự kiện / MBB: Số lượng cổ phiếu có quyền biểu quyết đang lưu hành là 8.054.999.909 cp |
| MBB | tang_von | MBB: MBB.CBTT Báo cáo kết quả phát hành cổ phiếu trả cổ tức và Thay đổi số lượng cổ phiếu có quyền biểu quyết đang lưu hành | 2025-01-14 00:00 / không phải sự kiện / MBB: Số lượng cổ phiếu có quyền biểu quyết đang lưu hành là 6.102.272.659 cp |
| MBB | tang_von | MBB: Báo cáo kết quả phát hành cổ phiếu để trả cổ tức | 2025-01-14 00:00 / không phải sự kiện / MBB: Đã phát hành 795.948.607 cổ phiếu để trả cổ tức |
| MBB | tang_von | MBB: MBB CBTT Báo cáo kết quả phát hành ESOP và Thay đổi số lượng cổ phiếu có quyền biểu quyết đang lưu hành | 2024-06-13 00:00 / không phải sự kiện / MBB: Số lượng cổ phiếu có quyền biểu quyết đang lưu hành là 5.306.324.052 cp |
| MBB | tang_von | MBB: MBB.CBTT Báo cáo đợt phát hành cổ phiếu để trả cổ tức từ LNST để lại lũy kế của năm 2022 | 2023-07-19 00:00 / không phải sự kiện / MBB: Đã phát hành 680.097.919 cổ phiếu để trả cổ tức |
| MBB | tang_von | MBB: Báo cáo kết quả đợt phát hành cổ phiếu để trả cổ tức | 2023-07-19 00:00 / không phải sự kiện / MBB: Đã phát hành 680.097.919 cổ phiếu để trả cổ tức |
| MBB | tang_von | MBB: Thông báo ngày ĐKCC trả cổ tức bằng cổ phiếu | 2022-08-16 14:15 / không phải sự kiện / MBB: 22.8.2022, ngày GDKHQ trả cổ tức bằng cổ phiếu (tỷ lệ 100:20) |
| MBB | tang_von | MB chốt quyền trả cổ tức bằng cổ phiếu tỷ lệ 20% | 2022-08-09 17:17 / không phải sự kiện / MB chốt quyền phát hành 755 triệu cổ phiếu trả cổ tức, tỷ lệ 20% |
| MBB | tang_von | MBB: Báo cáo kết quả phát hành cổ phiếu để trả cổ tức từ lợi nhuận sau thuế để lại lũy kế của năm 2020 | 2021-07-20 17:35 / không phải sự kiện / MBB: Đã phát hành 979.564.905 cp để trả cổ tức từ lợi nhuận sau thuế để lại lũy kế của năm 2020 |
| ACB | tang_von | ACB: Báo cáo kết quả phát hành cổ phiếu để trả cổ tức | 2025-06-02 00:00 / không phải sự kiện / ACB: Đã phát hành 669.998.687 cổ phiếu để trả cổ tức |
| ACB | doi_lanh_dao | ACB: Bổ nhiệm Ông Từ Tiến Phát tiếp tục giữ chức Tổng giám đốc | 2025-01-09 00:00 / không phải sự kiện / ACB: Bổ nhiệm lại ông Từ Tiến Phát giữ chức Tổng giám đốc |
| ACB | tang_von | ACB: Báo cáo kết quả đợt phát hành cổ phiếu để trả cổ tức | 2024-06-06 00:00 / không phải sự kiện / ACB: Đã phát hành 582.607.554 cổ phiếu để trả cổ tức |
