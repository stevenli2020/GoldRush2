"""DR2 extractor for the FOMC SEP next-year median projection."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from goldrush2.paths import DR2_ROOT as PROJECT_ROOT

VARIABLE_ID = "L3-005"
DATA_FREQUENCY = "Quarterly"
SOURCE_NAME = "FOMC SEP Summary"
SOURCE_URL = "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl.htm"
CACHE_PATH = PROJECT_ROOT / "data/cache/L3-005.json"


def _lag(observations: list[dict[str, Any]], current_date: str, months: int) -> dict[str, Any] | None:
    target = (pd.Timestamp(current_date) - pd.DateOffset(months=months)).date().isoformat()
    return next((row for row in observations if str(row.get("date")) == target), None)


def _comparison(observations: list[dict[str, Any]], current: dict[str, Any], months: int, label: str) -> dict[str, Any]:
    previous = _lag(observations, str(current["date"]), months)
    if previous is None:
        return {"signal": None, "confidence": 0, "evidence": {"error": f"No data exactly {label} prior", "current_date": current["date"]}}
    diff = float(current["value"]) - float(previous["value"])
    signal = 1 if diff < 0 else -1 if diff > 0 else 0
    data = {"current": current["value"], "previous": previous["value"], "current_date": current["date"], "previous_date": previous["date"], "diff": diff}
    if label == "5 years":
        data["previous_5y_value"] = previous["value"]
        data["previous_5y_date"] = previous["date"]
    return {"signal": signal, "confidence": 1, "evidence": {"data": data, "summary": f"FOMC next-year median projection {'fell' if diff < 0 else 'rose' if diff > 0 else 'was unchanged'} by {abs(diff):g} percentage points compared to {label} prior."}}


def build_output(observations: list[dict[str, Any]]) -> dict[str, Any]:
    rows = sorted(observations, key=lambda row: str(row["date"]))
    if not rows:
        raise ValueError("L3-005 cache contains no observations")
    current = rows[-1]
    return {
        "variable_id": VARIABLE_ID,
        "data_frequency": DATA_FREQUENCY,
        "source_name": SOURCE_NAME,
        "source_url": current.get("source_url", SOURCE_URL),
        "observation_date": current["date"],
        "horizons": {
            "1-5d": {"signal": 0, "confidence": 1, "evidence": {"reason": "quarterly data"}},
            "1-3m": {"signal": 0, "confidence": 1, "evidence": {"reason": "quarterly data"}},
            "1-3y": _comparison(rows, current, 12, "1 year"),
            "3-10y": _comparison(rows, current, 60, "5 years"),
        },
    }


def extract(variable_id: str = VARIABLE_ID, force_refresh: bool = False) -> dict[str, Any]:
    del force_refresh
    if variable_id.upper() != VARIABLE_ID:
        raise ValueError(f"Unsupported variable: {variable_id}")
    return build_output(json.loads(CACHE_PATH.read_text(encoding="utf-8")))


def run(cache_path: Path = CACHE_PATH, output_path: Path = PROJECT_ROOT / "data/current/L3-005.json") -> dict[str, Any]:
    observations = json.loads(Path(cache_path).read_text(encoding="utf-8"))
    output = build_output(observations)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, output_path)
    return output
