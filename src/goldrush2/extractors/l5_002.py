"""DR2 extractor for L5-002: gold share of official reserves."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors import wgc
from goldrush2.extractors._wgc_common import HORIZON_LOOKBACKS, build_output as _build_output, degraded, parse_official_holdings_workbook

VARIABLE_ID = "L5-002"
SOURCE_NAME = "WGC Official Holdings - Gold Share of Official Reserves"
SOURCE_URL = "https://www.gold.org/"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "wgc"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / f"{VARIABLE_ID}.json"


def parse_reserve_share_workbook(path: Path) -> list[dict[str, Any]]:
    """Aggregate canonical panel shares by reported holdings-as-of month."""
    totals: defaultdict[str, list[float]] = defaultdict(list)
    for record in parse_official_holdings_workbook(path):
        if record["date"] and record["share"] is not None:
            totals[str(record["date"])].append(float(record["share"]))
    if not totals:
        raise ValueError("WGC official-holdings sheet contained no dated share records")
    latest_date = max(totals)
    return [{"date": latest_date, "value": round(sum(totals[latest_date]) / len(totals[latest_date]), 10)}]


def build_output(observations: list[dict[str, Any]], *, cached: bool = False, as_of_date: str | None = None) -> dict[str, Any]:
    """Build the four-horizon L5-002 output."""
    output = _build_output(VARIABLE_ID, SOURCE_NAME, SOURCE_URL, observations, cached=cached, as_of_date=as_of_date, value_label="Gold share of official reserves", rising_signal=1, falling_signal=-1)
    output["calculation_method"] = "Mean of canonical WGC panel shares grouped by reported holdings-as-of month"
    return output


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build a zero-confidence output for collection or parsing failure."""
    return {"variable_id": VARIABLE_ID, "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_frequency": "Monthly", "observation_date": None, "horizons": {horizon: degraded(summary) for horizon in HORIZON_LOOKBACKS}}


def run(*, output_path: Path = OUTPUT_PATH, raw_dir: Path = RAW_DIR) -> dict[str, Any]:
    """Collect, parse, and write the current L5-002 output."""
    workbook = wgc.fetch_wgc_official_holdings(raw_dir)
    if workbook is None:
        summary = "STALE DATA — WGC official-holdings workbook is unavailable and no fresh cache exists." if wgc.LAST_FETCH_STALE else "SOURCE UNAVAILABLE — WGC official-holdings workbook could not be downloaded."
        output = build_degraded_output(summary)
    else:
        try:
            output = build_output(parse_reserve_share_workbook(workbook), cached=wgc.LAST_FETCH_USED_CACHE)
        except (OSError, ValueError, KeyError) as exc:
            output = build_degraded_output(f"EXTRACTION FAILED — {exc}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
