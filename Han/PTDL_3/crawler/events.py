"""Bảng 3 – Yếu tố phi tài chính (sự kiện) theo quý.

Nguồn (chọn theo độ phủ thời gian 2021–2025 & độ tin cậy của ngày công bố):
  1. CafeF – danh sách tin/công bố thông tin theo mã cổ phiếu (có lịch sử từ trước 2021,
     mỗi tin có ngày giờ công bố + link gốc).
  2. VNDirect /events – sự kiện quyền có cấu trúc (cổ tức bằng cổ phiếu, phát hành thêm...)
     -> nguồn chính xác nhất cho nhóm "tăng vốn".
  3. VNDirect /news (company_news) – chỉ có dữ liệu từ khoảng 2025, dùng bổ sung.

Quy trình: crawl -> loại tin thường quy -> phân loại theo từ khóa -> gộp tin trùng
-> áp dụng file rà soát thủ công (data/manual) -> tổng hợp theo quý.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup

from . import config
from .http_client import HttpClient

log = logging.getLogger(__name__)

BANK_ALIASES = {  # dùng để kiểm tra tin tức thực sự nói về ngân hàng nào
    "VCB": ["vcb", "vietcombank"],
    "BID": ["bid", "bidv"],
    "CTG": ["ctg", "vietinbank"],
    "TCB": ["tcb", "techcombank"],
    "MBB": ["mbb", "mb", "mb bank", "mbbank", "ngân hàng quân đội"],
    "ACB": ["acb", "á châu"],
    "STB": ["stb", "sacombank"],
    "VPB": ["vpb", "vpbank"],
}
# Ngân hàng ngoài phạm vi – chỉ dùng để nhận diện tin tổng hợp toàn ngành
OTHER_BANKS = ["agribank", "hdbank", "shb", "vib", "tpbank", "msb", "ocb", "lpbank", "seabank",
               "eximbank", "nam a bank", "abbank", "bac a bank", "vietbank", "kienlongbank",
               "pvcombank", "gpbank", "oceanbank", "cbbank", "dongabank", "scb", "ncb", "baoviet bank"]


def _nfc(text):
    """Chuẩn hóa Unicode về dạng dựng sẵn (NFC).

    Tiếng Việt có 2 cách lưu chữ có dấu: "ả" là 1 ký tự (NFC) hoặc "a" + dấu hỏi rời U+0309 (NFD).
    Nhìn giống hệt nhưng regex coi là khác nhau. Một số tiêu đề CafeF lưu kiểu NFD, khiến mẫu
    "giải tỏa" không khớp. Mọi so khớp và tiêu đề lưu ra đều đi qua hàm này."""
    return unicodedata.normalize("NFC", text) if isinstance(text, str) else text


def _word_rx(words: list[str]) -> re.Pattern:
    return re.compile(r"(?<!\w)(" + "|".join(re.escape(w) for w in words) + r")(?!\w)", re.IGNORECASE)


_BANK_RX = {code: _word_rx(al) for code, al in BANK_ALIASES.items()}
_OTHER_RX = {name: _word_rx([name]) for name in OTHER_BANKS}


def banks_mentioned(text: str) -> set[str]:
    """Tập ngân hàng (trong & ngoài phạm vi) được nhắc tới trong đoạn văn bản."""
    text = _nfc(text or "")
    found = {c for c, rx in _BANK_RX.items() if rx.search(text)}
    found |= {n for n, rx in _OTHER_RX.items() if rx.search(text)}
    return found


def _compile(patterns: list[str] | None) -> re.Pattern | None:
    return re.compile("|".join(patterns), re.IGNORECASE) if patterns else None


_EXCLUDE_RE = _compile(config.EVENT_EXCLUDE)
_RULES = [(cat, _compile(r.get("any")), _compile(r.get("require")), _compile(r.get("deny")))
          for cat, r in config.EVENT_RULES]


def classify(title: str) -> str | None:
    """Trả về mã loai_su_kien hoặc None nếu là tin thường quy / không thuộc nhóm nào."""
    t = " " + _nfc(title or "").lower() + " "
    if _EXCLUDE_RE.search(t):
        return None
    for cat, any_rx, req_rx, deny_rx in _RULES:
        if not any_rx.search(t):
            continue
        if req_rx is not None and not req_rx.search(t):
            continue
        if deny_rx is not None and deny_rx.search(t):
            continue
        return cat
    return None


def is_off_target(code: str, title: str) -> bool:
    """True nếu tin không nói riêng về ngân hàng `code`:
    - tiêu đề CBTT dạng 'XXX: ...' nhưng XXX là mã khác (CafeF đôi khi gắn nhầm mã),
    - hoặc là tin tổng hợp nhắc từ INDUSTRY_NEWS_MIN_BANKS ngân hàng trở lên."""
    m = re.match(r"^\s*([A-Z]{3}):", title or "")
    if m and m.group(1) != code:
        return True
    return len(banks_mentioned(title)) >= config.INDUSTRY_NEWS_MIN_BANKS


# ---------------------------------------------------------------------------
# 1. CafeF
# ---------------------------------------------------------------------------
def _parse_cafef_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for li in soup.select("ul.News_Title_Link li"):
        t = li.select_one("span.timeTitle")
        a = li.select_one("a")
        if not t or not a:
            continue
        try:
            ts = datetime.strptime(t.get_text(strip=True), "%d/%m/%Y %H:%M")
        except ValueError:
            continue
        href = a.get("href", "").split("?")[0]
        # Lấy chữ hiển thị của link, KHÔNG lấy thuộc tính title: CafeF để dấu " trong title
        # mà không mã hóa nên thuộc tính bị cắt cụt (vd 'Techcombank bắt tay "gã khổng lồ"...')
        title = " ".join(a.get_text(" ", strip=True).split()) or (a.get("title") or "").strip()
        items.append({
            "ngay_cong_bo": ts,
            "tieu_de": title,
            "nguon": href if href.startswith("http") else config.CAFEF_BASE + href,
        })
    return items


def fetch_cafef(client: HttpClient, code: str, page_size: int = 30, max_pages: int = 400) -> pd.DataFrame:
    start = pd.Timestamp(config.EVENT_FROM)
    end = pd.Timestamp(config.EVENT_TO) + pd.Timedelta(days=1)
    rows: list[dict] = []
    for page in range(1, max_pages + 1):
        params = {"symbol": code, "floorID": 0, "configID": 0,
                  "PageIndex": page, "PageSize": page_size, "Type": 2}
        html = client.get_text(config.CAFEF_EVENTS_URL, params, namespace="cafef_events",
                               key=f"{code}_p{page}_s{page_size}")
        items = _parse_cafef_page(html)
        if not items:
            break
        rows.extend(i for i in items if start <= i["ngay_cong_bo"] < end)
        if min(i["ngay_cong_bo"] for i in items) < start:  # tin xếp mới -> cũ
            break
    else:
        log.warning("CafeF %s: chạm giới hạn %d trang, có thể chưa lấy hết", code, max_pages)
    df = pd.DataFrame(rows, columns=["ngay_cong_bo", "tieu_de", "nguon"])
    df["ma_nh"] = code
    df["nguon_du_lieu"] = "CafeF"
    return df


# ---------------------------------------------------------------------------
# 2. VNDirect – sự kiện quyền (tăng vốn)
# ---------------------------------------------------------------------------
def fetch_vnd_capital_events(client: HttpClient, code: str) -> pd.DataFrame:
    q = f"code:{code}~locale:VN~disclosureDate:gte:{config.EVENT_FROM}~disclosureDate:lte:{config.EVENT_TO}"
    rows = client.vnd_paged("events", q, namespace="vnd_events", key=f"{code}_events",
                            sort="disclosureDate:asc", size=1000)
    out = []
    for r in rows:
        if r.get("type") not in config.VND_CAPITAL_EVENT_TYPES or not r.get("disclosureDate"):
            continue
        note = (r.get("note") or r.get("typeDesc") or "").strip()
        out.append({
            "ma_nh": code,
            "ngay_cong_bo": pd.Timestamp(r["disclosureDate"]),
            "tieu_de": f"{r.get('typeDesc', '').strip()}: {note}",
            "nguon": f"https://dstock.vndirect.com.vn/tong-quan/{code}/su-kien-quyen"
                     + (f"?newsId={int(r['newsId'])}" if r.get("newsId") else ""),
            "nguon_du_lieu": "VNDirect-events",
            "loai_su_kien": "tang_von",
        })
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# 3. VNDirect – tin doanh nghiệp (chỉ có từ ~2025)
# ---------------------------------------------------------------------------
def fetch_vnd_news(client: HttpClient, code: str) -> pd.DataFrame:
    q = (f"newsType:company_news~locale:VN~tagCodes:{code}"
         f"~newsDate:gte:{config.EVENT_FROM}~newsDate:lte:{config.EVENT_TO}")
    url = f"{config.VND_API}/news"
    rows, page = [], 1
    while True:
        params = {"q": q, "sort": "newsDate:desc~newsTime:desc", "size": 100, "page": page,
                  "fields": "newsId,newsTitle,newsAbstract,newsDate,newsTime,newsSource,tagCodes,newsUrl"}
        data = client.get_json(url, params, namespace="vnd_news", key=f"{code}_news_p{page}")
        rows.extend(data.get("data", []))
        if page >= int(data.get("totalPages") or 1):
            break
        page += 1
    out = []
    for r in rows:
        title = (r.get("newsTitle") or "").strip()
        # tagCodes thường gắn nhiều mã -> chỉ giữ tin có TIÊU ĐỀ nhắc đến ngân hàng này
        if not _BANK_RX[code].search(title):
            continue
        ts = pd.to_datetime(f"{r.get('newsDate')} {r.get('newsTime') or ''}".strip(), errors="coerce")
        if pd.isna(ts):
            ts = pd.to_datetime(r.get("newsDate"), errors="coerce")
        if pd.isna(ts):
            continue
        out.append({
            "ma_nh": code,
            "ngay_cong_bo": ts,
            "tieu_de": title,
            "nguon": r.get("newsUrl") or f"https://dstock.vndirect.com.vn/tin-tuc/{r.get('newsId')}",
            "nguon_du_lieu": f"VNDirect-news/{r.get('newsSource', '')}",
        })
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
def _dedup(df: pd.DataFrame) -> pd.DataFrame:
    """Gộp tin trùng: cùng NH, cùng loại, cách nhau <= N ngày -> 1 sự kiện (giữ tin sớm nhất)."""
    df = df.sort_values(["ma_nh", "loai_su_kien", "ngay_cong_bo"]).copy()
    df["_norm"] = df["tieu_de"].str.lower().str.replace(r"^[a-z]{3}:\s*", "", regex=True).str.strip()
    df["_day"] = df["ngay_cong_bo"].dt.date
    df = df.drop_duplicates(["ma_nh", "_norm", "_day"])  # cùng tiêu đề đăng lại trong ngày
    gap = df.groupby(["ma_nh", "loai_su_kien"])["ngay_cong_bo"].diff().dt.days
    new_cluster = gap.isna() | (gap > config.EVENT_DEDUP_WINDOW_DAYS)
    # Loại "1 sự kiện / quý" (vd tăng vốn): mọi tin cùng quý gộp làm 1, giữ tin sớm nhất
    per_q = df["loai_su_kien"].isin(config.EVENT_ONE_PER_QUARTER)
    if per_q.any():
        q = df["ngay_cong_bo"].dt.to_period("Q")
        q_changed = q.ne(df.groupby(["ma_nh", "loai_su_kien"])["ngay_cong_bo"].shift().dt.to_period("Q"))
        new_cluster = new_cluster.where(~per_q, q_changed)
    df["_cluster"] = new_cluster.cumsum()
    agg = (df.groupby("_cluster")
             .agg(ma_nh=("ma_nh", "first"), loai_su_kien=("loai_su_kien", "first"),
                  ngay_cong_bo=("ngay_cong_bo", "first"), tieu_de=("tieu_de", "first"),
                  nguon=("nguon", "first"), nguon_du_lieu=("nguon_du_lieu", "first"),
                  so_tin_gop=("tieu_de", "size"),
                  nguon_khac=("nguon", lambda s: " ; ".join(s.iloc[1:]))))
    return agg.reset_index(drop=True)


def _read_manual(path, required: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=required)
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig").dropna(subset=required)
    return df if df.empty else df.apply(lambda s: s.str.strip())


def _match_manual(raw: pd.DataFrame, manual: pd.DataFrame) -> pd.Series:
    """Tin thô nào khớp file rà soát: theo link `nguon`; nếu file có cột ma_nh thì khớp cả mã
    (một bài CafeF có thể nằm trong danh sách tin của nhiều mã)."""
    if manual.empty:
        return pd.Series(False, index=raw.index)
    if "ma_nh" in manual and manual["ma_nh"].notna().any():
        with_code = manual.dropna(subset=["ma_nh"])
        keys = set(zip(with_code["ma_nh"], with_code["nguon"]))
        hit = pd.Series([(c, n) in keys for c, n in zip(raw["ma_nh"], raw["nguon"])], index=raw.index)
        no_code = set(manual.loc[manual["ma_nh"].isna(), "nguon"])
        return hit | raw["nguon"].isin(no_code)
    return raw["nguon"].isin(set(manual["nguon"]))


def _apply_manual(raw: pd.DataFrame) -> pd.DataFrame:
    """Áp dụng rà soát thủ công trên TỪNG TIN THÔ, trước khi gộp tin.

    Làm trước bước gộp để việc loại một tin (vd tin tăng vốn của công ty con) không kéo theo
    các tin hợp lệ khác đã bị gộp chung cụm. Link dùng để loại/sửa có thể lấy ở cột `nguon`
    hoặc `nguon_khac` của bang3a, hoặc từ data/interim/tin_tho_da_phan_loai.csv.
    """
    raw = raw.copy()
    raw["ra_soat_tay"] = ""

    rm = _read_manual(config.MANUAL_DIR / "su_kien_loai_bo.csv", ["nguon"])
    hit = _match_manual(raw, rm)
    raw.loc[hit, ["loai_su_kien", "ra_soat_tay"]] = [None, "loai_bo"]
    log.info("Rà soát: loại %d tin theo su_kien_loai_bo.csv", int(hit.sum()))

    fix = _read_manual(config.MANUAL_DIR / "su_kien_sua_loai.csv", ["nguon", "loai_su_kien"])
    for r in fix.itertuples():
        one = pd.DataFrame([r._asdict()]).drop(columns="Index")
        m = _match_manual(raw, one)
        raw.loc[m, ["loai_su_kien", "ra_soat_tay"]] = [r.loai_su_kien, "sua_loai"]
    if not fix.empty:
        log.info("Rà soát: sửa loại %d tin theo su_kien_sua_loai.csv", int((raw["ra_soat_tay"] == "sua_loai").sum()))

    add = _read_manual(config.MANUAL_DIR / "su_kien_bo_sung.csv", ["ma_nh", "ngay_cong_bo", "loai_su_kien"])
    if not add.empty:
        add = add.assign(ngay_cong_bo=pd.to_datetime(add["ngay_cong_bo"]),
                         nguon_du_lieu="Bổ sung thủ công", ra_soat_tay="bo_sung",
                         tin_nganh_hoac_sai_ma=False)
        for c in ["tieu_de", "nguon"]:
            add[c] = add[c].fillna("") if c in add else ""
        raw = pd.concat([raw, add[[c for c in add.columns if c in raw.columns or c == "ra_soat_tay"]]],
                        ignore_index=True)
        log.info("Rà soát: bổ sung %d sự kiện từ su_kien_bo_sung.csv", len(add))

    bad = raw["loai_su_kien"].notna() & ~raw["loai_su_kien"].isin(config.EVENT_LABELS)
    if bad.any():
        log.warning("Bỏ %d dòng có loai_su_kien không hợp lệ: %s", int(bad.sum()),
                    sorted(raw.loc[bad, "loai_su_kien"].unique()))
        raw.loc[bad, "loai_su_kien"] = None
    return raw


def aggregate_quarterly(events: pd.DataFrame) -> pd.DataFrame:
    """Mỗi dòng = 1 ngân hàng x 1 quý. Quý không có sự kiện -> co_su_kien = 0, so_luong = 0."""
    grid = pd.MultiIndex.from_product(
        [list(config.BANKS), range(config.START_YEAR, config.END_YEAR + 1), ["Q1", "Q2", "Q3", "Q4"]],
        names=["ma_nh", "nam", "quy"]).to_frame(index=False)

    ev = events.copy()
    ev["nam"] = ev["ngay_cong_bo"].dt.year
    ev["quy"] = "Q" + ev["ngay_cong_bo"].dt.quarter.astype(str)
    ev = ev.sort_values("ngay_cong_bo")
    ev["_ngay"] = ev["ngay_cong_bo"].dt.strftime("%Y-%m-%d")
    ev["_nhan"] = ev["loai_su_kien"].map(config.EVENT_LABELS)

    g = ev.groupby(["ma_nh", "nam", "quy"])
    q = g.agg(so_luong_su_kien=("loai_su_kien", "size"),
              loai_su_kien=("_nhan", lambda s: "; ".join(dict.fromkeys(s))),
              ngay_cong_bo=("_ngay", "; ".join),
              mo_ta_ngan=("tieu_de", " | ".join),
              nguon=("nguon", " ; ".join)).reset_index()
    counts = (ev.pivot_table(index=["ma_nh", "nam", "quy"], columns="loai_su_kien",
                             values="tieu_de", aggfunc="size", fill_value=0)
                .reindex(columns=list(config.EVENT_LABELS), fill_value=0)
                .add_prefix("sk_").reset_index())

    out = grid.merge(q, on=["ma_nh", "nam", "quy"], how="left").merge(
        counts, on=["ma_nh", "nam", "quy"], how="left")
    out["so_luong_su_kien"] = out["so_luong_su_kien"].fillna(0).astype(int)
    out["co_su_kien"] = (out["so_luong_su_kien"] > 0).astype(int)
    for c in [f"sk_{k}" for k in config.EVENT_LABELS]:
        out[c] = out[c].fillna(0).astype(int)
    for c in ["loai_su_kien", "ngay_cong_bo", "mo_ta_ngan", "nguon"]:
        out[c] = out[c].fillna("")
    cols = ["ma_nh", "quy", "nam", "co_su_kien", "so_luong_su_kien", "loai_su_kien",
            *[f"sk_{k}" for k in config.EVENT_LABELS], "ngay_cong_bo", "mo_ta_ngan", "nguon"]
    return out[cols].sort_values(["ma_nh", "nam", "quy"]).reset_index(drop=True)


def collect_raw(client: HttpClient, use_vnd_news: bool = True) -> pd.DataFrame:
    """Tin thô từ mọi nguồn: đã gắn cờ tin ngành, phân loại và áp dụng rà soát thủ công, CHƯA gộp."""
    raw_frames = []
    for code in config.BANKS:
        log.info("[Bảng 3] Tin/sự kiện %s", code)
        raw_frames.append(fetch_cafef(client, code))
        if use_vnd_news:
            try:
                raw_frames.append(fetch_vnd_news(client, code))
            except Exception as exc:  # nguồn phụ – lỗi không làm dừng pipeline
                log.warning("Bỏ qua tin VNDirect %s: %s", code, exc)
        raw_frames.append(fetch_vnd_capital_events(client, code))

    raw = pd.concat([f for f in raw_frames if not f.empty], ignore_index=True)
    raw["tieu_de"] = raw["tieu_de"].map(_nfc)  # chuẩn hóa Unicode trước khi phân loại / gộp tin
    raw["tin_nganh_hoac_sai_ma"] = [is_off_target(c, t) for c, t in zip(raw["ma_nh"], raw["tieu_de"])]
    need = raw["loai_su_kien"].isna() if "loai_su_kien" in raw else pd.Series(True, index=raw.index)
    raw.loc[need, "loai_su_kien"] = raw.loc[need, "tieu_de"].map(classify)
    raw = _apply_manual(raw)  # rà soát thủ công áp dụng trên từng tin, TRƯỚC khi gộp
    return raw.sort_values(["ma_nh", "ngay_cong_bo"]).reset_index(drop=True)


def select_events(raw: pd.DataFrame) -> pd.DataFrame:
    """Giữ tin là sự kiện của chính ngân hàng rồi gộp tin trùng -> mỗi dòng 1 sự kiện."""
    # Tin được sửa loại / bổ sung bằng tay luôn được giữ, kể cả khi bộ lọc tự động coi là tin ngành
    manual_keep = raw["ra_soat_tay"].isin(["sua_loai", "bo_sung"])
    kept = raw[raw["loai_su_kien"].notna() & (~raw["tin_nganh_hoac_sai_ma"] | manual_keep)]
    events = _dedup(kept)
    events = events.sort_values(["ma_nh", "ngay_cong_bo"]).reset_index(drop=True)
    events["nam"] = events["ngay_cong_bo"].dt.year
    events["quy"] = "Q" + events["ngay_cong_bo"].dt.quarter.astype(str)
    return events


def build_bang3(client: HttpClient, use_vnd_news: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Trả về (tin_tho_da_phan_loai, su_kien_chi_tiet, bang3_theo_quy)."""
    raw = collect_raw(client, use_vnd_news)
    events = select_events(raw)
    bang3 = aggregate_quarterly(events)

    events_out = events.copy()
    events_out["loai_su_kien_nhan"] = events_out["loai_su_kien"].map(config.EVENT_LABELS)
    events_out["ngay_cong_bo"] = events_out["ngay_cong_bo"].dt.strftime("%Y-%m-%d %H:%M")
    events_out = events_out.rename(columns={"tieu_de": "mo_ta_ngan"})[
        ["ma_nh", "quy", "nam", "ngay_cong_bo", "loai_su_kien", "loai_su_kien_nhan",
         "mo_ta_ngan", "nguon", "nguon_du_lieu", "so_tin_gop", "nguon_khac"]]
    raw_out = raw.copy()
    raw_out["ngay_cong_bo"] = raw_out["ngay_cong_bo"].dt.strftime("%Y-%m-%d %H:%M")
    return raw_out, events_out, bang3
