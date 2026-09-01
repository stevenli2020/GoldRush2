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
WGC_OFFICIAL_CHANGES_PAGE_URL = "https://www.gold.org/goldhub/data/gold-reserves-by-country"
WGC_OFFICIAL_HOLDINGS_PAGE_URL = WGC_OFFICIAL_CHANGES_PAGE_URL
WGC_GDT_PAGE_URL = "https://www.gold.org/goldhub/data/gold-demand-by-country"
CACHE_MAX_AGE_DAYS = 7
USER_AGENT = "Mozilla/5.0 GoldRush2 WGC downloader"
LAST_FETCH_USED_CACHE = False
LAST_FETCH_STALE = False


class WGCError(RuntimeError):
    """Raised when the WGC workbook cannot be downloaded or validated."""


def _latest_workbook(cache_dir: Path, pattern: str | tuple[str, ...] = "ETF_Flows_*.xlsx") -> Path | None:
    patterns = (pattern,) if isinstance(pattern, str) else pattern
    candidates = [path for current_pattern in patterns for path in cache_dir.glob(current_pattern) if path.is_file()]
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


def _find_download_url(page: bytes, *, page_url: str = WGC_PAGE_URL, workbook_pattern: str = r"(?:etf[^\"']*flow|flow[^\"']*etf)") -> str:
    text = html.unescape(page.decode("utf-8", errors="replace"))
    pattern = rf"""href="([^"]*?/download/file/[^"]*{workbook_pattern}[^"]*\.xlsx?[^\"]*)"|href='([^']*?/download/file/[^']*{workbook_pattern}[^']*\.xlsx?[^']*)'"""
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        raise WGCError("WGC workbook link was not found; authentication or page structure may have changed")
    return urljoin(page_url, unquote((match.group(1) or match.group(2)).strip()))


def _filename(url: str) -> str:
    name = unquote(url.rsplit("/", 1)[-1].split("?", 1)[0])
    return name if name.lower().endswith((".xlsx", ".xls")) else "ETF_Flows_download.xlsx"


def _fetch_workbook(cache_dir: Path, *, page_url: str, cache_pattern: str, link_pattern: str) -> Path | None:
    global LAST_FETCH_USED_CACHE, LAST_FETCH_STALE
    LAST_FETCH_USED_CACHE = False
    LAST_FETCH_STALE = False
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = _latest_workbook(cache_dir, cache_pattern)
    if cached is not None and _fresh(cached):
        return cached
    try:
        page = _request(page_url)
        download_url = _find_download_url(page, page_url=page_url, workbook_pattern=link_pattern)
        content = _request(download_url, referer=page_url)
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


def fetch_wgc_workbook(cache_dir: Path) -> Path | None:
    """Download the current WGC ETF workbook, using a seven-day cache fallback."""
    return _fetch_workbook(cache_dir, page_url=WGC_PAGE_URL, cache_pattern="ETF_Flows_*.xlsx", link_pattern=r"(?:etf[^\"']*flow|flow[^\"']*etf)")


def fetch_wgc_official_changes(cache_dir: Path) -> Path | None:
    """Download the current WGC/IMF IFS official-changes workbook."""
    return _fetch_workbook(cache_dir, page_url=WGC_OFFICIAL_CHANGES_PAGE_URL, cache_pattern="Changes_*_IFS.xlsx", link_pattern="changes")


def fetch_wgc_official_holdings(cache_dir: Path) -> Path | None:
    """Download the current WGC official-holdings workbook."""
    return _fetch_workbook(cache_dir, page_url=WGC_OFFICIAL_HOLDINGS_PAGE_URL, cache_pattern="*official*holdings*.xlsx", link_pattern="official")


def fetch_wgc_gdt_workbook(cache_dir: Path) -> Path | None:
    """Download the current WGC Gold Demand Trends workbook."""
    return _fetch_workbook(
        cache_dir,
        page_url=WGC_GDT_PAGE_URL,
        cache_pattern=("GDT*.xlsx", "Gold_Demand_Trends_*.xlsx"),
        link_pattern=r"(?:gdt|gold[_-]?demand|demand[_-]?trends)",
    )
