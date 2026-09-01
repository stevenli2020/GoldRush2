"""DR2 extractor for L5-002: historical official-reserve gold-share proxy."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors import wgc
from goldrush2.extractors._wgc_common import HORIZON_LOOKBACKS, build_output as _build_output, cumulative_net_change_series, degraded

VARIABLE_ID = "L5-002"
SOURCE_NAME = "WGC/IMF IFS Official Changes - Gold Share of Official Reserves (cumulative net-change proxy)"
SOURCE_URL = "https://www.gold.org/"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "wgc"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / f"{VARIABLE_ID}.json"


def parse_reserve_share_workbook(path: Path) -> list[dict[str, Any]]:
    """Build the approved changes-only fallback for reserve-share history.

    The Monthly sheet contains signed country changes but no total-reserves
    denominator. Consequently this returns a cumulative net-change proxy,
    not a reported 0-1 reserve-share fraction.
    """
    return cumulative_net_change_series(path)


def build_output(observations: list[dict[str, Any]], *, cached: bool = False, as_of_date: str | None = None) -> dict[str, Any]:
    """Build the four-horizon L5-002 output from the cumulative proxy."""
    output = _build_output(VARIABLE_ID, SOURCE_NAME, SOURCE_URL, observations, cached=cached, as_of_date=as_of_date, value_label="Cumulative official-sector gold-change proxy", rising_signal=1, falling_signal=-1)
    first_date = observations[0]["date"] if observations else "unknown"
    output["calculation_method"] = f"cumulative_net_changes_proxy_from_{str(first_date)[:7]}"
    output["calculation_note"] = "The official-changes workbook has no total-reserves denominator; values are a tonnes proxy, not a true 0-1 gold-share series."
    return output


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build a zero-confidence output for collection or parsing failure."""
    return {"variable_id": VARIABLE_ID, "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_frequency": "Monthly", "observation_date": None, "calculation_method": "cumulative_net_changes_proxy_from_first_available_month", "calculation_note": "The official-changes workbook has no total-reserves denominator.", "horizons": {horizon: degraded(summary) for horizon in HORIZON_LOOKBACKS}}


def run(*, output_path: Path = OUTPUT_PATH, raw_dir: Path = RAW_DIR) -> dict[str, Any]:
    """Collect the historical changes workbook and write current L5-002 JSON."""
    workbook = wgc.fetch_wgc_official_changes(raw_dir)
    if workbook is None:
        summary = "STALE DATA — WGC/IMF IFS official-changes workbook is unavailable and no fresh cache exists." if wgc.LAST_FETCH_STALE else "SOURCE UNAVAILABLE — WGC/IMF IFS official-changes workbook could not be downloaded."
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
    """Run the extractor and print the resulting JSON."""
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
