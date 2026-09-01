"""Paginated collection from the public U.S. Treasury Fiscal Data API."""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

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
