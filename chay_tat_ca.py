"""
chay_tat_ca.py – Một lệnh chạy lại toàn bộ dự án Nhóm 5, từ thu thập dữ liệu đến web.

    py chay_tat_ca.py                  # thu thập tới quý mới nhất -> thống kê -> ML -> đồng bộ dashboard
    py chay_tat_ca.py --den-quy 2026Q3 --gia-den 2026-11-14 --offline   # tái lập đúng bộ dữ liệu của báo cáo, không cần mạng
    py chay_tat_ca.py --refresh        # bỏ cache, tải lại toàn bộ dữ liệu mới từ nguồn
    py chay_tat_ca.py --offline        # chỉ dùng cache (vd sau khi sửa tay data/manual/ của Hân)
    py chay_tat_ca.py --bo-thu-thap    # không crawl, dùng luôn data/output hiện có của Hân
    py chay_tat_ca.py --mo-web         # chạy xong thì mở web luôn (streamlit run)

Các bước, bước nào lỗi thì dừng ngay (web giữ nguyên bản cũ, không bị trộn dữ liệu mới với kết quả cũ):
  1. Hân   Han/PTDL_3/run_pipeline.py                 -> Han/PTDL_3/data/output/
  2. Chép 6 CSV + data_dictionary.md của Hân sang Nghi/Nhóm5-PTDL/data/ và Quan/dataset_nhom5/
  3. Nghi  chạy lần lượt các notebook 01 -> 06       -> Nghi/Nhóm5-PTDL/outputs/
  4. Quân  Quan/dataset_nhom5/src/run_pipeline.py     -> Quan/dataset_nhom5/outputs/
  5. Web   dashboard/dong_bo_du_lieu.py               -> dashboard/ (dữ liệu, kết quả, mô hình .pkl)

Notebook của Nghi được chạy bằng chính Python này (không cần Jupyter): mỗi notebook một tiến trình riêng,
chạy từng ô code theo thứ tự, tắt fig.show() và display(). Ô chỉ để vẽ/lưu hình (cần kaleido + Chrome)
mà lỗi thì chỉ cảnh báo, không dừng; ô tính toán hay xuất bảng kết quả mà lỗi thì dừng.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

GOC = Path(__file__).resolve().parent
HAN = GOC / "Han" / "PTDL_3"
NGHI = GOC / "Nghi" / "Nhóm5-PTDL"
QUAN = GOC / "Quan" / "dataset_nhom5"
WEB = GOC / "dashboard"

FILE_DU_LIEU = ["bang1_tai_chinh_quy.csv", "bang2a_gia_ngay.csv", "bang2b_gia_quy.csv",
                "bang3a_su_kien_chi_tiet.csv", "bang3b_su_kien_quy.csv", "bang4_tong_hop.csv",
                "data_dictionary.md"]
NOTEBOOK_NGHI = ["01_chuan_bi_du_lieu", "02_bieu_do_so_sanh", "03_cau1_sinh_loi",
                 "04_cau2_kiem_dinh", "05_cau3_tuong_quan", "06_tong_hop"]
NOTEBOOK_CHI_VE_HINH = {"02_bieu_do_so_sanh"}
KET_QUA_NGHI = ["thong_ke_mo_ta.csv", "xep_hang_nam.csv", "kiem_dinh_nhom.csv", "tuong_quan.csv"]
# Ô có các chữ này chỉ vẽ/ghép/chép hình -> lỗi thì bỏ qua
DAU_HIEU_O_PHU = ["THU_MUC_HINH", "from PIL"]
# Ô gọi script không còn trong repo (06_tong_hop gọi chay_lai_toan_bo.py) -> không chạy
DAU_HIEU_O_BO = ["chay_lai_toan_bo"]

MOI_TRUONG = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg"}


class LoiBuoc(Exception):
    pass


def chay(lenh, thu_muc):
    print(f"  $ {' '.join(str(x) for x in lenh)}   (trong {thu_muc.relative_to(GOC)})", flush=True)
    kq = subprocess.run([str(x) for x in lenh], cwd=thu_muc, env=MOI_TRUONG)
    if kq.returncode != 0:
        raise LoiBuoc(f"lệnh trả về mã lỗi {kq.returncode}")


def buoc_han(args):
    if args.bo_thu_thap:
        print("  Bỏ qua crawl (--bo-thu-thap), dùng dữ liệu đang có trong Han/PTDL_3/data/output/.")
        return
    lenh = [sys.executable, "run_pipeline.py", "--xlsx"]
    if args.refresh:
        lenh.append("--refresh")
    if args.offline:
        lenh.append("--offline")
    chay(lenh, HAN)


def buoc_chep_du_lieu(args):
    nguon = HAN / "data" / "output"
    thieu = [f for f in FILE_DU_LIEU if not (nguon / f).exists()]
    if thieu:
        raise LoiBuoc(f"Han/PTDL_3/data/output/ thiếu: {', '.join(thieu)}")
    for dich in (NGHI / "data", QUAN):
        dich.mkdir(parents=True, exist_ok=True)
        for f in FILE_DU_LIEU:
            shutil.copy2(nguon / f, dich / f)
        print(f"  {len(FILE_DU_LIEU)} file -> {dich.relative_to(GOC)}")


def buoc_nghi(args):
    bat_dau = time.time()
    for ten in NOTEBOOK_NGHI:
        f = NGHI / "notebooks" / f"{ten}.ipynb"
        print(f"  ▸ {f.name}", flush=True)
        kq = subprocess.run([sys.executable, __file__, "--chay-notebook", str(f)],
                            cwd=f.parent, env=MOI_TRUONG)
        if kq.returncode != 0:
            if ten in NOTEBOOK_CHI_VE_HINH:
                print(f"    ! {f.name} lỗi nhưng chỉ dùng để vẽ hình, bỏ qua.")
                continue
            raise LoiBuoc(f"notebook {f.name} lỗi")
    cu = [f for f in KET_QUA_NGHI
          if not (NGHI / "outputs" / f).exists() or (NGHI / "outputs" / f).stat().st_mtime < bat_dau]
    if cu:
        raise LoiBuoc(f"notebook chạy xong nhưng không ghi mới: {', '.join(cu)}")


def buoc_quan(args):
    chay([sys.executable, "src/run_pipeline.py"], QUAN)
    bao_cao = QUAN / "outputs" / "reports" / "ml_results.md"
    if "NOT READY" in bao_cao.read_text(encoding="utf-8"):
        raise LoiBuoc("dữ liệu không qua kiểm tra của Quân (NOT READY FOR ML) – xem "
                      "Quan/dataset_nhom5/outputs/reports/data_readiness_report.md")


def buoc_web(args):
    chay([sys.executable, "dong_bo_du_lieu.py"], WEB)


CAC_BUOC = [
    ("Thu thập + làm sạch dữ liệu (Hân)", buoc_han),
    ("Chép dữ liệu mới cho Nghi và Quân", buoc_chep_du_lieu),
    ("Thống kê + trực quan (Nghi)", buoc_nghi),
    ("Machine Learning (Quân)", buoc_quan),
    ("Đồng bộ dữ liệu, kết quả, mô hình lên web", buoc_web),
]


def chay_notebook(duong_dan):
    """Chạy các ô code của một notebook trong tiến trình hiện tại (cwd = thư mục notebook)."""
    import plotly.basedatatypes
    plotly.basedatatypes.BaseFigure.show = lambda *a, **k: None

    nb = json.loads(Path(duong_dan).read_text(encoding="utf-8"))
    ns = {"__name__": "__main__", "display": lambda *a, **k: None}
    o_code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    for i, o in enumerate(o_code, 1):
        ma = "".join(o["source"])
        if not ma.strip() or any(d in ma for d in DAU_HIEU_O_BO):
            continue
        try:
            exec(compile(ma, f"{Path(duong_dan).name}[ô {i}]", "exec"), ns)
        except Exception as e:
            if any(d in ma for d in DAU_HIEU_O_PHU):
                print(f"    ! ô {i} (vẽ/lưu hình) lỗi, bỏ qua: {type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}")
                continue
            import traceback
            traceback.print_exc()
            print(f"    ✗ ô {i}/{len(o_code)} lỗi", flush=True)
            return 1
    print(f"    ✓ {len(o_code)} ô code", flush=True)
    return 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="bỏ cache, tải lại toàn bộ dữ liệu từ nguồn")
    ap.add_argument("--offline", action="store_true", help="chỉ dùng cache đã tải, không gửi request")
    ap.add_argument("--bo-thu-thap", action="store_true", help="không chạy crawl, dùng data/output hiện có của Hân")
    ap.add_argument("--den-quy", help="chốt quý cuối, vd 2025Q4 (mặc định: quý mới nhất đã qua hạn công bố BCTC)")
    ap.add_argument("--gia-den", help="chốt ngày cuối của giá, vd 2026-10-28 (mặc định: mốc dự báo của quý sau "
                                      "kỳ cuối, hoặc hôm nay nếu chưa tới) – cần khi tái lập bằng --offline")
    ap.add_argument("--mo-web", action="store_true", help="chạy xong thì mở web (streamlit run)")
    ap.add_argument("--chay-notebook", help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.chay_notebook:
        return chay_notebook(args.chay_notebook)
    if args.refresh and args.offline:
        ap.error("--refresh và --offline không dùng cùng nhau")

    if args.den_quy:
        MOI_TRUONG["PTDL_DEN_QUY"] = args.den_quy
    if args.gia_den:
        MOI_TRUONG["PTDL_GIA_DEN"] = args.gia_den
    bat_dau = time.time()
    for so, (ten, ham) in enumerate(CAC_BUOC, 1):
        print(f"\n[{so}/{len(CAC_BUOC)}] {ten}", flush=True)
        t = time.time()
        try:
            ham(args)
        except LoiBuoc as e:
            print(f"\n✗ Dừng ở bước {so} ({ten}): {e}")
            print("  Web chưa được cập nhật ở lần chạy này.")
            return 1
        print(f"  ✓ xong sau {time.time() - t:.0f} giây", flush=True)
    print(f"\n✓ Hoàn tất toàn bộ sau {time.time() - bat_dau:.0f} giây. Web đã có dữ liệu và kết quả mới.")

    if args.mo_web:
        print("\nMở web tại http://localhost:8501 (Ctrl+C để tắt)…", flush=True)
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], cwd=WEB, env=MOI_TRUONG)
    else:
        print("Mở web:  cd dashboard; streamlit run app.py   (hoặc chạy lại với --mo-web)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
