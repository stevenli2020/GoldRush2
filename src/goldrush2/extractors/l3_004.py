"""L3-004 extractor for CME FedWatch cut-probability changes."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

VARIABLE_ID = "L3-004"
SOURCE_NAME = "CME FedWatch - Policy Outcome Probabilities (cut probability, %)"
SOURCE_URL = "https://www.cmegroup.com/"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CACHE_PATH = PROJECT_ROOT / "data" / "cache" / "fedwatch" / "l3_004.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / "L3-004.json"
HORIZONS = {"1-5d": (5, 0.9), "1-3m": (13, 0.7), "1-3y": (52, 0.5), "3-10y": (260, 0.3)}


def build_output(observations: list[dict[str, Any]]) -> dict[str, Any]:
    rows = sorted(observations, key=lambda row: str(row["date"]))
    latest = rows[-1] if rows else None
    output = {"variable_id": VARIABLE_ID, "data_frequency": "Daily", "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "observation_date": latest["date"] if latest else None, "horizons": {}}
    meeting_date = latest.get("meeting_date") if latest else None
    if meeting_date:
        days_until = (date.fromisoformat(str(meeting_date)) - date.fromisoformat(str(latest["date"]))).days
        base_confidence = 0.9 if days_until <= 7 else 0.7 if days_until <= 30 else 0.5
    else:
        base_confidence = 0.3
    for horizon, (lookback, _) in HORIZONS.items():
        if latest is None or len(rows) <= lookback:
            output["horizons"][horizon] = {"signal": 0, "confidence": 0.0, "evidence": {"error": "Insufficient data"}}
            continue
        old = rows[-lookback - 1]
        change = float(latest["cut_probability"]) - float(old["cut_probability"])
        output["horizons"][horizon] = {"signal": 1 if change > 0 else -1 if change < 0 else 0, "confidence": base_confidence, "evidence": {"data": {"current_prob": latest["cut_probability"], "comparison_prob": old["cut_probability"], "change_pp": change, "comparison_date": old["date"], "meeting_date": latest.get("meeting_date")}}}
    return output


def run(*, output_path: Path = OUTPUT_PATH, cache_path: Path = CACHE_PATH) -> dict[str, Any]:
    try:
        rows = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read FedWatch cache: {cache_path}") from exc
    output = build_output(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, output_path)
    return output
