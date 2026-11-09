"""Cấu hình chung cho pipeline thu thập & làm sạch dữ liệu – Nhóm 5 PTDL.

Mọi hằng số (mã ngân hàng, giai đoạn, mã chỉ tiêu BCTC, từ khóa phân loại sự kiện)
tập trung ở đây để dễ rà soát / chỉnh sửa mà không cần đụng vào logic crawl.
"""
from datetime import date, timedelta
from pathlib import Path
import os

import pandas as pd

# ---------------------------------------------------------------------------
# Phạm vi đề tài
# ---------------------------------------------------------------------------
BANKS = {
    # ma_nh: loai_hinh_so_huu  (phục vụ câu hỏi nghiên cứu 2)
    "VCB": "Quốc doanh",
    "BID": "Quốc doanh",
    "CTG": "Quốc doanh",
    "TCB": "Tư nhân",
    "MBB": "Tư nhân",  # NH TMCP; cổ đông lớn là Viettel/Bộ QP nhưng Nhà nước không nắm chi phối >50%
    "ACB": "Tư nhân",
    "STB": "Tư nhân",
    "VPB": "Tư nhân",
}

START_YEAR = 2021

# Mốc dự báo của mỗi quý = ngày kết thúc quý + LABEL_LAG_DAYS. 45 ngày là hạn chót công bố
# BCTC quý hợp nhất (Thông tư 96/2020/TT-BTC); dữ liệu VNDirect cho thấy BCTC muộn nhất nhập sau 39 ngày.
# Nhãn "quý sau" đo lợi suất từ mốc dự báo của quý t đến mốc dự báo của quý t+1, để mô hình
# chỉ dùng thông tin đã công bố tại thời điểm dự báo.
LABEL_LAG_DAYS = 45


def _ky_cuoi() -> pd.Period:
    """Quý cuối của bộ dữ liệu.

    Mặc định: quý gần nhất đã qua hạn công bố BCTC (cuối quý + LABEL_LAG_DAYS <= hôm nay), nên mỗi lần
    chạy pipeline tự lấy thêm quý mới. Đặt biến môi trường PTDL_DEN_QUY (vd "2025Q4") để chốt cố định –
    dùng khi cần tái lập đúng bộ dữ liệu 2021–2025 của báo cáo.
    """
    chot = os.environ.get("PTDL_DEN_QUY", "").strip().upper()
    if chot:
        return pd.Period(chot, freq="Q")
    ky = pd.Period(date.today(), freq="Q") - 1
    while ky.end_time.date() + timedelta(days=LABEL_LAG_DAYS) > date.today():
        ky -= 1
    return ky


END_PERIOD = _ky_cuoi()
END_YEAR, END_QUARTER = END_PERIOD.year, END_PERIOD.quarter
END_DATE = END_PERIOD.end_time.date()

# Lấy thêm 1 quý trước giai đoạn để tính bình quân (ROA/ROE/NIM) cho Q1/2021,
# và giá đến mốc dự báo của quý sau kỳ cuối để tính nhãn cho kỳ cuối (chưa tới mốc đó thì lấy đến
# hôm nay; nhãn của kỳ cuối khi ấy để trống – xem prices.price_on_or_before).
FIN_FROM = "2020-12-31"
FIN_TO = END_DATE.isoformat()
PRICE_FROM = "2020-12-01"
PRICE_TO = min((END_PERIOD + 1).end_time.date() + timedelta(days=LABEL_LAG_DAYS), date.today()).isoformat()
# Khóa cache giá có ghi ngày cuối, nên PRICE_TO mặc định trượt theo hôm nay làm --offline không tìm thấy cache cũ.
# Đặt biến môi trường PTDL_GIA_DEN (vd "2026-10-28") để chốt ngày cuối của giá khi tái lập một bộ dữ liệu đã có.
if os.environ.get("PTDL_GIA_DEN", "").strip():
    PRICE_TO = min(date.fromisoformat(os.environ["PTDL_GIA_DEN"].strip()), date.fromisoformat(PRICE_TO)).isoformat()
EVENT_FROM = f"{START_YEAR}-01-01"
EVENT_TO = END_DATE.isoformat()

# Khóa cache của các nguồn không ghi khoảng ngày trong khóa (BCTC, chỉ số, sự kiện, tin) được gắn thêm kỳ
# cuối, để khi có quý mới thì tải lại thay vì đọc cache cũ. Bộ cache gốc tải với kỳ cuối Q4/2025 giữ
# khóa cũ (không hậu tố) để `PTDL_DEN_QUY=2025Q4 python run_pipeline.py --offline` vẫn chạy được.
CACHE_TAG = "" if END_DATE == date(2025, 12, 31) else f"_den{FIN_TO}"

