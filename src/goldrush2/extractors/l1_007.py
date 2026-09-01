"""DR2 extractor for L1-007: 5Y5Y Forward Real Rate."""

from __future__ import annotations

import json
import math
import time
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors.fred import FredError, load_cached_series
from goldrush2.extractors import l1_001, l1_002

SOURCE_NAME = "Derived from DFII10 and DFII5 (5Y5Y forward real rate)"
SOURCE_URL = "https://fred.stlouisfed.org/series/DFII10 and https://fred.stlouisfed.org/series/DFII5"
CALCULATION_FORMULA = "((((1 + r10/100)^10 / (1 + r5/100)^5) ^ (1/5)) - 1) * 100"
CACHE_MAX_AGE_DAYS = 7
HORIZON_LOOKBACKS = {
    "1-5d": 5,
    "1-3m": 63,
    "1-3y": 252,
    "3-10y": 756,
}

OUTPUT_PATH = l1_001.PROJECT_ROOT / "data" / "current" / "L1-007.json"


class DependencyError(RuntimeError):
    """Raised when an L1-001 or L1-002 dependency cannot be used."""


def _empty_evidence_data() -> dict[str, None]:
    return {
        "current_value": None,
        "current_date": None,
        "comparison_value": None,
        "comparison_date": None,
        "change_percentage_points": None,
    }


def _degraded_horizon(summary: str) -> dict[str, Any]:
    return {
        "signal": 0,
        "confidence": 0,
        "evidence": {"data": _empty_evidence_data(), "summary": summary},
    }


def _forward_rate(r10: float, r5: float) -> float:
    """Calculate the 5Y5Y real forward rate from 5Y and 10Y spot yields."""
    if not math.isfinite(r10) or not math.isfinite(r5):
        raise DependencyError("DEPENDENCY FAILED — a real-yield input is non-finite")

    base10 = 1 + r10 / 100
    base5 = 1 + r5 / 100
    if base10 <= 0 or base5 <= 0:
        raise DependencyError("DEPENDENCY FAILED — real-yield input is outside the formula domain")

    return (((base10**10 / base5**5) ** (1 / 5)) - 1) * 100


def _valid_horizon(
    current: dict[str, str | float],
    comparison: dict[str, str | float],
    *,
    cached: bool,
) -> dict[str, Any]:
    current_value = float(current["value"])
    comparison_value = float(comparison["value"])
    change = round(current_value - comparison_value, 10)

    if change < 0:
        signal = 1
        summary = (
            f"The 5Y5Y forward real rate fell by {abs(change):.2f} percentage points, "
            "bullish for gold."
        )
    elif change > 0:
        signal = -1
        summary = (
            f"The 5Y5Y forward real rate rose by {change:.2f} percentage points, "
            "bearish for gold."
        )
    else:
        signal = 0
        summary = "The 5Y5Y forward real rate was unchanged, neutral for gold."

    if cached:
        summary += " DEPENDENT SOURCE UNAVAILABLE — cached data used."

    return {
        "signal": signal,
        "confidence": 1,
        "evidence": {
            "data": {
                "current_value": current_value,
                "current_date": current["date"],
                "comparison_value": comparison_value,
                "comparison_date": comparison["date"],
                "change_percentage_points": change,
            },
            "summary": summary,
        },
    }


def _output_template(
    horizons: dict[str, Any],
    *,
    observation_date: str | None,
    as_of_date: str | None = None,
) -> dict[str, Any]:
    return {
        "variable_id": "L1-007",
        "as_of_date": as_of_date or date.today().isoformat(),
        "observation_date": observation_date,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "calculation_formula": CALCULATION_FORMULA,
        "horizons": horizons,
    }


