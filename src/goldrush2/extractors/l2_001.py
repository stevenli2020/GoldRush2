"""DR2 extractor for L2-001: DXY US Dollar Index."""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors import yahoo

VARIABLE_ID = "L2-001"
SYMBOL = "DX-Y.NYB"
SOURCE_NAME = "Yahoo Finance DX-Y.NYB - US Dollar Index (DXY)"
SOURCE_URL = "https://finance.yahoo.com/quote/DX-Y.NYB/"
HORIZON_LOOKBACKS = {"1-5d": 5, "1-3m": 63, "1-3y": 252, "3-10y": 756}
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "yahoo" / f"{SYMBOL}.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / f"{VARIABLE_ID}.json"


def _empty_data() -> dict[str, None]:
    return {"current_value": None, "current_date": None, "comparison_value": None, "comparison_date": None, "change_absolute": None, "change_pct": None}


def _degraded(summary: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"signal": 0, "confidence": 0, "evidence": {"data": data or _empty_data(), "summary": summary}}


def _valid(current: dict[str, str | float], comparison: dict[str, str | float], *, cached: bool) -> dict[str, Any]:
    current_value = float(current["value"])
    comparison_value = float(comparison["value"])
    change = round(current_value - comparison_value, 10)
    change_pct = round(change / comparison_value * 100, 10) if comparison_value else None
    if change < 0:
        signal, summary = 1, f"USD index fell by {abs(change):.2f} points, bullish for gold."
    elif change > 0:
        signal, summary = -1, f"USD index rose by {change:.2f} points, bearish for gold."
    else:
        signal, summary = 0, "USD index was unchanged, neutral for gold."
    if cached:
        summary += " SOURCE UNAVAILABLE — cached data used."
    return {"signal": signal, "confidence": 1, "evidence": {"data": {"current_value": current_value, "current_date": current["date"], "comparison_value": comparison_value, "comparison_date": comparison["date"], "change_absolute": change, "change_pct": change_pct}, "summary": summary}}


def build_output(observations: list[dict[str, str | float]], *, cached: bool = False, as_of_date: str | None = None) -> dict[str, Any]:
    """Build the four-horizon L2-001 result from finalized Yahoo observations."""
    ordered = sorted(observations, key=lambda item: str(item["date"]))
    current = ordered[-1] if ordered else None
    horizons: dict[str, Any] = {}
    for horizon, lookback in HORIZON_LOOKBACKS.items():
        if current is None or len(ordered) < lookback:
            data = _empty_data()
            if current is not None:
                data["current_value"], data["current_date"] = float(current["value"]), str(current["date"])
            summary = f"MISSING DATA — {lookback} valid observations are required; {len(ordered)} are available."
            if cached:
                summary += " SOURCE UNAVAILABLE — cached data used."
            horizons[horizon] = _degraded(summary, data)
        else:
            horizons[horizon] = _valid(current, ordered[-lookback], cached=cached)
    return {"variable_id": VARIABLE_ID, "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "observation_date": str(current["date"]) if current else None, "horizons": horizons}


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build a zero-confidence result for a collection failure."""
    return {"variable_id": VARIABLE_ID, "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "observation_date": None, "horizons": {horizon: _degraded(summary) for horizon in HORIZON_LOOKBACKS}}


def _write_output(path: Path, output: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


def run(*, raw_path: Path = RAW_PATH, output_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Fetch DXY, apply Yahoo cache rules, and write current output."""
    try:
        observations = yahoo.fetch_yahoo_series(SYMBOL, raw_path)
        output = build_output(observations, cached=yahoo.LAST_FETCH_USED_CACHE)
    except yahoo.YahooError as exc:
        output = build_degraded_output(str(exc))
    _write_output(output_path, output)
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
