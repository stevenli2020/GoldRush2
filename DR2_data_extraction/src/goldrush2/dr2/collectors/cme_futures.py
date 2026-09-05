"""Specific-contract CME Gold futures collection for L0-009."""

from __future__ import annotations

import math
from calendar import monthrange
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.dr2.collectors.base import BaseCollector, SourceUnavailableError
from goldrush2.dr2.collectors.fred import FredError, fetch_series, load_cached_series

MONTH_CODES = {1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M", 7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"}
ACTIVE_MONTHS = (2, 4, 6, 8, 10, 12)
SOFR_SERIES_ID = "SOFR"


class CmeFuturesError(RuntimeError):
    """Raised when a specific CME Gold contract cannot produce usable prices."""


def _month_end(year: int, month: int) -> date:
    return date(year, month, monthrange(year, month)[1])


def get_contract_symbol(year: int, month: int) -> str:
    """Return Yahoo Finance's specific COMEX Gold contract ticker."""
    if month not in MONTH_CODES:
        raise ValueError(f"Unsupported contract month: {month}")
    return f"GC{MONTH_CODES[month]}{year % 100:02d}.CMX"


def get_near_and_far_contracts(target_date: date | None = None) -> tuple[str, str, int]:
    """Select the next two active COMEX Gold delivery months."""
    target = target_date or date.today()
    candidates = [
        (year, month)
        for year in range(target.year, target.year + 3)
        for month in ACTIVE_MONTHS
        if _month_end(year, month) > target
    ]
    candidates.sort()
    if len(candidates) < 2:
        raise CmeFuturesError("Unable to select active COMEX Gold contract pair")
    near_year, near_month = candidates[0]
    far_year, far_month = candidates[1]
    days_between = (_month_end(far_year, far_month) - _month_end(near_year, near_month)).days
    return get_contract_symbol(near_year, near_month), get_contract_symbol(far_year, far_month), days_between


def _download_contract(symbol: str, *, period: str = "max") -> dict[str, float]:
    try:
        import yfinance as yf

        frame = yf.download(symbol, period=period, interval="1d", auto_adjust=False, progress=False, threads=False, timeout=30)
    except Exception as exc:
        raise CmeFuturesError(f"Yahoo Finance request failed for {symbol}: {exc}") from exc
    if frame is None or frame.empty:
        raise CmeFuturesError(f"Yahoo Finance returned no data for {symbol}")

    close = frame["Close"]
    if hasattr(close, "iloc") and getattr(close, "ndim", 1) > 1:
        close = close.iloc[:, 0]
    prices: dict[str, float] = {}
    for index, raw_value in close.items():
        try:
            observation_date = index.date() if hasattr(index, "date") else date.fromisoformat(str(index)[:10])
            value = float(raw_value)
        except (TypeError, ValueError, OverflowError):
            continue
        if observation_date >= date.today() or value <= 0 or not math.isfinite(value):
            continue
        prices[observation_date.isoformat()] = value
    if not prices:
        raise CmeFuturesError(f"Yahoo Finance returned no finalized prices for {symbol}")
    return prices


def align_contract_prices(near_prices: dict[str, float], far_prices: dict[str, float], *, near_contract: str, far_contract: str, days_between: int) -> list[dict[str, Any]]:
    """Inner-join finalized near and far contract settlements by date."""
    if days_between <= 0:
        raise ValueError("days_between must be positive")
    rows = [
        {
            "date": observation_date,
            "near": near_prices[observation_date],
            "far": far_prices[observation_date],
            "near_contract": near_contract,
            "far_contract": far_contract,
            "days_between": days_between,
        }
        for observation_date in sorted(set(near_prices) & set(far_prices))
    ]
    if not rows:
        raise CmeFuturesError("The selected CME Gold contracts have no aligned observations")
    return rows


def apply_sofr(pair_rows: list[dict[str, Any]], sofr_rows: list[dict[str, str | float]]) -> list[dict[str, Any]]:
    """Attach SOFR, carrying its latest prior value across non-publication days."""
    ordered_sofr = sorted(sofr_rows, key=lambda row: str(row["date"]))
    result: list[dict[str, Any]] = []
    sofr_index = 0
    latest_sofr: dict[str, str | float] | None = None
    for row in pair_rows:
        while sofr_index < len(ordered_sofr) and str(ordered_sofr[sofr_index]["date"]) <= str(row["date"]):
            latest_sofr = ordered_sofr[sofr_index]
            sofr_index += 1
        if latest_sofr is None:
            continue
        near, far, days = float(row["near"]), float(row["far"]), int(row["days_between"])
        forward_rate = ((far / near) ** (365.0 / days) - 1.0) * 100.0
        sofr = float(latest_sofr["value"])
        result.append(
            {
                **row,
                "sofr": sofr,
                "sofr_date": latest_sofr["date"],
                "sofr_is_filled": latest_sofr["date"] != row["date"],
                "forward_rate": round(forward_rate, 8),
                "value": round(sofr - forward_rate, 8),
            }
        )
    if not result:
        raise CmeFuturesError("No CME Gold observations could be aligned with SOFR")
    return result


class CMEFuturesCollector(BaseCollector):
    """Collect an aligned specific-contract CME Gold forward/lease proxy series."""

    handles_vars = ["L0-009"]

    def __init__(self, cache_dir: Path, raw_path: Path, sofr_raw_path: Path, **kwargs: Any) -> None:
        super().__init__(cache_dir, **kwargs)
        self._l0_009_cache_path = Path(cache_dir) / "l0_009.json"
        self.raw_path = Path(raw_path)
        self.sofr_raw_path = Path(sofr_raw_path)

    @property
    def cache_path(self) -> Path:
        return self._l0_009_cache_path

    def fetch_latest_observation_date(self) -> str:
        near, _far, _days = get_near_and_far_contracts()
        return max(_download_contract(near, period="5d"))

    def _sofr_history(self) -> list[dict[str, str | float]]:
        try:
            return fetch_series(SOFR_SERIES_ID, raw_path=self.sofr_raw_path)
        except FredError as exc:
            if not self.sofr_raw_path.exists():
                raise CmeFuturesError(f"SOFR is unavailable: {exc}") from exc
            try:
                return load_cached_series(self.sofr_raw_path)
            except FredError as cache_exc:
                raise CmeFuturesError(f"SOFR and its cache are unavailable: {cache_exc}") from cache_exc

    def download_full(self) -> list[dict[str, Any]]:
        try:
            near, far, days_between = get_near_and_far_contracts()
            near_prices = _download_contract(near)
            far_prices = _download_contract(far)
            pair_rows = align_contract_prices(near_prices, far_prices, near_contract=near, far_contract=far, days_between=days_between)
            self._atomic_json(self.raw_path, {"near_contract": near, "far_contract": far, "days_between": days_between, "observations": pair_rows})
            rows = apply_sofr(pair_rows, self._sofr_history())
            self._log(f"CME Gold pair downloaded: near={near} far={far} aligned={len(rows)}", 1)
            return rows
        except CmeFuturesError as exc:
            raise SourceUnavailableError(str(exc)) from exc

    def download_incremental(self, since_date: str) -> list[dict[str, Any]]:
        raise NotImplementedError