def build_output(
    observations10: list[dict[str, str | float]],
    observations5: list[dict[str, str | float]],
    *,
    cached: bool = False,
    as_of_date: str | None = None,
) -> dict[str, Any]:
    """Build L1-007 from two aligned real-yield observation series."""
    series10 = {str(row["date"]): float(row["value"]) for row in observations10}
    series5 = {str(row["date"]): float(row["value"]) for row in observations5}
    common_dates = sorted(set(series10) & set(series5))
    if len(common_dates) < max(HORIZON_LOOKBACKS.values()):
        raise DependencyError(
            "MISSING DEPENDENT DATA — at least 756 aligned DFII10 and DFII5 observations are required"
        )

    forward_series = [
        {
            "date": observation_date,
            "value": _forward_rate(series10[observation_date], series5[observation_date]),
        }
        for observation_date in common_dates
    ]
    current = forward_series[-1]
    horizons = {
        horizon: _valid_horizon(current, forward_series[-lookback], cached=cached)
        for horizon, lookback in HORIZON_LOOKBACKS.items()
    }
    return _output_template(
        horizons,
        observation_date=str(current["date"]),
        as_of_date=as_of_date,
    )


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    return _output_template(
        {horizon: _degraded_horizon(summary) for horizon in HORIZON_LOOKBACKS},
        observation_date=None,
        as_of_date=as_of_date,
    )


def _cache_is_fresh(path: Path) -> bool:
    age_seconds = max(0.0, time.time() - path.stat().st_mtime)
    return age_seconds < CACHE_MAX_AGE_DAYS * 24 * 60 * 60


def _read_current_output(path: Path, variable_id: str) -> tuple[dict[str, Any], bool]:
    try:
        output = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DependencyError(f"DEPENDENCY FAILED — cannot read {variable_id} current output") from exc
    if output.get("variable_id") != variable_id:
        raise DependencyError(f"DEPENDENCY FAILED — current output is not {variable_id}")

    cached = False
    for horizon in ("1-5d", "1-3m", "1-3y"):
        result = output.get("horizons", {}).get(horizon)
        if not isinstance(result, dict) or result.get("confidence") != 1:
            raise DependencyError(f"DEPENDENCY FAILED — {variable_id} has zero-confidence data")
        summary = result.get("evidence", {}).get("summary", "")
        if "SOURCE UNAVAILABLE — cached data used" in summary:
            cached = True
    return output, cached


def _load_dependencies() -> tuple[list[dict[str, str | float]], list[dict[str, str | float]], bool]:
    output10, cached10 = _read_current_output(l1_001.OUTPUT_PATH, "L1-001")
    output5, cached5 = _read_current_output(l1_002.OUTPUT_PATH, "L1-002")
    raw_paths = ((l1_001.RAW_PATH, "L1-001"), (l1_002.RAW_PATH, "L1-002"))
    observations: list[list[dict[str, str | float]]] = []

    for raw_path, variable_id in raw_paths:
        if not raw_path.exists() or not _cache_is_fresh(raw_path):
            raise DependencyError(f"STALE DEPENDENT DATA — {variable_id} raw cache is missing or older than 7 days")
        try:
            observations.append(load_cached_series(raw_path))
        except FredError as exc:
            raise DependencyError(f"DEPENDENCY FAILED — cannot read {variable_id} raw cache") from exc

    if len(observations[0]) < 756 or len(observations[1]) < 756:
        raise DependencyError("MISSING DEPENDENT DATA — both dependencies need at least 756 valid observations")

    current10 = output10["horizons"]["1-5d"]["evidence"]["data"]
    current5 = output5["horizons"]["1-5d"]["evidence"]["data"]
    if current10.get("current_date") != observations[0][-1]["date"] or current5.get("current_date") != observations[1][-1]["date"]:
        raise DependencyError("DEPENDENCY FAILED — current output and raw cache dates do not align")
    for data, dependency_observations, variable_id in (
        (current10, observations[0], "L1-001"),
        (current5, observations[1], "L1-002"),
    ):
        value = data.get("current_value")
        if value is None or not math.isfinite(float(value)):
            raise DependencyError(f"DEPENDENCY FAILED — {variable_id} current value is unavailable")
        if not math.isclose(float(value), float(dependency_observations[-1]["value"]), abs_tol=1e-12):
            raise DependencyError(f"DEPENDENCY FAILED — {variable_id} current value does not match raw cache")

    return observations[0], observations[1], cached10 or cached5


def _write_output(path: Path, output: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


def run(*, output_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Read current L1-001/L1-002 data and write the derived L1-007 output."""
    try:
        observations10, observations5, cached = _load_dependencies()
        if cached:
            print("DEPENDENT SOURCE UNAVAILABLE — cached data used")
        output = build_output(observations10, observations5, cached=cached)
    except DependencyError as exc:
        output = build_degraded_output(str(exc))

    _write_output(output_path, output)
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
