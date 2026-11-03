"""
giao_dien.py – Nhận diện của dashboard: bảng màu sáng/tối, CSS, định dạng số kiểu Việt và các
thành phần HTML (đầu trang, nhận định, thẻ số liệu, thẻ nội dung, huy hiệu mã, sparkline, bảng, tin).

Nguyên tắc: nền sáng navy + trắng (mặc định) hoặc tối kiểu terminal; nội dung nằm trên thẻ; mỗi trang
một câu nhận định. Màu ngân hàng theo quy ước của Nghi (src/config.py), có bản sáng hơn cho nền tối.
Đổi màu: sửa BANG_MAU dưới đây và .streamlit/config.toml (màu nền, sidebar, widget của Streamlit).
"""
import base64
import html as _html

import numpy as np
import streamlit as st

from src import config as cf

TEN = "UpBank!"
KHAU_HIEU = "Dữ liệu 8 ngân hàng niêm yết"

# Chữ và biểu đồ: Inter · con số trong bảng, thẻ số, ngày: JetBrains Mono (độ rộng đều, cột số thẳng hàng)
# · câu nhận định: Merriweather (giọng bài phân tích)
CHU = "'Inter', 'Segoe UI', system-ui, sans-serif"
SO = "'JetBrains Mono', ui-monospace, Consolas, monospace"

# giay: nền trang · mat: nền thẻ · muc: chữ chính · muc2: chữ phụ · nhat: chú thích · ke: viền
# nen_xam: đường/cột làm nền so sánh · vung: dải tô mờ trên biểu đồ · nhan: màu nhấn
BANG_MAU = {
    "light": {
        "giay": "#F3F5F9", "mat": "#FFFFFF", "mat2": "#EEF2F7", "muc": "#0E1A2B", "muc2": "#3F4D61", "nhat": "#5F6E83",
        "ke": "#E1E6EE", "ke2": "#C9D2DE", "luoi": "#E9EDF3", "nen_xam": "#C3CCD8", "vung": "rgba(95,110,131,0.13)",
        "nhan": "#1C5BD6", "nhan_nhat": "#E7EEFC", "nhan_chu": "#174CB3", "nhan_dinh": "#174CB3",
        "tang": "#0A7A4A", "tang_nhat": "#E2F3EA", "giam": "#BF3328", "giam_nhat": "#FBE7E4",
        "canh_bao": "#985A00", "canh_bao_nhat": "#FBF0DC", "bong": "0 1px 2px rgba(14,26,43,.06)", "bo": "12px",
        "so": SO,
    },
    "dark": {
        "giay": "#0A0D12", "mat": "#10151C", "mat2": "#161D27", "muc": "#E2E8F0", "muc2": "#B4C0D0", "nhat": "#8E9BAE",
        "ke": "#1F2834", "ke2": "#2C3846", "luoi": "#1A222D", "nen_xam": "#3A4656", "vung": "rgba(142,155,174,0.12)",
        "nhan": "#5B9DFF", "nhan_nhat": "#132338", "nhan_chu": "#7FB2FF", "nhan_dinh": "#F0B13E",
        "tang": "#34C47C", "tang_nhat": "#0F2A1D", "giam": "#FF6A5C", "giam_nhat": "#2E1513",
        "canh_bao": "#F0B13E", "canh_bao_nhat": "#2A2110", "bong": "none", "bo": "6px",
        "so": SO,
    },
}
MAU = BANG_MAU["light"]   # bản sáng cố định cho ve_so_do.py (sơ đồ kiến trúc, vẽ ngoài Streamlit)
# Trên nền tối, các màu đậm (navy VCB, nâu VPB…) chìm mất – dùng bản sáng hơn, giữ nguyên tông
MAU_NGAN_HANG_TOI = {"VCB": "#4E86D9", "BID": "#86B4EE", "CTG": "#BCD8F6", "TCB": "#FF6B72", "MBB": "#F2B544",
                     "ACB": "#2FC79A", "STB": "#B58BE3", "VPB": "#CDA75E"}
