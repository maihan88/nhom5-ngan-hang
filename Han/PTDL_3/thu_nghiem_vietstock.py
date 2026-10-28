"""Chạy thử: Vietstock có thêm được sự kiện nào mà CafeF + VNDirect chưa có không?

KHÔNG thay đổi bộ dữ liệu bàn giao (data/output). Kết quả ghi vào data/interim/:
  - vietstock_thu_nghiem_tin.csv         : mọi tin Vietstock 2021–2025 và lý do giữ / bỏ
  - vietstock_thu_nghiem_su_kien_moi.csv : sự kiện CHỈ Vietstock có – cần đọc từng dòng (cột danh_gia)
  - vietstock_thu_nghiem_bao_cao.md      : thống kê tổng hợp

Mỗi tin Vietstock đi qua 3 cổng, trượt cổng nào thì dừng ở đó:
  1. Trùng tin đã có (CafeF/VNDirect/bổ sung tay) -> giữ quyết định cũ, không xét lại.
  2. Lọc giống CafeF: phải nhắc tên ngân hàng, qua bộ phân loại từ khóa, không phải tin ngành/sai mã.
  3. Gộp cùng quy tắc với pipeline: cùng NH + cùng loại + cách <= 3 ngày (tăng vốn: cùng quý)
     -> nếu rơi vào sự kiện đã có thì chỉ là "xác nhận", còn lập cụm riêng mới là "sự kiện mới".

Ví dụ:
    python thu_nghiem_vietstock.py            # lần đầu tải tin Vietstock (~10 phút); CafeF/VNDirect đọc cache
    python thu_nghiem_vietstock.py --offline  # chỉ dùng cache, không gửi request
"""
from __future__ import annotations

import argparse
import logging
import sys

import pandas as pd

from crawler import config, events, vietstock
from crawler.http_client import HttpClient

log = logging.getLogger("thu_nghiem_vietstock")

KET_QUA = {  # thứ tự hiển thị trong báo cáo
    "trung_tin_da_co": "Trùng tin đã có (giữ quyết định cũ)",
    "khong_nhac_ten_ngan_hang": "Tiêu đề không nhắc tới ngân hàng",
    "khong_phai_su_kien": "Tin thường quy / không thuộc nhóm nào",
    "tin_nganh_hoac_sai_ma": "Tin toàn ngành hoặc gắn nhầm mã",
    "trung_tieu_de_trong_ngay": "Trùng tiêu đề trong ngày",
    "xac_nhan_su_kien_da_co": "Gộp vào sự kiện đã có (xác nhận)",
    "su_kien_moi": "SỰ KIỆN MỚI",
}
CBTT_SOURCES = {"HOSE", "HNX", "UPCOM"}


def _decision(row) -> str:
    """Quyết định hiện tại của pipeline đối với một tin thô đã có."""
    if row["ra_soat_tay"] == "loai_bo":
        return "đã loại thủ công"
    if pd.isna(row["loai_su_kien"]):
        return "không phải sự kiện"
    if row["tin_nganh_hoac_sai_ma"] and row["ra_soat_tay"] not in ("sua_loai", "bo_sung"):
        return "tin ngành/sai mã"
    return f"sự kiện: {row['loai_su_kien']}"


def _cluster_links(ev: pd.DataFrame) -> list[list[str]]:
    return [[n] + [x for x in k.split(" ; ") if x] if isinstance(k, str) else [n]
            for n, k in zip(ev["nguon"], ev["nguon_khac"])]


def _md_table(df: pd.DataFrame) -> list[str]:
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v).replace("|", "/") for v in row) + " |"
              for row in df.itertuples(index=False)]
    return lines + [""]


