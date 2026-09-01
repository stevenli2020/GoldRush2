"""Collection of the World Gold Council ETF flows workbook."""

from __future__ import annotations

import html
import json
import os
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin
from urllib.request import Request, urlopen

WGC_PAGE_URL = "https://www.gold.org/goldhub/data/gold-etfs-holdings-and-flows"
CACHE_MAX_AGE_DAYS = 7
USER_AGENT = "Mozilla/5.0 GoldRush2 WGC downloader"
LAST_FETCH_USED_CACHE = False
LAST_FETCH_STALE = False


class WGCError(RuntimeError):
    """Raised when the WGC workbook cannot be downloaded or validated."""


def _latest_workbook(cache_dir: Path) -> Path | None:
    candidates = [path for path in cache_dir.glob("ETF_Flows_*.xlsx") if path.is_file()]
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def _fresh(path: Path) -> bool:
    return max(0.0, time.time() - path.stat().st_mtime) < CACHE_MAX_AGE_DAYS * 86400


def _cookie_header() -> str | None:
    cookie_path = os.getenv("WGC_COOKIES_PATH")
    if not cookie_path:
        return None
    try:
        cookies = json.loads(Path(cookie_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(cookies, list):
        return None
    pairs = [f"{item['name']}={item['value']}" for item in cookies if isinstance(item, dict) and item.get("name") and item.get("value")]
    return "; ".join(pairs) or None


def _request(url: str, *, referer: str | None = None) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    if referer:
        headers["Referer"] = referer
    cookie = _cookie_header()
    if cookie:
        headers["Cookie"] = cookie
    try:
        with urlopen(Request(url, headers=headers), timeout=60) as response:
            return response.read()
    except HTTPError as exc:
        raise WGCError(f"WGC request failed (HTTP {exc.code})") from exc
    except URLError as exc:
        raise WGCError(f"WGC is unavailable: {exc.reason}") from exc


def _find_download_url(page: bytes) -> str:
    text = html.unescape(page.decode("utf-8", errors="replace"))
    pattern = r"href=[\"']([^\"']*?/download/file/[^\"']*(?:etf[^\"']*flow|flow[^\"']*etf)[^\"']*\.xlsx?[^\"']*)[\"']"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        raise WGCError("WGC ETF workbook link was not found; authentication or page structure may have changed")
    return urljoin(WGC_PAGE_URL, unquote(match.group(1)))


def _filename(url: str) -> str:
    name = unquote(url.rsplit("/", 1)[-1].split("?", 1)[0])
    return name if name.lower().endswith((".xlsx", ".xls")) else "ETF_Flows_download.xlsx"


def fetch_wgc_workbook(cache_dir: Path) -> Path | None:
    """Download the current WGC ETF workbook, using a seven-day cache fallback."""
    global LAST_FETCH_USED_CACHE, LAST_FETCH_STALE
    LAST_FETCH_USED_CACHE = False
    LAST_FETCH_STALE = False
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = _latest_workbook(cache_dir)
    if cached is not None and _fresh(cached):
        return cached
    try:
        page = _request(WGC_PAGE_URL)
        download_url = _find_download_url(page)
        content = _request(download_url, referer=WGC_PAGE_URL)
        if not content.startswith(b"PK\x03\x04"):
            raise WGCError("WGC response is not a valid XLSX workbook")
        path = cache_dir / _filename(download_url)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(content)
        temporary.replace(path)
        return path
    except WGCError:
        if cached is not None and _fresh(cached):
            LAST_FETCH_USED_CACHE = True
            return cached
        LAST_FETCH_STALE = cached is not None
        return None