MAU_NHOM = {"light": {"A": "#2F6DB5", "B": "#E07B39", "C": "#4E9A5B", "D": "#8E6C9E"},
            "dark": {"A": "#5B9DFF", "B": "#FF9A57", "C": "#6CCB86", "D": "#C29BE0"}}


# ----------------------------------------------------------------------------
# Sáng / tối
# ----------------------------------------------------------------------------
# Streamlit không chạy lại script khi người xem đổi giao diện trong menu, nên biểu đồ Plotly (màu tính ở
# Python) sẽ lệch màu. Component nhỏ này đọc màu nền thật của trang, gắn data-nnh lên <html> để CSS đổi
# ngay, và báo về Python để chạy lại – biểu đồ vẽ lại đúng màu.
_JS_GIAO_DIEN = """
export default function(component) {
    const { setStateValue, data } = component;
    const app = document.querySelector('.stApp');
    if (!app) return;
    const doc = () => {
        const m = (getComputedStyle(app).backgroundColor.match(/\\d+/g) || [255, 255, 255]).map(Number);
        return 0.299 * m[0] + 0.587 * m[1] + 0.114 * m[2] < 128 ? 'dark' : 'light';
    };
    const ap = () => {
        const loai = doc();
        document.documentElement.dataset.nnh = loai;
        if (loai !== data) setStateValue('loai', loai);
    };
    ap();
    const quan_sat = new MutationObserver(ap);
    quan_sat.observe(app, { attributes: true, attributeFilter: ['class', 'style'] });
    return () => quan_sat.disconnect();
}
"""
_theo_doi = st.components.v2.component("nnh_giao_dien", js=_JS_GIAO_DIEN)


def theo_doi_giao_dien():
    """Gọi một lần mỗi lượt chạy (app.py), trước khi vẽ trang."""
    hien_tai = st.session_state.get("_nnh_loai") or st.context.theme.type or "light"
    with st.sidebar:
        kq = _theo_doi(key="nnh_giao_dien", data=hien_tai, on_loai_change=lambda: None)
    loai = getattr(kq, "loai", None) or st.context.theme.type or "light"
    st.session_state["_nnh_loai"] = "dark" if loai == "dark" else "light"


def loai_giao_dien():
    return st.session_state.get("_nnh_loai") or st.context.theme.type or "light"


def mau():
    """Bảng màu của giao diện hiện tại (dict)."""
    return BANG_MAU["dark" if loai_giao_dien() == "dark" else "light"]


def mau_nh(ma):
    return (MAU_NGAN_HANG_TOI if loai_giao_dien() == "dark" else cf.MAU_NGAN_HANG)[ma]


def mau_nhom(nhom):
    return MAU_NHOM["dark" if loai_giao_dien() == "dark" else "light"].get(nhom, "#888888")


def _bien(m):
    v = {k: m[k] for k in m if k not in ("so", "bong", "bo")}
    return ";".join(f"--{k.replace('_', '-')}:{x}" for k, x in v.items()) + f";--so:{m['so']};--bong:{m['bong']};--bo:{m['bo']}"


