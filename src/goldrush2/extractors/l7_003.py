"""DR2 extractor for BIS global private non-financial-sector credit growth."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

VARIABLE_ID = "L7-003"
SOURCE_NAME = "BIS WS_TC(2.0) - Private Non-Financial Sector Credit Growth (YoY, %)"
SOURCE_URL = "https://www.bis.org/statistics/totcredit.htm"
LOOKBACKS = {"1-3y": 4, "3-10y": 20}


def add_yoy(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(observations, key=lambda row: str(row["date"]))
    levels = {str(row["date"]): float(row["value"]) for row in ordered}
    result = []
    for row in ordered:
        observed = date.fromisoformat(str(row["date"]))
        prior = date(observed.year - 1, observed.month, observed.day).isoformat()
        growth = (levels[str(row["date"])] / levels[prior] - 1) * 100 if prior in levels else None
        result.append({"date": str(row["date"]), "value": float(row["value"]), "yoy_growth": growth})
    return result


def build_output(observations: list[dict[str, Any]], *, cached: bool = False, as_of_date: str | None = None, stale_days: int = 270) -> dict[str, Any]:
    rows = add_yoy(observations)
    current = rows[-1] if rows else None
    as_of = date.fromisoformat(as_of_date) if as_of_date else date.today()
    stale = current is not None and (as_of - date.fromisoformat(current["date"])).days > stale_days
    horizons: dict[str, Any] = {
        "1-5d": {"signal": 0, "confidence": 1, "evidence": {"summary": "Quarterly data does not support 1-5d horizon."}},
        "1-3m": {"signal": 0, "confidence": 1, "evidence": {"summary": "Quarterly data does not support 1-3m horizon."}},
    }
    for horizon, lookback in LOOKBACKS.items():
        if current is None or len(rows) <= lookback or current["yoy_growth"] is None:
            summary = f"MISSING DATA — {lookback} prior quarterly observations and a prior-year comparison are required."
            if cached:
                summary += " SOURCE UNAVAILABLE — cached data used."
            if stale:
                summary += f" STALE DATA — latest observation exceeds the {stale_days}-day threshold."
            horizons[horizon] = {"signal": 0, "confidence": 0, "evidence": {"data": {"current_yoy": current["yoy_growth"] if current else None, "current_date": current["date"] if current else None, "comparison_yoy": None, "comparison_date": None, "change_yoy_pp": None, "flag": None}, "summary": summary}}
            continue
        comparison = rows[-1 - lookback]
        if comparison["yoy_growth"] is None:
            horizons[horizon] = {"signal": 0, "confidence": 0, "evidence": {"data": {"current_yoy": current["yoy_growth"], "current_date": current["date"], "comparison_yoy": None, "comparison_date": comparison["date"], "change_yoy_pp": None, "flag": None}, "summary": "MISSING DATA — comparison YoY growth is unavailable."}}
            continue
        change = round(float(current["yoy_growth"]) - float(comparison["yoy_growth"]), 10)
        signal = 1 if change > 0 else -1 if change < 0 else 0
        direction = "rose" if signal == 1 else "fell" if signal == -1 else "was unchanged"
        flag = "HIGH_GROWTH" if abs(float(current["yoy_growth"])) > 30 else None
        data = {"current_yoy": round(float(current["yoy_growth"]), 10), "current_date": current["date"], "comparison_yoy": round(float(comparison["yoy_growth"]), 10), "comparison_date": comparison["date"], "change_yoy_pp": change, "flag": flag}
        summary = f"Credit growth YoY {direction} by {abs(change):.2f} percentage points compared to {lookback} quarters ago, indicating credit {'expansion, bullish' if signal == 1 else 'contraction, bearish' if signal == -1 else 'stability, neutral'} for gold."
        if cached:
            summary += " SOURCE UNAVAILABLE — cached data used."
        if stale:
            summary += f" STALE DATA — latest observation exceeds the {stale_days}-day threshold."
        horizons[horizon] = {"signal": signal, "confidence": 1, "evidence": {"data": data, "summary": summary}}
    return {"variable_id": VARIABLE_ID, "data_frequency": "Quarterly", "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "observation_date": current["date"] if current else None, "as_of_date": date.today().isoformat(), "horizons": horizons}


def run(cache_path: Path = Path("data/cache/bis/L7-003.json"), output_path: Path = Path("data/current/L7-003.json")) -> dict[str, Any]:
    rows = json.loads(Path(cache_path).read_text(encoding="utf-8"))
    output = build_output(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return output


if __name__ == "__main__":
    run()
