"""
bieu_do.py – Biểu đồ kiểu báo chí cho dashboard.

Quy tắc chung:
  • Màu chỉ dành cho đối tượng đang được nói tới (màu ngân hàng theo src/config.py của Nghi);
    phần còn lại xám nhạt làm nền để so sánh.
  • Nhãn ghi thẳng ở cuối đường thay cho hộp chú giải; đơn vị nằm trên vạch trục.
  • Lưới ngang mảnh, không lưới dọc, không tiêu đề trong hình (tiêu đề là câu kết luận ở trên).
  • Số kiểu Việt (dấu phẩy thập phân).
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import config as cf
from web.giao_dien import MAU, SANS, so

XAM = MAU["nen_xam"]
MAU_NHOM = {"A": "#9DAFC0", "B": "#C2702F", "C": "#6B8F5E", "D": "#8E6C9E"}   # A = nhóm đông nhất, để nhạt


def nen(fig, cao=360, hover="x unified", chu_giai=False, phai=12, tren=None):
    fig.update_layout(
        height=cao, margin=dict(l=4, r=phai, t=tren if tren is not None else (34 if chu_giai else 10), b=4),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", separators=",.",
        font=dict(family=SANS, size=12.5, color=MAU["muc2"]), hovermode=hover, showlegend=chu_giai,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title=None, font=dict(size=12)),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=MAU["ke"], font=dict(family=SANS, size=12.5, color=MAU["muc"])),
        barcornerradius=2,
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=MAU["muc2"], linewidth=1, ticks="outside",
                     tickcolor=MAU["ke"], ticklen=4, automargin=True, title=None, tickfont=dict(color=MAU["muc2"]))
    fig.update_yaxes(gridcolor=MAU["luoi"], zeroline=False, showline=False, ticks="", automargin=True, title=None,
                     tickfont=dict(color=MAU["muc2"]))
    return fig


def ve(fig, key=None):
    st.plotly_chart(fig, theme=None, width="stretch", key=key, config={"displayModeBar": False})


def _nhan_cuoi(fig, nhan, x, khoang):
    """Nhãn cuối đường, tự giãn để không đè nhau. nhan = list (y, chữ, đậm?)."""
    nhan = sorted(nhan, key=lambda t: -t[0])
    y_dat = []
    for y, *_ in nhan:
        y_dat.append(min(y, y_dat[-1] - khoang) if y_dat else y)
    for (y, chu, dam), yd in zip(nhan, y_dat):
        fig.add_annotation(x=x, y=yd, text=f"<b>{chu}</b>" if dam else chu, showarrow=False, xanchor="left",
                           xshift=8, font=dict(size=12, color=MAU["muc"] if dam else MAU["nhat"]))


# ============================================================================
# Đường theo thời gian
# ============================================================================
def duong(df, x, y, noi_bat, don_vi="%", trung_vi=True, cao=380, le=2, nhan_tat_ca=False, dau=False):
    """Mỗi ngân hàng một đường; ngân hàng trong noi_bat có màu + nhãn cuối, còn lại xám.
    df dạng dài với cột ma_nh, x, y."""
    fig = go.Figure()
    thu_tu = sorted(df[x].unique())
    for ma in cf.DS_NGAN_HANG:
        if ma in noi_bat:
            continue
        s = df[df["ma_nh"] == ma].sort_values(x)
        fig.add_trace(go.Scatter(x=s[x], y=s[y], mode="lines", line=dict(color=XAM, width=1.2), name=ma,
                                 hovertemplate=f"{ma}: %{{y:,.{le}f}}{don_vi}<extra></extra>"))
    if trung_vi:
        tv = df.groupby(x)[y].median().reindex(thu_tu)
        fig.add_trace(go.Scatter(x=tv.index, y=tv.values, mode="lines", name="Trung vị 8 NH",
                                 line=dict(color=MAU["muc2"], width=1.3, dash="dot"),
                                 hovertemplate=f"Trung vị: %{{y:,.{le}f}}{don_vi}<extra></extra>"))
    nhan = []
    for ma in noi_bat:
        s = df[df["ma_nh"] == ma].sort_values(x).dropna(subset=[y])
        if s.empty:
            continue
        fig.add_trace(go.Scatter(x=s[x], y=s[y], mode="lines", name=ma, line=dict(color=cf.MAU_NGAN_HANG[ma], width=2.6),
                                 hovertemplate=f"<b>{ma}</b>: %{{y:,.{le}f}}{don_vi}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[s[x].iloc[-1]], y=[s[y].iloc[-1]], mode="markers", hoverinfo="skip",
                                 marker=dict(size=8, color=cf.MAU_NGAN_HANG[ma], line=dict(color=MAU["giay"], width=2))))
        nhan.append((s[y].iloc[-1], f"{ma} {so(s[y].iloc[-1], le, don_vi, dau=dau)}", True))
    if nhan_tat_ca:
        for ma in [m for m in cf.DS_NGAN_HANG if m not in noi_bat]:
            s = df[df["ma_nh"] == ma].sort_values(x).dropna(subset=[y])
            if len(s):
                nhan.append((s[y].iloc[-1], ma, False))
    pham_vi = df[y].max() - df[y].min()
    _nhan_cuoi(fig, nhan, df[x].max() if not isinstance(df[x].iloc[0], str) else thu_tu[-1], pham_vi * 0.055)
    nen(fig, cao, phai=96)
    fig.update_yaxes(ticksuffix=don_vi if don_vi.strip() == "%" else "")
    if pd.api.types.is_datetime64_any_dtype(df[x]):
        fig.update_xaxes(tickformat="%m/%Y", hoverformat="%d/%m/%Y")
    elif isinstance(thu_tu[0], str) and len(thu_tu) > 8:
        q1 = [k for k in thu_tu if str(k).endswith("Q1")]
        fig.update_xaxes(tickvals=q1, ticktext=[k[:4] for k in q1], tickangle=0)
    return fig


def bump(xh, noi_bat, cao=400):
    """Thứ hạng qua các năm (1 ở trên). Ngân hàng nổi bật có màu, số hạng trong chấm; còn lại xám."""
    fig = go.Figure()
    nam_cuoi = xh["nam"].max()
    for ma in sorted(cf.DS_NGAN_HANG, key=lambda m: m in noi_bat):
        s = xh[xh["ma_nh"] == ma].sort_values("nam")
        if s.empty:
            continue
        sang = ma in noi_bat
        mau = cf.MAU_NGAN_HANG[ma] if sang else XAM
        fig.add_trace(go.Scatter(
            x=s["nam"], y=s["hang"], mode="lines+markers+text" if sang else "lines+markers", name=ma,
            line=dict(color=mau, width=3 if sang else 1.4),
            marker=dict(size=22 if sang else 7, color=mau, line=dict(color=MAU["giay"], width=2)),
            text=s["hang"], textfont=dict(color="#FFFFFF", size=11, family=SANS),
            customdata=s["gia_tri"],
            hovertemplate=f"<b>{ma}</b> %{{x}}: hạng %{{y}} · %{{customdata:,.2f}}%<extra></extra>"))
        cuoi = s[s["nam"] == nam_cuoi]
        if len(cuoi):
            fig.add_annotation(x=nam_cuoi, y=int(cuoi["hang"].iloc[0]), text=f"<b>{ma}</b>" if sang else ma,
                               showarrow=False, xanchor="left", xshift=18 if sang else 10,
                               font=dict(size=12.5, color=MAU["muc"] if sang else MAU["nhat"]))
    n = xh["ma_nh"].nunique()
    nen(fig, cao, hover="closest", phai=60)
    fig.update_yaxes(autorange=False, range=[n + 0.6, 0.25], tickvals=list(range(1, n + 1)), showgrid=False,
                     ticktext=[f"#{i}" for i in range(1, n + 1)])
    fig.update_xaxes(dtick=1, showline=False, ticks="")
    return fig


def dai_nganh(b4, ma, chi_so, ds_ky, ky_chon=None, cao=170):
    """Hình nhỏ: dải xám = khoảng 8 ngân hàng (thấp nhất–cao nhất), chấm = trung vị, đường màu = ngân hàng chọn."""
    p = b4.pivot_table(index="ky", columns="ma_nh", values=chi_so).reindex(ds_ky)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ds_ky, y=p.max(axis=1), mode="lines", line=dict(width=0), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=ds_ky, y=p.min(axis=1), mode="lines", line=dict(width=0), fill="tonexty",
                             fillcolor="rgba(201,194,180,0.38)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=ds_ky, y=p.median(axis=1), mode="lines", line=dict(color=MAU["nhat"], width=1, dash="dot"),
                             hovertemplate="Trung vị: %{y:,.2f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=ds_ky, y=p[ma], mode="lines", line=dict(color=cf.MAU_NGAN_HANG[ma], width=2.2),
                             hovertemplate=f"<b>{ma}</b> %{{x}}: %{{y:,.2f}}%<extra></extra>"))
    k = ky_chon or ds_ky[-1]
    fig.add_trace(go.Scatter(x=[k], y=[p.loc[k, ma]], mode="markers", hoverinfo="skip",
                             marker=dict(size=7, color=cf.MAU_NGAN_HANG[ma], line=dict(color=MAU["giay"], width=1.5))))
    nen(fig, cao, hover="closest")
    q1 = [x for x in ds_ky if x.endswith("Q1")]
    fig.update_xaxes(tickvals=q1, ticktext=[x[:4] for x in q1], tickfont=dict(size=11))
    fig.update_yaxes(ticksuffix="%", tickfont=dict(size=11), nticks=4)
    return fig


def gia_su_kien(gia, sk, ma, cao=360):
    """Giá điều chỉnh của 1 ngân hàng + chấm đánh dấu ngày có tin doanh nghiệp (rê chuột đọc tiêu đề)."""
    g = gia[gia["ma_nh"] == ma].sort_values("ngay")
    s = sk[sk["ma_nh"] == ma].copy()
    s["ngay_phien"] = s["ngay_cong_bo"].dt.normalize()
    s = pd.merge_asof(s.sort_values("ngay_phien"), g[["ngay", "gia_dong_cua_dieu_chinh"]].rename(columns={"ngay": "ngay_phien"}),
                      on="ngay_phien", direction="backward").dropna(subset=["gia_dong_cua_dieu_chinh"])
    s["tieu"] = s["mo_ta_ngan"].fillna("").str.slice(0, 110)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g["ngay"], y=g["gia_dong_cua_dieu_chinh"], mode="lines",
                             line=dict(color=cf.MAU_NGAN_HANG[ma], width=1.8),
                             hovertemplate="%{x|%d/%m/%Y}: %{y:,.2f} nghìn đ<extra></extra>"))
    fig.add_trace(go.Scatter(x=s["ngay_phien"], y=s["gia_dong_cua_dieu_chinh"], mode="markers",
                             marker=dict(size=9, color=MAU["muc"], symbol="circle", line=dict(color=MAU["giay"], width=2)),
                             customdata=np.c_[s["loai_su_kien_nhan"], s["tieu"]],
                             hovertemplate="<b>%{customdata[0]}</b> · %{x|%d/%m/%Y}<br>%{customdata[1]}<extra></extra>"))
    nen(fig, cao, hover="closest")
    fig.update_xaxes(tickformat="%m/%Y")
    return fig


# ============================================================================
# So sánh nhóm, tương quan
# ============================================================================
def tuong_quan(tq, cao=280):
    """Chấm hệ số tương quan Spearman trên thang −1..1, dải xám = liên hệ yếu (|ρ| < 0,3)."""
    d = tq.sort_values("spearman_rho")
    fig = go.Figure()
    fig.add_vrect(x0=-0.3, x1=0.3, fillcolor="rgba(201,194,180,0.30)", line_width=0, layer="below")
    fig.add_vline(x=0, line=dict(color=MAU["muc2"], width=1))
    from web.mo_hinh import TEN_BIEN
    fig.add_trace(go.Scatter(x=d["spearman_rho"], y=d["chi_so"].map(TEN_BIEN), mode="markers+text",
                             marker=dict(size=12, color=MAU["muc"], line=dict(color=MAU["giay"], width=2)),
                             text=[so(v, 2, "", dau=True) for v in d["spearman_rho"]], textposition="middle right",
                             textfont=dict(size=11.5, color=MAU["muc2"]),
                             hovertemplate="%{y}: ρ = %{x:,.3f}<extra></extra>"))
    for x, chu in [(-0.65, "ngược chiều rõ"), (0, "gần như không liên hệ"), (0.65, "cùng chiều rõ")]:
        fig.add_annotation(x=x, y=1.0, yref="paper", yanchor="bottom", text=chu, showarrow=False,
                           font=dict(size=11, color=MAU["nhat"]))
    nen(fig, cao, hover="closest", tren=28)
    fig.update_xaxes(range=[-1, 1], dtick=0.5, showline=False, ticks="", showgrid=True, gridcolor=MAU["luoi"])
    fig.update_yaxes(showgrid=False)
    return fig


# ============================================================================
# Dự báo
# ============================================================================
def xac_suat(df, cao=330):
    """Que kẹo: từ mốc 50% đến xác suất dự báo của từng ngân hàng (đậm: nghiêng về tăng)."""
    d = df.sort_values("xac_suat")
    fig = go.Figure()
    for r in d.itertuples():
        tang = r.xac_suat >= 0.5
        fig.add_trace(go.Scatter(x=[0.5, r.xac_suat], y=[r.ma_nh, r.ma_nh], mode="lines", hoverinfo="skip",
                                 line=dict(color=MAU["muc"] if tang else XAM, width=2.5)))
        fig.add_trace(go.Scatter(x=[r.xac_suat], y=[r.ma_nh], mode="markers+text", text=[f"{r.xac_suat:.0%}"],
                                 textposition="middle right" if tang else "middle left",
                                 textfont=dict(size=12, color=MAU["muc"] if tang else MAU["nhat"]),
                                 marker=dict(size=13, color=cf.MAU_NGAN_HANG[r.ma_nh], line=dict(color=MAU["giay"], width=2)),
                                 hovertemplate=f"{cf.TEN_DAY_DU[r.ma_nh]}: {r.xac_suat:.0%}<extra></extra>"))
    fig.add_vline(x=0.5, line=dict(color=MAU["muc2"], width=1))
    fig.add_annotation(x=0.5, y=1.0, yref="paper", yanchor="bottom", text="50% – không nghiêng bên nào", showarrow=False,
                       font=dict(size=11, color=MAU["nhat"]))
    nen(fig, cao, hover="closest", tren=28)
    fig.update_xaxes(range=[0.2, 0.8], tickformat=".0%", showgrid=True, gridcolor=MAU["luoi"], showline=False, ticks="")
    fig.update_yaxes(showgrid=False)
    return fig


def dong_gop(dg, cao=300):
    d = dg[(dg["dong_gop"].abs() > 1e-9) | dg["bien"].isin(["roa", "roe", "nim", "npl", "car", "ldr"])].sort_values("dong_gop")
    fig = go.Figure(go.Bar(
        x=d["dong_gop"], y=d["ten"], orientation="h",
        marker_color=np.where(d["dong_gop"] > 0, MAU["muc"], MAU["nen_xam"]),
        customdata=d["gia_tri"], hovertemplate="%{y} = %{customdata:,.2f} · tác động %{x:+,.2f}<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=MAU["muc2"], width=1))
    lim = max(0.3, d["dong_gop"].abs().max() * 1.15)
    fig.add_annotation(x=-lim, y=1.0, yref="paper", yanchor="bottom", xanchor="left", text="← kéo về “không tăng”",
                       showarrow=False, font=dict(size=11, color=MAU["nhat"]))
    fig.add_annotation(x=lim, y=1.0, yref="paper", yanchor="bottom", xanchor="right", text="kéo về “tăng” →",
                       showarrow=False, font=dict(size=11, color=MAU["nhat"]))
    nen(fig, cao, hover="closest", tren=28)
    fig.update_xaxes(range=[-lim, lim], showgrid=True, gridcolor=MAU["luoi"], showline=False, ticks="")
    fig.update_yaxes(showgrid=False)
    return fig


def lich_su_tin_hieu(ls, ma, nam_test, nhan, cao=280):
    fig = go.Figure()
    test = [k for k in ls["ky"] if int(k[:4]) >= nam_test]
    if test:
        fig.add_vrect(x0=test[0], x1=test[-1], fillcolor="rgba(201,194,180,0.30)", line_width=0, layer="below")
        fig.add_annotation(x=test[0], y=1.0, yref="paper", yanchor="bottom", xanchor="left", showarrow=False,
                           text=f"năm kiểm chứng {nam_test}", font=dict(size=11, color=MAU["nhat"]))
    fig.add_hline(y=0.5, line=dict(color=MAU["muc2"], width=1))
    fig.add_trace(go.Scatter(x=ls["ky"], y=ls["p"], mode="lines", line=dict(color=cf.MAU_NGAN_HANG[ma], width=2),
                             hovertemplate="%{x}: %{y:.0%}<extra></extra>"))
    co = ls.dropna(subset=[nhan])
    dung = (co["p"] >= 0.5) == (co[nhan] == 1)
    fig.add_trace(go.Scatter(x=co["ky"], y=co["p"], mode="markers",
                             marker=dict(size=9, symbol=np.where(dung, "circle", "x-thin-open"),
                                         color=np.where(dung, MAU["tang"], MAU["giam"]),
                                         line=dict(color=np.where(dung, MAU["giay"], MAU["giam"]), width=2)),
                             customdata=np.c_[np.where(co[nhan] == 1, "tăng", "không tăng"), co["ty_suat_sinh_loi_quy_sau"]],
                             hovertemplate="%{x}: dự báo %{y:.0%} · thực tế %{customdata[0]} (%{customdata[1]:+,.1f}%)<extra></extra>"))
    nen(fig, cao, hover="closest", tren=26)
    q1 = [k for k in ls["ky"] if k.endswith("Q1")]
    fig.update_xaxes(tickvals=q1, ticktext=[k[:4] for k in q1])
    fig.update_yaxes(range=[0, 1], tickformat=".0%", dtick=0.25)
    return fig


def so_sanh_mo_hinh(dg, cao=230):
    d = dg.iloc[::-1]
    fig = go.Figure()
    fig.add_vline(x=0.5, line=dict(color=MAU["muc2"], width=1))
    for chi_tieu, mau, ky_hieu in [("Accuracy", MAU["nen_xam"], "circle"), ("ROC-AUC", MAU["muc"], "diamond")]:
        fig.add_trace(go.Scatter(x=d[chi_tieu], y=d["ten"], mode="markers", name="Tỷ lệ đúng" if chi_tieu == "Accuracy" else "AUC",
                                 marker=dict(size=13, color=mau, symbol=ky_hieu, line=dict(color=MAU["giay"], width=2)),
                                 hovertemplate="%{y}: %{x:,.3f}<extra>" + chi_tieu + "</extra>"))
    nen(fig, cao, hover="closest", chu_giai=True)
    fig.update_xaxes(range=[0.4, 0.75], showgrid=True, gridcolor=MAU["luoi"], showline=False, ticks="")
    fig.update_yaxes(showgrid=False)
    return fig


# ============================================================================
# Phân nhóm
# ============================================================================
def ban_do(pn, noi_bat=None, cao=480):
    d = pn["du_lieu"]
    fig = go.Figure()
    for nhom in sorted(d["nhom"].unique()):
        s = d[d["nhom"] == nhom]
        fig.add_trace(go.Scatter(x=s["PC1"], y=s["PC2"], mode="markers", name=f"Nhóm {nhom}: {s['ten_nhom'].iloc[0]}",
                                 marker=dict(size=9, color=MAU_NHOM[nhom], opacity=0.55, line=dict(color=MAU["giay"], width=1)),
                                 customdata=np.c_[s["ma_nh"], s["ky"]],
                                 hovertemplate="%{customdata[0]} %{customdata[1]}<extra></extra>"))
    tam = d.groupby("ma_nh")[["PC1", "PC2"]].mean().sort_values("PC2", ascending=False)
    khoang_y = (d["PC2"].max() - d["PC2"].min()) * 0.05
    khoang_x = (d["PC1"].max() - d["PC1"].min()) * 0.08
    da_dat = []
    for ma, r in tam.iterrows():          # đẩy nhãn xuống nếu trùng chỗ nhãn đã đặt
        y = r["PC2"]
        while any(abs(r["PC1"] - x0) < khoang_x and abs(y - y0) < khoang_y for x0, y0 in da_dat):
            y -= khoang_y * 0.6
        da_dat.append((r["PC1"], y))
        tam.loc[ma, "PC2"] = y
    for ma, r in tam.iterrows():
        fig.add_annotation(x=r["PC1"], y=r["PC2"], text=f"<b>{ma}</b>", showarrow=False,
                           font=dict(size=12.5, color=MAU["muc"]), bgcolor="rgba(244,241,234,0.85)", borderpad=2)
    if noi_bat:
        s = d[d["ma_nh"] == noi_bat].sort_values("ky_so")
        fig.add_trace(go.Scatter(x=s["PC1"], y=s["PC2"], mode="lines+markers", name=f"Hành trình {noi_bat}",
                                 line=dict(color=cf.MAU_NGAN_HANG[noi_bat], width=1.6),
                                 marker=dict(size=6, color=cf.MAU_NGAN_HANG[noi_bat]), text=s["ky"],
                                 hovertemplate="%{text}<extra>" + noi_bat + "</extra>"))
    nen(fig, cao, hover="closest", chu_giai=True)
    fig.update_xaxes(showgrid=True, gridcolor=MAU["luoi"], showline=False, ticks="", zeroline=False)
    return fig


def luoi_nhom(d, ds_ky, cao=290):
    b = d.pivot(index="ma_nh", columns="ky", values="nhom").reindex(index=cf.DS_NGAN_HANG, columns=ds_ky)
    nhom = sorted(d["nhom"].unique())
    z = b.apply(lambda c: c.map({n: i for i, n in enumerate(nhom)}))
    fig = go.Figure(go.Heatmap(
        z=z.values, x=ds_ky, y=b.index, text=b.values, zmin=0, zmax=max(1, len(nhom) - 1), showscale=False,
        colorscale=[[i / max(1, len(nhom) - 1), MAU_NHOM[n]] for i, n in enumerate(nhom)], xgap=2, ygap=2,
        hovertemplate="%{y} %{x}: nhóm %{text}<extra></extra>"))
    nen(fig, cao, hover="closest")
    q1 = [k for k in ds_ky if k.endswith("Q1")]
    fig.update_xaxes(tickvals=q1, ticktext=[k[:4] for k in q1], showline=False, ticks="")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return fig


def lech_nhom(z, cao=260):
    from web.mo_hinh import TEN_BIEN
    fig = go.Figure()
    for nhom, r in z.iterrows():
        fig.add_trace(go.Bar(y=[TEN_BIEN[b] for b in r.index], x=r.values, orientation="h", name=f"Nhóm {nhom}",
                             marker_color=MAU_NHOM[nhom], hovertemplate="%{y}: %{x:+,.2f} độ lệch chuẩn<extra>Nhóm " + nhom + "</extra>"))
    fig.add_vline(x=0, line=dict(color=MAU["muc2"], width=1))
    nen(fig, cao, hover="closest", chu_giai=True)
    fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.1)
    fig.update_xaxes(showgrid=True, gridcolor=MAU["luoi"], showline=False, ticks="")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return fig


def duong_nho(x, y, ten_y, cao=200, mau=None):
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines+markers", line=dict(color=mau or MAU["muc"], width=2),
                               marker=dict(size=7), hovertemplate="K = %{x}: %{y:,.3f}<extra></extra>"))
    nen(fig, cao, hover="closest")
    fig.update_xaxes(dtick=1)
    fig.add_annotation(x=0, y=1.0, xref="paper", yref="paper", yanchor="bottom", xanchor="left", text=ten_y,
                       showarrow=False, font=dict(size=11.5, color=MAU["muc2"]))
    return fig