def _bien_nh(loai):
    bang = MAU_NGAN_HANG_TOI if loai == "dark" else cf.MAU_NGAN_HANG
    return ";".join(f"--nh-{ma.lower()}:{c}" for ma, c in bang.items())


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Merriweather:wght@700&display=swap');
/* ---------- Khung trang ---------- */
[data-testid="stMainBlockContainer"], .block-container { max-width: 1240px; padding-top: 2.4rem; padding-bottom: 3.5rem; }
[data-testid="stAppDeployButton"], [data-testid="stDecoration"], footer { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
.st-key-nnh_giao_dien { display: none !important; }
h1, h2, h3 { letter-spacing: -0.01em; }
.num, table.bang td { font-family: var(--so); font-variant-numeric: tabular-nums; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebarNavLink"] { min-height: 44px; border-radius: 8px; }
[data-testid="stSidebarNavLink"] span { font-weight: 500; }

/* ---------- Thẻ: st.container(border=True, key="the-…") ---------- */
div[class*="st-key-the-"] { background: var(--mat); border-color: var(--ke) !important; border-radius: var(--bo) !important;
  box-shadow: var(--bong); padding: 18px 20px 14px 20px; }

/* ---------- Đầu trang ---------- */
.dau-trang { display: flex; flex-direction: column; gap: 4px; margin: 0 0 4px 0; }
.dau-trang .nho { font-size: .75rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--nhat); }
.dau-trang h1 { font-size: 1.85rem; font-weight: 700; margin: 0; padding: 0; line-height: 1.2; color: var(--muc); }
.dau-trang .phu { color: var(--nhat); font-size: .92rem; }

/* ---------- Câu nhận định ---------- */
.nhan-dinh { background: var(--mat); border: 1px solid var(--ke); border-radius: var(--bo); box-shadow: var(--bong);
  padding: 20px 24px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px 32px; }
.nhan-dinh .nho { font-size: .75rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--nhan-dinh); }
.nhan-dinh .cau { font-family: 'Merriweather', Georgia, serif; font-size: 1.5rem; font-weight: 600; line-height: 1.28;
  color: var(--muc); margin: 4px 0 0 0; }
.nhan-dinh .phu { font-size: .9rem; color: var(--nhat); margin-top: 6px; }

