"""DR2 extractor for L4-008: annual interest expense as a share of revenue."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors.treasury import TreasuryError, fetch_treasury_table, flatten_data

VARIABLE_ID = "L4-008"
DATA_FREQUENCY = "Annual fiscal year"
SOURCE_NAME = "U.S. Treasury Fiscal Data - Monthly Treasury Statement Table 3"
SOURCE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/mts/mts_table_3"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "treasury" / "mts_table_3.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / f"{VARIABLE_ID}.json"


def _empty_data() -> dict[str, None]:
    return {"current_value": None, "current_date": None, "comparison_value": None, "comparison_date": None, "change_absolute": None}


def _degraded(summary: str, data: dict[str, Any] | None = None, *, confidence: int = 0) -> dict[str, Any]:
    return {"signal": 0, "confidence": confidence, "evidence": {"data": data if data is not None else _empty_data(), "summary": summary}}


def _amount(row: dict[str, Any]) -> float | None:
    raw = row.get("current_fytd_rcpt_outly_amt")
    try:
        value = float(str(raw).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return value


def parse_observations(rows: list[dict[str, Any]]) -> list[dict[str, str | float]]:
    """Pair September receipts and gross-interest rows into annual ratios."""
    grouped: dict[str, dict[str, float]] = {}
    for row in rows:
        record_date = str(row.get("record_date", ""))
        if len(record_date) < 7 or record_date[5:7] != "09":
            continue
        value = _amount(row)
        if value is None:
            continue
        code = str(row.get("line_code_nbr", "")).split(".")[0]
        if code == "130":
            grouped.setdefault(record_date, {})["receipts"] = value
        elif code == "360":
            grouped.setdefault(record_date, {})["interest"] = value
    result = []
    for record_date, values in grouped.items():
        if "receipts" in values and "interest" in values and values["receipts"] != 0:
            result.append({"date": record_date, "value": values["interest"] / values["receipts"] * 100})
    return sorted(result, key=lambda item: str(item["date"]))


def build_output(observations: list[dict[str, str | float]], *, cached: bool = False, as_of_date: str | None = None) -> dict[str, Any]:
    """Build annual fiscal-year and five-year L4-008 comparisons."""
    ordered = sorted(observations, key=lambda item: str(item["date"]))
    current = ordered[-1] if ordered else None
    horizons: dict[str, Any] = {}
    for horizon in ("1-5d", "1-3m"):
        summary = f"Annual fiscal-year data does not support {horizon} horizon."
        if cached:
            summary += " SOURCE UNAVAILABLE — cached data used."
        horizons[horizon] = _degraded(summary, confidence=1)
    for horizon, lookback in (("1-3y", 1), ("3-10y", 5)):
        if current is None or len(ordered) <= lookback:
            data = _empty_data()
            if current is not None:
                data["current_value"], data["current_date"] = float(current["value"]), str(current["date"])
            horizons[horizon] = _degraded(f"MISSING DATA — {lookback} prior annual observations are required; {max(0, len(ordered) - 1)} are available.", data)
            continue
        comparison = ordered[-1 - lookback]
        current_value, comparison_value = float(current["value"]), float(comparison["value"])
        change = round(current_value - comparison_value, 10)
        if change > 0:
            signal, summary = 1, f"Interest/revenue ratio rose by {change:.2f} percentage points (fiscal deterioration), bullish for gold."
        elif change < 0:
            signal, summary = -1, f"Interest/revenue ratio fell by {abs(change):.2f} percentage points, bearish for gold."
        else:
            signal, summary = 0, "Interest/revenue ratio was unchanged, neutral for gold."
        summary += " Note: annual fiscal-year data, short-term horizons not applicable."
        if cached:
            summary += " SOURCE UNAVAILABLE — cached data used."
        horizons[horizon] = {"signal": signal, "confidence": 1, "evidence": {"data": {"current_value": current_value, "current_date": current["date"], "comparison_value": comparison_value, "comparison_date": comparison["date"], "change_absolute": change}, "summary": summary}}
    return {"variable_id": VARIABLE_ID, "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_frequency": DATA_FREQUENCY, "observation_date": str(current["date"]) if current else None, "horizons": horizons}


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build a zero-confidence result for a Treasury failure."""
    return {"variable_id": VARIABLE_ID, "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_frequency": DATA_FREQUENCY, "observation_date": None, "horizons": {h: _degraded(summary) for h in ("1-5d", "1-3m", "1-3y", "3-10y")}}


def _write_output(path: Path, output: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


def run(*, raw_path: Path = RAW_PATH, output_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Fetch and transform Monthly Treasury Statement Table 3."""
    try:
        payload = fetch_treasury_table(SOURCE_URL, {"filter": "line_code_nbr:in:(130,360)", "sort": "record_date"}, raw_path)
        output = build_output(parse_observations(flatten_data(payload)), cached=payload.get("source_status") == "CACHED")
    except TreasuryError as exc:
        output = build_degraded_output(str(exc))
    _write_output(output_path, output)
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
