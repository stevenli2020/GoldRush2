"""L3-004 extractor for CME FedWatch easing-probability changes."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

VARIABLE_ID = "L3-004"
SOURCE_NAME = "CME FedWatch"
SOURCE_URL = "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch.html"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CACHE_PATH = PROJECT_ROOT / "data" / "cache" / "fedwatch" / "l3_004.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / "L3-004.json"
HORIZONS = {"1-5d": (5, 1.0), "1-3m": (91, 0.8), "1-3y": (364, 0.6), "3-10y": (1820, 0.4)}


def _lookback(rows: list[dict[str, Any]], target: date) -> dict[str, Any] | None:
    for row in reversed(rows):
        if date.fromisoformat(str(row["date"])) <= target:
            return row
    return None


def build_output(observations: list[dict[str, Any]]) -> dict[str, Any]:
    rows = sorted(observations, key=lambda row: str(row["date"]))
    latest = rows[-1] if rows else None
    output: dict[str, Any] = {"variable_id": VARIABLE_ID, "data_frequency": "Daily", "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "observation_date": latest["date"] if latest else None, "meeting_date": latest.get("meeting_date") if latest else None, "horizons": {}}
    if latest is None:
        for horizon in HORIZONS:
            output["horizons"][horizon] = {"signal": 0, "confidence": 0.0, "evidence": {"error": "Insufficient data"}}
        return output
    for horizon, (lookback_days, confidence) in HORIZONS.items():
        target = date.fromisoformat(str(latest["date"])) - timedelta(days=lookback_days)
        old = _lookback(rows, target)
        if old is None:
            output["horizons"][horizon] = {"signal": 0, "confidence": 0.0, "evidence": {"error": "Insufficient data"}}
            continue
        change = round(float(latest["easing_prob"]) - float(old["easing_prob"]), 6)
        output["horizons"][horizon] = {"signal": 1 if change > 0 else -1 if change < 0 else 0, "confidence": confidence, "evidence": {"current_easing_prob": latest["easing_prob"], "lookback_easing_prob": old["easing_prob"], "lookback_date": old["date"], "change": change, "lookback_is_filled": bool(old.get("is_filled", False))}}
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
