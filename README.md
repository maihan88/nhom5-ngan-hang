# Nhóm 5 – Phân tích tài chính 8 ngân hàng niêm yết

8 ngân hàng (VCB, BID, CTG, TCB, MBB, ACB, STB, VPB), dữ liệu từ Q1/2021 đến quý gần nhất đã qua hạn
công bố BCTC (cuối quý + 45 ngày). Sản phẩm cuối: bản tin web **Nhịp Ngân Hàng** (Streamlit).

| Thư mục | Phụ trách | Nội dung |
|---|---|---|
| `Han/PTDL_3/` | Nguyễn Ngọc Mai Hân | Thu thập & làm sạch → 6 bảng CSV (`data/output/`) |
| `Nghi/Nhóm5-PTDL/` | Hoàng Ngọc Gia Nghi | Thống kê, trực quan (notebook 01–06) → `outputs/` |
| `Quan/dataset_nhom5/` | Hoàng Mạnh Quân | Logistic Regression, K-Means, PCA → `outputs/` |
| `dashboard/` | Nguyễn Ngọc Mai Hân | Web bản tin (đọc dữ liệu + kết quả của cả nhóm) |

Sơ đồ kiến trúc: `dashboard/assets/so_do_kien_truc.png` (vẽ lại bằng `py dashboard/ve_so_do.py`).

## Cài đặt (một lần)

Python 3.12 trở lên. Trên Windows dùng `py`, trên macOS/Linux thay bằng `python3`.

```powershell
py -m pip install -r requirements.txt
```

## Chạy

Ở thư mục gốc:

```powershell
py chay_tat_ca.py --mo-web                     # thu thập tới quý mới nhất -> thống kê -> ML -> cập nhật web, rồi mở web
py chay_tat_ca.py --offline                    # không tải lại, dùng cache trong Han/PTDL_3/data/raw (vd sau khi sửa data/manual)
py chay_tat_ca.py --den-quy 2025Q4 --offline   # tái lập đúng bộ dữ liệu 2021–2025 của báo cáo
```

Chỉ mở web, không chạy lại gì:

```powershell
cd dashboard
streamlit run app.py
```

Bước nào lỗi thì `chay_tat_ca.py` dừng ở đó, web giữ nguyên bản cũ. Chi tiết từng phần: README trong từng thư mục.

## Rà soát thủ công

Tin bị phân loại sai, sự kiện thiếu, số CAR sai được sửa bằng các file CSV trong `Han/PTDL_3/data/manual/`
(mỗi dòng có link nguồn và lý do). Sửa xong chạy `py chay_tat_ca.py --offline`. Sự kiện từ năm 2026 trở đi
chưa được rà soát tay.

## Nhánh

- `main`: bản hiện tại, dữ liệu 2021 → quý mới nhất.
- `ban-2021-2025` (tag `ban-on-dinh-2021-2025`): bản đã chốt cho báo cáo, dữ liệu Q1/2021–Q4/2025.
