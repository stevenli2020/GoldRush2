"""DR2 extractor for L4-001: publication-aligned CPI purchasing power."""

from __future__ import annotations

import json
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

from goldrush2.dr2.collectors.fred import FredError, fetch_series, load_cached_series

VARIABLE_ID = "L4-001"
SERIES_ID = "CPIAUCSL"
DATA_FREQUENCY = "Monthly"
SOURCE_NAME = "FRED CPIAUCSL - Consumer Price Index for All Urban Consumers"
SOURCE_URL = "https://fred.stlouisfed.org/series/CPIAUCSL"
CACHE_MAX_AGE_DAYS = 7
MAX_PUBLICATION_AGE_DAYS = 62
HORIZON_LOOKBACKS = {"1-5d": 5, "1-3m": 1, "1-3y": 48, "3-10y": 132}
from goldrush2.paths import DR2_ROOT as PROJECT_ROOT
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "fred" / f"{SERIES_ID}.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / f"{VARIABLE_ID}.json"


def _empty_data() -> dict[str, Any]:
    return {"current_value": None, "current_date": None, "publication_date": None, "CPI_YoY_12m_MA": None}


def _degraded(summary: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"signal": 0, "confidence": 0, "evidence": {"data": data or _empty_data(), "summary": summary}}


def _month_key(value: str) -> int:
    parsed = datetime.strptime(value[:7], "%Y-%m")
    return parsed.year * 12 + parsed.month


def _publication_date(row: dict[str, Any]) -> str | None:
    value = row.get("publication_date")
    if not isinstance(value, str):
        return None
    try:
        date.fromisoformat(value)
    except ValueError:
        return None
    return value


def _eligible(observations: list[dict[str, str | float]], decision_date: str) -> list[dict[str, Any]]:
    """Keep only observations published by the decision date."""
    eligible: list[dict[str, Any]] = []
    for row in observations:
        publication_date = _publication_date(row)
        if publication_date is None or publication_date > decision_date:
            continue
        eligible.append({**row, "publication_date": publication_date})
    return sorted(eligible, key=lambda item: str(item["date"]))


def _smoothed_rates(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Calculate monthly CPI YoY rates and their trailing 12-month mean."""
    by_month = {_month_key(str(row["date"])): row for row in observations}
    yoy: dict[int, float] = {}
    for month, row in by_month.items():
        prior = by_month.get(month - 12)
        if prior is not None and float(prior["value"]) != 0:
            yoy[month] = (float(row["value"]) / float(prior["value"]) - 1) * 100
    smoothed: list[dict[str, Any]] = []
    for month in sorted(yoy):
        window = [yoy.get(month - offset) for offset in range(12)]
        if any(value is None for value in window):
            continue
        row = by_month[month]
        smoothed.append({"date": str(row["date"]), "publication_date": str(row["publication_date"]), "value": float(row["value"]), "yoy": yoy[month], "ma": sum(window) / 12})
    return smoothed


def _valid(current: dict[str, Any], *, cached: bool) -> dict[str, Any]:
    rate = float(current["ma"])
    if rate < 1.5:
        signal = -1.0
    elif rate < 2.5:
        signal = 0.0
    elif rate < 4.0:
        signal = 0.5
    else:
        signal = 1.0
    direction = "below purchasing-power pressure anchor" if signal < 0 else "within the neutral purchasing-power band" if signal == 0 else "above the purchasing-power pressure anchor"
    summary = f"CPI_YoY_12m_MA is {rate:.2f}%, {direction}; L4-001 reflects purchasing-power erosion only."
    if cached:
        summary += " SOURCE UNAVAILABLE — cached data used."
    return {"signal": signal, "confidence": 1, "evidence": {"data": {"CPI_YoY_12m": round(float(current["yoy"]), 6), "CPI_YoY_12m_MA": round(rate, 6), "current_value": float(current["value"]), "observation_date": current["date"], "publication_date": current["publication_date"]}, "summary": summary}}


def build_output(observations: list[dict[str, str | float]], *, cached: bool = False, as_of_date: str | None = None) -> dict[str, Any]:
    """Build CPI output using only publication-eligible monthly observations."""
    decision_date = as_of_date or date.today().isoformat()
    ordered = _eligible(observations, decision_date)
    smoothed = _smoothed_rates(ordered)
    current = smoothed[-1] if smoothed else None
    horizons: dict[str, Any] = {}
    # Freshness is a variable-specific data-availability rule.  It must be
    # based on the latest evidence observation period, never on FRED vintage
    # metadata or an incorrectly mapped publication date.
    stale = current is not None and (date.fromisoformat(decision_date) - date.fromisoformat(current["date"])).days > MAX_PUBLICATION_AGE_DAYS
    for horizon in HORIZON_LOOKBACKS:
        if current is None:
            data = _empty_data()
            summary = f"INSUFFICIENT HISTORY — publication-aligned CPI history cannot calculate CPI_YoY_12m_MA; {len(ordered)} eligible monthly observations are available."
            if cached:
                summary += " SOURCE UNAVAILABLE — cached data used."
            horizons[horizon] = _degraded(summary, data)
        elif stale:
            data = {"CPI_YoY_12m_MA": round(float(current["ma"]), 6), "observation_date": current["date"], "publication_date": current["publication_date"]}
            horizons[horizon] = _degraded(f"STALE DATA — latest smoothed CPI observation period is older than {MAX_PUBLICATION_AGE_DAYS} days.", data)
        else:
            horizons[horizon] = _valid(current, cached=cached)
    return {"variable_id": VARIABLE_ID, "as_of_date": decision_date, "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_frequency": DATA_FREQUENCY, "observation_date": str(current["date"]) if current else None, "publication_date": str(current["publication_date"]) if current else None, "horizons": horizons}


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build a zero-confidence result for a collection failure."""
    return {"variable_id": VARIABLE_ID, "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_frequency": DATA_FREQUENCY, "observation_date": None, "publication_date": None, "horizons": {horizon: _degraded(summary) for horizon in HORIZON_LOOKBACKS}}


def _cache_is_fresh(path: Path) -> bool:
    return max(0.0, time.time() - path.stat().st_mtime) < CACHE_MAX_AGE_DAYS * 86400


def _write_output(path: Path, output: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


def run(*, raw_path: Path = RAW_PATH, output_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Fetch CPIAUCSL, apply seven-day cache rules, and write current output."""
    try:
        output = build_output(fetch_series(SERIES_ID, raw_path=raw_path))
    except FredError as exc:
        if raw_path.exists() and _cache_is_fresh(raw_path):
            try:
                output = build_output(load_cached_series(raw_path), cached=True)
            except FredError as cache_exc:
                output = build_degraded_output(f"EXTRACTION FAILED — {cache_exc}")
        elif raw_path.exists():
            output = build_degraded_output(f"STALE DATA — FRED unavailable and cached data is 7 days old or older: {exc}")
        else:
            output = build_degraded_output(f"SOURCE UNAVAILABLE — {exc}")
    _write_output(output_path, output)
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
