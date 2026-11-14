"""
ve_so_do.py – Vẽ sơ đồ kiến trúc theo nhận diện của bản tin (giấy + mực, tiêu đề Fraunces, nhấn đỏ gạch).
Chỉ thể hiện ba thứ: giai đoạn, công cụ của từng giai đoạn, và luồng dữ liệu giữa chúng.

    py ve_so_do.py

Xuất (bản PNG cần Chrome hoặc Edge để chụp):
  assets/so_do_kien_truc.png      bản 16:9 có tiêu đề, 3200×1800 – để chèn PowerPoint
  assets/so_do_kien_truc_web.png  chỉ phần thân sơ đồ – trang Phương pháp (đã có tiêu đề mục riêng)
  assets/so_do_kien_truc.svg      phần thân dạng vector – để sửa/in; web không nhúng được vì st.html lọc bỏ <svg>

Sửa tên bước / công cụ: sửa KHOI bên dưới rồi chạy lại.
"""
from pathlib import Path
import html
import shutil
import subprocess
import tempfile

from web.giao_dien import MAU

GOC = Path(__file__).resolve().parent
RONG, CAO_THAN = 1600, 480
SANS = "'Be Vietnam Pro', 'Segoe UI', sans-serif"
SERIF = "'Fraunces', Georgia, serif"
MONO = "Consolas, 'Cascadia Mono', ui-monospace, monospace"
CHU_SANG = {"so": "#E9A08A", "cong_cu": "#CFC8BA"}   # chữ trên khối nền mực (Bản tin)

# Khối giai đoạn: khóa -> (x, y, rộng, cao, số, tên, công cụ)
KHOI = {
    "thu_thap": (330, 205, 230, 110, "02", "Thu thập", "requests · bs4 · PyMuPDF"),
    "lam_sach": (640, 205, 230, 110, "03", "Làm sạch", "pandas · NumPy"),
    "thong_ke": (960, 150, 240, 95, "04a", "Thống kê", "SciPy · statsmodels"),
    "hoc_may": (960, 275, 240, 95, "04b", "Học máy", "scikit-learn"),
    "ban_tin": (1290, 205, 180, 110, "05", "Bản tin", "Streamlit · Plotly"),
}
NGUON = [("VNDirect API", "JSON", 150), ("CafeF", "HTML", 230),
         ("Vietstock", "PDF báo cáo CAR", 310)]   # (tên, định dạng, y)
X_NGUON, RONG_NGUON, CAO_NGUON = 60, 180, 60


def _t(x, y, chu, co=15, mau=MAU["muc"], font=SANS, dam=400, neo="start", gian=0):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{co}" font-weight="{dam}" fill="{mau}" '
            f'text-anchor="{neo}" letter-spacing="{gian}">{html.escape(chu)}</text>')


def _duong(diem, mau=MAU["muc"], hai_dau=False):
    """Đường gấp khúc có mũi tên ở cuối (và đầu nếu hai_dau)."""
    p = " ".join(f"{x},{y}" for x, y in diem)
    muoi = "sd-muoi-nhan" if mau == MAU["nhan"] else "sd-muoi"
    dau = f' marker-start="url(#{muoi})"' if hai_dau else ""
    return f'<polyline points="{p}" fill="none" stroke="{mau}" stroke-width="1.6"{dau} marker-end="url(#{muoi})"/>'


def _nguoi(cx, cy, r, mau):
    return (f'<circle cx="{cx}" cy="{cy - r * 0.9}" r="{r * 0.55}" fill="none" stroke="{mau}" stroke-width="1.6"/>'
            f'<path d="M{cx - r},{cy + r * 0.95} a{r},{r * 0.85} 0 0 1 {2 * r},0" fill="none" stroke="{mau}" stroke-width="1.6"/>')


def _khoi(x, y, w, h, so, ten, cong_cu, dam_nen=False):
    nen, vien = (MAU["muc"], MAU["muc"]) if dam_nen else (MAU["mat"], MAU["muc"])
    mau_so = CHU_SANG["so"] if dam_nen else MAU["nhan"]
    mau_ten = MAU["giay"] if dam_nen else MAU["muc"]
    mau_cc = CHU_SANG["cong_cu"] if dam_nen else MAU["muc2"]
    thap = h < 100
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{nen}" stroke="{vien}" stroke-width="1.5"/>'
            + _t(x + 18, y + (26 if thap else 30), so, 12, mau_so, dam=600, gian=1.5)
            + _t(x + 18, y + (56 if thap else 64), ten, 24, mau_ten, SERIF, 600)
            + _t(x + 18, y + (80 if thap else 92), cong_cu, 13.5, mau_cc))


