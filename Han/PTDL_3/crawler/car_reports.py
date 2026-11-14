"""CAR cuối năm từ báo cáo công bố thông tin tỷ lệ an toàn vốn của chính ngân hàng.

Vì sao có nguồn này: VNDirect (BANK_CAR_AQ) chỉ có 1 số/năm, từng ghi sai (8,00 cho BID, CTG 2022–2024;
10,02 cho MBB 2021) và từ năm 2025 không còn cập nhật. Báo cáo gốc của ngân hàng (TT41/2016, từ cuối 2025
có ngân hàng tính theo TT14/2025) được Vietstock lưu theo mẫu link cố định – xem CAR_REPORT_URL trong config.

Mỗi (ngân hàng, năm):
  1. Tải PDF báo cáo 31/12 (cache data/raw/car_bao_cao/pdf/, KHÔNG đưa lên Git vì nặng).
  2. File có lớp text -> tự đọc số HỢP NHẤT kỳ 31/12 theo quy tắc cột của từng ngân hàng (CAR_COT_HOP_NHAT).
     File là bản scan, hoặc đọc không ra -> cần nhập tay vào data/manual/car_bao_cao_ngan_hang.csv.
  3. Kết quả (kể cả trạng thái "bản scan") ghi vào data/raw/car_bao_cao/<MÃ>_<NĂM>.json – file nhỏ, có trên Git,
     để chạy --offline ở máy khác không cần PDF.
Số nhập tay luôn được ưu tiên hơn số tự đọc (dùng để sửa khi tự đọc sai).
Không tự sửa, không đoán: đọc không chắc thì để trống và báo trong bao_cao_kiem_tra.md.
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from datetime import date

import pandas as pd
import requests

from . import config
from .http_client import HttpClient

log = logging.getLogger(__name__)

CACHE_DIR = config.RAW_DIR / "car_bao_cao"
PDF_DIR = CACHE_DIR / "pdf"
MANUAL_FILE = config.MANUAL_DIR / "car_bao_cao_ngan_hang.csv"

# Dòng "Tỷ lệ an toàn vốn" (không phải "cấp 1") theo sau ngay bởi 2–4 số phần trăm
_DONG_CAR = re.compile(
    r"(?:t\s*ỷ\s*l\s*ệ\s*an\s*toàn\s*v\s*ố\s*n|\bCAR\b)\s*(?:\(\s*CAR\s*\)|\(\s*%\s*\)|\(\*\))?\s*"
    r"((?:\d{1,2}[.,]\d{1,2}\s*%?\s*){2,4})", re.IGNORECASE)
_SO_PT = re.compile(r"\d{1,2}[.,]\d{1,2}")
_CHU_VIET = re.compile(r"[ạảấầậắằặẹẻếềệịọỏốồộớờợụủứừựỳýđ]")


def _url(ma: str, nam: int, duoi: str) -> str:
    return config.CAR_REPORT_URL.format(nam=nam, ma=ma, duoi=duoi)


def _doc_text(pdf_path) -> str:
    try:
        import pymupdf
    except ImportError:  # bản cũ chỉ có tên fitz
        import fitz as pymupdf
    with pymupdf.open(pdf_path) as doc:
        text = "\n".join(page.get_text() for page in doc)
    # Một số file ghi dấu tách rời (vd "toa" + dấu huyền U+0300) -> gộp về dạng dựng sẵn để so khớp chữ
    return unicodedata.normalize("NFC", text)


def doc_car_hop_nhat(ma: str, text: str) -> tuple[float | None, str, str]:
    """Trả về (CAR hợp nhất %, trạng thái, đoạn trích làm bằng chứng)."""
    if len(_CHU_VIET.findall(text)) < 50:
        return None, "ban_scan", ""
    quy_tac = config.CAR_COT_HOP_NHAT.get(ma)
    if quy_tac is None:
        return None, "khong_co_quy_tac", ""
    t = re.sub(r"\s+", " ", text)
    t = re.sub(r"(\d)\s*([.,])\s*(\d)", r"\1\2\3", t)  # "11 .28" / "11. 53" -> "11.28" / "11.53"
    for m in _DONG_CAR.finditer(t):
        cac_so = [float(s.replace(",", ".")) for s in _SO_PT.findall(m.group(1))]
        if len(cac_so) in quy_tac:
            gia_tri = cac_so[quy_tac[len(cac_so)]]
            trich = t[m.start():m.end()].strip()
            if 5 <= gia_tri <= 25:
                return gia_tri, "doc_duoc", trich
            return None, "ngoai_khoang", trich
    return None, "khong_doc_duoc", ""


def _mot_bao_cao(client: HttpClient, ma: str, nam: int) -> dict:
    cache = CACHE_DIR / f"{ma}_{nam}.json"
    if cache.exists() and not client.refresh:
        return json.loads(cache.read_text(encoding="utf-8"))
    rec = {"ma_nh": ma, "nam": nam, "car": None, "trang_thai": "chua_tai", "nguon": "", "trich": ""}
    if client.offline:
        return rec
    pdf = None
    for duoi in ("pdf", "PDF"):
        url = _url(ma, nam, duoi)
        try:
            pdf = client.get_file(url, PDF_DIR / f"{ma}_{nam}.pdf")
            rec["nguon"] = url
            break
        except requests.HTTPError as exc:
            if exc.response is None or exc.response.status_code != 404:
                log.warning("CAR %s %s: lỗi tải %s (%s)", ma, nam, url, exc)
                return rec | {"trang_thai": "loi_tai"}
    if pdf is None:  # chưa có file: không ghi cache, lần chạy sau thử lại
        return rec | {"trang_thai": "khong_co_file", "nguon": _url(ma, nam, "pdf")}
    if not pdf.read_bytes()[:4] == b"%PDF":
        pdf.unlink()
        return rec | {"trang_thai": "khong_phai_pdf"}
    car, trang_thai, trich = doc_car_hop_nhat(ma, _doc_text(pdf))
    rec.update(car=car, trang_thai=trang_thai, trich=trich)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def _nhap_tay() -> pd.DataFrame:
    if not MANUAL_FILE.exists():
        return pd.DataFrame(columns=["ma_nh", "nam", "car", "nguon"])
    m = pd.read_csv(MANUAL_FILE, encoding="utf-8-sig", dtype={"ma_nh": str})
    m["ma_nh"] = m["ma_nh"].str.strip()
    return m.dropna(subset=["car"])[["ma_nh", "nam", "car", "nguon"]]


def build_car_bao_cao(client: HttpClient) -> pd.DataFrame:
    """Bảng CAR 31/12 từng (ngân hàng, năm) trong giai đoạn: car, cach_lay, trang_thai, nguon, file_pdf."""
    rows = []
    for ma in config.BANKS:
        for nam in range(config.START_YEAR, config.END_YEAR + 1):
            if date(nam, 12, 31) > config.END_DATE:
                continue
            rows.append(_mot_bao_cao(client, ma, nam))
    df = pd.DataFrame(rows)
    df["cach_lay"] = df["car"].notna().map({True: "tu_doc", False: ""})
    df["file_pdf"] = [(PDF_DIR / f"{r.ma_nh}_{r.nam}.pdf").relative_to(config.ROOT).as_posix()
                      for r in df.itertuples()]

    tay = _nhap_tay()
    df = df.merge(tay.rename(columns={"car": "car_tay", "nguon": "nguon_tay"}), on=["ma_nh", "nam"], how="left")
    co_tay = df["car_tay"].notna()
    df["lech_tu_doc_nhap_tay"] = (df["car"] - df["car_tay"]).where(co_tay & df["car"].notna())
    df.loc[co_tay, "car"] = df.loc[co_tay, "car_tay"]
    df.loc[co_tay, "cach_lay"] = "nhap_tay"
    df.loc[co_tay, "nguon"] = df.loc[co_tay, "nguon_tay"].fillna(df.loc[co_tay, "nguon"])
    log.info("CAR báo cáo ngân hàng: %d tự đọc, %d nhập tay, %d chưa có số",
             (df["cach_lay"] == "tu_doc").sum(), co_tay.sum(), df["car"].isna().sum())
    return df.drop(columns=["car_tay", "nguon_tay"])
