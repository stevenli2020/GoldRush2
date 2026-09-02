"""DR2 extractor for IMF COFER USD share of allocated global FX reserves."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

VARIABLE_ID = "L5-003"
SOURCE_NAME = "IMF COFER - USD Share of Allocated Global FX Reserves (%)"
SOURCE_URL = "https://data.imf.org/COFER"
CACHE_PATH = Path("data/cache/imf/L5-003.json")
LOOKBACKS = {"1-3y": 4, "3-10y": 20}


def quarter_rows(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = sorted(observations, key=lambda row: str(row["date"]))
    result = []
    previous = None
    for row in rows:
        value = float(row["value"])
        change = None if previous is None else value - previous
        result.append({"date": str(row["date"]), "value": value, "qoq_change": change, "flag": "LARGE_SHIFT" if change is not None and abs(change) > 5 else None})
        previous = value
    return result


def build_output(observations: list[dict[str, Any]], *, cached: bool = False, as_of_date: str | None = None, stale_days: int = 200) -> dict[str, Any]:
    rows = quarter_rows(observations)
    current = rows[-1] if rows else None
    stale = current is not None and (date.fromisoformat(as_of_date) if as_of_date else date.today())
    stale = bool(current and (stale - date.fromisoformat(current["date"])).days > stale_days)
    horizons: dict[str, Any] = {
        "1-5d": {"signal": 0, "confidence": 1, "evidence": {"summary": "Quarterly data does not support 1-5d horizon."}},
        "1-3m": {"signal": 0, "confidence": 1, "evidence": {"summary": "Quarterly data does not support 1-3m horizon."}},
    }
    for horizon, lookback in LOOKBACKS.items():
        if current is None or len(rows) <= lookback:
            summary = f"MISSING DATA — {lookback} prior quarterly observations are required."
            data = {"current_share": current["value"] if current else None, "current_date": current["date"] if current else None, "comparison_share": None, "comparison_date": None, "change_pp": None, "flag": current["flag"] if current else None}
            horizons[horizon] = {"signal": 0, "confidence": 0, "evidence": {"data": data, "summary": summary + (" SOURCE UNAVAILABLE — cached data used." if cached else "")}}
            continue
        comparison = rows[-1 - lookback]
        change = round(current["value"] - comparison["value"], 10)
        signal = 1 if change < 0 else -1 if change > 0 else 0
        direction = "fell" if signal == 1 else "rose" if signal == -1 else "was unchanged"
        data = {"current_share": round(current["value"], 10), "current_date": current["date"], "comparison_share": round(comparison["value"], 10), "comparison_date": comparison["date"], "change_pp": change, "flag": current["flag"]}
        summary = f"USD reserve share {direction} by {abs(change):.2f} percentage points compared to {lookback} quarters ago, suggesting {'reserve diversification, bullish' if signal == 1 else 'continued USD dominance, bearish' if signal == -1 else 'stable reserve composition, neutral'} for gold."
        if cached:
            summary += " SOURCE UNAVAILABLE — cached data used."
        if stale:
            summary += f" STALE DATA — latest observation exceeds the {stale_days}-day threshold."
        horizons[horizon] = {"signal": signal, "confidence": 1, "evidence": {"data": data, "summary": summary}}
    return {"variable_id": VARIABLE_ID, "data_frequency": "Quarterly", "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "observation_date": current["date"] if current else None, "as_of_date": date.today().isoformat(), "horizons": horizons}


def run(cache_path: Path = CACHE_PATH, output_path: Path = Path("data/current/L5-003.json")) -> dict[str, Any]:
    output = build_output(json.loads(Path(cache_path).read_text(encoding="utf-8")))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return output


if __name__ == "__main__":
    run()
