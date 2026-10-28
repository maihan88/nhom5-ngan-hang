"""
config.py – Quy ước dùng chung cho khâu Trực quan hóa & Thống kê (Nhóm 5 PTDL)

Mọi notebook, viz.py và app Streamlit đều import từ file này để màu, thứ tự,
tên chỉ số và giao diện biểu đồ luôn thống nhất. Muốn đổi quy ước thì chỉ sửa ở đây.
"""
from pathlib import Path
import os

import pandas as pd

# ----------------------------------------------------------------------------
# 1. Đường dẫn
# ----------------------------------------------------------------------------
# Có thể đặt biến môi trường PTDL_DATA_DIR để trỏ tới thư mục dữ liệu khác
# (ví dụ trên Streamlit Cloud). Mặc định: <thư mục dự án>/data
THU_MUC_DU_AN = Path(__file__).resolve().parents[1]
THU_MUC_DATA = Path(os.environ.get("PTDL_DATA_DIR", THU_MUC_DU_AN / "data"))
THU_MUC_KET_QUA = THU_MUC_DU_AN / "outputs"          # 4 file CSV kết quả
THU_MUC_HINH = THU_MUC_DU_AN / "outputs" / "figures"  # hình PNG cho báo cáo

TEN_FILE = {
    "tai_chinh_quy": "bang1_tai_chinh_quy.csv",
    "gia_ngay": "bang2a_gia_ngay.csv",
    "gia_quy": "bang2b_gia_quy.csv",
    "su_kien_chi_tiet": "bang3a_su_kien_chi_tiet.csv",
    "su_kien_quy": "bang3b_su_kien_quy.csv",
    "tong_hop": "bang4_tong_hop.csv",
}

