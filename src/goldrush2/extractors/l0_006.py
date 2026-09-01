"""DR2 extractor for L0-006: quarterly recycled gold supply."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors import wgc
from goldrush2.extractors._wgc_common import build_quarterly_output, degraded, parse_gdt_quarterly_workbook

VARIABLE_ID = "L0-006"
SOURCE_NAME = "WGC GDT - Gold Recycling Flow (tonnes)"
SOURCE_URL = "https://www.gold.org/"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "wgc"
PARSED_CACHE_PATH = PROJECT_ROOT / "data" / "cache" / "wgc" / "gdt_quarterly.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / f"{VARIABLE_ID}.json"


def parse_recycling_workbook(path: Path, *, cache_path: Path | None = PARSED_CACHE_PATH) -> list[dict[str, Any]]:
    """Extract quarterly recycled-gold supply from the detected GDT row."""
    return parse_gdt_quarterly_workbook(path, cache_path=cache_path)["recycling"]


def build_output(observations: list[dict[str, Any]], *, cached: bool = False, as_of_date: str | None = None) -> dict[str, Any]:
    """Build the quarterly L0-006 output."""
    output = build_quarterly_output(VARIABLE_ID, SOURCE_NAME, SOURCE_URL, observations, value_label="Gold recycling supply", rising_signal=-1, falling_signal=1, cached=cached, as_of_date=as_of_date)
    output["calculation_method"] = "WGC GDT Gold Balance recycled-gold supply row"
    return output


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build a degraded quarterly output."""
    return {"variable_id": VARIABLE_ID, "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_frequency": "Quarterly", "observation_date": None, "calculation_method": "WGC GDT recycled-gold supply row", "horizons": {"1-5d": {"signal": 0, "confidence": 1, "evidence": {"summary": "Quarterly data does not support 1-5d horizon."}}, "1-3m": {"signal": 0, "confidence": 1, "evidence": {"summary": "Quarterly data does not support 1-3m horizon."}}, "1-3y": degraded(summary), "3-10y": degraded(summary)}}


def run(*, output_path: Path = OUTPUT_PATH, raw_dir: Path = RAW_DIR) -> dict[str, Any]:
    """Collect, parse, and write current L0-006 JSON."""
    workbook = wgc.fetch_wgc_gdt_workbook(raw_dir)
    if workbook is None:
        summary = "STALE DATA — WGC GDT workbook is unavailable and no fresh cache exists." if wgc.LAST_FETCH_STALE else "SOURCE UNAVAILABLE — WGC GDT workbook could not be downloaded."
        output = build_degraded_output(summary)
    else:
        try:
            output = build_output(parse_recycling_workbook(workbook), cached=wgc.LAST_FETCH_USED_CACHE)
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
