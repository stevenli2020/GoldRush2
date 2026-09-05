"""DR2 extractor for L5-001: monthly official-sector gold purchases."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.dr2.collectors import wgc
from goldrush2.dr2.extractors._wgc_common import HORIZON_LOOKBACKS, build_output as _build_output, degraded, parse_official_changes_workbook

VARIABLE_ID = "L5-001"
SOURCE_NAME = "WGC/IMF IFS Official-Sector Gold Purchases (tonnes)"
SOURCE_URL = "https://www.gold.org/"
from goldrush2.paths import DR2_ROOT as PROJECT_ROOT
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "wgc"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / f"{VARIABLE_ID}.json"


def parse_purchases_workbook(path: Path) -> list[dict[str, Any]]:
    """Aggregate canonical country changes into global monthly net purchases."""
    totals: defaultdict[str, float] = defaultdict(float)
    for record in parse_official_changes_workbook(path):
        totals[str(record["date"])] += float(record["value"])
    return [{"date": observation_date, "value": round(value, 10)} for observation_date, value in sorted(totals.items())]


def build_output(observations: list[dict[str, Any]], *, cached: bool = False, as_of_date: str | None = None) -> dict[str, Any]:
    """Build the four-horizon L5-001 output."""
    return _build_output(VARIABLE_ID, SOURCE_NAME, SOURCE_URL, observations, cached=cached, as_of_date=as_of_date, value_label="Official-sector net purchases", rising_signal=1, falling_signal=-1)


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build a zero-confidence output for collection or parsing failure."""
    return {"variable_id": VARIABLE_ID, "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_frequency": "Monthly", "observation_date": None, "horizons": {horizon: degraded(summary) for horizon in HORIZON_LOOKBACKS}}


def run(*, output_path: Path = OUTPUT_PATH, raw_dir: Path = RAW_DIR) -> dict[str, Any]:
    """Collect, parse, and write the current L5-001 output."""
    workbook = wgc.fetch_wgc_official_changes(raw_dir)
    if workbook is None:
        summary = "STALE DATA — WGC official-changes workbook is unavailable and no fresh cache exists." if wgc.LAST_FETCH_STALE else "SOURCE UNAVAILABLE — WGC official-changes workbook could not be downloaded."
        output = build_degraded_output(summary)
    else:
        try:
            output = build_output(parse_purchases_workbook(workbook), cached=wgc.LAST_FETCH_USED_CACHE)
        except (OSError, ValueError, KeyError) as exc:
            output = build_degraded_output(f"EXTRACTION FAILED — {exc}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()

