"""DR2 extractor for L1-004: 2Y TIPS Real Yield."""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors.frb_tips import (
    FrbTipsError,
    fetch_tips_yield,
    load_cached_tips_yield,
)

MATURITY = "2Y"
SOURCE_NAME = "Federal Reserve Board TIPS Yield Curve - TIPSY02"
SOURCE_URL = "https://www.federalreserve.gov/data/tips-yield-curve-and-inflation-compensation.htm"
CACHE_MAX_AGE_DAYS = 7
HORIZON_LOOKBACKS: dict[str, int | None] = {
    "1-5d": 5,
    "1-3m": 63,
    "1-3y": 252,
    "3-10y": None,
}

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "frb_tips" / "real_yield_curve.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / "L1-004.json"


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
            "summary": (
                "3–10 year horizon is structurally inapplicable for a 2-year "
                "maturity instrument."
            ),
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
            f"The 2Y real yield fell by {abs(change):.2f} percentage points, "
            "bullish for gold."
        )
    elif change > 0:
        signal = -1
        summary = (
            f"The 2Y real yield rose by {change:.2f} percentage points, "
            "bearish for gold."
        )
    else:
        signal = 0
        summary = "The 2Y real yield was unchanged, neutral for gold."

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
    """Build the complete L1-004 JSON result from valid observations."""
    ordered = sorted(observations, key=lambda item: str(item["date"]))
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
            horizons[horizon] = {
                "signal": 0,
                "confidence": 0,
                "evidence": {
                    "data": data,
                    "summary": (
                        "MISSING DATA — "
                        f"{lookback} valid observations are required; "
                        f"{len(ordered)} are available."
                    ),
                },
            }
            continue

        horizons[horizon] = _valid_horizon(current, ordered[-lookback], cached=cached)

    return {
        "variable_id": "L1-004",
        "as_of_date": as_of_date or date.today().isoformat(),
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "observation_date": str(current["date"]) if current is not None else None,
        "horizons": horizons,
    }


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build a degraded result while retaining structural inapplicability."""
    return {
        "variable_id": "L1-004",
        "as_of_date": as_of_date or date.today().isoformat(),
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
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
    """Collect TIPSY02, apply cache rules, and write the current L1-004 output."""
    try:
        observations = fetch_tips_yield(MATURITY, raw_path=raw_path)
        output = build_output(observations)
    except FrbTipsError as exc:
        if raw_path.exists() and _cache_is_fresh(raw_path):
            try:
                observations = load_cached_tips_yield(raw_path, MATURITY)
            except FrbTipsError as cache_exc:
                output = build_degraded_output(f"EXTRACTION FAILED — {cache_exc}")
            else:
                print("SOURCE UNAVAILABLE — cached data used")
                output = build_output(observations, cached=True)
        elif raw_path.exists():
            output = build_degraded_output(
                "STALE DATA — Federal Reserve TIPS source unavailable and cached "
                f"data is 7 days old or older: {exc}"
            )
        else:
            output = build_degraded_output(f"SOURCE UNAVAILABLE — {exc}")

    _write_output(output_path, output)
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
