# Kết quả Machine Learning

## 1. Data Readiness

READY FOR ML với bản CAR dự báo theo dictionary; 160 quan sát, 8 ngân hàng, 2021–2025. Không thay CSV gốc. Train 128; Test 32. Xem [Data Readiness](data_readiness_report.md).

## 2. Logistic Regression

| Model | Features | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| Baseline | - | 0.5 | 0.5 | 1.0 | 0.6667 | 0.5 |
| Financial Only | roa, roe, nim, npl, car, ldr | 0.5 | 0.5 | 0.9375 | 0.6522 | 0.5352 |
| Financial + General Event | roa, roe, nim, npl, car, ldr, co_su_kien | 0.625 | 0.6 | 0.75 | 0.6667 | 0.5703 |
| Financial + Event Categories | roa, roe, nim, npl, car, ldr, sk_tang_von, sk_chuyen_doi_so, sk_hop_tac_trung_thau, sk_doi_lanh_dao, sk_chinh_sach_nhnn, sk_khac | 0.5938 | 0.5714 | 0.75 | 0.6486 | 0.5469 |

Mặc định L2, C=1, ngưỡng 0.5; không tuning trên Test. Chỉ 6 biến tài chính được chuẩn hóa bằng Train; event giữ đơn vị tự nhiên (cờ/đếm), nên hệ số event không so trực tiếp magnitude với hệ số financial. Model 2A chọn cờ có sự kiện để tránh trùng thông tin với count. Model 2B giữ đủ 6 loại; hai loại chỉ có 2 quan sát Train nên hệ số dễ bất ổn. Regularization hỗ trợ nhưng không khắc phục thiếu thông tin.

| Model | delta_Accuracy | delta_F1 | delta_ROC-AUC |
|---|---|---|---|
| Financial + General Event | 0.125 | 0.0145 | 0.0352 |
| Financial + Event Categories | 0.0938 | -0.0035 | 0.0117 |

Hệ số dương/âm biểu thị liên hệ cùng/ngược chiều với log-odds nhóm tăng, có điều kiện trên các biến khác trong mô hình; không chứng minh nhân quả. Hệ số và hướng chi tiết ở logistic_coefficients.csv. Financial standardized: một đơn vị là một độ lệch chuẩn Train.

![Confusion matrices](../figures/confusion_matrices.png)

![ROC](../figures/roc_curves.png)

![Coefficients](../figures/logistic_coefficients.png)

## 3. K-Means

| K | Inertia | Silhouette | smallest_cluster |
|---|---|---|---|
| 2 | 611.8148 | 0.5337 | 21 |
| 3 | 413.2167 | 0.3738 | 20 |
| 4 | 340.1623 | 0.3566 | 18 |
| 5 | 283.0924 | 0.3764 | 3 |
| 6 | 261.2651 | 0.3105 | 3 |

Chọn K=2: silhouette cao nhất trong 2–6, đối chiếu đường inertia và profile dưới đây. Đây là quy tắc có thể tái lập; elbow chỉ mang tính bổ trợ, không khẳng định có điểm gãy rõ. Nhóm không được chọn bằng target hoặc Test performance. Fit scaler toàn bộ 160 mẫu cho mục đích mô tả; không dùng cụm/PCA để dự báo.

| cluster | roa | roe | nim | npl | car | ldr | observations | description |
|---|---|---|---|---|---|---|---|---|
| 0 | 1.779 | 19.529 | 3.614 | 1.291 | 10.935 | 103.311 | 139 | NPL thấp tương đối / LDR thấp tương đối |
| 1 | 1.987 | 12.811 | 6.335 | 4.797 | 14.664 | 134.825 | 21 | NPL cao tương đối / LDR cao tương đối |

Tên cụm theo hai độ lệch chuẩn lớn nhất so với trung bình toàn mẫu; “cao/thấp” là tương đối trong dataset, không phải xếp hạng chất lượng ngân hàng. Phân cụm các ngân hàng-quý, không phải 8 ngân hàng cố định. Số ngân hàng-quý theo ngân hàng:

| ma_nh | 0 | 1 |
|---|---|---|
| ACB | 20 | 0 |
| BID | 20 | 0 |
| CTG | 20 | 0 |
| MBB | 20 | 0 |
| STB | 19 | 1 |
| TCB | 20 | 0 |
| VCB | 20 | 0 |
| VPB | 0 | 20 |

Cluster_over_time và cluster_transitions cho thấy thay đổi theo thời gian; số cụm là nhãn tùy ý, không có thứ bậc. CAR phân cụm là CAR gốc đã được nhóm điền theo nguồn.

![K selection](../figures/k_selection.png)

![Cluster distribution](../figures/cluster_distribution.png)

## 4. PCA

| PC | explained_variance_ratio | cumulative |
|---|---|---|
| PC1 | 0.4991 | 0.4991 |
| PC2 | 0.3211 | 0.8202 |

| Feature | PC1 | PC2 |
|---|---|---|
| roa | 0.346 | 0.559 |
| roe | -0.0246 | 0.671 |
| nim | 0.5056 | 0.1221 |
| npl | 0.3577 | -0.445 |
| car | 0.4959 | -0.0027 |
| ldr | 0.5002 | -0.1564 |

PCA dùng chính ma trận standardized của K-Means. Bảng trên là components_ (hệ số vector thành phần); dấu PC tùy quy ước. Hai chiều chỉ là phép chiếu, các cụm có thể chồng lấn và không thể hiện toàn bộ khoảng cách 6 chiều.