/* ---------- Thẻ số liệu ---------- */
.the-so { display: grid; grid-template-columns: repeat(auto-fit, minmax(var(--rong, 220px), 1fr)); gap: 14px; }
.the-so .o { background: var(--mat); border: 1px solid var(--ke); border-radius: var(--bo); box-shadow: var(--bong);
  padding: 16px 18px; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.the-so .tren { display: flex; justify-content: space-between; gap: 8px; font-size: .84rem; color: var(--muc2); font-weight: 500; }
.the-so .tren span:last-child { color: var(--nhat); font-weight: 400; }
.the-so .giua { display: flex; align-items: flex-end; justify-content: space-between; gap: 8px; min-width: 0; }
.the-so .giua img { min-width: 0; max-width: 48%; height: auto; }
.the-so .so { font-family: var(--so); font-size: 1.7rem; font-weight: 600; letter-spacing: -0.01em; line-height: 1.05; color: var(--muc); }
.the-so.hep .so { font-size: 1.5rem; }
.the-so.hep .giua { flex-wrap: wrap; }
.the-so.hep .tren { font-size: .78rem; white-space: nowrap; }
.the-so .duoi { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: .76rem; color: var(--nhat); }

/* ---------- Tiêu đề trong thẻ ---------- */
.tieu-the { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 6px 16px; margin-bottom: 2px; }
.tieu-the h3 { font-size: 1.06rem; font-weight: 600; margin: 0; padding: 0; color: var(--muc); }
.tieu-the .phu { font-size: .84rem; color: var(--nhat); margin-top: 2px; }
.tieu-the .phai { font-size: .78rem; color: var(--nhat); }
.nguon { font-size: .76rem; color: var(--nhat); line-height: 1.5; }
code { overflow-wrap: anywhere; }
[data-testid="stButtonGroup"] > div { flex-wrap: wrap; row-gap: 6px; }

/* ---------- Huy hiệu, nhãn ---------- */
.chip { display: inline-flex; align-items: center; gap: 7px; font-weight: 650; white-space: nowrap; }
.chip i { width: 10px; height: 10px; border-radius: 3px; display: inline-block; flex: none; }
.chip span { font-weight: 400; color: var(--nhat); }
.vien { display: inline-flex; align-items: center; gap: 4px; font-size: .76rem; font-weight: 600; padding: 2px 9px;
  border-radius: 999px; background: var(--mat2); color: var(--muc2); white-space: nowrap; }
.vien.tot { background: var(--tang-nhat); color: var(--tang); }
.vien.xau { background: var(--giam-nhat); color: var(--giam); }
.the { display: inline-block; font-size: .74rem; font-weight: 500; padding: 2px 8px; border: 1px solid var(--ke);
  border-radius: 6px; color: var(--muc2); white-space: nowrap; }
.len { color: var(--tang); font-weight: 600; }  .xuong { color: var(--giam); font-weight: 600; }
.trung { color: var(--muc2); font-weight: 600; }
.canh-bao { display: flex; gap: 12px; align-items: flex-start; padding: 14px 18px; border-radius: var(--bo);
  background: var(--canh-bao-nhat); color: var(--muc); font-size: .92rem; line-height: 1.55; }
.i-tron { width: 18px; height: 18px; border-radius: 50%; border: 1.8px solid var(--canh-bao); color: var(--canh-bao);
  font-weight: 700; font-size: 11px; line-height: 1; display: inline-flex; align-items: center; justify-content: center;
  flex: none; margin-top: 2px; }

/* ---------- Bảng ---------- */
table.bang { width: 100%; border-collapse: collapse; font-size: .88rem; }
table.bang th { font-size: .74rem; font-weight: 600; color: var(--nhat); text-align: right; padding: 8px 10px;
  border-bottom: 1px solid var(--ke); white-space: nowrap; }
table.bang td { padding: 11px 10px; border-bottom: 1px solid var(--ke); text-align: right; vertical-align: middle; color: var(--muc); }
table.bang tr:last-child td { border-bottom: none; }
table.bang th:first-child, table.bang td:first-child, table.bang .trai { text-align: left; }
table.bang td.chu { font-family: inherit; }
table.bang tbody tr:hover td { background: var(--mat2); }
table.bang a { text-decoration: none; color: inherit; }
.cuon { overflow-x: auto; }

/* ---------- Danh sách tin ---------- */
.tin { display: grid; grid-template-columns: 96px 1fr; gap: 4px 16px; padding: 12px 0; border-top: 1px solid var(--ke); }
.tin .ngay { font-family: var(--so); font-size: .8rem; color: var(--nhat); padding-top: 2px; }
.tin .tieu { font-size: .93rem; line-height: 1.45; font-weight: 500; }
.tin .tieu a { text-decoration: none; } .tin .tieu a:hover { text-decoration: underline; }
.tin .meta { font-size: .76rem; color: var(--nhat); margin-bottom: 3px; }

/* ---------- Ô nhỏ trong thẻ ---------- */
.o-nho { border: 1px solid var(--ke); border-radius: 8px; padding: 8px 10px; display: flex; flex-direction: column; gap: 1px;
  font-size: .82rem; }
.o-nho.dung { background: var(--tang-nhat); border-color: transparent; }
.o-nho.sai { background: var(--giam-nhat); border-color: transparent; }

/* ---------- Widget ---------- */
[data-testid="stExpander"] details { border-radius: var(--bo); }
[data-testid="stExpander"] summary { font-weight: 600; }
</style>
"""


def nap_css():
    loai = loai_giao_dien()
    bien = (f"<style>:root{{{_bien(mau())};{_bien_nh(loai)}}}"
            f"html[data-nnh='light']{{{_bien(BANG_MAU['light'])};{_bien_nh('light')}}}"
            f"html[data-nnh='dark']{{{_bien(BANG_MAU['dark'])};{_bien_nh('dark')}}}</style>")
    st.html(bien + _CSS)


# ----------------------------------------------------------------------------
# Định dạng
# ----------------------------------------------------------------------------
def so(x, le=2, dv="%", dau=False):
    """Số kiểu Việt: 1.234,56 – dấu chấm ngăn nghìn, dấu phẩy thập phân."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    s = f"{x:{'+' if dau else ''},.{le}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".").replace("-", "−") + dv


def bien_dong(x, chieu=1, le=2, dv=" điểm"):
    """Mũi tên + số trong viên màu: xanh khi tốt / đỏ khi xấu theo chiều (1: tăng là tốt, -1: giảm là tốt, 0: trung tính)."""
    if x is None or np.isnan(x) or abs(x) < 10 ** -(le + 1):
        return "<span class='vien'>không đổi</span>"
    lop = "" if chieu == 0 else (" tot" if x * chieu > 0 else " xau")
    return f"<span class='vien{lop}'>{'▲' if x > 0 else '▼'} {so(x, le, dv, dau=True)}</span>"


def vien(chu, lop=""):
    return f"<span class='vien {lop}'>{chu}</span>"


def hoa_dau(s):
    return s[:1].upper() + s[1:]


def e(s):
    return _html.escape("" if s is None else str(s))


# ----------------------------------------------------------------------------
# Thành phần
# ----------------------------------------------------------------------------
def dau_trang(nho, tieu_de, phu=None):
    """Đầu trang: nhãn nhỏ, tiêu đề ngắn (tên trang, không phải câu kết luận), một dòng phụ."""
    st.html(f"<div class='dau-trang'><span class='nho'>{e(nho)}</span><h1>{e(tieu_de)}</h1>"
            f"{f'<span class=phu>{phu}</span>' if phu else ''}</div>")


def nhan_dinh(cau, nho="Nhận định", phu=None, ben_phai=""):
    """Câu nhận định duy nhất của trang."""
    st.html(f"<div class='nhan-dinh'><div style='flex:1 1 420px;min-width:0'><div class='nho'>{e(nho)}</div>"
            f"<p class='cau'>{cau}</p>{f'<div class=phu>{phu}</div>' if phu else ''}</div>"
            f"{f'<div style=display:flex;gap:8px;flex-wrap:wrap>{ben_phai}</div>' if ben_phai else ''}</div>")


def the_so(o, rong=220, hep=False):
    """Hàng thẻ số liệu. o = list dict(nhan, so, phu, ghi, spark, hang)."""
    st.html(f"<div class='the-so{' hep' if hep else ''}' style='--rong:{rong}px'>" + "".join(
        f"<div class='o'><div class='tren'><span>{x['nhan']}</span><span>{x.get('hang', '')}</span></div>"
        f"<div class='giua'><span class='so'>{x['so']}</span>{x.get('spark', '')}</div>"
        f"<div class='duoi'>{x.get('phu', '')}<span>{x.get('ghi', '')}</span></div></div>" for x in o) + "</div>")


def the(ten):
    """Thẻ nội dung (container có viền) – dùng với `with gd.the("…"):`."""
    return st.container(border=True, key=f"the-{ten}")


def tieu_the(tieu_de, phu=None, phai=None):
    st.html(f"<div class='tieu-the'><div><h3>{tieu_de}</h3>{f'<div class=phu>{phu}</div>' if phu else ''}</div>"
            f"{f'<div class=phai>{phai}</div>' if phai else ''}</div>")


def nguon(chu):
    st.html(f"<div class='nguon'>{chu}</div>")


def canh_bao(chu):
    st.html(f"<div class='canh-bao'><span class='i-tron'>i</span><span>{chu}</span></div>")


def chip(ma, ten=False):
    phu = f"<span>{e(cf.TEN_DAY_DU[ma])}</span>" if ten else ""
    return f"<span class='chip'><i style='background:var(--nh-{ma.lower()})'></i>{ma}{phu}</span>"


def sparkline(gia_tri, mau_duong=None, rong=110, cao=36, vung=True):
    v = np.asarray([x for x in gia_tri if x == x], dtype=float)
    if len(v) < 2:
        return ""
    lo, hi = v.min(), v.max()
    y = cao - 4 - (v - lo) / ((hi - lo) or 1) * (cao - 8)
    x = np.linspace(3, rong - 4, len(v))
    diem = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(x, y))
    mau_duong = mau_duong or mau()["nhan"]
    to = (f"<path d='M{x[0]:.1f},{cao} L{diem.replace(' ', ' L')} L{x[-1]:.1f},{cao} Z' fill='{mau_duong}' "
          f"fill-opacity='0.12'/>") if vung else ""
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{rong}' height='{cao}' viewBox='0 0 {rong} {cao}'>{to}"
           f"<polyline points='{diem}' fill='none' stroke='{mau_duong}' stroke-width='1.8' stroke-linejoin='round'/>"
           f"<circle cx='{x[-1]:.1f}' cy='{y[-1]:.1f}' r='2.6' fill='{mau_duong}'/></svg>")
    # st.html lọc thẻ <svg>, nên nhúng dưới dạng ảnh data URI
    return (f"<img src='data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}' width='{rong}' "
            f"height='{cao}' style='vertical-align:middle;flex:none' alt=''>")


