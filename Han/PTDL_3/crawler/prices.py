"""Bảng 2 – Giá cổ phiếu theo ngày và tổng hợp theo quý (nguồn: API công khai dstock/VNDirect).

Lưu ý quan trọng về giá điều chỉnh:
  Các ngân hàng trả cổ tức bằng cổ phiếu / phát hành thêm gần như hằng năm, khiến giá
  chưa điều chỉnh bị "rơi" tại ngày GDKHQ. Vì vậy tỷ suất sinh lời quý được tính trên
  GIÁ ĐIỀU CHỈNH (adClose). Giá chưa điều chỉnh vẫn được giữ lại để đối chiếu.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import config
from .http_client import HttpClient

log = logging.getLogger(__name__)


def fetch_daily(client: HttpClient, code: str) -> pd.DataFrame:
    q = f"code:{code}~date:gte:{config.PRICE_FROM}~date:lte:{config.PRICE_TO}"
    rows = client.vnd_paged("stock_prices", q, namespace="vnd_stock_prices",
                            key=f"{code}_{config.PRICE_FROM}_{config.PRICE_TO}", sort="date")
    df = pd.DataFrame(rows)
    if df.empty:
        log.warning("Không có dữ liệu giá cho %s", code)
        return df
    df = df.drop_duplicates(["code", "date"], keep="last")
    out = pd.DataFrame({
        "ma_nh": df["code"],
        "ngay": pd.to_datetime(df["date"]),
        "gia_dong_cua": df["close"],                        # nghìn đồng, chưa điều chỉnh
        "gia_dong_cua_dieu_chinh": df["adClose"],
        "gia_mo_cua_dieu_chinh": df["adOpen"],
        "gia_cao_nhat_dieu_chinh": df["adHigh"],
        "gia_thap_nhat_dieu_chinh": df["adLow"],
        "khoi_luong_gd": df["nmVolume"],                    # khớp lệnh (không gồm thỏa thuận)
        "khoi_luong_thoa_thuan": df.get("ptVolume"),
        "gia_tri_gd_ty": df["nmValue"] / 1e9,
    })
    return out.sort_values("ngay").reset_index(drop=True)


def price_on_or_before(daily: pd.DataFrame, codes: pd.Series, dates: pd.Series) -> pd.Series:
    """Giá đóng cửa điều chỉnh của phiên cuối cùng <= ngày cho trước, theo từng mã.
    Trả NaN nếu ngày đó vượt quá dữ liệu giá đã có (chưa biết giá thì không tạo nhãn)."""
    q = pd.DataFrame({"ma_nh": codes.values, "_d": pd.to_datetime(dates.values), "_i": range(len(codes))})
    px = daily[["ma_nh", "ngay", "gia_dong_cua_dieu_chinh"]].sort_values("ngay")
    out = pd.merge_asof(q.sort_values("_d"), px, left_on="_d", right_on="ngay",
                        by="ma_nh", direction="backward")
    last = px.groupby("ma_nh")["ngay"].max()
    out.loc[out["_d"] > out["ma_nh"].map(last), "gia_dong_cua_dieu_chinh"] = np.nan
    return pd.Series(out.sort_values("_i")["gia_dong_cua_dieu_chinh"].values, index=codes.index)


def aggregate_quarterly(daily: pd.DataFrame) -> pd.DataFrame:
    d = daily.copy()
    d["period"] = d["ngay"].dt.to_period("Q")
    agg = d.groupby(["ma_nh", "period"]).agg(
        ngay_dau=("ngay", "min"),
        ngay_cuoi=("ngay", "max"),
        gia_cuoi_quy=("gia_dong_cua_dieu_chinh", "last"),
        gia_cuoi_quy_chua_dieu_chinh=("gia_dong_cua", "last"),
        gia_max=("gia_cao_nhat_dieu_chinh", "max"),
        gia_min=("gia_thap_nhat_dieu_chinh", "min"),
        so_phien_gd=("ngay", "count"),
        kl_gd_tb_phien=("khoi_luong_gd", "mean"),
        tong_kl_gd_quy=("khoi_luong_gd", "sum"),
    ).reset_index()

    # Giá đầu quý = giá đóng cửa (điều chỉnh) phiên cuối cùng của quý TRƯỚC.
    # Tra theo Period (không dùng shift) để không bị lệch khi thiếu một quý.
    prev = agg[["ma_nh", "period", "gia_cuoi_quy"]].copy()
    prev["period"] = prev["period"] + 1
    agg = agg.merge(prev.rename(columns={"gia_cuoi_quy": "gia_dau_quy"}),
                    on=["ma_nh", "period"], how="left")

    agg["ty_suat_sinh_loi_quy"] = (agg["gia_cuoi_quy"] / agg["gia_dau_quy"] - 1) * 100
    agg["bien_dong_gia_max_min"] = (agg["gia_max"] - agg["gia_min"]) / agg["gia_min"] * 100

    # Biến mục tiêu cho Logistic Regression, "đóng vai người ở quá khứ":
    # lợi suất từ MỐC DỰ BÁO của quý t (cuối quý + LABEL_LAG_DAYS, khi BCTC quý t đã công bố)
    # đến mốc dự báo của quý t+1. Không tính từ cuối quý vì khi đó BCTC quý t chưa ai biết.
    lag = pd.Timedelta(days=config.LABEL_LAG_DAYS)
    agg["_moc"] = agg["period"].dt.end_time.dt.normalize() + lag
    agg["_moc_sau"] = (agg["period"] + 1).dt.end_time.dt.normalize() + lag
    agg["_p0"] = price_on_or_before(daily, agg["ma_nh"], agg["_moc"])
    agg["_p1"] = price_on_or_before(daily, agg["ma_nh"], agg["_moc_sau"])
    agg["ty_suat_sinh_loi_quy_sau"] = (agg["_p1"] / agg["_p0"] - 1) * 100
    agg["xu_huong_quy_sau"] = np.where(agg["ty_suat_sinh_loi_quy_sau"].isna(), np.nan,
                                       (agg["ty_suat_sinh_loi_quy_sau"] > 0).astype(float))

    agg["quy"] = "Q" + agg["period"].dt.quarter.astype(str)
    agg["nam"] = agg["period"].dt.year
    agg = agg[agg["nam"].between(config.START_YEAR, config.END_YEAR)]
    cols = ["ma_nh", "quy", "nam", "ngay_dau", "ngay_cuoi", "so_phien_gd",
            "gia_dau_quy", "gia_cuoi_quy", "gia_cuoi_quy_chua_dieu_chinh",
            "ty_suat_sinh_loi_quy", "bien_dong_gia_max_min", "gia_max", "gia_min",
            "kl_gd_tb_phien", "tong_kl_gd_quy",
            "ty_suat_sinh_loi_quy_sau", "xu_huong_quy_sau"]
    return agg[cols].sort_values(["ma_nh", "nam", "quy"]).reset_index(drop=True)


def build_bang2(client: HttpClient) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    for code in config.BANKS:
        log.info("[Bảng 2] Giá cổ phiếu %s", code)
        frames.append(fetch_daily(client, code))
    daily = pd.concat(frames, ignore_index=True)
    quarterly = aggregate_quarterly(daily)
    # Giữ MỌI phiên đã dùng để tính các cột giá quý, để kiểm tra lại được: gồm tháng 12/2020
    # (giá đầu quý Q1/2021) và các phiên đầu năm sau (chỉ dùng để tính nhãn quý sau).
    daily_out = daily[daily["ngay"].between(config.PRICE_FROM, config.PRICE_TO)].copy()
    daily_out["ngay"] = daily_out["ngay"].dt.strftime("%Y-%m-%d")
    return daily_out.reset_index(drop=True), quarterly