# ---------------------------------------------------------------------------
# Thư mục
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"            # cache JSON/HTML gốc (để truy vết & chạy lại không cần tải lại)
INTERIM_DIR = DATA_DIR / "interim"    # dữ liệu đã parse nhưng chưa tổng hợp
OUTPUT_DIR = DATA_DIR / "output"      # bộ dữ liệu bàn giao
MANUAL_DIR = DATA_DIR / "manual"      # file rà soát thủ công sự kiện

# ---------------------------------------------------------------------------
# Nguồn dữ liệu
# ---------------------------------------------------------------------------
VND_API = "https://api-finfo.vndirect.com.vn/v4"   # API công khai phía sau dstock.vndirect.com.vn
CAFEF_EVENTS_URL = "https://cafef.vn/du-lieu/Ajax/Events_RelatedNews_New.aspx"
CAFEF_BASE = "https://cafef.vn"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
}
REQUEST_DELAY_SEC = 0.8   # nghỉ giữa các request để không gây tải cho server
TIMEOUT_SEC = 30
MAX_RETRIES = 4

# ---------------------------------------------------------------------------
# Mã chỉ tiêu BCTC ngân hàng trên VNDirect (TT49/2014/TT-NHNN)
# modelType 101 = Bảng CĐKT, 102 = KQKD. Giá trị gốc tính bằng VND.
# ---------------------------------------------------------------------------
BS_ITEMS = {  # Bảng cân đối kế toán (số dư cuối quý)
    12700: "tong_tai_san",
    14000: "von_chu_so_huu",
    412100: "tong_du_no",               # Cho vay khách hàng (gộp, trước dự phòng)
    413300: "tien_gui_khach_hang",
    # Các khoản mục tài sản sinh lãi – dùng tính NIM
    411200: "tien_gui_nhnn",
    411400: "tien_gui_cho_vay_tctd",
    411500: "chung_khoan_kinh_doanh",
    412300: "chung_khoan_dau_tu",
    700491: "mua_no",
}
IS_ITEMS = {  # Kết quả kinh doanh (số phát sinh trong quý)
    421900: "thu_nhap_lai_thuan",
    23003: "loi_nhuan_sau_thue",
}
# Chỉ giữ chỉ tiêu dùng để tính 6 chỉ số hoặc đối chiếu; các chỉ tiêu khác vẫn còn nguyên trong data/raw.
EARNING_ASSET_COLS = [
    "tien_gui_nhnn", "tien_gui_cho_vay_tctd", "chung_khoan_kinh_doanh",
    "tong_du_no", "chung_khoan_dau_tu", "mua_no",
]

# Chỉ số VNDirect đã tính sẵn (endpoint /ratios) – dùng cho NPL, CAR và đối chiếu
RATIO_CODES = {
    "BAD_LOANS_RATIO_AQ": "npl",                     # Tỷ lệ nợ xấu – theo quý
    "BANK_CAR_AQ": "car",                            # Hệ số an toàn vốn – thường chỉ công bố cuối năm
    "NET_INTEREST_MARGIN_TR_AVG5Q": "nim_ttm_vnd",   # NIM 4 quý gần nhất (đối chiếu)
    "ROAA_TR_AVG5Q": "roa_ttm_vnd",
    "ROAE_TR_AVG5Q": "roe_ttm_vnd",
}

# ---------------------------------------------------------------------------
# Sự kiện phi tài chính
# ---------------------------------------------------------------------------
# Nhãn loai_su_kien theo đúng tài liệu bổ sung GL1
EVENT_LABELS = {
    "tang_von": "Tăng vốn",
    "chuyen_doi_so": "Chuyển đổi số - tiền số",
    "hop_tac_trung_thau": "Hợp tác chiến lược - trúng thầu",
    "doi_lanh_dao": "Đổi lãnh đạo",
    "chinh_sach_nhnn": "Chính sách NHNN",
    "khac": "Khác",  # dùng cho M&A / sáp nhập / chuyển giao bắt buộc
}

# Tin về công ty con / công ty liên kết của ngân hàng (không phải sự kiện của chính ngân hàng)
SUBSIDIARY_PATTERNS = [
    r"công ty con", r"campuchia", r"myanmar", r"\blào\b", r"\bsbl\b", r"\bmbs\b", r"\bacbs\b",
    r"ck acb", r"\bmic\b", r"\bcts\b", r"\btcbs\b", r"\bvpbanks\b", r"\bbsc\b", r"\bfc\b", r"fe credit",
    r"chứng khoán (acb|mb|vietinbank|bidv|techcombank|vpbank|sacombank)",
    r"công ty (tnhh|cổ phần|quản lý|chứng khoán|tài chính|bảo hiểm)",
    r"\bacba\b", r"\bvcbs\b", r"\bvcbm\b", r"cambodia",  # ACB Leasing, CK/Quỹ Vietcombank, MBCambodia
]