def than():
    """Phần thân sơ đồ (không tiêu đề), toạ độ 0..RONG × 0..CAO_THAN."""
    s = ['<defs>' + "".join(
        f'<marker id="{i}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{m}"/></marker>'
        for i, m in [("sd-muoi", MAU["muc"]), ("sd-muoi-nhan", MAU["nhan"])]) + '</defs>']

    # Khung pipeline: mọi bước một lệnh chạy lại
    s += [f'<rect x="300" y="122" width="930" height="278" rx="6" fill="none" stroke="{MAU["nhat"]}" '
          f'stroke-width="1.2" stroke-dasharray="6 5"/>',
          f'<text x="300" y="110" font-size="13" fill="{MAU["muc2"]}">'
          f'<tspan font-family="{SANS}" font-weight="600" letter-spacing="1.5" fill="{MAU["nhan"]}">PIPELINE</tspan>'
          f'<tspan font-family="{SANS}">  ·  chạy lại cả chuỗi bằng </tspan>'
          f'<tspan font-family="{MONO}" font-weight="600" fill="{MAU["muc"]}">py chay_tat_ca.py</tspan></text>']

    # 01 Nguồn
    s.append(_t(X_NGUON, 136, "01 · NGUỒN", 12, MAU["nhan"], dam=600, gian=1.5))
    for ten, dinh_dang, y in NGUON:
        s += [f'<rect x="{X_NGUON}" y="{y}" width="{RONG_NGUON}" height="{CAO_NGUON}" rx="3" fill="none" '
              f'stroke="{MAU["nhat"]}" stroke-width="1.3"/>',
              _t(X_NGUON + 16, y + 27, ten, 16, dam=600), _t(X_NGUON + 16, y + 47, dinh_dang, 12.5, MAU["nhat"])]
    x_tt, y_tt = KHOI["thu_thap"][0], KHOI["thu_thap"][1]
    xr = X_NGUON + RONG_NGUON
    for (_, _, y), dy in zip(NGUON, (30, 55, 80)):
        ym = y + CAO_NGUON / 2
        s.append(_duong([(xr, ym), (285, ym), (285, y_tt + dy), (x_tt - 8, y_tt + dy)]))

    # 02–05
    for k, (x, y, w, h, so, ten, cc) in KHOI.items():
        s.append(_khoi(x, y, w, h, so, ten, cc, dam_nen=(k == "ban_tin")))

    tt, ls, tk, hm, bt = (KHOI[k] for k in ["thu_thap", "lam_sach", "thong_ke", "hoc_may", "ban_tin"])
    y_giua = ls[1] + ls[3] / 2
    # Thu thập -> Làm sạch
    s += [_duong([(tt[0] + tt[2], y_giua), (ls[0] - 8, y_giua)]),
          _t((tt[0] + tt[2] + ls[0]) / 2, y_giua - 10, "dữ liệu gốc", 12, MAU["nhat"], neo="middle")]
    # Làm sạch -> rẽ nhánh Thống kê / Học máy
    xn = (ls[0] + ls[2] + tk[0]) / 2
    ytk, yhm = tk[1] + tk[3] / 2, hm[1] + hm[3] / 2
    s += [f'<polyline points="{ls[0] + ls[2]},{y_giua} {xn},{y_giua}" fill="none" stroke="{MAU["muc"]}" stroke-width="1.6"/>',
          _duong([(xn, y_giua), (xn, ytk), (tk[0] - 8, ytk)]), _duong([(xn, y_giua), (xn, yhm), (hm[0] - 8, yhm)]),
          _t(xn + 8, y_giua + 4, "6 bảng CSV", 12, MAU["nhat"])]
    # Thống kê / Học máy -> Bản tin
    xg = (tk[0] + tk[2] + bt[0]) / 2
    s += [f'<polyline points="{tk[0] + tk[2]},{ytk} {xg},{ytk} {xg},{yhm} {hm[0] + hm[2]},{yhm}" fill="none" '
          f'stroke="{MAU["muc"]}" stroke-width="1.6"/>',
          _duong([(xg, y_giua), (bt[0] - 8, y_giua)])]
    # Dữ liệu sạch đi thẳng tới Bản tin (tra cứu, so sánh)
    y_vong, xls, xbt = 452, ls[0] + ls[2] / 2, bt[0] + bt[2] / 2
    s += [_duong([(xls, ls[1] + ls[3]), (xls, y_vong), (xbt, y_vong), (xbt, bt[1] + bt[3] + 8)]),
          _t((xls + xbt) / 2, y_vong - 9, "dữ liệu sạch cho tra cứu, so sánh", 12, MAU["nhat"], neo="middle")]
    # Rà soát thủ công -> Làm sạch
    xm, ym = ls[0] + 10, 22
    s += [f'<rect x="{xm}" y="{ym}" width="{ls[2] - 20}" height="58" rx="3" fill="none" stroke="{MAU["nhan"]}" '
          f'stroke-width="1.3" stroke-dasharray="5 4"/>',
          _t(xm + 16, ym + 25, "Rà soát thủ công", 15, MAU["nhan"], dam=600),
          _t(xm + 16, ym + 44, "sự kiện; CAR bản scan", 12.5, MAU["muc2"]),
          _duong([(xls, ym + 58), (xls, ls[1] - 8)], MAU["nhan"])]
    # Bản tin <-> Người dùng
    xu = bt[0] + bt[2] + 76
    s += [_duong([(bt[0] + bt[2] + 8, y_giua), (xu - 32, y_giua)], hai_dau=True),
          _nguoi(xu, y_giua - 10, 20, MAU["muc"]),
          _t(xu, y_giua + 50, "Người dùng", 14.5, dam=600, neo="middle")]
    return "\n".join(s)


