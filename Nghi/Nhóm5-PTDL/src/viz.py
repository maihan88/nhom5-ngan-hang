"""
viz.py – Các hàm vẽ biểu đồ dùng chung (Nhóm 5 PTDL)

Mọi hàm tuân theo hợp đồng trong QUY_UOC.md:
  • tên bắt đầu bằng ve_
  • tham số đầu là DataFrame đọc từ data_loader; tham số lọc: ma_nh, nam, chi_so
  • trả về plotly Figure; không show(), không ghi file
  • gọi cf.ap_dung_giao_dien() trước khi return

Danh sách hàm (Phần 2):
  So sánh chỉ số : ve_duong_chi_so, ve_cot_trung_binh_nam, ve_hop_chi_so, ve_tong_quan_chi_so
  Xu hướng giá   : ve_gia_chuan_hoa, ve_bien_do_gia
  Sự kiện        : ve_dem_su_kien, ve_gia_su_kien
"""
import textwrap

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import config as cf
from .data_loader import loc, thu_tu_ky


# ----------------------------------------------------------------------------
# Tiện ích nội bộ
# ----------------------------------------------------------------------------
def _thu_tu():
    return {"ma_nh": cf.DS_NGAN_HANG, "ky": thu_tu_ky(),
            "loai_hinh_so_huu": cf.DS_NHOM, "nam": [str(n) for n in cf.DS_NAM],
            "loai_su_kien_nhan": cf.DS_LOAI_SU_KIEN}


def _ve_chuoi(d):
    """Categorical -> str để plotly vẽ ổn định (thứ tự đã do category_orders lo)."""
    d = d.copy()
    for c in ["ma_nh", "quy", "loai_hinh_so_huu"]:
        if c in d:
            d[c] = d[c].astype(str)
    return d


def _kiem_chi_so(chi_so):
    if chi_so not in cf.DS_CHI_SO:
        raise ValueError(f"chi_so phải là một trong {cf.DS_CHI_SO}")


def _chi_lay_car_cong_bo(d, chi_so):
    """CAR chỉ dùng 32 số thật cuối năm 2021–2024 (công bố + tra thủ công); các chỉ số khác giữ nguyên."""
    return d[d["car_nguon"].isin(cf.CAR_NGUON_SO_THAT)] if chi_so == "car" else d


def _tieu_de_pham_vi(ma_nh, nam, d=None):
    """d: nếu truyền dữ liệu đã lọc thì khoảng năm lấy theo dữ liệu thực có (vd CAR chỉ đến 2024)."""
    if nam is None and d is not None and "nam" in d and len(d):
        nam = sorted(int(x) for x in d["nam"].unique())
    nh = "8 ngân hàng" if ma_nh is None else (ma_nh if isinstance(ma_nh, str) else ", ".join(ma_nh))
    if nam is None:
        n = f"{cf.NAM_BAT_DAU}–{cf.NAM_KET_THUC}"
    elif isinstance(nam, int):
        n = str(nam)
    else:
        n = f"{min(nam)}–{max(nam)}" if len(nam) > 1 else str(nam[0])
    return f"{nh}, {n}"


# ============================================================================
# 1. SO SÁNH 6 CHỈ SỐ GIỮA 8 NGÂN HÀNG
# ============================================================================
def ve_duong_chi_so(b4, chi_so="roe", ma_nh=None, nam=None, trung_binh_nganh=True):
    """Line chart chỉ số theo quý. CAR: vẽ theo năm, chỉ số công bố.

    trung_binh_nganh=True: thêm đường xám đứt = trung bình 8 ngân hàng (để so với 'mặt bằng').
    """
    _kiem_chi_so(chi_so)
    d = _ve_chuoi(_chi_lay_car_cong_bo(loc(b4, nam=nam), chi_so))
    truc_x = "nam" if chi_so == "car" else "ky"
    if truc_x == "nam":
        d["nam"] = d["nam"].astype(str)

    tb = d.groupby(truc_x, as_index=False)[chi_so].mean()
    d = loc(d, ma_nh=ma_nh)

    fig = px.line(d, x=truc_x, y=chi_so, color="ma_nh", markers=True,
                  color_discrete_map=cf.MAU_NGAN_HANG, category_orders=_thu_tu(),
                  hover_data={"loai_hinh_so_huu": True})
    if trung_binh_nganh:
        fig.add_trace(go.Scatter(x=tb[truc_x], y=tb[chi_so], name="TB 8 NH",
                                 mode="lines", line=dict(color=cf.MAU_TRUNG_TINH, dash="dash", width=2)))
    ghi_chu = " (số công bố cuối năm)" if chi_so == "car" else " theo quý"
    return cf.ap_dung_giao_dien(fig, f"{cf.NHAN_CHI_SO[chi_so]}{ghi_chu} – {_tieu_de_pham_vi(ma_nh, nam, d)}",
                                "Năm" if chi_so == "car" else "Quý", cf.NHAN_CHI_SO[chi_so])


