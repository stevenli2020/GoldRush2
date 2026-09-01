"""Reusable Yahoo Finance daily-series collection with a local seven-day cache."""

from __future__ import annotations

import json
import math
import time
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors.base import BaseCollector, SourceUnavailableError

CACHE_MAX_AGE_DAYS = 7
LAST_FETCH_USED_CACHE = False


class YahooError(RuntimeError):
    """Base error for Yahoo Finance collection failures."""


class YahooDataError(YahooError):
    """Raised when Yahoo returns no usable observations."""


def _cache_is_fresh(path: Path) -> bool:
    return max(0.0, time.time() - path.stat().st_mtime) < CACHE_MAX_AGE_DAYS * 86400


def _load_cache(cache_path: Path) -> list[dict[str, str | float]]:
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        rows = payload["observations"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise YahooDataError(f"Cannot read cached Yahoo response: {cache_path}") from exc
    if not isinstance(rows, list):
        raise YahooDataError("Yahoo cache observations are not a list")
    return rows


def _write_cache(cache_path: Path, observations: list[dict[str, str | float]]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cached_at": date.today().isoformat(), "observations": observations}
    temporary = cache_path.with_suffix(cache_path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(cache_path)


def _download(symbol: str, *, start_date: str | None = None, period: str = "10y") -> list[dict[str, str | float]]:
    try:
        import yfinance as yf

        # Ten years comfortably covers the longest 756-observation lookback
        # while avoiding the much larger, timeout-prone full-history payload.
        parameters: dict[str, Any] = {"interval": "1d", "auto_adjust": False, "progress": False, "threads": False, "timeout": 30}
        if start_date is None:
            parameters["period"] = period
        else:
            parameters["start"] = start_date
        frame = yf.download(symbol, **parameters)
    except Exception as exc:
        raise YahooError(f"Yahoo Finance request failed for {symbol}: {exc}") from exc
    if frame is None or frame.empty:
        raise YahooDataError(f"Yahoo Finance returned no data for {symbol}")
    candidates: list[tuple[date, float, float]] = []
    for index, row in frame.iterrows():
        try:
            observation_date = index.date() if hasattr(index, "date") else date.fromisoformat(str(index)[:10])
            close_raw = row["Close"]
            volume_raw = row["Volume"]
            if hasattr(close_raw, "iloc"):
                close_raw = close_raw.iloc[0]
            if hasattr(volume_raw, "iloc"):
                volume_raw = volume_raw.iloc[0]
            close = float(close_raw)
            volume = float(volume_raw)
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if observation_date >= date.today() or not math.isfinite(close):
            continue
        candidates.append((observation_date, close, volume))
    # Some Yahoo index symbols (including DX-Y.NYB) publish Volume=0 for
    # every row. In that case volume cannot identify a finalized bar, so the
    # explicit current-date exclusion above is the available finalization rule.
    has_positive_volume = any(volume > 0 for _, _, volume in candidates)
    observations = [
        {"date": observation_date.isoformat(), "value": close}
        for observation_date, close, volume in candidates
        if not has_positive_volume or volume > 0
    ]
    if not observations:
        raise YahooDataError(f"Yahoo Finance returned no finalized observations for {symbol}")
    return observations


def fetch_yahoo_series(symbol: str, cache_path: Path) -> list[dict[str, str | float]]:
    """Fetch a finalized daily Yahoo series, preserving a fresh cache on failure."""
    global LAST_FETCH_USED_CACHE
    LAST_FETCH_USED_CACHE = False
    try:
        observations = _download(symbol)
        _write_cache(cache_path, observations)
        return observations
    except YahooError as exc:
        if cache_path.exists() and _cache_is_fresh(cache_path):
            LAST_FETCH_USED_CACHE = True
            return _load_cache(cache_path)
        if cache_path.exists():
            raise YahooError(f"STALE DATA — Yahoo cache is 7 days old or older: {exc}") from exc
        raise


class YahooCollector(BaseCollector):
    """Normalized-cache adapter for a finalized Yahoo daily series."""

    def __init__(self, cache_dir: Path, symbol: str, raw_path: Path, *, force: bool = False, always_refresh: bool = False) -> None:
        super().__init__(cache_dir, force=force, always_refresh=always_refresh)
        self.symbol = symbol
        self.raw_path = Path(raw_path)

    def fetch_latest_observation_date(self) -> str:
        try:
            observations = _download(self.symbol, period="5d")
        except YahooError as exc:
            raise SourceUnavailableError(str(exc)) from exc
        return max(str(row["date"]) for row in observations)

    def download_full(self) -> list[dict[str, str | float]]:
        try:
            return fetch_yahoo_series(self.symbol, self.raw_path)
        except YahooError as exc:
            raise SourceUnavailableError(str(exc)) from exc

    def download_incremental(self, since_date: str) -> list[dict[str, str | float]]:
        try:
            incoming = _download(self.symbol, start_date=since_date)
            prior = _load_cache(self.raw_path) if self.raw_path.exists() else []
            _write_cache(self.raw_path, self._deduplicate([*prior, *incoming]))
            return incoming
        except YahooError as exc:
            raise SourceUnavailableError(str(exc)) from exc