# Tiếng Việt có hai cách bỏ dấu (hóa/hoá, tỏa/toả, hủy/huỷ) -> mẫu phải bắt cả hai

# Quy tắc phân loại theo thứ tự ưu tiên (tiêu đề khớp nhóm hợp lệ đầu tiên):
#   any     – khớp ít nhất 1 mẫu thì là ứng viên của nhóm
#   require – (tùy chọn) phải khớp thêm ít nhất 1 mẫu này
#   deny    – khớp mẫu này thì KHÔNG thuộc nhóm (xét tiếp nhóm sau)
EVENT_RULES = [
    ("tang_von", {
        "any": [
            r"tăng vốn", r"vốn điều lệ", r"phát hành (thêm )?cổ phiếu", r"chào bán (thêm )?cổ phiếu",
            r"cổ tức bằng cổ phiếu", r"cổ phiếu thưởng", r"\besop\b", r"chào bán riêng lẻ",
            r"phát hành riêng lẻ", r"nhà đầu tư chiến lược", r"cổ đông chiến lược",
            r"bán \d+([.,]\d+)?% cổ phần", r"quyền mua cổ (phần|phiếu)",
        ],
        # Thủ tục giấy tờ của một đợt tăng vốn đã có -> không tính là sự kiện mới
        "deny": [
            r"ubcknn", r"ủy ban chứng khoán", r"nhận đủ hồ sơ", r"tài liệu báo cáo",
            r"giấy phép (thành lập|hoạt động)", r"gdkhq", r"giao dịch không hưởng quyền",
            r"margin", r"lên đỉnh", r"lãi gấp", *SUBSIDIARY_PATTERNS,
            # Giải tỏa hạn chế chuyển nhượng ESOP không phải phát hành mới
            r"giải t(ỏa|oả)", r"hạn chế chuyển nhượng",
            # Rút / hủy kế hoạch không phải là thực hiện tăng vốn
            r"\brút (nội dung|kế hoạch|phương án|lại)", r"(hủy|huỷ)",
            # "TP" = trái phiếu (không bắt "TP.HCM")
            r"\btp\b(?!\.)",
        ],
    }),
    ("doi_lanh_dao", {
        "any": [
            r"bổ nhiệm", r"miễn nhiệm", r"từ nhiệm", r"thôi (giữ chức|làm|đảm nhiệm)", r"kế nhiệm",
            r"\bbầu\b", r"thay đổi nhân sự", r"\btân (chủ tịch|tổng giám đốc|ceo)",
            r"(chủ tịch|tổng giám đốc|ceo) mới", r"giao quyền", r"người đại diện theo pháp luật",
            r"rời (ghế|vị trí)", r"ngồi ghế",
        ],
        # Chỉ tính lãnh đạo cấp cao của chính ngân hàng
        "require": [
            r"chủ tịch", r"tổng giám đốc", r"\btgđ\b", r"\bceo\b", r"\bhđqt\b",
            r"hội đồng quản trị", r"người đại diện theo pháp luật",
        ],
        "deny": [
            r"phó (tổng giám đốc|tgđ|tổng)", r"bổ nhiệm lại", r"tái bổ nhiệm", r"thư ký",
            r"phụ trách quản trị", r"thống đốc", r"ban kiểm soát", r"kiểm soát viên",
            r"giám đốc (khối|chi nhánh|tài chính|rủi ro|vùng|khu vực)", r"người đại diện (phần )?vốn",
            r"tổng biên tập", r"đề cử", r"ứng cử", r"gdkhq", r"văn phòng", *SUBSIDIARY_PATTERNS,
        ],
    }),
    ("khac", {  # M&A, chuyển giao bắt buộc, thoái vốn
        "any": [
            r"sáp nhập", r"\bm&a\b", r"mua lại ngân hàng", r"chuyển giao bắt buộc",
            r"nhận chuyển giao", r"(?<!phù )hợp nhất (ngân hàng|với)", r"thoái vốn",
        ],
        "deny": [r"khu vực", r"chi nhánh", r"phòng giao dịch", r"lợi nhuận", r"\blãi\b",
                 r"không thoái vốn", r"nhìn lại", r"kể từ (khi|sau)"],  # nhắc lại sự kiện cũ
    }),
    ("chinh_sach_nhnn", {
        "any": [
            r"hạn mức tăng trưởng tín dụng", r"chỉ tiêu tăng trưởng tín dụng", r"room tín dụng",
            r"nới room tín dụng", r"lãi suất điều hành", r"thông tư \d+",
            r"(ngân hàng nhà nước|\bnhnn\b).*(thanh tra|xử phạt|kiểm soát đặc biệt|can thiệp)",
            r"(thanh tra|xử phạt|kiểm soát đặc biệt).*(ngân hàng nhà nước|\bnhnn\b)",
        ],
        "deny": [r"mạng lưới", r"địa chỉ", r"trụ sở", r"giấy phép", r"người đại diện",
                 # Tin phỏng đoán / phát biểu, chưa phải chính sách đã ban hành
                 r"có thể", r"có khả năng", r"dự báo", r"kỳ vọng", r"dùng hết room"],
    }),
    ("hop_tac_trung_thau", {
        "any": [
            r"hợp tác", r"ký kết", r"biên bản ghi nhớ", r"\bmou\b", r"đối tác chiến lược",
            r"liên danh", r"trúng thầu", r"tài trợ vốn", r"cao tốc", r"hợp vốn (cho|tài trợ)",
            r"bancassurance", r"độc quyền phân phối", r"bắt tay",
        ],
        "deny": [
            r"bảo mật thông tin", r"quản lý nợ", r"cấp tín dụng", r"giao dịch vay", r"vay hợp vốn",
            r"bóng đá", r"\bclb\b", r"câu lạc bộ", r"tài trợ (giải|chương trình)", r"phụ lục hợp đồng",
            *SUBSIDIARY_PATTERNS,
        ],
    }),
    ("chuyen_doi_so", {
        "any": [
            r"chuyển đổi số", r"ngân hàng số", r"tiền số", r"tài sản số", r"tài sản mã h(óa|oá)",
            r"tiền mã h(óa|oá)", r"số h(óa|oá)", r"blockchain", r"trí tuệ nhân tạo", r"(ứng dụng|công nghệ|nền tảng|giải pháp) ai\b",
            r"\bgenai\b", r"super ?app", r"digital", r"fintech", r"sandbox", r"sinh trắc học",
            r"\bekyc\b", r"\bcbdc\b",
        ],
    }),
]