def ve_cot_trung_binh_nam(b4, chi_so="roe", ma_nh=None, nam=None):
    """Bar chart trung bình năm (trung bình 4 quý) theo ngân hàng. CAR: số công bố của năm."""
    _kiem_chi_so(chi_so)
    d = _ve_chuoi(_chi_lay_car_cong_bo(loc(b4, ma_nh=ma_nh, nam=nam), chi_so))
    tb = d.groupby(["nam", "ma_nh"], as_index=False)[chi_so].mean()
    tb["nam"] = tb["nam"].astype(str)
    fig = px.bar(tb, x="nam", y=chi_so, color="ma_nh", barmode="group",
                 color_discrete_map=cf.MAU_NGAN_HANG, category_orders=_thu_tu())
    fig.update_traces(hovertemplate="%{x} – %{fullData.name}: %{y:.2f}%<extra></extra>")
    ghi_chu = "số công bố cuối năm" if chi_so == "car" else "trung bình 4 quý"
    fig = cf.ap_dung_giao_dien(fig, f"{cf.NHAN_CHI_SO[chi_so]}, {ghi_chu} – {_tieu_de_pham_vi(ma_nh, nam, tb)}",
                               "Năm", cf.NHAN_CHI_SO[chi_so])
    fig.update_layout(hovermode="closest", bargap=0.18)
    return fig


def ve_hop_chi_so(b4, chi_so="roe", ma_nh=None, nam=None, theo="ma_nh"):
    """Boxplot phân phối chỉ số theo ngân hàng (theo='ma_nh') hoặc theo nhóm sở hữu
    (theo='loai_hinh_so_huu', dùng lại ở Phần 4). Mỗi chấm = 1 quý."""
    _kiem_chi_so(chi_so)
    d = _ve_chuoi(_chi_lay_car_cong_bo(loc(b4, ma_nh=ma_nh, nam=nam), chi_so))
    mau = cf.MAU_NGAN_HANG if theo == "ma_nh" else cf.MAU_NHOM
    fig = px.box(d, x=theo, y=chi_so, color=theo, points="all",
                 color_discrete_map=mau, category_orders=_thu_tu(),
                 hover_data={"ky": True, "ma_nh": True})
    fig.update_traces(jitter=0.35, pointpos=0, marker=dict(size=5, opacity=0.6))
    don_vi = "năm (CAR công bố)" if chi_so == "car" else "quý"
    fig = cf.ap_dung_giao_dien(
        fig, f"Phân phối {cf.NHAN_CHI_SO[chi_so]} – {_tieu_de_pham_vi(ma_nh, nam, d)} (mỗi chấm = 1 {don_vi})",
        "Ngân hàng" if theo == "ma_nh" else "Nhóm sở hữu", cf.NHAN_CHI_SO[chi_so])
    fig.update_layout(showlegend=False, hovermode="closest")
    return fig


def ve_tong_quan_chi_so(b4, ma_nh=None, nam=None):
    """Lưới 2×3 boxplot cho cả 6 chỉ số – 1 hình tổng quan cho báo cáo."""
    d = _ve_chuoi(loc(b4, ma_nh=ma_nh, nam=nam))
    d.loc[~d["car_nguon"].isin(cf.CAR_NGUON_SO_THAT), "car"] = float("nan")     # CAR: chỉ số thật
    dai = d.melt(id_vars=["ma_nh", "ky"], value_vars=cf.DS_CHI_SO,
                 var_name="chi_so", value_name="gia_tri").dropna(subset=["gia_tri"])
    dai["chi_so"] = dai["chi_so"].map(cf.NHAN_CHI_SO)
    fig = px.box(dai, x="ma_nh", y="gia_tri", color="ma_nh", facet_col="chi_so", facet_col_wrap=3,
                 color_discrete_map=cf.MAU_NGAN_HANG,
                 category_orders={**_thu_tu(), "chi_so": [cf.NHAN_CHI_SO[c] for c in cf.DS_CHI_SO]},
                 facet_row_spacing=0.14, facet_col_spacing=0.06)
    fig.update_yaxes(matches=None, showticklabels=True, title_text="")
    fig.update_xaxes(title_text="", tickangle=0, showticklabels=True)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=13)))
    fig = cf.ap_dung_giao_dien(fig, f"Tổng quan 6 chỉ số theo ngân hàng – {_tieu_de_pham_vi(ma_nh, nam)}")
    fig.update_layout(showlegend=False, height=640, hovermode="closest")
    return fig


