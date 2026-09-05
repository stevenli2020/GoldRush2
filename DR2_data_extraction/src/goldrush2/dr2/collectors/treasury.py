"""Paginated collection from the public U.S. Treasury Fiscal Data API."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from goldrush2.dr2.collectors.base import BaseCollector, SourceUnavailableError

CACHE_MAX_AGE_DAYS = 7


class TreasuryError(RuntimeError):
    """Raised when Treasury data cannot be fetched or parsed."""


def _fresh(path: Path) -> bool:
    return max(0.0, time.time() - path.stat().st_mtime) < CACHE_MAX_AGE_DAYS * 86400


def _read_cache(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TreasuryError(f"Cannot read Treasury cache: {path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("pages"), list):
        raise TreasuryError("Treasury cache has no pages list")
    payload["source_status"] = "CACHED"
    return payload


def _write_cache(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _query(filters: dict, page: int) -> str:
    params = {"page[number]": page, "page[size]": 1000}
    for key, value in filters.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, separators=(",", ":"))
        params[key] = value
    return urlencode(params)


def fetch_treasury_table(endpoint: str, filters: dict, cache_path: Path) -> dict:
    """Fetch every page of a Treasury table and cache the raw JSON responses."""
    pages: list[dict] = []
    try:
        page_number = 1
        total_pages: int | None = None
        while total_pages is None or page_number <= total_pages:
            try:
                with urlopen(f"{endpoint}?{_query(filters, page_number)}", timeout=30) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise TreasuryError(f"Treasury request failed: {exc}") from exc
            if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
                raise TreasuryError("Treasury response has no data list")
            pages.append(payload)
            meta = payload.get("meta", {}).get("pagination", {})
            if not meta:
                # Fiscal Data responses currently expose pagination directly
                # under meta using the `total-pages` field.
                meta = payload.get("meta", {})
            try:
                page_count = meta.get("pages", meta.get("total-pages"))
                total_pages = int(page_count) if page_count is not None else page_number
            except (TypeError, ValueError):
                total_pages = page_number
            if not payload["data"] or page_number >= total_pages:
                break
            page_number += 1
    except TreasuryError as exc:
        if cache_path.exists() and _fresh(cache_path):
            cached = _read_cache(cache_path)
            cached["fallback_note"] = "SOURCE UNAVAILABLE — cached data used"
            return cached
        if cache_path.exists():
            raise TreasuryError(f"STALE DATA — Treasury cache is 7 days old or older: {exc}") from exc
        raise
    cached = {"cached_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "endpoint": endpoint, "filters": filters, "pages": pages, "source_status": "LIVE"}
    _write_cache(cache_path, cached)
    return cached


def flatten_data(payload: dict) -> list[dict]:
    """Flatten cached page envelopes into their ordered row records."""
    rows: list[dict] = []
    for page in payload.get("pages", []):
        rows.extend(row for row in page.get("data", []) if isinstance(row, dict))
    return rows


def fetch_latest_treasury_date(endpoint: str, filters: dict) -> str:
    """Read the newest record date using the API's one-page response."""
    query_filters = dict(filters)
    query_filters["sort"] = "-record_date"
    try:
        with urlopen(f"{endpoint}?{_query(query_filters, 1)}", timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TreasuryError(f"Treasury latest-date request failed: {exc}") from exc
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        raise TreasuryError("Treasury latest-date response has no data")
    record_date = rows[0].get("record_date")
    if not isinstance(record_date, str) or not record_date:
        raise TreasuryError("Treasury latest-date response has no record_date")
    return record_date


class TreasuryCollector(BaseCollector):
    """Normalized-cache adapter for one paginated Treasury table."""

    def __init__(
        self,
        cache_dir: Path,
        endpoint: str,
        filters: dict[str, Any],
        raw_path: Path,
        normalizer: Callable[[list[dict]], list[dict[str, Any]]],
        *,
        force: bool = False,
        always_refresh: bool = False,
    ) -> None:
        super().__init__(cache_dir, force=force, always_refresh=always_refresh)
        self.endpoint = endpoint
        self.filters = filters
        self.raw_path = Path(raw_path)
        self.normalizer = normalizer

    def fetch_latest_observation_date(self) -> str:
        try:
            return fetch_latest_treasury_date(self.endpoint, self.filters)
        except TreasuryError as exc:
            raise SourceUnavailableError(str(exc)) from exc

    def download_full(self) -> list[dict[str, Any]]:
        try:
            payload = fetch_treasury_table(self.endpoint, self.filters, self.raw_path)
            return self.normalizer(flatten_data(payload))
        except TreasuryError as exc:
            raise SourceUnavailableError(str(exc)) from exc
