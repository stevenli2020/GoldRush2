"""L10-001 extractor: CFTC managed-money net positioning."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

VARIABLE_ID = "L10-001"
SOURCE_NAME = "CFTC Disaggregated COT Report"
SOURCE_URL = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CACHE_PATH = PROJECT_ROOT / "data" / "cache" / "L10-001.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / "L10-001.json"
HORIZONS = {"1-5d": (5, 1.0), "1-3m": (13, 0.8), "1-3y": (52, 0.6), "3-10y": (260, 0.4)}


def build_output(observations: list[dict[str, Any]], *, today: str | None = None) -> dict[str, Any]:
    rows = sorted(observations, key=lambda row: str(row["date"]))
    latest = rows[-1] if rows else None
    output = {"variable_id": VARIABLE_ID, "data_frequency": "Weekly", "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "observation_date": latest["date"] if latest else None, "horizons": {}}
    gap_days = 0 if not latest or not today else max(0, (date.fromisoformat(today) - date.fromisoformat(latest["date"])).days)
    for horizon, (lookback, confidence) in HORIZONS.items():
        if latest is None or len(rows) <= lookback or gap_days > 14:
            output["horizons"][horizon] = {"signal": 0, "confidence": 0.0, "evidence": {"error": "Insufficient data"}}
            continue
        old = rows[-lookback - 1]
        change = int(latest["net"]) - int(old["net"])
        output["horizons"][horizon] = {"signal": 1 if change > 0 else -1 if change < 0 else 0, "confidence": 0.0 if gap_days >= 7 else confidence, "evidence": {"current_net": latest["net"], f"{lookback}_weeks_ago_net": old["net"], f"{lookback}_weeks_ago_date": old["date"], "change": change}}
    return output


def run(*, output_path: Path = OUTPUT_PATH, cache_path: Path = CACHE_PATH) -> dict[str, Any]:
    try:
        rows = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read L10-001 cache: {cache_path}") from exc
    output = build_output(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, output_path)
    return output

