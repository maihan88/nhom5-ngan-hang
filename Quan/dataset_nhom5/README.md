# Machine Learning – Phân tích ngân hàng niêm yết

Dữ liệu gốc nằm ở thư mục gốc và được giữ nguyên. Mỗi mẫu là một ngân hàng × quý.

## Chạy lại trên Windows

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/run_pipeline.py
.\.venv\Scripts\python.exe src/create_notebooks.py
```

`run_pipeline.py` đọc dictionary và kiểm tra mọi bảng, lưu báo cáo readiness trước khi import/fit mô hình. Nếu NOT READY, dừng huấn luyện. Nếu READY, chạy Logistic, K-Means và PCA rồi xuất báo cáo cuối. Notebook đã có Markdown giải thích và output thực thi.

`requirements.txt` chốt các thư viện chính đúng phiên bản đã chạy. `requirements-lock.txt` chốt toàn bộ phụ thuộc. Có thể dùng `pip install -r requirements-lock.txt` để tái lập môi trường Python 3.13 đã sử dụng.

## Phương pháp

- Logistic: Train 2021–2024, Test 2025; chỉ scaler financial trên Train, giữ event ở đơn vị tự nhiên; baseline và 3 mô hình được xác định trước khi xem Test; không tuning.
- CAR dự báo Q4 dùng Q3 cùng năm theo dictionary, chỉ trong bản sao; CAR dữ liệu gốc và quy tắc điền của nhóm giữ nguyên. Bảng `car_audit.csv` truy vết.
- K-Means mô tả toàn kỳ trên 6 financial chuẩn hóa; thử K=2..6; PCA dùng chính ma trận này. Không dùng kết quả clustering/PCA làm feature Logistic.
- Random state 42; kết quả gốc không bị sửa. SHA-256 và phiên bản nằm trong `outputs/reports/reproducibility.json`.

## Kết quả

- `outputs/reports/data_readiness_report.md`: checkpoint và giới hạn dữ liệu.
- `outputs/reports/ml_results.md`: kết quả, diễn giải, trả lời RQ1–RQ3.
- `outputs/tables/`: audit, metrics, predictions, coefficients, profiles, loadings và phân bố theo thời gian.
- `outputs/figures/`: biểu đồ đã chạy thực tế.
- `notebooks/01_data_validation.ipynb`, `02_logistic_regression.ipynb`, `03_kmeans_pca.ipynb`: thứ tự học thuật.

Không chứng minh nhân quả, không khẳng định hiệu quả tổng quát từ một Test nhỏ. Mốc +45 ngày và bản BCTC sau soát xét là giới hạn cần bảo vệ rõ trong báo cáo. Những nguồn manual/dictionary CSV được dẫn chiếu nhưng chưa bàn giao không được giả lập.
