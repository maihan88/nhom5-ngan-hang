"""Nguồn tin thứ hai: Vietstock (đang thử nghiệm – chưa đưa vào Bảng 3).

Danh sách tin theo mã trên finance.vietstock.vn được tải bằng POST /data/GetNews (trả JSON),
kèm token chống giả mạo lấy từ trang "Tin tức & Sự kiện". Không cần đăng nhập.

Phần công bố thông tin (nguồn HOSE/HNX) trùng gần như hoàn toàn với CafeF: cùng giờ đăng,
chỉ khác cách viết tiêu đề ("Thông báo công văn của UBCKNN về..." / "Công văn của UBCKNN v/v...").
Vì vậy mỗi tin Vietstock được so với tin đã có TRƯỚC khi phân loại. Tin trùng giữ nguyên quyết định
đã có (kể cả quyết định rà soát thủ công) chứ không được phân loại lại thành một sự kiện mới.
"""
from __future__ import annotations

import logging
import re
import unicodedata

import pandas as pd
from bs4 import BeautifulSoup

from . import config
from .http_client import HttpClient

log = logging.getLogger(__name__)

PAGE_SIZE = 20  # server chỉ trả tối đa 20 tin/trang dù xin nhiều hơn

# Quy tắc coi một tin Vietstock là TRÙNG với tin đã có của cùng ngân hàng:
#   cung_luc – đăng cùng lúc và tiêu đề giống >= SAME_POST_MIN_SIM (CBTT do sàn phát hành: hai trang
#              đăng cùng phút nhưng viết tiêu đề khác nhau). "Cùng lúc" = cách <= SAME_POST_MINUTES phút;
#              riêng tin đã có chỉ ghi ngày (00:00 – CafeF từ 2023) thì = cách <= SAME_POST_DAYS ngày
#   gan_ngay – cách nhau <= NEAR_DAYS ngày và tiêu đề giống >= NEAR_MIN_SIM
SAME_POST_MINUTES = 10
SAME_POST_DAYS = 1
SAME_POST_MIN_SIM = 0.5
NEAR_DAYS = 3
NEAR_MIN_SIM = 0.7

# Hai cách bỏ dấu (hoá/hóa, thuỷ/thủy) -> đưa về một cách trước khi so tiêu đề
_OLD_TONE = {"oá": "óa", "oà": "òa", "oả": "ỏa", "oã": "õa", "oạ": "ọa",
             "oé": "óe", "oè": "òe", "oẻ": "ỏe", "oẽ": "õe", "oẹ": "ọe",
             "uý": "úy", "uỳ": "ùy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy"}
# Từ chỉ khác nhau do cách đặt tiêu đề của mỗi trang, không mang nội dung
_STOP = {"thông", "báo", "cbtt", "về", "việc", "v", "của", "và", "các", "cho", "với", "tại", "là"}


class SessionToken:
    """Token chống giả mạo (__RequestVerificationToken), chỉ lấy khi thật sự phải gửi request."""

    def __init__(self, client: HttpClient):
        self.client = client
        self.value: str | None = None

    def get(self, code: str) -> str:
        if self.value is None:
            html = self.client.get_text_uncached(config.VIETSTOCK_NEWS_PAGE.format(code=code))
            tag = BeautifulSoup(html, "html.parser").select_one("input[name=__RequestVerificationToken]")
            if tag is None or not tag.get("value"):
                raise RuntimeError("Không tìm thấy token trên trang tin Vietstock – giao diện có thể đã đổi")
            self.value = tag["value"]
        return self.value


def _parse_item(code: str, r: dict) -> dict:
    ms = int(re.search(r"-?\d+", r["PublishTime"]).group())
    url = r.get("URL") or ""
    return {
        "_id": r.get("ArticleID"),
        "ma_nh": code,
        "ngay_cong_bo": pd.Timestamp(ms, unit="ms") + pd.Timedelta(hours=7),  # epoch UTC -> giờ VN
        "tieu_de": " ".join((r.get("Title") or "").split()),
        "nguon": url if url.startswith("http") else config.VIETSTOCK_ARTICLE_BASE + url,
        "nguon_du_lieu": f"Vietstock/{(r.get('Source') or '').strip()}",
    }


