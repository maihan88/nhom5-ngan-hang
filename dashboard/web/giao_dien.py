"""
giao_dien.py – Nhận diện "bản tin dữ liệu" của dashboard: CSS, định dạng số kiểu Việt và các
thành phần HTML (tiêu đề mục, dải số liệu, huy hiệu mã, sparkline, bảng).

Nguyên tắc: giao diện đơn sắc (giấy + mực), màu chỉ dành cho dữ liệu – mỗi ngân hàng giữ màu
quy ước của Nghi (src/config.py). Đổi tên sản phẩm, màu nền, màu nhấn: sửa hằng số dưới đây
và .streamlit/config.toml.
"""
import base64
import html as _html

import numpy as np
import streamlit as st

from src import config as cf

TEN = "Nhịp Ngân Hàng"
KHAU_HIEU = "Bản tin dữ liệu 8 ngân hàng niêm yết"

MAU = {
    "giay": "#F4F1EA", "mat": "#FBFAF6", "muc": "#1A1A1A", "muc2": "#4A463F", "nhat": "#8A8478",
    "ke": "#D9D2C4", "luoi": "#E6E0D4", "nen_xam": "#C9C2B4", "nhan": "#A8381C",
    "tang": "#2E7D4F", "giam": "#B3261E",
}
SERIF = "'Fraunces', Georgia, 'Times New Roman', serif"
SANS = "'Be Vietnam Pro', 'Segoe UI', system-ui, sans-serif"

_CSS = f"""
<style>
:root {{ --giay:{MAU['giay']}; --mat:{MAU['mat']}; --muc:{MAU['muc']}; --muc2:{MAU['muc2']};
  --nhat:{MAU['nhat']}; --ke:{MAU['ke']}; --nhan:{MAU['nhan']}; --tang:{MAU['tang']}; --giam:{MAU['giam']}; }}
[data-testid="stMainBlockContainer"], .block-container {{ max-width: 1180px; padding-top: 4.2rem; padding-bottom: 4rem; }}
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"], [data-testid="stDecoration"], footer,
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebar"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: var(--giay); border-bottom: 1px solid var(--ke); }}
h1, h2, h3 {{ letter-spacing: -0.015em; }}
a {{ color: var(--muc); }}

/* ---------- Tiêu đề mục ---------- */
.muc {{ border-top: 2px solid var(--muc); padding-top: 14px; margin: 34px 0 6px 0; }}
.muc.dau {{ margin-top: 6px; }}
.muc .kicker {{ font: 600 .74rem/1 {SANS}; letter-spacing: .12em; text-transform: uppercase; color: var(--nhan); }}
.muc h2 {{ font-family: {SERIF}; font-weight: 600; font-size: 1.75rem; line-height: 1.22; margin: 10px 0 6px 0;
  padding: 0; color: var(--muc); max-width: 900px; }}
.muc .dek {{ font-size: 1rem; color: var(--muc2); line-height: 1.55; max-width: 780px; margin: 0; }}
.nguon {{ font-size: .76rem; color: var(--nhat); margin-top: 2px; line-height: 1.5; }}

/* ---------- Đầu báo ---------- */
.dau-bao {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px;
  border-bottom: 1px solid var(--muc); padding-bottom: 8px; margin-bottom: 22px; }}
.dau-bao .ten {{ font: 600 .8rem/1 {SANS}; letter-spacing: .14em; text-transform: uppercase; }}
.dau-bao .ngay {{ font-size: .8rem; color: var(--muc2); }}
.tit {{ font-family: {SERIF}; font-weight: 600; font-size: 2.65rem; line-height: 1.12; letter-spacing: -0.02em;
  margin: 0 0 12px 0; max-width: 980px; color: var(--muc); }}
.sapo {{ font-size: 1.12rem; line-height: 1.6; color: var(--muc2); max-width: 800px; margin: 0 0 8px 0; }}

/* ---------- Dải số liệu ---------- */
.day-so {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); border-top: 1px solid var(--ke);
  border-bottom: 1px solid var(--ke); margin: 18px 0 6px 0; }}
.day-so.hep {{ grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }}
.day-so.hep .hang {{ flex-direction: column; align-items: flex-start; gap: 4px; }}
.day-so.hep .so {{ font-size: 1.65rem; }}
.day-so .o {{ padding: 16px 18px 14px 0; }}
.day-so .o + .o {{ border-left: 1px solid var(--ke); padding-left: 18px; }}
.day-so .nhan {{ font-size: .78rem; color: var(--muc2); font-weight: 500; }}
.day-so .hang {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: 4px 0 2px 0; }}
.day-so .so {{ font-size: 2rem; font-weight: 650; letter-spacing: -0.02em; color: var(--muc); }}
.day-so .phu {{ font-size: .8rem; color: var(--nhat); line-height: 1.45; }}

/* ---------- Huy hiệu, nhãn ---------- */
.chip {{ display: inline-flex; align-items: center; gap: 7px; font-weight: 650; white-space: nowrap; }}
.chip i {{ width: 10px; height: 10px; border-radius: 2px; display: inline-block; }}
.chip span {{ font-weight: 400; color: var(--muc2); }}
.len {{ color: var(--tang); font-weight: 600; }}  .xuong {{ color: var(--giam); font-weight: 600; }}
.trung {{ color: var(--muc2); font-weight: 600; }}
.the {{ display: inline-block; font-size: .72rem; font-weight: 600; letter-spacing: .04em; padding: 2px 8px;
  border: 1px solid var(--ke); border-radius: 3px; color: var(--muc2); background: var(--mat); }}

/* ---------- Bảng ---------- */
table.bang {{ width: 100%; border-collapse: collapse; font-size: .9rem; font-variant-numeric: tabular-nums; }}
table.bang th {{ font-size: .72rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--muc2);
  text-align: right; padding: 8px 10px; border-bottom: 1px solid var(--muc); white-space: nowrap; }}
table.bang td {{ padding: 11px 10px; border-bottom: 1px solid var(--ke); text-align: right; vertical-align: middle; }}
table.bang th:first-child, table.bang td:first-child, table.bang .trai {{ text-align: left; }}
table.bang tr.link {{ cursor: pointer; }}
table.bang tr:hover td {{ background: var(--mat); }}
table.bang a {{ text-decoration: none; color: inherit; }}
.cuon {{ overflow-x: auto; }}

/* ---------- Danh sách tin ---------- */
.tin {{ display: grid; grid-template-columns: 92px 1fr; gap: 4px 16px; padding: 12px 0; border-bottom: 1px solid var(--ke); }}
.tin .ngay {{ font-size: .8rem; color: var(--nhat); padding-top: 2px; }}
.tin .tieu {{ font-size: .95rem; line-height: 1.45; }}
.tin .tieu a {{ text-decoration: none; }} .tin .tieu a:hover {{ text-decoration: underline; }}
.tin .meta {{ font-size: .78rem; color: var(--muc2); margin-bottom: 3px; }}

/* ---------- Hộp nhận định ---------- */
.ghi-chu {{ border-left: 3px solid var(--nhan); padding: 4px 0 4px 14px; color: var(--muc2); font-size: .92rem;
  line-height: 1.55; margin: 8px 0; }}
.ket-luan {{ font-family: {SERIF}; font-size: 1.25rem; line-height: 1.45; color: var(--muc); }}

/* ---------- Widget ---------- */
[data-testid="stExpander"] details {{ border: none; border-top: 1px solid var(--ke); border-radius: 0; background: transparent; }}
[data-testid="stExpander"] summary {{ padding-left: 0; font-weight: 600; }}
[data-testid="stTabs"] [data-baseweb="tab-list"] {{ gap: 18px; border-bottom: 1px solid var(--ke); }}
[data-testid="stTabs"] [data-baseweb="tab"] {{ padding-left: 0; padding-right: 0; font-weight: 600; }}
</style>
"""


