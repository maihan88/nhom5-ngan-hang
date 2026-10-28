"""
xuat_mo_hinh.py – Huấn luyện 3 mô hình Logistic Regression trên dữ liệu hiện tại và lưu ra thư mục mo_hinh/:

  logistic_tai_chinh.pkl               chỉ 6 chỉ số tài chính
  logistic_tai_chinh_co_su_kien.pkl    + cờ có/không sự kiện doanh nghiệp (phiên bản mặc định trên web)
  logistic_tai_chinh_loai_su_kien.pkl  + số sự kiện theo từng loại
  thong_tin.json                       danh sách và THỨ TỰ biến đầu vào của từng mô hình, ngày xuất, phiên bản
                                       scikit-learn, dấu vân tay dữ liệu, Accuracy/AUC trên năm kiểm chứng

Thiết kế mô hình theo code của Hoàng Mạnh Quân (Quan/dataset_nhom5/src/logistic_model.py), xem web/mo_hinh.py.
Tự chạy ở cuối dong_bo_du_lieu.py; chạy riêng:  python xuat_mo_hinh.py

Dùng lại mô hình ở nơi khác:
    import joblib, json, pandas as pd
    tt = json.load(open("mo_hinh/thong_tin.json", encoding="utf-8"))
    m = joblib.load("mo_hinh/logistic_tai_chinh_co_su_kien.pkl")
    bien = tt["mo_hinh"]["Financial + General Event"]["bien"]
    m.predict_proba(bang[bien])[:, 1]      # bang: DataFrame có đủ các cột trong `bien`
    # Lưu ý: CAR quý 4 phải lấy số quý 3 cùng năm như lúc huấn luyện (web.mo_hinh.du_lieu_du_bao).
"""
from pathlib import Path

GOC = Path(__file__).resolve().parent


def main():
    from src import data_loader as dl
    from web import mo_hinh as mh

    b4 = dl.doc_tong_hop()
    kq = mh.huan_luyen(b4)
    tt = mh.xuat(kq, b4, GOC / "mo_hinh")
    print(f"\nĐã xuất mô hình vào mo_hinh/ (scikit-learn {tt['scikit_learn']}, kiểm chứng năm {tt['nam_test']}):")
    for ten, m in tt["mo_hinh"].items():
        print(f"  {m['file']:40s} {len(m['bien']):2d} biến · Accuracy {m['accuracy_test']:.3f} · AUC {m['auc_test']:.3f}")


if __name__ == "__main__":
    main()
