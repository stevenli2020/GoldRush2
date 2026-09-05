"""DR2 extractor for L7-001: Federal Reserve total assets."""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.dr2.collectors.fred import FredError, fetch_series, load_cached_series

VARIABLE_ID = "L7-001"
SERIES_ID = "WALCL"
DATA_FREQUENCY = "Weekly"
SOURCE_NAME = "FRED WALCL - Federal Reserve Total Assets"
SOURCE_URL = "https://fred.stlouisfed.org/series/WALCL"
HORIZON_LOOKBACKS = {"1-5d": 5, "1-3m": 63, "1-3y": 252, "3-10y": 756}
CACHE_MAX_AGE_DAYS = 7
from goldrush2.paths import DR2_ROOT as PROJECT_ROOT
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "fred" / f"{SERIES_ID}.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / f"{VARIABLE_ID}.json"


def _empty_data() -> dict[str, None]:
    return {"current_value": None, "current_date": None, "comparison_value": None, "comparison_date": None, "change_absolute": None, "change_pct": None}


def _degraded(summary: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"signal": 0, "confidence": 0, "evidence": {"data": data or _empty_data(), "summary": summary}}


def _valid(current: dict[str, str | float], comparison: dict[str, str | float], *, cached: bool) -> dict[str, Any]:
    current_value, comparison_value = float(current["value"]), float(comparison["value"])
    change = round(current_value - comparison_value, 10)
    change_pct = round(change / comparison_value * 100, 10) if comparison_value else None
    if change > 0:
        signal, summary = 1, f"Fed balance sheet expanded by {change_pct or 0:.2f}%, bullish for gold."
    elif change < 0:
        signal, summary = -1, f"Fed balance sheet contracted by {abs(change_pct or 0):.2f}%, bearish for gold."
    else:
        signal, summary = 0, "Fed balance sheet was unchanged, neutral for gold."
    if cached:
        summary += " SOURCE UNAVAILABLE — cached data used."
    return {"signal": signal, "confidence": 1, "evidence": {"data": {"current_value": current_value, "current_date": current["date"], "comparison_value": comparison_value, "comparison_date": comparison["date"], "change_absolute": change, "change_pct": change_pct}, "summary": summary}}


def build_output(observations: list[dict[str, str | float]], *, cached: bool = False, as_of_date: str | None = None) -> dict[str, Any]:
    """Build the four-horizon WALCL result from valid weekly observations."""
    ordered = sorted(observations, key=lambda item: str(item["date"]))
    current = ordered[-1] if ordered else None
    horizons: dict[str, Any] = {}
    for horizon, lookback in HORIZON_LOOKBACKS.items():
        if current is None or len(ordered) < lookback:
            data = _empty_data()
            if current is not None:
                data["current_value"], data["current_date"] = float(current["value"]), str(current["date"])
            summary = f"MISSING DATA — {lookback} valid weekly observations are required; {len(ordered)} are available."
            if cached:
                summary += " SOURCE UNAVAILABLE — cached data used."
            horizons[horizon] = _degraded(summary, data)
        else:
            horizons[horizon] = _valid(current, ordered[-lookback], cached=cached)
    return {"variable_id": VARIABLE_ID, "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_frequency": DATA_FREQUENCY, "observation_date": str(current["date"]) if current else None, "horizons": horizons}


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build a zero-confidence result for a collection failure."""
    return {"variable_id": VARIABLE_ID, "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_frequency": DATA_FREQUENCY, "observation_date": None, "horizons": {h: _degraded(summary) for h in HORIZON_LOOKBACKS}}


def _fresh(path: Path) -> bool:
    return max(0.0, time.time() - path.stat().st_mtime) < CACHE_MAX_AGE_DAYS * 86400


def run(*, raw_path: Path = RAW_PATH, output_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Fetch WALCL, apply cache rules, and write current output."""
    try:
        output = build_output(fetch_series(SERIES_ID, raw_path=raw_path))
    except FredError as exc:
        if raw_path.exists() and _fresh(raw_path):
            try:
                output = build_output(load_cached_series(raw_path), cached=True)
            except FredError as cache_exc:
                output = build_degraded_output(f"EXTRACTION FAILED — {cache_exc}")
        elif raw_path.exists():
            output = build_degraded_output(f"STALE DATA — FRED unavailable and cached data is 7 days old or older: {exc}")
        else:
            output = build_degraded_output(f"SOURCE UNAVAILABLE — {exc}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
