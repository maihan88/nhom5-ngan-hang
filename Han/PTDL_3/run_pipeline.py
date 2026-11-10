"""Chạy pipeline thu thập & làm sạch dữ liệu – Nhóm 5 PTDL.

Ví dụ:
    python run_pipeline.py                 # crawl (dùng cache nếu có) + xuất toàn bộ bộ dữ liệu
    python run_pipeline.py --offline       # chỉ dùng cache đã tải, không gửi request (dùng sau khi rà soát thủ công)
    python run_pipeline.py --refresh       # bỏ qua cache, tải lại toàn bộ
    python run_pipeline.py --no-vnd-news   # không lấy tin VNDirect (chỉ CafeF + sự kiện quyền)
"""
from __future__ import annotations

import argparse
import logging
import sys

from crawler import build, config, events, financials, prices
from crawler.http_client import HttpClient


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="tải lại, bỏ qua cache data/raw")
    ap.add_argument("--offline", action="store_true", help="chỉ đọc cache, không gửi request")
    ap.add_argument("--no-vnd-news", action="store_true", help="bỏ nguồn tin VNDirect")
    ap.add_argument("--xlsx", action="store_true", help="xuất thêm file .xlsx (cần openpyxl)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    if args.refresh and args.offline:
        ap.error("--refresh và --offline không dùng cùng nhau")

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    sys.stdout.reconfigure(encoding="utf-8")
    for d in (config.RAW_DIR, config.INTERIM_DIR, config.OUTPUT_DIR, config.MANUAL_DIR):
        d.mkdir(parents=True, exist_ok=True)

    client = HttpClient(refresh=args.refresh, offline=args.offline)

    bang1, annual, ngay_nhap_bctc, doi_chieu_vnd = financials.build_bang1(client)
    bang2_ngay, bang2_quy = prices.build_bang2(client)
    tin_tho, su_kien, bang3_quy = events.build_bang3(client, use_vnd_news=not args.no_vnd_news)
    bang4 = build.build_bang4(bang1, bang2_quy, bang3_quy)

    build.save(tin_tho, "tin_tho_da_phan_loai", folder=config.INTERIM_DIR)
    build.save(bang1, "bang1_tai_chinh_quy", xlsx=args.xlsx)
    build.save(bang2_ngay, "bang2a_gia_ngay")
    build.save(bang2_quy, "bang2b_gia_quy", xlsx=args.xlsx)
    build.save(su_kien, "bang3a_su_kien_chi_tiet", xlsx=args.xlsx)
    build.save(bang3_quy, "bang3b_su_kien_quy", xlsx=args.xlsx)
    build.save(bang4, "bang4_tong_hop", xlsx=args.xlsx)

    build.write_dictionary({
        "bang1_tai_chinh_quy": ("Bảng 1 – Tài chính quý", bang1),
        "bang2a_gia_ngay": ("Bảng 2a – Giá ngày", bang2_ngay),
        "bang2b_gia_quy": ("Bảng 2b – Giá quý", bang2_quy),
        "bang3a_su_kien_chi_tiet": ("Bảng 3a – Sự kiện chi tiết", su_kien),
        "bang3b_su_kien_quy": ("Bảng 3b – Sự kiện quý", bang3_quy),
        "bang4_tong_hop": ("Bảng 4 – Tổng hợp (bàn giao)", bang4),
    })
    report = build.validation_report(bang4, annual, su_kien, ngay_nhap_bctc, doi_chieu_vnd)
    (config.OUTPUT_DIR / "bao_cao_kiem_tra.md").write_text(report, encoding="utf-8")
    logging.info("Hoàn tất. Kết quả trong %s – đọc bao_cao_kiem_tra.md trước khi bàn giao.", config.OUTPUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