def ds_tin(ds):
    """Danh sách tin doanh nghiệp: ds = iterable dòng có ngay_cong_bo, ma_nh, loai_su_kien_nhan, mo_ta_ngan, nguon."""
    return "".join(
        f"<div class='tin'><div class='ngay'>{r.ngay_cong_bo:%d/%m/%Y}</div><div>"
        f"<div class='meta'>{chip(r.ma_nh) + ' &nbsp;·&nbsp; ' if r.ma_nh else ''}{e(r.loai_su_kien_nhan)}</div>"
        f"<div class='tieu'><a href='{e(r.nguon)}' target='_blank'>{e(r.mo_ta_ngan)}</a></div></div></div>" for r in ds)


def dumbbell(dong, mau_qd, mau_tn):
    """Mỗi dòng một chỉ số: chấm quốc doanh và tư nhân trên thang riêng, nối bằng vạch (đậm = khác biệt rõ).
    dong = list dict(ten, qd, tn, y_nghia, ghi)."""
    html = []
    for r in dong:
        lo, hi = min(r["qd"], r["tn"]), max(r["qd"], r["tn"])
        dem = (hi - lo) * 0.45 + 0.3
        a, b = lo - dem, hi + dem

        def vt(v):
            return (v - a) / (b - a) * 100

        vach = "var(--muc2)" if r["y_nghia"] else "var(--ke2)"
        nhan = vien("Khác biệt rõ", "tot") if r["y_nghia"] else vien("Chưa khác biệt đáng kể")
        cham = "".join(
            f"<div style='position:absolute;left:{vt(v):.1f}%;top:32px;transform:translate(-50%,-50%);width:16px;"
            f"height:16px;border-radius:50%;background:{m};border:2px solid var(--mat)'></div>"
            f"<div style='position:absolute;left:{vt(v):.1f}%;top:0;transform:translateX(-50%);font-size:.8rem;"
            f"white-space:nowrap;color:var(--nhat)'>{t} <b class='num' style='color:var(--muc)'>{so(v)}</b></div>"
            for v, m, t in [(r["qd"], mau_qd, "QD"), (r["tn"], mau_tn, "TN")])
        html.append(
            "<div style='padding:12px 0;border-top:1px solid var(--ke)'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap'>"
            f"<b>{r['ten']}</b>{nhan}</div>"
            f"<div style='position:relative;height:46px;margin:6px 24px 0 24px'><div style='position:absolute;left:{vt(lo):.1f}%;"
            f"width:{vt(hi) - vt(lo):.1f}%;top:30px;height:4px;border-radius:2px;background:{vach}'></div>{cham}</div>"
            f"<div class='nguon'>{r.get('ghi', '')}</div></div>")
    st.html("".join(html))


def chan_trang():
    st.html(
        "<div class='nguon' style='margin-top:36px;border-top:1px solid var(--ke);padding-top:12px;display:flex;"
        "flex-wrap:wrap;justify-content:space-between;gap:6px 24px'>"
        f"<span><b style='color:var(--muc)'>{TEN}</b> · Nhóm 5 – Phân tích dữ liệu cho môi trường doanh nghiệp</span></div>")