def classify_vietstock(vs: pd.DataFrame, base_raw: pd.DataFrame) -> pd.DataFrame:
    """Cổng 1 + 2: gắn ket_qua cho các tin bị loại, loai_su_kien cho tin còn lại (ứng viên)."""
    vs = vs.join(vietstock.match_existing(vs, base_raw))
    decision = {i: _decision(r) for i, r in base_raw.iterrows()}
    near = vs["gan_nhat_idx"]
    vs["tin_gan_nhat_da_co"] = [
        "" if pd.isna(i) else
        f"{base_raw.at[int(i), 'ngay_cong_bo']:%Y-%m-%d %H:%M} | {decision[int(i)]} | {base_raw.at[int(i), 'tieu_de']}"
        for i in near]
    dup = vs["quy_tac"] != ""
    vs["quyet_dinh_tin_trung"] = [decision[int(i)] if d else "" for i, d in zip(near, dup)]

    # Phân loại theo tiêu đề Vietstock (cả tin trùng, chỉ để phát hiện bản CafeF bị bỏ sót – không dùng để đếm)
    vs["phan_loai_tieu_de"] = vs["tieu_de"].map(events.classify)
    mentions = pd.Series([c in events.banks_mentioned(t) for c, t in zip(vs["ma_nh"], vs["tieu_de"])],
                         index=vs.index)
    off = pd.Series([events.is_off_target(c, t) for c, t in zip(vs["ma_nh"], vs["tieu_de"])], index=vs.index)

    vs["ket_qua"] = "ung_vien"
    vs.loc[~dup & ~mentions, "ket_qua"] = "khong_nhac_ten_ngan_hang"
    vs.loc[~dup & mentions & vs["phan_loai_tieu_de"].isna(), "ket_qua"] = "khong_phai_su_kien"
    vs.loc[~dup & mentions & vs["phan_loai_tieu_de"].notna() & off, "ket_qua"] = "tin_nganh_hoac_sai_ma"
    vs.loc[dup, "ket_qua"] = "trung_tin_da_co"
    vs["loai_su_kien"] = vs["phan_loai_tieu_de"].where(vs["ket_qua"] == "ung_vien")
    return vs


