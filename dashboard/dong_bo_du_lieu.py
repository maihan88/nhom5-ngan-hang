"""
dong_bo_du_lieu.py – Gom dữ liệu và kết quả mới nhất của cả nhóm vào thư mục dashboard/.

Chạy lại mỗi khi Hân chạy lại pipeline hoặc Nghi/Quân cập nhật kết quả:
    python dong_bo_du_lieu.py

Nguồn (thư mục làm việc của từng người)                          ->  Đích (trong dashboard/)
  Han/PTDL_3/data/output/      6 bảng CSV + data_dictionary.csv     ->  data/
  Nghi/Nhóm5-PTDL/src/         config, data_loader, viz, thong_ke   ->  src/
  Nghi/Nhóm5-PTDL/outputs/     4 bảng kết quả thống kê              ->  outputs/
  Quan/dataset_nhom5/outputs/tables/   bảng kết quả mô hình         ->  outputs/ml/

Cuối cùng chạy xuat_mo_hinh.py để xuất lại mô hình (.pkl) khớp với dữ liệu vừa đồng bộ.
Sau khi đồng bộ, dashboard/ tự chứa đủ mọi thứ để đẩy lên GitHub và chạy trên Streamlit Community Cloud.
"""
from pathlib import Path
import shutil

GOC = Path(__file__).resolve().parent
NHOM = GOC.parent

NGUON = [
    (NHOM / "Han" / "PTDL_3" / "data" / "output", GOC / "data",
     ["bang1_tai_chinh_quy.csv", "bang2a_gia_ngay.csv", "bang2b_gia_quy.csv",
      "bang3a_su_kien_chi_tiet.csv", "bang3b_su_kien_quy.csv", "bang4_tong_hop.csv",
      "data_dictionary.csv"]),
    (NHOM / "Nghi" / "Nhóm5-PTDL" / "src", GOC / "src",
     ["__init__.py", "config.py", "data_loader.py", "viz.py", "thong_ke.py"]),
    (NHOM / "Nghi" / "Nhóm5-PTDL" / "outputs", GOC / "outputs",
     ["thong_ke_mo_ta.csv", "xep_hang_nam.csv", "kiem_dinh_nhom.csv", "tuong_quan.csv"]),
    (NHOM / "Quan" / "dataset_nhom5" / "outputs" / "tables", GOC / "outputs" / "ml",
     ["model_comparison.csv", "logistic_coefficients.csv", "test_predictions.csv",
      "cluster_assignments.csv", "cluster_profiles.csv", "k_selection.csv",
      "pca_explained_variance.csv", "pca_loadings.csv"]),
]


def main():
    thieu = []
    for nguon, dich, ds_file in NGUON:
        dich.mkdir(parents=True, exist_ok=True)
        for ten in ds_file:
            f = nguon / ten
            if not f.exists():
                thieu.append(str(f.relative_to(NHOM)))
                continue
            shutil.copy2(f, dich / ten)
            print(f"  {f.relative_to(NHOM)}  ->  {(dich / ten).relative_to(GOC)}")
    if thieu:
        print("\nThiếu file (bỏ qua):\n  " + "\n  ".join(thieu))
    print("\nĐồng bộ xong.")

    import xuat_mo_hinh      # nhập sau khi đã chép src/ và data/ mới
    xuat_mo_hinh.main()


if __name__ == "__main__":
    main()
