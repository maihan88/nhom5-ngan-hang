# DATA READINESS REPORT

**READY FOR ML**

## 1. Dataset Overview

| file | rows | columns | banks | years | quarters | exact_duplicates |
|---|---|---|---|---|---|---|
| bang1_tai_chinh_quy.csv | 160 | 30 | 8 | 2021,2022,2023,2024,2025 | Q1,Q2,Q3,Q4 | 0 |
| bang2a_gia_ngay.csv | 10851 | 10 | 8 |  |  | 0 |
| bang2b_gia_quy.csv | 160 | 17 | 8 | 2021,2022,2023,2024,2025 | Q1,Q2,Q3,Q4 | 0 |
| bang3a_su_kien_chi_tiet.csv | 121 | 11 | 8 | 2021,2022,2023,2024,2025 | Q1,Q2,Q3,Q4 | 0 |
| bang3b_su_kien_quy.csv | 160 | 15 | 8 | 2021,2022,2023,2024,2025 | Q1,Q2,Q3,Q4 | 0 |
| bang4_tong_hop.csv | 160 | 56 | 8 | 2021,2022,2023,2024,2025 | Q1,Q2,Q3,Q4 | 0 |

Ngân hàng: ACB, BID, CTG, MBB, STB, TCB, VCB, VPB; 2021–2025; Q1–Q4. Mỗi mẫu là ngân hàng × quý.

## 2. Missing Data

| feature | missing |
|---|---|
| roa | 0 |
| roe | 0 |
| nim | 0 |
| npl | 0 |
| car | 0 |
| ldr | 0 |
| co_su_kien | 0 |
| so_luong_su_kien | 0 |
| sk_tang_von | 0 |
| sk_chuyen_doi_so | 0 |
| sk_hop_tac_trung_thau | 0 |
| sk_doi_lanh_dao | 0 |
| sk_chinh_sach_nhnn | 0 |
| sk_khac | 0 |
| xu_huong_quy_sau | 0 |

Các ô trống mô tả sự kiện khi không có sự kiện là hợp lệ. Toàn bộ cột/kiểu/missing nằm trong dataset_schema_missing.csv.

## 3. Duplicate và consistency

0 lỗi nghiêm trọng; chi tiết dòng CSV (bao gồm header) ở validation_issues.csv. Đối chiếu mọi cột chung Bảng 1/2b/3b với Bảng 4; đối chiếu số sự kiện với 3a; tái tính nhãn từ 2a.

## 4. Target Distribution

| split | class | count | percent |
|---|---|---|---|
| All | 0 | 70 | 43.75 |
| All | 1 | 90 | 56.25 |
| Train 2021–2024 | 0 | 54 | 42.19 |
| Train 2021–2024 | 1 | 74 | 57.81 |
| Test 2025 | 0 | 16 | 50.0 |
| Test 2025 | 1 | 16 | 50.0 |

## 5. Event Frequency

| feature | sum_all | nonzero_all | sum_train | nonzero_train | rare_train_lt5 |
|---|---|---|---|---|---|
| co_su_kien | 88 | 88 | 70 | 70 | False |
| so_luong_su_kien | 121 | 88 | 94 | 70 | False |
| sk_tang_von | 61 | 61 | 49 | 49 | False |
| sk_chuyen_doi_so | 4 | 4 | 2 | 2 | True |
| sk_hop_tac_trung_thau | 15 | 15 | 10 | 10 | False |
| sk_doi_lanh_dao | 33 | 30 | 26 | 24 | False |
| sk_chinh_sach_nhnn | 2 | 2 | 2 | 2 | True |
| sk_khac | 6 | 6 | 5 | 5 | False |

Hiếm: dưới 5 quan sát khác 0 trong Train, chỉ là ngưỡng cảnh báo. co_su_kien được suy ra từ count; Model 2A chọn co_su_kien trước khi xem kết quả Test. Model 2B giữ tất cả loại, không thêm tổng count vì tổng này bằng tổng các loại.

## 6. Leakage Check

Cấm xu_huong_quy_sau và ty_suat_sinh_loi_quy_sau. Đối chiếu: roa_ttm_vnd, roe_ttm_vnd, nim_ttm_vnd, ldr_vnd. Các ngày, nguồn, URL, tiêu đề, car_nguon là mô tả, không làm input. Chỉ whitelist 6 financial và event được chọn. Train 2021–2024; Test 2025; mọi scaler dự báo fit Train. Nhãn theo mốc +45 ngày, không phải quý lịch. Không dùng Test chọn feature/hyperparameter.

## 7. CAR Check và giới hạn thời điểm

- CAR Q4 dùng Q3 cùng năm CHỈ ở bản đầu vào dự báo theo dictionary; CAR gốc dùng cho phân cụm mô tả. Không xử lý lại quy tắc điền CAR của nhóm.
- Không có ngày công bố BCTC thực tế: mốc +45 ngày là giả định của dictionary, chưa xác minh point-in-time; số VNDirect là bản sau cùng.
- Thiếu data_dictionary.csv và data/manual/car_tra_thu_cong.csv được dẫn chiếu: chưa thể xác minh nguồn CAR tra thủ công độc lập.

32 dòng Q4 có CAR đầu vào dự báo khác CAR gốc; xem car_audit.csv.

## 8. Kết luận

READY FOR ML — điều kiện: dùng bản CAR dự báo theo dictionary, chấp nhận hạn chế dữ liệu công bố nêu trên.

## Kiểm tra redundancy trên Train

| model | columns_including_intercept | rank | condition_number_standardized |
|---|---|---|---|
| Financial | 7 | 7 | 8.204 |
| Financial + general | 8 | 8 | 8.308 |
| Financial + categories | 13 | 13 | 9.012 |

Rank và condition number được kiểm tra trước train. Correlation ở train_feature_correlations.csv. Các financial giữ theo câu hỏi nghiên cứu; regularization L2 hỗ trợ khi tương quan lớn, nhưng hệ số cần diễn giải có điều kiện. Tổng count bằng tổng category nên không đưa đồng thời vào Model 2B.
