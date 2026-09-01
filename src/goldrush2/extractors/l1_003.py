"""DR2 extractor for L1-003: composite forward real rates."""

from __future__ import annotations

import json
import math
import time
from datetime import date
from pathlib import Path
from typing import Any

from goldrush2.collectors.frb_tips import (
    FrbTipsError,
    fetch_tips_yield,
    load_cached_tips_yield,
)

SOURCE_NAME = "Federal Reserve Board TIPS Yield Curve (smoothed yields)"
SOURCE_URL = "https://www.federalreserve.gov/data/yield-curve-tables/feds200805.csv"
CALCULATION_METHOD = (
    "Composite of 2Y3Y and 5Y5Y forward rates, equally weighted "
    "(1Y1Y omitted because 1Y TIPS spot data is not available from the FRB dataset)"
)
CACHE_MAX_AGE_DAYS = 7
HORIZON_LOOKBACKS = {
    "1-5d": 5,
    "1-3m": 63,
    "1-3y": 252,
    "3-10y": 756,
}

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "frb_tips" / "real_yield_curve.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "current" / "L1-003.json"


class DependencyError(RuntimeError):
    """Raised when a required FRB TIPS input cannot be used."""


def _forward_2y3y(r5: float, r2: float) -> float:
    """Calculate the implied three-year real rate beginning two years ahead."""
    if not all(math.isfinite(value) for value in (r5, r2)):
        raise DependencyError("DEPENDENCY FAILED — a real-yield input is non-finite")
    base5 = 1 + r5 / 100
    base2 = 1 + r2 / 100
    if base5 <= 0 or base2 <= 0:
        raise DependencyError("DEPENDENCY FAILED — real-yield input is outside formula domain")
    return (((base5**5 / base2**2) ** (1 / 3)) - 1) * 100


def _forward_5y5y(r10: float, r5: float) -> float:
    """Calculate the implied five-year real rate beginning five years ahead."""
    if not all(math.isfinite(value) for value in (r10, r5)):
        raise DependencyError("DEPENDENCY FAILED — a real-yield input is non-finite")
    base10 = 1 + r10 / 100
    base5 = 1 + r5 / 100
    if base10 <= 0 or base5 <= 0:
        raise DependencyError("DEPENDENCY FAILED — real-yield input is outside formula domain")
    return (((base10**10 / base5**5) ** (1 / 5)) - 1) * 100


def _composite(r2: float, r5: float, r10: float) -> tuple[float, dict[str, float]]:
    """Calculate the two-node composite and expose both node values."""
    node_2y3y = _forward_2y3y(r5, r2)
    node_5y5y = _forward_5y5y(r10, r5)
    return (node_2y3y + node_5y5y) / 2, {
        "forward_2y3y": node_2y3y,
        "forward_5y5y": node_5y5y,
    }


def build_composite_series(
    observations2: list[dict[str, str | float]],
    observations5: list[dict[str, str | float]],
    observations10: list[dict[str, str | float]],
) -> tuple[list[dict[str, str | float]], dict[str, float]]:
    """Build aligned composite observations, skipping incomplete dates."""
    series = []
    by_maturity = [
        {str(row["date"]): float(row["value"]) for row in observations}
        for observations in (observations2, observations5, observations10)
    ]
    common_dates = sorted(set(by_maturity[0]) & set(by_maturity[1]) & set(by_maturity[2]))
    for observation_date in common_dates:
        try:
            value, nodes = _composite(
                by_maturity[0][observation_date],
                by_maturity[1][observation_date],
                by_maturity[2][observation_date],
            )
        except DependencyError:
            continue
        series.append({"date": observation_date, "value": value, **nodes})

    if not series:
        raise DependencyError("MISSING DEPENDENT DATA — no complete FRB TIPS observations")
    return series, {
        "forward_2y3y": float(series[-1]["forward_2y3y"]),
        "forward_5y5y": float(series[-1]["forward_5y5y"]),
    }


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
            f"The composite forward real rate fell by {abs(change):.2f} percentage points, "
            "bullish for gold."
        )
    elif change > 0:
        signal = -1
        summary = (
            f"The composite forward real rate rose by {change:.2f} percentage points, "
            "bearish for gold."
        )
    else:
        signal = 0
        summary = "The composite forward real rate was unchanged, neutral for gold."
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
    forward_nodes: dict[str, float | None],
    as_of_date: str | None = None,
) -> dict[str, Any]:
    return {
        "variable_id": "L1-003",
        "as_of_date": as_of_date or date.today().isoformat(),
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "observation_date": observation_date,
        "calculation_method": CALCULATION_METHOD,
        "forward_nodes": forward_nodes,
        "horizons": horizons,
    }


