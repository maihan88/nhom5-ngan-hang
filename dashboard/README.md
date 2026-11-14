# UpBank! – dữ liệu 8 ngân hàng niêm yết

Sản phẩm đầu ra của Nhóm 5 (Phân tích dữ liệu cho môi trường doanh nghiệp): web Streamlit dạng dashboard –
sidebar trái, nội dung trên các thẻ, nền giấy ấm + thẻ trắng, tông than chì + vàng đồng. Mỗi trang có một câu nhận định tự sinh từ dữ liệu;
biểu đồ làm nổi bật đúng ngân hàng đang được nói tới.

Giao diện tối (kiểu terminal tài chính): menu ⋮ góc phải → Settings → Dark. Biểu đồ tự vẽ lại theo màu tối.

## Chạy trên máy

Trong PowerShell (thư mục `dashboard`):

```powershell
py -m pip install -r requirements.txt
py dong_bo_du_lieu.py      # gom dữ liệu + kết quả mới nhất của cả nhóm, rồi xuất lại mô hình .pkl
streamlit run app.py
```

### Một lệnh chạy lại cả dự án

Khi dữ liệu thay đổi, chạy ở thư mục gốc `PTDL_nhom5` (không phải trong `dashboard`):

```powershell
py chay_tat_ca.py             # crawl (dùng cache nếu có) -> thống kê (Nghi) -> ML (Quân) -> đồng bộ web
py chay_tat_ca.py --refresh   # bỏ cache, tải lại dữ liệu mới từ nguồn
py chay_tat_ca.py --offline   # chỉ dùng cache, vd sau khi sửa tay Han/PTDL_3/data/manual/
py chay_tat_ca.py --mo-web    # chạy xong mở web luôn
py chay_tat_ca.py --den-quy 2026Q3 --gia-den 2026-11-14 --offline   # tái lập đúng bộ dữ liệu của báo cáo, không cần mạng
```

Mặc định dữ liệu kéo tới quý gần nhất đã qua hạn công bố BCTC (cuối quý + 45 ngày). Năm kiểm chứng của mô hình là năm
cuối có nhãn đủ 4 quý; các quý của năm đang dở chỉ dùng để dự báo. ROA/ROE năm chỉ tính cho năm đủ 4 quý.

Script chép dữ liệu mới của Hân sang `Nghi/Nhóm5-PTDL/data/` và `Quan/dataset_nhom5/`, chạy các notebook của Nghi
(không cần Jupyter), chạy `src/run_pipeline.py` của Quân, rồi gọi `dong_bo_du_lieu.py`. Bước nào lỗi thì dừng
ở đó, web giữ nguyên bản cũ. Hình PNG cho báo cáo của Nghi (`Nghi/Nhóm5-PTDL/outputs/figures/bao_cao/`) cần
`kaleido` + Chrome (`py -m pip install kaleido`); thiếu thì bỏ qua hình, không ảnh hưởng tới web. Mất khoảng
5 phút khi xuất hình, 2–3 phút khi không (chưa tính thời gian crawl).

Dùng `py` thay vì `python`: trên máy này `python` đang trỏ tới Python 3.13 chưa cài thư viện, còn `py` và
`streamlit` dùng Python 3.14 đã đủ thư viện.

## Các mục

| Mục | Nội dung | Câu hỏi nghiên cứu |
|---|---|---|
| Bản tin | Tiêu đề quý, chỉ số ngành, bảng xếp hạng 8 ngân hàng (bấm tên → hồ sơ), sinh lời qua các năm, cổ phiếu 12 tháng, tin doanh nghiệp | 1 |
| Ngân hàng | Hồ sơ 1 ngân hàng: nhận định một câu, 6 chỉ số + thứ hạng, so với mặt bằng ngành, giá + sự kiện, góc nhìn mô hình | – |
| So sánh | Đối đầu nhiều ngân hàng, xu hướng chỉ số, xếp hạng ROE/ROA năm, quốc doanh vs tư nhân | 1, 2 |
| Dự báo | Tín hiệu quý tới, vì sao khó dự báo (tương quan), kiểm chứng 2025, có/không dữ liệu sự kiện, giải thích theo ngân hàng | 3, 4 |
| Phân nhóm | Bản đồ định vị (PCA), hồ sơ nhóm (K-Means), nhóm qua từng quý | 5 |
| Phương pháp | Bảng 5 câu hỏi ↔ mục, sơ đồ kiến trúc, tải dữ liệu, từ điển dữ liệu, giới hạn | – |