# ============================================================================
# 2. XU HƯỚNG GIÁ CỔ PHIẾU
# ============================================================================
def them_gia_chuan_hoa(gia, moc=None):
    """Thêm cột gia_chuan_hoa = giá điều chỉnh / giá phiên mốc × 100.
    moc=None: phiên đầu tiên có trong dữ liệu truyền vào (mặc định 04/01/2021)."""
    d = gia.sort_values(["ma_nh", "ngay"]).copy()
    if moc is not None:
        d = d[d["ngay"] >= pd.Timestamp(moc)]
    goc = d.groupby("ma_nh", observed=True)["gia_dong_cua_dieu_chinh"].transform("first")
    d["gia_chuan_hoa"] = d["gia_dong_cua_dieu_chinh"] / goc * 100
    return d


def ve_gia_chuan_hoa(gia, ma_nh=None, nam=None, dat_moc_lai=False):
    """Đường giá điều chỉnh chuẩn hóa = 100 tại phiên đầu năm 2021.

    dat_moc_lai=True: đặt mốc 100 tại phiên đầu của khoảng năm được lọc
    (hữu ích trên dashboard khi chỉ xem 1–2 năm).
    """
    d = loc(gia, ma_nh=ma_nh, nam=nam) if dat_moc_lai else gia
    d = them_gia_chuan_hoa(d)
    d = _ve_chuoi(loc(d, ma_nh=ma_nh, nam=nam))
    moc = d["ngay"].min()
    fig = px.line(d, x="ngay", y="gia_chuan_hoa", color="ma_nh",
                  color_discrete_map=cf.MAU_NGAN_HANG, category_orders=_thu_tu())
    fig.update_traces(line=dict(width=1.8), hovertemplate="%{fullData.name}: %{y:.0f}<extra></extra>")
    fig.add_hline(y=100, line=dict(color=cf.MAU_TRUNG_TINH, dash="dot", width=1))
    return cf.ap_dung_giao_dien(
        fig, f"Giá cổ phiếu điều chỉnh, chuẩn hóa = 100 tại phiên {moc:%d/%m/%Y} – {_tieu_de_pham_vi(ma_nh, nam)}",
        "Ngày", cf.NHAN_CHI_SO["gia_chuan_hoa"])


def ve_bien_do_gia(b4, ma_nh=None, nam=None, kieu="heatmap"):
    """Biên độ dao động giá trong quý (%) = (max − min)/min.
    kieu='heatmap' (ngân hàng × quý, dễ đọc cho 8 mã) hoặc 'line'."""
    d = _ve_chuoi(loc(b4, ma_nh=ma_nh, nam=nam))
    cot = "bien_dong_gia_max_min"
    if kieu == "line":
        fig = px.line(d, x="ky", y=cot, color="ma_nh", markers=True,
                      color_discrete_map=cf.MAU_NGAN_HANG, category_orders=_thu_tu())
        return cf.ap_dung_giao_dien(fig, f"Biên độ giá trong quý – {_tieu_de_pham_vi(ma_nh, nam)}",
                                    "Quý", cf.NHAN_CHI_SO[cot])
    bang = d.pivot_table(index="ma_nh", columns="ky", values=cot)
    bang = bang.reindex(index=[n for n in cf.DS_NGAN_HANG if n in bang.index],
                        columns=[k for k in thu_tu_ky() if k in bang.columns])
    fig = px.imshow(bang, text_auto=".0f", aspect="auto", color_continuous_scale="Oranges",
                    labels=dict(x="Quý", y="Ngân hàng", color="Biên độ (%)"))
    fig.update_traces(hovertemplate="%{y} %{x}: %{z:.1f}%<extra></extra>")
    fig = cf.ap_dung_giao_dien(fig, f"Biên độ giá trong quý (%) – {_tieu_de_pham_vi(ma_nh, nam)}",
                               "Quý", "Ngân hàng")
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(tickangle=-45)
    return fig