def fetch_vietstock_news(client: HttpClient, code: str, token: SessionToken,
                         max_pages: int = 300) -> pd.DataFrame:
    start = pd.Timestamp(config.EVENT_FROM)
    end = pd.Timestamp(config.EVENT_TO) + pd.Timedelta(days=1)
    headers = {"X-Requested-With": "XMLHttpRequest",
               "Referer": config.VIETSTOCK_NEWS_PAGE.format(code=code)}
    rows: list[dict] = []
    seen: set = set()
    for page in range(1, max_pages + 1):
        data = client.post_json(
            config.VIETSTOCK_NEWS_URL,
            lambda page=page: {"code": code, "type": -1, "page": page, "pageSize": PAGE_SIZE,
                               "__RequestVerificationToken": token.get(code)},
            namespace="vietstock_news", key=f"{code}_p{page}_s{PAGE_SIZE}", headers=headers)
        if not isinstance(data, list):
            raise RuntimeError(f"Vietstock trả dữ liệu lạ cho {code} trang {page}: {str(data)[:200]}")
        if not data:
            break
        items = [_parse_item(code, r) for r in data]
        for it in items:
            # Tin mới đăng giữa hai lần tải làm các trang dịch đi -> một tin có thể xuất hiện 2 lần
            if it["_id"] in seen:
                continue
            seen.add(it["_id"])
            if start <= it["ngay_cong_bo"] < end:
                rows.append(it)
        if min(i["ngay_cong_bo"] for i in items) < start:  # tin xếp mới -> cũ
            break
    else:
        log.warning("Vietstock %s: chạm giới hạn %d trang, có thể chưa lấy hết", code, max_pages)
    cols = ["ngay_cong_bo", "tieu_de", "nguon", "ma_nh", "nguon_du_lieu"]
    return pd.DataFrame(rows, columns=["_id", *cols])[cols]


# ---------------------------------------------------------------------------
def title_tokens(title: str) -> frozenset[str]:
    t = unicodedata.normalize("NFC", (title or "").lower())
    t = re.sub(r"^\s*[a-z]{3}\s*:\s*", "", t)  # bỏ tiền tố mã CK "vcb:"
    t = t.replace("v/v", " về việc ")
    for old, new in _OLD_TONE.items():
        t = t.replace(old, new)
    return frozenset(re.findall(r"\w+", t)) - _STOP


def similarity(a: frozenset[str], b: frozenset[str]) -> float:
    """Hệ số Dice trên tập từ: 1 = cùng bộ từ, 0 = không chung từ nào."""
    return 2 * len(a & b) / (len(a) + len(b)) if a and b else 0.0


def match_existing(vs: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    """Với mỗi tin Vietstock, tìm tin đã có (cùng mã, cách <= NEAR_DAYS ngày) giống nhất.

    Trả về DataFrame cùng index với `vs`:
      gan_nhat_idx – index trong `base` của tin giống nhất (kể cả khi không đủ ngưỡng trùng)
      do_giong, lech_phut – mức giống tiêu đề và độ lệch giờ đăng với tin đó
      cung_luc – tin đó có được đăng cùng lúc không (dù tiêu đề có đủ giống hay không)
      quy_tac – 'cung_luc' / 'gan_ngay' nếu coi là trùng, '' nếu không
    """
    base = base.assign(tok=base["tieu_de"].map(title_tokens))
    by_code = {c: g.sort_values("ngay_cong_bo") for c, g in base.groupby("ma_nh")}
    window = pd.Timedelta(days=NEAR_DAYS)
    out = []
    for r in vs.itertuples():
        best = None
        g = by_code.get(r.ma_nh)
        if g is not None:
            tok = title_tokens(r.tieu_de)
            cand = g[g["ngay_cong_bo"].between(r.ngay_cong_bo - window, r.ngay_cong_bo + window)]
            for c in cand.itertuples():
                sim = similarity(tok, c.tok)
                minutes = abs((c.ngay_cong_bo - r.ngay_cong_bo).total_seconds()) / 60
                if c.ngay_cong_bo == c.ngay_cong_bo.normalize():  # tin đã có chỉ ghi ngày
                    days = abs((c.ngay_cong_bo - r.ngay_cong_bo.normalize()).days)
                    same_time = days <= SAME_POST_DAYS
                else:
                    same_time = minutes <= SAME_POST_MINUTES
                if same_time and sim >= SAME_POST_MIN_SIM:
                    rule = "cung_luc"
                elif sim >= NEAR_MIN_SIM:
                    rule = "gan_ngay"
                else:
                    rule = ""
                key = (rule != "", sim, -minutes)
                if best is None or key > best[0]:
                    best = (key, c.Index, sim, minutes, same_time, rule)
        if best is None:
            out.append({"gan_nhat_idx": None, "do_giong": 0.0, "lech_phut": None,
                        "cung_luc": False, "quy_tac": ""})
        else:
            _, idx, sim, minutes, same_time, rule = best
            out.append({"gan_nhat_idx": idx, "do_giong": round(sim, 3), "lech_phut": round(minutes),
                        "cung_luc": same_time, "quy_tac": rule})
    return pd.DataFrame(out, index=vs.index)