def build_output(
    observations2: list[dict[str, str | float]],
    observations5: list[dict[str, str | float]],
    observations10: list[dict[str, str | float]],
    *,
    cached: bool = False,
    as_of_date: str | None = None,
) -> dict[str, Any]:
    """Build L1-003 from aligned FRB TIPS spot-rate observations."""
    series, nodes = build_composite_series(observations2, observations5, observations10)
    horizons: dict[str, Any] = {}
    current = series[-1]
    for horizon, lookback in HORIZON_LOOKBACKS.items():
        if len(series) < lookback:
            data = _empty_evidence_data()
            data["current_value"] = float(current["value"])
            data["current_date"] = str(current["date"])
            summary = (
                "MISSING DATA — "
                f"{lookback} valid composite observations are required; "
                f"{len(series)} are available."
            )
            if cached:
                summary += " DEPENDENT SOURCE UNAVAILABLE — cached data used."
            horizons[horizon] = {
                "signal": 0,
                "confidence": 0,
                "evidence": {
                    "data": data,
                    "summary": summary,
                },
            }
            continue
        horizons[horizon] = _valid_horizon(current, series[-lookback], cached=cached)
    return _output_template(
        horizons,
        observation_date=str(current["date"]),
        forward_nodes=nodes,
        as_of_date=as_of_date,
    )


def build_degraded_output(summary: str, *, as_of_date: str | None = None) -> dict[str, Any]:
    """Build an all-horizon zero-confidence derived result."""
    return _output_template(
        {horizon: _degraded_horizon(summary) for horizon in HORIZON_LOOKBACKS},
        observation_date=None,
        forward_nodes={"forward_2y3y": None, "forward_5y5y": None},
        as_of_date=as_of_date,
    )


def _cache_is_fresh(path: Path) -> bool:
    age_seconds = max(0.0, time.time() - path.stat().st_mtime)
    return age_seconds < CACHE_MAX_AGE_DAYS * 24 * 60 * 60


def _write_output(path: Path, output: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


def _load_from_cache(path: Path) -> tuple[list[dict[str, str | float]], list[dict[str, str | float]], list[dict[str, str | float]]]:
    return tuple(
        load_cached_tips_yield(path, maturity)
        for maturity in ("2Y", "5Y", "10Y")
    )  # type: ignore[return-value]


def run(*, raw_path: Path = RAW_PATH, output_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    """Collect the FRB curve once, apply cache rules, and write L1-003."""
    try:
        fetch_tips_yield("2Y", raw_path=raw_path)
        observations2, observations5, observations10 = _load_from_cache(raw_path)
        output = build_output(observations2, observations5, observations10)
    except (FrbTipsError, DependencyError) as exc:
        if raw_path.exists() and _cache_is_fresh(raw_path):
            try:
                observations2, observations5, observations10 = _load_from_cache(raw_path)
                output = build_output(
                    observations2, observations5, observations10, cached=True
                )
            except (FrbTipsError, DependencyError) as cache_exc:
                output = build_degraded_output(f"DEPENDENCY FAILED — {cache_exc}")
            else:
                print("DEPENDENT SOURCE UNAVAILABLE — cached data used")
        elif raw_path.exists():
            output = build_degraded_output(
                "STALE DEPENDENT DATA — Federal Reserve TIPS source unavailable and "
                f"cached data is 7 days old or older: {exc}"
            )
        else:
            output = build_degraded_output(f"DEPENDENCY FAILED — {exc}")
    _write_output(output_path, output)
    return output


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