def nap_css():
    st.html(_CSS)


# ----------------------------------------------------------------------------
# Định dạng
# ----------------------------------------------------------------------------
def so(x, le=2, dv="%", dau=False):
    """Số kiểu Việt: 1.234,56 – dấu chấm ngăn nghìn, dấu phẩy thập phân."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    s = f"{x:{'+' if dau else ''},.{le}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".") + dv


def bien_dong(x, chieu=1, le=2, dv=" điểm"):
    """Mũi tên + số, xanh khi tốt / đỏ khi xấu theo chiều (1: tăng là tốt, -1: giảm là tốt, 0: trung tính)."""
    if x is None or np.isnan(x) or abs(x) < 10 ** -(le + 1):
        return "<span class='trung'>không đổi</span>"
    lop = "trung" if chieu == 0 else ("len" if x * chieu > 0 else "xuong")
    return f"<span class='{lop}'>{'▲' if x > 0 else '▼'} {so(abs(x), le, dv)}</span>"


def hoa_dau(s):
    return s[:1].upper() + s[1:]


def e(s):
    return _html.escape("" if s is None else str(s))


# ----------------------------------------------------------------------------
# Thành phần
# ----------------------------------------------------------------------------
def muc(kicker, tieu_de, dek=None, dau=False):
    """Mở một mục: dòng kẻ đậm, nhãn nhỏ, tiêu đề là một câu kết luận, một dòng giải thích."""
    st.html(f"<div class='muc{' dau' if dau else ''}'><div class='kicker'>{e(kicker)}</div>"
            f"<h2>{tieu_de}</h2>{f'<p class=dek>{dek}</p>' if dek else ''}</div>")


def nguon(chu):
    st.html(f"<div class='nguon'>{chu}</div>")


def chip(ma, ten=False):
    phu = f"<span>{e(cf.TEN_DAY_DU[ma])}</span>" if ten else ""
    return f"<span class='chip'><i style='background:{cf.MAU_NGAN_HANG[ma]}'></i>{ma}{phu}</span>"


def sparkline(gia_tri, mau=None, rong=96, cao=26):
    v = np.asarray([x for x in gia_tri if x == x], dtype=float)
    if len(v) < 2:
        return ""
    lo, hi = v.min(), v.max()
    y = cao - 3 - (v - lo) / ((hi - lo) or 1) * (cao - 6)
    x = np.linspace(2, rong - 4, len(v))
    diem = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(x, y))
    mau = mau or MAU["muc"]
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{rong}' height='{cao}' viewBox='0 0 {rong} {cao}'>"
           f"<polyline points='{diem}' fill='none' stroke='{mau}' stroke-width='1.6' stroke-linejoin='round'/>"
           f"<circle cx='{x[-1]:.1f}' cy='{y[-1]:.1f}' r='2.4' fill='{mau}'/></svg>")
    # st.html lọc thẻ <svg>, nên nhúng dưới dạng ảnh data URI
    return (f"<img src='data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}' width='{rong}' "
            f"height='{cao}' style='vertical-align:middle' alt=''>")


def day_so(o, hep=False):
    """Dải số liệu: o = list dict(nhan, so, phu, spark). hep=True: ô hẹp hơn để vừa 6 ô một hàng."""
    st.html(f"<div class='day-so{' hep' if hep else ''}'>" + "".join(
        f"<div class='o'><div class='nhan'>{x['nhan']}</div><div class='hang'><div class='so'>{x['so']}</div>"
        f"{x.get('spark', '')}</div><div class='phu'>{x.get('phu', '')}</div></div>" for x in o) + "</div>")


def dumbbell(dong, mau_qd, mau_tn):
    """Mỗi dòng một chỉ số: chấm quốc doanh và tư nhân trên thang riêng, nối bằng vạch (đậm = khác biệt rõ).
    dong = list dict(ten, qd, tn, y_nghia)."""
    html = []
    for r in dong:
        lo, hi = min(r["qd"], r["tn"]), max(r["qd"], r["tn"])
        dem = (hi - lo) * 0.45 + 0.3
        a, b = lo - dem, hi + dem

        def vt(v):
            return (v - a) / (b - a) * 100

        vach = "var(--muc)" if r["y_nghia"] else "var(--ke)"
        nhan = ("<span class='the' style='border-color:var(--muc);color:var(--muc)'>Khác biệt rõ</span>"
                if r["y_nghia"] else "<span class='the'>Chưa rõ khác biệt</span>")
        cham = "".join(
            f"<div style='position:absolute;left:{vt(v):.1f}%;top:30px;transform:translate(-50%,-50%);width:14px;"
            f"height:14px;border-radius:50%;background:{m};border:2px solid var(--giay)'></div>"
            f"<div style='position:absolute;left:{vt(v):.1f}%;top:0;transform:translateX(-50%);font-size:.8rem;"
            f"white-space:nowrap;color:var(--muc2)'>{t} <b style='color:var(--muc)'>{so(v)}</b></div>"
            for v, m, t in [(r["qd"], mau_qd, "Quốc doanh"), (r["tn"], mau_tn, "Tư nhân")])
        html.append(
            "<div style='display:grid;grid-template-columns:170px 1fr 130px;align-items:center;gap:16px;"
            "padding:14px 0;border-bottom:1px solid var(--ke)'>"
            f"<div style='font-weight:600'>{r['ten']}</div>"
            f"<div style='position:relative;height:44px'><div style='position:absolute;left:{vt(lo):.1f}%;"
            f"width:{vt(hi) - vt(lo):.1f}%;top:29px;height:3px;background:{vach}'></div>{cham}</div>"
            f"<div style='text-align:right'>{nhan}</div></div>")
    st.html("".join(html))


def ghi_chu(chu):
    st.html(f"<div class='ghi-chu'>{chu}</div>")


def chan_trang():
    st.html(
        f"<div class='nguon' style='margin-top:48px;border-top:1px solid var(--muc);padding-top:12px'>"
        f"<b style='color:var(--muc)'>{TEN}</b> · {KHAU_HIEU}. Sản phẩm của Nhóm 5 – Phân tích dữ liệu cho môi trường "
        "doanh nghiệp: Nguyễn Ngọc Mai Hân (dữ liệu, web), Hoàng Ngọc Gia Nghi (thống kê), Hoàng Mạnh Quân (mô hình).<br>"
        "Nguồn: VNDirect (báo cáo tài chính, NPL, CAR, giá cổ phiếu), CafeF (tin doanh nghiệp). "
        "Thông tin chỉ để tham khảo, không phải khuyến nghị đầu tư.</div>")