# ============================================================================
# 3. SỰ KIỆN PHI TÀI CHÍNH
# ============================================================================
def ve_dem_su_kien(su_kien, theo="ma_nh", ma_nh=None, nam=None):
    """Cột chồng: số sự kiện theo ngân hàng (theo='ma_nh') hoặc theo năm (theo='nam'),
    tách màu theo loại sự kiện. su_kien = bảng 3a (doc_su_kien_chi_tiet)."""
    d = _ve_chuoi(loc(su_kien, ma_nh=ma_nh, nam=nam))
    if theo == "nam":
        d["nam"] = d["nam"].astype(str)
    dem = d.groupby([theo, "loai_su_kien_nhan"], as_index=False).size().rename(columns={"size": "so_su_kien"})
    tong = dem.groupby(theo, as_index=False)["so_su_kien"].sum()
    fig = px.bar(dem, x=theo, y="so_su_kien", color="loai_su_kien_nhan",
                 color_discrete_map=cf.MAU_SU_KIEN, category_orders=_thu_tu())
    fig.add_trace(go.Scatter(x=tong[theo], y=tong["so_su_kien"], text=tong["so_su_kien"],
                             mode="text", textposition="top center", showlegend=False, hoverinfo="skip"))
    fig.update_traces(selector=dict(type="bar"),
                      hovertemplate="%{x} – %{fullData.name}: %{y}<extra></extra>")
    fig = cf.ap_dung_giao_dien(
        fig, f"Số sự kiện phi tài chính theo {'ngân hàng' if theo == 'ma_nh' else 'năm'} – "
             f"{_tieu_de_pham_vi(ma_nh, nam)} (tổng {len(d)})",
        "Ngân hàng" if theo == "ma_nh" else "Năm", cf.NHAN_CHI_SO["so_luong_su_kien"], chu_thich="Loại sự kiện")
    fig.update_layout(barmode="stack", hovermode="closest")
    fig.update_yaxes(range=[0, tong["so_su_kien"].max() * 1.15])
    return fig


def ve_gia_su_kien(gia, su_kien, ma_nh="VCB", nam=None, hien_khoi_luong=True):
    """Đường giá điều chỉnh của 1 ngân hàng + đánh dấu ngày công bố sự kiện
    (tam giác, màu theo loại; rê chuột xem tiêu đề tin). Dưới là khối lượng khớp lệnh."""
    if not isinstance(ma_nh, str):
        raise ValueError("ve_gia_su_kien chỉ vẽ 1 ngân hàng, ví dụ ma_nh='VCB'")
    g = loc(gia, ma_nh=ma_nh, nam=nam).sort_values("ngay")
    sk = loc(su_kien, ma_nh=ma_nh, nam=nam).copy()

    # Gắn sự kiện vào phiên giao dịch gần nhất trước/đúng ngày công bố (tin ra cuối tuần -> phiên thứ 6)
    sk["ngay_phien"] = sk["ngay_cong_bo"].dt.normalize()
    sk = pd.merge_asof(sk.sort_values("ngay_phien"),
                       g[["ngay", "gia_dong_cua_dieu_chinh"]].rename(columns={"ngay": "ngay_phien"}),
                       on="ngay_phien", direction="backward")
    sk["mo_ta_hover"] = sk["mo_ta_ngan"].fillna("").map(lambda s: "<br>".join(textwrap.wrap(s, 60)))

    so_hang = 2 if hien_khoi_luong else 1
    fig = make_subplots(rows=so_hang, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                        row_heights=[0.75, 0.25] if hien_khoi_luong else [1])
    fig.add_trace(go.Scatter(x=g["ngay"], y=g["gia_dong_cua_dieu_chinh"], name=f"Giá {ma_nh}",
                             line=dict(color=cf.MAU_NGAN_HANG[ma_nh], width=1.6),
                             hovertemplate="%{x|%d/%m/%Y}: %{y:.2f}<extra></extra>"), row=1, col=1)
    for loai in cf.DS_LOAI_SU_KIEN:
        s = sk[sk["loai_su_kien_nhan"] == loai]
        if s.empty:
            continue
        fig.add_trace(go.Scatter(
            x=s["ngay_phien"], y=s["gia_dong_cua_dieu_chinh"], mode="markers", name=loai,
            marker=dict(symbol="triangle-down", size=12, color=cf.MAU_SU_KIEN[loai],
                        line=dict(width=1, color="white")),
            customdata=s[["ngay_cong_bo", "mo_ta_hover"]],
            hovertemplate="<b>" + loai + "</b> – %{customdata[0]|%d/%m/%Y}<br>%{customdata[1]}<extra></extra>"),
            row=1, col=1)
    if hien_khoi_luong:
        fig.add_trace(go.Bar(x=g["ngay"], y=g["khoi_luong_gd"] / 1e6, name="KL khớp lệnh",
                             marker_color="#8C8C8C", marker_line_width=0, showlegend=False,
                             hovertemplate="%{x|%d/%m/%Y}: %{y:.2f} triệu cp<extra></extra>"), row=2, col=1)
        fig.update_yaxes(title_text="KL (triệu cp)", row=2, col=1)

    fig = cf.ap_dung_giao_dien(
        fig, f"{cf.TEN_DAY_DU[ma_nh]} ({ma_nh}): giá điều chỉnh và {len(sk)} sự kiện – {_tieu_de_pham_vi(None, nam).split(', ')[1]}",
        chu_thich="Loại sự kiện")
    fig.update_yaxes(title_text=cf.NHAN_CHI_SO["gia_dong_cua_dieu_chinh"], row=1, col=1)
    fig.update_layout(hovermode="closest", height=600 if hien_khoi_luong else 480)
    return fig


