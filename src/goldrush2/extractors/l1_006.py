"""DR2 extractor for L1-006: expected policy rate."""

from __future__ import annotations

import json
import time
from calendar import monthrange
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors import cme
from goldrush2.collectors.fred import FredError, fetch_series, load_cached_series
from goldrush2.constants import POLICY_RATE_THRESHOLD_PP

SOURCE_NAME = "CME 30-Day Fed Funds Futures + FRED DFF/FEDTARMD"
SOURCE_URL = cme.SOURCE_URL
CACHE_MAX_AGE_DAYS = 7
FRED_DFF_RAW_PATH = Path(__file__).resolve().parents[3] / "data" / "raw" / "fred" / "DFF.json"
FRED_TARMD_RAW_PATH = Path(__file__).resolve().parents[3] / "data" / "raw" / "fred" / "FEDTARMD.json"
RAW_CME_PATH = cme.DEFAULT_RAW_PATH
MANIFEST_CME_PATH = cme.DEFAULT_MANIFEST_PATH
OUTPUT_PATH = Path(__file__).resolve().parents[3] / "data" / "current" / "L1-006.json"
SHARED_RATE_CACHE_PATH = Path(__file__).resolve().parents[3] / "data" / "cache" / "L1-006.json"


class DependencyError(RuntimeError):
    """Raised when an L1-006 dependency is unavailable."""


