# Nhóm 5 PTDL – Trực quan hóa & Phân tích thống kê

```
phan1/
├── data/                  # đặt 6 file CSV của Hân vào đây
├── src/
│   ├── config.py          # bảng màu, thứ tự, nhãn chỉ số, giao diện biểu đồ
│   ├── data_loader.py     # hàm đọc dữ liệu dùng chung (lọc 2021–2025, cột ky)
│   ├── kiem_tra.py        # kiểm tra chất lượng dữ liệu bàn giao
│   └── ket_qua.py         # cấu trúc + hàm xuất 4 bảng kết quả
├── notebooks/01_chuan_bi_du_lieu.ipynb
├── outputs/               # 4 CSV kết quả + figures/*.png
├── QUY_UOC.md             # văn bản quy ước gửi Hân
└── GL2_khau_truc_quan_thong_ke.md
```

Cài đặt: `pip install -r requirements.txt`. Chạy notebook từ thư mục `notebooks/`.
Xuất PNG lần đầu báo `ChromeNotFoundError` → chạy `plotly_get_chrome` một lần.