# ============================================================================
# 4. XẾP HẠNG SINH LỜI (PHẦN 3 – CÂU 1)
#    Đầu vào: nam_df = thong_ke.tinh_chi_so_nam(b1); xh = thong_ke.xep_hang(nam_df, ...)
# ============================================================================
def ve_xu_huong_nam(nam_df, chi_so="roe_nam", ma_nh=None):
    """Line chart ROA/ROE năm (tổng LNST 4 quý / TB số dư cuối 4 quý) + đường TB 8 NH."""
    d = _ve_chuoi(nam_df)
    tb = d.groupby("nam", as_index=False)[chi_so].mean()
    d = loc(d, ma_nh=ma_nh)
    fig = px.line(d, x="nam", y=chi_so, color="ma_nh", markers=True,
                  color_discrete_map=cf.MAU_NGAN_HANG, category_orders=_thu_tu())
    fig.add_trace(go.Scatter(x=tb["nam"], y=tb[chi_so], name="TB 8 NH", mode="lines",
                             line=dict(color=cf.MAU_TRUNG_TINH, dash="dash", width=2)))
    fig.update_traces(hovertemplate="%{x} – %{fullData.name}: %{y:.2f}%<extra></extra>")
    fig.update_xaxes(dtick=1)
    fig = cf.ap_dung_giao_dien(fig, f"{cf.NHAN_CHI_SO[chi_so]} – {_tieu_de_pham_vi(ma_nh, None, d)}",
                               "Năm", cf.NHAN_CHI_SO[chi_so])
    fig.update_layout(hovermode="closest")
    return fig


def ve_bump_xep_hang(xh, ma_nh=None):
    """Bump chart: thứ hạng 8 NH qua các năm (hạng 1 ở trên cùng).

    ma_nh: list ngân hàng muốn làm nổi bật; các ngân hàng khác vẽ mờ (None = tô màu tất cả).
    """
    d = _ve_chuoi(xh)
    chi_so = d["chi_so"].iloc[0]
    noi_bat = cf.DS_NGAN_HANG if ma_nh is None else ([ma_nh] if isinstance(ma_nh, str) else list(ma_nh))
    nam_cuoi = d["nam"].max()
    fig = go.Figure()
    for nh in cf.DS_NGAN_HANG:
        s = d[d["ma_nh"] == nh].sort_values("nam")
        if s.empty:
            continue
        sang = nh in noi_bat
        mau = cf.MAU_NGAN_HANG[nh] if sang else "#D0D0D0"
        fig.add_trace(go.Scatter(
            x=s["nam"], y=s["hang"], name=nh, mode="lines+markers+text",
            line=dict(color=mau, width=4 if sang else 2),
            marker=dict(size=26 if sang else 18, color=mau, line=dict(color="white", width=2)),
            text=s["hang"], textfont=dict(color="white", size=12), textposition="middle center",
            customdata=s[["gia_tri"]],
            hovertemplate=f"<b>{nh}</b> %{{x}}: hạng %{{y}} – %{{customdata[0]:.2f}}%<extra></extra>",
            showlegend=False, opacity=1 if sang else 0.6))
        cuoi = s[s["nam"] == nam_cuoi]
        if len(cuoi):
            fig.add_annotation(x=nam_cuoi, y=int(cuoi["hang"].iloc[0]), text=f"<b>{nh}</b>",
                               xanchor="left", xshift=20, showarrow=False,
                               font=dict(color=mau if sang else "#A0A0A0", size=13))
    n = d["ma_nh"].nunique()
    fig.update_yaxes(autorange="reversed", tickvals=list(range(1, n + 1)), range=[n + 0.6, 0.4])
    fig.update_xaxes(dtick=1, range=[d["nam"].min() - 0.3, nam_cuoi + 0.6])
    fig = cf.ap_dung_giao_dien(fig, f"Thứ hạng {cf.NHAN_CHI_SO[chi_so]} của 8 ngân hàng qua các năm",
                               "Năm", "Hạng (1 = cao nhất)")
    fig.update_layout(hovermode="closest", height=520)
    fig.update_yaxes(showgrid=False)
    return fig