def _add_months(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    year, month_zero = divmod(index, 12)
    month = month_zero + 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


def select_contract(rows: list[dict[str, str | float]], horizon: str, observation_date: date) -> tuple[dict[str, str | float], date | None]:
    """Select the approved active contract mapping for one horizon."""
    active = [row for row in rows if date.fromisoformat(str(row["expiry_date"])) > observation_date]
    if not active:
        raise DependencyError(f"MISSING DATA — no active CME ZQ contract for {horizon}")
    if horizon == "1-5d":
        return min(active, key=lambda row: str(row["expiry_date"])), None
    if horizon == "1-3m":
        target = _add_months(observation_date, 3)
        return min(active, key=lambda row: abs((date.fromisoformat(str(row["expiry_date"])) - target).days)), target
    return max(active, key=lambda row: str(row["expiry_date"])), None


def _empty_data() -> dict[str, None]:
    return {"current_value": None, "current_date": None, "comparison_value": None, "comparison_date": None, "change_percentage_points": None}


def _degraded(summary: str) -> dict[str, Any]:
    return {"signal": 0, "confidence": 0, "evidence": {"data": _empty_data(), "summary": summary}}


def _short_result(contract: dict[str, str | float], current_rate: dict[str, str | float], target: date | None, *, cached: bool) -> dict[str, Any]:
    implied = float(contract["implied_rate"])
    benchmark = float(current_rate["value"])
    change = round(implied - benchmark, 10)
    if change > POLICY_RATE_THRESHOLD_PP:
        signal, direction = -1, "expected rate increase, bearish for gold"
    elif change < -POLICY_RATE_THRESHOLD_PP:
        signal, direction = 1, "expected rate cut, bullish for gold"
    else:
        signal, direction = 0, "within the neutral threshold"
    summary = f"CME {contract['contract']} implied rate {implied:.2f}% vs current rate {benchmark:.2f}% — {direction}."
    if target is not None:
        actual = date.fromisoformat(str(contract["expiry_date"]))
        summary += f" Contract expires {actual.isoformat()} vs target {target.isoformat()}."
    if cached:
        summary += " DEPENDENT SOURCE UNAVAILABLE — cached data used."
    data: dict[str, Any] = {"contract": contract["contract"], "expiry_date": contract["expiry_date"], "settlement_price": contract["settlement_price"], "implied_rate": implied, "current_rate": benchmark, "current_rate_date": current_rate["date"], "expected_change_pp": change, "threshold_pp": POLICY_RATE_THRESHOLD_PP}
    if target is not None:
        data["target_date"] = target.isoformat()
        data["target_deviation_days"] = (date.fromisoformat(str(contract["expiry_date"])) - target).days
    return {"signal": signal, "confidence": 1, "evidence": {"data": data, "summary": summary}}


def _long_result(prediction: dict[str, str | float], current_rate: dict[str, str | float], *, cached: bool) -> dict[str, Any]:
    predicted = float(prediction["value"])
    benchmark = float(current_rate["value"])
    change = round(predicted - benchmark, 10)
    if change > POLICY_RATE_THRESHOLD_PP:
        signal, direction = -1, "long-term expected rate increase, bearish for gold"
    elif change < -POLICY_RATE_THRESHOLD_PP:
        signal, direction = 1, "long-term expected rate cut, bullish for gold"
    else:
        signal, direction = 0, "within the neutral threshold"
    summary = f"FEDTARMD annual SEP projection {predicted:.2f}% dated {prediction['date']} vs current rate {benchmark:.2f}% — {direction}; this is a central bank forecast, not market-implied."
    if cached:
        summary += " DEPENDENT SOURCE UNAVAILABLE — cached data used."
    return {"signal": signal, "confidence": 1, "evidence": {"data": {"source": "FEDTARMD_annual_sep_projection", "prediction_value": predicted, "prediction_date": prediction["date"], "current_rate": benchmark, "current_rate_date": current_rate["date"], "expected_change_pp": change, "threshold_pp": POLICY_RATE_THRESHOLD_PP, "frequency": "Annual"}, "summary": summary}}


def _cache_fresh(path: Path) -> bool:
    return max(0.0, time.time() - path.stat().st_mtime) < CACHE_MAX_AGE_DAYS * 86400


def _fred_dependency(series_id: str, raw_path: Path) -> tuple[list[dict[str, str | float]], bool, str | None]:
    try:
        return fetch_series(series_id, raw_path=raw_path), False, None
    except FredError as exc:
        if raw_path.exists() and _cache_fresh(raw_path):
            try:
                return load_cached_series(raw_path), True, None
            except FredError as cache_exc:
                return [], False, f"DEPENDENCY FAILED — {cache_exc}"
        if raw_path.exists():
            return [], False, f"STALE DATA — FRED {series_id} cache is 7 days old or older: {exc}"
        return [], False, f"DEPENDENCY FAILED — {exc}"


def _cme_dependency(raw_path: Path, manifest_path: Path) -> tuple[list[dict[str, str | float]], date, bool, str | None]:
    try:
        pdf_path, manifest = cme.fetch_cme_bulletin(raw_path=raw_path, manifest_path=manifest_path)
        return cme.parse_fed_futures_table(pdf_path), date.fromisoformat(str(manifest["download_date"])), False, None
    except cme.CmeError as exc:
        if raw_path.exists() and manifest_path.exists() and _cache_fresh(raw_path):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                return cme.parse_fed_futures_table(raw_path), date.fromisoformat(str(manifest["download_date"])), True, None
            except (OSError, json.JSONDecodeError, ValueError, cme.CmeError) as cache_exc:
                return [], date.today(), False, f"DEPENDENCY FAILED — {cache_exc}"
        if raw_path.exists():
            return [], date.today(), False, f"STALE DATA — CME PDF cache is 7 days old or older: {exc}"
        return [], date.today(), False, f"DEPENDENCY FAILED — {exc}"


def build_output(rows: list[dict[str, str | float]], observation_date: date, dff: list[dict[str, str | float]], tar_md: list[dict[str, str | float]], *, cme_cached: bool = False, dff_cached: bool = False, tar_md_cached: bool = False, as_of_date: str | None = None) -> dict[str, Any]:
    benchmark_rows = [row for row in dff if date.fromisoformat(str(row["date"])) <= observation_date]
    if not benchmark_rows:
        raise DependencyError("DEPENDENCY FAILED — no DFF observation on or before CME observation date")
    benchmark = max(benchmark_rows, key=lambda row: str(row["date"]))
    horizons: dict[str, Any] = {}
    for horizon in ("1-5d", "1-3m", "1-3y"):
        contract, target = select_contract(rows, horizon, observation_date)
        horizons[horizon] = _short_result(contract, benchmark, target, cached=cme_cached or dff_cached)
    if not tar_md:
        raise DependencyError("DEPENDENCY FAILED — FEDTARMD has no valid observation")
    prediction = max(tar_md, key=lambda row: str(row["date"]))
    horizons["3-10y"] = _long_result(prediction, benchmark, cached=dff_cached or tar_md_cached)
    return {"variable_id": "L1-006", "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "observation_date": observation_date.isoformat(), "current_rate_benchmark": "FRED DFF", "calculation_method": "CME ZQ implied rate (100 - settlement price) versus DFF; FEDTARMD annual SEP supplement for 3-10y", "horizons": horizons}


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    return {"variable_id": "L1-006", "as_of_date": as_of_date or date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "observation_date": None, "current_rate_benchmark": "FRED DFF", "calculation_method": "CME ZQ implied rate (100 - settlement price) versus DFF; FEDTARMD annual SEP supplement for 3-10y", "horizons": {horizon: _degraded(summary) for horizon in ("1-5d", "1-3m", "1-3y", "3-10y")}}


def _write_output(path: Path, output: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


def _write_shared_rate_cache(output: dict[str, Any]) -> None:
    """Append the current nearest-ZQ implied rate for dependent extractors."""
    data = output.get("horizons", {}).get("1-5d", {}).get("evidence", {}).get("data", {})
    rate = data.get("implied_rate")
    observation_date = output.get("observation_date")
    if rate is None or observation_date is None:
        return
    try:
        rows = json.loads(SHARED_RATE_CACHE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        rows = []
    rows = [row for row in rows if row.get("date") != observation_date]
    rows.append({"date": observation_date, "rate": rate})
    rows.sort(key=lambda row: str(row["date"]))
    SHARED_RATE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = SHARED_RATE_CACHE_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    temporary.replace(SHARED_RATE_CACHE_PATH)


def run(*, output_path: Path = OUTPUT_PATH, force: bool = False) -> dict[str, Any]:
    """Collect CME, DFF, and FEDTARMD dependencies and write L1-006."""
    rows, observation_date, cme_cached, cme_error = _cme_dependency(RAW_CME_PATH, MANIFEST_CME_PATH)
    dff, dff_cached, dff_error = _fred_dependency("DFF", FRED_DFF_RAW_PATH)
    tar_md, tar_md_cached, tar_md_error = _fred_dependency("FEDTARMD", FRED_TARMD_RAW_PATH)
    if dff_error:
        output = build_degraded_output(dff_error)
    else:
        benchmark_rows = [row for row in dff if date.fromisoformat(str(row["date"])) <= observation_date]
        if not benchmark_rows:
            output = build_degraded_output("DEPENDENCY FAILED — no DFF observation on or before CME observation date")
        else:
            benchmark = max(benchmark_rows, key=lambda row: str(row["date"]))
            horizons: dict[str, Any] = {}
            for horizon in ("1-5d", "1-3m", "1-3y"):
                if cme_error:
                    horizons[horizon] = _degraded(cme_error)
                else:
                    try:
                        contract, target = select_contract(rows, horizon, observation_date)
                        horizons[horizon] = _short_result(contract, benchmark, target, cached=cme_cached or dff_cached)
                    except DependencyError as exc:
                        horizons[horizon] = _degraded(str(exc))
            if tar_md_error or not tar_md:
                horizons["3-10y"] = _degraded(tar_md_error or "DEPENDENCY FAILED — FEDTARMD has no valid observation")
            else:
                prediction = max(tar_md, key=lambda row: str(row["date"]))
                horizons["3-10y"] = _long_result(prediction, benchmark, cached=dff_cached or tar_md_cached)
            output = {"variable_id": "L1-006", "as_of_date": date.today().isoformat(), "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "observation_date": observation_date.isoformat() if not cme_error else None, "current_rate_benchmark": "FRED DFF", "calculation_method": "CME ZQ implied rate (100 - settlement price) versus DFF; FEDTARMD annual SEP supplement for 3-10y", "horizons": horizons}
    try:
        cme.refresh_zq_history(force=force, cache_path=SHARED_RATE_CACHE_PATH)
    except cme.CmeError:
        # The current L1-006 output remains usable when Yahoo is unavailable.
        pass
    _write_output(output_path, output)
    _write_shared_rate_cache(output)
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