PC1: đóng góp mạnh theo trị tuyệt đối: nim (0.506), ldr (0.500), car (0.496). Không gán nhãn kinh tế vượt quá loadings.

PC2: đóng góp mạnh theo trị tuyệt đối: roe (0.671), roa (0.559), npl (-0.445). Không gán nhãn kinh tế vượt quá loadings.

![PCA](../figures/pca_scatter.png)

## 5. Research Question Answers

**RQ1:** Financial Only đạt Accuracy 0.500, F1 0.652, ROC-AUC 0.535 trên 32 mẫu Test 2025; cần đối chiếu baseline trong bảng. Đây là khả năng quan sát trong một năm kiểm tra, chưa chứng minh tính tổng quát.

**RQ2:** Chênh lệch khi thêm event được tính ở bảng delta phía trên. Các chỉ số không đồng thời cải thiện ở cả hai phiên bản; chưa đủ bằng chứng khẳng định cải thiện ổn định. Với 32 mẫu, một dự đoán khác làm Accuracy thay đổi 3.125 điểm %. Không chọn phiên bản “tốt nhất” dựa trên Test để triển khai.

**RQ3:** 2 cụm tài chính mô tả theo profile thực tế ở trên, gồm NPL thấp tương đối / LDR thấp tương đối; NPL cao tương đối / LDR cao tương đối.

## 6. Limitations

- Chỉ 160 quan sát, 8 ngân hàng, giai đoạn 2021–2025; các quan sát cùng ngân hàng và cùng quý phụ thuộc nhau.
- Test chỉ năm 2025, chưa có validation qua nhiều năm; chưa có khoảng tin cậy hay kết luận ý nghĩa thống kê về cải thiện.
- Event hiếm, nguồn tin và phân loại có thể thiếu; không âm thầm bỏ hoặc gộp loại.
- CAR công bố theo năm, giá trị điền tiếp tạo nhiều quý lặp lại; chưa có nguồn manual trong project để kiểm chứng độc lập.
- Financial VNDirect có thể là bản sau soát xét/kiểm toán; giả định BCTC biết ở +45 ngày chưa kiểm tra bằng ngày công bố thực tế.
- Giá điều chỉnh có thể được điều chỉnh hồi tố; chưa có snapshot giá point-in-time.
- Logistic chỉ thể hiện association, không causality. Nhãn là lợi suất giữa hai mốc +45 ngày, không phải lợi suất quý lịch.
- K-Means phụ thuộc khoảng cách, outlier và giả định cụm dạng cầu; PCA 2D mất một phần thông tin.

## 7. Đọc sâu kết quả và kiểm chứng diễn giải

Financial Only có F1 0.652, so với baseline 0.667; AUC 0.535 gần mức ngẫu nhiên 0.5. Vì vậy khả năng dự báo hiện tại yếu. Model event tổng quát tăng Accuracy nhưng chưa vượt baseline về F1; Model categories không cải thiện F1 so với financial only.

Financial + Event Categories: các financial có |hệ số| lớn nhất: roa +0.638 (cùng chiều), car -0.434 (ngược chiều), roe -0.390 (ngược chiều). Đây là liên hệ có điều kiện, không phải tác động nhân quả.

Financial + General Event: các financial có |hệ số| lớn nhất: roa +0.549 (cùng chiều), roe -0.355 (ngược chiều), car -0.351 (ngược chiều). Đây là liên hệ có điều kiện, không phải tác động nhân quả.

Financial Only: các financial có |hệ số| lớn nhất: roa +0.492 (cùng chiều), roe -0.327 (ngược chiều), car -0.276 (ngược chiều). Đây là liên hệ có điều kiện, không phải tác động nhân quả.

Có 1 lần chuyển cụm giữa các quý liên tiếp trong toàn bộ panel. Cụm 0: ACB 20 mẫu, BID 20 mẫu, CTG 20 mẫu, MBB 20 mẫu, TCB 20 mẫu, VCB 20 mẫu, STB 19 mẫu. Cụm 1: VPB 20 mẫu, STB 1 mẫu. Phân cụm chủ yếu phản ánh khác biệt cố hữu giữa ngân hàng, chưa chứng minh trạng thái tài chính biến đổi rộng theo thời gian. Các mẫu STB trong cụm ít quan sát: Q4/2025.

K=2 có silhouette 0.534; K=5 và 6 tạo cụm nhỏ nhất chỉ 3 mẫu. Đường inertia tiếp tục giảm nhưng tách thêm cụm kém gọn và khó bảo vệ trên dataset nhỏ. K=2 phù hợp hai profile đối lập về NPL/LDR, đồng thời nhóm NPL/LDR cao có NIM và CAR cao hơn, ROE thấp hơn. Chênh lệch ROA nhỏ, không nên gọi nhóm này profitability cao.

PC1 có NIM, LDR, CAR cùng dấu và đóng góp mạnh; mô tả trục đồng biến ba tỷ lệ này, không gọi chung là “tốt hơn”. PC2 chủ yếu đối chiếu ROE/ROA dương với NPL âm; hỗ trợ cách đọc lợi nhuận tương đối đối lập nợ xấu trong phép chiếu này. PCA scatter vẫn có một điểm cụm NPL cao lệch xa theo PC2; không xem mọi điểm cùng cụm là đồng nhất.