def ve_bang_xep_hang(xh):
    """Bảng màu xếp hạng: hàng = NH (theo hạng TB), cột = năm, ô ghi 'hạng (giá trị %)'.
    Ô càng xanh đậm hạng càng cao."""
    d = _ve_chuoi(xh)
    chi_so = d["chi_so"].iloc[0]
    hang = d.pivot(index="ma_nh", columns="nam", values="hang")
    thu_tu = hang.mean(axis=1).sort_values().index
    hang = hang.loc[thu_tu]
    gt = d.pivot(index="ma_nh", columns="nam", values="gia_tri").loc[thu_tu]
    chu = hang.astype(int).astype(str) + "<br>(" + gt.round(1).astype(str) + "%)"
    fig = go.Figure(go.Heatmap(
        z=hang.values, x=[str(c) for c in hang.columns], y=list(hang.index),
        text=chu.values, texttemplate="%{text}", colorscale="Blues_r", zmin=1, zmax=len(hang) + 2,
        showscale=False, hovertemplate="%{y} %{x}: hạng %{z}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig = cf.ap_dung_giao_dien(fig, f"Bảng xếp hạng {cf.NHAN_CHI_SO[chi_so]} (sắp theo hạng trung bình)",
                               "Năm", "")
    fig.update_layout(hovermode="closest", height=480)
    return fig


# ============================================================================
# 5. SO SÁNH QUỐC DOANH vs TƯ NHÂN (PHẦN 4 – CÂU 2)
#    Đầu vào: dl = thong_ke.du_lieu_cau2(b4); dùng dl['nh_nam'] (NIM, NPL) hoặc dl['car']
# ============================================================================
def ve_hop_nhom(df, chi_so="nim", ghi_chu=None):
    """Boxplot 2 nhóm sở hữu; mỗi chấm = 1 quan sát dùng trong kiểm định, tô màu theo ngân hàng
    (để thấy ngân hàng nào kéo nhóm lên/xuống). ghi_chu: dòng phụ dưới tiêu đề (vd kết quả kiểm định)."""
    d = _ve_chuoi(df)
    fig = go.Figure()
    for i, nhom in enumerate(cf.DS_NHOM):
        s = d[d["loai_hinh_so_huu"] == nhom]
        fig.add_trace(go.Box(y=s[chi_so], x=[i] * len(s), name=nhom, boxpoints=False, width=0.55,
                             marker_color=cf.MAU_NHOM[nhom], line=dict(width=2),
                             fillcolor="rgba(0,0,0,0)", showlegend=False, hoverinfo="skip"))
    rng = np.random.default_rng(1)          # rung ngẫu nhiên cố định để chấm không chồng nhau
    for nh in cf.DS_NGAN_HANG:
        s = d[d["ma_nh"] == nh]
        if s.empty:
            continue
        x_so = cf.DS_NHOM.index(cf.NHOM_CUA_NH[nh]) + rng.uniform(-0.18, 0.18, len(s))
        fig.add_trace(go.Scatter(
            x=x_so, y=s[chi_so], mode="markers", name=nh,
            marker=dict(color=cf.MAU_NGAN_HANG[nh], size=9, line=dict(color="white", width=1)),
            customdata=s[["nam"]] if "nam" in s else None,
            hovertemplate=f"<b>{nh}</b>" + (" %{customdata[0]}" if "nam" in s else "") + ": %{y:.2f}%<extra></extra>"))
    fig.update_xaxes(tickvals=[0, 1], ticktext=cf.DS_NHOM, range=[-0.6, 1.6])
    don_vi = "ngân hàng–năm" if "nam" in d else "ngân hàng"
    tieu_de = f"{cf.NHAN_CHI_SO[chi_so]}: quốc doanh vs tư nhân (mỗi chấm = 1 {don_vi})"
    if ghi_chu:
        tieu_de += f"<br><sup>{ghi_chu}</sup>"
    fig = cf.ap_dung_giao_dien(fig, tieu_de, "Nhóm sở hữu", cf.NHAN_CHI_SO[chi_so])
    fig.update_layout(hovermode="closest", boxmode="overlay")
    return fig


def ve_duong_nhom(df, chi_so="nim", bo_ma=None):
    """Trung bình 2 nhóm sở hữu theo năm. bo_ma: list mã muốn thêm đường 'Tư nhân (bỏ ...)'
    nét đứt, vd bo_ma=['VPB'] để thấy riêng VPB kéo nhóm tư nhân lên bao nhiêu."""
    d = _ve_chuoi(df)
    tb = d.groupby(["nam", "loai_hinh_so_huu"], as_index=False)[chi_so].mean()
    fig = go.Figure()
    for nhom in cf.DS_NHOM:
        s = tb[tb["loai_hinh_so_huu"] == nhom]
        fig.add_trace(go.Scatter(x=s["nam"], y=s[chi_so], name=nhom, mode="lines+markers",
                                 line=dict(color=cf.MAU_NHOM[nhom], width=3), marker=dict(size=9)))
    if bo_ma:
        bo_ma = [bo_ma] if isinstance(bo_ma, str) else list(bo_ma)
        s = (d[(d["loai_hinh_so_huu"] == cf.NHOM_TU_NHAN) & (~d["ma_nh"].isin(bo_ma))]
             .groupby("nam", as_index=False)[chi_so].mean())
        fig.add_trace(go.Scatter(x=s["nam"], y=s[chi_so], name=f"Tư nhân (bỏ {', '.join(bo_ma)})",
                                 mode="lines+markers",
                                 line=dict(color=cf.MAU_NHOM[cf.NHOM_TU_NHAN], width=2, dash="dash"),
                                 marker=dict(size=7, symbol="circle-open")))
    fig.update_traces(hovertemplate="%{x} – %{fullData.name}: %{y:.2f}%<extra></extra>")
    fig.update_xaxes(dtick=1)
    fig = cf.ap_dung_giao_dien(fig, f"{cf.NHAN_CHI_SO[chi_so]} trung bình theo nhóm sở hữu",
                               "Năm", cf.NHAN_CHI_SO[chi_so], chu_thich="Nhóm")
    fig.update_layout(hovermode="closest")
    return fig


# ============================================================================
# 6. TƯƠNG QUAN VỚI LỢI SUẤT CỔ PHIẾU (PHẦN 5 – CÂU 3)
#    Đầu vào: b4 (doc_tong_hop) hoặc bảng kết quả từ thong_ke.tuong_quan_voi_loi_suat
# ============================================================================
TEN_MAU_TQ = {
    "chinh": "Chính (160 quý)",
    "loai_bien_dong_chung": "Bỏ biến động chung",
    "thay_doi_chi_so": "Thay đổi chỉ số",
    "q4_2021_2024": "Chỉ quý 4 (32)",
    "car_cong_bo": "CAR công bố (32)",
    "cap_ngan_hang": "Cấp ngân hàng (8)",
}


def ve_ma_tran_tuong_quan(df, cot=None, phuong_phap="spearman"):
    """Heatmap ma trận tương quan giữa 6 chỉ số và lợi suất quý (đỏ = dương, xanh = âm)."""
    cot = cot or cf.DS_CHI_SO + ["ty_suat_sinh_loi_quy"]
    m = df[cot].corr(method=phuong_phap)
    ten = [cf.TEN_NGAN.get(c, c) for c in cot]
    m.index, m.columns = ten, ten
    fig = px.imshow(m, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r", aspect="auto")
    fig.update_traces(hovertemplate="%{y} – %{x}: %{z:.2f}<extra></extra>")
    fig = cf.ap_dung_giao_dien(
        fig, f"Ma trận tương quan {'Spearman' if phuong_phap == 'spearman' else 'Pearson'} "
             f"(n = {len(df)} ngân hàng–quý)")
    fig.update_layout(hovermode="closest", height=560, coloraxis_colorbar=dict(title="Hệ số"))
    return fig


def ve_cot_tuong_quan(tq, mau_du_lieu="chinh"):
    """Thanh ngang: hệ số Pearson & Spearman của 6 chỉ số với lợi suất, sắp theo độ mạnh.
    Ghi p-value đã hiệu chỉnh cạnh mỗi thanh Spearman."""
    d = tq[tq["mau_du_lieu"] == mau_du_lieu].copy()
    d["ten"] = d["chi_so"].map(cf.TEN_NGAN)
    d = d.sort_values("spearman_rho", key=lambda s: s.abs())
    fig = go.Figure()
    fig.add_trace(go.Bar(y=d["ten"], x=d["pearson_r"], name="Pearson r", orientation="h",
                         marker_color="#9DB9D8",
                         hovertemplate="%{y}: r = %{x:.3f}<extra></extra>"))
    fig.add_trace(go.Bar(y=d["ten"], x=d["spearman_rho"], name="Spearman ρ", orientation="h",
                         marker_color="#2F6DB5",
                         text=[f"p hc = {p:.2f}" for p in d["spearman_p_hieu_chinh"]],
                         textposition="outside", cliponaxis=False,
                         hovertemplate="%{y}: ρ = %{x:.3f}<extra></extra>"))
    lim = max(0.3, d[["pearson_r", "spearman_rho"]].abs().max().max() * 1.6)
    fig.update_xaxes(range=[-lim, lim], zeroline=True, zerolinecolor="#888", zerolinewidth=1)
    n = int(d["so_quan_sat"].iloc[0])
    fig = cf.ap_dung_giao_dien(
        fig, f"Tương quan của 6 chỉ số với lợi suất cổ phiếu quý – {TEN_MAU_TQ.get(mau_du_lieu, mau_du_lieu)}"
             f"<br><sup>n = {n}; p hc = p-value Spearman đã hiệu chỉnh Holm (có ý nghĩa nếu < 0,05)</sup>",
        "Hệ số tương quan", "", chu_thich="")
    fig.update_layout(barmode="group", hovermode="closest", height=470)
    return fig


def ve_tuong_quan_so_sanh(tq, gia_tri="spearman_rho", bo_mau=("car_cong_bo",)):
    """Heatmap chỉ số × cách kiểm tra: xem kết luận có thay đổi khi đổi mẫu/cách tính không.
    * = p < 0,05 chưa hiệu chỉnh; ** = vẫn < 0,05 sau hiệu chỉnh Holm.
    bo_mau: mẫu không vẽ (mặc định bỏ 'car_cong_bo' vì trùng ô CAR của mẫu quý 4)."""
    d = tq[~tq["mau_du_lieu"].isin(bo_mau or [])].copy()
    cot_p = gia_tri.split("_")[0] + "_p"
    d["sao"] = np.where(d[cot_p + "_hieu_chinh"] < 0.05, "**", np.where(d[cot_p] < 0.05, "*", ""))
    thu_tu_mau = [m for m in TEN_MAU_TQ if m in d["mau_du_lieu"].unique()]
    z = d.pivot(index="chi_so", columns="mau_du_lieu", values=gia_tri).reindex(index=cf.DS_CHI_SO, columns=thu_tu_mau)
    chu = (d.assign(t=d[gia_tri].map(lambda v: f"{v:.2f}") + d["sao"])
           .pivot(index="chi_so", columns="mau_du_lieu", values="t").reindex(index=cf.DS_CHI_SO, columns=thu_tu_mau))
    fig = go.Figure(go.Heatmap(
        z=z.values, x=[TEN_MAU_TQ[m] for m in thu_tu_mau], y=[cf.TEN_NGAN[c] for c in z.index],
        text=chu.fillna("").values, texttemplate="%{text}", zmin=-1, zmax=1, colorscale="RdBu_r",
        colorbar=dict(title="ρ"), hovertemplate="%{y} – %{x}: %{z:.2f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig = cf.ap_dung_giao_dien(
        fig, "Tương quan Spearman với lợi suất quý theo từng cách kiểm tra"
             "<br><sup>* p < 0,05 chưa hiệu chỉnh · ** vẫn < 0,05 sau hiệu chỉnh Holm</sup>")
    fig.update_layout(hovermode="closest", height=480)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def ve_phan_tan(df, chi_so="roe", bien="ty_suat_sinh_loi_quy", ma_nh=None, ghi_chu=None):
    """Scatter chỉ số – lợi suất, mỗi chấm = 1 ngân hàng–quý, kèm đường hồi quy OLS chung (xám)."""
    d = _ve_chuoi(loc(df, ma_nh=ma_nh)).dropna(subset=[chi_so, bien])
    fig = px.scatter(d, x=chi_so, y=bien, color="ma_nh", color_discrete_map=cf.MAU_NGAN_HANG,
                     category_orders=_thu_tu(), trendline="ols", trendline_scope="overall",
                     trendline_color_override=cf.MAU_TRUNG_TINH,
                     hover_data={"ky": True} if "ky" in d else None)
    fig.update_traces(selector=dict(mode="markers"), marker=dict(size=8, opacity=0.8,
                                                                  line=dict(color="white", width=0.5)))
    fig.update_traces(selector=dict(mode="lines"), name="Đường hồi quy (OLS)",
                      hovertemplate="Đường hồi quy: %{y:.2f}%<extra></extra>")
    fig.add_hline(y=0, line=dict(color="#BBB", width=1))
    r = d[[chi_so, bien]].corr().iloc[0, 1]
    rho = d[[chi_so, bien]].corr(method="spearman").iloc[0, 1]
    tieu_de = (f"{cf.TEN_NGAN.get(chi_so, chi_so)} và lợi suất cổ phiếu quý "
               f"(n = {len(d)}, Pearson r = {r:.2f}, Spearman ρ = {rho:.2f})")
    if ghi_chu:
        tieu_de += f"<br><sup>{ghi_chu}</sup>"
    fig = cf.ap_dung_giao_dien(fig, tieu_de, cf.NHAN_CHI_SO.get(chi_so, chi_so), cf.NHAN_CHI_SO[bien])
    fig.update_layout(hovermode="closest")
    return fig
