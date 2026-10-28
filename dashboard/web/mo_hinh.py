"""
mo_hinh.py – Mô hình dự báo và phân nhóm của dashboard, theo đúng code của Hoàng Mạnh Quân
(Quan/dataset_nhom5/src/logistic_model.py, clustering.py, utils.py).

Mô hình được xuất ra file .pkl kèm danh sách và thứ tự biến (xuat_mo_hinh.py, tự chạy cuối dong_bo_du_lieu.py).
Web ưu tiên nạp các file này; nếu file không khớp dữ liệu hiện tại hoặc khác phiên bản scikit-learn (thường gặp
khi triển khai lên máy khác) thì tự huấn luyện lại theo đúng thiết kế dưới đây – mất chưa tới 1 giây.
Đã đối chiếu với Quan/.../outputs/tables: xác suất Test, hệ số, Accuracy/AUC, nhãn cụm, tọa độ PCA khớp.

Logistic (logistic_model.py):
  • Pipeline = ColumnTransformer(StandardScaler cho 6 biến tài chính, giữ nguyên biến sự kiện)
               + LogisticRegression(max_iter=1000, random_state=42)  (L2, C = 1, ngưỡng 0,5)
  • Train = các năm trước năm cuối có nhãn, Test = năm cuối (2021–2024 / 2025 với dữ liệu hiện tại)
  • CAR đầu vào dự báo: quý 4 dùng CAR quý 3 cùng năm (utils.prediction_data)
  • Mốc so sánh: DummyClassifier(most_frequent)
K-Means + PCA (clustering.py): chuẩn hóa 6 chỉ số trên toàn bộ mẫu (CAR gốc), thử K = 2..6,
  chọn K theo silhouette cao nhất; PCA 2 chiều trên cùng ma trận.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score, silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FIN = ["roa", "roe", "nim", "npl", "car", "ldr"]
CAT = ["sk_tang_von", "sk_chuyen_doi_so", "sk_hop_tac_trung_thau", "sk_doi_lanh_dao", "sk_chinh_sach_nhnn", "sk_khac"]
KEY = ["ma_nh", "quy", "nam"]
NHAN = "xu_huong_quy_sau"

MO_HINH = {
    "Financial Only": FIN,
    "Financial + General Event": FIN + ["co_su_kien"],
    "Financial + Event Categories": FIN + CAT,
}
# Phiên bản hiển thị mặc định: tài chính + cờ có/không sự kiện – đúng mô hình đề tài đề xuất
# (bổ sung yếu tố phi tài chính theo góp ý GVHD). Người xem đổi được ở trang Dự báo.
MAC_DINH = "Financial + General Event"
TEN_FILE = {"Financial Only": "logistic_tai_chinh", "Financial + General Event": "logistic_tai_chinh_co_su_kien",
            "Financial + Event Categories": "logistic_tai_chinh_loai_su_kien"}
TEN_VIET = {
    "Baseline": "Luôn đoán “tăng”",
    "Financial Only": "Chỉ số tài chính",
    "Financial + General Event": "Tài chính + có sự kiện",
    "Financial + Event Categories": "Tài chính + từng loại sự kiện",
}
TEN_BIEN = {
    "roa": "ROA", "roe": "ROE", "nim": "NIM", "npl": "Nợ xấu", "car": "CAR", "ldr": "LDR",
    "co_su_kien": "Có sự kiện", "sk_tang_von": "Tăng vốn", "sk_chuyen_doi_so": "Chuyển đổi số",
    "sk_hop_tac_trung_thau": "Hợp tác, trúng thầu", "sk_doi_lanh_dao": "Đổi lãnh đạo",
    "sk_chinh_sach_nhnn": "Chính sách NHNN", "sk_khac": "Sự kiện khác",
}
TEN_DE_HIEU = {"roa": "ROA", "roe": "ROE", "nim": "biên lãi", "npl": "nợ xấu", "car": "vốn đệm", "ldr": "cho vay/huy động"}


def _chuoi(d):
    d = d.copy()
    for c in ["ma_nh", "quy", "loai_hinh_so_huu"]:
        if c in d:
            d[c] = d[c].astype(str)
    return d


def du_lieu_du_bao(b4):
    """utils.prediction_data của Quân: CAR quý 4 lấy CAR quý 3 cùng năm (số cuối năm chưa công bố tại mốc dự báo)."""
    d = _chuoi(b4).sort_values(["ma_nh", "nam", "quy"]).reset_index(drop=True)
    q3 = d[d["quy"] == "Q3"].set_index(["ma_nh", "nam"])["car"]
    la_q4 = d["quy"] == "Q4"
    d.loc[la_q4, "car"] = [q3.get((m, n), np.nan) for m, n in zip(d.loc[la_q4, "ma_nh"], d.loc[la_q4, "nam"])]
    return d


def _pipeline(bien):
    su_kien = [c for c in bien if c not in FIN]
    xu_ly = ColumnTransformer([("financial", StandardScaler(), FIN), ("events", "passthrough", su_kien)],
                              verbose_feature_names_out=False)
    return Pipeline([("preprocess", xu_ly), ("model", LogisticRegression(max_iter=1000, random_state=42))])


def _danh_gia(y, du_doan, xac_suat):
    return {"Accuracy": accuracy_score(y, du_doan), "Precision": precision_score(y, du_doan, zero_division=0),
            "Recall": recall_score(y, du_doan, zero_division=0), "F1": f1_score(y, du_doan, zero_division=0),
            "ROC-AUC": roc_auc_score(y, xac_suat) if y.nunique() > 1 else np.nan}


def huan_luyen(b4, co_san=None):
    """Huấn luyện mốc so sánh + 3 mô hình (hoặc dùng `co_san` = {tên: Pipeline} đã nạp từ file .pkl) rồi đánh giá
    trên năm kiểm chứng. Trả về dict: du_lieu (bản dự báo, đủ 160 dòng), nam_test, n_train, n_test,
    mo_hinh {tên: Pipeline}, danh_gia (DataFrame), du_doan_test (DataFrame), nguon (mô tả nguồn mô hình)."""
    d = du_lieu_du_bao(b4)
    co_nhan = d.dropna(subset=[NHAN] + FIN)
    nam_test = int(co_nhan["nam"].max())
    train, test = co_nhan[co_nhan["nam"] < nam_test], co_nhan[co_nhan["nam"] == nam_test]
    ytr, yte = train[NHAN].astype(int), test[NHAN].astype(int)

    goc = DummyClassifier(strategy="most_frequent", random_state=42).fit(train[FIN], ytr)
    dong = [{"mo_hinh": "Baseline", **_danh_gia(yte, goc.predict(test[FIN]), goc.predict_proba(test[FIN])[:, 1])}]
    mo_hinh, du_doan = {}, []
    for ten, bien in MO_HINH.items():
        m = co_san[ten] if co_san else _pipeline(bien).fit(train[bien], ytr)
        p = m.predict_proba(test[bien])[:, 1]
        mo_hinh[ten] = m
        dong.append({"mo_hinh": ten, **_danh_gia(yte, (p >= 0.5).astype(int), p)})
        du_doan.append(test[KEY + ["ky", NHAN, "ty_suat_sinh_loi_quy_sau"]].assign(mo_hinh=ten, xac_suat=p))
    danh_gia = pd.DataFrame(dong)
    danh_gia["ten"] = danh_gia["mo_hinh"].map(TEN_VIET)
    return {"du_lieu": d, "nam_test": nam_test, "n_train": len(train), "n_test": len(test), "mo_hinh": mo_hinh,
            "danh_gia": danh_gia, "du_doan_test": pd.concat(du_doan, ignore_index=True),
            "nguon": "huấn luyện khi khởi động"}


# ----------------------------------------------------------------------------
# Xuất / nạp file .pkl
# ----------------------------------------------------------------------------
def van_tay_du_lieu(b4):
    """SHA-256 của đúng các cột mô hình dùng – để biết file .pkl có được huấn luyện trên dữ liệu hiện tại không."""
    d = du_lieu_du_bao(b4)
    cot = KEY + FIN + CAT + ["co_su_kien", NHAN]
    return hashlib.sha256(d[cot].round(8).to_csv(index=False).encode()).hexdigest()


def xuat(kq, b4, thu_muc):
    """Lưu 3 mô hình Logistic ra .pkl và thong_tin.json (danh sách, thứ tự biến; dữ liệu và phiên bản dùng để huấn luyện)."""
    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)
    thong_tin = {
        "mo_ta": "Logistic Regression dự báo giá quý sau tăng/không tăng – thiết kế theo Quan/dataset_nhom5/src/logistic_model.py",
        "ngay_xuat": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "scikit_learn": sklearn.__version__,
        "van_tay_du_lieu": van_tay_du_lieu(b4),
        "nam_test": kq["nam_test"], "n_train": kq["n_train"], "n_test": kq["n_test"],
        "nhan": NHAN, "mo_hinh": {},
    }
    for ten, m in kq["mo_hinh"].items():
        joblib.dump(m, thu_muc / f"{TEN_FILE[ten]}.pkl")
        dg = kq["danh_gia"].set_index("mo_hinh").loc[ten]
        thong_tin["mo_hinh"][ten] = {"file": f"{TEN_FILE[ten]}.pkl", "ten": TEN_VIET[ten], "bien": MO_HINH[ten],
                                     "accuracy_test": round(float(dg["Accuracy"]), 4),
                                     "auc_test": round(float(dg["ROC-AUC"]), 4)}
    (thu_muc / "thong_tin.json").write_text(json.dumps(thong_tin, ensure_ascii=False, indent=2), encoding="utf-8")
    return thong_tin


def nap_hoac_huan_luyen(b4, thu_muc):
    """Nạp mô hình từ .pkl nếu khớp dữ liệu và phiên bản scikit-learn; ngược lại huấn luyện lại. Kết quả giống huan_luyen."""
    thu_muc = Path(thu_muc)
    try:
        tt = json.loads((thu_muc / "thong_tin.json").read_text(encoding="utf-8"))
        if tt["van_tay_du_lieu"] != van_tay_du_lieu(b4):
            ly_do = "dữ liệu mới hơn file .pkl"
        elif tt["scikit_learn"] != sklearn.__version__:
            ly_do = f"file .pkl tạo bằng scikit-learn {tt['scikit_learn']}, máy này dùng {sklearn.__version__}"
        else:
            co_san = {}
            for ten, bien in MO_HINH.items():
                if tt["mo_hinh"][ten]["bien"] != bien:
                    raise ValueError(f"danh sách biến của {ten} không khớp")
                co_san[ten] = joblib.load(thu_muc / tt["mo_hinh"][ten]["file"])
            kq = huan_luyen(b4, co_san=co_san)
            kq["nguon"] = f"nạp từ file .pkl (xuất {tt['ngay_xuat']})"
            return kq
    except FileNotFoundError:
        ly_do = "chưa có file .pkl"
    except Exception as loi:          # file hỏng, thiếu khóa… -> không để web chết, huấn luyện lại
        ly_do = f"không đọc được file .pkl ({loi})"
    kq = huan_luyen(b4)
    kq["nguon"] = f"huấn luyện lại khi khởi động ({ly_do})"
    return kq


def xac_suat(kq, ten, dong):
    """Xác suất giá quý sau tăng cho các dòng của bảng dự báo."""
    return kq["mo_hinh"][ten].predict_proba(dong[MO_HINH[ten]])[:, 1]


def dong_gop(kq, ten, dong):
    """Đóng góp của từng biến vào log-odds cho 1 dòng: hệ số × giá trị đã qua bước chuẩn hóa của pipeline."""
    m, bien = kq["mo_hinh"][ten], MO_HINH[ten]
    x = m.named_steps["preprocess"].transform(dong[bien])[0]
    ten_cot = m.named_steps["preprocess"].get_feature_names_out()
    he_so = m.named_steps["model"].coef_[0]
    goc = dong[bien].iloc[0]
    return pd.DataFrame({"bien": ten_cot, "ten": [TEN_BIEN[b] for b in ten_cot], "gia_tri": [goc[b] for b in ten_cot],
                         "he_so": he_so, "dong_gop": he_so * x}), float(m.named_steps["model"].intercept_[0])


def he_so(kq):
    dong = []
    for ten, m in kq["mo_hinh"].items():
        for b, h in zip(m.named_steps["preprocess"].get_feature_names_out(), m.named_steps["model"].coef_[0]):
            dong.append({"mo_hinh": ten, "bien": b, "ten": TEN_BIEN[b], "he_so": h})
    return pd.DataFrame(dong)


# ----------------------------------------------------------------------------
# Phân nhóm (clustering.py)
# ----------------------------------------------------------------------------
def _ten_nhom(z_tam):
    top = z_tam.abs().nlargest(2).index
    s = " · ".join(f"{TEN_DE_HIEU[b]} {'cao' if z_tam[b] > 0 else 'thấp'}" for b in top)
    return s[0].upper() + s[1:]


def phan_nhom(b4):
    d = _chuoi(b4).sort_values(["ma_nh", "nam", "quy"]).dropna(subset=FIN).reset_index(drop=True)
    x = StandardScaler().fit_transform(d[FIN])
    chon_k, ung_vien = [], {}
    for k in range(2, 7):
        km = KMeans(n_clusters=k, random_state=42, n_init="auto").fit(x)
        ung_vien[k] = km
        chon_k.append({"K": k, "Inertia": km.inertia_, "Silhouette": silhouette_score(x, km.labels_),
                       "Nhóm nhỏ nhất": int(np.bincount(km.labels_).min())})
    chon_k = pd.DataFrame(chon_k)
    k = int(chon_k.loc[chon_k["Silhouette"].idxmax(), "K"])
    d["cum"] = ung_vien[k].labels_
    pca = PCA(n_components=2, random_state=42)
    toa_do = pca.fit_transform(x)
    d["PC1"], d["PC2"] = toa_do[:, 0], toa_do[:, 1]

    z = (d.groupby("cum")[FIN].mean() - d[FIN].mean()) / d[FIN].std(ddof=0)
    chu = {c: chr(65 + i) for i, c in enumerate(d["cum"].value_counts().index)}   # A = nhóm đông nhất
    d["nhom"] = d["cum"].map(chu)
    d["ten_nhom"] = d["cum"].map({c: _ten_nhom(z.loc[c]) for c in z.index})
    ho_so = d.groupby("nhom").agg(**{c: (c, "mean") for c in FIN}, so_quan_sat=("cum", "size"),
                                  ten_nhom=("ten_nhom", "first")).reset_index()
    z.index = z.index.map(chu)
    return {"du_lieu": d, "ho_so": ho_so, "z": z.sort_index(), "k": k, "chon_k": chon_k,
            "tai_trong": pd.DataFrame(pca.components_.T, index=FIN, columns=["PC1", "PC2"]),
            "phuong_sai": pca.explained_variance_ratio_}
