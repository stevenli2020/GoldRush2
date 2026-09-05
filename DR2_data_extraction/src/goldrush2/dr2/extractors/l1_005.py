"""DR2 extractor for L1-005: 10Y Treasury term premium."""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.dr2.collectors.fred import FredError, fetch_series, load_cached_series

SERIES_ID = "THREEFFTP10"
SOURCE_NAME = "FRED THREEFFTP10 - 10-Year Treasury Term Premium"
SOURCE_URL = "https://fred.stlouisfed.org/series/THREEFFTP10"
DATA_FREQUENCY = "Monthly"
CACHE_MAX_AGE_DAYS = 7
HORIZON_LOOKBACKS: dict[str, int | None] = {
    "1-5d": None,
    "1-3m": 3,
    "1-3y": 12,
    "3-10y": 36,
}

from goldrush2.paths import DR2_ROOT as PROJECT_ROOT
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "fred" / f"{SERIES_ID}.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / "L1-005.json"


def _empty_evidence_data() -> dict[str, None]:
    return {
        "current_value": None,
        "current_date": None,
        "comparison_value": None,
        "comparison_date": None,
        "change_percentage_points": None,
    }


def _degraded_horizon(summary: str) -> dict[str, Any]:
    return {
        "signal": 0,
        "confidence": 0,
        "evidence": {"data": _empty_evidence_data(), "summary": summary},
    }


def _inapplicable_horizon() -> dict[str, Any]:
    return {
        "signal": 0,
        "confidence": 1,
        "evidence": {
            "data": _empty_evidence_data(),
            "summary": "1-5 day horizon is not applicable for monthly THREEFFTP10 data.",
        },
    }


def _valid_horizon(
    current: dict[str, str | float],
    comparison: dict[str, str | float],
    *,
    cached: bool,
) -> dict[str, Any]:
    current_value = float(current["value"])
    comparison_value = float(comparison["value"])
    change = round(current_value - comparison_value, 10)
    if change < 0:
        signal = 1
        summary = (
            f"The 10Y term premium fell by {abs(change):.2f} percentage points, "
            "bullish for gold."
        )
    elif change > 0:
        signal = -1
        summary = (
            f"The 10Y term premium rose by {change:.2f} percentage points, "
            "bearish for gold."
        )
    else:
        signal = 0
        summary = "The 10Y term premium was unchanged, neutral for gold."
    if cached:
        summary += " SOURCE UNAVAILABLE — cached data used."
    return {
        "signal": signal,
        "confidence": 1,
        "evidence": {
            "data": {
                "current_value": current_value,
                "current_date": current["date"],
                "comparison_value": comparison_value,
                "comparison_date": comparison["date"],
                "change_percentage_points": change,
            },
            "summary": summary,
        },
    }


def build_output(
    observations: list[dict[str, str | float]],
    *,
    cached: bool = False,
    as_of_date: str | None = None,
) -> dict[str, Any]:
    """Build the complete L1-005 JSON result from monthly observations."""
    ordered_by_date = sorted(observations, key=lambda item: str(item["date"]))
    monthly: dict[str, dict[str, str | float]] = {}
    for observation in ordered_by_date:
        monthly[str(observation["date"])[:7]] = observation
    ordered = list(monthly.values())
    current = ordered[-1] if ordered else None
    horizons: dict[str, Any] = {}
    for horizon, lookback in HORIZON_LOOKBACKS.items():
        if lookback is None:
            horizons[horizon] = _inapplicable_horizon()
            continue
        if current is None or len(ordered) < lookback:
            data = _empty_evidence_data()
            if current is not None:
                data["current_value"] = float(current["value"])
                data["current_date"] = str(current["date"])
            summary = (
                "MISSING DATA — "
                f"{lookback} valid monthly observations are required; "
                f"{len(ordered)} are available."
            )
            if cached:
                summary += " SOURCE UNAVAILABLE — cached data used."
            horizons[horizon] = {
                "signal": 0,
                "confidence": 0,
                "evidence": {"data": data, "summary": summary},
            }
            continue
        horizons[horizon] = _valid_horizon(current, ordered[-lookback], cached=cached)
    return {
        "variable_id": "L1-005",
        "as_of_date": as_of_date or date.today().isoformat(),
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "data_frequency": DATA_FREQUENCY,
        "observation_date": str(current["date"]) if current is not None else None,
        "horizons": horizons,
    }


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build a degraded result while retaining monthly inapplicability."""
    return {
        "variable_id": "L1-005",
        "as_of_date": as_of_date or date.today().isoformat(),
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "data_frequency": DATA_FREQUENCY,
        "observation_date": None,
        "horizons": {
            horizon: _inapplicable_horizon()
            if lookback is None
            else _degraded_horizon(summary)
            for horizon, lookback in HORIZON_LOOKBACKS.items()
        },
    }


def _cache_is_fresh(path: Path) -> bool:
    age_seconds = max(0.0, time.time() - path.stat().st_mtime)
    return age_seconds < CACHE_MAX_AGE_DAYS * 24 * 60 * 60


def _write_output(path: Path, output: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


def run(*, raw_path: Path = RAW_PATH, output_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Collect ACMTP10, apply cache rules, and write the current L1-005 output."""
    try:
        observations = fetch_series(SERIES_ID, raw_path=raw_path)
        output = build_output(observations)
    except FredError as exc:
        if raw_path.exists() and _cache_is_fresh(raw_path):
            try:
                observations = load_cached_series(raw_path)
            except FredError as cache_exc:
                output = build_degraded_output(f"EXTRACTION FAILED — {cache_exc}")
            else:
                print("SOURCE UNAVAILABLE — cached data used")
                output = build_output(observations, cached=True)
        elif raw_path.exists():
            output = build_degraded_output(
                "STALE DATA — FRED unavailable and cached data is 7 days old or older: "
                f"{exc}"
            )
        else:
            label = "CREDENTIAL MISSING" if "FRED_API_KEY" in str(exc) else "SOURCE UNAVAILABLE"
            output = build_degraded_output(f"{label} — {exc}")
    _write_output(output_path, output)
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
