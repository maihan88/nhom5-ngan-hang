"""HTTP client dùng chung: retry + backoff, giãn cách request, cache file gốc.

Mọi phản hồi được lưu vào data/raw/ theo khóa cache. Lần chạy sau sẽ đọc lại từ cache
(trừ khi truyền refresh=True), giúp:
  - không tải lại dữ liệu đã có (tôn trọng server nguồn),
  - truy vết được dữ liệu gốc khi có số liệu bất thường.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config

log = logging.getLogger(__name__)


class HttpClient:
    def __init__(self, refresh: bool = False, offline: bool = False):
        self.refresh = refresh
        self.offline = offline  # True: chỉ đọc cache, tuyệt đối không gửi request mới
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        retry = Retry(
            total=config.MAX_RETRIES,
            backoff_factor=2,  # 2s, 4s, 8s, ...
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST"),  # POST chỉ dùng cho endpoint đọc dữ liệu (Vietstock)
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self._last_call = 0.0

    # ------------------------------------------------------------------
    def _throttle(self) -> None:
        wait = config.REQUEST_DELAY_SEC - (time.time() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.time()

    @staticmethod
    def _cache_path(namespace: str, key: str, ext: str) -> Path:
        digest = hashlib.md5(key.encode("utf-8")).hexdigest()[:12]
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)[:80]
        return config.RAW_DIR / namespace / f"{safe}_{digest}.{ext}"

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        if self.offline:
            raise RuntimeError(f"Chế độ --offline: chưa có cache cho {method} {url} "
                               f"{kwargs.get('params') or ''}")
        self._throttle()
        resp = self.session.request(method, url, timeout=config.TIMEOUT_SEC, **kwargs)
        resp.raise_for_status()
        return resp

    def _get(self, url: str, params: dict | None) -> requests.Response:
        return self._request("GET", url, params=params)

    # ------------------------------------------------------------------
    def get_json(self, url: str, params: dict | None = None, *, namespace: str, key: str) -> dict:
        path = self._cache_path(namespace, key, "json")
        if path.exists() and not self.refresh:
            return json.loads(path.read_text(encoding="utf-8"))
        resp = self._get(url, params)
        data = resp.json()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    def get_text(self, url: str, params: dict | None = None, *, namespace: str, key: str) -> str:
        path = self._cache_path(namespace, key, "html")
        if path.exists() and not self.refresh:
            return path.read_text(encoding="utf-8")
        resp = self._get(url, params)
        resp.encoding = resp.encoding or "utf-8"
        text = resp.text
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return text

    def get_file(self, url: str, path: Path) -> Path:
        """Tải file nhị phân (PDF) về `path`; đã có file thì dùng lại (trừ khi refresh).
        Lỗi HTTP (vd 404 khi ngân hàng chưa công bố) được ném ra để nơi gọi xử lý."""
        if path.exists() and not self.refresh:
            return path
        resp = self._request("GET", url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(resp.content)
        return path

    def get_text_uncached(self, url: str) -> str:
        """Tải trang KHÔNG lưu cache – dùng cho trang chỉ để lấy cookie/token phiên."""
        return self._request("GET", url).text

    def post_json(self, url: str, form: Callable[[], dict], *, namespace: str, key: str,
                  headers: dict | None = None):
        """POST form và cache JSON trả về. `form` là hàm, chỉ được gọi khi chưa có cache,
        để token phiên (thay đổi mỗi lần) không nằm trong khóa cache và không phải lấy khi chạy lại."""
        path = self._cache_path(namespace, key, "json")
        if path.exists() and not self.refresh:
            return json.loads(path.read_text(encoding="utf-8"))
        resp = self._request("POST", url, data=form(), headers=headers)
        try:
            data = resp.json()
        except ValueError as exc:
            raise RuntimeError(f"{url} không trả JSON (token hết hạn hoặc bị chặn?): "
                               f"{resp.text[:200]!r}") from exc
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    # ------------------------------------------------------------------
    def vnd_paged(self, endpoint: str, q: str, *, namespace: str, key: str,
                  sort: str | None = None, size: int = 5000, max_pages: int = 50) -> list[dict]:
        """Lấy toàn bộ bản ghi từ một endpoint VNDirect có phân trang."""
        url = f"{config.VND_API}/{endpoint}"
        rows: list[dict] = []
        page = 1
        while page <= max_pages:
            params = {"q": q, "size": size, "page": page}
            if sort:
                params["sort"] = sort
            data = self.get_json(url, params, namespace=namespace, key=f"{key}_p{page}")
            if "data" not in data:
                raise RuntimeError(f"VNDirect trả lỗi cho {endpoint} q={q}: {data}")
            rows.extend(data["data"])
            total_pages = int(data.get("totalPages") or 1)
            if page >= total_pages:
                break
            page += 1
        log.debug("%s %s -> %d bản ghi", endpoint, q, len(rows))
        return rows