## Cấu trúc

```
dashboard/
├── app.py                 # điểm vào: sidebar các mục, theo dõi giao diện sáng/tối
├── trang/                 # mỗi mục một file
├── web/
│   ├── du_lieu.py         # đọc dữ liệu + kết quả (có cache, tự làm mới khi CSV đổi)
│   ├── mo_hinh.py         # Logistic Regression, K-Means, PCA theo đúng code của Quân
│   ├── giao_dien.py       # nhận diện: bảng màu sáng/tối, CSS, số kiểu Việt, thẻ và thành phần HTML (đổi màu ở đây)
│   └── bieu_do.py         # biểu đồ Plotly, màu theo giao diện sáng/tối
├── assets/                # logo, icon, sơ đồ kiến trúc (so_do_kien_truc.svg cho web, .png 16:9 cho ppt)
├── ve_so_do.py            # vẽ lại sơ đồ kiến trúc: py ve_so_do.py
├── .streamlit/config.toml # theme sáng/tối than chì + vàng đồng, font Inter (chữ) + JetBrains Mono (số) + Merriweather (câu nhận định)
├── src/                   # bản sao code của Nghi (config, data_loader, viz, thong_ke) – KHÔNG sửa ở đây
├── data/                  # 6 bảng CSV + data_dictionary.csv của Hân
├── outputs/               # 4 bảng kết quả thống kê của Nghi; outputs/ml: bảng kết quả của Quân
├── mo_hinh/               # 3 mô hình Logistic (.pkl) + thong_tin.json: danh sách & thứ tự biến, ngày xuất, phiên bản
├── xuat_mo_hinh.py        # huấn luyện và xuất mo_hinh/ (tự chạy cuối dong_bo_du_lieu.py)
└── dong_bo_du_lieu.py     # chép dữ liệu/kết quả từ thư mục từng người vào đây, rồi gọi xuat_mo_hinh.py
```

`src/`, `data/`, `outputs/` bị ghi đè mỗi lần chạy `dong_bo_du_lieu.py` – muốn sửa thì sửa ở thư mục gốc của từng người.

## Dữ liệu cập nhật thì web cập nhật theo

- Web đọc thẳng các CSV trong `data/`; cache tự làm mới khi file đổi.
- Mô hình dự báo được nạp từ `mo_hinh/*.pkl`. Nếu file không khớp dữ liệu hiện tại (dấu vân tay SHA-256 trong
  `thong_tin.json`) hoặc khác phiên bản scikit-learn, web tự huấn luyện lại (dưới 1 giây) và ghi rõ nguồn ở mục Dự báo.
- Mô hình dựng lại đúng `Quan/dataset_nhom5/src/logistic_model.py` và `clustering.py` (cùng Pipeline, tham số,
  cách chia Train/Test, quy tắc CAR quý 4). Đã đối chiếu với `Quan/dataset_nhom5/outputs/tables`: xác suất, hệ số,
  Accuracy/AUC, nhãn nhóm và tọa độ PCA khớp hoàn toàn.
- Mọi câu kết luận trên web được sinh từ số liệu, nên đổi dữ liệu là câu chữ đổi theo.

## Triển khai Streamlit Community Cloud

Triển khai thẳng từ repo của nhóm, không cần tách thư mục:

1. Chạy `py dong_bo_du_lieu.py` (hoặc `py chay_tat_ca.py`), commit và gộp vào nhánh `main`.
2. Vào https://share.streamlit.io → đăng nhập bằng GitHub → *Create app* → repo `maihan88/nhom5-ngan-hang`,
   branch `main`, **Main file path** = `dashboard/app.py`. Trong *Advanced settings* chọn Python 3.12 hoặc 3.13.
3. Gói cài từ `dashboard/requirements.txt` (cùng thư mục với `app.py`); không cần biến môi trường hay secrets.
4. Giao diện lấy từ `dashboard/.streamlit/config.toml`: Streamlit (từ bản 1.52 trở lên) đọc file cấu hình nằm cạnh
   `app.py` kể cả khi chạy từ thư mục gốc repo, nên không cần chép ra gốc (đã thử bằng
   `streamlit run dashboard/app.py` ở thư mục gốc).
5. Repo đang để riêng tư: app có thể mặc định chỉ người được mời mới xem được; chỉnh quyền xem trong mục *Share*
   của app nếu muốn ai có link cũng mở được.

Sau đó mỗi lần gộp code/dữ liệu mới vào `main`, Cloud tự cập nhật web.
