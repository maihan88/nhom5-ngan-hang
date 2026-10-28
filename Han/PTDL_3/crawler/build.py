"""Gộp Bảng 1 + 2 + 3 -> Bảng 4, xuất file bàn giao, Data Dictionary và báo cáo kiểm tra."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import config

log = logging.getLogger(__name__)

KEYS = ["ma_nh", "quy", "nam"]

# (cột, mô tả, đơn vị, nguồn / công thức)
DICTIONARY = [
    # --- khóa
    ("ma_nh", "Mã cổ phiếu ngân hàng", "-", "VCB, BID, CTG, TCB, MBB, ACB, STB, VPB"),
    ("quy", "Quý", "-", "Q1..Q4"),
    ("nam", "Năm", "-", f"{config.START_YEAR}..{config.END_YEAR}"),
    ("loai_hinh_so_huu", "Loại hình sở hữu", "-", "Quốc doanh (VCB, BID, CTG) / Tư nhân (còn lại)"),
    # --- Bảng 1
    ("ngay_bctc", "Ngày kết thúc kỳ BCTC", "yyyy-mm-dd", "VNDirect financial_statements"),
    ("tong_tai_san", "Tổng tài sản cuối quý", "tỷ đồng", "BCĐKT – TỔNG CỘNG TÀI SẢN (mã 12700)"),
    ("von_chu_so_huu", "Vốn chủ sở hữu cuối quý", "tỷ đồng", "BCĐKT – Vốn chủ sở hữu (mã 14000)"),
    ("loi_nhuan_sau_thue", "LNST trong quý (hợp nhất)", "tỷ đồng", "KQKD – LNST TNDN (mã 23003), số phát sinh trong quý"),
    ("lnst_cong_ty_me", "LNST của cổ đông công ty mẹ trong quý", "tỷ đồng", "KQKD mã 23000"),
    ("loi_nhuan_truoc_thue", "Lợi nhuận trước thuế trong quý", "tỷ đồng", "KQKD mã 23800"),
    ("tong_du_no", "Dư nợ cho vay khách hàng (gộp, trước dự phòng)", "tỷ đồng", "BCĐKT mã 412100"),
    ("du_phong_cho_vay", "Dự phòng rủi ro cho vay KH (số âm)", "tỷ đồng", "BCĐKT mã 412200"),
    ("tien_gui_khach_hang", "Tiền gửi của khách hàng", "tỷ đồng", "BCĐKT mã 413300"),
    ("thu_nhap_lai_thuan", "Thu nhập lãi thuần trong quý", "tỷ đồng", "KQKD mã 421900"),
    ("tong_thu_nhap_hoat_dong", "Tổng thu nhập hoạt động trong quý", "tỷ đồng", "KQKD mã 421701"),
    ("chi_phi_hoat_dong", "Chi phí hoạt động (quản lý) trong quý", "tỷ đồng", "KQKD mã 22200"),
    ("chi_phi_du_phong", "Chi phí dự phòng rủi ro tín dụng trong quý", "tỷ đồng", "KQKD mã 422900"),
    ("earning_assets", "Tài sản sinh lãi cuối quý", "tỷ đồng",
     "Tiền gửi NHNN + Tiền gửi & cho vay TCTD + CK kinh doanh + Cho vay KH + CK đầu tư + Mua nợ"),
    ("no_xau", "Nợ xấu (ƯỚC TÍNH)", "tỷ đồng", "npl/100 × tong_du_no"),
    ("roa", "ROA năm hóa", "%", "LNST quý × 4 / bình quân(Tổng TS đầu quý, cuối quý) × 100"),
    ("roe", "ROE năm hóa", "%", "LNST quý × 4 / bình quân(VCSH đầu quý, cuối quý) × 100"),
    ("nim", "NIM năm hóa", "%", "Thu nhập lãi thuần quý × 4 / bình quân(TS sinh lãi đầu, cuối quý) × 100"),
    ("npl", "Tỷ lệ nợ xấu (nhóm 3–5 / tổng dư nợ)", "%", "VNDirect ratio BAD_LOANS_RATIO_AQ (tổng hợp từ thuyết minh BCTC)"),
    ("car", "Hệ số an toàn vốn", "%",
     "VNDirect ratio BANK_CAR_AQ. **VNDirect chỉ có 1 số/năm (cuối năm)**; riêng BID, CTG 2022–2024 (VNDirect ghi "
     "đúng 8,00) được thay bằng số tra thủ công có link nguồn trong `data/manual/car_tra_thu_cong.csv`. Các quý khác "
     "(kể cả năm chưa có số) được điền bằng số thật gần nhất trước đó. Xem cột `car_nguon` và báo cáo kiểm tra"),
    ("car_nguon", "Cách có giá trị CAR", "-",
     "cong_bo = số VNDirect đúng kỳ; tra_thu_cong = số nhóm tự tra từ nguồn ngân hàng / công ty chứng khoán "
     "(xem data/manual/car_tra_thu_cong.csv); dien_tiep_ky_truoc = điền tiếp số thật gần nhất"),
    ("ldr", "Tỷ lệ cho vay / tiền gửi KH (hệ số thanh khoản)", "%", "tong_du_no / tien_gui_khach_hang × 100"),
    ("roa_ttm_vnd", "ROAA 4 quý gần nhất (VNDirect, đối chiếu)", "%", "VNDirect ROAA_TR_AVG5Q"),
    ("roe_ttm_vnd", "ROAE 4 quý gần nhất (VNDirect, đối chiếu)", "%", "VNDirect ROAE_TR_AVG5Q"),
    ("nim_ttm_vnd", "NIM 4 quý gần nhất (VNDirect, đối chiếu)", "%", "VNDirect NET_INTEREST_MARGIN_TR_AVG5Q"),
    ("ldr_vnd", "LDR (VNDirect, đối chiếu)", "%", "VNDirect LOANS_TO_DEPOSIT_AQ"),
    # --- Bảng 2
    ("ngay", "Ngày giao dịch (bảng giá ngày)", "yyyy-mm-dd",
     f"VNDirect stock_prices, từ {config.PRICE_FROM} đến {config.PRICE_TO}. Các phiên ngoài "
     f"{config.START_YEAR}–{config.END_YEAR} chỉ dùng để tính giá đầu quý Q1/{config.START_YEAR} và nhãn quý sau; "
     "khi vẽ biểu đồ nên lọc theo giai đoạn nghiên cứu"),
    ("gia_dong_cua", "Giá đóng cửa chưa điều chỉnh (bảng giá ngày)", "nghìn đồng", "close"),
    ("gia_dong_cua_dieu_chinh", "Giá đóng cửa đã điều chỉnh (bảng giá ngày)", "nghìn đồng", "adClose"),
    ("gia_mo_cua_dieu_chinh", "Giá mở cửa đã điều chỉnh (bảng giá ngày)", "nghìn đồng", "adOpen"),
    ("gia_cao_nhat_dieu_chinh", "Giá cao nhất trong phiên, đã điều chỉnh (bảng giá ngày)", "nghìn đồng", "adHigh"),
    ("gia_thap_nhat_dieu_chinh", "Giá thấp nhất trong phiên, đã điều chỉnh (bảng giá ngày)", "nghìn đồng", "adLow"),
    ("khoi_luong_gd", "Khối lượng khớp lệnh (bảng giá ngày)", "cổ phiếu", "nmVolume"),
    ("khoi_luong_thoa_thuan", "Khối lượng giao dịch thỏa thuận (bảng giá ngày)", "cổ phiếu", "ptVolume"),
    ("gia_tri_gd_ty", "Giá trị giao dịch khớp lệnh (bảng giá ngày)", "tỷ đồng", "nmValue / 1e9"),
    ("ngay_dau", "Phiên giao dịch đầu tiên của quý", "yyyy-mm-dd", ""),
    ("ngay_cuoi", "Phiên giao dịch cuối cùng của quý", "yyyy-mm-dd", ""),
    ("so_phien_gd", "Số phiên giao dịch trong quý", "phiên", ""),
    ("gia_dau_quy", "Giá đầu quý (điều chỉnh)", "nghìn đồng", "Giá đóng cửa điều chỉnh phiên cuối của quý trước"),
    ("gia_cuoi_quy", "Giá cuối quý (điều chỉnh)", "nghìn đồng", "Giá đóng cửa điều chỉnh phiên cuối của quý"),
    ("gia_cuoi_quy_chua_dieu_chinh", "Giá cuối quý chưa điều chỉnh", "nghìn đồng", "close phiên cuối quý"),
    ("ty_suat_sinh_loi_quy", "Tỷ suất sinh lời cổ phiếu trong quý", "%", "(gia_cuoi_quy / gia_dau_quy − 1) × 100"),
    ("bien_dong_gia_max_min", "Biên độ dao động giá trong quý", "%", "(giá cao nhất − giá thấp nhất) / giá thấp nhất × 100, giá điều chỉnh"),
    ("gia_max", "Giá cao nhất trong quý (điều chỉnh)", "nghìn đồng", "max adHigh"),
    ("gia_min", "Giá thấp nhất trong quý (điều chỉnh)", "nghìn đồng", "min adLow"),
    ("kl_gd_tb_phien", "KL khớp lệnh bình quân phiên", "cổ phiếu", ""),
    ("tong_kl_gd_quy", "Tổng KL khớp lệnh trong quý", "cổ phiếu", ""),
    ("ty_suat_sinh_loi_quy_sau", "Tỷ suất sinh lời kỳ tiếp theo, tính từ MỐC DỰ BÁO", "%",
     f"Mốc dự báo của quý t = ngày cuối quý t + {config.LABEL_LAG_DAYS} ngày (khi BCTC quý t đã công bố). "
     "Lợi suất = giá tại mốc của quý t+1 / giá tại mốc của quý t − 1, × 100; giá tại mốc = giá đóng cửa "
     "điều chỉnh của phiên cuối cùng trước hoặc đúng ngày mốc. KHÁC `ty_suat_sinh_loi_quy` của quý sau "
     f"(tính theo quý lịch). Giá dùng tính nhãn có đủ trong `bang2a_gia_ngay` (đến {config.PRICE_TO}). "
     "**Không dùng làm biến đầu vào**"),
    ("xu_huong_quy_sau", "Biến mục tiêu: giá kỳ tiếp theo (từ mốc dự báo) tăng?", "0/1",
     "1 nếu ty_suat_sinh_loi_quy_sau > 0, ngược lại 0"),
    # --- Bảng 3
    ("co_su_kien", "Có sự kiện phi tài chính đáng chú ý trong quý", "0/1", "1 nếu so_luong_su_kien > 0"),
    ("so_luong_su_kien", "Số sự kiện trong quý (sau khi gộp tin trùng)", "sự kiện",
     "Tin cùng loại cách nhau ≤ 3 ngày tính là 1; riêng tăng vốn tính tối đa 1 lần/quý"),
    ("loai_su_kien", "Các loại sự kiện trong quý", "-", "; ".join(config.EVENT_LABELS.values())),
    *[(f"sk_{k}", f"Có sự kiện loại '{v}' trong quý hay không", "0/1",
       "Mọi thông báo của cùng một đợt tăng vốn trong quý (nghị quyết, phát hành, kết quả…) gộp làm 1, "
       "nên cột này là biến có/không, KHÔNG phải số đợt tăng vốn")
      if k in config.EVENT_ONE_PER_QUARTER else
      (f"sk_{k}", f"Số sự kiện loại '{v}' trong quý", "sự kiện", "dùng làm biến giả/biến đếm theo nhóm")
      for k, v in config.EVENT_LABELS.items()],
    ("ngay_cong_bo", "Ngày công bố từng sự kiện (cách nhau bởi ;)", "yyyy-mm-dd", ""),
    ("mo_ta_ngan", "Tiêu đề/tóm tắt từng sự kiện (cách nhau bởi |)", "-", ""),
    ("nguon", "Link nguồn từng sự kiện (cách nhau bởi ;)", "URL", "CafeF / VNDirect"),
]

# Bảng 3a dùng lại tên cột của Bảng 3b nhưng mỗi dòng là MỘT sự kiện -> mô tả riêng
DICTIONARY_3A = [
    ("quy", "Quý của ngày công bố sự kiện", "-", "Q1..Q4"),
    ("nam", "Năm của ngày công bố sự kiện", "-", f"{config.START_YEAR}..{config.END_YEAR}"),
    ("ngay_cong_bo", "Ngày giờ đăng tin đầu tiên của sự kiện", "yyyy-mm-dd HH:MM",
     "Tin sớm nhất trong cụm tin đã gộp; 00:00 = nguồn chỉ ghi ngày, không ghi giờ"),
    ("loai_su_kien", "Mã loại sự kiện", "-",
     " / ".join(config.EVENT_LABELS) + ". Phân loại bằng từ khóa trên tiêu đề + rà soát thủ công (data/manual)"),
    ("loai_su_kien_nhan", "Tên loại sự kiện (tiếng Việt)", "-", "; ".join(config.EVENT_LABELS.values())),
    ("mo_ta_ngan", "Tiêu đề tin đại diện của sự kiện", "-", "Tin sớm nhất trong cụm"),
    ("nguon", "Link tin đại diện", "URL", ""),
    ("nguon_du_lieu", "Nguồn của tin đại diện", "-",
     "CafeF / VNDirect-news/<tên báo> / VNDirect-events (sự kiện quyền) / Bổ sung thủ công"),
    ("so_tin_gop", "Số tin thô được gộp thành sự kiện này", "tin",
     f"Cùng NH, cùng loại, cách nhau ≤ {config.EVENT_DEDUP_WINDOW_DAYS} ngày; riêng tăng vốn: cùng quý"),
    ("nguon_khac", "Link các tin còn lại trong cụm (cách nhau bởi ;)", "URL", "Để truy vết; trống nếu so_tin_gop = 1"),
]

# (vai trò, dùng cho, lưu ý khi dùng) – để người phân tích biết cột nào dùng vào việc gì.
# CH1..CH5 = 5 câu hỏi nghiên cứu trong đề xuất của nhóm.
_KEY = ("Khóa nối bảng", "Mọi bảng", "Nối các bảng theo ma_nh + quy + nam")
_RAW = ("Số liệu gốc", "Dashboard (tra cứu), mô tả quy mô",
        "Số tuyệt đối, quy mô các NH chênh nhau nhiều – chuẩn hóa trước khi đưa vào K-Means/PCA")
_RAW_EXTRA = ("Số liệu gốc", "Dashboard; tính thêm chỉ số nếu cần (vd CIR = chi phí HĐ / tổng thu nhập HĐ)", "")
_CHECK = ("Chỉ để đối chiếu", "Kiểm tra chéo với cột tự tính",
          "Trùng thông tin với cột chính – không đưa cùng vào mô hình (đa cộng tuyến)")
_TRACE = ("Mô tả / truy vết", "Dashboard, rà soát", "")
_EVENT_TEXT = ("Mô tả / truy vết", "Dashboard (xem tin), rà soát",
               "Để trống khi co_su_kien = 0 – ô trống hợp lệ, không phải thiếu dữ liệu")
_PRICE = ("Dữ liệu giá", "Biểu đồ xu hướng giá / thanh khoản", "")
_PRICE_Q = ("Biến bổ sung", "Mô tả biến động và thanh khoản; có thể thêm vào mô hình", "")
ROLES = {
    "ma_nh": _KEY, "quy": _KEY, "nam": _KEY,
    "ngay": ("Khóa nối bảng", "Biểu đồ giá",
             f"Có cả phiên ngoài {config.START_YEAR}–{config.END_YEAR} – lọc theo giai đoạn khi vẽ"),
    "loai_hinh_so_huu": ("Biến nhóm", "CH2 (so sánh quốc doanh / tư nhân)",
                         "Chỉ 3 NH quốc doanh và 5 NH tư nhân – các dòng của cùng NH không độc lập; nên kiểm định "
                         "trên trung bình theo NH-năm hoặc ghi rõ hạn chế"),
    "roa": ("Biến phân tích chính", "CH1 (xếp hạng), CH3 (tương quan), CH4–5 (mô hình)",
            "Năm hóa từ 1 quý (×4) nên dao động hơn số TTM; VPB Q1/2022 cao bất thường do lợi nhuận đột biến trong quý"),
    "roe": ("Biến phân tích chính", "CH1 (xếp hạng), CH3 (tương quan), CH4–5 (mô hình)",
            "Năm hóa từ 1 quý (×4) nên dao động hơn số TTM"),
    "nim": ("Biến phân tích chính", "CH2, CH3, CH4–5",
            "Năm hóa từ 1 quý; VPB 2021 > 8% do hợp nhất FE Credit (cho vay tiêu dùng lãi cao)"),
    "npl": ("Biến phân tích chính", "CH2, CH3, CH4–5", ""),
    "car": ("Biến phân tích chính", "CH2, CH3, CH4–5",
            "Chỉ dòng car_nguon = cong_bo hoặc tra_thu_cong là số thật (1 số/năm) – kiểm định CH2 nên chỉ dùng "
            "các dòng này. "
            "Làm biến đầu vào dự báo: dòng Q4 lấy car của Q3 cùng năm"),
    "ldr": ("Biến phân tích chính", "CH3, CH4–5",
            "Tỷ lệ đơn giản cho vay / tiền gửi KH, khác LDR theo quy định NHNN; VPB > 130% vì hợp nhất FE Credit"),
    **{c: _RAW for c in ["tong_tai_san", "von_chu_so_huu", "loi_nhuan_sau_thue", "tong_du_no"]},
    "no_xau": ("Số liệu gốc (ước tính)", "Dashboard", "ƯỚC TÍNH = npl × dư nợ, không phải số công bố"),
    **{c: _RAW_EXTRA for c in ["lnst_cong_ty_me", "loi_nhuan_truoc_thue", "thu_nhap_lai_thuan",
                               "tong_thu_nhap_hoat_dong", "chi_phi_hoat_dong", "chi_phi_du_phong",
                               "tien_gui_khach_hang", "du_phong_cho_vay"]},
    "earning_assets": ("Thành phần tính toán", "Mẫu số của NIM", ""),
    **{c: _CHECK for c in ["roa_ttm_vnd", "roe_ttm_vnd", "nim_ttm_vnd", "ldr_vnd"]},
    "ngay_bctc": _TRACE,
    "car_nguon": ("Mô tả / truy vết", "CH2 (lọc số CAR thật: cong_bo, tra_thu_cong)", ""),
    "gia_dong_cua": ("Chỉ để đối chiếu", "Giá thực tế trên bảng điện",
                     "Giá bị 'rơi' ở ngày GDKHQ khi chia cổ tức bằng cổ phiếu – tính lợi suất phải dùng giá điều chỉnh"),
    **{c: _PRICE for c in ["gia_dong_cua_dieu_chinh", "gia_mo_cua_dieu_chinh", "gia_cao_nhat_dieu_chinh",
                           "gia_thap_nhat_dieu_chinh", "khoi_luong_gd", "khoi_luong_thoa_thuan", "gia_tri_gd_ty"]},
    **{c: _TRACE for c in ["ngay_dau", "ngay_cuoi", "so_phien_gd"]},
    "gia_dau_quy": ("Thành phần tính toán", "Tính ty_suat_sinh_loi_quy", ""),
    "gia_cuoi_quy": ("Thành phần tính toán", "Tính ty_suat_sinh_loi_quy", ""),
    "gia_cuoi_quy_chua_dieu_chinh": ("Chỉ để đối chiếu", "Giá thực tế cuối quý", ""),
    "ty_suat_sinh_loi_quy": ("Biến phân tích chính", "CH3 (tương quan với chỉ số tài chính)",
                             "Tính theo quý lịch – KHÁC ty_suat_sinh_loi_quy_sau"),
    **{c: _PRICE_Q for c in ["bien_dong_gia_max_min", "gia_max", "gia_min", "kl_gd_tb_phien", "tong_kl_gd_quy"]},
    "ty_suat_sinh_loi_quy_sau": ("Nguồn của nhãn", "CH4 (chỉ để hiểu nhãn)",
                                 "KHÔNG dùng làm biến đầu vào – nhãn được tạo trực tiếp từ cột này (rò rỉ 100%)"),
    "xu_huong_quy_sau": ("Biến mục tiêu (nhãn)", "CH4 (Logistic Regression)",
                         "Chia train/test theo thời gian, không chia ngẫu nhiên"),
    "co_su_kien": ("Biến phân tích chính", "CH4 (so sánh mô hình có / không có sự kiện)", ""),
    "so_luong_su_kien": ("Biến phân tích chính", "CH4 (so sánh mô hình có / không có sự kiện)", ""),
    **{f"sk_{k}": ("Biến phân tích chính", "CH4", "") for k in ["tang_von", "doi_lanh_dao", "hop_tac_trung_thau"]},
    **{f"sk_{k}": ("Biến phân tích (hiếm)", "CH4",
                   "Rất ít quý khác 0 (xem cột trung_binh) – không nên ước lượng hệ số riêng; "
                   "dùng co_su_kien / so_luong_su_kien thay thế")
       for k in ["chuyen_doi_so", "chinh_sach_nhnn", "khac"]},
    **{c: _EVENT_TEXT for c in ["loai_su_kien", "ngay_cong_bo", "mo_ta_ngan", "nguon"]},
}
# Bảng 3a: mỗi dòng là 1 sự kiện nên các cột mô tả không bao giờ trống
ROLES_3A = {
    **{c: ("Mô tả / truy vết", "Dashboard (xem tin), rà soát thủ công", "")
       for c in ["ngay_cong_bo", "loai_su_kien", "loai_su_kien_nhan", "mo_ta_ngan", "nguon", "nguon_du_lieu",
                 "so_tin_gop", "nguon_khac"]},
}
# Bảng 4 ghép từ 3 bảng này (theo thứ tự) -> cột lay_tu_bang của từ điển
BANG4_SOURCES = ("bang1_tai_chinh_quy", "bang2b_gia_quy", "bang3b_su_kien_quy")


# ---------------------------------------------------------------------------
def build_bang4(bang1: pd.DataFrame, bang2q: pd.DataFrame, bang3q: pd.DataFrame) -> pd.DataFrame:
    grid = bang3q[KEYS].drop_duplicates()
    df = (grid.merge(bang1, on=KEYS, how="left")
              .merge(bang2q, on=KEYS, how="left")
              .merge(bang3q, on=KEYS, how="left"))
    df["loai_hinh_so_huu"] = df["ma_nh"].map(config.BANKS)
    order = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
    df = df.sort_values(["ma_nh", "nam", "quy"], key=lambda s: s.map(order) if s.name == "quy" else s)
    return df.reset_index(drop=True)


def _fmt(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%Y-%m-%d")
        elif pd.api.types.is_float_dtype(df[c]):
            df[c] = df[c].round(4)
    return df


def save(df: pd.DataFrame, name: str, folder=None, xlsx: bool = False) -> None:
    folder = folder or config.OUTPUT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    df = _fmt(df)
    # utf-8-sig để Excel hiển thị đúng tiếng Việt; ô trống = thiếu dữ liệu (NaN)
    df.to_csv(folder / f"{name}.csv", index=False, encoding="utf-8-sig")
    if xlsx:
        try:
            df.to_excel(folder / f"{name}.xlsx", index=False)
        except ImportError:
            log.warning("Chưa cài openpyxl -> bỏ qua file .xlsx (pip install openpyxl)")
    log.info("Đã ghi %s (%d dòng x %d cột)", name, *df.shape)


def _fmt_num(x) -> str:
    return ("%.4f" % x).rstrip("0").rstrip(".")


def _kind(s: pd.Series, unit: str) -> str:
    if unit.startswith("yyyy"):
        return "ngày giờ" if "HH" in unit else "ngày"
    if unit == "0/1":
        return "0/1"
    if pd.api.types.is_numeric_dtype(s):
        v = s.dropna()
        return "số nguyên" if len(v) and (v == v.round()).all() else "số thực"
    return "văn bản"


def _col_stats(s: pd.Series, kind: str) -> dict:
    """Thống kê nhanh của một cột, tính như khi đọc lại từ CSV (chuỗi rỗng = ô trống)."""
    blank = s.isna() | (s.astype(str).str.strip() == "")
    v = s[~blank]
    out = {"so_dong": len(s), "so_o_trong": int(blank.sum()), "so_gia_tri_khac_nhau": int(v.nunique()),
           "nho_nhat": "", "lon_nhat": "", "trung_binh": "", "vi_du": ""}
    if v.empty:
        return out
    if pd.api.types.is_datetime64_any_dtype(v):
        v = v.dt.strftime("%Y-%m-%d")
    if pd.api.types.is_numeric_dtype(v):
        out.update(nho_nhat=_fmt_num(v.min()), lon_nhat=_fmt_num(v.max()), trung_binh=_fmt_num(v.mean()),
                   vi_du=_fmt_num(v.iloc[0]))
    else:
        if kind.startswith("ngày"):
            out.update(nho_nhat=v.min(), lon_nhat=v.max())
        out["vi_du"] = str(v.iloc[0])[:80]
    return out


def _md(x) -> str:
    return str(x).replace("|", "\\|")


def write_dictionary(tables: dict[str, tuple[str, pd.DataFrame]]) -> None:
    """Từ điển MỌI cột của MỌI bảng bàn giao. `tables`: tên file (không đuôi) -> (tên bảng, DataFrame)."""
    meta = {c: (m, u, s) for c, m, u, s in DICTIONARY}
    meta_3a = {**meta, **{c: (m, u, s) for c, m, u, s in DICTIONARY_3A}}
    rows = []
    for fname, (table, df) in tables.items():
        is_3a = fname == "bang3a_su_kien_chi_tiet"
        for i, c in enumerate(df.columns, start=1):
            m, u, s = (meta_3a if is_3a else meta).get(c, ("", "", ""))
            if not m:
                log.warning("Data Dictionary: chưa có mô tả cho cột %s.%s", fname, c)
            role, use, note = (ROLES_3A.get(c) if is_3a else None) or ROLES.get(c, ("", "", ""))
            src = ""
            if fname == "bang4_tong_hop":
                src = "Khóa" if c in KEYS else next(
                    (tables[t][0] for t in BANG4_SOURCES if t in tables and c in tables[t][1].columns), "")
            kind = _kind(df[c], u)
            rows.append({"file": f"{fname}.csv", "bang": table, "thu_tu": i, "cot": c, "mo_ta": m, "don_vi": u,
                         "kieu_du_lieu": kind, "vai_tro": role, "dung_cho": use, "nguon_cong_thuc": s,
                         "luu_y": note, "lay_tu_bang": src, **_col_stats(df[c], kind)})
    dd = pd.DataFrame(rows)
    dd.to_csv(config.OUTPUT_DIR / "data_dictionary.csv", index=False, encoding="utf-8-sig")

    lines = ["# Data Dictionary – Bộ dữ liệu Nhóm 5 PTDL", "",
             "Bản đầy đủ (mọi cột của mọi file, kèm vai trò, dùng cho câu hỏi nào, lưu ý và thống kê nhanh: "
             "số ô trống, nhỏ nhất, lớn nhất, trung bình, ví dụ) nằm trong `data_dictionary.csv`. "
             "CH1..CH5 = 5 câu hỏi nghiên cứu trong đề xuất.", "",
             "**Quy ước dữ liệu thiếu:** ô trống (NaN) = không có dữ liệu từ nguồn; "
             "KHÔNG tự điền 0 cho biến tài chính/giá. Riêng biến sự kiện: quý không tìm thấy sự kiện = 0.",
             "", "**Khóa nối bảng:** `ma_nh` + `quy` + `nam`. Mỗi dòng Bảng 4 = 1 ngân hàng × 1 quý.", "",
             "**Các cột mô tả sự kiện** (`loai_su_kien`, `ngay_cong_bo`, `mo_ta_ngan`, `nguon`) để trống khi quý "
             "đó không có sự kiện (`co_su_kien = 0`). Đây là ô trống hợp lệ, không phải thiếu dữ liệu.", "",
             "**Lưu ý khi dùng cho mô hình (câu hỏi 4):**",
             "- **Nhãn, KHÔNG được dùng làm biến đầu vào:** `xu_huong_quy_sau` (nhãn) và `ty_suat_sinh_loi_quy_sau` "
             "(nhãn được tạo trực tiếp từ cột này; dùng làm đầu vào là rò rỉ dữ liệu 100%).",
             "- **Chỉ để đối chiếu, trùng thông tin với cột chính:** `roa_ttm_vnd`, `roe_ttm_vnd`, `nim_ttm_vnd`, `ldr_vnd`.",
             "- **Cột mô tả, không phải biến số:** `ngay_bctc`, `ngay_dau`, `ngay_cuoi`, `car_nguon`, "
             "`loai_su_kien`, `ngay_cong_bo`, `mo_ta_ngan`, `nguon`.",
             f"- **Nhãn đã căn thời điểm:** nhãn tính từ mốc dự báo (cuối quý + {config.LABEL_LAG_DAYS} ngày), sau "
             "khi BCTC quý đã công bố, nên các biến tài chính và sự kiện của quý t đều đã biết tại mốc dự báo.",
             "- **Riêng `car`:** CAR năm Y chỉ công bố cùng báo cáo năm, sau mốc dự báo của Q4/Y. Nếu dùng `car` "
             "làm biến đầu vào dự báo, dòng Q4 phải lấy giá trị `car` của dòng Q3 cùng năm.",
             "- **Chia train/test theo thời gian:** nhãn của quý t đã có vào đúng mốc dự báo của quý t+1, nên khi "
             "kiểm tra quý t có thể huấn luyện bằng mọi quý trước đó mà không nhìn trước tương lai.",
             "- **Hạn chế:** VNDirect chỉ lưu bản số liệu BCTC sau cùng (đã soát xét/kiểm toán). Không có bản "
             "công bố ban đầu nên không đo được mức điều chỉnh so với số liệu thị trường biết tại mốc dự báo.", ""]
    for (fname, table), grp in dd.groupby(["file", "bang"], sort=False):
        if fname == "bang4_tong_hop.csv":
            lines += [f"## {table} (`{fname}`)", "",
                      f"Ghép Bảng 1 + Bảng 2b + Bảng 3b theo `ma_nh` + `quy` + `nam`: {len(grp)} cột, mỗi dòng = "
                      "1 ngân hàng × 1 quý. Ý nghĩa từng cột giống ở bảng gốc phía trên; cột `lay_tu_bang` trong "
                      "`data_dictionary.csv` cho biết cột lấy từ bảng nào.", ""]
            continue
        lines += [f"## {table} (`{fname}`)", "",
                  "| Cột | Mô tả | Đơn vị | Nguồn / Công thức | Vai trò |", "|---|---|---|---|---|"]
        lines += [f"| `{r.cot}` | {_md(r.mo_ta)} | {r.don_vi} | {_md(r.nguon_cong_thuc)} | {r.vai_tro} |"
                  for r in grp.itertuples()]
        lines.append("")
    (config.OUTPUT_DIR / "data_dictionary.md").write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
CAR_THAT = ("cong_bo", "tra_thu_cong")  # car_nguon của các ô là số CAR thật (không phải điền tiếp)

RANGES = {  # khoảng hợp lý để phát hiện số liệu bất thường (không tự sửa, chỉ cảnh báo)
    "roa": (-3, 5), "roe": (-30, 45), "nim": (0.5, 8), "npl": (0, 10), "car": (7, 25),
    "ldr": (40, 130), "ty_suat_sinh_loi_quy": (-60, 120),
}


def validation_report(bang4: pd.DataFrame, annual: pd.DataFrame, events_detail: pd.DataFrame,
                      entry: pd.DataFrame | None = None) -> str:
    L = ["# Báo cáo kiểm tra chất lượng dữ liệu", ""]
    n_exp = len(config.BANKS) * (config.END_YEAR - config.START_YEAR + 1) * 4
    L += [f"- Số dòng Bảng 4: **{len(bang4)}** (kỳ vọng {n_exp})", ""]

    L += ["## 1. Số quý có dữ liệu theo ngân hàng", "",
          "| ma_nh | có BCTC | có giá | có NPL | có CAR thật (công bố / tra thủ công) |", "|---|---|---|---|---|"]
    for code, g in bang4.groupby("ma_nh"):
        L.append(f"| {code} | {g['tong_tai_san'].notna().sum()} | {g['gia_cuoi_quy'].notna().sum()} | "
                 f"{g['npl'].notna().sum()} | {g['car_nguon'].isin(CAR_THAT).sum()} |")
    L.append("")

    # Cột mô tả sự kiện được ghi "" khi không có sự kiện -> đọc lại CSV sẽ thành ô trống (NaN)
    event_meta = ["loai_su_kien", "ngay_cong_bo", "mo_ta_ngan", "nguon"]
    no_event = int((bang4["co_su_kien"] == 0).sum())
    miss = bang4.drop(columns=event_meta).isna().sum()
    miss = miss[miss > 0].sort_values(ascending=False)
    L += ["## 2. Số ô thiếu theo cột (Bảng 4)", ""]
    L += ([f"- `{c}`: {v}" for c, v in miss.items()]
          or ["- Các biến số (tài chính, giá, biến đếm sự kiện, nhãn): **không có ô thiếu**."])
    L.append(f"- `{'`, `'.join(event_meta)}`: mỗi cột trống {no_event} ô, đúng bằng {no_event} quý không có "
             "sự kiện (`co_su_kien = 0`). Đây là ô trống hợp lệ, không phải thiếu dữ liệu.")
    that = bang4["car_nguon"].isin(CAR_THAT)
    n_cb, n_tay = int((bang4["car_nguon"] == "cong_bo").sum()), int((bang4["car_nguon"] == "tra_thu_cong").sum())
    years_car = sorted(bang4.loc[that, "nam"].unique())
    L.append(f"- `car`: {bang4['car'].notna().sum()} ô có giá trị, nhưng chỉ {int(that.sum())} ô là số thật "
             f"({n_cb} số VNDirect công bố, {n_tay} số tra thủ công; năm {', '.join(map(str, years_car))}); "
             "còn lại được điền từ số thật gần nhất trước đó (xem `car_nguon`).")
    L.append(f"- `ty_suat_sinh_loi_quy_sau`, `xu_huong_quy_sau`: tính từ mốc dự báo, dùng giá đến "
             f"{config.PRICE_TO} (VNDirect); xem mục 8.")
    L.append("")

    L += ["## 3. Đối chiếu tổng LNST 4 quý với BCTC năm", "",
          "Chênh lệch lớn có thể do số quý bị lũy kế hoặc BCTC năm kiểm toán điều chỉnh.", "",
          "| ma_nh | nam | tổng 4 quý | BCTC năm | lệch % |", "|---|---|---|---|---|"]
    if not annual.empty:
        s = bang4.groupby(["ma_nh", "nam"]).agg(tong=("loi_nhuan_sau_thue", "sum"),
                                                 n=("loi_nhuan_sau_thue", "count")).reset_index()
        chk = s.merge(annual, on=["ma_nh", "nam"], how="inner")
        chk["lech"] = (chk["tong"] / chk["lnst_nam_bctc"] - 1) * 100
        flagged = chk[(chk["lech"].abs() > 2) | (chk["n"] < 4)]
        L += [f"| {r.ma_nh} | {r.nam} | {r.tong:,.0f} | {r.lnst_nam_bctc:,.0f} | {r.lech:.2f} |"
              for r in flagged.itertuples()] or ["| – | – | – | – | Tất cả lệch ≤ 2% |"]
    L.append("")

    L += ["## 4. Giá trị nằm ngoài khoảng hợp lý (cần kiểm tra thủ công, KHÔNG tự sửa)", ""]
    found = False
    for c, (lo, hi) in RANGES.items():
        bad = bang4[(bang4[c] < lo) | (bang4[c] > hi)]
        for r in bad.itertuples():
            found = True
            L.append(f"- {r.ma_nh} {r.quy}/{r.nam}: `{c}` = {getattr(r, c):.3f} (ngoài [{lo}, {hi}])")
    if not found:
        L.append("- Không phát hiện.")
    L.append("")

    L += ["## 4b. CAR: số nghi bị gán và số tra thủ công", "",
          "Kiểm tra theo khoảng ở mục 4 không bắt được số \"tròn đẹp bất thường\". CAR công bố đúng 8,00 (ngưỡng "
          "tối thiểu của NHNN) thường là do nguồn ghi ngưỡng khi ngân hàng chỉ công bố \"tuân thủ\".", ""]
    nghi = bang4[(bang4["car_nguon"] == "cong_bo") & (bang4["car"].round(4) == 8.0)]
    L += ([f"- Cảnh báo: {r.ma_nh} {r.quy}/{r.nam} có `car` = 8,00 -> nên tra thủ công "
           "(ghi vào data/manual/car_tra_thu_cong.csv)" for r in nghi.itertuples()]
          or ["- Không còn số CAR công bố nào đúng 8,00."])
    tay = bang4[bang4["car_nguon"] == "tra_thu_cong"]
    if len(tay):
        L.append("- Số tra thủ công đang dùng (Q4 từng năm): "
                 + ", ".join(f"{r.ma_nh} {r.nam} = {r.car:.2f}" for r in tay.itertuples()))
    L.append("")

    if {"nim", "nim_ttm_vnd"} <= set(bang4.columns):
        d = (bang4["nim"] - bang4["nim_ttm_vnd"]).abs()
        L += ["## 5. Đối chiếu NIM tự tính với NIM VNDirect (TTM)", "",
              f"- Chênh lệch tuyệt đối trung vị: {d.median():.3f} điểm %; lớn nhất: {d.max():.3f} điểm %",
              "- NIM tự tính là năm hóa từ 1 quý nên dao động hơn NIM TTM – đây là khác biệt phương pháp.", ""]

    thin = bang4[bang4["so_phien_gd"] < 50]
    L += ["## 6. Quý có ít phiên giao dịch (< 50)", ""]
    L += [f"- {r.ma_nh} {r.quy}/{r.nam}: {r.so_phien_gd:.0f} phiên" for r in thin.itertuples()] or ["- Không có."]
    L.append("")

    L += ["## 7. Sự kiện phi tài chính", ""]
    if not events_detail.empty:
        tab = events_detail.pivot_table(index="ma_nh", columns="loai_su_kien", values="mo_ta_ngan",
                                        aggfunc="size", fill_value=0)
        L += ["| ma_nh | " + " | ".join(tab.columns) + " |", "|---" * (len(tab.columns) + 1) + "|"]
        L += [f"| {i} | " + " | ".join(str(v) for v in row) + " |" for i, row in tab.iterrows()]
        L += ["", "Phân loại bằng từ khóa trên tiêu đề -> NÊN rà soát `bang3a_su_kien_chi_tiet.csv` "
                  "và ghi điều chỉnh vào thư mục `data/manual/` rồi chạy lại `python run_pipeline.py --offline --xlsx`."]
    L.append("")

    L += ["## 8. Căn thời điểm cho nhãn dự báo", "",
          f"- Mốc dự báo = ngày cuối quý + {config.LABEL_LAG_DAYS} ngày; nhãn = giá tăng hay không từ mốc của "
          "quý t đến mốc của quý t+1."]
    if entry is not None and not entry.empty:
        late = entry[entry["tre_ngay"] > config.LABEL_LAG_DAYS]
        L.append(f"- Ngày VNDirect nhập BCTC quý (lần đầu) trễ sau kỳ: trung vị {entry['tre_ngay'].median():.0f} ngày, "
                 f"muộn nhất {entry['tre_ngay'].max():.0f} ngày.")
        L.append(f"- Số kỳ BCTC nhập SAU mốc dự báo: **{len(late)}**"
                 + ("" if late.empty else " -> " + ", ".join(f"{r.ma_nh} {r.quy}/{r.nam} ({r.tre_ngay} ngày)"
                                                            for r in late.itertuples())))
    miss = bang4[bang4["xu_huong_quy_sau"].isna()]
    L.append(f"- Số dòng thiếu nhãn: **{len(miss)}**"
             + ("" if miss.empty else " -> " + ", ".join(f"{r.ma_nh} {r.quy}/{r.nam}" for r in miss.itertuples())))
    L.append(f"- Tỷ lệ nhãn 'tăng': {bang4['xu_huong_quy_sau'].mean():.1%}")
    L.append("")
    return "\n".join(L)
