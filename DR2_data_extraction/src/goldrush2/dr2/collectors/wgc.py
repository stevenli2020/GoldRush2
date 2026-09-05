"""Collection of the World Gold Council ETF flows workbook."""

from __future__ import annotations

import html
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin
from urllib.request import Request, urlopen

from goldrush2.dr2.collectors.base import BaseCollector, SourceUnavailableError

WGC_PAGE_URL = "https://www.gold.org/goldhub/data/gold-etfs-holdings-and-flows"
WGC_OFFICIAL_CHANGES_PAGE_URL = "https://www.gold.org/goldhub/data/gold-reserves-by-country"
WGC_OFFICIAL_HOLDINGS_PAGE_URL = WGC_OFFICIAL_CHANGES_PAGE_URL
WGC_GDT_PAGE_URL = "https://www.gold.org/goldhub/data/gold-demand-by-country"
WGC_PREMIUMS_PAGE_URL = "https://www.gold.org/goldhub/data/gold-premium"
WGC_ABOVE_GROUND_PAGE_URL = "https://www.gold.org/goldhub/data/how-much-gold"
CACHE_MAX_AGE_DAYS = 7
USER_AGENT = "Mozilla/5.0 GoldRush2 WGC downloader"
LAST_FETCH_USED_CACHE = False
LAST_FETCH_STALE = False
LAST_FETCH_ERROR: str | None = None


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
    # Group alternatives so every workbook-name variant remains constrained
    # by the surrounding download URL pattern.
    workbook_token = rf"(?:{workbook_pattern})"
    pattern = rf'''href="([^"]*?/download/file/[^"]*{workbook_token}[^"]*\.xlsx?[^"]*)"|href='([^']*?/download/file/[^']*{workbook_token}[^']*\.xlsx?[^']*)' '''.strip()
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        raise WGCError("WGC workbook link was not found; authentication or page structure may have changed")
    return urljoin(page_url, unquote((match.group(1) or match.group(2)).strip()))


def _filename(url: str) -> str:
    name = unquote(url.rsplit("/", 1)[-1].split("?", 1)[0])
    return name if name.lower().endswith((".xlsx", ".xls")) else "ETF_Flows_download.xlsx"


def _fetch_workbook(cache_dir: Path, *, page_url: str, cache_pattern: str, link_pattern: str, force: bool = False) -> Path | None:
    global LAST_FETCH_USED_CACHE, LAST_FETCH_STALE, LAST_FETCH_ERROR
    LAST_FETCH_USED_CACHE = False
    LAST_FETCH_STALE = False
    LAST_FETCH_ERROR = None
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = _latest_workbook(cache_dir, cache_pattern)
    if cached is not None and _fresh(cached) and not force:
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
    except WGCError as exc:
        LAST_FETCH_ERROR = str(exc)
        if cached is not None and (_fresh(cached) or force):
            # A force refresh still degrades safely to the last workbook when
            # WGC authentication or the download endpoint is unavailable.
            # The stale flag lets callers surface that provenance to users.
            LAST_FETCH_USED_CACHE = True
            LAST_FETCH_STALE = not _fresh(cached)
            return cached
        LAST_FETCH_STALE = cached is not None
        return None


def fetch_wgc_workbook(cache_dir: Path, *, force: bool = False) -> Path | None:
    """Download the current WGC ETF workbook, using a seven-day cache fallback."""
    return _fetch_workbook(cache_dir, page_url=WGC_PAGE_URL, cache_pattern="ETF_Flows_*.xlsx", link_pattern=r"(?:etf[^\"']*flow|flow[^\"']*etf)", force=force)


def fetch_wgc_official_changes(cache_dir: Path, *, force: bool = False) -> Path | None:
    """Download the current WGC/IMF IFS official-changes workbook."""
    return _fetch_workbook(cache_dir, page_url=WGC_OFFICIAL_CHANGES_PAGE_URL, cache_pattern="Changes_*_IFS.xlsx", link_pattern="changes", force=force)