def svg_than():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {RONG} {CAO_THAN}" width="100%" '
            f'role="img" aria-label="Sơ đồ kiến trúc hệ thống">\n{than()}\n</svg>')


def html_png(co_tieu_de=True):
    """Trang để chụp PNG: 1600×900 có tiêu đề (PowerPoint), hoặc chỉ phần thân 1600×CAO_THAN (web)."""
    tieu_de = (f'<line x1="60" y1="52" x2="{RONG - 60}" y2="52" stroke="{MAU["muc"]}" stroke-width="2"/>'
               + _t(60, 86, "NHÓM 5 · PHÂN TÍCH TÀI CHÍNH NGÂN HÀNG NIÊM YẾT", 14, MAU["nhan"], dam=600, gian=2)
               + _t(60, 140, "Kiến trúc hệ thống", 44, font=SERIF, dam=600)
               + _t(60, 178, "8 ngân hàng (VCB, BID, CTG, TCB, MBB, ACB, STB, VPB) · dữ liệu từ Q1/2021 đến quý mới nhất",
                    17, MAU["muc2"]))
    cao, dich = (900, 300) if co_tieu_de else (CAO_THAN + 20, 4)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {RONG} {cao}" width="{RONG}" height="{cao}">'
           f'<rect width="100%" height="100%" fill="{MAU["giay"]}"/>{tieu_de if co_tieu_de else ""}'
           f'<g transform="translate(0 {dich})">{than()}</g></svg>')
    return ('<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
            'family=Be+Vietnam+Pro:wght@400;600&family=Fraunces:opsz,wght@9..144,600&display=block">'
            f'<style>html,body{{margin:0;background:{MAU["giay"]}}}</style>{svg}')


def _trinh_duyet():
    for p in [shutil.which("chrome"), shutil.which("msedge"),
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]:
        if p and Path(p).exists():
            return p
    return None


def main():
    (GOC / "assets" / "so_do_kien_truc.svg").write_text(svg_than(), encoding="utf-8")
    print("Đã ghi assets/so_do_kien_truc.svg")
    tr = _trinh_duyet()
    if not tr:
        print("Không thấy Chrome/Edge – bỏ qua bản PNG.")
        return
    for ten, co_tieu_de, cao in [("so_do_kien_truc", True, 900), ("so_do_kien_truc_web", False, CAO_THAN + 20)]:
        with tempfile.TemporaryDirectory() as tmp:
            trang = Path(tmp) / "so_do.html"
            trang.write_text(html_png(co_tieu_de), encoding="utf-8")
            png = GOC / "assets" / f"{ten}.png"
            subprocess.run([tr, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                            f"--user-data-dir={Path(tmp) / 'hs'}", "--virtual-time-budget=8000",
                            f"--window-size={RONG},{cao}", f"--screenshot={png}", trang.as_uri()],
                           check=True, capture_output=True, timeout=120)
        print(f"Đã ghi assets/{ten}.png ({RONG * 2}×{cao * 2})")


if __name__ == "__main__":
    main()