# Tin nhắc tới từ N ngân hàng trở lên -> coi là tin ngành, không gán cho riêng ngân hàng nào
INDUSTRY_NEWS_MIN_BANKS = 3

# Tin thường quy cần loại bỏ (kiểm tra TRƯỚC khi phân loại)
EVENT_EXCLUDE = [
    r"báo cáo tài chính", r"\bbctc\b", r"giải trình", r"báo cáo thường niên",
    r"báo cáo (tình hình )?quản trị", r"báo cáo tiến độ sử dụng vốn",
    r"giao dịch cổ phiếu của (người|tổ chức)", r"người nội bộ", r"người có liên quan",
    r"cổ đông lớn", r"chốt danh sách", r"tài liệu họp", r"họp đại hội đồng cổ đông thường niên",
    r"đại hội đồng cổ đông thường niên", r"thư mời", r"biên bản họp",
    r"cổ tức bằng tiền", r"trả cổ tức (năm|đợt)(?!.*cổ phiếu)", r"trái phiếu", r"chứng chỉ tiền gửi",
    r"thay đổi địa điểm", r"chi nhánh", r"phòng giao dịch", r"thuê trụ sở",
    r"quy chế", r"danh sách (người|cổ đông)", r"ủy quyền công bố thông tin",
    r"người phụ trách quản trị", r"kế toán trưởng", r"kiểm toán", r"lãi suất tiền gửi",
    # Thủ tục hành chính phát sinh SAU một đợt tăng vốn – tránh đếm 1 sự kiện thành nhiều lần
    r"niêm yết bổ sung", r"thay đổi đăng ký niêm yết", r"giao dịch bổ sung", r"\bvsdc?\b",
    r"lưu ký", r"đăng ký chứng khoán", r"số lượng chứng khoán đăng ký",
]

# Nhóm sự kiện quyền trên VNDirect coi là "tăng vốn"
VND_CAPITAL_EVENT_TYPES = {"STOCKDIV", "KINDDIV", "ISSUE", "schedIssue"}

# Hai tin cùng ngân hàng, cùng loại, cách nhau <= số ngày này được coi là cùng 1 sự kiện
EVENT_DEDUP_WINDOW_DAYS = 3

# Các loại chỉ tính TỐI ĐA 1 sự kiện / ngân hàng / quý (một đợt tăng vốn kéo dài nhiều
# thông báo: nghị quyết, thông báo phát hành, kết quả... nhưng bản chất là 1 sự kiện)
EVENT_ONE_PER_QUARTER = {"tang_von"}
