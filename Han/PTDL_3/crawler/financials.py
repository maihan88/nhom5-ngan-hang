"""Bảng 1 – Dữ liệu tài chính theo quý (nguồn: API công khai dstock/VNDirect).

- Số liệu gốc (tổng tài sản, VCSH, LNST, dư nợ, thu nhập lãi thuần...) lấy từ BCTC quý
  theo mẫu ngân hàng (TT49/2014/TT-NHNN), đơn vị gốc VND -> quy đổi sang tỷ đồng.
- ROA, ROE, NIM: nhóm TỰ TÍNH từ số liệu gốc (công thức minh bạch, ghi trong Data Dictionary).
- NPL: BCTC không có bảng phân loại nợ ở dạng cấu trúc, nên lấy chỉ số VNDirect đã tổng hợp từ thuyết minh BCTC.
- CAR (1 số/năm, 31/12): ưu tiên số hợp nhất trong báo cáo tỷ lệ an toàn vốn của ngân hàng (car_reports.py),
  thiếu thì dùng số VNDirect; các quý khác điền tiếp.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import car_reports, config
from .http_client import HttpClient

log = logging.getLogger(__name__)

QUARTER_END = {"03-31": "Q1", "06-30": "Q2", "09-30": "Q3", "12-31": "Q4"}


def quarter_end_dates(start: str, end: str) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in pd.date_range(start, end, freq="QE")]


def _add_quarter_keys(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    md = df[date_col].str[5:10]
    df = df[md.isin(QUARTER_END)].copy()
    df["quy"] = df[date_col].str[5:10].map(QUARTER_END)
    df["nam"] = df[date_col].str[:4].astype(int)
    return df


# ---------------------------------------------------------------------------
def fetch_statements(client: HttpClient, code: str, report_type: str = "QUARTER",
                     model_types: str = "101,102") -> pd.DataFrame:
    if report_type == "QUARTER":
        dates = quarter_end_dates(config.FIN_FROM, config.FIN_TO)
    else:
        dates = [f"{y}-12-31" for y in range(config.START_YEAR, config.END_YEAR + 1)]
    q = (f"code:{code}~reportType:{report_type}~modelType:{model_types}"
         f"~fiscalDate:{','.join(dates)}")
    rows = client.vnd_paged("financial_statements", q, namespace="vnd_financial_statements",
                            key=f"{code}_{report_type}_{model_types}{config.CACHE_TAG}")
    df = pd.DataFrame(rows)
    if df.empty:
        log.warning("Không có BCTC %s cho %s", report_type, code)
        return df
    df["itemCode"] = df["itemCode"].astype(int)
    df["modelType"] = df["modelType"].astype(int)
    # Nếu một chỉ tiêu bị cập nhật (BCTC điều chỉnh/kiểm toán lại) -> giữ bản sửa sau cùng
    df = (df.sort_values("modifiedDate")
            .drop_duplicates(["code", "fiscalDate", "modelType", "itemCode"], keep="last"))
    return df


def _pivot_items(df: pd.DataFrame) -> pd.DataFrame:
    wanted = {**{(101, k): v for k, v in config.BS_ITEMS.items()},
              **{(102, k): v for k, v in config.IS_ITEMS.items()}}
    df = df[[(m, i) in wanted for m, i in zip(df["modelType"], df["itemCode"])]].copy()
    df["col"] = [wanted[(m, i)] for m, i in zip(df["modelType"], df["itemCode"])]
    wide = df.pivot_table(index=["code", "fiscalDate"], columns="col",
                          values="numericValue", aggfunc="last").reset_index()
    for col in list(config.BS_ITEMS.values()) + list(config.IS_ITEMS.values()):
        if col not in wide:
            wide[col] = np.nan
    return wide


def fetch_ratios(client: HttpClient, code: str) -> pd.DataFrame:
    q = (f"code:{code}~ratioCode:{','.join(config.RATIO_CODES)}"
         f"~reportDate:gte:{config.FIN_FROM}~reportDate:lte:{config.FIN_TO}")
    rows = client.vnd_paged("ratios", q, namespace="vnd_ratios", key=f"{code}_bank_ratios{config.CACHE_TAG}",
                            sort="reportDate:asc")
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["code", "fiscalDate", *config.RATIO_CODES.values()])
    df = df[df["reportDate"].str[5:10].isin(QUARTER_END)]
    wide = df.pivot_table(index=["code", "reportDate"], columns="ratioCode",
                          values="value", aggfunc="last").reset_index()
    wide = wide.rename(columns={"reportDate": "fiscalDate", **config.RATIO_CODES})
    for col in config.RATIO_CODES.values():
        if col not in wide:
            wide[col] = np.nan
    return wide


# ---------------------------------------------------------------------------
def _avg_with_prev(s: pd.Series) -> pd.Series:
    """Bình quân số dư đầu kỳ & cuối kỳ (đầu kỳ = cuối quý trước)."""
    return pd.concat([s, s.shift(1)], axis=1).mean(axis=1, skipna=True)


def _apply_car_bao_cao(df: pd.DataFrame, car_bc: pd.DataFrame | None) -> pd.DataFrame:
    """Thay CAR quý 4 bằng số trong báo cáo tỷ lệ an toàn vốn 31/12 của ngân hàng (tự đọc hoặc nhập tay).

    Thứ tự ưu tiên: báo cáo ngân hàng > VNDirect > điền tiếp. Năm chưa có số báo cáo thì giữ số VNDirect (nếu có).
    Lý do: VNDirect từng ghi sai (8,00 cho BID, CTG 2022–2024; 10,02 cho MBB 2021) và không cập nhật từ 2025.
    """
    if car_bc is None or car_bc.empty:
        return df
    co_so = car_bc.dropna(subset=["car"])[["ma_nh", "nam", "car"]].rename(columns={"car": "_car_bc"})
    df = df.merge(co_so.assign(quy="Q4"), on=["ma_nh", "nam", "quy"], how="left")
    hit = df["_car_bc"].notna()
    df.loc[hit, "car"] = df.loc[hit, "_car_bc"]
    df.loc[hit, "car_nguon"] = "bao_cao_ngan_hang"
    return df.drop(columns="_car_bc")


def compute_indicators(df: pd.DataFrame, car_bc: pd.DataFrame | None = None) -> pd.DataFrame:
    df = df.sort_values(["ma_nh", "nam", "quy"]).copy()
    g = df.groupby("ma_nh", group_keys=False)

    df["tai_san_sinh_lai"] = df[config.EARNING_ASSET_COLS].sum(axis=1, min_count=3)
    df["_ta_avg"] = g["tong_tai_san"].apply(_avg_with_prev)
    df["_eq_avg"] = g["von_chu_so_huu"].apply(_avg_with_prev)
    df["_ea_avg"] = g["tai_san_sinh_lai"].apply(_avg_with_prev)

    # Chỉ số năm hóa (x4) từ số liệu quý, đơn vị %
    df["roa"] = df["loi_nhuan_sau_thue"] * 4 / df["_ta_avg"] * 100
    df["roe"] = df["loi_nhuan_sau_thue"] * 4 / df["_eq_avg"] * 100
    df["nim"] = df["thu_nhap_lai_thuan"] * 4 / df["_ea_avg"] * 100
    df["ldr"] = df["tong_du_no"] / df["tien_gui_khach_hang"] * 100

    # NPL, CAR từ VNDirect (dạng thập phân -> %)
    for col in ["npl", "car", "nim_ttm_vnd", "roa_ttm_vnd", "roe_ttm_vnd"]:
        df[col] = df[col] * 100

    # CAR: chỉ lấy số 31/12 (1 số/năm); quý khác điền tiếp giá trị gần nhất ĐÃ có
    # (không dùng giá trị tương lai để tránh rò rỉ thông tin cho mô hình dự báo)
    df["car_vnd"] = df["car"]  # giữ số VNDirect để đối chiếu trong báo cáo kiểm tra
    df["car_nguon"] = np.where(df["car"].notna(), "vndirect", None)
    df = _apply_car_bao_cao(df, car_bc)  # TRƯỚC khi điền tiếp
    df["car"] = df.groupby("ma_nh")["car"].ffill()
    df.loc[df["car_nguon"].isna() & df["car"].notna(), "car_nguon"] = "dien_tiep_ky_truoc"

    return df.drop(columns=["_ta_avg", "_eq_avg", "_ea_avg"])


# Đối chiếu với số VNDirect công bố: chỉ số -> (tử số, mẫu số, cột VNDirect). Số VNDirect là số 4 quý gần nhất
# (tổng 4 quý / bình quân 5 thời điểm cuối quý), nên tính lại theo đúng cách đó rồi mới so.
DOI_CHIEU_VND = {
    "roa": ("loi_nhuan_sau_thue", "tong_tai_san", "roa_ttm_vnd"),
    "roe": ("loi_nhuan_sau_thue", "von_chu_so_huu", "roe_ttm_vnd"),
    "nim": ("thu_nhap_lai_thuan", "tai_san_sinh_lai", "nim_ttm_vnd"),
}


def _doi_chieu_vnd(df: pd.DataFrame) -> pd.DataFrame:
    """ROA, ROE, NIM tính lại theo cách 4 quý gần nhất cạnh số VNDirect – chỉ cho báo cáo kiểm tra."""
    df = df.sort_values(["ma_nh", "nam", "quy"])
    g = df.groupby("ma_nh")
    out = df[["ma_nh", "quy", "nam"]].copy()
    for cs, (tu, mau, vnd) in DOI_CHIEU_VND.items():
        tong_4_quy = g[tu].transform(lambda s: s.rolling(4).sum())
        bq_5_diem = g[mau].transform(lambda s: s.rolling(5).mean())
        out[f"{cs}_ttm_tu_tinh"] = tong_4_quy / bq_5_diem * 100
        out[f"{cs}_ttm_vnd"] = df[vnd]
    return out


def build_bang1(client: HttpClient) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Trả về (bang1, annual_check, ngay_nhap_bctc, doi_chieu_vnd, car_bao_cao) – bốn bảng sau chỉ dùng cho
    báo cáo kiểm tra."""
    frames, annual_frames, entry_frames = [], [], []
    for code in config.BANKS:
        log.info("[Bảng 1] BCTC quý %s", code)
        st = fetch_statements(client, code)
        if st.empty:
            continue
        # Ngày VNDirect nhập BCTC lần đầu ~ ngày thị trường biết số liệu (kiểm tra mốc dự báo)
        entry_frames.append(st.groupby(["code", "fiscalDate"], as_index=False)["createdDate"].min())
        wide = _pivot_items(st)
        ratios = fetch_ratios(client, code)
        wide = wide.merge(ratios, on=["code", "fiscalDate"], how="left")
        frames.append(wide)

        an = fetch_statements(client, code, report_type="ANNUAL", model_types="102")
        if not an.empty:
            an = an[(an["modelType"] == 102) & (an["itemCode"] == 23003)]
            annual_frames.append(an[["code", "fiscalDate", "numericValue"]])

    df = pd.concat(frames, ignore_index=True)
    df = _add_quarter_keys(df, "fiscalDate").rename(columns={"code": "ma_nh", "fiscalDate": "ngay_bctc"})

    money_cols = list(config.BS_ITEMS.values()) + list(config.IS_ITEMS.values())
    df[money_cols] = df[money_cols] / 1e9  # VND -> tỷ đồng

    car_bc = car_reports.build_car_bao_cao(client)
    df = compute_indicators(df, car_bc)
    q4 = df[df["quy"] == "Q4"][["ma_nh", "nam", "car_vnd"]]
    car_bc = car_bc.merge(q4, on=["ma_nh", "nam"], how="left")
    df["loai_hinh_so_huu"] = df["ma_nh"].map(config.BANKS)
    doi_chieu = _doi_chieu_vnd(df)  # trước khi lọc năm: cần cả Q4/2020 cho bình quân 5 điểm
    doi_chieu = doi_chieu[doi_chieu["nam"].between(config.START_YEAR, config.END_YEAR)].reset_index(drop=True)
    df = df[df["nam"].between(config.START_YEAR, config.END_YEAR)]

    cols = ["ma_nh", "quy", "nam", "ngay_bctc", "loai_hinh_so_huu",
            "tong_tai_san", "von_chu_so_huu", "loi_nhuan_sau_thue", "tong_du_no",
            "roa", "roe", "nim", "npl", "car", "car_nguon", "ldr",
            "thu_nhap_lai_thuan", "tien_gui_khach_hang", "tai_san_sinh_lai"]
    bang1 = df[cols].sort_values(["ma_nh", "nam", "quy"]).reset_index(drop=True)

    annual = pd.concat(annual_frames, ignore_index=True) if annual_frames else pd.DataFrame()
    if not annual.empty:
        annual = annual.rename(columns={"code": "ma_nh", "numericValue": "lnst_nam_bctc"})
        annual["nam"] = annual["fiscalDate"].str[:4].astype(int)
        annual["lnst_nam_bctc"] = annual["lnst_nam_bctc"] / 1e9
        annual = annual[["ma_nh", "nam", "lnst_nam_bctc"]]

    entry = pd.concat(entry_frames, ignore_index=True)
    entry = _add_quarter_keys(entry, "fiscalDate").rename(columns={"code": "ma_nh"})
    entry["tre_ngay"] = (pd.to_datetime(entry["createdDate"]) - pd.to_datetime(entry["fiscalDate"])).dt.days
    entry = entry[entry["nam"].between(config.START_YEAR, config.END_YEAR)]
    return bang1, annual, entry[["ma_nh", "quy", "nam", "fiscalDate", "createdDate", "tre_ngay"]], doi_chieu, car_bc