def fetch_wgc_official_holdings(cache_dir: Path, *, force: bool = False) -> Path | None:
    """Download the current WGC official-holdings workbook."""
    return _fetch_workbook(cache_dir, page_url=WGC_OFFICIAL_HOLDINGS_PAGE_URL, cache_pattern="*official*holdings*.xlsx", link_pattern="official", force=force)


def fetch_wgc_gdt_workbook(cache_dir: Path, *, force: bool = False) -> Path | None:
    """Download the current WGC Gold Demand Trends workbook."""
    return _fetch_workbook(
        cache_dir,
        page_url=WGC_GDT_PAGE_URL,
        cache_pattern=("GDT*.xlsx", "Gold_Demand_Trends_*.xlsx"),
        link_pattern=r"(?:gdt|gold[_-]?demand|demand[_-]?trends)",
        force=force,
    )


def fetch_wgc_gold_premiums(cache_dir: Path, *, force: bool = False) -> Path | None:
    """Download WGC's published China premium/discount workbook."""
    return _fetch_workbook(
        cache_dir,
        page_url=WGC_PREMIUMS_PAGE_URL,
        cache_pattern="gold-premiums.xlsx",
        link_pattern=r"gold-premiums",
        force=force,
    )


def fetch_wgc_above_ground_stocks(cache_dir: Path, *, force: bool = False) -> Path | None:
    """Download WGC's annual above-ground gold stocks workbook."""
    return _fetch_workbook(
        cache_dir,
        page_url=WGC_ABOVE_GROUND_PAGE_URL,
        cache_pattern=("Above-ground_stocks_*.xlsx", "above-ground-gold-stocks*.xlsx"),
        link_pattern=r"above-ground-gold-stocks|above-ground[_-]?stocks",
        force=force,
    )


class WGCWorkbookCollector(BaseCollector):
    """Normalized-cache adapter for a WGC workbook and variable parser."""

    def __init__(self, cache_dir: Path, raw_dir: Path, fetcher: Callable[..., Path | None], normalizer: Callable[[Path], list[dict[str, Any]]], *, force: bool = False, always_refresh: bool = False) -> None:
        super().__init__(cache_dir, force=force, always_refresh=always_refresh)
        self.raw_dir = Path(raw_dir)
        self.fetcher = fetcher
        self.normalizer = normalizer
        self._downloaded_records: list[dict[str, Any]] | None = None

    def _download_and_normalize(self) -> list[dict[str, Any]]:
        # WGC publishes the observation date inside the workbook, so checking
        # for a newer source observation requires fetching the current file.
        workbook = self.fetcher(self.raw_dir, force=True)
        if workbook is None:
            if LAST_FETCH_ERROR:
                self._log(f"WGC download failed: {LAST_FETCH_ERROR}", 1)
            raise SourceUnavailableError("WGC workbook is unavailable")
        try:
            records = self.normalizer(workbook)
        except (OSError, ValueError, KeyError) as exc:
            raise SourceUnavailableError(f"WGC workbook parsing failed: {exc}") from exc
        if LAST_FETCH_USED_CACHE:
            detail = f" ({LAST_FETCH_ERROR})" if LAST_FETCH_ERROR else ""
            self.warning = f"SOURCE UNAVAILABLE — cached workbook used{detail}"
        return records

    def fetch_latest_observation_date(self) -> str:
        self._downloaded_records = self._download_and_normalize()
        if not self._downloaded_records:
            raise SourceUnavailableError("WGC workbook contains no normalized observations")
        return max(str(row["date"]) for row in self._downloaded_records)

    def download_full(self) -> list[dict[str, Any]]:
        if self._downloaded_records is not None:
            records, self._downloaded_records = self._downloaded_records, None
            return records
        return self._download_and_normalize()
