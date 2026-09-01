"""DR2 extractor for L7-005: Treasury repo funding stress."""

from __future__ import annotations

import json
import math
import time
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors.fred import FredError, fetch_series, load_cached_series

VARIABLE_ID = "L7-005"
SOFR_SERIES_ID = "SOFR"
EFFR_SERIES_ID = "EFFR"
DATA_FREQUENCY = "Daily"
SOURCE_NAME = "FRED SOFR - EFFR spread (repo funding stress)"
SOURCE_URL = "https://fred.stlouisfed.org/series/SOFR"
HORIZON_LOOKBACKS = {"1-5d": 5, "1-3m": 63, "1-3y": 252, "3-10y": 756}
CACHE_MAX_AGE_DAYS = 7
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SOFR_RAW_PATH = PROJECT_ROOT / "data" / "raw" / "fred" / "SOFR.json"
EFFR_RAW_PATH = PROJECT_ROOT / "data" / "raw" / "fred" / "EFFR.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / f"{VARIABLE_ID}.json"


def _empty_data() -> dict[str, Any]:
    return {
        "current_value": None,
        "current_date": None,
        "comparison_value": None,
        "comparison_date": None,
        "change_basis_points": None,
        "change_pct": None,
        "sofr": None,
        "effr": None,
        "comparison_sofr": None,
        "comparison_effr": None,
    }


def _degraded(summary: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "signal": 0,
        "confidence": 0,
        "evidence": {"data": data or _empty_data(), "summary": summary},
    }


def align_spread_observations(
    sofr_observations: list[dict[str, str | float]],
    effr_observations: list[dict[str, str | float]],
) -> list[dict[str, Any]]:
    """Inner-join SOFR and EFFR by date and calculate the spread in basis points."""
    sofr = {
        str(observation["date"]): float(observation["value"])
        for observation in sofr_observations
        if _finite(observation.get("value"))
    }
    effr = {
        str(observation["date"]): float(observation["value"])
        for observation in effr_observations
        if _finite(observation.get("value"))
    }
    return [
        {"date": observation_date, "value": round((sofr[observation_date] - effr[observation_date]) * 100, 10), "sofr": sofr[observation_date], "effr": effr[observation_date]}
        for observation_date in sorted(set(sofr) & set(effr))
    ]


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _valid(current: dict[str, Any], comparison: dict[str, Any], *, cached: bool) -> dict[str, Any]:
    current_value = float(current["value"])
    comparison_value = float(comparison["value"])
    change = round(current_value - comparison_value, 10)
    change_pct = round(change / comparison_value * 100, 10) if comparison_value else None
    if change > 0:
        signal, summary = 1, f"SOFR-EFFR spread rose by {change:.2f}bp, indicating increased funding stress, bullish for gold."
    elif change < 0:
        signal, summary = -1, f"SOFR-EFFR spread fell by {abs(change):.2f}bp, indicating reduced funding stress, bearish for gold."
    else:
        signal, summary = 0, "SOFR-EFFR spread was unchanged, indicating no change in funding stress."
    if cached:
        summary += " SOURCE UNAVAILABLE — cached data used."
    current_sofr = current.get("sofr")
    current_effr = current.get("effr")
    comparison_sofr = comparison.get("sofr")
    comparison_effr = comparison.get("effr")
    data = {
        "current_value": current_value,
        "current_date": str(current["date"]),
        "comparison_value": comparison_value,
        "comparison_date": str(comparison["date"]),
        "change_basis_points": change,
        "change_pct": change_pct,
        "sofr": float(current_sofr) if _finite(current_sofr) else None,
        "effr": float(current_effr) if _finite(current_effr) else None,
        "comparison_sofr": float(comparison_sofr) if _finite(comparison_sofr) else None,
        "comparison_effr": float(comparison_effr) if _finite(comparison_effr) else None,
    }
    return {"signal": signal, "confidence": 1, "evidence": {"data": data, "summary": summary}}


def build_output(
    observations: list[dict[str, Any]],
    *,
    cached: bool = False,
    as_of_date: str | None = None,
) -> dict[str, Any]:
    """Build the four-horizon spread result from aligned observations."""
    ordered = sorted(observations, key=lambda item: str(item["date"]))
    current = ordered[-1] if ordered else None
    horizons: dict[str, Any] = {}
    for horizon, lookback in HORIZON_LOOKBACKS.items():
        if current is None or len(ordered) < lookback:
            data = _empty_data()
            if current is not None:
                data.update({"current_value": float(current["value"]), "current_date": str(current["date"]), "sofr": float(current["sofr"]) if _finite(current.get("sofr")) else None, "effr": float(current["effr"]) if _finite(current.get("effr")) else None})
            summary = f"MISSING DATA — {lookback} aligned SOFR/EFFR observations are required; {len(ordered)} are available."
            if cached:
                summary += " SOURCE UNAVAILABLE — cached data used."
            horizons[horizon] = _degraded(summary, data)
        else:
            horizons[horizon] = _valid(current, ordered[-lookback], cached=cached)
    return {
        "variable_id": VARIABLE_ID,
        "as_of_date": as_of_date or date.today().isoformat(),
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "data_frequency": DATA_FREQUENCY,
        "observation_date": str(current["date"]) if current else None,
        "horizons": horizons,
    }


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build a zero-confidence result when either FRED dependency is unavailable."""
    return {
        "variable_id": VARIABLE_ID,
        "as_of_date": as_of_date or date.today().isoformat(),
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "data_frequency": DATA_FREQUENCY,
        "observation_date": None,
        "horizons": {horizon: _degraded(summary) for horizon in HORIZON_LOOKBACKS},
    }


def _cache_is_fresh(path: Path) -> bool:
    return max(0.0, time.time() - path.stat().st_mtime) < CACHE_MAX_AGE_DAYS * 86400


def _load_dependency(series_id: str, raw_path: Path) -> tuple[list[dict[str, str | float]], bool]:
    """Fetch one FRED dependency, falling back to a fresh cache when needed."""
    try:
        return fetch_series(series_id, raw_path=raw_path), False
    except FredError as exc:
        if raw_path.exists() and _cache_is_fresh(raw_path):
            try:
                return load_cached_series(raw_path), True
            except FredError as cache_exc:
                raise FredError(f"{series_id} cache is unreadable: {cache_exc}") from cache_exc
        if raw_path.exists():
            raise FredError(f"{series_id} cache is stale (7 days or older): {exc}") from exc
        raise FredError(f"{series_id} unavailable and no cache exists: {exc}") from exc


def run(
    *,
    output_path: Path = OUTPUT_PATH,
    sofr_raw_path: Path = SOFR_RAW_PATH,
    effr_raw_path: Path = EFFR_RAW_PATH,
) -> dict[str, Any]:
    """Fetch SOFR and EFFR, apply cache rules, and write current output."""
    try:
        sofr, sofr_cached = _load_dependency(SOFR_SERIES_ID, sofr_raw_path)
        effr, effr_cached = _load_dependency(EFFR_SERIES_ID, effr_raw_path)
        output = build_output(align_spread_observations(sofr, effr), cached=sofr_cached or effr_cached)
    except FredError as exc:
        message = str(exc)
        if "stale" in message.lower():
            summary = f"STALE DATA — {message}"
        else:
            summary = f"SOURCE UNAVAILABLE — {message}"
        output = build_degraded_output(summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
