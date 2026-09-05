"""L0-009 extractor for the COMEX Gold forward/lease-rate proxy."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

VARIABLE_ID = "L0-009"
SOURCE_NAME = "CME Gold Futures + SOFR - Gold Forward/Lease Rate Proxy (%)"
SOURCE_URL = "https://www.cmegroup.com/"
from goldrush2.paths import DR2_ROOT as PROJECT_ROOT
CACHE_PATH = PROJECT_ROOT / "data" / "cache" / "cme" / "l0_009.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / "L0-009.json"
LOOKBACKS = {"1-5d": 5, "1-3m": 63, "1-3y": 252, "3-10y": 756}


def _insufficient() -> dict[str, Any]:
    return {"signal": 0, "confidence": 0.0, "evidence": {"error": "Insufficient valid observations"}}


def build_output(observations: list[dict[str, Any]]) -> dict[str, Any]:
    rows = sorted(observations, key=lambda row: str(row["date"]))
    latest = rows[-1] if rows else None
    output: dict[str, Any] = {
        "variable_id": VARIABLE_ID,
        "data_frequency": "Daily",
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "observation_date": latest["date"] if latest else None,
        "horizons": {},
    }
    for horizon, lookback in LOOKBACKS.items():
        if latest is None or len(rows) <= lookback:
            output["horizons"][horizon] = _insufficient()
            continue
        comparison = rows[-1 - lookback]
        change = round(float(latest["value"]) - float(comparison["value"]), 8)
        signal = 1 if change > 0 else -1 if change < 0 else 0
        data = {
            "current_value": latest["value"],
            "current_date": latest["date"],
            "comparison_value": comparison["value"],
            "comparison_date": comparison["date"],
            "change_pp": change,
            "forward_rate": latest["forward_rate"],
            "sofr": latest["sofr"],
            "near_contract": latest["near_contract"],
            "far_contract": latest["far_contract"],
            "days_between": latest["days_between"],
            "sofr_is_filled": latest.get("sofr_is_filled", False),
        }
        direction = "rose, indicating tighter bullion market conditions, bullish for gold" if signal == 1 else "fell, indicating looser bullion market conditions, bearish for gold" if signal == -1 else "was unchanged, indicating no directional change"
        output["horizons"][horizon] = {
            "signal": signal,
            "confidence": 1.0,
            "evidence": {"data": data, "summary": f"Gold forward-lease proxy {direction} by {abs(change):.4f} percentage points compared to {lookback} valid observations ago."},
        }
    return output


def run(*, output_path: Path = OUTPUT_PATH, cache_path: Path = CACHE_PATH) -> dict[str, Any]:
    try:
        observations = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read L0-009 cache: {cache_path}") from exc
    output = build_output(observations)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, output_path)
    return output