# ----------------------------------------------------------------------------
# 2. Giai đoạn nghiên cứu
# ----------------------------------------------------------------------------
# Kỳ cuối lấy theo dữ liệu (bang4), không gán cứng: giai đoạn chỉ quyết định ở END_YEAR của pipeline
# thu thập. Pipeline thêm quý mới thì mọi bảng, biểu đồ và web tự theo, không phải sửa file này.
def _ky_cuoi_trong_du_lieu(mac_dinh=(2025, 4)):
    try:
        b4 = pd.read_csv(THU_MUC_DATA / TEN_FILE["tong_hop"], usecols=["nam", "quy"])
    except (FileNotFoundError, ValueError):
        return mac_dinh
    ky = b4["nam"] * 10 + b4["quy"].str[1].astype(int)
    return int(ky.max() // 10), int(ky.max() % 10)


NAM_BAT_DAU = 2021
NAM_KET_THUC, QUY_CUOI = _ky_cuoi_trong_du_lieu()
NGAY_BAT_DAU = "2021-01-01"
NGAY_KET_THUC = str(pd.Period(f"{NAM_KET_THUC}Q{QUY_CUOI}").end_time.date())
DS_NAM = list(range(NAM_BAT_DAU, NAM_KET_THUC + 1))
SO_QUY = (NAM_KET_THUC - NAM_BAT_DAU) * 4 + QUY_CUOI   # 20 với dữ liệu 2021–2025
DS_QUY = ["Q1", "Q2", "Q3", "Q4"]

# ----------------------------------------------------------------------------
# 3. Ngân hàng, nhóm sở hữu và THỨ TỰ hiển thị cố định
# ----------------------------------------------------------------------------
NHOM_QUOC_DOANH = "Quốc doanh"
NHOM_TU_NHAN = "Tư nhân"
DS_NHOM = [NHOM_QUOC_DOANH, NHOM_TU_NHAN]

# Quốc doanh đứng trước, sau đó tư nhân (theo thứ tự trong Data Dictionary)
DS_NGAN_HANG = ["VCB", "BID", "CTG", "TCB", "MBB", "ACB", "STB", "VPB"]
NHOM_CUA_NH = {nh: (NHOM_QUOC_DOANH if nh in ("VCB", "BID", "CTG") else NHOM_TU_NHAN)
               for nh in DS_NGAN_HANG}

TEN_DAY_DU = {
    "VCB": "Vietcombank", "BID": "BIDV", "CTG": "VietinBank",
    "TCB": "Techcombank", "MBB": "MB Bank", "ACB": "ACB",
    "STB": "Sacombank", "VPB": "VPBank",
}

# ----------------------------------------------------------------------------
# 4. BẢNG MÀU CỐ ĐỊNH
# ----------------------------------------------------------------------------
# Quốc doanh: 3 sắc độ xanh dương (nhìn là biết cùng nhóm).
# Tư nhân: 5 màu khác hẳn tông xanh dương, đủ phân biệt kể cả khi in đen trắng
# nhờ khác độ sáng. Không dùng màu thương hiệu vì nhiều ngân hàng cùng màu xanh.
MAU_NGAN_HANG = {
    "VCB": "#0B3C6E",  # xanh navy đậm
    "BID": "#2F6DB5",  # xanh dương vừa
    "CTG": "#7CB3E6",  # xanh dương nhạt
    "TCB": "#C8323C",  # đỏ
    "MBB": "#E69F00",  # cam hổ phách
    "ACB": "#009E73",  # xanh lục
    "STB": "#7B4EA3",  # tím
    "VPB": "#8C6D31",  # nâu ô liu
}
MAU_NHOM = {
    NHOM_QUOC_DOANH: "#2F6DB5",  # trùng tông với nhóm quốc doanh
    NHOM_TU_NHAN: "#E07B39",     # cam
}
MAU_TRUNG_TINH = "#7F7F7F"        # đường tham chiếu, trung bình ngành
MAU_TANG, MAU_GIAM = "#2CA02C", "#D62728"   # dùng cho lợi suất dương/âm

# Chuỗi màu cho loại sự kiện (bang3a.loai_su_kien_nhan)
DS_LOAI_SU_KIEN = ["Tăng vốn", "Đổi lãnh đạo", "Hợp tác chiến lược - trúng thầu",
                   "Chuyển đổi số - tiền số", "Chính sách NHNN", "Khác"]
MAU_SU_KIEN = dict(zip(DS_LOAI_SU_KIEN,
                       ["#4E79A7", "#F28E2B", "#59A14F", "#B07AA1", "#E15759", "#BAB0AC"]))

# ----------------------------------------------------------------------------
# 5. Chỉ số: tên hiển thị + đơn vị (dùng cho tiêu đề trục, bảng kết quả)
# ----------------------------------------------------------------------------
DS_CHI_SO = ["roa", "roe", "nim", "npl", "car", "ldr"]

# Giá trị car_nguon được coi là SỐ CAR THẬT (32 giá trị cuối năm 2021–2024):
#   cong_bo      = số VNDirect đúng kỳ
#   tra_thu_cong = số nhóm tự tra từ nguồn ngân hàng/CTCK (BID, CTG 2022–2024, thay số 8,00 của VNDirect)
# Còn lại (dien_tiep_ky_truoc) là số điền tiếp, không dùng để so sánh/kiểm định.
CAR_NGUON_SO_THAT = ("cong_bo", "tra_thu_cong")
NHAN_CHI_SO = {
    "roa": "ROA (%)",
    "roe": "ROE (%)",
    "nim": "NIM (%)",
    "npl": "Tỷ lệ nợ xấu – NPL (%)",
    "car": "Hệ số an toàn vốn – CAR (%)",
    "ldr": "Tỷ lệ cho vay/tiền gửi – LDR (%)",
    "ty_suat_sinh_loi_quy": "Lợi suất cổ phiếu trong quý (%)",
    "bien_dong_gia_max_min": "Biên độ giá trong quý (%)",
    "gia_dong_cua_dieu_chinh": "Giá đóng cửa điều chỉnh (nghìn đồng)",
    "gia_chuan_hoa": "Giá điều chỉnh (đầu 2021 = 100)",
    "khoi_luong_gd": "Khối lượng khớp lệnh (cổ phiếu)",
    "so_luong_su_kien": "Số sự kiện",
    "roa_nam": "ROA năm (%)",
    "roe_nam": "ROE năm (%)",
}
# Tên ngắn (dùng cho trục heatmap, nhãn gọn)
TEN_NGAN = {"roa": "ROA", "roe": "ROE", "nim": "NIM", "npl": "NPL", "car": "CAR", "ldr": "LDR",
            "ty_suat_sinh_loi_quy": "Lợi suất quý", "bien_dong_gia_max_min": "Biên độ giá"}

# Chiều "tốt": +1 = càng cao càng tốt, -1 = càng thấp càng tốt, 0 = không đơn điệu
CHIEU_TOT = {"roa": 1, "roe": 1, "nim": 1, "npl": -1, "car": 1, "ldr": 0}

# ----------------------------------------------------------------------------
# 6. Giao diện biểu đồ plotly chung
# ----------------------------------------------------------------------------
FONT = "Arial, 'Helvetica Neue', sans-serif"
KICH_THUOC_PNG = dict(width=1000, height=560, scale=2)   # hình báo cáo


def ap_dung_giao_dien(fig, tieu_de=None, truc_x=None, truc_y=None, chu_thich="Ngân hàng"):
    """Áp giao diện thống nhất cho MỌI biểu đồ plotly rồi trả lại fig.

    Mọi hàm ve_* trong viz.py gọi hàm này ở cuối, trước khi return.
    """
    fig.update_layout(
        template="plotly_white",
        font=dict(family=FONT, size=13, color="#222"),
        title=dict(text=tieu_de, x=0.01, xanchor="left", font=dict(size=17)) if tieu_de else None,
        legend=dict(title=chu_thich, orientation="v", yanchor="top", y=1, x=1.01),
        margin=dict(l=60, r=20, t=60 if tieu_de else 30, b=50),
        hovermode="x unified",
    )
    if truc_x is not None:
        fig.update_xaxes(title_text=truc_x)
    if truc_y is not None:
        fig.update_yaxes(title_text=truc_y)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E5E5E5", zeroline=False)
    return fig


def luu_hinh(fig, ten_file, thu_muc=None):
    """Xuất PNG cho báo cáo (cần kaleido). Tách riêng khỏi hàm vẽ để Streamlit không ghi file."""
    thu_muc = Path(thu_muc or THU_MUC_HINH)
    thu_muc.mkdir(parents=True, exist_ok=True)
    duong_dan = thu_muc / f"{ten_file}.png"
    fig.write_image(duong_dan, **KICH_THUOC_PNG)
    return duong_dan