def merge_with_existing(vs: pd.DataFrame, base_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cổng 3: đưa ứng viên vào cùng bước gộp của pipeline. Trả về (vs đã gắn ket_qua, sự kiện gộp chung)."""
    cand = vs[vs["ket_qua"] == "ung_vien"].assign(ra_soat_tay="", tin_nganh_hoac_sai_ma=False)
    combined = pd.concat([base_raw, cand.reindex(columns=base_raw.columns)], ignore_index=True)
    comb_ev = events.select_events(combined)

    links = _cluster_links(comb_ev)
    comb_ev["chi_vietstock"] = [all(l.startswith(config.VIETSTOCK_ARTICLE_BASE) for l in ls) for ls in links]
    in_new = {(c, l) for c, ls, only in zip(comb_ev["ma_nh"], links, comb_ev["chi_vietstock"]) if only for l in ls}
    in_any = {(c, l) for c, ls in zip(comb_ev["ma_nh"], links) for l in ls}

    is_cand = vs["ket_qua"] == "ung_vien"
    key = list(zip(vs["ma_nh"], vs["nguon"]))
    vs.loc[is_cand & pd.Series([k in in_new for k in key], index=vs.index), "ket_qua"] = "su_kien_moi"
    vs.loc[is_cand & pd.Series([k in in_any and k not in in_new for k in key], index=vs.index),
           "ket_qua"] = "xac_nhan_su_kien_da_co"
    vs.loc[vs["ket_qua"] == "ung_vien", "ket_qua"] = "trung_tieu_de_trong_ngay"
    return vs, comb_ev


def review_table(new_ev: pd.DataFrame, vs: pd.DataFrame, base_ev: pd.DataFrame) -> pd.DataFrame:
    """Danh sách sự kiện mới kèm ngữ cảnh để đọc duyệt."""
    info = vs.drop_duplicates(["ma_nh", "nguon"]).set_index(["ma_nh", "nguon"])
    same_q = (base_ev.assign(_t=base_ev["loai_su_kien"] + ": " + base_ev["tieu_de"].str.slice(0, 90))
                     .groupby(["ma_nh", "nam", "quy"])["_t"].agg(" || ".join))
    rows = []
    for r in new_ev.itertuples():
        near = info.loc[(r.ma_nh, r.nguon)] if (r.ma_nh, r.nguon) in info.index else None
        rows.append({
            "ma_nh": r.ma_nh, "nam": r.nam, "quy": r.quy,
            "ngay_cong_bo": f"{r.ngay_cong_bo:%Y-%m-%d %H:%M}",
            "loai_su_kien": r.loai_su_kien, "loai_su_kien_nhan": config.EVENT_LABELS[r.loai_su_kien],
            "mo_ta_ngan": r.tieu_de, "nguon": r.nguon, "nguon_du_lieu": r.nguon_du_lieu,
            "so_tin_gop": r.so_tin_gop, "nguon_khac": r.nguon_khac,
            "tin_gan_nhat_da_co": "" if near is None else near["tin_gan_nhat_da_co"],
            "do_giong_tin_gan_nhat": "" if near is None else near["do_giong"],
            "su_kien_da_co_cung_quy": same_q.get((r.ma_nh, r.nam, r.quy), ""),
            "danh_gia": "",  # điền khi đọc: dung / sai / trung
        })
    return pd.DataFrame(rows)


def report(vs: pd.DataFrame, base_ev: pd.DataFrame, comb_ev: pd.DataFrame, new_ev: pd.DataFrame) -> str:
    L = ["# Thử nghiệm Vietstock làm nguồn tin thứ hai", "",
         "Chưa thay đổi gì trong `data/output`. Cách đọc: cột `ket_qua` của "
         "`vietstock_thu_nghiem_tin.csv` cho biết mỗi tin dừng ở cổng nào.", ""]

    src = vs["nguon_du_lieu"].str.replace("Vietstock/", "", regex=False).str.upper()
    n_cbtt = int(src.isin(CBTT_SOURCES).sum())
    L += ["## 1. Tin Vietstock 2021–2025 đi qua các cổng", "",
          f"- Tổng: **{len(vs)}** tin, trong đó {n_cbtt} tin công bố thông tin của sàn (HOSE/HNX/UPCOM), "
          f"{len(vs) - n_cbtt} tin báo chí.", ""]
    tab = (vs.pivot_table(index="ma_nh", columns="ket_qua", values="nguon", aggfunc="size", fill_value=0)
             .reindex(columns=[k for k in KET_QUA if k in set(vs["ket_qua"])], fill_value=0))
    tab.loc["Tổng"] = tab.sum()
    L += _md_table(tab.rename(columns=KET_QUA).reset_index())

    L += ["## 2. Sự kiện mới (chỉ Vietstock có)", ""]
    if new_ev.empty:
        L += ["- Không có.", ""]
    else:
        t = new_ev.pivot_table(index="loai_su_kien", columns="nam", values="tieu_de",
                               aggfunc="size", fill_value=0)
        t["Tổng"] = t.sum(axis=1)
        L += _md_table(t.reset_index())
        t = new_ev.groupby("ma_nh").size().rename("so_su_kien_moi").reset_index()
        L += _md_table(t)

    q_old = events.aggregate_quarterly(base_ev)
    q_new = events.aggregate_quarterly(comb_ev)
    m = q_old.merge(q_new, on=["ma_nh", "nam", "quy"], suffixes=("_cu", "_moi"))
    flips = m[(m["co_su_kien_cu"] == 0) & (m["co_su_kien_moi"] == 1)]
    bridged = len(base_ev) + len(new_ev) - len(comb_ev)
    L += ["## 3. Ảnh hưởng nếu đưa vào Bảng 3", "",
          f"- Số sự kiện: {len(base_ev)} -> {len(comb_ev)}",
          f"- Số quý đổi `co_su_kien` 0 -> 1: **{len(flips)}** / {len(m)}",
          f"- Số dòng đổi `so_luong_su_kien`: {int((m['so_luong_su_kien_cu'] != m['so_luong_su_kien_moi']).sum())}",
          f"- Sự kiện cũ bị nối lại với nhau qua tin Vietstock (nên = 0): {bridged}", ""]
    diff = {k: int(m[f"sk_{k}_moi"].sum() - m[f"sk_{k}_cu"].sum()) for k in config.EVENT_LABELS}
    L += [f"- Thay đổi tổng `sk_*`: " + ", ".join(f"{k} {v:+d}" for k, v in diff.items()), ""]

    near_miss = vs[vs["cung_luc"].astype(bool) & (vs["quy_tac"] == "")]
    weak = vs[(vs["quy_tac"] == "gan_ngay") & (vs["do_giong"] < 0.8)]
    L += ["## 4. Kiểm tra ngưỡng so trùng", "",
          f"- Đăng cùng lúc (≤ {vietstock.SAME_POST_MINUTES} phút; tin đã có chỉ ghi ngày thì lệch ≤ "
          f"{vietstock.SAME_POST_DAYS} ngày) nhưng tiêu đề KHÔNG đủ giống -> coi là khác tin: **{len(near_miss)}** "
          "(xem mẫu dưới, nếu thực ra là cùng tin thì phải hạ ngưỡng)", ""]
    if not near_miss.empty:
        L += _md_table(near_miss[["ma_nh", "do_giong", "tieu_de", "tin_gan_nhat_da_co", "ket_qua"]].head(15))
    L += [f"- Coi là trùng theo quy tắc 'gần ngày' với độ giống < 0.8: **{len(weak)}** "
          "(xem mẫu dưới, nếu thực ra là khác tin thì phải nâng ngưỡng)", ""]
    if not weak.empty:
        L += _md_table(weak[["ma_nh", "do_giong", "lech_phut", "tieu_de", "tin_gan_nhat_da_co"]].head(15))

    hint = vs[(vs["ket_qua"] == "trung_tin_da_co") & vs["phan_loai_tieu_de"].notna()
              & vs["quyet_dinh_tin_trung"].isin(["không phải sự kiện"])]
    L += ["## 5. Gợi ý rà soát bản CafeF", "",
          "Tin trùng mà tiêu đề Vietstock được phân loại là sự kiện, nhưng bản đã có đang bị coi là "
          f"'không phải sự kiện': **{len(hint)}**. Không tự đếm – nếu đúng là sự kiện thì ghi link bản đã có "
          "vào `data/manual/su_kien_sua_loai.csv`.", ""]
    if not hint.empty:
        L += _md_table(hint[["ma_nh", "phan_loai_tieu_de", "tieu_de", "tin_gan_nhat_da_co"]].head(30))
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true", help="chỉ đọc cache, không gửi request")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    sys.stdout.reconfigure(encoding="utf-8")

    client = HttpClient(offline=args.offline)
    base_raw = events.collect_raw(client)
    base_ev = events.select_events(base_raw)
    log.info("Pipeline hiện tại: %d tin thô -> %d sự kiện", len(base_raw), len(base_ev))

    token = vietstock.SessionToken(client)
    frames = []
    for code in config.BANKS:
        log.info("[Vietstock] Tin %s", code)
        frames.append(vietstock.fetch_vietstock_news(client, code, token))
    vs = pd.concat(frames, ignore_index=True)
    log.info("Vietstock: %d tin trong %s – %s", len(vs), config.EVENT_FROM, config.EVENT_TO)

    vs = classify_vietstock(vs, base_raw)
    vs, comb_ev = merge_with_existing(vs, base_raw)
    new_ev = comb_ev[comb_ev["chi_vietstock"]]

    out = vs.assign(ngay_cong_bo=vs["ngay_cong_bo"].dt.strftime("%Y-%m-%d %H:%M"))[
        ["ma_nh", "ngay_cong_bo", "nguon_du_lieu", "tieu_de", "ket_qua", "loai_su_kien", "quy_tac",
         "do_giong", "lech_phut", "cung_luc", "tin_gan_nhat_da_co", "quyet_dinh_tin_trung", "phan_loai_tieu_de", "nguon"]]
    out.to_csv(config.INTERIM_DIR / "vietstock_thu_nghiem_tin.csv", index=False, encoding="utf-8-sig")
    review_table(new_ev, vs, base_ev).to_csv(config.INTERIM_DIR / "vietstock_thu_nghiem_su_kien_moi.csv",
                                             index=False, encoding="utf-8-sig")
    (config.INTERIM_DIR / "vietstock_thu_nghiem_bao_cao.md").write_text(
        report(vs, base_ev, comb_ev, new_ev), encoding="utf-8")
    log.info("Sự kiện mới chỉ Vietstock có: %d. Xem data/interim/vietstock_thu_nghiem_bao_cao.md", len(new_ev))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
