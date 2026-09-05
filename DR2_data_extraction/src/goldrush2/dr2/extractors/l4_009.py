"""DR2 extractor for L4-009: Treasury debt maturing within one year."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from goldrush2.dr2.collectors.treasury import TreasuryError, fetch_treasury_table, flatten_data

VARIABLE_ID = "L4-009"
DATA_FREQUENCY = "Monthly"
SOURCE_NAME = "U.S. Treasury Fiscal Data - Monthly Statement of Public Debt Table 3 Marketable Securities"
SOURCE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/debt/mspd/mspd_table_3_market"
from goldrush2.paths import DR2_ROOT as PROJECT_ROOT
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "treasury" / "mspd_table_3.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / f"{VARIABLE_ID}.json"


def _amount(value: Any) -> float | None:
    try:
        result = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return result


def parse_observations(rows: list[dict[str, Any]]) -> list[dict[str, str | float]]:
    """Calculate monthly marketable debt maturity shares from Treasury rows."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        record_date = str(row.get("record_date", ""))[:10]
        if len(record_date) == 10:
            grouped.setdefault(record_date, []).append(row)
    output: list[dict[str, str | float]] = []
    for record_date, entries in grouped.items():
        as_of = date.fromisoformat(record_date)
        denominator = None
        numerator = 0.0
        for row in entries:
            labels = " ".join(str(row.get(key, "")) for key in ("security_type_desc", "security_class1_desc", "security_class2_desc"))
            amount = _amount(row.get("outstanding_amt"))
            if "total marketable" in labels.lower():
                if amount is not None:
                    denominator = amount
                continue
            if "summary" in labels.lower() or "total" in labels.lower():
                continue
            maturity_raw = str(row.get("maturity_date", ""))[:10]
            if amount is None or not maturity_raw:
                continue
            try:
                maturity = date.fromisoformat(maturity_raw)
            except ValueError:
                continue
            if as_of < maturity <= as_of + timedelta(days=365) and amount > 0:
                numerator += amount
        if denominator is not None and denominator > 0:
            output.append({"date": record_date, "value": numerator / denominator * 100})
    return sorted(output, key=lambda item: str(item["date"]))


def _empty_data() -> dict[str, None]:
    return {"current_value": None, "current_date": None, "comparison_value": None, "comparison_date": None, "change_absolute": None}


def _degraded(summary: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"signal": 0, "confidence": 0, "evidence": {"data": data if data is not None else _empty_data(), "summary": summary}}


def build_output(observations: list[dict[str, str | float]], *, cached: bool = False, as_of_date: str | None = None) -> dict[str, Any]:
    """Build monthly one-, three-, twelve-, and sixty-month comparisons."""
    ordered = sorted(observations, key=lambda item: str(item["date"]))
    current = ordered[-1] if ordered else None
    horizons: dict[str, Any] = {}
    for horizon, lookback in (("1-5d", 1), ("1-3m", 3), ("1-3y", 12), ("3-10y", 60)):
        if current is None or len(ordered) <= lookback:
            data = _empty_data()
            if current is not None:
                data["current_value"], data["current_date"] = float(current["value"]), str(current["date"])
            horizons[horizon] = _degraded(f"MISSING DATA — {lookback} prior monthly observations are required; {max(0, len(ordered) - 1)} are available.", data)
            continue
        comparison = ordered[-1 - lookback]
        current_value, comparison_value = float(current["value"]), float(comparison["value"])
        change = round(current_value - comparison_value, 10)
        if change > 0:
            signal, summary = 1, f"Short-term debt share rose by {change:.2f} percentage points (rollover risk increased), bullish for gold."
        elif change < 0:
            signal, summary = -1, f"Short-term debt share fell by {abs(change):.2f} percentage points, bearish for gold."
        else:
            signal, summary = 0, "Short-term debt share was unchanged, neutral for gold."
        summary += f" Note: data as of {current['date']}, subject to 1-2 month publication lag."
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
    """Fetch the recent MSPD marketable table and write the current result."""
    try:
        # The Treasury endpoint is operationally collected over a rolling
        # two-year window, matching the GR1 production collector. This covers
        # the current 1/3/12-month signals; the 60-month horizon degrades
        # explicitly when that window lacks sufficient history.
        start = (date.today() - timedelta(days=365 * 2)).isoformat()
        payload = fetch_treasury_table(SOURCE_URL, {"filter": f"record_date:gte:{start}", "sort": "record_date,src_line_nbr", "fields": "record_date,security_type_desc,security_class1_desc,security_class2_desc,maturity_date,outstanding_amt,src_line_nbr"}, raw_path)
        output = build_output(parse_observations(flatten_data(payload)), cached=payload.get("source_status") == "CACHED")
    except TreasuryError as exc:
        output = build_degraded_output(str(exc))
    _write_output(output_path, output)
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
